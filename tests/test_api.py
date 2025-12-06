"""Test NexBlue API."""

import asyncio
from datetime import datetime, timedelta

import aiohttp
import pytest
from homeassistant.helpers.aiohttp_client import async_get_clientsession

from custom_components.nexblue_hass.api import NexBlueApiClient


@pytest.mark.asyncio
async def test_api(hass, aioclient_mock, caplog):
    """Test API calls."""

    # To test the api submodule, we first create an instance of our API client
    api = NexBlueApiClient("test", "test", async_get_clientsession(hass))

    # Mock the login endpoint first since async_get_data requires authentication
    aioclient_mock.post(
        "https://api.nexblue.com/third_party/openapi/account/login",
        json={"access_token": "test_token", "refresh_token": "test_refresh"},
    )

    # Use aioclient_mock which is provided by `pytest_homeassistant_custom_components`
    # to mock responses to aiohttp requests. The API expects a 'data' key with an array of chargers
    aioclient_mock.get(
        "https://api.nexblue.com/third_party/openapi/chargers",
        json={
            "data": [
                {"serial_number": "test123", "name": "Test Charger", "status": "online"}
            ]
        },
    )

    # Mock the charger detail endpoint that gets called for each charger
    aioclient_mock.get(
        "https://api.nexblue.com/third_party/openapi/chargers/test123",
        json={
            "serial_number": "test123",
            "name": "Test Charger",
            "status": "online",
            "charging": False,
        },
    )

    # Mock the charger status endpoint
    aioclient_mock.get(
        "https://api.nexblue.com/third_party/openapi/chargers/test123/cmd/status",
        json={"status": "idle"},
    )

    result = await api.async_get_data()
    assert "chargers" in result
    assert len(result["chargers"]) > 0


@pytest.mark.asyncio
async def test_api_login_failure(hass, aioclient_mock, caplog):
    """Test API login failure."""
    api = NexBlueApiClient("test", "test", async_get_clientsession(hass))

    # Mock failed login
    aioclient_mock.post(
        "https://api.nexblue.com/third_party/openapi/account/login",
        status=401,
        json={"error": "Invalid credentials"},
    )

    result = await api.async_login()
    assert result is False


@pytest.mark.asyncio
async def test_api_token_refresh_failure_fallback_to_login(
    hass, aioclient_mock, caplog
):
    """Test token refresh failure fallback to login (covers lines 102-104)."""
    api = NexBlueApiClient("test", "test", async_get_clientsession(hass))

    # Set initial tokens
    api._access_token = "old_token"
    api._refresh_token = "refresh_token"
    api._token_expires_at = datetime.now() - timedelta(hours=1)  # Expired

    # Mock failed token refresh
    aioclient_mock.post(
        "https://api.nexblue.com/third_party/openapi/account/refresh_token",
        status=401,
        json={"error": "Invalid refresh token"},
    )

    # Mock successful login fallback
    aioclient_mock.post(
        "https://api.nexblue.com/third_party/openapi/account/login",
        json={"access_token": "new_token", "refresh_token": "new_refresh"},
    )

    result = await api.async_refresh_token()
    assert result is True


@pytest.mark.asyncio
async def test_api_token_validation_success(hass, aioclient_mock, caplog):
    """Test token validation success path (covers line 117)."""
    api = NexBlueApiClient("test", "test", async_get_clientsession(hass))

    # Set valid future token
    api._access_token = "valid_token"
    api._token_expires_at = datetime.now() + timedelta(hours=1)  # Valid

    result = await api.async_ensure_token_valid()
    assert result is True


@pytest.mark.asyncio
async def test_api_get_data_empty_response(hass, aioclient_mock, caplog):
    """Test get_data with empty response (covers lines 134-135)."""
    api = NexBlueApiClient("test", "test", async_get_clientsession(hass))

    # Mock login
    aioclient_mock.post(
        "https://api.nexblue.com/third_party/openapi/account/login",
        json={"access_token": "test_token", "refresh_token": "test_refresh"},
    )

    # Mock empty chargers response
    aioclient_mock.get(
        "https://api.nexblue.com/third_party/openapi/chargers", json=None
    )

    result = await api.async_get_data()
    assert result == {}
    assert "No charger data received" in caplog.text


