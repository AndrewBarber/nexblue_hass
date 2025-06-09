"""Test the NexBlue binary sensor platform."""
from unittest.mock import AsyncMock, patch

from homeassistant.components.binary_sensor import BinarySensorDeviceClass
from homeassistant.config_entries import ConfigEntry
from homeassistant.core import HomeAssistant
from homeassistant.helpers.entity import EntityCategory
from homeassistant.helpers.entity_platform import AddEntitiesCallback

from custom_components.nexblue_hass.binary_sensor import (
    async_setup_entry,
    NexBlueBinarySensor,
    BINARY_SENSOR_TYPES,
    NexBlueBinarySensorEntityDescription,
)
from custom_components.nexblue_hass.const import DOMAIN


async def test_async_setup_entry(
    hass: HomeAssistant, mock_config_entry: ConfigEntry
) -> None:
    """Test binary sensor setup with mock data."""
    # Setup mock coordinator with test data
    mock_coordinator = AsyncMock()
    mock_coordinator.data = {
        "chargers": [
            {
                "serial_number": "test_charger_1",
                "model": "Test Model",
                "firmware_version": "1.0.0",
                "status": {
                    "charging_state": 2,  # Charging
                },
            }
        ]
    }


    # Mock the async_add_entities callback
    mock_add_entities = AsyncMock()
    
    # Set up the coordinator in hass.data
    hass.data[DOMAIN] = {mock_config_entry.entry_id: mock_coordinator}
    
    # Call the setup function
    await async_setup_entry(hass, mock_config_entry, mock_add_entities)
    
    # Verify entities were added
    assert mock_add_entities.called
    added_entities = mock_add_entities.call_args[0][0]
    assert len(added_entities) == len(BINARY_SENSOR_TYPES)


async def test_async_setup_entry_no_chargers(
    hass: HomeAssistant, mock_config_entry: ConfigEntry
) -> None:
    """Test binary sensor setup with no chargers in data."""
    # Setup mock coordinator with no chargers
    mock_coordinator = AsyncMock()
    mock_coordinator.data = {}

    # Mock the async_add_entities callback
    mock_add_entities = AsyncMock()
    
    # Set up the coordinator in hass.data
    hass.data[DOMAIN] = {mock_config_entry.entry_id: mock_coordinator}
    
    # Call the setup function
    await async_setup_entry(hass, mock_config_entry, mock_add_entities)
    
    # Verify no entities were added
    assert not mock_add_entities.called


async def test_binary_sensor_properties(
    hass: HomeAssistant, mock_config_entry: ConfigEntry
) -> None:
    """Test binary sensor properties and methods."""
    # Setup test data
    test_data = {
        "serial_number": "test_charger_1",
        "model": "Test Model",
        "firmware_version": "1.0.0",
        "status": {
            "charging_state": 2,  # Charging
        },
    }

    # Setup mock coordinator
    mock_coordinator = AsyncMock()
    mock_coordinator.data = {"chargers": [test_data]}

    # Create a sensor for each type
    for description in BINARY_SENSOR_TYPES:
        sensor = NexBlueBinarySensor(
            coordinator=mock_coordinator,
            config_entry=mock_config_entry,
            charger_serial="test_charger_1",
            description=description,
        )

        # Test basic properties
        assert sensor.unique_id == f"{mock_config_entry.entry_id}_test_charger_1_{description.key}"
        assert sensor.name == f"NexBlue test_charger_1 {description.name}"
        
        # Test device info
        device_info = sensor.device_info
        assert device_info["identifiers"] == {(DOMAIN, "test_charger_1")}
        assert device_info["name"] == "NexBlue test_charger_1"
        assert device_info["manufacturer"] == "NexBlue"
        assert device_info["model"] == "Test Model"
        assert device_info["sw_version"] == "1.0.0"


async def test_binary_sensor_states(
    hass: HomeAssistant, mock_config_entry: ConfigEntry
) -> None:
    """Test binary sensor states with different charging states."""
    test_cases = [
        # (charging_state, expected_charging, expected_connected, expected_error)
        (0, False, False, False),  # Idle
        (1, False, True, False),   # Connected, not charging
        (2, True, True, False),    # Charging
        (3, False, True, False),   # Finishing
        (4, False, False, True),   # Error
        (5, False, True, False),   # In queue
        (6, False, True, False),   # Waiting for schedule
        (7, False, True, False),   # Waiting for energy
    ]

    # Setup mock coordinator
    mock_coordinator = AsyncMock()
    
    for charging_state, exp_charging, exp_connected, exp_error in test_cases:
        test_data = {
            "serial_number": "test_charger_1",
            "status": {"charging_state": charging_state},
        }
        mock_coordinator.data = {"chargers": [test_data]}

        # Test each sensor type
        for description in BINARY_SENSOR_TYPES:
            sensor = NexBlueBinarySensor(
                coordinator=mock_coordinator,
                config_entry=mock_config_entry,
                charger_serial="test_charger_1",
                description=description,
            )

            # Test the is_on property
            if description.key == "charging":
                assert sensor.is_on is exp_charging
            elif description.key == "vehicle_connected":
                assert sensor.is_on is exp_connected
            elif description.key == "error":
                assert sensor.is_on is exp_error


