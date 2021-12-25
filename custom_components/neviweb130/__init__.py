import logging
import requests
import json
from datetime import timedelta

import voluptuous as vol

import homeassistant.helpers.config_validation as cv
from homeassistant.helpers import discovery
from homeassistant.const import (
    CONF_USERNAME,
    CONF_EMAIL,
    CONF_PASSWORD,
    CONF_SCAN_INTERVAL,
)
from homeassistant.util import Throttle
from .const import (
    DOMAIN,
    CONF_NETWORK,
    ATTR_INTENSITY,
    ATTR_ONOFF,
    ATTR_POWER_MODE,
    ATTR_SETPOINT_MODE,
    ATTR_ROOM_SETPOINT,
    ATTR_ROOM_SETPOINT_MIN,
    ATTR_ROOM_SETPOINT_MAX,
    ATTR_KEYPAD,
    ATTR_BACKLIGHT,
    ATTR_BACKLIGHT_AUTO_DIM,
    ATTR_WIFI_DISPLAY2,
    ATTR_TIMER,
    ATTR_TIME,
    ATTR_TEMP,
    ATTR_LED_ON_INTENSITY,
    ATTR_LED_OFF_INTENSITY,
    ATTR_LED_ON_COLOR,
    ATTR_LED_OFF_COLOR,
    ATTR_LIGHT_WATTAGE,
    ATTR_LEAK_ALERT,
    ATTR_BATT_ALERT,
    ATTR_TEMP_ALERT,
    ATTR_CONF_CLOSURE,
    ATTR_MOTOR_TARGET,
    ATTR_FLOOR_AIR_LIMIT,
    ATTR_SIGNATURE,
    ATTR_EARLY_START,
    ATTR_FLOOR_MODE,
    ATTR_PHASE_CONTROL,
)

VERSION = '0.9.1'

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
            cv.time_period,
    })
},
    extra=vol.ALLOW_EXTRA,
)

def setup(hass, hass_config):
    """Set up neviweb130."""
    data = Neviweb130Data(hass_config[DOMAIN])
    hass.data[DOMAIN] = data

    global SCAN_INTERVAL 
    SCAN_INTERVAL = hass_config[DOMAIN].get(CONF_SCAN_INTERVAL)
    _LOGGER.debug("Setting scan interval to: %s", SCAN_INTERVAL)

    discovery.load_platform(hass, 'climate', DOMAIN, {}, hass_config)
    discovery.load_platform(hass, 'light', DOMAIN, {}, hass_config)
    discovery.load_platform(hass, 'switch', DOMAIN, {}, hass_config)
    discovery.load_platform(hass, 'sensor', DOMAIN, {}, hass_config)

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

# According to HA: 
# https://developers.home-assistant.io/docs/en/creating_component_code_review.html
# "All API specific code has to be part of a third party library hosted on PyPi. 
# Home Assistant should only interact with objects and not make direct calls to the API."
# So all code below this line should eventually be integrated in a PyPi project.

class PyNeviweb130Error(Exception):
    pass

