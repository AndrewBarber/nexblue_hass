"""Switch platform for NexBlue EV Chargers."""

from __future__ import annotations

import asyncio
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
            switches.append(
                NexBlueChargingSwitch(coordinator, entry, charger["serial_number"])
            )

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

    # Store the last command sent and when
    _last_command = None
    _command_timestamp = 0

    @property
    def is_on(self) -> bool:
        """Return true if charger is currently charging or in a charging-related state."""
        charger_data = self._get_charger_data()
        if not charger_data or "status" not in charger_data:
            return False

        # Consider both active charging and transitional states that indicate charging is starting
        # 2 = charging, 5 = load balancing, 6 = delayed, 7 = ev waiting
        status = charger_data.get("status", {})
        charging_state = status.get("charging_state")

        # If we recently sent a command, honor that command's intent for a short period
        # This prevents the switch from flickering during state transitions
        if (
            self._last_command is not None
            and (asyncio.get_event_loop().time() - self._command_timestamp) < 10
        ):
            # If we sent "turn_on" and we're in any non-idle state, show as on
            if self._last_command == "turn_on" and charging_state not in (
                0,
                4,
            ):  # Not idle or error
                return True
            # If we sent "turn_off" and we're not actively charging, show as off
            elif self._last_command == "turn_off" and charging_state != 2:
                return False

        # Otherwise use normal state detection
        # Consider charging (2), load balancing (5), delayed (6), and ev waiting (7) as "on" states
        return charging_state in (2, 5, 6, 7)

    async def async_turn_on(self, **kwargs: Any) -> None:
        """Turn the switch on (start charging)."""
        await self.coordinator.api.async_start_charging(self._charger_serial)

        # Record that we sent a turn_on command
        self._last_command = "turn_on"
        self._command_timestamp = asyncio.get_event_loop().time()

        # Add a small delay before refreshing to allow the charger to begin state transition
        await asyncio.sleep(1)
        await self.coordinator.async_request_refresh()

    async def async_turn_off(self, **kwargs: Any) -> None:
        """Turn the switch off (stop charging)."""
        await self.coordinator.api.async_stop_charging(self._charger_serial)

        # Record that we sent a turn_off command
        self._last_command = "turn_off"
        self._command_timestamp = asyncio.get_event_loop().time()

        # Add a small delay before refreshing to allow the charger to begin state transition
        await asyncio.sleep(1)
        await self.coordinator.async_request_refresh()
