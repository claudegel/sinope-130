"""
Support for Neviweb sensors connected via GT130 ZigBee.
model 5051 = WL4200ZB, water leak detector
model 5051 = WL4200S, water leak detector with sensor
model 4110 = LM4110-ZB, level monitor
For more details about this platform, please refer to the documentation at  
https://www.sinopetech.com/en/support/#api
"""

import logging

import voluptuous as vol
import time

import custom_components.neviweb130 as neviweb130
from . import (SCAN_INTERVAL)

from homeassistant.components.sensor import PLATFORM_SCHEMA
from homeassistant.const import (
    DEVICE_CLASS_BATTERY,
    DEVICE_CLASS_TEMPERATURE,
    TEMP_CELSIUS,
    TEMP_FAHRENHEIT,
    STATE_OK,
    ATTR_VOLTAGE,
)

from datetime import timedelta
from homeassistant.helpers.event import track_time_interval
from homeassistant.helpers.entity import Entity
from homeassistant.helpers.icon import icon_for_battery_level
from .const import (
    DOMAIN,
    ATTR_LEVEL_STATUS,
    ATTR_ROOM_TEMPERATURE,
    ATTR_WATER_LEAK_STATUS,
    ATTR_BATTERY_VOLTAGE,
    ATTR_BATTERY_STATUS,
    MODE_OFF,
    STATE_WATER_LEAK,
)

_LOGGER = logging.getLogger(__name__)

DEFAULT_NAME = 'neviweb130 sensor'

UPDATE_ATTRIBUTES = [ATTR_BATTERY_VOLTAGE, ATTR_BATTERY_STATUS]

IMPLEMENTED_TANK_MONITOR = [4110]
IMPLEMENTED_SENSOR_MODEL = [5051]
IMPLEMENTED_DEVICE_MODEL = IMPLEMENTED_SENSOR_MODEL + IMPLEMENTED_TANK_MONITOR

SENSOR_TYPES = {
    "leak": ["", None, None],
    "level": ["%", None, None],
}

async def async_setup_platform(
    hass,
    config,
    async_add_entities,
    discovery_info=None,
):
    """Set up the Neviweb sensor."""
    data = hass.data[DOMAIN]

    entities = []
    for device_info in data.neviweb130_client.gateway_data:
        if "signature" in device_info and \
            "model" in device_info["signature"] and \
            device_info["signature"]["model"] in IMPLEMENTED_DEVICE_MODEL:
            device_name = '{} {}'.format(DEFAULT_NAME, device_info["name"])
            if device_info["signature"]["model"] in IMPLEMENTED_SENSOR_MODEL:
                device_type = "leak"
            elif  device_info["signature"]["model"] in IMPLEMENTED_TANK_MONITOR:
                device_type = "level"
            entities.append(Neviweb130Sensor(data, device_info, device_name, device_type))

    async_add_entities(entities, True)

def voltage_to_percentage(voltage):
    """Convert voltage level from absolute 0..3.25 to percentage."""
    return int((voltage * 100.0) / 3.25)

class Neviweb130Sensor(Entity):
    """Implementation of a Neviweb sensor."""

    def __init__(self, data, device_info, name, device_type):
        """Initialize."""
        self._name = name
        self._client = data.neviweb130_client
        self._id = device_info["id"]
        self._device_type = device_type
        self._cur_temp = None
        self._leak_status = None
        self._battery_voltage = None
        self._battery_status = None
        self._is_monitor = device_info["signature"]["model"] in \
            IMPLEMENTED_TANK_MONITOR
        self._is_leak = device_info["signature"]["model"] in \
            IMPLEMENTED_SENSOR_MODEL
        self._level_status = None
        self._leak_status = None
        _LOGGER.debug("Setting up %s: %s", self._name, device_info)

    def update(self):
        if self._is_monitor:
            MONITOR_ATTRIBUTE = [ATTR_LEVEL_STATUS]
        else:
            MONITOR_ATTRIBUTE = [ATTR_WATER_LEAK_STATUS, ATTR_ROOM_TEMPERATURE]
        """Get the latest data from Neviweb and update the state."""
        start = time.time()
        device_data = self._client.get_device_attributes(self._id,
            UPDATE_ATTRIBUTES + MONITOR_ATTRIBUTE)
        device_daily_stats = self._client.get_device_daily_stats(self._id)
        end = time.time()
        elapsed = round(end - start, 3)
        _LOGGER.debug("Updating %s (%s sec): %s",
            self._name, elapsed, device_data)
        if "error" not in device_data:
            if "errorCode" not in device_data:
                if self._is_leak:
                    self._leak_status = STATE_WATER_LEAK if \
                        device_data[ATTR_WATER_LEAK_STATUS] == STATE_WATER_LEAK else "ok"
                    self._cur_temp = device_data[ATTR_ROOM_TEMPERATURE]
                else:
                    self._level_status = device_data[ATTR_LEVEL_STATUS]
                self._battery_voltage = device_data[ATTR_BATTERY_VOLTAGE]
                self._battery_status = device_data[ATTR_BATTERY_STATUS]
                return
            _LOGGER.warning("Error in reading device %s: (%s)", self._name, device_data)
            return
        _LOGGER.warning("Cannot update %s: %s", self._name, device_data)     

    @property
    def unique_id(self):
        """Return unique ID based on Neviweb device ID."""
        return self._id

    @property
    def name(self):
        """Return the name of the sensor."""
        return self._name

    @property
    def icon(self):
        """Return the icon to use in the frontend."""
        try:
            return SENSOR_TYPES.get(self._device_type)[1]
        except TypeError:
            return None

    @property
    def unit_of_measurement(self):
        """Return the unit of measurement of this entity, if any."""
        try:
            return SENSOR_TYPES.get(self._device_type)[0]
        except TypeError:
            return None

    @property
    def device_class(self):
        """Return the device class of this entity."""
        return (
            SENSOR_TYPES.get(self._device_type)[2]
            if self._device_type in SENSOR_TYPES
            else None
        )

    @property
    def current_temperature(self):
        """Return the current sensor temperature."""
        return self._cur_temp

    @property  
    def leak_status(self):
        """Return current sensor leak status: 'water' or 'ok' """
        return self._leak_status != None

    @property  
    def level_status(self):
        """Return current sensor liquid level status in % """
        return self._level_status != None

    @property
    def device_state_attributes(self):
        """Return the state attributes."""
        data = {}
        if self._is_monitor:
            data = {'Level': self._level_status}
        elif self._is_leak:
            data = {'Leak_status': self._leak_status,
                   'Temperature': self._cur_temp}
        data.update({'Battery': voltage_to_percentage(self._battery_voltage),
                     'Battery status': self._battery_status,
                     'Id': self._id})
        return data

    @property
    def battery_voltage(self):
        """Return the current battery voltage of the sensor in %."""
        return voltage_to_percentage(self._battery_voltage)

    @property
    def battery_status(self):
        """Return the current battery status."""
        return self._battery_status

    @property
    def state(self):
        """Return the state of the sensor."""
        if self._is_monitor:
            return self._level_status
        elif self._is_leak:
            return self._leak_status
