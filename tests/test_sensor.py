"""Test NexBlue sensor."""

from unittest.mock import AsyncMock

import pytest
from pytest_homeassistant_custom_component.common import MockConfigEntry

from custom_components.nexblue_hass.const import DOMAIN
from custom_components.nexblue_hass.sensor import (
    CHARGING_STATE_MAP,
    SENSOR_TYPES,
    NexBlueSensor,
    _voltage_from_list,
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
                "status": {
                    "charging_state": 0,
                    "power": 7.5,
                    "energy": 12.3,
                    "lifetime_energy": 1234.5,
                    "current_limit": 16,
                    "network_status": 1,
                    "voltage_list": [230.5, 231.2, 229.8],
                },
                "model": "EV Charger Model X",
                "firmware_version": "1.0.0",
            }
        ]
    }
    return coordinator


@pytest.fixture
def mock_config_entry():
    """Create a mock config entry."""
    return MockConfigEntry(domain=DOMAIN, data=MOCK_CONFIG, entry_id="test")


@pytest.mark.asyncio
async def test_sensor_setup_entry(mock_coordinator, mock_config_entry):
    """Test sensor setup entry function."""
    async_add_entities = AsyncMock()

    # Create a mock hass object with proper data structure
    mock_hass = AsyncMock()
    mock_hass.data = {DOMAIN: {mock_config_entry.entry_id: mock_coordinator}}

    await async_setup_entry(mock_hass, mock_config_entry, async_add_entities)

    # Verify that sensors were added
    async_add_entities.assert_called_once()
    sensors = async_add_entities.call_args[0][0]
    # Should create 9 sensors for 1 charger
    assert len(sensors) == 9
    for sensor in sensors:
        assert isinstance(sensor, NexBlueSensor)


@pytest.mark.asyncio
async def test_sensor_setup_entry_no_chargers(mock_coordinator, mock_config_entry):
    """Test sensor setup entry with no chargers."""
    async_add_entities = AsyncMock()

    # Mock coordinator with no chargers
    mock_coordinator.data = {}

    # Create a mock hass object with proper data structure
    mock_hass = AsyncMock()
    mock_hass.data = {DOMAIN: {mock_config_entry.entry_id: mock_coordinator}}

    await async_setup_entry(mock_hass, mock_config_entry, async_add_entities)

    # Verify no sensors were added
    async_add_entities.assert_not_called()


def test_sensor_initialization(mock_coordinator, mock_config_entry):
    """Test sensor initialization."""
    description = SENSOR_TYPES[0]  # charging_state sensor
    sensor = NexBlueSensor(mock_coordinator, mock_config_entry, "test123", description)

    assert sensor._charger_serial == "test123"
    assert sensor.entity_description == description
    assert sensor._attr_unique_id == "test_test123_charging_state"
    assert sensor._attr_name == "NexBlue test123 Charging State"


def test_sensor_get_charger_name(mock_coordinator, mock_config_entry):
    """Test getting charger name."""
    description = SENSOR_TYPES[0]
    sensor = NexBlueSensor(mock_coordinator, mock_config_entry, "test123", description)

    name = sensor._get_charger_name()
    assert name == "NexBlue test123"


def test_sensor_get_charger_data(mock_coordinator, mock_config_entry):
    """Test getting charger data."""
    description = SENSOR_TYPES[0]
    sensor = NexBlueSensor(mock_coordinator, mock_config_entry, "test123", description)

    data = sensor._get_charger_data()
    assert data["serial_number"] == "test123"
    assert data["name"] == "Test Charger"


def test_sensor_get_charger_data_not_found(mock_coordinator, mock_config_entry):
    """Test getting charger data when charger not found."""
    description = SENSOR_TYPES[0]
    sensor = NexBlueSensor(
        mock_coordinator, mock_config_entry, "nonexistent", description
    )

    data = sensor._get_charger_data()
    assert data == {}


def test_sensor_device_info(mock_coordinator, mock_config_entry):
    """Test device info property."""
    description = SENSOR_TYPES[0]
    sensor = NexBlueSensor(mock_coordinator, mock_config_entry, "test123", description)

    device_info = sensor.device_info
    assert "identifiers" in device_info
    assert device_info["identifiers"] == {(DOMAIN, "test123")}
    assert "name" in device_info
    assert device_info["name"] == "NexBlue test123"
    assert device_info["manufacturer"] == "NexBlue"
    assert device_info["model"] == "EV Charger Model X"
    assert device_info["sw_version"] == "1.0.0"


def test_sensor_native_value_no_data(mock_coordinator, mock_config_entry):
    """Test native_value when no charger data."""
    description = SENSOR_TYPES[0]
    sensor = NexBlueSensor(
        mock_coordinator, mock_config_entry, "nonexistent", description
    )

    value = sensor.native_value
    assert value is None


def test_sensor_charging_state_values(mock_coordinator, mock_config_entry):
    """Test charging state sensor with different values."""
    description = SENSOR_TYPES[0]
    sensor = NexBlueSensor(mock_coordinator, mock_config_entry, "test123", description)

    # Test idle state
    mock_coordinator.data["chargers"][0]["status"]["charging_state"] = 0
    assert sensor.native_value == "Idle"

    # Test charging state
    mock_coordinator.data["chargers"][0]["status"]["charging_state"] = 2
    assert sensor.native_value == "Charging"

    # Test unknown state
    mock_coordinator.data["chargers"][0]["status"]["charging_state"] = 99
    assert sensor.native_value == "Unknown"


