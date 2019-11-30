import logging
import requests
import json
from datetime import timedelta

import voluptuous as vol

import homeassistant.helpers.config_validation as cv
from homeassistant.helpers import discovery
from homeassistant.const import (CONF_USERNAME, CONF_EMAIL, CONF_PASSWORD,
    CONF_SCAN_INTERVAL)
from homeassistant.util import Throttle
from .const import (DOMAIN, CONF_NETWORK, ATTR_INTENSITY, ATTR_POWER_MODE,
    ATTR_SETPOINT_MODE, ATTR_ROOM_SETPOINT, ATTR_SIGNATURE)

VERSION = '0.0.1'

_LOGGER = logging.getLogger(__name__)

SCAN_INTERVAL = timedelta(seconds=540)

REQUESTS_TIMEOUT = 30
HOST = "https://neviweb.com"
LOGIN_URL = "{}/api/login".format(HOST)
LOCATIONS_URL = "{}/api/locations".format(HOST)
GATEWAY_DEVICE_URL = "{}/api/devices?location$id=".format(HOST)
DEVICE_DATA_URL = "{}/api/device/".format(HOST)

CONFIG_SCHEMA = vol.Schema({
    DOMAIN: vol.Schema({
        vol.Required(CONF_USERNAME): cv.string,
        vol.Required(CONF_PASSWORD): cv.string,
        vol.Optional(CONF_NETWORK): cv.string,
        vol.Optional(CONF_SCAN_INTERVAL, default=SCAN_INTERVAL):
            cv.time_period
    })
}, extra=vol.ALLOW_EXTRA)

async def async_setup(hass, hass_config):
    """Set up neviweb130."""
    data = Neviweb130Data(hass_config[DOMAIN])
    hass.data[DOMAIN] = data

    global SCAN_INTERVAL 
    SCAN_INTERVAL = hass_config[DOMAIN].get(CONF_SCAN_INTERVAL)
    _LOGGER.debug("Setting scan interval to: %s", SCAN_INTERVAL)

    discovery.load_platform(hass, 'climate', DOMAIN, {}, hass_config)
    discovery.load_platform(hass, 'light', DOMAIN, {}, hass_config)
    discovery.load_platform(hass, 'switch', DOMAIN, {}, hass_config)

    return True

class Neviweb130Data:
    """Get the latest data and update the states."""

    def __init__(self, config):
        """Init the neviweb130 data object."""
        # from pyneviweb130 import Neviweb130Client
        username = config.get(CONF_USERNAME)
        password = config.get(CONF_PASSWORD)
        network = config.get(CONF_NETWORK)
        self.neviweb130_client = Neviweb130Client(username, password, network)

    # Need some refactoring here concerning the class used to transport data
    # @Throttle(SCAN_INTERVAL)
    # def update(self):
    #     """Get the latest data from pyneviweb."""
    #     self.neviweb130_client.update()
    #     _LOGGER.debug("Neviweb130 data updated successfully")



# According to HA: 
# https://developers.home-assistant.io/docs/en/creating_component_code_review.html
# "All API specific code has to be part of a third party library hosted on PyPi. 
# Home Assistant should only interact with objects and not make direct calls to the API."
# So all code below this line should eventually be integrated in a PyPi project.

class PyNeviweb130Error(Exception):
    pass

