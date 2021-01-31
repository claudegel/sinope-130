"""
Support for Neviweb thermostat connected to GT130 ZigBee.
model 1123 = thermostat TH1123ZB 3000W
model 1124 = thermostat TH1124ZB 4000W
model 737 = thermostat TH1300ZB 3600W (floor)
model 7373 = thermostat TH1500ZB double pole thermostat
model 7372 = thermostat TH1400ZB low voltage
model 1124 = thermostat OTH4000-ZB Ouellet
model 737 = thermostat OTH3600-GA-ZB Ouellet

Support for Neviweb wifi thermostats
model 1510 = thermostat TH1123WF 3000W (wifi)
model 1510 = thermostat TH1124WF 4000W (wifi)
model 738 = thermostat TH1300WF 3600W and TH1310WF (wifi floor)
model ???? = thermostat TH1400WF low voltage (wifi)

For more details about this platform, please refer to the documentation at
https://www.sinopetech.com/en/support/#api
"""

import logging

import voluptuous as vol
import time

import custom_components.neviweb130 as neviweb130
from . import (SCAN_INTERVAL)
from homeassistant.components.climate import ClimateEntity
from homeassistant.components.climate.const import (
    HVAC_MODE_HEAT,
    HVAC_MODE_OFF,
    HVAC_MODE_AUTO,
    SUPPORT_TARGET_TEMPERATURE,
    SUPPORT_PRESET_MODE,
    PRESET_AWAY,
    PRESET_NONE,
    CURRENT_HVAC_HEAT,
    CURRENT_HVAC_IDLE,
    CURRENT_HVAC_OFF,
)
from homeassistant.const import (
    ATTR_ENTITY_ID,
    DEVICE_CLASS_TEMPERATURE,
    TEMP_CELSIUS,
    TEMP_FAHRENHEIT,
    ATTR_TEMPERATURE,
)

from homeassistant.helpers import (
    config_validation as cv,
    discovery,
    service,
    entity_platform,
    entity_component,
    entity_registry,
    device_registry,
)

from homeassistant.helpers.typing import HomeAssistantType

from datetime import timedelta
from homeassistant.helpers.event import track_time_interval
from .const import (
    DOMAIN,
    ATTR_SETPOINT_MODE,
    ATTR_ROOM_SETPOINT,
    ATTR_OUTPUT_PERCENT_DISPLAY,
    ATTR_ROOM_TEMPERATURE,
    ATTR_ROOM_SETPOINT_MIN,
    ATTR_ROOM_SETPOINT_MAX,
    ATTR_WATTAGE,
    ATTR_GFCI_STATUS,
    ATTR_FLOOR_MODE,
    ATTR_OCCUPANCY,
    ATTR_FLOOR_AUX,
    ATTR_FLOOR_OUTPUT2,
    ATTR_FLOOR_MAX,
    ATTR_KEYPAD,
    ATTR_BACKLIGHT,
    ATTR_TIME,
    ATTR_TEMP,
    ATTR_WIFI_FLOOR_OUTPUT1,
    ATTR_WIFI_WATTAGE,
    ATTR_WIFI,
    ATTR_WIFI_DISPLAY2,
    ATTR_WIFI_KEYPAD,
    ATTR_FLOOR_AIR_LIMIT,
    MODE_AUTO,
    MODE_AUTO_BYPASS,
    MODE_MANUAL,
    MODE_OFF,
    MODE_AWAY,
    SERVICE_SET_CLIMATE_KEYPAD_LOCK,
    SERVICE_SET_SECOND_DISPLAY,
    SERVICE_SET_BACKLIGHT,
    SERVICE_SET_TIME_FORMAT,
    SERVICE_SET_TEMPERATURE_FORMAT,
    SERVICE_SET_SETPOINT_MAX,
    SERVICE_SET_SETPOINT_MIN,
    SERVICE_SET_FLOOR_AIR_LIMIT,
)

_LOGGER = logging.getLogger(__name__)

SUPPORT_FLAGS = (SUPPORT_TARGET_TEMPERATURE | SUPPORT_PRESET_MODE)

DEFAULT_NAME = "neviweb130 climate"

UPDATE_ATTRIBUTES = [
    ATTR_ROOM_SETPOINT,
    ATTR_OUTPUT_PERCENT_DISPLAY,
    ATTR_ROOM_TEMPERATURE,
    ATTR_ROOM_SETPOINT_MIN,
    ATTR_ROOM_SETPOINT_MAX,
    ATTR_TIME,
    ATTR_TEMP,
]

