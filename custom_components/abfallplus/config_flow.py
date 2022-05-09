from homeassistant import config_entries
from homeassistant.helpers.selector import selector
import logging
import homeassistant.helpers.config_validation as cv
import voluptuous as vol
from .const import DOMAIN
from .helpers import get_api_key, get_cities

_LOGGER = logging.getLogger(__name__)

# https://github.com/home-assistant/example-custom-config/tree/master/custom_components/detailed_hello_world_push
# https://github.com/boralyl/github-custom-component-tutorial/blob/master/custom_components/github_custom/config_flow.py
# https://github.com/BenPru/luxtronik/blob/main/custom_components/luxtronik/config_flow.py


class AbfallPlusConfigFlow(config_entries.ConfigFlow, domain=DOMAIN):
    """AbfallPlus config flow."""

    async def async_step_user(self, user_input):
        """ get the municipality waste managemnet website URL from the user"""
        if user_input is not None:
            # If the user has entered the URL, scrape the API key from the website and continue
            try:
                self.api_key = await get_api_key(user_input["URL"])
            except Exception as e:
                _LOGGER.error(e)
            return await self.async_step_city()
        return self.async_show_form(step_id="user", data_schema=vol.Schema({vol.Required("URL"): str}))


    async def async_step_city(self, user_input=None):
        if user_input is not None:
            # if the user has selected a city and pressed confirm, go ahead to the next step
            self.city = user_input["CITY"]
            return await self.async_step_road()
        else:
            # if we just got to this step, fetch a list of citys with the API key we got in the initial step
            try:
                self.cities = await get_cities(self.api_key)
            except Exception as e:
                _LOGGER.error(e)
        
        return self.async_show_form(step_id="city", data_schema=vol.Schema({vol.Required("CITY"): vol.In(self.cities)}))
    
    async def async_step_road(self, user_input=None):

        _LOGGER.error(self.city)

        return self.async_show_form(step_id="road", data_schema=vol.Schema({vol.Required("ROAD"): str}))

