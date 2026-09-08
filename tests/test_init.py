"""Tests for the MyHOME custom component initialization."""
import os
import pytest
from unittest.mock import patch, AsyncMock
from homeassistant.core import HomeAssistant
from homeassistant.config_entries import ConfigEntryState
from pytest_homeassistant_custom_component.common import MockConfigEntry

from custom_components.myhome.const import DOMAIN
from custom_components.myhome.ownd.connection import OWNGateway


async def test_setup_entry_success(hass: HomeAssistant):
    """Test successful setup of the integration via MockConfigEntry."""
    # 1. Provide a realistic connection mock that succeeds
    with patch(
        "custom_components.myhome.gateway.OWNSession.test_connection",
        return_value={"Success": True, "Message": None}
    ), patch(
        "custom_components.myhome.gateway.MyHOMEGatewayHandler.listening_loop"
    ), patch(
        "custom_components.myhome.gateway.MyHOMEGatewayHandler.sending_loop"
    ):
        config_entry = MockConfigEntry(
            domain=DOMAIN,
            data={
                "host": "192.168.0.35",
                "port": 20000,
                "password": "pass",
                "mac": "00:03:50:00:12:34",
                "ssdp_location": "http://192.168.0.35:49153/description.xml",
                "ssdp_st": "urn:schemas-upnp-org:device:Basic:1",
                "deviceType": "urn:schemas-upnp-org:device:Basic:1",
                "friendly_name": "MyHOME Gateway",
                "manufacturer": "BTicino",
                "manufacturerURL": "http://www.bticino.com",
                "name": "F454",
                "firmware": "2.0.0",
                "UDN": "uuid:12345678-1234-1234-1234-123456789012"
            },
            unique_id="00:03:50:00:12:34",
        )
        config_entry.add_to_hass(hass)

        assert await hass.config_entries.async_setup(config_entry.entry_id)
        await hass.async_block_till_done()

        # Check entry loaded
        assert config_entry.state is ConfigEntryState.LOADED

        # Cleanup
        assert await hass.config_entries.async_unload(config_entry.entry_id)
        await hass.async_block_till_done()
        assert config_entry.state is ConfigEntryState.NOT_LOADED


async def test_setup_entry_connection_failed(hass: HomeAssistant):
    """Test failing setup due to bad password or timeout."""
    with patch(
        "custom_components.myhome.gateway.OWNSession.test_connection",
        return_value={"Success": False, "Message": "password_error"}
    ):
        config_entry = MockConfigEntry(
            domain=DOMAIN,
            data={
                "host": "192.168.0.35",
                "port": 20000,
                "password": "wrong",
                "mac": "00:03:50:00:12:34",
                "ssdp_location": "http://192.168.0.35:49153/description.xml",
                "ssdp_st": "urn:schemas-upnp-org:device:Basic:1",
                "deviceType": "urn:schemas-upnp-org:device:Basic:1",
                "friendly_name": "MyHOME Gateway",
                "manufacturer": "BTicino",
                "manufacturerURL": "http://www.bticino.com",
                "name": "F454",
                "firmware": "2.0.0",
                "UDN": "uuid:12345678-1234-1234-1234-123456789012"
            },
            unique_id="00:03:50:00:12:35",
        )
        config_entry.add_to_hass(hass)

        result = await hass.config_entries.async_setup(config_entry.entry_id)
        await hass.async_block_till_done()

        # Should return False
        assert not result
        assert config_entry.state is ConfigEntryState.SETUP_ERROR

async def test_setup_yaml(hass: HomeAssistant):
    """Test setup from yaml configurations returns false."""
    from custom_components.myhome import async_setup
    result = await async_setup(hass, {DOMAIN: {}})
    assert not result

