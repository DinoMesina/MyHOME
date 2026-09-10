"""Provides device triggers for MyHOME CEN / CEN+ buttons."""
from __future__ import annotations

from typing import Any

import voluptuous as vol
from homeassistant.components.device_automation import DEVICE_TRIGGER_BASE_SCHEMA
from homeassistant.const import (
    CONF_DEVICE_ID,
    CONF_DOMAIN,
    CONF_PLATFORM,
    CONF_TYPE,
)
from homeassistant.core import CALLBACK_TYPE, HomeAssistant
from homeassistant.helpers import device_registry as dr
from homeassistant.helpers.typing import ConfigType

from .const import (
    CONF_LONG_PRESS,
    CONF_LONG_RELEASE,
    CONF_ROTARY_CCW_FAST,
    CONF_ROTARY_CCW_SLOW,
    CONF_ROTARY_CW_FAST,
    CONF_ROTARY_CW_SLOW,
    CONF_SHORT_PRESS,
    CONF_SHORT_RELEASE,
    DOMAIN,
)

CONF_ADDRESS = "address"
CONF_OBJECT = "object"
CONF_SUBTYPE = "subtype"

TRIGGER_TYPES = {
    CONF_SHORT_PRESS,
    CONF_SHORT_RELEASE,
    CONF_LONG_PRESS,
    CONF_LONG_RELEASE,
    CONF_ROTARY_CW_SLOW,
    CONF_ROTARY_CW_FAST,
    CONF_ROTARY_CCW_SLOW,
    CONF_ROTARY_CCW_FAST,
}

TRIGGER_SUBTYPES = [f"button_{i}" for i in range(0, 32)]

TRIGGER_SCHEMA = DEVICE_TRIGGER_BASE_SCHEMA.extend(
    {
        vol.Required(CONF_TYPE): vol.In(TRIGGER_TYPES),
        vol.Required(CONF_SUBTYPE): vol.In(TRIGGER_SUBTYPES),
        vol.Optional(CONF_ADDRESS): vol.Coerce(int),
        vol.Optional(CONF_OBJECT): vol.Coerce(int),
    }
)


def _get_cen_info_from_device(device: dr.DeviceEntry) -> tuple[bool, int | None]:
    """Check if device is a CEN/CEN+ scenario device or gateway, and extract address if available.

    Returns:
        (is_cen_or_gateway, address)
    """
    is_myhome = any(identifier[0] == DOMAIN for identifier in device.identifiers)
    if not is_myhome:
        return False, None

    for identifier in device.identifiers:
        if identifier[0] != DOMAIN:
            continue
        ident = str(identifier[1])
        parts = ident.split("-")
        # Identifiers like "{mac}-15-{where}" or "{mac}-25-{where}"
        if len(parts) >= 3 and parts[-2] in ("15", "25", "cen", "cenplus"):
            try:
                return True, int(parts[-1])
            except ValueError:
                pass
        elif ident.startswith("cen_") or ident.startswith("cenplus_"):
            try:
                return True, int(ident.split("_", 1)[1])
            except ValueError:
                pass

    # Reject standard entities that are not button transmitters
    # (e.g. lights, covers, thermostats, binary sensors with WHO in 1, 2, 4, 5, 9, 18)
    for identifier in device.identifiers:
        if identifier[0] != DOMAIN:
            continue
        ident = str(identifier[1])
        parts = ident.split("-")
        if len(parts) >= 3 and parts[-2] in ("1", "2", "4", "5", "9", "18"):
            return False, None

    # Gateway or unspecified MyHOME device
    return True, None


async def async_get_triggers(
    hass: HomeAssistant, device_id: str
) -> list[dict[str, Any]]:
    """List device triggers for MyHOME CEN/CEN+ devices."""
    device_registry = dr.async_get(hass)
    device = device_registry.async_get(device_id)

    if device is None:
        return []

    is_valid, address = _get_cen_info_from_device(device)
    if not is_valid:
        return []

    triggers = []
    for trigger_type in TRIGGER_TYPES:
        for subtype in TRIGGER_SUBTYPES:
            trigger: dict[str, Any] = {
                CONF_PLATFORM: "device",
                CONF_DEVICE_ID: device_id,
                CONF_DOMAIN: DOMAIN,
                CONF_TYPE: trigger_type,
                CONF_SUBTYPE: subtype,
            }
            if address is not None:
                trigger[CONF_ADDRESS] = address
            triggers.append(trigger)

    return triggers


async def async_attach_trigger(
    hass: HomeAssistant,
    config: ConfigType,
    action: Any,
    trigger_info: dict[str, Any],
) -> CALLBACK_TYPE:
    """Attach a trigger to Home Assistant event bus."""
    trigger_type = config[CONF_TYPE]
    subtype = config[CONF_SUBTYPE]
    button_num = int(subtype.replace("button_", ""))

    # Determine target scenario address from config or associated device
    target_address = config.get(CONF_ADDRESS)
    if target_address is None:
        target_address = config.get(CONF_OBJECT)
    if target_address is None and CONF_DEVICE_ID in config:
        device_registry = dr.async_get(hass)
        device = device_registry.async_get(config[CONF_DEVICE_ID])
        if device is not None:
            _, dev_addr = _get_cen_info_from_device(device)
            if dev_addr is not None:
                target_address = dev_addr

    async def _handle_event(event: Any) -> None:
        event_data = event.data
        if (
            event_data.get("event") == trigger_type
            and event_data.get("pushbutton") == button_num
        ):
            # If an address is specified or resolved from device, filter on event object
            if target_address is not None:
                event_object = event_data.get("object")
                if event_object is not None and int(event_object) != int(target_address):
                    return

            await action(
                {
                    "trigger": {
                        **trigger_info,
                        "platform": "device",
                        "event": event_data,
                    }
                }
            )

    # Listen to both CEN and CEN+ event streams
    unsub_cen = hass.bus.async_listen("myhome_cen_event", _handle_event)
    unsub_cenplus = hass.bus.async_listen("myhome_cenplus_event", _handle_event)

    def _unsubscribe_all() -> None:
        unsub_cen()
        unsub_cenplus()

    return _unsubscribe_all
