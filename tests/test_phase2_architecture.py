"""Unit tests for Phase 2 Architecture:
- P2: Native CEN / CEN+ Command Builders, string-preserved addressing, and Device Triggers
- P4: Thermoregulation Central Unit (3550 / 4695) coordination & master seasonal mode propagation
- P6: Multi-Gateway Routing and plant event isolation
"""
from unittest.mock import AsyncMock, MagicMock, patch

import pytest
from homeassistant.components.climate import (
    HVACAction,
    HVACMode,
)
from homeassistant.const import (
    CONF_DEVICE_ID,
    CONF_TYPE,
)
from homeassistant.core import HomeAssistant
from homeassistant.helpers import device_registry as dr
from OWNd.message import (
    OWNCenCommand,
    OWNCenPlusCommand,
    OWNCommand,
)
from pytest_homeassistant_custom_component.common import MockConfigEntry

from custom_components.myhome.climate import MyHOMEClimate
from custom_components.myhome.const import (
    CONF_SHORT_PRESS,
    DOMAIN,
)
from custom_components.myhome.device_trigger import (
    CONF_ADDRESS,
    CONF_SUBTYPE,
    async_attach_trigger,
)
from custom_components.myhome.gateway import MyHOMEGatewayHandler

# ==============================================================================
# P2: CEN / CEN+ Command Builders & Roundtrip
# ==============================================================================

def test_p2_cen_command_builders_exact_framing():
    """Verify strongly typed OWNCenCommand and OWNCenPlusCommand emit exact OpenWebNet frames."""
    # CEN (WHO=15)
    press = OWNCenCommand.press("11", 2)
    assert str(press) == "*15*1*11#2##"

    start_long = OWNCenCommand.start_long_press("11", 2)
    assert str(start_long) == "*15*0*11#2##"

    release = OWNCenCommand.release("11", 2)
    assert str(release) == "*15*2*11#2##"

    # CEN+ (WHO=25)
    press_plus = OWNCenPlusCommand.press("12", 1)
    assert str(press_plus) == "*25*21#1*12##"

    start_long_plus = OWNCenPlusCommand.start_long_press("12", 1)
    assert str(start_long_plus) == "*25*22#1*12##"

    release_plus = OWNCenPlusCommand.release("12", 1)
    assert str(release_plus) == "*25*24#1*12##"

    held_plus = OWNCenPlusCommand.still_held("12", 1)
    assert str(held_plus) == "*25*23#1*12##"

    # Roundtrip parser instantiation
    parsed_cen = OWNCommand.parse("*15*1*11#2##")
    assert isinstance(parsed_cen, OWNCenCommand)

    parsed_cen_plus = OWNCommand.parse("*25*21#1*12##")
    assert isinstance(parsed_cen_plus, OWNCenPlusCommand)


# ==============================================================================
# P2: String-Preserved Addressing & Zero-Padding in Gateway & Trigger
# ==============================================================================

@pytest.mark.asyncio
async def test_p2_gateway_cen_string_preservation_and_event_enrichment(hass: HomeAssistant):
    """Test that gateway preserves zero-padded string addresses in events and registry."""
    mock_entry = MagicMock()
    mock_entry.data = {
        "address": "192.168.1.50",
        "port": 20000,
        "serialNumber": "00:03:50:aa:bb:cc",
    }
    mock_entry.entry_id = "entry_12345"
    gateway = MyHOMEGatewayHandler(hass, mock_entry)
    gateway.gateway = MagicMock()
    gateway.gateway.serial = "00:03:50:aa:bb:cc"

    fired_events = []

    def _event_listener(event):
        fired_events.append(event.data)

    hass.bus.async_listen("myhome_cen_event", _event_listener)
    hass.bus.async_listen("myhome_cenplus_event", _event_listener)

    # Mock CEN event with zero-padded address "0001"
    cen_msg = MagicMock()
    cen_msg.__class__.__name__ = "OWNCENEvent"
    from OWNd.message import OWNCENEvent
    cen_msg = MagicMock(spec=OWNCENEvent)
    cen_msg.object = "0001"
    cen_msg.push_button = "1"
    cen_msg.is_pressed = True
    cen_msg.is_released_after_short_press = False
    cen_msg.is_held = False
    cen_msg.is_released_after_long_press = False
    cen_msg.human_readable_log = "Short press on CEN 0001 button 1"

    with patch.object(gateway, "_ensure_cen_device") as mock_ensure:
        await gateway._process_message(cen_msg)

        mock_ensure.assert_called_once_with(15, "0001")
        assert len(fired_events) == 1
        data = fired_events[0]
        assert data["where"] == "0001"
        assert data["object"] == 1
        assert data["pushbutton"] == 1
        assert data["gateway_mac"] == "00:03:50:aa:bb:cc"
        assert data["entry_id"] == "entry_12345"