class Neviweb130Client(object):

    def __init__(self, email, password, network, timeout=REQUESTS_TIMEOUT):
        """Initialize the client object."""
        self._email = email
        self._password = password
        self._network_name = network
        self._gateway_id = None
        self.gateway_data = {}
        self._headers = None
        self._cookies = None
        self._timeout = timeout
        self.user = None

        self.__post_login_page()
        self.__get_network()
        self.__get_gateway_data()

    def update(self):
        self.__get_gateway_data()

    def __post_login_page(self):
        """Login to Neviweb."""
        data = {"username": self._email, "password": self._password, 
            "interface": "neviweb", "stayConnected": 1}
        try:
            raw_res = requests.post(LOGIN_URL, data=data, 
                cookies=self._cookies, allow_redirects=False, 
                timeout=self._timeout)
        except OSError:
            raise PyNeviweb130Error("Cannot submit login form")
        if raw_res.status_code != 200:
            raise PyNeviweb130Error("Cannot log in")

        # Update session
        self._cookies = raw_res.cookies
        data = raw_res.json()
        _LOGGER.debug("Login response: %s", data)
        if "error" in data:
            if data["error"]["code"] == "ACCSESSEXC":
                _LOGGER.error("Too many active sessions. Close all neviweb130 " +
                "sessions you have opened on other platform (mobile, browser" +
                ", ...), wait a few minutes, then reboot Home Assistant.")
            return False
        else:
            self.user = data["user"]
            self._headers = {"Session-Id": data["session"]}
            _LOGGER.debug("Successfully logged in")
            return True

    def __get_network(self):
        """Get gateway id associated to the desired network."""
        # Http request
        try:
            raw_res = requests.get(LOCATIONS_URL, headers=self._headers, 
                cookies=self._cookies, timeout=self._timeout)
            networks = raw_res.json()

            if self._network_name == None: # Use 1st network found
                self._gateway_id = networks[0]["id"]
                self._network_name = networks[0]["name"]
            else:
                for network in networks:
                    if network["name"] == self._network_name:
                        self._gateway_id = network["id"]
                        break
            _LOGGER.debug("Selecting %s network among: %s",
                self._network_name, networks)
        except OSError:
            raise PyNeviweb130Error("Cannot get network")
        # Update cookies
        self._cookies.update(raw_res.cookies)
        # Prepare data
        self.gateway_data = raw_res.json()

    def __get_gateway_data(self):
        """Get gateway data."""
        # Http request
        try:
            raw_res = requests.get(GATEWAY_DEVICE_URL + str(self._gateway_id),
                headers=self._headers, cookies=self._cookies, 
                timeout=self._timeout)
            _LOGGER.debug("Received gateway data: %s", raw_res.json())
        except OSError:
            raise PyNeviweb130Error("Cannot get gateway data")
        # Update cookies
        self._cookies.update(raw_res.cookies)
        # Prepare data
        self.gateway_data = raw_res.json()

        for device in self.gateway_data:
            data = self.get_device_attributes(device["id"], [ATTR_SIGNATURE])
            if ATTR_SIGNATURE in data:
                device[ATTR_SIGNATURE] = data[ATTR_SIGNATURE]
            _LOGGER.debug("Received signature data: %s", data)     ###
        # _LOGGER.debug("Updated gateway data: %s", self.gateway_data) 

    def get_device_attributes(self, device_id, attributes):
        """Get device attributes."""
        # Prepare return
        data = {}
        # Http request
        try:
            raw_res = requests.get(DEVICE_DATA_URL + str(device_id) +
                "/attribute?attributes=" + ",".join(attributes), 
                headers=self._headers, cookies=self._cookies,
                timeout=self._timeout)
#            _LOGGER.debug("Received devices data: %s", raw_res.json())
        except requests.exceptions.ReadTimeout:
            return {"errorCode": "ReadTimeout"}
        except Exception as e:
            raise PyNeviweb130Error("Cannot get device attributes", e)
        # Update cookies
        self._cookies.update(raw_res.cookies)
        # Prepare data
        data = raw_res.json()
        if "error" in data:
            if data["error"]["code"] == "USRSESSEXP":
                _LOGGER.error("Session expired. Set a scan_interval less" +
                "than 10 minutes, otherwise the session will end.")
                raise PyNeviweb130Error("Session expired")
        return data

    def get_device_daily_stats(self, device_id):
        """Get device power consumption (in Wh) for the last 30 days."""
        # Prepare return
        data = {}
        # Http request
        try:
            raw_res = requests.get(DEVICE_DATA_URL + str(device_id) +
                    "/statistics/30days", headers=self._headers,
                    cookies=self._cookies, timeout=self._timeout)
        except OSError:
            raise PyNeviweb130Error("Cannot get device daily stats")
        # Update cookies
        self._cookies.update(raw_res.cookies)
        # Prepare data
        data = raw_res.json()
        if "values" in data:
            return data["values"]
        return []

    def get_device_hourly_stats(self, device_id):
        """Get device power consumption (in Wh) for the last 24 hours."""
        # Prepare return
        data = {}
        # Http request
        try:
            raw_res = requests.get(DEVICE_DATA_URL + str(device_id) +
                "/statistics/24hours", headers=self._headers,
                cookies=self._cookies, timeout=self._timeout)
        except OSError:
            raise PyNeviweb130Error("Cannot get device hourly stats")
        # Update cookies
        self._cookies.update(raw_res.cookies)
        # Prepare data
        data = raw_res.json()
        if "values" in data:
            return data["values"]
        return []

    def set_brightness(self, device_id, brightness):
        """Set device brightness."""
        data = {ATTR_INTENSITY: brightness}
        self.set_device_attributes(device_id, data)

    def set_mode(self, device_id, mode):
        """Set device operation mode."""
        data = {ATTR_POWER_MODE: mode}
        self.set_device_attributes(device_id, data)

    def set_setpoint_mode(self, device_id, mode):
        """Set thermostat operation mode."""
        data = {ATTR_SETPOINT_MODE: mode}
        self.set_device_attributes(device_id, data)

    def set_temperature(self, device_id, temperature):
        """Set device temperature."""
        data = {ATTR_ROOM_SETPOINT: temperature}
        self.set_device_attributes(device_id, data)

    def set_device_attributes(self, device_id, data):
        try:
            requests.put(DEVICE_DATA_URL + str(device_id) + "/attribute",
                data=data, headers=self._headers, cookies=self._cookies,
                timeout=self._timeout)
        except OSError:
            raise PyNeviweb130Error("Cannot set device %s attributes: %s", 
                device_id, data)
