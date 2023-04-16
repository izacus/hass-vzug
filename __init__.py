"""The V-Zug integration."""
from __future__ import annotations

import logging

from datetime import timedelta
from random import randrange

from homeassistant.config_entries import ConfigEntry
from homeassistant.const import Platform
from homeassistant.core import HomeAssistant
from homeassistant.helpers.update_coordinator import DataUpdateCoordinator, UpdateFailed

from .const import DOMAIN, CONF_DEVICE_IP
from .vzug import get_device_status

_LOGGER = logging.getLogger(__name__)

PLATFORMS: list[Platform] = [Platform.SENSOR, Platform.BINARY_SENSOR]

async def async_setup_entry(hass: HomeAssistant, entry: ConfigEntry) -> bool:
    """Set up V-Zug from a config entry."""

    _LOGGER.debug("Setting up async entry...")
    coordinator = VZugDataCoordinator(hass, entry)
    await coordinator.async_config_entry_first_refresh()

    hass.data.setdefault(DOMAIN, {})
    hass.data[DOMAIN][entry.entry_id] = coordinator
    await hass.config_entries.async_forward_entry_setups(entry, PLATFORMS)
    return True


async def async_unload_entry(hass: HomeAssistant, entry: ConfigEntry) -> bool:
    """Unload a config entry."""

    _LOGGER.debug("Unloading entries...")

    if unload_ok := await hass.config_entries.async_unload_platforms(entry, PLATFORMS):
        hass.data[DOMAIN].pop(entry.entry_id)

    return unload_ok


class VZugDataCoordinator(DataUpdateCoordinator["VZugDataCoordinator"]):
    """ Data Update Coordinator """

    def __init__(self, hass: HomeAssistant, config_entry: ConfigEntry) -> None:
        self._ip = config_entry.data[CONF_DEVICE_IP]
        update_interval = timedelta(minutes=randrange(4, 6))
        super().__init__(hass, _LOGGER, name=DOMAIN, update_interval=update_interval)

    async def _async_update_data(self):
        _LOGGER.info(f"Updating V-Zug device data on {self._ip}")
        try:
            current_state = await get_device_status(self.hass, self._ip)
            _LOGGER.debug(f"Current state: {current_state}")
        except Exception as e:
            _LOGGER.exception(e, exc_info=True)
            current_state = None
        return current_state