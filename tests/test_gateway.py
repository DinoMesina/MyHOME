import pytest
import asyncio
from unittest.mock import MagicMock, patch, AsyncMock
from homeassistant.core import HomeAssistant

from custom_components.myhome.gateway import MyHOMEGatewayHandler
from custom_components.myhome.const import (
    DOMAIN,
    CONF_SHORT_PRESS,
    CONF_SHORT_RELEASE,
    CONF_LONG_PRESS,
    CONF_LONG_RELEASE,
    CONF_SSDP_LOCATION,
    CONF_SSDP_ST,
    CONF_DEVICE_TYPE,
    CONF_MANUFACTURER,
    CONF_MANUFACTURER_URL,
    CONF_FIRMWARE,
    CONF_UDN,
)
from homeassistant.const import (
    CONF_HOST,
    CONF_PORT,
    CONF_PASSWORD,
    CONF_NAME,
    CONF_MAC,
    CONF_FRIENDLY_NAME,
)
from custom_components.myhome.ownd.message import (
    OWNLightingEvent,
    OWNLightingCommand,
    OWNAutomationEvent,
    OWNHeatingCommand,
    OWNCENPlusEvent,
    OWNCENEvent,
    OWNGatewayEvent,
    OWNGatewayCommand,
    OWNMessage,
    OWNCommand,
)


@pytest.fixture
def mock_config_entry():
    entry = MagicMock()
    entry.data = {
        CONF_HOST: "192.168.1.5",
        CONF_PORT: 20000,
        CONF_PASSWORD: "open",
        CONF_SSDP_LOCATION: "",
        CONF_SSDP_ST: "",
        CONF_DEVICE_TYPE: "Gateway",
        CONF_FRIENDLY_NAME: "GW",
        CONF_MANUFACTURER: "Bticino",
        CONF_MANUFACTURER_URL: "",
        CONF_NAME: "MYHOME",
        CONF_FIRMWARE: "1.0",
        CONF_MAC: "00:11:22:33:44:55",
        CONF_UDN: "1234",
    }
    return entry


@pytest.fixture
def gateway_handler(mock_config_entry):
    mock_hass = MagicMock()
    mock_hass.data = {}
    handler = MyHOMEGatewayHandler(mock_hass, mock_config_entry)
    return handler


def test_gateway_properties(gateway_handler, mock_config_entry):
    assert gateway_handler.mac == "00:11:22:33:44:55"
    assert gateway_handler.unique_id == "00:11:22:33:44:55"
    assert gateway_handler.log_id == "[MYHOME gateway - 192.168.1.5]"
    assert gateway_handler.manufacturer == "Bticino"
    assert gateway_handler.name == "MYHOME Gateway"
    assert gateway_handler.model == "MYHOME"
    assert gateway_handler.firmware == "1.0"
    assert gateway_handler.profile is not None

    # Test mac fallback when serial is empty
    mock_config_entry.data[CONF_MAC] = ""
    handler_no_mac = MyHOMEGatewayHandler(gateway_handler.hass, mock_config_entry)
    assert handler_no_mac.mac == ""

    # Test mac fallback when dr.format_mac returns None
    with patch("custom_components.myhome.gateway.dr.format_mac", return_value=None):
        assert gateway_handler.mac == "00:11:22:33:44:55"


@pytest.mark.asyncio
async def test_gateway_test_connection(gateway_handler):
    with patch("custom_components.myhome.gateway.OWNSession") as mock_session_cls:
        mock_session = MagicMock()
        mock_session.test_connection = AsyncMock(return_value={"Success": True})
        mock_session_cls.return_value = mock_session

        res = await gateway_handler.test()
        assert res == {"Success": True}
        mock_session.test_connection.assert_called_once()


@pytest.mark.asyncio
async def test_gateway_send_and_send_status_request(gateway_handler):
    cmd = MagicMock(spec=OWNCommand)
    await gateway_handler.send(cmd)
    item = await gateway_handler.send_buffer.get()
    assert item["message"] == cmd
    assert item["is_status_request"] is False

    await gateway_handler.send_status_request(cmd)
    item_status = await gateway_handler.send_buffer.get()
    assert item_status["message"] == cmd
    assert item_status["is_status_request"] is True


