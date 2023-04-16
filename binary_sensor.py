
from homeassistant.components.binary_sensor import BinarySensorEntity, BinarySensorEntityDescription, BinarySensorDeviceClass

from .const import DOMAIN, CONF_DEVICE_UUID
from .vzug import get_device_info

from homeassistant.config_entries import ConfigEntry
from homeassistant.core import HomeAssistant
from homeassistant.helpers.device_registry import DeviceEntryType
from homeassistant.helpers.entity import DeviceInfo
from homeassistant.helpers.entity_platform import AddEntitiesCallback
from homeassistant.helpers.typing import StateType

async def async_setup_entry(
    hass: HomeAssistant,
    config_entry: ConfigEntry,
    async_add_entities: AddEntitiesCallback,
) -> None:
    coordinator = hass.data[DOMAIN][config_entry.entry_id]    
    uuid = config_entry.data[CONF_DEVICE_UUID]
    entities: list[VZugActiveSensor] = [VZugActiveSensor(uuid, coordinator, get_device_info(config_entry))]
    async_add_entities(entities)

class VZugActiveSensor(BinarySensorEntity):

    def __init__(self, uuid: str, coordinator,  device_info: DeviceInfo) -> None:
        self.entity_description = BinarySensorEntityDescription(key="active", 
            device_class=BinarySensorDeviceClass.RUNNING,
            name = "Running")
        self._coordinator = coordinator
        self._attr_name = f"V-Zug {device_info['model']} {uuid} Active"
        self._attr_unique_id = f"vzug_{device_info['model']}_{uuid}_active"
        self._attr_device_info = device_info

    @property
    def available(self) -> bool:
        return self._coordinator.last_update_success

    async def async_added_to_hass(self) -> None:
        """Connect to dispatcher listening for entity data notifications."""
        self.async_on_remove(
            self._coordinator.async_add_listener(self.async_write_ha_state)
        )

    @property
    def is_on(self) -> bool | None:
        """Return true if the binary sensor is on."""
        if self._coordinator.data is None or "Inactive" not in self._coordinator.data:
            return None
        return not bool(self._coordinator.data["Inactive"])