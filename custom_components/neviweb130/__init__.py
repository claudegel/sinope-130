"""Sinopé GT130 Zigbee and Wi-Fi support."""

from __future__ import annotations

import asyncio
import json
import logging
import os
from typing import Any

import aiohttp
import requests
from homeassistant.components.climate.const import PRESET_AWAY, PRESET_HOME, HVACMode
from homeassistant.components.persistent_notification import DOMAIN as PN_DOMAIN
from homeassistant.const import CONF_PASSWORD, CONF_SCAN_INTERVAL, CONF_USERNAME, Platform
from homeassistant.core import HomeAssistant, callback
from homeassistant.exceptions import ConfigEntryAuthFailed, ConfigEntryError, ConfigEntryNotReady, IntegrationError
from homeassistant.helpers import discovery, entity_registry
from requests.cookies import RequestsCookieJar

from .const import (
    ATTR_ACCESSORY_TYPE,
    ATTR_AIR_EX_MIN_TIME_ON,
    ATTR_AUX_CYCLE_LENGTH,
    ATTR_AUX_HEAT_MIN_TIME_OFF,
    ATTR_AUX_HEAT_MIN_TIME_ON,
    ATTR_AUX_HEAT_SOURCE_TYPE,
    ATTR_AUX_HEAT_START_DELAY,
    ATTR_AUX_INTERSTAGE_DELAY,
    ATTR_AUX_INTERSTAGE_MIN_DELAY,
    ATTR_BACKLIGHT,
    ATTR_BACKLIGHT_AUTO_DIM,
    ATTR_BALANCE_PT,
    ATTR_BATT_ALERT,
    ATTR_BATTERY_TYPE,
    ATTR_COLD_LOAD_PICKUP_REMAIN_TIME,
    ATTR_CONF_CLOSURE,
    ATTR_CONTROLLED_DEVICE,
    ATTR_COOL_CYCLE_LENGTH,
    ATTR_COOL_INTERSTAGE_DELAY,
    ATTR_COOL_INTERSTAGE_MIN_DELAY,
    ATTR_COOL_LOCK_TEMP,
    ATTR_COOL_MIN_TIME_OFF,
    ATTR_COOL_MIN_TIME_ON,
    ATTR_COOL_PURGE_TIME,
    ATTR_COOL_SETPOINT,
    ATTR_COOL_SETPOINT_AWAY,
    ATTR_COOL_SETPOINT_MAX,
    ATTR_COOL_SETPOINT_MIN,
    ATTR_CYCLE_LENGTH,
    ATTR_CYCLE_OUTPUT2,
    ATTR_DISPLAY2,
    ATTR_DISPLAY_CONF,
    ATTR_DR_AUX_CONF,
    ATTR_DR_FAN_SPEED_CONF,
    ATTR_DRSETPOINT,
    ATTR_DRSTATUS,
    ATTR_EARLY_START,
    ATTR_FAN_FILTER_REMAIN,
    ATTR_FAN_SPEED,
    ATTR_FAN_SWING_HORIZ,
    ATTR_FAN_SWING_VERT,
    ATTR_FLOOR_AIR_LIMIT,
    ATTR_FLOOR_AUX,
    ATTR_FLOOR_MAX,
    ATTR_FLOOR_MIN,
    ATTR_FLOOR_MODE,
    ATTR_FLOOR_OUTPUT2,
    ATTR_FLOOR_SENSOR,
    ATTR_FLOW_ALARM1_LENGTH,
    ATTR_FLOW_ALARM1_OPTION,
    ATTR_FLOW_ALARM1_PERIOD,
    ATTR_FLOW_ALARM_TIMER,
    ATTR_FLOW_ENABLED,
    ATTR_FLOW_METER_CONFIG,
    ATTR_FLOW_THRESHOLD,
    ATTR_FUEL_ALERT,
    ATTR_FUEL_PERCENT_ALERT,
    ATTR_GAUGE_TYPE,
    ATTR_HEAT_COOL,
    ATTR_HEAT_INSTALLATION_TYPE,
    ATTR_HEAT_INTERSTAGE_DELAY,
    ATTR_HEAT_INTERSTAGE_MIN_DELAY,
    ATTR_HEAT_LOCK_TEMP,
    ATTR_HEAT_LOCKOUT_TEMP,
    ATTR_HEAT_MIN_TIME_OFF,
    ATTR_HEAT_MIN_TIME_ON,
    ATTR_HEAT_PURGE_TIME,
    ATTR_HEATCOOL_SETPOINT_MIN_DELTA,
    ATTR_HUMIDITY_SETPOINT,
    ATTR_HUMIDITY_SETPOINT_MODE,
    ATTR_HUMIDITY_SETPOINT_OFFSET,
    ATTR_INPUT_1_OFF_DELAY,
    ATTR_INPUT_1_ON_DELAY,
    ATTR_INPUT_2_OFF_DELAY,
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
    ATTR_REVERSING_VALVE_POLARITY,
    ATTR_ROOM_SETPOINT,
    ATTR_ROOM_SETPOINT_AWAY,
    ATTR_ROOM_SETPOINT_MAX,
    ATTR_ROOM_SETPOINT_MIN,
    ATTR_SETPOINT_MODE,
    ATTR_SIGNATURE,
    ATTR_SOUND_CONF,
    ATTR_SYSTEM_MODE,
    ATTR_TANK_HEIGHT,
    ATTR_TANK_SIZE,
    ATTR_TANK_TYPE,
    ATTR_TEMP,
    ATTR_TEMP_ALERT,
    ATTR_TEMP_OFFSET_HEAT,
    ATTR_TIME_FORMAT,
    ATTR_TIMER,
    ATTR_TIMER2,
    ATTR_WATER_TEMP_MIN,
    ATTR_WIFI_KEYPAD,
    CONF_HOMEKIT_MODE,
    CONF_IGNORE_MIWI,
    CONF_NETWORK,
    CONF_NETWORK2,
    CONF_NETWORK3,
    CONF_NOTIFY,
    CONF_STAT_INTERVAL,
    DOMAIN,
    MODE_MANUAL,
    STARTUP_MESSAGE,
    VERSION,
)
from .helpers import fetch_release_notes, increment_request_counter, init_request_counter, setup_logger
from .schema import CONFIG_SCHEMA as CONFIG_SCHEMA  # noqa: F401
from .schema import HOMEKIT_MODE as DEFAULT_HOMEKIT_MODE
from .schema import IGNORE_MIWI as DEFAULT_IGNORE_MIWI
from .schema import NEVIWEB_MODE_MAP
from .schema import NOTIFY as DEFAULT_NOTIFY
from .schema import SCAN_INTERVAL as DEFAULT_SCAN_INTERVAL
from .schema import STAT_INTERVAL as DEFAULT_STAT_INTERVAL

REQUESTS_TIMEOUT = 30
HOST = "https://neviweb.com"
LOGIN_URL = f"{HOST}/api/login"
LOCATIONS_URL = f"{HOST}/api/locations?account$id="
GATEWAY_DEVICE_URL = f"{HOST}/api/devices?location$id="
DEVICE_DATA_URL = f"{HOST}/api/device/"
NEVIWEB_LOCATION = f"{HOST}/api/location/"
NEVIWEB_WEATHER = f"{HOST}/api/weather?code="

SCAN_INTERVAL = DEFAULT_SCAN_INTERVAL
HOMEKIT_MODE = DEFAULT_HOMEKIT_MODE
IGNORE_MIWI = DEFAULT_IGNORE_MIWI
STAT_INTERVAL = DEFAULT_STAT_INTERVAL
NOTIFY = DEFAULT_NOTIFY

DEFAULT_LOG_MAX_BYTES = 2 * 1024 * 1024
DEFAULT_LOG_BACKUP_COUNT = 3
DEFAULT_LOG_RESET_ON_START = True
LOGGER_NAME = "custom_components.neviweb130"

LOG_PATH = os.path.abspath(os.path.join(os.path.dirname(__file__), "../../neviweb130_log.txt"))

existing_logger = logging.getLogger(LOGGER_NAME)
level_name = logging.getLevelName(existing_logger.level)

setup_logger(
    name=LOGGER_NAME,
    log_path=LOG_PATH,
    level=level_name,
    max_bytes=DEFAULT_LOG_MAX_BYTES,
    backup_count=DEFAULT_LOG_BACKUP_COUNT,
    reset_on_start=DEFAULT_LOG_RESET_ON_START,
)

_LOGGER = logging.getLogger(__name__)


@callback
def migrate_entity_unique_id(hass: HomeAssistant):
    registry = entity_registry.async_get(hass)
    for entity in list(registry.entities.values()):
        if entity.platform == DOMAIN and isinstance(entity.unique_id, int):
            registry.async_update_entity(entity.entity_id, new_unique_id=str(entity.unique_id))
            _LOGGER.debug(f"Migrated unique_id from int to str for {entity.entity_id}")

    # All platforms will wait for this asynchronously, before loading anything.
    hass.data[DOMAIN]["data"].migration_done.set()