@pytest.mark.asyncio
async def test_p2_device_trigger_string_and_zero_padded_matching(hass: HomeAssistant):
    """Test that device triggers match zero-padded strings and numeric addresses interchangeably."""
    action = AsyncMock()
    config = {
        CONF_TYPE: CONF_SHORT_PRESS,
        CONF_SUBTYPE: "button_1",
        CONF_ADDRESS: "0001",
    }
    unsub = await async_attach_trigger(hass, config, action, {})

    # Mismatched address ("0002") -> ignored
    hass.bus.async_fire(
        "myhome_cen_event",
        {
            "event": CONF_SHORT_PRESS,
            "pushbutton": 1,
            "where": "0002",
            "object": 2,
        },
    )
    await hass.async_block_till_done()
    action.assert_not_called()

    # Matched string address ("0001")
    hass.bus.async_fire(
        "myhome_cen_event",
        {
            "event": CONF_SHORT_PRESS,
            "pushbutton": 1,
            "where": "0001",
            "object": 1,
        },
    )
    await hass.async_block_till_done()
    action.assert_called_once()
    action.reset_mock()

    unsub()


# ==============================================================================
# P4: Thermoregulation Central Unit (3550 & 4695)
# ==============================================================================

@pytest.mark.asyncio
async def test_p4_central_unit_3550_initialization_and_commands(hass: HomeAssistant):
    """Test 99-zone Central Unit (#0) command emission and modes."""
    gateway = MagicMock()
    gateway.mac = "00:03:50:11:22:33"
    gateway.send = AsyncMock()
    gateway.send_status_request = AsyncMock()

    cu99 = MyHOMEClimate(
        hass=hass,
        device_id="cu_99",
        who="4",
        where="#0",
        interface=None,
        name="Central Unit 99",
        heating=True,
        cooling=True,
        fan=False,
        standalone=False,
        central=True,
        manufacturer="BTicino",
        model="Central Unit (3550)",
        gateway=gateway,
    )

    assert cu99._central is True
    assert cu99._standalone is False
    assert HVACMode.HEAT in cu99._attr_hvac_modes
    assert HVACMode.COOL in cu99._attr_hvac_modes
    assert HVACMode.AUTO in cu99._attr_hvac_modes
    assert HVACMode.OFF in cu99._attr_hvac_modes

    # Set master heat mode -> *4*101*#0##
    await cu99.async_set_hvac_mode(HVACMode.HEAT)
    assert gateway.send.call_count == 1
    sent_cmd = gateway.send.call_args[0][0]
    assert str(sent_cmd) == "*4*101*#0##"
    assert cu99._attr_hvac_mode == HVACMode.HEAT

    # Set master cool mode -> *4*102*#0##
    gateway.send.reset_mock()
    await cu99.async_set_hvac_mode(HVACMode.COOL)
    sent_cmd = gateway.send.call_args[0][0]
    assert str(sent_cmd) == "*4*102*#0##"
    assert cu99._attr_hvac_mode == HVACMode.COOL

    # Set master off mode -> *4*100*#0##
    gateway.send.reset_mock()
    await cu99.async_set_hvac_mode(HVACMode.OFF)
    sent_cmd = gateway.send.call_args[0][0]
    assert str(sent_cmd) == "*4*100*#0##"
    assert cu99._attr_hvac_mode == HVACMode.OFF

    # Set master temperature setpoint -> *#4*#0*#14*0215*1##
    gateway.send.reset_mock()
    cu99._attr_hvac_mode = HVACMode.HEAT
    await cu99.async_set_temperature(temperature=21.5)
    sent_cmd = gateway.send.call_args[0][0]
    assert str(sent_cmd) == "*#4*#0*#14*0215*1##"


