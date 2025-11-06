"""
Support for Neviweb thermostat connected to GT130 Zigbee.
model 1123 = thermostat TH1123ZB 3000W
model 300 = thermostat TH1123ZB-G2 3000W
model 1124 = thermostat TH1124ZB 4000W
model 300 = thermostat TH1124ZB-G2 4000W
model 737 = thermostat TH1300ZB 3600W (floor)
model 737 = thermostat TH1320ZB-04 (floor)
model 7373 = thermostat TH1500ZB double pole thermostat
model 7372 = thermostat TH1400ZB low voltage
model 7372 = thermostat TH1420ZB-01 Nordik low voltage radiant hydroponic floor thermostat
model 1124 = thermostat OTH4000-ZB Ouellet
model 737 = thermostat OTH3600-GA-ZB Ouellet
model 1512 = Thermostat TH1134ZB-HC for heating/cooling interlocking

Support for Neviweb Wi-Fi thermostats
model 1510 = thermostat TH1123WF 3000W (Wi-Fi)
model 1510 = thermostat TH1124WF 4000W (Wi-Fi)
model 336 = thermostat TH1133WF 3000W (Wi-Fi lite) Three wires connection
model 336 = thermostat TH1133CR Sinopé Evo 3000W (Wi-Fi lite)
model 336 = thermostat TH1134WF 4000W (Wi-Fi lite) three wires connection
model 336 = thermostat TH1134CR Sinopé Evo 4000W (Wi-Fi lite)
model 350 = thermostat TH1143WF 3000W (Wi-Fi) two wires connection, color screen
model 350 = thermostat TH1144WF 4000W (Wi-Fi) two wires connection, color screen
model 738 = thermostat TH1300WF 3600W, TH1325WF, TH1310WF, SRM40, True Comfort (Wi-Fi floor)
model 739 = thermostat TH1400WF low voltage (Wi-Fi)
model 742 = thermostat TH1500WF double pole thermostat (Wi-Fi)
model 6727 = thermostat TH6500WF heat/cool (Wi-Fi)
model 6727 = thermostat TH6510WF heat/cool (Wi-Fi)
model 6730 = thermostat TH6250WF heat/cool (Wi-Fi)
model 6730 = thermostat TH6250WF-PRO heat/cool (Wi-Fi)

Support for Flextherm Wi-Fi thermostat
model 738 = Thermostat Flextherm concerto connect FLP55 (Wi-Fi floor), (sku: FLP55), no energy stats

Support for heat pump interfaces
model 6810 = HP6000ZB-GE for Ouellet heat pump with Gree connector
model 6811 = HP6000ZB-MA for Ouellet Convectair heat pump with Midea connector
model 6812 = HP6000ZB-HS for Hisense, Haxxair and Zephyr heat pump

For more details about this platform, please refer to the documentation at
https://www.sinopetech.com/en/support/#api
"""

from __future__ import annotations

import logging
import time
from datetime import date, datetime, timezone
from threading import Lock
from typing import Any, Mapping, override

from homeassistant.components.climate import ClimateEntity, ClimateEntityFeature, HVACAction, HVACMode
from homeassistant.components.climate.const import (
    ATTR_TARGET_TEMP_HIGH,
    ATTR_TARGET_TEMP_LOW,
    PRESET_AWAY,
    PRESET_BOOST,
    PRESET_HOME,
    PRESET_NONE,
)
from homeassistant.components.persistent_notification import DOMAIN as PN_DOMAIN
from homeassistant.components.sensor import SensorDeviceClass
from homeassistant.const import ATTR_ENTITY_ID, ATTR_TEMPERATURE, UnitOfTemperature
from homeassistant.core import ServiceCall
from homeassistant.exceptions import ServiceValidationError

from . import NOTIFY
from . import SCAN_INTERVAL as scan_interval
from . import STAT_INTERVAL
from .const import (
    ATTR_ACCESSORY_TYPE,
    ATTR_ACTIVE,
    ATTR_AIR_ACTIVATION_TEMP,
    ATTR_AIR_CONFIG,
    ATTR_AIR_EX_MIN_TIME_ON,
    ATTR_AIR_MAX_POWER_TEMP,
    ATTR_AUX_CYCLE_LENGTH,
    ATTR_AUX_HEAT_MIN_TIME_OFF,
    ATTR_AUX_HEAT_MIN_TIME_ON,
    ATTR_AUX_HEAT_SOURCE_TYPE,
    ATTR_AUX_HEAT_START_DELAY,
    ATTR_AUX_INTERSTAGE_DELAY,
    ATTR_AUX_INTERSTAGE_MIN_DELAY,
    ATTR_AUX_OPTIM,
    ATTR_AVAIL_MODE,
    ATTR_BACK_LIGHT,
    ATTR_BACKLIGHT,
    ATTR_BACKLIGHT_AUTO_DIM,
    ATTR_BALANCE_PT,
    ATTR_BALANCE_PT_TEMP_HIGH,
    ATTR_BALANCE_PT_TEMP_LOW,
    ATTR_COLD_LOAD_PICKUP,
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
    ATTR_DISPLAY_CAP,
    ATTR_DISPLAY_CONF,
    ATTR_DRACCESORYCONF,
    ATTR_DRACTIVE,
    ATTR_DRAIR_CURT_CONF,
    ATTR_DRAUXCONF,
    ATTR_DRFANCONF,
    ATTR_DRSETPOINT,
    ATTR_DRSTATUS,
    ATTR_DUAL_STATUS,
    ATTR_EARLY_START,
    ATTR_FAN_CAP,
    ATTR_FAN_FILTER_LIFE,
    ATTR_FAN_FILTER_REMAIN,
    ATTR_FAN_SPEED,
    ATTR_FAN_SPEED_OPTIM,
    ATTR_FAN_SWING_CAP,
    ATTR_FAN_SWING_CAP_HORIZ,
    ATTR_FAN_SWING_CAP_VERT,
    ATTR_FAN_SWING_HORIZ,
    ATTR_FAN_SWING_VERT,
    ATTR_FLOOR_AIR_LIMIT,
    ATTR_FLOOR_AUX,
    ATTR_FLOOR_MAX,
    ATTR_FLOOR_MIN,
    ATTR_FLOOR_MODE,
    ATTR_FLOOR_OUTPUT1,
    ATTR_FLOOR_OUTPUT2,
    ATTR_FLOOR_SENSOR,
    ATTR_GFCI_ALERT,
    ATTR_GFCI_STATUS,
    ATTR_HC_DEV,
    ATTR_HC_LOCK_STATUS,
    ATTR_HEAT_COOL,
    ATTR_HEAT_INSTALL_TYPE,
    ATTR_HEAT_INTERSTAGE_DELAY,
    ATTR_HEAT_INTERSTAGE_MIN_DELAY,
    ATTR_HEAT_LOCK_TEMP,
    ATTR_HEAT_LOCKOUT_TEMP,
    ATTR_HEAT_MIN_TIME_OFF,
    ATTR_HEAT_MIN_TIME_ON,
    ATTR_HEAT_PURGE_TIME,
    ATTR_HEAT_SOURCE_TYPE,
    ATTR_HEATCOOL_SETPOINT_MIN_DELTA,
    ATTR_HUMIDITY_DISPLAY,
    ATTR_HUMIDITY_SETPOINT,
    ATTR_HUMIDITY_SETPOINT_MODE,
    ATTR_HUMIDITY_SETPOINT_OFFSET,
    ATTR_INTERLOCK_ID,
    ATTR_INTERLOCK_PARTNER,
    ATTR_KEYPAD,
    ATTR_LANGUAGE,
    ATTR_MODE,
    ATTR_MODEL,
    ATTR_OCCUPANCY,
    ATTR_OPTOUT,
    ATTR_OUTPUT1,
    ATTR_OUTPUT_CONNECT_STATE,
    ATTR_OUTPUT_PERCENT_DISPLAY,
    ATTR_POLARITY,
    ATTR_PUMP_PROTEC,
    ATTR_PUMP_PROTEC_DURATION,
    ATTR_PUMP_PROTEC_PERIOD,
    ATTR_REVERSING_VALVE_POLARITY,
    ATTR_ROOM_SETPOINT,
    ATTR_ROOM_SETPOINT_AWAY,
    ATTR_ROOM_SETPOINT_MAX,
    ATTR_ROOM_SETPOINT_MIN,
    ATTR_ROOM_TEMP_DISPLAY,
    ATTR_ROOM_TEMPERATURE,
    ATTR_RSSI,
    ATTR_SETPOINT,
    ATTR_SETPOINT_MODE,
    ATTR_SOUND_CAP,
    ATTR_SOUND_CONF,
    ATTR_STATUS,
    ATTR_SYSTEM_MODE,
    ATTR_TEMP,
    ATTR_TEMP_OFFSET_HEAT,
    ATTR_TIME,
    ATTR_TIME_FORMAT,
    ATTR_VALUE,
    ATTR_WATTAGE,
    ATTR_WIFI,
    ATTR_WIFI_KEYPAD,
    ATTR_WIFI_WATTAGE,
    DOMAIN,
    MODE_AUTO_BYPASS,
    MODE_EM_HEAT,
    MODE_MANUAL,
    SERVICE_SET_ACCESSORY_TYPE,
    SERVICE_SET_ACTIVATION,
    SERVICE_SET_AIR_FLOOR_MODE,
    SERVICE_SET_AUX_CYCLE_OUTPUT,
    SERVICE_SET_AUX_HEATING_SOURCE,
    SERVICE_SET_AUXILIARY_LOAD,
    SERVICE_SET_BACKLIGHT,
    SERVICE_SET_CLIMATE_KEYPAD_LOCK,
    SERVICE_SET_CLIMATE_NEVIWEB_STATUS,
    SERVICE_SET_COOL_DISSIPATION_TIME,
    SERVICE_SET_COOL_INTERSTAGE_DELAY,
    SERVICE_SET_COOL_LOCKOUT_TEMPERATURE,
    SERVICE_SET_COOL_SETPOINT_AWAY,
    SERVICE_SET_COOL_SETPOINT_MAX,
    SERVICE_SET_COOL_SETPOINT_MIN,
    SERVICE_SET_CYCLE_OUTPUT,
    SERVICE_SET_DISPLAY_CONFIG,
    SERVICE_SET_EARLY_START,
    SERVICE_SET_EM_HEAT,
    SERVICE_SET_FAN_FILTER_REMINDER,
    SERVICE_SET_FAN_SPEED,
    SERVICE_SET_FLOOR_AIR_LIMIT,
    SERVICE_SET_FLOOR_LIMIT_HIGH,
    SERVICE_SET_FLOOR_LIMIT_LOW,
    SERVICE_SET_HC_SECOND_DISPLAY,
    SERVICE_SET_HEAT_DISSIPATION_TIME,
    SERVICE_SET_HEAT_INTERSTAGE_DELAY,
    SERVICE_SET_HEAT_LOCKOUT_TEMPERATURE,
    SERVICE_SET_HEAT_PUMP_OPERATION_LIMIT,
    SERVICE_SET_HEATCOOL_SETPOINT_DELTA,
    SERVICE_SET_HUMIDITY_SETPOINT_MODE,
    SERVICE_SET_HVAC_DR_OPTIONS,
    SERVICE_SET_HVAC_DR_SETPOINT,
    SERVICE_SET_LANGUAGE,
    SERVICE_SET_MIN_TIME_OFF,
    SERVICE_SET_MIN_TIME_ON,
    SERVICE_SET_PUMP_PROTECTION,
    SERVICE_SET_REVERSING_VALVE_POLARITY,
    SERVICE_SET_ROOM_SETPOINT_AWAY,
    SERVICE_SET_SCHEDULE_MODE,
    SERVICE_SET_SECOND_DISPLAY,
    SERVICE_SET_SENSOR_TYPE,
    SERVICE_SET_SETPOINT_MAX,
    SERVICE_SET_SETPOINT_MIN,
    SERVICE_SET_SOUND_CONFIG,
    SERVICE_SET_TEMPERATURE_FORMAT,
    SERVICE_SET_TEMPERATURE_OFFSET,
    SERVICE_SET_TIME_FORMAT,
)
from .schema import (
    AUX_HEATING,
    CYCLE_LENGTH_VALUES,
    FAN_SPEED,
    FULL_SWING,
    FULL_SWING_OFF,
    SET_ACCESSORY_TYPE_SCHEMA,
    SET_ACTIVATION_SCHEMA,
    SET_AIR_FLOOR_MODE_SCHEMA,
    SET_AUX_CYCLE_OUTPUT_SCHEMA,
    SET_AUX_HEATING_SOURCE_SCHEMA,
    SET_AUXILIARY_LOAD_SCHEMA,
    SET_BACKLIGHT_SCHEMA,
    SET_CLIMATE_KEYPAD_LOCK_SCHEMA,
    SET_CLIMATE_NEVIWEB_STATUS_SCHEMA,
    SET_COOL_DISSIPATION_TIME_SCHEMA,
    SET_COOL_INTERSTAGE_DELAY_SCHEMA,
    SET_COOL_LOCKOUT_TEMPERATURE_SCHEMA,
    SET_COOL_SETPOINT_AWAY_SCHEMA,
    SET_COOL_SETPOINT_MAX_SCHEMA,
    SET_COOL_SETPOINT_MIN_SCHEMA,
    SET_CYCLE_OUTPUT_SCHEMA,
    SET_DISPLAY_CONFIG_SCHEMA,
    SET_EARLY_START_SCHEMA,
    SET_EM_HEAT_SCHEMA,
    SET_FAN_FILTER_REMINDER_SCHEMA,
    SET_FAN_SPEED_SCHEMA,
    SET_FLOOR_AIR_LIMIT_SCHEMA,
    SET_FLOOR_LIMIT_HIGH_SCHEMA,
    SET_FLOOR_LIMIT_LOW_SCHEMA,
    SET_HC_SECOND_DISPLAY_SCHEMA,
    SET_HEAT_DISSIPATION_TIME_SCHEMA,
    SET_HEAT_INTERSTAGE_DELAY_SCHEMA,
    SET_HEAT_LOCKOUT_TEMPERATURE_SCHEMA,
    SET_HEAT_PUMP_OPERATION_LIMIT_SCHEMA,
    SET_HEATCOOL_SETPOINT_DELTA_SCHEMA,
    SET_HUMIDITY_SETPOINT_MODE_SCHEMA,
    SET_HVAC_DR_OPTIONS_SCHEMA,
    SET_HVAC_DR_SETPOINT_SCHEMA,
    SET_LANGUAGE_SCHEMA,
    SET_MIN_TIME_OFF_SCHEMA,
    SET_MIN_TIME_ON_SCHEMA,
    SET_PUMP_PROTECTION_SCHEMA,
    SET_REVERSING_VALVE_POLARITY_SCHEMA,
    SET_ROOM_SETPOINT_AWAY_SCHEMA,
    SET_SCHEDULE_MODE_SCHEMA,
    SET_SECOND_DISPLAY_SCHEMA,
    SET_SENSOR_TYPE_SCHEMA,
    SET_SETPOINT_MAX_SCHEMA,
    SET_SETPOINT_MIN_SCHEMA,
    SET_SOUND_CONFIG_SCHEMA,
    SET_TEMPERATURE_FORMAT_SCHEMA,
    SET_TEMPERATURE_OFFSET_SCHEMA,
    SET_TIME_FORMAT_SCHEMA,
    VERSION,
    WIFI_FAN_SPEED,
)

_LOGGER = logging.getLogger(__name__)

SUPPORT_FLAGS = (
    ClimateEntityFeature.TARGET_TEMPERATURE
    | ClimateEntityFeature.PRESET_MODE
    | ClimateEntityFeature.TURN_OFF
    | ClimateEntityFeature.TURN_ON
)
SUPPORT_AUX_FLAGS = (
    ClimateEntityFeature.TARGET_TEMPERATURE
    | ClimateEntityFeature.PRESET_MODE
    | ClimateEntityFeature.TURN_OFF
    | ClimateEntityFeature.TURN_ON
)

SUPPORT_HP_FLAGS = (
    ClimateEntityFeature.TARGET_TEMPERATURE
    | ClimateEntityFeature.PRESET_MODE
    | ClimateEntityFeature.FAN_MODE
    | ClimateEntityFeature.SWING_HORIZONTAL_MODE
    | ClimateEntityFeature.SWING_MODE
    | ClimateEntityFeature.TURN_OFF
    | ClimateEntityFeature.TURN_ON
)

SUPPORT_H_c_FLAGS = (
    ClimateEntityFeature.TARGET_TEMPERATURE
    | ClimateEntityFeature.PRESET_MODE
    | ClimateEntityFeature.FAN_MODE
    | ClimateEntityFeature.SWING_MODE
    | ClimateEntityFeature.TURN_OFF
    | ClimateEntityFeature.TURN_ON
)

SUPPORT_HC_FLAGS = ClimateEntityFeature.PRESET_MODE | ClimateEntityFeature.TURN_OFF | ClimateEntityFeature.TURN_ON

DEFAULT_NAME = f"{DOMAIN} climate"
DEFAULT_NAME_2 = f"{DOMAIN} climate 2"
DEFAULT_NAME_3 = f"{DOMAIN} climate 3"
SNOOZE_TIME = 1200
SCAN_INTERVAL = scan_interval

UPDATE_ATTRIBUTES = [
    ATTR_DRSETPOINT,
    ATTR_DRSTATUS,
    ATTR_OUTPUT_PERCENT_DISPLAY,
    ATTR_ROOM_SETPOINT,
    ATTR_ROOM_SETPOINT_MAX,
    ATTR_ROOM_SETPOINT_MIN,
    ATTR_ROOM_TEMPERATURE,
    ATTR_TEMP,
    ATTR_TIME_FORMAT,
]

UPDATE_LITE_ATTRIBUTES = [
    ATTR_DRSETPOINT,
    ATTR_DRSTATUS,
    ATTR_OUTPUT_PERCENT_DISPLAY,
    ATTR_ROOM_SETPOINT,
    ATTR_ROOM_SETPOINT_MAX,
    ATTR_ROOM_SETPOINT_MIN,
    ATTR_ROOM_TEMPERATURE,
    ATTR_TEMP,
]

UPDATE_HP_ATTRIBUTES = [
    ATTR_ROOM_SETPOINT,
    ATTR_ROOM_SETPOINT_MAX,
    ATTR_ROOM_SETPOINT_MIN,
    ATTR_COOL_SETPOINT_MIN,
    ATTR_COOL_SETPOINT_MAX,
    ATTR_ROOM_TEMPERATURE,
    ATTR_TEMP,
]

UPDATE_HEAT_COOL_ATTRIBUTES = [
    ATTR_OUTPUT_PERCENT_DISPLAY,
    ATTR_ROOM_SETPOINT,
    ATTR_COOL_SETPOINT,
    ATTR_ROOM_SETPOINT_MAX,
    ATTR_ROOM_SETPOINT_MIN,
    ATTR_COOL_SETPOINT_MAX,
    ATTR_COOL_SETPOINT_MIN,
    ATTR_ROOM_TEMP_DISPLAY,
    ATTR_ROOM_TEMPERATURE,
    ATTR_TEMP,
    ATTR_TIME_FORMAT,
]

SUPPORTED_HVAC_WIFI_MODES: list[HVACMode] = [
    HVACMode.AUTO,
    HVACMode.HEAT,
    HVACMode.OFF,
]

SUPPORTED_HVAC_WIFI_LITE_MODES: list[HVACMode] = [
    HVACMode.AUTO,
    HVACMode.OFF,
]

SUPPORTED_HVAC_MODES: list[HVACMode] = [
    HVACMode.HEAT,
    HVACMode.OFF,
]

SUPPORTED_HVAC_H_C_MODES: list[HVACMode] = [
    HVACMode.COOL,
    HVACMode.HEAT,
    HVACMode.OFF,
]

SUPPORTED_HVAC_HC_MODES = [
    HVACMode.HEAT_COOL,
    HVACMode.HEAT,
    HVACMode.COOL,
    HVACMode.OFF,
]

SUPPORTED_HVAC_HP_MODES: list[HVACMode] = [
    HVACMode.COOL,
    HVACMode.DRY,
    HVACMode.FAN_ONLY,
    HVACMode.HEAT,
    HVACMode.OFF,
]

SUPPORTED_HVAC_HEAT_MODES: list[HVACMode] = [
    HVACMode.FAN_ONLY,
    HVACMode.HEAT,
    HVACMode.OFF,
]

SUPPORTED_HVAC_COOL_MODES: list[HVACMode] = [
    HVACMode.COOL,
    HVACMode.DRY,
    HVACMode.FAN_ONLY,
    HVACMode.OFF,
]

PRESET_WIFI_MODES = [
    PRESET_HOME,
    PRESET_AWAY,
    PRESET_NONE,
]

PRESET_MODES = [
    PRESET_AWAY,
    PRESET_NONE,
]

PRESET_HP_MODES = [
    PRESET_HOME,
    PRESET_AWAY,
    PRESET_NONE,
]

PRESET_HC_MODES = [
    PRESET_HOME,
    PRESET_AWAY,
]

PRESET_h_c_MODES = [
    PRESET_HOME,
    PRESET_AWAY,
]

DEVICE_MODEL_LOW = [7372]
DEVICE_MODEL_LOW_WIFI = [739]
DEVICE_MODEL_FLOOR = [737]
DEVICE_MODEL_WIFI_FLOOR = [738]
DEVICE_MODEL_WIFI = [1510, 742]
DEVICE_MODEL_WIFI_LITE = [336]
DEVICE_MODEL_COLOR_WIFI = [350]
DEVICE_MODEL_HEAT = [1123, 1124]
DEVICE_MODEL_DOUBLE = [7373]
DEVICE_MODEL_HEAT_G2 = [300]
DEVICE_MODEL_HC = [1512]
DEVICE_MODEL_HEAT_PUMP = [6810, 6811, 6812]
DEVICE_MODEL_HEAT_COOL = [6727, 6730]
IMPLEMENTED_DEVICE_MODEL = (
    DEVICE_MODEL_HEAT
    + DEVICE_MODEL_FLOOR
    + DEVICE_MODEL_LOW
    + DEVICE_MODEL_WIFI_FLOOR
    + DEVICE_MODEL_WIFI
    + DEVICE_MODEL_LOW_WIFI
    + DEVICE_MODEL_HEAT_G2
    + DEVICE_MODEL_HC
    + DEVICE_MODEL_DOUBLE
    + DEVICE_MODEL_HEAT_PUMP
    + DEVICE_MODEL_HEAT_COOL
    + DEVICE_MODEL_WIFI_LITE
    + DEVICE_MODEL_COLOR_WIFI
)


