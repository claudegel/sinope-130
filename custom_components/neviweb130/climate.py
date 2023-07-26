"""
Support for Neviweb thermostat connected to GT130 ZigBee.
model 1123 = thermostat TH1123ZB 3000W
model 300 = thermostat TH1123ZB-G2 3000W
model 1124 = thermostat TH1124ZB 4000W
model 300 = thermostat TH1124ZB-G2 4000W
model 737 = thermostat TH1300ZB 3600W (floor)
model 7373 = thermostat TH1500ZB double pole thermostat
model 7372 = thermostat TH1400ZB low voltage
model 1124 = thermostat OTH4000-ZB Ouellet
model 737 = thermostat OTH3600-GA-ZB Ouellet
model 1134 = Thermostat TH1134ZB-HC for heating/cooling interlocking

Support for Neviweb wifi thermostats
model 1510 = thermostat TH1123WF 3000W (wifi)
model 1510 = thermostat TH1124WF 4000W (wifi)
model 738 = thermostat TH1300WF 3600W and TH1310WF (wifi floor)
model 739 = thermostat TH1400WF low voltage (wifi)
model 742 = thermostat TH1500WF double pole thermostat (wifi)

Support for Flextherm wifi thermostat
model 738 = Thermostat concerto connect FLP55 (wifi floor), (sku: FLP55), no energy stats

For more details about this platform, please refer to the documentation at
https://www.sinopetech.com/en/support/#api
"""

import logging

import voluptuous as vol
import time

import custom_components.neviweb130 as neviweb130
from . import (SCAN_INTERVAL, HOMEKIT_MODE, STAT_INTERVAL)
from homeassistant.components.climate import ClimateEntity
from homeassistant.components.climate.const import (
    HVAC_MODE_COOL,
    HVAC_MODE_HEAT,
    HVAC_MODE_OFF,
    HVAC_MODE_AUTO,
    SUPPORT_TARGET_TEMPERATURE,
    SUPPORT_PRESET_MODE,
    SUPPORT_AUX_HEAT,
    PRESET_AWAY,
    PRESET_NONE,
    PRESET_HOME,
    CURRENT_HVAC_HEAT,
    CURRENT_HVAC_IDLE,
    CURRENT_HVAC_OFF,
)
from homeassistant.const import (
    ATTR_ENTITY_ID,
    ATTR_TEMPERATURE,
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
    ATTR_ROOM_SETPOINT_AWAY,
    ATTR_WATTAGE,
    ATTR_GFCI_STATUS,
    ATTR_GFCI_ALERT,
    ATTR_FLOOR_MODE,
    ATTR_OCCUPANCY,
    ATTR_FLOOR_AUX,
    ATTR_FLOOR_OUTPUT1,
    ATTR_FLOOR_OUTPUT2,
    ATTR_KEYPAD,
    ATTR_BACKLIGHT,
    ATTR_BACKLIGHT_AUTO_DIM,
    ATTR_TIME,
    ATTR_TEMP,
    ATTR_WIFI_WATTAGE,
    ATTR_WIFI,
    ATTR_DISPLAY2,
    ATTR_WIFI_KEYPAD,
    ATTR_FLOOR_AIR_LIMIT,
    ATTR_FLOOR_MAX,
    ATTR_FLOOR_MIN,
    ATTR_ROOM_TEMP_DISPLAY,
    ATTR_EARLY_START,
    ATTR_FLOOR_SENSOR,
    ATTR_AUX_CYCLE,
    ATTR_CYCLE,
    ATTR_CYCLE_OUTPUT2,
    ATTR_PUMP_PROTEC,
    ATTR_PUMP_PROTEC_DURATION,
    ATTR_PUMP_PROTEC_PERIOD,
    ATTR_TYPE,
    ATTR_SYSTEM_MODE,
    ATTR_DRSTATUS,
    ATTR_DRACTIVE,
    ATTR_OPTOUT,
    ATTR_DRSETPOINT,
    ATTR_SETPOINT,
    ATTR_STATUS,
    ATTR_RSSI,
    ATTR_COOL_SETPOINT,
    ATTR_COOL_SETPOINT_MIN,
    ATTR_COOL_SETPOINT_MAX,
    MODE_AUTO_BYPASS,
    MODE_MANUAL,
    SERVICE_SET_CLIMATE_KEYPAD_LOCK,
    SERVICE_SET_SECOND_DISPLAY,
    SERVICE_SET_BACKLIGHT,
    SERVICE_SET_TIME_FORMAT,
    SERVICE_SET_TEMPERATURE_FORMAT,
    SERVICE_SET_SETPOINT_MAX,
    SERVICE_SET_SETPOINT_MIN,
    SERVICE_SET_FLOOR_AIR_LIMIT,
    SERVICE_SET_EARLY_START,
    SERVICE_SET_AIR_FLOOR_MODE,
    SERVICE_SET_HVAC_DR_OPTIONS,
    SERVICE_SET_HVAC_DR_SETPOINT,
    SERVICE_SET_AUXILIARY_LOAD,
    SERVICE_SET_AUX_CYCLE_OUTPUT,
    SERVICE_SET_CYCLE_OUTPUT,
    SERVICE_SET_PUMP_PROTECTION,
    SERVICE_SET_COOL_SETPOINT_MIN,
    SERVICE_SET_COOL_SETPOINT_MAX,
    SERVICE_SET_FLOOR_LIMIT_LOW,
    SERVICE_SET_FLOOR_LIMIT_HIGH,
    SERVICE_SET_ACTIVATION,
)

_LOGGER = logging.getLogger(__name__)

SUPPORT_FLAGS = (SUPPORT_TARGET_TEMPERATURE | SUPPORT_PRESET_MODE)
SUPPORT_AUX_FLAGS = (SUPPORT_TARGET_TEMPERATURE | SUPPORT_PRESET_MODE |SUPPORT_AUX_HEAT)

DEFAULT_NAME = "neviweb130 climate"
DEFAULT_NAME_2 = "neviweb130 climate 2"

PERIOD_VALUE = {"15 sec", "5 min", "10 min", "15 min", "20 min", "25 min", "30 min"}

HA_TO_NEVIWEB_PERIOD = {
    "15 sec": 15,
    "5 min": 300,
    "10 min": 600,
    "15 min": 900,
    "20 min": 1200,
    "25 min": 1500,
    "30 min": 1800
}

UPDATE_ATTRIBUTES = [
    ATTR_ROOM_SETPOINT,
    ATTR_OUTPUT_PERCENT_DISPLAY,
    ATTR_ROOM_TEMPERATURE,
    ATTR_ROOM_SETPOINT_MIN,
    ATTR_ROOM_SETPOINT_MAX,
    ATTR_ROOM_TEMP_DISPLAY,
    ATTR_TIME,
    ATTR_TEMP,
    ATTR_DRSTATUS,
    ATTR_DRSETPOINT,
]

SUPPORTED_HVAC_WIFI_MODES = [
    HVAC_MODE_OFF,
    HVAC_MODE_AUTO,
    HVAC_MODE_HEAT,
]

SUPPORTED_HVAC_MODES = [
    HVAC_MODE_OFF,
    HVAC_MODE_HEAT,
]

SUPPORTED_HVAC_HC_MODES = [
    HVAC_MODE_OFF,
    HVAC_MODE_HEAT,
    HVAC_MODE_COOL,
]

PRESET_WIFI_MODES = [
    PRESET_AWAY,
    PRESET_HOME,
    PRESET_NONE,
]

PRESET_MODES = [
    PRESET_AWAY,
    PRESET_NONE,
]

