from __future__ import annotations
import re
from hashlib import md5
import logging
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


#  s = requests.Session()
#  s.headers.update(
#      {
#          "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64; rv:100.0) Gecko/20100101 Firefox/100.0",
#          "Accept": "text/html,application/xhtml+xml,application/xml;q=0.9,image/avif,image/webp,*/*;q=0.8",
#          "Accept-Language": "en",
#          "Accept-Encoding": "gzip, deflate, br",
#          "Connection": "keep-alive",
#          "Upgrade-Insecure-Requests": "1",
#          "Sec-Fetch-Dest": "document",
#          "Sec-Fetch-Mode": "navigate",
#          "Sec-Fetch-Site": "cross-site",
#          "Pragma": "no-cache",
#          "Cache-Control": "no-cache",
#      }
#  )
#  class AbfallPlusOptions:
#      def __init__(self, url: str):
#          self.url = url
#          self.api_key = None
#          self.modus = {
#              "scripts": "d6c5855a62cf32a4dadbc2831f0f295f",
#              "javascript": "de9b9ed78d7e2e1dceeffee780e2f919",
#              "css": "c7a628cba22e28eb17b5f5c6ae2a266a",
#          }
#          self.cities = None
#          self.get_data()
#
#      def get_data(self):
#          self.api_key = self.get_api_key()
#          self.get_cities()
#
#      def get_api_key(self) -> str:
#          r = s.get(self.url)
#          match = re.search(r"https://api.abfall.io/\?key=([a-f0-9]{32})", r.text)
#          if match:
#              return match.group(1)
#
#      def get_cities(self) -> list:
#          r = s.get(
#              f"https://api.abfall.io/?key={self.api_key}&modus={self.modus.get('scripts')}&waction=init"
#          )
#          cities = [
#              m.groupdict()
#              for m in re.finditer(
#                  r"<option value=\"(?P<id>\d+)\">(?P<city>[^<]*)</option>", r.text
#              )
#          ]
#          if cities:
#              self.cities = cities
#
#  if __name__ == "__main__":
#      APO = AbfallPlusOptions("https://www.abfall-landkreis-waldshut.de/de/termine/")
