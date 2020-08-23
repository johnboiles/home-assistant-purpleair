""" The Purple Air air_quality platform. """
import asyncio

from homeassistant.config_entries import ConfigEntry
from homeassistant.core import HomeAssistant
from homeassistant.helpers.dispatcher import async_dispatcher_connect
from homeassistant.helpers.entity import Entity

from .const import DISPATCHER_PURPLE_AIR, DOMAIN


async def async_setup_entry(hass, config_entry, async_schedule_add_entities):
    node_id = config_entry.data["id"]
    title = config_entry.data["title"]

    async_schedule_add_entities([PurpleAirQualityIndex(hass, node_id, title)])


class PurpleAirQualityIndex(Entity):
    def __init__(self, hass, node_id, title):
        self._hass = hass
        self._node_id = node_id
        self._title = title
        self._api = hass.data[DOMAIN]
        self._stop_listening = None

    @property
    def attribution(self):
        return 'Data provided by PurpleAir'

    @property
    def available(self):
        return self._api.is_node_registered(self._node_id)

    @property
    def icon(self):
        return 'mdi:weather-hazy'

    @property
    def name(self):
        return f'{self._title} Air Quality Index'

    @property
    def should_poll(self):
        return False

    @property
    def state(self):
        return self._api.get_reading(self._node_id, 'pm2_5_atm_aqi')

    @property
    def unique_id(self):
        return f'{self._node_id}_air_quality_index'

    @property
    def unit_of_measurement(self):
        return 'AQI'

    async def async_added_to_hass(self):
        self._stop_listening = async_dispatcher_connect(
            self._hass,
            DISPATCHER_PURPLE_AIR,
            self.async_write_ha_state
        )

    async def async_will_remove_from_hass(self):
        if self._stop_listening:
            self._stop_listening()
            self._stop_listening = None
