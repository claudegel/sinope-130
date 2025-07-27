"""The data update coordinator for neviweb130."""

import logging
import aiohttp
import json
from datetime import timedelta

import voluptuous as vol

import homeassistant.helpers.device_registry as dr
from homeassistant.helpers.update_coordinator import (
    DataUpdateCoordinator,
    UpdateFailed,
)
from homeassistant import config_entries
from homeassistant.core import HomeAssistant, callback
from homeassistant.helpers import (
    config_validation as cv,
    discovery, 
    entity_registry as er,
)
from homeassistant.helpers.event import async_call_later
from homeassistant.helpers.typing import ConfigType
from homeassistant.const import (
    CONF_USERNAME,
    CONF_EMAIL,
    CONF_PASSWORD,
    CONF_SCAN_INTERVAL,
    EVENT_HOMEASSISTANT_STOP,
)
from homeassistant.util import Throttle

from homeassistant.components.climate.const import (
    HVACMode,
    PRESET_AWAY,
    PRESET_HOME,
    )
from homeassistant.components.persistent_notification import DOMAIN as PN_DOMAIN
from .schema import (
    CONFIG_SCHEMA,
    PLATFORMS,
    VERSION,
)
from .session_manager import session_manager

from .const import (
    ATTR_AUX_CYCLE,
    ATTR_AUX_HEAT_TIMEON,
    ATTR_BACKLIGHT,
    ATTR_BACKLIGHT_AUTO_DIM,
    ATTR_BALANCE_PT,
    ATTR_BATT_ALERT,
    ATTR_BATTERY_TYPE,
    ATTR_COLD_LOAD_PICKUP_REMAIN_TIME,
    ATTR_CONF_CLOSURE,
    ATTR_CONTROLLED_DEVICE,
    ATTR_COOL_MIN_TIME_OFF,
    ATTR_COOL_MIN_TIME_ON,
    ATTR_COOL_LOCK_TEMP,
    ATTR_COOL_SETPOINT,
    ATTR_COOL_SETPOINT_MAX,
    ATTR_COOL_SETPOINT_MIN,
    ATTR_CYCLE,
    ATTR_CYCLE_OUTPUT2,
    ATTR_DISPLAY_CONF,
    ATTR_DISPLAY2,
    ATTR_DRSETPOINT,
    ATTR_DRSTATUS,
    ATTR_EARLY_START,
    ATTR_FAN_SPEED,
    ATTR_FAN_SWING_HORIZ,
    ATTR_FAN_SWING_VERT,
    ATTR_FLOOR_AUX,
    ATTR_FLOOR_AIR_LIMIT,
    ATTR_FLOOR_MAX,
    ATTR_FLOOR_MIN,
    ATTR_FLOW_ENABLED,
    ATTR_FLOW_METER_CONFIG,
    ATTR_FLOOR_MODE,
    ATTR_FLOOR_OUTPUT2,
    ATTR_FLOOR_SENSOR,
    ATTR_FLOW_ALARM1_LENGHT,
    ATTR_FLOW_ALARM1_OPTION,
    ATTR_FLOW_ALARM1_PERIOD,
    ATTR_FLOW_THRESHOLD,
    ATTR_FUEL_ALERT,
    ATTR_FUEL_PERCENT_ALERT,
    ATTR_GAUGE_TYPE,
    ATTR_HEAT_COOL,
    ATTR_HEAT_LOCK_TEMP,
    ATTR_HUMIDITY,
    ATTR_HUMIDIFIER_TYPE,
    ATTR_HUMID_SETPOINT,
    ATTR_INPUT_1_OFF_DELAY,
    ATTR_INPUT_2_OFF_DELAY,
    ATTR_INPUT_1_ON_DELAY,
    ATTR_INPUT_2_ON_DELAY,
    ATTR_INTENSITY,
    ATTR_INTENSITY_MIN,
    ATTR_KEY_DOUBLE_UP,
    ATTR_KEYPAD,
    ATTR_LANGUAGE,
    ATTR_LEAK_ALERT,
    ATTR_LED_OFF_COLOR,
    ATTR_LED_OFF_INTENSITY,
    ATTR_LED_ON_COLOR,
    ATTR_LED_ON_INTENSITY,
    ATTR_LIGHT_WATTAGE,
    ATTR_MODE,
    ATTR_MOTOR_TARGET,
    ATTR_NAME_1,
    ATTR_NAME_2,
    ATTR_OCCUPANCY,
    ATTR_ONOFF,
    ATTR_ONOFF2,
    ATTR_OUTPUT_NAME_1,
    ATTR_OUTPUT_NAME_2,
    ATTR_PHASE_CONTROL,
    ATTR_POWER_MODE,
    ATTR_POWER_SUPPLY,
    ATTR_PUMP_PROTEC,
    ATTR_PUMP_PROTEC_DURATION,
    ATTR_PUMP_PROTEC_PERIOD,
    ATTR_REFUEL,
    ATTR_ROOM_SETPOINT,
    ATTR_ROOM_SETPOINT_MIN,
    ATTR_ROOM_SETPOINT_MAX,
    ATTR_SETPOINT_MODE,
    ATTR_SIGNATURE,
    ATTR_SOUND_CONF,
    ATTR_SYSTEM_MODE,
    ATTR_TANK_HEIGHT,
    ATTR_TANK_SIZE,
    ATTR_TANK_TYPE,
    ATTR_TIMER,
    ATTR_TIMER2,
    ATTR_TIME,
    ATTR_TEMP,
    ATTR_TEMP_ALERT,
    ATTR_WATER_TEMP_MIN,
    ATTR_WIFI_KEYPAD,
    DOMAIN,
    CONF_HOMEKIT_MODE,
    CONF_IGNORE_MIWI,
    CONF_NETWORK,
    CONF_NETWORK2,
    CONF_NETWORK3,
    CONF_NOTIFY,
    CONF_STAT_INTERVAL,
    MODE_AWAY,
    MODE_HOME,
    MODE_MANUAL,
)

_LOGGER = logging.getLogger(__name__)

REQUESTS_TIMEOUT = 30
HOST = "https://neviweb.com"
LOGIN_URL = f"{HOST}/api/login"
LOCATIONS_URL = f"{HOST}/api/locations?account$id="
GATEWAY_DEVICE_URL = f"{HOST}/api/devices?location$id="
DEVICE_DATA_URL = f"{HOST}/api/device/"
NEVIWEB_LOCATION = f"{HOST}/api/location/"

# According to HA: 
# https://developers.home-assistant.io/docs/en/creating_component_code_review.html
# "All API specific code has to be part of a third party library hosted on PyPi. 
# Home Assistant should only interact with objects and not make direct calls to the API."
# So all code below this line should eventually be integrated in a PyPi project.


class PyNeviweb130Error(Exception):
    pass


class Neviweb130Client:

    def __init__(self, hass: HomeAssistant, ignore_miwi, username: str, password: str, network: str, network2: str = None, network3: str = None, timeout=REQUESTS_TIMEOUT):
        """Initialize the client object."""
