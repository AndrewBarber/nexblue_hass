"""Global fixtures for NexBlue integration."""

import os
from unittest.mock import patch

import pytest

pytest_plugins = "pytest_homeassistant_custom_component"


# Set the config directory to the project root so Home Assistant can discover the integration
@pytest.fixture(autouse=True)
def set_config_dir(hass):
    """Set the config directory to project root for integration discovery."""
    hass.config.config_dir = os.path.dirname(os.path.dirname(__file__))


# This fixture is used to prevent HomeAssistant from attempting to create and dismiss persistent
# notifications. These calls would fail without this fixture since the persistent_notification
# integration is never loaded during a test.
@pytest.fixture(name="skip_notifications", autouse=True)
def skip_notifications_fixture():
    """Skip notification calls."""
    with patch("homeassistant.components.persistent_notification.async_create"), patch(
        "homeassistant.components.persistent_notification.async_dismiss"
    ):
        yield


# This fixture, when used, will result in calls to async_get_data to return None. To have the call
# return a value, we would add the `return_value=<VALUE_TO_RETURN>` parameter to the patch call.
@pytest.fixture(name="bypass_get_data")
def bypass_get_data_fixture():
    """Skip calls to get data from API."""
    with patch("custom_components.nexblue_hass.NexBlueApiClient.async_get_data"):
        yield


# In this fixture, we are forcing calls to async_get_data to raise an Exception. This is useful
# for exception handling.
@pytest.fixture(name="error_on_get_data")
def error_get_data_fixture():
    """Simulate error when retrieving data from API."""
    with patch(
        "custom_components.nexblue_hass.NexBlueApiClient.async_get_data",
        side_effect=Exception,
    ):
        yield
