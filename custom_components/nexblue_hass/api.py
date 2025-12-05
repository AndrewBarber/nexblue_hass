"""NexBlue API Client."""

import asyncio
import logging
import socket
from datetime import datetime, timedelta
from typing import Any, Dict, Optional

import aiohttp
import async_timeout

TIMEOUT = 10
# API endpoints based on the OpenAPI specification
API_BASE_URL = "https://api.nexblue.com/third_party/openapi"
LOGIN_URL = f"{API_BASE_URL}/account/login"
REFRESH_TOKEN_URL = f"{API_BASE_URL}/account/refresh_token"
CHARGERS_URL = f"{API_BASE_URL}/chargers"

_LOGGER: logging.Logger = logging.getLogger(__package__)

HEADERS = {"Content-Type": "application/json"}


class NexBlueApiClient:
    def __init__(
        self, username: str, password: str, session: aiohttp.ClientSession
    ) -> None:
        """NexBlue API Client."""
        self._username = username
        self._password = password
        self._session = session
        self._access_token = None
        self._refresh_token = None
        self._token_expires_at = None
        self._headers = HEADERS.copy()

    async def async_login(self) -> bool:
        """Login to NexBlue API and get auth token."""
        _LOGGER.debug("Logging in to NexBlue API")

        login_data = {
            "username": self._username,
            "password": self._password,
            "account_type": 0,  # 0 for end user, 1 for installer
        }

        response = await self.api_wrapper("post", LOGIN_URL, data=login_data)

        if response and "access_token" in response:
            self._access_token = response["access_token"]
            self._refresh_token = response.get("refresh_token")
            expires_in = response.get(
                "expires_in", 3600
            )  # Default to 1 hour if not provided

            # Calculate token expiration time (with a small buffer)
            self._token_expires_at = datetime.now() + timedelta(seconds=expires_in - 60)

            # Update headers with the new token
            self._headers["Authorization"] = f"Bearer {self._access_token}"

            _LOGGER.debug("Successfully logged in to NexBlue API")
            return True

        _LOGGER.error("Failed to login to NexBlue API: %s", response)
        return False

    async def async_refresh_token(self) -> bool:
        """Refresh the access token using the refresh token."""
        if not self._refresh_token:
            _LOGGER.debug("No refresh token available, need to login again")
            return await self.async_login()

        _LOGGER.debug("Refreshing NexBlue API token")

        refresh_data = {
            "refresh_token": self._refresh_token,
            "account_type": 0,  # 0 for end user, 1 for installer
        }

        response = await self.api_wrapper("post", REFRESH_TOKEN_URL, data=refresh_data)

        if response and "access_token" in response:
            self._access_token = response["access_token"]
            # Update refresh token if provided
            if "refresh_token" in response:
                self._refresh_token = response["refresh_token"]

            expires_in = response.get(
                "expires_in", 3600
            )  # Default to 1 hour if not provided

            # Calculate token expiration time (with a small buffer)
            self._token_expires_at = datetime.now() + timedelta(seconds=expires_in - 60)

            # Update headers with the new token
            self._headers["Authorization"] = f"Bearer {self._access_token}"

            _LOGGER.debug("Successfully refreshed NexBlue API token")
            return True

        _LOGGER.error("Failed to refresh token: %s", response)
        # If refresh fails, try logging in again
        return await self.async_login()

    async def async_ensure_token_valid(self) -> bool:
        """Ensure the access token is valid, refresh or login if needed."""
        # If we don't have a token or expiration time, login
        if not self._access_token or not self._token_expires_at:
            return await self.async_login()

        # If token is expired or about to expire, refresh it
        if datetime.now() >= self._token_expires_at:
            return await self.async_refresh_token()

        # Token is still valid
        return True

    async def async_get_data(self) -> dict:
        """Get data from the NexBlue API."""
        # Ensure we have a valid token before making API calls
        if not await self.async_ensure_token_valid():
            _LOGGER.error("Failed to authenticate with NexBlue API")
            return {}

        try:
            # Get list of chargers
            chargers_data = await self.api_wrapper("get", CHARGERS_URL)

            # Add detailed debug logging to see the actual response
            _LOGGER.debug("Chargers API response: %s", chargers_data)

            if not chargers_data:
                _LOGGER.error("No charger data received from NexBlue API")
                return {}

            # The API returns a 'data' key with an array of chargers instead of 'chargers'
            if "data" not in chargers_data:
                _LOGGER.error(
                    "Invalid response format from NexBlue API. Expected 'data' key, got: %s",
                    (
                        list(chargers_data.keys())
                        if isinstance(chargers_data, dict)
                        else type(chargers_data)
                    ),
                )
                return {}

            # For each charger, get detailed status
            result = {"chargers": []}

            for charger in chargers_data.get("data", []):
                charger_serial = charger.get("serial_number")
                if charger_serial:
                    # Get detailed status for this charger
                    detail_url = f"{CHARGERS_URL}/{charger_serial}"
                    detail_data = await self.api_wrapper("get", detail_url)

                    # Add detailed debug logging for charger details
                    _LOGGER.debug(
                        "Charger detail response for %s: %s",
                        charger_serial,
                        detail_data,
                    )

                    if detail_data:
                        # Get status data
                        status_url = f"{CHARGERS_URL}/{charger_serial}/cmd/status"
                        status_data = await self.api_wrapper("get", status_url)

                        # Add detailed debug logging for status data
                        _LOGGER.debug(
                            "Charger status response for %s: %s",
                            charger_serial,
                            status_data,
                        )

                        # Combine charger details with status data
                        charger_info = {**detail_data}
                        if status_data:
                            charger_info["status"] = status_data

                        result["chargers"].append(charger_info)

            return result

        except Exception as ex:
            _LOGGER.error("Error fetching data from NexBlue API: %s", ex)
            return {}

    async def async_start_charging(self, charger_serial: str) -> bool:
        """Start charging for a specific charger."""
        # Ensure we have a valid token before making API calls
        if not await self.async_ensure_token_valid():
            _LOGGER.error("Failed to authenticate with NexBlue API")
            return False

        try:
            # Send start charging command
            start_url = f"{CHARGERS_URL}/{charger_serial}/cmd/start_charging"
            response = await self.api_wrapper("post", start_url)

            # According to API spec, response contains a result field with status code
            # 0 = success for both start_charging and stop_charging commands
            if response and response.get("result", -1) == 0:
                _LOGGER.info(
                    "Successfully started charging for charger %s", charger_serial
                )
                return True
            else:
                _LOGGER.error("Failed to start charging session: %s", response)
                return False

        except Exception as ex:
            _LOGGER.error("Error starting charging session: %s", ex)
            return False

    async def async_stop_charging(self, charger_serial: str) -> bool:
        """Stop a charging session for a specific charger."""
        # Ensure we have a valid token before making API calls
        if not await self.async_ensure_token_valid():
            _LOGGER.error("Failed to authenticate with NexBlue API")
            return False

        try:
            stop_url = f"{CHARGERS_URL}/{charger_serial}/cmd/stop_charging"
            response = await self.api_wrapper("post", stop_url)

            # According to API spec, response contains a result field with status code
            # 0 means success
            if response and response.get("result", -1) == 0:
                _LOGGER.info(
                    "Successfully stopped charging session for charger %s",
                    charger_serial,
                )
                return True
            else:
                _LOGGER.error("Failed to stop charging session: %s", response)
                return False

        except Exception as ex:
            _LOGGER.error("Error stopping charging session: %s", ex)
            return False

    # Note: Advanced features like set_current_limit and get_schedule removed for v1
    # to focus on essential functionality and safety

    async def api_wrapper(
        self, method: str, url: str, data: dict = None, headers: dict = None
    ) -> Optional[Dict[str, Any]]:
        """Get information from the API."""
        method = method.lower()

        # Only default to empty dict for non-GET requests to avoid sending empty bodies
        if data is None and method != "get":
            data = {}
        if headers is None:
            headers = self._headers.copy() if self._access_token else HEADERS.copy()

        try:
            async with async_timeout.timeout(TIMEOUT):
                _LOGGER.debug(
                    "%s request to %s with data: %s", method.upper(), url, data
                )

                if method == "get":
                    # Remove Content-Type for GET requests to avoid servers expecting a body
                    get_headers = headers.copy()
                    get_headers.pop("Content-Type", None)
                    response = await self._session.get(url, headers=get_headers)

                elif method == "post":
                    response = await self._session.post(url, headers=headers, json=data)

                elif method == "put":
                    response = await self._session.put(url, headers=headers, json=data)

                elif method == "patch":
                    response = await self._session.patch(
                        url, headers=headers, json=data
                    )

                elif method == "delete":
                    response = await self._session.delete(url, headers=headers)
                else:
                    _LOGGER.error("Unsupported method: %s", method)
                    return None

                _LOGGER.debug("Response status: %s", response.status)

                if response.status in (200, 201):
                    return await response.json()
                else:
                    response_text = await response.text()
                    _LOGGER.error(
                        "Error response from API: %s - %s",
                        response.status,
                        response_text,
                    )
                    return None

        except asyncio.TimeoutError as exception:
            _LOGGER.error(
                "Timeout error fetching information from %s - %s",
                url,
                exception,
            )
            return None

        except (KeyError, TypeError) as exception:
            _LOGGER.error(
                "Error parsing information from %s - %s",
                url,
                exception,
            )
            return None

        except (aiohttp.ClientError, socket.gaierror) as exception:
            _LOGGER.error(
                "Error fetching information from %s - %s",
                url,
                exception,
            )
            return None

        except Exception as exception:  # pylint: disable=broad-except
            _LOGGER.error("Something really wrong happened! - %s", exception)
            return None
