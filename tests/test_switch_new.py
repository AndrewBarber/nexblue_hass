"""Test the NexBlue switch platform."""

from __future__ import annotations

from unittest.mock import AsyncMock

import pytest
from homeassistant.components.switch import DOMAIN as SWITCH_DOMAIN
from homeassistant.const import (
    ATTR_ENTITY_ID,
    SERVICE_TURN_OFF,
    SERVICE_TURN_ON,
    STATE_OFF,
    STATE_ON,
    STATE_UNAVAILABLE,
)
from homeassistant.core import HomeAssistant
from pytest_homeassistant_custom_component.common import MockConfigEntry

from custom_components.nexblue_hass.const import SWITCH_ICON

# Enable async support for all tests
pytestmark = pytest.mark.asyncio


def create_mock_charger(charging=False, connected=True, serial_number="CHARGER123"):
    """Create a mock charger with the given state."""
    return {
        "serial_number": serial_number,
        "name": f"Charger {serial_number}",
        "model": "Test Model",
        "firmware_version": "1.0.0",
        "status": {
            "is_charging": charging,
            "is_connected": connected,
            "current_power": 6.5 if charging else 0.0,
            "current_limit": 32.0,
            "charging_state": "charging" if charging else "standby",
            "plug_state": "connected" if connected else "disconnected",
            "max_charging_current": 32.0,
            "actual_charging_current": 6.5 if charging else 0.0,
            "actual_power": 1500.0 if charging else 0.0,
            "total_energy": 123.45,
        },
    }


@pytest.mark.asyncio
async def test_switch_turn_on(
    hass: HomeAssistant,
    setup_integration: MockConfigEntry,
    mock_api_client: AsyncMock,
) -> None:
    """Test turning the switch on."""
    # Setup test data
    charger = create_mock_charger(charging=False)
    serial_number = charger["serial_number"]
    entity_id = f"{SWITCH_DOMAIN}.charger_{serial_number.lower()}"

    # Configure mock API client with proper data structure
    async def mock_get_data():
        return {"chargers": [charger]}

    mock_api_client.async_get_data.side_effect = mock_get_data
    mock_api_client.async_start_charging = AsyncMock(return_value=True)
    mock_api_client.async_get_data.return_value = {"chargers": [charger]}

    # Let HA settle
    await hass.async_block_till_done()

    # Verify initial state is off
    state = hass.states.get(entity_id)
    assert state is not None, f"State for {entity_id} is None"
    assert (
        state.state == STATE_OFF
    ), f"Expected {entity_id} to be off, was {state.state}"
    assert state.attributes.get("icon") == SWITCH_ICON

    # Test turning on
    mock_api_client.async_start_charging.reset_mock()
    await hass.services.async_call(
        SWITCH_DOMAIN,
        SERVICE_TURN_ON,
        {ATTR_ENTITY_ID: entity_id},
        blocking=True,
    )

    # Verify the API was called with the correct parameters
    mock_api_client.async_start_charging.assert_called_once()
    args, _ = mock_api_client.async_start_charging.call_args
    assert (
        args[0] == serial_number
    ), f"Expected serial number {serial_number}, got {args[0]}"

    # Update the mock to reflect the state change
    updated_charger = {**charger, "charging": True}
    mock_api_client.async_get_data.return_value = {"chargers": [updated_charger]}

    # Trigger state refresh
    await hass.services.async_call(
        "homeassistant",
        "update_entity",
        {ATTR_ENTITY_ID: entity_id},
        blocking=True,
    )
    await hass.async_block_till_done()

    # Verify the state changed to on
    state = hass.states.get(entity_id)
    assert state is not None, f"State for {entity_id} is None after update"
    assert state.state == STATE_ON, f"Expected {entity_id} to be on, was {state.state}"


@pytest.mark.asyncio
async def test_switch_turn_off(
    hass: HomeAssistant,
    setup_integration: MockConfigEntry,
    mock_api_client: AsyncMock,
) -> None:
    """Test turning the switch off."""
    # Setup test data
    charger = create_mock_charger(charging=True)
    serial_number = charger["serial_number"]
    entity_id = f"{SWITCH_DOMAIN}.charger_{serial_number.lower()}"

    # Configure mock API client with proper data structure
    mock_api_client.async_get_data.return_value = {"chargers": [charger]}

    # Let HA settle
    await hass.async_block_till_done()

    # Verify initial state is on
    state = hass.states.get(entity_id)
    assert state is not None, f"State for {entity_id} is None"
    assert state.state == STATE_ON, f"Expected {entity_id} to be on, was {state.state}"
    assert state.attributes.get("icon") == SWITCH_ICON

    # Test turning off
    mock_api_client.async_stop_charging.reset_mock()
    await hass.services.async_call(
        SWITCH_DOMAIN,
        SERVICE_TURN_OFF,
        {ATTR_ENTITY_ID: entity_id},
        blocking=True,
    )

    # Verify the API was called with the correct parameters
    mock_api_client.async_stop_charging.assert_called_once()
    args, _ = mock_api_client.async_stop_charging.call_args
    assert (
        args[0] == serial_number
    ), f"Expected serial number {serial_number}, got {args[0]}"

    # Update the mock to reflect the state change
    updated_charger = {**charger, "charging": False}
    mock_api_client.async_get_data.return_value = {"chargers": [updated_charger]}

    # Trigger state refresh
    await hass.services.async_call(
        "homeassistant",
        "update_entity",
        {ATTR_ENTITY_ID: entity_id},
        blocking=True,
    )
    await hass.async_block_till_done()

    # Verify the state changed to off
    state = hass.states.get(entity_id)
    assert state is not None, f"State for {entity_id} is None after update"
    assert (
        state.state == STATE_OFF
    ), f"Expected {entity_id} to be off, was {state.state}"


