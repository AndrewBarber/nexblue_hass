"""Sensor platform for NexBlue EV Chargers."""

from __future__ import annotations

from dataclasses import dataclass
from typing import Any

from homeassistant.components.sensor import (
    SensorDeviceClass,
    SensorEntity,
    SensorEntityDescription,
    SensorStateClass,
)
from homeassistant.config_entries import ConfigEntry
from homeassistant.const import UnitOfElectricCurrent, UnitOfEnergy, UnitOfPower
from homeassistant.core import HomeAssistant
from homeassistant.helpers.entity import DeviceInfo, EntityCategory
from homeassistant.helpers.entity_platform import AddEntitiesCallback
from homeassistant.helpers.typing import StateType

from .const import DOMAIN
from .entity import NexBlueEntity


@dataclass
class NexBlueSensorEntityDescription(SensorEntityDescription):
    """Class describing NexBlue sensor entities."""

    value_fn: callable[[dict], StateType] = None


# Mapping of charging state values to human-readable strings
CHARGING_STATE_MAP = {
    0: "Idle",
    1: "Connected",
    2: "Charging",
    3: "Finished",
    4: "Error",
    5: "Load Balancing",
    6: "Delayed",
    7: "EV Waiting",
}

SENSOR_TYPES: tuple[NexBlueSensorEntityDescription, ...] = (
    NexBlueSensorEntityDescription(
        key="charging_state",
        name="Charging State",
        icon="mdi:ev-station",
        value_fn=lambda data: CHARGING_STATE_MAP.get(
            data.get("status", {}).get("charging_state"), "Unknown"
        ),
    ),
    NexBlueSensorEntityDescription(
        key="power",
        name="Power",
        native_unit_of_measurement=UnitOfPower.KILO_WATT,
        device_class=SensorDeviceClass.POWER,
        state_class=SensorStateClass.MEASUREMENT,
        icon="mdi:flash",
        value_fn=lambda data: data.get("status", {}).get("power"),
    ),
    NexBlueSensorEntityDescription(
        key="energy_session",
        name="Energy (Session)",
        native_unit_of_measurement=UnitOfEnergy.KILO_WATT_HOUR,
        device_class=SensorDeviceClass.ENERGY,
        state_class=SensorStateClass.TOTAL_INCREASING,
        icon="mdi:lightning-bolt",
        value_fn=lambda data: data.get("status", {}).get("energy"),
    ),
    NexBlueSensorEntityDescription(
        key="energy_total",
        name="Energy (Total)",
        native_unit_of_measurement=UnitOfEnergy.KILO_WATT_HOUR,
        device_class=SensorDeviceClass.ENERGY,
        state_class=SensorStateClass.TOTAL_INCREASING,
        icon="mdi:lightning-bolt-circle",
        value_fn=lambda data: data.get("status", {}).get("lifetime_energy"),
    ),
    NexBlueSensorEntityDescription(
        key="current_limit",
        name="Current Limit",
        native_unit_of_measurement=UnitOfElectricCurrent.AMPERE,
        device_class=SensorDeviceClass.CURRENT,
        state_class=SensorStateClass.MEASUREMENT,
        entity_category=EntityCategory.DIAGNOSTIC,
        icon="mdi:current-ac",
        value_fn=lambda data: data.get("status", {}).get("current_limit"),
    ),
    NexBlueSensorEntityDescription(
        key="network_status",
        name="Network Status",
        entity_category=EntityCategory.DIAGNOSTIC,
        icon="mdi:wifi",
        value_fn=lambda data: {0: "None", 1: "WiFi", 2: "LTE"}.get(
            data.get("status", {}).get("network_status"), "Unknown"
        ),
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
        self._attr_unique_id = (
            f"{config_entry.entry_id}_{charger_serial}_{description.key}"
        )
        charger_name = self._get_charger_name()
        self._attr_name = f"{charger_name} {description.name}"

    def _get_charger_name(self) -> str:
        """Get the name of the charger."""
        # Just use the serial number for a cleaner name
        return f"NexBlue {self._charger_serial}"

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
            name=f"{self._get_charger_name()}",
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