@pytest.mark.asyncio
async def test_gateway_close_listener(gateway_handler):
    gateway_handler.sending_workers = [MagicMock(), MagicMock()]
    res = await gateway_handler.close_listener()
    assert res is True
    assert gateway_handler._terminate_sender is True
    assert gateway_handler._terminate_listener is True

    # Queue full handling
    with patch.object(gateway_handler.send_buffer, "put_nowait", side_effect=asyncio.QueueFull):
        res2 = await gateway_handler.close_listener()
        assert res2 is True


@pytest.mark.asyncio
async def test_listening_loop_lighting(gateway_handler):
    with patch("custom_components.myhome.gateway.OWNEventSession") as mock_session_class:
        mock_session = MagicMock()
        mock_session.connect = AsyncMock(return_value={"Success": True})
        mock_session.get_next = AsyncMock()

        msg_gen = MagicMock(spec=OWNLightingEvent)
        msg_gen.is_translation = False
        msg_gen.is_general = True
        msg_gen.is_on = True
        msg_gen.human_readable_log = "L Gen"

        msg_area = MagicMock(spec=OWNLightingEvent)
        msg_area.is_translation = False
        msg_area.is_general = False
        msg_area.is_area = True
        msg_area.is_on = False
        msg_area.area = "1"
        msg_area.human_readable_log = "L Area"

        msg_group = MagicMock(spec=OWNLightingEvent)
        msg_group.is_translation = False
        msg_group.is_general = False
        msg_group.is_area = False
        msg_group.is_group = True
        msg_group.is_on = True
        msg_group.group = "5"
        msg_group.human_readable_log = "L Grp"

        mock_session.get_next.side_effect = [
            msg_gen,
            msg_area,
            msg_group,
            asyncio.CancelledError(),
        ]
        mock_session_class.return_value = mock_session

        gateway_handler.send_status_request = AsyncMock()

        try:
            await gateway_handler.listening_loop()
        except asyncio.CancelledError:
            pass

        assert gateway_handler.hass.bus.async_fire.call_count >= 3
        gateway_handler.hass.bus.async_fire.assert_any_call("myhome_general_light_event", {"message": str(msg_gen), "event": "on"})
        gateway_handler.hass.bus.async_fire.assert_any_call("myhome_area_light_event", {"message": str(msg_area), "area": "1", "event": "off"})
        gateway_handler.hass.bus.async_fire.assert_any_call("myhome_group_light_event", {"message": str(msg_group), "group": "5", "event": "on"})


@pytest.mark.asyncio
async def test_listening_loop_automation(gateway_handler):
    with patch("custom_components.myhome.gateway.OWNEventSession") as mock_session_class:
        mock_session = MagicMock()
        mock_session.connect = AsyncMock(return_value={"Success": True})
        mock_session.get_next = AsyncMock()

        msg_gen = MagicMock(spec=OWNAutomationEvent)
        msg_gen.is_translation = False
        msg_gen.is_general = True
        msg_gen.is_opening = True
        msg_gen.is_closing = False
        msg_gen.human_readable_log = "A Gen"

        msg_area = MagicMock(spec=OWNAutomationEvent)
        msg_area.is_translation = False
        msg_area.is_general = False
        msg_area.is_area = True
        msg_area.is_opening = False
        msg_area.is_closing = True
        msg_area.area = "2"
        msg_area.human_readable_log = "A Area"

        msg_group = MagicMock(spec=OWNAutomationEvent)
        msg_group.is_translation = False
        msg_group.is_general = False
        msg_group.is_area = False
        msg_group.is_group = True
        msg_group.is_opening = False
        msg_group.is_closing = False
        msg_group.group = "6"
        msg_group.human_readable_log = "A Grp"

        mock_session.get_next.side_effect = [
            msg_gen,
            msg_area,
            msg_group,
            asyncio.CancelledError(),
        ]
        mock_session_class.return_value = mock_session

        gateway_handler.send_status_request = AsyncMock()

        try:
            await gateway_handler.listening_loop()
        except asyncio.CancelledError:
            pass

        gateway_handler.hass.bus.async_fire.assert_any_call("myhome_general_automation_event", {"message": str(msg_gen), "event": "open"})
        gateway_handler.hass.bus.async_fire.assert_any_call("myhome_area_automation_event", {"message": str(msg_area), "area": "2", "event": "close"})
        gateway_handler.hass.bus.async_fire.assert_any_call("myhome_group_automation_event", {"message": str(msg_group), "group": "6", "event": "stop"})