SUPPORTED_HVAC_MODES = [
    HVAC_MODE_OFF,
    HVAC_MODE_AUTO,
    HVAC_MODE_HEAT,
]

PRESET_BYPASS = 'temporary'
PRESET_MODES = [
    PRESET_NONE,
    PRESET_AWAY,
    PRESET_BYPASS,
]

DEVICE_MODEL_LOW = [7372]
DEVICE_MODEL_FLOOR = [737]
DEVICE_MODEL_WIFI_FLOOR = [738]
DEVICE_MODEL_WIFI = [1510]
DEVICE_MODEL_HEAT = [1123, 1124, 7373]
IMPLEMENTED_DEVICE_MODEL = DEVICE_MODEL_HEAT + DEVICE_MODEL_FLOOR + DEVICE_MODEL_LOW + DEVICE_MODEL_WIFI_FLOOR + DEVICE_MODEL_WIFI

SET_SECOND_DISPLAY_SCHEMA = vol.Schema(
    {
         vol.Required(ATTR_ENTITY_ID): cv.entity_id,
         vol.Required(ATTR_WIFI_DISPLAY2): cv.string,
    }
)

SET_BACKLIGHT_SCHEMA = vol.Schema(
    {
         vol.Required(ATTR_ENTITY_ID): cv.entity_id,
         vol.Required(ATTR_BACKLIGHT): cv.string,
    }
)

SET_CLIMATE_KEYPAD_LOCK_SCHEMA = vol.Schema(
    {
         vol.Required(ATTR_ENTITY_ID): cv.entity_id,
         vol.Required(ATTR_KEYPAD): cv.string,
    }
)

SET_TIME_FORMAT_SCHEMA = vol.Schema(
    {
         vol.Required(ATTR_ENTITY_ID): cv.entity_id,
         vol.Required(ATTR_TIME): vol.All(
             vol.Coerce(int), vol.Range(min=12, max=24)
         ),
    }
)

SET_TEMPERATURE_FORMAT_SCHEMA = vol.Schema(
    {
         vol.Required(ATTR_ENTITY_ID): cv.entity_id,
         vol.Required(ATTR_TEMP): cv.string,
    }
)

SET_SETPOINT_MAX_SCHEMA = vol.Schema(
    {
         vol.Required(ATTR_ENTITY_ID): cv.entity_id,
         vol.Required(ATTR_ROOM_SETPOINT_MAX): vol.All(
             vol.Coerce(float), vol.Range(min=8, max=36)
         ),
    }
)

SET_SETPOINT_MIN_SCHEMA = vol.Schema(
    {
         vol.Required(ATTR_ENTITY_ID): cv.entity_id,
         vol.Required(ATTR_ROOM_SETPOINT_MIN): vol.All(
             vol.Coerce(float), vol.Range(min=5, max=26)
         ),
    }
)

SET_FLOOR_AIR_LIMIT_SCHEMA = vol.Schema(
    {
         vol.Required(ATTR_ENTITY_ID): cv.entity_id,
         vol.Required(ATTR_FLOOR_AIR_LIMIT): vol.All(
             vol.Coerce(float), vol.Range(min=0, max=36)
         ),
    }
)

