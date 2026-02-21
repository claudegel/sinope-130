"""The data update coordinator for neviweb130."""

import logging
from http.cookies import SimpleCookie
from typing import Any, Mapping, Union

import aiohttp
from aiohttp import ClientSession
from homeassistant.components.climate.const import PRESET_AWAY, PRESET_HOME, HVACMode
from homeassistant.components.persistent_notification import DOMAIN as PN_DOMAIN
from homeassistant.core import HomeAssistant
from homeassistant.helpers.update_coordinator import DataUpdateCoordinator

from .const import (
    ATTR_ACCESSORY_TYPE,
    ATTR_AIR_EX_MIN_TIME_ON,
    ATTR_AUX_CYCLE_LENGTH,
    ATTR_AUX_HEAT_MIN_TIME_OFF,
    ATTR_AUX_HEAT_MIN_TIME_ON,
    ATTR_AUX_HEAT_SOURCE_TYPE,
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
    EXPOSED_ATTRIBUTES,
    MODE_EM_HEAT,
    MODE_MANUAL,
    VERSION,
)
from .helpers import (
    async_notify_once_or_update,
    async_notify_throttled,
    async_notify_critical,
    DailyRequestCounter,
    translate_error,
)
from .schema import (
    HA_TO_NEVIWEB_CONTROLLED,
    HA_TO_NEVIWEB_DELAY,
    HA_TO_NEVIWEB_DURATION,
    HA_TO_NEVIWEB_FAN_SPEED,
    HA_TO_NEVIWEB_FAN_SPEED_5,
    HA_TO_NEVIWEB_FLOW,
    HA_TO_NEVIWEB_GAUGE,
    HA_TO_NEVIWEB_HEIGHT,
    HA_TO_NEVIWEB_LEVEL,
    HA_TO_NEVIWEB_MODE,
    HA_TO_NEVIWEB_PERIOD,
    HA_TO_NEVIWEB_SUPPLY,
    HA_TO_NEVIWEB_TEMPERATURE,
    HA_TO_NEVIWEB_TIMER,
    color_to_rgb,
)

_LOGGER = logging.getLogger(__name__)

REQUESTS_TIMEOUT = 30
HOST = "https://neviweb.com"
LOGIN_URL = f"{HOST}/api/login"
LOCATIONS_URL = f"{HOST}/api/locations?account$id="
GATEWAY_DEVICE_URL = f"{HOST}/api/devices?location$id="
DEVICE_DATA_URL = f"{HOST}/api/device/"
NEVIWEB_LOCATION = f"{HOST}/api/location/"
NEVIWEB_WEATHER = f"{HOST}/api/weather?code="


def extract_device_attributes(dev) -> dict:
    return {attr: value for attr in EXPOSED_ATTRIBUTES if (value := getattr(dev, attr, None)) is not None}


def ha_to_neviweb(value: str | None) -> int:
    result = HA_TO_NEVIWEB_PERIOD.get(value or "off", 0)
    if value not in HA_TO_NEVIWEB_PERIOD and value is not None:
        _LOGGER.warning("Unknown HA value for period: %s, fallback to %s", value, result)
    return result


def ha_to_neviweb_controlled(value: str | None) -> str:
    result = HA_TO_NEVIWEB_CONTROLLED.get(value or "unknown", "-")
    if value not in HA_TO_NEVIWEB_CONTROLLED and value is not None:
        _LOGGER.warning("Unknown HA value for controlled device: %s, fallback to %s", value, result)
    return result


def ha_to_neviweb_delay(value: str | None) -> int:
    result = HA_TO_NEVIWEB_DELAY.get(value or "off", 0)
    if value not in HA_TO_NEVIWEB_DELAY and value is not None:
        _LOGGER.warning("Unknown HA value for output delay: %s, fallback to %s", value, result)
    return result


def ha_to_neviweb_duration(value: str | None) -> int:
    result = HA_TO_NEVIWEB_DURATION.get(value or "off", 0)
    if value not in HA_TO_NEVIWEB_DURATION and value is not None:
        _LOGGER.warning("Unknown HA value for output delay: %s, fallback to %s", value, result)
    return result


def ha_to_neviweb_fan_speed(value: str | None, model: int) -> int:
    """Convert HA fan speed value to Neviweb integer code for HP6000WF-xx."""
    if value is None:
        _LOGGER.debug("Fan speed value is None, fallback to 0")
        return 0

    if model == 6813:
        result = HA_TO_NEVIWEB_FAN_SPEED.get(value)
    else:
        result = HA_TO_NEVIWEB_FAN_SPEED_5.get(value)

    if result is None:
        _LOGGER.warning("Unknown HA value for fan speed: %s, fallback to 0", value)
        return 0

    return result


def ha_to_neviweb_flow(value: str | None) -> str:
    result = HA_TO_NEVIWEB_FLOW.get(value or "Noflow", "No flow meter")
    if value not in HA_TO_NEVIWEB_FLOW and value is not None:
        _LOGGER.warning("Unknown HA value for controlled device: %s, fallback to %s", value, result)
    return result


def ha_to_neviweb_gauge(value: str | None) -> int:
    result = HA_TO_NEVIWEB_GAUGE.get(value or "unknown", 0)
    if value not in HA_TO_NEVIWEB_GAUGE and value is not None:
        _LOGGER.warning("Unknown HA value for gauge type: %s, fallback to %s", value, result)
    return result


def ha_to_neviweb_height(value: str | None) -> int:
    result = HA_TO_NEVIWEB_HEIGHT.get(value or "none", 0)
    if value not in HA_TO_NEVIWEB_HEIGHT and value is not None:
        _LOGGER.warning("Unknown HA value for output delay: %s, fallback to %s", value, result)
    return result


def ha_to_neviweb_level(value: str | None) -> int:
    result = HA_TO_NEVIWEB_LEVEL.get(value or "off", 0)
    if value not in HA_TO_NEVIWEB_LEVEL and value is not None:
        _LOGGER.warning("Unknown HA value for gauge type: %s, fallback to %s", value, result)
    return result

def ha_to_neviweb_mode(mode) -> str:
    # For HC thermostat
    if mode == MODE_EM_HEAT:
        return MODE_EM_HEAT
    # others thermostats
    result = HA_TO_NEVIWEB_MODE.get(mode or HVACMode.OFF, "off")
    if mode not in HA_TO_NEVIWEB_MODE and mode is not None:
        _LOGGER.warning("Unknown HA value for heatCoolMode: %s, fallback to %s", mode, result)
    return result

def ha_to_neviweb_supply(value: str | None) -> str:
    result = HA_TO_NEVIWEB_SUPPLY.get(value or "unknown", "-")
    if value not in HA_TO_NEVIWEB_SUPPLY and value is not None:
        _LOGGER.warning("Unknown HA value for controlled device: %s, fallback to %s", value, result)
    return result


def ha_to_neviweb_temperature(value: str | None) -> int:
    result = HA_TO_NEVIWEB_TEMPERATURE.get(value or "off", 0)
    if value not in HA_TO_NEVIWEB_CONTROLLED and value is not None:
        _LOGGER.warning("Unknown HA value for temperature value: %s, fallback to %s", value, result)
    return result


def ha_to_neviweb_timer(value: str | None) -> int:
    result = HA_TO_NEVIWEB_TIMER.get(value or "off", 0)
    if value not in HA_TO_NEVIWEB_TIMER and value is not None:
        _LOGGER.warning("Unknown HA value for timer: %s, fallback to %s", value, result)
    return result


class PyNeviweb130Error(Exception):
    pass