@pytest.mark.asyncio
async def test_listening_loop_automation_remaining_branches(gateway_handler):
    with patch("custom_components.myhome.gateway.OWNEventSession") as mock_session_class:
        mock_session = MagicMock()
        mock_session.connect = AsyncMock(return_value={"Success": True})
        mock_session.get_next = AsyncMock()

        # General close and stop
        msg_gen_close = MagicMock(spec=OWNAutomationEvent)
        msg_gen_close.is_translation = False
        msg_gen_close.is_general = True
        msg_gen_close.is_opening = False
        msg_gen_close.is_closing = True
        msg_gen_close.human_readable_log = "A Gen Close"

        msg_gen_stop = MagicMock(spec=OWNAutomationEvent)
        msg_gen_stop.is_translation = False
        msg_gen_stop.is_general = True
        msg_gen_stop.is_opening = False
        msg_gen_stop.is_closing = False
        msg_gen_stop.human_readable_log = "A Gen Stop"

        # Area open and stop
        msg_area_open = MagicMock(spec=OWNAutomationEvent)
        msg_area_open.is_translation = False
        msg_area_open.is_general = False
        msg_area_open.is_area = True
        msg_area_open.is_opening = True
        msg_area_open.is_closing = False
        msg_area_open.area = "3"
        msg_area_open.human_readable_log = "A Area Open"

        msg_area_stop = MagicMock(spec=OWNAutomationEvent)
        msg_area_stop.is_translation = False
        msg_area_stop.is_general = False
        msg_area_stop.is_area = True
        msg_area_stop.is_opening = False
        msg_area_stop.is_closing = False
        msg_area_stop.area = "3"
        msg_area_stop.human_readable_log = "A Area Stop"

        # Group open and close
        msg_grp_open = MagicMock(spec=OWNAutomationEvent)
        msg_grp_open.is_translation = False
        msg_grp_open.is_general = False
        msg_grp_open.is_area = False
        msg_grp_open.is_group = True
        msg_grp_open.is_opening = True
        msg_grp_open.is_closing = False
        msg_grp_open.group = "7"
        msg_grp_open.human_readable_log = "A Grp Open"

        msg_grp_close = MagicMock(spec=OWNAutomationEvent)
        msg_grp_close.is_translation = False
        msg_grp_close.is_general = False
        msg_grp_close.is_area = False
        msg_grp_close.is_group = True
        msg_grp_close.is_opening = False
        msg_grp_close.is_closing = True
        msg_grp_close.group = "7"
        msg_grp_close.human_readable_log = "A Grp Close"

        mock_session.get_next.side_effect = [
            msg_gen_close,
            msg_gen_stop,
            msg_area_open,
            msg_area_stop,
            msg_grp_open,
            msg_grp_close,
            asyncio.CancelledError(),
        ]
        mock_session_class.return_value = mock_session
        gateway_handler.send_status_request = AsyncMock()

        try:
            await gateway_handler.listening_loop()
        except asyncio.CancelledError:
            pass

        gateway_handler.hass.bus.async_fire.assert_any_call("myhome_general_automation_event", {"message": str(msg_gen_close), "event": "close"})
        gateway_handler.hass.bus.async_fire.assert_any_call("myhome_general_automation_event", {"message": str(msg_gen_stop), "event": "stop"})
        gateway_handler.hass.bus.async_fire.assert_any_call("myhome_area_automation_event", {"message": str(msg_area_open), "area": "3", "event": "open"})
        gateway_handler.hass.bus.async_fire.assert_any_call("myhome_area_automation_event", {"message": str(msg_area_stop), "area": "3", "event": "stop"})
        gateway_handler.hass.bus.async_fire.assert_any_call("myhome_group_automation_event", {"message": str(msg_grp_open), "group": "7", "event": "open"})
        gateway_handler.hass.bus.async_fire.assert_any_call("myhome_group_automation_event", {"message": str(msg_grp_close), "group": "7", "event": "close"})