async def async_setup_platform(
    hass,
    config,
    async_add_entities,
    discovery_info=None,
) -> None:
    """Set up the neviweb130 thermostats."""
    data = hass.data[DOMAIN]

    # Wait for async migration to be done
    await data.migration_done.wait()

    entities: list[Neviweb130Thermostat] = []
    for device_info in data.neviweb130_client.gateway_data:
        if (
            "signature" in device_info
            and "model" in device_info["signature"]
            and device_info["signature"]["model"] in IMPLEMENTED_DEVICE_MODEL
        ):
            device_name = "{} {}".format(DEFAULT_NAME, device_info["name"])
            device_sku = device_info["sku"]
            location_id = device_info["location$id"]
            device_firmware = "{}.{}.{}".format(
                device_info["signature"]["softVersion"]["major"],
                device_info["signature"]["softVersion"]["middle"],
                device_info["signature"]["softVersion"]["minor"],
            )
            if device_info["signature"]["model"] in DEVICE_MODEL_HEAT:
                entities.append(
                    Neviweb130Thermostat(
                        data,
                        device_info,
                        device_name,
                        device_sku,
                        device_firmware,
                        location_id,
                    )
                )
            elif device_info["signature"]["model"] in DEVICE_MODEL_HEAT_G2:
                entities.append(
                    Neviweb130G2Thermostat(
                        data,
                        device_info,
                        device_name,
                        device_sku,
                        device_firmware,
                        location_id,
                    )
                )
            elif device_info["signature"]["model"] in DEVICE_MODEL_FLOOR:
                entities.append(
                    Neviweb130FloorThermostat(
                        data,
                        device_info,
                        device_name,
                        device_sku,
                        device_firmware,
                        location_id,
                    )
                )
            elif device_info["signature"]["model"] in DEVICE_MODEL_LOW:
                entities.append(
                    Neviweb130LowThermostat(
                        data,
                        device_info,
                        device_name,
                        device_sku,
                        device_firmware,
                        location_id,
                    )
                )
            elif device_info["signature"]["model"] in DEVICE_MODEL_DOUBLE:
                entities.append(
                    Neviweb130DoubleThermostat(
                        data,
                        device_info,
                        device_name,
                        device_sku,
                        device_firmware,
                        location_id,
                    )
                )
            elif device_info["signature"]["model"] in DEVICE_MODEL_WIFI:
                entities.append(
                    Neviweb130WifiThermostat(
                        data,
                        device_info,
                        device_name,
                        device_sku,
                        device_firmware,
                        location_id,
                    )
                )
            elif device_info["signature"]["model"] in DEVICE_MODEL_WIFI_LITE:
                entities.append(
                    Neviweb130WifiLiteThermostat(
                        data,
                        device_info,
                        device_name,
                        device_sku,
                        device_firmware,
                        location_id,
                    )
                )
            elif device_info["signature"]["model"] in DEVICE_MODEL_COLOR_WIFI:
                entities.append(
                    Neviweb130ColorWifiThermostat(
                        data,
                        device_info,
                        device_name,
                        device_sku,
                        device_firmware,
                        location_id,
                    )
                )
            elif device_info["signature"]["model"] in DEVICE_MODEL_LOW_WIFI:
                entities.append(
                    Neviweb130LowWifiThermostat(
                        data,
                        device_info,
                        device_name,
                        device_sku,
                        device_firmware,
                        location_id,
                    )
                )
            elif device_info["signature"]["model"] in DEVICE_MODEL_WIFI_FLOOR:
                entities.append(
                    Neviweb130WifiFloorThermostat(
                        data,
                        device_info,
                        device_name,
                        device_sku,
                        device_firmware,
                        location_id,
                    )
                )
            elif device_info["signature"]["model"] in DEVICE_MODEL_HC:
                entities.append(
                    Neviweb130HcThermostat(
                        data,
                        device_info,
                        device_name,
                        device_sku,
                        device_firmware,
                        location_id,
                    )
                )
            elif device_info["signature"]["model"] in DEVICE_MODEL_HEAT_PUMP:
                entities.append(
                    Neviweb130HPThermostat(
                        data,
                        device_info,
                        device_name,
                        device_sku,
                        device_firmware,
                        location_id,
                    )
                )
            else:
                entities.append(
                    Neviweb130HeatCoolThermostat(
                        data,
                        device_info,
                        device_name,
                        device_sku,
                        device_firmware,
                        location_id,
                    )
                )
    for device_info in data.neviweb130_client.gateway_data2:
        if (
            "signature" in device_info
            and "model" in device_info["signature"]
            and device_info["signature"]["model"] in IMPLEMENTED_DEVICE_MODEL
        ):
            device_name = "{} {}".format(DEFAULT_NAME_2, device_info["name"])
            device_sku = device_info["sku"]
            location_id = device_info["location$id"]
            device_firmware = "{}.{}.{}".format(
                device_info["signature"]["softVersion"]["major"],
                device_info["signature"]["softVersion"]["middle"],
                device_info["signature"]["softVersion"]["minor"],
            )
            if device_info["signature"]["model"] in DEVICE_MODEL_HEAT:
                entities.append(
                    Neviweb130Thermostat(
                        data,
                        device_info,
                        device_name,
                        device_sku,
                        device_firmware,
                        location_id,
                    )
                )
            elif device_info["signature"]["model"] in DEVICE_MODEL_HEAT_G2:
                entities.append(
                    Neviweb130G2Thermostat(
                        data,
                        device_info,
                        device_name,
                        device_sku,
                        device_firmware,
                        location_id,
                    )
                )
            elif device_info["signature"]["model"] in DEVICE_MODEL_FLOOR:
                entities.append(
                    Neviweb130FloorThermostat(
                        data,
                        device_info,
                        device_name,
                        device_sku,
                        device_firmware,
                        location_id,
                    )
                )
            elif device_info["signature"]["model"] in DEVICE_MODEL_LOW:
                entities.append(
                    Neviweb130LowThermostat(
                        data,
                        device_info,
                        device_name,
                        device_sku,
                        device_firmware,
                        location_id,
                    )
                )
            elif device_info["signature"]["model"] in DEVICE_MODEL_DOUBLE:
                entities.append(
                    Neviweb130DoubleThermostat(
                        data,
                        device_info,
                        device_name,
                        device_sku,
                        device_firmware,
                        location_id,
                    )
                )
            elif device_info["signature"]["model"] in DEVICE_MODEL_WIFI:
                entities.append(
                    Neviweb130WifiThermostat(
                        data,
                        device_info,
                        device_name,
                        device_sku,
                        device_firmware,
                        location_id,
                    )
                )
            elif device_info["signature"]["model"] in DEVICE_MODEL_WIFI_LITE:
                entities.append(
                    Neviweb130WifiLiteThermostat(
                        data,
                        device_info,
                        device_name,
                        device_sku,
                        device_firmware,
                        location_id,
                    )
                )
            elif device_info["signature"]["model"] in DEVICE_MODEL_COLOR_WIFI:
                entities.append(
                    Neviweb130ColorWifiThermostat(
                        data,
                        device_info,
                        device_name,
                        device_sku,
                        device_firmware,
                        location_id,
                    )
                )
            elif device_info["signature"]["model"] in DEVICE_MODEL_LOW_WIFI:
                entities.append(
                    Neviweb130LowWifiThermostat(
                        data,
                        device_info,
                        device_name,
                        device_sku,
                        device_firmware,
                        location_id,
                    )
                )
            elif device_info["signature"]["model"] in DEVICE_MODEL_WIFI_FLOOR:
                entities.append(
                    Neviweb130WifiFloorThermostat(
                        data,
                        device_info,
                        device_name,
                        device_sku,
                        device_firmware,
                        location_id,
                    )
                )
            elif device_info["signature"]["model"] in DEVICE_MODEL_HC:
                entities.append(
                    Neviweb130HcThermostat(
                        data,
                        device_info,
                        device_name,
                        device_sku,
                        device_firmware,
                        location_id,
                    )
                )
            elif device_info["signature"]["model"] in DEVICE_MODEL_HEAT_PUMP:
                entities.append(
                    Neviweb130HPThermostat(
                        data,
                        device_info,
                        device_name,
                        device_sku,
                        device_firmware,
                        location_id,
                    )
                )
            else:
                entities.append(
                    Neviweb130HeatCoolThermostat(
                        data,
                        device_info,
                        device_name,
                        device_sku,
                        device_firmware,
                        location_id,
                    )
                )
    for device_info in data.neviweb130_client.gateway_data3:
        if (
            "signature" in device_info
            and "model" in device_info["signature"]
            and device_info["signature"]["model"] in IMPLEMENTED_DEVICE_MODEL
        ):
            device_name = "{} {}".format(DEFAULT_NAME_3, device_info["name"])
            device_sku = device_info["sku"]
            location_id = device_info["location$id"]
            device_firmware = "{}.{}.{}".format(
                device_info["signature"]["softVersion"]["major"],
                device_info["signature"]["softVersion"]["middle"],
                device_info["signature"]["softVersion"]["minor"],
            )
            if device_info["signature"]["model"] in DEVICE_MODEL_HEAT:
                entities.append(
                    Neviweb130Thermostat(
                        data,
                        device_info,
                        device_name,
                        device_sku,
                        device_firmware,
                        location_id,
                    )
                )
            elif device_info["signature"]["model"] in DEVICE_MODEL_HEAT_G2:
                entities.append(
                    Neviweb130G2Thermostat(
                        data,
                        device_info,
                        device_name,
                        device_sku,
                        device_firmware,
                        location_id,
                    )
                )
            elif device_info["signature"]["model"] in DEVICE_MODEL_FLOOR:
                entities.append(
                    Neviweb130FloorThermostat(
                        data,
                        device_info,
                        device_name,
                        device_sku,
                        device_firmware,
                        location_id,
                    )
                )
            elif device_info["signature"]["model"] in DEVICE_MODEL_LOW:
                entities.append(
                    Neviweb130LowThermostat(
                        data,
                        device_info,
                        device_name,
                        device_sku,
                        device_firmware,
                        location_id,
                    )
                )
            elif device_info["signature"]["model"] in DEVICE_MODEL_DOUBLE:
                entities.append(
                    Neviweb130DoubleThermostat(
                        data,
                        device_info,
                        device_name,
                        device_sku,
                        device_firmware,
                        location_id,
                    )
                )
            elif device_info["signature"]["model"] in DEVICE_MODEL_WIFI:
                entities.append(
                    Neviweb130WifiThermostat(
                        data,
                        device_info,
                        device_name,
                        device_sku,
                        device_firmware,
                        location_id,
                    )
                )
            elif device_info["signature"]["model"] in DEVICE_MODEL_WIFI_LITE:
                entities.append(
                    Neviweb130WifiLiteThermostat(
                        data,
                        device_info,
                        device_name,
                        device_sku,
                        device_firmware,
                        location_id,
                    )
                )
            elif device_info["signature"]["model"] in DEVICE_MODEL_COLOR_WIFI:
                entities.append(
                    Neviweb130ColorWifiThermostat(
                        data,
                        device_info,
                        device_name,
                        device_sku,
                        device_firmware,
                        location_id,
                    )
                )
            elif device_info["signature"]["model"] in DEVICE_MODEL_LOW_WIFI:
                entities.append(
                    Neviweb130LowWifiThermostat(
                        data,
                        device_info,
                        device_name,
                        device_sku,
                        device_firmware,
                        location_id,
                    )
                )
            elif device_info["signature"]["model"] in DEVICE_MODEL_WIFI_FLOOR:
                entities.append(
                    Neviweb130WifiFloorThermostat(
                        data,
                        device_info,
                        device_name,
                        device_sku,
                        device_firmware,
                        location_id,
                    )
                )
            elif device_info["signature"]["model"] in DEVICE_MODEL_HC:
                entities.append(
                    Neviweb130HcThermostat(
                        data,
                        device_info,
                        device_name,
                        device_sku,
                        device_firmware,
                        location_id,
                    )
                )
            elif device_info["signature"]["model"] in DEVICE_MODEL_HEAT_PUMP:
                entities.append(
                    Neviweb130HPThermostat(
                        data,
                        device_info,
                        device_name,
                        device_sku,
                        device_firmware,
                        location_id,
                    )
                )
            else:
                entities.append(
                    Neviweb130HeatCoolThermostat(
                        data,
                        device_info,
                        device_name,
                        device_sku,
                        device_firmware,
                        location_id,
                    )
                )

    async_add_entities(entities, True)

    entity_map: dict[str, Neviweb130Thermostat] | None = None
    _entity_map_lock = Lock()

    def get_thermostat(service: ServiceCall) -> Neviweb130Thermostat:
        entity_id = service.data.get(ATTR_ENTITY_ID)
        if entity_id is None:
            raise ServiceValidationError(f"Missing required parameter: {ATTR_ENTITY_ID}")

        nonlocal entity_map
        if entity_map is None:
            with _entity_map_lock:
                if entity_map is None:
                    entity_map = {entity.entity_id: entity for entity in entities if entity.entity_id is not None}
                    if len(entity_map) != len(entities):
                        entity_map = None
                        raise ServiceValidationError("Entities not finished loading, try again shortly")

        thermostat = entity_map.get(entity_id)
        if thermostat is None:
            raise ServiceValidationError(f"Entity {entity_id} must be a {DOMAIN} thermostat")
        return thermostat

    def set_second_display_service(service: ServiceCall) -> None:
        """Set to outside or setpoint temperature display for Wi-Fi thermostats."""
        thermostat = get_thermostat(service)
        value = {
            "id": thermostat.unique_id,
            "display": service.data[ATTR_DISPLAY2],
        }
        thermostat.set_second_display(value)
        thermostat.schedule_update_ha_state(True)

    def set_backlight_service(service: ServiceCall) -> None:
        """Set backlight always on or auto."""
        thermostat = get_thermostat(service)
        value = {
            "id": thermostat.unique_id,
            "level": service.data[ATTR_BACKLIGHT],
        }
        thermostat.set_backlight(value)
        thermostat.schedule_update_ha_state(True)

    def set_climate_keypad_lock_service(service: ServiceCall) -> None:
        """Lock/unlock keypad device."""
        thermostat = get_thermostat(service)
        value = {
            "id": thermostat.unique_id,
            "lock": service.data[ATTR_KEYPAD],
        }
        thermostat.set_keypad_lock(value)
        thermostat.schedule_update_ha_state(True)

    def set_time_format_service(service: ServiceCall) -> None:
        """Set time format 12h or 24h."""
        thermostat = get_thermostat(service)
        if isinstance(thermostat, Neviweb130WifiLiteThermostat):
            raise ServiceValidationError(f"Entity {thermostat.entity_id} must be a {DOMAIN} Wi-Fi (lite) thermostat")

        value = {
            "id": thermostat.unique_id,
            ATTR_TIME: service.data[ATTR_TIME_FORMAT],
        }
        thermostat.set_time_format(value)
        thermostat.schedule_update_ha_state(True)

    def set_temperature_format_service(service: ServiceCall) -> None:
        """Set temperature format, celsius or fahrenheit."""
        thermostat = get_thermostat(service)
        value = {
            "id": thermostat.unique_id,
            "temp": service.data[ATTR_TEMP],
        }
        thermostat.set_temperature_format(value)
        thermostat.schedule_update_ha_state(True)

    def set_setpoint_max_service(service: ServiceCall) -> None:
        """Set maximum setpoint for device."""
        thermostat = get_thermostat(service)
        value = {
            "id": thermostat.unique_id,
            "temp": service.data[ATTR_ROOM_SETPOINT_MAX],
        }
        thermostat.set_setpoint_max(value)
        thermostat.schedule_update_ha_state(True)

    def set_setpoint_min_service(service: ServiceCall) -> None:
        """Set minimum setpoint for device."""
        thermostat = get_thermostat(service)
        value = {
            "id": thermostat.unique_id,
            "temp": service.data[ATTR_ROOM_SETPOINT_MIN],
        }
        thermostat.set_setpoint_min(value)
        thermostat.schedule_update_ha_state(True)

    def set_floor_air_limit_service(service: ServiceCall) -> None:
        """Set minimum setpoint for device."""
        thermostat = get_thermostat(service)
        value = {
            "id": thermostat.unique_id,
            "temp": service.data[ATTR_FLOOR_AIR_LIMIT],
        }
        thermostat.set_floor_air_limit(value)
        thermostat.schedule_update_ha_state(True)

    def set_early_start_service(service: ServiceCall) -> None:
        """Set early heating on/off for Wi-Fi thermostat."""
        thermostat = get_thermostat(service)
        value = {
            "id": thermostat.unique_id,
            "start": service.data[ATTR_EARLY_START],
        }
        thermostat.set_early_start(value)
        thermostat.schedule_update_ha_state(True)

    def set_air_floor_mode_service(service: ServiceCall) -> None:
        """Switch between ambient or floor temperature sensor."""
        thermostat = get_thermostat(service)
        value = {
            "id": thermostat.unique_id,
            "mode": service.data[ATTR_FLOOR_MODE],
        }
        thermostat.set_air_floor_mode(value)
        thermostat.schedule_update_ha_state(True)

    def set_hvac_dr_options_service(service: ServiceCall) -> None:
        """Set options for hvac dr in Eco Sinope."""
        thermostat = get_thermostat(service)
        if not isinstance(thermostat, Neviweb130HeatCoolThermostat):
            value = {
                "id": thermostat.unique_id,
                "dractive": service.data(ATTR_DRACTIVE),
                "optout": service.data(ATTR_OPTOUT),
                "setpoint": service.data(ATTR_SETPOINT),
            }
        else:
            value = {
                "id": thermostat.unique_id,
                ATTR_AUX_OPTIM: service.data.get(ATTR_AUX_OPTIM),
                ATTR_FAN_SPEED_OPTIM: service.data.get(ATTR_FAN_SPEED_OPTIM),
            }
        thermostat.set_hvac_dr_options(value)
        thermostat.schedule_update_ha_state(True)

    def set_hvac_dr_setpoint_service(service: ServiceCall) -> None:
        """Set options for hvac dr setpoint in Eco Sinope."""
        thermostat = get_thermostat(service)
        value = {
            "id": thermostat.unique_id,
            "status": service.data[ATTR_STATUS],
            "val": service.data[ATTR_VALUE],
        }
        thermostat.set_hvac_dr_setpoint(value)
        thermostat.schedule_update_ha_state(True)

    def set_auxiliary_load_service(service: ServiceCall) -> None:
        """Set options for auxiliary heating."""
        thermostat = get_thermostat(service)
        value = {
            "id": thermostat.unique_id,
            "status": service.data[ATTR_STATUS],
            "val": service.data[ATTR_VALUE],
        }
        thermostat.set_auxiliary_load(value)
        thermostat.schedule_update_ha_state(True)

    def set_aux_cycle_output_service(service: ServiceCall) -> None:
        """Set options for auxiliary cycle length for low voltage thermostats."""
        thermostat = get_thermostat(service)
        val = service.data.get(ATTR_VALUE)
        if val is None:
            raise ServiceValidationError(f"Missing required parameter: {ATTR_VALUE}")
        value = {
            "id": thermostat.unique_id,
            "val": val,
        }
        thermostat.set_aux_cycle_output(value)
        thermostat.schedule_update_ha_state(True)

    def set_cycle_output_service(service: ServiceCall) -> None:
        """Set options for main cycle length for low voltage thermostats."""
        thermostat = get_thermostat(service)
        value = {
            "id": thermostat.unique_id,
            "val": service.data[ATTR_VALUE],
        }
        thermostat.set_cycle_output(value)
        thermostat.schedule_update_ha_state(True)

    def set_pump_protection_service(service: ServiceCall) -> None:
        """Set status of pump protection for low voltage thermostats."""
        thermostat = get_thermostat(service)
        value = {
            "id": thermostat.unique_id,
            "status": service.data[ATTR_STATUS],
        }
        thermostat.set_pump_protection(value)
        thermostat.schedule_update_ha_state(True)

    def set_cool_setpoint_max_service(service: ServiceCall) -> None:
        """Set maximum cooling setpoint for device."""
        thermostat = get_thermostat(service)
        value = {
            "id": thermostat.unique_id,
            "temp": service.data[ATTR_COOL_SETPOINT_MAX],
        }
        thermostat.set_cool_setpoint_max(value)
        thermostat.schedule_update_ha_state(True)

    def set_cool_setpoint_min_service(service: ServiceCall) -> None:
        """Set minimum cooling setpoint for device."""
        thermostat = get_thermostat(service)
        value = {
            "id": thermostat.unique_id,
            "temp": service.data[ATTR_COOL_SETPOINT_MIN],
        }
        thermostat.set_cool_setpoint_min(value)
        thermostat.schedule_update_ha_state(True)

    def set_room_setpoint_away_service(service: ServiceCall) -> None:
        """Set away heating setpoint."""
        thermostat = get_thermostat(service)
        value = {
            "id": thermostat.unique_id,
            "temp": service.data[ATTR_ROOM_SETPOINT_AWAY],
        }
        thermostat.set_room_setpoint_away(value)
        thermostat.schedule_update_ha_state(True)

    def set_cool_setpoint_away_service(service: ServiceCall) -> None:
        """Set away cooling setpoint."""
        thermostat = get_thermostat(service)
        if not isinstance(thermostat, Neviweb130HeatCoolThermostat):
            raise ServiceValidationError(f"Entity {thermostat.entity_id} must be a {DOMAIN} heat-cool thermostat")
        value = {
            "id": thermostat.unique_id,
            "temp": service.data[ATTR_COOL_SETPOINT_AWAY],
        }
        thermostat.set_cool_setpoint_away(value)
        thermostat.schedule_update_ha_state(True)

    def set_floor_limit_high_service(service: ServiceCall) -> None:
        """Set maximum floor heating limit for floor device."""
        thermostat = get_thermostat(service)
        value = {
            "id": thermostat.unique_id,
            "level": service.data[ATTR_FLOOR_MAX],
            "limit": "high",
        }
        thermostat.set_floor_limit(value)
        thermostat.schedule_update_ha_state(True)

    def set_floor_limit_low_service(service: ServiceCall) -> None:
        """Set minimum floor heating limit for floor device."""
        thermostat = get_thermostat(service)
        value = {
            "id": thermostat.unique_id,
            "level": service.data[ATTR_FLOOR_MIN],
            "limit": "low",
        }
        thermostat.set_floor_limit(value)
        thermostat.schedule_update_ha_state(True)

    def set_activation_service(service: ServiceCall) -> None:
        """Activate or deactivate Neviweb polling for missing device."""
        thermostat = get_thermostat(service)
        value = {
            "id": thermostat.unique_id,
            "active": service.data[ATTR_ACTIVE],
        }
        thermostat.set_activation(value)
        thermostat.schedule_update_ha_state(True)

    def set_sensor_type_service(service: ServiceCall) -> None:
        """Set floor sensor type."""
        thermostat = get_thermostat(service)
        value = {
            "id": thermostat.unique_id,
            "type": service.data[ATTR_FLOOR_SENSOR],
        }
        thermostat.set_sensor_type(value)
        thermostat.schedule_update_ha_state(True)

    def set_em_heat_service(service: ServiceCall) -> None:
        """Set emergency heat on/off for thermostats."""
        thermostat = get_thermostat(service)
        if service.data[ATTR_VALUE] == "on":
            thermostat.turn_em_heat_on()
        else:
            thermostat.turn_em_heat_off()
        thermostat.schedule_update_ha_state(True)

    def set_heat_pump_operation_limit_service(service: ServiceCall) -> None:
        """Set minimum temperature for heat pump device operation."""
        thermostat = get_thermostat(service)
        value = {
            "id": thermostat.unique_id,
            "temp": service.data[ATTR_BALANCE_PT],
        }
        thermostat.set_heat_pump_operation_limit(value)
        thermostat.schedule_update_ha_state(True)

    def set_heat_lockout_temperature_service(service: ServiceCall) -> None:
        """Set maximum outside temperature limit to allow heating device operation."""
        thermostat = get_thermostat(service)
        value = {
            "id": thermostat.unique_id,
            "temp": service.data[ATTR_HEAT_LOCK_TEMP],
        }
        thermostat.set_heat_lockout_temperature(value)
        thermostat.schedule_update_ha_state(True)

    def set_cool_lockout_temperature_service(service: ServiceCall) -> None:
        """Set minimum outside temperature limit to allow cooling device operation."""
        thermostat = get_thermostat(service)
        value = {
            "id": thermostat.unique_id,
            "temp": service.data[ATTR_COOL_LOCK_TEMP],
        }
        thermostat.set_cool_lockout_temperature(value)
        thermostat.schedule_update_ha_state(True)

    def set_display_config_service(service: ServiceCall) -> None:
        """Set display on/off for heat pump."""
        thermostat = get_thermostat(service)
        value = {
            "id": thermostat.unique_id,
            "display": service.data[ATTR_DISPLAY_CONF],
        }
        thermostat.set_display_config(value)
        thermostat.schedule_update_ha_state(True)

    def set_sound_config_service(service: ServiceCall) -> None:
        """Set sound on/off for heat pump."""
        thermostat = get_thermostat(service)
        value = {
            "id": thermostat.unique_id,
            "sound": service.data[ATTR_SOUND_CONF],
        }
        thermostat.set_sound_config(value)
        thermostat.schedule_update_ha_state(True)

    def set_hc_second_display_service(service: ServiceCall) -> None:
        """Set second display for TH1134ZB-HC thermostat."""
        thermostat = get_thermostat(service)
        value = {
            "id": thermostat.unique_id,
            "display": service.data[ATTR_DISPLAY2],
        }
        thermostat.set_hc_second_display(value)
        thermostat.schedule_update_ha_state(True)

    def set_language_service(service: ServiceCall) -> None:
        """Set display language for TH1134ZB-HC thermostat."""
        thermostat = get_thermostat(service)
        value = {
            "id": thermostat.unique_id,
            "lang": service.data[ATTR_LANGUAGE],
        }
        thermostat.set_language(value)
        thermostat.schedule_update_ha_state(True)

    def set_reversing_valve_polarity(service: ServiceCall) -> None:
        """Set minimum time the device is on before letting be off again (run-on time)
        for TH6500WF and TH6250WF thermostats."""
        thermostat = get_thermostat(service)
        if not isinstance(thermostat, Neviweb130HeatCoolThermostat):
            raise ServiceValidationError(f"Entity {thermostat.entity_id} must be a {DOMAIN} heat-cool thermostat")
        thermostat.set_reversing_valve_polarity(service.data)
        thermostat.schedule_update_ha_state(True)

    def set_min_time_on_service(service: ServiceCall) -> None:
        """Set minimum time the device is on before letting be off again (run-on time)
        for TH6500WF and TH6250WF thermostats."""
        thermostat = get_thermostat(service)
        if not isinstance(thermostat, Neviweb130HeatCoolThermostat):
            raise ServiceValidationError(f"Entity {thermostat.entity_id} must be a {DOMAIN} heat-cool thermostat")
        thermostat.set_min_time_on(service.data)
        thermostat.schedule_update_ha_state(True)

    def set_min_time_off_service(service: ServiceCall) -> None:
        """Set minimum time the device is off before letting it be on again (cooldown time)
        for TH6500WF and TH6250WF thermostats."""
        thermostat = get_thermostat(service)
        if not isinstance(thermostat, Neviweb130HeatCoolThermostat):
            raise ServiceValidationError(f"Entity {thermostat.entity_id} must be a {DOMAIN} heat-cool thermostat")
        thermostat.set_min_time_off(service.data)
        thermostat.schedule_update_ha_state(True)

    def set_heat_interstage_delay(service: ServiceCall) -> None:
        """Set minimum time the device is heating before letting it increment the heater stage
        for TH6500WF and TH6250WF thermostats."""
        thermostat = get_thermostat(service)
        if not isinstance(thermostat, Neviweb130HeatCoolThermostat):
            raise ServiceValidationError(f"Entity {thermostat.entity_id} must be a {DOMAIN} heat-cool thermostat")
        thermostat.set_heat_interstage_delay(service.data)
        thermostat.schedule_update_ha_state(True)

    def set_cool_interstage_delay(service: ServiceCall) -> None:
        """Set minimum time the device is cooling before letting it increment the cooler stage
        for TH6500WF and TH6250WF thermostats."""
        thermostat = get_thermostat(service)
        if not isinstance(thermostat, Neviweb130HeatCoolThermostat):
            raise ServiceValidationError(f"Entity {thermostat.entity_id} must be a {DOMAIN} heat-cool thermostat")
        thermostat.set_cool_interstage_delay(service.data)
        thermostat.schedule_update_ha_state(True)

    def set_accessory_type_service(service: ServiceCall) -> None:
        """Set TH6500WF accessory (humidifier, dehumidifier, air exchanger) type."""
        thermostat = get_thermostat(service)
        if not isinstance(thermostat, Neviweb130HeatCoolThermostat):
            raise ServiceValidationError(f"Entity {thermostat.entity_id} must be a {DOMAIN} heat-cool thermostat")
        value = {
            "id": thermostat.unique_id,
            "type": service.data[ATTR_ACCESSORY_TYPE],
        }
        thermostat.set_accessory_type(value)
        thermostat.schedule_update_ha_state(True)

    def set_schedule_mode_service(service: ServiceCall) -> None:
        """Set TH6500WF, TH6250WF schedule mode, manual or auto."""
        thermostat = get_thermostat(service)
        if not isinstance(thermostat, Neviweb130HeatCoolThermostat):
            raise ServiceValidationError(f"Entity {thermostat.entity_id} must be a {DOMAIN} heat-cool thermostat")
        value = {
            "id": thermostat.unique_id,
            "mode": service.data[ATTR_SETPOINT_MODE],
        }
        thermostat.set_schedule_mode(value)
        thermostat.schedule_update_ha_state(True)

    def set_heatcool_setpoint_delta_service(service: ServiceCall) -> None:
        """Set TH6500WF, TH6250WF delta temperature between heating and cooling setpoint."""
        thermostat = get_thermostat(service)
        if not isinstance(thermostat, Neviweb130HeatCoolThermostat):
            raise ServiceValidationError(f"Entity {thermostat.entity_id} must be a {DOMAIN} heat-cool thermostat")
        value = {
            "id": thermostat.unique_id,
            "level": service.data[ATTR_HEATCOOL_SETPOINT_MIN_DELTA],
        }
        thermostat.set_heatcool_setpoint_delta(value)
        thermostat.schedule_update_ha_state(True)

    def set_fan_filter_reminder_service(service: ServiceCall) -> None:
        """Set TH6500WF, TH6250WF fan filter reminder period from 1 to 12 month."""
        thermostat = get_thermostat(service)
        if not isinstance(thermostat, Neviweb130HeatCoolThermostat):
            raise ServiceValidationError(f"Entity {thermostat.entity_id} must be a {DOMAIN} heat-cool thermostat")
        value = {
            "id": thermostat.unique_id,
            "month": service.data[ATTR_FAN_FILTER_REMAIN],
        }
        thermostat.set_fan_filter_reminder(value)
        thermostat.schedule_update_ha_state(True)

    def set_temperature_offset_service(service: ServiceCall) -> None:
        """Set TH6500WF, TH6250WF temperature sensor offset from -2 to 2°C with a 0.5°C increment."""
        thermostat = get_thermostat(service)
        if not isinstance(thermostat, Neviweb130HeatCoolThermostat):
            raise ServiceValidationError(f"Entity {thermostat.entity_id} must be a {DOMAIN} heat-cool thermostat")
        value = {
            "id": thermostat.unique_id,
            "temp": service.data[ATTR_TEMP_OFFSET_HEAT],
        }
        thermostat.set_temperature_offset(value)
        thermostat.schedule_update_ha_state(True)

    def set_aux_heating_source_service(service: ServiceCall) -> None:
        """Set TH6500WF, TH6250WF auxiliary heating device."""
        thermostat = get_thermostat(service)
        if not isinstance(thermostat, Neviweb130HeatCoolThermostat):
            raise ServiceValidationError(f"Entity {thermostat.entity_id} must be a {DOMAIN} heat-cool thermostat")
        value = {
            "id": thermostat.unique_id,
            ATTR_AUX_HEAT_SOURCE_TYPE: service.data[ATTR_AUX_HEAT_SOURCE_TYPE],
        }
        thermostat.set_aux_heating_source(value)
        thermostat.schedule_update_ha_state(True)

    def set_fan_speed_service(service: ServiceCall) -> None:
        """Set TH6500WF, TH6250WF fan speed, On or Auto."""
        thermostat = get_thermostat(service)
        if not isinstance(thermostat, Neviweb130HeatCoolThermostat):
            raise ServiceValidationError(f"Entity {thermostat.entity_id} must be a {DOMAIN} heat-cool thermostat")
        value = {
            "id": thermostat.unique_id,
            "speed": service.data[ATTR_FAN_SPEED],
        }
        thermostat.set_fan_speed(value)
        thermostat.schedule_update_ha_state(True)

    def set_humidity_mode_service(service: ServiceCall) -> None:
        """Set TH6500WF, TH6250WF fan speed, On or Auto."""
        thermostat = get_thermostat(service)
        if not isinstance(thermostat, Neviweb130HeatCoolThermostat):
            raise ServiceValidationError(f"Entity {thermostat.entity_id} must be a {DOMAIN} heat-cool thermostat")
        value = {
            "id": thermostat.unique_id,
            "mode": service.data[ATTR_HUMIDITY_SETPOINT_MODE],
        }
        thermostat.set_humidity_mode(value)
        thermostat.schedule_update_ha_state(True)

    def set_heat_dissipation_time_service(service: ServiceCall) -> None:
        """Set TH6500WF, TH6250WF fan speed, On or Auto."""
        thermostat = get_thermostat(service)
        if not isinstance(thermostat, Neviweb130HeatCoolThermostat):
            raise ServiceValidationError(f"Entity {thermostat.entity_id} must be a {DOMAIN} heat-cool thermostat")
        value = {
            "id": thermostat.unique_id,
            ATTR_TIME: service.data[ATTR_TIME] * 60,
        }
        thermostat.set_heat_dissipation_time(value)
        thermostat.schedule_update_ha_state(True)

    def set_cool_dissipation_time_service(service: ServiceCall) -> None:
        """Set TH6500WF, TH6250WF fan speed, On or Auto."""
        thermostat = get_thermostat(service)
        if not isinstance(thermostat, Neviweb130HeatCoolThermostat):
            raise ServiceValidationError(f"Entity {thermostat.entity_id} must be a {DOMAIN} heat-cool thermostat")
        value = {
            "id": thermostat.unique_id,
            ATTR_TIME: service.data[ATTR_TIME] * 60,
        }
        thermostat.set_cool_dissipation_time(value)
        thermostat.schedule_update_ha_state(True)

    def set_climate_neviweb_status_service(service):
        """Set Neviweb global status per location, home or away."""
        entity_id = service.data[ATTR_ENTITY_ID]
        for thermostat in entities:
            if thermostat.entity_id == entity_id:
                value = {"id": thermostat.unique_id, "mode": service.data[ATTR_MODE]}
                thermostat.set_climate_neviweb_status(value)
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
        SERVICE_SET_ROOM_SETPOINT_AWAY,
        set_room_setpoint_away_service,
        schema=SET_ROOM_SETPOINT_AWAY_SCHEMA,
    )

    hass.services.async_register(
        DOMAIN,
        SERVICE_SET_COOL_SETPOINT_AWAY,
        set_cool_setpoint_away_service,
        schema=SET_COOL_SETPOINT_AWAY_SCHEMA,
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

    hass.services.async_register(
        DOMAIN,
        SERVICE_SET_SENSOR_TYPE,
        set_sensor_type_service,
        schema=SET_SENSOR_TYPE_SCHEMA,
    )

    hass.services.async_register(
        DOMAIN,
        SERVICE_SET_EM_HEAT,
        set_em_heat_service,
        schema=SET_EM_HEAT_SCHEMA,
    )

    hass.services.async_register(
        DOMAIN,
        SERVICE_SET_HEAT_PUMP_OPERATION_LIMIT,
        set_heat_pump_operation_limit_service,
        schema=SET_HEAT_PUMP_OPERATION_LIMIT_SCHEMA,
    )

    hass.services.async_register(
        DOMAIN,
        SERVICE_SET_COOL_LOCKOUT_TEMPERATURE,
        set_cool_lockout_temperature_service,
        schema=SET_COOL_LOCKOUT_TEMPERATURE_SCHEMA,
    )

    hass.services.async_register(
        DOMAIN,
        SERVICE_SET_HEAT_LOCKOUT_TEMPERATURE,
        set_heat_lockout_temperature_service,
        schema=SET_HEAT_LOCKOUT_TEMPERATURE_SCHEMA,
    )

    hass.services.async_register(
        DOMAIN,
        SERVICE_SET_DISPLAY_CONFIG,
        set_display_config_service,
        schema=SET_DISPLAY_CONFIG_SCHEMA,
    )

    hass.services.async_register(
        DOMAIN,
        SERVICE_SET_SOUND_CONFIG,
        set_sound_config_service,
        schema=SET_SOUND_CONFIG_SCHEMA,
    )

    hass.services.async_register(
        DOMAIN,
        SERVICE_SET_HC_SECOND_DISPLAY,
        set_hc_second_display_service,
        schema=SET_HC_SECOND_DISPLAY_SCHEMA,
    )

    hass.services.async_register(
        DOMAIN,
        SERVICE_SET_LANGUAGE,
        set_language_service,
        schema=SET_LANGUAGE_SCHEMA,
    )

    hass.services.async_register(
        DOMAIN,
        SERVICE_SET_REVERSING_VALVE_POLARITY,
        set_reversing_valve_polarity,
        schema=SET_REVERSING_VALVE_POLARITY_SCHEMA,
    )

    hass.services.async_register(
        DOMAIN,
        SERVICE_SET_MIN_TIME_ON,
        set_min_time_on_service,
        schema=SET_MIN_TIME_ON_SCHEMA,
    )

    hass.services.async_register(
        DOMAIN,
        SERVICE_SET_MIN_TIME_OFF,
        set_min_time_off_service,
        schema=SET_MIN_TIME_OFF_SCHEMA,
    )

    hass.services.async_register(
        DOMAIN,
        SERVICE_SET_HEAT_INTERSTAGE_DELAY,
        set_heat_interstage_delay,
        schema=SET_HEAT_INTERSTAGE_DELAY_SCHEMA,
    )

    hass.services.async_register(
        DOMAIN,
        SERVICE_SET_COOL_INTERSTAGE_DELAY,
        set_cool_interstage_delay,
        schema=SET_COOL_INTERSTAGE_DELAY_SCHEMA,
    )

    hass.services.async_register(
        DOMAIN,
        SERVICE_SET_ACCESSORY_TYPE,
        set_accessory_type_service,
        schema=SET_ACCESSORY_TYPE_SCHEMA,
    )

    hass.services.async_register(
        DOMAIN,
        SERVICE_SET_SCHEDULE_MODE,
        set_schedule_mode_service,
        schema=SET_SCHEDULE_MODE_SCHEMA,
    )

    hass.services.async_register(
        DOMAIN,
        SERVICE_SET_HEATCOOL_SETPOINT_DELTA,
        set_heatcool_setpoint_delta_service,
        schema=SET_HEATCOOL_SETPOINT_DELTA_SCHEMA,
    )

    hass.services.async_register(
        DOMAIN,
        SERVICE_SET_FAN_FILTER_REMINDER,
        set_fan_filter_reminder_service,
        schema=SET_FAN_FILTER_REMINDER_SCHEMA,
    )

    hass.services.async_register(
        DOMAIN,
        SERVICE_SET_TEMPERATURE_OFFSET,
        set_temperature_offset_service,
        schema=SET_TEMPERATURE_OFFSET_SCHEMA,
    )

    hass.services.async_register(
        DOMAIN,
        SERVICE_SET_AUX_HEATING_SOURCE,
        set_aux_heating_source_service,
        schema=SET_AUX_HEATING_SOURCE_SCHEMA,
    )

    hass.services.async_register(
        DOMAIN,
        SERVICE_SET_FAN_SPEED,
        set_fan_speed_service,
        schema=SET_FAN_SPEED_SCHEMA,
    )

    hass.services.async_register(
        DOMAIN,
        SERVICE_SET_HUMIDITY_SETPOINT_MODE,
        set_humidity_mode_service,
        schema=SET_HUMIDITY_SETPOINT_MODE_SCHEMA,
    )

    hass.services.async_register(
        DOMAIN,
        SERVICE_SET_HEAT_DISSIPATION_TIME,
        set_heat_dissipation_time_service,
        schema=SET_HEAT_DISSIPATION_TIME_SCHEMA,
    )

    hass.services.async_register(
        DOMAIN,
        SERVICE_SET_COOL_DISSIPATION_TIME,
        set_cool_dissipation_time_service,
        schema=SET_COOL_DISSIPATION_TIME_SCHEMA,
    )

    hass.services.async_register(
        DOMAIN,
        SERVICE_SET_CLIMATE_NEVIWEB_STATUS,
        set_climate_neviweb_status_service,
        schema=SET_CLIMATE_NEVIWEB_STATUS_SCHEMA,
    )


def neviweb_to_ha(value: int) -> str:
    last = ""
    for k, v in sorted(CYCLE_LENGTH_VALUES.items(), key=lambda x: x[1]):
        last = k
        if value <= v:
            return k
    return last


def lock_to_ha(lock: str) -> str:
    """Convert keypad lock state to better description."""
    match lock:
        case "locked":
            return "Locked"
        case "lock":
            return "Locked"
        case "partiallyLocked":
            return "Tamper protection"
        case "partialLock":
            return "Tamper protection"
    return "Unlocked"


def extract_capability_full(cap):
    """Extract swing capability which are True for each HP device and add general capability."""
    value = {i for i in cap if cap[i] is True}
    return FULL_SWING_OFF + sorted(value)


def extract_capability(cap):
    """Extract capability which are True for each HP device."""
    value = {i for i in cap if cap[i] is True}
    return sorted(value)


class Neviweb130Thermostat(ClimateEntity):
    """Implementation of Neviweb TH1123ZB, TH1124ZB thermostat."""

    _enable_turn_on_off_backwards_compatibility = False
    _attr_precision = 0.1
    _attr_target_temperature_step = 0.5

    def __init__(self, data, device_info, name, sku, firmware, location):
        """Initialize."""
        _LOGGER.debug("Setting up %s: %s", name, device_info)
        self._name = name
        self._location = str(location)
        self._sku = sku
        self._firmware = firmware
        self._client = data.neviweb130_client
        self._id = str(device_info["id"])
        self._device_model = device_info["signature"]["model"]
        self._device_model_cfg = device_info["signature"]["modelCfg"]
        self._is_double = device_info["signature"]["model"] in DEVICE_MODEL_DOUBLE
        self._is_h_c = device_info["signature"]["model"] in DEVICE_MODEL_HC
        self._is_HC = device_info["signature"]["model"] in DEVICE_MODEL_HEAT_COOL
        self._is_gen2 = device_info["signature"]["model"] in DEVICE_MODEL_HEAT_G2
        self._is_floor = device_info["signature"]["model"] in DEVICE_MODEL_FLOOR
        self._is_wifi_floor = device_info["signature"]["model"] in DEVICE_MODEL_WIFI_FLOOR
        self._is_wifi = (
            device_info["signature"]["model"] in DEVICE_MODEL_WIFI_FLOOR
            or device_info["signature"]["model"] in DEVICE_MODEL_WIFI
            or device_info["signature"]["model"] in DEVICE_MODEL_LOW_WIFI
            or device_info["signature"]["model"] in DEVICE_MODEL_WIFI_LITE
            or device_info["signature"]["model"] in DEVICE_MODEL_HEAT_COOL
            or device_info["signature"]["model"] in DEVICE_MODEL_COLOR_WIFI
        )
        self._is_wifi_lite = device_info["signature"]["model"] in DEVICE_MODEL_WIFI_LITE
        self._is_low_voltage = device_info["signature"]["model"] in DEVICE_MODEL_LOW
        self._is_low_wifi = device_info["signature"]["model"] in DEVICE_MODEL_LOW_WIFI
        self._is_HP = device_info["signature"]["model"] in DEVICE_MODEL_HEAT_PUMP
        self._is_color_wifi = device_info["signature"]["model"] in DEVICE_MODEL_COLOR_WIFI
        self._active = True
        self._aux_cycle_length = 0
        self._avail_mode = None
        self._backlight = None
        self._balance_pt = None
        self._balance_pt_high = None
        self._balance_pt_low = None
        self._cool_lock_temp = None
        self._cool_max = 36
        self._cool_min = 15
        self._cur_temp = None
        self._cur_temp_before = None
        self._cycle_length = 0
        self._cycle_length_output2_status = "off"
        self._cycle_length_output2_value = 0
        self._daily_kwh_count = 0
        self._display2 = None
        self._display_conf = None
        self._drsetpoint_status = "off"
        self._drsetpoint_value = 0
        self._drstatus_abs = "off"
        self._drstatus_active = "off"
        self._drstatus_onoff = "off"
        self._drstatus_optout = "off"
        self._drstatus_rel = "off"
        self._drstatus_setpoint = "off"
        self._early_start = None
        self._em_heat = "off"
        self._energy_stat_time = time.time() - 1500
        self._error_code = None
        self._fan_speed = None
        self._fan_swing_cap = None
        self._fan_swing_cap_horiz = None
        self._fan_swing_cap_vert = None
        self._fan_swing_horiz = None
        self._fan_swing_vert = None
        self._floor_air_limit = None
        self._floor_max = None
        self._floor_max_status = None
        self._floor_min = None
        self._floor_min_status = None
        self._floor_mode = None
        self._floor_sensor_type = None
        self._heat_level = 0
        self._heat_lockout_temp = None
        self._hour_kwh = 0
        self._hourly_kwh_count = 0
        self._keypad = "unlocked"
        self._language = None
        self._load2 = None
        self._load2_status = None
        self._mark = None
        self._marker = None
        self._max_temp = 30
        self._min_temp = 5
        self._month_kwh = 0
        self._monthly_kwh_count = 0
        self._occupancy = "home"
        self._occupancy_mode = "home"
        self._operation_mode = None
        self._pump_protec_duration = None
        self._pump_protec_period = None
        self._pump_protec_status = None
        self._rssi = None
        self._snooze = 0.0
        self._sound_conf = None
        self._target_cool = 21.5
        self._target_temp = 20.0
        self._target_temp_away = None
        self._temp_display_value = None
        self._temperature = 20.0
        self._temperature_format = "celsius"
        self._time_format = "24h"
        self._today_kwh = 0
        self._total_kwh_count = 0
        self._wattage = 0
        self._weather_icon = 0

    def update(self) -> None:
        if self._active:
            HEAT_ATTRIBUTES = [
                ATTR_WATTAGE,
                ATTR_KEYPAD,
                ATTR_BACKLIGHT,
                ATTR_SYSTEM_MODE,
                ATTR_CYCLE_LENGTH,
                ATTR_DISPLAY2,
                ATTR_RSSI,
            ]
            if self._firmware == "0.6.4" or self._firmware == "0.6.0":
                FIRMWARE_SPECIAL = []
            else:
                FIRMWARE_SPECIAL = [ATTR_ROOM_TEMP_DISPLAY]
            """Get the latest data from Neviweb and update the state."""
            start = time.time()
            _LOGGER.debug(
                "Updated attributes for %s: %s",
                self._name,
                UPDATE_ATTRIBUTES + HEAT_ATTRIBUTES + FIRMWARE_SPECIAL,
            )
            device_data = self._client.get_device_attributes(
                self._id, UPDATE_ATTRIBUTES + HEAT_ATTRIBUTES + FIRMWARE_SPECIAL
            )
            neviweb_status = self._client.get_neviweb_status(self._location)
            end = time.time()
            elapsed = round(end - start, 3)
            _LOGGER.debug(
                "Updating %s (%s sec): %s",
                self._name,
                elapsed,
                device_data,
            )

            if "error" not in device_data:
                if "errorCode" not in device_data:
                    self._cur_temp_before = self._cur_temp
                    self._cur_temp = (
                        float(device_data[ATTR_ROOM_TEMPERATURE]["value"])
                        if device_data[ATTR_ROOM_TEMPERATURE]["value"] is not None
                        else self._cur_temp_before
                    )
                    self._target_temp = float(device_data[ATTR_ROOM_SETPOINT])
                    self._min_temp = device_data[ATTR_ROOM_SETPOINT_MIN]
                    self._max_temp = device_data[ATTR_ROOM_SETPOINT_MAX]
                    self._temperature_format = device_data[ATTR_TEMP]
                    self._time_format = device_data[ATTR_TIME_FORMAT]
                    if ATTR_ROOM_TEMP_DISPLAY in device_data:
                        self._temp_display_value = device_data[ATTR_ROOM_TEMP_DISPLAY]
                    self._display2 = device_data[ATTR_DISPLAY2]
                    if ATTR_DRSETPOINT in device_data:
                        self._drsetpoint_status = device_data[ATTR_DRSETPOINT]["status"]
                        self._drsetpoint_value = (
                            device_data[ATTR_DRSETPOINT]["value"]
                            if device_data[ATTR_DRSETPOINT]["value"] is not None
                            else 0
                        )
                    if ATTR_DRSTATUS in device_data:
                        self._drstatus_active = device_data[ATTR_DRSTATUS]["drActive"]
                        self._drstatus_optout = device_data[ATTR_DRSTATUS]["optOut"]
                        self._drstatus_setpoint = device_data[ATTR_DRSTATUS]["setpoint"]
                        self._drstatus_abs = device_data[ATTR_DRSTATUS]["powerAbsolute"]
                        self._drstatus_rel = device_data[ATTR_DRSTATUS]["powerRelative"]

                    self._heat_level = device_data[ATTR_OUTPUT_PERCENT_DISPLAY]
                    self._keypad = device_data[ATTR_KEYPAD]
                    self._backlight = device_data[ATTR_BACKLIGHT]
                    if ATTR_CYCLE_LENGTH in device_data:
                        self._cycle_length = device_data[ATTR_CYCLE_LENGTH]
                    if ATTR_RSSI in device_data:
                        self._rssi = device_data[ATTR_RSSI]
                    self._operation_mode = device_data[ATTR_SYSTEM_MODE]
                    if not self._is_low_voltage:
                        self._wattage = device_data[ATTR_WATTAGE]
                elif device_data["errorCode"] == "ReadTimeout":
                    _LOGGER.warning(
                        "A timeout occur during data update. Device %s do not respond. Check your network... (%s)",
                        self._name,
                        device_data,
                    )
                else:
                    _LOGGER.warning("Error in updating device %s: (%s)", self._name, device_data)
            else:
                self.log_error(device_data["error"]["code"])
            self._occupancy_mode = neviweb_status[ATTR_OCCUPANCY]
            self.do_stat(start)
            self.get_sensor_error_code(start)
            self.get_weather()
        else:
            if time.time() - self._snooze > SNOOZE_TIME:
                self._active = True
                if NOTIFY == "notification" or NOTIFY == "both":
                    self.notify_ha("Warning: Neviweb Device update restarted for " + self._name + ", Sku: " + self._sku)

    @property
    @override
    def unique_id(self) -> str:
        """Return unique ID based on Neviweb130 device ID."""
        return self._id

    @property
    @override
    def name(self) -> str:
        """Return the name of the thermostat."""
        return self._name

    @property
    @override
    def temperature_unit(self) -> UnitOfTemperature:
        """Return the unit of measurement of this entity, if any."""
        # Will always send Celsius values even if it's configured to display in Fahrenheit
        return UnitOfTemperature.CELSIUS

    @property
    @override
    def device_class(self) -> SensorDeviceClass:
        """Return the device class of this entity."""
        return SensorDeviceClass.TEMPERATURE

    @property
    @override
    def extra_state_attributes(self) -> Mapping[str, Any]:
        """Return the state attributes."""
        data = {}
        data.update(
            {
                "neviweb_occupancy_mode": self._occupancy_mode,
                "wattage": self._wattage,
                "cycle_length": neviweb_to_ha(self._cycle_length),
                "error_code": self._error_code,
                "heat_level": self._heat_level,
                "pi_heating_demand": self._heat_level,
                "temp_display_value": self._temp_display_value,
                "second_display": self._display2,
                "keypad": lock_to_ha(self._keypad),
                "backlight": self._backlight,
                "time_format": self._time_format,
                "temperature_format": self._temperature_format,
                "setpoint_max": self._max_temp,
                "setpoint_min": self._min_temp,
                "eco_status": self._drstatus_active,
                "eco_optOut": self._drstatus_optout,
                "eco_setpoint": self._drstatus_setpoint,
                "eco_power_relative": self._drstatus_rel,
                "eco_power_absolute": self._drstatus_abs,
                "eco_setpoint_status": self._drsetpoint_status,
                "eco_setpoint_delta": self._drsetpoint_value,
                "total_kwh_count": self._total_kwh_count,
                "monthly_kwh_count": self._monthly_kwh_count,
                "daily_kwh_count": self._daily_kwh_count,
                "hourly_kwh_count": self._hourly_kwh_count,
                "hourly_kwh": self._hour_kwh,
                "daily_kwh": self._today_kwh,
                "monthly_kwh": self._month_kwh,
                "last_energy_stat_update": self._mark,
                "outdoor_temp": self._temperature,
                "weather_icon": self._weather_icon,
                "rssi": self._rssi,
                "sku": self._sku,
                "device_model": str(self._device_model),
                "device_model_cfg": self._device_model_cfg,
                "firmware": self._firmware,
                "activation": self._active,
                "id": self._id,
            }
        )
        return data

    @property
    def pi_heating_demand(self) -> int:
        """Heating demand."""
        return self._heat_level

    @property
    @override
    def supported_features(self) -> ClimateEntityFeature:
        """Return the list of supported features."""
        if self._is_floor or self._is_wifi_floor or self._is_low_wifi or self._is_low_voltage:
            return SUPPORT_AUX_FLAGS
        elif self._is_HP:
            return SUPPORT_HP_FLAGS
        elif self._is_h_c:
            return SUPPORT_H_c_FLAGS
        else:
            return SUPPORT_FLAGS

    @property
    def is_em_heat(self) -> bool:
        """Return emergency heat state."""
        if self._em_heat == "slave":
            return True
        elif self._cycle_length_output2_status == "on":
            return True
        elif self._aux_cycle_length > 0:
            return True
        else:
            return False

    @property
    @override
    def target_temperature_low(self) -> float:
        """(deprecated, use min_temp) Return the minimum heating temperature."""
        return self._min_temp

    @property
    @override
    def target_temperature_high(self) -> float:
        """(deprecated, use max_temp) Return the maximum heating temperature."""
        return self._max_temp

    @property
    @override
    def min_temp(self) -> float:
        """Return the minimum temperature."""
        return self._min_temp

    @property
    @override
    def max_temp(self) -> float:
        """Return the maximum temperature."""
        return self._max_temp

    @property
    def min_cool_temp(self) -> float:
        """Return the minimum cooling temperature."""
        return self._cool_min

    @property
    def max_cool_temp(self) -> float:
        """Return the maximum cooling temperature."""
        return self._cool_max

    @property
    def outdoor_temp(self) -> float:
        return self._temperature

    @property
    def weather_icon(self) -> int:
        return self._weather_icon

    @property
    @override
    def hvac_mode(self) -> HVACMode:
        """Return current operation."""
        if self._operation_mode == HVACMode.OFF:
            return HVACMode.OFF
        elif self._operation_mode in [HVACMode.AUTO, MODE_AUTO_BYPASS]:
            return HVACMode.AUTO
        elif self._operation_mode == HVACMode.COOL:
            return HVACMode.COOL
        elif self._operation_mode == HVACMode.DRY:
            return HVACMode.DRY
        elif self._operation_mode == HVACMode.FAN_ONLY:
            return HVACMode.FAN_ONLY
        else:
            return HVACMode.HEAT

    @property
    @override
    def hvac_modes(self) -> list[HVACMode]:
        """Return the list of available operation modes."""
        if self._is_wifi_lite:
            return SUPPORTED_HVAC_WIFI_LITE_MODES
        elif self._is_wifi:
            return SUPPORTED_HVAC_WIFI_MODES
        elif self._is_h_c:
            return SUPPORTED_HVAC_H_C_MODES
        elif self._is_HP:
            if self._avail_mode == "heatingOnly":
                return SUPPORTED_HVAC_HEAT_MODES
            elif self._avail_mode == "coolingOnly":
                return SUPPORTED_HVAC_COOL_MODES
            else:
                return SUPPORTED_HVAC_HP_MODES
        else:
            return SUPPORTED_HVAC_MODES

    @property
    @override
    def current_temperature(self) -> float | None:
        """Return the room current temperature."""
        return self._cur_temp

    @property
    @override
    def target_temperature(self) -> float | None:
        """Return the temperature we try to reach less Eco Sinope dr_setpoint delta."""
        if self._target_temp is not None:
            temp = self._target_temp + self._drsetpoint_value
        else:
            temp = 0
        if temp < self._min_temp:
            return self._min_temp
        if temp > self._max_temp:
            return self._max_temp
        return temp

    @property
    def target_cool_temperature(self) -> float:
        """Return the cooling temperature we try to reach."""
        if self._target_cool is not None:
            temp = self._target_cool
        else:
            temp = 0
        if temp < self._cool_min:
            return self._cool_min
        if temp > self._cool_max:
            return self._cool_max
        return temp

    @property
    @override
    def preset_mode(self) -> str:
        """Return current preset mode."""
        if self._occupancy == PRESET_HOME:
            return PRESET_HOME
        elif self._occupancy == PRESET_AWAY:
            return PRESET_AWAY
        else:
            return PRESET_NONE

    @property
    @override
    def preset_modes(self) -> list[str]:
        """Return available preset modes."""
        if self._is_h_c:
            return PRESET_h_c_MODES
        elif self._is_wifi:
            return PRESET_WIFI_MODES
        elif self._is_HP:
            return PRESET_HP_MODES
        else:
            return PRESET_MODES

    @property
    @override
    def hvac_action(self) -> HVACAction:
        """Return current HVAC action."""
        if self._operation_mode == HVACMode.OFF:
            return HVACAction.OFF
        elif self._operation_mode == HVACMode.COOL:
            return HVACAction.COOLING
        elif self._operation_mode == HVACMode.FAN_ONLY:
            return HVACAction.FAN
        elif self._operation_mode == HVACMode.DRY:
            return HVACAction.DRYING
        elif self._heat_level == 0:
            return HVACAction.IDLE
        else:
            return HVACAction.HEATING

    @property
    def is_on(self) -> bool:
        """Return True if mode = HVACMode.HEAT or HVACMode.COOL."""
        return (
            self._operation_mode == HVACMode.HEAT
            or self._operation_mode == HVACMode.COOL
            or self._operation_mode == HVACMode.DRY
            or self._operation_mode == HVACMode.AUTO
            or self._operation_mode == MODE_MANUAL
        )

    @property
    @override
    def fan_mode(self) -> str | None:
        """Return the fan setting."""
        return self._fan_speed

    @property
    @override
    def fan_modes(self) -> list[str] | None:
        """Return available fan modes."""
        if self._is_HP or self._is_h_c:
            return FAN_SPEED
        else:
            return None

    @property
    @override
    def swing_mode(self) -> str | None:
        """Return the fan vertical swing setting."""
        if self._is_HP or self._is_h_c:
            return self._fan_swing_vert
        return None

    @property
    @override
    def swing_modes(self) -> list[str] | None:
        """Return available vertical swing modes."""
        if self._is_HP or self._is_h_c:
            if self._fan_swing_cap is None or self._fan_swing_cap_vert is None:
                return None
            elif not extract_capability(self._fan_swing_cap):
                return None
            elif "fullVertical" in extract_capability(self._fan_swing_cap):
                return FULL_SWING + extract_capability_full(self._fan_swing_cap_vert)
            else:
                return extract_capability_full(self._fan_swing_cap_vert)
        else:
            return None

    @property
    @override
    def swing_horizontal_mode(self) -> str | None:
        """Return the fan swing setting."""
        if self._is_HP or self._is_h_c:
            return self._fan_swing_horiz
        return None

    @property
    @override
    def swing_horizontal_modes(self) -> list[str] | None:
        """Return available horizontal swing modes"""
        if self._is_HP or self._is_h_c:
            if self._fan_swing_cap is None or self._fan_swing_cap_horiz is None:
                return None
            elif not extract_capability(self._fan_swing_cap):
                return None
            elif "fullHorizontal" in extract_capability(self._fan_swing_cap):
                return FULL_SWING + extract_capability_full(self._fan_swing_cap_horiz)
            else:
                return extract_capability_full(self._fan_swing_cap_horiz)
        else:
            return None

    @override
    def set_fan_mode(self, speed: str) -> None:
        """Set new fan mode."""
        if speed is None:
            return
        self._client.set_fan_mode(self._id, speed)
        self._fan_speed = speed

    @override
    def set_swing_mode(self, swing: str) -> None:
        """Set new vertical swing mode."""
        if swing is None:
            return
        else:
            self._client.set_swing_vertical(self._id, swing)
            self._fan_swing_vert = swing

    @override
    def set_swing_horizontal_mode(self, swing: str) -> None:
        """Set new horizontal swing mode."""
        if swing is None:
            return
        else:
            self._client.set_swing_horizontal(self._id, swing)
            self._fan_swing_horiz = swing

    @override
    def turn_on(self) -> None:
        """Turn the thermostat to HVACMode.HEAT."""
        self._client.set_setpoint_mode(self._id, HVACMode.HEAT, self._is_wifi, self._is_HC)
        self._operation_mode = HVACMode.HEAT

    @override
    def turn_off(self) -> None:
        """Turn the thermostat to HVACMode.OFF."""
        self._client.set_setpoint_mode(self._id, HVACMode.OFF, self._is_wifi, self._is_HC)
        self._operation_mode = HVACMode.OFF

    @override
    def set_temperature(self, **kwargs: Any) -> None:
        """Set new target temperature."""
        temperature = kwargs.get(ATTR_TEMPERATURE)
        if temperature is None:
            return
        temperature = min(temperature, self._max_temp)
        temperature = max(temperature, self._min_temp)
        self._client.set_temperature(self._id, temperature)
        self._target_temp = temperature

    def set_second_display(self, value):
        """Set thermostat second display between outside and setpoint temperature."""
        if value["display"] == "outsideTemperature":
            display_name = "Outside"
        else:
            display_name = "Setpoint"
        self._client.set_second_display(value["id"], value["display"])
        self._display2 = display_name

    def set_backlight(self, value):
        """Set thermostat backlight «auto» = off when idle / on when active or «on» = always on.
        Work differently for Zigbee and Wi-Fi devices."""
        is_wifi = self._is_wifi or self._is_low_wifi or self._is_wifi_lite or self._is_wifi_floor
        if value["level"] == "on":
            if is_wifi:
                level_command = "alwaysOn"
            else:
                level_command = "always"
            level_name = "On"
        elif value["level"] == "bedroom":
            level_command = "bedroom"
            level_name = "bedroom"
        else:
            if is_wifi:
                level_command = "onUserAction"
            else:
                level_command = "onActive"
            level_name = "Auto"
        self._client.set_backlight(value["id"], level_command, is_wifi)
        self._backlight = level_name

    def set_keypad_lock(self, value):
        """Lock or unlock device's keypad, locked = Locked, unlocked = Unlocked."""
        if value["lock"] == "partiallyLocked" and self._is_wifi:
            lock = "partialLock"
        elif value["lock"] == "locked":
            lock = "lock"
        else:
            lock = "unlock"
        self._client.set_keypad_lock(value["id"], lock, self._is_wifi)
        self._keypad = lock

    def set_time_format(self, value):
        """Set time format 12h or 24h."""
        if value[ATTR_TIME] == 12:
            time_command = "12h"
        else:
            time_command = "24h"
        self._client.set_time_format(value["id"], time_command)
        self._time_format = time_command

    def set_temperature_format(self, value):
        """Set temperature format, celsius or fahrenheit."""
        self._client.set_temperature_format(value["id"], value["temp"])
        self._temperature_format = value["temp"]

    def set_air_floor_mode(self, value):
        """Switch temperature control between floor and ambient sensor."""
        self._client.set_air_floor_mode(value["id"], value["mode"])
        self._floor_mode = value["mode"]

    def set_setpoint_max(self, value):
        """Set maximum setpoint temperature."""
        self._client.set_setpoint_max(value["id"], value["temp"])
        self._max_temp = value["temp"]

    def set_setpoint_min(self, value):
        """Set minimum setpoint temperature."""
        self._client.set_setpoint_min(value["id"], value["temp"])
        self._min_temp = value["temp"]

    def set_room_setpoint_away(self, value):
        """Set device away heating setpoint."""
        self._client.set_room_setpoint_away(value["id"], value["temp"])
        self._target_temp_away = value["temp"]

    def set_cool_setpoint_max(self, value):
        """Set maximum cooling setpoint temperature."""
        self._client.set_cool_setpoint_max(value["id"], value["temp"])
        self._cool_max = value["temp"]

    def set_cool_setpoint_min(self, value):
        """Set minimum cooling setpoint temperature."""
        self._client.set_cool_setpoint_min(value["id"], value["temp"])
        self._cool_min = value["temp"]

    def set_floor_air_limit(self, value):
        """Set maximum temperature air limit for floor thermostat."""
        if value["temp"] == 0:
            status = "off"
        else:
            status = "on"
        self._client.set_floor_air_limit(value["id"], status, value["temp"])
        self._floor_air_limit = value["temp"]

    def set_early_start(self, value):
        """Set early heating on/off for Wi-Fi thermostat."""
        self._client.set_early_start(value["id"], value["start"])
        self._early_start = value["start"]

    def set_hvac_dr_options(self, value):
        """Set thermostat DR options for Eco Sinope."""
        self._client.set_hvac_dr_options(
            value["id"], dractive=value["dractive"], optout=value["optout"], setpoint=value["setpoint"]
        )
        self._drstatus_active = value["dractive"]
        self._drstatus_optout = value["optout"]
        self._drstatus_setpoint = value["setpoint"]

    def set_hvac_dr_setpoint(self, value):
        """Set thermostat DR setpoint values for Eco Sinope."""
        self._client.set_hvac_dr_setpoint(value["id"], value["status"], value["val"])
        self._drsetpoint_status = value["status"]
        self._drsetpoint_value = value["val"]

    @override
    def set_hvac_mode(self, hvac_mode: HVACMode) -> None:
        """Set new hvac mode."""

        # Simple modes, we call directly set_point_mode
        simple_modes = [
            HVACMode.OFF,
            HVACMode.HEAT,
            MODE_MANUAL,
            HVACMode.COOL,
            HVACMode.DRY,
            HVACMode.FAN_ONLY,
            MODE_EM_HEAT,
        ]

        if hvac_mode in simple_modes:
            self._client.set_setpoint_mode(self._id, hvac_mode, self._is_wifi, self._is_HC)

        elif hvac_mode == HVACMode.AUTO:
            self._client.set_setpoint_mode(self._id, hvac_mode, self._is_wifi, self._is_HC)

        elif hvac_mode == HVACMode.HEAT_COOL:
            self._client.set_setpoint_mode(self._id, hvac_mode, self._is_wifi, self._is_HC)

        elif hvac_mode == MODE_AUTO_BYPASS:
            if self._operation_mode == HVACMode.AUTO:
                self._client.set_setpoint_mode(self._id, hvac_mode, self._is_wifi, self._is_HC)

        else:
            _LOGGER.error("Unable to set hvac mode: %s", hvac_mode)

        self._operation_mode = hvac_mode
        self.update()

    @override
    def set_preset_mode(self, preset_mode: str) -> None:
        """Activate a preset."""
        if preset_mode == self.preset_mode:
            return
        if preset_mode == PRESET_AWAY:
            self._client.set_occupancy_mode(self._id, PRESET_AWAY, self._is_wifi)
        elif preset_mode == PRESET_HOME:
            self._client.set_occupancy_mode(self._id, PRESET_HOME, self._is_wifi)
        elif preset_mode == PRESET_NONE:
            self._client.set_occupancy_mode(self._id, PRESET_NONE, self._is_wifi)
            # Re-apply current hvac_mode without any preset
            self.set_hvac_mode(self.hvac_mode)
        else:
            _LOGGER.error("Unable to set preset mode: %s", preset_mode)
        self._occupancy = preset_mode

    def turn_em_heat_on(self):
        """Turn emergency heater on."""
        if self._is_low_voltage:
            value = "on"
            low = "voltage"
            sec = self._cycle_length_output2_value
            self._cycle_length_output2_status = "on"
        elif self._is_low_wifi:
            value = ""
            low = "wifi"
            sec = self._aux_cycle_length
        else:
            value = "slave"
            sec = 0
            low = "floor"
            self._em_heat = "slave"
        self._client.set_em_heat(self._id, value, low, sec)

    def turn_em_heat_off(self):
        """Turn emergency heater off."""
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
            self._em_heat = "off"
            sec = 0
        self._client.set_em_heat(self._id, "off", low, sec)

    def set_auxiliary_load(self, value):
        """Set thermostat auxiliary output status and load."""
        self._client.set_auxiliary_load(value["id"], value["status"], value["val"])
        self._load2_status = value["status"]
        self._load2 = value["val"]

    def set_aux_cycle_output(self, value):
        """Set low voltage thermostats auxiliary cycle status and length."""
        length: int = CYCLE_LENGTH_VALUES[value["val"]]
        is_wifi = self._is_low_wifi or (self._is_wifi and self._is_HC)
        if is_wifi and length == 0:
            raise ServiceValidationError(f"Entity {self.entity_id} does not support value 'off'")
        self._client.set_aux_cycle_output(value["id"], length, is_wifi)
        if is_wifi:
            self._aux_cycle_length = length
        elif length > 0:
            self._cycle_length_output2_status = "on"
            self._cycle_length_output2_value = length
        else:
            # Leaving self._cycle_length_output2_value to the old value on purpose
            self._cycle_length_output2_status = "off"

    def set_cycle_output(self, value):
        """Set low voltage thermostats main cycle output length."""
        length: int = CYCLE_LENGTH_VALUES[value["val"]]
        if length == 0:
            raise ServiceValidationError(f"Entity {self.entity_id} does not support value 'off'")
        self._client.set_cycle_output(value["id"], length, self._is_HC)
        self._cycle_length = length

    def set_pump_protection(self, value):
        """Set pump protection value."""
        self._client.set_pump_protection(value["id"], value["status"], self._is_low_wifi)
        self._pump_protec_status = value["status"]
        self._pump_protec_duration = 60
        self._pump_protec_period = 1

    def set_sensor_type(self, value):
        """Set sensor type."""
        self._client.set_sensor_type(value["id"], value["type"])
        self._floor_sensor_type = value["type"]

    def set_floor_limit(self, value):
        """Set maximum/minimum floor setpoint temperature."""
        temp = value["level"]
        limit = value["limit"]
        if limit == "low":
            if 0 < temp < 5:
                temp = 5
        else:
            if 0 < temp < 7:
                temp = 7
        self._client.set_floor_limit(value["id"], temp, limit, self._is_wifi_floor)
        if limit == "low":
            self._floor_min = temp if temp != 0 else None
            self._floor_min_status = "on"
        else:
            self._floor_max = temp if temp != 0 else None
            self._floor_max_status = "on"

    def set_activation(self, value):
        """Activate or deactivate neviweb polling for a missing device."""
        self._active = value["active"]

    def set_heat_pump_operation_limit(self, value):
        """Set minimum temperature for heat pump operation."""
        temp = value["temp"]
        if temp < self._balance_pt_low:
            temp = self._balance_pt_low
        self._client.set_heat_pump_limit(value["id"], temp)
        self._balance_pt = temp

    def set_heat_lockout_temperature(self, value):
        """Set maximum outside temperature limit to allow heat device operation."""
        self._client.set_heat_lockout(value["id"], value["temp"])
        self._heat_lockout_temp = value["temp"]

    def set_cool_lockout_temperature(self, value):
        """Set minimum outside temperature limit to allow cooling device operation."""
        self._client.set_cool_lockout(value["id"], value["temp"])
        self._cool_lock_temp = value["temp"]

    def set_display_config(self, value):
        """Set display on/off for heat pump."""
        self._client.set_hp_display(value["id"], value["display"])
        self._display_conf = value["display"]

    def set_sound_config(self, value):
        """Set sound on/off for heat pump."""
        self._client.set_hp_sound(value["id"], value["sound"])
        self._sound_conf = value["sound"]

    def set_hc_second_display(self, value):
        """Set second display value for TH1134ZB-HC."""
        self._client.set_hc_display(value["id"], value["display"])
        self._display2 = value["display"]

    def set_language(self, value):
        """Set display language value for TH1134ZB-HC."""
        self._client.set_language(value["id"], value["lang"])
        self._language = value["lang"]

    def get_weather(self):
        """Get weather temperature for my location."""
        weather = self._client.get_weather()
        self._temperature = weather["temperature"]
        self._weather_icon = weather["icon"]

    def set_climate_neviweb_status(self, value):
        """Set Neviweb global occupancy mode, away or home"""
        self._client.post_neviweb_status(self._location, value["mode"])
        self._occupancy_mode = value["mode"]

    def do_stat(self, start):
        """Get device energy statistic."""
        if start - self._energy_stat_time > STAT_INTERVAL and self._energy_stat_time != 0:
            today = date.today()
            current_month = today.month
            current_day = today.day
            device_monthly_stats = self._client.get_device_monthly_stats(self._id)
            _LOGGER.debug("%s device_monthly_stats = %s", self._name, device_monthly_stats)
            if device_monthly_stats is not None and len(device_monthly_stats) > 1:
                n = len(device_monthly_stats)
                monthly_kwh_count = 0
                k = 0
                while k < n:
                    monthly_kwh_count += device_monthly_stats[k]["period"] / 1000
                    k += 1
                self._monthly_kwh_count = round(monthly_kwh_count, 3)
                self._month_kwh = round(device_monthly_stats[n - 1]["period"] / 1000, 3)
                dt_month = datetime.fromisoformat(device_monthly_stats[n - 1]["date"][:-1] + "+00:00").astimezone(
                    timezone.utc
                )
                _LOGGER.debug("stat month = %s", dt_month.month)
            else:
                self._month_kwh = 0
                _LOGGER.warning("%s Got None for device_monthly_stats", self._name)
            device_daily_stats = self._client.get_device_daily_stats(self._id)
            _LOGGER.debug("%s device_daily_stats = %s", self._name, device_daily_stats)
            if device_daily_stats is not None and len(device_daily_stats) > 1:
                n = len(device_daily_stats)
                daily_kwh_count = 0
                k = 0
                while k < n:
                    if (
                        datetime.fromisoformat(device_daily_stats[k]["date"][:-1] + "+00:00")
                        .astimezone(timezone.utc)
                        .month
                        == current_month
                    ):
                        daily_kwh_count += device_daily_stats[k]["period"] / 1000
                    k += 1
                self._daily_kwh_count = round(daily_kwh_count, 3)
                self._today_kwh = round(device_daily_stats[n - 1]["period"] / 1000, 3)
                dt_day = datetime.fromisoformat(device_daily_stats[n - 1]["date"][:-1].replace("Z", "+00:00"))
                _LOGGER.debug("stat day = %s", dt_day.day)
            else:
                self._today_kwh = 0
                _LOGGER.warning("%s Got None for device_daily_stats", self._name)
            device_hourly_stats = self._client.get_device_hourly_stats(self._id)
            _LOGGER.debug(
                "%s device hourly stat (SKU: %s): %s, size = %s",
                self._name,
                self._sku,
                device_hourly_stats,
                len(device_hourly_stats) if device_hourly_stats is not None else None,
            )
            if device_hourly_stats is not None and len(device_hourly_stats) > 1:
                n = len(device_hourly_stats)
                hourly_kwh_count = 0
                k = 0
                while k < n:
                    if (
                        datetime.fromisoformat(device_hourly_stats[k]["date"][:-1].replace("Z", "+00:00")).day
                        == current_day
                    ):
                        hourly_kwh_count += device_hourly_stats[k]["period"] / 1000
                    k += 1
                self._hourly_kwh_count = round(hourly_kwh_count, 3)
                self._hour_kwh = round(device_hourly_stats[n - 1]["period"] / 1000, 3)
                self._marker = device_hourly_stats[n - 1]["date"]
                dt_hour = datetime.strptime(device_hourly_stats[n - 1]["date"], "%Y-%m-%dT%H:%M:%S.%fZ")
                _LOGGER.debug("stat hour = %s", dt_hour.hour)
            else:
                self._hour_kwh = 0
                _LOGGER.warning("%s Got None for device_hourly_stats", self._name)
            if self._total_kwh_count == 0:
                self._total_kwh_count = round(
                    self._monthly_kwh_count + self._daily_kwh_count + self._hourly_kwh_count,
                    3,
                )
                # await async_add_data(self._id, self._total_kwh_count, self._marker)
                # self.async_write_ha_state()
                self._mark = self._marker
            else:
                if self._marker != self._mark:
                    self._total_kwh_count += round(self._hour_kwh, 3)
                    # save_data(self._id, self._total_kwh_count, self._marker)
                    self._mark = self._marker
            self._energy_stat_time = time.time()
        if self._energy_stat_time == 0:
            self._energy_stat_time = start

    def get_sensor_error_code(self, start):
        """Get device sensor error code."""
        if not self._is_wifi:
            device_error_code = self._client.get_device_sensor_error(self._id)
            if device_error_code is not None and device_error_code != {}:
                if device_error_code["raw"] != 0:
                    self._error_code = device_error_code["raw"]
                    self.notify_ha(
                        "Warning: Neviweb Device error code detected: "
                        + str(device_error_code["raw"])
                        + " for device: "
                        + self._name
                        + ", ID: "
                        + str(self._id)
                        + ", Sku: "
                        + self._sku
                    )
                    _LOGGER.warning("Error code set1 updated: %s", str(device_error_code["raw"]))
                    self._energy_stat_time = time.time()
                if self._energy_stat_time == 0:
                    self._energy_stat_time = start

    def log_error(self, error_data):
        """Send error message to LOG."""
        if error_data == "USRSESSEXP":
            _LOGGER.warning("Session expired... Reconnecting...")
            if NOTIFY == "notification" or NOTIFY == "both":
                self.notify_ha(
                    "Warning: Got USRSESSEXP error, Neviweb session expired. "
                    + "Set your scan_interval parameter to less than 10 "
                    + "minutes to avoid this... Reconnecting..."
                )
            self._client.reconnect()
        elif error_data == "ACCDAYREQMAX":
            _LOGGER.warning("Maximum daily request reached... Reduce polling frequency")
        elif error_data == "TimeoutError":
            _LOGGER.warning("Timeout error detected... Retry later")
        elif error_data == "MAINTENANCE":
            _LOGGER.warning("Access blocked for maintenance... Retry later")
            self.notify_ha("Warning: Neviweb access temporary blocked for maintenance... Retry later")
            self._client.reconnect()
        elif error_data == "ACCSESSEXC":
            _LOGGER.warning("Maximum session number reached... Close other connections and try again")
            self.notify_ha("Warning: Maximum Neviweb session number reached... Close other connections and try again")
            self._client.reconnect()
        elif error_data == "DVCATTRNSPTD":
            _LOGGER.warning(
                "Device attribute not supported for %s (id: %s): %s... (SKU: %s)",
                self._name,
                str(self._id),
                error_data,
                self._sku,
            )
        elif error_data == "DVCACTNSPTD":
            _LOGGER.warning(
                "Device action not supported for %s... (id: %s, SKU: %s) Report to maintainer",
                self._name,
                str(self._id),
                self._sku,
            )
        elif error_data == "DVCCOMMTO":
            _LOGGER.warning(
                "Device Communication Timeout... The device %s (id: %s) "
                + "did not respond to the server within the prescribed delay"
                + " (SKU: %s)",
                self._name,
                str(self._id),
                self._sku,
            )
        elif error_data == "SVCERR":
            _LOGGER.warning(
                "Service error, device not available retry later %s: %s... (id: %s, SKU: %s)",
                self._name,
                error_data,
                str(self._id),
                self._sku,
            )
        elif error_data == "DVCBUSY":
            _LOGGER.warning(
                "Device busy can't reach (neviweb update ?), retry later %s (id: %s): %s... (SKU: %s)",
                self._name,
                str(self._id),
                error_data,
                self._sku,
            )
        elif error_data == "DVCUNVLB":
            _LOGGER.warning("NOTIFY value: %s, (SKU: %s)", NOTIFY, self._sku)
            if NOTIFY == "logging" or NOTIFY == "both":
                _LOGGER.warning(
                    "Device %s (id: %s) is disconnected from Neviweb: %s... (SKU: %s)",
                    self._name,
                    str(self._id),
                    error_data,
                    self._sku,
                )
                _LOGGER.warning(
                    "This device %s is de-activated and won't be updated for 20 minutes",
                    self._name,
                )
                _LOGGER.warning(
                    "You can re-activate device %s with "
                    + "service.neviweb130_set_activation or wait 20 minutes "
                    + "for update to restart or just restart HA",
                    self._name,
                )
            if NOTIFY == "notification" or NOTIFY == "both":
                self.notify_ha(
                    "Warning: Received message from Neviweb, device "
                    + "disconnected... Check your log... Neviweb update will "
                    + "be halted for 20 minutes for "
                    + self._name
                    + ", id: "
                    + str(self._id)
                    + ", Sku: "
                    + self._sku
                )
            self._active = False
            self._snooze = time.time()
        elif error_data == "DVCERR":
            _LOGGER.warning(
                "Device error for %s (id: %s), service already active: %s... (SKU: %s)",
                self._name,
                str(self._id),
                error_data,
                self._sku,
            )
        elif error_data == "SVCUNAUTH":
            _LOGGER.warning(
                "Service not authorised for device %s (id: %s): %s... (SKU: %s)",
                self._name,
                str(self._id),
                error_data,
                self._sku,
            )
        else:
            _LOGGER.warning(
                "Unknown error for %s (id: %s): %s... (SKU: %s) Report to maintainer",
                self._name,
                str(self._id),
                error_data,
                self._sku,
            )

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


class Neviweb130G2Thermostat(Neviweb130Thermostat):
    """Implementation of Neviweb TH1123ZB-G2, TH1124ZB-G2 thermostats."""

    def __init__(self, data, device_info, name, sku, firmware, location):
        super().__init__(data, device_info, name, sku, firmware, location)
        self._cold_load_pickup = None

    @override
    def update(self) -> None:
        if self._active:
            GEN2_ATTRIBUTES = [
                ATTR_ROOM_TEMP_DISPLAY,
                ATTR_WATTAGE,
                ATTR_DISPLAY2,
                ATTR_KEYPAD,
                ATTR_BACKLIGHT,
                ATTR_SYSTEM_MODE,
                ATTR_CYCLE_LENGTH,
                ATTR_COLD_LOAD_PICKUP,
                ATTR_HEAT_LOCKOUT_TEMP,
            ]
            """Get the latest data from Neviweb and update the state."""
            start = time.time()
            _LOGGER.debug(
                "Updated attributes for %s: %s",
                self._name,
                UPDATE_ATTRIBUTES + GEN2_ATTRIBUTES,
            )
            device_data = self._client.get_device_attributes(self._id, UPDATE_ATTRIBUTES + GEN2_ATTRIBUTES)
            neviweb_status = self._client.get_neviweb_status(self._location)
            end = time.time()
            elapsed = round(end - start, 3)
            _LOGGER.debug("Updating %s (%s sec): %s", self._name, elapsed, device_data)
            if "error" not in device_data:
                if "errorCode" not in device_data:
                    self._cur_temp_before = self._cur_temp
                    self._cur_temp = (
                        float(device_data[ATTR_ROOM_TEMPERATURE]["value"])
                        if device_data[ATTR_ROOM_TEMPERATURE]["value"] is not None
                        else self._cur_temp_before
                    )
                    self._target_temp = float(device_data[ATTR_ROOM_SETPOINT])
                    self._min_temp = device_data[ATTR_ROOM_SETPOINT_MIN]
                    self._max_temp = device_data[ATTR_ROOM_SETPOINT_MAX]
                    self._temperature_format = device_data[ATTR_TEMP]
                    self._time_format = device_data[ATTR_TIME_FORMAT]
                    self._temp_display_value = device_data[ATTR_ROOM_TEMP_DISPLAY]
                    self._display2 = device_data[ATTR_DISPLAY2]
                    if ATTR_DRSETPOINT in device_data:
                        self._drsetpoint_status = device_data[ATTR_DRSETPOINT]["status"]
                        self._drsetpoint_value = (
                            device_data[ATTR_DRSETPOINT]["value"]
                            if device_data[ATTR_DRSETPOINT]["value"] is not None
                            else 0
                        )
                    if ATTR_DRSTATUS in device_data:
                        self._drstatus_active = device_data[ATTR_DRSTATUS]["drActive"]
                        self._drstatus_optout = device_data[ATTR_DRSTATUS]["optOut"]
                        self._drstatus_setpoint = device_data[ATTR_DRSTATUS]["setpoint"]
                        self._drstatus_abs = device_data[ATTR_DRSTATUS]["powerAbsolute"]
                        self._drstatus_rel = device_data[ATTR_DRSTATUS]["powerRelative"]
                    if ATTR_COLD_LOAD_PICKUP in device_data:
                        self._cold_load_pickup = device_data[ATTR_COLD_LOAD_PICKUP]
                    if ATTR_HEAT_LOCKOUT_TEMP in device_data:
                        self._heat_lockout_temp = device_data[ATTR_HEAT_LOCKOUT_TEMP]
                    self._heat_level = device_data[ATTR_OUTPUT_PERCENT_DISPLAY]
                    self._keypad = device_data[ATTR_KEYPAD]
                    self._backlight = device_data[ATTR_BACKLIGHT]
                    if ATTR_CYCLE_LENGTH in device_data:
                        self._cycle_length = device_data[ATTR_CYCLE_LENGTH]
                    self._operation_mode = device_data[ATTR_SYSTEM_MODE]
                    self._wattage = device_data[ATTR_WATTAGE]
                elif device_data["errorCode"] == "ReadTimeout":
                    _LOGGER.warning(
                        "A timeout occur during data update. Device %s do not respond. Check your network... (%s)",
                        self._name,
                        device_data,
                    )
                else:
                    _LOGGER.warning("Error in updating device %s: (%s)", self._name, device_data)
            else:
                self.log_error(device_data["error"]["code"])
            self._occupancy_mode = neviweb_status[ATTR_OCCUPANCY]
            self.do_stat(start)
            self.get_sensor_error_code(start)
            self.get_weather()
        else:
            if time.time() - self._snooze > SNOOZE_TIME:
                self._active = True
                if NOTIFY == "notification" or NOTIFY == "both":
                    self.notify_ha("Warning: Neviweb Device update restarted for " + self._name + ", Sku: " + self._sku)

    @property
    @override
    def extra_state_attributes(self) -> Mapping[str, Any]:
        """Return the state attributes."""
        data = {}
        data.update(
            {
                "neviweb_occupancy_mode": self._occupancy_mode,
                "wattage": self._wattage,
                "cycle_length": neviweb_to_ha(self._cycle_length),
                "error_code": self._error_code,
                "heat_level": self._heat_level,
                "pi_heating_demand": self._heat_level,
                "temp_display_value": self._temp_display_value,
                "second_display": self._display2,
                "keypad": lock_to_ha(self._keypad),
                "backlight": self._backlight,
                "time_format": self._time_format,
                "temperature_format": self._temperature_format,
                "setpoint_max": self._max_temp,
                "setpoint_min": self._min_temp,
                "eco_status": self._drstatus_active,
                "eco_optOut": self._drstatus_optout,
                "eco_setpoint": self._drstatus_setpoint,
                "eco_power_relative": self._drstatus_rel,
                "eco_power_absolute": self._drstatus_abs,
                "eco_setpoint_status": self._drsetpoint_status,
                "eco_setpoint_delta": self._drsetpoint_value,
                "cold_load_pickup": self._cold_load_pickup,
                "heat_lockout_temp": self._heat_lockout_temp,
                "total_kwh_count": self._total_kwh_count,
                "monthly_kwh_count": self._monthly_kwh_count,
                "daily_kwh_count": self._daily_kwh_count,
                "hourly_kwh_count": self._hourly_kwh_count,
                "hourly_kwh": self._hour_kwh,
                "daily_kwh": self._today_kwh,
                "monthly_kwh": self._month_kwh,
                "last_energy_stat_update": self._mark,
                "outdoor_temp": self._temperature,
                "weather_icon": self._weather_icon,
                "sku": self._sku,
                "device_model": str(self._device_model),
                "device_model_cfg": self._device_model_cfg,
                "firmware": self._firmware,
                "activation": self._active,
                "id": self._id,
            }
        )
        return data


class Neviweb130FloorThermostat(Neviweb130Thermostat):
    """Implementation of Neviweb TH1300ZB, TH1320ZB-04, OTH3600-GA-ZB thermostat."""

    def __init__(self, data, device_info, name, sku, firmware, location):
        """Initialize."""
        super().__init__(data, device_info, name, sku, firmware, location)
        self._floor_air_limit_status = None
        self._floor_max_status = "off"
        self._floor_min_status = "off"
        self._gfci_alert = None
        self._gfci_status = None
        self._load2 = 0

    @override
    def update(self) -> None:
        if self._active:
            FLOOR_ATTRIBUTES = [
                ATTR_ROOM_TEMP_DISPLAY,
                ATTR_WATTAGE,
                ATTR_GFCI_STATUS,
                ATTR_GFCI_ALERT,
                ATTR_FLOOR_MODE,
                ATTR_FLOOR_AUX,
                ATTR_FLOOR_OUTPUT2,
                ATTR_FLOOR_AIR_LIMIT,
                ATTR_FLOOR_SENSOR,
                ATTR_FLOOR_MAX,
                ATTR_FLOOR_MIN,
                ATTR_KEYPAD,
                ATTR_BACKLIGHT,
                ATTR_SYSTEM_MODE,
                ATTR_CYCLE_LENGTH,
                ATTR_DISPLAY2,
                ATTR_RSSI,
            ]
            """Get the latest data from Neviweb and update the state."""
            start = time.time()
            _LOGGER.debug(
                "Updated attributes for %s: %s",
                self._name,
                UPDATE_ATTRIBUTES + FLOOR_ATTRIBUTES,
            )
            device_data = self._client.get_device_attributes(self._id, UPDATE_ATTRIBUTES + FLOOR_ATTRIBUTES)
            neviweb_status = self._client.get_neviweb_status(self._location)
            end = time.time()
            elapsed = round(end - start, 3)
            _LOGGER.debug("Updating %s (%s sec): %s", self._name, elapsed, device_data)
            if "error" not in device_data:
                if "errorCode" not in device_data:
                    self._cur_temp_before = self._cur_temp
                    self._cur_temp = (
                        float(device_data[ATTR_ROOM_TEMPERATURE]["value"])
                        if device_data[ATTR_ROOM_TEMPERATURE]["value"] is not None
                        else self._cur_temp_before
                    )
                    self._target_temp = float(device_data[ATTR_ROOM_SETPOINT])
                    self._min_temp = device_data[ATTR_ROOM_SETPOINT_MIN]
                    self._max_temp = device_data[ATTR_ROOM_SETPOINT_MAX]
                    self._temperature_format = device_data[ATTR_TEMP]
                    self._time_format = device_data[ATTR_TIME_FORMAT]
                    self._temp_display_value = device_data[ATTR_ROOM_TEMP_DISPLAY]
                    self._display2 = device_data[ATTR_DISPLAY2]
                    if ATTR_DRSETPOINT in device_data:
                        self._drsetpoint_status = device_data[ATTR_DRSETPOINT]["status"]
                        self._drsetpoint_value = (
                            device_data[ATTR_DRSETPOINT]["value"]
                            if device_data[ATTR_DRSETPOINT]["value"] is not None
                            else 0
                        )
                    if ATTR_DRSTATUS in device_data:
                        self._drstatus_active = device_data[ATTR_DRSTATUS]["drActive"]
                        self._drstatus_optout = device_data[ATTR_DRSTATUS]["optOut"]
                        self._drstatus_setpoint = device_data[ATTR_DRSTATUS]["setpoint"]
                        self._drstatus_abs = device_data[ATTR_DRSTATUS]["powerAbsolute"]
                        self._drstatus_rel = device_data[ATTR_DRSTATUS]["powerRelative"]
                    self._heat_level = device_data[ATTR_OUTPUT_PERCENT_DISPLAY]
                    self._keypad = device_data[ATTR_KEYPAD]
                    self._backlight = device_data[ATTR_BACKLIGHT]
                    if ATTR_CYCLE_LENGTH in device_data:
                        self._cycle_length = device_data[ATTR_CYCLE_LENGTH]
                    if ATTR_RSSI in device_data:
                        self._rssi = device_data[ATTR_RSSI]
                    self._operation_mode = device_data[ATTR_SYSTEM_MODE]
                    self._wattage = device_data[ATTR_WATTAGE]
                    self._gfci_status = device_data[ATTR_GFCI_STATUS]
                    self._floor_mode = device_data[ATTR_FLOOR_MODE]
                    self._em_heat = device_data[ATTR_FLOOR_AUX]
                    self._floor_air_limit = device_data[ATTR_FLOOR_AIR_LIMIT]["value"]
                    self._floor_air_limit_status = device_data[ATTR_FLOOR_AIR_LIMIT]["status"]
                    self._floor_sensor_type = device_data[ATTR_FLOOR_SENSOR]
                    if ATTR_FLOOR_MAX in device_data:
                        self._floor_max = device_data[ATTR_FLOOR_MAX]["value"]
                        self._floor_max_status = device_data[ATTR_FLOOR_MAX]["status"]
                    if ATTR_FLOOR_MIN in device_data:
                        self._floor_min = device_data[ATTR_FLOOR_MIN]["value"]
                        self._floor_min_status = device_data[ATTR_FLOOR_MIN]["status"]
                    self._load2_status = device_data[ATTR_FLOOR_OUTPUT2]["status"]
                    if device_data[ATTR_FLOOR_OUTPUT2]["status"] == "on":
                        self._load2 = device_data[ATTR_FLOOR_OUTPUT2]["value"]
                    else:
                        self._load2 = 0
                    self._gfci_alert = device_data[ATTR_GFCI_ALERT]
                elif device_data["errorCode"] == "ReadTimeout":
                    _LOGGER.warning(
                        "A timeout occur during data update. Device %s do not respond. Check your network... (%s)",
                        self._name,
                        device_data,
                    )
                else:
                    _LOGGER.warning("Error in updating device %s: (%s)", self._name, device_data)
            else:
                self.log_error(device_data["error"]["code"])
            self._occupancy_mode = neviweb_status[ATTR_OCCUPANCY]
            self.do_stat(start)
            self.get_sensor_error_code(start)
            self.get_weather()
        else:
            if time.time() - self._snooze > SNOOZE_TIME:
                self._active = True
                if NOTIFY == "notification" or NOTIFY == "both":
                    self.notify_ha("Warning: Neviweb Device update restarted for " + self._name + ", Sku: " + self._sku)

    @property
    @override
    def extra_state_attributes(self) -> Mapping[str, Any]:
        """Return the state attributes."""
        data = {}
        data.update(
            {
                "neviweb_occupancy_mode": self._occupancy_mode,
                "wattage": self._wattage,
                "gfci_status": self._gfci_status,
                "gfci_alert": self._gfci_alert,
                "sensor_mode": self._floor_mode,
                "auxiliary_heat": self._em_heat,
                "auxiliary_status": self._load2_status,
                "auxiliary_load": self._load2,
                "floor_setpoint_max": self._floor_max,
                "floor_setpoint_low": self._floor_min,
                "floor_air_limit": self._floor_air_limit,
                "floor_sensor_type": self._floor_sensor_type,
                "load_watt": self._wattage,
                "error_code": self._error_code,
                "heat_level": self._heat_level,
                "pi_heating_demand": self._heat_level,
                "cycle_length": neviweb_to_ha(self._cycle_length),
                "temp_display_value": self._temp_display_value,
                "second_display": self._display2,
                "keypad": lock_to_ha(self._keypad),
                "backlight": self._backlight,
                "time_format": self._time_format,
                "temperature_format": self._temperature_format,
                "setpoint_max": self._max_temp,
                "setpoint_min": self._min_temp,
                "eco_status": self._drstatus_active,
                "eco_optOut": self._drstatus_optout,
                "eco_setpoint": self._drstatus_setpoint,
                "eco_power_relative": self._drstatus_rel,
                "eco_power_absolute": self._drstatus_abs,
                "eco_setpoint_status": self._drsetpoint_status,
                "eco_setpoint_delta": self._drsetpoint_value,
                "total_kwh_count": self._total_kwh_count,
                "monthly_kwh_count": self._monthly_kwh_count,
                "daily_kwh_count": self._daily_kwh_count,
                "hourly_kwh_count": self._hourly_kwh_count,
                "hourly_kwh": self._hour_kwh,
                "daily_kwh": self._today_kwh,
                "monthly_kwh": self._month_kwh,
                "last_energy_stat_update": self._mark,
                "outdoor_temp": self._temperature,
                "weather_icon": self._weather_icon,
                "rssi": self._rssi,
                "sku": self._sku,
                "device_model": str(self._device_model),
                "device_model_cfg": self._device_model_cfg,
                "firmware": self._firmware,
                "activation": self._active,
                "id": self._id,
            }
        )
        return data


class Neviweb130LowThermostat(Neviweb130Thermostat):
    """Implementation of Neviweb TH1400ZB thermostat."""

    def __init__(self, data, device_info, name, sku, firmware, location):
        """Initialize."""
        super().__init__(data, device_info, name, sku, firmware, location)
        self._floor_air_limit_status = None
        self._floor_max_status = "off"
        self._floor_min_status = "off"
        self._load1 = 0
        self._load2 = 0
        self._pump_protec_period_status = None

    @override
    def update(self) -> None:
        if self._active:
            LOW_VOLTAGE_ATTRIBUTES = [
                ATTR_ROOM_TEMP_DISPLAY,
                ATTR_KEYPAD,
                ATTR_BACKLIGHT,
                ATTR_SYSTEM_MODE,
                ATTR_CYCLE_LENGTH,
                ATTR_DISPLAY2,
                ATTR_RSSI,
                ATTR_PUMP_PROTEC_DURATION,
                ATTR_PUMP_PROTEC_PERIOD,
                ATTR_FLOOR_AIR_LIMIT,
                ATTR_FLOOR_MODE,
                ATTR_FLOOR_SENSOR,
                ATTR_FLOOR_MAX,
                ATTR_FLOOR_MIN,
                ATTR_CYCLE_OUTPUT2,
                ATTR_FLOOR_OUTPUT1,
                ATTR_FLOOR_OUTPUT2,
            ]
            """Get the latest data from Neviweb and update the state."""
            start = time.time()
            _LOGGER.debug(
                "Updated attributes for %s: %s",
                self._name,
                UPDATE_ATTRIBUTES + LOW_VOLTAGE_ATTRIBUTES,
            )
            device_data = self._client.get_device_attributes(self._id, UPDATE_ATTRIBUTES + LOW_VOLTAGE_ATTRIBUTES)
            neviweb_status = self._client.get_neviweb_status(self._location)
            end = time.time()
            elapsed = round(end - start, 3)
            _LOGGER.debug("Updating %s (%s sec): %s", self._name, elapsed, device_data)

            if "error" not in device_data:
                if "errorCode" not in device_data:
                    self._cur_temp_before = self._cur_temp
                    self._cur_temp = (
                        float(device_data[ATTR_ROOM_TEMPERATURE]["value"])
                        if device_data[ATTR_ROOM_TEMPERATURE]["value"] is not None
                        else self._cur_temp_before
                    )
                    self._target_temp = float(device_data[ATTR_ROOM_SETPOINT])
                    self._min_temp = device_data[ATTR_ROOM_SETPOINT_MIN]
                    self._max_temp = device_data[ATTR_ROOM_SETPOINT_MAX]
                    self._temperature_format = device_data[ATTR_TEMP]
                    self._time_format = device_data[ATTR_TIME_FORMAT]
                    self._temp_display_value = device_data[ATTR_ROOM_TEMP_DISPLAY]
                    self._display2 = device_data[ATTR_DISPLAY2]
                    self._heat_level = device_data[ATTR_OUTPUT_PERCENT_DISPLAY]
                    self._keypad = device_data[ATTR_KEYPAD]
                    self._backlight = device_data[ATTR_BACKLIGHT]
                    if ATTR_DRSETPOINT in device_data:
                        self._drsetpoint_status = device_data[ATTR_DRSETPOINT]["status"]
                        self._drsetpoint_value = (
                            device_data[ATTR_DRSETPOINT]["value"]
                            if device_data[ATTR_DRSETPOINT]["value"] is not None
                            else 0
                        )
                    if ATTR_DRSTATUS in device_data:
                        self._drstatus_active = device_data[ATTR_DRSTATUS]["drActive"]
                        self._drstatus_optout = device_data[ATTR_DRSTATUS]["optOut"]
                        self._drstatus_setpoint = device_data[ATTR_DRSTATUS]["setpoint"]
                        self._drstatus_abs = device_data[ATTR_DRSTATUS]["powerAbsolute"]
                        self._drstatus_rel = device_data[ATTR_DRSTATUS]["powerRelative"]
                    if ATTR_CYCLE_LENGTH in device_data:
                        self._cycle_length = device_data[ATTR_CYCLE_LENGTH]
                    if ATTR_RSSI in device_data:
                        self._rssi = device_data[ATTR_RSSI]
                    self._operation_mode = device_data[ATTR_SYSTEM_MODE]
                    self._floor_mode = device_data[ATTR_FLOOR_MODE]
                    self._floor_air_limit = device_data[ATTR_FLOOR_AIR_LIMIT]["value"]
                    self._floor_air_limit_status = device_data[ATTR_FLOOR_AIR_LIMIT]["status"]
                    self._cycle_length_output2_status = device_data[ATTR_CYCLE_OUTPUT2]["status"]
                    self._cycle_length_output2_value = int(device_data[ATTR_CYCLE_OUTPUT2]["value"])
                    self._floor_max = device_data[ATTR_FLOOR_MAX]["value"]
                    self._floor_max_status = device_data[ATTR_FLOOR_MAX]["status"]
                    self._floor_min = device_data[ATTR_FLOOR_MIN]["value"]
                    self._floor_min_status = device_data[ATTR_FLOOR_MIN]["status"]
                    self._pump_protec_status = device_data[ATTR_PUMP_PROTEC_DURATION]["status"]
                    if device_data[ATTR_PUMP_PROTEC_DURATION]["status"] == "on":
                        self._pump_protec_duration = device_data[ATTR_PUMP_PROTEC_DURATION]["value"]
                        self._pump_protec_period = device_data[ATTR_PUMP_PROTEC_PERIOD]["value"]
                        self._pump_protec_period_status = device_data[ATTR_PUMP_PROTEC_PERIOD]["status"]
                    self._floor_sensor_type = device_data[ATTR_FLOOR_SENSOR]
                    if ATTR_FLOOR_OUTPUT1 in device_data:
                        self._load1 = device_data[ATTR_FLOOR_OUTPUT1]
                    if ATTR_FLOOR_OUTPUT2 in device_data:
                        self._load2_status = device_data[ATTR_FLOOR_OUTPUT2]["status"]
                        if device_data[ATTR_FLOOR_OUTPUT2]["status"] == "on":
                            self._load2 = device_data[ATTR_FLOOR_OUTPUT2]["value"]
                elif device_data["errorCode"] == "ReadTimeout":
                    _LOGGER.warning(
                        "A timeout occur during data update. Device %s do not respond. Check your network... (%s)",
                        self._name,
                        device_data,
                    )
                else:
                    _LOGGER.warning("Error updating device %s: (%s)", self._name, device_data)
            else:
                self.log_error(device_data["error"]["code"])
            self._occupancy_mode = neviweb_status[ATTR_OCCUPANCY]
            self.do_stat(start)
            self.get_sensor_error_code(start)
            self.get_weather()
        else:
            if time.time() - self._snooze > SNOOZE_TIME:
                self._active = True
                if NOTIFY == "notification" or NOTIFY == "both":
                    self.notify_ha("Warning: Neviweb Device update restarted for " + self._name + ", Sku: " + self._sku)

    @property
    @override
    def extra_state_attributes(self) -> Mapping[str, Any]:
        """Return the state attributes."""
        data = {}
        data.update(
            {
                "neviweb_occupancy_mode": self._occupancy_mode,
                "sensor_mode": self._floor_mode,
                "cycle_length": neviweb_to_ha(self._cycle_length),
                "auxiliary_cycle_status": self._cycle_length_output2_status,
                "auxiliary_cycle_value": neviweb_to_ha(self._cycle_length_output2_value),
                "floor_limit_high": self._floor_max,
                "floor_limit_high_status": self._floor_max_status,
                "floor_limit_low": self._floor_min,
                "floor_limit_low_status": self._floor_min_status,
                "max_air_limit": self._floor_air_limit,
                "max_air_limit_status": self._floor_air_limit_status,
                "floor_sensor_type": self._floor_sensor_type,
                "pump_protection_status": self._pump_protec_status,
                "pump_protection_duration": self._pump_protec_duration,
                "pump_protection_frequency": self._pump_protec_period,
                "pump_protection_frequency_status": self._pump_protec_period_status,
                "error_code": self._error_code,
                "heat_level": self._heat_level,
                "pi_heating_demand": self._heat_level,
                "temp_display_value": self._temp_display_value,
                "second_display": self._display2,
                "keypad": lock_to_ha(self._keypad),
                "backlight": self._backlight,
                "time_format": self._time_format,
                "temperature_format": self._temperature_format,
                "setpoint_max": self._max_temp,
                "setpoint_min": self._min_temp,
                "cycle_length_output": self._load1,
                "cycle_length_output_2": self._load2,
                "cycle_length_output_2_status": self._load2_status,
                "eco_status": self._drstatus_active,
                "eco_optOut": self._drstatus_optout,
                "eco_setpoint": self._drstatus_setpoint,
                "eco_power_relative": self._drstatus_rel,
                "eco_power_absolute": self._drstatus_abs,
                "eco_setpoint_status": self._drsetpoint_status,
                "eco_setpoint_delta": self._drsetpoint_value,
                "total_kwh_count": self._total_kwh_count,
                "monthly_kwh_count": self._monthly_kwh_count,
                "daily_kwh_count": self._daily_kwh_count,
                "hourly_kwh_count": self._hourly_kwh_count,
                "hourly_kwh": self._hour_kwh,
                "daily_kwh": self._today_kwh,
                "monthly_kwh": self._month_kwh,
                "last_energy_stat_update": self._mark,
                "outdoor_temp": self._temperature,
                "weather_icon": self._weather_icon,
                "rssi": self._rssi,
                "sku": self._sku,
                "device_model": str(self._device_model),
                "device_model_cfg": self._device_model_cfg,
                "firmware": self._firmware,
                "activation": self._active,
                "id": self._id,
            }
        )
        return data


class Neviweb130DoubleThermostat(Neviweb130Thermostat):
    """Implementation of Neviweb TH1500ZB thermostat."""

    @override
    def update(self) -> None:
        if self._active:
            DOUBLE_ATTRIBUTES = [
                ATTR_ROOM_TEMP_DISPLAY,
                ATTR_KEYPAD,
                ATTR_BACKLIGHT,
                ATTR_SYSTEM_MODE,
                ATTR_CYCLE_LENGTH,
                ATTR_DISPLAY2,
                ATTR_RSSI,
                ATTR_WATTAGE,
            ]
            """Get the latest data from Neviweb and update the state."""
            start = time.time()
            _LOGGER.debug(
                "Updated attributes for %s: %s",
                self._name,
                UPDATE_ATTRIBUTES + DOUBLE_ATTRIBUTES,
            )
            device_data = self._client.get_device_attributes(self._id, UPDATE_ATTRIBUTES + DOUBLE_ATTRIBUTES)
            neviweb_status = self._client.get_neviweb_status(self._location)
            end = time.time()
            elapsed = round(end - start, 3)
            _LOGGER.debug("Updating %s (%s sec): %s", self._name, elapsed, device_data)

            if "error" not in device_data:
                if "errorCode" not in device_data:
                    self._cur_temp_before = self._cur_temp
                    self._cur_temp = (
                        float(device_data[ATTR_ROOM_TEMPERATURE]["value"])
                        if device_data[ATTR_ROOM_TEMPERATURE]["value"] is not None
                        else self._cur_temp_before
                    )
                    self._target_temp = float(device_data[ATTR_ROOM_SETPOINT])
                    self._min_temp = device_data[ATTR_ROOM_SETPOINT_MIN]
                    self._max_temp = device_data[ATTR_ROOM_SETPOINT_MAX]
                    self._temperature_format = device_data[ATTR_TEMP]
                    self._time_format = device_data[ATTR_TIME_FORMAT]
                    self._temp_display_value = device_data[ATTR_ROOM_TEMP_DISPLAY]
                    self._display2 = device_data[ATTR_DISPLAY2]
                    if ATTR_DRSETPOINT in device_data:
                        self._drsetpoint_status = device_data[ATTR_DRSETPOINT]["status"]
                        self._drsetpoint_value = (
                            device_data[ATTR_DRSETPOINT]["value"]
                            if device_data[ATTR_DRSETPOINT]["value"] is not None
                            else 0
                        )
                    if ATTR_DRSTATUS in device_data:
                        self._drstatus_active = device_data[ATTR_DRSTATUS]["drActive"]
                        self._drstatus_optout = device_data[ATTR_DRSTATUS]["optOut"]
                        self._drstatus_setpoint = device_data[ATTR_DRSTATUS]["setpoint"]
                        self._drstatus_abs = device_data[ATTR_DRSTATUS]["powerAbsolute"]
                        self._drstatus_rel = device_data[ATTR_DRSTATUS]["powerRelative"]
                    self._heat_level = device_data[ATTR_OUTPUT_PERCENT_DISPLAY]
                    self._keypad = device_data[ATTR_KEYPAD]
                    self._backlight = device_data[ATTR_BACKLIGHT]
                    if ATTR_CYCLE_LENGTH in device_data:
                        self._cycle_length = device_data[ATTR_CYCLE_LENGTH]
                    if ATTR_RSSI in device_data:
                        self._rssi = device_data[ATTR_RSSI]
                    self._operation_mode = device_data[ATTR_SYSTEM_MODE]
                    self._wattage = device_data[ATTR_WATTAGE]
                elif device_data["errorCode"] == "ReadTimeout":
                    _LOGGER.warning(
                        "A timeout occur during data update. Device %s do not respond. Check your network... (%s)",
                        self._name,
                        device_data,
                    )
                else:
                    _LOGGER.warning("Error in updating device %s: (%s)", self._name, device_data)
            else:
                self.log_error(device_data["error"]["code"])
            self._occupancy_mode = neviweb_status[ATTR_OCCUPANCY]
            self.do_stat(start)
            self.get_sensor_error_code(start)
            self.get_weather()
        else:
            if time.time() - self._snooze > SNOOZE_TIME:
                self._active = True
                if NOTIFY == "notification" or NOTIFY == "both":
                    self.notify_ha("Warning: Neviweb Device update restarted for " + self._name + ", Sku: " + self._sku)

    @property
    @override
    def extra_state_attributes(self) -> Mapping[str, Any]:
        """Return the state attributes."""
        data = {}
        data.update(
            {
                "neviweb_occupancy_mode": self._occupancy_mode,
                "wattage": self._wattage,
                "cycle_length": neviweb_to_ha(self._cycle_length),
                "error_code": self._error_code,
                "heat_level": self._heat_level,
                "pi_heating_demand": self._heat_level,
                "temp_display_value": self._temp_display_value,
                "second_display": self._display2,
                "keypad": lock_to_ha(self._keypad),
                "backlight": self._backlight,
                "time_format": self._time_format,
                "temperature_format": self._temperature_format,
                "setpoint_max": self._max_temp,
                "setpoint_min": self._min_temp,
                "eco_status": self._drstatus_active,
                "eco_optOut": self._drstatus_optout,
                "eco_setpoint": self._drstatus_setpoint,
                "eco_power_relative": self._drstatus_rel,
                "eco_power_absolute": self._drstatus_abs,
                "eco_setpoint_status": self._drsetpoint_status,
                "eco_setpoint_delta": self._drsetpoint_value,
                "total_kwh_count": self._total_kwh_count,
                "monthly_kwh_count": self._monthly_kwh_count,
                "daily_kwh_count": self._daily_kwh_count,
                "hourly_kwh_count": self._hourly_kwh_count,
                "hourly_kwh": self._hour_kwh,
                "daily_kwh": self._today_kwh,
                "monthly_kwh": self._month_kwh,
                "last_energy_stat_update": self._mark,
                "outdoor_temp": self._temperature,
                "weather_icon": self._weather_icon,
                "rssi": self._rssi,
                "sku": self._sku,
                "device_model": str(self._device_model),
                "device_model_cfg": self._device_model_cfg,
                "firmware": self._firmware,
                "activation": self._active,
                "id": self._id,
            }
        )
        return data


class Neviweb130WifiThermostat(Neviweb130Thermostat):
    """Implementation of Neviweb TH1123WF, TH1124WF, TH1500WF thermostats."""

    def __init__(self, data, device_info, name, sku, firmware, location):
        """Initialize."""
        super().__init__(data, device_info, name, sku, firmware, location)
        self._early_start = "off"
        self._heat_source_type = None
        self._load1 = 0
        self._room_temp_error = None
        self._room_temp_error = None
        self._target_temp_away = None
        self._temp_display_status = None

    @override
    def update(self) -> None:
        if self._active:
            WIFI_ATTRIBUTES = [
                ATTR_ROOM_TEMP_DISPLAY,
                ATTR_CYCLE_LENGTH,
                ATTR_FLOOR_OUTPUT1,
                ATTR_WIFI_WATTAGE,
                ATTR_WIFI,
                ATTR_WIFI_KEYPAD,
                ATTR_DISPLAY2,
                ATTR_SETPOINT_MODE,
                ATTR_OCCUPANCY,
                ATTR_BACKLIGHT_AUTO_DIM,
                ATTR_EARLY_START,
                ATTR_ROOM_SETPOINT_AWAY,
            ]
            """Get the latest data from Neviweb and update the state."""
            start = time.time()
            _LOGGER.debug(
                "Updated attributes for %s: %s",
                self._name,
                UPDATE_ATTRIBUTES + WIFI_ATTRIBUTES,
            )
            device_data = self._client.get_device_attributes(self._id, UPDATE_ATTRIBUTES + WIFI_ATTRIBUTES)
            neviweb_status = self._client.get_neviweb_status(self._location)
            end = time.time()
            elapsed = round(end - start, 3)
            _LOGGER.debug("Updating %s (%s sec): %s", self._name, elapsed, device_data)

            if "error" not in device_data:
                if "errorCode" not in device_data:
                    self._cur_temp_before = self._cur_temp
                    self._cur_temp = (
                        float(device_data[ATTR_ROOM_TEMPERATURE]["value"])
                        if device_data[ATTR_ROOM_TEMPERATURE]["value"] is not None
                        else self._cur_temp_before
                    )
                    self._room_temp_error = device_data[ATTR_ROOM_TEMPERATURE]["error"]
                    self._target_temp = float(device_data[ATTR_ROOM_SETPOINT])
                    self._min_temp = device_data[ATTR_ROOM_SETPOINT_MIN]
                    self._max_temp = device_data[ATTR_ROOM_SETPOINT_MAX]
                    self._temperature_format = device_data[ATTR_TEMP]
                    self._time_format = device_data[ATTR_TIME_FORMAT]
                    self._display2 = device_data[ATTR_DISPLAY2]
                    if ATTR_DRSETPOINT in device_data:
                        self._drsetpoint_status = device_data[ATTR_DRSETPOINT]["status"]
                        self._drsetpoint_value = (
                            device_data[ATTR_DRSETPOINT]["value"]
                            if device_data[ATTR_DRSETPOINT]["value"] is not None
                            else 0
                        )
                    if ATTR_DRSTATUS in device_data:
                        self._drstatus_active = device_data[ATTR_DRSTATUS]["drActive"]
                        self._drstatus_optout = device_data[ATTR_DRSTATUS]["optOut"]
                        self._drstatus_setpoint = device_data[ATTR_DRSTATUS]["setpoint"]
                        self._drstatus_abs = device_data[ATTR_DRSTATUS]["powerAbsolute"]
                        self._drstatus_rel = device_data[ATTR_DRSTATUS]["powerRelative"]
                        self._drstatus_onoff = device_data[ATTR_DRSTATUS]["onOff"]
                    self._heat_level = device_data[ATTR_OUTPUT_PERCENT_DISPLAY]["percent"]
                    self._heat_source_type = device_data[ATTR_OUTPUT_PERCENT_DISPLAY]["sourceType"]
                    self._operation_mode = device_data[ATTR_SETPOINT_MODE]
                    self._occupancy = device_data[ATTR_OCCUPANCY]
                    self._keypad = device_data[ATTR_WIFI_KEYPAD]
                    self._rssi = device_data[ATTR_WIFI]
                    self._backlight = device_data[ATTR_BACKLIGHT_AUTO_DIM]
                    self._early_start = device_data[ATTR_EARLY_START]
                    self._target_temp_away = device_data[ATTR_ROOM_SETPOINT_AWAY]
                    self._load1 = device_data[ATTR_FLOOR_OUTPUT1]
                    if ATTR_WIFI_WATTAGE in device_data:
                        self._wattage = device_data[ATTR_WIFI_WATTAGE]
                    if ATTR_CYCLE_LENGTH in device_data:
                        self._cycle_length = device_data[ATTR_CYCLE_LENGTH]
                    if ATTR_ROOM_TEMP_DISPLAY in device_data:
                        self._temp_display_status = device_data[ATTR_ROOM_TEMP_DISPLAY]["status"]
                        self._temp_display_value = device_data[ATTR_ROOM_TEMP_DISPLAY]["value"]
                elif device_data["errorCode"] == "ReadTimeout":
                    _LOGGER.warning(
                        "A timeout occur during data update. Device %s do not respond. Check your network... (%s)",
                        self._name,
                        device_data,
                    )
                else:
                    _LOGGER.warning("Error in updating device %s: (%s)", self._name, device_data)
            else:
                self.log_error(device_data["error"]["code"])
            self._occupancy_mode = neviweb_status[ATTR_OCCUPANCY]
            self.do_stat(start)
            self.get_sensor_error_code(start)
            self.get_weather()
        else:
            if time.time() - self._snooze > SNOOZE_TIME:
                self._active = True
                if NOTIFY == "notification" or NOTIFY == "both":
                    self.notify_ha("Warning: Neviweb Device update restarted for " + self._name + ", Sku: " + self._sku)

    @property
    @override
    def extra_state_attributes(self) -> Mapping[str, Any]:
        """Return the state attributes."""
        data = {}
        data.update(
            {
                "neviweb_occupancy_mode": self._occupancy_mode,
                "wattage": self._wattage,
                "occupancy": self._occupancy,
                "temp_display_status": self._temp_display_status,
                "temp_display_error": self._room_temp_error,
                "source_type": self._heat_source_type,
                "early_start": self._early_start,
                "setpoint_away": self._target_temp_away,
                "load_watt_1": self._load1,
                "cycle_length": neviweb_to_ha(self._cycle_length),
                "error_code": self._error_code,
                "heat_level": self._heat_level,
                "pi_heating_demand": self._heat_level,
                "temp_display_value": self._temp_display_value,
                "second_display": self._display2,
                "keypad": lock_to_ha(self._keypad),
                "backlight": self._backlight,
                "time_format": self._time_format,
                "temperature_format": self._temperature_format,
                "setpoint_max": self._max_temp,
                "setpoint_min": self._min_temp,
                "eco_status": self._drstatus_active,
                "eco_optOut": self._drstatus_optout,
                "eco_setpoint": self._drstatus_setpoint,
                "eco_power_relative": self._drstatus_rel,
                "eco_power_absolute": self._drstatus_abs,
                "eco_onOff": self._drstatus_onoff,
                "eco_setpoint_status": self._drsetpoint_status,
                "eco_setpoint_delta": self._drsetpoint_value,
                "total_kwh_count": self._total_kwh_count,
                "monthly_kwh_count": self._monthly_kwh_count,
                "daily_kwh_count": self._daily_kwh_count,
                "hourly_kwh_count": self._hourly_kwh_count,
                "hourly_kwh": self._hour_kwh,
                "daily_kwh": self._today_kwh,
                "monthly_kwh": self._month_kwh,
                "last_energy_stat_update": self._mark,
                "outdoor_temp": self._temperature,
                "weather_icon": self._weather_icon,
                "rssi": self._rssi,
                "sku": self._sku,
                "device_model": str(self._device_model),
                "device_model_cfg": self._device_model_cfg,
                "firmware": self._firmware,
                "activation": self._active,
                "id": self._id,
            }
        )
        return data


class Neviweb130WifiLiteThermostat(Neviweb130Thermostat):
    """Implementation of Neviweb TH1133WF, TH1133CR, TH1134WF and TH1134CR thermostats."""

    _attr_precision = 1.0
    _attr_target_temperature_step = 1.0

    def __init__(self, data, device_info, name, sku, firmware, location):
        """Initialize."""
        super().__init__(data, device_info, name, sku, firmware, location)
        self._early_start = "off"
        self._heat_source_type = None
        self._load1 = 0
        self._room_temp_error = None
        self._target_temp_away = None
        self._temp_display_status = None
        self._interlock_id = None
        self._interlock_partner = None

    @override
    def update(self) -> None:
        if self._active:
            LITE_ATTRIBUTES = [
                ATTR_ROOM_TEMP_DISPLAY,
                ATTR_CYCLE_LENGTH,
                ATTR_OUTPUT1,
                ATTR_WIFI,
                ATTR_WIFI_KEYPAD,
                ATTR_SETPOINT_MODE,
                ATTR_OCCUPANCY,
                ATTR_BACKLIGHT_AUTO_DIM,
                ATTR_EARLY_START,
                ATTR_ROOM_SETPOINT_AWAY,
                ATTR_INTERLOCK_PARTNER,
                ATTR_INTERLOCK_ID,
            ]
            """Get the latest data from Neviweb and update the state."""
            start = time.time()
            _LOGGER.debug(
                "Updated attributes for %s: %s",
                self._name,
                UPDATE_LITE_ATTRIBUTES + LITE_ATTRIBUTES,
            )
            device_data = self._client.get_device_attributes(self._id, UPDATE_LITE_ATTRIBUTES + LITE_ATTRIBUTES)
            neviweb_status = self._client.get_neviweb_status(self._location)
            end = time.time()
            elapsed = round(end - start, 3)
            _LOGGER.debug("Updating %s (%s sec): %s", self._name, elapsed, device_data)

            if "error" not in device_data:
                if "errorCode" not in device_data:
                    self._cur_temp_before = self._cur_temp
                    self._cur_temp = (
                        float(device_data[ATTR_ROOM_TEMPERATURE]["value"])
                        if device_data[ATTR_ROOM_TEMPERATURE]["value"] is not None
                        else self._cur_temp_before
                    )
                    self._room_temp_error = device_data[ATTR_ROOM_TEMPERATURE]["error"]
                    self._target_temp = float(device_data[ATTR_ROOM_SETPOINT])
                    self._min_temp = device_data[ATTR_ROOM_SETPOINT_MIN]
                    self._max_temp = device_data[ATTR_ROOM_SETPOINT_MAX]
                    self._temperature_format = device_data[ATTR_TEMP]
                    if ATTR_DRSETPOINT in device_data:
                        self._drsetpoint_status = device_data[ATTR_DRSETPOINT]["status"]
                        self._drsetpoint_value = (
                            device_data[ATTR_DRSETPOINT]["value"]
                            if device_data[ATTR_DRSETPOINT]["value"] is not None
                            else 0
                        )
                    if ATTR_DRSTATUS in device_data:
                        self._drstatus_active = device_data[ATTR_DRSTATUS]["drActive"]
                        self._drstatus_optout = device_data[ATTR_DRSTATUS]["optOut"]
                        self._drstatus_setpoint = device_data[ATTR_DRSTATUS]["setpoint"]
                        self._drstatus_abs = device_data[ATTR_DRSTATUS]["powerAbsolute"]
                        self._drstatus_rel = device_data[ATTR_DRSTATUS]["powerRelative"]
                        self._drstatus_onoff = device_data[ATTR_DRSTATUS]["onOff"]
                    self._heat_level = device_data.get(ATTR_OUTPUT_PERCENT_DISPLAY, {}).get("percent")
                    source_info = device_data.get(ATTR_OUTPUT_PERCENT_DISPLAY, {})
                    if isinstance(source_info, dict) and "sourceType" in source_info:
                        self._heat_source_type = source_info["sourceType"]
                    self._operation_mode = device_data[ATTR_SETPOINT_MODE]
                    self._occupancy = device_data[ATTR_OCCUPANCY]
                    self._keypad = device_data[ATTR_WIFI_KEYPAD]
                    self._rssi = device_data[ATTR_WIFI]
                    self._backlight = device_data[ATTR_BACKLIGHT_AUTO_DIM]
                    self._early_start = device_data[ATTR_EARLY_START]
                    self._target_temp_away = device_data[ATTR_ROOM_SETPOINT_AWAY]
                    self._load1 = device_data[ATTR_OUTPUT1]
                    if ATTR_CYCLE_LENGTH in device_data:
                        self._cycle_length = device_data[ATTR_CYCLE_LENGTH]
                    if ATTR_ROOM_TEMP_DISPLAY in device_data:
                        self._temp_display_status = device_data[ATTR_ROOM_TEMP_DISPLAY]["status"]
                        self._temp_display_value = device_data[ATTR_ROOM_TEMP_DISPLAY]["value"]
                    if ATTR_INTERLOCK_ID in device_data:
                        self._interlock_id = device_data[ATTR_INTERLOCK_ID]
                        self._interlock_partner = device_data[ATTR_INTERLOCK_PARTNER]

                elif device_data["errorCode"] == "ReadTimeout":
                    _LOGGER.warning(
                        "A timeout occur during data update. Device %s do not respond. Check your network... (%s)",
                        self._name,
                        device_data,
                    )
                else:
                    _LOGGER.warning("Error in updating device %s: (%s)", self._name, device_data)
            else:
                self.log_error(device_data["error"]["code"])
            self._occupancy_mode = neviweb_status[ATTR_OCCUPANCY]
            if (
                self._sku != "TH1133WF"
                and self._sku != "TH1133CR"
                and self._sku != "TH1134WF"
                and self._sku != "TH1134CR"
            ):
                self.do_stat(start)
            self.get_sensor_error_code(start)
            self.get_weather()
        else:
            if time.time() - self._snooze > SNOOZE_TIME:
                self._active = True
                if NOTIFY == "notification" or NOTIFY == "both":
                    self.notify_ha("Warning: Neviweb Device update restarted for " + self._name + ", Sku: " + self._sku)

    @property
    @override
    def extra_state_attributes(self) -> Mapping[str, Any]:
        """Return the state attributes."""
        data = {}
        data.update(
            {
                "neviweb_occupancy_mode": self._occupancy_mode,
                "occupancy": self._occupancy,
                "temp_display_status": self._temp_display_status,
                "temp_display_error": self._room_temp_error,
                "source_type": self._heat_source_type,
                "early_start": self._early_start,
                "setpoint_away": self._target_temp_away,
                "load_watt_1": self._load1,
                "cycle_length": neviweb_to_ha(self._cycle_length),
                "error_code": self._error_code,
                "heat_level": self._heat_level,
                "pi_heating_demand": self._heat_level,
                "temp_display_value": self._temp_display_value,
                "keypad": lock_to_ha(self._keypad),
                "backlight": self._backlight,
                "temperature_format": self._temperature_format,
                "setpoint_max": self._max_temp,
                "setpoint_min": self._min_temp,
                "eco_status": self._drstatus_active,
                "eco_optOut": self._drstatus_optout,
                "eco_setpoint": self._drstatus_setpoint,
                "eco_power_relative": self._drstatus_rel,
                "eco_power_absolute": self._drstatus_abs,
                "eco_onOff": self._drstatus_onoff,
                "eco_setpoint_status": self._drsetpoint_status,
                "eco_setpoint_delta": self._drsetpoint_value,
                "total_kwh_count": self._total_kwh_count,
                "monthly_kwh_count": self._monthly_kwh_count,
                "daily_kwh_count": self._daily_kwh_count,
                "hourly_kwh_count": self._hourly_kwh_count,
                "hourly_kwh": self._hour_kwh,
                "daily_kwh": self._today_kwh,
                "monthly_kwh": self._month_kwh,
                "last_energy_stat_update": self._mark,
                "outdoor_temp": self._temperature,
                "weather_icon": self._weather_icon,
                "interlock_id": self._interlock_id,
                "interlock_partner": self._interlock_partner,
                "rssi": self._rssi,
                "sku": self._sku,
                "device_model": str(self._device_model),
                "device_model_cfg": self._device_model_cfg,
                "firmware": self._firmware,
                "activation": self._active,
                "id": self._id,
            }
        )
        return data


class Neviweb130ColorWifiThermostat(Neviweb130Thermostat):
    """Implementation of Neviweb TH1143WF, TH1144WF thermostats."""

    _attr_precision = 0.5
    _attr_target_temperature_step = 0.5

    def __init__(self, data, device_info, name, sku, firmware, location):
        """Initialize."""
        super().__init__(data, device_info, name, sku, firmware, location)
        self._early_start = "off"
        self._heat_source_type = None
        self._load1 = 0
        self._room_temp_error = None
        self._target_temp_away = None
        self._temp_display_status = None

    @override
    def update(self) -> None:
        if self._active:
            LITE_ATTRIBUTES = [
                ATTR_ROOM_TEMP_DISPLAY,
                ATTR_OUTPUT1,
                ATTR_WIFI,
                ATTR_WIFI_KEYPAD,
                ATTR_SETPOINT_MODE,
                ATTR_OCCUPANCY,
                ATTR_BACKLIGHT_AUTO_DIM,
                ATTR_EARLY_START,
                ATTR_ROOM_SETPOINT_AWAY,
                ATTR_LANGUAGE,
            ]
            """Get the latest data from Neviweb and update the state."""
            start = time.time()
            _LOGGER.debug(
                "Updated attributes for %s: %s",
                self._name,
                UPDATE_ATTRIBUTES + LITE_ATTRIBUTES,
            )
            device_data = self._client.get_device_attributes(self._id, UPDATE_ATTRIBUTES + LITE_ATTRIBUTES)
            neviweb_status = self._client.get_neviweb_status(self._location)
            end = time.time()
            elapsed = round(end - start, 3)
            _LOGGER.debug("Updating %s (%s sec): %s", self._name, elapsed, device_data)

            if "error" not in device_data:
                if "errorCode" not in device_data:
                    self._cur_temp_before = self._cur_temp
                    self._cur_temp = (
                        float(device_data[ATTR_ROOM_TEMPERATURE]["value"])
                        if device_data[ATTR_ROOM_TEMPERATURE]["value"] is not None
                        else self._cur_temp_before
                    )
                    self._room_temp_error = device_data[ATTR_ROOM_TEMPERATURE]["error"]
                    self._target_temp = float(device_data[ATTR_ROOM_SETPOINT])
                    self._min_temp = device_data[ATTR_ROOM_SETPOINT_MIN]
                    self._max_temp = device_data[ATTR_ROOM_SETPOINT_MAX]
                    self._temperature_format = device_data[ATTR_TEMP]
                    self._time_format = device_data[ATTR_TIME_FORMAT]
                    if ATTR_DRSETPOINT in device_data:
                        self._drsetpoint_status = device_data[ATTR_DRSETPOINT]["status"]
                        self._drsetpoint_value = (
                            device_data[ATTR_DRSETPOINT]["value"]
                            if device_data[ATTR_DRSETPOINT]["value"] is not None
                            else 0
                        )
                    if ATTR_DRSTATUS in device_data:
                        self._drstatus_active = device_data[ATTR_DRSTATUS]["drActive"]
                        self._drstatus_optout = device_data[ATTR_DRSTATUS]["optOut"]
                        self._drstatus_setpoint = device_data[ATTR_DRSTATUS]["setpoint"]
                        self._drstatus_abs = device_data[ATTR_DRSTATUS]["powerAbsolute"]
                        self._drstatus_rel = device_data[ATTR_DRSTATUS]["powerRelative"]
                        self._drstatus_onoff = device_data[ATTR_DRSTATUS]["onOff"]
                    self._heat_level = device_data.get(ATTR_OUTPUT_PERCENT_DISPLAY, {}).get("percent")
                    source_info = device_data.get(ATTR_OUTPUT_PERCENT_DISPLAY, {})
                    if isinstance(source_info, dict) and "sourceType" in source_info:
                        self._heat_source_type = source_info["sourceType"]
                    self._operation_mode = device_data[ATTR_SETPOINT_MODE]
                    self._occupancy = device_data[ATTR_OCCUPANCY]
                    self._keypad = device_data[ATTR_WIFI_KEYPAD]
                    self._rssi = device_data[ATTR_WIFI]
                    self._backlight = device_data[ATTR_BACKLIGHT_AUTO_DIM]
                    self._early_start = device_data[ATTR_EARLY_START]
                    self._target_temp_away = device_data[ATTR_ROOM_SETPOINT_AWAY]
                    self._load1 = device_data[ATTR_OUTPUT1]
                    self._language = device_data[ATTR_LANGUAGE]
                    if ATTR_ROOM_TEMP_DISPLAY in device_data:
                        self._temp_display_status = device_data[ATTR_ROOM_TEMP_DISPLAY]["status"]
                        self._temp_display_value = device_data[ATTR_ROOM_TEMP_DISPLAY]["value"]

                elif device_data["errorCode"] == "ReadTimeout":
                    _LOGGER.warning(
                        "A timeout occur during data update. Device %s do not respond. Check your network... (%s)",
                        self._name,
                        device_data,
                    )
                else:
                    _LOGGER.warning("Error in updating device %s: (%s)", self._name, device_data)
            else:
                self.log_error(device_data["error"]["code"])
            self._occupancy_mode = neviweb_status[ATTR_OCCUPANCY]
            self.do_stat(start)
            self.get_sensor_error_code(start)
            self.get_weather()
        else:
            if time.time() - self._snooze > SNOOZE_TIME:
                self._active = True
                if NOTIFY == "notification" or NOTIFY == "both":
                    self.notify_ha("Warning: Neviweb Device update restarted for " + self._name + ", Sku: " + self._sku)

    @property
    @override
    def extra_state_attributes(self) -> Mapping[str, Any]:
        """Return the state attributes."""
        data = {}
        data.update(
            {
                "neviweb_occupancy_mode": self._occupancy_mode,
                "occupancy": self._occupancy,
                "temp_display_status": self._temp_display_status,
                "temp_display_error": self._room_temp_error,
                "source_type": self._heat_source_type,
                "early_start": self._early_start,
                "setpoint_away": self._target_temp_away,
                "load_watt_1": self._load1,
                "error_code": self._error_code,
                "heat_level": self._heat_level,
                "pi_heating_demand": self._heat_level,
                "temp_display_value": self._temp_display_value,
                "keypad": lock_to_ha(self._keypad),
                "backlight": self._backlight,
                "temperature_format": self._temperature_format,
                "time_format": self._time_format,
                "language": self._language,
                "setpoint_max": self._max_temp,
                "setpoint_min": self._min_temp,
                "eco_status": self._drstatus_active,
                "eco_optOut": self._drstatus_optout,
                "eco_setpoint": self._drstatus_setpoint,
                "eco_power_relative": self._drstatus_rel,
                "eco_power_absolute": self._drstatus_abs,
                "eco_onOff": self._drstatus_onoff,
                "eco_setpoint_status": self._drsetpoint_status,
                "eco_setpoint_delta": self._drsetpoint_value,
                "total_kwh_count": self._total_kwh_count,
                "monthly_kwh_count": self._monthly_kwh_count,
                "daily_kwh_count": self._daily_kwh_count,
                "hourly_kwh_count": self._hourly_kwh_count,
                "hourly_kwh": self._hour_kwh,
                "daily_kwh": self._today_kwh,
                "monthly_kwh": self._month_kwh,
                "last_energy_stat_update": self._mark,
                "outdoor_temp": self._temperature,
                "weather_icon": self._weather_icon,
                "rssi": self._rssi,
                "sku": self._sku,
                "device_model": str(self._device_model),
                "device_model_cfg": self._device_model_cfg,
                "firmware": self._firmware,
                "activation": self._active,
                "id": self._id,
            }
        )
        return data


class Neviweb130LowWifiThermostat(Neviweb130Thermostat):
    """Implementation of Neviweb TH1400WF thermostat."""

    def __init__(self, data, device_info, name, sku, firmware, location):
        """Initialize."""
        super().__init__(data, device_info, name, sku, firmware, location)
        self._early_start = "off"
        self._floor_air_limit_status = None
        self._floor_max_status = "off"
        self._floor_min_status = "off"
        self._heat_source_type = None
        self._load1 = 0
        self._load2 = 0
        self._pump_duration_value = None
        self._target_temp_away = None
        self._temp_display_status = None

    @override
    def update(self) -> None:
        if self._active:
            LOW_WIFI_ATTRIBUTES = [
                ATTR_ROOM_TEMP_DISPLAY,
                ATTR_FLOOR_OUTPUT2,
                ATTR_FLOOR_AUX,
                ATTR_ROOM_SETPOINT_AWAY,
                ATTR_EARLY_START,
                ATTR_BACKLIGHT_AUTO_DIM,
                ATTR_OCCUPANCY,
                ATTR_SETPOINT_MODE,
                ATTR_DISPLAY2,
                ATTR_WIFI_KEYPAD,
                ATTR_WIFI,
                ATTR_WIFI_WATTAGE,
                ATTR_FLOOR_OUTPUT1,
                ATTR_PUMP_PROTEC,
                ATTR_PUMP_PROTEC_DURATION,
                ATTR_FLOOR_AIR_LIMIT,
                ATTR_FLOOR_MODE,
                ATTR_FLOOR_SENSOR,
                ATTR_AUX_CYCLE_LENGTH,
                ATTR_CYCLE_LENGTH,
                ATTR_FLOOR_MAX,
                ATTR_FLOOR_MIN,
            ]
            """Get the latest data from Neviweb and update the state."""
            start = time.time()
            _LOGGER.debug(
                "Updated attributes for %s: %s",
                self._name,
                UPDATE_ATTRIBUTES + LOW_WIFI_ATTRIBUTES,
            )
            device_data = self._client.get_device_attributes(self._id, UPDATE_ATTRIBUTES + LOW_WIFI_ATTRIBUTES)
            neviweb_status = self._client.get_neviweb_status(self._location)
            end = time.time()
            elapsed = round(end - start, 3)
            _LOGGER.debug("Updating %s (%s sec): %s", self._name, elapsed, device_data)

            if "error" not in device_data:
                if "errorCode" not in device_data:
                    self._cur_temp_before = self._cur_temp
                    self._cur_temp = (
                        float(device_data[ATTR_ROOM_TEMPERATURE]["value"])
                        if device_data[ATTR_ROOM_TEMPERATURE]["value"] is not None
                        else self._cur_temp_before
                    )
                    self._target_temp = float(device_data[ATTR_ROOM_SETPOINT])
                    self._min_temp = device_data[ATTR_ROOM_SETPOINT_MIN]
                    self._max_temp = device_data[ATTR_ROOM_SETPOINT_MAX]
                    self._temperature_format = device_data[ATTR_TEMP]
                    self._time_format = device_data[ATTR_TIME_FORMAT]
                    self._temp_display_value = device_data[ATTR_ROOM_TEMP_DISPLAY]["value"]
                    self._temp_display_status = device_data[ATTR_ROOM_TEMP_DISPLAY]["status"]
                    self._display2 = device_data[ATTR_DISPLAY2]
                    if ATTR_DRSETPOINT in device_data:
                        self._drsetpoint_status = device_data[ATTR_DRSETPOINT]["status"]
                        self._drsetpoint_value = (
                            device_data[ATTR_DRSETPOINT]["value"]
                            if device_data[ATTR_DRSETPOINT]["value"] is not None
                            else 0
                        )
                    if ATTR_DRSTATUS in device_data:
                        self._drstatus_active = device_data[ATTR_DRSTATUS]["drActive"]
                        self._drstatus_optout = device_data[ATTR_DRSTATUS]["optOut"]
                        self._drstatus_setpoint = device_data[ATTR_DRSTATUS]["setpoint"]
                        self._drstatus_abs = device_data[ATTR_DRSTATUS]["powerAbsolute"]
                        self._drstatus_rel = device_data[ATTR_DRSTATUS]["powerRelative"]
                    self._heat_level = device_data[ATTR_OUTPUT_PERCENT_DISPLAY]["percent"]
                    self._heat_source_type = device_data[ATTR_OUTPUT_PERCENT_DISPLAY]["sourceType"]
                    self._operation_mode = device_data[ATTR_SETPOINT_MODE]
                    self._occupancy = device_data[ATTR_OCCUPANCY]
                    self._keypad = device_data[ATTR_WIFI_KEYPAD]
                    self._rssi = device_data[ATTR_WIFI]
                    self._wattage = device_data[ATTR_WIFI_WATTAGE]
                    self._backlight = device_data[ATTR_BACKLIGHT_AUTO_DIM]
                    self._early_start = device_data[ATTR_EARLY_START]
                    self._target_temp_away = device_data[ATTR_ROOM_SETPOINT_AWAY]
                    self._load1 = device_data[ATTR_FLOOR_OUTPUT1]
                    self._floor_mode = device_data[ATTR_FLOOR_MODE]
                    self._floor_sensor_type = device_data[ATTR_FLOOR_SENSOR]
                    self._aux_cycle_length = device_data[ATTR_AUX_CYCLE_LENGTH]
                    self._cycle_length = device_data[ATTR_CYCLE_LENGTH]
                    self._floor_max = device_data[ATTR_FLOOR_MAX]["value"]
                    self._floor_max_status = device_data[ATTR_FLOOR_MAX]["status"]
                    self._floor_min = device_data[ATTR_FLOOR_MIN]["value"]
                    self._floor_min_status = device_data[ATTR_FLOOR_MIN]["status"]
                    self._floor_air_limit = device_data[ATTR_FLOOR_AIR_LIMIT]["value"]
                    status = device_data[ATTR_FLOOR_AIR_LIMIT]["status"]
                    self._floor_air_limit_status = status
                    self._pump_protec_status = device_data[ATTR_PUMP_PROTEC]["status"]
                    if device_data[ATTR_PUMP_PROTEC]["status"] == "on":
                        self._pump_protec_period = device_data[ATTR_PUMP_PROTEC]["frequency"]
                        self._pump_protec_duration = device_data[ATTR_PUMP_PROTEC]["duration"]
                    if ATTR_PUMP_PROTEC_DURATION in device_data:
                        self._pump_duration_value = device_data[ATTR_PUMP_PROTEC_DURATION]
                    if ATTR_FLOOR_AUX in device_data:
                        self._em_heat = device_data[ATTR_FLOOR_AUX]
                    self._load2 = device_data[ATTR_FLOOR_OUTPUT2]
                elif device_data["errorCode"] == "ReadTimeout":
                    _LOGGER.warning(
                        "A timeout occur during data update. Device %s do not respond. Check your network... (%s)",
                        self._name,
                        device_data,
                    )
                else:
                    _LOGGER.warning("Error in updating device %s: (%s)", self._name, device_data)
            else:
                self.log_error(device_data["error"]["code"])
            self._occupancy_mode = neviweb_status[ATTR_OCCUPANCY]
            self.do_stat(start)
            self.get_sensor_error_code(start)
            self.get_weather()
        else:
            if time.time() - self._snooze > SNOOZE_TIME:
                self._active = True
                if NOTIFY == "notification" or NOTIFY == "both":
                    self.notify_ha("Warning: Neviweb Device update restarted for " + self._name + ", Sku: " + self._sku)

    @property
    @override
    def extra_state_attributes(self) -> Mapping[str, Any]:
        """Return the state attributes."""
        data = {}
        data.update(
            {
                "neviweb_occupancy_mode": self._occupancy_mode,
                "sensor_mode": self._floor_mode,
                "floor_sensor_type": self._floor_sensor_type,
                "load_watt": self._wattage,
                "auxiliary_cycle_length": neviweb_to_ha(self._aux_cycle_length),
                "cycle_length": neviweb_to_ha(self._cycle_length),
                "pump_protection_status": self._pump_protec_status,
                "pump_protection_duration": self._pump_protec_duration,
                "pump_protection_frequency": self._pump_protec_period,
                "pump_duration_value": self._pump_duration_value,
                "floor_limit_high": self._floor_max,
                "floor_limit_high_status": self._floor_max_status,
                "floor_limit_low": self._floor_min,
                "floor_limit_low_status": self._floor_min_status,
                "max_air_limit": self._floor_air_limit,
                "max_air_limit_status": self._floor_air_limit_status,
                "temp_display_status": self._temp_display_status,
                "temp_display_value": self._temp_display_value,
                "source_type": self._heat_source_type,
                "early_start": self._early_start,
                "setpoint_away": self._target_temp_away,
                "load_watt_1": self._load1,
                "second_display": self._display2,
                "occupancy": self._occupancy,
                "operation_mode": self._operation_mode,
                "auxiliary_heat": self._em_heat,
                "auxiliary_load": self._load2,
                "error_code": self._error_code,
                "heat_level": self._heat_level,
                "pi_heating_demand": self._heat_level,
                "keypad": lock_to_ha(self._keypad),
                "backlight": self._backlight,
                "time_format": self._time_format,
                "temperature_format": self._temperature_format,
                "setpoint_max": self._max_temp,
                "setpoint_min": self._min_temp,
                "eco_status": self._drstatus_active,
                "eco_optOut": self._drstatus_optout,
                "eco_setpoint": self._drstatus_setpoint,
                "eco_power_relative": self._drstatus_rel,
                "eco_power_absolute": self._drstatus_abs,
                "eco_setpoint_status": self._drsetpoint_status,
                "eco_setpoint_delta": self._drsetpoint_value,
                "total_kwh_count": self._total_kwh_count,
                "monthly_kwh_count": self._monthly_kwh_count,
                "daily_kwh_count": self._daily_kwh_count,
                "hourly_kwh_count": self._hourly_kwh_count,
                "hourly_kwh": self._hour_kwh,
                "daily_kwh": self._today_kwh,
                "monthly_kwh": self._month_kwh,
                "last_energy_stat_update": self._mark,
                "outdoor_temp": self._temperature,
                "weather_icon": self._weather_icon,
                "rssi": self._rssi,
                "sku": self._sku,
                "device_model": str(self._device_model),
                "device_model_cfg": self._device_model_cfg,
                "firmware": self._firmware,
                "activation": self._active,
                "id": self._id,
            }
        )
        return data


class Neviweb130WifiFloorThermostat(Neviweb130Thermostat):
    """Implementation of Neviweb TH1300WF, TH1325WF, TH1310WF and SRM40 thermostat."""

    def __init__(self, data, device_info, name, sku, firmware, location):
        """Initialize."""
        super().__init__(data, device_info, name, sku, firmware, location)
        self._early_start = "off"
        self._floor_air_limit_status = None
        self._floor_max_status = "off"
        self._floor_min_status = "off"
        self._gfci_alert = None
        self._gfci_status = None
        self._heat_source_type = None
        self._load1 = 0
        self._load2 = 0
        self._target_temp_away = None

    @override
    def update(self) -> None:
        if self._active:
            WIFI_FLOOR_ATTRIBUTES = [
                ATTR_ROOM_TEMP_DISPLAY,
                ATTR_GFCI_ALERT,
                ATTR_FLOOR_MAX,
                ATTR_FLOOR_MIN,
                ATTR_GFCI_STATUS,
                ATTR_FLOOR_MODE,
                ATTR_FLOOR_AUX,
                ATTR_FLOOR_OUTPUT2,
                ATTR_FLOOR_AIR_LIMIT,
                ATTR_FLOOR_SENSOR,
                ATTR_FLOOR_OUTPUT1,
                ATTR_WIFI_WATTAGE,
                ATTR_WIFI,
                ATTR_WIFI_KEYPAD,
                ATTR_DISPLAY2,
                ATTR_SETPOINT_MODE,
                ATTR_OCCUPANCY,
                ATTR_BACKLIGHT_AUTO_DIM,
                ATTR_EARLY_START,
                ATTR_ROOM_SETPOINT_AWAY,
                ATTR_ROOM_SETPOINT_MIN,
                ATTR_ROOM_SETPOINT_MAX,
            ]
            """Get the latest data from Neviweb and update the state."""
            start = time.time()
            _LOGGER.debug(
                "Updated attributes for %s: %s",
                self._name,
                UPDATE_ATTRIBUTES + WIFI_FLOOR_ATTRIBUTES,
            )
            device_data = self._client.get_device_attributes(self._id, UPDATE_ATTRIBUTES + WIFI_FLOOR_ATTRIBUTES)
            neviweb_status = self._client.get_neviweb_status(self._location)
            end = time.time()
            elapsed = round(end - start, 3)
            _LOGGER.debug("Updating %s (%s sec): %s", self._name, elapsed, device_data)

            if "error" not in device_data:
                if "errorCode" not in device_data:
                    self._cur_temp_before = self._cur_temp
                    self._cur_temp = (
                        float(device_data[ATTR_ROOM_TEMPERATURE]["value"])
                        if device_data[ATTR_ROOM_TEMPERATURE]["value"] is not None
                        else self._cur_temp_before
                    )
                    self._target_temp = float(device_data[ATTR_ROOM_SETPOINT])
                    self._min_temp = device_data[ATTR_ROOM_SETPOINT_MIN]
                    self._max_temp = device_data[ATTR_ROOM_SETPOINT_MAX]
                    self._temperature_format = device_data[ATTR_TEMP]
                    self._time_format = device_data[ATTR_TIME_FORMAT]
                    self._display2 = device_data[ATTR_DISPLAY2]
                    if ATTR_DRSETPOINT in device_data:
                        self._drsetpoint_status = device_data[ATTR_DRSETPOINT]["status"]
                        self._drsetpoint_value = (
                            device_data[ATTR_DRSETPOINT]["value"]
                            if device_data[ATTR_DRSETPOINT]["value"] is not None
                            else 0
                        )
                    if ATTR_DRSTATUS in device_data:
                        self._drstatus_active = device_data[ATTR_DRSTATUS]["drActive"]
                        self._drstatus_optout = device_data[ATTR_DRSTATUS]["optOut"]
                        self._drstatus_setpoint = device_data[ATTR_DRSTATUS]["setpoint"]
                        self._drstatus_abs = device_data[ATTR_DRSTATUS]["powerAbsolute"]
                        self._drstatus_rel = device_data[ATTR_DRSTATUS]["powerRelative"]
                    self._heat_level = device_data[ATTR_OUTPUT_PERCENT_DISPLAY]["percent"]
                    self._heat_source_type = device_data[ATTR_OUTPUT_PERCENT_DISPLAY]["sourceType"]
                    self._operation_mode = device_data[ATTR_SETPOINT_MODE]
                    self._occupancy = device_data[ATTR_OCCUPANCY]
                    self._keypad = device_data[ATTR_WIFI_KEYPAD]
                    self._rssi = device_data[ATTR_WIFI]
                    self._wattage = device_data[ATTR_WIFI_WATTAGE]
                    self._backlight = device_data[ATTR_BACKLIGHT_AUTO_DIM]
                    self._early_start = device_data[ATTR_EARLY_START]
                    self._target_temp_away = device_data[ATTR_ROOM_SETPOINT_AWAY]
                    self._load1 = device_data[ATTR_FLOOR_OUTPUT1]
                    self._gfci_status = device_data[ATTR_GFCI_STATUS]
                    self._floor_mode = device_data[ATTR_FLOOR_MODE]
                    self._em_heat = device_data[ATTR_FLOOR_AUX]
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
                    self._gfci_alert = device_data[ATTR_GFCI_ALERT]
                    self._load2 = device_data[ATTR_FLOOR_OUTPUT2]
                elif device_data["errorCode"] == "ReadTimeout":
                    _LOGGER.warning(
                        "A timeout occur during data update. Device %s do not respond. Check your network... (%s)",
                        self._name,
                        device_data,
                    )
                else:
                    _LOGGER.warning("Error in updating device %s: (%s)", self._name, device_data)
            else:
                self.log_error(device_data["error"]["code"])
            self._occupancy_mode = neviweb_status[ATTR_OCCUPANCY]
            if self._sku != "FLP55" and self._sku != "True Comfort":
                self.do_stat(start)
            self.get_sensor_error_code(start)
            self.get_weather()
        else:
            if time.time() - self._snooze > SNOOZE_TIME:
                self._active = True
                if NOTIFY == "notification" or NOTIFY == "both":
                    self.notify_ha("Warning: Neviweb Device update restarted for " + self._name + ", Sku: " + self._sku)

    @property
    @override
    def extra_state_attributes(self) -> Mapping[str, Any]:
        """Return the state attributes."""
        data = {}
        data.update(
            {
                "neviweb_occupancy_mode": self._occupancy_mode,
                "load_watt": self._wattage,
                "gfci_status": self._gfci_status,
                "sensor_mode": self._floor_mode,
                "operation_mode": self._operation_mode,
                "auxiliary_heat": self._em_heat,
                "auxiliary_load": self._load2,
                "floor_sensor_type": self._floor_sensor_type,
                "floor_limit_high": self._floor_max,
                "floor_limit_high_status": self._floor_max_status,
                "floor_limit_low": self._floor_min,
                "floor_limit_low_status": self._floor_min_status,
                "max_air_limit": self._floor_air_limit,
                "max_air_limit_status": self._floor_air_limit_status,
                "occupancy": self._occupancy,
                "gfci_alert": self._gfci_alert,
                "source_type": self._heat_source_type,
                "early_start": self._early_start,
                "setpoint_away": self._target_temp_away,
                "load_watt_1": self._load1,
                "error_code": self._error_code,
                "heat_level": self._heat_level,
                "pi_heating_demand": self._heat_level,
                "second_display": self._display2,
                "keypad": lock_to_ha(self._keypad),
                "backlight": self._backlight,
                "time_format": self._time_format,
                "temperature_format": self._temperature_format,
                "setpoint_max": self._max_temp,
                "setpoint_min": self._min_temp,
                "eco_status": self._drstatus_active,
                "eco_optOut": self._drstatus_optout,
                "eco_setpoint": self._drstatus_setpoint,
                "eco_power_relative": self._drstatus_rel,
                "eco_power_absolute": self._drstatus_abs,
                "eco_setpoint_status": self._drsetpoint_status,
                "eco_setpoint_delta": self._drsetpoint_value,
                "total_kwh_count": self._total_kwh_count,
                "monthly_kwh_count": self._monthly_kwh_count,
                "daily_kwh_count": self._daily_kwh_count,
                "hourly_kwh_count": self._hourly_kwh_count,
                "hourly_kwh": self._hour_kwh,
                "daily_kwh": self._today_kwh,
                "monthly_kwh": self._month_kwh,
                "last_energy_stat_update": self._mark,
                "outdoor_temp": self._temperature,
                "weather_icon": self._weather_icon,
                "rssi": self._rssi,
                "sku": self._sku,
                "device_model": str(self._device_model),
                "device_model_cfg": self._device_model_cfg,
                "firmware": self._firmware,
                "activation": self._active,
                "id": self._id,
            }
        )
        return data


class Neviweb130HcThermostat(Neviweb130Thermostat):
    """Implementation of Neviweb TH1134ZB-HC thermostat."""

    def __init__(self, data, device_info, name, sku, firmware, location):
        """Initialize."""
        super().__init__(data, device_info, name, sku, firmware, location)
        self._cool_max = 30
        self._cool_min = 16
        self._display_cap = None
        self._fan_cap = None
        self._hc_device = None
        self._heat_lock_temp = None
        self._model = None
        self._sound_cap = None

    @override
    def update(self) -> None:
        if self._active:
            HC_ATTRIBUTES = [
                ATTR_DISPLAY2,
                ATTR_RSSI,
                ATTR_COOL_SETPOINT,
                ATTR_COOL_SETPOINT_MIN,
                ATTR_COOL_SETPOINT_MAX,
                ATTR_SYSTEM_MODE,
                ATTR_CYCLE_LENGTH,
                ATTR_WATTAGE,
                ATTR_BACKLIGHT,
                ATTR_KEYPAD,
                ATTR_HC_DEV,
                ATTR_LANGUAGE,
                ATTR_MODEL,
                ATTR_FAN_SPEED,
                ATTR_FAN_SWING_VERT,
                ATTR_FAN_SWING_HORIZ,
                ATTR_FAN_CAP,
                ATTR_FAN_SWING_CAP,
                ATTR_FAN_SWING_CAP_HORIZ,
                ATTR_FAN_SWING_CAP_VERT,
                ATTR_BALANCE_PT,
                ATTR_HEAT_LOCK_TEMP,
                ATTR_COOL_LOCK_TEMP,
                ATTR_AVAIL_MODE,
                ATTR_DISPLAY_CONF,
                ATTR_DISPLAY_CAP,
                ATTR_SOUND_CONF,
                ATTR_SOUND_CAP,
                ATTR_ROOM_TEMP_DISPLAY,
            ]
            """Get the latest data from Neviweb and update the state."""
            start = time.time()
            _LOGGER.debug(
                "Updated attributes for %s: %s",
                self._name,
                UPDATE_ATTRIBUTES + HC_ATTRIBUTES,
            )
            device_data = self._client.get_device_attributes(self._id, UPDATE_ATTRIBUTES + HC_ATTRIBUTES)
            neviweb_status = self._client.get_neviweb_status(self._location)
            end = time.time()
            elapsed = round(end - start, 3)
            _LOGGER.debug("Updating %s (%s sec): %s", self._name, elapsed, device_data)

            if "error" not in device_data:
                if "errorCode" not in device_data:
                    self._cur_temp_before = self._cur_temp
                    self._cur_temp = (
                        float(device_data[ATTR_ROOM_TEMP_DISPLAY])
                        if device_data[ATTR_ROOM_TEMP_DISPLAY] is not None
                        else self._cur_temp_before
                    )
                    self._target_temp = float(device_data[ATTR_ROOM_SETPOINT])
                    self._min_temp = device_data[ATTR_ROOM_SETPOINT_MIN]
                    self._max_temp = device_data[ATTR_ROOM_SETPOINT_MAX]
                    self._temperature_format = device_data[ATTR_TEMP]
                    self._time_format = device_data[ATTR_TIME_FORMAT]
                    self._temp_display_value = device_data[ATTR_ROOM_TEMP_DISPLAY]
                    self._display2 = device_data[ATTR_DISPLAY2]
                    if ATTR_DRSETPOINT in device_data:
                        self._drsetpoint_status = device_data[ATTR_DRSETPOINT]["status"]
                        self._drsetpoint_value = (
                            device_data[ATTR_DRSETPOINT]["value"]
                            if device_data[ATTR_DRSETPOINT]["value"] is not None
                            else 0
                        )
                    if ATTR_DRSTATUS in device_data:
                        self._drstatus_active = device_data[ATTR_DRSTATUS]["drActive"]
                        self._drstatus_optout = device_data[ATTR_DRSTATUS]["optOut"]
                        self._drstatus_setpoint = device_data[ATTR_DRSTATUS]["setpoint"]
                        self._drstatus_abs = device_data[ATTR_DRSTATUS]["powerAbsolute"]
                        self._drstatus_rel = device_data[ATTR_DRSTATUS]["powerRelative"]
                    if ATTR_OUTPUT_PERCENT_DISPLAY in device_data:
                        self._heat_level = device_data[ATTR_OUTPUT_PERCENT_DISPLAY]
                    self._keypad = device_data[ATTR_KEYPAD]
                    self._backlight = device_data[ATTR_BACKLIGHT]
                    if ATTR_RSSI in device_data:
                        self._rssi = device_data[ATTR_RSSI]
                    self._wattage = device_data[ATTR_WATTAGE]
                    self._cycle_length = device_data[ATTR_CYCLE_LENGTH]
                    self._target_cool = device_data[ATTR_COOL_SETPOINT]
                    self._cool_min = device_data[ATTR_COOL_SETPOINT_MIN]
                    self._cool_max = device_data[ATTR_COOL_SETPOINT_MAX]
                    self._hc_device = device_data[ATTR_HC_DEV]
                    self._language = device_data[ATTR_LANGUAGE]
                    self._model = device_data[ATTR_MODEL]
                    self._fan_speed = device_data[ATTR_FAN_SPEED]
                    self._fan_swing_vert = device_data[ATTR_FAN_SWING_VERT]
                    self._fan_swing_horiz = device_data[ATTR_FAN_SWING_HORIZ]
                    self._fan_cap = device_data[ATTR_FAN_CAP]
                    self._fan_swing_cap = device_data[ATTR_FAN_SWING_CAP]
                    self._fan_swing_cap_vert = device_data[ATTR_FAN_SWING_CAP_VERT]
                    self._fan_swing_cap_horiz = device_data[ATTR_FAN_SWING_CAP_HORIZ]
                    self._balance_pt = device_data[ATTR_BALANCE_PT]
                    self._heat_lock_temp = device_data[ATTR_HEAT_LOCK_TEMP]
                    self._cool_lock_temp = device_data[ATTR_COOL_LOCK_TEMP]
                    self._avail_mode = device_data[ATTR_AVAIL_MODE]
                    self._display_cap = device_data[ATTR_DISPLAY_CAP]
                    self._display_conf = device_data[ATTR_DISPLAY_CONF]
                    self._sound_cap = device_data[ATTR_SOUND_CAP]
                    self._sound_conf = device_data[ATTR_SOUND_CONF]
                elif device_data["errorCode"] == "ReadTimeout":
                    _LOGGER.warning(
                        "A timeout occur during data update. Device %s do not respond. Check your network... (%s)",
                        self._name,
                        device_data,
                    )
                else:
                    _LOGGER.warning("Error in updating device %s: (%s)", self._name, device_data)
            else:
                self.log_error(device_data["error"]["code"])
            self._occupancy_mode = neviweb_status[ATTR_OCCUPANCY]
            self.do_stat(start)
            self.get_sensor_error_code(start)
            self.get_weather()
        else:
            if time.time() - self._snooze > SNOOZE_TIME:
                self._active = True
                if NOTIFY == "notification" or NOTIFY == "both":
                    self.notify_ha("Warning: Neviweb Device update restarted for " + self._name + ", Sku: " + self._sku)

    @property
    @override
    def extra_state_attributes(self) -> Mapping[str, Any]:
        """Return the state attributes."""
        data = {}
        data.update(
            {
                "neviweb_occupancy_mode": self._occupancy_mode,
                "wattage": self._wattage,
                "error_code": self._error_code,
                "cool setpoint min": self._cool_min,
                "cool setpoint max": self._cool_max,
                "cool setpoint": self._target_cool,
                "cycle_length": neviweb_to_ha(self._cycle_length),
                "hc_device": self._hc_device,
                "language": self._language,
                "model": self._model,
                "fan_speed": self._fan_speed,
                "fan_swing_vertical": self._fan_swing_vert,
                "fan_swing_horizontal": self._fan_swing_horiz,
                "fan_capability": self._fan_cap,
                "fan_swing_capability": extract_capability(self._fan_swing_cap),
                "fan_swing_capability_vertical": extract_capability_full(self._fan_swing_cap_vert),
                "fan_swing_capability_horizontal": extract_capability_full(self._fan_swing_cap_horiz),
                "display_conf": self._display_conf,
                "display_capability": extract_capability(self._display_cap),
                "sound_conf": self._sound_conf,
                "sound_capability": extract_capability(self._sound_cap),
                "balance_point": self._balance_pt,
                "heat_lock_temp": self._heat_lock_temp,
                "cool_lock_temp": self._cool_lock_temp,
                "available_mode": self._avail_mode,
                "heat_level": self._heat_level,
                "pi_heating_demand": self._heat_level,
                "temp_display_value": self._temp_display_value,
                "second_display": self._display2,
                "keypad": lock_to_ha(self._keypad),
                "backlight": self._backlight,
                "time_format": self._time_format,
                "temperature_format": self._temperature_format,
                "setpoint_max": self._max_temp,
                "setpoint_min": self._min_temp,
                "eco_status": self._drstatus_active,
                "eco_optOut": self._drstatus_optout,
                "eco_setpoint": self._drstatus_setpoint,
                "eco_power_relative": self._drstatus_rel,
                "eco_power_absolute": self._drstatus_abs,
                "eco_setpoint_status": self._drsetpoint_status,
                "eco_setpoint_delta": self._drsetpoint_value,
                "total_kwh_count": self._total_kwh_count,
                "monthly_kwh_count": self._monthly_kwh_count,
                "daily_kwh_count": self._daily_kwh_count,
                "hourly_kwh_count": self._hourly_kwh_count,
                "hourly_kwh": self._hour_kwh,
                "daily_kwh": self._today_kwh,
                "monthly_kwh": self._month_kwh,
                "last_energy_stat_update": self._mark,
                "outdoor_temp": self._temperature,
                "weather_icon": self._weather_icon,
                "rssi": self._rssi,
                "sku": self._sku,
                "device_model": str(self._device_model),
                "device_model_cfg": self._device_model_cfg,
                "firmware": self._firmware,
                "activation": self._active,
                "id": self._id,
            }
        )
        return data


class Neviweb130HPThermostat(Neviweb130Thermostat):
    """Implementation of Neviweb HP6000ZB-GE, HP6000ZB-MA and HP6000ZB-HS heat pump interfaces thermostats."""

    def __init__(self, data, device_info, name, sku, firmware, location):
        """Initialize."""
        super().__init__(data, device_info, name, sku, firmware, location)
        self._cool_max = 30
        self._cool_min = 16
        self._display_cap = None
        self._fan_cap = None
        self._heat_lock_temp = None
        self._model = None
        self._sound_cap = None

    @override
    def update(self) -> None:
        if self._active:
            HP_ATTRIBUTES = [
                ATTR_RSSI,
                ATTR_COOL_SETPOINT,
                ATTR_SYSTEM_MODE,
                ATTR_KEYPAD,
                ATTR_MODEL,
                ATTR_FAN_SPEED,
                ATTR_FAN_SWING_VERT,
                ATTR_FAN_CAP,
                ATTR_AVAIL_MODE,
            ]
            if self._firmware != "0.1.7":
                NEW_HP_ATTRIBUTES = [
                    ATTR_DRSTATUS,
                    ATTR_DRSETPOINT,
                    ATTR_FAN_SWING_HORIZ,
                    ATTR_FAN_SWING_CAP,
                    ATTR_FAN_SWING_CAP_HORIZ,
                    ATTR_FAN_SWING_CAP_VERT,
                    ATTR_BALANCE_PT,
                    ATTR_HEAT_LOCK_TEMP,
                    ATTR_COOL_LOCK_TEMP,
                    ATTR_DISPLAY_CONF,
                    ATTR_DISPLAY_CAP,
                    ATTR_SOUND_CONF,
                    ATTR_SOUND_CAP,
                ]
            else:
                NEW_HP_ATTRIBUTES = []
            """Get the latest data from Neviweb and update the state."""
            start = time.time()
            _LOGGER.debug(
                "Updated attributes for %s: %s",
                self._name,
                UPDATE_HP_ATTRIBUTES + HP_ATTRIBUTES + NEW_HP_ATTRIBUTES,
            )
            device_data = self._client.get_device_attributes(
                self._id, UPDATE_HP_ATTRIBUTES + HP_ATTRIBUTES + NEW_HP_ATTRIBUTES
            )
            neviweb_status = self._client.get_neviweb_status(self._location)
            end = time.time()
            elapsed = round(end - start, 3)
            _LOGGER.debug("Updating %s (%s sec): %s", self._name, elapsed, device_data)

            if "error" not in device_data:
                if "errorCode" not in device_data:
                    self._cur_temp_before = self._cur_temp
                    self._cur_temp = (
                        float(device_data[ATTR_ROOM_TEMPERATURE])
                        if device_data[ATTR_ROOM_TEMPERATURE] is not None
                        else self._cur_temp_before
                    )
                    self._operation_mode = device_data[ATTR_SYSTEM_MODE]
                    self._target_temp = (
                        float(device_data[ATTR_COOL_SETPOINT])
                        if self._operation_mode == "cool"
                        else float(device_data[ATTR_ROOM_SETPOINT])
                    )
                    self._min_temp = device_data[ATTR_ROOM_SETPOINT_MIN]
                    self._max_temp = device_data[ATTR_ROOM_SETPOINT_MAX]
                    self._target_cool = device_data[ATTR_COOL_SETPOINT]
                    self._cool_min = device_data[ATTR_COOL_SETPOINT_MIN]
                    self._cool_max = device_data[ATTR_COOL_SETPOINT_MAX]
                    self._temperature_format = device_data[ATTR_TEMP]
                    if ATTR_MODEL in device_data and ATTR_MODEL is not None:
                        self._model = device_data[ATTR_MODEL]
                    if ATTR_DRSETPOINT in device_data:
                        self._drsetpoint_status = device_data[ATTR_DRSETPOINT]["status"]
                        self._drsetpoint_value = (
                            device_data[ATTR_DRSETPOINT]["value"]
                            if device_data[ATTR_DRSETPOINT]["value"] is not None
                            else 0
                        )
                    if ATTR_DRSTATUS in device_data:
                        self._drstatus_active = device_data[ATTR_DRSTATUS]["drActive"]
                        self._drstatus_optout = device_data[ATTR_DRSTATUS]["optOut"]
                        self._drstatus_setpoint = device_data[ATTR_DRSTATUS]["setpoint"]
                        self._drstatus_abs = device_data[ATTR_DRSTATUS]["powerAbsolute"]
                        self._drstatus_rel = device_data[ATTR_DRSTATUS]["powerRelative"]
                    self._keypad = device_data[ATTR_KEYPAD]
                    if ATTR_RSSI in device_data:
                        self._rssi = device_data[ATTR_RSSI]
                    self._fan_speed = device_data[ATTR_FAN_SPEED]
                    self._fan_swing_vert = device_data[ATTR_FAN_SWING_VERT]
                    self._fan_cap = device_data[ATTR_FAN_CAP]
                    self._avail_mode = device_data[ATTR_AVAIL_MODE]
                    if ATTR_FAN_SWING_HORIZ in device_data:
                        self._fan_swing_horiz = device_data[ATTR_FAN_SWING_HORIZ]
                        self._fan_swing_cap = device_data[ATTR_FAN_SWING_CAP]
                        self._fan_swing_cap_horiz = device_data[ATTR_FAN_SWING_CAP_HORIZ]
                        self._fan_swing_cap_vert = device_data[ATTR_FAN_SWING_CAP_VERT]
                        self._balance_pt = device_data[ATTR_BALANCE_PT]
                        self._heat_lock_temp = device_data[ATTR_HEAT_LOCK_TEMP]
                        self._cool_lock_temp = device_data[ATTR_COOL_LOCK_TEMP]
                    if ATTR_BALANCE_PT_TEMP_LOW in device_data:
                        self._balance_pt_low = device_data[ATTR_BALANCE_PT_TEMP_LOW]
                        self._balance_pt_high = device_data[ATTR_BALANCE_PT_TEMP_HIGH]
                    if ATTR_DISPLAY_CONF in device_data:
                        self._display_conf = device_data[ATTR_DISPLAY_CONF]
                        self._display_cap = device_data[ATTR_DISPLAY_CAP]
                        self._sound_conf = device_data[ATTR_SOUND_CONF]
                        self._sound_cap = device_data[ATTR_SOUND_CAP]
                elif device_data["errorCode"] == "ReadTimeout":
                    _LOGGER.warning(
                        "A timeout occur during data update. Device %s do not respond. Check your network... (%s)",
                        self._name,
                        device_data,
                    )
                else:
                    _LOGGER.warning("Error in updating device %s: (%s)", self._name, device_data)
            else:
                self.log_error(device_data["error"]["code"])
            self._occupancy_mode = neviweb_status[ATTR_OCCUPANCY]
            self.get_sensor_error_code(start)
            self.get_weather()
        else:
            if time.time() - self._snooze > SNOOZE_TIME:
                self._active = True
                if NOTIFY == "notification" or NOTIFY == "both":
                    self.notify_ha("Warning: Neviweb Device update restarted for " + self._name + ", Sku: " + self._sku)

    @property
    @override
    def extra_state_attributes(self) -> Mapping[str, Any]:
        """Return the state attributes."""
        data = {}
        data.update(
            {
                "neviweb_occupancy_mode": self._occupancy_mode,
                "heat_pump_model": self._model,
                "error_code": self._error_code,
                "operation modes": self._operation_mode,
                "cool setpoint min": self._cool_min,
                "cool setpoint max": self._cool_max,
                "setpoint_max": self._max_temp,
                "setpoint_min": self._min_temp,
                "temperature_format": self._temperature_format,
                "keypad": lock_to_ha(self._keypad),
                "fan_speed": self._fan_speed,
                "fan_swing_vertical": self._fan_swing_vert,
                "fan_capability": self._fan_cap,
                "available_mode": self._avail_mode,
            }
        )
        if self._firmware != "0.1.7":
            data.update(
                {
                    "heat_pump_limit_temp": self._balance_pt,
                    #                         'min_heat_pump_limit_temp': self._balance_pt_low,
                    #                         'max_heat_pump_limit_temp': self._balance_pt_high,
                    "heat_lock_temp": self._heat_lock_temp,
                    "cool_lock_temp": self._cool_lock_temp,
                    "fan_swing_horizontal": self._fan_swing_horiz,
                    "fan_swing_capability": extract_capability(self._fan_swing_cap),
                    "fan_swing_capability_vertical": extract_capability_full(self._fan_swing_cap_vert),
                    "fan_swing_capability_horizontal": extract_capability_full(self._fan_swing_cap_horiz),
                    "display_conf": self._display_conf,
                    "display_capability": extract_capability(self._display_cap),
                    "sound_conf": self._sound_conf,
                    "sound_capability": extract_capability(self._sound_cap),
                    "eco_status": self._drstatus_active,
                    "eco_optOut": self._drstatus_optout,
                    "eco_setpoint": self._drstatus_setpoint,
                    "eco_power_relative": self._drstatus_rel,
                    "eco_power_absolute": self._drstatus_abs,
                    "eco_setpoint_status": self._drsetpoint_status,
                    "eco_setpoint_delta": self._drsetpoint_value,
                }
            )
        data.update(
            {
                "outdoor_temp": self._temperature,
                "weather_icon": self._weather_icon,
                "rssi": self._rssi,
                "sku": self._sku,
                "device_model": str(self._device_model),
                "device_model_cfg": self._device_model_cfg,
                "firmware": self._firmware,
                "activation": self._active,
                "id": self._id,
            }
        )
        return data


class Neviweb130HeatCoolThermostat(Neviweb130Thermostat):
    """Implementation of Neviweb TH6500WF, TH6510WF, TH6250WF, TH6250WF-PRO heat cool thermostats."""

    def __init__(self, data, device_info, name, sku, firmware, location):
        """Initialize."""
        super().__init__(data, device_info, name, sku, firmware, location)
        self._accessory_type = "none"
        self._air_curt_activation_temp = None
        self._air_curt_activation_temp = None
        self._air_curt_conf = None
        self._air_curt_max_temp = None
        self._air_ex_min_time_on = None
        self._air_min_time_on = 0
        self._aux_cycle = None
        self._aux_heat_min_time_off = None
        self._aux_heat_min_time_on = None
        self._aux_heat_source_type = None
        self._aux_heat_start_delay = None
        self._aux_interstage_delay = None
        self._aux_interstage_min_delay = None
        self._reversing_valve_polarity = "cooling"
        self._backlight_auto_dim = None
        self._balance_pt = -15
        self._cool_cycle_length = 0
        self._cool_interstage_delay = None
        self._cool_interstage_min_delay = None
        self._cool_max = 36
        self._cool_min = 16
        self._cool_min_time_off = None
        self._cool_min_time_on = None
        self._cool_purge_time = 0
        self._cool_target_temp = None
        self._cool_target_temp_away = None
        self._cycle = None
        self._dr_accessory_conf = None
        self._dr_air_curt_conf = None
        self._dr_aux_config = None
        self._dr_fan_speed_conf = None
        self._dual_status = None
        self._fan_filter_life = None
        self._fan_filter_remain = None
        self._heat_cool = None
        self._heat_inst_type = None
        self._heat_interstage_delay = None
        self._heat_interstage_min_delay = None
        self._heat_level_source_type = "heating"
        self._heat_lock_temp = None
        self._heat_min_time_off = None
        self._heat_min_time_off = None
        self._heat_min_time_on = None
        self._heat_min_time_on = None
        self._heat_purge_time = 0
        self._heat_source_type = None
        self._heatcool_lock_balance_point_status = None
        self._heatcool_lock_cool_status = None
        self._heatcool_lock_heat_status = None
        self._heatcool_setpoint_delta = 2
        self._humidity_display = None
        self._humidity_setpoint = None
        self._humidity_setpoint_mode = None
        self._humidity_setpoint_offset = 0
        self._interlock_id = None
        self._output_connect_state = {
            "Y1": False,
            "Y2": False,
            "OB": False,
            "W": False,
            "W2": False,
            "G": False,
            "Rh": False,
            "Acc": False,
            "LC": False,
        }
        self._temp_display_status = None
        self._temp_offset_heat = None

    @override
    def update(self) -> None:
        if self._active:
            HC_ATTRIBUTES = [
                ATTR_WIFI_KEYPAD,
                ATTR_HEAT_COOL,
                ATTR_SETPOINT_MODE,
                ATTR_LANGUAGE,
                ATTR_BACK_LIGHT,
                ATTR_BACKLIGHT_AUTO_DIM,
                ATTR_HEAT_SOURCE_TYPE,
                ATTR_AUX_HEAT_SOURCE_TYPE,
                ATTR_FAN_SPEED,
                ATTR_BALANCE_PT,
                ATTR_HEAT_LOCK_TEMP,
                ATTR_COOL_LOCK_TEMP,
                ATTR_REVERSING_VALVE_POLARITY,
                ATTR_HUMIDITY_SETPOINT,
                ATTR_COOL_CYCLE_LENGTH,
                ATTR_CYCLE_LENGTH,
                ATTR_AUX_CYCLE_LENGTH,
                ATTR_HEATCOOL_SETPOINT_MIN_DELTA,
                ATTR_TEMP_OFFSET_HEAT,
                ATTR_HUMIDITY_DISPLAY,
                ATTR_DUAL_STATUS,
                ATTR_EARLY_START,
                ATTR_ROOM_SETPOINT_AWAY,
                ATTR_COOL_SETPOINT_AWAY,
                ATTR_FAN_FILTER_REMAIN,
                ATTR_FAN_FILTER_LIFE,
                ATTR_AUX_HEAT_MIN_TIME_ON,
                ATTR_AUX_HEAT_START_DELAY,
                ATTR_OUTPUT_CONNECT_STATE,
                ATTR_COOL_MIN_TIME_ON,
                ATTR_COOL_MIN_TIME_OFF,
                ATTR_HEAT_INSTALL_TYPE,
                ATTR_OCCUPANCY,
            ]
            """Get specific attributes"""
            if self._device_model == 6727:
                HC_EXTRA = [
                    ATTR_HEAT_INTERSTAGE_MIN_DELAY,
                    ATTR_AUX_INTERSTAGE_MIN_DELAY,
                    ATTR_HEAT_INTERSTAGE_DELAY,
                    ATTR_AUX_INTERSTAGE_DELAY,
                    ATTR_COOL_INTERSTAGE_MIN_DELAY,
                    ATTR_COOL_INTERSTAGE_DELAY,
                    ATTR_DRSETPOINT,
                    ATTR_DRSTATUS,
                ]
            else:
                HC_EXTRA = []
            if self._firmware == "4.2.1" or self._firmware == "4.3.0":
                HC_SPECIAL_FIRMWARE = [
                    ATTR_HEAT_MIN_TIME_ON,
                    ATTR_HEAT_MIN_TIME_OFF,
                    ATTR_ACCESSORY_TYPE,
                    ATTR_HUMIDITY_SETPOINT_OFFSET,
                    ATTR_HUMIDITY_SETPOINT_MODE,
                    ATTR_AIR_EX_MIN_TIME_ON,
                    ATTR_HC_LOCK_STATUS,
                    ATTR_DRAUXCONF,
                    ATTR_DRFANCONF,
                    ATTR_DRACCESORYCONF,
                    ATTR_DRAIR_CURT_CONF,
                    ATTR_HEAT_PURGE_TIME,
                    ATTR_COOL_PURGE_TIME,
                    ATTR_AIR_CONFIG,
                    ATTR_AIR_ACTIVATION_TEMP,
                    ATTR_AIR_MAX_POWER_TEMP,
                    ATTR_AUX_HEAT_MIN_TIME_OFF,
                ]
                if self._firmware == "4.3.0":
                    HC_43 = [ATTR_INTERLOCK_ID]
                else:
                    HC_43 = []
            else:
                HC_SPECIAL_FIRMWARE = []
                HC_43 = []

            """Get the latest data from Neviweb and update the state."""
            start = time.time()
            _LOGGER.debug(
                "Updated attributes for %s (firmware %s): %s",
                self._name,
                self._firmware,
                UPDATE_HEAT_COOL_ATTRIBUTES + HC_ATTRIBUTES + HC_EXTRA + HC_SPECIAL_FIRMWARE + HC_43,
            )
            device_data = self._client.get_device_attributes(
                self._id,
                UPDATE_HEAT_COOL_ATTRIBUTES + HC_ATTRIBUTES + HC_EXTRA + HC_SPECIAL_FIRMWARE + HC_43,
            )
            neviweb_status = self._client.get_neviweb_status(self._location)
            end = time.time()
            elapsed = round(end - start, 3)
            _LOGGER.debug("Updating %s (%s sec): %s", self._name, elapsed, device_data)

            if "error" not in device_data:
                if "errorCode" not in device_data:
                    self._cur_temp_before = self._cur_temp
                    self._cur_temp = (
                        float(device_data[ATTR_ROOM_TEMPERATURE]["value"])
                        if device_data[ATTR_ROOM_TEMPERATURE]["value"] is not None
                        else self._cur_temp_before
                    )
                    self._heat_cool = device_data[ATTR_HEAT_COOL]
                    self._target_temp = float(device_data[ATTR_ROOM_SETPOINT])
                    self._min_temp = device_data[ATTR_ROOM_SETPOINT_MIN]
                    self._max_temp = device_data[ATTR_ROOM_SETPOINT_MAX]
                    self._target_cool = float(device_data[ATTR_COOL_SETPOINT])
                    self._cool_min = device_data[ATTR_COOL_SETPOINT_MIN]
                    self._cool_max = device_data[ATTR_COOL_SETPOINT_MAX]
                    self._heatcool_setpoint_delta = device_data[ATTR_HEATCOOL_SETPOINT_MIN_DELTA]
                    self._temperature_format = device_data[ATTR_TEMP]
                    self._time_format = device_data[ATTR_TIME_FORMAT]
                    self._heat_level = device_data[ATTR_OUTPUT_PERCENT_DISPLAY]["percent"]
                    self._heat_level_source_type = device_data[ATTR_OUTPUT_PERCENT_DISPLAY]["sourceType"]
                    self._heat_source_type = device_data[ATTR_HEAT_SOURCE_TYPE]
                    self._aux_heat_source_type = device_data[ATTR_AUX_HEAT_SOURCE_TYPE]
                    self._operation_mode = device_data[ATTR_SETPOINT_MODE]
                    if ATTR_DRSETPOINT in device_data:
                        self._drsetpoint_status = device_data[ATTR_DRSETPOINT]["status"]
                        self._drsetpoint_value = (
                            device_data[ATTR_DRSETPOINT]["value"]
                            if device_data[ATTR_DRSETPOINT]["value"] is not None
                            else 0
                        )
                    if ATTR_DRSTATUS in device_data:
                        self._drstatus_active = device_data[ATTR_DRSTATUS]["drActive"]
                        self._drstatus_optout = device_data[ATTR_DRSTATUS]["optOut"]
                        self._drstatus_setpoint = device_data[ATTR_DRSTATUS]["setpoint"]
                        self._drstatus_abs = device_data[ATTR_DRSTATUS]["powerAbsolute"]
                        self._drstatus_rel = device_data[ATTR_DRSTATUS]["powerRelative"]
                    if ATTR_RSSI in device_data:
                        self._rssi = device_data[ATTR_RSSI]
                    self._fan_speed = device_data[ATTR_FAN_SPEED]
                    self._fan_filter_remain = device_data[ATTR_FAN_FILTER_REMAIN]
                    if ATTR_FAN_FILTER_LIFE in device_data:
                        self._fan_filter_life = device_data[ATTR_FAN_FILTER_LIFE]
                    if ATTR_ROOM_TEMP_DISPLAY in device_data:
                        self._temp_display_status = device_data[ATTR_ROOM_TEMP_DISPLAY]["status"]
                        self._temp_display_value = device_data[ATTR_ROOM_TEMP_DISPLAY]["value"]
                    self._language = device_data[ATTR_LANGUAGE]
                    if ATTR_OCCUPANCY in device_data:
                        self._occupancy = device_data[ATTR_OCCUPANCY]
                    self._keypad = device_data[ATTR_WIFI_KEYPAD]
                    if ATTR_BACK_LIGHT in device_data:
                        self._backlight = device_data[ATTR_BACK_LIGHT]
                    self._backlight_auto_dim = device_data[ATTR_BACKLIGHT_AUTO_DIM]
                    self._early_start = device_data[ATTR_EARLY_START]
                    self._target_temp_away = device_data[ATTR_ROOM_SETPOINT_AWAY]
                    self._cool_target_temp_away = device_data[ATTR_COOL_SETPOINT_AWAY]
                    self._reversing_valve_polarity = device_data[ATTR_REVERSING_VALVE_POLARITY]
                    self._heat_lock_temp = device_data[ATTR_HEAT_LOCK_TEMP]
                    self._cool_lock_temp = device_data[ATTR_COOL_LOCK_TEMP]
                    self._balance_pt = device_data[ATTR_BALANCE_PT]
                    self._humidity_display = device_data[ATTR_HUMIDITY_DISPLAY]
                    self._humidity_setpoint = device_data[ATTR_HUMIDITY_SETPOINT]
                    self._cycle = device_data[ATTR_CYCLE_LENGTH]
                    self._aux_cycle = device_data[ATTR_AUX_CYCLE_LENGTH]
                    self._cool_cycle_length = device_data[ATTR_COOL_CYCLE_LENGTH]
                    self._temp_offset_heat = device_data[ATTR_TEMP_OFFSET_HEAT]
                    self._aux_heat_min_time_on = device_data[ATTR_AUX_HEAT_MIN_TIME_ON]
                    self._aux_heat_start_delay = device_data[ATTR_AUX_HEAT_START_DELAY]
                    if ATTR_HEAT_INTERSTAGE_MIN_DELAY in device_data:
                        self._heat_interstage_min_delay = device_data[ATTR_HEAT_INTERSTAGE_MIN_DELAY]
                        self._aux_interstage_min_delay = device_data[ATTR_AUX_INTERSTAGE_MIN_DELAY]
                        self._heat_interstage_delay = device_data[ATTR_HEAT_INTERSTAGE_DELAY]
                        self._aux_interstage_delay = device_data[ATTR_AUX_INTERSTAGE_DELAY]
                        self._cool_interstage_min_delay = device_data[ATTR_COOL_INTERSTAGE_MIN_DELAY]
                        self._cool_interstage_delay = device_data[ATTR_COOL_INTERSTAGE_DELAY]
                    self._dual_status = device_data[ATTR_DUAL_STATUS]
                    self._cool_min_time_on = device_data[ATTR_COOL_MIN_TIME_ON]
                    self._cool_min_time_off = device_data[ATTR_COOL_MIN_TIME_OFF]
                    if ATTR_HEAT_INSTALL_TYPE in device_data:
                        self._heat_inst_type = device_data[ATTR_HEAT_INSTALL_TYPE]
                    self._output_connect_state = device_data[ATTR_OUTPUT_CONNECT_STATE]
                    if self._firmware == "4.2.1" or self._firmware == "4.3.0":
                        accessory_type = [
                            str(accessory_type).removesuffix("Standalone")
                            for accessory_type, value in device_data[ATTR_ACCESSORY_TYPE].items()
                            if value
                        ]
                        self._accessory_type = accessory_type[0] if accessory_type else "none"
                        self._humidity_setpoint_offset = device_data[ATTR_HUMIDITY_SETPOINT_OFFSET]
                        self._humidity_setpoint_mode = device_data[ATTR_HUMIDITY_SETPOINT_MODE]
                        self._air_ex_min_time_on = device_data[ATTR_AIR_EX_MIN_TIME_ON]
                        self._heatcool_lock_cool_status = device_data[ATTR_HC_LOCK_STATUS]["cool"]
                        self._heatcool_lock_heat_status = device_data[ATTR_HC_LOCK_STATUS]["heat"]
                        self._heatcool_lock_balance_point_status = device_data[ATTR_HC_LOCK_STATUS]["balancePoint"]
                        self._dr_aux_config = device_data[ATTR_DRAUXCONF]
                        self._dr_fan_speed_conf = device_data[ATTR_DRFANCONF]
                        self._dr_accessory_conf = device_data[ATTR_DRACCESORYCONF]
                        self._dr_air_curt_conf = device_data[ATTR_DRAIR_CURT_CONF]
                        self._heat_purge_time = device_data[ATTR_HEAT_PURGE_TIME]
                        self._cool_purge_time = device_data[ATTR_COOL_PURGE_TIME]
                        self._air_curt_conf = device_data[ATTR_AIR_CONFIG]
                        self._air_curt_activation_temp = device_data[ATTR_AIR_ACTIVATION_TEMP]
                        self._air_curt_max_temp = device_data[ATTR_AIR_MAX_POWER_TEMP]
                        self._aux_heat_min_time_off = device_data[ATTR_AUX_HEAT_MIN_TIME_OFF]
                        self._heat_min_time_on = device_data[ATTR_HEAT_MIN_TIME_ON]
                        self._heat_min_time_off = device_data[ATTR_HEAT_MIN_TIME_OFF]
                        if self._firmware == "4.3.0":
                            self._interlock_id = device_data[ATTR_INTERLOCK_ID]
                elif device_data["errorCode"] == "ReadTimeout":
                    _LOGGER.warning(
                        "A timeout occur during data update. Device %s do not respond. Check your network... (%s)",
                        self._name,
                        device_data,
                    )
                else:
                    _LOGGER.warning("Error in updating device %s: (%s)", self._name, device_data)
            else:
                self.log_error(device_data["error"]["code"])
            self._occupancy_mode = neviweb_status[ATTR_OCCUPANCY]
            self.get_sensor_error_code(start)
            self.get_weather()
        else:
            if time.time() - self._snooze > SNOOZE_TIME:
                self._active = True
                if NOTIFY == "notification" or NOTIFY == "both":
                    self.notify_ha("Warning: Neviweb Device update restarted for " + self._name + ", Sku: " + self._sku)

    @property
    @override
    def supported_features(self) -> ClimateEntityFeature:
        """Return the list of supported features."""
        features = SUPPORT_HC_FLAGS

        if self._accessory_type != "none":
            features |= ClimateEntityFeature.TARGET_HUMIDITY

        if self.hvac_mode == HVACMode.HEAT_COOL:
            features |= ClimateEntityFeature.TARGET_TEMPERATURE_RANGE
        elif self.hvac_mode != HVACMode.OFF:
            features |= ClimateEntityFeature.TARGET_TEMPERATURE

        can_control_fan = self._output_connect_state["G"]
        if can_control_fan:
            features |= ClimateEntityFeature.FAN_MODE

        return features

    @property
    @override
    def is_on(self) -> bool:
        """Return True if mode = HVACMode.HEAT or HVACMode.COOL."""
        return (
            self._heat_cool == HVACMode.HEAT
            or self._heat_cool == HVACMode.COOL
            or self._heat_cool == HVACMode.AUTO
            or self._heat_cool == MODE_EM_HEAT
        )

    @property
    @override
    def hvac_action(self) -> HVACAction:
        """Return current HVAC action."""
        if self.hvac_mode == HVACMode.OFF:
            return HVACAction.OFF
        if self._heat_level == 0:
            return HVACAction.IDLE
        if self._heat_cool == HVACMode.COOL:
            return HVACAction.COOLING
        if self._heat_cool == HVACMode.HEAT:
            return HVACAction.HEATING
        return HVACAction(self._heat_level_source_type)

    @property
    @override
    def hvac_mode(self) -> HVACMode:
        """Return current operation."""
        if self._heat_cool == HVACMode.OFF:
            return HVACMode.OFF
        elif self._heat_cool == HVACMode.AUTO:
            return HVACMode.HEAT_COOL
        elif self._heat_cool == HVACMode.COOL:
            return HVACMode.COOL
        else:
            return HVACMode.HEAT

    @property
    @override
    def hvac_modes(self) -> list[HVACMode]:
        """Return the list of available operation modes."""
        outputs = self._output_connect_state
        hp_can_cool = self._reversing_valve_polarity == "heating" or outputs["OB"]
        hp_can_heat = self._reversing_valve_polarity == "cooling" or outputs["OB"]
        can_cool = outputs["Y1"] or outputs["Y2"] or hp_can_cool
        can_heat = outputs["W"] or outputs["W2"] or hp_can_heat

        return (
            ([HVACMode.HEAT_COOL] if can_heat and can_cool else [])
            + ([HVACMode.HEAT] if can_heat else [])
            + ([HVACMode.COOL] if can_cool else [])
            + [HVACMode.OFF]
        )

    @property
    @override
    def preset_mode(self) -> str:
        """Return current preset mode."""
        if self._heat_cool == MODE_EM_HEAT:
            return PRESET_BOOST

        return super().preset_mode

    @property
    @override
    def preset_modes(self) -> list[str]:
        """Return available preset modes."""
        outputs = self._output_connect_state

        hp_can_heat = self._reversing_valve_polarity == "cooling" or outputs["OB"]

        can_heat_emergency = (outputs["W"] or outputs["W2"]) and hp_can_heat and (outputs["Y1"] or outputs["Y2"])

        return PRESET_HC_MODES + ([PRESET_BOOST] if can_heat_emergency else [])

    @property
    def is_em_heat(self) -> bool:
        """Return emergency heat state."""
        return self._heat_cool == MODE_EM_HEAT

    @property
    @override
    def fan_modes(self) -> list[str] | None:
        """Return available fan modes."""
        return WIFI_FAN_SPEED

    @property
    @override
    def min_temp(self) -> float:
        """Return the minimum temperature."""
        if self.hvac_mode == HVACMode.HEAT_COOL:
            return min(self._min_temp, self._cool_min)
        elif self.hvac_mode == HVACMode.COOL:
            return self._cool_min
        else:
            return self._min_temp

    @property
    @override
    def max_temp(self) -> float:
        """Return the maximum temperature."""
        if self.hvac_mode == HVACMode.HEAT_COOL:
            return max(self._max_temp, self._cool_max)
        elif self.hvac_mode == HVACMode.COOL:
            return self._cool_max
        else:
            return self._max_temp

    @property
    @override
    def target_temperature(self) -> float | None:
        """Return the temperature we try to reach less Eco Sinope dr_setpoint delta."""
        if self.hvac_mode == HVACMode.COOL:
            return self.target_temperature_high
        else:
            return self.target_temperature_low

    @property
    @override
    def target_temperature_low(self) -> float:
        """Return the heating temperature we try to reach less Eco Sinope dr_setpoint delta."""
        return self._target_temp + self._drsetpoint_value

    @property
    @override
    def target_temperature_high(self) -> float:
        """Return the cooling temperature we try to reach."""
        return self._target_cool

    @property
    @override
    def current_humidity(self) -> float | None:
        """Show current humidity percent."""
        return self._humidity_display

    @property
    @override
    def target_humidity(self) -> float | None:
        """Return target humidity."""
        if self._humidity_setpoint_mode == "defog":
            return self._humidity_setpoint_offset
        return self._humidity_setpoint

    @property
    @override
    def min_humidity(self) -> float:
        if self._humidity_setpoint_mode == "defog":
            return -10.0
        else:
            return 10.0

    @property
    @override
    def max_humidity(self) -> float:
        if self._humidity_setpoint_mode == "defog":
            return 10.0
        else:
            return 70.0

    @override
    def turn_on(self) -> None:
        """Turn the thermostat to HVACMode.HEAT_COOL."""
        self._heat_cool = HVACMode.AUTO
        self._client.set_setpoint_mode(self._id, self._heat_cool, self._is_wifi, self._is_HC)

    @override
    def turn_off(self) -> None:
        """Turn the thermostat to HVACMode.OFF."""
        self._heat_cool = HVACMode.OFF
        self._client.set_setpoint_mode(self._id, self._heat_cool, self._is_wifi, self._is_HC)

    @override
    def set_hvac_mode(self, hvac_mode: HVACMode) -> None:
        """Set new hvac mode."""
        self._client.set_setpoint_mode(self._id, hvac_mode, self._is_wifi, self._is_HC)

        self._heat_cool = hvac_mode if hvac_mode != HVACMode.HEAT_COOL else HVACMode.AUTO

        # Reset the preset to the occupancy
        self.set_preset_mode(self._occupancy)

        self.update()

    @override
    def set_preset_mode(self, preset_mode: str) -> None:
        """Activate a preset."""

        if preset_mode == PRESET_BOOST:
            self._heat_cool = MODE_EM_HEAT
            self._client.set_setpoint_mode(self._id, self._heat_cool, self._is_wifi, self._is_HC)
        else:
            self._occupancy = preset_mode
            self._client.set_occupancy_mode(self._id, self._occupancy, self._is_wifi)

            if self._heat_cool == MODE_EM_HEAT:
                self.set_hvac_mode(HVACMode.HEAT)

    @override
    def set_temperature(self, **kwargs: Any) -> None:
        """Set new target temperature."""
        temperature_low = None
        temperature_high = None
        if self.hvac_mode == HVACMode.HEAT_COOL:
            temperature_low = kwargs.get(ATTR_TARGET_TEMP_LOW)
            temperature_high = kwargs.get(ATTR_TARGET_TEMP_HIGH)
        else:
            temperature = kwargs.get(ATTR_TEMPERATURE)
            if self.hvac_mode == HVACMode.COOL:
                temperature_high = temperature
            else:
                temperature_low = temperature

        if temperature_low is not None:
            temperature_low = max(temperature_low, self._min_temp)
            if self.hvac_mode == HVACMode.HEAT_COOL:
                temperature_low = min(temperature_low, self._target_cool - self._heatcool_setpoint_delta)
            else:
                temperature_low = min(temperature_low, self._max_temp)

            if self._target_temp != temperature_low:
                self._client.set_temperature(self._id, temperature_low)
                self._target_temp = temperature_low

        if temperature_high is not None:
            temperature_high = min(temperature_high, self._cool_max)
            if self.hvac_mode == HVACMode.HEAT_COOL:
                temperature_high = max(temperature_high, self._target_temp + self._heatcool_setpoint_delta)
            else:
                temperature_high = max(temperature_high, self._cool_min)

            if self._target_cool != temperature_high:
                self._client.set_cool_temperature(self._id, temperature_high)
                self._target_cool = temperature_high

    def set_min_time_on(self, value):
        """Set minimum time the device is on before letting be off again (run-on time)"""
        heat_min_time_on = value.get(ATTR_HEAT_MIN_TIME_ON)
        cool_min_time_on = value.get(ATTR_COOL_MIN_TIME_ON)
        aux_heat_min_time_on = value.get(ATTR_AUX_HEAT_MIN_TIME_ON)
        air_ex_min_time_on = value.get(ATTR_AIR_EX_MIN_TIME_ON)

        if heat_min_time_on is not None:
            self._client.set_heat_min_time_on(self.unique_id, heat_min_time_on)
            self._heat_min_time_on = heat_min_time_on
        if cool_min_time_on is not None:
            self._client.set_cool_min_time_on(self.unique_id, cool_min_time_on)
            self._cool_min_time_on = cool_min_time_on
        if aux_heat_min_time_on is not None:
            self._client.set_aux_heat_min_time_on(self.unique_id, aux_heat_min_time_on)
            self._aux_heat_min_time_on = aux_heat_min_time_on
        if air_ex_min_time_on is not None:
            self._client.set_air_ex_min_time_on(self.unique_id, air_ex_min_time_on)
            self._air_ex_min_time_on = air_ex_min_time_on

    def set_reversing_valve_polarity(self, value):
        """Set minimum time the device is on before letting be off again (run-on time)"""
        polarity = value[ATTR_POLARITY]
        self._client.set_reversing_valve_polarity(self.unique_id, polarity)
        self._reversing_valve_polarity = polarity

    def set_min_time_off(self, value):
        """Set minimum time the device is off before letting it be on again (cooldown time)"""
        heat_min_time_off = value.get(ATTR_HEAT_MIN_TIME_OFF)
        cool_min_time_off = value.get(ATTR_COOL_MIN_TIME_OFF)
        aux_heat_min_time_off = value.get(ATTR_AUX_HEAT_MIN_TIME_OFF)

        if heat_min_time_off is not None:
            self._client.set_heat_min_time_off(self.unique_id, heat_min_time_off)
            self._heat_min_time_off = heat_min_time_off
        if cool_min_time_off is not None:
            self._client.set_cool_min_time_off(self.unique_id, cool_min_time_off)
            self._cool_min_time_off = cool_min_time_off
        if aux_heat_min_time_off is not None:
            self._client.set_aux_heat_min_time_off(self.unique_id, aux_heat_min_time_off)
            self._aux_heat_min_time_off = aux_heat_min_time_off

    def set_heat_interstage_delay(self, value):
        try:
            time_val = int(value[ATTR_TIME])
        except KeyError:
            raise ServiceValidationError(f"Missing required parameter: {ATTR_TIME}")
        except ValueError:
            raise ServiceValidationError(f"Invalid value for {ATTR_TIME}, must be an integer")

        outputs = self._output_connect_state
        hp_can_heat = self._reversing_valve_polarity == "cooling" or outputs["OB"]
        has_multiple_hp_heat_stages = outputs["Y1"] and outputs["Y2"] and hp_can_heat
        has_multiple_aux_stages = outputs["W"] and outputs["W2"]
        if not has_multiple_hp_heat_stages and not has_multiple_aux_stages:
            raise ServiceValidationError(
                f"Entity {self.entity_id} does not support multiple levels of heating with current configuration"
            )

        if has_multiple_hp_heat_stages:
            self._client.set_heat_interstage_min_delay(self.unique_id, time_val * 60)
            self._client.set_heat_interstage_delay(self.unique_id, time_val * 60 * 2)
        if has_multiple_aux_stages:
            self._client.set_aux_interstage_min_delay(self.unique_id, time_val * 60)
            self._client.set_aux_interstage_delay(self.unique_id, time_val * 60 * 2)

    def set_cool_interstage_delay(self, value):
        try:
            time_val = int(value[ATTR_TIME])
        except KeyError:
            raise ServiceValidationError(f"Missing required parameter: {ATTR_TIME}")
        except ValueError:
            raise ServiceValidationError(f"Invalid value for {ATTR_TIME}, must be an integer")

        outputs = self._output_connect_state
        hp_can_cool = self._reversing_valve_polarity == "heating" or outputs["OB"]
        has_multiple_cooling_stages = outputs["Y1"] and outputs["Y2"] and hp_can_cool
        if not has_multiple_cooling_stages:
            raise ServiceValidationError(
                f"Entity {self.entity_id} does not support multiple cooling levels "
                f"with the current output configuration"
            )

        self._client.set_cool_interstage_min_delay(self.unique_id, time_val * 60)
        self._client.set_cool_interstage_delay(self.unique_id, time_val * 60 * 2)

    def set_aux_heating_source(self, value):
        """Set auxiliary heating device."""
        equip = AUX_HEATING.get(value[ATTR_AUX_HEAT_SOURCE_TYPE])
        if equip is None:
            raise ServiceValidationError(
                f"Invalid value for {ATTR_AUX_HEAT_SOURCE_TYPE}, must be one of {AUX_HEATING.keys()}"
            )

        self._client.set_aux_heating_source(value["id"], equip)
        self._aux_heat_source_type = equip

    def set_fan_speed(self, value):
        """Set fan speed On or Auto."""
        self._client.set_fan_mode(value["id"], value["speed"])
        self._fan_speed = value["speed"]

    @override
    def set_humidity(self, humidity: int) -> None:
        """Set new target humidity %."""
        if self._humidity_setpoint_mode == "defog":
            self._client.set_humidity_offset(self._id, humidity, self._is_HC)
            self._humidity_setpoint_offset = humidity
        else:
            self._client.set_humidity(self._id, humidity)
            self._humidity_setpoint = humidity

    def set_accessory_type(self, value):
        """Set accessory (humidifier, dehumidifier, air exchanger) type for TH6500WF."""
        self._client.set_accessory_type(value["id"], value["type"])
        self._accessory_type = value["type"]

    def set_schedule_mode(self, value):
        """Set schedule mode, manual or auto."""
        self._client.set_schedule_mode(value["id"], value["mode"], self._is_HC)
        self._operation_mode = value["mode"]

    def set_heatcool_setpoint_delta(self, value):
        """Set delta temperature between heating and cooling setpoint from 1 to 5°C."""
        self._client.set_heatcool_delta(value["id"], value["level"], self._is_HC)
        self._heatcool_setpoint_delta = value["level"]

    def set_cool_setpoint_away(self, value):
        """Set device away cooling setpoint."""
        self._client.set_cool_setpoint_away(value["id"], value["temp"], self._is_HC)
        self._cool_target_temp_away = value["temp"]

    def set_cool_dissipation_time(self, value):
        """Set device cool dissipation time."""
        self._client.set_cool_dissipation_time(value["id"], value[ATTR_TIME], self._is_HC)
        self._heat_purge_time = value[ATTR_TIME]

    def set_heat_dissipation_time(self, value):
        """Set device heat dissipation time."""
        self._client.set_heat_dissipation_time(value["id"], value[ATTR_TIME], self._is_HC)
        self._cool_purge_time = value[ATTR_TIME]

    def set_fan_filter_reminder(self, value):
        """Set fan filter reminder period from 1 to 12 month."""
        self._client.set_fan_filter_reminder(value["id"], value["month"], self._is_HC)
        self._fan_filter_remain = value["month"]

    def set_temperature_offset(self, value):
        """Set thermostat sensor offset from -2 to 2°C with a 0.5°C increment."""
        self._client.set_temperature_offset(value["id"], value["temp"], self._is_HC)
        self._temp_offset_heat = value["temp"]

    def set_humidity_mode(self, value):
        """Set thermostat humidity setpoint mode, defog or manual"""
        self._client.set_humidity_mode(value["id"], value["mode"], self._is_HC)
        self._humidity_setpoint_mode = value["mode"]

    def set_hvac_dr_options(self, value):
        """Set thermostat DR options for Eco Sinope."""
        aux_conf = value.get(ATTR_AUX_OPTIM)
        fan_speed_config = value.get(ATTR_FAN_SPEED_OPTIM)
        if aux_conf is None and fan_speed_config is None:
            raise ServiceValidationError(
                f"Missing required parameter: either {ATTR_AUX_OPTIM} or {ATTR_FAN_SPEED_OPTIM} must be set"
            )
        self._client.set_hvac_dr_options(value["id"], aux_conf=aux_conf, fan_speed_conf=fan_speed_config)
        if aux_conf is not None:
            self._dr_aux_config = "activated" if aux_conf == "on" else "deactivated"
        if fan_speed_config is not None:
            # Not a typo: Disabled is really sending "on" (allow fan to be always on when the optim is disabled)
            self._dr_fan_speed_conf = "auto" if fan_speed_config == "on" else "on"

    @property
    @override
    def extra_state_attributes(self) -> Mapping[str, Any]:
        """Return the state attributes."""
        data = {}
        data.update(
            {
                "neviweb_occupancy_mode": self._occupancy_mode,
                "error_code": self._error_code,
                "operation_modes": self._operation_mode,
                "cool_setpoint": self._target_cool,
                "cool_setpoint_min": self._cool_min,
                "cool_setpoint_max": self._cool_max,
                "setpoint_max": self._max_temp,
                "setpoint_min": self._min_temp,
                "temperature_format": self._temperature_format,
                "time_format": self._time_format,
                "keypad": lock_to_ha(self._keypad),
                "fan_speed": self._fan_speed,
                "backlight": self._backlight,
                "backlight_auto_dim": self._backlight_auto_dim,
                "early_start": self._early_start,
                "target_temp_away": self._target_temp_away,
                "cool_target_temp_away": self._cool_target_temp_away,
                "heat_cool_setpoint_delta": self._heatcool_setpoint_delta,
                "language": self._language,
                "occupancy": self._occupancy,
                "heat_source_type": self._heat_source_type,
                "heat_level": self._heat_level,
                "heat_level_source_type": self._heat_level_source_type,
                "aux_heat_source_type": self._aux_heat_source_type,
                "fan_filter_remain": self._fan_filter_remain,
                "fan_filter_life": self._fan_filter_life,
                "sensor_temp_offset": self._temp_offset_heat,
                "cycle": self._cycle,
                "aux_cycle": self._aux_cycle,
                "cool_cycle_length": neviweb_to_ha(self._cool_cycle_length),
                "humidity_display": self._humidity_display,
                "humidity_setpoint": self._humidity_setpoint,
                "accessory_type": self._accessory_type,
                "heat_cool": self._heat_cool,
                "temp_offset_heat": self._temp_offset_heat,
                "cool_min_time_on": self._cool_min_time_on,
                "cool_min_time_off": self._cool_min_time_off,
                "heat_installation_type": self._heat_inst_type,
                "aux_heat_min_time_on": self._aux_heat_min_time_on,
                "aux_heat_start_delay": self._aux_heat_start_delay,
                "reversing_valve_polarity": self._reversing_valve_polarity,
                "temp_display_status": self._temp_display_status,
                "temp_display_value": self._temp_display_value,
                "dual_status": self._dual_status,
                "balance_point": self._balance_pt,
                "heat_lock_temp": self._heat_lock_temp,
                "cool_lock_temp": self._cool_lock_temp,
                "output_connect_state": self._output_connect_state,
                "outdoor_temp": self._temperature,
                "weather_icon": self._weather_icon,
                "rssi": self._rssi,
                "sku": self._sku,
                "device_model": str(self._device_model),
                "device_model_cfg": self._device_model_cfg,
                "firmware": self._firmware,
                "activation": self._active,
                "id": self._id,
            }
        )
        if self._device_model == 6727:
            data.update(
                {
                    "heat_interstage_min_delay": self._aux_interstage_min_delay,
                    "aux_interstage_min_delay": self._aux_interstage_min_delay,
                    "heat_interstage_delay": self._heat_interstage_delay,
                    "aux_interstage_delay": self._aux_interstage_delay,
                    "cool_interstage_min_delay": self._cool_interstage_min_delay,
                    "cool_interstage_delay": self._cool_interstage_delay,
                    "eco_status": self._drstatus_active,
                    "eco_optout": self._drstatus_optout,
                    "eco_setpoint": self._drstatus_setpoint,
                    "eco_power_relative": self._drstatus_rel,
                    "eco_power_absolute": self._drstatus_abs,
                    "eco_setpoint_status": self._drsetpoint_status,
                    "eco_setpoint_delta": self._drsetpoint_value,
                }
            )
        if self._firmware == "4.2.1" or self._firmware == "4.3.0":
            data.update(
                {
                    "humidity_setpoint_offset": self._humidity_setpoint_offset,
                    "humidity_setpoint_mode": self._humidity_setpoint_mode,
                    "exchanger_min_time_on": self._air_min_time_on,
                    "heatcool_lock_cool_status": self._heatcool_lock_cool_status,
                    "heatcool_lock_heat_status": self._heatcool_lock_heat_status,
                    "heatcool_lock_balancePoint_status": self._heatcool_lock_balance_point_status,
                    "dr_aux_config": self._dr_aux_config,
                    "dr_fan_speed_conf": self._dr_fan_speed_conf,
                    "dr_accessory_conf": self._dr_accessory_conf,
                    "dr_air_curtain_conf": self._dr_air_curt_conf,
                    "heat_purge_time": self._heat_purge_time,
                    "cool_purge_time": self._cool_purge_time,
                    "air_curtain_conf": self._air_curt_conf,
                    "air_curtain_activation_temp": self._air_curt_activation_temp,
                    "air_curtain_max_temp": self._air_curt_max_temp,
                    "aux_heat_min_time_off": self._aux_heat_min_time_off,
                    "heat_min_time_on": self._heat_min_time_on,
                    "heat_min_time_off": self._heat_min_time_off,
                }
            )
        if self._firmware == "4.3.0":
            data.update(
                {
                    "interlock_id": self._interlock_id,
                }
            )
        return data
