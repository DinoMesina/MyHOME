"""WebSocket API for MyHOME OpenWebNet integration.

Provides real-time bus streaming, historical frame inspection, and diagnostic
injection for the Lovelace bus monitor card.
"""
from __future__ import annotations

import logging
from typing import Any, Callable, Optional

import voluptuous as vol

from homeassistant.components import websocket_api
from homeassistant.core import HomeAssistant, callback
from homeassistant.helpers import config_validation as cv, device_registry as dr

from .bus_monitor import BusFrame, BusMonitor
from .const import CONF_ENTITY, DOMAIN
from .ownd.message import OWNMessage

_LOGGER = logging.getLogger(__name__)

WS_TYPE_HISTORY = "myhome/bus_monitor/history"
WS_TYPE_STREAM = "myhome/bus_monitor/stream"
WS_TYPE_SEND = "myhome/bus_monitor/send"
WS_TYPE_CLEAR = "myhome/bus_monitor/clear"

SCHEMA_WS_HISTORY = websocket_api.BASE_COMMAND_MESSAGE_SCHEMA.extend(
    {
        vol.Required("type"): WS_TYPE_HISTORY,
        vol.Optional("mac"): cv.string,
        vol.Optional("limit", default=100): vol.All(vol.Coerce(int), vol.Range(min=1, max=500)),
        vol.Optional("who"): vol.Any(cv.string, vol.Coerce(int)),
        vol.Optional("where"): cv.string,
        vol.Optional("direction"): vol.In(["rx", "tx", "all"]),
    }
)

SCHEMA_WS_STREAM = websocket_api.BASE_COMMAND_MESSAGE_SCHEMA.extend(
    {
        vol.Required("type"): WS_TYPE_STREAM,
        vol.Optional("mac"): cv.string,
        vol.Optional("who"): vol.Any(cv.string, vol.Coerce(int)),
        vol.Optional("where"): cv.string,
        vol.Optional("direction"): vol.In(["rx", "tx", "all"]),
    }
)

SCHEMA_WS_SEND = websocket_api.BASE_COMMAND_MESSAGE_SCHEMA.extend(
    {
        vol.Required("type"): WS_TYPE_SEND,
        vol.Required("frame"): cv.string,
        vol.Optional("mac"): cv.string,
    }
)

SCHEMA_WS_CLEAR = websocket_api.BASE_COMMAND_MESSAGE_SCHEMA.extend(
    {
        vol.Required("type"): WS_TYPE_CLEAR,
        vol.Optional("mac"): cv.string,
    }
)


def _get_gateway_and_monitor(
    hass: HomeAssistant, mac: Optional[str] = None
) -> tuple[Optional[Any], Optional[BusMonitor]]:
    """Retrieve the gateway handler and bus monitor for a given MAC or the primary gateway."""
    domain_data = hass.data.get(DOMAIN, {})
    if not isinstance(domain_data, dict):
        return None, None

    # If MAC is provided, look up specifically
    if mac:
        try:
            formatted_mac = dr.format_mac(mac)
        except Exception:
            formatted_mac = mac

        for key, val in domain_data.items():
            if isinstance(val, dict) and (key == mac or key == formatted_mac):
                gw = val.get(CONF_ENTITY)
                bm = val.get("bus_monitor") or getattr(gw, "bus_monitor", None)
                if gw or bm:
                    return gw, bm

    # Fallback to the first available gateway entry
    for key, val in domain_data.items():
        if isinstance(val, dict) and CONF_ENTITY in val:
            gw = val.get(CONF_ENTITY)
            bm = val.get("bus_monitor") or getattr(gw, "bus_monitor", None)
            if gw or bm:
                return gw, bm

    return None, None


def _matches_filter(
    frame: dict[str, Any] | BusFrame,
    who: Optional[Any] = None,
    where: Optional[str] = None,
    direction: Optional[str] = None,
) -> bool:
    """Check if a frame matches filter criteria."""
    f_who = str(getattr(frame, "who", None) if isinstance(frame, BusFrame) else frame.get("who"))
    f_where = str(getattr(frame, "where", None) if isinstance(frame, BusFrame) else frame.get("where"))
    f_dir = (getattr(frame, "direction", "") if isinstance(frame, BusFrame) else frame.get("direction", "")).lower()

    if direction and direction != "all" and f_dir != direction.lower():
        return False

    if who is not None and str(who) != f_who:
        return False

    if where is not None and str(where) != f_where:
        return False

    return True