#        self.coordinator = coordinator
        self.hass = hass
        self._email = username
        self._password = password
        self._network_name = network
        self._network_name2 = network2
        self._network_name3 = network3
        self._ignore_miwi = ignore_miwi
        self._gateway_id = None
        self._gateway_id2 = None
        self._gateway_id3 = None
        self.gateway_data = {}
        self.gateway_data2 = {}
        self.gateway_data3 = {}
        self._session = None
        self._headers = None
        self._account = None
        self._cookies = None
        self._timeout = timeout
        self._occupancyMode = None
        self.user = None
        self._response = None

    async def create_session(self):
        """Create a new session for Neviweb API."""
        self._session = await session_manager.create_session()
        return self._session

    async def async_initialize(self):
        """Asynchronously initialize the client."""
        _LOGGER.debug("Initializing Neviweb130Client...")
        await self.create_session()
        if self._account is None:
            await self.async_post_login_page()
            await self.async_get_network()
            await self.async_get_gateway_data()

    async def async_update(self):
        _LOGGER.debug("Fetching devices data from Neviweb API")
        await self.async_get_gateway_data()
        return {
            "gateway_data": self.gateway_data,
            "gateway_data2": self.gateway_data2,
            "gateway_data3": self.gateway_data3,
        }

    async def async_reconnect(self):
        await self.async_post_login_page()
        await self.async_get_network()
        await self.async_get_gateway_data()

    def notify_ha(self, msg: str, title: str = "Neviweb130 integration "+VERSION):
        """Notify user via HA web frontend."""
        self.hass.services.call(
            PN_DOMAIN,
            "create",
            service_data={
                "title": title,
                "message": msg,
            },
            blocking=False,
        )
        return True

    async def async_post_login_page(self):
        """Login to Neviweb."""
        data = {"username": self._email, "password": self._password, 
                "interface": "neviweb", "stayConnected": 1}

        try:
            async with self._session.post(LOGIN_URL, json=data, 
                                    cookies = self._cookies, 
                                    allow_redirects = False, 
                                    timeout = self._timeout) as response:
#                _LOGGER.debug("login status: %s", response.status)
                if response.status != 200:
                    if response.status == 429:
                        _LOGGER.debug("Login fail status: %s, too many requests, retry later", response.status)
                    else:
                        _LOGGER.debug("Fail login status: %s", response.status)
                    raise PyNeviweb130Error("Cannot log in")

                raw_res = await response.json()
        except aiohttp.ClientError as e:
            raise PyNeviweb130Error("Cannot submit login form... Check your network or firewall.") from e

        # Update session
#        _LOGGER.debug("cookies = %s", response)
        self._cookies = response.cookies
        data = raw_res
        _LOGGER.debug("Login response: %s", data)
        if "error" in data:
            if data["error"]["code"] == "ACCSESSEXC":
                _LOGGER.error(
                    "Too many active sessions. Close all neviweb130 "
                    + "sessions you have opened on other platform (mobile, browser"
                    + ", ...), wait a few minutes, then restart Home Assistant."
                )
                self.notify_ha(
                    "Warning: Got ACCSESSEXC error, Too many active sessions."
                    + "Close all neviweb130 sessions, wait few minutes and "
                    + "restart HA."
                )
            elif data["error"]["code"] == "USRBADLOGIN":
                _LOGGER.error(
                    "Invalid Neviweb username and/or password... "
                    + "Check your configuration parameters"
                )
                self.notify_ha(
                    "Warning: Got USRBADLOGIN error, Invalid Neviweb username "
                    + "and/or password... Check your configuration parameters"
                )
            return False
        else:
            self.user = data["user"]
            self._headers = {"Session-Id": data["session"]}
            self._account = str(data["account"]["id"])
            _LOGGER.debug("Successfully logged in to: %s", self._account)
            return True

    async def async_get_network(self):
        """Get gateway id associated to the desired network."""
#        session = await create_session()
        try:
            async with self._session.get(LOCATIONS_URL + self._account, headers=self._headers, cookies=self._cookies, timeout=self._timeout) as response:
                raw_res = await response.json()
                networks = raw_res
                _LOGGER.debug("Number of networks found on Neviweb: %s", len(networks))
                _LOGGER.debug("networks: %s", networks)
                if self._network_name == None and self._network_name2 == None and self._network_name3 == None:
                    # Use 1st network found, second or third if found
                    self._gateway_id = networks[0]["id"]
                    self._network_name = networks[0]["name"]
                    self._occupancyMode = networks[0]["mode"]
                    _LOGGER.debug("Selecting %s as first network", self._network_name)
                    if len(networks) > 1:
                        self._gateway_id2 = networks[1]["id"]
                        self._network_name2 = networks[1]["name"]
                        _LOGGER.debug("Selecting %s as second network", self._network_name2)
                        if len(networks) > 2:
                            self._gateway_id3 = networks[2]["id"]
                            self._network_name3 = networks[2]["name"]
                            _LOGGER.debug("Selecting %s as third network", self._network_name3)
                else:
                    for network in networks:
                        if network["name"] == self._network_name:
                            self._gateway_id = network["id"]
                            self._occupancyMode = network["mode"]
                            _LOGGER.debug(
                                "Selecting %s network among: %s",
                                self._network_name,
                                networks,
                            )
                            continue
                        elif (network["name"] == self._network_name.capitalize()) or (
                            network["name"]
                            == self._network_name[0].lower() + self._network_name[1:]
                        ):
                            self._gateway_id = network["id"]
                            _LOGGER.debug(
                                "Please check first letter of your network "
                                + "name, In capital letter or not? Selecting "
                                + "%s network among: %s",
                                self._network_name,
                                networks,
                            )
                            continue
                        else:
                            _LOGGER.debug(
                                "Your network name %s do not correspond to "
                                + "discovered network %s, skipping this one"
                                + "... Please check your config if nothing "
                                + "is discovered.",
                                self._network_name,
                                network["name"],
                            )
                        if (
                            self._network_name2 is not None
                            and self._network_name2 != ""
                        ):
                            if network["name"] == self._network_name2:
                                self._gateway_id2 = network["id"]
                                _LOGGER.debug(
                                    "Selecting %s network among: %s",
                                    self._network_name2,
                                    networks,
                                )
                                continue
                            elif (
                                network["name"] == self._network_name2.capitalize()
                            ) or (
                                network["name"]
                                == self._network_name2[0].lower()
                                + self._network_name2[1:]
                            ):
                                self._gateway_id = network["id"]
                                _LOGGER.debug(
                                    "Please check first letter of your "
                                    + "network2 name, In capital letter or "
                                    + "not? Selecting %s network among: %s",
                                    self._network_name2,
                                    networks,
                                )
                                continue
                            else:
                                _LOGGER.debug(
                                    "Your network name %s do not correspond "
                                    + "to discovered network %s, skipping "
                                    + "this one...",
                                    self._network_name2,
                                    network["name"],
                                )
                        if (
                            self._network_name3 is not None
                            and self._network_name3 != ""
                        ):
                            if network["name"] == self._network_name3:
                                self._gateway_id3 = network["id"]
                                _LOGGER.debug(
                                    "Selecting %s network among: %s",
                                    self._network_name3,
                                    networks,
                                )
                                continue
                            elif (
                                network["name"] == self._network_name3.capitalize()
                            ) or (
                                network["name"]
                                == self._network_name3[0].lower()
                                + self._network_name3[1:]
                            ):
                                self._gateway_id = network["id"]
                                _LOGGER.debug(
                                    "Please check first letter of your "
                                    + "network3 name, In capital letter or "
                                    + "not? Selecting %s network among: %s",
                                    self._network_name3,
                                    networks,
                                )
                                continue
                            else:
                                _LOGGER.debug(
                                    "Your network name %s do not correspond "
                                    + "to discovered network %s, skipping "
                                    + "this one...",
                                    self._network_name3,
                                    network["name"],
                                )

        except aiohttp.ClientError as e:
            raise PyNeviweb130Error("Cannot get Neviweb's networks") from e
        # Update cookies
        self._cookies.update(response.cookies)
        # Prepare data
        self.gateway_data = raw_res

    async def async_get_gateway_data(self):
        """Get gateway data."""
        if self._gateway_id == None and self._gateway_id2 == None and self._gateway_id3 == None:
            _LOGGER.debug("No gateway defined, check your config for networks names...")
            return False
        else:
