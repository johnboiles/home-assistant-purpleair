"""Config flow for Purple Air integration."""
import logging
import voluptuous as vol

from homeassistant import config_entries, core, exceptions
from homeassistant.const import CONF_URL
from homeassistant.helpers.aiohttp_client import async_get_clientsession

from .const import DOMAIN

_LOGGER = logging.getLogger(__name__)


async def validate_input(hass: core.HomeAssistant, data):
    """Validate the user input allows us to connect.

    Data has the keys from DATA_SCHEMA with values provided by the user.
    """

    json = {}
    client = async_get_clientsession(hass)
    url = data['url']
    _LOGGER.debug('using url: %s', url)
    async with client.get(url) as resp:
        if not resp.status == 200:
            raise InvalidResponse(resp)

        json = await resp.json()

    node = json['results'][0]
    node_id = str(node['ID'])
    if ('ParentID' in node):
        node_id = str(node['ParentID'])

    config = {
        'title': node['Label'],
        'id': node_id,
    }

    _LOGGER.debug('generated config data: %s', config)

    return config


class ConfigFlow(config_entries.ConfigFlow, domain=DOMAIN):
    """Handle a config flow for PurpleAir."""

    VERSION = 1
    CONNECTION_CLASS = config_entries.CONN_CLASS_CLOUD_POLL

    async def async_step_user(self, user_input=None):
        errors = {}
        if user_input is not None:
            try:
                info = await validate_input(self.hass, user_input)

                await self.async_set_unique_id(info['id'])
                self._abort_if_unique_id_configured()

                return self.async_create_entry(title=info["title"], data=info)
            except CannotConnect:
                errors["base"] = "cannot_connect"
            except InvalidAuth:
                errors["base"] = "invalid_auth"
            except Exception:  # pylint: disable=broad-except
                _LOGGER.exception("Unexpected exception")
                errors["base"] = "unknown"

        data_schema = vol.Schema(
            {
                vol.Required(CONF_URL): str,
            }
        )

        return self.async_show_form(
            step_id="user", data_schema=data_schema, errors=errors
        )


class CannotConnect(exceptions.HomeAssistantError):
    """Error to indicate we cannot connect."""


class InvalidAuth(exceptions.HomeAssistantError):
    """Error to indicate there is invalid auth."""


class InvalidResponse(exceptions.HomeAssistantError):
    """Error to indicate a bad HTTP response."""

    def __init__(self, response):
        self.response = response
