"""Support for common values for MyHome devices."""

from __future__ import annotations

from typing import TYPE_CHECKING

if TYPE_CHECKING:
    from .gateway import MyHOMEGatewayHandler

from homeassistant.helpers.device_registry import DeviceInfo
from homeassistant.helpers.entity import Entity

from .const import DOMAIN


class MyHOMEEntity(Entity):
    def __init__(
        self,
        hass,
        name: str,
        platform: str,
        device_id: str,
        who: str,
        where: str,
        manufacturer: str,
        model: str,
        gateway: MyHOMEGatewayHandler,
    ):
        self._hass = hass
        self._platform = platform
        self._who = who
        self._where = where
        self._device_id = device_id
        self._attr_unique_id = f"{gateway.mac}-{self._who}-{self._device_id}"
        self._manufacturer = manufacturer or "BTicino S.p.A."
        self._model = model
        self._gateway_handler = gateway
        self._attr_has_entity_name = False
        self._attr_name = name
        self.entity_id = f"{platform.lower()}.{name.lower().replace(' ', '_')}"

        self._attr_entity_registry_enabled_default = True
        self._attr_should_poll = False

        self._attr_device_info = DeviceInfo(
            identifiers={(DOMAIN, f"{gateway.mac}-{self._who}-{self._device_id}")},
            name=self._attr_name,
            manufacturer=self._manufacturer,
            model=self._model,
        )
        if "via_device_id" in DeviceInfo.__annotations__:
            self._attr_device_info["via_device_id"] = gateway.device_registry_id
        else:
            self._attr_device_info["via_device"] = (DOMAIN, gateway.unique_id)

    @property
    def via_device_id(self) -> str:
        """Return gateway unique ID associated with this device."""
        return self._gateway_handler.unique_id

    async def async_added_to_hass(self):
        """When entity is added to hass."""
        await self.async_update()

    async def async_will_remove_from_hass(self):
        """When entity is removed from hass."""
        pass