@pytest.mark.asyncio
async def test_api_get_data_missing_data_key(hass, aioclient_mock, caplog):
    """Test get_data with missing data key (covers lines 187-189)."""
    api = NexBlueApiClient("test", "test", async_get_clientsession(hass))

    # Mock login
    aioclient_mock.post(
        "https://api.nexblue.com/third_party/openapi/account/login",
        json={"access_token": "test_token", "refresh_token": "test_refresh"},
    )

    # Mock response without 'data' key
    aioclient_mock.get(
        "https://api.nexblue.com/third_party/openapi/chargers",
        json={"chargers": []},  # Wrong format
    )

    result = await api.async_get_data()
    assert result == {}
    assert "Expected 'data' key" in caplog.text


@pytest.mark.asyncio
async def test_api_get_data_invalid_data_format(hass, aioclient_mock, caplog):
    """Test get_data with invalid data format (covers lines 152-153 exception)."""
    api = NexBlueApiClient("test", "test", async_get_clientsession(hass))

    # Mock login
    aioclient_mock.post(
        "https://api.nexblue.com/third_party/openapi/account/login",
        json={"access_token": "test_token", "refresh_token": "test_refresh"},
    )

    # Mock response with invalid data format (string instead of list)
    aioclient_mock.get(
        "https://api.nexblue.com/third_party/openapi/chargers",
        json={"data": "not_a_list"},  # Should be a list
    )

    result = await api.async_get_data()
    assert result == {}  # Exception handler returns {} on error
    assert "'str' object has no attribute 'get'" in caplog.text


@pytest.mark.asyncio
async def test_api_get_data_charger_missing_serial(hass, aioclient_mock, caplog):
    """Test get_data with charger missing serial number (covers lines 152-154)."""
    api = NexBlueApiClient("test", "test", async_get_clientsession(hass))

    # Mock login
    aioclient_mock.post(
        "https://api.nexblue.com/third_party/openapi/account/login",
        json={"access_token": "test_token", "refresh_token": "test_refresh"},
    )

    # Mock response with charger missing serial number
    aioclient_mock.get(
        "https://api.nexblue.com/third_party/openapi/chargers",
        json={
            "data": [
                {
                    "name": "Test Charger",
                    # Missing serial_number
                }
            ]
        },
    )

    # Mock the charger detail endpoint that won't be called due to missing serial
    aioclient_mock.get(
        "https://api.nexblue.com/third_party/openapi/chargers/test123",
        json={"serial_number": "test123", "status": "online"},
    )

    result = await api.async_get_data()
    assert result == {
        "chargers": []
    }  # Returns empty chargers list when no valid chargers


@pytest.mark.asyncio
async def test_api_start_charging_error(hass, aioclient_mock, caplog):
    """Test start charging error scenarios (covers lines 275-287)."""
    api = NexBlueApiClient("test", "test", async_get_clientsession(hass))

    # Mock login
    aioclient_mock.post(
        "https://api.nexblue.com/third_party/openapi/account/login",
        json={"access_token": "test_token", "refresh_token": "test_refresh"},
    )

    # Mock failed start charging response
    aioclient_mock.post(
        "https://api.nexblue.com/third_party/openapi/chargers/test123/start",
        status=400,
        json={"error": "Charger not available"},
    )

    result = await api.async_start_charging("test123")
    assert result is False
    assert "Failed to start charging" in caplog.text


