"""Test fixtures for API responses."""

from typing import Any


def mock_charger_data(charger_id: str = "SN123456", **kwargs) -> dict[str, Any]:
    """Return mock charger data."""
    return {
        "serial_number": charger_id,
        "name": f"Charger {charger_id}",
        "model": "NexBlue Pro",
        "firmware_version": "1.2.3",
        "connected": True,
        "vehicle_connected": False,
        "charging": False,
        "power": 0.0,
        "energy": 10.5,
        "current": 0.0,
        "voltage": 230.0,
        **kwargs,
    }


def mock_chargers_list(count: int = 1) -> list[dict[str, Any]]:
    """Return a list of mock chargers."""
    return [mock_charger_data(f"SN{1000 + i}") for i in range(count)]
