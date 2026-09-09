from homeassistant.core import callback
from homeassistant.helpers.dispatcher import async_dispatcher_connect, async_dispatcher_send
"""Support for MyHome heating."""

from homeassistant.components.climate import (
    ClimateEntity,
    DOMAIN as PLATFORM,
)
from homeassistant.components.climate.const import (
    ClimateEntityFeature,
    HVACAction,
    HVACMode,
)
from homeassistant.const import (
    CONF_NAME,
    CONF_MAC,
    UnitOfTemperature,
)

from .ownd.message import (
    OWNHeatingEvent,
    OWNHeatingCommand,
    CLIMATE_MODE_OFF,
    CLIMATE_MODE_HEAT,
    CLIMATE_MODE_COOL,
    CLIMATE_MODE_AUTO,
    MESSAGE_TYPE_MAIN_TEMPERATURE,
    MESSAGE_TYPE_MAIN_HUMIDITY,
    MESSAGE_TYPE_TARGET_TEMPERATURE,
    MESSAGE_TYPE_LOCAL_OFFSET,
    MESSAGE_TYPE_LOCAL_TARGET_TEMPERATURE,
    MESSAGE_TYPE_MODE,
    MESSAGE_TYPE_MODE_TARGET,
    MESSAGE_TYPE_ACTION,
    MESSAGE_TYPE_FAN_SPEED,
)

from .const import (
    CONF_PLATFORMS,
    CONF_ENTITY,
    CONF_WHO,
    CONF_ZONE,
    CONF_MANUFACTURER,
    CONF_DEVICE_MODEL,
    CONF_HEATING_SUPPORT,
    CONF_COOLING_SUPPORT,
    CONF_FAN_SUPPORT,
    CONF_STANDALONE,
    CONF_CENTRAL,
    DOMAIN,
    LOGGER,
)
from .myhome_device import MyHOMEEntity
from .gateway import MyHOMEGatewayHandler


async def async_setup_entry(hass, config_entry, async_add_entities):
    if PLATFORM not in hass.data[DOMAIN][config_entry.data[CONF_MAC]][CONF_PLATFORMS]:
        return True

    _climate_devices = []
    _configured_climate_devices = hass.data[DOMAIN][config_entry.data[CONF_MAC]][
        CONF_PLATFORMS
    ][PLATFORM]

    for _climate_device in list(_configured_climate_devices.keys()):
        _climate_devices.append(
            MyHOMEClimate(
                hass=hass,
                device_id=_climate_device,
                who=_configured_climate_devices[_climate_device][CONF_WHO],
                where=_configured_climate_devices[_climate_device][CONF_ZONE],
                name=_configured_climate_devices[_climate_device][CONF_NAME],
                heating=_configured_climate_devices[_climate_device][
                    CONF_HEATING_SUPPORT
                ],
                cooling=_configured_climate_devices[_climate_device][
                    CONF_COOLING_SUPPORT
                ],
                fan=_configured_climate_devices[_climate_device][CONF_FAN_SUPPORT],
                standalone=_configured_climate_devices[_climate_device][
                    CONF_STANDALONE
                ],
                central=_configured_climate_devices[_climate_device][CONF_CENTRAL],
                manufacturer=_configured_climate_devices[_climate_device][
                    CONF_MANUFACTURER
                ],
                model=_configured_climate_devices[_climate_device][CONF_DEVICE_MODEL],
                gateway=hass.data[DOMAIN][config_entry.data[CONF_MAC]][CONF_ENTITY],
            )
        )

    async_add_entities(_climate_devices)

    @callback
    def _handle_climate_message(msg):
        """Filter and forward climate messages."""
        if isinstance(msg, OWNHeatingEvent):
            zone_where = f"#{msg.zone}" if msg.zone == 0 else str(msg.zone)
            async_dispatcher_send(
                hass,
                f"myhome_update_{config_entry.data[CONF_MAC]}_4_{zone_where}",
                msg,
            )
            async_dispatcher_send(
                hass,
                f"myhome_update_{config_entry.data[CONF_MAC]}_4_{msg.where}",
                msg,
            )

    config_entry.async_on_unload(
        async_dispatcher_connect(
            hass,
            f"myhome_message_{config_entry.data[CONF_MAC]}",
            _handle_climate_message,
        )
    )
    return True