@pytest.mark.asyncio
async def test_api_stop_charging_error(hass, aioclient_mock, caplog):
    """Test stop charging error scenarios (covers lines 311-316)."""
    api = NexBlueApiClient("test", "test", async_get_clientsession(hass))

    # Mock login
    aioclient_mock.post(
        "https://api.nexblue.com/third_party/openapi/account/login",
        json={"access_token": "test_token", "refresh_token": "test_refresh"},
    )

    # Mock failed stop charging response
    aioclient_mock.post(
        "https://api.nexblue.com/third_party/openapi/chargers/test123/stop",
        status=400,
        json={"error": "Charger not charging"},
    )

    result = await api.async_stop_charging("test123")
    assert result is False
    assert "Failed to stop charging" in caplog.text


@pytest.mark.asyncio
async def test_api_get_data_authentication_failure(hass, aioclient_mock, caplog):
    """Test get_data authentication failure (covers lines 123-124)."""
    api = NexBlueApiClient("test", "test", async_get_clientsession(hass))

    # Mock failed login to trigger authentication failure
    aioclient_mock.post(
        "https://api.nexblue.com/third_party/openapi/account/login",
        status=401,
        json={"error": "Invalid credentials"},
    )

    result = await api.async_get_data()
    assert result == {}
    assert "Failed to authenticate with NexBlue API" in caplog.text


@pytest.mark.asyncio
async def test_api_wrapper_unsupported_method(hass, aioclient_mock, caplog):
    """Test api_wrapper unsupported method (covers lines 286-287)."""
    api = NexBlueApiClient("test", "test", async_get_clientsession(hass))

    # Mock login
    aioclient_mock.post(
        "https://api.nexblue.com/third_party/openapi/account/login",
        json={"access_token": "test_token", "refresh_token": "test_refresh"},
    )

    # Test unsupported method - should return None and log error
    result = await api.api_wrapper(
        "invalid_method", "https://api.nexblue.com/third_party/openapi/test"
    )
    assert result is None
    assert "Unsupported method: invalid_method" in caplog.text


@pytest.mark.asyncio
async def test_api_wrapper_put_method(hass, aioclient_mock, caplog):
    """Test api_wrapper PUT method (covers lines 275-276)."""
    api = NexBlueApiClient("test", "test", async_get_clientsession(hass))

    # Mock login
    aioclient_mock.post(
        "https://api.nexblue.com/third_party/openapi/account/login",
        json={"access_token": "test_token", "refresh_token": "test_refresh"},
    )

    # Mock PUT request
    aioclient_mock.put(
        "https://api.nexblue.com/third_party/openapi/test", json={"status": "success"}
    )

    result = await api.api_wrapper(
        "put", "https://api.nexblue.com/third_party/openapi/test", {"data": "test"}
    )
    assert result == {"status": "success"}


@pytest.mark.asyncio
async def test_api_wrapper_patch_method(hass, aioclient_mock, caplog):
    """Test api_wrapper PATCH method (covers lines 278-280)."""
    api = NexBlueApiClient("test", "test", async_get_clientsession(hass))

    # Mock login
    aioclient_mock.post(
        "https://api.nexblue.com/third_party/openapi/account/login",
        json={"access_token": "test_token", "refresh_token": "test_refresh"},
    )

    # Mock PATCH request
    aioclient_mock.patch(
        "https://api.nexblue.com/third_party/openapi/test", json={"status": "success"}
    )

    result = await api.api_wrapper(
        "patch", "https://api.nexblue.com/third_party/openapi/test", {"data": "test"}
    )
    assert result == {"status": "success"}


@pytest.mark.asyncio
async def test_api_wrapper_delete_method(hass, aioclient_mock, caplog):
    """Test api_wrapper DELETE method (covers lines 282-284)."""
    api = NexBlueApiClient("test", "test", async_get_clientsession(hass))

    # Mock login
    aioclient_mock.post(
        "https://api.nexblue.com/third_party/openapi/account/login",
        json={"access_token": "test_token", "refresh_token": "test_refresh"},
    )

    # Mock DELETE request
    aioclient_mock.delete(
        "https://api.nexblue.com/third_party/openapi/test", json={"status": "success"}
    )

    result = await api.api_wrapper(
        "delete", "https://api.nexblue.com/third_party/openapi/test"
    )
    assert result == {"status": "success"}


