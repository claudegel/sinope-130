"""
Support for Neviweb switch connected via GT130 ZigBee.
Multi-Controller
model 2180 = Multi controller for sedna valve MC3100ZB connected to GT130
model 2181 = Multi controller for sedna valve MC3100ZB connected sedna valve

load controler
Support for Neviweb switch connected via GT130 ZigBee.
model 2506 = load controller device, RM3250ZB, 50A
model 2151 = Calypso load controller for water heater, RM3500ZB 20,8A
model xxxx = Calypso load controller for water heater, RM3500WF 20,8A wifi
model 2610 = wall outlet, SP2610ZB
model 2600 = portable plug, SP2600ZB

Water valves
model 3150 = VA4201WZ, sedna valve 1 inch via wifi
model 3150 = VA4200WZ, sedna valve 3/4 inch via wifi
model 3151 = VA4200ZB, sedna valve 3/4 inch via GT130, zigbee
model 3153 = VA4220ZB, sedna 2e generation 3/4 inch, zigbee
model 3150 = VA4220WZ, sedna 2e gen 3/4 inch
model 3155 = ACT4220WF-M, sedna multi-residential master valve 2e gen 3/4 inch, wifi
model 31532 = ACT4220ZB-M, sedna multi-residential slave valve 2e gen 3/4 inch, zigbee
model 3150 = VA4220WF, sedna 2e generation 3/4 inch, wifi
model 3150 = VA4221WZ, sedna 2e gen 1 inch
model 3150 = VA4221WF, sedna 2e generation 1 inch, wifi
model 3155 = ACT4221WF-M, sedna multi-residential master valve 2e gen. 1 inch, wifi
model 31532 = ACT4221ZB-M, sedna multi-residential slave valve 2e gen. 1 inch, zigbee

Flow sensors
FS4220 flow sensor 3/4 inch connected to sedna valve second gen
FS4221 flow sensor 1 inch connected to sedna valve second gen

Door lock
model 7000 = door lock

For more details about this platform, please refer to the documentation at  
https://www.sinopetech.com/en/support/#api
"""
import logging

import voluptuous as vol
import time

import custom_components.neviweb130 as neviweb130
from . import (SCAN_INTERVAL, STAT_INTERVAL)
from homeassistant.components.switch import (
    SwitchEntity,
)

