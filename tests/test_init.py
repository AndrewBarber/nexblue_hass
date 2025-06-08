"""Test the NexBlue init module."""

from __future__ import annotations

from unittest.mock import AsyncMock, patch

import pytest
from homeassistant.config_entries import ConfigEntryState
from homeassistant.core import HomeAssistant
from homeassistant.exceptions import ConfigEntryNotReady
from pytest_homeassistant_custom_component.common import MockConfigEntry

from custom_components.nexblue_hass import (
    NexBlueDataUpdateCoordinator,
    async_reload_entry,
    async_setup,
    async_setup_entry,
    async_unload_entry,
)

pytestmark = pytest.mark.asyncio

# Mock data for testing
MOCK_CONFIG_DATA = {
    "username": "test@example.com",
    "password": "test-password",
}


@pytest.fixture
def coordinator(
    hass: HomeAssistant, mock_api_client: AsyncMock
) -> NexBlueDataUpdateCoordinator:
    """Fixture for creating a coordinator instance with a mock API client."""
    return NexBlueDataUpdateCoordinator(hass, mock_api_client)


async def test_async_setup(hass: HomeAssistant) -> None:
    """Test async_setup function."""
    # Test that async_setup returns True
    assert await async_setup(hass, {}) is True


async def test_setup_entry_success(
    hass: HomeAssistant,
    mock_config_entry: MockConfigEntry,
    mock_api_client: AsyncMock,
) -> None:
    """Test successful setup of the integration."""
    # Setup the integration
    mock_config_entry.add_to_hass(hass)

    # Mock the API client and coordinator
    with (
        patch(
            "custom_components.nexblue_hass.NexBlueApiClient",
            return_value=mock_api_client,
        ),
        patch(
            "custom_components.nexblue_hass.NexBlueDataUpdateCoordinator"
        ) as mock_coordinator,
    ):
        # Configure the coordinator mock
        coordinator_mock = AsyncMock()
        coordinator_mock.async_refresh = AsyncMock()
        coordinator_mock.last_update_success = True
        coordinator_mock.platforms = []
        mock_coordinator.return_value = coordinator_mock

        # Setup the entry
        result = await async_setup_entry(hass, mock_config_entry)
        await hass.async_block_till_done()

        # Verify the setup was successful
        assert result is True
        assert mock_config_entry.state == ConfigEntryState.LOADED

        # Verify the coordinator was created and refresh was called
        mock_coordinator.assert_called_once()
        coordinator_mock.async_refresh.assert_called_once()

        # Verify the API client was initialized with correct credentials
        mock_api_client.async_login.assert_called_once()


async def test_unload_entry_success(
    hass: HomeAssistant,
    mock_config_entry: MockConfigEntry,
) -> None:
    """Test successful unloading of the integration."""
    # Setup the integration first
    mock_config_entry.add_to_hass(hass)

    # Create a mock for the unload function
    with patch(
        "custom_components.nexblue_hass.async_unload_entry", return_value=True
    ) as mock_unload:
        # Unload the entry
        result = await async_unload_entry(hass, mock_config_entry)

        # Verify the unload was successful
        assert result is True
        mock_unload.assert_called_once_with(hass, mock_config_entry)


async def test_setup_entry_auth_failure(
    hass: HomeAssistant,
    mock_config_entry: MockConfigEntry,
    mock_api_client: AsyncMock,
) -> None:
    """Test authentication failure during setup."""
    # Setup the integration with auth failure
    mock_api_client.async_login = AsyncMock(return_value=False)
    mock_config_entry.add_to_hass(hass)

    with (
        patch(
            "custom_components.nexblue_hass.NexBlueApiClient",
            return_value=mock_api_client,
        ),
        pytest.raises(ConfigEntryNotReady),
    ):
        await async_setup_entry(hass, mock_config_entry)
        await hass.async_block_till_done()

    # Verify the API client was called
    mock_api_client.async_login.assert_called_once()


async def test_setup_entry_exception(
    hass: HomeAssistant,
    mock_config_entry: MockConfigEntry,
    mock_api_client: AsyncMock,
) -> None:
    """Test exception during setup."""
    # Setup the integration with an exception
    mock_api_client.async_login.side_effect = Exception("Test exception")
    mock_config_entry.add_to_hass(hass)

    with (
        patch(
            "custom_components.nexblue_hass.NexBlueApiClient",
            return_value=mock_api_client,
        ),
        pytest.raises(ConfigEntryNotReady),
    ):
        await async_setup_entry(hass, mock_config_entry)
        await hass.async_block_till_done()

    # Verify the API client was called
    mock_api_client.async_login.assert_called_once()


async def test_coordinator_update_success(
    coordinator: NexBlueDataUpdateCoordinator, mock_api_client: AsyncMock
) -> None:
    """Test successful data update in the coordinator."""
    # Setup test data
    test_data = {"test": "data"}
    mock_api_client.async_get_data = AsyncMock(return_value=test_data)

    # Trigger update
    result = await coordinator._async_update_data()

    # Verify results
    assert result == test_data
    mock_api_client.async_get_data.assert_called_once()


async def test_coordinator_update_failure(
    coordinator: NexBlueDataUpdateCoordinator, mock_api_client: AsyncMock
) -> None:
    """Test data update failure in the coordinator."""
    # Setup exception
    mock_api_client.async_get_data.side_effect = Exception("Test error")

    # Verify UpdateFailed is raised
    with pytest.raises(Exception):
        await coordinator._async_update_data()

    mock_api_client.async_get_data.assert_called_once()


async def test_async_reload_entry(
    hass: HomeAssistant,
    mock_config_entry: MockConfigEntry,
) -> None:
    """Test reloading the config entry."""
    # Setup mocks
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
        # Reload the entry
        await async_reload_entry(hass, mock_config_entry)

        # Verify unload and setup were called
        mock_unload.assert_called_once_with(hass, mock_config_entry)
        mock_setup.assert_called_once_with(hass, mock_config_entry)
