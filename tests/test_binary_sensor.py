"""Test NexBlue binary sensors."""

import pytest

from custom_components.nexblue_hass.binary_sensor import (
    BINARY_SENSOR_TYPES,
    NexBlueBinarySensor,
    async_setup_entry,
)
from custom_components.nexblue_hass.const import DOMAIN


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
                        "status": {
                            "charging_state": 0,  # idle
                            "cable_lock_mode": 1,  # always_locked
                            "model": "EV Charger Model X",
                            "firmware_version": "1.0.0",
                        },
                    }
                ]
            }

    return MockCoordinator()


@pytest.fixture
def mock_config_entry():
    """Mock config entry."""

    class MockConfigEntry:
        def __init__(self):
            self.entry_id = "test_entry"

    return MockConfigEntry()


@pytest.mark.asyncio
async def test_binary_sensor_setup_entry(mock_coordinator, mock_config_entry):
    """Test binary sensor setup entry."""
    # Create a mock hass object with data (simple dict approach)
    mock_hass = type("MockHass", (), {})()
    mock_hass.data = {DOMAIN: {mock_config_entry.entry_id: mock_coordinator}}

    entities_added = []

    def mock_async_add_entities(entities):
        entities_added.extend(entities)

    await async_setup_entry(mock_hass, mock_config_entry, mock_async_add_entities)

    # Should create 4 binary sensors for 1 charger (added cable lock sensor)
    assert len(entities_added) == 4
    assert all(isinstance(entity, NexBlueBinarySensor) for entity in entities_added)

    # Check that all sensor types are represented
    keys = [entity.entity_description.key for entity in entities_added]
    assert "charging" in keys
    assert "vehicle_connected" in keys
    assert "error" in keys
    assert "cable_locked" in keys


@pytest.mark.asyncio
async def test_binary_sensor_setup_entry_no_chargers(
    mock_coordinator, mock_config_entry
):
    """Test binary sensor setup entry with no chargers."""
    # Create mock coordinator with no chargers
    mock_coordinator.data = {}

    # Create a mock hass object with data (simple dict approach)
    mock_hass = type("MockHass", (), {})()
    mock_hass.data = {DOMAIN: {mock_config_entry.entry_id: mock_coordinator}}

    entities_added = []

    def mock_async_add_entities(entities):
        entities_added.extend(entities)

    await async_setup_entry(mock_hass, mock_config_entry, mock_async_add_entities)

    # Should create no entities when no chargers
    assert len(entities_added) == 0


def test_binary_sensor_charging_idle(mock_coordinator, mock_config_entry):
    """Test charging binary sensor when idle."""
    description = BINARY_SENSOR_TYPES[0]  # charging sensor
    sensor = NexBlueBinarySensor(
        mock_coordinator, mock_config_entry, "test123", description
    )

    # Test idle state (charging_state = 0)
    assert sensor.is_on is False
    assert sensor.unique_id == "test_entry_test123_charging"
    assert sensor.name == "NexBlue test123 Charging"


def test_binary_sensor_charging_active(mock_coordinator, mock_config_entry):
    """Test charging binary sensor when charging."""
    description = BINARY_SENSOR_TYPES[0]  # charging sensor
    # Set charging state to active
    mock_coordinator.data["chargers"][0]["status"]["charging_state"] = 2
    sensor = NexBlueBinarySensor(
        mock_coordinator, mock_config_entry, "test123", description
    )

    # Test charging state (charging_state = 2)
    assert sensor.is_on is True


def test_binary_sensor_vehicle_connected_disconnected(
    mock_coordinator, mock_config_entry
):
    """Test vehicle connected binary sensor when disconnected."""
    description = BINARY_SENSOR_TYPES[1]  # vehicle_connected sensor
    sensor = NexBlueBinarySensor(
        mock_coordinator, mock_config_entry, "test123", description
    )

    # Test disconnected state (charging_state = 0)
    assert sensor.is_on is False
    assert sensor.unique_id == "test_entry_test123_vehicle_connected"
    assert sensor.name == "NexBlue test123 Vehicle Connected"


