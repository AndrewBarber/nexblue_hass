"""Number platform for NexBlue EV Chargers."""

from __future__ import annotations

from typing import Any

from homeassistant.components.number import NumberEntity
from homeassistant.config_entries import ConfigEntry
from homeassistant.core import HomeAssistant
from homeassistant.helpers.entity import DeviceInfo
from homeassistant.helpers.entity_platform import AddEntitiesCallback

from .const import DOMAIN
from .entity import NexBlueEntity


async def async_setup_entry(
    hass: HomeAssistant, entry: ConfigEntry, async_add_entities: AddEntitiesCallback
) -> None:
    """Set up NexBlue current limit numbers based on config entry."""
    coordinator = hass.data[DOMAIN][entry.entry_id]

    numbers = []

    # Check if we have any chargers in the data
    if "chargers" in coordinator.data:
        for charger in coordinator.data["chargers"]:
            numbers.append(
                NexBlueCurrentLimitNumber(coordinator, entry, charger["serial_number"])
            )

    if numbers:
        async_add_entities(numbers)


class NexBlueCurrentLimitNumber(NexBlueEntity, NumberEntity):
    """Number to control NexBlue EV charger current limit."""

    def __init__(self, coordinator, config_entry, charger_serial):
        """Initialize the number."""
        super().__init__(coordinator, config_entry)
        self._charger_serial = charger_serial
        self._attr_name = f"{self._get_charger_name()} Current Limit"
        self._attr_unique_id = f"{config_entry.entry_id}_{charger_serial}_current_limit"
        self._attr_icon = "mdi:current-ac"
        self._attr_native_min_value = 6  # Minimum current limit from API spec
        self._attr_native_max_value = 32  # Maximum current limit from API spec
        self._attr_native_step = 1  # 1 amp increments
        self._attr_native_unit_of_measurement = "A"

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
            name=f"NexBlue {self._get_charger_name()}",
            manufacturer="NexBlue",
            model=self._get_charger_data().get("model", "EV Charger"),
            sw_version=self._get_charger_data().get("firmware_version"),
        )

    @property
    def native_value(self) -> float | None:
        """Return the current value of the current limit."""
        charger_data = self._get_charger_data()
        if not charger_data or "status" not in charger_data:
            return None

        return charger_data.get("status", {}).get("current_limit")

    async def async_set_native_value(self, value: float) -> None:
        """Set the current limit."""
        # Convert float to int for API
        current_limit = int(value)

        try:
            success = await self.coordinator.api.async_set_current_limit(
                self._charger_serial, current_limit
            )

            if success:
                # Add a small delay before refreshing to allow the charger to update
                await self.coordinator.async_request_refresh()
            else:
                raise ValueError("Failed to set current limit")
        except Exception as e:
            raise ValueError("Failed to set current limit") from e
