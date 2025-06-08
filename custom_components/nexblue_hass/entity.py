"""NexBlueEntity class"""
from __future__ import annotations

from homeassistant.helpers.update_coordinator import CoordinatorEntity

from .const import ATTRIBUTION
from .const import DOMAIN


class NexBlueEntity(CoordinatorEntity):
    """Base class for NexBlue entities."""

    def __init__(self, coordinator, config_entry):
        """Initialize the entity."""
        super().__init__(coordinator)
        self.config_entry = config_entry

    @property
    def extra_state_attributes(self):
        """Return common attributes for all entities."""
        return {
            "attribution": ATTRIBUTION,
            "integration": DOMAIN,
        }