class Neviweb130Client:
    def __init__(
        self,
        hass: HomeAssistant,
        ignore_miwi,
        username: str,
        password: str,
        network: str | None,
        network2: str | None = None,
        network3: str | None = None,
        session_manager=None,
        counter=None,
        timeout=REQUESTS_TIMEOUT,
    ):
        """Initialize the client object."""
        #        self.coordinator = coordinator
        self.hass = hass
        self._email = username
        self._password = password
        self._network_name = network
        self._network_name2 = network2
        self._network_name3 = network3
        self._code: str | None = None
        self._ignore_miwi = ignore_miwi

        # Gateway info
        self._gateway_id = None
        self._gateway_id2 = None
        self._gateway_id3 = None
        self.gateway_data: dict[str, Any] = {}
        self.gateway_data2: dict[str, Any] = {}
        self.gateway_data3: dict[str, Any] = {}

        # Session manager injection
        self._session_manager = session_manager
        self._counter = counter

        self._headers: Mapping[str, str] = {}
        self._account: str | None = None
        self._cookies: SimpleCookie | None = None
        self._timeout = timeout
        self._occupancyMode = None
        self.user = None
        self._response = None

    @property
    async def session(self) -> ClientSession:
        """Return a valid aiohttp session from the session manager."""
        return await self._session_manager.create_session()

    async def async_initialize(self):
        """Asynchronously initialize the client."""
        _LOGGER.debug("Initializing Neviweb130Client...")

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

    async def async_stop(self):
        """Stop the client and close its session."""
        await self._session_manager.close_session()

    async def _increment(self):
        if self._counter is not None:
            await self._counter.async_increment()

    async def async_post_login_page(self):
        """Login to Neviweb."""
        await self._increment()
        session = await self.session

        data = {
            "username": self._email,
            "password": self._password,
            "interface": "neviweb",
            "stayConnected": 1,
        }

        _LOGGER.debug("Sending login request to Neviweb for user %s", self._email)

        try:
            async with session.post(
                LOGIN_URL,
                json=data,
                cookies=self._cookies,
                allow_redirects=False,
                timeout=self._timeout,
            ) as response:
                #                _LOGGER.debug("login status: %s", response.status)
                if response.status != 200:
                    if response.status == 429:
                        _LOGGER.debug(
                            "Login fail status: %s, too many requests, retry later",
                            response.status,
                        )
                    else:
                        _LOGGER.debug("Fail login status: %s", response.status)
                    msg = translate_error(self.hass, "login_failed")
                    raise PyNeviweb130Error(msg)

                raw_cookies = response.cookies
                raw_res = await response.json()
        except aiohttp.ClientError as e:
            msg = translate_error(self.hass, "login_submit_failed")
            raise PyNeviweb130Error(msg) from e

        # Update cookies
        self._cookies = raw_cookies
        data = raw_res
        _LOGGER.debug("Login response: %s", data)

        # Handle errors
        if "error" in data:
            code = data["error"]["code"]

            if code == "ACCSESSEXC":
                msg = translate_error(self.hass, "too_many_sessions", code=data['error']['code'])
                await async_notify_critical(
                    self.hass,
                    msg,
                    title=f"Neviweb130 integration {VERSION}",
                    notification_id="neviweb130_session_error",
                )
            elif code == "USRBADLOGIN":
                msg = translate_error(self.hass, "bad_credentials", code=data['error']['code'])
                await async_notify_critical(
                    self.hass,
                    msg,
                    title=f"Neviweb130 integration {VERSION}",
                    notification_id="neviweb130_session_error",
                )
            return False

        # Success
        self.user = data["user"]
        self._headers = {"Session-Id": data["session"]}
        self._account = str(data["account"]["id"])
        _LOGGER.info("Successfully logged for user %s on account: %s", self._email, self._account)

        return True

    async def async_get_network(self):
        """Get gateway id associated to the desired network."""

        if self._account is None:
            msg = translate_error(self.hass, "account_id_empty")
            raise ConfigEntryAuthFailed(msg)

        await self._increment()
        session = await self.session

        try:
            async with session.get(
                LOCATIONS_URL + self._account,
                headers=self._headers,
                cookies=self._cookies,
                timeout=self._timeout,
            ) as response:

                raw_res = await response.json()
                networks = raw_res

                _LOGGER.info("Number of networks found on Neviweb: %s", len(networks))
                _LOGGER.debug("networks: %s", networks)

                # Auto selection mode
                if self._network_name is None and self._network_name2 is None and self._network_name3 is None:
                    # Use 1st network found, second or third if found
                    self._gateway_id = networks[0]["id"]
                    self._network_name = networks[0]["name"]
                    self._occupancyMode = networks[0]["mode"]
                    self._code = networks[0]["postalCode"]
                    _LOGGER.info("Selecting %s as first network", self._network_name)
                    if len(networks) > 1:
                        self._gateway_id2 = networks[1]["id"]
                        self._network_name2 = networks[1]["name"]
                        self._occupancyMode = networks[1]["mode"]
                        self._code = networks[1]["postalCode"]
                        _LOGGER.info("Selecting %s as second network", self._network_name2)
                        if len(networks) > 2:
                            self._gateway_id3 = networks[2]["id"]
                            self._network_name3 = networks[2]["name"]
                            self._occupancyMode = networks[2]["mode"]
                            self._code = networks[2]["postalCode"]
                            _LOGGER.info("Selecting %s as third network", self._network_name3)

                # Manual selection mode
                else:
                    for network in networks:
                        name = network["name"]

                        # Network 1
                        if self._network_name:
                            if name == self._network_name:
                                self._gateway_id = network["id"]
                                self._occupancyMode = network["mode"]
                                self._code = network["postalCode"]
                                _LOGGER.info(
                                    "Selecting %s network among: %s", name, networks)
                                continue
                            if name.lower() == self._network_name.lower():
                                self._gateway_id = network["id"]
                                self._occupancyMode = network["mode"]
                                self._code = network["postalCode"]
                                _LOGGER.warning(
                                    "Case mismatch for network1 name. Using %s", name
                                )
                                continue

                        # Network 2
                        if self._network_name2:
                            if name == self._network_name2:
                                self._gateway_id2 = network["id"]
                                self._occupancyMode = network["mode"]
                                self._code = network["postalCode"]
                                _LOGGER.info("Selecting %s network among: %s", self._network_name2, networks)
                                continue

                            if name.lower() == self._network_name2.lower():
                                self._gateway_id2 = network["id"]
                                self._occupancyMode = network["mode"]
                                self._code = network["postalCode"]
                                _LOGGER.warning(
                                    "Case mismatch for network2 name. Using %s", name
                                )
                                continue

                        # network 3
                        if self._network_name3:
                            if name == self._network_name3:
                                self._gateway_id3 = network["id"]
                                self._occupancyMode = network["mode"]
                                self._code = network["postalCode"]
                                _LOGGER.info("Selecting %s network among: %s", self._network_name3, networks)
                                continue

                            if name.lower() == self._network_name3.lower():
                                self._gateway_id3 = network["id"]
                                self._occupancyMode = network["mode"]
                                self._code = network["postalCode"]
                                _LOGGER.warning(
                                    "Case mismatch for network3 name. Using %s", name
                                )
                                continue

                    # If nothing matched
                    if (
                        self._gateway_id is None
                        and self._gateway_id2 is None
                        and self._gateway_id3 is None
                    ):
                        _LOGGER.error(
                            "None of the configured network names match discovered networks. "
                            "Please check your configuration."
                        )

                # Update cookies
                self._cookies.update(response.cookies)

        except aiohttp.ClientError as e:
            raise PyNeviweb130Error(translate_error(self.hass, "networks_fetch_failed")) from e

        # Prepare data
        self.gateway_data = raw_res

    async def async_get_gateway_data(self):
        """Get gateway data."""
        await self._increment()
        session = await self.session

        if (
            self._gateway_id is None
            and self._gateway_id2 is None
            and self._gateway_id3 is None
        ):
            msg = translate_error(self.hass, "no_gateway_defined")
            await async_notify_critical(
                self.hass,
                msg,
                title=f"Neviweb130 integration {VERSION}",
                notification_id="neviweb130_session_error",
            )
            return False

        # Fetching gateway
        async def _fetch_gateway_data(gateway_id: str):
            try:
                async with session.get(
                    GATEWAY_DEVICE_URL + str(gateway_id),
                    headers=self._headers,
                    cookies=self._cookies,
                    timeout=self._timeout,
                ) as response:

                    raw = await response.json()
                    _LOGGER.debug("Received gateway data: %s", raw)

                    if "error" in raw and raw["error"]["code"] == "VALINVLD":
                        msg = translate_error(self.hass, "gateway_data_failed")
                        raise PyNeviweb130Error(msg)

                    # Update cookies
                    self._cookies.update(response.cookies)

                    return raw

            except aiohttp.ClientError as e:
                msg = translate_error(self.hass, "gateway_data_failed")
                raise PyNeviweb130Error(msg) from e

        # Fetch gateway 1
        raw_res = await _fetch_gateway_data(self._gateway_id)
        self.gateway_data = raw_res
        _LOGGER.debug("Gateway_data : %s", self.gateway_data)

        # fetch gateway 2
        if self._gateway_id2 is not None:
            raw_res2 = await _fetch_gateway_data(self._gateway_id2)
            self.gateway_data2 = raw_res2
            _LOGGER.debug("Gateway_data2: %s", self.gateway_data2)

        # fetch gateway 3
        if self._gateway_id3 is not None:
            raw_res3 = await _fetch_gateway_data(self._gateway_id3)
            self.gateway_data3 = raw_res3
            _LOGGER.debug("Gateway_data3: %s", self.gateway_data3)

        # Fetch signature gateway 1
        for device in self.gateway_data:
            data = await self.async_get_device_attributes(device["id"], [ATTR_SIGNATURE])
            if ATTR_SIGNATURE in data:
                device[ATTR_SIGNATURE] = data[ATTR_SIGNATURE]

            _LOGGER.debug("Received signature data: %s", data)

            if data[ATTR_SIGNATURE]["protocol"] == "miwi" and not self._ignore_miwi:
                msg = translate_error(self.hass, "ignore_miwi", param="«network»")
                _LOGGER.debug(msg)

        # Fetch signature gateway 2
        if self._gateway_id2 is not None:
            for device in self.gateway_data2:
                data2 = await self.async_get_device_attributes(device["id"], [ATTR_SIGNATURE])
                if ATTR_SIGNATURE in data2:
                    device[ATTR_SIGNATURE] = data2[ATTR_SIGNATURE]

                _LOGGER.debug("Received signature data 2: %s", data2)

                if data2[ATTR_SIGNATURE]["protocol"] == "miwi" and not self._ignore_miwi:
                    msg = translate_error(self.hass, "ignore_miwi", param="«network3»")
                    _LOGGER.debug(msg)

        # Fetching signature gateway 3
        if self._gateway_id3 is not None:
            for device in self.gateway_data3:
                data3 = await self.async_get_device_attributes(device["id"], [ATTR_SIGNATURE])
                if ATTR_SIGNATURE in data3:
                    device[ATTR_SIGNATURE] = data3[ATTR_SIGNATURE]

                _LOGGER.debug("Received signature data 3: %s", data3)

                if data3[ATTR_SIGNATURE]["protocol"] == "miwi" and not self._ignore_miwi:
                    msg = translate_error(self.hass, "ignore_miwi", param="«network3»")
                    _LOGGER.debug(msg)

        _LOGGER.info("Loaded gateway %s with %s devices", self._gateway_id, len(self.gateway_data))
        _LOGGER.info("Loaded gateway2 %s with %s devices", self._gateway_id2, len(self.gateway_data2))
        _LOGGER.info("Loaded gateway3 %s with %s devices", self._gateway_id3, len(self.gateway_data3))

        return True

    async def async_get_device_attributes(self, device_id: str, attributes):
        """Get device attributes."""
        await self._increment()
        session = await self.session


        url = (
            DEVICE_DATA_URL
            + str(device_id)
            + "/attribute?attributes="
            + ",".join(attributes)
        )
        _LOGGER.debug("Fetching attributes for device %s with URL: %s", device_id, url)

        try:
            async with session.get(
                url,
                headers=self._headers,
                cookies=self._cookies,
                timeout=self._timeout,
            ) as response:

                raw = await response.json()
                # _LOGGER.debug("Received devices data: %s", raw_res)

                # Update cookies
                self._cookies.update(response.cookies)

                # Handle errors
                if "error" in raw:
                    code = raw["error"].get("code")
                    _LOGGER.debug("Error response for device %s: %s", device_id, raw)

                    if code == "USRSESSEXP":
                        msg = translate_error(self.hass, "usr_session")
                        _LOGGER.error(msg)

                    return raw