async def test_binary_sensor_missing_data(
    hass: HomeAssistant, mock_config_entry: ConfigEntry
) -> None:
    """Test binary sensor with missing or invalid data."""
    # Setup mock coordinator with missing data
    mock_coordinator = AsyncMock()
    mock_coordinator.data = {"chargers": [{"serial_number": "test_charger_1"}]}

    # Test each sensor type
    for description in BINARY_SENSOR_TYPES:
        sensor = NexBlueBinarySensor(
            coordinator=mock_coordinator,
            config_entry=mock_config_entry,
            charger_serial="test_charger_1",
            description=description,
        )
        
        # Should handle missing status gracefully
        assert sensor.is_on is False
        
        # Should handle missing device info gracefully
        device_info = sensor.device_info
        assert device_info["identifiers"] == {(DOMAIN, "test_charger_1")}
        assert device_info["name"] == "NexBlue test_charger_1"
        assert device_info["manufacturer"] == "NexBlue"
        assert device_info["model"] == "EV Charger"  # Default model
        assert device_info["sw_version"] is None


def test_binary_sensor_descriptions() -> None:
    """Test binary sensor entity descriptions."""
    # Verify we have the expected number of sensors
    assert len(BINARY_SENSOR_TYPES) == 3
    
    # Verify each sensor type
    sensor_keys = {sensor.key for sensor in BINARY_SENSOR_TYPES}
    assert "charging" in sensor_keys
    assert "vehicle_connected" in sensor_keys
    assert "error" in sensor_keys
    
    # Verify sensor attributes
    for sensor in BINARY_SENSOR_TYPES:
        if sensor.key == "charging":
            assert sensor.name == "Charging"
            assert sensor.device_class == BinarySensorDeviceClass.BATTERY_CHARGING
        elif sensor.key == "vehicle_connected":
            assert sensor.name == "Vehicle Connected"
            assert sensor.device_class == BinarySensorDeviceClass.PLUG
        elif sensor.key == "error":
            assert sensor.name == "Error"
            assert sensor.device_class == BinarySensorDeviceClass.PROBLEM
            assert sensor.entity_category == EntityCategory.DIAGNOSTIC


async def test_binary_sensor_custom_is_on_fn(
    hass: HomeAssistant, mock_config_entry: ConfigEntry
) -> None:
    """Test binary sensor with a custom is_on function."""
    # Setup test data with a custom is_on function
    test_data = {
        "serial_number": "test_charger_1",
        "custom_field": "special_value"
    }
    
    # Create a custom description with a custom is_on function
    custom_description = NexBlueBinarySensorEntityDescription(
        key="custom_sensor",
        name="Custom Sensor",
        is_on_fn=lambda data: data.get("custom_field") == "special_value"
    )
    
    # Setup mock coordinator
    mock_coordinator = AsyncMock()
    mock_coordinator.data = {"chargers": [test_data]}
    
    # Create the sensor with our custom description
    sensor = NexBlueBinarySensor(
        coordinator=mock_coordinator,
        config_entry=mock_config_entry,
        charger_serial="test_charger_1",
        description=custom_description,
    )
    
    # Test that the custom is_on function works
    assert sensor.is_on is True
    
    # Test with data that doesn't match the condition
    test_data["custom_field"] = "other_value"
    assert sensor.is_on is False
    
    # Test with missing data
    test_data.clear()
    assert sensor.is_on is False


async def test_binary_sensor_empty_chargers(
    hass: HomeAssistant, mock_config_entry: ConfigEntry
) -> None:
    """Test binary sensor behavior when chargers list is empty."""
    # Setup mock coordinator with empty chargers list
    mock_coordinator = AsyncMock()
    mock_coordinator.data = {"chargers": []}
    
    # Create a sensor
    sensor = NexBlueBinarySensor(
        coordinator=mock_coordinator,
        config_entry=mock_config_entry,
        charger_serial="test_charger_1",
        description=BINARY_SENSOR_TYPES[0],  # Use the first sensor type
    )
    
    # Should handle empty chargers list gracefully
    assert sensor._get_charger_data() == {}
    assert sensor.is_on is False
    
    # Device info should still work with default values
    device_info = sensor.device_info
    assert device_info["identifiers"] == {(DOMAIN, "test_charger_1")}
    assert device_info["name"] == "NexBlue test_charger_1"
    assert device_info["manufacturer"] == "NexBlue"
    assert device_info["model"] == "EV Charger"  # Default model
    assert device_info["sw_version"] is None
