"""Switch platform for NexBlue EV Chargers."""
from __future__ import annotations

from typing import Any

from homeassistant.components.switch import SwitchEntity
from homeassistant.config_entries import ConfigEntry
from homeassistant.core import HomeAssistant
from homeassistant.helpers.entity import DeviceInfo
from homeassistant.helpers.entity_platform import AddEntitiesCallback

from .const import DOMAIN
from .entity import NexBlueEntity


async def async_setup_entry(
    hass: HomeAssistant, entry: ConfigEntry, async_add_entities: AddEntitiesCallback
) -> None:
    """Set up NexBlue charging switches based on config entry."""
    coordinator = hass.data[DOMAIN][entry.entry_id]

    switches = []

    # Check if we have any chargers in the data
    if "chargers" in coordinator.data:
        for charger in coordinator.data["chargers"]:
            switches.append(NexBlueChargingSwitch(coordinator, entry, charger["serial_number"]))

    if switches:
        async_add_entities(switches)


class NexBlueChargingSwitch(NexBlueEntity, SwitchEntity):
    """Switch to control NexBlue EV charger charging state."""

    def __init__(self, coordinator, config_entry, charger_serial):
        """Initialize the switch."""
        super().__init__(coordinator, config_entry)
        self._charger_serial = charger_serial
        self._attr_name = f"{self._get_charger_name()} Charging"
        self._attr_unique_id = f"{config_entry.entry_id}_{charger_serial}_charging"
        self._attr_icon = "mdi:ev-station"

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
    def is_on(self) -> bool:
        """Return true if charger is currently charging."""
        charger_data = self._get_charger_data()
        if not charger_data or "status" not in charger_data:
            return False

        # Check if the charger is in charging state
        # This will need to be adjusted based on the actual API response structure
        status = charger_data.get("status", {})
        return status.get("charging_status") == "charging"

    async def async_turn_on(self, **kwargs: Any) -> None:
        """Turn the switch on (start charging)."""
        result = await self.coordinator.api.async_start_charging(self._charger_serial)
        await self.coordinator.async_request_refresh()

    async def async_turn_off(self, **kwargs: Any) -> None:
        """Turn the switch off (stop charging)."""
        result = await self.coordinator.api.async_stop_charging(self._charger_serial)
        await self.coordinator.async_request_refresh()
