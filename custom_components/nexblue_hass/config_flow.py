"""Adds config flow for NexBlue."""
import logging

import aiohttp
import voluptuous as vol
from homeassistant import config_entries
from homeassistant.core import callback
from homeassistant.helpers.aiohttp_client import async_create_clientsession

from .api import NexBlueApiClient
from .const import CONF_PASSWORD
from .const import CONF_USERNAME
from .const import DOMAIN
from .const import PLATFORMS

_LOGGER = logging.getLogger(__package__)


class NexBlueFlowHandler(config_entries.ConfigFlow, domain=DOMAIN):
    """Config flow for nexblue_hass."""

    VERSION = 1
    CONNECTION_CLASS = config_entries.CONN_CLASS_CLOUD_POLL

    def __init__(self):
        """Initialize."""
        self._errors = {}

    async def async_step_user(self, user_input=None):
        """Handle a flow initialized by the user."""
        self._errors = {}

        # Uncomment the next 2 lines if only a single instance of the integration is allowed:
        # if self._async_current_entries():
        #     return self.async_abort(reason="single_instance_allowed")

        if user_input is not None:
            valid = await self._test_credentials(
                user_input[CONF_USERNAME], user_input[CONF_PASSWORD]
            )
            if valid:
                return self.async_create_entry(
                    title=f"NexBlue ({user_input[CONF_USERNAME]})", data=user_input
                )

            # If we have specific errors from _test_credentials, they're already set
            # Otherwise, default to auth error
            if not self._errors:
                self._errors["base"] = "auth"

            return await self._show_config_form(user_input)

        return await self._show_config_form(user_input)

    @staticmethod
    @callback
    def async_get_options_flow(config_entry):
        return NexBlueOptionsFlowHandler(config_entry)

    async def _show_config_form(self, user_input):  # pylint: disable=unused-argument
        """Show the configuration form to edit location data."""
        return self.async_show_form(
            step_id="user",
            data_schema=vol.Schema(
                {vol.Required(CONF_USERNAME): str, vol.Required(CONF_PASSWORD): str}
            ),
            errors=self._errors,
        )

    async def _test_credentials(self, username, password):
        """Return true if credentials is valid."""
        try:
            session = async_create_clientsession(self.hass)
            client = NexBlueApiClient(username, password, session)
            # Directly test login instead of using async_get_data
            login_successful = await client.async_login()
            if not login_successful:
                _LOGGER.error("Failed to authenticate with NexBlue API")
                return False
            return True
        except aiohttp.ClientError:
            _LOGGER.error("Cannot connect to NexBlue API")
            self._errors["base"] = "cannot_connect"
            return False
        except Exception as exception:  # pylint: disable=broad-except
            _LOGGER.exception("Unexpected exception: %s", exception)
            self._errors["base"] = "unknown"
            return False


class NexBlueOptionsFlowHandler(config_entries.OptionsFlow):
    """Config flow options handler for nexblue_hass."""

    def __init__(self, config_entry):
        """Initialize HACS options flow."""
        self.config_entry = config_entry
        self.options = dict(config_entry.options)

    async def async_step_init(self, user_input=None):  # pylint: disable=unused-argument
        """Manage the options."""
        return await self.async_step_user()

    async def async_step_user(self, user_input=None):
        """Handle a flow initialized by the user."""
        if user_input is not None:
            self.options.update(user_input)
            return await self._update_options()

        return self.async_show_form(
            step_id="user",
            data_schema=vol.Schema(
                {
                    vol.Required(x, default=self.options.get(x, True)): bool
                    for x in sorted(PLATFORMS)
                }
            ),
        )

    async def _update_options(self):
        """Update config entry options."""
        return self.async_create_entry(
            title=self.config_entry.data.get(CONF_USERNAME), data=self.options
        )