@pytest.mark.asyncio
async def test_listening_loop_other_events(gateway_handler):
    with patch("custom_components.myhome.gateway.OWNEventSession") as mock_session_class:
        mock_session = MagicMock()
        mock_session.connect = AsyncMock(return_value={"Success": True})
        mock_session.get_next = AsyncMock()

        msg_heat = MagicMock(spec=OWNHeatingCommand)
        msg_heat.dimension = 14
        msg_heat.where = "#4"

        msg_heat2 = MagicMock(spec=OWNHeatingCommand)
        msg_heat2.dimension = 14
        msg_heat2.where = "5"

        msg_cenplus = MagicMock(spec=OWNCENPlusEvent)
        msg_cenplus.is_short_pressed = True
        msg_cenplus.is_short_pressed_and_hold = False
        msg_cenplus.is_held = False
        msg_cenplus.is_still_held = False
        msg_cenplus.is_released = False
        msg_cenplus.object = "1"
        msg_cenplus.push_button = "2"
        msg_cenplus.human_readable_log = "CP"

        msg_cen = MagicMock(spec=OWNCENEvent)
        msg_cen.is_pressed = False
        msg_cen.is_released_after_short_press = False
        msg_cen.is_held = True
        msg_cen.is_released_after_long_press = False
        msg_cen.object = "3"
        msg_cen.push_button = "4"
        msg_cen.human_readable_log = "C"

        mock_session.get_next.side_effect = [
            msg_heat,
            msg_heat2,
            msg_cenplus,
            msg_cen,
            asyncio.CancelledError(),
        ]
        mock_session_class.return_value = mock_session

        gateway_handler.send_status_request = AsyncMock()

        try:
            await gateway_handler.listening_loop()
        except asyncio.CancelledError:
            pass

        gateway_handler.hass.bus.async_fire.assert_any_call("myhome_cenplus_event", {"object": 1, "pushbutton": 2, "event": CONF_SHORT_PRESS})
        gateway_handler.hass.bus.async_fire.assert_any_call("myhome_cen_event", {"object": 3, "pushbutton": 4, "event": CONF_LONG_PRESS})
        assert gateway_handler.send_status_request.call_count >= 2


@pytest.mark.asyncio
async def test_listening_loop_cen_and_cenplus_variants(gateway_handler):
    with patch("custom_components.myhome.gateway.OWNEventSession") as mock_session_class:
        mock_session = MagicMock()
        mock_session.connect = AsyncMock(return_value={"Success": True})
        mock_session.get_next = AsyncMock()

        # CENPlus: held, still_held, released, unmapped
        cp_held = MagicMock(spec=OWNCENPlusEvent, is_short_pressed=False, is_held=True, is_still_held=False, is_released=False, object="1", push_button="1", human_readable_log="cp_held")
        cp_still_held = MagicMock(spec=OWNCENPlusEvent, is_short_pressed=False, is_held=False, is_still_held=True, is_released=False, object="1", push_button="2", human_readable_log="cp_still_held")
        cp_released = MagicMock(spec=OWNCENPlusEvent, is_short_pressed=False, is_held=False, is_still_held=False, is_released=True, object="1", push_button="3", human_readable_log="cp_rel")
        cp_unmapped = MagicMock(spec=OWNCENPlusEvent, is_short_pressed=False, is_held=False, is_still_held=False, is_released=False, object="1", push_button="4", human_readable_log="cp_unm")

        # CEN: pressed, released_after_short, released_after_long, unmapped
        c_pressed = MagicMock(spec=OWNCENEvent, is_pressed=True, is_released_after_short_press=False, is_held=False, is_released_after_long_press=False, object="2", push_button="1", human_readable_log="c_press")
        c_rel_short = MagicMock(spec=OWNCENEvent, is_pressed=False, is_released_after_short_press=True, is_held=False, is_released_after_long_press=False, object="2", push_button="2", human_readable_log="c_rel_short")
        c_rel_long = MagicMock(spec=OWNCENEvent, is_pressed=False, is_released_after_short_press=False, is_held=False, is_released_after_long_press=True, object="2", push_button="3", human_readable_log="c_rel_long")
        c_unmapped = MagicMock(spec=OWNCENEvent, is_pressed=False, is_released_after_short_press=False, is_held=False, is_released_after_long_press=False, object="2", push_button="4", human_readable_log="c_unm")

        mock_session.get_next.side_effect = [
            cp_held,
            cp_still_held,
            cp_released,
            cp_unmapped,
            c_pressed,
            c_rel_short,
            c_rel_long,
            c_unmapped,
            asyncio.CancelledError(),
        ]
        mock_session_class.return_value = mock_session
        gateway_handler.send_status_request = AsyncMock()

        try:
            await gateway_handler.listening_loop()
        except asyncio.CancelledError:
            pass

        gateway_handler.hass.bus.async_fire.assert_any_call("myhome_cenplus_event", {"object": 1, "pushbutton": 1, "event": CONF_LONG_PRESS})
        gateway_handler.hass.bus.async_fire.assert_any_call("myhome_cenplus_event", {"object": 1, "pushbutton": 2, "event": CONF_LONG_PRESS})
        gateway_handler.hass.bus.async_fire.assert_any_call("myhome_cenplus_event", {"object": 1, "pushbutton": 3, "event": CONF_LONG_RELEASE})
        gateway_handler.hass.bus.async_fire.assert_any_call("myhome_cenplus_event", {"object": 1, "pushbutton": 4, "event": None})

        gateway_handler.hass.bus.async_fire.assert_any_call("myhome_cen_event", {"object": 2, "pushbutton": 1, "event": CONF_SHORT_PRESS})
        gateway_handler.hass.bus.async_fire.assert_any_call("myhome_cen_event", {"object": 2, "pushbutton": 2, "event": CONF_SHORT_RELEASE})
        gateway_handler.hass.bus.async_fire.assert_any_call("myhome_cen_event", {"object": 2, "pushbutton": 3, "event": CONF_LONG_RELEASE})
        gateway_handler.hass.bus.async_fire.assert_any_call("myhome_cen_event", {"object": 2, "pushbutton": 4, "event": None})


