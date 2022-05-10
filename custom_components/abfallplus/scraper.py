from __future__ import annotations

import logging
import re
from hashlib import md5

import aiohttp

_LOGGER = logging.getLogger(__name__)


async def get_api_key(url: str) -> str:
    """Scrape the API key from the supplied URL"""
    async with aiohttp.ClientSession() as session:
        async with session.get(url) as r:
            page = await r.text()
            api_key = re.search(r"https://api.abfall.io/\?key=([a-f0-9]{32})", page)
            if api_key:
                return api_key.group(1)
            return ""


async def get_cities(api_key: str) -> dict:
    """Get the list of cities from the API (which is not a real API  but a HTML widget)"""
    async with aiohttp.ClientSession() as session:
        # modus = md5 hash of "scripts"
        url = f"https://api.abfall.io/?key={api_key}&modus=d6c5855a62cf32a4dadbc2831f0f295f&waction=init"
        async with session.get(url) as r:
            page = await r.text()
            hidden = re.search(
                r"name=\"([a-f0-9]{32})\" value=\"([a-f0-9]{32})\"", page
            )
            data = {
                "cities": {},
                "hidden_name": hidden.group(1),
                "hidden_value": hidden.group(2),
            }
            for match in re.findall(
                r"<option value=\"([\d,]+)\">([^<]*)</option>", page
            ):
                if match[0] != "0":
                    data["cities"][match[0]] = match[1]
            return data


async def get_districts(
    api_key: str, city_id: str, hidden_name: str, hidden_value: str
) -> dict:
    """Get districts for a certain city_id"""
    async with aiohttp.ClientSession() as session:
        payload = {"f_id_kommune": city_id, hidden_name: hidden_value}
        url = f"https://api.abfall.io/?key={api_key}&modus=d6c5855a62cf32a4dadbc2831f0f295f&waction=auswahl_kommune_set"
        async with session.post(url, data=payload) as r:
            page = await r.text()
            districts = {}
            for match in re.findall(
                r"<option value=\"([\d,]+)\">([^<]*)</option>", page
            ):
                if match[0] != "0":
                    districts[match[0]] = match[1]
            return districts


async def get_streets(
    api_key: str, city_id: str, district_id: str, hidden_name: str, hidden_value: str
) -> dict:
    """Get streets for a certain city_id and district_id"""
    async with aiohttp.ClientSession() as session:
        data = {
            "f_id_kommune": city_id,
            "f_id_bezirk": district_id,
            hidden_name: hidden_value,
        }
        url = f"https://api.abfall.io/?key={api_key}&modus=d6c5855a62cf32a4dadbc2831f0f295f&waction=auswahl_bezirk_set"
        async with session.post(url, data=data) as r:
            page = await r.text()
            streets = {}
            for match in re.findall(
                r"<option value=\"([\d,]+)\">([^<]*)</option>", page
            ):
                if match[0] != "0":
                    streets[match[0]] = match[1]
            return streets


async def get_trash_types(
    api_key: str,
    city_id: str,
    district_id: str,
    street_id: str,
    hidden_name: str,
    hidden_value: str,
) -> dict:
    """Get trash types for a certain city_id, district_id, and street_id"""
    async with aiohttp.ClientSession() as session:
        data = {
            "f_id_kommune": city_id,
            "f_id_bezirk": district_id,
            "f_id_strasse": street_id,
            hidden_name: hidden_value,
        }
        url = f"https://api.abfall.io/?key={api_key}&modus=d6c5855a62cf32a4dadbc2831f0f295f&waction=auswahl_strasse_set"
        async with session.post(url, data=data) as r:
            page = await r.text()
            trash_types = {}
            trash_names = re.findall(r"Abfallart <\/span>([^<]+)*", page)
            trash_ids = re.findall(r"name=\"f_id_abfalltyp_\d+\" value=\"(\d+)\"", page)
            trash_types = dict(zip(trash_ids, trash_names))
            return trash_types