@pytest.mark.asyncio
async def test_api_token_refresh_success(hass, aioclient_mock, caplog):
    """Test API token refresh success."""
    api = NexBlueApiClient("test", "test", async_get_clientsession(hass))

    # Mock initial login
    aioclient_mock.post(
        "https://api.nexblue.com/third_party/openapi/account/login",
        json={"access_token": "old_token", "refresh_token": "refresh_token"},
    )

    # Mock token refresh
    aioclient_mock.post(
        "https://api.nexblue.com/third_party/openapi/account/refresh_token",
        json={"access_token": "new_token", "refresh_token": "new_refresh"},
    )

    # Mock chargers data
    aioclient_mock.get(
        "https://api.nexblue.com/third_party/openapi/chargers", json={"data": []}
    )

    result = await api.async_get_data()
    assert "chargers" in result


@pytest.mark.asyncio
async def test_api_start_charging_success(hass, aioclient_mock, caplog):
    """Test API start charging success."""
    api = NexBlueApiClient("test", "test", async_get_clientsession(hass))

    # Mock login
    aioclient_mock.post(
        "https://api.nexblue.com/third_party/openapi/account/login",
        json={"access_token": "test_token", "refresh_token": "test_refresh"},
    )

    # Mock start charging success
    aioclient_mock.post(
        "https://api.nexblue.com/third_party/openapi/chargers/test123/cmd/start_charging",
        json={"result": 0},
    )

    result = await api.async_start_charging("test123")
    assert result is True


@pytest.mark.asyncio
async def test_api_stop_charging_success(hass, aioclient_mock, caplog):
    """Test API stop charging success."""
    api = NexBlueApiClient("test", "test", async_get_clientsession(hass))

    # Mock login
    aioclient_mock.post(
        "https://api.nexblue.com/third_party/openapi/account/login",
        json={"access_token": "test_token", "refresh_token": "test_refresh"},
    )

    # Mock stop charging success
    aioclient_mock.post(
        "https://api.nexblue.com/third_party/openapi/chargers/test123/cmd/stop_charging",
        json={"result": 0},
    )

    result = await api.async_stop_charging("test123")
    assert result is True


@pytest.mark.asyncio
async def test_api_wrapper_timeout(hass, aioclient_mock, caplog):
    """Test API wrapper timeout handling."""
    api = NexBlueApiClient("test", "test", async_get_clientsession(hass))

    # Mock timeout
    aioclient_mock.get(
        "https://api.nexblue.com/third_party/openapi/chargers",
        exc=asyncio.TimeoutError(),
    )

    result = await api.api_wrapper(
        "get", "https://api.nexblue.com/third_party/openapi/chargers"
    )
    assert result is None
    assert "Timeout error" in caplog.text


@pytest.mark.asyncio
async def test_api_token_refresh_failure(hass, aioclient_mock, caplog):
    """Test API token refresh failure."""
    api = NexBlueApiClient("test", "test", async_get_clientsession(hass))

    # Set expired token to force refresh
    api._access_token = "expired_token"
    api._refresh_token = "refresh_token"

    # Mock token refresh failure
    aioclient_mock.post(
        "https://api.nexblue.com/third_party/openapi/account/refresh_token", status=401
    )

    result = await api.async_ensure_token_valid()
    assert result is False


@pytest.mark.asyncio
async def test_api_start_charging_auth_failure(hass, aioclient_mock, caplog):
    """Test API start charging authentication failure."""
    api = NexBlueApiClient("test", "test", async_get_clientsession(hass))

    # Mock authentication failure
    aioclient_mock.post(
        "https://api.nexblue.com/third_party/openapi/account/login", status=401
    )

    result = await api.async_start_charging("test123")
    assert result is False