def test_binary_sensor_vehicle_connected_states(mock_coordinator, mock_config_entry):
    """Test vehicle connected binary sensor with various connected states."""
    description = BINARY_SENSOR_TYPES[1]  # vehicle_connected sensor

    # Test all connected states (1, 2, 3, 5, 6, 7)
    connected_states = [1, 2, 3, 5, 6, 7]
    for state in connected_states:
        mock_coordinator.data["chargers"][0]["status"]["charging_state"] = state
        sensor = NexBlueBinarySensor(
            mock_coordinator, mock_config_entry, "test123", description
        )
        assert sensor.is_on is True, f"State {state} should be connected"


def test_binary_sensor_vehicle_connected_error(mock_coordinator, mock_config_entry):
    """Test vehicle connected binary sensor when in error state."""
    description = BINARY_SENSOR_TYPES[1]  # vehicle_connected sensor
    # Set error state
    mock_coordinator.data["chargers"][0]["status"]["charging_state"] = 4
    sensor = NexBlueBinarySensor(
        mock_coordinator, mock_config_entry, "test123", description
    )

    # Test error state (charging_state = 4) - should be disconnected
    assert sensor.is_on is False


def test_binary_sensor_error_no_error(mock_coordinator, mock_config_entry):
    """Test error binary sensor when no error."""
    description = BINARY_SENSOR_TYPES[2]  # error sensor
    sensor = NexBlueBinarySensor(
        mock_coordinator, mock_config_entry, "test123", description
    )

    # Test no error state (charging_state = 0)
    assert sensor.is_on is False
    assert sensor.unique_id == "test_entry_test123_error"
    assert sensor.name == "NexBlue test123 Error"


def test_binary_sensor_error_active(mock_coordinator, mock_config_entry):
    """Test error binary sensor when in error state."""
    description = BINARY_SENSOR_TYPES[2]  # error sensor
    # Set error state
    mock_coordinator.data["chargers"][0]["status"]["charging_state"] = 4
    sensor = NexBlueBinarySensor(
        mock_coordinator, mock_config_entry, "test123", description
    )

    # Test error state (charging_state = 4)
    assert sensor.is_on is True


def test_binary_sensor_get_charger_name(mock_coordinator, mock_config_entry):
    """Test _get_charger_name method."""
    description = BINARY_SENSOR_TYPES[0]
    sensor = NexBlueBinarySensor(
        mock_coordinator, mock_config_entry, "test123", description
    )

    name = sensor._get_charger_name()
    assert name == "NexBlue test123"


def test_binary_sensor_get_charger_data_found(mock_coordinator, mock_config_entry):
    """Test _get_charger_data method when charger is found."""
    description = BINARY_SENSOR_TYPES[0]
    sensor = NexBlueBinarySensor(
        mock_coordinator, mock_config_entry, "test123", description
    )

    data = sensor._get_charger_data()
    assert data == mock_coordinator.data["chargers"][0]
    assert data["serial_number"] == "test123"


def test_binary_sensor_get_charger_data_not_found(mock_coordinator, mock_config_entry):
    """Test _get_charger_data method when charger is not found."""
    description = BINARY_SENSOR_TYPES[0]
    sensor = NexBlueBinarySensor(
        mock_coordinator, mock_config_entry, "nonexistent", description
    )

    data = sensor._get_charger_data()
    assert data == {}


def test_binary_sensor_device_info(mock_coordinator, mock_config_entry):
    """Test device_info property."""
    description = BINARY_SENSOR_TYPES[0]
    sensor = NexBlueBinarySensor(
        mock_coordinator, mock_config_entry, "test123", description
    )

    device_info = sensor.device_info
    assert "identifiers" in device_info
    assert device_info["identifiers"] == {(DOMAIN, "test123")}
    assert "name" in device_info
    assert device_info["name"] == "NexBlue test123"
    assert device_info["manufacturer"] == "NexBlue"
    assert device_info["model"] == "EV Charger"  # Default value from get() method
    assert (
        device_info["sw_version"] is None
    )  # firmware_version is in status, not at top level


def test_binary_sensor_is_on_no_data(mock_coordinator, mock_config_entry):
    """Test is_on property when no charger data is available."""
    description = BINARY_SENSOR_TYPES[0]
    # Create sensor with nonexistent charger
    sensor = NexBlueBinarySensor(
        mock_coordinator, mock_config_entry, "nonexistent", description
    )

    # Should return False when no data available
    assert sensor.is_on is False


