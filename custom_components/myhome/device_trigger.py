"""Provides device triggers for MyHOME CEN / CEN+ buttons."""
from __future__ import annotations

from typing import Any
import voluptuous as vol

from homeassistant.components.device_automation import DEVICE_TRIGGER_BASE_SCHEMA
from homeassistant.components.homeassistant.triggers import event as event_trigger
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
    CONF_SHORT_PRESS,
    CONF_SHORT_RELEASE,
    DOMAIN,
)

CONF_SUBTYPE = "subtype"

TRIGGER_TYPES = {
    CONF_SHORT_PRESS,
    CONF_SHORT_RELEASE,
    CONF_LONG_PRESS,
    CONF_LONG_RELEASE,
}

TRIGGER_SUBTYPES = [f"button_{i}" for i in range(1, 10)]

TRIGGER_SCHEMA = DEVICE_TRIGGER_BASE_SCHEMA.extend(
    {
        vol.Required(CONF_TYPE): vol.In(TRIGGER_TYPES),
        vol.Required(CONF_SUBTYPE): vol.In(TRIGGER_SUBTYPES),
    }
)


async def async_get_triggers(
    hass: HomeAssistant, device_id: str
) -> list[dict[str, Any]]:
    """List device triggers for MyHOME CEN/CEN+ devices."""
    device_registry = dr.async_get(hass)
    device = device_registry.async_get(device_id)

    if device is None:
        return []

    # Verify that this device belongs to the MyHOME integration
    is_myhome = any(identifier[0] == DOMAIN for identifier in device.identifiers)
    if not is_myhome:
        return []

    triggers = []
    for trigger_type in TRIGGER_TYPES:
        for subtype in TRIGGER_SUBTYPES:
            triggers.append(
                {
                    CONF_PLATFORM: "device",
                    CONF_DEVICE_ID: device_id,
                    CONF_DOMAIN: DOMAIN,
                    CONF_TYPE: trigger_type,
                    CONF_SUBTYPE: subtype,
                }
            )

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

    async def _handle_event(event: Any) -> None:
        event_data = event.data
        if (
            event_data.get("event") == trigger_type
            and event_data.get("pushbutton") == button_num
        ):
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
