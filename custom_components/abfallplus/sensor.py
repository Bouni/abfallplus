""" Abfallplus municipal waste sensor."""

import asyncio
import logging
import re
from datetime import date
from datetime import datetime as dt
from datetime import timedelta as td
from hashlib import md5

import recurring_ical_events
from icalendar import Calendar
import aiohttp
import homeassistant.helpers.config_validation as cv
import voluptuous as vol
from homeassistant.components.sensor import ENTITY_ID_FORMAT, PLATFORM_SCHEMA
from homeassistant.const import CONF_NAME
from homeassistant.helpers.entity import Entity, async_generate_entity_id
from homeassistant.helpers.typing import HomeAssistantType
from homeassistant.util import Throttle
from .const import (
    CONF_KEY,
    CONF_MUNICIPALITY_ID,
    CONF_DISTRICT_ID,
    CONF_STREET_ID,
    CONF_TRASH_IDS,
    CONF_NAME,
    CONF_PATTERN,
    CONF_TIMEFORMAT,
    CONF_LOOKAHEAD,
    ICON,
    DEFAULT_NAME,
    DEFAULT_PATTERN,
    DEFAULT_LOOKAHEAD,
    DEFAULT_TIMEFORMAT,
    DOMAIN,
)

_LOGGER = logging.getLogger(__name__)

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
    def extra_state_attributes(self):
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

    def parse_ics_data(self, ics):
        """Parse the AbfallPlus ICS data"""
        try:
            cal = Calendar.from_ical(ics)
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

    async def get_data(self):
        """Fetch ICS data from AbfallPlus"""
        headers = {
            "User-Agent": "Mozilla/5.0 (X11; Linux x86_64; rv:86.0) Gecko/20100101 Firefox/86.0",
        }
        base_url = f"https://api.abfallplus.de/?key={self._key}&modus={self._modus}"
        async with aiohttp.ClientSession(headers=headers) as session:
            url = f"{base_url}&waction=init"
            try:
                async with session.get(url) as r:
                    data = await r.text()
                    res = re.search(
                        r'type="hidden" name="([a-f0-9]+)" value="([a-f0-9]+)"', data
                    )
                    if not res:
                        _LOGGER.error(f"Failed to get hidden key value pair")
                        return
            except Exception as e:
                _LOGGER.error(f"Failed to fetch hidden key value resource")
                return
            data = {
                res.group(1): res.group(2),
                "f_id_kommune": self._municipality,
                "f_id_strasse": self._street,
                "f_abfallarten": self._trashtypes,
                "f_zeitraum": f"{dt.now().strftime('%Y0101')}-{dt.now().strftime('%Y1231')}",
            }
            url = f"{base_url}&waction=export_ics"
            try:
                async with session.post(url, data=data) as r:
                    self.parse_ics_data(await r.text())
            except Exception as e:
                _LOGGER.error(f"Failed to fetch ICS resource")
                return

    @Throttle(MIN_TIME_BETWEEN_UPDATES)
    async def async_update(self):
        """Fetch new state data for the sensor from the ics file url."""
        await self.get_data()
