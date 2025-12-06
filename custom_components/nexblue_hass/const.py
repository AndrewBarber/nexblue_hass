"""Constants for NexBlue EV Charger integration."""

# Base component constants
NAME = "NexBlue EV Charger"
DOMAIN = "nexblue_hass"
DOMAIN_DATA = f"{DOMAIN}_data"
VERSION = "0.2.0"

ATTRIBUTION = "Data provided by NexBlue API"
ISSUE_URL = "https://github.com/AndrewBarber/nexblue_hass/issues"

# Icons
ICON = "mdi:format-quote-close"

# Device classes
BINARY_SENSOR_DEVICE_CLASS = "connectivity"

# Platforms
BINARY_SENSOR = "binary_sensor"
NUMBER = "number"
SENSOR = "sensor"
SWITCH = "switch"
PLATFORMS = [BINARY_SENSOR, NUMBER, SENSOR, SWITCH]


# Configuration and options
CONF_ENABLED = "enabled"
CONF_USERNAME = "username"
CONF_PASSWORD = "password"

# Defaults
DEFAULT_NAME = DOMAIN


STARTUP_MESSAGE = f"""
-------------------------------------------------------------------
{NAME}
Version: {VERSION}
This is a custom integration!
If you have any issues with this you need to open an issue here:
{ISSUE_URL}
-------------------------------------------------------------------
"""