class Neviweb130Client(object):

    def __init__(self, username, password, network, timeout=REQUESTS_TIMEOUT):
        """Initialize the client object."""
        self._email = username
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

    def reconnect(self):
        self.__post_login_page()
        self.__get_network()
        self.__get_gateway_data()

    def __post_login_page(self):
        """Login to Neviweb."""
        data = {"username": self._email, "password": self._password, 
            "interface": "neviweb", "stayConnected": 1}
        try:
            raw_res = requests.post(LOGIN_URL, data=data, 
                cookies = self._cookies, allow_redirects=False, 
                timeout = self._timeout)
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
            _LOGGER.debug("Number of networks found on Neviweb: %s", len(networks))
            if self._network_name == None: # Use 1st network found
                self._gateway_id = networks[0]["id"]
                self._network_name = networks[0]["name"]
                _LOGGER.debug("Selecting %s as network", self._network_name)
            else:
                for network in networks:
                    if network["name"] == self._network_name:
                        self._gateway_id = network["id"]
                        _LOGGER.debug("Selecting %s network among: %s",self._network_name, networks)
                        break
                    elif (network["name"] == self._network_name.capitalize()) or (network["name"] == self._network_name[0].lower()+self._network_name[1:]):
                        self._gateway_id = network["id"]
                        _LOGGER.debug("Please check first letter of your network name, In capital letter or not? Selecting %s network among: %s",
                            self._network_name, networks)
                        break
                    else:
                        _LOGGER.debug("Your network name %s do not correspond to discovered network %s, skipping this one.... Please check your config if nothing is discovered.", self._network_name, network["name"])
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
#        _LOGGER.debug("Updated gateway data: %s", self.gateway_data) 

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
                #raise PyNeviweb130Error("Session expired... reconnecting...")
                return data
        return data

    def get_device_daily_stats(self, device_id):
        """Get device power consumption (in Wh) for the last 30 days."""
        # Prepare return
        data = {}
        # Http request
        try:
            raw_res = requests.get(DEVICE_DATA_URL + str(device_id) +
                    "/energy/daily", headers=self._headers,
                    cookies=self._cookies, timeout=self._timeout)
            _LOGGER.debug("Cannot get devices daily stat: %s", raw_res.json())
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
                "/energy/hourly", headers=self._headers,
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

    def set_onOff(self, device_id, onoff):
        """Set device onOff state."""
        data = {ATTR_ONOFF: onoff}
        self.set_device_attributes(device_id, data)

    def set_valve_onOff(self, device_id, onoff):
        """Set sedna valve onOff state."""
        data = {ATTR_MOTOR_TARGET: onoff}
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

    def set_backlight(self, device_id, level, device):
        """ Set backlight intensity when idle, on or auto """
        """ Work differently for wifi and zigbee devices """
        if device == "wifi":
            data = {ATTR_BACKLIGHT_AUTO_DIM: level}
        else:
            data = {ATTR_BACKLIGHT: level}
        _LOGGER.debug("backlight.data = %s", data)
        self.set_device_attributes(device_id, data)

    def set_second_display(self, device_id, display):
        """Set device second display for outside temperature or setpoint temperature."""
        data = {ATTR_WIFI_DISPLAY2: display}
        _LOGGER.debug("display.data = %s", data)
        self.set_device_attributes(device_id, data)

    def set_keypad_lock(self, device_id, lock):
        """Set device keyboard locked/unlocked."""
        data = {ATTR_KEYPAD: lock}
        _LOGGER.debug("lock.data = %s", data)
        self.set_device_attributes(device_id, data)

    def set_phase(self, device_id, phase):
        """Set device phase control mode."""
        data = {ATTR_PHASE_CONTROL: phase}
        _LOGGER.debug("phase.data = %s", data)
        self.set_device_attributes(device_id, data)

    def set_timer(self, device_id, time):
        """Set device auto off timer."""
        data = {ATTR_TIMER: time}
        _LOGGER.debug("timer.data = %s", data)
        self.set_device_attributes(device_id, data)

    def set_time_format(self, device_id, time):
        """Set device time format 12h or 24h."""
        data = {ATTR_TIME: time}
        _LOGGER.debug("time.data = %s", data)
        self.set_device_attributes(device_id, data)

    def set_temperature_format(self, device_id, deg):
        """Set device temperature format: celsius or fahrenheit."""
        data = {ATTR_TEMP: deg}
        _LOGGER.debug("temperature.data = %s", data)
        self.set_device_attributes(device_id, data)

    def set_floor_air_limit(self, device_id, status, temp):
        """ Set device maximum air temperature limit. """
        if temp == 0:
            temp = Null
        data = {ATTR_FLOOR_AIR_LIMIT:{"status":status,"value":temp}}
        _LOGGER.debug("floorairlimit.data = %s", data)
        self.set_device_attributes(device_id, data)

    def set_early_start(self, device_id, start):
        """Set early start on/off for wifi thermostats."""
        data = {ATTR_EARLY_START: start}
        _LOGGER.debug("early_start.data = %s", data)
        self.set_device_attributes(device_id, data)

    def set_air_floor_mode(self, device_id, mode):
        """switch temperature control between floor and ambiant sensor."""
        data = {ATTR_FLOOR_MODE: mode}
        _LOGGER.debug("floor_mode.data = %s", data)
        self.set_device_attributes(device_id, data)

    def set_setpoint_min(self, device_id, temp):
        """Set device setpoint minimum temperature."""
        data = {ATTR_ROOM_SETPOINT_MIN: temp}
        _LOGGER.debug("setpointMin.data = %s", data)
        self.set_device_attributes(device_id, data)

    def set_setpoint_max(self, device_id, temp):
        """Set device setpoint maximum temperature."""
        data = {ATTR_ROOM_SETPOINT_MAX: temp}
        _LOGGER.debug("setpointMax.data = %s", data)
        self.set_device_attributes(device_id, data)

    def set_led_indicator(self, device_id, state, intensity, red, green, blue):
        """Set devive led indicator intensity and color for on and off state"""
        if state == 1:
            data = {ATTR_LED_ON_COLOR:{"red":red,"green":green,"blue":blue}}
            self.set_device_attributes(device_id, data)
            data2 = {ATTR_LED_ON_INTENSITY:intensity}
            self.set_device_attributes(device_id, data2)
        else:
            data = {ATTR_LED_OFF_COLOR:{"red":red,"green":green,"blue":blue}}
            self.set_device_attributes(device_id, data)
            data2 = {ATTR_LED_OFF_INTENSITY:intensity}
            self.set_device_attributes(device_id, data2)
        _LOGGER.debug("led.data = %s, led.data2 = %s", data, data2)
        self.set_device_attributes(device_id, data)

    def set_wattage(self, device_id, watt):
        """Set light and dimmer watt load."""
        data = {ATTR_LIGHT_WATTAGE:{"status":"on","value":watt}}
        _LOGGER.debug("wattage.data = %s", data)
        self.set_device_attributes(device_id, data)

    def set_valve_alert(self, device_id, batt):
        """Set Sedna valve battery alert on/off."""
        data = {ATTR_BATT_ALERT: batt}
        _LOGGER.debug("valve.data = %s", data)
        self.set_device_attributes(device_id, data)

    def set_valve_temp_alert(self, device_id, temp):
        """Set Sedna valve temperature alert on/off."""
        data = {ATTR_TEMP_ALERT: temp}
        _LOGGER.debug("valve.data = %s", data)
        self.set_device_attributes(device_id, data)

    def set_sensor_alert(self, device_id, leak, batt, temp, close):
        """Set leak detector alert, battery, temperature, leak, Sedna valve closing."""
        data = {ATTR_LEAK_ALERT: leak, ATTR_BATT_ALERT: batt, ATTR_TEMP_ALERT: temp, ATTR_CONF_CLOSURE: close}
        _LOGGER.debug("leak.data = %s", data)
        self.set_device_attributes(device_id, data)

    def set_device_attributes(self, device_id, data):
        result = 1
        while result < 4:
            try:
                resp = requests.put(DEVICE_DATA_URL + str(device_id) + "/attribute",
                    json=data, headers=self._headers, cookies=self._cookies,
                    timeout=self._timeout)
                _LOGGER.debug("Data = %s", data)
                _LOGGER.debug("Request response = %s", resp.status_code)
                _LOGGER.debug("Json Data received= %s", resp.json())
                _LOGGER.debug("Content = %s", resp.content)
                _LOGGER.debug("Text = %s", resp.text)
            except OSError:
                raise PyNeviweb130Error("Cannot set device %s attributes: %s", 
                    device_id, data)
            finally:
                if "error" in resp.json():
                    result += 1
                    _LOGGER.debug("Service error received: %s, resending request %s",resp.json(), result)
                    continue
                else:
                    break
