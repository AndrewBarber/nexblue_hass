"""Test NexBlue numbers."""

from unittest.mock import AsyncMock

import pytest
from homeassistant.helpers.entity import DeviceInfo
from homeassistant.helpers.typing import StateType

from custom_components.nexblue_hass.const import DOMAIN
from custom_components.nexblue_hass.number import (
    NexBlueCurrentLimitNumber,
    async_setup_entry,
)

from .const import MOCK_CONFIG


@pytest.fixture
def mock_coordinator():
    """Mock coordinator with test data."""
    class MockCoordinator:
        def __init__(self):
            self.data = {
                "chargers": [
                    {
                        "serial_number": "test123",
                        "name": "Test Charger",
                        "model": "EV Charger Model X",
                        "firmware_version": "1.0.0",
                        "status": {
                            "charging_state": 0,
                            "current_limit": 16,
                        },
                    }
                ]
            }
            self.api = AsyncMock()
    
    return MockCoordinator()


@pytest.fixture
def mock_config_entry():
    """Mock config entry."""
    class MockConfigEntry:
        def __init__(self):
            self.entry_id = "test_entry"
            self.data = MOCK_CONFIG
    
    return MockConfigEntry()


@pytest.mark.asyncio
async def test_number_setup_entry(mock_coordinator, mock_config_entry):
    """Test number setup entry function."""
    async_add_entities = AsyncMock()
    
    # Create a mock hass object with proper data structure
    mock_hass = AsyncMock()
    mock_hass.data = {DOMAIN: {mock_config_entry.entry_id: mock_coordinator}}
    
    await async_setup_entry(mock_hass, mock_config_entry, async_add_entities)
    
    # Verify that numbers were added
    async_add_entities.assert_called_once()
    numbers = async_add_entities.call_args[0][0]
    assert len(numbers) == 1
    assert isinstance(numbers[0], NexBlueCurrentLimitNumber)


@pytest.mark.asyncio
async def test_number_setup_entry_no_chargers(mock_coordinator, mock_config_entry):
    """Test number setup entry with no chargers."""
    async_add_entities = AsyncMock()
    
    # Mock coordinator with no chargers
    mock_coordinator.data = {}
    
    # Create a mock hass object with proper data structure
    mock_hass = AsyncMock()
    mock_hass.data = {DOMAIN: {mock_config_entry.entry_id: mock_coordinator}}
    
    await async_setup_entry(mock_hass, mock_config_entry, async_add_entities)
    
    # Verify no numbers were added
    async_add_entities.assert_not_called()


def test_number_init(mock_coordinator, mock_config_entry):
    """Test number initialization."""
    number = NexBlueCurrentLimitNumber(mock_coordinator, mock_config_entry, "test123")
    
    assert number._charger_serial == "test123"
    assert number.native_min_value == 6
    assert number.native_max_value == 32
    assert number.native_step == 1
    assert number.native_unit_of_measurement == "A"
    assert number._attr_unique_id == "test_entry_test123_current_limit"


def test_number_get_charger_name(mock_coordinator, mock_config_entry):
    """Test getting charger name."""
    number = NexBlueCurrentLimitNumber(mock_coordinator, mock_config_entry, "test123")
    
    name = number._get_charger_name()
    assert name == "NexBlue test123"


def test_number_get_charger_data(mock_coordinator, mock_config_entry):
    """Test getting charger data."""
    number = NexBlueCurrentLimitNumber(mock_coordinator, mock_config_entry, "test123")
    
    data = number._get_charger_data()
    assert data["serial_number"] == "test123"
    assert data["name"] == "Test Charger"
    assert data["status"]["current_limit"] == 16


def test_number_get_charger_data_not_found(mock_coordinator, mock_config_entry):
    """Test getting charger data when charger not found."""
    number = NexBlueCurrentLimitNumber(mock_coordinator, mock_config_entry, "nonexistent")
    
    data = number._get_charger_data()
    assert data == {}


