"""Test the NexBlue integration init file."""

# Standard library imports
from unittest.mock import AsyncMock, MagicMock, patch

# Third-party imports
import pytest
from homeassistant.config_entries import ConfigEntry, ConfigEntryState
from homeassistant.core import HomeAssistant
from homeassistant.exceptions import ConfigEntryNotReady
from homeassistant.helpers.update_coordinator import DataUpdateCoordinator

# Local application imports
from custom_components.nexblue_hass import (
    async_setup,
    async_setup_entry,
    async_unload_entry,
    async_reload_entry,
    NexBlueDataUpdateCoordinator,
)
from custom_components.nexblue_hass.const import DOMAIN, CONF_USERNAME, CONF_PASSWORD, PLATFORMS


async def test_async_setup(hass: HomeAssistant) -> None:
    """Test the async_setup function."""
    # Test that async_setup returns True
    result = await async_setup(hass, {})
    assert result is True


async def test_setup_entry_success(
    hass: HomeAssistant, mock_config_entry: ConfigEntry, mock_api_client: AsyncMock
) -> None:
    """Test successful setup of the integration."""
    # Create a mock coordinator
    coordinator_mock = MagicMock(spec=DataUpdateCoordinator)
    coordinator_mock.async_refresh = AsyncMock()
    coordinator_mock.last_update_success = True
    coordinator_mock.platforms = []
    coordinator_mock.data = {}

    # Mock the dependencies
    with (
        patch(
            "custom_components.nexblue_hass.NexBlueApiClient",
            return_value=mock_api_client,
        ) as mock_client,
        patch(
            "custom_components.nexblue_hass.NexBlueDataUpdateCoordinator",
            return_value=coordinator_mock,
        ) as mock_coordinator,
        patch.object(
            hass.config_entries,
            "async_forward_entry_setups",
            return_value=True,
        ) as mock_forward_entry_setups,
    ):
        # Call the setup entry function
        result = await async_setup_entry(hass, mock_config_entry)
        
        # Assertions
        assert result is True
        mock_client.assert_called_once()
        mock_coordinator.assert_called_once()
        mock_forward_entry_setups.assert_called_once()
        
        # Verify the coordinator was stored in hass.data
        assert DOMAIN in hass.data
        assert mock_config_entry.entry_id in hass.data[DOMAIN]
        assert hass.data[DOMAIN][mock_config_entry.entry_id] == coordinator_mock


async def test_setup_entry_failure(
    hass: HomeAssistant, mock_config_entry: ConfigEntry, mock_api_client: AsyncMock
) -> None:
    """Test setup when the coordinator fails to refresh."""
    # Create a mock coordinator that fails to refresh
    coordinator_mock = MagicMock(spec=DataUpdateCoordinator)
    coordinator_mock.async_refresh = AsyncMock()
    coordinator_mock.last_update_success = False
    coordinator_mock.platforms = []

    with (
        patch(
            "custom_components.nexblue_hass.NexBlueApiClient",
            return_value=mock_api_client,
        ),
        patch(
            "custom_components.nexblue_hass.NexBlueDataUpdateCoordinator",
            return_value=coordinator_mock,
        ),
        pytest.raises(ConfigEntryNotReady),
    ):
        await async_setup_entry(hass, mock_config_entry)


async def test_unload_entry_success(
    hass: HomeAssistant, mock_config_entry: ConfigEntry
) -> None:
    """Test successful unloading of the integration."""
    # Setup the coordinator in hass.data with platforms
    coordinator_mock = MagicMock()
    coordinator_mock.platforms = list(PLATFORMS)  # Add platforms to unload
    
    hass.data.setdefault(DOMAIN, {})
    hass.data[DOMAIN][mock_config_entry.entry_id] = coordinator_mock

    # Mock the async_unload_platforms method
    with patch.object(
        hass.config_entries,
        "async_unload_platforms",
        return_value=True,
    ) as mock_unload_platforms:
        # Call the unload function
        result = await async_unload_entry(hass, mock_config_entry)
        
        # Assertions
        assert result is True
        mock_unload_platforms.assert_called_once()
        
        # Get the arguments passed to async_unload_platforms
        called_args = mock_unload_platforms.call_args[0]
        assert called_args[0] == mock_config_entry  # Should be the config entry
        assert set(called_args[1]) == set(PLATFORMS)  # Check all platforms are being unloaded
        
        # Verify the coordinator was removed from hass.data
        assert mock_config_entry.entry_id not in hass.data[DOMAIN]


async def test_unload_entry_no_platforms(
    hass: HomeAssistant, mock_config_entry: ConfigEntry
) -> None:
    """Test unloading when there are no platforms to unload."""
    # Setup the coordinator in hass.data with no platforms
    coordinator_mock = MagicMock()
    coordinator_mock.platforms = []  # No platforms to unload
    
    hass.data.setdefault(DOMAIN, {})
    hass.data[DOMAIN][mock_config_entry.entry_id] = coordinator_mock

    # Call the unload function
    result = await async_unload_entry(hass, mock_config_entry)
    
    # Assertions
    assert result is True  # Should still return True
    assert mock_config_entry.entry_id not in hass.data[DOMAIN]  # Coordinator should still be removed


async def test_async_reload_entry(
    hass: HomeAssistant, mock_config_entry: ConfigEntry, mock_api_client: AsyncMock
) -> None:
    """Test reloading the config entry."""
    # Setup the coordinator in hass.data
    coordinator_mock = MagicMock()
    coordinator_mock.platforms = list(PLATFORMS)
    hass.data.setdefault(DOMAIN, {})
    hass.data[DOMAIN][mock_config_entry.entry_id] = coordinator_mock
    
    # Mock the unload and setup functions
    with (
        patch(
            "custom_components.nexblue_hass.async_unload_entry",
            return_value=True,
        ) as mock_unload,
        patch(
            "custom_components.nexblue_hass.async_setup_entry",
            return_value=True,
        ) as mock_setup,
    ):
        # Call the reload function
        await async_reload_entry(hass, mock_config_entry)
        
        # Verify both unload and setup were called
        mock_unload.assert_called_once_with(hass, mock_config_entry)
        mock_setup.assert_called_once_with(hass, mock_config_entry)


async def test_coordinator_update_success(
    hass: HomeAssistant, mock_api_client: AsyncMock
) -> None:
    """Test the coordinator's update method."""
    # Create test data
    test_data = {"test": "data"}
    mock_api_client.async_get_data = AsyncMock(return_value=test_data)
    
    # Create the coordinator
    coordinator = NexBlueDataUpdateCoordinator(hass, mock_api_client)
    
    # Call the update method
    result = await coordinator._async_update_data()
    
    # Assertions
    assert result == test_data
    mock_api_client.async_get_data.assert_called_once()


async def test_coordinator_update_failure(
    hass: HomeAssistant, mock_api_client: AsyncMock
) -> None:
    """Test the coordinator's update method when the API fails."""
    # Mock the API to raise an exception
    mock_api_client.async_get_data = AsyncMock(side_effect=Exception("Test error"))
    
    # Create the coordinator
    coordinator = NexBlueDataUpdateCoordinator(hass, mock_api_client)
    
    # The exception should be wrapped in UpdateFailed
    with pytest.raises(Exception) as exc_info:
        await coordinator._async_update_data()
    
    assert isinstance(exc_info.value.__cause__, Exception)
    assert str(exc_info.value.__cause__) == "Test error"