async def test_services(hass: HomeAssistant):
    """Test sync_time and send_message services."""
    from custom_components.myhome.const import ATTR_GATEWAY, ATTR_MESSAGE

    with patch(
        "custom_components.myhome.gateway.OWNSession.test_connection",
        return_value={"Success": True, "Message": None}
    ), patch(
        "custom_components.myhome.gateway.MyHOMEGatewayHandler.listening_loop"
    ), patch(
        "custom_components.myhome.gateway.MyHOMEGatewayHandler.sending_loop"
    ):
        config_entry = MockConfigEntry(
            domain=DOMAIN,
            data={
                "host": "192.168.0.35",
                "port": 20000,
                "password": "pass",
                "mac": "00:03:50:00:12:34",
                "ssdp_location": "http://192.168.0.35:49153/description.xml",
                "ssdp_st": "urn:schemas-upnp-org:device:Basic:1",
                "deviceType": "urn:schemas-upnp-org:device:Basic:1",
                "friendly_name": "MyHOME Gateway",
                "manufacturer": "BTicino",
                "manufacturerURL": "http://www.bticino.com",
                "name": "F454",
                "firmware": "2.0.0",
                "UDN": "uuid:12345678-1234-1234-1234-123456789012"
            },
            unique_id="00:03:50:00:12:34",
        )
        config_entry.add_to_hass(hass)

        await hass.config_entries.async_setup(config_entry.entry_id)
        await hass.async_block_till_done()

        gateway = hass.data[DOMAIN]["00:03:50:00:12:34"]["entity"]
        gateway.send = AsyncMock()

        # Test sync_time service
        await hass.services.async_call(
            DOMAIN, "sync_time", {ATTR_GATEWAY: "00:03:50:00:12:34"}, blocking=True
        )
        gateway.send.assert_called_once()
        gateway.send.reset_mock()

        # Test sync_time without gateway specified
        await hass.services.async_call(
            DOMAIN, "sync_time", {}, blocking=True
        )
        gateway.send.assert_called_once()
        gateway.send.reset_mock()

        # Test send_message service (valid)
        await hass.services.async_call(
            DOMAIN, "send_message", {ATTR_GATEWAY: "00:03:50:00:12:34", ATTR_MESSAGE: "*1*1*12##"}, blocking=True
        )
        gateway.send.assert_called_once()
        gateway.send.reset_mock()

        # Test send_message service (invalid)
        await hass.services.async_call(
            DOMAIN, "send_message", {ATTR_GATEWAY: "00:03:50:00:12:34", ATTR_MESSAGE: "invalid"}, blocking=True
        )
        gateway.send.assert_not_called()

        # Test missing gateway
        await hass.services.async_call(
            DOMAIN, "send_message", {ATTR_GATEWAY: "00:03:50:00:00:00", ATTR_MESSAGE: "*1*1*12##"}, blocking=True
        )
        gateway.send.assert_not_called()

        # Test send_message without gateway specified (hits line 266: gateway = _gw_keys[0])
        await hass.services.async_call(
            DOMAIN, "send_message", {ATTR_MESSAGE: "*1*1*12##"}, blocking=True
        )
        gateway.send.assert_called_once()
        gateway.send.reset_mock()

        # Test sync_time with invalid MAC format (lines 237-241)
        with patch("homeassistant.helpers.device_registry.format_mac", return_value=None):
            await hass.services.async_call(
                DOMAIN, "sync_time", {ATTR_GATEWAY: "invalid_mac"}, blocking=True
            )

        # Test sync_time with unconfigured valid MAC (lines 250-254)
        await hass.services.async_call(
            DOMAIN, "sync_time", {ATTR_GATEWAY: "00:03:50:00:99:99"}, blocking=True
        )

        # Test send_message with invalid MAC format (lines 270-275)
        with patch("homeassistant.helpers.device_registry.format_mac", return_value=None):
            await hass.services.async_call(
                DOMAIN, "send_message", {ATTR_GATEWAY: "invalid_mac", ATTR_MESSAGE: "*1*1*12##"}, blocking=True
            )

        # Test sync_time and send_message when no gateways exist in hass.data[DOMAIN] (lines 231-232, 262-266)
        saved_data = hass.data[DOMAIN]
        hass.data[DOMAIN] = {}
        try:
            await hass.services.async_call(
                DOMAIN, "sync_time", {}, blocking=True
            )
            await hass.services.async_call(
                DOMAIN, "send_message", {ATTR_MESSAGE: "*1*1*12##"}, blocking=True
            )
        finally:
            hass.data[DOMAIN] = saved_data


