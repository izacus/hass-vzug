import logging
import asyncio

from homeassistant.helpers.aiohttp_client import async_get_clientsession
from homeassistant.helpers.entity import DeviceInfo

from .const import DOMAIN, STATUS_URL, CONF_DEVICE_UUID, CONF_DEVICE_MODEL, CONF_DEVICE_NAME, CONF_DEVICE_SERIAL

_LOGGER = logging.getLogger(__name__)

async def get_device_status(hass, ip):
    session = async_get_clientsession(hass)
    url = STATUS_URL % (ip, )
    _LOGGER.debug(f"Retrieving status from {url}")

    headers = {
        "Accept": "text/html,application/xhtml+xml,application/xml,text/plain",
        "Accept-Encoding": "gzip, deflate",
        "Accept-Language": "en-GB,en",
        "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/112.0.0.0 Safari/537.36 Edg/112.0.1722.46"
    }

    retry_count = 12    
    success = False
    while not success:
        async with session.get(f"http://{ip}/hh?command=getZHMode") as response:
            _LOGGER.debug(await response.text())
        await asyncio.sleep(1)    

        async with session.get(url, headers=headers) as response:
            r = await response.json(content_type="text/plain")
            _LOGGER.debug(f"Response {r}")
            if "error" in r:
                _LOGGER.debug(f"Received error, retry {retry_count}...")
                retry_count = retry_count - 1
                if retry_count == 0:
                    return None
                else: 
                    await asyncio.sleep(5)
                    continue
            return r

def get_device_info(config_entry):
    uuid = config_entry.data[CONF_DEVICE_UUID]
    model = config_entry.data[CONF_DEVICE_MODEL]
    name = config_entry.data[CONF_DEVICE_NAME]
    return DeviceInfo(manufacturer="V-Zug", model=model, name=name, identifiers={(DOMAIN, uuid)})