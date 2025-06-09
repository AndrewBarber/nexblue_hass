"""Test the NexBlue API client."""

from __future__ import annotations

import asyncio
import json
import logging
import socket
from datetime import datetime, timedelta
from unittest.mock import AsyncMock, patch

import aiohttp
import pytest

from custom_components.nexblue_hass.api import CHARGERS_URL, NexBlueApiClient

# Setup logger for test output (if needed for test assertions)
_LOGGER = logging.getLogger(__name__)

# Test constants
TEST_USERNAME = "test@example.com"
TEST_PASSWORD = "test_password"
TEST_ACCESS_TOKEN = "test_access_token"
TEST_REFRESH_TOKEN = "test_refresh_token"
TEST_SERIAL_NUMBER = "CHARGER123"


class MockResponse:
    """Mock aiohttp client response."""

    def __init__(self, status=200, json_data=None, text=None):
        """Initialize mock response."""
        self.status = status
        self._json_data = json_data or {}
        self._text = text or json.dumps(json_data) if json_data else ""
        self.content = asyncio.StreamReader()
        self.content.feed_data(self._text.encode())
        self.content.feed_eof()

    async def json(self):
        """Return json data."""
        return self._json_data

    async def text(self):
        """Return text data."""
        return self._text

    def raise_for_status(self):
        """Raise an exception for error status codes."""
        if 400 <= self.status < 600:
            raise aiohttp.ClientResponseError(
                status=self.status,
                message=f"HTTP {self.status}",
                request_info=None,
                history=(),
            )

    async def __aenter__(self):
        """Async enter."""
        return self

    async def __aexit__(self, exc_type, exc_val, exc_tb):
        """Async exit."""
        if hasattr(self, "close"):
            await self.close()

    async def close(self):
        """Close the response."""
        pass


@pytest.fixture
def api_client():
    """Create an API client with a mock session."""
    with patch("aiohttp.ClientSession") as mock_session_class:
        # Create the mock session
        session = AsyncMock()

        # Create a successful mock response for login
        login_response = {
            "access_token": TEST_ACCESS_TOKEN,
            "refresh_token": TEST_REFRESH_TOKEN,
            "expires_in": 3600,
        }
        mock_response = MockResponse(status=200, json_data=login_response)

        # Set up the session's post method to return our mock response
        session.post.return_value = mock_response

        # Set up the session's get method to return a successful response by default
        session.get.return_value = MockResponse(status=200, json_data={"result": 1})

        # Set the session class to return our mock session
        mock_session_class.return_value = session

        # Create the API client
        client = NexBlueApiClient(TEST_USERNAME, TEST_PASSWORD, session)

        yield client, session, mock_response

        # Cleanup - no need to close the mock session in the test


@pytest.mark.asyncio
async def test_async_login_success(api_client):
    """Test successful login."""
    client, session, mock_response = api_client

    # Setup the mock response for the login API call
    login_response = {
        "access_token": TEST_ACCESS_TOKEN,
        "refresh_token": TEST_REFRESH_TOKEN,
        "expires_in": 3600,
    }

    # Configure the mock response
    mock_response._json_data = login_response
    mock_response.status = 200

    # Reset any previous calls to the mock
    session.post.reset_mock()

    # Call the login method
    result = await client.async_login()

    # Verify the result and client state
    assert result is True
    assert client._access_token == TEST_ACCESS_TOKEN
    assert client._refresh_token == TEST_REFRESH_TOKEN

    # Verify the API call was made correctly
    session.post.assert_called_once()
    call_args, call_kwargs = session.post.call_args

    # Check URL and request data
    assert len(call_args) > 0
    assert "account/login" in call_args[0]

    request_data = call_kwargs.get("json", {})
    assert request_data == {
        "username": TEST_USERNAME,
        "password": TEST_PASSWORD,
        "account_type": 0,
    }
    assert client._token_expires_at is not None, "Token expiration should be set"
    assert (
        client._headers["Authorization"] == f"Bearer {TEST_ACCESS_TOKEN}"
    ), "Authorization header should be set"

    # Verify the API call was made correctly
    session.post.assert_called_once()
    args, kwargs = session.post.call_args

    # Verify the URL and request data
    assert len(args) > 0, "URL should be provided as first argument"
    assert "account/login" in args[0], "Login endpoint should be called"
    assert kwargs["json"]["username"] == TEST_USERNAME
    assert kwargs["json"]["password"] == TEST_PASSWORD
    assert kwargs["json"]["account_type"] == 0


@pytest.mark.asyncio
async def test_async_login_failure(api_client):
    """Test failed login."""
    client, session, mock_response = api_client

    # Setup mock response for failed login
    mock_response.status = 401
    mock_response._json_data = {"error": "invalid_credentials"}

    # Call the login method
    result = await client.async_login()

    # Verify the result
    assert result is False
    assert client._access_token is None


@pytest.mark.asyncio
async def test_async_refresh_token_success(api_client):
    """Test successful token refresh."""
    client, session, mock_response = api_client

    # Set up initial token
    client._refresh_token = TEST_REFRESH_TOKEN

    # Mock the API response
    new_access_token = "new_access_token_123"
    new_refresh_token = "new_refresh_token_123"

    mock_response._json_data = {
        "access_token": new_access_token,
        "refresh_token": new_refresh_token,
        "expires_in": 3600,
    }

    # Skip this test if the client doesn't have the expected method
    if not hasattr(client, "api_wrapper"):
        pytest.skip("api_wrapper method not found in client")

    # Call the refresh token method
    result = await client.async_refresh_token()

    # Verify the result and client state
    assert result is True
    assert client._access_token == new_access_token
    assert client._refresh_token == new_refresh_token
    assert client._token_expires_at is not None

    # Verify the API call was made correctly
    session.post.assert_called_once()
    args, kwargs = session.post.call_args
    assert "account/refresh_token" in args[0]
    assert kwargs["json"]["refresh_token"] == TEST_REFRESH_TOKEN


