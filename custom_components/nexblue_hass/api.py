"""NexBlue API Client."""
import asyncio
import logging
import socket
from datetime import datetime
from datetime import timedelta
from typing import Any
from typing import Dict
from typing import Optional

import aiohttp
import async_timeout

TIMEOUT = 10
API_BASE_URL = "https://api.nexblue.com/third_party/openapi"
LOGIN_URL = f"{API_BASE_URL}/account/login"
REFRESH_TOKEN_URL = f"{API_BASE_URL}/account/refresh_token"

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

        login_data = {"username": self._username, "password": self._password}

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

        refresh_data = {"refresh_token": self._refresh_token}

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

        # For now, return a simple placeholder
        # We'll expand this in the next steps
        return {"authenticated": True}

    async def api_wrapper(
        self, method: str, url: str, data: dict = None, headers: dict = None
    ) -> Optional[Dict[str, Any]]:
        """Get information from the API."""
        if data is None:
            data = {}
        if headers is None:
            headers = self._headers.copy() if self._access_token else HEADERS.copy()

        try:
            async with async_timeout.timeout(TIMEOUT):
                _LOGGER.debug(
                    "%s request to %s with data: %s", method.upper(), url, data
                )

                if method == "get":
                    response = await self._session.get(url, headers=headers)

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