#            session = await create_session()
            try:
                async with self._session.get(GATEWAY_DEVICE_URL + str(self._gateway_id), headers=self._headers, cookies=self._cookies, timeout=self._timeout) as response:
                    raw_res = await response.json()
                    _LOGGER.debug("Received gateway data: %s", raw_res)
                    if "error" in raw_res:
                        if raw_res["error"]["code"] == "VALINVLD":
                            _LOGGER.debug("No network found, check your configuration")
                            raise PyNeviweb130Error("No network found, check your configuration")
                            return False
            except aiohttp.ClientError as e:
                raise PyNeviweb130Error("Cannot get gateway data") from e
            # Update cookies
            self._cookies.update(response.cookies)
            # Prepare data
            self.gateway_data = raw_res
            _LOGGER.debug("Gateway_data : %s", self.gateway_data)
            if self._gateway_id2 is not None:
                try:
                    async with self._session.get(GATEWAY_DEVICE_URL + str(self._gateway_id2), headers=self._headers, cookies=self._cookies, timeout=self._timeout) as response:
                        raw_res2 = await response.json()
                        _LOGGER.debug("Received gateway data 2: %s", raw_res2)
                except aiohttp.ClientError as e:
                    raise PyNeviweb130Error("Cannot get gateway data 2") from e
                # Prepare data
                self.gateway_data2 = raw_res2
                _LOGGER.debug("Gateway_data2 : %s", self.gateway_data2)
            if self._gateway_id3 is not None:
                try:
                    async with self._session.get(GATEWAY_DEVICE_URL + str(self._gateway_id3), headers=self._headers, cookies=self._cookies, timeout=self._timeout) as response:
                        raw_res3 = await response.json()
                        _LOGGER.debug("Received gateway data 3: %s", raw_res3)
                except aiohttp.ClientError as e:
                    raise PyNeviweb130Error("Cannot get gateway data 3") from e
                # Prepare data
                self.gateway_data3 = raw_res3
                _LOGGER.debug("Gateway_data3 : %s", self.gateway_data3)
            for device in self.gateway_data:
                data = await self.async_get_device_attributes(device["id"], [ATTR_SIGNATURE])
                if ATTR_SIGNATURE in data:
                    device[ATTR_SIGNATURE] = data[ATTR_SIGNATURE]
                _LOGGER.debug("Received signature data: %s", data)
                if data[ATTR_SIGNATURE]["protocol"] == "miwi":
                    if not self._ignore_miwi:
                        _LOGGER.debug(
                            "The Neviweb location selected for parameter "
                            + "«network» contain unsupported device with protocol"
                            + " miwi. If this location contain only miwi devices "
                            + "it should be added to custom_component "
                            + "«sinope neviweb» custom_components instead. If the"
                            + " location contain mixed miwi, zigbee and/or wifi "
                            + "devices, add parameter: ignore_miwi: True, in your "
                            + "neviweb130 configuration."
                        )
            if self._gateway_id2 is not None:
                for device in self.gateway_data2:
                    data2 = await self.async_get_device_attributes(device["id"], [ATTR_SIGNATURE])
                    if ATTR_SIGNATURE in data2:
                        device[ATTR_SIGNATURE] = data2[ATTR_SIGNATURE]
                    _LOGGER.debug("Received signature data 2: %s", data2)
                    if data2[ATTR_SIGNATURE]["protocol"] == "miwi":
                        if not self._ignore_miwi:
                            _LOGGER.debug(
                                "The Neviweb location selected for parameter "
                                + "«network2» contain unsupported device with protocol"
                                + " miwi. If this location contain only miwi devices "
                                + "it should be added to custom_component "
                                + "«sinope neviweb» custom_components instead. If the"
                                + " location contain mixed miwi, zigbee and/or wifi "
                                + "devices, add parameter: ignore_miwi: True, in your "
                                + "neviweb130 configuration."
                            )
            if self._gateway_id3 is not None:
                for device in self.gateway_data3:
                    data3 = await self.async_get_device_attributes(device["id"], [ATTR_SIGNATURE])
                    if ATTR_SIGNATURE in data3:
                        device[ATTR_SIGNATURE] = data2[ATTR_SIGNATURE]
                    _LOGGER.debug("Received signature data 3: %s", data3)
                    if data3[ATTR_SIGNATURE]["protocol"] == "miwi":
                        if not self._ignore_miwi:
                            _LOGGER.debug(
                                "The Neviweb location selected for parameter "
                                + "«network3» contain unsupported device with protocol"
                                + " miwi. If this location contain only miwi devices "
                                + "it should be added to custom_component "
                                + "«sinope neviweb» custom_components instead. If the"
                                + " location contain mixed miwi, zigbee and/or wifi "
                                + "devices, add parameter: ignore_miwi: True, in your "
                                + "neviweb130 configuration."
                            )

#            _LOGGER.debug("Updated gateway data: %s", self.gateway_data) 
#            _LOGGER.debug("Updated gateway data2: %s", self.gateway_data2)
#            _LOGGER.debug("Updated gateway data3: %s", self.gateway_data3)

    async def async_get_device_attributes(self, device_id, attributes):
        """Get device attributes."""
        # Prepare return
        data = {}
#        session = await create_session()
        try:
            async with self._session.get(DEVICE_DATA_URL + str(device_id) + "/attribute?attributes=" + ",".join(attributes), 
                     headers=self._headers, cookies=self._cookies, timeout=self._timeout) as response:
                raw_res = await response.json()
#                _LOGGER.debug("Received devices data: %s", raw_res) 
        except aiohttp.ClientError as e:
            raise PyNeviweb130Error("Cannot get device attributes") from e
        # Update cookies
        self._cookies.update(response.cookies)
        # Prepare data
        data = raw_res
        if "error" in data:
            if data["error"]["code"] == "USRSESSEXP":
                _LOGGER.error(
                    "Session expired. Set a scan_interval less"
                    + "than 10 minutes, otherwise the session will end."
                )
                #raise PyNeviweb130Error("Session expired... reconnecting...")
        return data

    async def async_get_device_status(self, device_id):
        """Get device status for the GT130."""
        # Prepare return
        data = {}
#        session = await create_session()
        try:
            async with self._session.get(DEVICE_DATA_URL + str(device_id) + "/status", headers=self._headers, cookies=self._cookies, timeout=self._timeout) as response:
                raw_res = await response.json()
                _LOGGER.debug("Received devices status: %s", raw_res)
        except aiohttp.ClientError as e:
            raise PyNeviweb130Error("Cannot get device status") from e
        # Update cookies
        self._cookies.update(response.cookies)
        # Prepare data
        data = raw_res
        if "error" in data:
            if data["error"]["code"] == "USRSESSEXP":
                _LOGGER.error(
                    "Session expired. Set a scan_interval less"
                    + "than 10 minutes, otherwise the session will end."
                )
                #raise PyNeviweb130Error("Session expired... reconnecting...")
        return data

    async def async_get_neviweb_status(self, location):
        """Get neviweb occupancyMode status."""
        # Prepare return
        data = {}