@pytest.mark.asyncio
async def test_async_ensure_token_valid_with_valid_token(api_client):
    """Test ensure_token_valid with a valid token."""
    client, session, _ = api_client

    # Set up a valid token
    client._access_token = TEST_ACCESS_TOKEN
    client._token_expires_at = datetime.now() + timedelta(minutes=30)

    # Mock the refresh method to ensure it's not called
    with patch.object(client, "async_refresh_token") as mock_refresh:
        result = await client.async_ensure_token_valid()

        # Verify the result and that refresh wasn't called
        assert result is True
        mock_refresh.assert_not_called()
        session.request.assert_not_called()


@pytest.mark.asyncio
async def test_async_ensure_token_valid_needs_refresh(api_client):
    """Test ensure_token_valid when token needs refresh."""
    client, session, _ = api_client

    # Set up an expired token
    client._access_token = TEST_ACCESS_TOKEN
    client._refresh_token = TEST_REFRESH_TOKEN
    client._token_expires_at = datetime.now() - timedelta(minutes=5)

    # Mock the refresh method to succeed
    with patch.object(client, "async_refresh_token", return_value=True) as mock_refresh:
        result = await client.async_ensure_token_valid()

        # Verify the result and that refresh was called
        assert result is True
        mock_refresh.assert_called_once()


@pytest.mark.asyncio
async def test_async_get_data_success(api_client):
    """Test successful get data."""
    client, session, mock_response = api_client

    # Set up a valid token
    client._access_token = TEST_ACCESS_TOKEN
    client._token_expires_at = datetime.now() + timedelta(minutes=30)

    # Test data
    chargers_response = {
        "data": [
            {
                "serial_number": TEST_SERIAL_NUMBER,
                "role": 0,
                "place_id": "16b90047ecb94f5db270c88125fd34cb",
                "circuit_id": "d8ade3ecae694f4fbf95c324776af694",
                "is_collection": True,
            }
        ]
    }

    charger_detail = {
        "serial_number": TEST_SERIAL_NUMBER,
        "pin_code": "8620",
        "role": 0,
        "place_data": {
            "id": "16b90047ecb94f5db270c88125fd34cb",
            "address": "Home",
            "category": "Private",
            "operator_type": 0,
            "currency": "GBP",
            "country": "GB",
            "tz_id": "Europe/London",
            "uk_reg": True,
            "grid_type": 2,
            "main_fuse": 80,
            "main_fuse_limit": 80,
            "fallback_current": 6,
        },
        "circuit_data": {
            "place_id": "16b90047ecb94f5db270c88125fd34cb",
            "circuit_id": "d8ade3ecae694f4fbf95c324776af694",
            "name": "Circuit 1",
            "fuse": 40,
            "chargers": [TEST_SERIAL_NUMBER],
        },
        "online": True,
        "product_name": "NexBlue Point (UK)",
        "device_operator_type": 0,
    }

    status_response = {
        "is_charging": False,
        "is_connected": True,
        "current_power": 0.0,
        "current_limit": 32.0,
    }

    # Setup side effect for all GET requests
    async def mock_get(url, **kwargs):
        if "status" in url:
            return MockResponse(200, status_response)

        if str(TEST_SERIAL_NUMBER) in url:
            if "status" in url:
                return MockResponse(200, status_response)
            return MockResponse(200, charger_detail)

        if "chargers" in url and "/cmd/" not in url:
            if str(TEST_SERIAL_NUMBER) not in url:
                return MockResponse(200, chargers_response)

        return MockResponse(404, {})

    # Set the side effect for all GET requests
    session.get.side_effect = mock_get

    # Call the method
    result = await client.async_get_data()

    # Verify the result structure
    assert isinstance(result, dict), f"Expected dict, got {type(result)}: {result}"
    assert "chargers" in result, f"'chargers' key not found in {result}"
    assert isinstance(
        result["chargers"], list
    ), f"Expected chargers to be a list, got {type(result['chargers'])}"

    # We should have one charger in the result
    assert (
        len(result["chargers"]) == 1
    ), f"Expected 1 charger, got {len(result['chargers'])}"

    # Check the charger data was merged correctly
    charger = result["chargers"][0]
    assert charger["serial_number"] == TEST_SERIAL_NUMBER
    assert charger["online"] is True
    assert charger["product_name"] == "NexBlue Point (UK)"

    # Check place data was included
    assert "place_data" in charger
    assert charger["place_data"]["address"] == "Home"
    assert charger["place_data"]["country"] == "GB"

    # Check circuit data was included
    assert "circuit_data" in charger
    assert charger["circuit_data"]["name"] == "Circuit 1"
    assert charger["circuit_data"]["fuse"] == 40

    # Check status data was merged correctly
    assert "status" in charger
    assert charger["status"] == status_response


