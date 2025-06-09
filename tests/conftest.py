"""Global fixtures for NexBlue integration tests."""

# Standard library imports
from __future__ import annotations

import asyncio
import sys
from collections.abc import AsyncGenerator, Callable, Generator
from pathlib import Path
from typing import Any, TypeVar
from unittest.mock import AsyncMock, patch

# Third-party imports
import pytest
import pytest_asyncio
from homeassistant.config_entries import ConfigEntry, ConfigFlow
from homeassistant.core import HomeAssistant
from homeassistant.setup import async_setup_component
from pytest_homeassistant_custom_component.common import (
    MockConfigEntry,
    MockModule,
    MockPlatform,
    mock_integration,
    mock_platform,
)

# Local application imports
from custom_components.nexblue_hass.const import DOMAIN  # noqa: E402

# Add the custom component to the Python path
TEST_DIR = Path(__file__).parent
ROOT_DIR = TEST_DIR.parent
CUSTOM_COMPONENTS_DIR = ROOT_DIR / "custom_components"
sys.path.insert(0, str(CUSTOM_COMPONENTS_DIR.parent.absolute()))

# Type variables for fixtures
_T = TypeVar("_T")
PytestFixture = Callable[..., _T]  # Type alias for pytest fixtures


# Mock the config flow
class MockFlow(ConfigFlow):
    """Test config flow."""
    VERSION = 1
    
    def __init__(self):
        """Initialize the mock flow."""
        super().__init__()
        # Skip registration in init, will be done in fixture

    def register_flow(self, hass):
        """Register this flow with the provided hass instance."""
        self.hass = hass
        if hasattr(hass, 'config_entries') and hass.config_entries is not None:
            # In newer versions of Home Assistant, flows are registered differently
            # The actual registration is handled by the test framework
            pass


# Fixture for enabling/disabling auto-use of fixtures
@pytest.fixture(autouse=True)
async def auto_enable_custom_integrations(hass):
    """Auto enable custom integrations."""
    # Ensure the component is set up
    if hasattr(hass, 'config'):
        hass.config.components.add(DOMAIN)
    
    # Create and register the mock flow
    flow = MockFlow()
    if hasattr(hass, 'config_entries') and hass.config_entries is not None:
        # In newer versions, the test framework handles flow registration
        flow.register_flow(hass)
    
    # Set up the integration mock
    mock_integration(
        hass,
        MockModule(
            DOMAIN,
            async_setup=AsyncMock(return_value=True),
            async_setup_entry=AsyncMock(return_value=True),
            async_unload_entry=AsyncMock(return_value=True),
            async_migrate_entry=AsyncMock(return_value=True),
            async_remove_entry=AsyncMock(return_value=True),
        ),
    )
    
    yield


@pytest_asyncio.fixture(autouse=True)
async def setup_ha(
    hass: HomeAssistant, request: Any
) -> AsyncGenerator[HomeAssistant, None]:
    """Set up Home Assistant instance with required components."""
    # Ensure hass is properly initialized
    if not hasattr(hass, "data"):
        hass.data = {}

    # Setup required components
    await async_setup_component(hass, "homeassistant", {})
    await hass.async_block_till_done()

    # Setup the integration domain
    hass.config_entries.flow.async_init = AsyncMock()

    # Mock the component platforms
    for platform in ["switch", "sensor", "binary_sensor"]:
        mock_platform(
            hass,
            f"{DOMAIN}.{platform}",
            MockPlatform(async_setup_entry=AsyncMock(return_value=True)),
        )

    # Mock the config flow
    mock_integration(
        hass,
        MockModule(
            DOMAIN,
            async_setup_entry=AsyncMock(return_value=True),
            async_unload_entry=AsyncMock(return_value=True),
            async_migrate_entry=AsyncMock(return_value=True),
            async_remove_entry=AsyncMock(return_value=True),
        ),
    )

    # Ensure the custom component is in the components set
    if not hasattr(hass.config, "components"):
        hass.config.components = set()
    hass.config.components.add(DOMAIN)

    yield hass

    # Clean up
    await hass.async_stop()
    await hass.async_block_till_done()


