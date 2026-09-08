"""Tests for MyHOME WebSocket API commands."""
import pytest
from unittest.mock import AsyncMock, MagicMock, patch

from homeassistant.components import websocket_api
from homeassistant.core import HomeAssistant

from custom_components.myhome.bus_monitor import BusFrame, BusMonitor
from custom_components.myhome.const import CONF_ENTITY, DOMAIN
from custom_components.myhome.ownd.message import OWNEvent, OWNMessage
from custom_components.myhome.websocket import (
    _get_gateway_and_monitor,
    _matches_filter,
    async_setup_websocket_api,
    ws_bus_monitor_clear,
    ws_bus_monitor_history,
    ws_bus_monitor_send,
    ws_bus_monitor_stream,
)


@pytest.fixture
def mock_ws_connection():
    """Create a mock active WebSocket connection."""
    conn = MagicMock(spec=websocket_api.ActiveConnection)
    conn.send_result = MagicMock()
    conn.send_error = MagicMock()
    conn.send_message = MagicMock()
    conn.subscriptions = {}
    return conn


async def test_websocket_registration_idempotent(hass: HomeAssistant):
    """Test that async_setup_websocket_api can be called multiple times safely."""
    async_setup_websocket_api(hass)
    assert hass.data[DOMAIN]["_ws_registered"] is True

    # Second call should be a no-op
    with patch("homeassistant.components.websocket_api.async_register_command") as mock_reg:
        async_setup_websocket_api(hass)
        mock_reg.assert_not_called()


async def test_ws_history_no_gateway(hass: HomeAssistant, mock_ws_connection):
    """Test history request returns ERR_NOT_FOUND when no gateway is configured."""
    hass.data[DOMAIN] = {}
    ws_bus_monitor_history(hass, mock_ws_connection, {"id": 1, "type": "myhome/bus_monitor/history"})
    await hass.async_block_till_done()
    mock_ws_connection.send_error.assert_called_once_with(
        1, websocket_api.ERR_NOT_FOUND, "No active MyHOME gateway or bus monitor found"
    )


async def test_ws_history_with_frames_and_filters(hass: HomeAssistant, mock_ws_connection):
    """Test history request returns frames filtered by who, where, and direction."""
    monitor = BusMonitor(maxlen=100)
    gateway = MagicMock()
    mac = "00:03:50:00:12:34"
    hass.data[DOMAIN] = {
        mac: {
            CONF_ENTITY: gateway,
            "bus_monitor": monitor,
        }
    }

    # Record some frames
    ev1 = OWNEvent.parse("*1*1*12##")
    ev2 = OWNEvent.parse("*2*1*25##")
    ev3 = OWNEvent.parse("*1*0*12##")

    monitor.record_frame("rx", "*1*1*12##", ev1)
    monitor.record_frame("tx", "*2*1*25##", ev2)
    monitor.record_frame("rx", "*1*0*12##", ev3)

    # 1. Unfiltered request with limit
    ws_bus_monitor_history(
        hass,
        mock_ws_connection,
        {"id": 2, "type": "myhome/bus_monitor/history", "limit": 2},
    )
    await hass.async_block_till_done()
    mock_ws_connection.send_result.assert_called_once()
    msg_id, result = mock_ws_connection.send_result.call_args[0]
    assert msg_id == 2
    assert len(result["frames"]) == 2
    assert result["stats"]["captured"] == 3

    # 2. Filter by WHO=1 and where=12
    mock_ws_connection.send_result.reset_mock()
    ws_bus_monitor_history(
        hass,
        mock_ws_connection,
        {"id": 3, "type": "myhome/bus_monitor/history", "who": "1", "where": "12", "direction": "rx"},
    )
    await hass.async_block_till_done()
    _, result = mock_ws_connection.send_result.call_args[0]
    assert len(result["frames"]) == 2
    assert all(f["who"] == "1" and f["where"] == "12" and f["direction"] == "rx" for f in result["frames"])


