"""Config flow for V-Zug."""

import logging

from typing import Any
from aiohttp import ClientConnectorError

import asyncio
import voluptuous as vol

from homeassistant import config_entries
from homeassistant.core import HomeAssistant
from homeassistant.data_entry_flow import FlowResult
from homeassistant.exceptions import HomeAssistantError
from homeassistant.helpers.aiohttp_client import async_get_clientsession

from .const import DOMAIN, CONF_DEVICE_IP, CONF_DEVICE_NAME, CONF_DEVICE_SERIAL, CONF_DEVICE_UUID, CONF_DEVICE_MODEL
from .vzug import get_device_status

_LOGGER = logging.getLogger(__name__)

MODEL_DESCRIPTION_URL = "http://%s/ai?command=getModelDescription"

STEP_USER_DATA_SCHEMA = vol.Schema(
    {
        vol.Required(CONF_DEVICE_IP): str
    }
)

async def validate_input(hass: HomeAssistant, data: dict[str, Any]) -> dict[str, Any]:
    """Validate the user input allows us to connect.
    Data has the keys from STEP_USER_DATA_SCHEMA with values provided by the user.
    """
    
    _LOGGER.debug(f"Validating {data}")

    result = {}        
    session = async_get_clientsession(hass)
    try:
        url = MODEL_DESCRIPTION_URL % (data["device_ip"])
        _LOGGER.debug(f"Retrieving model descrption from {url}")

        modelName = None
        async with session.get(url) as response:
            modelName = await response.text()
            result["title"] = "V-Zug %s" % (modelName, )
        await asyncio.sleep(3)

        r = await get_device_status(hass, data["device_ip"])
        if r is None:
            raise CannotConnect()       

        name = r["DeviceName"]
        if name is None or len(name) == 0:
            name = modelName

        result[CONF_DEVICE_NAME] = name        
        result[CONF_DEVICE_SERIAL] = r["Serial"]
        result[CONF_DEVICE_UUID] = r["deviceUuid"]
        result[CONF_DEVICE_IP] = data["device_ip"]
        result[CONF_DEVICE_MODEL] = modelName
    except ClientConnectorError as e:
        raise CannotConnect(e)

    # Return info that you want to store in the config entry.
    return result

class ConfigFlow(config_entries.ConfigFlow, domain=DOMAIN):
    VERSION = 1

    async def async_step_user(self, user_input: dict[str, Any] | None = None) -> FlowResult:
        if user_input is None:
            return self.async_show_form(step_id="user", data_schema=STEP_USER_DATA_SCHEMA)
        
        errors = {}
        try:
            info = await validate_input(self.hass, user_input)
        except CannotConnect:
            errors["base"] = "cannot_connect"
        except InvalidAuth:
            errors["base"] = "invalid_auth"
        except Exception:
            _LOGGER.error("Failed to retrieve data.", exc_info=True)
            errors["base"] = "unknown"
        else:
            _LOGGER.info(f"Configuring V-Zug with {info}")
            return self.async_create_entry(title=info["title"], data=info, description=f'{info["title"]} / {user_input[CONF_DEVICE_IP]}')

        return self.async_show_form(step_id="user", data_schema=STEP_USER_DATA_SCHEMA, errors=errors)

class CannotConnect(HomeAssistantError):
    """Error to indicate we cannot connect."""

class InvalidAuth(HomeAssistantError):
    """Error to indicate there is invalid auth."""