@pytest.mark.asyncio
async def test_api_stop_charging_auth_failure(hass, aioclient_mock, caplog):
    """Test API stop charging authentication failure."""
    api = NexBlueApiClient("test", "test", async_get_clientsession(hass))

    # Mock authentication failure
    aioclient_mock.post(
        "https://api.nexblue.com/third_party/openapi/account/login", status=401
    )

    result = await api.async_stop_charging("test123")
    assert result is False


@pytest.mark.asyncio
async def test_api_wrapper_client_error(hass, aioclient_mock, caplog):
    """Test API wrapper client error handling."""
    api = NexBlueApiClient("test", "test", async_get_clientsession(hass))

    # Mock client error
    aioclient_mock.get(
        "https://api.nexblue.com/third_party/openapi/chargers",
        exc=aiohttp.ClientError("Connection failed"),
    )

    result = await api.api_wrapper(
        "get", "https://api.nexblue.com/third_party/openapi/chargers"
    )
    assert result is None
    assert "Error fetching information" in caplog.text


@pytest.mark.asyncio
async def test_api_wrapper_exception(hass, aioclient_mock, caplog):
    """Test API wrapper general exception handling."""
    api = NexBlueApiClient("test", "test", async_get_clientsession(hass))

    # Mock general exception
    aioclient_mock.get(
        "https://api.nexblue.com/third_party/openapi/chargers",
        exc=Exception("Unexpected error"),
    )

    result = await api.api_wrapper(
        "get", "https://api.nexblue.com/third_party/openapi/chargers"
    )
    assert result is None
    assert "Something really wrong happened" in caplog.text


@pytest.mark.asyncio
async def test_api_empty_chargers_data(hass, aioclient_mock, caplog):
    """Test API with empty chargers data response."""
    api = NexBlueApiClient("test", "test", async_get_clientsession(hass))

    # Mock login success
    aioclient_mock.post(
        "https://api.nexblue.com/third_party/openapi/account/login",
        json={"access_token": "test_token", "refresh_token": "test_refresh"},
    )

    # Mock empty chargers data
    aioclient_mock.get(
        "https://api.nexblue.com/third_party/openapi/chargers", json={"data": []}
    )

    result = await api.async_get_data()
    assert "chargers" in result
    assert len(result["chargers"]) == 0


@pytest.mark.asyncio
async def test_api_token_expiration(hass, aioclient_mock, caplog):
    """Test API token expiration handling."""
    api = NexBlueApiClient("test", "test", async_get_clientsession(hass))

    # Set expired token
    api._access_token = "expired_token"
    api._refresh_token = "valid_refresh_token"
    api._token_expires_at = datetime.now() - timedelta(minutes=5)

    # Mock successful token refresh
    aioclient_mock.post(
        "https://api.nexblue.com/third_party/openapi/account/refresh_token",
        json={"access_token": "new_token", "refresh_token": "new_refresh"},
    )

    result = await api.async_ensure_token_valid()
    assert result is True
    assert api._access_token == "new_token"


@pytest.mark.asyncio
async def test_async_set_current_limit_success(hass, aioclient_mock, caplog):
    """Test successful current limit setting."""
    api = NexBlueApiClient("test", "test", async_get_clientsession(hass))

    # Mock login
    aioclient_mock.post(
        "https://api.nexblue.com/third_party/openapi/account/login",
        json={"access_token": "test_token", "refresh_token": "test_refresh"},
    )

    # Mock set_current_limit success
    aioclient_mock.post(
        "https://api.nexblue.com/third_party/openapi/chargers/test123/cmd/set_current_limit",
        json={"result": 0},
    )

    result = await api.async_set_current_limit("test123", 16)
    assert result is True
    assert "Successfully set current limit to 16A for charger test123" in caplog.text


