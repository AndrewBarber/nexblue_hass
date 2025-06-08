"""Sensor platform for NexBlue EV Chargers."""
from __future__ import annotations

from dataclasses import dataclass
from typing import Any

from homeassistant.components.sensor import SensorDeviceClass
from homeassistant.components.sensor import SensorEntity
from homeassistant.components.sensor import SensorEntityDescription
from homeassistant.components.sensor import SensorStateClass
from homeassistant.config_entries import ConfigEntry
from homeassistant.const import UnitOfElectricCurrent
from homeassistant.const import UnitOfElectricPotential
from homeassistant.const import UnitOfEnergy
from homeassistant.const import UnitOfPower
from homeassistant.core import HomeAssistant
from homeassistant.helpers.entity import DeviceInfo
from homeassistant.helpers.entity import EntityCategory
from homeassistant.helpers.entity_platform import AddEntitiesCallback
from homeassistant.helpers.typing import StateType

from .const import DOMAIN
from .entity import NexBlueEntity


@dataclass
class NexBlueSensorEntityDescription(SensorEntityDescription):
    """Class describing NexBlue sensor entities."""

    value_fn: callable[[dict], StateType] = None


SENSOR_TYPES: tuple[NexBlueSensorEntityDescription, ...] = (
    NexBlueSensorEntityDescription(
        key="power",
        name="Power",
        native_unit_of_measurement=UnitOfPower.KILO_WATT,
        device_class=SensorDeviceClass.POWER,
        state_class=SensorStateClass.MEASUREMENT,
        icon="mdi:flash",
        value_fn=lambda data: data.get("status", {}).get("power_kw"),
    ),
    NexBlueSensorEntityDescription(
        key="energy_session",
        name="Energy (Session)",
        native_unit_of_measurement=UnitOfEnergy.KILO_WATT_HOUR,
        device_class=SensorDeviceClass.ENERGY,
        state_class=SensorStateClass.TOTAL_INCREASING,
        icon="mdi:lightning-bolt",
        value_fn=lambda data: data.get("status", {}).get("energy_session_kwh"),
    ),
    NexBlueSensorEntityDescription(
        key="energy_total",
        name="Energy (Total)",
        native_unit_of_measurement=UnitOfEnergy.KILO_WATT_HOUR,
        device_class=SensorDeviceClass.ENERGY,
        state_class=SensorStateClass.TOTAL_INCREASING,
        icon="mdi:lightning-bolt-circle",
        value_fn=lambda data: data.get("status", {}).get("energy_total_kwh"),
    ),
    NexBlueSensorEntityDescription(
        key="current",
        name="Current",
        native_unit_of_measurement=UnitOfElectricCurrent.AMPERE,
        device_class=SensorDeviceClass.CURRENT,
        state_class=SensorStateClass.MEASUREMENT,
        icon="mdi:current-ac",
        value_fn=lambda data: data.get("status", {}).get("current_a"),
    ),
    NexBlueSensorEntityDescription(
        key="voltage",
        name="Voltage",
        native_unit_of_measurement=UnitOfElectricPotential.VOLT,
        device_class=SensorDeviceClass.VOLTAGE,
        state_class=SensorStateClass.MEASUREMENT,
        icon="mdi:sine-wave",
        value_fn=lambda data: data.get("status", {}).get("voltage_v"),
    ),
    NexBlueSensorEntityDescription(
        key="status",
        name="Status",
        icon="mdi:information-outline",
        value_fn=lambda data: data.get("status", {}).get("state", "unknown"),
    ),
    NexBlueSensorEntityDescription(
        key="wifi_signal",
        name="WiFi Signal",
        device_class=SensorDeviceClass.SIGNAL_STRENGTH,
        state_class=SensorStateClass.MEASUREMENT,
        entity_category=EntityCategory.DIAGNOSTIC,
        icon="mdi:wifi",
        value_fn=lambda data: data.get("status", {}).get("wifi_signal_strength"),
    ),
)


async def async_setup_entry(
    hass: HomeAssistant, entry: ConfigEntry, async_add_entities: AddEntitiesCallback
) -> None:
    """Set up NexBlue sensors based on config entry."""
    coordinator = hass.data[DOMAIN][entry.entry_id]

    entities = []

    # Check if we have any chargers in the data
    if "chargers" in coordinator.data:
        for charger in coordinator.data["chargers"]:
            charger_serial = charger["serial_number"]
            for description in SENSOR_TYPES:
                entities.append(
                    NexBlueSensor(
                        coordinator=coordinator,
                        config_entry=entry,
                        charger_serial=charger_serial,
                        description=description,
                    )
                )

    if entities:
        async_add_entities(entities)


class NexBlueSensor(NexBlueEntity, SensorEntity):
    """NexBlue sensor class."""

    def __init__(self, coordinator, config_entry, charger_serial, description):
        """Initialize the sensor."""
        super().__init__(coordinator, config_entry)
        self.entity_description = description
        self._charger_serial = charger_serial
        self._attr_unique_id = f"{config_entry.entry_id}_{charger_serial}_{description.key}"
        charger_name = self._get_charger_name()
        self._attr_name = f"{charger_name} {description.name}"

    def _get_charger_name(self) -> str:
        """Get the name of the charger."""
        for charger in self.coordinator.data.get("chargers", []):
            if charger.get("serial_number") == self._charger_serial:
                # Try to get a friendly name, fall back to serial number if not available
                return charger.get("product_name", f"Charger {self._charger_serial}")
        return f"Charger {self._charger_serial}"

    def _get_charger_data(self) -> dict[str, Any]:
        """Get the data for this specific charger."""
        for charger in self.coordinator.data.get("chargers", []):
            if charger.get("serial_number") == self._charger_serial:
                return charger
        return {}

    @property
    def device_info(self) -> DeviceInfo:
        """Return device information about this NexBlue charger."""
        return DeviceInfo(
            identifiers={(DOMAIN, self._charger_serial)},
            name=f"NexBlue {self._get_charger_name()}",
            manufacturer="NexBlue",
            model=self._get_charger_data().get("model", "EV Charger"),
            sw_version=self._get_charger_data().get("firmware_version"),
        )

    @property
    def native_value(self) -> StateType:
        """Return the state of the sensor."""
        charger_data = self._get_charger_data()
        if not charger_data:
            return None

        if self.entity_description.value_fn:
            return self.entity_description.value_fn(charger_data)
