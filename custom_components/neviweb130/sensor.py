"""
Support for Neviweb sensors connected via GT130 ZigBee.
model 5051 = WL4200, WL4210 and WL4200S water leak detector connected to GT130
model 5053 = WL4200C, perimeter cable water leak detector connected to GT130
model 5050 = WL4200, WL4210 and WL4200S, water leak detector connected to Sedna valve
model 5052 = WL4200C, perimeter cable water leak detector connected to sedna 2 gen.
model 5056 = LM4110-ZB, level monitor
model 5055 = LM4110-ZB, level monitor, multiples tanks
model 130 = gateway GT130
model xxx = gateway GT4220WF-M for mesh valve network
For more details about this platform, please refer to the documentation at  
https://www.sinopetech.com/en/support/#api
"""

import logging

import voluptuous as vol
import time

from datetime import datetime

import custom_components.neviweb130 as neviweb130
from . import (SCAN_INTERVAL)

from homeassistant.components.sensor import PLATFORM_SCHEMA
from homeassistant.const import (
    ATTR_ENTITY_ID,
    PERCENTAGE,
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
    ATTR_SAMPLING,
    ATTR_TANK_TYPE,
    ATTR_TANK_HEIGHT,
    ATTR_GAUGE_TYPE,
    ATTR_FUEL_ALERT,
    ATTR_TANK_PERCENT,
    ATTR_FUEL_PERCENT_ALERT,
    MODE_OFF,
    STATE_WATER_LEAK,
    SERVICE_SET_SENSOR_ALERT,
    SERVICE_SET_BATTERY_TYPE,
    SERVICE_SET_TANK_TYPE,
    SERVICE_SET_GAUGE_TYPE,
    SERVICE_SET_LOW_FUEL_ALERT,
    SERVICE_SET_TANK_HEIGHT,
    SERVICE_SET_FUEL_ALERT,
    SERVICE_SET_BATTERY_ALERT,
    SERVICE_SET_ACTIVATION,
)

_LOGGER = logging.getLogger(__name__)

DEFAULT_NAME = 'neviweb130 sensor'
DEFAULT_NAME_2 = 'neviweb130 sensor 2'

UPDATE_ATTRIBUTES = [ATTR_BATTERY_VOLTAGE, ATTR_BATTERY_STATUS]

IMPLEMENTED_GATEWAY = [130]
IMPLEMENTED_TANK_MONITOR = [5055, 5056]
IMPLEMENTED_SENSOR_MODEL = [5051, 5053]
IMPLEMENTED_CONNECTED_SENSOR = [5050, 5052]
IMPLEMENTED_DEVICE_MODEL = IMPLEMENTED_SENSOR_MODEL + IMPLEMENTED_TANK_MONITOR + IMPLEMENTED_CONNECTED_SENSOR + IMPLEMENTED_GATEWAY