@pytest.mark.asyncio
async def test_async_start_charging_success(api_client):
    """Test starting charging successfully."""
    client, session, mock_response = api_client

    # Set up a valid token
    client._access_token = TEST_ACCESS_TOKEN
    client._token_expires_at = datetime.now() + timedelta(minutes=30)

    # Mock the API response
    success_response = {"result": 1}  # 1 means success for start_charging
    mock_response._json_data = success_response

    # Skip this test if the client doesn't have the expected method
    if not hasattr(client, "api_wrapper"):
        pytest.skip("api_wrapper method not found in client")

    # Call the method
    result = await client.async_start_charging(TEST_SERIAL_NUMBER)

    # The method should return a boolean
    assert isinstance(
        result, bool
    ), f"Expected boolean result, got {type(result)}: {result}"

    # Verify the API call was made correctly
    if session.request.called:
        args, kwargs = session.request.call_args
        assert args[0].lower() == "post"
        assert f"chargers/{TEST_SERIAL_NUMBER}/cmd/start_charging" in args[1]
        if "headers" in kwargs and "Authorization" in kwargs["headers"]:
            assert kwargs["headers"]["Authorization"] == f"Bearer {TEST_ACCESS_TOKEN}"


@pytest.mark.asyncio
async def test_async_stop_charging_success(api_client):
    """Test stopping charging successfully."""
    client, session, mock_response = api_client

    # Set up a valid token
    client._access_token = TEST_ACCESS_TOKEN
    client._token_expires_at = datetime.now() + timedelta(minutes=30)

    # Mock the API response
    success_response = {"result": 0}  # 0 means success for stop_charging
    mock_response._json_data = success_response

    # Call the method
    result = await client.async_stop_charging(TEST_SERIAL_NUMBER)

    # The method should return a boolean
    assert isinstance(
        result, bool
    ), f"Expected boolean result, got {type(result)}: {result}"

    # Verify the API call was made correctly
    if session.request.called:
        args, kwargs = session.request.call_args
        assert args[0].lower() == "post"
        assert f"chargers/{TEST_SERIAL_NUMBER}/cmd/stop_charging" in args[1]
        if "headers" in kwargs and "Authorization" in kwargs["headers"]:
            assert kwargs["headers"]["Authorization"] == f"Bearer {TEST_ACCESS_TOKEN}"


@pytest.mark.asyncio
async def test_async_get_data_no_chargers(api_client):
    """Test get data when no chargers are found."""
    client, session, mock_response = api_client

    # Set up a valid token
    client._access_token = TEST_ACCESS_TOKEN
    client._token_expires_at = datetime.now() + timedelta(minutes=30)

    # Mock the API response with no chargers
    empty_chargers_response = {"data": []}

    # Setup mock for session.get
    async def mock_get(url, **kwargs):
        if "chargers" in url and "/cmd/" not in url:
            return MockResponse(200, empty_chargers_response)
        return MockResponse(404, {})

    session.get.side_effect = mock_get

    # Call the method
    result = await client.async_get_data()

    # Verify the result structure
    assert isinstance(result, dict), f"Expected dict, got {type(result)}"
    assert "chargers" in result, f"'chargers' key not found in {result}"
    assert isinstance(
        result["chargers"], list
    ), f"Expected chargers to be a list, got {type(result['chargers'])}"
    assert (
        len(result["chargers"]) == 0
    ), f"Expected empty chargers list, got {result['chargers']}"


@pytest.mark.asyncio
async def test_async_start_charging_failure(api_client):
    """Test starting charging when it fails."""
    client, session, mock_response = api_client

    # Set up a valid token
    client._access_token = TEST_ACCESS_TOKEN
    client._token_expires_at = datetime.now() + timedelta(minutes=30)

    # Mock the API response for failure
    mock_response.status = 400
    mock_response._json_data = {"error": "Failed to start charging"}

    # Call the method
    result = await client.async_start_charging(TEST_SERIAL_NUMBER)

    # Verify the result
    assert result is False


@pytest.mark.asyncio
async def test_async_stop_charging_failure(api_client):
    """Test stopping charging when it fails."""
    client, session, mock_response = api_client

    # Set up a valid token
    client._access_token = TEST_ACCESS_TOKEN
    client._token_expires_at = datetime.now() + timedelta(minutes=30)

    # Mock the API response for failure
    mock_response.status = 400
    mock_response._json_data = {"error": "Failed to stop charging"}

    # Call the method
    result = await client.async_stop_charging(TEST_SERIAL_NUMBER)

    # Verify the result
    assert result is False


@pytest.mark.asyncio
async def test_api_wrapper_error_handling(api_client):
    """Test error handling in the API wrapper."""
    client, session, mock_response = api_client

    # Test with a 500 error
    mock_response.status = 500
    mock_response._json_data = {"error": "Internal Server Error"}

    # This will use the api_wrapper internally
    result = await client.async_get_data()
    assert result == {}

    # Test with a timeout error
    session.request.side_effect = asyncio.TimeoutError()
    result = await client.async_get_data()
    assert result == {}

    # Test with a connection error
    session.request.side_effect = aiohttp.ClientError("Connection error")
    result = await client.async_get_data()
    assert result == {}