@pytest.mark.asyncio
async def test_listening_loop_translation_gateway_and_unsupported(gateway_handler):
    with patch("custom_components.myhome.gateway.OWNEventSession") as mock_session_class:
        mock_session = MagicMock()
        mock_session.connect = AsyncMock(return_value={"Success": True})
        mock_session.get_next = AsyncMock()

        # Translation message
        msg_trans = MagicMock(spec=OWNLightingEvent)
        msg_trans.is_translation = True
        msg_trans.human_readable_log = "Trans"

        # Gateway Event
        msg_gw_evt = MagicMock(spec=OWNGatewayEvent)
        msg_gw_evt.human_readable_log = "GW Evt"

        # Gateway Command
        msg_gw_cmd = MagicMock(spec=OWNGatewayCommand)
        msg_gw_cmd.human_readable_log = "GW Cmd"

        # Unsupported OWNMessage
        msg_unsupported = MagicMock(spec=OWNMessage)
        msg_unsupported.human_readable_log = "Unsupported"

        # Non-message raw data
        raw_non_msg = "RAW_BYTES_STRING"

        mock_session.get_next.side_effect = [
            msg_trans,
            msg_gw_evt,
            msg_gw_cmd,
            msg_unsupported,
            raw_non_msg,
            asyncio.CancelledError(),
        ]
        mock_session_class.return_value = mock_session
        gateway_handler.send_status_request = AsyncMock()

        try:
            await gateway_handler.listening_loop()
        except asyncio.CancelledError:
            pass

        assert len(gateway_handler.bus_monitor.get_recent_frames()) >= 4


@pytest.mark.asyncio
async def test_listening_loop_generate_events_and_clean_termination(gateway_handler):
    gateway_handler.generate_events = True
    with patch("custom_components.myhome.gateway.OWNEventSession") as mock_session_class:
        mock_session = MagicMock()
        mock_session.connect = AsyncMock(return_value={"Success": True})
        mock_session.close = AsyncMock()
        mock_session.get_next = AsyncMock()

        msg_own = MagicMock(spec=OWNLightingEvent)
        msg_own.event_content = {"what": "1", "where": "12"}
        msg_own.is_translation = False
        msg_own.is_general = False
        msg_own.is_area = False
        msg_own.is_group = False
        msg_own.human_readable_log = "Msg"

        raw_str = "NON_OWN_MESSAGE"

        def side_effect():
            # Terminate listener after 2 messages
            yield msg_own
            yield raw_str
            gateway_handler._terminate_listener = True
            yield None

        gen = side_effect()
        mock_session.get_next.side_effect = lambda: next(gen)
        mock_session_class.return_value = mock_session
        gateway_handler.send_status_request = AsyncMock()

        await gateway_handler.listening_loop()

        # Both messages dispatched to event bus
        gateway_handler.hass.bus.async_fire.assert_any_call(
            "myhome_message_event",
            {"gateway": "192.168.1.5", "what": "1", "where": "12"},
        )
        gateway_handler.hass.bus.async_fire.assert_any_call(
            "myhome_message_event",
            {"gateway": "192.168.1.5", "message": "NON_OWN_MESSAGE"},
        )
        mock_session.close.assert_called_once()
        assert gateway_handler.is_connected is False


