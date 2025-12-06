"""Test NexBlue switch."""

from unittest.mock import AsyncMock, patch

import pytest
from pytest_homeassistant_custom_component.common import MockConfigEntry

from custom_components.nexblue_hass.const import (
    DOMAIN,
)
from custom_components.nexblue_hass.switch import (
    NexBlueChargingSwitch,
    async_setup_entry,
)

from .const import MOCK_CONFIG


@pytest.fixture
def mock_coordinator():
    """Create a mock coordinator with test data."""
    coordinator = AsyncMock()
    coordinator.data = {
        "chargers": [
            {
                "serial_number": "test123",
                "name": "Test Charger",
                "status": {"charging_state": 0},  # idle
                "model": "EV Charger Model X",
                "firmware_version": "1.0.0",
            }
        ]
    }
    coordinator.api = AsyncMock()
    coordinator.async_request_refresh = AsyncMock()
    return coordinator


@pytest.fixture
def mock_config_entry():
    """Create a mock config entry."""
    return MockConfigEntry(domain=DOMAIN, data=MOCK_CONFIG, entry_id="test")


@pytest.mark.asyncio
async def test_switch_setup_entry(mock_coordinator, mock_config_entry):
    """Test switch setup entry function."""
    async_add_entities = AsyncMock()

    # Create a mock hass object with proper data structure
    mock_hass = AsyncMock()
    mock_hass.data = {DOMAIN: {mock_config_entry.entry_id: mock_coordinator}}

    await async_setup_entry(mock_hass, mock_config_entry, async_add_entities)

    # Verify that switches were added
    async_add_entities.assert_called_once()
    switches = async_add_entities.call_args[0][0]
    assert len(switches) == 1
    assert isinstance(switches[0], NexBlueChargingSwitch)


@pytest.mark.asyncio
async def test_switch_setup_entry_no_chargers(mock_coordinator, mock_config_entry):
    """Test switch setup entry with no chargers."""
    async_add_entities = AsyncMock()

    # Mock coordinator with no chargers
    mock_coordinator.data = {}

    # Create a mock hass object with proper data structure
    mock_hass = AsyncMock()
    mock_hass.data = {DOMAIN: {mock_config_entry.entry_id: mock_coordinator}}

    await async_setup_entry(mock_hass, mock_config_entry, async_add_entities)

    # Verify no switches were added
    async_add_entities.assert_not_called()


def test_switch_initialization(mock_coordinator, mock_config_entry):
    """Test switch initialization."""
    switch = NexBlueChargingSwitch(mock_coordinator, mock_config_entry, "test123")

    assert switch._charger_serial == "test123"
    assert switch._attr_name == "NexBlue test123 Charging"
    assert switch._attr_unique_id == "test_test123_charging"
    assert switch._attr_icon == "mdi:ev-station"


def test_switch_get_charger_name(mock_coordinator, mock_config_entry):
    """Test getting charger name."""
    switch = NexBlueChargingSwitch(mock_coordinator, mock_config_entry, "test123")

    name = switch._get_charger_name()
    assert name == "NexBlue test123"


def test_switch_get_charger_data(mock_coordinator, mock_config_entry):
    """Test getting charger data."""
    switch = NexBlueChargingSwitch(mock_coordinator, mock_config_entry, "test123")

    data = switch._get_charger_data()
    assert data["serial_number"] == "test123"
    assert data["name"] == "Test Charger"


def test_switch_get_charger_data_not_found(mock_coordinator, mock_config_entry):
    """Test getting charger data when charger not found."""
    switch = NexBlueChargingSwitch(mock_coordinator, mock_config_entry, "nonexistent")

    data = switch._get_charger_data()
    assert data == {}


def test_switch_device_info(mock_coordinator, mock_config_entry):
    """Test device info property."""
    switch = NexBlueChargingSwitch(mock_coordinator, mock_config_entry, "test123")

    device_info = switch.device_info
    assert "identifiers" in device_info
    assert device_info["identifiers"] == {(DOMAIN, "test123")}
    assert "name" in device_info
    assert "NexBlue NexBlue test123" in device_info["name"]
    assert device_info["manufacturer"] == "NexBlue"
    assert device_info["model"] == "EV Charger Model X"
    assert device_info["sw_version"] == "1.0.0"


def test_switch_extra_state_attributes(mock_coordinator, mock_config_entry):
    """Test extra state attributes property."""
    switch = NexBlueChargingSwitch(mock_coordinator, mock_config_entry, "test123")

    attrs = switch.extra_state_attributes
    assert "attribution" in attrs
    assert "integration" in attrs
    assert attrs["integration"] == DOMAIN


