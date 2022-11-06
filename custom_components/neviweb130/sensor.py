"""
Support for Neviweb sensors connected via GT130 ZigBee.
model 5051 = WL4200ZB, and WL4200S water leak detector connected to GT130
model 5053 = WL4200S, and WL4200C, perimeter cable water leak detector connected to GT130
model 5050 = WL4200ZB, and WL4200S, water leak detector connected to Sedna valve
model 5052 = WL4200S, and WL4200C, perimeter cable water leak detector connected to sedna 2 gen.
model 5056 = LM4110-ZB, level monitor
model 130 = gateway GT130
model xxx = gateway GT4220WF-M for mesh valve network
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
    ATTR_ENTITY_ID,
    TEMP_CELSIUS,
    TEMP_FAHRENHEIT,
    STATE_OK,
    ATTR_VOLTAGE,
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

from homeassistant.components.sensor import SensorStateClass

from homeassistant.components.binary_sensor import BinarySensorDeviceClass

from datetime import timedelta
from homeassistant.helpers.event import track_time_interval
from homeassistant.helpers.entity import Entity
from homeassistant.helpers.icon import icon_for_battery_level
from .const import (
    DOMAIN,
    ATTR_ROOM_TEMPERATURE,
    ATTR_WATER_LEAK_STATUS,
    ATTR_BATTERY_VOLTAGE,
    ATTR_BATTERY_STATUS,
    ATTR_BATTERY_TYPE,
    ATTR_ROOM_TEMP_ALARM,
    ATTR_LEAK_ALERT,
    ATTR_BATT_ALERT,
    ATTR_TEMP_ALERT,
    ATTR_CONF_CLOSURE,
    ATTR_STATUS,
    ATTR_RSSI,
    ATTR_ERROR_CODE_SET1,
    ATTR_ANGLE,
    ATTR_TANK_TYPE,
    ATTR_TANK_HEIGHT,
    MODE_OFF,
    STATE_WATER_LEAK,
    SERVICE_SET_SENSOR_ALERT,
    SERVICE_SET_BATTERY_TYPE,
)

_LOGGER = logging.getLogger(__name__)

DEFAULT_NAME = 'neviweb130 sensor'

UPDATE_ATTRIBUTES = [ATTR_BATTERY_VOLTAGE, ATTR_BATTERY_STATUS, ATTR_BATTERY_TYPE]

IMPLEMENTED_GATEWAY = [130]
IMPLEMENTED_TANK_MONITOR = [5056, 5055]
IMPLEMENTED_SENSOR_MODEL = [5051, 5053]
IMPLEMENTED_CONNECTED_SENSOR = [5050, 5052]
IMPLEMENTED_DEVICE_MODEL = IMPLEMENTED_SENSOR_MODEL + IMPLEMENTED_TANK_MONITOR + IMPLEMENTED_CONNECTED_SENSOR + IMPLEMENTED_GATEWAY

SENSOR_TYPES = {
    "leak": ["", None, BinarySensorDeviceClass.MOISTURE],
    "level": ["%", None, SensorStateClass.MEASUREMENT],
    "gateway": ["", None, BinarySensorDeviceClass.CONNECTIVITY],
}

SET_SENSOR_ALERT_SCHEMA = vol.Schema(
    {
        vol.Required(ATTR_ENTITY_ID): cv.entity_id,
        vol.Required(ATTR_LEAK_ALERT): vol.All(
            vol.Coerce(int), vol.Range(min=0, max=1)
        ),
        vol.Required(ATTR_BATT_ALERT): vol.All(
            vol.Coerce(int), vol.Range(min=0, max=1)
        ),
        vol.Required(ATTR_TEMP_ALERT): vol.All(
            vol.Coerce(int), vol.Range(min=0, max=1)
        ),
        vol.Required(ATTR_CONF_CLOSURE): vol.In(["on", "off"]),
    }
)

SET_BATTERY_TYPE_SCHEMA = vol.Schema(
    {
        vol.Required(ATTR_ENTITY_ID): cv.entity_id,
        vol.Required(ATTR_BATTERY_TYPE): vol.In(["alkaline", "lithium"]),
    }
)

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
            if device_info["signature"]["model"] in IMPLEMENTED_SENSOR_MODEL \
              or device_info["signature"]["model"] in IMPLEMENTED_CONNECTED_SENSOR:
                device_type = "leak"
            elif  device_info["signature"]["model"] in IMPLEMENTED_TANK_MONITOR:
                device_type = "level"
            else:
                device_type = "gateway"
            device_sku = device_info["sku"]
            entities.append(Neviweb130Sensor(data, device_info, device_name, device_type, device_sku))

    async_add_entities(entities, True)

    def set_sensor_alert_service(service):
        """ Set different alert and action for water leak sensor """
        entity_id = service.data[ATTR_ENTITY_ID]
        value = {}
        for sensor in entities:
            if sensor.entity_id == entity_id:
                value = {"id": sensor.unique_id, "leak": service.data[ATTR_LEAK_ALERT], "temp": service.data[ATTR_TEMP_ALERT], "batt": service.data[ATTR_BATT_ALERT], "close": service.data[ATTR_CONF_CLOSURE]}
                sensor.set_sensor_alert(value)
                sensor.schedule_update_ha_state(True)
                break

    def set_battery_type_service(service):
        """ Set battery type for water leak sensor """
        entity_id = service.data[ATTR_ENTITY_ID]
        value = {}
        for sensor in entities:
            if sensor.entity_id == entity_id:
                value = {"id": sensor.unique_id, "type": service.data[ATTR_BATTERY_TYPE]}
                sensor.set_battery_type(value)
                sensor.schedule_update_ha_state(True)
                break

    hass.services.async_register(
        DOMAIN,
        SERVICE_SET_SENSOR_ALERT,
        set_sensor_alert_service,
        schema=SET_SENSOR_ALERT_SCHEMA,
    )

    hass.services.async_register(
        DOMAIN,
        SERVICE_SET_BATTERY_TYPE,
        set_battery_type_service,
        schema=SET_BATTERY_TYPE_SCHEMA,
    )

def voltage_to_percentage(voltage, type):
    """Convert voltage level from volt to percentage."""
    if type == "alkaline":
        return int((min(voltage,3.0)-2.0)/(3.0-2.0) * 100)
    else:
        return int((min(voltage,3.0)-2.2)/(3.0-2.2) * 100)

class Neviweb130Sensor(Entity):
    """Implementation of a Neviweb sensor."""

    def __init__(self, data, device_info, name, device_type, sku):
        """Initialize."""
        self._name = name
        self._sku = sku
        self._client = data.neviweb130_client
        self._id = device_info["id"]
        self._device_type = device_type
        self._cur_temp = None
        self._leak_status = None
        self._battery_voltage = None
        self._battery_status = None
        self._temp_status = None
        self._battery_type = "alkaline"
        self._is_gateway = device_info["signature"]["model"] in \
            IMPLEMENTED_GATEWAY
        self._is_monitor = device_info["signature"]["model"] in \
            IMPLEMENTED_TANK_MONITOR
        self._is_leak = device_info["signature"]["model"] in \
            IMPLEMENTED_SENSOR_MODEL or device_info["signature"]["model"] in IMPLEMENTED_CONNECTED_SENSOR
        self._is_connected = device_info["signature"]["model"] in \
            IMPLEMENTED_CONNECTED_SENSOR
        self._leak_status = None
        self._gateway_status = None
        self._leak_alert = None
        self._temp_alert = None
        self._battery_alert = None
        self._closure_action = None
        self._rssi = None
        self._angle = None
        self._tank_type = None
        self._tank_height = None
        self._relayK1 = None
        self._relayK2 = None
        _LOGGER.debug("Setting up %s: %s", self._name, device_info)

    def update(self):
        if self._is_monitor:
            MONITOR_ATTRIBUTE = [ATTR_ANGLE, ATTR_TANK_TYPE, ATTR_TANK_HEIGHT, ATTR_ERROR_CODE_SET1, ATTR_RSSI]
        else:
            if self._is_connected:
                CONNECTED_ATTRIBUTE = [ATTR_BATT_ALERT, ATTR_TEMP_ALERT, ATTR_CONF_CLOSURE]
            else:
                CONNECTED_ATTRIBUTE = []
            MONITOR_ATTRIBUTE = [ATTR_WATER_LEAK_STATUS, ATTR_ROOM_TEMPERATURE, ATTR_ROOM_TEMP_ALARM, ATTR_LEAK_ALERT, ATTR_RSSI]
        """Get the latest data from Neviweb and update the state."""
        start = time.time()
        if self._is_gateway:
            device_status = self._client.get_device_status(self._id)
        else:
            device_data = self._client.get_device_attributes(self._id,
            UPDATE_ATTRIBUTES + MONITOR_ATTRIBUTE + CONNECTED_ATTRIBUTE)
#        device_daily_stats = self._client.get_device_daily_stats(self._id)
        end = time.time()
        elapsed = round(end - start, 3)
        if self._is_gateway:
            _LOGGER.debug("Updating %s (%s sec): %s",
                self._name, elapsed, device_status)
        else:
            _LOGGER.debug("Updating %s (%s sec): %s",
                self._name, elapsed, device_data)
        if self._is_gateway:
            self._gateway_status = device_status[ATTR_STATUS]
            return
        if "error" not in device_data or device_data is not None:
            if "errorCode" not in device_data:
                if self._is_leak:
                    self._leak_status = STATE_WATER_LEAK if \
                        device_data[ATTR_WATER_LEAK_STATUS] == STATE_WATER_LEAK else "ok"
                    self._cur_temp = device_data[ATTR_ROOM_TEMPERATURE]
                    self._leak_alert = device_data[ATTR_LEAK_ALERT]
                    if self._is_connected:
                        self._temp_status = device_data[ATTR_ROOM_TEMP_ALARM]
                        self._temp_alert = device_data[ATTR_TEMP_ALERT]
                        self._battery_alert = device_data[ATTR_BATT_ALERT]
                        self._closure_action = device_data[ATTR_CONF_CLOSURE]
                else:
                    self._angle = device_data[ATTR_ANGLE]
                    self._tank_type = device_data[ATTR_TANK_TYPE]
                    self._tank_height = device_data[ATTR_TANK_HEIGHT]
                    if ATTR_ERROR_CODE_SET1 in device_data:
                        self._relayK1 = device_data[ATTR_ERROR_CODE_SET1]["relayK1"]
                        self._relayK2 = device_data[ATTR_ERROR_CODE_SET1]["relayK2"]
                self._battery_voltage = device_data[ATTR_BATTERY_VOLTAGE]
                if ATTR_BATTERY_STATUS in device_data:
                    self._battery_status = device_data[ATTR_BATTERY_STATUS]
                    self._battery_type = device_data[ATTR_BATTERY_TYPE]
                if ATTR_RSSI in device_data:
                        self._rssi = device_data[ATTR_RSSI]
                return
            _LOGGER.warning("Error in reading device %s: (%s)", self._name, device_data)
            return
        if device_data["error"]["code"] == "USRSESSEXP":
            _LOGGER.warning("Session expired... reconnecting...")
            self._client.reconnect()
        elif device_data["error"]["code"] == "ACCSESSEXC":
            _LOGGER.warning("Maximun session number reached...Close other connections and try again.")
            self._client.reconnect()
        elif device_data["error"]["code"] == "DVCACTNSPTD":
            _LOGGER.warning("Device action not supported... Report to maintainer.")
        elif device_data["error"]["code"] == "DVCCOMMTO":
            _LOGGER.warning("Device Communication Timeout... The device did not respond to the server within the prescribed delay.")
        else:
            _LOGGER.warning("Unknown error for %s: %s... Report to maintainer.", self._name, device_data)

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
    def gateway_status(self):
        """Return current gateway status: 'online' or 'offline' """
        return self._gateway_status != None

    @property  
    def level_status(self):
        """Return current sensor liquid level status in % """
        return self._level_status != None

    @property
    def extra_state_attributes(self):
        """Return the state attributes."""
        data = {}
        if self._is_monitor:
            data = {'Angle': self._angle,
                    'Battery_level': voltage_to_percentage(self._battery_voltage, self._battery_type),
                    'Battery_voltage': self._battery_voltage,
                    'Battery_type': self._battery_type,
                    'Tank_type': self._tank_type,
                    'Tank_height': self._tank_height,
                    'RelayK1': self._relayK1,
                    'RelayK2': self._relayK2,
                    'Rssi': self._rssi}
        elif self._is_leak:
            data = {'Leak_status': self._leak_status,
                    'Temperature': self._cur_temp,
                    'leak_alert': self._leak_alert,
                    'Battery_level': voltage_to_percentage(self._battery_voltage, self._battery_type),
                    'Battery_voltage': self._battery_voltage,
                    'Battery_status': self._battery_status,
                    'Battery_type': self._battery_type,
                    'Rssi': self._rssi}
            if self._is_connected:
                data.update({'Temp_alarm': self._temp_status,
                             'Temperature_alert': self._temp_alert,
                             'Battery_alert': self._battery_alert,
                             'Closure_action': self._closure_action})
        elif self._is_gateway:
            data = {'Gateway_status': self._gateway_status}
        data.update({'sku': self._sku,
                    'Id': self._id})
        return data

    @property
    def battery_voltage(self):
        """Return the current battery voltage of the sensor in %."""
        return voltage_to_percentage(self._battery_voltage, self._battery_type)

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
        elif self._is_gateway:
            return self._gateway_status

    def set_sensor_alert(self, value):
        """ Set water leak sensor alert and action """
        leak = value["leak"]
        batt = value["batt"]
        temp = value["temp"]
        close = value["close"]
        entity = value["id"]
        self._client.set_sensor_alert(
            entity, leak, batt, temp, close)
        self._leak_alert = True if leak == 1 else False
        self._temp_alert = True if temp == 1 else False
        self._battery_alert = True if batt == 1 else False
        self._closure_action = close

    def set_battery_type(self, value):
        """ Set battery type, alkaline or lithium for water leak sensor. """
        batt = value["type"]
        entity = value["id"]
        self._client.set_battery_type(
            entity, batt)
        self._battery_type = batt