@pytest.mark.asyncio
async def test_async_set_current_limit_api_failure(hass, aioclient_mock, caplog):
    """Test current limit setting with API failure."""
    api = NexBlueApiClient("test", "test", async_get_clientsession(hass))

    # Mock login
    aioclient_mock.post(
        "https://api.nexblue.com/third_party/openapi/account/login",
        json={"access_token": "test_token", "refresh_token": "test_refresh"},
    )

    # Mock set_current_limit failure
    aioclient_mock.post(
        "https://api.nexblue.com/third_party/openapi/chargers/test123/cmd/set_current_limit",
        json={"result": -1, "error": "Invalid current limit"},
    )

    result = await api.async_set_current_limit("test123", 16)
    assert result is False
    assert "Failed to set current limit" in caplog.text


@pytest.mark.asyncio
async def test_async_set_current_limit_auth_failure(hass, aioclient_mock, caplog):
    """Test current limit setting with authentication failure."""
    api = NexBlueApiClient("test", "test", async_get_clientsession(hass))

    # Mock login failure
    aioclient_mock.post(
        "https://api.nexblue.com/third_party/openapi/account/login", status=401
    )

    result = await api.async_set_current_limit("test123", 16)
    assert result is False
    assert "Failed to authenticate with NexBlue API" in caplog.text


@pytest.mark.asyncio
async def test_async_set_current_limit_exception(hass, aioclient_mock, caplog):
    """Test current limit setting with network exception."""
    api = NexBlueApiClient("test", "test", async_get_clientsession(hass))

    # Mock login
    aioclient_mock.post(
        "https://api.nexblue.com/third_party/openapi/account/login",
        json={"access_token": "test_token", "refresh_token": "test_refresh"},
    )

    # Mock network exception
    aioclient_mock.post(
        "https://api.nexblue.com/third_party/openapi/chargers/test123/cmd/set_current_limit",
        exc=aiohttp.ClientError("Network error"),
    )

    result = await api.async_set_current_limit("test123", 16)
    assert result is False
    assert "Failed to set current limit" in caplog.text


@pytest.mark.asyncio
async def test_async_set_current_limit_boundary_values(hass, aioclient_mock, caplog):
    """Test current limit setting with boundary values."""
    api = NexBlueApiClient("test", "test", async_get_clientsession(hass))

    # Mock login
    aioclient_mock.post(
        "https://api.nexblue.com/third_party/openapi/account/login",
        json={"access_token": "test_token", "refresh_token": "test_refresh"},
    )

    # Mock set_current_limit success for boundary values
    aioclient_mock.post(
        "https://api.nexblue.com/third_party/openapi/chargers/test123/cmd/set_current_limit",
        json={"result": 0},
    )

    # Test minimum value (6A)
    result = await api.async_set_current_limit("test123", 6)
    assert result is True

    # Test maximum value (32A)
    result = await api.async_set_current_limit("test123", 32)
    assert result is True


@pytest.mark.asyncio
async def test_api_invalid_response_format(hass, aioclient_mock, caplog):
    """Test API with invalid response format."""
    api = NexBlueApiClient("test", "test", async_get_clientsession(hass))

    # Mock login success
    aioclient_mock.post(
        "https://api.nexblue.com/third_party/openapi/account/login",
        json={"access_token": "test_token", "refresh_token": "test_refresh"},
    )

    # Mock invalid response format (missing 'data' key)
    aioclient_mock.get(
        "https://api.nexblue.com/third_party/openapi/chargers",
        json={"chargers": []},  # Wrong format - should be 'data'
    )

    result = await api.async_get_data()
    assert result == {}
    assert "Invalid response format" in caplog.text


@pytest.mark.asyncio
async def test_api_no_refresh_token(hass, aioclient_mock, caplog):
    """Test API with no refresh token available."""
    api = NexBlueApiClient("test", "test", async_get_clientsession(hass))

    # Set expired token but no refresh token
    api._access_token = "expired_token"
    api._refresh_token = None
    api._token_expires_at = datetime.now() - timedelta(minutes=5)

    # Mock login fallback
    aioclient_mock.post(
        "https://api.nexblue.com/third_party/openapi/account/login",
        json={"access_token": "new_token", "refresh_token": "new_refresh"},
    )

    result = await api.async_ensure_token_valid()
    assert result is True
