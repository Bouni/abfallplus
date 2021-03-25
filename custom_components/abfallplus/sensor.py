""" Abfallplus municipal waste sensor."""

import asyncio
import logging
import re
from datetime import date
from datetime import datetime as dt
from datetime import timedelta as td
from hashlib import md5

import pytz
import recurring_ical_events
import requests
from icalendar import Calendar, Event

import homeassistant.helpers.config_validation as cv
import voluptuous as vol
from homeassistant.components.sensor import ENTITY_ID_FORMAT, PLATFORM_SCHEMA
from homeassistant.const import CONF_NAME
from homeassistant.helpers.entity import Entity, async_generate_entity_id
from homeassistant.helpers.typing import HomeAssistantType
from homeassistant.util import Throttle

_LOGGER = logging.getLogger(__name__)

ICON = "mdi:calendar"
DOMAIN = "abfallplus"

CONF_KEY = "key"
CONF_MUNICIPALITY_ID = "municipality"
CONF_DISTRICT_ID = "district"
CONF_STREET_ID = "street"
CONF_TRASH_IDS = "trash_ids"
CONF_NAME = "name"
CONF_TIMEFORMAT = "timeformat"
CONF_LOOKAHEAD = "lookahead"
CONF_PATTERN = "pattern"

DEFAULT_NAME = "abfallplus"
DEFAULT_PATTERN = ""
DEFAULT_TIMEFORMAT = "%A, %d.%m.%Y"
DEFAULT_LOOKAHEAD = 365

MIN_TIME_BETWEEN_UPDATES = td(seconds=1800)


PLATFORM_SCHEMA = PLATFORM_SCHEMA.extend(
    {
        vol.Required(CONF_KEY): cv.string,
        vol.Required(CONF_MUNICIPALITY_ID): vol.Coerce(int),
        vol.Optional(CONF_DISTRICT_ID): cv.string,
        vol.Required(CONF_STREET_ID): vol.Coerce(int),
        vol.Required(CONF_TRASH_IDS): cv.string,
        vol.Optional(CONF_NAME, default=DEFAULT_NAME): cv.string,
        vol.Optional(CONF_TIMEFORMAT, default=DEFAULT_TIMEFORMAT): cv.string,
        vol.Optional(CONF_PATTERN, default=DEFAULT_PATTERN): cv.string,
        vol.Optional(CONF_LOOKAHEAD, default=DEFAULT_LOOKAHEAD): vol.Coerce(int),
    }
)


@asyncio.coroutine
def async_setup_platform(hass, config, async_add_devices, discovery_info=None):
    """Set up date sensor."""
    key = config.get(CONF_KEY)
    municipality = config.get(CONF_MUNICIPALITY_ID)
    district = config.get(CONF_DISTRICT_ID)
    street = config.get(CONF_STREET_ID)
    trashtypes = config.get(CONF_TRASH_IDS)
    name = config.get(CONF_NAME)
    pattern = config.get(CONF_PATTERN)
    timeformat = config.get(CONF_TIMEFORMAT)
    lookahead = config.get(CONF_LOOKAHEAD)

    devices = []
    devices.append(
        AbfallPlusSensor(
            hass,
            name,
            key,
            municipality,
            district,
            street,
            trashtypes,
            timeformat,
            lookahead,
            pattern,
        )
    )
    async_add_devices(devices)


class AbfallPlusSensor(Entity):
    """Representation of a AbfallPlus Sensor."""

    def __init__(
        self,
        hass: HomeAssistantType,
        name,
        key,
        municipality,
        district,
        street,
        trashtypes,
        timeformat,
        lookahead,
        pattern,
    ):
        """Initialize the sensor."""
        self._state_attributes = {}
        self._state = None
        self._name = name
        self._key = key
        self._modus = md5(b"scripts").hexdigest()
        self._municipality = municipality
        self._district = district
        self._street = street
        self._trashtypes = trashtypes
        self._pattern = pattern
        self._timeformat = timeformat
        self._lookahead = lookahead
        self._lastUpdate = -1

        self.entity_id = async_generate_entity_id(
            ENTITY_ID_FORMAT, self._name, hass=hass
        )

    @property
    def name(self):
        """Return the name of the sensor."""
        return self._name

    @property
    def device_state_attributes(self):
        """Return the state attributes."""
        return self._state_attributes

    @property
    def state(self):
        """Return the state of the sensor."""
        return self._state

    @property
    def icon(self):
        """Return the icon to use in the frontend."""
        return ICON

    def get_hidden(self):
        _LOGGER.debug(f"try to get hidden values using {self._key} as key")
        headers = {
            'User-Agent': 'Mozilla/5.0 (X11; Linux x86_64; rv:86.0) Gecko/20100101 Firefox/86.0'
        }
        url = f"https://api.abfallplus.de/?key={self._key}&modus={self._modus}&waction=init"
        _LOGGER.debug(f"get_hidden request URL {url}")
        try:
            r = requests.get(url, headers=headers)
        except Exception as e:
            _LOGGER.error(f"Failed to get hidden value")
            _LOGGER.error(e)
            return
        kv = re.search(r'type="hidden" name="([a-f0-9]+)" value="([a-f0-9]+)"', r.text)
        if kv:
            _LOGGER.debug(f"get_hidden was successful")
            return kv.group(1), kv.group(2)
        _LOGGER.error(f"get_hidden was not successful")
        return None, None


    def get_data(self):
        hk, hv = self.get_hidden() 
        headers = {
            'User-Agent': 'Mozilla/5.0 (X11; Linux x86_64; rv:86.0) Gecko/20100101 Firefox/86.0',
        }
        data = {
            hk: hv,
            "f_id_kommune": self._municipality,
            "f_id_strasse": self._street,
            "f_abfallarten": self._trashtypes,
            "f_zeitraum": f"{dt.now().strftime('%Y0101')}-{dt.now().strftime('%Y1231')}",
        }
        if self._district:
            data["f_id_bezirk"] = self._district
        url = f"https://api.abfallplus.de/?key={self._key}&modus={self._modus}&waction=export_ics"
        _LOGGER.debug(f"get_ical headers: {headers}")
        _LOGGER.debug(f"get_ical data: {data}")
        _LOGGER.debug(f"get_ical URL: {url}")
        try:
            r = requests.post(url, headers=headers, data=data)
        except Exception as e:
            _LOGGER.error(f"Couldn't get ical from url")
            _LOGGER.error(e)
            return

        _LOGGER.debug(f"get_ical was successful")

        try:
            cal = Calendar.from_ical(r.content)
            reoccuring_events = recurring_ical_events.of(cal).between(
                dt.now(), dt.now() + td(self._lookahead)
            )
        except Exception as e:
            _LOGGER.error(f"Couldn't parse ical file, {e}")
            return

        self._state = "unknown"

        for event in reoccuring_events:
            if event.has_key("SUMMARY"):
                if re.match(self._pattern, event.get("SUMMARY")):
                    self._state = event["DTSTART"].dt.strftime(self._timeformat)
                    self._state_attributes["remaining"] = (
                        event["DTSTART"].dt - date.today()
                    ).days
                    self._state_attributes["description"] = event.get("DESCRIPTION", "")
                    break

    @Throttle(MIN_TIME_BETWEEN_UPDATES)
    def update(self):
        """Fetch new state data for the sensor from the ics file url."""
        self.get_data()
