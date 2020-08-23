from datetime import timedelta
import logging

from homeassistant.helpers.dispatcher import async_dispatcher_send
from homeassistant.helpers.event import async_track_time_interval, async_track_point_in_utc_time
from homeassistant.util import dt

from .const import AQI_BREAKPOINTS, DISPATCHER_PURPLE_AIR, JSON_PROPERTIES, SCAN_INTERVAL, URL

_LOGGER = logging.getLogger(__name__)


def calc_aqi(value, index):
    if index not in AQI_BREAKPOINTS:
        _LOGGER.debug('calc_aqi requested for unknown type: %s', index)
        return None

    bp = next((bp for bp in AQI_BREAKPOINTS[index] if value >= bp['pm_low'] and value <=
              bp['pm_high']), None)
    if not bp:
        _LOGGER.debug('value %s did not fall in valid range for type %s', value, index)
        return None

    aqi_range = bp['aqi_high'] - bp['aqi_low']
    pm_range = bp['pm_high'] - bp['pm_low']
    c = value - bp['pm_low']
    return round((aqi_range/pm_range) * c + bp['aqi_low'])


class PurpleAirApi:
    def __init__(self, hass, session):
        self._hass = hass
        self._session = session
        self._nodes = []
        self._data = {}
        self._scan_interval = timedelta(seconds=SCAN_INTERVAL)
        self._shutdown_interval = None

    def is_node_registered(self, node_id):
        return node_id in self._data

    def get_property(self, node_id, prop):
        if node_id not in self._data:
            return None

        node = self._data[node_id]
        return node[prop]

    def get_reading(self, node_id, prop):
        readings = self.get_property(node_id, 'readings')
        return readings[prop] if prop in readings else None

    def register_node(self, node_id):
        if node_id in self._nodes:
            _LOGGER.debug('detected duplicate registration: %s', node_id)
            return

        self._nodes.append(node_id)
        _LOGGER.debug('registered new node: %s', node_id)

        if not self._shutdown_interval:
            _LOGGER.debug('starting background poll: %s', self._scan_interval)
            self._shutdown_interval = async_track_time_interval(
                self._hass,
                self._update,
                self._scan_interval
            )

            async_track_point_in_utc_time(
                self._hass,
                self._update,
                dt.utcnow() + timedelta(seconds=5)
            )

    def unregister_node(self, node_id):
        if node_id not in self._nodes:
            _LOGGER.debug('detected non-existent unregistration: %s', node_id)
            return

        self._nodes.remove(node_id)
        _LOGGER.debug('unregistered node: %s', node_id)

        if not self._nodes and self._shutdown_interval:
            _LOGGER.debug('no more nodes, shutting down interval')
            self._shutdown_interval()
            self._shutdown_interval = None

    async def _update(self, now=None):
        url = URL.format(node_list='|'.join(self._nodes))
        _LOGGER.debug('calling update url: %s', url)

        results = {}
        async with self._session.get(url) as resp:
            if resp.status != 200:
                _LOGGER.warning('bad API response for %s: %s', url, resp.status)
                return

            json = await resp.json()
            results = json['results']

        nodes = {}
        for result in results:
            node_id = str(result['ID'] if 'ParentID' not in result else result['ParentID'])
            if 'ParentID' not in result:
                nodes[node_id] = {
                    'last_seen': result['LastSeen'],
                    'last_update': result['LastUpdateCheck'],
                    'readings': {},
                }

            sensor = 'A' if 'ParentID' not in result else 'B'
            readings = nodes[node_id]['readings']

            if sensor not in readings:
                readings[sensor] = {}

            for prop in JSON_PROPERTIES:
                readings[sensor][prop] = result[prop] if prop in result else None

        for node in nodes:
            readings = nodes[node]['readings']
            if 'A' in readings and 'B' in readings:
                for prop in JSON_PROPERTIES:
                    if prop in readings['A'] and prop in readings['B']:
                        a = float(readings['A'][prop])
                        b = float(readings['B'][prop])
                        readings[prop] = round((a + b) / 2, 1)
                        readings[f'{prop}_confidence'] = 'Good' if abs(a - b) < 45 else 'Questionable'
                    else:
                        readings[prop] = None
            else:
                for prop in JSON_PROPERTIES:
                    if prop in readings['A']:
                        readings[prop] = readings['A'][prop]
                        readings[f'{prop}_confidence'] = 'Good'
                    else:
                        readings[prop] = None

            if 'pm2_5_atm' in readings:
                readings['pm2_5_atm_aqi'] = calc_aqi(readings['pm2_5_atm'], 'pm2_5')

        self._data = nodes
        async_dispatcher_send(self._hass, DISPATCHER_PURPLE_AIR)
