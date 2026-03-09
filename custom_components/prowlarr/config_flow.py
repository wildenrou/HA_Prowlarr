from __future__ import annotations

import voluptuous as vol

from homeassistant import config_entries
from homeassistant.const import CONF_HOST, CONF_PORT
from homeassistant.helpers.aiohttp_client import async_get_clientsession

from .api import (
    ProwlarrApiClient,
    ProwlarrAuthenticationError,
    ProwlarrConnectionError,
)
from .const import CONF_API_KEY, CONF_SSL, DEFAULT_PORT, DOMAIN


class ProwlarrConfigFlow(config_entries.ConfigFlow, domain=DOMAIN):
    """Handle a config flow for Prowlarr."""

    VERSION = 1

    async def async_step_user(self, user_input=None):
        errors = {}

        if user_input is not None:
            session = async_get_clientsession(self.hass)
            client = ProwlarrApiClient(
                session=session,
                host=user_input[CONF_HOST],
                port=user_input[CONF_PORT],
                api_key=user_input[CONF_API_KEY],
                use_ssl=user_input[CONF_SSL],
            )

            try:
                system = await client.async_validate()
                unique_id = (
                    system.get("instanceName")
                    or f"{user_input[CONF_HOST]}:{user_input[CONF_PORT]}"
                )
                await self.async_set_unique_id(unique_id)
                self._abort_if_unique_id_configured()
                return self.async_create_entry(title="Prowlarr", data=user_input)
            except ProwlarrAuthenticationError:
                errors["base"] = "invalid_auth"
            except ProwlarrConnectionError:
                errors["base"] = "cannot_connect"
            except Exception:
                errors["base"] = "unknown"

        data_schema = vol.Schema(
            {
                vol.Required(CONF_HOST): str,
                vol.Required(CONF_PORT, default=DEFAULT_PORT): int,
                vol.Required(CONF_API_KEY): str,
                vol.Required(CONF_SSL, default=False): bool,
            }
        )

        return self.async_show_form(
            step_id="user",
            data_schema=data_schema,
            errors=errors,
        )