@pytest.mark.asyncio
async def test_p4_central_unit_4695_four_zone(hass: HomeAssistant):
    """Test 4-zone Central Unit (#0#1) command emission."""
    gateway = MagicMock()
    gateway.mac = "00:03:50:11:22:33"
    gateway.send = AsyncMock()

    cu4 = MyHOMEClimate(
        hass=hass,
        device_id="cu_4",
        who="4",
        where="#0#1",
        interface=None,
        name="Central Unit 4 Zone",
        heating=True,
        cooling=True,
        fan=False,
        standalone=False,
        central=True,
        manufacturer="BTicino",
        model="Central Unit (4695)",
        gateway=gateway,
    )

    assert cu4._central is True
    assert cu4._standalone is False

    # Set master heat mode on 4-zone CU -> *4*101*#0#1##
    await cu4.async_set_hvac_mode(HVACMode.HEAT)
    sent_cmd = gateway.send.call_args[0][0]
    assert str(sent_cmd) == "*4*101*#0#1##"


@pytest.mark.asyncio
async def test_p4_master_seasonal_mode_propagation_to_subordinate_zones(hass: HomeAssistant):
    """Test that Central Unit master mode switches propagate to subordinate non-standalone zones."""
    gateway = MagicMock()
    gateway.mac = "00:03:50:11:22:33"
    gateway.send = AsyncMock()
    gateway.send_status_request = AsyncMock()

    # Central Unit
    cu = MyHOMEClimate(
        hass=hass,
        device_id="cu_master",
        who="4",
        where="#0",
        interface=None,
        name="Central Unit",
        heating=True,
        cooling=True,
        fan=False,
        standalone=False,
        central=True,
        manufacturer="BTicino",
        model="Central Unit (3550)",
        gateway=gateway,
    )

    # Subordinate Zone 1 (non-standalone, follows central)
    zone1 = MyHOMEClimate(
        hass=hass,
        device_id="zone_1",
        who="4",
        where="1",
        interface=None,
        name="Zone 1",
        heating=True,
        cooling=True,
        fan=False,
        standalone=False,
        central=False,
        manufacturer="BTicino",
        model="Heating Zone",
        gateway=gateway,
    )

    # Standalone Zone 2 (independent thermostat)
    zone2_standalone = MyHOMEClimate(
        hass=hass,
        device_id="zone_2",
        who="4",
        where="2",
        interface=None,
        name="Zone 2",
        heating=True,
        cooling=True,
        fan=False,
        standalone=True,
        central=False,
        manufacturer="BTicino",
        model="Heating Zone",
        gateway=gateway,
    )

    # Register to Home Assistant
    await cu.async_added_to_hass()
    await zone1.async_added_to_hass()
    await zone2_standalone.async_added_to_hass()

    # Set both zones initially active
    zone1._attr_hvac_mode = HVACMode.HEAT
    zone2_standalone._attr_hvac_mode = HVACMode.HEAT

    # Switch Central Unit to COOL
    await cu.async_set_hvac_mode(HVACMode.COOL)

    # Subordinate Zone 1 follows master mode switch to COOL
    assert zone1._attr_hvac_mode == HVACMode.COOL
    # Standalone Zone 2 remains unaffected
    assert zone2_standalone._attr_hvac_mode == HVACMode.HEAT

    # Switch Central Unit to OFF
    await cu.async_set_hvac_mode(HVACMode.OFF)
    assert zone1._attr_hvac_mode == HVACMode.OFF
    assert zone1._attr_hvac_action == HVACAction.OFF
    # Standalone Zone 2 remains unaffected
    assert zone2_standalone._attr_hvac_mode == HVACMode.HEAT


# ==============================================================================
# P6: Multi-Gateway Routing & Plant Event Isolation
# ==============================================================================

