"""Test services module directly."""
from unittest.mock import MagicMock

from homeassistant.core import HomeAssistant

from custom_components.myhome.const import CONF_ENTITY, DOMAIN
from custom_components.myhome.services import (
    SERVICE_SEND_MESSAGE,
    SERVICE_SWEEP_BUS,
    SERVICE_SYNC_TIME,
    _get_gateway_handler,
    async_setup_services,
    async_unload_services,
)


async def test_services_setup_and_unload(hass: HomeAssistant) -> None:
    """Test setting up and unloading services idempotently."""
    assert not hass.services.has_service(DOMAIN, SERVICE_SYNC_TIME)
    assert not hass.services.has_service(DOMAIN, SERVICE_SEND_MESSAGE)
    assert not hass.services.has_service(DOMAIN, SERVICE_SWEEP_BUS)

    await async_setup_services(hass)
    assert hass.services.has_service(DOMAIN, SERVICE_SYNC_TIME)
    assert hass.services.has_service(DOMAIN, SERVICE_SEND_MESSAGE)
    assert hass.services.has_service(DOMAIN, SERVICE_SWEEP_BUS)

    # Idempotent re-setup
    await async_setup_services(hass)
    assert hass.services.has_service(DOMAIN, SERVICE_SYNC_TIME)

    # Unload
    await async_unload_services(hass)
    assert not hass.services.has_service(DOMAIN, SERVICE_SYNC_TIME)
    assert not hass.services.has_service(DOMAIN, SERVICE_SEND_MESSAGE)
    assert not hass.services.has_service(DOMAIN, SERVICE_SWEEP_BUS)


async def test_get_gateway_handler_helper(hass: HomeAssistant) -> None:
    """Test _get_gateway_handler lookup helper."""
    # When DOMAIN not in hass.data
    hass.data.pop(DOMAIN, None)
    assert _get_gateway_handler(hass, None) is None

    # When no gateways configured
    hass.data[DOMAIN] = {}
    assert _get_gateway_handler(hass, None) is None

    # When valid gateway configured
    mock_handler = MagicMock()
    gw_mac = "00:03:50:AA:BB:CC"
    hass.data[DOMAIN][gw_mac] = {CONF_ENTITY: mock_handler}

    # Default lookup (None)
    assert _get_gateway_handler(hass, None) == mock_handler

    # Specific valid lookup
    assert _get_gateway_handler(hass, gw_mac) == mock_handler

    # Invalid MAC format
    assert _get_gateway_handler(hass, "invalid_mac") is None

    # Unconfigured MAC
    assert _get_gateway_handler(hass, "00:03:50:99:99:99") is None