#        session = await create_session()
        try:
            async with self._session.get(NEVIWEB_LOCATION + str(location) + "/notifications", headers=self._headers, cookies=self._cookies, timeout=self._timeout) as response:
                raw_res = await response.json()
                _LOGGER.debug("Received neviweb status: %s", raw_res)
        except aiohttp.ClientError as e:
            raise PyNeviweb130Error("Cannot get neviweb status") from e
        # Update cookies
        self._cookies.update(response.cookies)
        # Prepare data
        data = raw_res
        if "error" in data:
            if data["error"]["code"] == "USRSESSEXP":
                _LOGGER.error(
                    "Session expired. Set a scan_interval less"
                    + "than 10 minutes, otherwise the session will end."
                )
                #raise PyNeviweb130Error("Session expired... reconnecting...")
        return data

    async def async_get_device_alert(self, device_id):
        """Get device alert for Sedna valve."""
        # Prepare return
        data = {}
#        session = await create_session()
        try:
            async with self._session.get(DEVICE_DATA_URL + str(device_id) + "/alert", headers=self._headers, cookies=self._cookies, timeout=self._timeout) as response:
                raw_res = await response.json()
                _LOGGER.debug(
                    "Received devices alert (%s): %s",
                    str(device_id),
                    raw_res,
                )
        except aiohttp.ClientError as e:
            raise PyNeviweb130Error("Cannot get device alert") from e
        # Update cookies
        self._cookies.update(response.cookies)
        # Prepare data
        data = raw_res
        if "error" in data:
            if data["error"]["code"] == "USRSESSEXP":
                _LOGGER.error(
                    "Session expired. Set a scan_interval less"
                    + "than 10 minutes, otherwise the session will end."
                )
                #raise PyNeviweb130Error("Session expired... reconnecting...")
        return data

    async def async_get_device_monthly_stats(self, device_id):
        """Get device power consumption (in Wh) for the last 24 months."""
        # Prepare return
        data = {}
#        session = await create_session()
        try:
            async with self._session.get(DEVICE_DATA_URL + str(device_id) + "/consumption/monthly", headers=self._headers, cookies=self._cookies, timeout=self._timeout) as response:
                raw_res = await response.json()
                _LOGGER.debug("Received devices monthly stat (%s): %s",str(device_id), raw_res)
        except aiohttp.ClientError as e:
            raise PyNeviweb130Error("Cannot get device monthly stats...") from e
            return None
        # Update cookies
        self._cookies.update(response.cookies)
        # Prepare data
        data = raw_res
        #_LOGGER.debug("Monthly_stats data: %s", data)
        if "history" in data:
            return data["history"]
        else:
            _LOGGER.debug("Monthly stat error: %s", data)
            return None

    async def async_get_device_daily_stats(self, device_id):
        """Get device power consumption (in Wh) for the last 30 days."""
        # Prepare return
        data = {}
#        session = await create_session()
        try:
            async with self._session.get(DEVICE_DATA_URL + str(device_id) + "/consumption/daily", headers=self._headers, cookies=self._cookies, timeout=self._timeout) as response:
                raw_res = await response.json()
                _LOGGER.debug("Received devices daily stat (%s): %s",str(device_id), raw_res)
        except aiohttp.ClientError as e:
            raise PyNeviweb130Error("Cannot get device daily stats...") from e
            return None
        # Update cookies
        self._cookies.update(response.cookies)
        # Prepare data
        data = raw_res
        #_LOGGER.debug("Daily_stats data: %s", data)
        if "history" in data:
            return data["history"]
        else:
            _LOGGER.debug("Daily stat error: %s", data)
            return None

    async def async_get_device_hourly_stats(self, device_id):
        """Get device power consumption (in Wh) for the last 24 hours."""
        # Prepare return
        data = {}
#        session = await create_session()
        try:
            async with self._session.get(DEVICE_DATA_URL + str(device_id) + "/consumption/hourly", headers=self._headers, cookies=self._cookies, timeout=self._timeout) as response:
                raw_res = await response.json()
                _LOGGER.debug("Received devices hourly stat (%s): %s",str(device_id), raw_res)
        except aiohttp.ClientError as e:
            raise PyNeviweb130Error("Cannot get device hourly stats...") from e
            return None
        # Update cookies
        self._cookies.update(response.cookies)
        # Prepare data
        data = raw_res
        #_LOGGER.debug("Hourly_stats data: %s", data)
        if "history" in data:
            return data["history"]
        else:
            _LOGGER.debug("Hourly stat error: %s", data)
            return None

    async def async_get_device_sensor_error(self, device_id):
        """Get device error code status."""
        # Prepare return
        data = {}