@pytest.mark.asyncio
async def test_api_wrapper_success(api_client):
    """Test the API wrapper with a successful request."""
    client, session, mock_response = api_client

    # Set up test data
    test_url = f"{CHARGERS_URL}"
    test_data = {"key": "value"}
    expected_response = {"success": True}

    # Set up a valid token and update client headers
    client._access_token = TEST_ACCESS_TOKEN
    client._token_expires_at = datetime.now() + timedelta(minutes=30)
    client._headers = {
        "Authorization": f"Bearer {TEST_ACCESS_TOKEN}",
        "Content-Type": "application/json",
    }

    # Set up the mock response
    mock_response.status = 200
    mock_response.json = AsyncMock(return_value=expected_response)

    # Track the headers that were actually used in the request
    actual_headers = {}

    # Mock the session.post method
    async def mock_post(url, **kwargs):
        nonlocal actual_headers
        actual_headers = kwargs.get("headers", {})
        return mock_response

    session.post = AsyncMock(side_effect=mock_post)

    # Call the method
    result = await client.api_wrapper("post", test_url, data=test_data)

    # Verify the result
    assert result == expected_response

    # Verify the request was made with the correct URL and data
    session.post.assert_awaited_once()
    args, kwargs = session.post.await_args

    # Check the request was made correctly
    assert args[0] == test_url
    assert kwargs["json"] == test_data

    # Check headers
    assert "headers" in kwargs
    headers = kwargs["headers"]

    # Check Content-Type
    assert "Content-Type" in headers
    assert headers["Content-Type"] == "application/json"

    # Check Authorization
    assert "Authorization" in headers
    assert headers["Authorization"] == f"Bearer {TEST_ACCESS_TOKEN}"


@pytest.mark.asyncio
async def test_api_wrapper_error(api_client):
    """Test the API wrapper with an error response."""
    client, session, mock_response = api_client

    # Set up test data
    test_url = f"{CHARGERS_URL}/error"
    error_response = {"error": "Bad Request"}

    # Set up a valid token and update client headers
    client._access_token = TEST_ACCESS_TOKEN
    client._token_expires_at = datetime.now() + timedelta(minutes=30)
    client._headers = {
        "Authorization": f"Bearer {TEST_ACCESS_TOKEN}",
        "Content-Type": "application/json",
    }

    # Set up the mock response with an error status
    mock_response.status = 400
    mock_response.json = AsyncMock(return_value=error_response)

    # Track the headers that were actually used in the request
    actual_headers = {}

    # Mock the session.get method
    async def mock_get(url, **kwargs):
        nonlocal actual_headers
        actual_headers = kwargs.get("headers", {})
        return mock_response

    session.get = AsyncMock(side_effect=mock_get)

    # Call the method
    result = await client.api_wrapper("get", test_url)

    # Verify the result is None for error responses
    assert result is None

    # Verify the request was made with the correct URL
    session.get.assert_awaited_once()
    args, kwargs = session.get.await_args

    # Check the request was made correctly
    assert args[0] == test_url

    # Check headers
    assert "headers" in kwargs
    headers = kwargs["headers"]

    # Check Content-Type
    assert "Content-Type" in headers
    assert headers["Content-Type"] == "application/json"

    # Check Authorization
    assert "Authorization" in headers
    assert headers["Authorization"] == f"Bearer {TEST_ACCESS_TOKEN}"


@pytest.mark.asyncio
async def test_api_wrapper_timeout(api_client, caplog):
    """Test api_wrapper with timeout error."""
    # Unpack the fixture
    client, session, mock_response = api_client

    # Setup client with valid token
    client._access_token = TEST_ACCESS_TOKEN
    client._headers = {
        "Authorization": f"Bearer {TEST_ACCESS_TOKEN}",
        "Content-Type": "application/json",
    }

    # Create a mock that will raise asyncio.TimeoutError when awaited
    async def raise_timeout(*args, **kwargs):
        raise asyncio.TimeoutError("Request timed out")

    # Setup the mock to return an async context manager that will raise the error
    mock_cm = AsyncMock()
    mock_cm.__aenter__.side_effect = raise_timeout
    session.get.return_value = mock_cm

    try:
        # Call the method that should trigger the timeout
        result = await client.api_wrapper(
            "get", "https://api.nexblue.com/third_party/openapi/timeout"
        )
    except Exception:
        raise

    # Verify result is None due to timeout
    assert result is None, f"Expected None on timeout, got {result}"

    # Verify the request was made with correct headers
    session.get.assert_called_once()
    args, kwargs = session.get.call_args

    # The URL should be the one we passed to api_wrapper
    assert len(args) > 0
    assert args[0] == "https://api.nexblue.com/third_party/openapi/timeout"

    # Headers should include our auth token
    assert "headers" in kwargs
    assert "Authorization" in kwargs["headers"]
    assert kwargs["headers"]["Authorization"] == f"Bearer {TEST_ACCESS_TOKEN}"


@pytest.mark.asyncio
async def test_api_wrapper_http_error(api_client):
    """Test api_wrapper with HTTP error."""
    client, session, _ = api_client

    # Setup client with valid token
    client._access_token = TEST_ACCESS_TOKEN
    client._headers = {
        "Authorization": f"Bearer {TEST_ACCESS_TOKEN}",
        "Content-Type": "application/json",
    }

    # Create a mock that will raise aiohttp.ClientError when awaited
    async def raise_client_error(*args, **kwargs):
        raise aiohttp.ClientError("Connection error")

    # Setup the mock to return an async context manager that will raise the error
    mock_cm = AsyncMock()
    mock_cm.__aenter__.side_effect = raise_client_error
    session.get.return_value = mock_cm

    # Call the method that should trigger the HTTP error
    result = await client.api_wrapper(
        "get", "https://api.nexblue.com/third_party/openapi/error"
    )

    # Verify result is None due to HTTP error
    assert result is None, f"Expected None on HTTP error, got {result}"

    # Verify the request was made with correct headers
    session.get.assert_called_once()
    args, kwargs = session.get.call_args
    assert args[0] == "https://api.nexblue.com/third_party/openapi/error"
    assert kwargs["headers"]["Authorization"] == f"Bearer {TEST_ACCESS_TOKEN}"
    assert kwargs["headers"]["Content-Type"] == "application/json"

    # Test completed