async def test_options_update_rebuilds_decoder_pool(hass: HomeAssistant):
    """Test options update listener rebuilds decoder pool."""
    from custom_components.myhome.const import (
        CONF_DECODER_ENTITY,
        CONF_DECODER_SOURCE,
        CONF_DECODER_PRE_GAIN,
    )

    with patch(
        "custom_components.myhome.gateway.OWNSession.test_connection",
        return_value={"Success": True, "Message": None}
    ), patch(
        "custom_components.myhome.gateway.MyHOMEGatewayHandler.listening_loop"
    ), patch(
        "custom_components.myhome.gateway.MyHOMEGatewayHandler.sending_loop"
    ):
        config_entry = MockConfigEntry(
            domain=DOMAIN,
            data={
                "host": "192.168.0.35",
                "port": 20000,
                "password": "pass",
                "mac": "00:03:50:00:12:34",
            },
            options={},
            unique_id="00:03:50:00:12:34",
        )
        config_entry.add_to_hass(hass)
        await hass.config_entries.async_setup(config_entry.entry_id)
        await hass.async_block_till_done()

        # Update options with a decoder mapping (lines 196-197)
        new_options = {
            CONF_DECODER_ENTITY.format(1): "media_player.zone1",
            CONF_DECODER_SOURCE.format(1): 1,
            CONF_DECODER_PRE_GAIN.format(1): 2,
        }
        hass.config_entries.async_update_entry(config_entry, options=new_options)
        await hass.async_block_till_done()

        pool = hass.data[DOMAIN]["00:03:50:00:12:34"]["decoder_pool"]
        assert pool is not None
        assert pool.is_configured is True
        assert "media_player.zone1" in pool._decoder_map


async def test_entity_migration_and_yaml_recovery_edges(hass: HomeAssistant):
    """Test entity registry auto-migration branches and customize.yaml error handling."""
    from unittest.mock import MagicMock
    mock_entry_reg = MagicMock()
    
    # Entity 1: unformatted MAC e.g. "000350001234-12" (lines 82-86)
    reg_e1 = MagicMock()
    reg_e1.domain = "light"
    reg_e1.entity_id = "light.myhome_light_12"
    reg_e1.unique_id = "000350001234-12"

    # Entity 2: causes ValueError in async_update_entity (lines 100-101)
    reg_e2 = MagicMock()
    reg_e2.domain = "light"
    reg_e2.entity_id = "light.myhome_conflict"
    reg_e2.unique_id = "00:03:50:00:12:34-13"

    # Entity 3: causes Exception in dr.format_mac (lines 85-86)
    reg_e3 = MagicMock()
    reg_e3.domain = "light"
    reg_e3.entity_id = "light.bad_mac"
    reg_e3.unique_id = "bad_mac-14"

    from homeassistant.helpers import device_registry as dr
    real_format_mac = dr.format_mac

    def fake_format_mac(val):
        if val == "bad_mac":
            raise ValueError("Corrupt MAC")
        return real_format_mac(val)

    mock_entry_reg.async_get_entity_id.return_value = None

    def update_side_effect(entity_id, new_unique_id):
        if "conflict" in entity_id:
            raise ValueError("Conflict")
        return MagicMock()

    mock_entry_reg.async_update_entity.side_effect = update_side_effect

    real_isfile = os.path.isfile

    def fake_isfile(p):
        if "customize.yaml" in str(p):
            return True
        return real_isfile(p)

    with patch(
        "custom_components.myhome.gateway.OWNSession.test_connection",
        return_value={"Success": True, "Message": None}
    ), patch(
        "custom_components.myhome.gateway.MyHOMEGatewayHandler.listening_loop"
    ), patch(
        "custom_components.myhome.gateway.MyHOMEGatewayHandler.sending_loop"
    ), patch(
        "homeassistant.helpers.entity_registry.async_get",
        return_value=mock_entry_reg,
    ), patch(
        "homeassistant.helpers.entity_registry.async_entries_for_config_entry",
        return_value=[reg_e1, reg_e2, reg_e3],
    ), patch(
        "homeassistant.helpers.device_registry.format_mac",
        side_effect=fake_format_mac,
    ), patch(
        "os.path.isfile",
        side_effect=fake_isfile,
    ), patch(
        "homeassistant.util.yaml.loader.load_yaml",
        side_effect=Exception("Corrupt YAML"),
    ):
        config_entry = MockConfigEntry(
            domain=DOMAIN,
            data={
                "host": "192.168.0.35",
                "port": 20000,
                "password": "pass",
                "mac": "00:03:50:00:12:34",
            },
            unique_id="00:03:50:00:12:34",
        )
        config_entry.add_to_hass(hass)
        await hass.config_entries.async_setup(config_entry.entry_id)
        await hass.async_block_till_done()

        # Both entities processed without crash despite ValueError and Corrupt YAML
        assert config_entry.state is ConfigEntryState.LOADED


