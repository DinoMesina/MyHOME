"""Tests for the MyHOME cover component."""
import asyncio
import pytest
from unittest.mock import AsyncMock, MagicMock, patch

from homeassistant.const import (
    CONF_NAME,
)
from homeassistant.core import HomeAssistant
from homeassistant.components.cover import (
    CoverDeviceClass,
    CoverEntityFeature,
    ATTR_POSITION,
)
from homeassistant.helpers.dispatcher import async_dispatcher_send

from custom_components.myhome.const import (
    DOMAIN,
    CONF_PLATFORMS,
    CONF_ENTITIES,
    CONF_WHERE,
    CONF_WHO,
    CONF_BUS_INTERFACE,
    CONF_ENTITY_NAME,
    CONF_MANUFACTURER,
    CONF_DEVICE_MODEL,
    CONF_ADVANCED_SHUTTER,
)
from custom_components.myhome.cover import (
    MyHOMECover,
    PLATFORM,
    async_setup_entry,
    async_unload_entry,
)
from custom_components.myhome.ownd.message import (
    OWNAutomationEvent,
    OWNAutomationCommand,
    OWNEvent,
)


@pytest.fixture
def mock_gateway():
    gw = MagicMock()
    gw.mac = "00:03:50:00:12:34"
    gw.unique_id = "00:03:50:00:12:34"
    gw.log_id = "[Test Gateway]"
    gw.send = AsyncMock()
    gw.send_status_request = AsyncMock()
    return gw


async def test_cover_setup_restores_and_discovers(hass: HomeAssistant, mock_gateway):
    """Test cover platform setup restoring from registry and discovering new devices."""
    mac = mock_gateway.mac
    hass.data = {
        DOMAIN: {
            mac: {
                "entity": mock_gateway,
                CONF_PLATFORMS: {
                    PLATFORM: {
                        "33": {
                            CONF_WHERE: "33",
                            CONF_NAME: "Configured Cover 33",
                            CONF_ADVANCED_SHUTTER: True,
                        },
                        "33_dup": {
                            CONF_WHERE: "33",
                            CONF_NAME: "Configured Cover 33 Duplicate",
                        },
                        "34#4#02": {
                            CONF_WHERE: "34",
                            CONF_BUS_INTERFACE: "02",
                            CONF_NAME: "Interface Cover 34",
                        },
                    }
                },
            }
        }
    }

    config_entry = MagicMock()
    config_entry.data = {"mac": mac}
    config_entry.entry_id = "test_entry"

    # Mock entity registry restore check
    mock_er = MagicMock()
    reg_1 = MagicMock()
    reg_1.domain = PLATFORM
    reg_1.unique_id = f"{mac}-2-21"

    reg_2 = MagicMock()
    reg_2.domain = PLATFORM
    reg_2.unique_id = f"{mac}-2-22#4#01"

    with patch("homeassistant.helpers.entity_registry.async_get", return_value=mock_er), \
         patch("homeassistant.helpers.entity_registry.async_entries_for_config_entry", return_value=[reg_1, reg_2]):
        
        added_entities = []

        def fake_add_entities(entities):
            added_entities.extend(entities)

        await async_setup_entry(hass, config_entry, fake_add_entities)

        # Restored (21, 22#4#01) + Configured from YAML (33, 34#4#02) = 4 covers
        assert len(added_entities) == 4

        # Test discovering a new cover via message dispatcher
        new_cover_msg = OWNEvent.parse("*2*1*41##")
        async_dispatcher_send(hass, f"myhome_message_{mac}", new_cover_msg)
        assert len(added_entities) == 5

        # Test discovering cover with interface
        new_iface_msg = OWNEvent.parse("*2*1*42#4#02##")
        async_dispatcher_send(hass, f"myhome_message_{mac}", new_iface_msg)
        assert len(added_entities) == 6

        # Sending message for existing cover triggers update signal rather than creating duplicate
        async_dispatcher_send(hass, f"myhome_message_{mac}", new_cover_msg)
        assert len(added_entities) == 6

        # Skip messages for group, area, general, or without where
        async_dispatcher_send(hass, f"myhome_message_{mac}", OWNEvent.parse("*2*1*#1##"))
        async_dispatcher_send(hass, f"myhome_message_{mac}", OWNEvent.parse("*2*1*1##")) # area 1
        async_dispatcher_send(hass, f"myhome_message_{mac}", OWNEvent.parse("*2*1*0##")) # general
        bad_msg = OWNEvent.parse("*2*1*21##")
        bad_msg._where = None
        async_dispatcher_send(hass, f"myhome_message_{mac}", bad_msg)
        assert len(added_entities) == 6

        # Unload
        assert await async_unload_entry(hass, config_entry) is True