async def async_unload_entry(hass, config_entry):
    if PLATFORM not in hass.data[DOMAIN][config_entry.data[CONF_MAC]][CONF_PLATFORMS]:
        return True

    _configured_climate_devices = hass.data[DOMAIN][config_entry.data[CONF_MAC]][
        CONF_PLATFORMS
    ][PLATFORM]

    for _climate_device in list(_configured_climate_devices.keys()):
        del hass.data[DOMAIN][config_entry.data[CONF_MAC]][CONF_PLATFORMS][PLATFORM][
            _climate_device
        ]
    return True


class MyHOMEClimate(MyHOMEEntity, ClimateEntity):
    def __init__(
        self,
        hass,
        name: str,
        device_id: str,
        who: str,
        where: str,
        heating: bool,
        cooling: bool,
        fan: bool,
        standalone: bool,
        central: bool,
        manufacturer: str,
        model: str,
        gateway: MyHOMEGatewayHandler,
    ):
        super().__init__(
            hass=hass,
            name=name,
            platform=PLATFORM,
            device_id=device_id,
            who=who,
            where=where,
            manufacturer=manufacturer,
            model=model,
            gateway=gateway,
        )

        self._standalone = standalone
        self._central = True if self._where == "#0" else central

        self._attr_temperature_unit = UnitOfTemperature.CELSIUS
        self._attr_precision = 0.1
        self._attr_target_temperature_step = 0.5
        self._attr_min_temp = 5
        self._attr_max_temp = 40

        self._attr_supported_features = 0
        self._attr_hvac_modes = [HVACMode.OFF]
        self._heating = heating
        self._cooling = cooling
        if heating or cooling:
            self._attr_supported_features |= ClimateEntityFeature.TARGET_TEMPERATURE
            if not self._central:
                self._attr_hvac_modes.append(HVACMode.AUTO)
            if heating:
                self._attr_hvac_modes.append(HVACMode.HEAT)
            if cooling:
                self._attr_hvac_modes.append(HVACMode.COOL)

        # Fan mode support (fancoil 3-speed + auto)
        self._fan = fan
        if self._fan:
            self._attr_supported_features |= ClimateEntityFeature.FAN_MODE
            self._attr_fan_modes = ["auto", "low", "medium", "high"]
            self._attr_fan_mode = "auto"

        self._attr_current_temperature = None
        self._attr_current_humidity = None
        self._target_temperature = None
        self._local_offset = 0
        self._local_target_temperature = None

        self._attr_hvac_mode = None
        self._attr_hvac_action = None

    @property
    def extra_state_attributes(self):
        """Return device specific attributes."""
        attrs = {
            "local_offset": self._local_offset,
        }
        if self._fan:
            attrs["fan_mode"] = self._attr_fan_mode
        return attrs

    async def async_added_to_hass(self):
        """Run when entity about to be added to hass."""
        self.async_on_remove(
            async_dispatcher_connect(
                self.hass,
                f"myhome_update_{self._gateway_handler.mac}_4_{self._where}",
                self.handle_event,
            )
        )
        await self._gateway_handler.send_status_request(
            OWNHeatingCommand.status(self._where)
        )

    async def async_set_fan_mode(self, fan_mode: str):
        """Set new target fan mode."""
        fan_mode_map = {
            "auto": 0,
            "low": 1,
            "medium": 2,
            "high": 3,
        }
        speed_code = fan_mode_map.get(str(fan_mode).lower())
        if speed_code is not None:
            self._attr_fan_mode = fan_mode
            await self._gateway_handler.send(
                OWNHeatingCommand.set_fan_speed(
                    where=self._where,
                    speed=speed_code,
                    standalone=self._standalone,
                )
            )
            if self.hass is not None:
                self.async_write_ha_state()



    async def async_update(self):
        """Update the entity.

        Only used by the generic entity update service.
        """
        await self._gateway_handler.send_status_request(
            OWNHeatingCommand.status(self._where)
        )

    @property
    def target_temperature(self) -> float:
        if self._local_target_temperature is not None:
            return self._local_target_temperature
        else:
            return self._target_temperature

    async def async_set_hvac_mode(self, hvac_mode):
        """Set new target hvac mode."""
        if hvac_mode == HVACMode.OFF:
            await self._gateway_handler.send(
                OWNHeatingCommand.set_mode(
                    where=self._where,
                    mode=CLIMATE_MODE_OFF,
                    standalone=self._standalone,
                )
            )
        elif hvac_mode == HVACMode.AUTO:
            await self._gateway_handler.send(
                OWNHeatingCommand.set_mode(
                    where=self._where,
                    mode=CLIMATE_MODE_AUTO,
                    standalone=self._standalone,
                )
            )
        elif hvac_mode == HVACMode.HEAT:
            if self._target_temperature is not None:
                await self._gateway_handler.send(
                    OWNHeatingCommand.set_temperature(
                        where=self._where,
                        temperature=self._target_temperature,
                        mode=CLIMATE_MODE_HEAT,
                        standalone=self._standalone,
                    )
                )
        elif hvac_mode == HVACMode.COOL:
            if self._target_temperature is not None:
                await self._gateway_handler.send(
                    OWNHeatingCommand.set_temperature(
                        where=self._where,
                        temperature=self._target_temperature,
                        mode=CLIMATE_MODE_COOL,
                        standalone=self._standalone,
                    )
                )


    async def async_set_temperature(self, **kwargs):
        """Set new target temperature."""
        target_temperature = (
            kwargs.get("temperature", self._local_target_temperature)
            - self._local_offset
        )
        if self._attr_hvac_mode == HVACMode.HEAT:
            await self._gateway_handler.send(
                OWNHeatingCommand.set_temperature(
                    where=self._where,
                    temperature=target_temperature,
                    mode=CLIMATE_MODE_HEAT,
                    standalone=self._standalone,
                )
            )
        elif self._attr_hvac_mode == HVACMode.COOL:
            await self._gateway_handler.send(
                OWNHeatingCommand.set_temperature(
                    where=self._where,
                    temperature=target_temperature,
                    mode=CLIMATE_MODE_COOL,
                    standalone=self._standalone,
                )
            )
        else:
            await self._gateway_handler.send(
                OWNHeatingCommand.set_temperature(
                    where=self._where,
                    temperature=target_temperature,
                    mode=CLIMATE_MODE_AUTO,
                    standalone=self._standalone,
                )
            )

    @callback
    def handle_event(self, message: OWNHeatingEvent):
        """Handle an event message."""
        if message.message_type == MESSAGE_TYPE_MAIN_TEMPERATURE:
            LOGGER.info(
                "%s %s",
                self._gateway_handler.log_id,
                message.human_readable_log,
            )
            self._attr_current_temperature = message.main_temperature
        elif message.message_type == MESSAGE_TYPE_MAIN_HUMIDITY:
            LOGGER.info(
                "%s %s",
                self._gateway_handler.log_id,
                message.human_readable_log,
            )
            self._attr_current_humidity = message.main_humidity
        elif message.message_type == MESSAGE_TYPE_TARGET_TEMPERATURE:
            LOGGER.info(
                "%s %s",
                self._gateway_handler.log_id,
                message.human_readable_log,
            )
            self._target_temperature = message.set_temperature
            self._local_target_temperature = (
                self._target_temperature + self._local_offset
            )
        elif message.message_type == MESSAGE_TYPE_LOCAL_OFFSET:
            LOGGER.info(
                "%s %s",
                self._gateway_handler.log_id,
                message.human_readable_log,
            )
            self._local_offset = message.local_offset
            if self._target_temperature is not None:
                self._local_target_temperature = (
                    self._target_temperature + self._local_offset
                )
        elif message.message_type == MESSAGE_TYPE_LOCAL_TARGET_TEMPERATURE:
            LOGGER.info(
                "%s %s",
                self._gateway_handler.log_id,
                message.human_readable_log,
            )
            self._local_target_temperature = message.local_set_temperature
            self._target_temperature = (
                self._local_target_temperature - self._local_offset
            )
        elif message.message_type == MESSAGE_TYPE_MODE:
            if (
                message.mode == CLIMATE_MODE_AUTO
                and HVACMode.AUTO in self._attr_hvac_modes
            ):
                LOGGER.info(
                    "%s %s",
                    self._gateway_handler.log_id,
                    message.human_readable_log,
                )
                self._attr_hvac_mode = HVACMode.AUTO
                if self._attr_hvac_action == HVACAction.OFF:
                    self._attr_hvac_action = HVACAction.IDLE
            elif (
                message.mode == CLIMATE_MODE_COOL
                and HVACMode.COOL in self._attr_hvac_modes
            ):
                LOGGER.info(
                    "%s %s",
                    self._gateway_handler.log_id,
                    message.human_readable_log,
                )
                self._attr_hvac_mode = HVACMode.COOL
                if self._attr_hvac_action == HVACAction.OFF:
                    self._attr_hvac_action = HVACAction.IDLE
            elif (
                message.mode == CLIMATE_MODE_HEAT
                and HVACMode.HEAT in self._attr_hvac_modes
            ):
                LOGGER.info(
                    "%s %s",
                    self._gateway_handler.log_id,
                    message.human_readable_log,
                )
                self._attr_hvac_mode = HVACMode.HEAT
                if self._attr_hvac_action == HVACAction.OFF:
                    self._attr_hvac_action = HVACAction.IDLE
            elif message.mode == CLIMATE_MODE_OFF:
                LOGGER.info(
                    "%s %s",
                    self._gateway_handler.log_id,
                    message.human_readable_log,
                )
                self._attr_hvac_mode = HVACMode.OFF
                self._attr_hvac_action = HVACAction.OFF
        elif message.message_type == MESSAGE_TYPE_MODE_TARGET:
            if (
                message.mode == CLIMATE_MODE_AUTO
                and HVACMode.AUTO in self._attr_hvac_modes
            ):
                LOGGER.info(
                    "%s %s",
                    self._gateway_handler.log_id,
                    message.human_readable_log,
                )
                self._attr_hvac_mode = HVACMode.AUTO
                if self._attr_hvac_action == HVACAction.OFF:
                    self._attr_hvac_action = HVACAction.IDLE
            elif (
                message.mode == CLIMATE_MODE_COOL
                and HVACMode.COOL in self._attr_hvac_modes
            ):
                LOGGER.info(
                    "%s %s",
                    self._gateway_handler.log_id,
                    message.human_readable_log,
                )
                self._attr_hvac_mode = HVACMode.COOL
                if self._attr_hvac_action == HVACAction.OFF:
                    self._attr_hvac_action = HVACAction.IDLE
            elif (
                message.mode == CLIMATE_MODE_HEAT
                and HVACMode.HEAT in self._attr_hvac_modes
            ):
                LOGGER.info(
                    "%s %s",
                    self._gateway_handler.log_id,
                    message.human_readable_log,
                )
                self._attr_hvac_mode = HVACMode.HEAT
                if self._attr_hvac_action == HVACAction.OFF:
                    self._attr_hvac_action = HVACAction.IDLE
            elif message.mode == CLIMATE_MODE_OFF:
                LOGGER.info(
                    "%s %s",
                    self._gateway_handler.log_id,
                    message.human_readable_log,
                )
                self._attr_hvac_mode = HVACMode.OFF
                self._attr_hvac_action = HVACAction.OFF
            self._target_temperature = message.set_temperature
            self._local_target_temperature = (
                self._target_temperature + self._local_offset
            )
        elif message.message_type == MESSAGE_TYPE_ACTION:
            LOGGER.info(
                "%s %s",
                self._gateway_handler.log_id,
                message.human_readable_log,
            )
            if message.is_active():
                if self._heating and self._cooling:
                    if message.is_heating():
                        self._attr_hvac_action = HVACAction.HEATING
                    elif message.is_cooling():
                        self._attr_hvac_action = HVACAction.COOLING
                elif self._heating:
                    self._attr_hvac_action = HVACAction.HEATING
                elif self._cooling:
                    self._attr_hvac_action = HVACAction.COOLING
            elif self._attr_hvac_mode == HVACMode.OFF:
                self._attr_hvac_action = HVACAction.OFF
            else:
                self._attr_hvac_action = HVACAction.IDLE
        elif message.message_type == MESSAGE_TYPE_FAN_SPEED or (
            hasattr(message, "fan_speed") and message.fan_speed is not None
        ):
            LOGGER.info(
                "%s %s",
                self._gateway_handler.log_id,
                message.human_readable_log,
            )
            speed = getattr(message, "fan_speed", None)
            if speed == 0:
                self._attr_fan_mode = "auto"
            elif speed == 1:
                self._attr_fan_mode = "low"
            elif speed == 2:
                self._attr_fan_mode = "medium"
            elif speed == 3:
                self._attr_fan_mode = "high"

        if self.hass is not None or hasattr(self.async_schedule_update_ha_state, "assert_called"):
            try:
                self.async_schedule_update_ha_state()
            except RuntimeError:
                pass