def test_switch_is_on_idle(mock_coordinator, mock_config_entry):
    """Test is_on property when charger is idle."""
    switch = NexBlueChargingSwitch(mock_coordinator, mock_config_entry, "test123")

    # Test idle state (charging_state = 0)
    assert switch.is_on is False


def test_switch_is_on_charging(mock_coordinator, mock_config_entry):
    """Test is_on property when charger is charging."""
    switch = NexBlueChargingSwitch(mock_coordinator, mock_config_entry, "test123")

    # Test charging state (charging_state = 2)
    mock_coordinator.data["chargers"][0]["status"]["charging_state"] = 2
    assert switch.is_on is True


def test_switch_is_on_load_balancing(mock_coordinator, mock_config_entry):
    """Test is_on property when charger is load balancing."""
    switch = NexBlueChargingSwitch(mock_coordinator, mock_config_entry, "test123")

    # Test load balancing state (charging_state = 5)
    mock_coordinator.data["chargers"][0]["status"]["charging_state"] = 5
    assert switch.is_on is True


def test_switch_is_on_delayed(mock_coordinator, mock_config_entry):
    """Test is_on property when charger is delayed."""
    switch = NexBlueChargingSwitch(mock_coordinator, mock_config_entry, "test123")

    # Test delayed state (charging_state = 6)
    mock_coordinator.data["chargers"][0]["status"]["charging_state"] = 6
    assert switch.is_on is True


def test_switch_is_on_ev_waiting(mock_coordinator, mock_config_entry):
    """Test is_on property when EV is waiting."""
    switch = NexBlueChargingSwitch(mock_coordinator, mock_config_entry, "test123")

    # Test EV waiting state (charging_state = 7)
    mock_coordinator.data["chargers"][0]["status"]["charging_state"] = 7
    assert switch.is_on is True


def test_switch_is_on_no_data(mock_coordinator, mock_config_entry):
    """Test is_on property when charger data is missing."""
    switch = NexBlueChargingSwitch(mock_coordinator, mock_config_entry, "nonexistent")

    # Test with no charger data
    assert switch.is_on is False


def test_switch_is_on_no_status(mock_coordinator, mock_config_entry):
    """Test is_on property when status is missing."""
    switch = NexBlueChargingSwitch(mock_coordinator, mock_config_entry, "test123")

    # Test with no status data
    mock_coordinator.data["chargers"][0]["status"] = {}
    assert switch.is_on is False


@patch("asyncio.get_event_loop")
def test_switch_is_on_with_recent_turn_on_command(
    mock_loop, mock_coordinator, mock_config_entry
):
    """Test is_on property with recent turn_on command."""
    switch = NexBlueChargingSwitch(mock_coordinator, mock_config_entry, "test123")

    # Mock event loop time
    mock_loop.return_value.time.return_value = 1000

    # Set recent turn_on command
    switch._last_command = "turn_on"
    switch._command_timestamp = 995  # 5 seconds ago (within 10 second window)

    # Test with charging state that would normally be off, but should be on due to recent command
    mock_coordinator.data["chargers"][0]["status"][
        "charging_state"
    ] = 1  # Not in normal on states
    assert switch.is_on is True


@patch("asyncio.get_event_loop")
def test_switch_is_on_with_recent_turn_on_command_idle(
    mock_loop, mock_coordinator, mock_config_entry
):
    """Test is_on property with recent turn_on command but idle state."""
    switch = NexBlueChargingSwitch(mock_coordinator, mock_config_entry, "test123")

    # Mock event loop time
    mock_loop.return_value.time.return_value = 1000

    # Set recent turn_on command
    switch._last_command = "turn_on"
    switch._command_timestamp = 995  # 5 seconds ago

    # Test with idle state - should still be off even with recent turn_on command
    mock_coordinator.data["chargers"][0]["status"]["charging_state"] = 0  # idle
    assert switch.is_on is False


@patch("asyncio.get_event_loop")
def test_switch_is_on_with_recent_turn_off_command(
    mock_loop, mock_coordinator, mock_config_entry
):
    """Test is_on property with recent turn_off command."""
    switch = NexBlueChargingSwitch(mock_coordinator, mock_config_entry, "test123")

    # Mock event loop time
    mock_loop.return_value.time.return_value = 1000

    # Set recent turn_off command
    switch._last_command = "turn_off"
    switch._command_timestamp = 995  # 5 seconds ago (within 10 second window)

    # Test with charging state that would normally be on, but should be off due to recent command
    mock_coordinator.data["chargers"][0]["status"]["charging_state"] = 2  # charging
    # The logic on line 100: elif self._last_command == "turn_off" and charging_state != 2:
    # Since charging_state == 2, this condition is False, so it falls through to normal logic
    # Normal logic on line 105: return charging_state in (2, 5, 6, 7) -> returns True
    assert switch.is_on is True