class TestMyHOMECoverEntity:
    """Test MyHOMECover entity methods and features."""

    @pytest.fixture
    def basic_cover(self, hass, mock_gateway):
        with patch("custom_components.myhome.myhome_device.Entity.__init__", return_value=None):
            cover = MyHOMECover(
                hass=hass,
                name="Basic Shutter",
                entity_name="Basic Shutter",
                device_id="21",
                who="2",
                where="21",
                interface=None,
                advanced=False,
                manufacturer="BTicino",
                model="Shutter",
                gateway=mock_gateway,
            )
            cover.hass = hass
            cover.async_schedule_update_ha_state = MagicMock()
            return cover

    @pytest.fixture
    def advanced_cover(self, hass, mock_gateway):
        with patch("custom_components.myhome.myhome_device.Entity.__init__", return_value=None):
            cover = MyHOMECover(
                hass=hass,
                name="Advanced Shutter",
                entity_name="Advanced Shutter",
                device_id="22#4#02",
                who="2",
                where="22",
                interface="02",
                advanced=True,
                manufacturer="BTicino",
                model="Advanced Shutter",
                gateway=mock_gateway,
            )
            cover.hass = hass
            cover.async_schedule_update_ha_state = MagicMock()
            return cover

    def test_cover_attributes(self, basic_cover, advanced_cover):
        assert basic_cover.device_class == CoverDeviceClass.SHUTTER
        assert basic_cover.supported_features == (
            CoverEntityFeature.OPEN
            | CoverEntityFeature.CLOSE
            | CoverEntityFeature.STOP
            | CoverEntityFeature.SET_POSITION
        )
        assert basic_cover.extra_state_attributes["A"] == "2"
        assert basic_cover.extra_state_attributes["PL"] == "1"
        assert basic_cover.extra_state_attributes["travel_time"] == 25
        assert "Int" not in basic_cover.extra_state_attributes

        assert advanced_cover.supported_features == (
            CoverEntityFeature.OPEN
            | CoverEntityFeature.CLOSE
            | CoverEntityFeature.STOP
            | CoverEntityFeature.SET_POSITION
        )
        assert advanced_cover.extra_state_attributes["Int"] == "02"

        # When current_cover_position is None, is_closed falls back to _attr_is_closed
        basic_cover._attr_current_cover_position = None
        basic_cover._attr_is_closed = True
        assert basic_cover.is_closed is True

    async def test_async_lifecycle_and_update(self, basic_cover, hass):
        basic_cover.async_on_remove = MagicMock()
        await basic_cover.async_added_to_hass()
        basic_cover.async_on_remove.assert_called_once()

        await basic_cover.async_update()
        basic_cover._gateway_handler.send_status_request.assert_awaited_once()

    async def test_cover_commands(self, basic_cover, advanced_cover):
        await basic_cover.async_open_cover()
        basic_cover._gateway_handler.send.assert_awaited()

        basic_cover._gateway_handler.send.reset_mock()
        await basic_cover.async_close_cover()
        basic_cover._gateway_handler.send.assert_awaited()

        basic_cover._gateway_handler.send.reset_mock()
        await basic_cover.async_stop_cover()
        basic_cover._gateway_handler.send.assert_awaited()

        # Set position
        advanced_cover._gateway_handler.send.reset_mock()
        await advanced_cover.async_set_cover_position(**{ATTR_POSITION: 45})
        advanced_cover._gateway_handler.send.assert_awaited()

        # Set position without ATTR_POSITION kwarg
        advanced_cover._gateway_handler.send.reset_mock()
        await advanced_cover.async_set_cover_position()
        advanced_cover._gateway_handler.send.assert_not_called()

        # Virtual travel time positioning for basic cover
        basic_cover._gateway_handler.send.reset_mock()
        basic_cover._attr_current_cover_position = 50
        # Set to 50 (same) -> no-op
        await basic_cover.async_set_cover_position(**{ATTR_POSITION: 50})
        basic_cover._gateway_handler.send.assert_not_called()

        # Set to 80 (open)
        with patch("asyncio.sleep", new_callable=AsyncMock) as mock_sleep:
            await basic_cover.async_set_cover_position(**{ATTR_POSITION: 80})
            assert basic_cover.is_opening is True
            assert basic_cover._stop_task is not None
            # Await the stop task
            await basic_cover._stop_task
            assert basic_cover.is_opening is False

        # Set to 20 (close)
        with patch("asyncio.sleep", new_callable=AsyncMock) as mock_sleep:
            await basic_cover.async_set_cover_position(**{ATTR_POSITION: 20})
            assert basic_cover.is_closing is True
            assert basic_cover._stop_task is not None
            await basic_cover._stop_task
            assert basic_cover.is_closing is False

        # Test active stop task cancellation
        await basic_cover.async_set_cover_position(**{ATTR_POSITION: 80})
        task = basic_cover._stop_task
        assert task is not None
        await asyncio.sleep(0)
        basic_cover._cancel_stop_task()
        assert basic_cover._stop_task is None
        await asyncio.sleep(0)

        # Unload / remove from hass cleans up tasks
        await basic_cover.async_will_remove_from_hass()
        assert basic_cover._stop_task is None

    def test_handle_event(self, basic_cover):
        # Opening event
        msg_opening = OWNEvent.parse("*2*1*21##")
        basic_cover.handle_event(msg_opening)
        assert basic_cover.is_opening is True
        assert basic_cover.is_closing is False

        # Moving position interpolation
        with patch("time.monotonic", return_value=basic_cover._move_start_time + 12.5):
            # After 12.5s out of 25s full travel time from 50%, position should advance ~50%
            pos = basic_cover.current_cover_position
            assert pos >= 90

        # Stop event
        msg_stop = OWNEvent.parse("*2*0*21##")
        basic_cover.handle_event(msg_stop)
        assert basic_cover.is_opening is False
        assert basic_cover.is_closing is False

        # Closing event
        msg_closing = OWNEvent.parse("*2*2*21##")
        basic_cover.handle_event(msg_closing)
        assert basic_cover.is_opening is False
        assert basic_cover.is_closing is True

        # Moving closing interpolation
        with patch("time.monotonic", return_value=basic_cover._move_start_time + 12.5):
            pos = basic_cover.current_cover_position
            assert pos <= 60

        basic_cover.handle_event(msg_stop)
        assert basic_cover.is_closing is False

        # Position event
        msg_pos = OWNEvent.parse("*#2*21*10*10*0*0*0##")
        basic_cover.handle_event(msg_pos)
        assert basic_cover.is_closed is True
        assert basic_cover.current_cover_position == 0

        # Position event without is_closed
        msg_pos_no_closed = MagicMock(spec=OWNAutomationEvent)
        msg_pos_no_closed.current_position = 0
        msg_pos_no_closed.is_closed = None
        msg_pos_no_closed.human_readable_log = "Pos no closed"
        basic_cover.handle_event(msg_pos_no_closed)
        assert basic_cover.is_closed is True

        # Stop event with is_closed reported
        msg_stopped_with_closed = MagicMock(spec=OWNAutomationEvent)
        msg_stopped_with_closed.current_position = None
        msg_stopped_with_closed.is_opening = False
        msg_stopped_with_closed.is_closing = False
        msg_stopped_with_closed.is_closed = True
        msg_stopped_with_closed.human_readable_log = "Stopped with closed"
        basic_cover.handle_event(msg_stopped_with_closed)
        assert basic_cover.is_closed is True