@pytest.mark.asyncio
async def test_switch_unavailable(
    hass: HomeAssistant,
    setup_integration: MockConfigEntry,
    mock_api_client: AsyncMock,
) -> None:
    """Test switch becomes unavailable when charger is offline."""
    # Setup test data
    charger = create_mock_charger(connected=False)
    serial_number = charger["serial_number"]
    entity_id = f"{SWITCH_DOMAIN}.charger_{serial_number.lower()}"

    # Configure mock API client with proper data structure
    mock_api_client.async_get_data.return_value = {"chargers": [charger]}

    # Let HA settle
    await hass.async_block_till_done()

    # Verify initial state is unavailable
    state = hass.states.get(entity_id)
    assert state is not None, f"State for {entity_id} is None"
    assert (
        state.state == STATE_UNAVAILABLE
    ), f"Expected {entity_id} to be unavailable, was {state.state}"
    assert state.attributes.get("icon") == SWITCH_ICON

    # Test that turning on/off doesn't call the API when offline
    mock_api_client.async_start_charging.reset_mock()
    mock_api_client.async_stop_charging.reset_mock()

    # Try to turn on (should not call the API)
    await hass.services.async_call(
        SWITCH_DOMAIN,
        SERVICE_TURN_ON,
        {ATTR_ENTITY_ID: entity_id},
        blocking=True,
    )
    mock_api_client.async_start_charging.assert_not_called()

    # Try to turn off (should not call the API)
    await hass.services.async_call(
        SWITCH_DOMAIN,
        SERVICE_TURN_OFF,
        {ATTR_ENTITY_ID: entity_id},
        blocking=True,
    )
    mock_api_client.async_stop_charging.assert_not_called()


@pytest.mark.asyncio
async def test_multiple_chargers(
    hass: HomeAssistant,
    setup_integration: MockConfigEntry,
    mock_api_client: AsyncMock,
) -> None:
    """Test multiple chargers are handled correctly."""
    # Setup test data with multiple chargers
    charger1 = create_mock_charger(charging=True, serial_number="CHARGER1")
    charger2 = create_mock_charger(charging=False, serial_number="CHARGER2")

    # Configure mock API client with proper data structure
    mock_api_client.async_get_data.return_value = {"chargers": [charger1, charger2]}

    # Let HA settle
    await hass.async_block_till_done()

    # Get entity IDs
    entity_id1 = f"{SWITCH_DOMAIN}.charger_{charger1['serial_number'].lower()}"
    entity_id2 = f"{SWITCH_DOMAIN}.charger_{charger2['serial_number'].lower()}"

    # Verify initial states
    state1 = hass.states.get(entity_id1)
    state2 = hass.states.get(entity_id2)

    assert state1 is not None, f"State for {entity_id1} is None"
    assert state2 is not None, f"State for {entity_id2} is None"
    assert (
        state1.state == STATE_ON
    ), f"Expected {entity_id1} to be on, was {state1.state}"
    assert (
        state2.state == STATE_OFF
    ), f"Expected {entity_id2} to be off, was {state2.state}"
    assert state1.attributes.get("icon") == SWITCH_ICON
    assert state2.attributes.get("icon") == SWITCH_ICON

    # Test controlling one of the chargers
    charger_to_test = charger2  # The second charger that's off
    entity_id = f"{SWITCH_DOMAIN}.charger_{charger_to_test['serial_number'].lower()}"

    # Turn it on
    mock_api_client.async_start_charging.reset_mock()
    await hass.services.async_call(
        SWITCH_DOMAIN,
        SERVICE_TURN_ON,
        {ATTR_ENTITY_ID: entity_id},
        blocking=True,
    )

    # Verify the API was called with the correct parameters
    mock_api_client.async_start_charging.assert_called_once()
    args, _ = mock_api_client.async_start_charging.call_args
    assert (
        args[0] == charger_to_test["serial_number"]
    ), f"Expected serial number {charger_to_test['serial_number']}, got {args[0]}"

    # Update the mock to reflect the state change for both chargers
    updated_charger1 = {**charger1, "charging": True}
    updated_charger2 = {**charger2, "charging": True}
    mock_api_client.async_get_data.return_value = {
        "chargers": [updated_charger1, updated_charger2]
    }

    # Trigger state refresh
    await hass.services.async_call(
        "homeassistant",
        "update_entity",
        {ATTR_ENTITY_ID: entity_id},
        blocking=True,
    )
    await hass.async_block_till_done()

    # Verify the state changed to on
    state = hass.states.get(entity_id)
    assert state is not None, f"State for {entity_id} is None after update"
    assert state.state == STATE_ON, f"Expected {entity_id} to be on, was {state.state}"
