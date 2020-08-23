""" The Purple Air air_quality platform. """
import asyncio
import logging

from homeassistant.components.air_quality import AirQualityEntity
from homeassistant.config_entries import ConfigEntry
from homeassistant.core import HomeAssistant
from homeassistant.helpers.dispatcher import async_dispatcher_connect

from .const import DISPATCHER_PURPLE_AIR, DOMAIN

_LOGGER = logging.getLogger(__name__)


async def async_setup_entry(hass, config_entry, async_schedule_add_entities):
    node_id = config_entry.data["id"]
    title = config_entry.data["title"]

    async_schedule_add_entities([PurpleAirQuality(hass, node_id, title)])


class PurpleAirQuality(AirQualityEntity):
    def __init__(self, hass, node_id, title):
        self._hass = hass
        self._node_id = node_id
        self._title = title
        self._api = hass.data[DOMAIN]
        self._stop_listening = None

    @property
    def air_quality_index(self):
        return self._api.get_reading(self._node_id, 'pm2_5_atm_aqi')

    @property
    def attribution(self):
        return 'Data provided by PurpleAir'

    @property
    def available(self):
        return self._api.is_node_registered(self._node_id)

    @property
    def name(self):
        return self._title

    @property
    def particulate_matter_1_0(self):
        return self._api.get_reading(self._node_id, 'pm1_0_atm')

    @property
    def particulate_matter_2_5(self):
        return self._api.get_reading(self._node_id, 'pm2_5_atm')

    @property
    def particulate_matter_10(self):
        return self._api.get_reading(self._node_id, 'pm10_0_atm')

    @property
    def should_poll(self):
        return False

    @property
    def state_attributes(self):
        attributes = super().state_attributes
        pm1_0 = self.particulate_matter_1_0

        if pm1_0:
            attributes['particulate_matter_1_0'] = pm1_0

        return attributes

    @property
    def unique_id(self):
        return f'{self._node_id}_air_quality'

    async def async_added_to_hass(self):
        _LOGGER.debug('registering with node_id: %s', self._node_id)
        self._api.register_node(self._node_id)
        self._stop_listening = async_dispatcher_connect(
            self._hass,
            DISPATCHER_PURPLE_AIR,
            self.async_write_ha_state
        )


    async def async_will_remove_from_hass(self):
        _LOGGER.debug('unregistering node_id: %s', self._node_id)
        self._api.unregister_node(self._node_id)
        if self._stop_listening:
            self._stop_listening()
            self._stop_listening = None