def test_sensor_power_value(mock_coordinator, mock_config_entry):
    """Test power sensor value."""
    description = SENSOR_TYPES[1]  # power sensor
    sensor = NexBlueSensor(mock_coordinator, mock_config_entry, "test123", description)

    value = sensor.native_value
    assert value == 7.5


def test_sensor_energy_session_value(mock_coordinator, mock_config_entry):
    """Test energy session sensor value."""
    description = SENSOR_TYPES[2]  # energy_session sensor
    sensor = NexBlueSensor(mock_coordinator, mock_config_entry, "test123", description)

    value = sensor.native_value
    assert value == 12.3


def test_sensor_energy_total_value(mock_coordinator, mock_config_entry):
    """Test energy total sensor value."""
    description = SENSOR_TYPES[3]  # energy_total sensor
    sensor = NexBlueSensor(mock_coordinator, mock_config_entry, "test123", description)

    value = sensor.native_value
    assert value == 1234.5


def test_sensor_current_limit_value(mock_coordinator, mock_config_entry):
    """Test current limit sensor value."""
    description = SENSOR_TYPES[4]  # current_limit sensor
    sensor = NexBlueSensor(mock_coordinator, mock_config_entry, "test123", description)

    value = sensor.native_value
    assert value == 16


def test_sensor_network_status_values(mock_coordinator, mock_config_entry):
    """Test network status sensor with different values."""
    description = SENSOR_TYPES[5]  # network_status sensor
    sensor = NexBlueSensor(mock_coordinator, mock_config_entry, "test123", description)

    # Test WiFi
    mock_coordinator.data["chargers"][0]["status"]["network_status"] = 1
    assert sensor.native_value == "WiFi"

    # Test LTE
    mock_coordinator.data["chargers"][0]["status"]["network_status"] = 2
    assert sensor.native_value == "LTE"

    # Test unknown
    mock_coordinator.data["chargers"][0]["status"]["network_status"] = 99
    assert sensor.native_value == "Unknown"


def test_sensor_voltage_values(mock_coordinator, mock_config_entry):
    """Test voltage sensor values."""
    # Test L1 voltage
    description = SENSOR_TYPES[6]  # voltage_l1 sensor
    sensor = NexBlueSensor(mock_coordinator, mock_config_entry, "test123", description)
    value = sensor.native_value
    assert value == 230.5

    # Test L2 voltage
    description = SENSOR_TYPES[7]  # voltage_l2 sensor
    sensor = NexBlueSensor(mock_coordinator, mock_config_entry, "test123", description)
    value = sensor.native_value
    assert value == 231.2

    # Test L3 voltage
    description = SENSOR_TYPES[8]  # voltage_l3 sensor
    sensor = NexBlueSensor(mock_coordinator, mock_config_entry, "test123", description)
    value = sensor.native_value
    assert value == 229.8


def test_voltage_from_list_valid():
    """Test _voltage_from_list with valid data."""
    data = {"status": {"voltage_list": ["220.5", "230.1", "240.3"]}}

    result = _voltage_from_list(data, 0)
    assert result == 220.5

    result = _voltage_from_list(data, 2)
    assert result == 240.3


def test_voltage_from_list_invalid_index():
    """Test _voltage_from_list with invalid index."""
    data = {"status": {"voltage_list": ["220.5", "230.1"]}}

    result = _voltage_from_list(data, 2)  # Index out of range
    assert result is None


def test_voltage_from_list_no_voltage_list():
    """Test _voltage_from_list with no voltage_list."""
    data = {"status": {}}

    result = _voltage_from_list(data, 0)
    assert result is None


def test_voltage_from_list_not_a_list():
    """Test _voltage_from_list when voltage_list is not a list."""
    data = {"status": {"voltage_list": "not_a_list"}}

    result = _voltage_from_list(data, 0)
    assert result is None


def test_voltage_from_list_invalid_values():
    """Test _voltage_from_list with invalid float values."""
    data = {"status": {"voltage_list": ["220.5", "invalid", None, "230.1"]}}

    result = _voltage_from_list(data, 1)  # Invalid string
    assert result is None

    result = _voltage_from_list(data, 2)  # None value
    assert result is None


def test_charging_state_map():
    """Test CHARGING_STATE_MAP contains all expected values."""
    expected_states = {
        0: "Idle",
        1: "Connected",
        2: "Charging",
        3: "Finished",
        4: "Error",
        5: "Load Balancing",
        6: "Delayed",
        7: "EV Waiting",
    }

    assert CHARGING_STATE_MAP == expected_states


def test_sensor_types_count():
    """Test that SENSOR_TYPES contains expected number of sensors."""
    assert len(SENSOR_TYPES) == 9


def test_sensor_types_structure():
    """Test that all sensor types have required attributes."""
    for sensor_type in SENSOR_TYPES:
        assert hasattr(sensor_type, "key")
        assert hasattr(sensor_type, "name")
        assert hasattr(sensor_type, "value_fn")
        assert callable(sensor_type.value_fn)
