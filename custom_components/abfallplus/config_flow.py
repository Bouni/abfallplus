from homeassistant import config_entries
import logging
import homeassistant.helpers.config_validation as cv
import voluptuous as vol
from .const import DOMAIN
from .scraper import get_api_key, get_cities, get_districts, get_streets, get_trash_types

_LOGGER = logging.getLogger(__name__)
# https://github.com/home-assistant/example-custom-config/tree/master/custom_components/detailed_hello_world_push
# https://github.com/boralyl/github-custom-component-tutorial/blob/master/custom_components/github_custom/config_flow.py
# https://github.com/BenPru/luxtronik/blob/main/custom_components/luxtronik/config_flow.py


class AbfallPlusConfigFlow(config_entries.ConfigFlow, domain=DOMAIN):
    """AbfallPlus config flow."""

    async def async_step_user(self, user_input):
        """get the municipality waste managemnet website URL from the user"""
        if user_input is not None:
            # If the user has entered the URL, scrape the API key from the website and continue
            try:
                self.api_key = await get_api_key(user_input["URL"])
            except Exception as e:
                _LOGGER.error(e)
            return await self.async_step_city()
        return self.async_show_form(
            step_id="user", data_schema=vol.Schema({vol.Required("URL"): str})
        )

    async def async_step_city(self, user_input=None):
        if user_input is not None:
            self.city = user_input["CITY"]
            return await self.async_step_district()
        else:
            self.cities = {}
            try:
                data = await get_cities(self.api_key)
                self.cities = data.get("cities")
                self.hidden_name = data.get("hidden_name")
                self.hidden_value = data.get("hidden_value")
            except Exception as e:
                _LOGGER.error(e)
        return self.async_show_form(
            step_id="city",
            data_schema=vol.Schema({vol.Required("CITY"): vol.In(self.cities)}),
        )

    async def async_step_district(self, user_input=None):
        if user_input is not None:
            self.district = user_input["DISTRICT"]
            return await self.async_step_street()
        else:
            self.districts = {}
            try:
                self.districts = await get_districts(
                    self.api_key, self.city, self.hidden_name, self.hidden_value
                )
                if len(self.districts) == 1:
                    self.district = list(self.districts.keys())[0]
                    return await self.async_step_street()
            except Exception as e:
                _LOGGER.error(e)
        return self.async_show_form(
            step_id="district",
            data_schema=vol.Schema({vol.Required("DISTRICT", default=list(self.districts.keys())[0]): vol.In(self.districts)}),
        )

    async def async_step_street(self, user_input=None):
        if user_input is not None:
            self.street = user_input["STREET"]
            return await self.async_step_trash_type()
        else:
            self.streets = {}
            try:
                self.streets = await get_streets(
                    self.api_key,
                    self.city,
                    self.district,
                    self.hidden_name,
                    self.hidden_value,
                )
                if len(self.streets) == 1:
                    self.street = list(self.streets.keys())[0]
                    return await self.async_step_trash_type()
            except Exception as e:
                _LOGGER.error(e)

        return self.async_show_form(
            step_id="street",
            data_schema=vol.Schema({vol.Required("STREET", default=list(self.streets.keys())[0]): vol.In(self.streets)}),
        )

    async def async_step_trash_type(self, user_input=None):
        _LOGGER.warning("Step trash type") 
        if user_input is not None:
            self.trash_type = user_input["TRASH_TYPE"]
        else:
            self.trash_types = {}
            try:
                self.trash_types = await get_trash_types(
                    self.api_key,
                    self.city,
                    self.district,
                    self.street,
                    self.hidden_name,
                    self.hidden_value,
                )
                _LOGGER.error(self.trash_types)
                
            except Exception as e:
                _LOGGER.error(e)

        return self.async_show_form(
            step_id="trash_type",
            data_schema=vol.Schema({vol.Required("TRASH_TYPE", default=list(self.trash_types.keys())): cv.multi_select(self.trash_types)})
        )

