from __future__ import annotations
import re
from hashlib import md5
import logging
import aiohttp

_LOGGER = logging.getLogger(__name__)


async def get_api_key(url: str) -> str | None:
    """Scrape the API key from the supplied URL"""
    async with aiohttp.ClientSession() as session:
        _LOGGER.error(url)
        async with session.get(url) as r:
            page = await r.text()
            match = re.search(r"https://api.abfall.io/\?key=([a-f0-9]{32})", page)
            if match:
                return match.group(1)


async def get_cities(api_key: str) -> dict | None:
    """Get the list of cities from the API (which is not a real API  but a HTML widget) """
    async with aiohttp.ClientSession() as session:
        # modus = md5 hash of "scripts"
        url = f"https://api.abfall.io/?key={api_key}&modus=d6c5855a62cf32a4dadbc2831f0f295f&waction=init"
        _LOGGER.error(url)
        async with session.get(url) as r:
            page = await r.text()
            cities = {}
            for match in re.findall(
                r"<option value=\"(\d+)\">([^<]*)</option>", page
            ):
                if match[0] != '0':
                 cities[match[0]] = match[1]
            return cities


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