@websocket_api.async_response
async def ws_bus_monitor_history(
    hass: HomeAssistant,
    connection: websocket_api.ActiveConnection,
    msg: dict[str, Any],
) -> None:
    """Return historical bus frames from the circular ring buffer."""
    _, monitor = _get_gateway_and_monitor(hass, msg.get("mac"))
    if monitor is None:
        connection.send_error(
            msg["id"],
            websocket_api.ERR_NOT_FOUND,
            "No active MyHOME gateway or bus monitor found",
        )
        return

    limit = msg.get("limit", 100)
    who = msg.get("who")
    where = msg.get("where")
    direction = msg.get("direction", "all")

    raw_frames = monitor.get_recent_frames(limit=monitor.maxlen)
    filtered = [
        f for f in raw_frames if _matches_filter(f, who=who, where=where, direction=direction)
    ]

    # Return newest frames up to requested limit
    if len(filtered) > limit:
        filtered = filtered[-limit:]

    connection.send_result(
        msg["id"],
        {
            "frames": filtered,
            "stats": monitor.get_stats(),
        },
    )


@websocket_api.async_response
async def ws_bus_monitor_stream(
    hass: HomeAssistant,
    connection: websocket_api.ActiveConnection,
    msg: dict[str, Any],
) -> None:
    """Subscribe to real-time bus monitor frames."""
    _, monitor = _get_gateway_and_monitor(hass, msg.get("mac"))
    if monitor is None:
        connection.send_error(
            msg["id"],
            websocket_api.ERR_NOT_FOUND,
            "No active MyHOME gateway or bus monitor found",
        )
        return

    who = msg.get("who")
    where = msg.get("where")
    direction = msg.get("direction", "all")

    @callback
    def forward_frame(frame: BusFrame) -> None:
        if _matches_filter(frame, who=who, where=where, direction=direction):
            connection.send_message(
                websocket_api.event_message(msg["id"], frame.to_dict())
            )

    unsub = monitor.subscribe(forward_frame)
    connection.subscriptions[msg["id"]] = unsub
    connection.send_result(msg["id"])


@websocket_api.async_response
async def ws_bus_monitor_send(
    hass: HomeAssistant,
    connection: websocket_api.ActiveConnection,
    msg: dict[str, Any],
) -> None:
    """Send an OpenWebNet diagnostic frame directly to the gateway."""
    gateway, _ = _get_gateway_and_monitor(hass, msg.get("mac"))
    if gateway is None:
        connection.send_error(
            msg["id"],
            websocket_api.ERR_NOT_FOUND,
            "No active MyHOME gateway found to transmit frame",
        )
        return

    frame_str = msg["frame"].strip()
    if not (frame_str.startswith("*") and frame_str.endswith("##")):
        connection.send_error(
            msg["id"],
            websocket_api.ERR_INVALID_FORMAT,
            f"Invalid OpenWebNet frame format: {frame_str}",
        )
        return

    try:
        parsed = OWNMessage.parse(frame_str)
        if parsed is None:
            parsed = OWNMessage(frame_str)
        await gateway.send(parsed)
    except Exception as ex:  # pylint: disable=broad-except
        _LOGGER.error("Failed to transmit frame %s via WebSocket: %s", frame_str, ex)
        connection.send_error(
            msg["id"],
            websocket_api.ERR_UNKNOWN_ERROR,
            f"Failed to transmit frame: {ex}",
        )
        return

    connection.send_result(
        msg["id"],
        {"success": True, "frame": frame_str},
    )


@websocket_api.async_response
async def ws_bus_monitor_clear(
    hass: HomeAssistant,
    connection: websocket_api.ActiveConnection,
    msg: dict[str, Any],
) -> None:
    """Clear the in-memory bus monitor ring buffer."""
    _, monitor = _get_gateway_and_monitor(hass, msg.get("mac"))
    if monitor is None:
        connection.send_error(
            msg["id"],
            websocket_api.ERR_NOT_FOUND,
            "No active MyHOME gateway or bus monitor found",
        )
        return

    monitor.clear()
    connection.send_result(msg["id"], {"success": True})


@callback
def async_setup_websocket_api(hass: HomeAssistant) -> None:
    """Register all MyHOME WebSocket commands."""
    domain_data = hass.data.setdefault(DOMAIN, {})
    if domain_data.get("_ws_registered"):
        return

    websocket_api.async_register_command(
        hass,
        ws_bus_monitor_history,
        SCHEMA_WS_HISTORY,
    )
    websocket_api.async_register_command(
        hass,
        ws_bus_monitor_stream,
        SCHEMA_WS_STREAM,
    )
    websocket_api.async_register_command(
        hass,
        ws_bus_monitor_send,
        SCHEMA_WS_SEND,
    )
    websocket_api.async_register_command(
        hass,
        ws_bus_monitor_clear,
        SCHEMA_WS_CLEAR,
    )

    domain_data["_ws_registered"] = True
    _LOGGER.info("Registered MyHOME WebSocket API commands for Bus Monitor")