def test_binary_sensor_extra_state_attributes(mock_coordinator, mock_config_entry):
    """Test extra state attributes property."""
    description = BINARY_SENSOR_TYPES[0]
    sensor = NexBlueBinarySensor(
        mock_coordinator, mock_config_entry, "test123", description
    )

    attrs = sensor.extra_state_attributes
    assert "attribution" in attrs
    assert "integration" in attrs
    assert attrs["integration"] == DOMAIN


def test_binary_sensor_types_count():
    """Test that we have the expected number of binary sensor types."""
    assert len(BINARY_SENSOR_TYPES) == 4  # Added cable lock binary sensor


def test_binary_sensor_types_structure():
    """Test the structure of BINARY_SENSOR_TYPES."""
    for description in BINARY_SENSOR_TYPES:
        assert hasattr(description, "key")
        assert hasattr(description, "name")
        assert hasattr(description, "device_class")
        assert hasattr(description, "is_on_fn")
        assert callable(description.is_on_fn)


def test_binary_sensor_charging_states_comprehensive(
    mock_coordinator, mock_config_entry
):
    """Test charging binary sensor with all possible states."""
    description = BINARY_SENSOR_TYPES[0]  # charging sensor

    # Test all possible charging states
    state_results = {
        0: False,  # idle
        1: False,  # connected
        2: True,  # charging
        3: False,  # load balancing
        4: False,  # error
        5: False,  # delayed
        6: False,  # EV waiting
        7: False,  # other
    }

    for state, expected in state_results.items():
        mock_coordinator.data["chargers"][0]["status"]["charging_state"] = state
        sensor = NexBlueBinarySensor(
            mock_coordinator, mock_config_entry, "test123", description
        )
        assert sensor.is_on is expected, f"Charging state {state} should be {expected}"


def test_cable_locked_binary_sensor(mock_coordinator, mock_config_entry):
    """Test cable locked binary sensor."""
    # Find the cable locked binary sensor
    cable_locked_sensor = None
    for description in BINARY_SENSOR_TYPES:
        if description.key == "cable_locked":
            cable_locked_sensor = NexBlueBinarySensor(
                mock_coordinator, mock_config_entry, "test123", description
            )
            break

    assert cable_locked_sensor is not None
    assert cable_locked_sensor.name == "NexBlue test123 Cable Locked"
    assert cable_locked_sensor.unique_id == "test_entry_test123_cable_locked"
    assert cable_locked_sensor.is_on is True  # cable_lock_mode = 1 (always_locked)


def test_cable_locked_binary_sensor_unlocked(mock_coordinator, mock_config_entry):
    """Test cable locked binary sensor when unlocked."""
    # Set cable lock mode to 0 (lock_while_charging)
    mock_coordinator.data["chargers"][0]["status"]["cable_lock_mode"] = 0

    cable_locked_sensor = None
    for description in BINARY_SENSOR_TYPES:
        if description.key == "cable_locked":
            cable_locked_sensor = NexBlueBinarySensor(
                mock_coordinator, mock_config_entry, "test123", description
            )
            break

    assert cable_locked_sensor.is_on is False  # cable_lock_mode = 0 (not always_locked)


def test_cable_locked_binary_sensor_no_status(mock_coordinator, mock_config_entry):
    """Test cable locked binary sensor when no status data is available."""
    # Remove status from charger data
    mock_coordinator.data["chargers"][0].pop("status")

    cable_locked_sensor = None
    for description in BINARY_SENSOR_TYPES:
        if description.key == "cable_locked":
            cable_locked_sensor = NexBlueBinarySensor(
                mock_coordinator, mock_config_entry, "test123", description
            )
            break

    assert cable_locked_sensor.is_on is False  # Default to False when no data


def test_cable_locked_binary_sensor_unknown_mode(mock_coordinator, mock_config_entry):
    """Test cable locked binary sensor with unknown mode."""
    # Set cable lock mode to unknown value
    mock_coordinator.data["chargers"][0]["status"]["cable_lock_mode"] = 99

    cable_locked_sensor = None
    for description in BINARY_SENSOR_TYPES:
        if description.key == "cable_locked":
            cable_locked_sensor = NexBlueBinarySensor(
                mock_coordinator, mock_config_entry, "test123", description
            )
            break

    assert cable_locked_sensor.is_on is False  # Only True for mode 1 (always_locked)