#        session = await create_session()
        try:
            async with self._session.get(DEVICE_DATA_URL + str(device_id) + "/attribute?attributes=errorCodeSet1", headers=self._headers, cookies=self._cookies, timeout=self._timeout) as response:
                raw_res = await response.json()
                _LOGGER.debug("Received device error code status (%s): %s",str(device_id), raw_res)
        except aiohttp.ClientError as e:
            raise PyNeviweb130Error("Cannot get device error code status...") from e
            return None
        # Update cookies
        self._cookies.update(response.cookies)
        # Prepare data
        data = raw_res
        if "errorCodeSet1" in data:
            return data["errorCodeSet1"]
        else:
            _LOGGER.debug("Error code status data: %s", data)
            return None

    async def async_set_brightness(self, device_id, brightness):
        """Set device brightness."""
        data = {ATTR_INTENSITY: brightness}
        await self.async_set_device_attributes(device_id, data)

    async def async_set_onoff(self, device_id, onoff):
        """Set device onOff state."""
        data = {ATTR_ONOFF: onoff}
        await self.async_set_device_attributes(device_id, data)

    async def async_set_onoff2(self, device_id, onoff):
        """Set device onOff state."""
        data = {ATTR_ONOFF2: onoff}
        await self.async_set_device_attributes(device_id, data)

    async def async_set_light_onoff(self, device_id, onoff, brightness):
        """Set light device onOff state."""
        data = {ATTR_ONOFF: onoff, ATTR_INTENSITY: brightness}
        await self.async_set_device_attributes(device_id, data)

    async def async_set_valve_onoff(self, device_id, onoff):
        """Set sedna valve onOff state."""
        data = {ATTR_MOTOR_TARGET: onoff}
        await self.async_set_device_attributes(device_id, data)

    async def async_set_mode(self, device_id, mode):
        """Set device operation mode."""
        data = {ATTR_POWER_MODE: mode}
        await self.async_set_device_attributes(device_id, data)

    async def async_set_setpoint_mode(self, device_id, mode, wifi, HC):
        """Set thermostat operation mode."""
        """Work differently for wifi and zigbee devices."""
        if wifi:
            if HC:
                data = {ATTR_HEAT_COOL: mode}
            else:
                if mode in [HVACMode.HEAT, MODE_MANUAL]:
                    mode = MODE_MANUAL
                data = {ATTR_SETPOINT_MODE: mode}
        else:
            data = {ATTR_SYSTEM_MODE: mode}
        await self.async_set_device_attributes(device_id, data)

    async def async_set_occupancy_mode(self, device_id, mode, wifi):
        """Set thermostat preset mode."""
        """Work differently for wifi and zigbee devices."""
        if wifi:
            if mode in [PRESET_AWAY, PRESET_HOME]:
                data = {ATTR_OCCUPANCY: mode}
        else:
            data = {ATTR_SYSTEM_MODE: mode}
        await self.async_set_device_attributes(device_id, data)

    async def async_set_temperature(self, device_id, temperature):
        """Set device temperature."""
        data = {ATTR_ROOM_SETPOINT: temperature}
        await self.async_set_device_attributes(device_id, data)

    async def async_set_cool_temperature(self, device_id, temperature):
        """Set device cooling temperature target."""
        data = {ATTR_COOL_SETPOINT: temperature}
        await self.async_set_device_attributes(device_id, data)

    async def async_set_humidity(self, device_id, humidity):
        """Set device humidity target."""
        data = {ATTR_HUMID_SETPOINT: humidity}
        await self.async_set_device_attributes(device_id, data)

    async def async_set_humidifier_type(self, device_id, type):
        """Set humidifier type for TH6500WF and TH6250WF."""
        data = {ATTR_HUMIDIFIER_TYPE: type}
        await self.async_set_device_attributes(device_id, data)

    async def async_set_schedule_mode(self, device_id, mode, HC):
        """Set schedule mode for TH6500WF and TH6250WF."""
        if HC:
            data = {ATTR_SETPOINT_MODE: mode}
            await self.async_set_device_attributes(device_id, data)
        else:
            self.notify_ha(
                "Warning: Service set_schedule_mode is only for "
                + "TH6500WF or TH6250WF thermostats."
            )

    async def async_set_backlight(self, device_id, level, device):
        """Set backlight intensity when idle, on or auto."""
        """Work differently for wifi and zigbee devices."""
        if device == "wifi":
            data = {ATTR_BACKLIGHT_AUTO_DIM: level}
        else:
            data = {ATTR_BACKLIGHT: level}
        _LOGGER.debug("backlight.data = %s", data)
        await self.async_set_device_attributes(device_id, data)

    async def async_set_second_display(self, device_id, display):
        """Set device second display for outside temperature or setpoint temperature."""
        data = {ATTR_DISPLAY2: display}
        _LOGGER.debug("display.data = %s", data)
        await self.async_set_device_attributes(device_id, data)

    async def async_set_keypad_lock(self, device_id, lock, wifi):
        """Set device keyboard locked/unlocked."""
        if wifi:
            data = {ATTR_WIFI_KEYPAD: lock}
        else:
            data = {ATTR_KEYPAD: lock}
        _LOGGER.debug("lock.data = %s", data)
        await self.async_set_device_attributes(device_id, data)

    async def async_set_phase(self, device_id, phase):
        """Set device phase control mode."""
        data = {ATTR_PHASE_CONTROL: phase}
        _LOGGER.debug("phase.data = %s", data)
        await self.async_set_device_attributes(device_id, data)

    async def async_set_double_up(self, device_id, double):
        """Set device key double up action."""
        data = {ATTR_KEY_DOUBLE_UP: double}
        _LOGGER.debug("double_up.data = %s", data)
        await self.async_set_device_attributes(device_id, data)

    async def async_set_timer(self, device_id, time):
        """Set device auto off for timer on switch and multi controller."""
        data = {ATTR_TIMER: time}
        _LOGGER.debug("timer.data = %s", data)
        await self.async_set_device_attributes(device_id, data)

    async def async_set_timer2(self, device_id, time):
        """Set device auto off for timer2 on multi controller."""
        data = {ATTR_TIMER2: time}
        _LOGGER.debug("timer2.data = %s", data)
        await self.async_set_device_attributes(device_id, data)

    async def async_set_time_format(self, device_id, time):
        """Set device time format 12h or 24h."""
        data = {ATTR_TIME: time}
        _LOGGER.debug("time.data = %s", data)
        await self.async_set_device_attributes(device_id, data)

    async def async_set_temperature_format(self, device_id, deg):
        """Set device temperature format: celsius or fahrenheit."""
        data = {ATTR_TEMP: deg}
        _LOGGER.debug("temperature.data = %s", data)
        await self.async_set_device_attributes(device_id, data)

    async def async_set_floor_air_limit(self, device_id, status, temp):
        """Set device maximum air temperature limit."""
        if temp == 0:
            temp = None
        data = {ATTR_FLOOR_AIR_LIMIT:{"status":status,"value":temp}}
        _LOGGER.debug("floorairlimit.data = %s", data)
        await self.async_set_device_attributes(device_id, data)

    async def async_set_early_start(self, device_id, start):
        """Set early start on/off for wifi thermostats."""
        data = {ATTR_EARLY_START: start}
        _LOGGER.debug("early_start.data = %s", data)
        await self.async_set_device_attributes(device_id, data)

    async def async_set_air_floor_mode(self, device_id, mode):
        """Switch temperature control between floor and ambiant sensor."""
        data = {ATTR_FLOOR_MODE: mode}
        _LOGGER.debug("floor_mode.data = %s", data)
        await self.async_set_device_attributes(device_id, data)

    async def async_set_setpoint_min(self, device_id, temp):
        """Set device setpoint minimum temperature."""
        data = {ATTR_ROOM_SETPOINT_MIN: temp}
        _LOGGER.debug("setpointMin.data = %s", data)
        await self.async_set_device_attributes(device_id, data)

    async def async_set_setpoint_max(self, device_id, temp):
        """Set device setpoint maximum temperature."""
        data = {ATTR_ROOM_SETPOINT_MAX: temp}
        _LOGGER.debug("setpointMax.data = %s", data)
        await self.async_set_device_attributes(device_id, data)

    async def async_set_cool_setpoint_min(self, device_id, temp):
        """Set device cooling setpoint minimum temperature."""
        data = {ATTR_COOL_SETPOINT_MIN: temp}
        _LOGGER.debug("CoolsetpointMin.data = %s", data)
        await self.async_set_device_attributes(device_id, data)

    async def async_set_cool_setpoint_max(self, device_id, temp):
        """Set device cooling setpoint maximum temperature."""
        data = {ATTR_COOL_SETPOINT_MAX: temp}
        _LOGGER.debug("CoolsetpointMax.data = %s", data)
        await self.async_set_device_attributes(device_id, data)

    async def async_set_aux_cycle_output(self, device_id, status, val, wifi):
        """Set low voltage thermostat aux cycle status and length."""
        if wifi:
            data = {ATTR_AUX_CYCLE: val}
        else:
            data = {ATTR_CYCLE_OUTPUT2: {"status": status, "value": val}}
        _LOGGER.debug("auxCycleoutput.data = %s", data)
        await self.async_set_device_attributes(device_id, data)

    async def async_set_cycle_output(self, device_id, val):
        """Set low voltage thermostat main cycle length."""
        data = {ATTR_CYCLE:val}
        _LOGGER.debug("Cycleoutput.data = %s", data)
        await self.async_set_device_attributes(device_id, data)

    async def async_set_tank_size(self, device_id, val):
        """Set water heater tank size for RM3500ZB."""
        data = {ATTR_TANK_SIZE:val}
        _LOGGER.debug("TankSize.data = %s", data)
        await self.async_set_device_attributes(device_id, data)

    async def async_set_remaining_time(self, device_id, time):
        """Activate or deactivate calypso for time period."""
        data = {ATTR_COLD_LOAD_PICKUP_REMAIN_TIME:time}
        _LOGGER.debug("RemainingTime.data = %s", data)
        await self.async_set_device_attributes(device_id, data)

    async def async_set_sensor_type(self, device_id, val):
        """Set floor sensor type 10k, 12k."""
        data = {
            ATTR_FLOOR_SENSOR:val,
            ATTR_FLOOR_OUTPUT2:{ "status": "off", "value": 0},
        }
        _LOGGER.debug("sensor.data = %s", data)
        await self.async_set_device_attributes(device_id, data)

    async def async_set_low_temp_protection(self, device_id, val):
        """Set water heater temperature protection for RM3500ZB."""
        data = {ATTR_WATER_TEMP_MIN:val}
        _LOGGER.debug("Low temp protection.data = %s", data)
        await self.async_set_device_attributes(device_id, data)

    async def async_set_controlled_device(self, device_id, val):
        """Set device name controlled by RM3250ZB."""
        data = {ATTR_CONTROLLED_DEVICE:val}
        _LOGGER.debug("ControlledDevice.data = %s", data)
        await self.async_set_device_attributes(device_id, data)

    async def async_set_em_heat(self, device_id, heat, low, sec):
        """Set floor, low voltage, wifi floor and low voltage wifi thermostats auxiliary heat slave/off or on/off."""
        if low == "voltage":
            data = {ATTR_CYCLE_OUTPUT2:{"status":heat,"value":sec}}
        elif low == "wifi":
            data = {ATTR_AUX_CYCLE: sec}
        else:
            data = {ATTR_FLOOR_AUX: heat}
        _LOGGER.debug("em_heat.data = %s", data)
        await self.async_set_device_attributes(device_id, data)

    async def async_set_floor_limit(self, device_id, level, low, wifi):
        """Set floor setpoint limit low and high for zigbee and wifi thermostats. (0 = off)."""
        if level == 0:
            if wifi:
                if low == "low":
                    data = {ATTR_FLOOR_MIN:{"value": None, "status": "off"}}
                else:
                    data = {ATTR_FLOOR_MAX:{"value": None, "status": "off"}}
            else:
                if low == "low":
                    data = {
                        ATTR_FLOOR_MIN:{"status": "off", "value": None},
                        ATTR_FLOOR_OUTPUT2:{ "status": "off", "value": 0},
                    }
                else:
                    data = {
                        ATTR_FLOOR_MAX:{"status": "off", "value": None},
                        ATTR_FLOOR_OUTPUT2:{ "status": "off", "value": 0},
                    }
        else:
            if wifi:
                if low == "low":
                    data = {ATTR_FLOOR_MIN:{"value": level, "status": "on"}}
                else:
                    data = {ATTR_FLOOR_MAX:{"value": level, "status": "on"}}
            else:
                if low == "low":
                    data = {
                        ATTR_FLOOR_MIN:{"status": "on", "value": level},
                        ATTR_FLOOR_OUTPUT2:{ "status": "off", "value": 0},
                    }
                else:
                    data = {
                        ATTR_FLOOR_MAX:{"status": "on", "value": level},
                        ATTR_FLOOR_OUTPUT2:{ "status": "off", "value": 0},
                    }
        _LOGGER.debug("Floor limit = %s", data)
        await self.async_set_device_attributes(device_id, data)

    async def async_set_pump_protection(self, device_id, status, wifi):
        """Set low voltage thermostat pump protection status."""
        """Work differently for wifi and zigbee devices."""
        if wifi:
            data = {ATTR_PUMP_PROTEC: status}
        else:
            if status == "on":
                data = {
                    ATTR_PUMP_PROTEC_DURATION:{"status": "on", "value": 60},
                    ATTR_PUMP_PROTEC_PERIOD:{"status": "on", "value": 1},
                }
            else:
                data = {
                    ATTR_PUMP_PROTEC_DURATION:{"status": "off"},
                    ATTR_PUMP_PROTEC_PERIOD:{"status": "off"},
                }
        _LOGGER.debug("pump.data = %s", data)
        await self.async_set_device_attributes(device_id, data)

    async def async_set_flow_meter_model(self, device_id, model):
        """Set flow meter model connected to the Sedna valve 2e gen."""
        if model == "FS4221":
            data = {
                ATTR_FLOW_METER_CONFIG: {
                    "multiplier":9887,
                    "offset":87372,
                    "divisor":1,
                },
                ATTR_FLOW_ENABLED: True,
            }
        elif model == "FS4220":
            data = {
                ATTR_FLOW_METER_CONFIG: {
                    "multiplier":4546,
                    "offset":30600,
                    "divisor":1,
                },
                ATTR_FLOW_ENABLED: True,
            }
        else:
            data = {
                ATTR_FLOW_METER_CONFIG: {
                    "multiplier":0,
                    "offset":0,
                    "divisor":1,
                },
                ATTR_FLOW_ENABLED: False,
            }
        _LOGGER.debug("Flowmeter model.data = %s", data)
        await self.async_set_device_attributes(device_id, data)

    async def async_set_flow_meter_delay(self, device_id, delay):
        """Set flow meter delay before alarm is activated on Sedna valve 2e gen."""
        data = {ATTR_FLOW_ALARM1_PERIOD:delay}
        _LOGGER.debug("Flowmeter delay.data = %s", data)
        await self.async_set_device_attributes(device_id, data)

    async def async_set_flow_meter_options(self, device_id, alarm, action, lenght, threshold):
        """Set flow meter options when leak alarm is activated on Sedna valve 2e gen."""
        data = {
            ATTR_FLOW_ALARM1_OPTION: {
                "triggerAlarm":alarm,
                "closeValve":action,
            },
            ATTR_FLOW_ALARM1_LENGHT:lenght,
            ATTR_FLOW_THRESHOLD:threshold,
        }
        _LOGGER.debug("Flowmeter options.data = %s", data)
        await self.async_set_device_attributes(device_id, data)

    async def async_set_led_indicator(self, device_id, state, red, green, blue):
        """Set devive led indicator color for on and off state."""
        if state == 1:
            data = {
                ATTR_LED_ON_COLOR: {
                    "red":red,
                    "green":green,
                    "blue":blue,
                }
            }
            _LOGGER.debug("led on color.data = %s", data)
        else:
            data = {
                ATTR_LED_OFF_COLOR: {
                    "red":red,
                    "green":green,
                    "blue":blue,
                }
            }
            _LOGGER.debug("led off color.data = %s", data)
        await self.async_set_device_attributes(device_id, data)

    async def async_set_led_on_intensity(self, device_id, intensity):
        """Set devive led indicator intensity for on state."""
        data = {ATTR_LED_ON_INTENSITY:intensity}
        await self.async_set_device_attributes(device_id, data)
        _LOGGER.debug("led on intensity.data on = %s", data)

    async def async_set_led_off_intensity(self, device_id, intensity):
        """Set devive led indicator intensity for off state."""
        data = {ATTR_LED_OFF_INTENSITY:intensity}
        await self.async_set_device_attributes(device_id, data)
        _LOGGER.debug("led off intensity.data on = %s", data)

    async def async_set_light_min_intensity(self, device_id, intensity):
        """Set dimmer light minimum intensity from 1 to 3000."""
        data = {ATTR_INTENSITY_MIN:intensity}
        await self.async_set_device_attributes(device_id, data)
        _LOGGER.debug("led min intensity.data on = %s", data)

    async def async_set_wattage(self, device_id, watt):
        """Set light and dimmer watt load."""
        data = {ATTR_LIGHT_WATTAGE:{"status":"on","value":watt}}
        _LOGGER.debug("wattage.data = %s", data)
        await self.async_set_device_attributes(device_id, data)

    async def async_set_auxiliary_load(self, device_id, status, load):
        """Set auxiliary output load in watt."""
        data = {ATTR_FLOOR_OUTPUT2:{"status":status,"value":load}}
        _LOGGER.debug("auxiliary_load.data = %s", data)
        await self.async_set_device_attributes(device_id, data)

    async def async_set_valve_alert(self, device_id, batt):
        """Set Sedna valve battery alert on/off."""
        data = {ATTR_BATT_ALERT: batt}
        _LOGGER.debug("valve.data = %s", data)
        await self.async_set_device_attributes(device_id, data)

    async def async_set_valve_temp_alert(self, device_id, temp):
        """Set Sedna valve temperature alert on/off."""
        data = {ATTR_TEMP_ALERT: temp}
        _LOGGER.debug("valve.data = %s", data)
        await self.async_set_device_attributes(device_id, data)

    async def async_set_battery_type(self, device_id, batt):
        """Set water leak sensor battery type, lithium or alkaline."""
        data = {ATTR_BATTERY_TYPE: batt}
        _LOGGER.debug("battery_type.data = %s", data)
        await self.async_set_device_attributes(device_id, data)

    async def async_set_sensor_alert(self, device_id, leak, batt, temp, close):
        """Set leak detector alert, battery, temperature, leak, Sedna valve closing."""
        data = {
            ATTR_LEAK_ALERT: leak,
            ATTR_BATT_ALERT: batt,
            ATTR_TEMP_ALERT: temp,
            ATTR_CONF_CLOSURE: close,
        }
        _LOGGER.debug("leak.data = %s", data)
        await self.async_set_device_attributes(device_id, data)

    async def async_set_load_dr_options(self, device_id, onoff, optout, dr):
        """Set load controler Eco Sinope attributes."""
        data = {
            ATTR_DRSTATUS: {
                "drActive":dr,
                "optOut":optout,
                "onOff":onoff,
            }
        }
        _LOGGER.debug("Load.DR.options = %s", data)
        await self.async_set_device_attributes(device_id, data)

    async def async_set_hvac_dr_options(self, device_id, dr, optout, setpoint):
        """Set load controler Eco Sinope attributes."""
        data = {
            ATTR_DRSTATUS: {
                "drActive":dr,
                "optOut":optout,
                "setpoint":setpoint,
            }
        }
        _LOGGER.debug("hvac.DR.options = %s", data)
        await self.async_set_device_attributes(device_id, data)

    async def async_set_hvac_dr_setpoint(self, device_id, status, val):
        """Set load controler Eco Sinope attributes."""
        data = {ATTR_DRSETPOINT:{"status":status,"value":val}}
        _LOGGER.debug("hvac.DR.setpoint = %s", data)
        await self.async_set_device_attributes(device_id, data)

    async def async_set_control_onoff(self, device_id, number, status):
        """Set valve controller onOff or OnOff2 status, on or off."""
        if number == 1:
            data = {ATTR_ONOFF: status}
        else:
            data = {ATTR_ONOFF2: status}
        _LOGGER.debug("control.valve.data = %s", data)
        await self.async_set_device_attributes(device_id, data)

    async def async_set_tank_type(self, device_id, tank):
        """Set tank type for LM4110-ZB sensor."""
        data = {ATTR_TANK_TYPE: tank}
        _LOGGER.debug("tank_type.data = %s", data)
        await self.async_set_device_attributes(device_id, data)

    async def async_set_gauge_type(self, device_id, gauge):
        """Set gauge type for LM4110-ZB sensor on propane tank."""
        data = {ATTR_GAUGE_TYPE: gauge}
        _LOGGER.debug("gauge_type.data = %s", data)
        await self.async_set_device_attributes(device_id, data)

    async def async_set_low_fuel_alert(self, device_id, alert):
        """Set low fuel alert limit for LM4110-ZB sensor."""
        data = {ATTR_FUEL_PERCENT_ALERT: alert}
        _LOGGER.debug("low_fuel_alert.data = %s", data)
        await self.async_set_device_attributes(device_id, data)

    async def async_set_refuel_alert(self, device_id, alert):
        """Set refuel alert for LM4110-ZB sensor."""
        data = {ATTR_REFUEL: alert}
        _LOGGER.debug("Refuel_alert.data = %s", data)
        await self.async_set_device_attributes(device_id, data)

    async def async_set_tank_height(self, device_id, height):
        """Set low fuel alert limit for LM4110-ZB sensor."""
        data = {ATTR_TANK_HEIGHT: height}
        _LOGGER.debug("tank_height.data = %s", data)
        await self.async_set_device_attributes(device_id, data)

    async def async_set_fuel_alert(self, device_id, fuel):
        """Set low fuel alert limit for LM4110-ZB sensor."""
        data = {ATTR_FUEL_ALERT: fuel}
        _LOGGER.debug("Fuel_alert.data = %s", data)
        await self.async_set_device_attributes(device_id, data)

    async def async_set_battery_alert(self, device_id, batt):
        """Set low fuel alert limit for LM4110-ZB sensor."""
        data = {ATTR_BATT_ALERT: batt}
        _LOGGER.debug("battery_alert.data = %s", data)
        await self.async_set_device_attributes(device_id, data)

    async def async_set_power_supply(self, device_id, supply):
        """Set power supply for Sedna valve."""
        data = {ATTR_POWER_SUPPLY: supply}
        _LOGGER.debug("power_supply.data = %s", data)
        await self.async_set_device_attributes(device_id, data)

    async def async_set_on_off_input_delay(self, device_id, delay, onoff, inputnumber):
        """Set input 1 or 2 on/off delay in seconds."""
        if inputnumber == 1:
            match onoff:
                case "on":
                    data = {ATTR_INPUT_1_ON_DELAY: delay}
                case _:
                    data = {ATTR_INPUT_1_OFF_DELAY: delay}
        else:
            match onoff:
                case "on":
                    data = {ATTR_INPUT_2_ON_DELAY: delay}
                case _:
                    data = {ATTR_INPUT_2_OFF_DELAY: delay}
        _LOGGER.debug("input_delay.data = %s", data)
        await self.async_set_device_attributes(device_id, data)

    async def async_set_input_output_names(self, device_id, in1, in2, out1, out2):
        """Set names for input 1 and 2, output 1 and 2 for MC3100ZB device."""
        data = {}
        if len(in1) > 0:
            data.update({ATTR_NAME_1: in1})
        else:
            data.update({ATTR_NAME_1: ""})
        if len(in2) > 0:
            data.update({ATTR_NAME_2: in2})
        else:
            data.update({ATTR_NAME_2: ""})
        if len(out1) > 0:
            data.update({ATTR_OUTPUT_NAME_1: out1})
        else:
            data.update({ATTR_OUTPUT_NAME_1: ""})
        if len(out2) > 0:
            data.update({ATTR_OUTPUT_NAME_2: out2})
        else:
            data.update({ATTR_OUTPUT_NAME_2: ""})
        _LOGGER.debug("in/out names.data = %s", data)
        await self.async_set_device_attributes(device_id, data)

    async def async_set_heat_pump_limit(self, device_id, temp):
        """Set minimum temperature for heat pump operation."""
        data = {ATTR_BALANCE_PT: temp}
        _LOGGER.debug("Heat pump limit value.data = %s", data)
        await self.async_set_device_attributes(device_id, data)

    async def async_set_heat_lockout(self, device_id, temp):
        """Set maximum outside temperature limit to allow heating device operation."""
        data = {ATTR_HEAT_LOCK_TEMP: temp}
        _LOGGER.debug("Heat lockout limit value.data = %s", data)
        await self.async_set_device_attributes(device_id, data)

    async def async_set_cool_lockout(self, device_id, temp):
        """Set minimum outside temperature limit to allow cooling devices operation."""
        data = {ATTR_COOL_LOCK_TEMP: temp}
        _LOGGER.debug("Cool lockout limit value.data = %s", data)
        await self.async_set_device_attributes(device_id, data)

    async def async_set_hp_display(self, device_id, display):
        """Set display on/off for heat pump."""
        data = {ATTR_DISPLAY_CONF: display}
        _LOGGER.debug("Display config value.data = %s", data)
        await self.async_set_device_attributes(device_id, data)

    async def async_set_hp_sound(self, device_id, sound):
        """Set display on/off for heat pump."""
        data = {ATTR_SOUND_CONF: sound}
        _LOGGER.debug("Sound config value.data = %s", data)
        await self.async_set_device_attributes(device_id, data)

    async def async_set_swing_horizontal(self, device_id, swing):
        """Set horizontal fan swing action for heat pump."""
        data = {ATTR_FAN_SWING_HORIZ: swing}
        _LOGGER.debug("Fan horizontal swing value.data = %s", data)
        await self.async_set_device_attributes(device_id, data)

    async def async_set_swing_vertical(self, device_id, swing):
        """Set vertical fan swing action for heat pump."""
        data = {ATTR_FAN_SWING_VERT: swing}
        _LOGGER.debug("Fan vertical swing value.data = %s", data)
        await self.async_set_device_attributes(device_id, data)

    async def async_set_fan_mode(self, device_id, speed):
        """Set fan speed (mode) for heat pump."""
        data = {ATTR_FAN_SPEED: speed}
        _LOGGER.debug("Fan speed value.data = %s", data)
        await self.async_set_device_attributes(device_id, data)

    async def async_set_hc_display(self, device_id, display):
        """Set device second display for outside temperature or setpoint temperature for TH1134ZB-HC."""
        data = {ATTR_DISPLAY2: display}
        _LOGGER.debug("Hc display.data = %s", data)
        await self.async_set_device_attributes(device_id, data)

    async def async_set_language(self, device_id, lang):
        """Set display language for TH1134ZB-HC."""
        data = {ATTR_LANGUAGE: lang}
        _LOGGER.debug("Hc language.data = %s", data)
        await self.async_set_device_attributes(device_id, data)

    async def async_set_aux_heat_time_on(self, device_id, time):
        """Set display language for TH1134ZB-HC."""
        data = {ATTR_AUX_HEAT_TIMEON: time}
        _LOGGER.debug("HC aux_heat_time_on.data = %s", data)
        await self.async_set_device_attributes(device_id, data)

    async def async_set_cool_time(self, device_id, time, state):
        """Set display language for TH1134ZB-HC."""
        if state == "on":
            data = {ATTR_COOL_MIN_TIME_ON: time}
        else:
            data = {ATTR_COOL_MIN_TIME_OFF: time}
        _LOGGER.debug("HC cool_min_time_on/off.data = %s", data)
        await self.async_set_device_attributes(device_id, data)

    async def async_set_device_attributes(self, device_id, data):
        """Ser devices attributes."""
        result = 1
        while result < 3:
#            session = await create_session()
            try:
                async with self._session.put(DEVICE_DATA_URL + str(device_id) + "/attribute", json=data, headers=self._headers, cookies=self._cookies, timeout=self._timeout) as response:
                    resp = await response.json()
                    _LOGGER.debug (
                        "http_request = %s%s%s %s",
                        DEVICE_DATA_URL,
                        str(device_id),
                        "/attribute",
                        data,
                    )
                    _LOGGER.debug("Data = %s", data)
                    _LOGGER.debug("Request response = %s", response.status)
                    _LOGGER.debug("Json Data received= %s", resp)
            except aiohttp.ClientError as e:
                raise PyNeviweb130Error("Cannot set device %s attributes: %s", device_id, data) from e
            finally:
                if "error" in resp:
                    result += 1
                    _LOGGER.debug(
                        "Service error received: %s, resending request %s",
                        resp,
                        result,
                    )
                    continue
                else:
                    break

    async def async_post_neviweb_status(self, device_id, location, mode):
        """Send post requests to Neviweb for global occupancy mode"""
        data = {ATTR_MODE: mode}
        try:
            async with self._session.post(NEVIWEB_LOCATION + location + "/mode", json=data, headers=self._headers, cookies=self._cookies, timeout=self._timeout)  as response:
                resp = await response.json()
                _LOGGER.debug("Data = %s", data)
                _LOGGER.debug("Requests response = %s", response.status)
                _LOGGER.debug("Json Data received= %s", resp)
        except aiohttp.ClientError as e:
            raise PyNeviweb130Error("Cannot post Neviweb: %s", data) from e
        if "error" in resp:
            _LOGGER.debug("Service error received: %s",resp)

