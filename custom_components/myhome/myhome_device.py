"""Support for common values for MyHome devices."""

from __future__ import annotations

from typing import TYPE_CHECKING

if TYPE_CHECKING:
    from .gateway import MyHOMEGatewayHandler

from homeassistant.core import callback
from homeassistant.helpers.device_registry import DeviceInfo
from homeassistant.helpers.dispatcher import async_dispatcher_connect
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
        clean_dev_id = str(self._device_id)
        if clean_dev_id.startswith(f"{self._who}-"):
            clean_dev_id = clean_dev_id[len(f"{self._who}-") :]
        elif clean_dev_id.startswith(f"{self._who}_"):
            clean_dev_id = clean_dev_id[len(f"{self._who}_") :]

        self._attr_unique_id = f"{gateway.mac}-{self._who}-{clean_dev_id}"
        self._manufacturer = manufacturer or "BTicino S.p.A."
        self._model = model
        self._gateway_handler = gateway
        self._availability_listener_registered = False
        self._attr_has_entity_name = False
        self._attr_name = name
        self.entity_id = f"{platform.lower()}.{name.lower().replace(' ', '_').replace('#', '')}"

        self._attr_entity_registry_enabled_default = True
        self._attr_should_poll = False

        self._attr_device_info = DeviceInfo(
            identifiers={(DOMAIN, f"{gateway.mac}-{self._who}-{clean_dev_id}")},
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

    @property
    def available(self) -> bool:
        """Return whether the gateway is available."""
        return self._gateway_handler.available

    @callback
    def _handle_availability_update(self) -> None:
        """Write state when the gateway availability changes."""
        self.async_write_ha_state()

    @callback
    def _register_availability_listener(self) -> None:
        """Register the gateway availability listener once."""
        if self._availability_listener_registered:
            return
        target_hass = self.hass or self._hass
        if target_hass is None:
            return
        self.async_on_remove(
            async_dispatcher_connect(
                target_hass,
                self._gateway_handler.availability_signal,
                self._handle_availability_update,
            )
        )
        self._availability_listener_registered = True

    async def async_added_to_hass(self):
        """When entity is added to hass."""
        self._register_availability_listener()
        await self.async_update()

    async def async_will_remove_from_hass(self):
        """When entity is removed from hass."""
        pass