async def async_setup_platform(
    hass,
    config,
    async_add_entities,
    discovery_info=None,
):
    """Set up the neviweb130 thermostats."""
    data = hass.data[DOMAIN]

    entities = []
    for device_info in data.neviweb130_client.gateway_data:
        if "signature" in device_info and \
            "model" in device_info["signature"] and \
            device_info["signature"]["model"] in IMPLEMENTED_DEVICE_MODEL:
            device_name = "{} {}".format(DEFAULT_NAME, device_info["name"])
            entities.append(Neviweb130Thermostat(data, device_info, device_name))

    async_add_entities(entities, True)

    def set_second_display_service(service):
        """Set to outside or setpoint temperature display for wifi thermostats"""
        entity_id = service.data[ATTR_ENTITY_ID]
        value = {}
        for thermostat in entities:
            if thermostat.entity_id == entity_id:
                value = {"id": thermostat.unique_id, "display": service.data[ATTR_WIFI_DISPLAY2]}
                thermostat.set_second_display(value)
                thermostat.schedule_update_ha_state(True)
                break

    def set_backlight_service(service):
        """Set backlight always on or auto"""
        entity_id = service.data[ATTR_ENTITY_ID]
        value = {}
        for thermostat in entities:
            if thermostat.entity_id == entity_id:
                value = {"id": thermostat.unique_id, "level": service.data[ATTR_BACKLIGHT]}
                thermostat.set_backlight(value)
                thermostat.schedule_update_ha_state(True)
                break

    def set_climate_keypad_lock_service(service):
        """ lock/unlock keypad device"""
        entity_id = service.data[ATTR_ENTITY_ID]
        value = {}
        for thermostat in entities:
            if thermostat.entity_id == entity_id:
                value = {"id": thermostat.unique_id, "lock": service.data[ATTR_KEYPAD]}
                thermostat.set_keypad_lock(value)
                thermostat.schedule_update_ha_state(True)
                break

    def set_time_format_service(service):
        """ set time format 12h or 24h"""
        entity_id = service.data[ATTR_ENTITY_ID]
        value = {}
        for thermostat in entities:
            if thermostat.entity_id == entity_id:
                value = {"id": thermostat.unique_id, "time": service.data[ATTR_TIME]}
                thermostat.set_time_format(value)
                thermostat.schedule_update_ha_state(True)
                break

    def set_temperature_format_service(service):
        """ set temperature format, celsius or fahrenheit"""
        entity_id = service.data[ATTR_ENTITY_ID]
        value = {}
        for thermostat in entities:
            if thermostat.entity_id == entity_id:
                value = {"id": thermostat.unique_id, "temp": service.data[ATTR_TEMP]}
                thermostat.set_temperature_format(value)
                thermostat.schedule_update_ha_state(True)
                break

    def set_setpoint_max_service(service):
        """ set maximum setpoint for device"""
        entity_id = service.data[ATTR_ENTITY_ID]
        value = {}
        for thermostat in entities:
            if thermostat.entity_id == entity_id:
                value = {"id": thermostat.unique_id, "temp": service.data[ATTR_ROOM_SETPOINT_MAX]}
                thermostat.set_setpoint_max(value)
                thermostat.schedule_update_ha_state(True)
                break

    def set_setpoint_min_service(service):
        """ set minimum setpoint for device"""
        entity_id = service.data[ATTR_ENTITY_ID]
        value = {}
        for thermostat in entities:
            if thermostat.entity_id == entity_id:
                value = {"id": thermostat.unique_id, "temp": service.data[ATTR_ROOM_SETPOINT_MIN]}
                thermostat.set_setpoint_min(value)
                thermostat.schedule_update_ha_state(True)
                break

    def set_floor_air_limit_service(service):
        """ set minimum setpoint for device"""
        entity_id = service.data[ATTR_ENTITY_ID]
        value = {}
        for thermostat in entities:
            if thermostat.entity_id == entity_id:
                value = {"id": thermostat.unique_id, "temp": service.data[ATTR_FLOOR_AIR_LIMIT]}
                thermostat.set_floor_air_limit(value)
                thermostat.schedule_update_ha_state(True)
                break

    hass.services.async_register(
        DOMAIN,
        SERVICE_SET_SECOND_DISPLAY,
        set_second_display_service,
        schema=SET_SECOND_DISPLAY_SCHEMA,
    )

    hass.services.async_register(
        DOMAIN,
        SERVICE_SET_BACKLIGHT,
        set_backlight_service,
        schema=SET_BACKLIGHT_SCHEMA,
    )

    hass.services.async_register(
        DOMAIN,
        SERVICE_SET_CLIMATE_KEYPAD_LOCK,
        set_climate_keypad_lock_service,
        schema=SET_CLIMATE_KEYPAD_LOCK_SCHEMA,
    )

    hass.services.async_register(
        DOMAIN,
        SERVICE_SET_TIME_FORMAT,
        set_time_format_service,
        schema=SET_TIME_FORMAT_SCHEMA,
    )

    hass.services.async_register(
        DOMAIN,
        SERVICE_SET_TEMPERATURE_FORMAT,
        set_temperature_format_service,
        schema=SET_TEMPERATURE_FORMAT_SCHEMA,
    )

    hass.services.async_register(
        DOMAIN,
        SERVICE_SET_SETPOINT_MAX,
        set_setpoint_max_service,
        schema=SET_SETPOINT_MAX_SCHEMA,
    )

    hass.services.async_register(
        DOMAIN,
        SERVICE_SET_SETPOINT_MIN,
        set_setpoint_min_service,
        schema=SET_SETPOINT_MIN_SCHEMA,
    )

    hass.services.async_register(
        DOMAIN,
        SERVICE_SET_FLOOR_AIR_LIMIT,
        set_floor_air_limit_service,
        schema=SET_FLOOR_AIR_LIMIT_SCHEMA,
    )