@pytest.fixture
def event_loop() -> Generator[asyncio.AbstractEventLoop, None, None]:
    """Create an instance of the default event loop for each test case."""
    loop = asyncio.new_event_loop()
    yield loop
    loop.close()


# Mock the API client
@pytest.fixture
def mock_api_client() -> Generator[AsyncMock, None, None]:
    """Mock the NexBlue API client."""
    with patch(f"custom_components.{DOMAIN}.NexBlueApiClient") as mock_client:
        client = AsyncMock()
        client.async_login = AsyncMock(return_value=True)
        client.async_start_charging = AsyncMock(return_value=True)
        client.async_stop_charging = AsyncMock(return_value=True)
        client.async_update = AsyncMock(return_value=True)
        client.available = True

        # Mock the async_get_data to return data in the format expected by the coordinator
        async def mock_async_get_data():
            return {
                "chargers": [
                    {
                        "serial_number": "12345",
                        "name": "Test Charger",
                        "model": "Test Model",
                        "firmware_version": "1.0.0",
                        "status": {
                            "is_charging": False,
                            "is_connected": True,
                            "current_power": 0.0,
                            "current_limit": 32.0,
                            "charging_state": "standby",
                            "plug_state": "connected",
                            "max_charging_current": 32.0,
                            "actual_charging_current": 0.0,
                            "actual_power": 0.0,
                            "total_energy": 0.0,
                        },
                    }
                ]
            }

        client.async_get_data = AsyncMock(side_effect=mock_async_get_data)

        # Set the mock client's return value
        mock_client.return_value = client

        yield client

        # Clean up any pending tasks
        for task in asyncio.all_tasks(loop=asyncio.get_event_loop()):
            if not task.done() and not task.cancelled():
                task.cancel()
                try:
                    asyncio.get_event_loop().run_until_complete(task)
                except asyncio.CancelledError:
                    pass


# Mock config entry
@pytest.fixture
def mock_config_entry() -> ConfigEntry:
    """Return a mock config entry."""
    return MockConfigEntry(
        domain=DOMAIN,
        data={
            "username": "test@example.com",
            "password": "test-password",
        },
        unique_id="test-username",
        entry_id="test-entry-id",
    )


# Setup integration with mocks
@pytest_asyncio.fixture
async def setup_integration(
    hass: HomeAssistant,
    mock_config_entry: ConfigEntry,
    mock_api_client: AsyncMock,
) -> AsyncGenerator[ConfigEntry, None]:
    """Set up the integration with a mock config entry and API client."""
    # Add the config entry
    mock_config_entry.add_to_hass(hass)

    # Setup the integration with our mock API client
    with (
        patch(
            f"custom_components.{DOMAIN}.NexBlueApiClient",
            return_value=mock_api_client,
        ),
        patch(
            f"custom_components.{DOMAIN}.async_setup_entry",
            return_value=True,
        ),
    ):
        # Initialize the integration
        assert await async_setup_component(hass, DOMAIN, {})
        await hass.async_block_till_done()

        # Setup the config entry
        assert await hass.config_entries.async_setup(mock_config_entry.entry_id)
        await hass.async_block_till_done()

        # Ensure the coordinator is set up
        if DOMAIN in hass.data and "coordinator" in hass.data[DOMAIN]:
            await hass.data[DOMAIN]["coordinator"].async_refresh()
            await hass.async_block_till_done()

        yield mock_config_entry

        # Clean up
        await hass.config_entries.async_unload(mock_config_entry.entry_id)
        await hass.async_block_till_done()

        # Ensure the integration is unloaded
        assert not hass.data.get(DOMAIN)