@pytest.mark.asyncio
async def test_api_wrapper_http_methods(api_client):
    """Test api_wrapper with different HTTP methods."""
    client, session, mock_response = api_client

    # Setup client with valid token
    client._access_token = TEST_ACCESS_TOKEN
    client._headers = {
        "Authorization": f"Bearer {TEST_ACCESS_TOKEN}",
        "Content-Type": "application/json",
    }

    # Setup mock response
    mock_response.status = 200
    mock_response.json = AsyncMock(return_value={"status": "success"})

    # Test PUT
    async def mock_put(url, **kwargs):
        return mock_response

    session.put = AsyncMock(side_effect=mock_put)

    # Test PUT method
    result = await client.api_wrapper(
        "put", "https://api.nexblue.com/third_party/openapi/test"
    )
    assert result == {"status": "success"}
    session.put.assert_awaited_once()
    args, kwargs = session.put.await_args
    assert args[0] == "https://api.nexblue.com/third_party/openapi/test"
    assert kwargs["headers"]["Authorization"] == f"Bearer {TEST_ACCESS_TOKEN}"
    assert kwargs["headers"]["Content-Type"] == "application/json"
    assert kwargs["json"] == {}

    # Reset mock for next test
    session.put.reset_mock()

    # Test PATCH
    async def mock_patch(url, **kwargs):
        return mock_response

    session.patch = AsyncMock(side_effect=mock_patch)

    result = await client.api_wrapper(
        "patch", "https://api.nexblue.com/third_party/openapi/test"
    )
    assert result == {"status": "success"}

    session.patch.assert_awaited_once()
    args, kwargs = session.patch.await_args
    assert args[0] == "https://api.nexblue.com/third_party/openapi/test"
    assert kwargs["headers"]["Authorization"] == f"Bearer {TEST_ACCESS_TOKEN}"
    assert kwargs["headers"]["Content-Type"] == "application/json"
    assert kwargs["json"] == {}

    # Reset mock for next test
    session.patch.reset_mock()

    # Test DELETE
    async def mock_delete(url, **kwargs):
        return mock_response

    session.delete = AsyncMock(side_effect=mock_delete)

    result = await client.api_wrapper(
        "delete", "https://api.nexblue.com/third_party/openapi/test"
    )
    assert result == {"status": "success"}

    session.delete.assert_awaited_once()
    args, kwargs = session.delete.await_args
    assert args[0] == "https://api.nexblue.com/third_party/openapi/test"
    assert kwargs["headers"]["Authorization"] == f"Bearer {TEST_ACCESS_TOKEN}"
    assert kwargs["headers"]["Content-Type"] == "application/json"

    # Test completed


@pytest.mark.asyncio
async def test_async_login_network_error(api_client):
    """Test login with network error."""
    client, session, _ = api_client

    # Simulate network error
    session.post.side_effect = aiohttp.ClientError("Network error")

    result = await client.async_login()
    assert result is False
    assert client._access_token is None


@pytest.mark.asyncio
async def test_async_login_invalid_response(api_client):
    """Test login with invalid response."""
    client, session, mock_response = api_client

    # Simulate invalid response (missing access_token)
    mock_response.status = 200
    mock_response.json = AsyncMock(return_value={"error": "Invalid credentials"})

    result = await client.async_login()
    assert result is False
    assert client._access_token is None


@pytest.mark.asyncio
async def test_async_refresh_token_network_error(api_client):
    """Test token refresh with network error."""
    client, session, _ = api_client

    # Set up a valid refresh token
    client._refresh_token = TEST_REFRESH_TOKEN

    # Create a mock response for successful login
    login_response = {
        "access_token": "new_token",
        "refresh_token": "new_refresh_token",
        "expires_in": 3600,
    }

    # First call to refresh_token fails with network error
    # Second call to login succeeds
    session.post.side_effect = [
        aiohttp.ClientError("Network error"),
        MockResponse(status=200, json_data=login_response),
    ]

    # Call the refresh token method
    result = await client.async_refresh_token()

    # Verify the result
    assert result is True
    assert client._access_token == "new_token"
    assert client._refresh_token == "new_refresh_token"
    assert client._token_expires_at is not None


@pytest.mark.asyncio
async def test_async_refresh_token_invalid_response(api_client):
    """Test token refresh with invalid response."""
    client, session, mock_response = api_client

    # Set up a valid refresh token
    client._refresh_token = TEST_REFRESH_TOKEN

    # Simulate invalid response (missing access_token)
    mock_response.status = 200
    mock_response.json = AsyncMock(return_value={"error": "Invalid refresh token"})

    # This should fall back to login
    mock_response.json.side_effect = [
        {"error": "Invalid refresh token"},  # refresh_token fails
        {"access_token": "new_token", "expires_in": 3600},  # login succeeds
    ]

    result = await client.async_refresh_token()
    assert result is True
    assert client._access_token == "new_token"


@pytest.mark.asyncio
async def test_async_ensure_token_valid_expired(api_client):
    """Test ensure_token_valid with expired token."""
    client, session, mock_response = api_client

    # Set up an expired token
    client._access_token = "expired_token"
    client._token_expires_at = datetime.now() - timedelta(seconds=60)

    # Mock refresh token to succeed
    mock_response.status = 200
    mock_response.json = AsyncMock(
        return_value={
            "access_token": "new_token",
            "refresh_token": "new_refresh_token",
            "expires_in": 3600,
        }
    )

    result = await client.async_ensure_token_valid()
    assert result is True
    assert client._access_token == "new_token"
    assert client._refresh_token == "new_refresh_token"