@pytest.mark.asyncio
async def test_listening_loop_auth_failure_lockout_protection(gateway_handler):
    with patch("custom_components.myhome.gateway.OWNEventSession") as mock_session_class:
        mock_session = MagicMock()
        mock_session.connect = AsyncMock(return_value={"Success": False, "Message": "password_error"})
        mock_session_class.return_value = mock_session

        await gateway_handler.listening_loop()
        assert gateway_handler.is_connected is False


@pytest.mark.asyncio
async def test_sending_loop(gateway_handler):
    with patch("custom_components.myhome.gateway.OWNCommandSession") as mock_cmd_class:
        mock_cmd_session = MagicMock()
        mock_cmd_session.connect = AsyncMock(return_value={"Success": True})
        mock_cmd_session.send = AsyncMock()
        mock_cmd_session.close = AsyncMock()
        mock_cmd_class.return_value = mock_cmd_session

        gateway_handler.sending_workers = [MagicMock()]

        mock_queue = MagicMock()
        mock_queue.get = AsyncMock(side_effect=[
            {"message": "msg1", "is_status_request": False},
            {"message": "msg2", "is_status_request": True},
        ])
        gateway_handler.send_buffer = mock_queue

        def mock_send(message, is_status_request):
            if message == "msg2":
                gateway_handler._terminate_sender = True

        mock_cmd_session.send.side_effect = mock_send

        await gateway_handler.sending_loop(0)

        assert mock_cmd_session.send.call_count == 2
        mock_cmd_session.close.assert_called_once()


@pytest.mark.asyncio
async def test_sending_loop_auth_failure_lockout_protection(gateway_handler):
    with patch("custom_components.myhome.gateway.OWNCommandSession") as mock_cmd_class:
        mock_cmd_session = MagicMock()
        mock_cmd_session.connect = AsyncMock(return_value={"Success": False, "Message": "negotiation_refused"})
        mock_cmd_class.return_value = mock_cmd_session

        await gateway_handler.sending_loop(0)
        mock_cmd_session.connect.assert_called_once()


@pytest.mark.asyncio
async def test_sending_loop_collected_responses_and_pacing(gateway_handler):
    with patch("custom_components.myhome.gateway.OWNCommandSession") as mock_cmd_class:
        mock_cmd_session = MagicMock()
        mock_cmd_session.connect = AsyncMock(return_value={"Success": True})
        mock_cmd_session.close = AsyncMock()

        resp_msg = MagicMock(spec=OWNMessage)
        resp_raw = "*#1*0##"
        mock_cmd_session.send = AsyncMock(return_value=[resp_msg, resp_raw])
        mock_cmd_class.return_value = mock_cmd_session

        # Configure gateway profile delay
        gateway_handler.gateway.profile.command_queue_delay = 0.01

        # Queue contains 1 message, then None to terminate
        cmd = MagicMock(spec=OWNCommand)
        await gateway_handler.send_buffer.put({"message": cmd, "is_status_request": False})
        await gateway_handler.send_buffer.put(None)

        with patch("custom_components.myhome.gateway.async_dispatcher_send") as mock_dispatcher:
            await gateway_handler.sending_loop(0)

            mock_cmd_session.send.assert_called_once_with(message=cmd, is_status_request=False)
            mock_dispatcher.assert_called_once_with(
                gateway_handler.hass,
                f"myhome_message_{gateway_handler.mac}",
                resp_msg,
            )
            assert len(gateway_handler.bus_monitor.get_recent_frames()) >= 2
            mock_cmd_session.close.assert_called_once()
