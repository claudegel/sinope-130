"""
Need to be changed
Support for Neviweb thermostat connected to GT130 ZigBee.
model 1124 = thermostat TH1123ZB 3000W and TH1124ZB 4000W
model 737 = thermostat TH1300ZB 3600W floor 
model xxx = thermostat TH1500ZB double pole thermostat
model xxx = thermostat TH1400ZB low voltage
For more details about this platform, please refer to the documentation at  
https://www.sinopetech.com/en/support/#api
"""
import logging

import voluptuous as vol
import time

import custom_components.neviweb130 as neviweb130
from . import (SCAN_INTERVAL)
from homeassistant.components.climate import ClimateDevice
from homeassistant.components.climate.const import (HVAC_MODE_HEAT, 
    HVAC_MODE_OFF, HVAC_MODE_AUTO, SUPPORT_TARGET_TEMPERATURE, 
    SUPPORT_PRESET_MODE, PRESET_AWAY, PRESET_NONE, CURRENT_HVAC_HEAT, 
    CURRENT_HVAC_IDLE, CURRENT_HVAC_OFF)
from homeassistant.const import (TEMP_CELSIUS, TEMP_FAHRENHEIT, 
    ATTR_TEMPERATURE)
from datetime import timedelta
from homeassistant.helpers.event import track_time_interval
from .const import (DOMAIN, ATTR_SETPOINT_MODE, ATTR_ROOM_SETPOINT,
    ATTR_OUTPUT_PERCENT_DISPLAY, ATTR_ROOM_TEMPERATURE, ATTR_ROOM_SETPOINT_MIN,
    ATTR_ROOM_SETPOINT_MAX, ATTR_WATTAGE, ATTR_GFCI_STATUS, MODE_AUTO, MODE_AUTO_BYPASS, 
    MODE_MANUAL, MODE_OFF, MODE_AWAY)

_LOGGER = logging.getLogger(__name__)

SUPPORT_FLAGS = (SUPPORT_TARGET_TEMPERATURE | SUPPORT_PRESET_MODE)

DEFAULT_NAME = "neviweb130 climate"

UPDATE_ATTRIBUTES = [ATTR_SETPOINT_MODE, ATTR_ROOM_SETPOINT,
    ATTR_OUTPUT_PERCENT_DISPLAY, ATTR_ROOM_TEMPERATURE, ATTR_ROOM_SETPOINT_MIN,
    ATTR_ROOM_SETPOINT_MAX, ATTR_WATTAGE]

SUPPORTED_HVAC_MODES = [HVAC_MODE_OFF, HVAC_MODE_AUTO, HVAC_MODE_HEAT]

PRESET_BYPASS = 'temporary'
PRESET_MODES = [
    PRESET_NONE,
    PRESET_AWAY,
    PRESET_BYPASS
]

DEVICE_MODEL_FLOOR = [737]
DEVICE_MODEL_HEAT = [1124]
IMPLEMENTED_DEVICE_MODEL = DEVICE_MODEL_HEAT + DEVICE_MODEL_FLOOR

async def async_setup_platform(hass, config, async_add_entities, discovery_info=None):
    """Set up the neviweb130 thermostats."""
    data = hass.data[DOMAIN]
    
    devices = []
    for device_info in data.neviweb130_client.gateway_data:
        if "signature" in device_info and \
            "model" in device_info["signature"] and \
            device_info["signature"]["model"] in IMPLEMENTED_DEVICE_MODEL:
            device_name = "{} {}".format(DEFAULT_NAME, device_info["name"])
            devices.append(Neviweb130Thermostat(data, device_info, device_name))

    async_add_entities(devices, True)

class Neviweb130Thermostat(ClimateDevice):
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
        self._operation_mode = None
        self._heat_level = 0
        self._is_floor = device_info["signature"]["model"] in \
            DEVICE_MODEL_FLOOR
#        self._gfci_status = None
        _LOGGER.debug("Setting up %s: %s", self._name, device_info)

    def update(self):
        """Get the latest data from Neviweb and update the state."""
        start = time.time()
        device_data = self._client.get_device_attributes(self._id,
            UPDATE_ATTRIBUTES)
        end = time.time()
        elapsed = round(end - start, 3)
        _LOGGER.debug("Updating %s (%s sec): %s",
            self._name, elapsed, device_data)

        if "error" not in device_data:
            if "errorCode" not in device_data:
                self._cur_temp = float(device_data[ATTR_ROOM_TEMPERATURE]["value"])
                self._target_temp = float(device_data[ATTR_ROOM_SETPOINT]) #if \
#                    device_data[ATTR_SETPOINT_MODE] != MODE_OFF else 0.0
                self._heat_level = device_data[ATTR_OUTPUT_PERCENT_DISPLAY]
#                self._operation_mode = device_data[ATTR_SETPOINT_MODE]
                self._min_temp = device_data[ATTR_ROOM_SETPOINT_MIN]
                self._max_temp = device_data[ATTR_ROOM_SETPOINT_MAX]
                self._wattage = device_data[ATTR_WATTAGE]
#                if self._is_floor:
#                    self._gfci_status = device_data[ATTR_GFCI_STATUS]
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
    def device_state_attributes(self):
        """Return the state attributes."""
#        data = {}
#        if self._is_floor:
#            data = {'gfci_status': self._gfci_status}
#        data.update({'heat_level': self._heat_level,
#                     'wattage': self._wattage,
#                     'id': self._id})
#        return data
        return {'heat_level': self._heat_level,
                'wattage': self._wattage,
                'id': self._id}

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