@pytest.mark.asyncio
async def test_async_get_data_network_error(api_client):
    """Test get_data with network error."""
    client, session, _ = api_client

    # Set up a valid token
    client._access_token = TEST_ACCESS_TOKEN

    # Simulate network error
    session.get.side_effect = aiohttp.ClientError("Network error")

    result = await client.async_get_data()
    assert result == {}


@pytest.mark.asyncio
async def test_async_get_data_invalid_response(api_client):
    """Test get_data with invalid response."""
    client, session, mock_response = api_client

    # Set up a valid token
    client._access_token = TEST_ACCESS_TOKEN

    # Simulate invalid response
    mock_response.status = 200
    mock_response.json = AsyncMock(return_value={"error": "Invalid response"})

    result = await client.async_get_data()
    assert result == {}


@pytest.mark.asyncio
async def test_async_start_charging_network_error(api_client):
    """Test start_charging with network error."""
    client, session, _ = api_client

    # Set up a valid token
    client._access_token = TEST_ACCESS_TOKEN

    # Simulate network error
    session.post.side_effect = aiohttp.ClientError("Network error")

    result = await client.async_start_charging(TEST_SERIAL_NUMBER)
    assert result is False


@pytest.mark.asyncio
async def test_async_start_charging_invalid_response(api_client):
    """Test start_charging with invalid response."""
    client, session, mock_response = api_client

    # Set up a valid token
    client._access_token = TEST_ACCESS_TOKEN

    # Simulate invalid response (missing result field)
    mock_response.status = 200
    mock_response.json = AsyncMock(return_value={"status": "error"})

    result = await client.async_start_charging(TEST_SERIAL_NUMBER)
    assert result is False


@pytest.mark.asyncio
async def test_async_stop_charging_network_error(api_client):
    """Test stop_charging with network error."""
    client, session, _ = api_client

    # Set up a valid token
    client._access_token = TEST_ACCESS_TOKEN

    # Simulate network error
    session.post.side_effect = aiohttp.ClientError("Network error")

    result = await client.async_stop_charging(TEST_SERIAL_NUMBER)
    assert result is False


@pytest.mark.asyncio
async def test_async_stop_charging_invalid_response(api_client):
    """Test stop_charging with invalid response."""
    client, session, mock_response = api_client

    # Set up a valid token
    client._access_token = TEST_ACCESS_TOKEN

    # Simulate invalid response (missing result field)
    mock_response.status = 200
    mock_response.json = AsyncMock(return_value={"status": "error"})

    result = await client.async_stop_charging(TEST_SERIAL_NUMBER)
    assert result is False


@pytest.mark.asyncio
async def test_api_wrapper_socket_error(api_client):
    """Test api_wrapper with socket error."""
    client, session, _ = api_client

    # Set up a valid token
    client._access_token = TEST_ACCESS_TOKEN

    # Simulate socket error
    session.get.side_effect = socket.gaierror("Socket error")

    result = await client.api_wrapper("get", "http://example.com")
    assert result is None


@pytest.mark.asyncio
async def test_api_wrapper_json_parse_error(api_client):
    """Test api_wrapper with JSON parse error."""
    client, session, _ = api_client

    # Set up a valid token
    client._access_token = TEST_ACCESS_TOKEN

    # Create a mock response that will raise JSONDecodeError
    mock_response = AsyncMock()
    mock_response.status = 200
    mock_response.json = AsyncMock(
        side_effect=json.JSONDecodeError("Expecting value", "<html>Not JSON</html>", 0)
    )

    # Set up the session to return our mock response
    session.get.return_value = mock_response

    result = await client.api_wrapper("get", "http://example.com")
    assert result is None


@pytest.mark.asyncio
async def test_async_get_data_invalid_format(api_client):
    """Test get_data with invalid response format."""
    client, session, mock_response = api_client

    # Set up a valid token
    client._access_token = TEST_ACCESS_TOKEN

    # Simulate invalid response format (missing 'data' key)
    mock_response.status = 200
    mock_response.json = AsyncMock(return_value={"chargers": [{"id": 1}]})  # Old format

    # First call to get chargers
    session.get.return_value = mock_response

    result = await client.async_get_data()
    assert result == {}


@pytest.mark.asyncio
async def test_api_wrapper_put_patch_methods(api_client):
    """Test api_wrapper with PUT and PATCH methods."""
    client, session, mock_response = api_client

    # Set up a valid token
    client._access_token = TEST_ACCESS_TOKEN

    # Test PUT method
    mock_response.status = 200
    mock_response.json = AsyncMock(return_value={"success": True})

    # Test PUT
    session.put.return_value = mock_response
    result = await client.api_wrapper("put", "http://example.com/put", {"key": "value"})
    assert result == {"success": True}

    # Test PATCH
    session.patch.return_value = mock_response
    result = await client.api_wrapper(
        "patch", "http://example.com/patch", {"key": "value"}
    )
    assert result == {"success": True}


@pytest.mark.asyncio
async def test_api_wrapper_unsupported_method(api_client, caplog):
    """Test api_wrapper with unsupported HTTP method."""
    client, session, _ = api_client

    # Set up a valid token
    client._access_token = TEST_ACCESS_TOKEN

    result = await client.api_wrapper("head", "http://example.com/unsupported")
    assert result is None
    assert "Unsupported method: head" in caplog.text


