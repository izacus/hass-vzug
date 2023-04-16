import json
import logging

from homeassistant.components.sensor import SensorEntity, SensorEntityDescription

from .const import DOMAIN, CONF_DEVICE_UUID
from .vzug import get_device_info

from homeassistant.config_entries import ConfigEntry
from homeassistant.core import HomeAssistant
from homeassistant.helpers.entity import DeviceInfo
from homeassistant.helpers.entity_platform import AddEntitiesCallback
from homeassistant.helpers.typing import StateType
from homeassistant.const import UnitOfTime

_LOGGER = logging.getLogger(__name__)

async def async_setup_entry(
    hass: HomeAssistant,
    config_entry: ConfigEntry,
    async_add_entities: AddEntitiesCallback,
) -> None:
    coordinator = hass.data[DOMAIN][config_entry.entry_id]    
    uuid = config_entry.data[CONF_DEVICE_UUID]
    entities: list = [VZugProgramSensor(uuid, coordinator, get_device_info(config_entry)), VZugProgramEndSensor(uuid, coordinator, get_device_info(config_entry))]
    async_add_entities(entities)

class VZugProgramSensor(SensorEntity):

    def __init__(self, uuid: str, coordinator,  device_info: DeviceInfo) -> None:
        self.entity_description = SensorEntityDescription(key="program", 
            name = "Program")
        self._coordinator = coordinator
        self._attr_name = f"V-Zug {device_info['model']} {uuid} Program"
        self._attr_unique_id = f"vzug_{device_info['model']}_{uuid}_program"
        self._attr_device_info = device_info

    @property
    def available(self) -> bool:
        return self._coordinator.last_update_success and "Program" in self._coordinator.data

    async def async_added_to_hass(self) -> None:
        """Connect to dispatcher listening for entity data notifications."""
        self.async_on_remove(
            self._coordinator.async_add_listener(self.async_write_ha_state)
        )

    @property
    def native_value(self) -> str | None:
        if self._coordinator.data is None or "Program" not in self._coordinator.data:
            return None
        
        value = str(self._coordinator.data["Program"])
        if len(value) == 0:
            return "None"
        return value

class VZugProgramEndSensor(SensorEntity):

    def __init__(self, uuid: str, coordinator,  device_info: DeviceInfo) -> None:
        self.entity_description = SensorEntityDescription(key="program_End", 
            name = "Program End", native_unit_of_measurement=UnitOfTime.MINUTES)
        self._coordinator = coordinator
        self._attr_name = f"V-Zug {device_info['model']} {uuid} Program End"
        self._attr_unique_id = f"vzug_{device_info['model']}_{uuid}_program_end"
        self._attr_device_info = device_info

    @property
    def available(self) -> bool:
        return self._coordinator.last_update_success and "ProgramEnd" in self._coordinator.data

    async def async_added_to_hass(self) -> None:
        """Connect to dispatcher listening for entity data notifications."""
        self.async_on_remove(
            self._coordinator.async_add_listener(self.async_write_ha_state)
        )

    def native_unit_of_measurement(self) -> str | None:
        return UnitOfTime.MINUTES

    @property
    def native_value(self) -> str | None:
        end_minutes = self.get_end_minutes()
        if end_minutes is None:
            return 0
        return end_minutes

    def get_end_minutes(self):        
        if self._coordinator.data is None:
            return None
        
        if "ProgramEnd" not in self._coordinator.data:
            return None

        try:            
            program_end_data = str(self._coordinator.data["ProgramEnd"])
            program_end_data = program_end_data.replace("\'", "\"")
            _LOGGER.debug(f"Program end data {program_end_data}")
            program_end_json = json.loads(program_end_data)
            
            if not "End" in program_end_json:
                return None 
            end_string = program_end_json["End"]
            _LOGGER.debug(f"Program end value {end_string}")
            if len(end_string) == 0:
                return None
            split_end = end_string.split('h')
            if len(split_end) < 2:
                return None
            hours = int(split_end[0])
            minutes = int(split_end[1])
            return hours * 60 + minutes
        except json.JSONDecodeError:
            _LOGGER.error("Failed to decode JSON", exc_info=True)
            return None

        