async def test_ws_stream_subscription_and_dispatch(hass: HomeAssistant, mock_ws_connection):
    """Test real-time bus stream subscription, frame dispatching, and filtering."""
    monitor = BusMonitor(maxlen=50)
    gateway = MagicMock()
    mac = "00:03:50:00:12:34"
    hass.data[DOMAIN] = {
        mac: {
            CONF_ENTITY: gateway,
            "bus_monitor": monitor,
        }
    }

    # Subscribe with filter: who=1
    ws_bus_monitor_stream(
        hass,
        mock_ws_connection,
        {"id": 10, "type": "myhome/bus_monitor/stream", "who": 1, "direction": "rx"},
    )
    await hass.async_block_till_done()
    mock_ws_connection.send_result.assert_called_once_with(10)
    assert 10 in mock_ws_connection.subscriptions

    # Record matching frame
    ev1 = OWNEvent.parse("*1*1*14##")
    monitor.record_frame("rx", "*1*1*14##", ev1)

    mock_ws_connection.send_message.assert_called_once()
    sent = mock_ws_connection.send_message.call_args[0][0]
    assert sent["id"] == 10
    assert sent["type"] == "event"
    assert sent["event"]["raw"] == "*1*1*14##"

    # Record non-matching frame (who=2, automation)
    mock_ws_connection.send_message.reset_mock()
    ev2 = OWNEvent.parse("*2*1*21##")
    monitor.record_frame("rx", "*2*1*21##", ev2)
    mock_ws_connection.send_message.assert_not_called()

    # Unsubscribe
    unsub = mock_ws_connection.subscriptions[10]
    unsub()
    assert len(monitor._subscribers) == 0


async def test_ws_stream_no_gateway(hass: HomeAssistant, mock_ws_connection):
    """Test stream subscription returns error when no gateway is configured."""
    hass.data[DOMAIN] = {}
    ws_bus_monitor_stream(hass, mock_ws_connection, {"id": 11, "type": "myhome/bus_monitor/stream"})
    await hass.async_block_till_done()
    mock_ws_connection.send_error.assert_called_once_with(
        11, websocket_api.ERR_NOT_FOUND, "No active MyHOME gateway or bus monitor found"
    )


async def test_ws_send_frame(hass: HomeAssistant, mock_ws_connection):
    """Test transmitting an OpenWebNet frame via the WebSocket API."""
    gateway = MagicMock()
    gateway.send = AsyncMock()
    hass.data[DOMAIN] = {
        "00:03:50:00:12:34": {
            CONF_ENTITY: gateway,
        }
    }

    # 1. Successful frame send
    ws_bus_monitor_send(
        hass,
        mock_ws_connection,
        {"id": 20, "type": "myhome/bus_monitor/send", "frame": "*1*1*12##"},
    )
    await hass.async_block_till_done()
    mock_ws_connection.send_result.assert_called_once_with(
        20, {"success": True, "frame": "*1*1*12##"}
    )
    gateway.send.assert_awaited_once()

    # 2. Invalid frame format
    mock_ws_connection.send_error.reset_mock()
    ws_bus_monitor_send(
        hass,
        mock_ws_connection,
        {"id": 21, "type": "myhome/bus_monitor/send", "frame": "invalid_frame"},
    )
    await hass.async_block_till_done()
    mock_ws_connection.send_error.assert_called_once_with(
        21, websocket_api.ERR_INVALID_FORMAT, "Invalid OpenWebNet frame format: invalid_frame"
    )

    # 3. Gateway send error
    gateway.send.side_effect = ConnectionError("Gateway disconnected")
    mock_ws_connection.send_error.reset_mock()
    ws_bus_monitor_send(
        hass,
        mock_ws_connection,
        {"id": 22, "type": "myhome/bus_monitor/send", "frame": "*1*0*12##"},
    )
    await hass.async_block_till_done()
    mock_ws_connection.send_error.assert_called_once_with(
        22, websocket_api.ERR_UNKNOWN_ERROR, "Failed to transmit frame: Gateway disconnected"
    )

    # 4. Frame parse fallback to raw OWNMessage
    gateway.send.side_effect = None
    mock_ws_connection.send_result.reset_mock()
    with patch("custom_components.myhome.websocket.OWNMessage.parse", return_value=None):
        ws_bus_monitor_send(
            hass,
            mock_ws_connection,
            {"id": 24, "type": "myhome/bus_monitor/send", "frame": "*999*999*999##"},
        )
        await hass.async_block_till_done()
        mock_ws_connection.send_result.assert_called_once_with(
            24, {"success": True, "frame": "*999*999*999##"}
        )