def setup(hass: HomeAssistant, hass_config: dict[str, Any]) -> bool:
    """Set up neviweb130."""
    _LOGGER.warning(STARTUP_MESSAGE)

    hass.data.setdefault(DOMAIN, {})

    # Initialise request counter
    init_request_counter(hass)

    try:
        data = Neviweb130Data(hass, hass_config[DOMAIN])
        hass.data[DOMAIN]["data"] = data
    except IntegrationError as e:
        # Temporary workaround for sync setup: Avoid verbose traceback in logs. Once async_setup_entry is used,
        # we can remove the try-except as HomeAssistant will correctly handle the raised exception
        _LOGGER.error("Neviweb initialization failed: %s", e)
        return False

    # Migrate entity unique_ids from int -> str.
    hass.add_job(migrate_entity_unique_id, hass)

    global SCAN_INTERVAL
    SCAN_INTERVAL = hass_config[DOMAIN].get(CONF_SCAN_INTERVAL, DEFAULT_SCAN_INTERVAL)
    _LOGGER.debug("Setting scan interval to: %s", SCAN_INTERVAL)

    global HOMEKIT_MODE
    HOMEKIT_MODE = hass_config[DOMAIN].get(CONF_HOMEKIT_MODE, DEFAULT_HOMEKIT_MODE)
    _LOGGER.debug("Setting Homekit mode to: %s", HOMEKIT_MODE)

    global IGNORE_MIWI
    IGNORE_MIWI = hass_config[DOMAIN].get(CONF_IGNORE_MIWI, DEFAULT_IGNORE_MIWI)
    _LOGGER.debug("Setting ignore miwi to: %s", IGNORE_MIWI)

    global STAT_INTERVAL
    STAT_INTERVAL = hass_config[DOMAIN].get(CONF_STAT_INTERVAL, DEFAULT_STAT_INTERVAL)
    _LOGGER.debug("Setting stat interval to: %s", STAT_INTERVAL)

    global NOTIFY
    NOTIFY = hass_config[DOMAIN].get(CONF_NOTIFY, DEFAULT_NOTIFY)
    _LOGGER.debug("Setting notification method to: %s", NOTIFY)

    async def fetch_latest_version():
        url = "https://api.github.com/repos/claudegel/sinope-130/tags"

        async with aiohttp.ClientSession() as session:
            async with session.get(url) as resp:
                if resp.status == 200:
                    text = await resp.text()
                    try:
                        tags = json.loads(text)
                        if isinstance(tags, list) and len(tags) > 0:
                            latest_tag = tags[0].get("name")
                            if latest_tag and latest_tag.startswith("v"):
                                latest_tag = latest_tag[1:]
                            return latest_tag
                    except Exception as err:
                        _LOGGER.error("Failed to parse GitHub tags: %s", err)
                        return None

        return None

    async def async_reload_integration(call):
        """Reload Neviweb130 integration (V1)."""
        _LOGGER.warning("Reloading Neviweb130 integration via service call")

       # List platforms
        platforms = [
            Platform.CLIMATE,
            Platform.LIGHT,
            Platform.SWITCH,
            Platform.SENSOR,
            Platform.VALVE,
            Platform.UPDATE,
        ]

        # Reload each plateform
        for platform in platforms:
            try:
                await hass.helpers.entity_platform.async_reload(platform, DOMAIN)
                _LOGGER.debug("Reloaded platform: %s", platform)
            except Exception as err:
                _LOGGER.error("Failed to reload platform %s: %s", platform, err)

        _LOGGER.warning("Neviweb130 integration reloaded successfully")

    hass.services.register(DOMAIN, "reload", async_reload_integration)

    async def async_init_update():
        latest = await fetch_latest_version()
        if latest is None:
            _LOGGER.warning("Could not fetch latest version from GitHub")
            return

        hass.data[DOMAIN]["data"].available_version = latest
        result = await fetch_release_notes(latest)
        if result is None:
            title = "No title available."
            notes = "No release notes available."
        else:
            title, notes = result

        hass.data[DOMAIN]["data"].release_title = title
        hass.data[DOMAIN]["data"].release_notes = notes

    hass.loop.call_soon_threadsafe(hass.async_create_task, async_init_update())

    discovery.load_platform(hass, Platform.CLIMATE, DOMAIN, {}, hass_config)
    discovery.load_platform(hass, Platform.LIGHT, DOMAIN, {}, hass_config)
    discovery.load_platform(hass, Platform.SWITCH, DOMAIN, {}, hass_config)
    discovery.load_platform(hass, Platform.SENSOR, DOMAIN, {}, hass_config)
    discovery.load_platform(hass, Platform.VALVE, DOMAIN, {}, hass_config)
    discovery.load_platform(hass, Platform.UPDATE, DOMAIN, {}, hass_config)

    return True


class Neviweb130Data:
    """Get the latest data and update the states."""

    def __init__(self, hass, config):
        """Init the neviweb130 data object."""
        # from pyneviweb130 import Neviweb130Client
        username = config.get(CONF_USERNAME)
        password = config.get(CONF_PASSWORD)
        network = config.get(CONF_NETWORK)
        network2 = config.get(CONF_NETWORK2)
        network3 = config.get(CONF_NETWORK3)
        ignore_miwi = config.get(CONF_IGNORE_MIWI)
        self.neviweb130_client = Neviweb130Client(hass, username, password, network, network2, network3, ignore_miwi)

        self.migration_done = asyncio.Event()

        # Attributes for versioning and release notes
        self.current_version = VERSION
        self.available_version = None
        self.release_notes = ""


# According to HA:
# https://developers.home-assistant.io/docs/en/creating_component_code_review.html
# "All API specific code has to be part of a third party library hosted on PyPi.
# Home Assistant should only interact with objects and not make direct calls to the API."
# So all code below this line should eventually be integrated in a PyPi project.


class PyNeviweb130Error(Exception):
    pass