class Neviweb130Thermostat(ClimateEntity):
    """Implementation of a Neviweb thermostat."""

    def __init__(self, data, device_info, name):
        """Initialize."""
        self._name = name
        self._client = data.neviweb130_client
        self._id = device_info["id"]
        self._wattage = 0
        self._min_temp = 0
        self._max_temp = 0
        self._target_temp = None
        self._cur_temp = None
        self._cur_temp_before = None
        self._operation_mode = None
        self._heat_level = 0
        self._gfci_status = None
        self._floor_mode = None
        self._aux_heat = None
        self._keypad = None
        self._load2 = 0
        self._load2_status = None
        self._rssi = None
        self._occupancy = None
        self._wifi_display2 = None
        self._backlight = None
        self._floor_max = None
        self._time_format = "24h"
        self._floor_air_limit = None
        self._temperature_format = TEMP_CELSIUS
        self._is_floor = device_info["signature"]["model"] in \
            DEVICE_MODEL_FLOOR
        self._is_wifi_floor = device_info["signature"]["model"] in \
            DEVICE_MODEL_WIFI_FLOOR
        self._is_wifi = device_info["signature"]["model"] in \
            DEVICE_MODEL_WIFI_FLOOR or device_info["signature"]["model"] in DEVICE_MODEL_WIFI
        self._is_low_voltage = device_info["signature"]["model"] in \
            DEVICE_MODEL_LOW
        _LOGGER.debug("Setting up %s: %s", self._name, device_info)

    def update(self):
        if not self._is_low_voltage and not self._is_wifi_floor:
            WATT_ATTRIBUTE = [ATTR_WATTAGE]
        else:
            WATT_ATTRIBUTE = []
        if self._is_floor or self._is_wifi_floor:
            FLOOR_ATTRIBUTE = [ATTR_GFCI_STATUS, ATTR_FLOOR_MODE, ATTR_FLOOR_AUX, ATTR_FLOOR_OUTPUT2, ATTR_FLOOR_MAX, ATTR_FLOOR_AIR_LIMIT]
        else:
            FLOOR_ATTRIBUTE = []
        if self._is_wifi_floor:
            WIFI_FLOOR_ATTRIBUTE = [ATTR_WIFI_FLOOR_OUTPUT1]
        else:
            WIFI_FLOOR_ATTRIBUTE = []
        if self._is_wifi:
            WIFI_ATTRIBUTE = [ATTR_WIFI_WATTAGE, ATTR_WIFI, ATTR_WIFI_KEYPAD, ATTR_WIFI_DISPLAY2, ATTR_SETPOINT_MODE, ATTR_OCCUPANCY]
        else:
            WIFI_ATTRIBUTE = [ATTR_KEYPAD, ATTR_BACKLIGHT]
        """Get the latest data from Neviweb and update the state."""
        start = time.time()
        device_data = self._client.get_device_attributes(self._id,
            UPDATE_ATTRIBUTES + FLOOR_ATTRIBUTE + WATT_ATTRIBUTE + WIFI_FLOOR_ATTRIBUTE + WIFI_ATTRIBUTE)
        end = time.time()
        elapsed = round(end - start, 3)
        _LOGGER.debug("Updating %s (%s sec): %s",
            self._name, elapsed, device_data)

        if "error" not in device_data:
            if "errorCode" not in device_data:
                self._cur_temp_before = self._cur_temp
                self._cur_temp = float(device_data[ATTR_ROOM_TEMPERATURE]["value"]) if \
                    device_data[ATTR_ROOM_TEMPERATURE]["value"] != None else self._cur_temp_before
                self._target_temp = float(device_data[ATTR_ROOM_SETPOINT])
                self._min_temp = device_data[ATTR_ROOM_SETPOINT_MIN]
                self._max_temp = device_data[ATTR_ROOM_SETPOINT_MAX]
                self._temperature_format = device_data[ATTR_TEMP]
                self._time_format = device_data[ATTR_TIME]
                if not self._is_wifi:
                    self._heat_level = device_data[ATTR_OUTPUT_PERCENT_DISPLAY]
                    self._keypad = device_data[ATTR_KEYPAD]
                    self._backlight = device_data[ATTR_BACKLIGHT]
                    self._rssi = None
                    if not self._is_low_voltage:
                        self._wattage = device_data[ATTR_WATTAGE]
                else:
                    self._heat_level = device_data[ATTR_OUTPUT_PERCENT_DISPLAY]["percent"]
                    self._keypad = device_data[ATTR_WIFI_KEYPAD]
                    self._rssi = device_data[ATTR_WIFI]
                    self._wifi_display2 = device_data[ATTR_WIFI_DISPLAY2]
                    self._wattage = device_data[ATTR_WIFI_WATTAGE]
                    self._operation_mode = device_data[ATTR_SETPOINT_MODE]
                    self._occupancy = device_data[ATTR_OCCUPANCY]
                if self._is_floor or self._is_wifi_floor:
                    self._gfci_status = device_data[ATTR_GFCI_STATUS]
                    self._floor_mode = device_data[ATTR_FLOOR_MODE]
                    self._aux_heat = device_data[ATTR_FLOOR_AUX]
                    self._floor_air_limit = device_data[ATTR_FLOOR_AIR_LIMIT]["value"]
                    if not self._is_wifi_floor:
                        self._load2_status = device_data[ATTR_FLOOR_OUTPUT2]["status"]
                        self._load2 = device_data[ATTR_FLOOR_OUTPUT2]["value"]
                        self._floor_max = device_data[ATTR_FLOOR_MAX]["value"]
                    else:
                        self._load2_status = None
                        self._load2 = device_data[ATTR_FLOOR_OUTPUT2]
                return
            _LOGGER.warning("Error in reading device %s: (%s)", self._name, device_data)
            return
        _LOGGER.warning("Cannot update %s: %s", self._name, device_data)

    @property
    def unique_id(self):
        """Return unique ID based on Neviweb130 device ID."""
        return self._id

    @property
    def name(self):
        """Return the name of the thermostat."""
        return self._name

    @property
    def unit_of_measurement(self):
        """Return the unit of measurement of this entity, if any."""
        return self._temperature_format

    @property
    def device_class(self):
        """Return the device class of this entity."""
        return DEVICE_CLASS_TEMPERATURE

    @property
    def device_state_attributes(self):
        """Return the state attributes."""
        data = {}
        if not self._is_low_voltage:
            data = {'wattage': self._wattage}
        if self._is_floor or self._is_wifi_floor:
            data.update({'gfci_status': self._gfci_status,
                    'sensor_mode': self._floor_mode,
                    'slave_heat': self._aux_heat,
                    'slave_status': self._load2_status,
                    'slave_load': self._load2,
                    'floor_setpoint_max': self._floor_max,
                    'floor_air_limit': self._floor_air_limit})
        if self._is_wifi:
            data.update({'second_display': self._wifi_display2,
                         'occupancy': self._occupancy})
        data.update({'heat_level': self._heat_level,
                     'keypad': self._keypad,
                     'backlight': self._backlight,
                     'time_format': self._time_format,
                     'temperature_format': self._temperature_format,
                     'setpoint_max': self._max_temp,
                     'setpoint_min': self._min_temp,
                     'rssi': self._rssi,
                     'id': self._id})
        return data

    @property
    def supported_features(self):
        """Return the list of supported features."""
        return SUPPORT_FLAGS

    @property
    def min_temp(self):
        """Return the min temperature."""
        return self._min_temp

    @property
    def max_temp(self):
        """Return the max temperature."""
        return self._max_temp

    @property
    def temperature_unit(self):
        """Return the unit of measurement."""
        return TEMP_CELSIUS

    @property
    def hvac_mode(self):
        """Return current operation"""
        if self._operation_mode == MODE_OFF:
            return HVAC_MODE_OFF
        elif self._operation_mode in [MODE_AUTO, MODE_AUTO_BYPASS]:
            return HVAC_MODE_AUTO
        else:
            return HVAC_MODE_HEAT

    @property
    def hvac_modes(self):
        """Return the list of available operation modes."""
        return SUPPORTED_HVAC_MODES

    @property
    def current_temperature(self):
        """Return the current temperature."""
        return self._cur_temp

    @property
    def target_temperature (self):
        """Return the temperature we try to reach."""
        return self._target_temp

    @property
    def preset_modes(self):
        """Return available preset modes."""
        return PRESET_MODES

    @property
    def preset_mode(self):
        """Return current preset mode."""
        if self._operation_mode in [MODE_AUTO_BYPASS]:
            return PRESET_BYPASS
        elif self._operation_mode == MODE_AWAY:
            return PRESET_AWAY
        else:
            return PRESET_NONE

    @property
    def hvac_action(self):
        """Return current HVAC action."""
        if self._operation_mode == MODE_OFF:
            return CURRENT_HVAC_OFF
        elif self._heat_level == 0:
            return CURRENT_HVAC_IDLE
        else:
            return CURRENT_HVAC_HEAT

    def set_temperature(self, **kwargs):
        """Set new target temperature."""
        temperature = kwargs.get(ATTR_TEMPERATURE)
        if temperature is None:
            return
        self._client.set_temperature(self._id, temperature)
        self._target_temp = temperature

    def set_second_display(self, value):
        """Set thermostat second display between outside and setpoint temperature"""
        display = value["display"]
        entity = value["id"]
        if display == "outsideTemperature":
            display_name = "Outside"
        else:
            display_name = "Setpoint"
        self._client.set_second_display(
            entity, display)
        self._wifi_display2 = display_name

    def set_backlight(self, value):
        """Set thermostat backlight «auto» = off when idle / on when active or «on» = always on"""
        level = value["level"]
        entity = value["id"]
        if level == "on":
            level_command = "always"
            level_name = "On"
        else:
            level_command = "onActive"
            level_name = "Auto"
        self._client.set_backlight(
            entity, level_command)
        self._backlight = level_name

    def set_keypad_lock(self, value):
        """Lock or unlock device's keypad, locked = Locked, unlocked = Unlocked"""
        lock = value["lock"]
        entity = value["id"]
