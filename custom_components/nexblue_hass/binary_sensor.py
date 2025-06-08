"""Binary sensor platform for NexBlue EV Chargers."""

from __future__ import annotations

from dataclasses import dataclass
from typing import Any
from typing import Callable

from homeassistant.components.binary_sensor import BinarySensorDeviceClass
from homeassistant.components.binary_sensor import BinarySensorEntity
from homeassistant.components.binary_sensor import BinarySensorEntityDescription
from homeassistant.config_entries import ConfigEntry
from homeassistant.core import HomeAssistant
from homeassistant.helpers.entity import DeviceInfo
from homeassistant.helpers.entity import EntityCategory
from homeassistant.helpers.entity_platform import AddEntitiesCallback

from .const import DOMAIN
from .entity import NexBlueEntity


@dataclass
class NexBlueBinarySensorEntityDescription(BinarySensorEntityDescription):
    """Class describing NexBlue binary sensor entities."""

    is_on_fn: Callable[[dict], bool] = None


BINARY_SENSOR_TYPES: tuple[NexBlueBinarySensorEntityDescription, ...] = (
    NexBlueBinarySensorEntityDescription(
        key="connected",
        name="Connected",
        device_class=BinarySensorDeviceClass.CONNECTIVITY,
        entity_category=EntityCategory.DIAGNOSTIC,
        is_on_fn=lambda data: data.get("status", {}).get("connected", False),
    ),
    NexBlueBinarySensorEntityDescription(
        key="vehicle_connected",
        name="Vehicle Connected",
        device_class=BinarySensorDeviceClass.PLUG,
        is_on_fn=lambda data: data.get("status", {}).get("vehicle_connected", False),
    ),
    NexBlueBinarySensorEntityDescription(
        key="charging",
        name="Charging",
        device_class=BinarySensorDeviceClass.BATTERY_CHARGING,
        is_on_fn=lambda data: data.get("status", {}).get("charging_state") == 2,
    ),
    NexBlueBinarySensorEntityDescription(
        key="error",
        name="Error",
        device_class=BinarySensorDeviceClass.PROBLEM,
        entity_category=EntityCategory.DIAGNOSTIC,
        is_on_fn=lambda data: data.get("status", {}).get("error_state", False),
    ),
)


async def async_setup_entry(
    hass: HomeAssistant, entry: ConfigEntry, async_add_entities: AddEntitiesCallback
) -> None:
    """Set up NexBlue binary sensors based on config entry."""
    coordinator = hass.data[DOMAIN][entry.entry_id]

    entities = []

    # Check if we have any chargers in the data
    if "chargers" in coordinator.data:
        for charger in coordinator.data["chargers"]:
            charger_serial = charger["serial_number"]
            for description in BINARY_SENSOR_TYPES:
                entities.append(
                    NexBlueBinarySensor(
                        coordinator=coordinator,
                        config_entry=entry,
                        charger_serial=charger_serial,
                        description=description,
                    )
                )

    if entities:
        async_add_entities(entities)


class NexBlueBinarySensor(NexBlueEntity, BinarySensorEntity):
    """NexBlue binary sensor class."""

    def __init__(self, coordinator, config_entry, charger_serial, description):
        """Initialize the binary sensor."""
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
    def is_on(self) -> bool:
        """Return true if the binary sensor is on."""
        charger_data = self._get_charger_data()
        if not charger_data:
            return False

        if self.entity_description.is_on_fn:
            return self.entity_description.is_on_fn(charger_data)