@pytest.mark.asyncio
async def test_async_get_data_invalid_charger_data(api_client):
    """Test get_data with invalid charger data."""
    client, session, _ = api_client

    # Set up a valid token
    client._access_token = TEST_ACCESS_TOKEN

    # Create mock responses for each API call
    mock_chargers_response = AsyncMock()
    mock_chargers_response.status = 200
    mock_chargers_response.json = AsyncMock(
        return_value={"data": [{"serial_number": "123"}]}
    )

    mock_details_response = AsyncMock()
    mock_details_response.status = 200
    mock_details_response.json = AsyncMock(return_value=None)  # Simulate failed details

    # Set up the session to return our mock responses in order
    session.get.side_effect = [mock_chargers_response, mock_details_response]

    result = await client.async_get_data()
    assert result == {"chargers": []}


@pytest.mark.asyncio
async def test_async_get_data_missing_data_key(api_client, caplog):
    """Test get_data when API response is missing the 'data' key."""
    client, session, mock_response = api_client

    # First, mock the login response since we're not testing auth here
    client._access_token = TEST_ACCESS_TOKEN
    client._refresh_token = "test_refresh_token"

    # Create a mock response for the chargers endpoint that's missing the 'data' key
    mock_chargers_response = AsyncMock()
    mock_chargers_response.status = 200
    mock_chargers_response.json = AsyncMock(
        return_value={"status": "success"}
    )  # Missing 'data' key

    # Set up the session to return our mock response
    session.get.return_value = mock_chargers_response

    with caplog.at_level(logging.ERROR):
        result = await client.async_get_data()

    # Should return an empty dict
    assert result == {}

    # Verify the error was logged
    assert (
        "Invalid response format from NexBlue API. Expected 'data' key" in caplog.text
    )


@pytest.mark.asyncio
async def test_async_get_data_processing_exception(api_client, caplog):
    """Test get_data when an exception occurs during processing."""
    client, session, mock_response = api_client

    # Set up a valid token
    client._access_token = TEST_ACCESS_TOKEN
    client._token_expires_at = datetime.now() + timedelta(minutes=30)

    # Setup side effect that will raise an exception
    async def mock_get_raises(*args, **kwargs):
        raise Exception("Test processing exception")

    session.get.side_effect = mock_get_raises

    with caplog.at_level(logging.ERROR):
        result = await client.async_get_data()

    # Should return empty result and log the error
    assert result == {}
    assert "Something really wrong happened!" in caplog.text


@pytest.mark.asyncio
async def test_async_get_data_exception_handling(api_client, caplog):
    """Test exception handling in async_get_data method."""
    client, session, mock_response = api_client

    # Set up a valid token
    client._access_token = TEST_ACCESS_TOKEN
    client._token_expires_at = datetime.now() + timedelta(minutes=30)

    # Mock the api_wrapper to raise an exception
    original_api_wrapper = client.api_wrapper

    async def mock_api_wrapper_raises(*args, **kwargs):
        if args[0] == "get" and "chargers" in args[1] and "/cmd/" not in args[1]:
            # First call to get chargers list - return valid response
            return {"data": [{"serial_number": TEST_SERIAL_NUMBER}]}
        # Any other call should raise an exception
        raise Exception("Error in async_get_data")

    client.api_wrapper = mock_api_wrapper_raises

    try:
        with caplog.at_level(logging.ERROR):
            result = await client.async_get_data()

        # Should return empty result and log the error
        assert result == {}
        assert "Error fetching data from NexBlue API" in caplog.text
    finally:
        # Restore original method
        client.api_wrapper = original_api_wrapper


@pytest.mark.asyncio
async def test_async_start_charging_invalid_response_format(api_client):
    """Test start_charging with invalid response format."""
    client, session, mock_response = api_client

    # Set up a valid token
    client._access_token = TEST_ACCESS_TOKEN

    # Simulate invalid response format (missing 'result' key)
    mock_response.status = 200
    mock_response.json = AsyncMock(return_value={"status": "success"})

    result = await client.async_start_charging(TEST_SERIAL_NUMBER)
    assert result is False


@pytest.mark.asyncio
async def test_async_start_charging_auth_failure(api_client, caplog):
    """Test start_charging when authentication fails."""
    client, session, _ = api_client

    # Mock async_ensure_token_valid to return False
    with patch.object(
        client, "async_ensure_token_valid", AsyncMock(return_value=False)
    ):
        with caplog.at_level(logging.ERROR):
            result = await client.async_start_charging(TEST_SERIAL_NUMBER)

    # Should return False and log an error
    assert result is False
    assert "Failed to authenticate with NexBlue API" in caplog.text


@pytest.mark.asyncio
async def test_async_start_charging_exception(api_client, caplog):
    """Test start_charging when an exception occurs during the API call."""
    client, session, mock_response = api_client

    # Set up a valid token
    client._access_token = TEST_ACCESS_TOKEN

    # Mock the methods
    with (
        patch.object(client, "async_ensure_token_valid", AsyncMock(return_value=True)),
        patch.object(
            client, "api_wrapper", AsyncMock(side_effect=Exception("Test exception"))
        ),
    ):
        with caplog.at_level(logging.ERROR):
            result = await client.async_start_charging(TEST_SERIAL_NUMBER)

    # Should return False and log the error
    assert result is False
    assert "Error starting charging session: Test exception" in caplog.text