from homeassistant.const import (
    ATTR_ENTITY_ID,
    TEMP_CELSIUS,
    TEMP_FAHRENHEIT,
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

from homeassistant.components.sensor import SensorDeviceClass

from homeassistant.components.binary_sensor import BinarySensorDeviceClass

from datetime import timedelta
from homeassistant.helpers.event import track_time_interval
from homeassistant.helpers.icon import icon_for_battery_level
from .const import (
    DOMAIN,
    ATTR_ALERT,
    ATTR_ONOFF,
    ATTR_ONOFF2,
    ATTR_WATTAGE_INSTANT,
    ATTR_WATTAGE,
    ATTR_BATTERY_VOLTAGE,
    ATTR_BATTERY_STATUS,
    ATTR_TIMER,
    ATTR_TIMER2,
    ATTR_KEYPAD,
    ATTR_DRSTATUS,
    ATTR_MOTOR_POS,
    ATTR_MOTOR_TARGET,
    ATTR_TEMP_ALARM,
    ATTR_BATT_ALERT,
    ATTR_TEMP_ALERT,
    ATTR_VALVE_CLOSURE,
    ATTR_DRACTIVE,
    ATTR_OPTOUT,
    ATTR_INPUT_STATUS,
    ATTR_INPUT2_STATUS,
    ATTR_EXT_TEMP,
    ATTR_REL_HUMIDITY,
    ATTR_ROOM_TEMPERATURE,
    ATTR_STATUS,
    ATTR_ERROR_CODE_SET1,
    ATTR_RSSI,
    ATTR_FLOW_METER_CONFIG,
    ATTR_VALVE_INFO,
    ATTR_STM8_ERROR,
    ATTR_WATER_LEAK_STATUS,
    ATTR_TANK_SIZE,
    ATTR_CONTROLLED_DEVICE,
    ATTR_COLD_LOAD_PICKUP,
    ATTR_ROOM_TEMPERATURE,
    ATTR_WATER_TEMP_MIN,
    ATTR_WATT_TIME_ON,
    ATTR_WATER_TEMP_TIME,
    ATTR_FLOW_MODEL_CONFIG,
    ATTR_FLOW_ALARM_TIMER,
    ATTR_FLOW_THRESHOLD,
    ATTR_FLOW_ALARM1_PERIOD,
    ATTR_FLOW_ALARM1_LENGHT,
    ATTR_FLOW_ALARM1_OPTION,
    MODE_AUTO,
    MODE_MANUAL,
    MODE_OFF,
    STATE_VALVE_STATUS,
    STATE_KEYPAD_STATUS,
    SERVICE_SET_SWITCH_KEYPAD_LOCK,
    SERVICE_SET_SWITCH_TIMER,
    SERVICE_SET_SWITCH_TIMER_2,
    SERVICE_SET_VALVE_ALERT,
    SERVICE_SET_VALVE_TEMP_ALERT,
    SERVICE_SET_LOAD_DR_OPTIONS,
    SERVICE_SET_CONTROL_ONOFF,
    SERVICE_SET_TANK_SIZE,
    SERVICE_SET_CONTROLLED_DEVICE,
    SERVICE_SET_LOW_TEMP_PROTECTION,
    SERVICE_SET_FLOW_METER_MODEL,
    SERVICE_SET_FLOW_METER_DELAY,
    SERVICE_SET_FLOW_METER_OPTIONS,
)

_LOGGER = logging.getLogger(__name__)

DEFAULT_NAME = 'neviweb130 switch'

UPDATE_ATTRIBUTES = [ATTR_ONOFF]

TANK_VALUE = {"40 gal", "50 gal", "60 gal", "80 gal"}
CONTROLLED_VALUE = {"Hot water heater", "Pool pump", "Eletric vehicle charger", "Other"}
FLOW_MODEL = {"FS4220", "FS4221", "No flow meter"}
FLOW_DURATION = {"15 min", "30 min", "45 min", "60 min", "75 min", "90 min", "3 h", "6 h", "12 h", "24 h"}

HA_TO_NEVIWEB_SIZE = {
    "40 gal": 40,
    "50 gal": 50,
    "60 gal": 60,
    "80 gal": 80
}

HA_TO_NEVIWEB_DELAY = {
    "15 min": 900,
    "30 min": 1800,
    "45 min": 2700,
    "60 min": 3600,
    "75 min": 4500,
    "90 min": 5400,
    "3 h": 10800,
    "6 h": 21600,
    "12 h": 43200,
    "24 h": 86400
}

HA_TO_NEVIWEB_CONTROLLED = {
    "Hot water heater": "hotWaterHeater",
    "Pool pump": "poolPump",
    "Eletric vehicle charger": "eletricVehicleCharger",
    "Other": "other"
}

IMPLEMENTED_WATER_HEATER_LOAD_MODEL = [2151]
IMPLEMENTED_WIFI_MESH_VALVE_MODEL = [3155]
IMPLEMENTED_ZB_MESH_VALVE_MODEL = [31532, 3153]
IMPLEMENTED_ZB_DEVICE_CONTROL = [2180]
IMPLEMENTED_SED_DEVICE_CONTROL = [2181]
IMPLEMENTED_WIFI_VALVE_MODEL = [3150]
IMPLEMENTED_ZB_VALVE_MODEL = [3151]
IMPLEMENTED_WALL_DEVICES = [2600, 2610]
IMPLEMENTED_LOAD_DEVICES = [2506]
IMPLEMENTED_DEVICE_MODEL = IMPLEMENTED_LOAD_DEVICES + IMPLEMENTED_WALL_DEVICES + IMPLEMENTED_WIFI_VALVE_MODEL + IMPLEMENTED_ZB_VALVE_MODEL + IMPLEMENTED_ZB_DEVICE_CONTROL + IMPLEMENTED_SED_DEVICE_CONTROL + IMPLEMENTED_WIFI_MESH_VALVE_MODEL + IMPLEMENTED_ZB_MESH_VALVE_MODEL + IMPLEMENTED_WATER_HEATER_LOAD_MODEL

SET_SWITCH_KEYPAD_LOCK_SCHEMA = vol.Schema(
    {
        vol.Required(ATTR_ENTITY_ID): cv.entity_id,
        vol.Required(ATTR_KEYPAD): vol.In(["locked", "unlocked"]),
    }
)

SET_SWITCH_TIMER_SCHEMA = vol.Schema(
    {
        vol.Required(ATTR_ENTITY_ID): cv.entity_id,
        vol.Required(ATTR_TIMER): vol.All(
            vol.Coerce(int), vol.Range(min=0, max=255)
        ),
    }
)

SET_SWITCH_TIMER_2_SCHEMA = vol.Schema(
    {
        vol.Required(ATTR_ENTITY_ID): cv.entity_id,
        vol.Required(ATTR_TIMER2): vol.All(
            vol.Coerce(int), vol.Range(min=0, max=255)
        ),
    }
)

SET_VALVE_ALERT_SCHEMA = vol.Schema(
    {
        vol.Required(ATTR_ENTITY_ID): cv.entity_id,
        vol.Required(ATTR_BATT_ALERT): vol.In(["true", "false"]),
    }
)

SET_VALVE_TEMP_ALERT_SCHEMA = vol.Schema(
    {
        vol.Required(ATTR_ENTITY_ID): cv.entity_id,
        vol.Required(ATTR_TEMP_ALERT): vol.All(
            vol.Coerce(int), vol.Range(min=0, max=1)
        ),
    }
)

SET_LOAD_DR_OPTIONS_SCHEMA = vol.Schema(
    {
        vol.Required(ATTR_ENTITY_ID): cv.entity_id,
        vol.Required(ATTR_DRACTIVE): vol.In(["on", "off"]),
        vol.Required(ATTR_OPTOUT): vol.In(["on", "off"]),
        vol.Required(ATTR_ONOFF): vol.In(["on", "off"]),
    }
)

SET_CONTROL_ONOFF_SCHEMA = vol.Schema(
    {
        vol.Required(ATTR_ENTITY_ID): cv.entity_id,
        vol.Required(ATTR_STATUS): vol.In(["on", "off"]),
        vol.Required("onOff_num"): vol.All(
            vol.Coerce(int), vol.Range(min=1, max=2)
        ),
    }
)

SET_TANK_SIZE_SCHEMA = vol.Schema(
    {
        vol.Required(ATTR_ENTITY_ID): cv.entity_id,
        vol.Required("value"): vol.All(
            cv.ensure_list, [vol.In(TANK_VALUE)]
        ),
    }
)

SET_CONTROLLED_DEVICE_SCHEMA = vol.Schema(
    {
        vol.Required(ATTR_ENTITY_ID): cv.entity_id,
        vol.Required("value"): vol.All(
            cv.ensure_list, [vol.In(CONTROLLED_VALUE)]
        ),
    }
)

SET_LOW_TEMP_PROTECTION_SCHEMA = vol.Schema(
    {
        vol.Required(ATTR_ENTITY_ID): cv.entity_id,
        vol.Required(ATTR_WATER_TEMP_MIN): vol.In([0, 45]),
    }
)

SET_FLOW_METER_MODEL_SCHEMA = vol.Schema(
    {
        vol.Required(ATTR_ENTITY_ID): cv.entity_id,
        vol.Required(ATTR_FLOW_MODEL_CONFIG): vol.All(
            cv.ensure_list, [vol.In(FLOW_MODEL)]
        ),
    }
)

SET_FLOW_METER_DELAY_SCHEMA= vol.Schema(
    {
        vol.Required(ATTR_ENTITY_ID): cv.entity_id,
        vol.Required(ATTR_FLOW_ALARM1_PERIOD): vol.All(
            cv.ensure_list, [vol.In(FLOW_DURATION)]
        ),
    }
)

SET_FLOW_METER_OPTIONS_SCHEMA= vol.Schema(
    {
        vol.Required(ATTR_ENTITY_ID): cv.entity_id,
        vol.Required("triggerAlarm"): vol.In(["on", "off"]),
        vol.Required("closeValve"): vol.In(["on", "off"]),
    }
)

async def async_setup_platform(
    hass,
    config,
    async_add_entities,
    discovery_info=None,
):
    """Set up the Neviweb130 switch."""
    data = hass.data[DOMAIN]

    entities = []
    for device_info in data.neviweb130_client.gateway_data:
        if "signature" in device_info and \
            "model" in device_info["signature"] and \
            device_info["signature"]["model"] in IMPLEMENTED_DEVICE_MODEL:
            device_name = '{} {}'.format(DEFAULT_NAME, device_info["name"])
            device_sku = device_info["sku"]
            entities.append(Neviweb130Switch(data, device_info, device_name, device_sku))

    async_add_entities(entities, True)

    def set_switch_keypad_lock_service(service):
        """ lock/unlock keypad device"""
        entity_id = service.data[ATTR_ENTITY_ID]
        value = {}
        for switch in entities:
            if switch.entity_id == entity_id:
                value = {"id": switch.unique_id, "lock": service.data[ATTR_KEYPAD]}
                switch.set_keypad_lock(value)
                switch.schedule_update_ha_state(True)
                break

    def set_switch_timer_service(service):
        """ set timer for switch device"""
        entity_id = service.data[ATTR_ENTITY_ID]
        value = {}
        for switch in entities:
            if switch.entity_id == entity_id:
                value = {"id": switch.unique_id, "time": service.data[ATTR_TIMER]}
                switch.set_timer(value)
                switch.schedule_update_ha_state(True)
                break

    def set_switch_timer2_service(service):
        """ set timer for switch device"""
        entity_id = service.data[ATTR_ENTITY_ID]
        value = {}
        for switch in entities:
            if switch.entity_id == entity_id:
                value = {"id": switch.unique_id, "time": service.data[ATTR_TIMER2]}
                switch.set_timer2(value)
                switch.schedule_update_ha_state(True)
                break

    def set_valve_alert_service(service):
        """ Set alert for water valve """
        entity_id = service.data[ATTR_ENTITY_ID]
        value = {}
        for switch in entities:
            if switch.entity_id == entity_id:
                value = {"id": switch.unique_id, "batt": service.data[ATTR_BATT_ALERT]}
                switch.set_valve_alert(value)
                switch.schedule_update_ha_state(True)
                break

    def set_valve_temp_alert_service(service):
        """ Set alert for water valve temperature location """
        entity_id = service.data[ATTR_ENTITY_ID]
        value = {}
        for switch in entities:
            if switch.entity_id == entity_id:
                value = {"id": switch.unique_id, "temp": service.data[ATTR_TEMP_ALERT]}
                switch.set_valve_temp_alert(value)
                switch.schedule_update_ha_state(True)
                break

    def set_load_dr_options_service(service):
        """ Set dr mode options for load controler """
        entity_id = service.data[ATTR_ENTITY_ID]
        value = {}
        for switch in entities:
            if switch.entity_id == entity_id:
                value = {"id": switch.unique_id, "dractive": service.data[ATTR_DRACTIVE], "droptout": service.data[ATTR_OPTOUT], "onoff": service.data[ATTR_ONOFF]}
                switch.set_load_dr_options(value)
                switch.schedule_update_ha_state(True)
                break

    def set_control_onOff_service(service):
        """ Set status of both onoff controler water valve """
        entity_id = service.data[ATTR_ENTITY_ID]
        value = {}
        for switch in entities:
            if switch.entity_id == entity_id:
                value = {"id": switch.unique_id, "onOff_num": service.data["onOff_num"], "status": service.data[ATTR_STATUS]}
                switch.set_control_onOff(value)
                switch.schedule_update_ha_state(True)
                break

    def set_tank_size_service(service):
        """ Set water tank size for RM3500ZB """
        entity_id = service.data[ATTR_ENTITY_ID]
        value = {}
        for switch in entities:
            if switch.entity_id == entity_id:
                value = {"id": switch.unique_id, "val": service.data["value"][0]}
                switch.set_tank_size(value)
                switch.schedule_update_ha_state(True)
                break

    def set_controlled_device_service(service):
        """ Set controlled device type for RM3250ZB """
        entity_id = service.data[ATTR_ENTITY_ID]
        value = {}
        for switch in entities:
            if switch.entity_id == entity_id:
                value = {"id": switch.unique_id, "val": service.data["value"][0]}
                switch.set_controlled_device(value)
                switch.schedule_update_ha_state(True)
                break

    def set_low_temp_protection_service(service):
        """ Set water tank temperature protection for RM3500ZB """
        entity_id = service.data[ATTR_ENTITY_ID]
        value = {}
        for switch in entities:
            if switch.entity_id == entity_id:
                value = {"id": switch.unique_id, "val": service.data[ATTR_WATER_TEMP_MIN]}
                switch.set_low_temp_protection(value)
                switch.schedule_update_ha_state(True)
                break

    def set_flow_meter_model_service(service):
        """ Set the flow meter model connected to water valve """
        entity_id = service.data[ATTR_ENTITY_ID]
        value = {}
        for switch in entities:
            if switch.entity_id == entity_id:
                value = {"id": switch.unique_id, "model": service.data[ATTR_FLOW_MODEL_CONFIG]}
                switch.set_flow_meter_model(value)
                switch.schedule_update_ha_state(True)
                break

    def set_flow_meter_delay_service(service):
        """ Set the flow meter delay before alert is turned on """
        entity_id = service.data[ATTR_ENTITY_ID]
        value = {}
        for switch in entities:
            if switch.entity_id == entity_id:
                value = {"id": switch.unique_id, "delay": service.data[ATTR_FLOW_ALARM1_PERIOD]}
                switch.set_flow_meter_delay(value)
                switch.schedule_update_ha_state(True)
                break

    def set_flow_meter_options_service(service):
        """ Set the flow meter options when leak is detected """
        entity_id = service.data[ATTR_ENTITY_ID]
        value = {}
        for switch in entities:
            if switch.entity_id == entity_id:
                value = {"id": switch.unique_id, "alarm": service.data["triggerAlarm"], "close": service.data["closeValve"]}
                switch.set_flow_meter_options(value)
                switch.schedule_update_ha_state(True)
                break

    hass.services.async_register(
        DOMAIN,
        SERVICE_SET_SWITCH_KEYPAD_LOCK,
        set_switch_keypad_lock_service,
        schema=SET_SWITCH_KEYPAD_LOCK_SCHEMA,
    )

    hass.services.async_register(
        DOMAIN,
        SERVICE_SET_SWITCH_TIMER,
        set_switch_timer_service,
        schema=SET_SWITCH_TIMER_SCHEMA,
    )

    hass.services.async_register(
        DOMAIN,
        SERVICE_SET_SWITCH_TIMER_2,
        set_switch_timer2_service,
        schema=SET_SWITCH_TIMER_2_SCHEMA,
    )

    hass.services.async_register(
        DOMAIN,
        SERVICE_SET_VALVE_ALERT,
        set_valve_alert_service,
        schema=SET_VALVE_ALERT_SCHEMA,
    )

    hass.services.async_register(
        DOMAIN,
        SERVICE_SET_VALVE_TEMP_ALERT,
        set_valve_temp_alert_service,
        schema=SET_VALVE_TEMP_ALERT_SCHEMA,
    )

    hass.services.async_register(
        DOMAIN,
        SERVICE_SET_LOAD_DR_OPTIONS,
        set_load_dr_options_service,
        schema=SET_LOAD_DR_OPTIONS_SCHEMA,
    )

    hass.services.async_register(
        DOMAIN,
        SERVICE_SET_CONTROL_ONOFF,
        set_control_onOff_service,
        schema=SET_CONTROL_ONOFF_SCHEMA,
    )

    hass.services.async_register(
        DOMAIN,
        SERVICE_SET_TANK_SIZE,
        set_tank_size_service,
        schema=SET_TANK_SIZE_SCHEMA,
    )

    hass.services.async_register(
        DOMAIN,
        SERVICE_SET_CONTROLLED_DEVICE,
        set_controlled_device_service,
        schema=SET_CONTROLLED_DEVICE_SCHEMA,
    )

    hass.services.async_register(
        DOMAIN,
        SERVICE_SET_LOW_TEMP_PROTECTION,
        set_low_temp_protection_service,
        schema=SET_LOW_TEMP_PROTECTION_SCHEMA,
    )

    hass.services.async_register(
        DOMAIN,
        SERVICE_SET_FLOW_METER_MODEL,
        set_flow_meter_model_service,
        schema=SET_FLOW_METER_MODEL_SCHEMA,
    )

    hass.services.async_register(
        DOMAIN,
        SERVICE_SET_FLOW_METER_DELAY,
        set_flow_meter_delay_service,
        schema=SET_FLOW_METER_DELAY_SCHEMA,
    )

    hass.services.async_register(
        DOMAIN,
        SERVICE_SET_FLOW_METER_OPTIONS,
        set_flow_meter_options_service,
        schema=SET_FLOW_METER_OPTIONS_SCHEMA,
    )

def voltage_to_percentage(voltage, num):
    """Convert voltage level from volt to percentage."""
    if num == 2:
        return int((min(voltage,2.7)-2.3)/(2.7-2.3) * 100)
    else:
        return int((min(voltage,6.0)-3.0)/(6.0-3.0) * 100)

def alert_to_text(alert, value):
    """Convert numeric alert activation to text"""
    if alert == 1:
        match value:
            case "bat":
                return "Activ"
            case "temp":
                return "Activ"
    else:
        match value:
            case "bat":
                return "Off"
            case "temp":
                return "Off"

def neviweb_to_ha(value):
    keys = [k for k, v in HA_TO_NEVIWEB_SIZE.items() if v == value]
    if keys:
        return keys[0]
    return None

def neviweb_to_ha_controlled(value):
    keys = [k for k, v in HA_TO_NEVIWEB_CONTROLLED.items() if v == value]
    if keys:
        return keys[0]
    return None

def neviweb_to_ha_delay(value):
    keys = [k for k, v in HA_TO_NEVIWEB_DELAY.items() if v == value]
    if keys:
        return keys[0]
    return None

def trigger_close(action, alarm):
    """No action", "Close and send", "Close only", "Send only"""
    if action:
        if alarm:
            return "Close and send"
        else:
            return "Close only"
    else:
        if alarm:
            return "Send only"
        else:
            return "No action"

def L_2_sqm(value):
    """convert liters valuer to cubic meter for water flow stat"""
    if value is not None:
        return value/1000
    else:
        return None

def model_to_HA(value):
    if value == 9887:
        return "FS4221"
    elif value == 4546:
        return "FS4220"
    else:
        return "No flow meter"

class Neviweb130Switch(SwitchEntity):
    """Implementation of a Neviweb switch."""

    def __init__(self, data, device_info, name, sku):
        """Initialize."""
        self._name = name
        self._sku = sku
        self._client = data.neviweb130_client
        self._id = device_info["id"]
        self._current_power_w = 0
        self._wattage = 0
        self._hour_energy_kwh_count = None
        self._today_energy_kwh_count = None
        self._month_energy_kwh_count = None
        self._hour_kwh = None
        self._today_kwh = None
        self._month_kwh = None
        self._onOff = None
        self._onOff2 = None
        self._is_flow = device_info["signature"]["model"] in \
            IMPLEMENTED_WIFI_MESH_VALVE_MODEL or device_info["signature"]["model"] in \
            IMPLEMENTED_ZB_MESH_VALVE_MODEL or device_info["signature"]["model"] in \
            IMPLEMENTED_WIFI_VALVE_MODEL or device_info["signature"]["model"] in \
            IMPLEMENTED_ZB_VALVE_MODEL
        self._is_tank_load = device_info["signature"]["model"] in \
            IMPLEMENTED_WATER_HEATER_LOAD_MODEL
        self._is_wifi_mesh_valve = device_info["signature"]["model"] in \
            IMPLEMENTED_WIFI_MESH_VALVE_MODEL
        self._is_zb_mesh_valve = device_info["signature"]["model"] in \
            IMPLEMENTED_ZB_MESH_VALVE_MODEL
        self._is_wall = device_info["signature"]["model"] in \
            IMPLEMENTED_WALL_DEVICES
        self._is_load = device_info["signature"]["model"] in \
            IMPLEMENTED_LOAD_DEVICES
        self._is_wifi_valve = device_info["signature"]["model"] in \
            IMPLEMENTED_WIFI_VALVE_MODEL
        self._is_zb_valve = device_info["signature"]["model"] in \
            IMPLEMENTED_ZB_VALVE_MODEL
        self._is_zb_control = device_info["signature"]["model"] in \
            IMPLEMENTED_ZB_DEVICE_CONTROL
        self._is_sedna_control = device_info["signature"]["model"] in \
            IMPLEMENTED_SED_DEVICE_CONTROL
        self._valve_status = None
        self._cur_temp = None
        self._battery_voltage = 0
        self._battery_status = None
        self._valve_closure = None
        self._timer = 0
        self._timer2 = 0
        self._keypad = None
        self._drstatus_active = "off"
        self._drstatus_optout = "off"
        self._drstatus_onoff = "off"
        self._battery_alert = None
        self._temp_alert = None
        self._humidity = None
        self._ext_temp = None
        self._room_temp = None
        self._water_temp = None
        self._input_status = None
        self._input2_status = None
        self._relayK1 = None
        self._relayK2 = None
        self._rssi = None
        self._flowmeter_multiplier = 0
        self._flowmeter_offset = 0
        self._flowmeter_divisor = 1
        self._flowmeter_model = None
        self._flowmeter_timer = 0
        self._flowmeter_threshold = 1
        self._flowmeter_alarm_lenght = 0
        self._flowmeter_alert_delay = 0
        self._flowmeter_opt_alarm = None
        self._flowmeter_opt_action = None
        self._stm8Error_motorJam = None
        self._stm8Error_motorPosition = None
        self._stm8Error_motorLimit = None
        self._motor_target = None
        self._valve_info_status = None
        self._valve_info_cause = None
        self._valve_info_id = None
        self._water_leak_status = None
        self._cold_load_status = None
        self._tank_size = None
        self._controlled_device = None
        self._energy_stat_time = time.time() - 1500
        self._water_temp_min = None
        self._watt_time_on = None
        self._water_temp_time = None
        self._stm_mcu = None
        self._temp_status = None
        _LOGGER.debug("Setting up %s: %s", self._name, device_info)

    def update(self):
        if self._is_zb_control or self._is_sedna_control:
            LOAD_ATTRIBUTE = [ATTR_ONOFF2, ATTR_BATTERY_VOLTAGE, ATTR_BATTERY_STATUS, ATTR_EXT_TEMP, ATTR_REL_HUMIDITY, ATTR_INPUT_STATUS, ATTR_INPUT2_STATUS, ATTR_ROOM_TEMPERATURE, ATTR_TIMER, ATTR_TIMER2, ATTR_RSSI]
        elif self._is_load:
            LOAD_ATTRIBUTE = [ATTR_WATTAGE_INSTANT, ATTR_WATTAGE, ATTR_TIMER, ATTR_KEYPAD, ATTR_DRSTATUS, ATTR_ERROR_CODE_SET1, ATTR_RSSI, ATTR_CONTROLLED_DEVICE]
        elif self._is_wifi_valve:
            LOAD_ATTRIBUTE = [ATTR_MOTOR_POS, ATTR_MOTOR_TARGET, ATTR_TEMP_ALARM, ATTR_VALVE_INFO, ATTR_BATTERY_VOLTAGE, ATTR_BATTERY_STATUS, ATTR_VALVE_CLOSURE, ATTR_BATT_ALERT, ATTR_STM8_ERROR, ATTR_FLOW_METER_CONFIG]
        elif self._is_zb_valve:
            LOAD_ATTRIBUTE = [ATTR_BATTERY_VOLTAGE, ATTR_BATTERY_STATUS, ATTR_RSSI]
        elif self._is_wifi_mesh_valve:
            LOAD_ATTRIBUTE = [ATTR_MOTOR_POS, ATTR_MOTOR_TARGET, ATTR_TEMP_ALARM, ATTR_VALVE_INFO, ATTR_BATTERY_STATUS, ATTR_BATTERY_VOLTAGE, ATTR_STM8_ERROR, ATTR_FLOW_METER_CONFIG, ATTR_WATER_LEAK_STATUS, ATTR_FLOW_ALARM_TIMER,
            ATTR_FLOW_THRESHOLD, ATTR_FLOW_ALARM1_PERIOD, ATTR_FLOW_ALARM1_LENGHT, ATTR_FLOW_ALARM1_OPTION]
        elif self._is_zb_mesh_valve:
            LOAD_ATTRIBUTE = [ATTR_BATTERY_VOLTAGE, ATTR_BATTERY_STATUS, ATTR_STM8_ERROR, ATTR_WATER_LEAK_STATUS, ATTR_FLOW_METER_CONFIG, ATTR_FLOW_ALARM_TIMER,
            ATTR_FLOW_THRESHOLD, ATTR_FLOW_ALARM1_PERIOD, ATTR_FLOW_ALARM1_LENGHT, ATTR_FLOW_ALARM1_OPTION]
        elif self._is_tank_load:
            LOAD_ATTRIBUTE = [ATTR_WATER_LEAK_STATUS, ATTR_ROOM_TEMPERATURE, ATTR_ERROR_CODE_SET1, ATTR_WATTAGE, ATTR_WATTAGE_INSTANT, ATTR_COLD_LOAD_PICKUP, ATTR_TANK_SIZE, ATTR_WATER_TEMP_MIN, ATTR_WATT_TIME_ON,
            ATTR_WATER_TEMP_TIME, ATTR_RSSI, ATTR_DRSTATUS]
        else:
            LOAD_ATTRIBUTE = [ATTR_WATTAGE_INSTANT]
        """Get the latest data from Neviweb and update the state."""
        start = time.time()
        device_data = self._client.get_device_attributes(self._id,
            UPDATE_ATTRIBUTES + LOAD_ATTRIBUTE)
        end = time.time()
        elapsed = round(end - start, 3)
        if self._is_zb_valve or self._is_zb_mesh_valve:
            device_alert = self._client.get_device_alert(self._id)
            _LOGGER.debug("Updating alert for %s (%s sec): %s",self._name, elapsed, device_alert)
        _LOGGER.debug("Updating %s (%s sec): %s",
            self._name, elapsed, device_data)
        if "error" not in device_data:
            if "errorCode" not in device_data:
                if self._is_wifi_valve:
                    self._valve_status = STATE_VALVE_STATUS if \
                        device_data[ATTR_MOTOR_POS] == 100 else "closed"
                    self._onOff = "on" if self._valve_status == STATE_VALVE_STATUS else MODE_OFF
                    self._temp_alert = device_data[ATTR_TEMP_ALARM]
                    self._battery_voltage = device_data[ATTR_BATTERY_VOLTAGE] if \
                        device_data[ATTR_BATTERY_VOLTAGE] is not None else 0
                    self._battery_status = device_data[ATTR_BATTERY_STATUS]
                    self._battery_alert = device_data[ATTR_BATT_ALERT]
                    if ATTR_WATER_LEAK_STATUS in device_data:
                        self._water_leak_status = device_data[ATTR_WATER_LEAK_STATUS]
                    if ATTR_MOTOR_TARGET in device_data:
                        self._motor_target = device_data[ATTR_MOTOR_TARGET]
                    if ATTR_VALVE_CLOSURE in device_data:
                        self._valve_closure = device_data[ATTR_VALVE_CLOSURE]["source"]
                    if ATTR_VALVE_INFO in device_data:
                        self._valve_info_status = device_data[ATTR_VALVE_INFO]["status"]
                        self._valve_info_cause = device_data[ATTR_VALVE_INFO]["cause"]
                        self._valve_info_id = device_data[ATTR_VALVE_INFO]["identifier"]
                    if ATTR_STM8_ERROR in device_data:
                        self._stm8Error_motorJam = device_data[ATTR_STM8_ERROR]["motorJam"]
                    if ATTR_FLOW_METER_CONFIG in device_data:
                        self._flowmeter_multiplier = device_data[ATTR_FLOW_METER_CONFIG]["multiplier"]
                        self._flowmeter_offset = device_data[ATTR_FLOW_METER_CONFIG]["offset"]
                        self._flowmeter_divisor = device_data[ATTR_FLOW_METER_CONFIG]["divisor"]
                elif self._is_zb_valve:
                    self._valve_status = STATE_VALVE_STATUS if \
                        device_data[ATTR_ONOFF] == "on" else "closed"
                    self._onOff = device_data[ATTR_ONOFF]
                    self._battery_voltage = device_data[ATTR_BATTERY_VOLTAGE] if \
                        device_data[ATTR_BATTERY_VOLTAGE] is not None else 0
                    self._battery_status = device_data[ATTR_BATTERY_STATUS]
                    if device_alert[ATTR_BATT_ALERT] in device_alert:
                        self._battery_alert = device_alert[ATTR_BATT_ALERT]
                    if device_alert[ATTR_TEMP_ALERT] in device_alert:
                        self._temp_alert = device_alert[ATTR_TEMP_ALERT]
                    if ATTR_RSSI in device_data:
                        self._rssi = device_data[ATTR_RSSI]
                elif self._is_wifi_mesh_valve:
                    self._valve_status = STATE_VALVE_STATUS if \
                        device_data[ATTR_MOTOR_POS] == 100 else "closed"
                    self._onOff = "on" if self._valve_status == STATE_VALVE_STATUS else MODE_OFF
                    self._motor_target = device_data[ATTR_MOTOR_TARGET]
                    self._temp_alert = device_data[ATTR_TEMP_ALARM]
                    if ATTR_VALVE_INFO in device_data:
                        self._valve_info_status = device_data[ATTR_VALVE_INFO]["status"]
                        self._valve_info_cause = device_data[ATTR_VALVE_INFO]["cause"]
                        self._valve_info_id = device_data[ATTR_VALVE_INFO]["identifier"]
                    self._battery_status = device_data[ATTR_BATTERY_STATUS]
                    self._battery_voltage = device_data[ATTR_BATTERY_VOLTAGE] if \
                        device_data[ATTR_BATTERY_VOLTAGE] is not None else 0
                    if ATTR_STM8_ERROR in device_data:
                        self._stm8Error_motorJam = device_data[ATTR_STM8_ERROR]["motorJam"]
                        self._stm8Error_motorLimit = device_data[ATTR_STM8_ERROR]["motorLimit"]
                        self._stm8Error_motorPosition = device_data[ATTR_STM8_ERROR]["motorPosition"]
                    if ATTR_FLOW_METER_CONFIG in device_data:
                        self._flowmeter_multiplier = device_data[ATTR_FLOW_METER_CONFIG]["multiplier"]
                        self._flowmeter_offset = device_data[ATTR_FLOW_METER_CONFIG]["offset"]
                        self._flowmeter_divisor = device_data[ATTR_FLOW_METER_CONFIG]["divisor"]
                        self._flowmeter_model = model_to_HA(self._flowmeter_multiplier)
                    self._water_leak_status = device_data[ATTR_WATER_LEAK_STATUS]
                    if ATTR_FLOW_ALARM_TIMER in device_data:
                        self._flowmeter_timer = device_data[ATTR_FLOW_ALARM_TIMER]
                        self._flowmeter_threshold = device_data[ATTR_FLOW_THRESHOLD]
                        self._flowmeter_alert_delay = neviweb_to_ha_delay(device_data[ATTR_FLOW_ALARM1_PERIOD])
                        self._flowmeter_alarm_lenght = device_data[ATTR_FLOW_ALARM1_LENGHT]
                        self._flowmeter_opt_alarm = device_data[ATTR_FLOW_ALARM1_OPTION]["triggerAlarm"]
                        self._flowmeter_opt_action = device_data[ATTR_FLOW_ALARM1_OPTION]["closeValve"]
                elif self._is_zb_mesh_valve:
                    self._valve_status = STATE_VALVE_STATUS if \
                        device_data[ATTR_ONOFF] == "on" else "closed"
                    self._onOff = device_data[ATTR_ONOFF]
                    self._battery_voltage = device_data[ATTR_BATTERY_VOLTAGE] if \
                        device_data[ATTR_BATTERY_VOLTAGE] is not None else 0
                    self._battery_status = device_data[ATTR_BATTERY_STATUS]
                    if device_alert[ATTR_BATT_ALERT] in device_alert:
                        self._battery_alert = device_alert[ATTR_BATT_ALERT]
                    if ATTR_STM8_ERROR in device_data:
                        self._stm8Error_motorJam = device_data[ATTR_STM8_ERROR]["motorJam"]
                        self._stm8Error_motorLimit = device_data[ATTR_STM8_ERROR]["motorLimit"]
                        self._stm8Error_motorPosition = device_data[ATTR_STM8_ERROR]["motorPosition"]
                    if ATTR_FLOW_METER_CONFIG in device_data:
                        self._flowmeter_multiplier = device_data[ATTR_FLOW_METER_CONFIG]["multiplier"]
                        self._flowmeter_offset = device_data[ATTR_FLOW_METER_CONFIG]["offset"]
                        self._flowmeter_divisor = device_data[ATTR_FLOW_METER_CONFIG]["divisor"]
                        self._flowmeter_model = model_to_HA(self._flowmeter_multiplier)
                    self._water_leak_status = device_data[ATTR_WATER_LEAK_STATUS]
                    if ATTR_FLOW_ALARM_TIMER in device_data:
                        self._flowmeter_timer = device_data[ATTR_FLOW_ALARM_TIMER]
                        self._flowmeter_threshold = device_data[ATTR_FLOW_THRESHOLD]
                        self._flowmeter_alert_delay = neviweb_to_ha_delay(device_data[ATTR_FLOW_ALARM1_PERIOD])
                        self._flowmeter_alarm_lenght = device_data[ATTR_FLOW_ALARM1_LENGHT]
                        self._flowmeter_opt_alarm = device_data[ATTR_FLOW_ALARM1_OPTION]["triggerAlarm"]
                        self._flowmeter_opt_action = device_data[ATTR_FLOW_ALARM1_OPTION]["closeValve"]
                elif self._is_load: #for is_load
                    self._current_power_w = device_data[ATTR_WATTAGE_INSTANT]
                    self._wattage = device_data[ATTR_WATTAGE]
                    self._keypad = STATE_KEYPAD_STATUS if \
                        device_data[ATTR_KEYPAD] == STATE_KEYPAD_STATUS else "locked" 
                    self._timer = device_data[ATTR_TIMER]
                    self._onOff = device_data[ATTR_ONOFF]
                    if ATTR_DRSTATUS in device_data:
                        self._drstatus_active = device_data[ATTR_DRSTATUS]["drActive"]
                        self._drstatus_optout = device_data[ATTR_DRSTATUS]["optOut"]
                        self._drstatus_onoff = device_data[ATTR_DRSTATUS]["onOff"]
                    if ATTR_ERROR_CODE_SET1 in device_data:
                        self._relayK1 = device_data[ATTR_ERROR_CODE_SET1]["relayK1"]
                        self._relayK2 = device_data[ATTR_ERROR_CODE_SET1]["relayK2"]
                    if ATTR_RSSI in device_data:
                        self._rssi = device_data[ATTR_RSSI]
                    self._controlled_device = device_data[ATTR_CONTROLLED_DEVICE]
                elif self._is_tank_load:
                    self._onOff = device_data[ATTR_ONOFF]
                    self._water_leak_status = device_data[ATTR_WATER_LEAK_STATUS]
                    self._water_temp = device_data[ATTR_ROOM_TEMPERATURE]
                    if ATTR_ERROR_CODE_SET1 in device_data:
                        self._temp_status = device_data[ATTR_ERROR_CODE_SET1]["temperature"]
                        self._stm_mcu = device_data[ATTR_ERROR_CODE_SET1]["stm_mcu"]
                    self._wattage = device_data[ATTR_WATTAGE]
                    self._current_power_w = device_data[ATTR_WATTAGE_INSTANT]
                    self._cold_load_status = device_data[ATTR_COLD_LOAD_PICKUP]
                    self._rssi = device_data[ATTR_RSSI]
                    self._tank_size = device_data[ATTR_TANK_SIZE]
                    if ATTR_DRSTATUS in device_data:
                        self._drstatus_active = device_data[ATTR_DRSTATUS]["drActive"]
                        self._drstatus_optout = device_data[ATTR_DRSTATUS]["optOut"]
                        self._drstatus_onoff = device_data[ATTR_DRSTATUS]["onOff"]
                    self._water_temp_min = device_data[ATTR_WATER_TEMP_MIN]
                    self._watt_time_on = device_data[ATTR_WATT_TIME_ON]
                    self._water_temp_time = device_data[ATTR_WATER_TEMP_TIME]
                elif self._is_zb_control or self._is_sedna_control:
                    self._onOff = device_data[ATTR_ONOFF]
                    self._onOff2 = device_data[ATTR_ONOFF2]
                    self._battery_status = device_data[ATTR_BATTERY_STATUS]
                    self._battery_voltage = device_data[ATTR_BATTERY_VOLTAGE]
                    self._input_status = device_data[ATTR_INPUT_STATUS]
                    self._input2_status = device_data[ATTR_INPUT2_STATUS]
                    self._humidity = device_data[ATTR_REL_HUMIDITY]
                    self._room_temp = device_data[ATTR_ROOM_TEMPERATURE]
                    self._ext_temp = device_data[ATTR_EXT_TEMP]
                    self._timer = device_data[ATTR_TIMER]
                    self._timer2 = device_data[ATTR_TIMER2]
                    if ATTR_RSSI in device_data:
                        self._rssi = device_data[ATTR_RSSI]
                else: #for is_wall
                    self._current_power_w = device_data[ATTR_WATTAGE_INSTANT]
                    self._onOff = device_data[ATTR_ONOFF]
            else:
                _LOGGER.warning("Error in reading device %s: (%s)", self._name, device_data)
        elif device_data["error"]["code"] == "USRSESSEXP":
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
        if self._is_load or self._is_wall or self._is_flow or self._is_tank_load:
            if start - self._energy_stat_time > STAT_INTERVAL and self._energy_stat_time != 0:
                device_hourly_stats = self._client.get_device_hourly_stats(self._id)
                if device_hourly_stats is not None:
                    self._hour_energy_kwh_count = device_hourly_stats[1]["counter"] / 1000
                    self._hour_kwh = device_hourly_stats[1]["period"] / 1000
                else:
                    _LOGGER.warning("Got None for device_hourly_stats")
                device_daily_stats = self._client.get_device_daily_stats(self._id)
                if device_daily_stats is not None:
                    self._today_energy_kwh_count = device_daily_stats[0]["counter"] / 1000
                    self._today_kwh = device_daily_stats[0]["period"] / 1000
                else:
                    _LOGGER.warning("Got None for device_daily_stats")
                device_monthly_stats = self._client.get_device_monthly_stats(self._id)
                if device_monthly_stats is not None:
                    self._month_energy_kwh_count = device_monthly_stats[0]["counter"] / 1000
                    self._month_kwh = device_monthly_stats[0]["period"] / 1000
                else:
                    _LOGGER.warning("Got None for device_monthly_stats")
                self._energy_stat_time = time.time()
            if self._energy_stat_time == 0:
                self._energy_stat_time = start

    @property
    def unique_id(self):
        """Return unique ID based on Neviweb device ID."""
        return self._id

    @property
    def name(self):
        """Return the name of the switch."""
        return self._name

    @property
    def device_class(self):
        """Return the device class of this entity."""
        if self._is_wifi_valve or self._is_zb_valve or self._is_wifi_mesh_valve or self._is_zb_mesh_valve:
            return BinarySensorDeviceClass.MOISTURE
        else:
            return SensorDeviceClass.POWER

    @property  
    def is_on(self):
        """Return current operation i.e. ON, OFF """
        if self._is_zb_control:
            if self._onOff != MODE_OFF or self._onOff2 != MODE_OFF:
                return True
            else:
                return False
        else:
            return self._onOff != MODE_OFF

    def turn_on(self, **kwargs):
        """Turn the device on."""
        if self._is_wifi_valve or self._is_wifi_mesh_valve:
            self._client.set_valve_onOff(self._id, 100)
            self._valve_status = "open"
        else:
            self._client.set_onOff(self._id, "on")
            if self._is_zb_valve or self._is_zb_mesh_valve:
                self._valve_status = "open"
        self._onOff = "on"

    def turn_off(self, **kwargs):
        """Turn the device off."""
        if self._is_wifi_valve or self._is_wifi_mesh_valve:
            self._client.set_valve_onOff(self._id, 0)
            self._valve_status = "closed"
        else:
            self._client.set_onOff(self._id, "off")
            if self._is_zb_valve or self._is_zb_mesh_valve:
                self._valve_status = "closed"
        self._onOff = MODE_OFF

    @property  
    def valve_status(self):
        """Return current valve status, open or closed"""
        return self._valve_status != None

    @property  
    def keypad_status(self):
        """Return current keypad status, unlocked or locked"""
        return self._keypad_status != None

    @property
    def current_temperature(self):
        """Return the current valve or controler temperature."""
        if self._is_zb_control or self._is_sedna_control or self._is_tank_load:
            return self._room_temp
        else:
            return self._cur_temp

    @property
    def extra_state_attributes(self):
        """Return the extra state attributes."""
        data = {}
        if self._is_load:
            data = {'onOff': self._onOff,
                   'Controlled_device': neviweb_to_ha_controlled(self._controlled_device),
                   'Wattage': self._wattage,
                   'Wattage_instant': self._current_power_w,
                   'hourly_kwh_count': self._hour_energy_kwh_count,
                   'daily_kwh_count': self._today_energy_kwh_count,
                   'monthly_kwh_count': self._month_energy_kwh_count,
                   'hourly_kwh': self._hour_kwh,
                   'daily_kwh': self._today_kwh,
                   'monthly_kwh': self._month_kwh,
                   'Keypad': self._keypad,
                   'Timer': self._timer,
                   'eco_status': self._drstatus_active,
                   'eco_optOut': self._drstatus_optout,
                   'eco_onoff': self._drstatus_onoff,
                   'RelayK1': self._relayK1,
                   'RelayK2': self._relayK2,
                   'Rssi': self._rssi}
        elif self._is_tank_load:
            data = {'onOff': self._onOff,
                   'Wattage': self._wattage,
                   'Wattage_instant': self._current_power_w,
                   'hourly_kwh_count': self._hour_energy_kwh_count,
                   'daily_kwh_count': self._today_energy_kwh_count,
                   'monthly_kwh_count': self._month_energy_kwh_count,
                   'hourly_kwh': self._hour_kwh,
                   'daily_kwh': self._today_kwh,
                   'monthly_kwh': self._month_kwh,
                   'Water_leak_status': self._water_leak_status,
                   'Water_temperature': self._water_temp,
                   'Cold_load_pickup_status': self._cold_load_status,
                   'Tank_size': neviweb_to_ha(self._tank_size),
                   'Temperature_status': self._temp_status,
                   'Stm_Mcu': self._stm_mcu,
                   'eco_status': self._drstatus_active,
                   'eco_optOut': self._drstatus_optout,
                   'eco_onoff': self._drstatus_onoff,
                   'Water_temp_min': self._water_temp_min,
                   'Water_time_on': self._watt_time_on,
                   'Water_temp_time': self._water_temp_time,
                   'Rssi': self._rssi}
        elif self._is_wifi_valve:
            data = {'Valve_status': self._valve_status,
                   'Temperature_alert': self._temp_alert,
                   'Battery_level': voltage_to_percentage(self._battery_voltage, 4),
                   'Battery_voltage': self._battery_voltage,
                   'Battery_status': self._battery_status,
                   'Valve_closure_source': self._valve_closure,
                   'Battery_alert': self._battery_alert,
                   'Motor_target_position': self._motor_target,
                   'Water_leak_status': self._water_leak_status,
                   'Valve_status': self._valve_info_status,
                   'Valve_cause': self._valve_info_cause,
                   'Valve_info_id': self._valve_info_id,
                   'Alert_motor_jam': self._stm8Error_motorJam,
                   'Flow_meter_multiplier': self._flowmeter_multiplier,
                   'Flow_meter_offset': self._flowmeter_offset,
                   'Flow_meter_divisor': self._flowmeter_divisor,
                   'hourly_flow_count': L_2_sqm(self._hour_energy_kwh_count),
                   'daily_flow_count': L_2_sqm(self._today_energy_kwh_count),
                   'monthly_flow_count': L_2_sqm(self._month_energy_kwh_count),
                   'hourly_flow': L_2_sqm(self._hour_kwh),
                   'daily_flow': L_2_sqm(self._today_kwh),
                   'monthly_flow': L_2_sqm(self._month_kwh)}
        elif self._is_zb_valve:
            data = {'Valve_status': self._valve_status,
                   'Battery_level': voltage_to_percentage(self._battery_voltage, 4),
                   'Battery_voltage': self._battery_voltage,
                   'Battery_status': self._battery_status,
                   'Battery_alert': alert_to_text(self._battery_alert, "bat"),
                   'Temperature_alert': alert_to_text(self._temp_alert, "temp")}
        elif self._is_wifi_mesh_valve:
            data = {'Valve_status': self._valve_status,
                   'Motor_target_position': self._motor_target,
                   'Temperature_alert': self._temp_alert,
                   'Valve_status': self._valve_info_status,
                   'Valve_cause': self._valve_info_cause,
                   'Valve_info_id': self._valve_info_id,
                   'Battery_level': voltage_to_percentage(self._battery_voltage, 4),
                   'Battery_voltage': self._battery_voltage,
                   'Battery_status': self._battery_status,
                   'Alert_motor_jam': self._stm8Error_motorJam,
                   'Alert_motor_position': self._stm8Error_motorPosition,
                   'Alert_motor_limit': self._stm8Error_motorLimit,
                   'Flow_meter_multiplier': self._flowmeter_multiplier,
                   'Flow_meter_offset': self._flowmeter_offset,
                   'Flow_meter_divisor': self._flowmeter_divisor,
                   'Flow_meter_model': self._flowmeter_model,
                   'Flow_meter_alert_delay': self._flowmeter_alert_delay,
                   'Flowmeter_options': trigger_close(self._flowmeter_opt_action, self._flowmeter_opt_alarm),
                   'Water_leak_status': self._water_leak_status}
        elif self._is_zb_mesh_valve:
            data = {'Valve_status': self._valve_status,
                   'Battery_level': voltage_to_percentage(self._battery_voltage, 4),
                   'Battery_voltage': self._battery_voltage,
                   'Battery_status': self._battery_status,
                   'Alert_motor_jam': self._stm8Error_motorJam,
                   'Alert_motor_position': self._stm8Error_motorPosition,
                   'Alert_motor_limit': self._stm8Error_motorLimit,
                   'Flow_meter_multiplier': self._flowmeter_multiplier,
                   'Flow_meter_offset': self._flowmeter_offset,
                   'Flow_meter_divisor': self._flowmeter_divisor,
                   'Flow_meter_model': self._flowmeter_model,
                   'Flow_meter_alert_delay': self._flowmeter_alert_delay,
                   'Flowmeter_options': trigger_close(self._flowmeter_opt_action, self._flowmeter_opt_alarm),
                   'Water_leak_status': self._water_leak_status,
                   'Battery_alert': alert_to_text(self._battery_alert, "bat")}
        elif self._is_zb_control or self._is_sedna_control:
            data = {'Battery_level': voltage_to_percentage(self._battery_voltage, 2),
                   'Battery_voltage': self._battery_voltage,
                   'Battery_status': self._battery_status,
                   'Extern_temperature': self._ext_temp,
                   'Room_humidity': self._humidity,
                   'Timer': self._timer,
                   'Timer2': self._timer2,
                   'Input1_status': self._input_status,
                   'Input2_status': self._input2_status,
                   'onOff': self._onOff,
                   'onOff2': self._onOff2,
                   'Room_temperature': self._room_temp,
                   'Rssi': self._rssi}
        else:
            data = {'onOff': self._onOff,
                   'Wattage_instant': self._current_power_w,
                   'hourly_kwh_count': self._hour_energy_kwh_count,
                   'daily_kwh_count': self._today_energy_kwh_count,
                   'monthly_kwh_count': self._month_energy_kwh_count,
                   'hourly_kwh': self._hour_kwh,
                   'daily_kwh': self._today_kwh,
                   'monthly_kwh': self._month_kwh}
        data.update({'sku': self._sku,
                    'id': self._id})
        return data

    @property
    def battery_voltage(self):
        """Return the current battery voltage of the valve in %."""
        if self._is_zb_control or self._is_sedna_control:
            type = 2
        else:
            type = 4
        return voltage_to_percentage(self._battery_voltage, type)

    @property
    def is_standby(self):
        """Return true if device is in standby."""
        return self._current_power_w == 0

    def set_control_onOff(self, value):
        """Set onOff or onOff2 to on or off"""
        entity = value["id"]
        onoff_no = value["onOff_num"]
        status = value["status"]
        self._client.set_control_onOff(
            entity, onoff_no, status)
        if onoff_no == 1:
            self._onOff = status
        else:
            self._onOff2 = status

    def set_keypad_lock(self, value):
        """Lock or unlock device's keypad, lock = locked, unlock = unlocked"""
        lock = value["lock"]
        entity = value["id"]
        if lock == "locked":
            lock_name = "Locked"
        else:
            lock_name = "Unlocked"
        self._client.set_keypad_lock(
            entity, lock)
        self._keypad = lock_name

    def set_timer(self, value):
        """Set device timer, 0 = off, 1 to 255 = timer length"""
        time = value["time"]
        entity = value["id"]
        self._client.set_timer(
            entity, time)
        self._timer = time

    def set_timer2(self, value):
        """Set device timer 2 for Multi controller, 0 = off, 1 to 255 = timer length"""
        time = value["time"]
        entity = value["id"]
        self._client.set_timer2(
            entity, time)
        self._timer2 = time

    def set_valve_alert(self, value):
        """ Set valve batt alert action"""
        if self._is_zb_valve or self._is_zb_mesh_valve:
            if value["batt"] == "true":
                batt = 1
            else:
                batt = 0;
        else:
            batt = value["batt"]
        entity = value["id"]
        self._client.set_valve_alert(
            entity, batt)
        self._battery_alert = batt

    def set_valve_temp_alert(self, value):
        """ Set valve temperature alert action """
        temp = value["temp"]
        entity = value["id"]
        self._client.set_valve_temp_alert(
            entity, temp)
        self._temp_alert = temp

    def set_load_dr_options(self, value):
        """ set load controler Éco Sinopé attributes """
        onoff = value["onoff"]
        optout = value["optout"]
        dr = value["dractive"]
        self._client.set_load_dr_options(
            entity, onoff, optout, dr)
        self._drstatus_active = dr
        self._drstatus_optout = optout
        self._drstatus_onoff = onoff

    def set_tank_size(self, value):
        """ set water tank size for RM3500ZB Calypso controler. """
        entity = value["id"]
        val = value["val"]
        size = [v for k, v in HA_TO_NEVIWEB_SIZE.items() if k == val][0]
        self._client.set_tank_size(
            entity, size)
        self._tank_size = size

    def set_controlled_device(self, value):
        """ set device name controlled by RM3250ZB load controler. """
        entity = value["id"]
        val = value["val"]
        tipe = [v for k, v in HA_TO_NEVIWEB_CONTROLLED.items() if k == val][0]
        self._client.set_controlled_device(
            entity, tipe)
        self._controlled_device = tipe

    def set_low_temp_protection(self, value):
        """ Set water temperature protection for Calypso """
        temp = value["val"]
        entity = value["id"]
        self._client.set_low_temp_protection(
            entity, temp)
        self._water_temp_min = temp

    def set_flow_meter_model(self, value):
        """ Set water valve flow meter model connected """
        model = value["model"]
        entity = value["id"]
        self._client.set_flow_meter_model(entity, model)
        self._flowmeter_model = model

    def set_flow_meter_delay(self, value):
        """ Set water valve flow meter delay befor alert """
        val = value["delay"]
        delay = [v for k, v in HA_TO_NEVIWEB_DELAY.items() if k == val][0]
        entity = value["id"]
        self._client.set_flow_meter_delay(entity, delay)
        self._flowmeter_alert_delay = val

    def set_flow_meter_options(self, value):
        """ Set water valve flow meter options when leak detected """
        if value["alarm"] == "on":
            alarm = True
        else:
            alarm = False
        if value["close"] == "on":
            action = True
        else:
            action = False
        if not alarm and not action:
            lenght = 0
            threshold = 0
        else:
            lenght = 60
            threshold = 1
        entity = value["id"]
        self._client.set_flow_meter_action(entity, alarm, action, lenght, threshold)
        self._flowmeter_opt_alarm = alarm
        self._flowmeter_opt_action = action
        self._flowmeter_threshold = threshold
        self._flowmeter_alarm_lenght = lenght