async def test_setup_entry_duplicate_and_timeout(hass: HomeAssistant):
    """Test duplicate entry setup and gateway connection timeout error."""
    import asyncio
    from homeassistant.exceptions import ConfigEntryNotReady

    # 1. Config entry unique_id migration (lines 58-62)
    hass.data.setdefault(DOMAIN, {})
    unformatted_entry = MockConfigEntry(
        domain=DOMAIN,
        data={"mac": "00:03:50:00:99:88", "host": "192.168.0.99", "port": 20000},
        unique_id="000350009988",  # Unformatted MAC triggers lines 58-62
    )
    unformatted_entry.add_to_hass(hass)
    with patch(
        "custom_components.myhome.gateway.OWNSession.test_connection",
        return_value={"Success": True},
    ), patch(
        "custom_components.myhome.gateway.MyHOMEGatewayHandler.listening_loop"
    ), patch(
        "custom_components.myhome.gateway.MyHOMEGatewayHandler.sending_loop"
    ):
        assert await hass.config_entries.async_setup(unformatted_entry.entry_id)
        await hass.async_block_till_done()
        assert unformatted_entry.unique_id == "00:03:50:00:99:88"
        assert unformatted_entry.state is ConfigEntryState.LOADED

        assert await hass.config_entries.async_unload(unformatted_entry.entry_id)
        await hass.async_block_till_done()

    # 2. Gateway test raises TimeoutError -> ConfigEntryNotReady (lines 126-133)
    timeout_entry = MockConfigEntry(
        domain=DOMAIN,
        data={"mac": "00:03:50:00:99:77", "host": "192.168.0.98", "port": 20000},
        unique_id="00:03:50:00:99:77",
    )
    timeout_entry.add_to_hass(hass)
    from custom_components.myhome import async_setup_entry
    real_isfile = os.path.isfile

    def fake_isfile(p):
        if "customize.yaml" in str(p):
            return True
        return real_isfile(p)

    with patch(
        "custom_components.myhome.gateway.OWNSession.test_connection",
        side_effect=asyncio.TimeoutError("Timed out connecting"),
    ), patch(
        "os.path.isfile",
        side_effect=fake_isfile,
    ), patch(
        "homeassistant.util.yaml.loader.load_yaml",
        return_value={"light.test": {"friendly_name": "Test Light"}},
    ):
        with pytest.raises(ConfigEntryNotReady):
            await async_setup_entry(hass, timeout_entry)


