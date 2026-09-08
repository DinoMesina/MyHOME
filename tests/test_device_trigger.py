"""Tests for MyHOME device triggers."""
import pytest
from unittest.mock import AsyncMock, MagicMock

from homeassistant.const import (
    CONF_DEVICE_ID,
    CONF_DOMAIN,
    CONF_PLATFORM,
    CONF_TYPE,
)
from homeassistant.core import HomeAssistant

from custom_components.myhome.const import (
    CONF_LONG_PRESS,
    CONF_SHORT_PRESS,
    DOMAIN,
)
from custom_components.myhome.device_trigger import (
    CONF_SUBTYPE,
    TRIGGER_SUBTYPES,
    TRIGGER_TYPES,
    async_attach_trigger,
    async_get_triggers,
)


@pytest.mark.asyncio
async def test_async_get_triggers_device_not_found(hass: HomeAssistant):
    """Test async_get_triggers returns empty list when device is not found."""
    mock_registry = MagicMock()
    mock_registry.async_get.return_value = None

    with pytest.MonkeyPatch.context() as mp:
        mp.setattr("homeassistant.helpers.device_registry.async_get", lambda h: mock_registry)
        triggers = await async_get_triggers(hass, "non_existent_device_id")
        assert triggers == []


@pytest.mark.asyncio
async def test_async_get_triggers_non_myhome_device(hass: HomeAssistant):
    """Test async_get_triggers returns empty list for devices not from myhome domain."""
    mock_device = MagicMock()
    mock_device.identifiers = {("other_domain", "12345")}
    mock_registry = MagicMock()
    mock_registry.async_get.return_value = mock_device

    with pytest.MonkeyPatch.context() as mp:
        mp.setattr("homeassistant.helpers.device_registry.async_get", lambda h: mock_registry)
        triggers = await async_get_triggers(hass, "other_device_id")
        assert triggers == []


@pytest.mark.asyncio
async def test_async_get_triggers_success(hass: HomeAssistant):
    """Test async_get_triggers returns 36 triggers (4 types x 9 buttons)."""
    mock_device = MagicMock()
    mock_device.identifiers = {(DOMAIN, "00:03:50:aa:bb:cc")}
    mock_registry = MagicMock()
    mock_registry.async_get.return_value = mock_device

    with pytest.MonkeyPatch.context() as mp:
        mp.setattr("homeassistant.helpers.device_registry.async_get", lambda h: mock_registry)
        triggers = await async_get_triggers(hass, "myhome_device_id")

        assert len(triggers) == len(TRIGGER_TYPES) * len(TRIGGER_SUBTYPES)
        first_trigger = triggers[0]
        assert first_trigger[CONF_PLATFORM] == "device"
        assert first_trigger[CONF_DOMAIN] == DOMAIN
        assert first_trigger[CONF_DEVICE_ID] == "myhome_device_id"
        assert first_trigger[CONF_TYPE] in TRIGGER_TYPES
        assert first_trigger[CONF_SUBTYPE] in TRIGGER_SUBTYPES


@pytest.mark.asyncio
async def test_async_attach_trigger_and_dispatch(hass: HomeAssistant):
    """Test attaching a trigger and receiving matched/unmatched events."""
    config = {
        CONF_TYPE: CONF_SHORT_PRESS,
        CONF_SUBTYPE: "button_3",
    }
    action = AsyncMock()
    trigger_info = {"extra_info": 123}

    unsub = await async_attach_trigger(hass, config, action, trigger_info)
    assert callable(unsub)

    # Fire unmatched event (wrong button)
    hass.bus.async_fire("myhome_cen_event", {"event": CONF_SHORT_PRESS, "pushbutton": 2})
    await hass.async_block_till_done()
    action.assert_not_called()

    # Fire unmatched event (wrong event type)
    hass.bus.async_fire("myhome_cen_event", {"event": CONF_LONG_PRESS, "pushbutton": 3})
    await hass.async_block_till_done()
    action.assert_not_called()

    # Fire matched CEN event
    hass.bus.async_fire("myhome_cen_event", {"event": CONF_SHORT_PRESS, "pushbutton": 3})
    await hass.async_block_till_done()
    action.assert_called_once()
    call_arg = action.call_args[0][0]
    assert call_arg["trigger"]["platform"] == "device"
    assert call_arg["trigger"]["extra_info"] == 123
    assert call_arg["trigger"]["event"]["pushbutton"] == 3

    action.reset_mock()

    # Fire matched CEN+ event
    hass.bus.async_fire("myhome_cenplus_event", {"event": CONF_SHORT_PRESS, "pushbutton": 3})
    await hass.async_block_till_done()
    action.assert_called_once()

    # Unsubscribe
    unsub()
    action.reset_mock()

    # Fire event after unsubscribing -> should not be called
    hass.bus.async_fire("myhome_cen_event", {"event": CONF_SHORT_PRESS, "pushbutton": 3})
    await hass.async_block_till_done()
    action.assert_not_called()