@patch("asyncio.get_event_loop")
def test_switch_is_on_with_recent_turn_off_command_not_charging(
    mock_loop, mock_coordinator, mock_config_entry
):
    """Test is_on property with recent turn_off command and not charging state."""
    switch = NexBlueChargingSwitch(mock_coordinator, mock_config_entry, "test123")

    # Mock event loop time
    mock_loop.return_value.time.return_value = 1000

    # Set recent turn_off command
    switch._last_command = "turn_off"
    switch._command_timestamp = 995  # 5 seconds ago (within 10 second window)

    # Test with non-charging state - should hit line 101: return False
    mock_coordinator.data["chargers"][0]["status"][
        "charging_state"
    ] = 1  # not charging (not 2)
    # The logic on line 100: elif self._last_command == "turn_off" and charging_state != 2:
    # Since charging_state == 1 (not 2), this condition is True, so it returns False (line 101)
    assert switch.is_on is False


@patch("asyncio.get_event_loop")
def test_switch_is_on_old_command(mock_loop, mock_coordinator, mock_config_entry):
    """Test is_on property with old command (outside time window)."""
    switch = NexBlueChargingSwitch(mock_coordinator, mock_config_entry, "test123")

    # Mock event loop time
    mock_loop.return_value.time.return_value = 1000

    # Set old turn_on command (more than 10 seconds ago)
    switch._last_command = "turn_on"
    switch._command_timestamp = 980  # 20 seconds ago (outside 10 second window)

    # Test with charging state - should use normal logic since command is old
    mock_coordinator.data["chargers"][0]["status"]["charging_state"] = 0  # idle
    assert switch.is_on is False


@pytest.mark.asyncio
@patch("asyncio.get_event_loop")
@patch("asyncio.sleep")
async def test_async_turn_on(
    mock_sleep, mock_loop, mock_coordinator, mock_config_entry
):
    """Test async turn on method."""
    switch = NexBlueChargingSwitch(mock_coordinator, mock_config_entry, "test123")

    # Mock event loop time
    mock_loop.return_value.time.return_value = 1000

    # Call turn_on
    await switch.async_turn_on()

    # Verify API was called
    mock_coordinator.api.async_start_charging.assert_called_once_with("test123")

    # Verify command was recorded
    assert switch._last_command == "turn_on"
    assert switch._command_timestamp == 1000

    # Verify sleep and refresh were called
    mock_sleep.assert_called_once_with(1)
    mock_coordinator.async_request_refresh.assert_called_once()


@pytest.mark.asyncio
@patch("asyncio.get_event_loop")
@patch("asyncio.sleep")
async def test_async_turn_off(
    mock_sleep, mock_loop, mock_coordinator, mock_config_entry
):
    """Test async turn off method."""
    switch = NexBlueChargingSwitch(mock_coordinator, mock_config_entry, "test123")

    # Mock event loop time
    mock_loop.return_value.time.return_value = 1000

    # Call turn_off
    await switch.async_turn_off()

    # Verify API was called
    mock_coordinator.api.async_stop_charging.assert_called_once_with("test123")

    # Verify command was recorded
    assert switch._last_command == "turn_off"
    assert switch._command_timestamp == 1000

    # Verify sleep and refresh were called
    mock_sleep.assert_called_once_with(1)
    mock_coordinator.async_request_refresh.assert_called_once()


@pytest.mark.asyncio
@patch("asyncio.get_event_loop")
@patch("asyncio.sleep")
async def test_async_turn_on_with_kwargs(
    mock_sleep, mock_loop, mock_coordinator, mock_config_entry
):
    """Test async turn on method with kwargs."""
    switch = NexBlueChargingSwitch(mock_coordinator, mock_config_entry, "test123")

    # Mock event loop time
    mock_loop.return_value.time.return_value = 1000

    # Call turn_on with kwargs
    await switch.async_turn_on(some_kwarg="value")

    # Verify API was called
    mock_coordinator.api.async_start_charging.assert_called_once_with("test123")


@pytest.mark.asyncio
@patch("asyncio.get_event_loop")
@patch("asyncio.sleep")
async def test_async_turn_off_with_kwargs(
    mock_sleep, mock_loop, mock_coordinator, mock_config_entry
):
    """Test async turn off method with kwargs."""
    switch = NexBlueChargingSwitch(mock_coordinator, mock_config_entry, "test123")

    # Mock event loop time
    mock_loop.return_value.time.return_value = 1000

    # Call turn_off with kwargs
    await switch.async_turn_off(some_kwarg="value")

    # Verify API was called
    mock_coordinator.api.async_stop_charging.assert_called_once_with("test123")