DEVICE_MODEL_LOW = [7372]
DEVICE_MODEL_LOW_WIFI = [739]
DEVICE_MODEL_FLOOR = [737]
DEVICE_MODEL_WIFI_FLOOR = [738]
DEVICE_MODEL_WIFI = [1510, 742]
DEVICE_MODEL_HEAT = [1123, 1124]
DEVICE_MODEL_DOUBLE = [7373]
DEVICE_MODEL_HEAT_G2 = [300]
DEVICE_MODEL_HC = [1134]
IMPLEMENTED_DEVICE_MODEL = DEVICE_MODEL_HEAT + DEVICE_MODEL_FLOOR + DEVICE_MODEL_LOW + DEVICE_MODEL_WIFI_FLOOR + DEVICE_MODEL_WIFI + DEVICE_MODEL_LOW_WIFI + DEVICE_MODEL_HEAT_G2 + DEVICE_MODEL_HC + DEVICE_MODEL_DOUBLE

SET_SECOND_DISPLAY_SCHEMA = vol.Schema(
    {
        vol.Required(ATTR_ENTITY_ID): cv.entity_id,
        vol.Required(ATTR_DISPLAY2): vol.In(["outsideTemperature", "default"]),
    }
)

SET_BACKLIGHT_SCHEMA = vol.Schema(
    {
        vol.Required(ATTR_ENTITY_ID): cv.entity_id,
        vol.Required(ATTR_TYPE): vol.In(["wifi", "zigbee"]),
        vol.Required(ATTR_BACKLIGHT): vol.In(["auto", "on"]),
    }
)