#                _LOGGER.debug("Attributes for device %s: %s", device_id, raw)
                missing = [a for a in attributes if a not in raw]
                if missing:
                    _LOGGER.warning(
                        "Device %s did not return all requested attributes (%s). Missing: %s",
                        device_id,
                        attributes,
                        missing,
                    )

                return raw

        except aiohttp.ClientError as e:
            raise PyNeviweb130Error(
                f"Cannot get device attributes for device {device_id}"
            ) from e

    async def async_get_device_status(self, device_id: str):
        """Get device status for the GT130."""
        await self._increment()
        session = await self.session

        url = DEVICE_DATA_URL + str(device_id) + "/status"
        _LOGGER.debug("Fetching status for device %s with URL: %s", device_id, url)

        try:
            async with session.get(
                url,
                headers=self._headers,
                cookies=self._cookies,
                timeout=self._timeout,
            ) as response:

                raw = await response.json()

                # Update cookies
                self._cookies.update(response.cookies)

        except aiohttp.ClientError as e:
            raise PyNeviweb130Error(
                f"Cannot get device status for device {device_id}"
            ) from e

        # Handle error
        if "error" in raw:
            code = raw["error"].get("code")
            _LOGGER.debug("Error response for device %s: %s", device_id, raw)

            if code == "USRSESSEXP":
                msg = translate_error(self.hass, "usr_session")
                _LOGGER.error(msg)

        _LOGGER.debug("Received device %s status: %s", device_id, raw)

        return raw

    async def async_get_neviweb_status(self, location):
        """Get neviweb occupancyMode status."""
        await self._increment()
        session = await self.session

        url = NEVIWEB_LOCATION + str(location) + "/notifications"
        _LOGGER.debug("Fetching Neviweb status with URL: %s", url)

        try:
            async with session.get(
                url,
                headers=self._headers,
                cookies=self._cookies,
                timeout=self._timeout,
            ) as response:

                raw = await response.json()

                # Update cookies
                self._cookies.update(response.cookies)

        except aiohttp.ClientError as e:
            raise PyNeviweb130Error("Cannot get neviweb status") from e

        # Handle error
        if "error" in raw:
            code = raw["error"].get("code")
            _LOGGER.debug("Error response for Neviweb status: %s", raw)

            if code == "USRSESSEXP":
                msg = translate_error(self.hass, "location_status", param=location)
                _LOGGER.error(msg)

        _LOGGER.debug("Received Neviweb status for location %s: %s", str(location), raw)

        return raw

    async def async_get_device_alert(self, device_id: str):
        """Get device alert for Sedna valve."""
        await self._increment()
        session = await self.session

        url = DEVICE_DATA_URL + str(device_id) + "/alert"
        _LOGGER.debug("Fetching device %s alert with URL: %s", device_id, url)

        try:
            async with session.get(
                url,
                headers=self._headers,
                cookies=self._cookies,
                timeout=self._timeout,
            ) as response:

                raw = await response.json()

                # Update cookies
                self._cookies.update(response.cookies)

        except aiohttp.ClientError as e:
            msg = translate_error(self.hass, "device_alert", id=device_id)
            raise PyNeviweb130Error(msg) from e

        # Handle error
        if "error" in raw:
            code = raw["error"].get("code")
            _LOGGER.debug("Error response for device %s alert: %s", device_id, raw)

            if code == "USRSESSEXP":
                msg = translate_error(self.hass, "usr_session")
                _LOGGER.error(msg)

        _LOGGER.debug("Received device %s alert: %s", device_id, raw)

        return raw

    async def async_get_device_monthly_stats(self, device_id: str, HC: bool):
        """Get device power consumption (in Wh) for the last 24 months."""
        await self._increment()
        session = await self.session
        if HC:
            url = DEVICE_DATA_URL + str(device_id) + "/energy/monthly"
        else:
            url = DEVICE_DATA_URL + str(device_id) + "/consumption/monthly"
        _LOGGER.debug("Fetching device %s monthly stats with URL: %s", device_id, url)

        try:
            async with session.get(
                url,
                headers=self._headers,
                cookies=self._cookies,
                timeout=self._timeout,
            ) as response:

                raw = await response.json()
                _LOGGER.debug("Raw monthly stats response for device %s: %s", device_id, raw)

                # Update cookies
                self._cookies.update(response.cookies)

        except aiohttp.ClientError as e:
            msg = translate_error(self.hass, "energy_stat", param="monthly", id=device_id)
            raise PyNeviweb130Error(msg) from e

        # Handle error
        if "error" in raw:
            code = raw["error"].get("code")
            _LOGGER.debug("Error response for device %s monthly stats: %s", device_id, raw)

            if code == "USRSESSEXP":
                _LOGGER.error(
                    "Session expired while fetching monthly stats for device %s. "
                    "Set scan_interval < 10 minutes to avoid session expiration.",
                    device_id,
                )

            return None

        # Normal case
        if HC:
            return raw
        else:
            if "history" in raw:
                _LOGGER.debug("Received monthly stats for device %s: %s", device_id, raw["history"])
                return raw["history"]

        # Unexpected structure
        _LOGGER.debug(
            "Unexpected response format for monthly stats of device %s: %s",
            device_id,
            raw,
        )
        return None

    async def async_get_device_daily_stats(self, device_id: str, HC: bool):
        """Get device power consumption (in Wh) for the last 30 days."""
        await self._increment()
        session = await self.session
        if HC:
            url = DEVICE_DATA_URL + str(device_id) + "/energy/daily"
        else:
            url = DEVICE_DATA_URL + str(device_id) + "/consumption/daily"
        _LOGGER.debug("Fetching device %s daily stats with URL: %s", device_id, url)

        try:
            async with session.get(
                url,
                headers=self._headers,
                cookies=self._cookies,
                timeout=self._timeout,
            ) as response:

                raw = await response.json()
                _LOGGER.debug("Raw daily stats response for device %s: %s", device_id, raw)

                # Update cookies
                self._cookies.update(response.cookies)

        except aiohttp.ClientError as e:
            msg = translate_error(self.hass, "energy_stat", param="daily", id=device_id)
            raise PyNeviweb130Error(msg) from e

        # Handle error
        if "error" in raw:
            code = raw["error"].get("code")
            _LOGGER.debug("Error response for device %s daily stats: %s", device_id, raw)

            if code == "USRSESSEXP":
                _LOGGER.error(
                    "Session expired while fetching daily stats for device %s. "
                    "Set scan_interval < 10 minutes to avoid session expiration.",
                    device_id,
                )

            return None

        # Normal case
        if HC:
            return raw
        else:
            if "history" in raw:
                _LOGGER.debug("Received daily stats for device %s: %s", device_id, raw["history"])
                return raw["history"]

        # Unexpected structure
        _LOGGER.debug(
            "Unexpected response format for daily stats of device %s: %s",
            device_id,
            raw,
        )
        return None

    async def async_get_device_hourly_stats(self, device_id: str, HC: bool):
        """Get device power consumption (in Wh) for the last 24 hours."""
        await self._increment()
        session = await self.session
        if HC:
            url = DEVICE_DATA_URL + str(device_id) + "/energy/hourly"
        else:
            url = DEVICE_DATA_URL + str(device_id) + "/consumption/hourly"
        _LOGGER.debug("Fetching device %s hourly stats with URL: %s", device_id, url)

        try:
            async with session.get(
                url,
                headers=self._headers,
                cookies=self._cookies,
                timeout=self._timeout,
            ) as response:
                raw = await response.json()
                _LOGGER.debug("Raw hourly stats response for device %s: %s", device_id, raw)

                # Update cookies
                self._cookies.update(response.cookies)

        except aiohttp.ClientError as e:
            msg = translate_error(self.hass, "energy_stat", param="hourly", id=device_id)
            raise PyNeviweb130Error(msg) from e

        # Handle error
        if "error" in raw:
            code = raw["error"].get("code")
            _LOGGER.debug("Error response for device %s hourly stats: %s", device_id, raw)

            if code == "USRSESSEXP":
                msg = translate_error(self.hass, "usr_session")
                _LOGGER.error(msg)

            return None

        # Normal case
        if HC:
            return raw
        else:
            if "history" in raw:
                _LOGGER.debug("Received hourly stats for device %s: %s", device_id, raw["history"])
                return raw["history"]

        # Unexpected structure
        _LOGGER.debug(
            "Unexpected response format for hourly stats of device %s: %s",
            device_id,
            raw,
        )
        return None

    async def async_get_weather(self):
        """Get Neviweb weather for my location."""
        await self._increment()
        if self._code is None:
            raise ValueError("self._code is None")

        session = await self.session

        url = NEVIWEB_WEATHER + self._code
        _LOGGER.debug("Fetching Neviweb weather data with URL: %s", url)

        try:
            async with session.get(
                url,
                headers=self._headers,
                cookies=self._cookies,
                timeout=self._timeout,
            ) as response:

                raw = await response.json()
                _LOGGER.debug("Raw weather data response from Neviweb for code %s: %s", self._code, raw)

                # Update cookies
                self._cookies.update(response.cookies)

        except aiohttp.ClientError as e:
            msg = translate_error(self.hass, "weather_data", code=self._code)
            raise PyNeviweb130Error(msg) from e

        # Handle error
        if "error" in raw:
            code = raw["error"].get("code")
            _LOGGER.debug("Error response for weather data from Neviweb: %s", raw)

            if code == "USRSESSEXP":
                msg = translate_error(self.hass, "usr_session")
                _LOGGER.error(msg)

            return None

        # Normal case
        _LOGGER.debug("Received Neviweb weather data for code %s: %s", self._code, raw)
        return raw

    async def async_get_device_sensor_error(self, device_id: str):
        """Get device error code status."""
        await self._increment()
        session = await self.session

        url = DEVICE_DATA_URL + str(device_id) + "/attribute?attributes=errorCodeSet1"
        _LOGGER.debug("Fetching device %s sensor error with URL: %s", device_id, url)

        try:
            async with session.get(
                url,
                headers=self._headers,
                cookies=self._cookies,
                timeout=self._timeout,
            ) as response:

                raw = await response.json()
                _LOGGER.debug("Raw sensor error response for device %s: %s", device_id, raw)

                # Update cookies
                self._cookies.update(response.cookies)

        except aiohttp.ClientError as e:
            raise PyNeviweb130Error(
                f"Cannot get device error code status for device {device_id}"
            ) from e

        # Handle error
        if "error" in raw:
            code = raw["error"].get("code")
            _LOGGER.debug("Error response for device %s for sensor error: %s", device_id, raw)

            if code == "USRSESSEXP":
                msg = translate_error(self.hass, "usr_session")
                _LOGGER.error(msg)

            return None

        # Normal case
        if "errorCodeSet1" in raw:
            _LOGGER.debug("Received sensor error code for device %s: %s", device_id, raw)
            return raw

        # Unexpected structure
        _LOGGER.debug(
            "Unexpected sensor error response format for device %s: %s",
            device_id,
            raw,
        )
        return None

    async def async_set_brightness(self, device_id: str, brightness) -> bool:
        """Set device brightness."""
        data = {ATTR_INTENSITY: brightness}
        return await self.async_set_device_attributes(device_id, data)

    async def async_set_onoff(self, device_id: str, onoff) -> bool:
        """Set device onOff state."""
        data = {ATTR_ONOFF: onoff}
        return await self.async_set_device_attributes(device_id, data)

    async def async_set_onoff2(self, device_id: str, onoff) -> bool:
        """Set device onOff state for MC3100ZB."""
        data = {ATTR_ONOFF2: onoff}
        return await self.async_set_device_attributes(device_id, data)

    async def async_set_light_onoff(self, device_id: str, onoff, brightness) -> bool:
        """Set light device onOff state."""
        data = {ATTR_ONOFF: onoff, ATTR_INTENSITY: brightness}
        return await self.async_set_device_attributes(device_id, data)

    async def async_set_valve_onoff(self, device_id: str, onoff) -> bool:
        """Set sedna valve onOff state."""
        data = {ATTR_MOTOR_TARGET: onoff}
        return await self.async_set_device_attributes(device_id, data)

    async def async_set_mode(self, device_id: str, mode) -> bool:
        """Set device operation mode."""
        data = {ATTR_POWER_MODE: mode}
        return await self.async_set_device_attributes(device_id, data)

    async def async_set_setpoint_mode(self, device_id: str, mode, wifi, HC) -> bool:
        """Set thermostat operation mode."""
        """Work differently for Wi-Fi and Zigbee devices."""
        if wifi:
            if HC:
                data = {ATTR_HEAT_COOL: ha_to_neviweb_mode(mode)}
            else:
                if mode in [HVACMode.HEAT, MODE_MANUAL]:
                    mode = MODE_MANUAL
                data = {ATTR_SETPOINT_MODE: mode}
        else:
            data = {ATTR_SYSTEM_MODE: mode}
        return await self.async_set_device_attributes(device_id, data)

    async def async_set_occupancy_mode(self, device_id: str, mode, wifi) -> bool:
        """Set thermostat preset mode."""
        """Work differently for Wi-Fi and Zigbee devices."""
        if wifi:
            if mode in [PRESET_AWAY, PRESET_HOME]:
                data = {ATTR_OCCUPANCY: mode}
            else:
                return None
        else:
            data = {ATTR_SYSTEM_MODE: mode}
        return await self.async_set_device_attributes(device_id, data)

    async def async_set_temperature(self, device_id: str, temperature) -> bool:
        """Set device heating temperature target."""
        data = {ATTR_ROOM_SETPOINT: temperature}
        return await self.async_set_device_attributes(device_id, data)

    async def async_set_cool_temperature(self, device_id: str, temperature) -> bool:
        """Set device cooling temperature target."""
        data = {ATTR_COOL_SETPOINT: temperature}
        return await self.async_set_device_attributes(device_id, data)

    async def async_set_room_setpoint_away(self, device_id: str, temperature) -> bool:
        """Set device away heating temperature target for all Wi-Fi thermostats."""
        data = {ATTR_ROOM_SETPOINT_AWAY: temperature}
        return await self.async_set_device_attributes(device_id, data)

    async def async_set_cool_setpoint_away(self, device_id: str, temperature, HC) -> bool:
        """Set device away cooling temperature target for TH6500WF and TH6250WF."""
        if HC:
            data = {ATTR_COOL_SETPOINT_AWAY: temperature}
            return await self.async_set_device_attributes(device_id, data)
        else:
            await async_notify_once_or_update(
                self.hass,
                "Warning: Service set_cool_setpoint_away is only for TH6500WF or TH6250WF thermostats.",
                title=f"Neviweb130 integration {VERSION}",
                notification_id="neviweb130_service_error",
            )
            return False

    async def async_set_humidity(self, device_id: str, humidity) -> bool:
        """Set device humidity target."""
        data = {ATTR_HUMID_SETPOINT: humidity}
        return await self.async_set_device_attributes(device_id, data)

    async def async_set_accessory_type(self, device_id: str, accessory_type) -> bool:
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
        return await self.async_set_device_attributes(device_id, data)

    async def async_set_schedule_mode(self, device_id: str, mode, HC) -> bool:
        """Set schedule mode for TH6500WF and TH6250WF."""
        if HC:
            data = {ATTR_SETPOINT_MODE: mode}
            return await self.async_set_device_attributes(device_id, data)
        else:
            msg = translate_error(self.hass, "heat_cool_warning", code="set_schedule_mode")
            await async_notify_once_or_update(
                self.hass,
                msg,
                title=f"Neviweb130 integration {VERSION}",
                notification_id="neviweb130_service_error",
            )
            return False

    async def async_set_heatcool_delta(self, device_id: str, level, HC) -> bool:
        """Set schedule mode for TH6500WF and TH6250WF."""
        if HC:
            data = {ATTR_HEATCOOL_SETPOINT_MIN_DELTA: level}
            return await self.async_set_device_attributes(device_id, data)
        else:
            msg = translate_error(self.hass, "heat_cool_warning", code="set_heatcool_min_delta")
            await async_notify_once_or_update(
                self.hass,
                msg,
                title=f"Neviweb130 integration {VERSION}",
                notification_id="neviweb130_service_error",
            )
            return False

    async def async_set_fan_filter_reminder(self, device_id: str, month, HC) -> bool:
        """Set schedule mode for TH6500WF and TH6250WF."""
        if HC:
            month_val = month * 720
            data = {ATTR_FAN_FILTER_REMAIN: month_val}
            return await self.async_set_device_attributes(device_id, data)
        else:
            msg = translate_error(self.hass, "heat_cool_warning", code="set_fan_filter_reminder")
            await async_notify_once_or_update(
                self.hass,
                msg,
                title=f"Neviweb130 integration {VERSION}",
                notification_id="neviweb130_service_error",
            )
            return False

    async def async_set_temperature_offset(self, device_id: str, temp, HC) -> bool:
        """Set schedule mode for TH6500WF and TH6250WF."""
        if HC:
            data = {ATTR_TEMP_OFFSET_HEAT: temp}
            return await self.async_set_device_attributes(device_id, data)
        else:
            msg = translate_error(self.hass, "heat_cool_warning", code="set_temperature_offset")
            await async_notify_once_or_update(
                self.hass,
                msg,
                title=f"Neviweb130 integration {VERSION}",
                notification_id="neviweb130_service_error",
            )
            return False

    async def async_set_humidity_offset(self, device_id: str, offset, HC) -> bool:
        """Set humidity setpoint offset for TH6500WF and TH6250WF."""
        if HC:
            data = {ATTR_HUMIDITY_SETPOINT_OFFSET: offset}
            return await self.async_set_device_attributes(device_id, data)
        else:
            msg = translate_error(self.hass, "heat_cool_warning", code="set_humidity_offset")
            await async_notify_once_or_update(
                self.hass,
                msg,
                title=f"Neviweb130 integration {VERSION}",
                notification_id="neviweb130_service_error",
            )
            return False

    async def async_set_humidity_mode(self, device_id: str, mode, HC) -> bool:
        """Set humidity setpoint mode for TH6500WF and TH6250WF."""
        if HC:
            data = {ATTR_HUMIDITY_SETPOINT_MODE: mode}
            return await self.async_set_device_attributes(device_id, data)
        else:
            msg = translate_error(self.hass, "heat_cool_warning", code="set_humidity_mode")
            await async_notify_once_or_update(
                self.hass,
                msg,
                title=f"Neviweb130 integration {VERSION}",
                notification_id="neviweb130_service_error",
            )
            return False

    async def async_set_air_ex_min_time_on(self, device_id: str, time, HC) -> bool:
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
            return await self.async_set_device_attributes(device_id, data)
        else:
            msg = translate_error(self.hass, "heat_cool_warning", code="set_air_ex_time_on")
            await async_notify_once_or_update(
                self.hass,
                msg,
                title=f"Neviweb130 integration {VERSION}",
                notification_id="neviweb130_service_error",
            )
            return False

    async def async_set_backlight(self, device_id: str, level: str, wifi: bool) -> bool:
        """Set backlight intensity when idle, on or auto."""
        """Work differently for Wi-Fi and Zigbee devices."""
        if wifi:
            match level:
                case "on":
                    level = "alwaysOn"
                case "auto":
                    level = "onUserAction"
            data = {ATTR_BACKLIGHT_AUTO_DIM: level}
        else:
            match level:
                case "on":
                    level = "always"
                case "auto":
                    level = "onActive"
            data = {ATTR_BACKLIGHT: level}
        _LOGGER.debug("backlight.data = %s", data)
        return await self.async_set_device_attributes(device_id, data)

    async def async_set_second_display(self, device_id: str, display) -> bool:
        """Set device second display for outside temperature or setpoint temperature."""
        data = {ATTR_DISPLAY2: display}
        _LOGGER.debug("display.data = %s", data)
        return await self.async_set_device_attributes(device_id, data)

    async def async_set_keypad_lock(self, device_id: str, lock: str | None, wifi: bool) -> bool:
        """Set device keyboard locked/unlocked."""
        if wifi:
            match lock:
                case "locked":
                    lock = "lock"
                case "unlocked":
                    lock = "unlock"
                case "partiallyLocked":
                    lock = "partialLock"
                case _:
                    msg = translate_error(self.hass, "Invalid_lock_value", lock=lock, model=self._model)
                    raise ValueError(msg)
            data = {ATTR_WIFI_KEYPAD: lock}
        else:
            match lock:
                case "tamper protection":
                    lock = "partiallyLocked"
            data = {ATTR_KEYPAD: lock}
        _LOGGER.debug("lock.data = %s", data)
        return await self.async_set_device_attributes(device_id, data)

    async def async_set_phase(self, device_id: str, phase: str | None) -> bool:
        """Set device phase control mode."""
        data: dict[str, Any] = {ATTR_PHASE_CONTROL: phase}
        _LOGGER.debug("phase.data = %s", data)
        return await self.async_set_device_attributes(device_id, data)

    async def async_set_double_up(self, device_id: str, double) -> bool:
        """Set device key double up action."""
        data = {ATTR_KEY_DOUBLE_UP: double}
        _LOGGER.debug("double_up.data = %s", data)
        return await self.async_set_device_attributes(device_id, data)

    async def async_set_timer(self, device_id: str, time: str | None) -> bool:
        """Set device auto off for timer on light, switch and multi controller."""
        seconds = ha_to_neviweb_timer(time)
        data: dict[str, Any] = {ATTR_TIMER: seconds}
        _LOGGER.debug("timer.data = %s", data)
        return await self.async_set_device_attributes(device_id, data)

    async def async_set_timer2(self, device_id: str, time: str | None) -> bool:
        """Set device auto off for timer2 on multi controller."""
        seconds = ha_to_neviweb_timer(time)
        data: dict[str, Any] = {ATTR_TIMER2: seconds}
        _LOGGER.debug("timer2.data = %s", data)
        return await self.async_set_device_attributes(device_id, data)

    async def async_set_time_format(self, device_id: str, time) -> bool:
        """Set device time format 12h or 24h."""
        data = {ATTR_TIME_FORMAT: time}
        _LOGGER.debug("time.data = %s", data)
        return await self.async_set_device_attributes(device_id, data)

    async def async_set_temperature_format(self, device_id: str, deg) -> bool:
        """Set device temperature format: celsius or fahrenheit."""
        data = {ATTR_TEMP: deg}
        _LOGGER.debug("temperature.data = %s", data)
        return await self.async_set_device_attributes(device_id, data)

    async def async_set_floor_air_limit(self, device_id: str, status, temp) -> bool:
        """Set device maximum air temperature limit."""
        if temp == 0:
            temp = None
        data = {ATTR_FLOOR_AIR_LIMIT: {"status": status, "value": temp}}
        _LOGGER.debug("floorairlimit.data = %s", data)
        return await self.async_set_device_attributes(device_id, data)

    async def async_set_early_start(self, device_id: str, start) -> bool:
        """Set early start on/off for Wi-Fi thermostats."""
        data = {ATTR_EARLY_START: start}
        _LOGGER.debug("early_start.data = %s", data)
        return await self.async_set_device_attributes(device_id, data)

    async def async_set_air_floor_mode(self, device_id: str, mode) -> bool:
        """Switch temperature control between floor and ambient sensor."""
        data = {ATTR_FLOOR_MODE: mode}
        _LOGGER.debug("floor_mode.data = %s", data)
        return await self.async_set_device_attributes(device_id, data)

    async def async_set_setpoint_min(self, device_id: str, temp) -> bool:
        """Set device setpoint minimum temperature."""
        data = {ATTR_ROOM_SETPOINT_MIN: temp}
        _LOGGER.debug("setpointMin.data = %s", data)
        return await self.async_set_device_attributes(device_id, data)

    async def async_set_setpoint_max(self, device_id: str, temp) -> bool:
        """Set device setpoint maximum temperature."""
        data = {ATTR_ROOM_SETPOINT_MAX: temp}
        _LOGGER.debug("setpointMax.data = %s", data)
        return await self.async_set_device_attributes(device_id, data)

    async def async_set_cool_setpoint_min(self, device_id: str, temp) -> bool:
        """Set device cooling setpoint minimum temperature."""
        data = {ATTR_COOL_SETPOINT_MIN: temp}
        _LOGGER.debug("CoolsetpointMin.data = %s", data)
        return await self.async_set_device_attributes(device_id, data)

    async def async_set_cool_setpoint_max(self, device_id: str, temp) -> bool:
        """Set device cooling setpoint maximum temperature."""
        data = {ATTR_COOL_SETPOINT_MAX: temp}
        _LOGGER.debug("CoolsetpointMax.data = %s", data)
        return await self.async_set_device_attributes(device_id, data)

    async def async_set_aux_cycle_output(self, device_id: str, val: str | None, wifi: bool) -> bool:
        """Set low voltage thermostat aux cycle status and length."""
        length = ha_to_neviweb(val)
        if wifi:
            data: dict[str, Any] = {ATTR_AUX_CYCLE_LENGTH: length}
        else:
            data: dict[str, Any] = {ATTR_CYCLE_OUTPUT2: {"status": "on" if length > 0 else "off", "value": length}}
        _LOGGER.debug("auxCycleoutput.data = %s", data)
        return await self.async_set_device_attributes(device_id, data)

    async def async_set_cycle_output(self, device_id: str, val: str | None, is_hc: bool) -> bool:
        """Set low voltage thermostat main cycle length."""
        length = ha_to_neviweb(val)
        if is_hc:
            datadict[str, Any] = {ATTR_COOL_CYCLE_LENGTH: val}
            _LOGGER.debug("coolCycleLength.data = %s", data)
        else:
            data: dict[str, Any] = {ATTR_CYCLE_LENGTH: length}
            _LOGGER.debug("Cycleoutput.data = %s", data)
        return await self.async_set_device_attributes(device_id, data)

    async def async_set_tank_size(self, device_id: str, val) -> bool:
        """Set water heater tank size for RM3500ZB."""
        data = {ATTR_TANK_SIZE: val}
        _LOGGER.debug("TankSize.data = %s", data)
        return await self.async_set_device_attributes(device_id, data)

    async def async_set_remaining_time(self, device_id: str, time) -> bool:
        """Activate or deactivate calypso for time period."""
        data = {ATTR_COLD_LOAD_PICKUP_REMAIN_TIME: time}
        _LOGGER.debug("RemainingTime.data = %s", data)
        return await self.async_set_device_attributes(device_id, data)

    async def async_set_sensor_type(self, device_id: str, val) -> bool:
        """Set floor sensor type 10k, 12k."""
        data = {
            ATTR_FLOOR_SENSOR: val,
            ATTR_FLOOR_OUTPUT2: {"status": "off", "value": 0},
        }
        _LOGGER.debug("sensor.data = %s", data)
        return await self.async_set_device_attributes(device_id, data)

    async def async_set_low_temp_protection(self, device_id: str, val: str | None) -> bool:
        """Set water heater temperature protection for RM3500ZB."""
        value = ha_to_neviweb_temperature(val)
        data: dict[str, Any] = {ATTR_WATER_TEMP_MIN: value}
        _LOGGER.debug("Low temp protection.data = %s", data)
        return await self.async_set_device_attributes(device_id, data)

    async def async_set_controlled_device(self, device_id: str, val: str | None) -> bool:
        """Set device name controlled by RM3250ZB and RM3250WF."""
        name_id = ha_to_neviweb_controlled(val)
        data: dict[str, Any] = {ATTR_CONTROLLED_DEVICE: name_id}
        _LOGGER.debug("ControlledDevice.data = %s", data)
        return await self.async_set_device_attributes(device_id, data)

    async def async_set_em_heat(self, device_id: str, heat: str, low: str, sec: str | None) -> bool:
        """Set floor, low voltage, Wi-Fi floor and low voltage Wi-Fi thermostats auxiliary heat slave/off or on/off."""
        length = ha_to_neviweb(sec)
        if low == "voltage":
            data: dict[str, dict[str, str | int]] = {
                ATTR_CYCLE_OUTPUT2: {"status": heat, "value": length}
            }
        elif low == "wifi":
            data: dict[str, int] = {ATTR_AUX_CYCLE_LENGTH: length}
        else:
            data: dict[str, str] = {ATTR_FLOOR_AUX: heat}
        _LOGGER.debug("em_heat.data = %s", data)
        return await self.async_set_device_attributes(device_id, data)

    async def async_set_floor_limit(self, device_id: str, level: int, low: str, wifi: bool) -> bool:
        """Set floor setpoint limit low and high for Zigbee and Wi-Fi thermostats. (0 = off)."""
        data: dict[str, dict[str, None | str | int]]
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
        return await self.async_set_device_attributes(device_id, data)

    async def async_set_pump_protection(self, device_id: str, status: str, wifi: bool) -> bool:
        """Set low voltage thermostat pump protection status."""
        """Work differently for Wi-Fi and Zigbee devices."""
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
        return await self.async_set_device_attributes(device_id, data)

    async def async_set_flow_meter_model(self, device_id: str, model: str | None) -> bool:
        """Set flow meter model connected to the Sedna valve 2e gen."""
        data: dict[str, Union[dict[str, int], bool]]
        model_val = ha_to_neviweb_flow(model)
        if model_val == "FS4221":
            data = {
                ATTR_FLOW_METER_CONFIG: {
                    "multiplier": 9887,
                    "offset": 87372,
                    "divisor": 1,
                },
                ATTR_FLOW_ENABLED: True,
            }
        elif model_val == "FS4220":
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
        return await self.async_set_device_attributes(device_id, data)

    async def async_set_flow_meter_delay(self, device_id: str, delay: str | None) -> bool:
        """Set flow meter delay before alarm is activated on Sedna valve 2e gen."""
        delay_val = ha_to_neviweb_duration(delay)
        data: dict[str, Any] = {ATTR_FLOW_ALARM1_PERIOD: delay_val}
        _LOGGER.debug("Flowmeter delay.data = %s", data)
        return await self.async_set_device_attributes(device_id, data)

    async def async_set_flow_meter_options(self, device_id: str, action: bool, alarm: bool) -> bool:
        """Set valve action with optional alert."""
        if not alarm and not action:
            length = 0
            threshold = 0
        else:
            length = 60
            threshold = 1
        data: dict[str, dict[str, bool] | int] = {
            ATTR_FLOW_ALARM1_OPTION: {
                "triggerAlarm": alarm,
                "closeValve": action,
            },
            ATTR_FLOW_ALARM1_LENGTH: length,
            ATTR_FLOW_THRESHOLD: threshold,
        }
        _LOGGER.debug("Flowmeter options.data = %s", data)
        return await self.async_set_device_attributes(device_id, data)

    async def async_set_flow_alarm_timer(self, device_id: str, timer: str | None) -> bool:
        """Set flowmeter alarm action disabled timer, for valves with flowmeter."""
        timer_val = ha_to_neviweb_duration(timer)
        data: dict[str, Any] = {ATTR_FLOW_ALARM_TIMER: timer_val}
        _LOGGER.debug("Flowmeter alarm disable timer.data = %s", data)
        return await self.async_set_device_attributes(device_id, data)

    async def async_set_led_indicator(self, device_id: str, state: int, color: str) -> bool:
        """Set device led indicator color for on and off state."""
        color = color_to_rgb(color)
        r, g, b = map(int, color.split(","))
        if state == 1:
            data = {
                ATTR_LED_ON_COLOR: {
                    "red": r,
                    "green": g,
                    "blue": b,
                }
            }
            _LOGGER.debug("led on color.data = %s", data)
        else:
            data = {
                ATTR_LED_OFF_COLOR: {
                    "red": r,
                    "green": g,
                    "blue": b,
                }
            }
            _LOGGER.debug("led off color.data = %s", data)
        return await self.async_set_device_attributes(device_id, data)

    async def async_set_led_on_intensity(self, device_id: str, intensity) -> bool:
        """Set device led indicator intensity for on state."""
        data = {ATTR_LED_ON_INTENSITY: intensity}
        _LOGGER.debug("led on intensity.data on = %s", data)
        return await self.async_set_device_attributes(device_id, data)

    async def async_set_led_off_intensity(self, device_id: str, intensity) -> bool:
        """Set device led indicator intensity for off state."""
        data = {ATTR_LED_OFF_INTENSITY: intensity}
        _LOGGER.debug("led off intensity.data on = %s", data)
        return await self.async_set_device_attributes(device_id, data)

    async def async_set_light_min_intensity(self, device_id: str, intensity) -> bool:
        """Set dimmer light minimum intensity from 1 to 3000."""
        data = {ATTR_INTENSITY_MIN: intensity}
        _LOGGER.debug("led min intensity.data on = %s", data)
        return await self.async_set_device_attributes(device_id, data)

    async def async_set_wattage(self, device_id: str, watt) -> bool:
        """Set light and dimmer watt load."""
        data = {ATTR_LIGHT_WATTAGE: {"status": "on", "value": watt}}
        _LOGGER.debug("wattage.data = %s", data)
        return await self.async_set_device_attributes(device_id, data)

    async def async_set_auxiliary_load(self, device_id: str, status, load) -> bool:
        """Set auxiliary output load in watt."""
        data = {ATTR_FLOOR_OUTPUT2: {"status": status, "value": load}}
        _LOGGER.debug("auxiliary_load.data = %s", data)
        return await self.async_set_device_attributes(device_id, data)

    async def async_set_valve_alert(self, device_id: str, batt: bool | None, ZB_valve: bool, mesh: bool) -> bool:
        """Set Sedna valve battery alert on/off."""
        if ZB_valve or mesh:
            if batt:
                data: dict[str, Any] = {ATTR_BATT_ALERT: 1}
            else:
                data: dict[str, Any] = {ATTR_BATT_ALERT: 0}
        else:
            data: dict[str, Any] = {ATTR_BATT_ALERT: batt}
        _LOGGER.debug("valve.data = %s", data)
        return await self.async_set_device_attributes(device_id, data)

    async def async_set_valve_temp_alert(self, device_id: str, temp: bool | None) -> bool:
        """Set Sedna valve temperature alert on/off."""
        data: dict[str, Any] = {ATTR_TEMP_ALERT: temp}
        _LOGGER.debug("valve temp alert.data = %s", data)
        return await self.async_set_device_attributes(device_id, data)

    async def async_set_switch_temp_alert(self, device_id: str, temp: int | None) -> bool:
        """Set Sedna valve temperature alert on/off."""
        data: dict[str, Any] = {ATTR_TEMP_ALERT: temp}
        _LOGGER.debug("switch temp alert.data = %s", data)
        return await self.async_set_device_attributes(device_id, data)

    async def async_set_battery_type(self, device_id: str, batt: str) -> bool:
        """Set water leak sensor battery type, lithium or alkaline."""
        data: dict[str, Any] = {ATTR_BATTERY_TYPE: batt}
        _LOGGER.debug("battery_type.data = %s", data)
        return await self.async_set_device_attributes(device_id, data)

    async def async_set_sensor_leak_alert(self, device_id: str, leak: bool | None) -> bool:
        """Set leak detector water leak alert action."""
        if leak is None:
            _LOGGER.warning("Leak alert value is None for device %s", device_id)
            return False
        data: dict[str, Any] = {ATTR_BATT_ALERT: leak}
        _LOGGER.debug("leak.data = %s", data)
        return await self.async_set_device_attributes(device_id, data)

    async def async_set_sensor_temp_alert(self, device_id: str, temp: bool | None) -> bool:
        """Set leak detector low temperature alert action."""
        if temp is None:
            _LOGGER.warning("Temperature alert value is None for device %s", device_id)
            return False
        data: dict[str, Any] = {ATTR_BATT_ALERT: temp}
        _LOGGER.debug("leak.data = %s", data)
        return await self.async_set_device_attributes(device_id, data)

    async def async_set_sensor_closure_action(self, device_id: str, close: str | None) -> bool:
        """Set leak detector connected to Sedna valve, closure action in case of leak alert."""
        if close is None:
            _LOGGER.warning("Closure action value is None for device %s", device_id)
            return False
        data: dict[str, Any] = {ATTR_BATT_ALERT: close}
        _LOGGER.debug("leak.data = %s", data)
        return await self.async_set_device_attributes(device_id, data)

    async def async_set_load_dr_options(self, device_id: str, onoff, optout, dr) -> bool:
        """Set load controller Eco Sinope attributes."""
        data = {
            ATTR_DRSTATUS: {
                "drActive": dr,
                "optOut": optout,
                "onOff": onoff,
            }
        }
        _LOGGER.debug("Load.DR.options = %s", data)
        return await self.async_set_device_attributes(device_id, data)

    async def async_set_hvac_dr_options(
        self, device_id: str, *,dr=None, optout=None, setpoint=None, aux_conf=None, fan_speed_conf=None
    ) -> bool:
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
            return await self.async_set_device_attributes(device_id, data)

        if aux_conf is not None:
            data = {ATTR_DR_AUX_CONF: "activated" if aux_conf == "on" else "deactivated"}
            _LOGGER.debug("hvac.DR.options = %s", data)
            return await self.async_set_device_attributes(device_id, data)

        if fan_speed_conf is not None:
            data = {
                # Not a typo: Disabled is really sending "on" (allow fan to be always on when the optim is disabled)
                ATTR_DR_FAN_SPEED_CONF: "auto" if fan_speed_conf == "on" else "on"
            }
            _LOGGER.debug("hvac.DR.options = %s", data)
            return await self.async_set_device_attributes(device_id, data)

    async def async_set_hvac_dr_setpoint(self, device_id: str, status, val) -> bool:
        """Set load controller Eco Sinope attributes."""
        data = {ATTR_DRSETPOINT: {"status": status, "value": val}}
        _LOGGER.debug("hvac.DR.setpoint = %s", data)
        return await self.async_set_device_attributes(device_id, data)

    async def async_set_control_onoff(self, device_id: str, number, status) -> bool:
        """Set valve controller onOff or OnOff2 status, on or off."""
        if number == 1:
            data = {ATTR_ONOFF: status}
        else:
            data = {ATTR_ONOFF2: status}
        _LOGGER.debug("control.valve.data = %s", data)
        return await self.async_set_device_attributes(device_id, data)

    async def async_set_tank_type(self, device_id: str, tank: str | None) -> bool:
        """Set tank type for LM4110-ZB sensor."""
        data: dict[str, Any] = {ATTR_TANK_TYPE: tank}
        _LOGGER.debug("tank_type.data = %s", data)
        return await self.async_set_device_attributes(device_id, data)

    async def async_set_gauge_type(self, device_id: str, gauge: str | None) -> bool:
        """Set gauge type for LM4110-ZB sensor on propane tank."""
        gauge_type = ha_to_neviweb_gauge(gauge)
        data: dict[str, Any] = {ATTR_GAUGE_TYPE: gauge_type}
        _LOGGER.debug("gauge_type.data = %s", data)
        return await self.async_set_device_attributes(device_id, data)

    async def async_set_aux_heating_source(self, device_id: str, equip: str) -> bool:
        """Set auxiliary heating source for TH6500WF and TH6250WF."""
        data: dict[str, Any] = {ATTR_AUX_HEAT_SOURCE_TYPE: equip}
        _LOGGER.debug("aux_heating_source.data = %s", data)
        return  await self.async_set_device_attributes(device_id, data)

    async def async_set_low_fuel_alert(self, device_id: str, alert: str | None) -> bool:
        """Set low fuel alert limit for LM4110-ZB sensor."""
        level = ha_to_neviweb_level(alert)
        data: dict[str, Any] = {ATTR_FUEL_PERCENT_ALERT: level}
        _LOGGER.debug("low_fuel_alert.data = %s", data)
        return await self.async_set_device_attributes(device_id, data)

    async def async_set_refuel_alert(self, device_id: str, alert: bool) -> bool:
        """Set refuel alert for LM4110-ZB sensor."""
        data: dict[str, Any] = {ATTR_REFUEL: alert}
        _LOGGER.debug("Refuel_alert.data = %s", data)
        return await self.async_set_device_attributes(device_id, data)

    async def async_set_tank_height(self, device_id: str, height: str | None) -> bool:
        """Set tank height in inch for LM4110-ZB sensor."""
        high = ha_to_neviweb_height(height)
        data: dict[str, Any] = {ATTR_TANK_HEIGHT: high}
        _LOGGER.debug("tank_height.data = %s", data)
        return await self.async_set_device_attributes(device_id, data)

    async def async_set_fuel_alert(self, device_id: str, fuel: bool | None) -> bool:
        """Set low fuel alert limit for LM4110-ZB sensor."""
        data: dict[str, Any] = {ATTR_FUEL_ALERT: fuel}
        _LOGGER.debug("Fuel_alert.data = %s", data)
        return await self.async_set_device_attributes(device_id, data)

    async def async_set_battery_alert(self, device_id: str, batt: bool | None) -> bool:
        """Set low fuel alert limit for LM4110-ZB sensor."""
        if batt is None:
            _LOGGER.warning("Battery alert value is None for device %s", device_id)
            return False
        data: dict[str, Any] = {ATTR_BATT_ALERT: batt}
        _LOGGER.debug("battery_alert.data = %s", data)
        return await self.async_set_device_attributes(device_id, data)

    async def async_set_power_supply(self, device_id: str, supply: str | None) -> bool:
        """Set power supply for Sedna valve."""
        supply_val = ha_to_neviweb_supply(supply)
        data: dict[str, Any] = {ATTR_POWER_SUPPLY: supply_val}
        _LOGGER.debug("power_supply.data = %s", data)
        return await self.async_set_device_attributes(device_id, data)

    async def async_set_on_off_input_delay(self, device_id: str, delay: str | None, onoff: str, input_number: int) -> bool:
        """Set input 1 or 2 on/off delay in seconds."""
        data: dict[str, Any]
        length = ha_to_neviweb_delay(delay)
        if input_number == 1:
            match onoff:
                case "on":
                    data = {ATTR_INPUT_1_ON_DELAY: length}
                case _:
                    data = {ATTR_INPUT_1_OFF_DELAY: length}
        else:
            match onoff:
                case "on":
                    data = {ATTR_INPUT_2_ON_DELAY: length}
                case _:
                    data = {ATTR_INPUT_2_OFF_DELAY: length}
        _LOGGER.debug("input_delay.data = %s", data)
        return await self.async_set_device_attributes(device_id, data)

    async def async_set_input_output_names(self, device_id: str, in1: str, in2: str, out1: str, out2: str) -> bool:
        """Set names for input 1 and 2, output 1 and 2 for MC3100ZB device."""
        data: dict[str, Any] = {}
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
        return await self.async_set_device_attributes(device_id, data)

    async def async_set_heat_pump_limit(self, device_id: str, temp: int) -> bool:
        """Set minimum temperature for heat pump operation."""
        data: dict[str, Any] = {ATTR_BALANCE_PT: temp}
        _LOGGER.debug("Heat pump limit value.data = %s", data)
        return await self.async_set_device_attributes(device_id, data)

    async def async_set_heat_lockout(self, device_id: str, temp: int, G2: bool) -> bool:
        """Set maximum outside temperature limit to allow heating device operation."""
        if G2:
            data = {ATTR_HEAT_LOCKOUT_TEMP: temp}
        else:
            data: dict[str, Any] = {ATTR_HEAT_LOCK_TEMP: temp}
        _LOGGER.debug("Heat lockout limit value.data = %s", data)
        return await self.async_set_device_attributes(device_id, data)

    async def async_set_cool_lockout(self, device_id: str, temp: int) -> bool:
        """Set minimum outside temperature limit to allow cooling devices operation."""
        data: dict[str, Any] = {ATTR_COOL_LOCK_TEMP: temp}
        _LOGGER.debug("Cool lockout limit value.data = %s", data)
        return await self.async_set_device_attributes(device_id, data)

    async def async_set_hp_display(self, device_id: str, display: str) -> bool:
        """Set display on/off for heat pump."""
        data: dict[str, Any] = {ATTR_DISPLAY_CONF: display}
        _LOGGER.debug("Display config value.data = %s", data)
        return await self.async_set_device_attributes(device_id, data)

    async def async_set_hp_sound(self, device_id: str, sound: str) -> bool:
        """Set display on/off for heat pump."""
        data: dict[str, Any] = {ATTR_SOUND_CONF: sound}
        _LOGGER.debug("Sound config value.data = %s", data)
        return await self.async_set_device_attributes(device_id, data)

    async def async_set_swing_horizontal(self, device_id: str, swing: str) -> bool:
        """Set horizontal fan swing action for heat pump."""
        data: dict[str, Any] = {ATTR_FAN_SWING_HORIZ: swing}
        _LOGGER.debug("Fan horizontal swing value.data = %s", data)
        return await self.async_set_device_attributes(device_id, data)

    async def async_set_swing_vertical(self, device_id: str, swing: str) -> bool:
        """Set vertical fan swing action for heat pump."""
        data: dict[str, Any] = {ATTR_FAN_SWING_VERT: swing}
        _LOGGER.debug("Fan vertical swing value.data = %s", data)
        return await self.async_set_device_attributes(device_id, data)

    async def async_set_fan_mode(self, device_id: str, speed: str | None, model: int) -> bool:
        """Set fan speed (mode) for heat pump."""

        if model == 6813 or model == 6814:
            speed_val = ha_to_neviweb_fan_speed(speed, model)
        else:
            speed_val = speed

        data: dict[str, Any] = {ATTR_FAN_SPEED: speed_val}

        _LOGGER.debug("Fan speed value.data = %s", data)
        return await self.async_set_device_attributes(device_id, data)

    async def async_set_hc_display(self, device_id: str, display: str) -> bool:
        """Set device second display for outside temperature or setpoint temperature for TH1134ZB-HC."""
        data: dict[str, Any] = {ATTR_DISPLAY2: display}
        _LOGGER.debug("Hc display.data = %s", data)
        return await self.async_set_device_attributes(device_id, data)

    async def async_set_language(self, device_id: str, lang: str) -> bool:
        """Set display language for TH1134ZB-HC."""
        data: dict[str, Any] = {ATTR_LANGUAGE: lang}
        _LOGGER.debug("Hc language.data = %s", data)
        return await self.async_set_device_attributes(device_id, data)

    async def async_set_heat_dissipation_time(self, device_id: str, time: int, HC: bool) -> bool:
        """Set heating purge time for TH6500WF and TH6250WF thermostats."""
        if HC:
            data: dict[str, Any] = {ATTR_HEAT_PURGE_TIME: time}
            _LOGGER.debug("HC heat_dissipation_time.data = %s", data)
            return await self.async_set_device_attributes(device_id, data)
        else:
            msg = translate_error(self.hass, "heat_cool_warning", code="set_heat_dissipation_time")
            await async_notify_once_or_update(
                self.hass,
                msg,
                title=f"Neviweb130 integration {VERSION}",
                notification_id="neviweb130_service_error",
            )
            return False

    async def async_set_cool_dissipation_time(self, device_id: str, time: int, HC: bool) -> bool:
        """Set cooling purge time for TH6500WF and TH6250WF thermostats."""
        if HC:
            data: dict[str, Any] = {ATTR_COOL_PURGE_TIME: time}
            _LOGGER.debug("HC cool_dissipation_time.data = %s", data)
            return await self.async_set_device_attributes(device_id, data)
        else:
            msg = translate_error(self.hass, "heat_cool_warning", code="set_cool_dissipation_time")
            await async_notify_once_or_update(
                self.hass,
                msg,
                title=f"Neviweb130 integration {VERSION}",
                notification_id="neviweb130_service_error",
            )
            return False

    async def async_set_reversing_valve_polarity(self, device_id: str, polarity: str) -> bool:
        """Set minimum time the heater is on before letting be off again (run-on time).
        for TH6500WF and TH6250WF thermostats."""
        data: dict[str, Any] = {ATTR_REVERSING_VALVE_POLARITY: polarity}
        _LOGGER.debug("HC set_reversing_valve_polarity.data = %s", data)
        return await self.async_set_device_attributes(device_id, data)

    async def async_set_heat_min_time_on(self, device_id: str, time: int) -> bool:
        """Set minimum time the heater is on before letting be off again (run-on time).
        for TH6500WF and TH6250WF thermostats."""
        data: dict[str, Any] = {ATTR_HEAT_MIN_TIME_ON: time}
        _LOGGER.debug("HC heat_min_time_on.data = %s", data)
        return await self.async_set_device_attributes(device_id, data)

    async def async_set_heat_min_time_off(self, device_id: str, time: int) -> bool:
        """Set minimum time the heater is off before letting it be on again (cooldown time).
        for TH6500WF and TH6250WF thermostats."""
        data: dict[str, Any] = {ATTR_HEAT_MIN_TIME_OFF: time}
        _LOGGER.debug("HC heat_min_time_off.data = %s", data)
        return await self.async_set_device_attributes(device_id, data)

    async def async_set_cool_min_time_on(self, device_id: str, time: int) -> bool:
        """Set minimum time the cooler is on before letting be off again (run-on time).
        for TH6500WF and TH6250WF thermostats."""
        data: dict[str, Any] = {ATTR_COOL_MIN_TIME_ON: time}
        _LOGGER.debug("HC cool_min_time_on.data = %s", data)
        return await self.async_set_device_attributes(device_id, data)

    async def async_set_cool_min_time_off(self, device_id: str, time: int) -> bool:
        """Set minimum time the cooler is off before letting it be on again (cooldown time).
        for TH6500WF and TH6250WF thermostats."""
        data: dict[str, Any] = {ATTR_COOL_MIN_TIME_OFF: time}
        _LOGGER.debug("HC cool_min_time_off.data = %s", data)
        return await self.async_set_device_attributes(device_id, data)

    async def async_set_aux_heat_min_time_on(self, device_id: str, time: int) -> bool:
        """Set minimum time the auxiliary heater is on before letting be off again (run-on time).
        for TH6500WF and TH6250WF thermostats."""
        data: dict[str, Any] = {ATTR_AUX_HEAT_MIN_TIME_ON: time}
        _LOGGER.debug("HC aux_heat_min_time_on.data = %s", data)
        return await self.async_set_device_attributes(device_id, data)

    async def async_set_aux_heat_min_time_off(self, device_id: str, time: int) -> bool:
        """Set minimum time the auxiliary heater is off before letting it be on again (cooldown time).
        for TH6500WF and TH6250WF thermostats."""
        data: dict[str, Any] = {ATTR_AUX_HEAT_MIN_TIME_OFF: time}
        _LOGGER.debug("HC aux_heat_min_time_off.data = %s", data)
        return await self.async_set_device_attributes(device_id, data)

    async def async_set_heat_interstage_delay(self, device_id: str, time: int) -> bool:
        """Set total time before reaching last heat stage (interstage delay).
        for TH6500WF and TH6250WF thermostats."""
        data: dict[str, Any] = {ATTR_HEAT_INTERSTAGE_DELAY: time}
        _LOGGER.debug("HC set_heat_interstage_delay.data = %s", data)
        return await self.async_set_device_attributes(device_id, data)

    async def async_set_aux_interstage_delay(self, device_id: str, time: int) -> bool:
        """Set total time before reaching last auxiliary heat stage (interstage delay).
        for TH6500WF and TH6250WF thermostats."""
        data: dict[str, Any] = {ATTR_AUX_INTERSTAGE_DELAY: time}
        _LOGGER.debug("HC set_aux_interstage_delay.data = %s", data)
        return await self.async_set_device_attributes(device_id, data)

    async def async_set_cool_interstage_delay(self, device_id: str, time: int) -> bool:
        """Set total time before reaching last cool stage (interstage delay).
        for TH6500WF and TH6250WF thermostats."""
        data: dict[str, Any] = {ATTR_COOL_INTERSTAGE_DELAY: time}
        _LOGGER.debug("HC set_cool_interstage_delay.data = %s", data)
        return await self.async_set_device_attributes(device_id, data)

    async def async_set_heat_interstage_min_delay(self, device_id: str, time: int) -> bool:
        """Set minimum time before reaching next heat stage (min interstage delay).
        for TH6500WF and TH6250WF thermostats."""
        data: dict[str, Any] = {ATTR_HEAT_INTERSTAGE_MIN_DELAY: time}
        _LOGGER.debug("HC set_heat_min_interstage_delay.data = %s", data)
        return await self.async_set_device_attributes(device_id, data)

    async def async_set_aux_interstage_min_delay(self, device_id: str, time: int) -> bool:
        """Set minimum time before reaching next auxiliary stage (min interstage delay).
        for TH6500WF and TH6250WF thermostats."""
        data: dict[str, Any] = {ATTR_AUX_INTERSTAGE_MIN_DELAY: time}
        _LOGGER.debug("HC set_aux_min_interstage_delay.data = %s", data)
        return await self.async_set_device_attributes(device_id, data)

    async def async_set_cool_interstage_min_delay(self, device_id: str, time: int) -> bool:
        """Set minimum time before reaching next cool stage (min interstage delay).
        for TH6500WF and TH6250WF thermostats."""
        data: dict[str, Any] = {ATTR_COOL_INTERSTAGE_MIN_DELAY: time}
        _LOGGER.debug("HC set_cool_min_interstage_delay.data = %s", data)
        return await self.async_set_device_attributes(device_id, data)

    async def async_set_device_attributes(self, device_id: str, data: dict[str, Any]) -> bool:
        """Set devices attributes and return True if successful."""
        await self._increment()
        session = await self.session

        url = DEVICE_DATA_URL + str(device_id) + "/attribute"
        _LOGGER.debug("sending device %s attributes with URL: %s", device_id, url)

        attempts = 0
        resp: dict[str, Any] = {}

        while attempts < 3:
            try:
                async with session.put(
                    url,
                    json=data,
                    headers=self._headers,
                    cookies=self._cookies,
                    timeout=self._timeout,
                ) as response:

                    resp = await response.json()
                    _LOGGER.debug("Data = %s", data)
                    _LOGGER.debug("Request response = %s", response.status)
                    _LOGGER.debug("Json Data received= %s", resp)

                    # Update cookies
                    self._cookies.update(response.cookies)

                    # Success case
                    if response.status == 200 and "error" not in resp:
                        _LOGGER.debug("Device %s attributes successfully updated.", device_id)
                        return True

            except aiohttp.ClientError as e:
                msg = translate_error(self.hass, "set_attribute", id=device_id, data=data)
                raise PyNeviweb130Error(msg) from e

            # Handle API error
            if "error" in resp:
                code = resp["error"].get("code")
                _LOGGER.debug("Error response for device %s attribute update: %s", device_id, resp)

                if code == "USRSESSEXP":
                    msg = translate_error(self.hass, "usr_session")
                    _LOGGER.error(msg)
                    return False

            attempts += 1
            _LOGGER.debug("Retrying device %s attribute update (attempt %s/3)", device_id, attempts)

        # All attempts failed
        _LOGGER.debug("Failed to update attributes for device %s after 3 attempts.", device_id)
        return False

    async def async_post_neviweb_status(self, location: int | str, mode: str) -> bool:
        """Send post requests to Neviweb for global occupancy mode"""
        await self._increment()
        session = await self.session

        url = NEVIWEB_LOCATION + str(location) + "/mode"
        _LOGGER.debug("Setting Neviweb status for location %s with URL: %s", location, url)

        resp: dict[str, Any] = {}
        data = {ATTR_MODE: mode}

        try:
            async with session.post(
                url,
                json=data,
                headers=self._headers,
                cookies=self._cookies,
                timeout=self._timeout,
            ) as response:

                resp = await response.json()
                _LOGGER.debug("Data = %s", data)
                _LOGGER.debug("Requests response = %s", response.status)
                _LOGGER.debug("Json Data received= %s", resp)

                # Update cookies
                self._cookies.update(response.cookies)

                # Success case
                if response.status == 200 and "error" not in resp:
                    _LOGGER.debug("Neviweb status successfully updated for location %s.", location)
                    return True

        except aiohttp.ClientError as e:
            msg = translate_error(self.hass, "neviweb_status", location=location, data=data)
            raise PyNeviweb130Error(msg) from e

        # Handle API error
        if "error" in resp:
            code = resp["error"].get("code")
            _LOGGER.debug("Error response for Neviweb location %s status update: %s", location, resp)

            if code == "USRSESSEXP":
                _LOGGER.error(
                    "Session expired while setting Neviweb status for location %s. "
                    "Set scan_interval < 10 minutes to avoid session expiration.",
                    location,
                )
                return False

        # All failed
        _LOGGER.debug("Failed to update Neviweb status for location %s.", location)
        return False