SENSOR_TYPES = {
    "leak": [None, None, BinarySensorDeviceClass.MOISTURE],
    "level": [PERCENTAGE, None, SensorStateClass.MEASUREMENT],
    "gateway": [None, None, BinarySensorDeviceClass.CONNECTIVITY],
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

SET_TANK_TYPE_SCHEMA = vol.Schema(
    {
        vol.Required(ATTR_ENTITY_ID): cv.entity_id,
        vol.Required(ATTR_TANK_TYPE): vol.In(["propane", "oil"]),
    }
)

SET_GAUGE_TYPE_SCHEMA = vol.Schema(
    {
        vol.Required(ATTR_ENTITY_ID): cv.entity_id,
        vol.Required(ATTR_GAUGE_TYPE): vol.All(
            vol.Coerce(int), vol.In([595, 1080])),
    }
)

SET_LOW_FUEL_ALERT_SCHEMA = vol.Schema(
    {
        vol.Required(ATTR_ENTITY_ID): cv.entity_id,
        vol.Required(ATTR_FUEL_PERCENT_ALERT): vol.All(
            vol.Coerce(int), vol.In([0, 10, 20, 30])),
    }
)

SET_TANK_HEIGHT_SCHEMA = vol.Schema(
    {
        vol.Required(ATTR_ENTITY_ID): cv.entity_id,
        vol.Required(ATTR_TANK_HEIGHT): vol.All(
            vol.Coerce(int), vol.In([23, 24, 35, 38, 47, 48, 50])),
    }
)

SET_FUEL_ALERT_SCHEMA = vol.Schema(
    {
        vol.Required(ATTR_ENTITY_ID): cv.entity_id,
        vol.Required(ATTR_FUEL_ALERT): vol.In([True, False]),
    }
)

SET_BATTERY_ALERT_SCHEMA = vol.Schema(
    {
        vol.Required(ATTR_ENTITY_ID): cv.entity_id,
        vol.Required(ATTR_BATT_ALERT): vol.In([True, False]),
    }
)

SET_ACTIVATION_SCHEMA = vol.Schema(
    {
        vol.Required(ATTR_ENTITY_ID): cv.entity_id,
        vol.Required("active"): vol.In([True, False]),
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
    for device_info in data.neviweb130_client.gateway_data2:
        if "signature" in device_info and \
            "model" in device_info["signature"] and \
            device_info["signature"]["model"] in IMPLEMENTED_DEVICE_MODEL:
            device_name = '{} {}'.format(DEFAULT_NAME_2, device_info["name"])
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

    def set_tank_type_service(service):
        """ Set tank type for fuel tank """
        entity_id = service.data[ATTR_ENTITY_ID]
        value = {}
        for sensor in entities:
            if sensor.entity_id == entity_id:
                value = {"id": sensor.unique_id, "type": service.data[ATTR_TANK_TYPE]}
                sensor.set_tank_type(value)
                sensor.schedule_update_ha_state(True)
                break

    def set_gauge_type_service(service):
        """ Set gauge type for propane tank """
        entity_id = service.data[ATTR_ENTITY_ID]
        value = {}
        for sensor in entities:
            if sensor.entity_id == entity_id:
                value = {"id": sensor.unique_id, "gauge": service.data[ATTR_GAUGE_TYPE]}
                sensor.set_gauge_type(value)
                sensor.schedule_update_ha_state(True)
                break

    def set_low_fuel_alert_service(service):
        """ Set low fuel alert on tank, propane or oil """
        entity_id = service.data[ATTR_ENTITY_ID]
        value = {}
        for sensor in entities:
            if sensor.entity_id == entity_id:
                value = {"id": sensor.unique_id, "low": service.data[ATTR_FUEL_PERCENT_ALERT]}
                sensor.set_low_fuel_alert(value)
                sensor.schedule_update_ha_state(True)
                break

    def set_tank_height_service(service):
        """ Set tank height for oil tank """
        entity_id = service.data[ATTR_ENTITY_ID]
        value = {}
        for sensor in entities:
            if sensor.entity_id == entity_id:
                value = {"id": sensor.unique_id, "height": service.data[ATTR_TANK_HEIGHT]}
                sensor.set_tank_height(value)
                sensor.schedule_update_ha_state(True)
                break

    def set_fuel_alert_service(service):
        """ Set fuel alert for LM4110-ZB """
        entity_id = service.data[ATTR_ENTITY_ID]
        value = {}
        for sensor in entities:
            if sensor.entity_id == entity_id:
                value = {"id": sensor.unique_id, "fuel": service.data[ATTR_FUEL_ALERT]}
                sensor.set_fuel_alert(value)
                sensor.schedule_update_ha_state(True)
                break

    def set_battery_alert_service(service):
        """ Set battery alert for LM4110-ZB """
        entity_id = service.data[ATTR_ENTITY_ID]
        value = {}
        for sensor in entities:
            if sensor.entity_id == entity_id:
                value = {"id": sensor.unique_id, "batt": service.data[ATTR_BATT_ALERT]}
                sensor.set_battery_alert(value)
                sensor.schedule_update_ha_state(True)
                break

    def set_activation_service(service):
        """ Activate or deactivate Neviweb polling for missing device """
        entity_id = service.data[ATTR_ENTITY_ID]
        value = {}
        for switch in entities:
            if switch.entity_id == entity_id:
                value = {"id": switch.unique_id, "active": service.data["active"]}
                switch.set_activation(value)
                switch.schedule_update_ha_state(True)
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

    hass.services.async_register(
        DOMAIN,
        SERVICE_SET_TANK_TYPE,
        set_tank_type_service,
        schema=SET_TANK_TYPE_SCHEMA,
    )

    hass.services.async_register(
        DOMAIN,
        SERVICE_SET_GAUGE_TYPE,
        set_gauge_type_service,
        schema=SET_GAUGE_TYPE_SCHEMA,
    )

    hass.services.async_register(
        DOMAIN,
        SERVICE_SET_LOW_FUEL_ALERT,
        set_low_fuel_alert_service,
        schema=SET_LOW_FUEL_ALERT_SCHEMA,
    )

    hass.services.async_register(
        DOMAIN,
        SERVICE_SET_TANK_HEIGHT,
        set_tank_height_service,
        schema=SET_TANK_HEIGHT_SCHEMA,
    )

    hass.services.async_register(
        DOMAIN,
        SERVICE_SET_FUEL_ALERT,
        set_fuel_alert_service,
        schema=SET_FUEL_ALERT_SCHEMA,
    )

    hass.services.async_register(
        DOMAIN,
        SERVICE_SET_BATTERY_ALERT,
        set_battery_alert_service,
        schema=SET_BATTERY_ALERT_SCHEMA,
    )

    hass.services.async_register(
        DOMAIN,
        SERVICE_SET_ACTIVATION,
        set_activation_service,
        schema=SET_ACTIVATION_SCHEMA,
    )

def voltage_to_percentage(voltage, type):
    """Convert voltage level from volt to percentage."""
    if type == "alkaline":
        return int((min(voltage,3.0)-2.0)/(3.0-2.0) * 100)
    else:
        return int((min(voltage,3.0)-2.2)/(3.0-2.2) * 100)

def convert(sampling):
    sample = str(sampling)
    date = datetime.fromtimestamp(int(sample[0:-3]))
    return date

def convert_to_percent(angle, low, high):
    x = angle
    x_min = 110
    if low == 5:
        x_max = 415
        delta = 55
    else:
        x_max = 406
        delta = 46
    if delta <= x and x <= 70:
        x = delta
    if 0 <= x and x <= delta:
        x = x + 360
    y = (x - x_min) / (x_max - x_min)
    lower_limit = low
    upper_limit = high
    value_range = upper_limit - lower_limit
    pct = y * value_range + lower_limit
    return round(pct)

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
        self._fuel_alert = None
        self._fuel_percent_alert = None
        self._closure_action = None
        self._rssi = None
        self._angle = None
        self._sampling = None
        self._tank_type = None
        self._tank_height = None
        self._tank_percent = None
        self._gauge_type = None
        self._temperature = None
        self._activ = True
        _LOGGER.debug("Setting up %s: %s", self._name, device_info)

    def update(self):
        if self._activ:
            if self._is_monitor:
                MONITOR_ATTRIBUTE = [ATTR_ANGLE, ATTR_TANK_PERCENT, ATTR_TANK_TYPE, ATTR_GAUGE_TYPE, ATTR_TANK_HEIGHT, ATTR_FUEL_ALERT, ATTR_BATT_ALERT, ATTR_FUEL_PERCENT_ALERT, ATTR_ERROR_CODE_SET1, ATTR_RSSI]
            else:
                MONITOR_ATTRIBUTE = []
            if self._is_leak or self._is_connected:
                LEAK_ATTRIBUTE = [ATTR_WATER_LEAK_STATUS, ATTR_ROOM_TEMPERATURE, ATTR_ROOM_TEMP_ALARM, ATTR_LEAK_ALERT, ATTR_BATTERY_TYPE, ATTR_BATT_ALERT, ATTR_TEMP_ALERT, ATTR_RSSI]
            else:
                LEAK_ATTRIBUTE = []
            if self._is_connected:
                CONNECTED_ATTRIBUTE = [ATTR_CONF_CLOSURE]
            else:
                CONNECTED_ATTRIBUTE = []

            """Get the latest data from Neviweb and update the state."""
            start = time.time()
            if self._is_gateway:
                device_status = self._client.get_device_status(self._id)
            else:
                device_data = self._client.get_device_attributes(self._id,
                UPDATE_ATTRIBUTES + MONITOR_ATTRIBUTE + LEAK_ATTRIBUTE + CONNECTED_ATTRIBUTE)
#            device_daily_stats = self._client.get_device_daily_stats(self._id)
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
                    if self._is_leak or self._is_connected:
                        self._leak_status = STATE_WATER_LEAK if \
                            device_data[ATTR_WATER_LEAK_STATUS] == STATE_WATER_LEAK else "ok"
                        self._cur_temp = device_data[ATTR_ROOM_TEMPERATURE]
                        self._leak_alert = device_data[ATTR_LEAK_ALERT]
                        self._temp_status = device_data[ATTR_ROOM_TEMP_ALARM]
                        self._temp_alert = device_data[ATTR_TEMP_ALERT]
                        self._battery_alert = device_data[ATTR_BATT_ALERT]
                        if ATTR_BATTERY_STATUS in device_data:
                            self._battery_status = device_data[ATTR_BATTERY_STATUS]
                            self._battery_type = device_data[ATTR_BATTERY_TYPE]
                        if self._is_connected:
                            self._closure_action = device_data[ATTR_CONF_CLOSURE]
                    else:
                        self._angle = device_data[ATTR_ANGLE]["value"]
                        self._sampling = device_data[ATTR_ANGLE][ATTR_SAMPLING]
                        self._tank_percent = device_data[ATTR_TANK_PERCENT]
                        self._tank_type = device_data[ATTR_TANK_TYPE]
                        self._tank_height = device_data[ATTR_TANK_HEIGHT]
                        self._gauge_type = device_data[ATTR_GAUGE_TYPE]
                        self._fuel_alert = device_data[ATTR_FUEL_ALERT]
                        self._fuel_percent_alert = device_data[ATTR_FUEL_PERCENT_ALERT]
                        self._battery_alert = device_data[ATTR_BATT_ALERT]
                        if ATTR_ERROR_CODE_SET1 in device_data:
                            self._temperature = device_data[ATTR_ERROR_CODE_SET1]["temperature"]
                    self._battery_voltage = device_data[ATTR_BATTERY_VOLTAGE]
                    if ATTR_RSSI in device_data:
                            self._rssi = device_data[ATTR_RSSI]
                    return
                _LOGGER.warning("Error in reading device %s: (%s)", self._name, device_data)
                return
            if device_data["error"]["code"] == "USRSESSEXP":
                _LOGGER.warning("Session expired... reconnecting...")
                self._client.reconnect()
            elif device_data["error"]["code"] == "ACCSESSEXC":
                _LOGGER.warning("Maximun session number reached...Close other connections to Neviweb and try again.")
                self._client.reconnect()
            elif device_data["error"]["code"] == "DVCACTNSPTD":
                _LOGGER.warning("Device action not supported...(SKU: %s) Report to maintainer.", self._sku)
            elif device_data["error"]["code"] == "DVCCOMMTO":
                _LOGGER.warning("Device Communication Timeout... The device did not respond to the server within the prescribed delay. (SKU: %s)", self._sku)
            elif device_data["error"]["code"] == "DVCBUSY":
                _LOGGER.warning("Device busy can't connect, retry later %s: %s...(SKU: %s)", self._name, device_data, self._sku)
            elif device_data["error"]["code"] == "DVCUNVLB":
                _LOGGER.warning("Device %s is disconected from Neviweb: %s...(SKU: %s)", self._name, device_data, self._sku)
                _LOGGER.warning("This device %s is de-activated and won't be polled until you put it back on HA and neviweb.",self._name)
                _LOGGER.warning("Then you will have to re-activate device %s with service.neviweb130_set_activation.",self._name)
                self._activ = False
            else:
                _LOGGER.warning("Unknown error for %s: %s...(SKU: %s) Report to maintainer.", self._name, device_data, self._sku)

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
        """Return current sensor fuel level status """
        if self._fuel_alert:
            return  "OK"
        else:
            return "Low"

    @property
    def extra_state_attributes(self):
        """Return the state attributes."""
        data = {}
        if self._is_monitor:
            data = {'Gauge_angle': self._angle,
                    'Last_sampling_time': convert(self._sampling),
                    'Battery_level': voltage_to_percentage(self._battery_voltage, "lithium"),
                    'Battery_voltage': self._battery_voltage,
                    'Battery_alert': self._battery_alert,
                    'Tank_type': self._tank_type,
                    'Tank_height': self._tank_height,
                    'Tank_percent': self._tank_percent,
                    'Gauge_type': self._gauge_type,
                    'Fuel_alert': self._fuel_alert,
                    'Fuel_percent_alert': self._fuel_percent_alert,
                    'Temperature': self._temperature,
                    'Rssi': self._rssi}
        elif self._is_leak:
            data = {'Leak_status': self._leak_status,
                    'Temperature': self._cur_temp,
                    'Temp_alarm': self._temp_status,
                    'Temperature_alert': self._temp_alert,
                    'leak_alert': self._leak_alert,
                    'Battery_level': voltage_to_percentage(self._battery_voltage, self._battery_type),
                    'Battery_voltage': self._battery_voltage,
                    'Battery_status': self._battery_status,
                    'Battery_alert': self._battery_alert,
                    'Battery_type': self._battery_type,
                    'Rssi': self._rssi}
            if self._is_connected:
                data.update({'Closure_action': self._closure_action})
        elif self._is_gateway:
            data = {'Gateway_status': self._gateway_status}
        data.update({'sku': self._sku,
                    'Activation': self._activ,
                    'device_type': self._device_type,
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
            return self._tank_percent
#            return convert_to_percent(self._angle, 10, 80)
        elif self._is_leak or self._is_connected:
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

    def set_tank_type(self, value):
        """ Set tank type for LM4110-ZB sensor. """
        tank = value["type"]
        entity = value["id"]
        self._client.set_tank_type(
            entity, tank)
        self._tank_type = tank

    def set_gauge_type(self, value):
        """ Set gauge type for LM4110-ZB sensor. """
        gauge = str(value["gauge"])
        entity = value["id"]
        self._client.set_gauge_type(
            entity, gauge)
        self._gauge_type = gauge

    def set_low_fuel_alert(self, value):
        """ Set low fuel alert limit LM4110-ZB sensor. """
        alert = value["low"]
        entity = value["id"]
        self._client.set_low_fuel_alert(
            entity, alert)
        self._fuel_percent_alert = alert

    def set_tank_height(self, value):
        """ Set low fuel alert LM4110-ZB sensor. """
        height = value["height"]
        entity = value["id"]
        self._client.set_tank_height(
            entity, height)
        self._tank_height = height

    def set_fuel_alert(self, value):
        """ Set low fuel alert LM4110-ZB sensor. """
        fuel = value["fuel"]
        entity = value["id"]
        self._client.set_fuel_alert(
            entity, fuel)
        self._fuel_alert = fuel

    def set_battery_alert(self, value):
        """ Set low battery alert LM4110-ZB sensor. """
        batt = value["batt"]
        entity = value["id"]
        self._client.set_battery_alert(
            entity, batt)
        self._battery_alert = batt

    def set_activation(self, value):
        """ Activate or deactivate neviweb polling for a missing device """
        action = value["active"]
        self._activ = action