SET_CLIMATE_KEYPAD_LOCK_SCHEMA = vol.Schema(
    {
        vol.Required(ATTR_ENTITY_ID): cv.entity_id,
        vol.Required(ATTR_KEYPAD): vol.In(["locked", "unlocked"]),
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
        vol.Required(ATTR_TEMP): vol.In(["celcius", "fahrenheit"]),
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

SET_EARLY_START_SCHEMA = vol.Schema(
    {
        vol.Required(ATTR_ENTITY_ID): cv.entity_id,
        vol.Required(ATTR_EARLY_START): vol.In(["on", "off"]),
    }
)

SET_AIR_FLOOR_MODE_SCHEMA = vol.Schema(
    {
        vol.Required(ATTR_ENTITY_ID): cv.entity_id,
        vol.Required(ATTR_FLOOR_MODE): vol.In(["airByFloor", "roomByFloor", "floor"]),
    }
)

SET_HVAC_DR_OPTIONS_SCHEMA = vol.Schema(
    {
        vol.Required(ATTR_ENTITY_ID): cv.entity_id,
        vol.Required(ATTR_DRACTIVE): vol.In(["on", "off"]),
        vol.Required(ATTR_OPTOUT): vol.In(["on", "off"]),
        vol.Required(ATTR_SETPOINT): vol.In(["on", "off"]),
    }
)

SET_HVAC_DR_SETPOINT_SCHEMA = vol.Schema(
    {
        vol.Required(ATTR_ENTITY_ID): cv.entity_id,
        vol.Required(ATTR_STATUS): vol.In(["on", "off"]),
        vol.Required("value"): vol.All(
            vol.Coerce(float), vol.Range(min=-10, max=0)
        ),
    }
)

SET_COOL_SETPOINT_MAX_SCHEMA = vol.Schema(
    {
        vol.Required(ATTR_ENTITY_ID): cv.entity_id,
        vol.Required(ATTR_COOL_SETPOINT_MAX): vol.All(
            vol.Coerce(float), vol.Range(min=16, max=30)
        ),
    }
)

SET_COOL_SETPOINT_MIN_SCHEMA = vol.Schema(
    {
        vol.Required(ATTR_ENTITY_ID): cv.entity_id,
        vol.Required(ATTR_COOL_SETPOINT_MIN): vol.All(
            vol.Coerce(float), vol.Range(min=16, max=30)
        ),
    }
)

SET_AUXILIARY_LOAD_SCHEMA = vol.Schema(
    {
        vol.Required(ATTR_ENTITY_ID): cv.entity_id,
        vol.Required(ATTR_STATUS): vol.In(["on", "off"]),
        vol.Required("value"): vol.All(
            vol.Coerce(int), vol.Range(min=0, max=4000)
        ),
    }
)

SET_AUX_CYCLE_OUTPUT_SCHEMA = vol.Schema(
    {
        vol.Required(ATTR_ENTITY_ID): cv.entity_id,
        vol.Required(ATTR_STATUS): vol.In(["on", "off"]),
        vol.Required("value"): vol.All(
            cv.ensure_list, [vol.In(PERIOD_VALUE)]
        ),
    }
)

SET_CYCLE_OUTPUT_SCHEMA = vol.Schema(
    {
        vol.Required(ATTR_ENTITY_ID): cv.entity_id,
        vol.Required("value"): vol.All(
            cv.ensure_list, [vol.In(PERIOD_VALUE)]
        ),
    }
)

SET_PUMP_PROTECTION_SCHEMA = vol.Schema(
    {
        vol.Required(ATTR_ENTITY_ID): cv.entity_id,
        vol.Required(ATTR_STATUS): vol.In(["on", "off"]),
    }
)

SET_FLOOR_LIMIT_LOW_SCHEMA = vol.Schema(
    {
        vol.Required(ATTR_ENTITY_ID): cv.entity_id,
        vol.Required(ATTR_FLOOR_MIN): vol.All(
            vol.Coerce(float), vol.Range(min=0, max=34)
        ),
    }
)

SET_FLOOR_LIMIT_HIGH_SCHEMA = vol.Schema(
    {
        vol.Required(ATTR_ENTITY_ID): cv.entity_id,
        vol.Required(ATTR_FLOOR_MAX): vol.All(
            vol.Coerce(float), vol.Range(min=0, max=36)
        ),
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
    """Set up the neviweb130 thermostats."""
    data = hass.data[DOMAIN]

    entities = []
    for device_info in data.neviweb130_client.gateway_data:
        if "signature" in device_info and \
            "model" in device_info["signature"] and \
            device_info["signature"]["model"] in IMPLEMENTED_DEVICE_MODEL:
            device_name = "{} {}".format(DEFAULT_NAME, device_info["name"])
            device_sku = device_info["sku"]
            entities.append(Neviweb130Thermostat(data, device_info, device_name, device_sku))
    for device_info in data.neviweb130_client.gateway_data2:
        if "signature" in device_info and \
            "model" in device_info["signature"] and \
            device_info["signature"]["model"] in IMPLEMENTED_DEVICE_MODEL:
            device_name = "{} {}".format(DEFAULT_NAME_2, device_info["name"])
            device_sku = device_info["sku"]
            entities.append(Neviweb130Thermostat(data, device_info, device_name, device_sku))

    async_add_entities(entities, True)

    def set_second_display_service(service):
        """Set to outside or setpoint temperature display for wifi thermostats"""
        entity_id = service.data[ATTR_ENTITY_ID]
        value = {}
        for thermostat in entities:
            if thermostat.entity_id == entity_id:
                value = {"id": thermostat.unique_id, "display": service.data[ATTR_DISPLAY2]}
                thermostat.set_second_display(value)
                thermostat.schedule_update_ha_state(True)
                break

    def set_backlight_service(service):
        """Set backlight always on or auto"""
        entity_id = service.data[ATTR_ENTITY_ID]
        value = {}
        for thermostat in entities:
            if thermostat.entity_id == entity_id:
                value = {"id": thermostat.unique_id, "type": service.data[ATTR_TYPE], "level": service.data[ATTR_BACKLIGHT]}
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

    def set_early_start_service(service):
        """ set early heating on/off for wifi thermostat """
        entity_id = service.data[ATTR_ENTITY_ID]
        value = {}
        for thermostat in entities:
            if thermostat.entity_id == entity_id:
                value = {"id": thermostat.unique_id, "start": service.data[ATTR_EARLY_START]}
                thermostat.set_early_start(value)
                thermostat.schedule_update_ha_state(True)
                break

    def set_air_floor_mode_service(service):
        """ switch between ambiant or floor temperature sensor """
        entity_id = service.data[ATTR_ENTITY_ID]
        value = {}
        for thermostat in entities:
            if thermostat.entity_id == entity_id:
                value = {"id": thermostat.unique_id, "mode": service.data[ATTR_FLOOR_MODE]}
                thermostat.set_air_floor_mode(value)
                thermostat.schedule_update_ha_state(True)
                break

    def set_hvac_dr_options_service(service):
        """ Set options for hvac dr in Eco Sinope """
        entity_id = service.data[ATTR_ENTITY_ID]
        value = {}
        for thermostat in entities:
            if thermostat.entity_id == entity_id:
                value = {"id": thermostat.unique_id, "dractive": service.data[ATTR_DRACTIVE], "optout": service.data[ATTR_OPTOUT], "setpoint": service.data[ATTR_SETPOINT]}
                thermostat.set_hvac_dr_options(value)
                thermostat.schedule_update_ha_state(True)
                break

    def set_hvac_dr_setpoint_service(service):
        """ Set options for hvac dr setpoint in Eco Sinope """
        entity_id = service.data[ATTR_ENTITY_ID]
        value = {}
        for thermostat in entities:
            if thermostat.entity_id == entity_id:
                value = {"id": thermostat.unique_id, "status": service.data[ATTR_STATUS], "val": service.data["value"]}
                thermostat.set_hvac_dr_setpoint(value)
                thermostat.schedule_update_ha_state(True)
                break

    def set_auxiliary_load_service(service):
        """ Set options for auxilary heating """
        entity_id = service.data[ATTR_ENTITY_ID]
        value = {}
        for thermostat in entities:
            if thermostat.entity_id == entity_id:
                value = {"id": thermostat.unique_id, "status": service.data[ATTR_STATUS], "val": service.data["value"]}
                thermostat.set_auxiliary_load(value)
                thermostat.schedule_update_ha_state(True)
                break

    def set_aux_cycle_output_service(service):
        """ Set options for auxilary cycle length for low voltage thermostats """
        entity_id = service.data[ATTR_ENTITY_ID]
        value = {}
        for thermostat in entities:
            if thermostat.entity_id == entity_id:
                value = {"id": thermostat.unique_id, "status": service.data[ATTR_STATUS], "val": service.data["value"][0]}
                thermostat.set_aux_cycle_output(value)
                thermostat.schedule_update_ha_state(True)
                break

    def set_cycle_output_service(service):
        """ Set options for main cycle length for low voltage thermostats """
        entity_id = service.data[ATTR_ENTITY_ID]
        value = {}
        for thermostat in entities:
            if thermostat.entity_id == entity_id:
                value = {"id": thermostat.unique_id, "val": service.data["value"][0]}
                thermostat.set_cycle_output(value)
                thermostat.schedule_update_ha_state(True)
                break

    def set_pump_protection_service(service):
        """ Set status of pump protection for low voltage thermostats """
        entity_id = service.data[ATTR_ENTITY_ID]
        value = {}
        for thermostat in entities:
            if thermostat.entity_id == entity_id:
                value = {"id": thermostat.unique_id, "status": service.data[ATTR_STATUS]}
                thermostat.set_pump_protection(value)
                thermostat.schedule_update_ha_state(True)
                break

    def set_cool_setpoint_max_service(service):
        """ set maximum cooling setpoint for device"""
        entity_id = service.data[ATTR_ENTITY_ID]
        value = {}
        for thermostat in entities:
            if thermostat.entity_id == entity_id:
                value = {"id": thermostat.unique_id, "temp": service.data[ATTR_COOL_SETPOINT_MAX]}
                thermostat.set_cool_setpoint_max(value)
                thermostat.schedule_update_ha_state(True)
                break

    def set_cool_setpoint_min_service(service):
        """ set minimum cooling setpoint for device"""
        entity_id = service.data[ATTR_ENTITY_ID]
        value = {}
        for thermostat in entities:
            if thermostat.entity_id == entity_id:
                value = {"id": thermostat.unique_id, "temp": service.data[ATTR_COOL_SETPOINT_MIN]}
                thermostat.set_cool_setpoint_min(value)
                thermostat.schedule_update_ha_state(True)
                break

    def set_floor_limit_high_service(service):
        """ set maximum floor heating limit for floor device"""
        entity_id = service.data[ATTR_ENTITY_ID]
        value = {}
        for thermostat in entities:
            if thermostat.entity_id == entity_id:
                value = {"id": thermostat.unique_id, "level": service.data[ATTR_FLOOR_MAX], "limit": "high"}
                thermostat.set_floor_limit(value)
                thermostat.schedule_update_ha_state(True)
                break

    def set_floor_limit_low_service(service):
        """ set minimum floor heating limit for floor device"""
        entity_id = service.data[ATTR_ENTITY_ID]
        value = {}
        for thermostat in entities:
            if thermostat.entity_id == entity_id:
                value = {"id": thermostat.unique_id, "level": service.data[ATTR_FLOOR_MIN], "limit": "low"}
                thermostat.set_floor_limit(value)
                thermostat.schedule_update_ha_state(True)
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

    hass.services.async_register(
        DOMAIN,
        SERVICE_SET_EARLY_START,
        set_early_start_service,
        schema=SET_EARLY_START_SCHEMA,
    )

    hass.services.async_register(
        DOMAIN,
        SERVICE_SET_AIR_FLOOR_MODE,
        set_air_floor_mode_service,
        schema=SET_AIR_FLOOR_MODE_SCHEMA,
    )

    hass.services.async_register(
        DOMAIN,
        SERVICE_SET_HVAC_DR_OPTIONS,
        set_hvac_dr_options_service,
        schema=SET_HVAC_DR_OPTIONS_SCHEMA,
    )

    hass.services.async_register(
        DOMAIN,
        SERVICE_SET_HVAC_DR_SETPOINT,
        set_hvac_dr_setpoint_service,
        schema=SET_HVAC_DR_SETPOINT_SCHEMA,
    )

    hass.services.async_register(
        DOMAIN,
        SERVICE_SET_AUXILIARY_LOAD,
        set_auxiliary_load_service,
        schema=SET_AUXILIARY_LOAD_SCHEMA,
    )

    hass.services.async_register(
        DOMAIN,
        SERVICE_SET_AUX_CYCLE_OUTPUT,
        set_aux_cycle_output_service,
        schema=SET_AUX_CYCLE_OUTPUT_SCHEMA,
    )

    hass.services.async_register(
        DOMAIN,
        SERVICE_SET_CYCLE_OUTPUT,
        set_cycle_output_service,
        schema=SET_CYCLE_OUTPUT_SCHEMA,
    )

    hass.services.async_register(
        DOMAIN,
        SERVICE_SET_PUMP_PROTECTION,
        set_pump_protection_service,
        schema=SET_PUMP_PROTECTION_SCHEMA,
    )

    hass.services.async_register(
        DOMAIN,
        SERVICE_SET_COOL_SETPOINT_MAX,
        set_cool_setpoint_max_service,
        schema=SET_COOL_SETPOINT_MAX_SCHEMA,
    )

    hass.services.async_register(
        DOMAIN,
        SERVICE_SET_COOL_SETPOINT_MIN,
        set_cool_setpoint_min_service,
        schema=SET_COOL_SETPOINT_MIN_SCHEMA,
    )

    hass.services.async_register(
        DOMAIN,
        SERVICE_SET_FLOOR_LIMIT_HIGH,
        set_floor_limit_high_service,
        schema=SET_FLOOR_LIMIT_HIGH_SCHEMA,
    )

    hass.services.async_register(
        DOMAIN,
        SERVICE_SET_FLOOR_LIMIT_LOW,
        set_floor_limit_low_service,
        schema=SET_FLOOR_LIMIT_LOW_SCHEMA,
    )

    hass.services.async_register(
        DOMAIN,
        SERVICE_SET_ACTIVATION,
        set_activation_service,
        schema=SET_ACTIVATION_SCHEMA,
    )

def neviweb_to_ha(value):
    keys = [k for k, v in HA_TO_NEVIWEB_PERIOD.items() if v == value]
    if keys:
        return keys[0]
    return None

def temp_format_to_ha(value):
    if value == "celsius":
        return TEMP_CELSIUS
    else:
        return TEMP_FAHRENHEIT

class Neviweb130Thermostat(ClimateEntity):
    """Implementation of a Neviweb thermostat."""

    def __init__(self, data, device_info, name, sku):
        """Initialize."""
        self._name = name
        self._sku = sku
        self._client = data.neviweb130_client
        self._id = device_info["id"]
        self._model = device_info["signature"]["model"]
        self._hour_energy_kwh_count = None
        self._today_energy_kwh_count = None
        self._month_energy_kwh_count = None
        self._hour_kwh = None
        self._today_kwh = None
        self._month_kwh = None
        self._wattage = 0
        self._min_temp = 0
        self._max_temp = 0
        self._target_temp = None
        self._target_temp_away = None
        self._cur_temp = None
        self._cur_temp_before = None
        self._operation_mode = None
        self._heat_level = 0
        self._heat_source_type = None
        self._gfci_status = None
        self._gfci_alert = None
        self._floor_mode = None
        self._floor_sensor_type = None
        self._aux_heat = "off"
        self._early_start = "off"
        self._keypad = None
        self._load1 = 0
        self._load2 = 0
        self._load2_status = None
        self._rssi = None
        self._occupancy = None
        self._display2 = None
        self._backlight = None
        self._time_format = "24h"
        self._floor_air_limit = None
        self._floor_air_limit_status = None
        self._floor_max = None
        self._floor_max_status = "off"
        self._floor_min = None
        self._floor_min_status = "off"
        self._temperature_format = TEMP_CELSIUS
        self._temp_display_status = None
        self._temp_display_value = None
        self._cycle_length = 0
        self._aux_cycle_length = 0
        self._cycle_length_output2_status = "off"
        self._cycle_length_output2_value = 0
        self._pump_protec_status = None
        self._pump_protec_duration = None
        self._pump_protec_period = None
        self._drstatus_active = "off"
        self._drstatus_optout = "off"
        self._drstatus_setpoint = "off"
        self._drstatus_abs = "off"
        self._drstatus_rel = "off"
        self._drsetpoint_status = "off"
        self._drsetpoint_value = None
        self._energy_stat_time = time.time() - 1500
        self._code_reference_sensor = None
        self._code_compensation_sensor = None
        self._code_air_sensor = None
        self._code_floor_sensor = None
        self._code_wire_sensor = None
        self._code_current_overload = None
        self._code_thermal_overload = None
        self._code_load_error = None
        self._code_gfcibase = None
        self._code_end_of_life = None
        self._air_top = None
        self._air_bottom = None
        self._line_error = None
        self._inductive_mode = None
        self._target_cool = None
        self._cool_min = None
        self._cool_max = None
        self._base = None
        self._activ = True
        self._is_double = device_info["signature"]["model"] in \
            DEVICE_MODEL_DOUBLE
        self._is_hc = device_info["signature"]["model"] in \
            DEVICE_MODEL_HC
        self._is_gen2 = device_info["signature"]["model"] in \
            DEVICE_MODEL_HEAT_G2
        self._is_floor = device_info["signature"]["model"] in \
            DEVICE_MODEL_FLOOR
        self._is_wifi_floor = device_info["signature"]["model"] in \
            DEVICE_MODEL_WIFI_FLOOR
        self._is_wifi = device_info["signature"]["model"] in \
            DEVICE_MODEL_WIFI_FLOOR or device_info["signature"]["model"] in DEVICE_MODEL_WIFI or device_info["signature"]["model"] in DEVICE_MODEL_LOW_WIFI
        self._is_low_voltage = device_info["signature"]["model"] in \
            DEVICE_MODEL_LOW
        self._is_low_wifi = device_info["signature"]["model"] in \
            DEVICE_MODEL_LOW_WIFI
        _LOGGER.debug("Setting up %s: %s", self._name, device_info)

    def update(self):
        if self._activ:
            if not self._is_low_voltage and not self._is_wifi_floor:
                WATT_ATTRIBUTE = [ATTR_WATTAGE]
            else:
                WATT_ATTRIBUTE = []
            if self._is_floor or self._is_wifi_floor:
                FLOOR_ATTRIBUTE = [ATTR_GFCI_STATUS, ATTR_FLOOR_MODE, ATTR_FLOOR_AUX, ATTR_FLOOR_OUTPUT2, ATTR_FLOOR_AIR_LIMIT, ATTR_FLOOR_SENSOR]
            else:
                FLOOR_ATTRIBUTE = []
            if self._is_wifi_floor:
                WIFI_FLOOR_ATTRIBUTE = [ATTR_GFCI_ALERT, ATTR_FLOOR_MAX, ATTR_FLOOR_MIN]
            else:
                WIFI_FLOOR_ATTRIBUTE = []
            if self._is_wifi:
                WIFI_ATTRIBUTE = [ATTR_FLOOR_OUTPUT1, ATTR_WIFI_WATTAGE, ATTR_WIFI, ATTR_WIFI_KEYPAD, ATTR_DISPLAY2, ATTR_SETPOINT_MODE, ATTR_OCCUPANCY, ATTR_BACKLIGHT_AUTO_DIM, ATTR_EARLY_START, ATTR_ROOM_SETPOINT_AWAY]
            else:
                WIFI_ATTRIBUTE = [ATTR_KEYPAD, ATTR_BACKLIGHT, ATTR_SYSTEM_MODE, ATTR_CYCLE]
            if self._is_low_wifi:
                LOW_WIFI_ATTRIBUTE = [ATTR_PUMP_PROTEC, ATTR_FLOOR_AIR_LIMIT, ATTR_FLOOR_MODE, ATTR_FLOOR_SENSOR, ATTR_AUX_CYCLE, ATTR_CYCLE, ATTR_FLOOR_MAX, ATTR_FLOOR_MIN]
            else:
                LOW_WIFI_ATTRIBUTE = []
            if self._is_low_voltage:
                LOW_VOLTAGE_ATTRIBUTE = [ATTR_PUMP_PROTEC_DURATION, ATTR_PUMP_PROTEC_PERIOD, ATTR_FLOOR_AIR_LIMIT, ATTR_FLOOR_MODE, ATTR_FLOOR_SENSOR, ATTR_FLOOR_MAX, ATTR_FLOOR_MIN, ATTR_CYCLE_OUTPUT2]
            else:
                LOW_VOLTAGE_ATTRIBUTE = []
            if self._is_gen2:
                GEN2_ATTRIBUTE = [ATTR_DISPLAY2]
            else:
                GEN2_ATTRIBUTE = [ATTR_DISPLAY2, ATTR_RSSI]
            if self._is_hc:
                HC_ATTRIBUTE = [ATTR_COOL_SETPOINT, ATTR_COOL_SETPOINT_MIN, ATTR_COOL_SETPOINT_MAX, ATTR_SYSTEM_MODE, ATTR_CYCLE, ATTR_WATTAGE, ATTR_BACKLIGHT, ATTR_KEYPAD, ATTR_RSSI]
            else:
                HC_ATTRIBUTE = []
            """Get the latest data from Neviweb and update the state."""
            start = time.time()
            _LOGGER.debug("Updated attributes for %s: %s", self._name, UPDATE_ATTRIBUTES + FLOOR_ATTRIBUTE + WATT_ATTRIBUTE + WIFI_FLOOR_ATTRIBUTE + WIFI_ATTRIBUTE + LOW_WIFI_ATTRIBUTE + LOW_VOLTAGE_ATTRIBUTE + GEN2_ATTRIBUTE + HC_ATTRIBUTE)
            device_data = self._client.get_device_attributes(self._id,
                UPDATE_ATTRIBUTES + FLOOR_ATTRIBUTE + WATT_ATTRIBUTE + WIFI_FLOOR_ATTRIBUTE + WIFI_ATTRIBUTE + LOW_WIFI_ATTRIBUTE + LOW_VOLTAGE_ATTRIBUTE + GEN2_ATTRIBUTE + HC_ATTRIBUTE)
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
                    self._temp_display_value = device_data[ATTR_ROOM_TEMP_DISPLAY]
                    self._display2 = device_data[ATTR_DISPLAY2]
                    if ATTR_DRSETPOINT in device_data:
                        self._drsetpoint_status = device_data[ATTR_DRSETPOINT]["status"]
                        self._drsetpoint_value = device_data[ATTR_DRSETPOINT]["value"]
                    if ATTR_DRSTATUS in device_data:
                        self._drstatus_active = device_data[ATTR_DRSTATUS]["drActive"]
                        self._drstatus_optout = device_data[ATTR_DRSTATUS]["optOut"]
                        self._drstatus_setpoint = device_data[ATTR_DRSTATUS]["setpoint"]
                        self._drstatus_abs = device_data[ATTR_DRSTATUS]["powerAbsolute"]
                        self._drstatus_rel = device_data[ATTR_DRSTATUS]["powerRelative"]
                    if not self._is_wifi:
                        self._heat_level = device_data[ATTR_OUTPUT_PERCENT_DISPLAY]
                        self._keypad = device_data[ATTR_KEYPAD]
                        self._backlight = device_data[ATTR_BACKLIGHT]
                        if ATTR_CYCLE in device_data:
                            self._cycle_length = device_data[ATTR_CYCLE]
                        if ATTR_RSSI in device_data:
                            self._rssi = device_data[ATTR_RSSI]
                        self._operation_mode = device_data[ATTR_SYSTEM_MODE]
                        if not self._is_low_voltage:
                            self._wattage = device_data[ATTR_WATTAGE]
                        else:
                            self._floor_mode = device_data[ATTR_FLOOR_MODE]
                            self._floor_air_limit = device_data[ATTR_FLOOR_AIR_LIMIT]["value"]
                            self._floor_air_limit_status = device_data[ATTR_FLOOR_AIR_LIMIT]["status"]
                            self._cycle_length = device_data[ATTR_CYCLE]
                            self._cycle_length_output2_status = device_data[ATTR_CYCLE_OUTPUT2]["status"]
                            self._cycle_length_output2_value = device_data[ATTR_CYCLE_OUTPUT2]["value"]
                            self._floor_max = device_data[ATTR_FLOOR_MAX]["value"]
                            self._floor_max_status = device_data[ATTR_FLOOR_MAX]["status"]
                            self._floor_min = device_data[ATTR_FLOOR_MIN]["value"]
                            self._floor_min_status = device_data[ATTR_FLOOR_MIN]["status"]
                            self._pump_protec_status = device_data[ATTR_PUMP_PROTEC_DURATION]["status"]
                            if device_data[ATTR_PUMP_PROTEC_DURATION]["status"] == "on":
                                self._pump_protec_duration = device_data[ATTR_PUMP_PROTEC_DURATION]["value"]
                                self._pump_protec_period = device_data[ATTR_PUMP_PROTEC_PERIOD]["value"]
                            self._floor_sensor_type = device_data[ATTR_FLOOR_SENSOR]
                    else:
                        self._heat_level = device_data[ATTR_OUTPUT_PERCENT_DISPLAY]["percent"]
                        self._heat_source_type = device_data[ATTR_OUTPUT_PERCENT_DISPLAY]["sourceType"]
                        self._operation_mode = device_data[ATTR_SETPOINT_MODE]
                        self._occupancy = device_data[ATTR_OCCUPANCY]
                        self._keypad = device_data[ATTR_WIFI_KEYPAD]
                        self._rssi = device_data[ATTR_WIFI]
                        self._wattage = device_data[ATTR_WIFI_WATTAGE]
                        self._backlight = device_data[ATTR_BACKLIGHT_AUTO_DIM]
                        self._early_start= device_data[ATTR_EARLY_START]
                        self._target_temp_away = device_data[ATTR_ROOM_SETPOINT_AWAY]
                        self._load1 = device_data[ATTR_FLOOR_OUTPUT1]
                        self._temp_display_status = device_data[ATTR_ROOM_TEMP_DISPLAY]["status"]
                        self._temp_display_value = device_data[ATTR_ROOM_TEMP_DISPLAY]["value"]
                        if self._is_low_wifi:
                            self._floor_mode = device_data[ATTR_FLOOR_MODE]
                            self._floor_sensor_type = device_data[ATTR_FLOOR_SENSOR]
                            self._aux_cycle_length = device_data[ATTR_AUX_CYCLE]
                            self._cycle_length = device_data[ATTR_CYCLE]
                            self._floor_max = device_data[ATTR_FLOOR_MAX]["value"]
                            self._floor_max_status = device_data[ATTR_FLOOR_MAX]["status"]
                            self._floor_min = device_data[ATTR_FLOOR_MIN]["value"]
                            self._floor_min_status = device_data[ATTR_FLOOR_MIN]["status"]
                            self._floor_air_limit = device_data[ATTR_FLOOR_AIR_LIMIT]["value"]
                            self._floor_air_limit_status = device_data[ATTR_FLOOR_AIR_LIMIT]["status"]
                            self._pump_protec_status = device_data[ATTR_PUMP_PROTEC]["status"]
                            if device_data[ATTR_PUMP_PROTEC]["status"] == "on":
                                self._pump_protec_duration = device_data[ATTR_PUMP_PROTEC]["duration"]
                                self._pump_protec_period = device_data[ATTR_PUMP_PROTEC]["frequency"]
                            if ATTR_FLOOR_AIR_LIMIT in device_data:
                                self._floor_air_limit = device_data[ATTR_FLOOR_AIR_LIMIT]["value"]
                                self._floor_air_limit_status = device_data[ATTR_FLOOR_AIR_LIMIT]["status"]
                    if self._is_floor or self._is_wifi_floor:
                        self._gfci_status = device_data[ATTR_GFCI_STATUS]
                        self._floor_mode = device_data[ATTR_FLOOR_MODE]
                        self._aux_heat = device_data[ATTR_FLOOR_AUX]
                        self._floor_air_limit = device_data[ATTR_FLOOR_AIR_LIMIT]["value"]
                        self._floor_air_limit_status = device_data[ATTR_FLOOR_AIR_LIMIT]["status"]
                        self._floor_sensor_type = device_data[ATTR_FLOOR_SENSOR]
                        if ATTR_FLOOR_AIR_LIMIT in device_data:
                            self._floor_air_limit = device_data[ATTR_FLOOR_AIR_LIMIT]["value"]
                            self._floor_air_limit_status = device_data[ATTR_FLOOR_AIR_LIMIT]["status"]
                        if ATTR_FLOOR_MAX in device_data:
                            self._floor_max = device_data[ATTR_FLOOR_MAX]["value"]
                            self._floor_max_status = device_data[ATTR_FLOOR_MAX]["status"]
                        if ATTR_FLOOR_MIN in device_data:
                            self._floor_min = device_data[ATTR_FLOOR_MIN]["value"]
                            self._floor_min_status = device_data[ATTR_FLOOR_MIN]["status"]
                        if not self._is_wifi_floor:
                            self._load2_status = device_data[ATTR_FLOOR_OUTPUT2]["status"]
                            if device_data[ATTR_FLOOR_OUTPUT2]["status"] == "on":
                                self._load2 = device_data[ATTR_FLOOR_OUTPUT2]["value"]
                        else:
                            self._gfci_alert = device_data[ATTR_GFCI_ALERT]
                            self._load2 = device_data[ATTR_FLOOR_OUTPUT2]
                    if self._is_hc:
                        self._cycle_length = device_data[ATTR_CYCLE]
                        self._target_cool = device_data[ATTR_COOL_SETPOINT]
                        self._cool_min = device_data[ATTR_COOL_SETPOINT_MIN]
                        self._cool_max = device_data[ATTR_COOL_SETPOINT_MAX]
                elif device_data["errorCode"] == "ReadTimeout":
                    _LOGGER.warning("A timeout occur during data update. Device %s do not respond. Check your network... (%s)", self._name, device_data)
                else:    
                    _LOGGER.warning("Error in updating device %s: (%s)", self._name, device_data)
            elif device_data["error"]["code"] == "USRSESSEXP":
                _LOGGER.warning("Session expired... reconnecting...")
                self._client.reconnect()
            elif device_data["error"]["code"] == "ACCSESSEXC":
                _LOGGER.warning("Maximun session number reached...Close other connections and try again.")
                self._client.reconnect()
            elif device_data["error"]["code"] == "DVCACTNSPTD":
                _LOGGER.warning("Device action not supported...(SKU: %s) Report to maintainer.", self._sku)
            elif device_data["error"]["code"] == "DVCCOMMTO":
                _LOGGER.warning("Device Communication Timeout... The device did not respond to the server within the prescribed delay. (SKU: %s)", self._sku)
            elif device_data["error"]["code"] == "DVCUNVLB":
                _LOGGER.warning("Device %s is disconected from Neviweb: %s...(SKU: %s)", self._name, device_data, self._sku)
                _LOGGER.warning("This device %s is de-activated and won't be polled until you put it back on HA and neviweb.",self._name)
                _LOGGER.warning("Then you will have to re-activate device %s with service.neviweb130_set_activation.",self._name)
                self._activ = False
            elif device_data["error"]["code"] == "DVCATTRNSPTD":
                _LOGGER.warning("Device attribute not supported for %s: %s...(SKU: %s)", self._name, device_data, self._sku)
            elif device_data["error"]["code"] == "SVCERR":
                _LOGGER.warning("Service error, device not available retry later %s: %s...(SKU: %s)", self._name, device_data, self._sku)
            elif device_data["error"]["code"] == "DVCBUSY":
                _LOGGER.warning("Device busy can't reach (neviweb update ?), retry later %s: %s...(SKU: %s)", self._name, device_data, self._sku)
            else:
                _LOGGER.warning("Unknown error for %s: %s...(SKU: %s) Report to maintainer.", self._name, device_data, self._sku)
            if self._sku != "FLP55":
                if start - self._energy_stat_time > STAT_INTERVAL and self._energy_stat_time != 0:
                    device_hourly_stats = self._client.get_device_hourly_stats(self._id)
#                    _LOGGER.debug("Energy data for %s: %s, size = %s", self._sku, device_hourly_stats, len(device_hourly_stats))
                    if device_hourly_stats is not None and len(device_hourly_stats) > 1:
                        self._hour_energy_kwh_count = device_hourly_stats[1]["counter"] / 1000
                        self._hour_kwh = device_hourly_stats[1]["period"] / 1000
                    else:
                        _LOGGER.warning("Got None for device_hourly_stats")
                    device_daily_stats = self._client.get_device_daily_stats(self._id)
                    if device_daily_stats is not None and len(device_daily_stats) > 1:
                        self._today_energy_kwh_count = device_daily_stats[0]["counter"] / 1000
                        self._today_kwh = device_daily_stats[0]["period"] / 1000
                    else:
                        _LOGGER.warning("Got None for device_daily_stats")
                    device_monthly_stats = self._client.get_device_monthly_stats(self._id)
                    if device_monthly_stats is not None and len(device_monthly_stats) > 1:
                        self._month_energy_kwh_count = device_monthly_stats[0]["counter"] / 1000
                        self._month_kwh = device_monthly_stats[0]["period"] / 1000
                    else:
                        _LOGGER.warning("Got None for device_monthly_stats")
                    if not self._is_wifi and not self._is_hc:
                        device_error_code = self._client.get_device_sensor_error(self._id)
#                        _LOGGER.warning("Updating error code: %s",device_error_code)
                        if device_error_code is not None:
                            self._code_compensation_sensor = device_error_code["compensationSensor"]
                            self._code_thermal_overload = device_error_code["thermalOverload"]
                            if self._is_floor and not self._is_wifi:
                                self._code_floor_sensor = device_error_code["floorSensor"]
                                self._code_gfcibase = device_error_code["gfciBase"]
                            elif self._is_low_voltage or self._is_double:
                                self._code_air_sensor = device_error_code["airSensor"]
                                self._code_floor_sensor = device_error_code["floorSensor"]
                            elif self._is_double:
                                self._base = device_error_code["base"]
                            else:
                                self._code_wire_sensor = device_error_code["wireSensor"]
                                self._code_current_overload = device_error_code["currentOverload"]
                                self._code_end_of_life = device_error_code["endOfLife"]
                                if self._is_gen2:
                                    self._air_top = device_error_code["airTopSensor"]
                                    self._air_bottom = device_error_code["airBottomSensor"]
                                    self._line_error = device_error_code["lineError"]
                                    self._inductive_mode = device_error_code["inductiveMode"]
                                else:
                                    self._code_air_sensor = device_error_code["airSensor"]
                                    self._code_load_error = device_error_code["loadError"]
                                    self._code_reference_sensor = device_error_code["referenceSensor"]
                    self._energy_stat_time = time.time()
                if self._energy_stat_time == 0:
                    self._energy_stat_time = start
        
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
        return temp_format_to_ha(self._temperature_format)

    @property
    def device_class(self):
        """Return the device class of this entity."""
        return SensorDeviceClass.TEMPERATURE

    @property
    def extra_state_attributes(self):
        """Return the state attributes."""
        data = {}
        if not self._is_low_voltage and not self._is_low_wifi:
            data.update({'wattage': self._wattage})
        if self._is_low_voltage:
            data.update({'sensor_mode': self._floor_mode,
                    'cycle_length': neviweb_to_ha(self._cycle_length),
                    'auxiliary_cycle_status': self._cycle_length_output2_status,
                    'auxiliary_cycle_value': neviweb_to_ha(self._cycle_length_output2_value),
                    'floor_limit_high': self._floor_max,
                    'floor_limit_high_status': self._floor_max_status,
                    'floor_limit_low': self._floor_min,
                    'floor_limit_low_status': self._floor_min_status,
                    'max_air_limit': self._floor_air_limit,
                    'max_air_limit_status': self._floor_air_limit_status,
                    'floor_sensor_type': self._floor_sensor_type,
                    'pump_protection_status': self._pump_protec_status,
                    'pump_protection_duration': self._pump_protec_duration,
                    'pump_protection_frequency': self._pump_protec_period})
        if self._is_low_wifi:
            data.update({'sensor_mode': self._floor_mode,
                    'floor_sensor_type': self._floor_sensor_type,
                    'load_watt': self._wattage,
                    'auxiliary_cycle_length': self._aux_cycle_length,
                    'cycle_length': neviweb_to_ha(self._cycle_length),
                    'pump_protection_status': self._pump_protec_status,
                    'pump_protection_duration': self._pump_protec_duration,
                    'pump_protection_frequency': self._pump_protec_period})
        if self._is_floor or self._is_wifi_floor:
            data.update({'gfci_status': self._gfci_status,
                    'sensor_mode': self._floor_mode,
                    'auxiliary_heat': self._aux_heat,
                    'auxiliary_status': self._load2_status,
                    'auxiliary_load': self._load2,
                    'floor_setpoint_max': self._floor_max,
                    'floor_setpoint_low': self._floor_min,
                    'floor_air_limit': self._floor_air_limit,
                    'floor_sensor_type': self._floor_sensor_type,
                    'load_watt': self._wattage})
        if self._is_wifi_floor or self._is_low_wifi:
            data.update({'floor_limit_high': self._floor_max,
                    'floor_limit_high_status': self._floor_max_status,
                    'floor_limit_low': self._floor_min,
                    'floor_limit_low_status': self._floor_min_status,
                    'max_air_limit': self._floor_air_limit,
                    'max_air_limit_status': self._floor_air_limit_status})
        if self._is_wifi and not self._is_low_wifi:
            data.update({'occupancy': self._occupancy})
        if self._is_wifi_floor:
            data.update({'gfci_alert': self._gfci_alert})
        if self._is_wifi:
            data.update({'temp_display_status': self._temp_display_status,
                    'source_type': self._heat_source_type,
                    'early_start': self._early_start,
                    'setpoint_away': self._target_temp_away,
                    'load_watt_1': self._load1,
                    'second_display': self._display2})
        if not self._is_wifi:
            if self._is_floor:
                data.update({'status compensation sensor': self._code_compensation_sensor,
                    'status floor sensor': self._code_floor_sensor,
                    'status thermal overload': self._code_thermal_overload,
                    'status gfci base': self._code_gfcibase})
            elif not self._is_low_voltage and not self._is_double:
                data.update({'status compensation sensor': self._code_compensation_sensor,
                    'status wire sensor': self._code_wire_sensor,
                    'status current sensor': self._code_current_overload,
                    'status thermal sensor': self._code_thermal_overload,
                    'status end of life sensor': self._code_end_of_life,
                    'cycle_length': self._cycle_length})
            elif self._is_low_voltage:
                data.update({'status compensation sensor': self._code_compensation_sensor,
                            'status thermal overload': self._code_thermal_overload,
                            'status air sensor': self._code_air_sensor,
                            'status floor sensor': self._code_floor_sensor})
            elif self._is_double:
                data.update({'status compensation sensor': self._code_compensation_sensor,
                            'status thermal overload': self._code_thermal_overload,
                            'status air sensor': self._code_air_sensor,
                            'status floor sensor': self._code_floor_sensor,
                            'status base': self._base})
            if not self._is_gen2:
                data.update({'status air sensor': self._code_air_sensor})
        if self._is_gen2:
            data.update({'Status air top': self._air_top,
                    'status air bottom': self._air_bottom,
                    'status line error': self._line_error,
                    'status inductive mode': self._inductive_mode})
        elif not self._is_low_voltage:
            data.update({'status reference sensor': self._code_reference_sensor,
                    'status load sensor': self._code_load_error})
        if self._is_hc:
            data.update({'cool setpoint min': self._cool_min,
                    'cool setpoint max': self._cool_max,
                    'cool setpoint': self._target_cool,
                    'cycle_length': self._cycle_length})
        data.update({'heat_level': self._heat_level,
                    'temp_display_value': self._temp_display_value,
                    'second_display': self._display2,
                    'keypad': self._keypad,
                    'backlight': self._backlight,
                    'time_format': self._time_format,
                    'temperature_format': self._temperature_format,
                    'setpoint_max': self._max_temp,
                    'setpoint_min': self._min_temp,
                    'eco_status': self._drstatus_active,
                    'eco_optOut': self._drstatus_optout,
                    'eco_setpoint': self._drstatus_setpoint,
                    'eco_power_relative': self._drstatus_rel,
                    'eco_power_absolute': self._drstatus_abs,
                    'eco_setpoint_status': self._drsetpoint_status,
                    'eco_setpoint_value': self._drsetpoint_value,
                    'hourly_kwh_count': self._hour_energy_kwh_count,
                    'daily_kwh_count': self._today_energy_kwh_count,
                    'monthly_kwh_count': self._month_energy_kwh_count,
                    'hourly_kwh': self._hour_kwh,
                    'daily_kwh': self._today_kwh,
                    'monthly_kwh': self._month_kwh,
                    'rssi': self._rssi,
                    'sku': self._sku,
                    'Activation': self._activ,
                    'model': self._model,
                    'id': self._id})
        return data

    @property
    def supported_features(self):
        """Return the list of supported features."""
        if self._is_floor or self._is_wifi_floor or self._is_low_wifi:
            return SUPPORT_AUX_FLAGS
        else:
            return SUPPORT_FLAGS

    @property
    def is_aux_heat(self):
        """return auxilary heat state."""
        if self._aux_heat == "slave":
            return True
        elif self._cycle_length_output2_status == "on":
            return True
        elif self._aux_cycle_length > 0:
            return True
        else:
            return  False

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
        if self._operation_mode == HVAC_MODE_OFF:
            return HVAC_MODE_OFF
        elif self._operation_mode in [HVAC_MODE_AUTO, MODE_AUTO_BYPASS]:
            return HVAC_MODE_AUTO
        else:
            return HVAC_MODE_HEAT

    @property
    def hvac_modes(self):
        """Return the list of available operation modes."""
        if self._is_wifi:
            return SUPPORTED_HVAC_WIFI_MODES
        elif self._is_hc:
            return SUPPORTED_HVAC_HC_MODES
        else:
            return SUPPORTED_HVAC_MODES

    @property
    def current_temperature(self):
        """Return the room current temperature."""
        return self._cur_temp

    @property
    def target_temperature (self):
        """Return the temperature we try to reach."""
        return self._target_temp

    @property
    def preset_modes(self):
        """Return available preset modes."""
        if self._is_wifi:
            return PRESET_WIFI_MODES
        else:
            return PRESET_MODES

    @property
    def preset_mode(self):
        """Return current preset mode."""
        if self._occupancy == PRESET_HOME:
            return PRESET_NONE
        elif self._occupancy == PRESET_AWAY:
            return PRESET_AWAY
        else:
            return PRESET_NONE

    @property
    def hvac_action(self):
        """Return current HVAC action."""
        if HOMEKIT_MODE:
            if self._operation_mode == HVAC_MODE_OFF:
                return CURRENT_HVAC_OFF
            elif self._heat_level == 0:
                return CURRENT_HVAC_IDLE
            else:
                return CURRENT_HVAC_HEAT
        else:
            if self._operation_mode == HVAC_MODE_OFF:
                return CURRENT_HVAC_OFF
            elif self._operation_mode == MODE_AUTO_BYPASS:
                return MODE_AUTO_BYPASS
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
        self._display2 = display_name

    def set_backlight(self, value):
        """Set thermostat backlight «auto» = off when idle / on when active or «on» = always on"""
        """fonction differently for zigbee and wifi devices"""
        level = value["level"]
        device = value["type"]
        entity = value["id"]
        if level == "on":
            if device == "wifi":
                level_command = "alwaysOn"
            else:
                level_command = "always"
            level_name = "On"
        else:
            if device == "wifi":
                level_command = "onUserActive"
            else:
                level_command = "onActive"
            level_name = "Auto"
        self._client.set_backlight(
            entity, level_command, device)
        self._backlight = level_name

    def set_keypad_lock(self, value):
        """Lock or unlock device's keypad, locked = Locked, unlocked = Unlocked"""
        lock = value["lock"]
        entity = value["id"]
        if lock == "locked":
            lock_name = "Locked"
            if self._is_wifi:
                lock = "lock"
        else:
            lock_name = "Unlocked"
            if self._is_wifi:
                lock = "unlock"
        self._client.set_keypad_lock(
            entity, lock, self._is_wifi)
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

    def set_air_floor_mode(self, value):
        """switch temperature control between floor and ambiant sensor"""
        mode = value["mode"]
        entity = value["id"]
        self._client.set_air_floor_mode(
            entity, mode)
        self._floor_mode = mode

    def set_setpoint_max(self, value):
        """set maximum setpoint temperature"""
        temp = value["temp"]
        entity = value["id"]
        self._client.set_setpoint_max(
            entity, temp)
        self._max_temp = temp

    def set_setpoint_min(self, value):
        """ set minimum setpoint temperature. """
        temp = value["temp"]
        entity = value["id"]
        self._client.set_setpoint_min(
            entity, temp)
        self._min_temp = temp

    def set_cool_setpoint_max(self, value):
        """set maximum cooling setpoint temperature"""
        temp = value["temp"]
        entity = value["id"]
        self._client.set_cool_setpoint_max(
            entity, temp)
        self._cool_max = temp

    def set_cool_setpoint_min(self, value):
        """ set minimum cooling setpoint temperature. """
        temp = value["temp"]
        entity = value["id"]
        self._client.set_cool_setpoint_min(
            entity, temp)
        self._cool_min = temp

    def set_floor_air_limit(self, value):
        """ set maximum temperature air limit for floor thermostat. """
        temp = value["temp"]
        entity = value["id"]
        if temp == 0:
           status = "off"
        else:
            status = "on"
        self._client.set_floor_air_limit(
            entity, status, temp)
        self._floor_air_limit = temp

    def set_early_start(self, value):
        """ set early heating on/off for wifi thermostat. """
        start = value["start"]
        entity = value["id"]
        self._client.set_early_start(
            entity, start)
        self._early_start = start

    def set_hvac_dr_options(self, value):
        """ set thermostat DR options for Eco Sinope. """
        entity = value["id"]
        dr = value["dractive"]
        optout = value["optout"]
        setpoint = value["setpoint"]
        self._client.set_hvac_dr_options(
            entity, dr, optout, setpoint)
        self._drstatus_active = dr
        self._drstatus_optout = optout
        self._drstatus_setpoint = setpoint

    def set_hvac_dr_setpoint(self, value):
        """ set thermostat DR setpoint values for Eco Sinope. """
        entity = value["id"]
        status = value["status"]
        val = value["val"]
        self._client.set_hvac_dr_setpoint(
            entity, status, val)
        self._drsetpoint_status = status
        self._drsetpoint_value = val

    def set_hvac_mode(self, hvac_mode):
        """Set new hvac mode."""
        if hvac_mode == HVAC_MODE_OFF:
            self._client.set_setpoint_mode(self._id, HVAC_MODE_OFF, self._is_wifi)
        elif hvac_mode in [HVAC_MODE_HEAT, MODE_MANUAL]:
            self._client.set_setpoint_mode(self._id, hvac_mode, self._is_wifi)
        elif hvac_mode == HVAC_MODE_AUTO:
            self._client.set_setpoint_mode(self._id, HVAC_MODE_AUTO, self._is_wifi)
        elif hvac_mode == MODE_AUTO_BYPASS:
            if self._operation_mode == HVAC_MODE_AUTO:
                self._client.set_setpoint_mode(self._id, MODE_AUTO_BYPASS, self._is_wifi)
        else:
            _LOGGER.error("Unable to set hvac mode: %s.", hvac_mode)
        self._operation_mode = hvac_mode

    def set_preset_mode(self, preset_mode):
        """Activate a preset."""
        if preset_mode == self.preset_mode:
            return
        if preset_mode == PRESET_AWAY:
            self._client.set_occupancy_mode(self._id, PRESET_AWAY, self._is_wifi)
        elif preset_mode == PRESET_HOME:
            self._client.set_occupancy_mode(self._id, PRESET_HOME, self._is_wifi)
        elif preset_mode == PRESET_NONE:
            # Re-apply current hvac_mode without any preset
            self.set_hvac_mode(self.hvac_mode)
        else:
            _LOGGER.error("Unable to set preset mode: %s.", preset_mode)
        self._occupancy = preset_mode

    def turn_aux_heat_on(self):
        """Turn auxiliary heater on/off."""
        if self._is_low_voltage:
            value = "on"
            low = "voltage"
            sec = self._cycle_length_output2_value
            self._cycle_length_output2_status = "on"
        elif self._is_low_wifi:
            value = self._aux_cycle_length
            low = "wifi"
            sec = self._aux_cycle_length
        else:
            value = "slave"
            sec = 0
            low = "floor"
            self._aux_heat = "slave"
        self._client.set_aux_heat(
            self._id, value, low, sec)

    def turn_aux_heat_off(self):
        """Turn auxiliary heater on/off."""
        if self._is_low_voltage:
            low = "voltage"
            self._cycle_length_output2_status = "off"
            sec = self._cycle_length_output2_value
        elif self._is_low_wifi:
            low = "wifi"
            self._aux_cycle_length = 0
            sec = 0
        else:
            low = "floor"
            self._aux_heat = "off"
            sec = 0
        self._client.set_aux_heat(
            self._id, "off", low, sec)

    def set_auxiliary_load(self, value):
        """ set thermostat auxiliary output status and load. """
        entity = value["id"]
        status = value["status"]
        val = value["val"]
        self._client.set_auxiliary_load(
            entity, status, val)
        self._load2_status = status
        self._load2 = val

    def set_aux_cycle_output(self, value):
        """ set low voltage thermostats auxiliary cycle status and length. """
        entity = value["id"]
        status = value["status"]
        val = value["val"]
        length = [v for k, v in HA_TO_NEVIWEB_PERIOD.items() if k == val][0]
        self._client.set_aux_cycle_output(
            entity, status, length)
        self._cycle_length_output2_status = status
        self._cycle_length_output2_value = length

    def set_cycle_output(self, value):
        """ set low voltage thermostats main cycle output length. """
        entity = value["id"]
        val = value["val"]
        length = [v for k, v in HA_TO_NEVIWEB_PERIOD.items() if k == val][0]
        self._client.set_aux_cycle_output(
            entity, length)
        self._cycle_length = length

    def set_pump_protection(self, value):
        entity = value["id"]
        status = value["status"]
        self._client.set_pump_protection(
            entity, status, self._is_low_wifi)
        self._pump_protec_status = status
        self._pump_protec_duration = 60
        self._pump_protec_period = 1

    def set_floor_limit(self, value):
        """set maximum/minimum floor setpoint temperature"""
        temp = value["level"]
        entity = value["id"]
        limit = value["limit"]
        wifi = self._is_wifi_floor
        if limit == "low":
            if temp > 0 and temp < 5:
                temp = 5
        else:
            if temp > 0 and temp < 7:
                temp = 7
        self._client.set_floor_limit(
            entity, temp, limit, wifi)
        if limit == "low":
            self._floor_min = temp if temp != 0 else None
            self._floor_min_status = "on"
        else:
            self._floor_max = temp if temp != 0 else None
            self._floor_max_status = "on"

    def set_activation(self, value):
        """ Activate or deactivate neviweb polling for a missing device """
        action = value["active"]
        self._activ = action