create_session = Neviweb130Client.create_session

class Neviweb130Coordinator(DataUpdateCoordinator):
    def __init__(self, hass: HomeAssistant, client: Neviweb130Client, scan_interval):
        """Initialize the Neviweb130Coordinator.timedelta(seconds=360)"""

        _LOGGER.debug("Coordinator scan interval = %s", scan_interval)
        super().__init__(
            hass,
            _LOGGER,
            name="neviweb130",
            update_method = self.async_update_data,
            update_interval = scan_interval,
        )
        self.client = client
        self._devices: list = []  # liste des device objects

    async def _async_update_data(self) -> dict:
        """Call async_update() on each device and return a dict {id: device}."""
        result = {}
        for dev in self._devices:
            _LOGGER.debug("Thermostat attrs: %s", dir(dev))
            _LOGGER.debug("Thermostat __dict__: %s", vars(dev))
            try:
                await dev.async_update()
                # fetch .id, or .unique_id
                device_id = getattr(dev, "id", None) or getattr(dev, "unique_id", None)
                if not device_id:
                    _LOGGER.error("No ID found for %s", dev)
                    continue

                #result[str(dev.id)] = dev
                result[str(device_id)] = dev
            except Exception as err:
                raise UpdateFailed(f"Eooro on update of device {dev.id}: {err}")
        _LOGGER.debug("Coordinator data after update : %s", list(result.keys()))
        return result

    def register_device(self, device):
        """Register a device to be managed by the coordinator."""
#        self.devices.append(device)
        if device not in self._devices:
            self._devices.append(device)

#    async def async_update_data(self):
#        """Fetch data from Neviweb130 devices."""
#        for device in self.devices.values():
#            await device.async_update()

    async def async_initialize(self):
        """Initialize the coordinator."""
        await self.client.async_initialize()
        await self.async_refresh()

    async def stop(self):
        _LOGGER.info("Stopping Neviweb130 Coordinator")
        await session.close()
        _LOGGER.info("All aiohttp.ClientSession instances closed")

async def async_setup_coordinator(hass: HomeAssistant, client: Neviweb130Client, scan_interval):
    coordinator = Neviweb130Coordinator(hass, client, scan_interval)
    await coordinator.async_initialize()
    return coordinator