@pytest.mark.asyncio
async def test_p6_multi_gateway_scenario_trigger_isolation(hass: HomeAssistant):
    """Test that CEN/CEN+ triggers bound to Gateway A do NOT fire on Gateway B events."""
    entry1 = MockConfigEntry(
        domain=DOMAIN,
        data={"serialNumber": "00:03:50:aa:aa:aa"},
        entry_id="config_gw1",
    )
    entry1.add_to_hass(hass)

    entry2 = MockConfigEntry(
        domain=DOMAIN,
        data={"serialNumber": "00:03:50:bb:bb:bb"},
        entry_id="config_gw2",
    )
    entry2.add_to_hass(hass)

    device_registry = dr.async_get(hass)

    # Gateway 1 device & Scenario Button device on Gateway 1
    device_registry.async_get_or_create(
        config_entry_id="config_gw1",
        identifiers={(DOMAIN, "00:03:50:aa:aa:aa")},
        name="Gateway 1",
    )
    btn_gw1 = device_registry.async_get_or_create(
        config_entry_id="config_gw1",
        identifiers={(DOMAIN, "00:03:50:aa:aa:aa-15-7")},
        name="CEN Button 7 GW1",
        via_device=(DOMAIN, "00:03:50:aa:aa:aa"),
    )

    # Gateway 2 device & Scenario Button device on Gateway 2
    device_registry.async_get_or_create(
        config_entry_id="config_gw2",
        identifiers={(DOMAIN, "00:03:50:bb:bb:bb")},
        name="Gateway 2",
    )
    btn_gw2 = device_registry.async_get_or_create(
        config_entry_id="config_gw2",
        identifiers={(DOMAIN, "00:03:50:bb:bb:bb-15-7")},
        name="CEN Button 7 GW2",
        via_device=(DOMAIN, "00:03:50:bb:bb:bb"),
    )

    action_gw1 = AsyncMock()
    action_gw2 = AsyncMock()

    # Attach trigger for Button on Gateway 1
    unsub1 = await async_attach_trigger(
        hass,
        {
            CONF_DEVICE_ID: btn_gw1.id,
            CONF_TYPE: CONF_SHORT_PRESS,
            CONF_SUBTYPE: "button_1",
        },
        action_gw1,
        {},
    )

    # Attach trigger for Button on Gateway 2
    unsub2 = await async_attach_trigger(
        hass,
        {
            CONF_DEVICE_ID: btn_gw2.id,
            CONF_TYPE: CONF_SHORT_PRESS,
            CONF_SUBTYPE: "button_1",
        },
        action_gw2,
        {},
    )

    # Event arrives from Gateway 1: button 1 of address 7
    hass.bus.async_fire(
        "myhome_cen_event",
        {
            "event": CONF_SHORT_PRESS,
            "pushbutton": 1,
            "where": "7",
            "object": 7,
            "gateway_mac": "00:03:50:aa:aa:aa",
            "entry_id": "config_gw1",
        },
    )
    await hass.async_block_till_done()

    # ONLY Action for Gateway 1 was called; Gateway 2 was completely isolated!
    action_gw1.assert_called_once()
    action_gw2.assert_not_called()
    action_gw1.reset_mock()

    # Event arrives from Gateway 2: button 1 of address 7
    hass.bus.async_fire(
        "myhome_cen_event",
        {
            "event": CONF_SHORT_PRESS,
            "pushbutton": 1,
            "where": "7",
            "object": 7,
            "gateway_mac": "00:03:50:bb:bb:bb",
            "entry_id": "config_gw2",
        },
    )
    await hass.async_block_till_done()

    # ONLY Action for Gateway 2 was called; Gateway 1 was completely isolated!
    action_gw1.assert_not_called()
    action_gw2.assert_called_once()

    unsub1()
    unsub2()


@pytest.mark.asyncio
async def test_p6_multi_gateway_central_unit_isolation(hass: HomeAssistant):
    """Test that Central Unit seasonal mode updates are strictly namespaced by gateway MAC."""
    gw1 = MagicMock()
    gw1.mac = "00:03:50:aa:aa:aa"
    gw1.send = AsyncMock()
    gw1.send_status_request = AsyncMock()

    gw2 = MagicMock()
    gw2.mac = "00:03:50:bb:bb:bb"
    gw2.send = AsyncMock()
    gw2.send_status_request = AsyncMock()

    # Central Unit on Gateway 1
    cu_gw1 = MyHOMEClimate(
        hass=hass,
        device_id="cu_gw1",
        who="4",
        where="#0",
        interface=None,
        name="Central Unit GW1",
        heating=True,
        cooling=True,
        fan=False,
        standalone=False,
        central=True,
        manufacturer="BTicino",
        model="Central Unit (3550)",
        gateway=gw1,
    )

    # Subordinate Zone on Gateway 2 (separate physical plant)
    zone_gw2 = MyHOMEClimate(
        hass=hass,
        device_id="zone_gw2",
        who="4",
        where="1",
        interface=None,
        name="Zone 1 GW2",
        heating=True,
        cooling=True,
        fan=False,
        standalone=False,
        central=False,
        manufacturer="BTicino",
        model="Heating Zone",
        gateway=gw2,
    )

    await cu_gw1.async_added_to_hass()
    await zone_gw2.async_added_to_hass()

    zone_gw2._attr_hvac_mode = HVACMode.HEAT

    # Switch CU on Gateway 1 to COOL
    await cu_gw1.async_set_hvac_mode(HVACMode.COOL)

    # Zone on Gateway 2 MUST NOT be affected!
    assert zone_gw2._attr_hvac_mode == HVACMode.HEAT