#        lock_key = ATTR_FLOOR_OUTPUT2+':{"status":self._load2_status,"value":self._load2}'
        lock_key = "on"
        if lock == "locked":
            lock_name = "Locked"
        else:
            lock_name = "Unlocked"
        self._client.set_keypad_lock(
            entity, lock, lock_key)
        self._keypad = lock_name

    def set_time_format(self, value):
        """set time format 12h or 24h"""
        time = value["time"]
        entity = value["id"]
        if time == 12:
            time_commande = "12h"
        else:
            time_commande = "24h"
        self._client.set_time_format(
            entity, time_commande)
        self._time_format = time_commande

    def set_temperature_format(self, value):
        """set temperature format, celsius or fahrenheit"""
        temp = value["temp"]
        entity = value["id"]
        self._client.set_temperature_format(
            entity, temp)
        self._temperature_format = temp

    def set_setpoint_max(self, value):
        """set maximum setpoint temperature"""
        temp = value["temp"]
        entity = value["id"]
        self._client.set_setpoint_max(
            entity, temp)
        self._max_temp = temp

    def set_setpoint_min(self, value):
        """set minimum setpoint temperature"""
        temp = value["temp"]
        entity = value["id"]
        self._client.set_setpoint_min(
            entity, temp)
        self._min_temp = temp

    def set_floor_air_limit(self, value):
        """ set maximum temperature air limit for floor thermostat """
        temp = value["temp"]
        entity = value["id"]
        if temp == 0:
           status = "off"
        else:
            status = "on"
        self._client.set_floor_air_limit(
            entity, status, temp)
        self._floor_air_limit = temp

    def set_hvac_mode(self, hvac_mode):
        """Set new hvac mode."""
        if hvac_mode == HVAC_MODE_OFF:
            self._client.set_setpoint_mode(self._id, MODE_OFF)
        elif hvac_mode == HVAC_MODE_HEAT:
            self._client.set_setpoint_mode(self._id, MODE_MANUAL)
        elif hvac_mode == HVAC_MODE_AUTO:
            self._client.set_setpoint_mode(self._id, MODE_AUTO)
        else:
            _LOGGER.error("Unable to set hvac mode: %s.", hvac_mode)

    def set_preset_mode(self, preset_mode):
        """Activate a preset."""
        if preset_mode == self.preset_mode:
            return

        if preset_mode == PRESET_AWAY:
            self._client.set_setpoint_mode(self._id, MODE_AWAY)
        elif preset_mode == PRESET_BYPASS:
            if self._operation_mode == MODE_AUTO:
                self._client.set_setpoint_mode(self._id, MODE_AUTO_BYPASS)
        elif preset_mode == PRESET_NONE:
            # Re-apply current hvac_mode without any preset
            self.set_hvac_mode(self.hvac_mode)
        else:
            _LOGGER.error("Unable to set preset mode: %s.", preset_mode)