async def test_ws_send_no_gateway(hass: HomeAssistant, mock_ws_connection):
    """Test send returns error when no gateway is configured."""
    hass.data[DOMAIN] = {}
    ws_bus_monitor_send(hass, mock_ws_connection, {"id": 23, "type": "myhome/bus_monitor/send", "frame": "*1*1*12##"})
    await hass.async_block_till_done()
    mock_ws_connection.send_error.assert_called_once_with(
        23, websocket_api.ERR_NOT_FOUND, "No active MyHOME gateway found to transmit frame"
    )


async def test_ws_clear_buffer(hass: HomeAssistant, mock_ws_connection):
    """Test clearing the bus monitor ring buffer."""
    monitor = BusMonitor(maxlen=50)
    monitor.record_frame("rx", "*1*1*12##")
    assert monitor.get_stats()["captured"] == 1

    hass.data[DOMAIN] = {
        "00:03:50:00:12:34": {
            CONF_ENTITY: MagicMock(),
            "bus_monitor": monitor,
        }
    }

    ws_bus_monitor_clear(hass, mock_ws_connection, {"id": 30, "type": "myhome/bus_monitor/clear"})
    await hass.async_block_till_done()
    mock_ws_connection.send_result.assert_called_once_with(30, {"success": True})
    assert monitor.get_stats()["captured"] == 0

    # Test error when no gateway
    hass.data[DOMAIN] = {}
    mock_ws_connection.send_error.reset_mock()
    ws_bus_monitor_clear(hass, mock_ws_connection, {"id": 31, "type": "myhome/bus_monitor/clear"})
    await hass.async_block_till_done()
    mock_ws_connection.send_error.assert_called_once_with(
        31, websocket_api.ERR_NOT_FOUND, "No active MyHOME gateway or bus monitor found"
    )


def test_get_gateway_and_monitor_edge_cases(hass: HomeAssistant):
    """Test _get_gateway_and_monitor with MAC lookups and non-dict domain data."""
    # 1. Non-dict domain data
    hass.data[DOMAIN] = "not_a_dict"
    gw, bm = _get_gateway_and_monitor(hass)
    assert gw is None and bm is None

    # 2. Lookup with unformatted MAC
    mock_gw = MagicMock()
    mock_bm = MagicMock()
    hass.data[DOMAIN] = {
        "00:03:50:00:12:34": {
            CONF_ENTITY: mock_gw,
            "bus_monitor": mock_bm,
        }
    }
    gw, bm = _get_gateway_and_monitor(hass, mac="000350001234")
    assert gw is mock_gw
    assert bm is mock_bm

    # 3. Format MAC exception branch
    with patch("homeassistant.helpers.device_registry.format_mac", side_effect=ValueError("Bad MAC")):
        gw, bm = _get_gateway_and_monitor(hass, mac="00:03:50:00:12:34")
        assert gw is mock_gw
        assert bm is mock_bm

    # 4. Lookup when no gateway in domain data
    hass.data[DOMAIN] = {}
    gw, bm = _get_gateway_and_monitor(hass, mac="invalid_mac")
    assert gw is None and bm is None


def test_matches_filter_helpers():
    """Test _matches_filter logic covering all branches."""
    frame = BusFrame(direction="rx", raw="*1*1*12##", parsed=OWNEvent.parse("*1*1*12##"))
    assert _matches_filter(frame, who="1", where="12", direction="rx") is True
    assert _matches_filter(frame, who="2") is False
    assert _matches_filter(frame, where="99") is False
    assert _matches_filter(frame, direction="tx") is False
    assert _matches_filter(frame, direction="all") is True

    frame_dict = frame.to_dict()
    assert _matches_filter(frame_dict, who=1, where="12", direction="rx") is True
    assert _matches_filter(frame_dict, who=4) is False