# create_session = Neviweb130Client.create_session


class Neviweb130Coordinator(DataUpdateCoordinator):
    def __init__(self, hass: HomeAssistant, client: Neviweb130Client, scan_interval):
        """Initialize the Neviweb130Coordinator."""

        _LOGGER.debug("Coordinator scan interval = %s", scan_interval)
        super().__init__(
            hass,
            _LOGGER,
            name="neviweb130",
            update_method=self._async_update_data,
            update_interval=scan_interval,
        )
        self.client = client
        self._devices: list = []  # list of devices objects

        _LOGGER.debug("Coordinator instance in coordinator.py: %s", self)

    async def _async_update_data(self) -> dict:
        """Call async_update() on each device and return a dict {id: device}."""
        _LOGGER.debug("Number of devices to update : %d", len(self._devices))
        result = {}
        for dev in self._devices:
            # _LOGGER.debug("Thermostat attrs: %s", dir(dev))
            # _LOGGER.debug("Thermostat __dict__: %s", vars(dev))
            await dev.async_update()
            device_id = str(getattr(dev, "id", None) or getattr(dev, "unique_id", None))
            if not device_id:
                _LOGGER.error("No ID found for %s", dev)
                continue
            # Collect attributes you want to expose
            result[device_id] = extract_device_attributes(dev)

        return result

    def register_device(self, device):
        """Register a device to be managed by the coordinator."""
        if device not in self._devices:
            self._devices.append(device)

    async def async_initialize(self):
        """Initialize the coordinator."""
        await self.client.async_initialize()
        await self.async_refresh()

    async def stop(self):
        _LOGGER.info("Stopping Neviweb130 Coordinator")
        await self.client.async_stop()
        _LOGGER.info("All aiohttp.ClientSession instances closed")


async def async_setup_coordinator(hass: HomeAssistant, client: Neviweb130Client, scan_interval):
    coordinator = Neviweb130Coordinator(hass, client, scan_interval)
    await coordinator.async_initialize()
    return coordinator