def test_number_device_info(mock_coordinator, mock_config_entry):
    """Test device info property."""
    number = NexBlueCurrentLimitNumber(mock_coordinator, mock_config_entry, "test123")
    
    device_info = number.device_info
    assert "identifiers" in device_info
    assert device_info["identifiers"] == {(DOMAIN, "test123")}
    assert device_info["name"] == "NexBlue NexBlue test123"
    assert device_info["manufacturer"] == "NexBlue"
    assert device_info["model"] == "EV Charger Model X"
    assert device_info["sw_version"] == "1.0.0"


def test_number_native_value(mock_coordinator, mock_config_entry):
    """Test native_value property."""
    number = NexBlueCurrentLimitNumber(mock_coordinator, mock_config_entry, "test123")
    
    value = number.native_value
    assert value == 16


def test_number_native_value_no_data(mock_coordinator, mock_config_entry):
    """Test native_value when no charger data."""
    number = NexBlueCurrentLimitNumber(mock_coordinator, mock_config_entry, "nonexistent")
    
    value = number.native_value
    assert value is None


def test_number_native_value_no_status(mock_coordinator, mock_config_entry):
    """Test native_value when no status in charger data."""
    # Remove status from charger data
    mock_coordinator.data["chargers"][0].pop("status")
    
    number = NexBlueCurrentLimitNumber(mock_coordinator, mock_config_entry, "test123")
    
    value = number.native_value
    assert value is None


@pytest.mark.asyncio
async def test_number_set_native_value(mock_coordinator, mock_config_entry):
    """Test setting native value."""
    number = NexBlueCurrentLimitNumber(mock_coordinator, mock_config_entry, "test123")
    
    # Mock successful API call
    mock_coordinator.api.async_set_current_limit.return_value = True
    mock_coordinator.async_request_refresh = AsyncMock()
    
    await number.async_set_native_value(20)
    
    # Verify API was called with correct parameters
    mock_coordinator.api.async_set_current_limit.assert_called_once_with("test123", 20)
    mock_coordinator.async_request_refresh.assert_called_once()


@pytest.mark.asyncio
async def test_number_set_native_value_float(mock_coordinator, mock_config_entry):
    """Test setting native value with float (should convert to int)."""
    number = NexBlueCurrentLimitNumber(mock_coordinator, mock_config_entry, "test123")
    
    # Mock successful API call
    mock_coordinator.api.async_set_current_limit.return_value = True
    mock_coordinator.async_request_refresh = AsyncMock()
    
    await number.async_set_native_value(20.0)
    
    # Verify API was called with int value
    mock_coordinator.api.async_set_current_limit.assert_called_once_with("test123", 20)


@pytest.mark.asyncio
async def test_number_set_native_value_failure(mock_coordinator, mock_config_entry):
    """Test setting native value when API call fails."""
    number = NexBlueCurrentLimitNumber(mock_coordinator, mock_config_entry, "test123")
    
    # Mock failed API call
    mock_coordinator.api.async_set_current_limit.return_value = False
    
    with pytest.raises(ValueError, match="Failed to set current limit"):
        await number.async_set_native_value(20)


@pytest.mark.asyncio
async def test_number_set_native_value_api_exception(mock_coordinator, mock_config_entry):
    """Test setting native value when API raises exception."""
    number = NexBlueCurrentLimitNumber(mock_coordinator, mock_config_entry, "test123")
    
    # Mock API exception
    mock_coordinator.api.async_set_current_limit.side_effect = Exception("API Error")
    
    with pytest.raises(ValueError, match="Failed to set current limit"):
        await number.async_set_native_value(20)


def test_number_properties(mock_coordinator, mock_config_entry):
    """Test number properties."""
    number = NexBlueCurrentLimitNumber(mock_coordinator, mock_config_entry, "test123")
    
    assert number.name == "NexBlue test123 Current Limit"
    assert number.icon == "mdi:current-ac"
    assert number.unique_id == "test_entry_test123_current_limit"


def test_number_current_limit_values(mock_coordinator, mock_config_entry):
    """Test current limit with different values."""
    number = NexBlueCurrentLimitNumber(mock_coordinator, mock_config_entry, "test123")
    
    # Test different current limit values
    test_values = [6, 16, 32]
    for value in test_values:
        mock_coordinator.data["chargers"][0]["status"]["current_limit"] = value
        assert number.native_value == value