class Neviweb130Client:
    def __init__(
        self,
        hass,
        username,
        password,
        network,
        network2,
        network3,
        ignore_miwi,
        timeout=REQUESTS_TIMEOUT,
    ):
        """Initialize the client object."""
        self.hass = hass
        self._email = username
        self._password = password
        self._network_name = network
        self._network_name2 = network2
        self._network_name3 = network3
        self._code: str | None = None
        self._ignore_miwi = ignore_miwi
        self._gateway_id = None
        self._gateway_id2 = None
        self._gateway_id3 = None
        self.gateway_data = {}
        self.gateway_data2 = {}
        self.gateway_data3 = {}
        self._headers = None
        self._account = None
        self._cookies: RequestsCookieJar | None = None
        self._timeout = timeout
        self._occupancyMode = None
        self.user = None

        self.__post_login_page()
        self.__get_network()
        self.__get_gateway_data()

    def update(self):
        self.__get_gateway_data()

    def test_connect(self):
        self.__post_login_page()

    def reconnect(self):
        self.__post_login_page()
        self.__get_network()
        self.__get_gateway_data()

    def notify_ha(self, msg: str, title: str = "Neviweb130 integration " + VERSION):
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

    def __post_login_page(self) -> None:
        """Login to Neviweb."""
        increment_request_counter(self.hass)
        data = {
            "username": self._email,
            "password": self._password,
            "interface": "neviweb",
            "stayConnected": 1,
        }
        try:
            raw_res = requests.post(
                LOGIN_URL,
                json=data,
                cookies=self._cookies,
                allow_redirects=False,
                timeout=self._timeout,
            )
        except OSError:
            raise PyNeviweb130Error("Cannot submit login form... Check your network or firewall")
        if raw_res.status_code != 200:
            _LOGGER.debug("Login status: %s", raw_res.json())
            raise PyNeviweb130Error("Cannot log in")

        # Update cookies
        if self._cookies is None:
            self._cookies = raw_res.cookies
        else:
            self._cookies.update(raw_res.cookies)

        data = raw_res.json()
        _LOGGER.debug("Login response: %s", data)
        if "error" in data:
            if data["error"]["code"] == "ACCSESSEXC":
                raise ConfigEntryNotReady(
                    "Too many active sessions. "
                    "Close all neviweb130 sessions you have opened on other platform (mobile, browser, ...). "
                    "If this error persists, deactivate this integration (or shutdown homeassistant), "
                    f"wait a few minutes, then reactivate (or restart) it. Error code: {data['error']['code']}"
                )
            elif data["error"]["code"] == "USRBADLOGIN":
                raise ConfigEntryAuthFailed(
                    "Invalid Neviweb username and/or password... "
                    f"Check your configuration parameters. Error code: {data['error']['code']}"
                )

            raise ConfigEntryError(f"Unknown error while logging to Neviweb. Error code: {data['error']['code']}")

        self.user = data["user"]
        self._headers = {"Session-Id": data["session"]}
        self._account = str(data["account"]["id"])
        _LOGGER.debug("Successfully logged in to: %s", self._account)

    def __get_network(self) -> None:
        """Get gateway id associated to the desired network."""
        increment_request_counter(self.hass)
        # Http requests
        if self._account is None:
            raise ConfigEntryAuthFailed("Account ID is empty, check your username and password to log into Neviweb...")

        try:
            raw_res = requests.get(
                LOCATIONS_URL + self._account,
                headers=self._headers,
                cookies=self._cookies,
                timeout=self._timeout,
            )
            networks = raw_res.json()
            _LOGGER.warning("Number of networks found on Neviweb: %s", len(networks))
            _LOGGER.warning("networks: %s", networks)
            if (
                self._network_name is None and self._network_name2 is None and self._network_name3 is None
            ):  # Use 1st network found, second or third if found
                self._gateway_id = networks[0]["id"]
                self._network_name = networks[0]["name"]
                self._occupancyMode = networks[0]["mode"]
                self._code = networks[0]["postalCode"]
                _LOGGER.warning("Selecting %s as first network", self._network_name)
                if len(networks) > 1:
                    self._gateway_id2 = networks[1]["id"]
                    self._network_name2 = networks[1]["name"]
                    self._occupancyMode = networks[1]["mode"]
                    self._code = networks[1]["postalCode"]
                    _LOGGER.warning("Selecting %s as second network", self._network_name2)
                    if len(networks) > 2:
                        self._gateway_id3 = networks[2]["id"]
                        self._network_name3 = networks[2]["name"]
                        self._occupancyMode = networks[2]["mode"]
                        self._code = networks[2]["postalCode"]
                        _LOGGER.warning("Selecting %s as third network", self._network_name3)
            else:
                for network in networks:
                    if network["name"] == self._network_name:
                        self._gateway_id = network["id"]
                        self._occupancyMode = network["mode"]
                        self._code = network["postalCode"]
                        _LOGGER.warning(
                            "Selecting %s network among: %s",
                            self._network_name,
                            networks,
                        )
                        continue
                    elif (network["name"] == self._network_name.capitalize()) or (
                        network["name"] == self._network_name[0].lower() + self._network_name[1:]
                    ):
                        self._gateway_id = network["id"]
                        self._occupancyMode = network["mode"]
                        self._code = network["postalCode"]
                        _LOGGER.warning(
                            "Please check first letter of your network name. "
                            "Is it a capital letter or not? "
                            f"Selecting {self._network_name} network among: {networks}"
                        )
                        continue
                    else:
                        _LOGGER.warning(
                            f"Your network name {self._network_name} do not correspond to "
                            f"discovered network {network['name']}, skipping this one... "
                            f"Please check your config if nothing get discovered"
                        )

                    if self._network_name2 is not None and self._network_name2 != "":
                        if network["name"] == self._network_name2:
                            self._gateway_id2 = network["id"]
                            self._occupancyMode = network["mode"]
                            self._code = network["postalCode"]
                            _LOGGER.debug(
                                "Selecting %s network among: %s",
                                self._network_name2,
                                networks,
                            )
                            continue
                        elif (network["name"] == self._network_name2.capitalize()) or (
                            network["name"] == self._network_name2[0].lower() + self._network_name2[1:]
                        ):
                            self._gateway_id = network["id"]
                            self._occupancyMode = network["mode"]
                            self._code = network["postalCode"]
                            _LOGGER.warning(
                                "Please check first letter of your network2 name. "
                                "Is it a capital letter or not? "
                                f"Selecting {self._network_name2} network among: {networks}"
                            )
                            continue
                        else:
                            _LOGGER.warning(
                                f"Your network2 name {self._network_name2} do not correspond to "
                                f"discovered network {network['name']}, skipping this one..."
                            )

                    if self._network_name3 is not None and self._network_name3 != "":
                        if network["name"] == self._network_name3:
                            self._gateway_id3 = network["id"]
                            self._occupancyMode = network["mode"]
                            self._code = network["postalCode"]
                            _LOGGER.warning(
                                "Selecting %s network among: %s",
                                self._network_name3,
                                networks,
                            )
                            continue
                        elif (network["name"] == self._network_name3.capitalize()) or (
                            network["name"] == self._network_name3[0].lower() + self._network_name3[1:]
                        ):
                            self._gateway_id = network["id"]
                            self._occupancyMode = network["mode"]
                            self._code = network["postalCode"]
                            _LOGGER.warning(
                                "Please check first letter of your network3 name. "
                                "Is it a capital letter or not? "
                                f"Selecting {self._network_name3} network among: {networks}"
                            )
                            continue
                        else:
                            _LOGGER.warning(
                                f"Your network3 name {self._network_name3} do not correspond to "
                                f"discovered network {network['name']}, skipping this one..."
                            )
        except OSError:
            raise PyNeviweb130Error("Cannot get Neviweb's networks")

        # Update cookies
        if self._cookies is None:
            self._cookies = raw_res.cookies
        else:
            self._cookies.update(raw_res.cookies)

        # Prepare data
        self.gateway_data = raw_res.json()

    def __get_gateway_data(self) -> None:
        """Get gateway data."""
        increment_request_counter(self.hass)
        # Check if gateway_id was set
        if self._gateway_id is None and self._gateway_id2 is None and self._gateway_id3 is None:
            _LOGGER.warning("No gateway defined, check your config for networks names...")
            self.notify_ha(
                "All Gateway ID are None. Network selection failed. "
                + "Check that your configuration network names match one of the networks in your Neviweb account. "
                + "Available networks were logged during network selection. Check your log"
            )
        # Http requests
        try:
            raw_res = requests.get(
                GATEWAY_DEVICE_URL + str(self._gateway_id),
                headers=self._headers,
                cookies=self._cookies,
                timeout=self._timeout,
            )
            _LOGGER.debug("Received gateway data: %s", raw_res.json())
        except OSError:
            raise PyNeviweb130Error("Cannot get gateway data")

        # Update cookies
        if self._cookies is None:
            self._cookies = raw_res.cookies
        else:
            self._cookies.update(raw_res.cookies)

        # Prepare data
        self.gateway_data = raw_res.json()
        _LOGGER.debug("Gateway_data: %s", self.gateway_data)

        if self._gateway_id2 is not None:
            try:
                raw_res2 = requests.get(
                    GATEWAY_DEVICE_URL + str(self._gateway_id2),
                    headers=self._headers,
                    cookies=self._cookies,
                    timeout=self._timeout,
                )
                _LOGGER.debug("Received gateway data 2: %s", raw_res2.json())
            except OSError:
                raise PyNeviweb130Error("Cannot get gateway data 2")

            # Prepare data
            self.gateway_data2 = raw_res2.json()
            _LOGGER.debug("Gateway_data2: %s", self.gateway_data2)

        if self._gateway_id3 is not None:
            try:
                raw_res3 = requests.get(
                    GATEWAY_DEVICE_URL + str(self._gateway_id3),
                    headers=self._headers,
                    cookies=self._cookies,
                    timeout=self._timeout,
                )
                _LOGGER.debug("Received gateway data 3: %s", raw_res3.json())
            except OSError:
                raise PyNeviweb130Error("Cannot get gateway data 3")

            # Prepare data
            self.gateway_data3 = raw_res3.json()
            _LOGGER.debug("Gateway_data3: %s", self.gateway_data3)

        for device in self.gateway_data:
            data = self.get_device_attributes(str(device["id"]), [ATTR_SIGNATURE])
            if ATTR_SIGNATURE in data:
                device[ATTR_SIGNATURE] = data[ATTR_SIGNATURE]
            _LOGGER.debug("Received signature data: %s", data)
            if data[ATTR_SIGNATURE]["protocol"] == "miwi":
                if not self._ignore_miwi:
                    _LOGGER.debug(
                        "The Neviweb location selected for parameter «network» contain unsupported device "
                        "with protocol miwi. If this location contain only miwi devices, "
                        "it should be added to custom_component «sinope neviweb» instead. "
                        "If the location contain mixed miwi, Zigbee and/or Wi-Fi devices, "
                        "add parameter: ignore_miwi: True, in your neviweb130 configuration"
                    )
        if self._gateway_id2 is not None:
            for device in self.gateway_data2:
                data2 = self.get_device_attributes(str(device["id"]), [ATTR_SIGNATURE])
                if ATTR_SIGNATURE in data2:
                    device[ATTR_SIGNATURE] = data2[ATTR_SIGNATURE]
                _LOGGER.debug("Received signature data: %s", data2)
                if data2[ATTR_SIGNATURE]["protocol"] == "miwi":
                    if not self._ignore_miwi:
                        _LOGGER.debug(
                            "The Neviweb location selected for parameter «network2» contain unsupported device "
                            "with protocol miwi. If this location contain only miwi devices, "
                            "it should be added to custom_component «sinope neviweb» instead. "
                            "If the location contain mixed miwi, Zigbee and/or Wi-Fi devices, "
                            "add parameter: ignore_miwi: True, in your neviweb130 configuration"
                        )
        if self._gateway_id3 is not None:
            for device in self.gateway_data3:
                data3 = self.get_device_attributes(str(device["id"]), [ATTR_SIGNATURE])
                if ATTR_SIGNATURE in data3:
                    device[ATTR_SIGNATURE] = data3[ATTR_SIGNATURE]
                _LOGGER.debug("Received signature data: %s", data3)
                if data3[ATTR_SIGNATURE]["protocol"] == "miwi":
                    if not self._ignore_miwi:
                        _LOGGER.debug(
                            "The Neviweb location selected for parameter «network3» contain unsupported device "
                            "with protocol miwi. If this location contain only miwi devices, "
                            "it should be added to custom_component «sinope neviweb» instead. "
                            "If the location contain mixed miwi, Zigbee and/or Wi-Fi devices, "
                            "add parameter: ignore_miwi: True, in your neviweb130 configuration"
                        )

    def get_device_attributes(self, device_id: str, attributes: list[str]) -> Any:
        """Get device attributes."""
        increment_request_counter(self.hass)
        # Http requests
        try:
            raw_res = requests.get(
                DEVICE_DATA_URL + device_id + "/attribute?attributes=" + ",".join(attributes),
                headers=self._headers,
                cookies=self._cookies,
                timeout=self._timeout,
            )
        #            _LOGGER.debug("Received devices data: %s", raw_res.json())
        except requests.exceptions.ReadTimeout:
            return {"errorCode": "ReadTimeout"}
        except Exception as e:
            raise PyNeviweb130Error(f"Cannot get device attributes {e}")
        # Update cookies
        if self._cookies is None:
            self._cookies = raw_res.cookies
        else:
            self._cookies.update(raw_res.cookies)
        # Prepare data
        data = raw_res.json()
        if "error" in data:
            if data["error"]["code"] == "USRSESSEXP":
                _LOGGER.error(
                    "Session expired. Set a scan_interval less than 10 minutes, otherwise the session will end"
                )
                # raise PyNeviweb130Error("Session expired... Reconnecting...")
        return data

    def get_device_status(self, device_id: str):
        """Get device status for the GT130."""
        increment_request_counter(self.hass)
        # Http requests
        try:
            raw_res = requests.get(
                DEVICE_DATA_URL + device_id + "/status",
                headers=self._headers,
                cookies=self._cookies,
                timeout=self._timeout,
            )
            _LOGGER.debug("Received devices status: %s", raw_res.json())
        except requests.exceptions.ReadTimeout:
            return {"errorCode": "ReadTimeout"}
        except Exception as e:
            raise PyNeviweb130Error("Cannot get device status", e)
        # Prepare data
        data = raw_res.json()
        if "error" in data:
            if data["error"]["code"] == "USRSESSEXP":
                _LOGGER.error(
                    "Session expired. Set a scan_interval less than 10 minutes, otherwise the session will end"
                )
                # raise PyNeviweb130Error("Session expired... Reconnecting...")
        return data

    def get_neviweb_status(self, location):
        """Get neviweb occupancyMode status."""
        increment_request_counter(self.hass)
        # Http requests
        try:
            raw_res = requests.get(
                NEVIWEB_LOCATION + str(location) + "/notifications",
                headers=self._headers,
                cookies=self._cookies,
                timeout=self._timeout,
            )
            _LOGGER.debug("Received neviweb status: %s", raw_res.json())
        except requests.exceptions.ReadTimeout:
            return {"errorCode": "ReadTimeout"}
        except Exception as e:
            raise PyNeviweb130Error("Cannot get neviweb status", e)
        data = raw_res.json()
        if "error" in data:
            if data["error"]["code"] == "USRSESSEXP":
                _LOGGER.error(
                    "Session expired. Set a scan_interval less than 10 minutes, otherwise the session will end"
                )
                # raise PyNeviweb130Error("Session expired...reconnecting...")
        return data

    def get_device_alert(self, device_id: str):
        """Get device alert for Sedna valve."""
        increment_request_counter(self.hass)
        # Http requests
        try:
            raw_res = requests.get(
                DEVICE_DATA_URL + device_id + "/alert",
                headers=self._headers,
                cookies=self._cookies,
                timeout=self._timeout,
            )
            _LOGGER.debug("Received devices alert (%s): %s", device_id, raw_res.json())
        except requests.exceptions.ReadTimeout:
            return {"errorCode": "ReadTimeout"}
        except Exception as e:
            raise PyNeviweb130Error("Cannot get device alert", e)
        # Update cookies
        if self._cookies is None:
            self._cookies = raw_res.cookies
        else:
            self._cookies.update(raw_res.cookies)
        # Prepare data
        data = raw_res.json()
        if "error" in data:
            if data["error"]["code"] == "USRSESSEXP":
                _LOGGER.error(
                    "Session expired. Set a scan_interval less than 10 minutes, otherwise the session will end"
                )
                # raise PyNeviweb130Error("Session expired... Reconnecting...")
        return data

    def get_device_monthly_stats(self, device_id: str, HC: bool):
        """Get device power consumption (in Wh) for the last 24 months."""
        increment_request_counter(self.hass)
        # Http requests
        if HC:
            data = DEVICE_DATA_URL + device_id + "/energy/monthly"
        else:
            data = DEVICE_DATA_URL + device_id + "/consumption/monthly"
        _LOGGER.debug("monthly data = %s", data)
        try:
            raw_res = requests.get(
                data,
                headers=self._headers,
                cookies=self._cookies,
                timeout=self._timeout,
            )
        except OSError:
            raise PyNeviweb130Error("Cannot get device monthly stats...")
        # Update cookies
        if self._cookies is None:
            self._cookies = raw_res.cookies
        else:
            self._cookies.update(raw_res.cookies)
        # Prepare data
        data = raw_res.json()
        # _LOGGER.debug("Monthly_stats data: %s", data)
        if "history" in data:
            return data["history"]
        else:
            _LOGGER.debug("Monthly stat error: %s", data)
            return None

    def get_device_daily_stats(self, device_id: str, HC: bool):
        """Get device power consumption (in Wh) for the last 30 days."""
        increment_request_counter(self.hass)
        # Http requests
        if HC:
            data = DEVICE_DATA_URL + device_id + "/energy/daily"
        else:
            data = DEVICE_DATA_URL + device_id + "/consumption/daily"
        _LOGGER.debug("daily data = %s", data)
        try:
            raw_res = requests.get(
                data,
                headers=self._headers,
                cookies=self._cookies,
                timeout=self._timeout,
            )
        except OSError:
            raise PyNeviweb130Error("Cannot get device daily stats...")
        # Update cookies
        if self._cookies is None:
            self._cookies = raw_res.cookies
        else:
            self._cookies.update(raw_res.cookies)
        # Prepare data
        data = raw_res.json()
        # _LOGGER.debug("Daily_stats data: %s", data)
        if "history" in data:
            return data["history"]
        else:
            _LOGGER.debug("Daily stat error: %s", data)
            return None

    def get_device_hourly_stats(self, device_id: str, HC: bool):
        """Get device power consumption (in Wh) for the last 24 hours."""
        increment_request_counter(self.hass)
        # Http requests
        if HC:
            data = DEVICE_DATA_URL + device_id + "/energy/hourly"
        else:
            data = DEVICE_DATA_URL + device_id + "/consumption/hourly"
        _LOGGER.debug("hourly data = %s", data)
        try:
            raw_res = requests.get(
                data,
                headers=self._headers,
                cookies=self._cookies,
                timeout=self._timeout,
            )
        except OSError:
            raise PyNeviweb130Error("Cannot get device hourly stats...")
        # Update cookies
        if self._cookies is None:
            self._cookies = raw_res.cookies
        else:
            self._cookies.update(raw_res.cookies)
        # Prepare data
        data = raw_res.json()
        # _LOGGER.debug("Hourly_stats data: %s", data)
        if "history" in data:
            return data["history"]
        else:
            _LOGGER.debug("Hourly stat error: %s", data)
            return None

    def get_weather(self):
        """Get Neviweb weather for my location."""
        increment_request_counter(self.hass)
        if self._code is None:
            raise ValueError("self._code is None")
        try:
            raw_res = requests.get(
                NEVIWEB_WEATHER + self._code,
                headers=self._headers,
                cookies=self._cookies,
                timeout=self._timeout,
            )
        except OSError:
            raise PyNeviweb130Error("Cannot get Neviweb weather and icon...")
        # Update cookies
        if self._cookies is None:
            self._cookies = raw_res.cookies
        else:
            self._cookies.update(raw_res.cookies)
        # Prepare data
        data = raw_res.json()
        # _LOGGER.debug("weather data: %s", data)
        return data

    def get_device_sensor_error(self, device_id: str):
        """Get device error code status."""
        increment_request_counter(self.hass)
        # Http requests
        try:
            raw_res = requests.get(
                DEVICE_DATA_URL + device_id + "/attribute?attributes=errorCodeSet1",
                headers=self._headers,
                cookies=self._cookies,
                timeout=self._timeout,
            )
        except OSError:
            raise PyNeviweb130Error("Cannot get device error code status...")
        # Update cookies
        if self._cookies is None:
            self._cookies = raw_res.cookies
        else:
            self._cookies.update(raw_res.cookies)
        # Prepare data
        data = raw_res.json()
        if "errorCodeSet1" in data:
            return data["errorCodeSet1"]
        _LOGGER.debug("Error code status data: %s", data)
        return None

    def set_brightness(self, device_id: str, brightness):
        """Set device brightness."""
        data = {ATTR_INTENSITY: brightness}
        self.set_device_attributes(device_id, data)

    def set_onoff(self, device_id: str, onoff):
        """Set device onOff state."""
        data = {ATTR_ONOFF: onoff}
        self.set_device_attributes(device_id, data)

    def set_light_onoff(self, device_id: str, onoff, brightness):
        """Set light device onOff state."""
        data = {ATTR_ONOFF: onoff, ATTR_INTENSITY: brightness}
        self.set_device_attributes(device_id, data)

    def set_valve_onoff(self, device_id: str, onoff):
        """Set sedna valve onOff state."""
        data = {ATTR_MOTOR_TARGET: onoff}
        self.set_device_attributes(device_id, data)

    def set_mode(self, device_id: str, mode):
        """Set device operation mode."""
        data = {ATTR_POWER_MODE: mode}
        self.set_device_attributes(device_id, data)

    def set_setpoint_mode(self, device_id: str, mode, wifi, HC):
        """Set thermostat operation mode."""
        """Work differently for Wi-Fi and Zigbee devices and TH6250xx devices."""
        if wifi:
            if HC:
                neviweb_mode = NEVIWEB_MODE_MAP.get(mode, "off")
                data = {ATTR_HEAT_COOL: neviweb_mode}
            else:
                if mode in [HVACMode.HEAT, MODE_MANUAL]:
                    mode = MODE_MANUAL
                data = {ATTR_SETPOINT_MODE: mode}
        else:
            data = {ATTR_SYSTEM_MODE: mode}
        _LOGGER.debug("Setpoint mode data: %s", data)
        self.set_device_attributes(device_id, data)

    def set_occupancy_mode(self, device_id: str, mode, wifi):
        """Set thermostat preset mode."""
        """Work differently for Wi-Fi and Zigbee devices."""
        if wifi:
            if mode in [PRESET_AWAY, PRESET_HOME]:
                data = {ATTR_OCCUPANCY: mode}
            else:
                return
        else:
            data = {ATTR_SYSTEM_MODE: mode}
        self.set_device_attributes(device_id, data)

    def set_temperature(self, device_id: str, temperature):
        """Set device heating temperature target."""
        data = {ATTR_ROOM_SETPOINT: temperature}
        self.set_device_attributes(device_id, data)

    def set_cool_temperature(self, device_id: str, temperature):
        """Set device cooling temperature target."""
        data = {ATTR_COOL_SETPOINT: temperature}
        self.set_device_attributes(device_id, data)

    def set_room_setpoint_away(self, device_id: str, temperature):
        """Set device away heating temperature target for all Wi-Fi thermostats."""
        data = {ATTR_ROOM_SETPOINT_AWAY: temperature}
        self.set_device_attributes(device_id, data)

    def set_cool_setpoint_away(self, device_id: str, temperature, HC):
        """Set device away cooling temperature target for TH6500WF and TH6250WF."""
        if HC:
            data = {ATTR_COOL_SETPOINT_AWAY: temperature}
            self.set_device_attributes(device_id, data)
        else:
            self.notify_ha("Warning: Service set_cool_setpoint_away is only for TH6500WF or TH6250WF thermostats")

    def set_humidity(self, device_id: str, humidity):
        """Set device humidity target."""
        data = {ATTR_HUMIDITY_SETPOINT: humidity}
        self.set_device_attributes(device_id, data)

    def set_accessory_type(self, device_id: str, accessory_type):
        """Set accessory (humidifier, dehumidifier, air exchanger) type for TH6500WF and TH6250WF."""
        data = {
            ATTR_ACCESSORY_TYPE: {
                "humOnHeat": accessory_type == "humOnHeat",
                "humOnFan": accessory_type == "humOnFan",
                "humStandalone": False,
                "dehumStandalone": accessory_type == "dehum",
                "airExchangerStandalone": accessory_type == "airExchanger",
            }
        }
        self.set_device_attributes(device_id, data)

    def set_schedule_mode(self, device_id: str, mode, HC):
        """Set schedule mode for TH6500WF and TH6250WF."""
        if HC:
            data = {ATTR_SETPOINT_MODE: mode}
            self.set_device_attributes(device_id, data)
        else:
            self.notify_ha("Warning: Service set_schedule_mode is only for TH6500WF or TH6250WF thermostats")

    def set_heatcool_delta(self, device_id: str, level, HC):
        """Set schedule mode for TH6500WF and TH6250WF."""
        if HC:
            data = {ATTR_HEATCOOL_SETPOINT_MIN_DELTA: level}
            self.set_device_attributes(device_id, data)
        else:
            self.notify_ha("Warning: Service set_heatcool_min_delta is only for TH6500WF or TH6250WF thermostats")

    def set_fan_filter_reminder(self, device_id: str, month, HC):
        """Set schedule mode for TH6500WF and TH6250WF."""
        if HC:
            month_val = month * 720
            data = {ATTR_FAN_FILTER_REMAIN: month_val}
            self.set_device_attributes(device_id, data)
        else:
            self.notify_ha("Warning: Service set_fan_filter_reminder is only for TH6500WF or TH6250WF thermostats")

    def set_temperature_offset(self, device_id: str, temp, HC):
        """Set schedule mode for TH6500WF and TH6250WF."""
        if HC:
            data = {ATTR_TEMP_OFFSET_HEAT: temp}
            self.set_device_attributes(device_id, data)
        else:
            self.notify_ha("Warning: Service set_temperature_offset is only for TH6500WF or TH6250WF thermostats")

    def set_humidity_offset(self, device_id: str, offset, HC):
        """Set humidity setpoint offset for TH6500WF and TH6250WF."""
        if HC:
            data = {ATTR_HUMIDITY_SETPOINT_OFFSET: offset}
            self.set_device_attributes(device_id, data)
        else:
            self.notify_ha("Warning: Service set_humidity_offset is only for TH6500WF or TH6250WF thermostats")

    def set_humidity_mode(self, device_id: str, mode, HC):
        """Set humidity setpoint mode for TH6500WF and TH6250WF."""
        if HC:
            data = {ATTR_HUMIDITY_SETPOINT_MODE: mode}
            self.set_device_attributes(device_id, data)
        else:
            self.notify_ha("Warning: Service set_humidity_mode is only for TH6500WF or TH6250WF thermostats")

    def set_air_ex_min_time_on(self, device_id: str, time, HC):
        """Set minimum time the air exchanger is on per hour."""
        if HC:
            time_val = None
            match time:
                case "Off":
                    time_val = 0
                case "20 min":
                    time_val = 20
                case "40 min":
                    time_val = 40
                case "Continuous":
                    time_val = 60
            data = {ATTR_AIR_EX_MIN_TIME_ON: time_val}
            self.set_device_attributes(device_id, data)
        else:
            self.notify_ha("Warning: Service set_air_ex_time_on is only for TH6500WF or TH6250WF thermostats")

    def set_heat_installation_type(self, device_id: str, type_val: str):
        """Set heater installation type (add-on or conventional)."""
        data = {ATTR_HEAT_INSTALLATION_TYPE: type_val}
        self.set_device_attributes(device_id, data)

    def set_backlight(self, device_id: str, level, is_wifi: bool):
        """Set backlight intensity when idle, on or auto.
        Work differently for Wi-Fi and Zigbee devices."""
        if is_wifi:
            data = {ATTR_BACKLIGHT_AUTO_DIM: level}
        else:
            data = {ATTR_BACKLIGHT: level}
        _LOGGER.debug("backlight.data = %s", data)
        self.set_device_attributes(device_id, data)

    def set_second_display(self, device_id: str, display):
        """Set device second display for outside temperature or setpoint temperature."""
        data = {ATTR_DISPLAY2: display}
        _LOGGER.debug("display.data = %s", data)
        self.set_device_attributes(device_id, data)

    def set_keypad_lock(self, device_id: str, lock, wifi):
        """Set device keyboard locked/unlocked."""
        if wifi:
            data = {ATTR_WIFI_KEYPAD: lock}
        else:
            data = {ATTR_KEYPAD: lock}
        _LOGGER.debug("lock.data = %s", data)
        self.set_device_attributes(device_id, data)

    def set_phase(self, device_id: str, phase):
        """Set device phase control mode."""
        data = {ATTR_PHASE_CONTROL: phase}
        _LOGGER.debug("phase.data = %s", data)
        self.set_device_attributes(device_id, data)

    def set_double_up(self, device_id: str, double):
        """Set device key double up action."""
        data = {ATTR_KEY_DOUBLE_UP: double}
        _LOGGER.debug("double_up.data = %s", data)
        self.set_device_attributes(device_id, data)

    def set_timer(self, device_id: str, time):
        """Set device auto off for timer on switch and multi controller."""
        data = {ATTR_TIMER: time}
        _LOGGER.debug("timer.data = %s", data)
        self.set_device_attributes(device_id, data)

    def set_timer2(self, device_id: str, time):
        """Set device auto off for timer2 on multi controller."""
        data = {ATTR_TIMER2: time}
        _LOGGER.debug("timer2.data = %s", data)
        self.set_device_attributes(device_id, data)

    def set_time_format(self, device_id: str, time):
        """Set device time format 12h or 24h."""
        data = {ATTR_TIME_FORMAT: time}
        _LOGGER.debug("time.data = %s", data)
        self.set_device_attributes(device_id, data)

    def set_temperature_format(self, device_id: str, deg):
        """Set device temperature format: celsius or fahrenheit."""
        data = {ATTR_TEMP: deg}
        _LOGGER.debug("temperature.data = %s", data)
        self.set_device_attributes(device_id, data)

    def set_floor_air_limit(self, device_id: str, status, temp):
        """Set device maximum air temperature limit."""
        if temp == 0:
            temp = None
        data = {ATTR_FLOOR_AIR_LIMIT: {"status": status, "value": temp}}
        _LOGGER.debug("floorairlimit.data = %s", data)
        self.set_device_attributes(device_id, data)

    def set_early_start(self, device_id: str, start):
        """Set early start on/off for Wi-Fi thermostats."""
        data = {ATTR_EARLY_START: start}
        _LOGGER.debug("early_start.data = %s", data)
        self.set_device_attributes(device_id, data)

    def set_air_floor_mode(self, device_id: str, mode):
        """Switch temperature control between floor and ambient sensor."""
        data = {ATTR_FLOOR_MODE: mode}
        _LOGGER.debug("floor_mode.data = %s", data)
        self.set_device_attributes(device_id, data)

    def set_setpoint_min(self, device_id: str, temp):
        """Set device setpoint minimum temperature."""
        data = {ATTR_ROOM_SETPOINT_MIN: temp}
        _LOGGER.debug("setpointMin.data = %s", data)
        self.set_device_attributes(device_id, data)

    def set_setpoint_max(self, device_id: str, temp):
        """Set device setpoint maximum temperature."""
        data = {ATTR_ROOM_SETPOINT_MAX: temp}
        _LOGGER.debug("setpointMax.data = %s", data)
        self.set_device_attributes(device_id, data)

    def set_cool_setpoint_min(self, device_id: str, temp):
        """Set device cooling setpoint minimum temperature."""
        data = {ATTR_COOL_SETPOINT_MIN: temp}
        _LOGGER.debug("CoolsetpointMin.data = %s", data)
        self.set_device_attributes(device_id, data)

    def set_cool_setpoint_max(self, device_id: str, temp):
        """Set device cooling setpoint maximum temperature."""
        data = {ATTR_COOL_SETPOINT_MAX: temp}
        _LOGGER.debug("CoolsetpointMax.data = %s", data)
        self.set_device_attributes(device_id, data)

    def set_aux_cycle_output(self, device_id: str, val: int, wifi: bool):
        """Set low voltage thermostat aux cycle status and length."""
        data: dict[str, Any]
        if wifi:
            data = {ATTR_AUX_CYCLE_LENGTH: val}
            _LOGGER.debug("auxCycleLength.data = %s", data)
        else:
            data = {ATTR_CYCLE_OUTPUT2: {"status": "on" if val > 0 else "off", "value": val}}
            _LOGGER.debug("auxCycleOutput.data = %s", data)
        self.set_device_attributes(device_id, data)

    def set_cycle_output(self, device_id: str, val: int, is_hc: bool):
        """Set low voltage thermostat main cycle length."""
        if is_hc:
            data = {ATTR_COOL_CYCLE_LENGTH: val}
            _LOGGER.debug("coolCycleLength.data = %s", data)
        else:
            data = {ATTR_CYCLE_LENGTH: val}
            _LOGGER.debug("cycleOutput.data = %s", data)
        self.set_device_attributes(device_id, data)

    def set_tank_size(self, device_id: str, val):
        """Set water heater tank size for RM3500ZB."""
        data = {ATTR_TANK_SIZE: val}
        _LOGGER.debug("TankSize.data = %s", data)
        self.set_device_attributes(device_id, data)

    def set_remaining_time(self, device_id: str, time):
        """Activate or deactivate calypso for time period."""
        data = {ATTR_COLD_LOAD_PICKUP_REMAIN_TIME: time}
        _LOGGER.debug("RemainingTime.data = %s", data)
        self.set_device_attributes(device_id, data)

    def set_sensor_type(self, device_id: str, val):
        """Set floor sensor type 10k, 12k."""
        data = {
            ATTR_FLOOR_SENSOR: val,
            ATTR_FLOOR_OUTPUT2: {"status": "off", "value": 0},
        }
        _LOGGER.debug("sensor.data = %s", data)
        self.set_device_attributes(device_id, data)

    def set_low_temp_protection(self, device_id: str, val):
        """Set water heater temperature protection for RM3500ZB."""
        data = {ATTR_WATER_TEMP_MIN: val}
        _LOGGER.debug("Low temp protection.data = %s", data)
        self.set_device_attributes(device_id, data)

    def set_controlled_device(self, device_id: str, val):
        """Set device name controlled by RM3250ZB and RM3250WF."""
        data = {ATTR_CONTROLLED_DEVICE: val}
        _LOGGER.debug("ControlledDevice.data = %s", data)
        self.set_device_attributes(device_id, data)

    def set_em_heat(self, device_id: str, heat, low, sec):
        """Set floor, low voltage, Wi-Fi floor and low voltage Wi-Fi thermostats auxiliary heat slave/off or on/off."""
        if low == "voltage":
            data = {ATTR_CYCLE_OUTPUT2: {"status": heat, "value": sec}}
        elif low == "wifi":
            data = {ATTR_AUX_CYCLE_LENGTH: sec}
        else:
            data = {ATTR_FLOOR_AUX: heat}
        _LOGGER.debug("em_heat.data = %s", data)
        self.set_device_attributes(device_id, data)

    def set_floor_limit(self, device_id: str, level, low, wifi):
        """Set floor setpoint limit low and high for Zigbee and Wi-Fi thermostats. (0 = off)."""
        data: dict[str, dict[str, str | int | None]]
        if level == 0:
            if wifi:
                if low == "low":
                    data = {ATTR_FLOOR_MIN: {"value": None, "status": "off"}}
                else:
                    data = {ATTR_FLOOR_MAX: {"value": None, "status": "off"}}
            else:
                if low == "low":
                    data = {
                        ATTR_FLOOR_MIN: {"status": "off", "value": None},
                        ATTR_FLOOR_OUTPUT2: {"status": "off", "value": 0},
                    }
                else:
                    data = {
                        ATTR_FLOOR_MAX: {"status": "off", "value": None},
                        ATTR_FLOOR_OUTPUT2: {"status": "off", "value": 0},
                    }
        else:
            if wifi:
                if low == "low":
                    data = {ATTR_FLOOR_MIN: {"value": level, "status": "on"}}
                else:
                    data = {ATTR_FLOOR_MAX: {"value": level, "status": "on"}}
            else:
                if low == "low":
                    data = {
                        ATTR_FLOOR_MIN: {"status": "on", "value": level},
                        ATTR_FLOOR_OUTPUT2: {"status": "off", "value": 0},
                    }
                else:
                    data = {
                        ATTR_FLOOR_MAX: {"status": "on", "value": level},
                        ATTR_FLOOR_OUTPUT2: {"status": "off", "value": 0},
                    }
        _LOGGER.debug("Floor limit = %s", data)
        self.set_device_attributes(device_id, data)

    def set_pump_protection(self, device_id: str, status, wifi):
        """Set low voltage thermostat pump protection status.
        Work differently for Wi-Fi and zigbee devices."""
        if wifi:
            data = {ATTR_PUMP_PROTEC: status}
        else:
            if status == "on":
                data = {
                    ATTR_PUMP_PROTEC_DURATION: {"status": "on", "value": 60},
                    ATTR_PUMP_PROTEC_PERIOD: {"status": "on", "value": 1},
                }
            else:
                data = {
                    ATTR_PUMP_PROTEC_DURATION: {"status": "off"},
                    ATTR_PUMP_PROTEC_PERIOD: {"status": "off"},
                }
        _LOGGER.debug("pump.data = %s", data)
        self.set_device_attributes(device_id, data)

    def set_flow_meter_model(self, device_id: str, model):
        """Set flow meter model connected to the Sedna valve 2e gen."""
        if model == "FS4221":
            data = {
                ATTR_FLOW_METER_CONFIG: {
                    "multiplier": 9887,
                    "offset": 87372,
                    "divisor": 1,
                },
                ATTR_FLOW_ENABLED: True,
            }
        elif model == "FS4220":
            data = {
                ATTR_FLOW_METER_CONFIG: {
                    "multiplier": 4546,
                    "offset": 30600,
                    "divisor": 1,
                },
                ATTR_FLOW_ENABLED: True,
            }
        else:
            data = {
                ATTR_FLOW_METER_CONFIG: {
                    "multiplier": 0,
                    "offset": 0,
                    "divisor": 1,
                },
                ATTR_FLOW_ENABLED: False,
            }
        _LOGGER.debug("Flowmeter model.data = %s", data)
        self.set_device_attributes(device_id, data)

    def set_flow_meter_delay(self, device_id: str, delay):
        """Set flow meter delay before alarm is activated on Sedna valve 2e gen."""
        data = {ATTR_FLOW_ALARM1_PERIOD: delay}
        _LOGGER.debug("Flowmeter delay.data = %s", data)
        self.set_device_attributes(device_id, data)

    def set_flow_meter_options(self, device_id: str, alarm, action, length, threshold):
        """Set flow meter options when leak alarm is activated on Sedna valve 2e gen."""
        data = {
            ATTR_FLOW_ALARM1_OPTION: {
                "triggerAlarm": alarm,
                "closeValve": action,
            },
            ATTR_FLOW_ALARM1_LENGTH: length,
            ATTR_FLOW_THRESHOLD: threshold,
        }
        _LOGGER.debug("Flowmeter options.data = %s", data)
        self.set_device_attributes(device_id, data)

    def set_flow_alarm_timer(self, device_id: str, timer):
        """Set flowmeter alarm action disabled timer, for valves with flowmeter."""
        data = {ATTR_FLOW_ALARM_TIMER: timer}
        _LOGGER.debug("Flowmeter alarm disable timer.data = %s", data)
        self.set_device_attributes(device_id, data)

    def set_led_indicator(self, device_id: str, state, red, green, blue):
        """Set device led indicator intensity and color for on and off state."""
        if state == 1:
            data = {
                ATTR_LED_ON_COLOR: {
                    "red": red,
                    "green": green,
                    "blue": blue,
                }
            }
            _LOGGER.debug("led on color.data = %s", data)
        else:
            data = {
                ATTR_LED_OFF_COLOR: {
                    "red": red,
                    "green": green,
                    "blue": blue,
                }
            }
            _LOGGER.debug("led off color.data = %s", data)
        self.set_device_attributes(device_id, data)

    def set_led_on_intensity(self, device_id: str, intensity):
        """Set device led indicator intensity for on state."""
        data = {ATTR_LED_ON_INTENSITY: intensity}
        self.set_device_attributes(device_id, data)
        _LOGGER.debug("led on intensity.data on = %s", data)

    def set_led_off_intensity(self, device_id: str, intensity):
        """Set device led indicator intensity for off state."""
        data = {ATTR_LED_OFF_INTENSITY: intensity}
        self.set_device_attributes(device_id, data)
        _LOGGER.debug("led off intensity.data on = %s", data)

    def set_light_min_intensity(self, device_id: str, intensity):
        """Set dimmer light minimum intensity from 1 to 3000."""
        data = {ATTR_INTENSITY_MIN: intensity}
        self.set_device_attributes(device_id, data)
        _LOGGER.debug("led min intensity.data on = %s", data)

    def set_wattage(self, device_id: str, watt):
        """Set light and dimmer watt load."""
        data = {ATTR_LIGHT_WATTAGE: {"status": "on", "value": watt}}
        _LOGGER.debug("wattage.data = %s", data)
        self.set_device_attributes(device_id, data)

    def set_auxiliary_load(self, device_id: str, status, load):
        """Set auxiliary output load in watt."""
        data = {ATTR_FLOOR_OUTPUT2: {"status": status, "value": load}}
        _LOGGER.debug("auxiliary_load.data = %s", data)
        self.set_device_attributes(device_id, data)

    def set_valve_alert(self, device_id: str, batt):
        """Set Sedna valve battery alert on/off."""
        data = {ATTR_BATT_ALERT: batt}
        _LOGGER.debug("valve.data = %s", data)
        self.set_device_attributes(device_id, data)

    def set_valve_temp_alert(self, device_id: str, temp):
        """Set Sedna valve temperature alert on/off."""
        data = {ATTR_TEMP_ALERT: temp}
        _LOGGER.debug("valve.data = %s", data)
        self.set_device_attributes(device_id, data)

    def set_battery_type(self, device_id: str, batt):
        """Set water leak sensor battery type, lithium or alkaline."""
        data = {ATTR_BATTERY_TYPE: batt}
        _LOGGER.debug("battery_type.data = %s", data)
        self.set_device_attributes(device_id, data)

    def set_sensor_alert(self, device_id: str, leak, batt, temp, close):
        """Set leak detector alert, battery, temperature, leak, Sedna valve closing."""
        data = {
            ATTR_LEAK_ALERT: leak,
            ATTR_BATT_ALERT: batt,
            ATTR_TEMP_ALERT: temp,
            ATTR_CONF_CLOSURE: close,
        }
        _LOGGER.debug("leak.data = %s", data)
        self.set_device_attributes(device_id, data)

    def set_load_dr_options(self, device_id: str, onoff, optout, dr):
        """Set load controller Eco Sinope attributes."""
        data = {
            ATTR_DRSTATUS: {
                "drActive": dr,
                "optOut": optout,
                "onOff": onoff,
            }
        }
        _LOGGER.debug("Load.DR.options = %s", data)
        self.set_device_attributes(device_id, data)

    def set_hvac_dr_options(
        self, device_id: str, *, dr=None, optout=None, setpoint=None, aux_conf=None, fan_speed_conf=None
    ):
        """Set load controller Eco Sinope attributes."""
        data: dict[str, Any]
        if dr is not None and optout is not None and setpoint is not None:
            data = {
                ATTR_DRSTATUS: {
                    "drActive": dr,
                    "optOut": optout,
                    "setpoint": setpoint,
                }
            }
            _LOGGER.debug("hvac.DR.options = %s", data)
            self.set_device_attributes(device_id, data)

        if aux_conf is not None:
            data = {ATTR_DR_AUX_CONF: "activated" if aux_conf == "on" else "deactivated"}
            _LOGGER.debug("hvac.DR.options = %s", data)
            self.set_device_attributes(device_id, data)

        if fan_speed_conf is not None:
            data = {
                # Not a typo: Disabled is really sending "on" (allow fan to be always on when the optim is disabled)
                ATTR_DR_FAN_SPEED_CONF: "auto" if fan_speed_conf == "on" else "on"
            }
            _LOGGER.debug("hvac.DR.options = %s", data)
            self.set_device_attributes(device_id, data)

    def set_hvac_dr_setpoint(self, device_id: str, status, val):
        """Set load controller Eco Sinope attributes."""
        data = {ATTR_DRSETPOINT: {"status": status, "value": val}}
        _LOGGER.debug("hvac.DR.setpoint = %s", data)
        self.set_device_attributes(device_id, data)

    def set_control_onoff(self, device_id: str, number, status):
        """Set valve controller onOff or OnOff2 status, on or off."""
        if number == 1:
            data = {ATTR_ONOFF: status}
        else:
            data = {ATTR_ONOFF2: status}
        _LOGGER.debug("control.valve.data = %s", data)
        self.set_device_attributes(device_id, data)

    def set_tank_type(self, device_id: str, tank):
        """Set tank type for LM4110-ZB sensor."""
        data = {ATTR_TANK_TYPE: tank}
        _LOGGER.debug("tank_type.data = %s", data)
        self.set_device_attributes(device_id, data)

    def set_gauge_type(self, device_id: str, gauge):
        """Set gauge type for LM4110-ZB sensor on propane tank."""
        data = {ATTR_GAUGE_TYPE: gauge}
        _LOGGER.debug("gauge_type.data = %s", data)
        self.set_device_attributes(device_id, data)

    def set_aux_heating_source(self, device_id: str, equip: str):
        """Set auxiliary heating source for TH6500WF and TH6250WF."""
        data = {ATTR_AUX_HEAT_SOURCE_TYPE: equip}
        _LOGGER.debug("aux_heating_source.data = %s", data)
        self.set_device_attributes(device_id, data)

    def set_low_fuel_alert(self, device_id: str, alert):
        """Set low fuel alert limit for LM4110-ZB sensor."""
        data = {ATTR_FUEL_PERCENT_ALERT: alert}
        _LOGGER.debug("low_fuel_alert.data = %s", data)
        self.set_device_attributes(device_id, data)

    def set_refuel_alert(self, device_id: str, alert):
        """Set refuel alert for LM4110-ZB sensor."""
        data = {ATTR_REFUEL: alert}
        _LOGGER.debug("Refuel_alert.data = %s", data)
        self.set_device_attributes(device_id, data)

    def set_tank_height(self, device_id: str, height):
        """Set low fuel alert limit for LM4110-ZB sensor."""
        data = {ATTR_TANK_HEIGHT: height}
        _LOGGER.debug("tank_height.data = %s", data)
        self.set_device_attributes(device_id, data)

    def set_fuel_alert(self, device_id: str, fuel):
        """Set low fuel alert limit for LM4110-ZB sensor."""
        data = {ATTR_FUEL_ALERT: fuel}
        _LOGGER.debug("tank_height.data = %s", data)
        self.set_device_attributes(device_id, data)

    def set_battery_alert(self, device_id: str, batt):
        """Set low fuel alert limit for LM4110-ZB sensor."""
        data = {ATTR_BATT_ALERT: batt}
        _LOGGER.debug("battery_alert.data = %s", data)
        self.set_device_attributes(device_id, data)

    def set_power_supply(self, device_id: str, supply):
        """Set power supply for Sedna valve."""
        data = {ATTR_POWER_SUPPLY: supply}
        _LOGGER.debug("power_supply.data = %s", data)
        self.set_device_attributes(device_id, data)

    def set_on_off_input_delay(self, device_id: str, delay, onoff, input_number):
        """Set input 1 or 2 on/off delay in seconds."""
        data = None
        match onoff:
            case "on":
                data = {ATTR_INPUT_1_ON_DELAY: delay} if input_number == 1 else {ATTR_INPUT_2_ON_DELAY: delay}
            case _:
                data = {ATTR_INPUT_1_OFF_DELAY: delay} if input_number == 1 else {ATTR_INPUT_2_OFF_DELAY: delay}
        _LOGGER.debug("input_delay.data = %s", data)
        self.set_device_attributes(device_id, data)

    def set_input_output_names(self, device_id: str, in1, in2, out1, out2):
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
        self.set_device_attributes(device_id, data)

    def set_heat_pump_limit(self, device_id: str, temp):
        """Set minimum temperature for heat pump operation."""
        data = {ATTR_BALANCE_PT: temp}
        _LOGGER.debug("Heat pump limit value.data = %s", data)
        self.set_device_attributes(device_id, data)

    def set_heat_lockout(self, device_id: str, temp, G2):
        """Set maximum outside temperature limit to allow heating device operation."""
        if G2:
            data = {ATTR_HEAT_LOCKOUT_TEMP: temp}
        else:
            data = {ATTR_HEAT_LOCK_TEMP: temp}
        _LOGGER.debug("Heat lockout limit value.data = %s", data)
        self.set_device_attributes(device_id, data)

    def set_cool_lockout(self, device_id: str, temp):
        """Set minimum outside temperature limit to allow cooling device operation."""
        data = {ATTR_COOL_LOCK_TEMP: temp}
        _LOGGER.debug("Cool lockout limit value.data = %s", data)
        self.set_device_attributes(device_id, data)

    def set_hp_display(self, device_id: str, display):
        """Set display on/off for heat pump."""
        data = {ATTR_DISPLAY_CONF: display}
        _LOGGER.debug("Display config value.data = %s", data)
        self.set_device_attributes(device_id, data)

    def set_hp_sound(self, device_id: str, sound):
        """Set display on/off for heat pump."""
        data = {ATTR_SOUND_CONF: sound}
        _LOGGER.debug("Sound config value.data = %s", data)
        self.set_device_attributes(device_id, data)

    def set_swing_horizontal(self, device_id: str, swing):
        """Set horizontal fan swing action for heat pump."""
        data = {ATTR_FAN_SWING_HORIZ: swing}
        _LOGGER.debug("Fan horizontal swing value.data = %s", data)
        self.set_device_attributes(device_id, data)

    def set_swing_vertical(self, device_id: str, swing):
        """Set vertical fan swing action for heat pump."""
        data = {ATTR_FAN_SWING_VERT: swing}
        _LOGGER.debug("Fan vertical swing value.data = %s", data)
        self.set_device_attributes(device_id, data)

    def set_fan_mode(self, device_id: str, speed):
        """Set fan speed (mode) for heat pump."""
        data = {ATTR_FAN_SPEED: speed}
        _LOGGER.debug("Fan speed value.data = %s", data)
        self.set_device_attributes(device_id, data)

    def set_hc_display(self, device_id: str, display):
        """Set device second display for outside temperature or setpoint temperature for TH1134ZB-HC."""
        data = {ATTR_DISPLAY2: display}
        _LOGGER.debug("Hc display.data = %s", data)
        self.set_device_attributes(device_id, data)

    def set_language(self, device_id: str, lang):
        """Set display language for TH1134ZB-HC."""
        data = {ATTR_LANGUAGE: lang}
        _LOGGER.debug("Hc language.data = %s", data)
        self.set_device_attributes(device_id, data)

    def set_heat_dissipation_time(self, device_id: str, time: int, HC):
        """Set heating purge time for TH6500WF and TH6250WF thermostats."""
        if HC:
            data = {ATTR_HEAT_PURGE_TIME: time}
            _LOGGER.debug("HC heat_dissipation_time.data = %s", data)
            self.set_device_attributes(device_id, data)
        else:
            self.notify_ha("Warning: Service set_heat_dissipation_time is only for TH6500WF or TH6250WF thermostats")

    def set_cool_dissipation_time(self, device_id: str, time: int, HC):
        """Set cooling purge time for TH6500WF and TH6250WF thermostats."""
        if HC:
            data = {ATTR_COOL_PURGE_TIME: time}
            _LOGGER.debug("HC cool_dissipation_time.data = %s", data)
            self.set_device_attributes(device_id, data)
        else:
            self.notify_ha("Warning: Service set_cool_dissipation_time is only for TH6500WF or TH6250WF thermostats")

    def set_reversing_valve_polarity(self, device_id: str, polarity: str):
        """Set minimum time the heater is on before letting be off again (run-on time).
        for TH6500WF and TH6250WF thermostats."""
        data = {ATTR_REVERSING_VALVE_POLARITY: polarity}
        _LOGGER.debug("HC set_reversing_valve_polarity.data = %s", data)
        self.set_device_attributes(device_id, data)

    def set_heat_min_time_on(self, device_id: str, time: int):
        """Set minimum time the heater is on before letting be off again (run-on time).
        for TH6500WF and TH6250WF thermostats."""
        data = {ATTR_HEAT_MIN_TIME_ON: time}
        _LOGGER.debug("HC heat_min_time_on.data = %s", data)
        self.set_device_attributes(device_id, data)

    def set_heat_min_time_off(self, device_id: str, time: int):
        """Set minimum time the heater is off before letting it be on again (cooldown time).
        for TH6500WF and TH6250WF thermostats."""
        data = {ATTR_HEAT_MIN_TIME_OFF: time}
        _LOGGER.debug("HC heat_min_time_off.data = %s", data)
        self.set_device_attributes(device_id, data)

    def set_cool_min_time_on(self, device_id: str, time: int):
        """Set minimum time the cooler is on before letting be off again (run-on time).
        for TH6500WF and TH6250WF thermostats."""
        data = {ATTR_COOL_MIN_TIME_ON: time}
        _LOGGER.debug("HC cool_min_time_on.data = %s", data)
        self.set_device_attributes(device_id, data)

    def set_cool_min_time_off(self, device_id: str, time: int):
        """Set minimum time the cooler is off before letting it be on again (cooldown time).
        for TH6500WF and TH6250WF thermostats."""
        data = {ATTR_COOL_MIN_TIME_OFF: time}
        _LOGGER.debug("HC cool_min_time_off.data = %s", data)
        self.set_device_attributes(device_id, data)

    def set_aux_heat_min_time_on(self, device_id: str, time: int):
        """Set minimum time the auxiliary heater is on before letting be off again (run-on time).
        for TH6500WF and TH6250WF thermostats."""
        data = {ATTR_AUX_HEAT_MIN_TIME_ON: time}
        _LOGGER.debug("HC aux_heat_min_time_on.data = %s", data)
        self.set_device_attributes(device_id, data)

    def set_aux_heat_min_time_off(self, device_id: str, time: int):
        """Set minimum time the auxiliary heater is off before letting it be on again (cooldown time).
        for TH6500WF and TH6250WF thermostats."""
        data = {ATTR_AUX_HEAT_MIN_TIME_OFF: time}
        _LOGGER.debug("HC aux_heat_min_time_off.data = %s", data)
        self.set_device_attributes(device_id, data)

    def set_heat_interstage_delay(self, device_id: str, time: int):
        """Set total time before reaching last heat stage (interstage delay).
        for TH6500WF and TH6250WF thermostats."""
        data = {ATTR_HEAT_INTERSTAGE_DELAY: time}
        _LOGGER.debug("HC set_heat_interstage_delay.data = %s", data)
        self.set_device_attributes(device_id, data)

    def set_aux_interstage_delay(self, device_id: str, time: int):
        """Set total time before reaching last auxiliary heat stage (interstage delay).
        for TH6500WF and TH6250WF thermostats."""
        data = {ATTR_AUX_INTERSTAGE_DELAY: time}
        _LOGGER.debug("HC set_aux_interstage_delay.data = %s", data)
        self.set_device_attributes(device_id, data)

    def set_cool_interstage_delay(self, device_id: str, time: int):
        """Set total time before reaching last cool stage (interstage delay).
        for TH6500WF and TH6250WF thermostats."""
        data = {ATTR_COOL_INTERSTAGE_DELAY: time}
        _LOGGER.debug("HC set_cool_interstage_delay.data = %s", data)
        self.set_device_attributes(device_id, data)

    def set_heat_interstage_min_delay(self, device_id: str, time: int):
        """Set minimum time before reaching next heat stage (min interstage delay).
        for TH6500WF and TH6250WF thermostats."""
        data = {ATTR_HEAT_INTERSTAGE_MIN_DELAY: time}
        _LOGGER.debug("HC set_heat_min_interstage_delay.data = %s", data)
        self.set_device_attributes(device_id, data)

    def set_aux_interstage_min_delay(self, device_id: str, time: int):
        """Set minimum time before reaching next auxiliary stage (min interstage delay).
        for TH6500WF and TH6250WF thermostats."""
        data = {ATTR_AUX_INTERSTAGE_MIN_DELAY: time}
        _LOGGER.debug("HC set_aux_min_interstage_delay.data = %s", data)
        self.set_device_attributes(device_id, data)

    def set_cool_interstage_min_delay(self, device_id: str, time: int):
        """Set minimum time before reaching next cool stage (min interstage delay).
        for TH6500WF and TH6250WF thermostats."""
        data = {ATTR_COOL_INTERSTAGE_MIN_DELAY: time}
        _LOGGER.debug("HC set_cool_min_interstage_delay.data = %s", data)
        self.set_device_attributes(device_id, data)

    def set_aux_heat_start_delay(self, device_id: str, time: int):
        """Set minimum time using the heat pump before using the auxiliary heaters.
        for TH6500WF and TH6250WF thermostats."""
        data = {ATTR_AUX_HEAT_START_DELAY: time}
        _LOGGER.debug("HC set_aux_heat_start_delay.data = %s", data)
        self.set_device_attributes(device_id, data)

    def set_device_attributes(self, device_id: str, data: dict[str, Any]):
        """Set devices attributes."""
        increment_request_counter(self.hass)
        result = 1
        while result < 4:
            try:
                resp = requests.put(
                    DEVICE_DATA_URL + device_id + "/attribute",
                    json=data,
                    headers=self._headers,
                    cookies=self._cookies,
                    timeout=self._timeout,
                )
                _LOGGER.debug(
                    "Requests = %s%s%s %s",
                    DEVICE_DATA_URL,
                    device_id,
                    "/attribute",
                    data,
                )
                _LOGGER.debug("Data = %s", data)
                _LOGGER.debug("Requests response = %s", resp.status_code)
                _LOGGER.debug("Json Data received= %s", resp.json())
                _LOGGER.debug("Content = %s", resp.content)
                _LOGGER.debug("Text = %s", resp.text)

                if "error" not in resp.json():
                    break

                result += 1
                _LOGGER.debug(
                    "Service error received: %s, resending requests %s",
                    resp.json(),
                    result,
                )
            except OSError:
                raise PyNeviweb130Error("Cannot set device %s attributes: %s", device_id, data)

    def post_neviweb_status(self, location: int | str, mode: str):
        """Send post requests to Neviweb for global occupancy mode"""
        increment_request_counter(self.hass)
        location = str(location)
        data = {ATTR_MODE: mode}
        try:
            resp = requests.post(
                NEVIWEB_LOCATION + location + "/mode",
                json=data,
                headers=self._headers,
                cookies=self._cookies,
                timeout=self._timeout,
            )

            _LOGGER.debug("Data = %s", data)
            _LOGGER.debug("Requests response = %s", resp.status_code)
            _LOGGER.debug("Json Data received= %s", resp.json())
        except OSError:
            raise PyNeviweb130Error("Cannot post Neviweb: %s", data)
        if "error" in resp.json():
            _LOGGER.debug("Service error received: %s", resp.json())