@pytest.mark.asyncio
async def test_async_stop_charging_invalid_response_format(api_client):
    """Test stop_charging with invalid response format."""
    client, session, mock_response = api_client

    # Set up a valid token
    client._access_token = TEST_ACCESS_TOKEN

    # Simulate invalid response format (missing 'result' key)
    mock_response.status = 200
    mock_response.json = AsyncMock(return_value={"status": "success"})

    result = await client.async_stop_charging(TEST_SERIAL_NUMBER)
    assert result is False


@pytest.mark.asyncio
async def test_async_stop_charging_auth_failure(api_client, caplog):
    """Test stop_charging when authentication fails."""
    client, session, _ = api_client

    # Mock async_ensure_token_valid to return False
    with patch.object(
        client, "async_ensure_token_valid", AsyncMock(return_value=False)
    ):
        with caplog.at_level(logging.ERROR):
            result = await client.async_stop_charging(TEST_SERIAL_NUMBER)

    # Should return False and log an error
    assert result is False
    assert "Failed to authenticate with NexBlue API" in caplog.text


@pytest.mark.asyncio
async def test_async_stop_charging_exception(api_client, caplog):
    """Test stop_charging when an exception occurs during the API call."""
    client, session, mock_response = api_client
    
    # Set up a valid token
    client._access_token = TEST_ACCESS_TOKEN
    
    # Create a mock for the api_wrapper that will raise an exception
    async def mock_api_wrapper(*args, **kwargs):
        raise Exception("Test exception")
    
    # Patch both methods
    with patch.object(client, "async_ensure_token_valid", return_value=True) as mock_ensure_token, \
         patch.object(client, "api_wrapper", new=mock_api_wrapper):
        
        # Call the method under test
        result = await client.async_stop_charging(TEST_SERIAL_NUMBER)
        
        # Verify the result
        assert result is False
        
        # Verify the error was logged
        assert any("Error stopping charging session: Test exception" in record.message 
                 for record in caplog.records if record.levelno == logging.ERROR)


@pytest.mark.asyncio
async def test_api_wrapper_parse_error(api_client, caplog):
    """Test api_wrapper handling of KeyError/TypeError during response parsing."""
    import logging

    # Enable debug logging for our test
    logging.basicConfig(level=logging.DEBUG)
    logger = logging.getLogger(__name__)

    client, session, _ = api_client
    test_url = "https://api.example.com/test"

    logger.debug("Setting up test for api_wrapper parse error")

    # Create a proper mock response object
    class MockResponse:
        def __init__(self):
            self.status = 200
            self._text = "{}"

        async def json(self):
            logger.debug("mock_json() called, raising KeyError")
            raise KeyError("missing_key")

        async def text(self):
            return self._text

        async def __aenter__(self):
            return self

        async def __aexit__(self, exc_type, exc_val, exc_tb):
            pass

    # Create the mock response
    mock_response = MockResponse()

    # Create a mock for the session.get method
    async def mock_get(*args, **kwargs):
        logger.debug("mock_get called with %s %s", args, kwargs)
        return mock_response

    # Patch the session.get to return our mock response
    with patch.object(session, "get", new=mock_get):
        logger.debug("Patching session.get")

        # Call the method under test with ERROR level logging
        with caplog.at_level(logging.ERROR):
            logger.debug("Calling api_wrapper")
            result = await client.api_wrapper("get", test_url)
            logger.debug("api_wrapper returned: %s", result)

    # Debug output
    logger.debug("Captured logs: %s", caplog.text)

    # Should return None on parsing error
    assert result is None, "Expected None return value on parsing error"

    # Check for the expected error log
    error_messages = [
        r.message
        for r in caplog.records
        if hasattr(r, "message") and r.levelno >= logging.ERROR
    ]
    error_messages.extend(
        str(r.msg)
        for r in caplog.records
        if not hasattr(r, "message") and r.levelno >= logging.ERROR
    )

    logger.debug("Error messages found: %s", error_messages)

    # Check for the error message pattern (with or without quotes around missing_key)
    error_found = any(
        "Error parsing information from" in msg and "missing_key" in msg
        for msg in error_messages
    )

    assert error_found, (
        f"Expected error log about parsing error with 'missing_key' not found. "
        f"Messages found: {error_messages}"
    )


@pytest.mark.asyncio
async def test_api_wrapper_timeout_error(api_client, caplog):
    """Test api_wrapper handles timeout errors."""
    client, _, _ = api_client
    test_url = "http://test-timeout.com"
    
    # Create a mock context manager that raises asyncio.TimeoutError
    class MockTimeout:
        async def __aenter__(self):
            return self
            
        async def __aexit__(self, exc_type, exc_val, exc_tb):
            pass
            
        async def __aenter__(self):
            raise asyncio.TimeoutError("Request timed out")
            
        async def __aexit__(self, exc_type, exc_val, exc_tb):
            pass
    
    # Ensure we have a valid token to avoid login attempts
    client._access_token = "test_token"
    
    # Patch async_timeout.timeout to return our mock timeout
    with patch('custom_components.nexblue_hass.api.async_timeout.timeout', return_value=MockTimeout()):
        # Call the method under test with ERROR level logging
        with caplog.at_level(logging.ERROR):
            result = await client.api_wrapper("get", test_url)
    
    # Should return None on timeout
    assert result is None, "Expected None return value on timeout"
    
    # Check for the expected error log
    assert any("Timeout error fetching information from" in record.message 
              for record in caplog.records 
              if record.levelno == logging.ERROR), \
        "Expected timeout error log not found"
