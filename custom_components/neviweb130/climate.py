"""
Support for Neviweb thermostat connected to GT130 ZigBee.
model 1123 = thermostat TH1123ZB 3000W
model 300 = thermostat TH1123ZB-G2 3000W
model 1124 = thermostat TH1124ZB 4000W
model 300 = thermostat TH1124ZB-G2 4000W
model 737 = thermostat TH1300ZB 3600W (floor)
model 737 = thermostat TH1320ZB-04 (floor)
model 7373 = thermostat TH1500ZB double pole thermostat
model 7372 = thermostat TH1400ZB low voltage
model 7372 = thermostat TH1420ZB-01 Nordik low voltage radiant hydroponic
             floor thermostat
model 1124 = thermostat OTH4000-ZB Ouellet
model 737 = thermostat OTH3600-GA-ZB Ouellet
model 1512 = Thermostat TH1134ZB-HC for heating/cooling interlocking

Support for Neviweb wifi thermostats
model 1510 = thermostat TH1123WF 3000W (wifi)
model 1510 = thermostat TH1124WF 4000W (wifi)
model 336 = thermostat TH1133WF 3000W (wifi lite)
model 336 = thermostat TH1133CR Sinopé Evo 3000W (wifi lite)
model 336 = thermostat TH1134WF 3000W (wifi lite)
model 336 = thermostat TH1134CR Sinopé Evo 3000W (wifi lite)
model 738 = thermostat TH1300WF 3600W, TH1325WF, TH1310WF, SRM40, True Comfort
            (wifi floor)
model 739 = thermostat TH1400WF low voltage (wifi)
model 742 = thermostat TH1500WF double pole thermostat (wifi)
model 6727 = thermostat TH6500WF heat/cool (wifi)
model 6727 = thermostat TH6510WF heat/cool (wifi)
model 6730 = thermostat TH6250WF heat/cool (wifi)
model 6730 = thermostat TH6250WF-PRO keat/cool (wifi)

Support for Flextherm wifi thermostat
model 738 = Thermostat Flextherm concerto connect FLP55 (wifi floor),
            (sku: FLP55), no energy stats

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

from homeassistant.components.climate import (ClimateEntity,
                                              ClimateEntityFeature, HVACAction,
                                              HVACMode)
from homeassistant.components.climate.const import (PRESET_AWAY, PRESET_HOME,
                                                    PRESET_NONE)
from homeassistant.components.persistent_notification import \
    DOMAIN as PN_DOMAIN
from homeassistant.components.sensor import SensorDeviceClass
from homeassistant.const import (ATTR_ENTITY_ID, ATTR_TEMPERATURE,
                                 UnitOfTemperature)

from . import HOMEKIT_MODE, NOTIFY
from . import SCAN_INTERVAL as scan_interval
from . import STAT_INTERVAL
from .const import (ATTR_ACTIVE, ATTR_AUX_CYCLE, ATTR_AUX_HEAT_SOURCE_TYPE,
                    ATTR_AUX_HEAT_START_DELAY, ATTR_AUX_HEAT_TIMEON,
                    ATTR_AVAIL_MODE, ATTR_BACK_LIGHT, ATTR_BACKLIGHT,
                    ATTR_BACKLIGHT_AUTO_DIM, ATTR_BALANCE_PT,
                    ATTR_BALANCE_PT_TEMP_HIGH, ATTR_BALANCE_PT_TEMP_LOW,
                    ATTR_COLD_LOAD_PICKUP, ATTR_COOL_CYCLE_LENGTH,
                    ATTR_COOL_INTERSTAGE_MIN_DELAY, ATTR_COOL_LOCK_TEMP,
                    ATTR_COOL_MIN_TIME_OFF, ATTR_COOL_MIN_TIME_ON,
                    ATTR_COOL_SETPOINT, ATTR_COOL_SETPOINT_AWAY,
                    ATTR_COOL_SETPOINT_MAX, ATTR_COOL_SETPOINT_MIN, ATTR_CYCLE,
                    ATTR_CYCLE_OUTPUT2, ATTR_DISPLAY2, ATTR_DISPLAY_CAP,
                    ATTR_DISPLAY_CONF, ATTR_DRACTIVE, ATTR_DRSETPOINT,
                    ATTR_DRSTATUS, ATTR_DUAL_STATUS, ATTR_EARLY_START,
                    ATTR_FAN_CAP, ATTR_FAN_FILTER_REMAIN, ATTR_FAN_SPEED,
                    ATTR_FAN_SWING_CAP, ATTR_FAN_SWING_CAP_HORIZ,
                    ATTR_FAN_SWING_CAP_VERT, ATTR_FAN_SWING_HORIZ,
                    ATTR_FAN_SWING_VERT, ATTR_FLOOR_AIR_LIMIT, ATTR_FLOOR_AUX,
                    ATTR_FLOOR_MAX, ATTR_FLOOR_MIN, ATTR_FLOOR_MODE,
                    ATTR_FLOOR_OUTPUT1, ATTR_FLOOR_OUTPUT2, ATTR_FLOOR_SENSOR,
                    ATTR_GFCI_ALERT, ATTR_GFCI_STATUS, ATTR_HC_DEV,
                    ATTR_HEAT_COOL, ATTR_HEAT_INSTALL_TYPE,
                    ATTR_HEAT_INTERSTAGE_MIN_DELAY, ATTR_HEAT_LOCK_TEMP,
                    ATTR_HEAT_LOCKOUT_TEMP, ATTR_HEAT_SOURCE_TYPE,
                    ATTR_HEATCOOL_SETPOINT_MIN_DELTA, ATTR_HUMID_DISPLAY,
                    ATTR_HUMID_SETPOINT, ATTR_HUMIDIFIER_TYPE, ATTR_KEYPAD,
                    ATTR_LANGUAGE, ATTR_MODEL, ATTR_OCCUPANCY, ATTR_OPTOUT,
                    ATTR_OUTPUT1, ATTR_OUTPUT_CONNECT_STATE,
                    ATTR_OUTPUT_PERCENT_DISPLAY, ATTR_PUMP_PROTEC,
                    ATTR_PUMP_PROTEC_DURATION, ATTR_PUMP_PROTEC_PERIOD,
                    ATTR_ROOM_SETPOINT, ATTR_ROOM_SETPOINT_AWAY,
                    ATTR_ROOM_SETPOINT_MAX, ATTR_ROOM_SETPOINT_MIN,
                    ATTR_ROOM_TEMP_DISPLAY, ATTR_ROOM_TEMPERATURE, ATTR_RSSI,
                    ATTR_SETPOINT, ATTR_SETPOINT_MODE, ATTR_SOUND_CAP,
                    ATTR_SOUND_CONF, ATTR_STATUS, ATTR_SYSTEM_MODE, ATTR_TEMP,
                    ATTR_TEMP_OFFSET_HEAT, ATTR_TIME, ATTR_TYPE, ATTR_VALUE,
                    ATTR_VALVE_POLARITY, ATTR_WATTAGE, ATTR_WIFI,
                    ATTR_WIFI_KEYPAD, ATTR_WIFI_WATTAGE, DOMAIN, MODE_AUTO,
                    MODE_AUTO_BYPASS, MODE_EM_HEAT, MODE_MANUAL,
                    SERVICE_SET_ACTIVATION, SERVICE_SET_AIR_FLOOR_MODE,
                    SERVICE_SET_AUX_CYCLE_OUTPUT,
                    SERVICE_SET_AUX_HEAT_MIN_TIME_ON,
                    SERVICE_SET_AUXILIARY_LOAD, SERVICE_SET_BACKLIGHT,
                    SERVICE_SET_CLIMATE_KEYPAD_LOCK,
                    SERVICE_SET_COOL_LOCKOUT_TEMPERATURE,
                    SERVICE_SET_COOL_MIN_TIME_OFF,
                    SERVICE_SET_COOL_MIN_TIME_ON,
                    SERVICE_SET_COOL_SETPOINT_MAX,
                    SERVICE_SET_COOL_SETPOINT_MIN, SERVICE_SET_CYCLE_OUTPUT,
                    SERVICE_SET_DISPLAY_CONFIG, SERVICE_SET_EARLY_START,
                    SERVICE_SET_EM_HEAT, SERVICE_SET_FLOOR_AIR_LIMIT,
                    SERVICE_SET_FLOOR_LIMIT_HIGH, SERVICE_SET_FLOOR_LIMIT_LOW,
                    SERVICE_SET_HC_SECOND_DISPLAY,
                    SERVICE_SET_HEAT_LOCKOUT_TEMPERATURE,
                    SERVICE_SET_HEAT_PUMP_OPERATION_LIMIT,
                    SERVICE_SET_HVAC_DR_OPTIONS, SERVICE_SET_HVAC_DR_SETPOINT,
                    SERVICE_SET_LANGUAGE, SERVICE_SET_PUMP_PROTECTION,
                    SERVICE_SET_SECOND_DISPLAY, SERVICE_SET_SENSOR_TYPE,
                    SERVICE_SET_SETPOINT_MAX, SERVICE_SET_SETPOINT_MIN,
                    SERVICE_SET_SOUND_CONFIG, SERVICE_SET_TEMPERATURE_FORMAT,
                    SERVICE_SET_TIME_FORMAT)
from .schema import (FAN_SPEED, FULL_SWING, FULL_SWING_OFF,
                     SET_ACTIVATION_SCHEMA, SET_AIR_FLOOR_MODE_SCHEMA,
                     SET_AUX_CYCLE_OUTPUT_SCHEMA,
                     SET_AUX_HEAT_MIN_TIME_ON_SCHEMA,
                     SET_AUXILIARY_LOAD_SCHEMA, SET_BACKLIGHT_SCHEMA,
                     SET_CLIMATE_KEYPAD_LOCK_SCHEMA,
                     SET_COOL_LOCKOUT_TEMPERATURE_SCHEMA,
                     SET_COOL_MIN_TIME_OFF_SCHEMA, SET_COOL_MIN_TIME_ON_SCHEMA,
                     SET_COOL_SETPOINT_MAX_SCHEMA,
                     SET_COOL_SETPOINT_MIN_SCHEMA, SET_CYCLE_OUTPUT_SCHEMA,
                     SET_DISPLAY_CONFIG_SCHEMA, SET_EARLY_START_SCHEMA,
                     SET_EM_HEAT_SCHEMA, SET_FLOOR_AIR_LIMIT_SCHEMA,
                     SET_FLOOR_LIMIT_HIGH_SCHEMA, SET_FLOOR_LIMIT_LOW_SCHEMA,
                     SET_HC_SECOND_DISPLAY_SCHEMA,
                     SET_HEAT_LOCKOUT_TEMPERATURE_SCHEMA,
                     SET_HEAT_PUMP_OPERATION_LIMIT_SCHEMA,
                     SET_HVAC_DR_OPTIONS_SCHEMA, SET_HVAC_DR_SETPOINT_SCHEMA,
                     SET_LANGUAGE_SCHEMA, SET_PUMP_PROTECTION_SCHEMA,
                     SET_SECOND_DISPLAY_SCHEMA, SET_SENSOR_TYPE_SCHEMA,
                     SET_SETPOINT_MAX_SCHEMA, SET_SETPOINT_MIN_SCHEMA,
                     SET_SOUND_CONFIG_SCHEMA, SET_TEMPERATURE_FORMAT_SCHEMA,
                     SET_TIME_FORMAT_SCHEMA, VERSION, WIFI_FAN_SPEED)

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

SUPPORT_Hc_FLAGS = (
    ClimateEntityFeature.TARGET_TEMPERATURE
    | ClimateEntityFeature.PRESET_MODE
    | ClimateEntityFeature.FAN_MODE
    | ClimateEntityFeature.SWING_MODE
    | ClimateEntityFeature.TURN_OFF
    | ClimateEntityFeature.TURN_ON
)

SUPPORT_HC_FLAGS = (
    ClimateEntityFeature.TARGET_TEMPERATURE
    | ClimateEntityFeature.PRESET_MODE
    | ClimateEntityFeature.FAN_MODE
    | ClimateEntityFeature.TURN_OFF
    | ClimateEntityFeature.TURN_ON
)

DEFAULT_NAME = "neviweb130 climate"
DEFAULT_NAME_2 = "neviweb130 climate 2"
DEFAULT_NAME_3 = "neviweb130 climate 3"
SNOOZE_TIME = 1200
SCAN_INTERVAL = scan_interval

HA_TO_NEVIWEB_PERIOD = {
    "15 sec": 15,
    "5 min": 300,
    "10 min": 600,
    "15 min": 900,
    "20 min": 1200,
    "25 min": 1500,
    "30 min": 1800,
}

UPDATE_ATTRIBUTES = [
    ATTR_DRSETPOINT,
    ATTR_DRSTATUS,
    ATTR_OUTPUT_PERCENT_DISPLAY,
    ATTR_ROOM_SETPOINT,
    ATTR_ROOM_SETPOINT_MAX,
    ATTR_ROOM_SETPOINT_MIN,
    ATTR_ROOM_TEMPERATURE,
    ATTR_TEMP,
    ATTR_TIME,
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
    ATTR_TIME,
]

SUPPORTED_HVAC_WIFI_MODES = [
    HVACMode.AUTO,
    HVACMode.HEAT,
    HVACMode.OFF,
]

SUPPORTED_HVAC_WIFI_LITE_MODES = [
    HVACMode.AUTO,
    MODE_MANUAL,
    HVACMode.OFF,
]

SUPPORTED_HVAC_MODES = [
    HVACMode.HEAT,
    HVACMode.OFF,
]

SUPPORTED_HVAC_H_C_MODES = [
    HVACMode.COOL,
    HVACMode.HEAT,
    HVACMode.OFF,
]

SUPPORTED_HVAC_HC_MODES = [
    HVACMode.COOL,
    HVACMode.HEAT,
    HVACMode.OFF,
    MODE_AUTO,
    MODE_EM_HEAT,
]

SUPPORTED_HVAC_HP_MODES = [
    HVACMode.COOL,
    HVACMode.DRY,
    HVACMode.FAN_ONLY,
    HVACMode.HEAT,
    HVACMode.OFF,
]

SUPPORTED_HVAC_HEAT_MODES = [
    HVACMode.FAN_ONLY,
    HVACMode.HEAT,
    HVACMode.OFF,
]

SUPPORTED_HVAC_COOL_MODES = [
    HVACMode.COOL,
    HVACMode.DRY,
    HVACMode.FAN_ONLY,
    HVACMode.OFF,
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

PRESET_HP_MODES = [
    PRESET_AWAY,
    PRESET_HOME,
    PRESET_NONE,
]

PRESET_HC_MODES = [
    PRESET_AWAY,
    PRESET_NONE,
]

DEVICE_MODEL_LOW = [7372]
DEVICE_MODEL_LOW_WIFI = [739]
DEVICE_MODEL_FLOOR = [737]
DEVICE_MODEL_WIFI_FLOOR = [738]
DEVICE_MODEL_WIFI = [1510, 742]
DEVICE_MODEL_WIFI_LITE = [336]
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
)


async def async_setup_platform(
    hass,
    config,
    async_add_entities,
    discovery_info=None,
) -> None:
    """Set up the neviweb130 thermostats."""
    data = hass.data[DOMAIN]

    entities = []
    for device_info in data.neviweb130_client.gateway_data:
        if (
            "signature" in device_info
            and "model" in device_info["signature"]
            and device_info["signature"]["model"] in IMPLEMENTED_DEVICE_MODEL
        ):
            device_name = "{} {}".format(DEFAULT_NAME, device_info["name"])
            device_sku = device_info["sku"]
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
                    )
                )

    async_add_entities(entities, True)

    def set_second_display_service(service):
        """Set to outside or setpoint temperature display for wifi thermostats."""
        entity_id = service.data[ATTR_ENTITY_ID]
        value = {}
        for thermostat in entities:
            if thermostat.entity_id == entity_id:
                value = {
                    "id": thermostat.unique_id,
                    "display": service.data[ATTR_DISPLAY2],
                }
                thermostat.set_second_display(value)
                thermostat.schedule_update_ha_state(True)
                break

    def set_backlight_service(service):
        """Set backlight always on or auto."""
        entity_id = service.data[ATTR_ENTITY_ID]
        value = {}
        for thermostat in entities:
            if thermostat.entity_id == entity_id:
                value = {
                    "id": thermostat.unique_id,
                    "type": service.data[ATTR_TYPE],
                    "level": service.data[ATTR_BACKLIGHT],
                }
                thermostat.set_backlight(value)
                thermostat.schedule_update_ha_state(True)
                break

    def set_climate_keypad_lock_service(service):
        """Lock/unlock keypad device."""
        entity_id = service.data[ATTR_ENTITY_ID]
        value = {}
        for thermostat in entities:
            if thermostat.entity_id == entity_id:
                value = {
                    "id": thermostat.unique_id,
                    "lock": service.data[ATTR_KEYPAD],
                }
                thermostat.set_keypad_lock(value)
                thermostat.schedule_update_ha_state(True)
                break

    def set_time_format_service(service):
        """Set time format 12h or 24h."""
        entity_id = service.data[ATTR_ENTITY_ID]
        value = {}
        for thermostat in entities:
            if thermostat.entity_id == entity_id:
                value = {
                    "id": thermostat.unique_id,
                    "time": service.data[ATTR_TIME],
                }
                thermostat.set_time_format(value)
                thermostat.schedule_update_ha_state(True)
                break

    def set_temperature_format_service(service):
        """Set temperature format, celsius or fahrenheit."""
        entity_id = service.data[ATTR_ENTITY_ID]
        value = {}
        for thermostat in entities:
            if thermostat.entity_id == entity_id:
                value = {
                    "id": thermostat.unique_id,
                    "temp": service.data[ATTR_TEMP],
                }
                thermostat.set_temperature_format(value)
                thermostat.schedule_update_ha_state(True)
                break

    def set_setpoint_max_service(service):
        """Set maximum setpoint for device."""
        entity_id = service.data[ATTR_ENTITY_ID]
        value = {}
        for thermostat in entities:
            if thermostat.entity_id == entity_id:
                value = {
                    "id": thermostat.unique_id,
                    "temp": service.data[ATTR_ROOM_SETPOINT_MAX],
                }
                thermostat.set_setpoint_max(value)
                thermostat.schedule_update_ha_state(True)
                break

    def set_setpoint_min_service(service):
        """Set minimum setpoint for device."""
        entity_id = service.data[ATTR_ENTITY_ID]
        value = {}
        for thermostat in entities:
            if thermostat.entity_id == entity_id:
                value = {
                    "id": thermostat.unique_id,
                    "temp": service.data[ATTR_ROOM_SETPOINT_MIN],
                }
                thermostat.set_setpoint_min(value)
                thermostat.schedule_update_ha_state(True)
                break

    def set_floor_air_limit_service(service):
        """Set minimum setpoint for device."""
        entity_id = service.data[ATTR_ENTITY_ID]
        value = {}
        for thermostat in entities:
            if thermostat.entity_id == entity_id:
                value = {
                    "id": thermostat.unique_id,
                    "temp": service.data[ATTR_FLOOR_AIR_LIMIT],
                }
                thermostat.set_floor_air_limit(value)
                thermostat.schedule_update_ha_state(True)
                break

    def set_early_start_service(service):
        """Set early heating on/off for wifi thermostat."""
        entity_id = service.data[ATTR_ENTITY_ID]
        value = {}
        for thermostat in entities:
            if thermostat.entity_id == entity_id:
                value = {
                    "id": thermostat.unique_id,
                    "start": service.data[ATTR_EARLY_START],
                }
                thermostat.set_early_start(value)
                thermostat.schedule_update_ha_state(True)
                break

    def set_air_floor_mode_service(service):
        """Switch between ambiant or floor temperature sensor."""
        entity_id = service.data[ATTR_ENTITY_ID]
        value = {}
        for thermostat in entities:
            if thermostat.entity_id == entity_id:
                value = {
                    "id": thermostat.unique_id,
                    "mode": service.data[ATTR_FLOOR_MODE],
                }
                thermostat.set_air_floor_mode(value)
                thermostat.schedule_update_ha_state(True)
                break

    def set_hvac_dr_options_service(service):
        """Set options for hvac dr in Eco Sinope."""
        entity_id = service.data[ATTR_ENTITY_ID]
        value = {}
        for thermostat in entities:
            if thermostat.entity_id == entity_id:
                value = {
                    "id": thermostat.unique_id,
                    "dractive": service.data[ATTR_DRACTIVE],
                    "optout": service.data[ATTR_OPTOUT],
                    "setpoint": service.data[ATTR_SETPOINT],
                }
                thermostat.set_hvac_dr_options(value)
                thermostat.schedule_update_ha_state(True)
                break

    def set_hvac_dr_setpoint_service(service):
        """Set options for hvac dr setpoint in Eco Sinope."""
        entity_id = service.data[ATTR_ENTITY_ID]
        value = {}
        for thermostat in entities:
            if thermostat.entity_id == entity_id:
                value = {
                    "id": thermostat.unique_id,
                    "status": service.data[ATTR_STATUS],
                    "val": service.data[ATTR_VALUE],
                }
                thermostat.set_hvac_dr_setpoint(value)
                thermostat.schedule_update_ha_state(True)
                break

    def set_auxiliary_load_service(service):
        """Set options for auxilary heating."""
        entity_id = service.data[ATTR_ENTITY_ID]
        value = {}
        for thermostat in entities:
            if thermostat.entity_id == entity_id:
                value = {
                    "id": thermostat.unique_id,
                    "status": service.data[ATTR_STATUS],
                    "val": service.data[ATTR_VALUE],
                }
                thermostat.set_auxiliary_load(value)
                thermostat.schedule_update_ha_state(True)
                break

    def set_aux_cycle_output_service(service):
        """Set options for auxilary cycle length for low voltage thermostats."""
        entity_id = service.data[ATTR_ENTITY_ID]
        value = {}
        for thermostat in entities:
            if thermostat.entity_id == entity_id:
                value = {
                    "id": thermostat.unique_id,
                    "status": service.data[ATTR_STATUS],
                    "val": service.data[ATTR_VALUE][0],
                }
                thermostat.set_aux_cycle_output(value)
                thermostat.schedule_update_ha_state(True)
                break

    def set_cycle_output_service(service):
        """Set options for main cycle length for low voltage thermostats."""
        entity_id = service.data[ATTR_ENTITY_ID]
        value = {}
        for thermostat in entities:
            if thermostat.entity_id == entity_id:
                value = {
                    "id": thermostat.unique_id,
                    "val": service.data[ATTR_VALUE][0],
                }
                thermostat.set_cycle_output(value)
                thermostat.schedule_update_ha_state(True)
                break

    def set_pump_protection_service(service):
        """Set status of pump protection for low voltage thermostats."""
        entity_id = service.data[ATTR_ENTITY_ID]
        value = {}
        for thermostat in entities:
            if thermostat.entity_id == entity_id:
                value = {
                    "id": thermostat.unique_id,
                    "status": service.data[ATTR_STATUS],
                }
                thermostat.set_pump_protection(value)
                thermostat.schedule_update_ha_state(True)
                break

    def set_cool_setpoint_max_service(service):
        """Set maximum cooling setpoint for device."""
        entity_id = service.data[ATTR_ENTITY_ID]
        value = {}
        for thermostat in entities:
            if thermostat.entity_id == entity_id:
                value = {
                    "id": thermostat.unique_id,
                    "temp": service.data[ATTR_COOL_SETPOINT_MAX],
                }
                thermostat.set_cool_setpoint_max(value)
                thermostat.schedule_update_ha_state(True)
                break

    def set_cool_setpoint_min_service(service):
        """Set minimum cooling setpoint for device."""
        entity_id = service.data[ATTR_ENTITY_ID]
        value = {}
        for thermostat in entities:
            if thermostat.entity_id == entity_id:
                value = {
                    "id": thermostat.unique_id,
                    "temp": service.data[ATTR_COOL_SETPOINT_MIN],
                }
                thermostat.set_cool_setpoint_min(value)
                thermostat.schedule_update_ha_state(True)
                break

    def set_floor_limit_high_service(service):
        """Set maximum floor heating limit for floor device."""
        entity_id = service.data[ATTR_ENTITY_ID]
        value = {}
        for thermostat in entities:
            if thermostat.entity_id == entity_id:
                value = {
                    "id": thermostat.unique_id,
                    "level": service.data[ATTR_FLOOR_MAX],
                    "limit": "high",
                }
                thermostat.set_floor_limit(value)
                thermostat.schedule_update_ha_state(True)
                break

    def set_floor_limit_low_service(service):
        """Set minimum floor heating limit for floor device."""
        entity_id = service.data[ATTR_ENTITY_ID]
        value = {}
        for thermostat in entities:
            if thermostat.entity_id == entity_id:
                value = {
                    "id": thermostat.unique_id,
                    "level": service.data[ATTR_FLOOR_MIN],
                    "limit": "low",
                }
                thermostat.set_floor_limit(value)
                thermostat.schedule_update_ha_state(True)
                break

    def set_activation_service(service):
        """Activate or deactivate Neviweb polling for missing device."""
        entity_id = service.data[ATTR_ENTITY_ID]
        value = {}
        for thermostat in entities:
            if thermostat.entity_id == entity_id:
                value = {
                    "id": thermostat.unique_id,
                    "active": service.data[ATTR_ACTIVE],
                }
                thermostat.set_activation(value)
                thermostat.schedule_update_ha_state(True)
                break

    def set_sensor_type_service(service):
        """Set floor sensor type."""
        entity_id = service.data[ATTR_ENTITY_ID]
        value = {}
        for thermostat in entities:
            if thermostat.entity_id == entity_id:
                value = {
                    "id": thermostat.unique_id,
                    "type": service.data[ATTR_FLOOR_SENSOR],
                }
                thermostat.set_sensor_type(value)
                thermostat.schedule_update_ha_state(True)
                break

    def set_em_heat_service(service):
        """Set emergency heat on/off for thermostats."""
        entity_id = service.data[ATTR_ENTITY_ID]
        for thermostat in entities:
            if thermostat.entity_id == entity_id:
                if service.data[ATTR_VALUE] == "on":
                    thermostat.turn_em_heat_on()
                else:
                    thermostat.turn_em_heat_off()
                thermostat.schedule_update_ha_state(True)
                break

    def set_heat_pump_operation_limit_service(service):
        """Set minimum temperature for heat pump device operation."""
        entity_id = service.data[ATTR_ENTITY_ID]
        value = {}
        for thermostat in entities:
            if thermostat.entity_id == entity_id:
                value = {
                    "id": thermostat.unique_id,
                    "temp": service.data[ATTR_BALANCE_PT],
                }
                thermostat.set_heat_pump_operation_limit(value)
                thermostat.schedule_update_ha_state(True)
                break

    def set_heat_lockout_temperature_service(service):
        """Set maximum outside temperature limit to allow heating device operation."""
        entity_id = service.data[ATTR_ENTITY_ID]
        value = {}
        for thermostat in entities:
            if thermostat.entity_id == entity_id:
                value = {
                    "id": thermostat.unique_id,
                    "temp": service.data[ATTR_HEAT_LOCK_TEMP],
                }
                thermostat.set_heat_lockout_temperature(value)
                thermostat.schedule_update_ha_state(True)
                break

    def set_cool_lockout_temperature_service(service):
        """Set minimum outside temperature limit to allow cooling device operation."""
        entity_id = service.data[ATTR_ENTITY_ID]
        value = {}
        for thermostat in entities:
            if thermostat.entity_id == entity_id:
                value = {
                    "id": thermostat.unique_id,
                    "temp": service.data[ATTR_COOL_LOCK_TEMP],
                }
                thermostat.set_cool_lockout_temperature(value)
                thermostat.schedule_update_ha_state(True)
                break

    def set_display_config_service(service):
        """Set display on/off for heat pump."""
        entity_id = service.data[ATTR_ENTITY_ID]
        value = {}
        for thermostat in entities:
            if thermostat.entity_id == entity_id:
                value = {
                    "id": thermostat.unique_id,
                    "display": service.data[ATTR_DISPLAY_CONF],
                }
                thermostat.set_display_config(value)
                thermostat.schedule_update_ha_state(True)
                break

    def set_sound_config_service(service):
        """Set sound on/off for heat pump."""
        entity_id = service.data[ATTR_ENTITY_ID]
        value = {}
        for thermostat in entities:
            if thermostat.entity_id == entity_id:
                value = {
                    "id": thermostat.unique_id,
                    "sound": service.data[ATTR_SOUND_CONF],
                }
                thermostat.set_sound_config(value)
                thermostat.schedule_update_ha_state(True)
                break

    def set_hc_second_display_service(service):
        """Set second display for TH1134ZB-HC thermostat."""
        entity_id = service.data[ATTR_ENTITY_ID]
        value = {}
        for thermostat in entities:
            if thermostat.entity_id == entity_id:
                value = {
                    "id": thermostat.unique_id,
                    "display": service.data[ATTR_DISPLAY2],
                }
                thermostat.set_hc_second_display(value)
                thermostat.schedule_update_ha_state(True)
                break

    def set_language_service(service):
        """Set display language for TH1134ZB-HC thermostat."""
        entity_id = service.data[ATTR_ENTITY_ID]
        value = {}
        for thermostat in entities:
            if thermostat.entity_id == entity_id:
                value = {
                    "id": thermostat.unique_id,
                    "lang": service.data[ATTR_LANGUAGE],
                }
                thermostat.set_language(value)
                thermostat.schedule_update_ha_state(True)
                break

    def set_aux_heat_min_time_on_service(service):
        """Set auxiliary minimum heating time on for TH6500WF and TH6250WF thermostat."""
        entity_id = service.data[ATTR_ENTITY_ID]
        value = {}
        for thermostat in entities:
            if thermostat.entity_id == entity_id:
                value = {
                    "id": thermostat.unique_id,
                    "time": service.data[ATTR_AUX_HEAT_TIMEON],
                }
                thermostat.set_aux_heat_min_time_on(value)
                thermostat.schedule_update_ha_state(True)
                break

    def set_cool_min_time_on_service(service):
        """Set auxiliary minimum heating time on for TH6500WF and TH6250WF thermostat."""
        entity_id = service.data[ATTR_ENTITY_ID]
        value = {}
        for thermostat in entities:
            if thermostat.entity_id == entity_id:
                value = {
                    "id": thermostat.unique_id,
                    "time": service.data[ATTR_COOL_MIN_TIME_ON],
                    "state": "on",
                }
                thermostat.set_cool_min_time(value)
                thermostat.schedule_update_ha_state(True)
                break

    def set_cool_min_time_off_service(service):
        """Set auxiliary minimum heating time on for TH6500WF and TH6250WF thermostat."""
        entity_id = service.data[ATTR_ENTITY_ID]
        value = {}
        for thermostat in entities:
            if thermostat.entity_id == entity_id:
                value = {
                    "id": thermostat.unique_id,
                    "time": service.data[ATTR_COOL_MIN_TIME_OFF],
                    "state": "off",
                }
                thermostat.set_cool_min_time(value)
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
        SERVICE_SET_AUX_HEAT_MIN_TIME_ON,
        set_aux_heat_min_time_on_service,
        schema=SET_AUX_HEAT_MIN_TIME_ON_SCHEMA,
    )

    hass.services.async_register(
        DOMAIN,
        SERVICE_SET_COOL_MIN_TIME_ON,
        set_cool_min_time_on_service,
        schema=SET_COOL_MIN_TIME_ON_SCHEMA,
    )

    hass.services.async_register(
        DOMAIN,
        SERVICE_SET_COOL_MIN_TIME_OFF,
        set_cool_min_time_off_service,
        schema=SET_COOL_MIN_TIME_OFF_SCHEMA,
    )


def neviweb_to_ha(value):
    keys = [k for k, v in HA_TO_NEVIWEB_PERIOD.items() if v == value]
    if keys:
        return keys[0]
    return None


def temp_format_to_ha(value):
    if value == "celsius":
        return UnitOfTemperature.CELSIUS
    else:
        return UnitOfTemperature.FAHRENHEIT


def lock_to_ha(lock):
    """Convert keypad lock state to better description."""
    match lock:
        case "locked":
            return "Locked"
        case "lock":
            return "Locked"
        case "unlocked":
            return "Unlocked"
        case "unlock":
            return "Unlocked"
        case "partiallyLocked":
            return "Tamper protection"
        case "partialLock":
            return "Tamper protection"


def extract_capability_full(cap):
    """Extract swing capability which are True for each HP device and add genegal capability."""
    value = {i for i in cap if cap[i] is True}
    return FULL_SWING_OFF + sorted(value)


def extract_capability(cap):
    """Extract capability which are True for each HP device."""
    value = {i for i in cap if cap[i] is True}
    return sorted(value)


class Neviweb130Thermostat(ClimateEntity):
    """Implementation of Neviweb TH1123ZB, TH1124ZB thermostat."""

    _enable_turn_on_off_backwards_compatibility = False
    _attr_temperature_unit = UnitOfTemperature.CELSIUS
    _attr_precision = 0.1
    _attr_target_temperature_step = 0.5

    def __init__(self, data, device_info, name, sku, firmware):
        """Initialize."""
        self._name = name
        self._sku = sku
        self._firmware = firmware
        self._client = data.neviweb130_client
        self._id = device_info["id"]
        self._device_model = device_info["signature"]["model"]
        self._device_model_cfg = device_info["signature"]["modelCfg"]
        self._hour_kwh = 0
        self._today_kwh = 0
        self._month_kwh = 0
        self._current_hour_kwh = 0
        self._current_today_kwh = 0
        self._current_month_kwh = 0
        self._drstatus_active = "off"
        self._drstatus_optout = "off"
        self._drstatus_setpoint = "off"
        self._drstatus_abs = "off"
        self._drstatus_rel = "off"
        self._drsetpoint_status = "off"
        self._drsetpoint_value = 0
        self._cur_temp = None
        self._cur_temp_before = None
        self._target_temp = None
        self._operation_mode = None
        self._occupancy = None
        self._wattage = 0
        self._min_temp = 5
        self._max_temp = 30
        self._temperature_format = UnitOfTemperature.CELSIUS
        self._time_format = "24h"
        self._temp_display_value = None
        self._display2 = None
        self._heat_level = 0
        self._keypad = None
        self._backlight = None
        self._cycle_length = 0
        self._rssi = None
        self._error_code = None
        self._is_double = device_info["signature"]["model"] in DEVICE_MODEL_DOUBLE
        self._is_hc = device_info["signature"]["model"] in DEVICE_MODEL_HC
        self._is_HC = device_info["signature"]["model"] in DEVICE_MODEL_HEAT_COOL
        self._is_gen2 = device_info["signature"]["model"] in DEVICE_MODEL_HEAT_G2
        self._is_floor = device_info["signature"]["model"] in DEVICE_MODEL_FLOOR
        self._is_wifi_floor = (
            device_info["signature"]["model"] in DEVICE_MODEL_WIFI_FLOOR
        )
        self._is_wifi = (
            device_info["signature"]["model"] in DEVICE_MODEL_WIFI_FLOOR
            or device_info["signature"]["model"] in DEVICE_MODEL_WIFI
            or device_info["signature"]["model"] in DEVICE_MODEL_LOW_WIFI
            or device_info["signature"]["model"] in DEVICE_MODEL_WIFI_LITE
        )
        self._is_wifi_lite = device_info["signature"]["model"] in DEVICE_MODEL_WIFI_LITE
        self._is_low_voltage = device_info["signature"]["model"] in DEVICE_MODEL_LOW
        self._is_low_wifi = device_info["signature"]["model"] in DEVICE_MODEL_LOW_WIFI
        self._is_HP = device_info["signature"]["model"] in DEVICE_MODEL_HEAT_PUMP
        self._energy_stat_time = time.time() - 1500
        self._snooze = 0
        self._activ = True
        _LOGGER.debug("Setting up %s: %s", self._name, device_info)

    def update(self):
        if self._activ:
            HEAT_ATTRIBUTES = [
                ATTR_WATTAGE,
                ATTR_KEYPAD,
                ATTR_BACKLIGHT,
                ATTR_SYSTEM_MODE,
                ATTR_CYCLE,
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
                    self._time_format = device_data[ATTR_TIME]
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
                    if ATTR_CYCLE in device_data:
                        self._cycle_length = device_data[ATTR_CYCLE]
                    if ATTR_RSSI in device_data:
                        self._rssi = device_data[ATTR_RSSI]
                    self._operation_mode = device_data[ATTR_SYSTEM_MODE]
                    if not self._is_low_voltage:
                        self._wattage = device_data[ATTR_WATTAGE]
                elif device_data["errorCode"] == "ReadTimeout":
                    _LOGGER.warning(
                        "A timeout occur during data update. Device %s do not "
                        + "respond. Check your network... (%s)",
                        self._name,
                        device_data,
                    )
                else:
                    _LOGGER.warning(
                        "Error in updating device %s: (%s)", self._name, device_data
                    )
            else:
                self.log_error(device_data["error"]["code"])
            if self._sku != "FLP55" and self._sku != "True Comfort":
                self.do_stat(start)
            self.get_sensor_error_code(start)
        else:
            if time.time() - self._snooze > SNOOZE_TIME:
                self._activ = True
                if NOTIFY == "notification" or NOTIFY == "both":
                    self.notify_ha(
                        "Warning: Neviweb Device update restarted for "
                        + self._name
                        + ", Sku: "
                        + self._sku
                    )

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
        data.update(
            {
                "wattage": self._wattage,
                "cycle_length": self._cycle_length,
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
                "hourly_kwh": self._hour_kwh,
                "daily_kwh": self._today_kwh,
                "monthly_kwh": self._month_kwh,
                "current_hour_kwh": self._current_hour_kwh,
                "current_today_kwh": self._current_today_kwh,
                "current_month_kwh": self._current_month_kwh,
                "rssi": self._rssi,
                "sku": self._sku,
                "device_model": str(self._device_model),
                "device_model_cfg": self._device_model_cfg,
                "firmware": self._firmware,
                "activation": self._activ,
                "id": str(self._id),
            }
        )
        return data

    @property
    def pi_heating_demand(self) -> int:
        """Heating demand."""
        return self._heat_level

    @property
    def supported_features(self):
        """Return the list of supported features."""
        if (
            self._is_floor
            or self._is_wifi_floor
            or self._is_low_wifi
            or self._is_low_voltage
        ):
            return SUPPORT_AUX_FLAGS
        elif self._is_HP:
            return SUPPORT_HP_FLAGS
        elif self._is_HC:
            return SUPPORT_HC_FLAGS
        elif self._is_hc:
            return SUPPORT_Hc_FLAGS
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
    def target_temperature_low(self) -> float:
        """Return the minimum heating temperature."""
        return self._min_temp

    @property
    def target_temperature_high(self) -> float:
        """Return the maximum heating temperature."""
        return self._max_temp

    @property
    def min_temp(self) -> float:
        """Return the minimum temperature."""
        return self._min_temp

    @property
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
    def temperature_unit(self):
        """Return the unit of measurement."""
        return UnitOfTemperature.CELSIUS

    @property
    def hvac_mode(self):
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
    def hvac_modes(self):
        """Return the list of available operation modes."""
        if self._is_wifi:
            return SUPPORTED_HVAC_WIFI_MODES
        elif self._is_wifi_lite:
            return SUPPORTED_HVAC_WIFI_LITE_MODES
        elif self._is_hc:
            return SUPPORTED_HVAC_H_C_MODES
        elif self._is_HC:
            return SUPPORTED_HVAC_HC_MODES
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
    def current_temperature(self) -> float:
        """Return the room current temperature."""
        return self._cur_temp

    @property
    def target_temperature(self) -> float:
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
    def preset_mode(self):
        """Return current preset mode."""
        if self._occupancy == PRESET_HOME:
            return PRESET_NONE
        elif self._occupancy == PRESET_AWAY:
            return PRESET_AWAY
        else:
            return PRESET_NONE

    @property
    def preset_modes(self):
        """Return available preset modes."""
        if self._is_wifi:
            return PRESET_WIFI_MODES
        elif self._is_HP:
            return PRESET_HP_MODES
        elif self._is_HC or self._is_hc:
            return PRESET_HC_MODES
        else:
            return PRESET_MODES

    @property
    def hvac_action(self):
        """Return current HVAC action."""
        if self._operation_mode == HVACMode.OFF:
            return HVACAction.OFF
        elif self._operation_mode == HVACMode.COOL:
            return HVACAction.COOLING
        elif self._operation_mode == HVACMode.FAN_ONLY:
            return HVACAction.FAN
        elif self._operation_mode == HVACMode.DRY:
            return HVACAction.DRYING
        elif not HOMEKIT_MODE and self._operation_mode == MODE_AUTO_BYPASS:
            if self._heat_level == 0:
                return HVACAction.IDLE + "(" + MODE_AUTO_BYPASS + ")"
            else:
                return HVACAction.HEATING + "(" + MODE_AUTO_BYPASS + ")"
        elif self._heat_level == 0:
            return HVACAction.IDLE
        else:
            return HVACAction.HEATING

    @property
    def is_on(self) -> bool:
        """Return True if mode = HVACMode.HEAT."""
        if (
            self._operation_mode == HVACMode.HEAT
            or self._operation_mode == HVACMode.AUTO
            or self._operation_mode == MODE_MANUAL
        ):
            return True
        return False

    @property
    def fan_mode(self) -> str | None:
        """Return the fan setting."""
        return self._fan_speed

    @property
    def fan_modes(self) -> list[str] | None:
        """Return available fan modes."""
        if self._is_HP or self._is_hc:
            return FAN_SPEED
        elif self._is_HC:
            return WIFI_FAN_SPEED
        else:
            return None

    @property
    def swing_mode(self) -> str | None:
        """Return the fan vertical swing setting."""
        if self._is_HP or self._is_hc:
            return self._fan_swing_vert
        return None

    @property
    def swing_modes(self) -> list[str] | None:
        """Return availables vertical swing modes."""
        if self._is_HP or self._is_hc:
            if self._fan_swing_cap is None or self._fan_swing_cap_vert is None:
                return None
            elif extract_capability(self._fan_swing_cap) == []:
                return None
            elif "fullVertical" in extract_capability(self._fan_swing_cap):
                return FULL_SWING + extract_capability_full(self._fan_swing_cap_vert)
            else:
                return extract_capability_full(self._fan_swing_cap_vert)
        else:
            return None

    @property
    def swing_horizontal_mode(self) -> str | None:
        """Return the fan swing setting."""
        if self._is_HP or self._is_hc:
            return self._fan_swing_horiz
        return None

    @property
    def swing_horizontal_modes(self) -> list[str] | None:
        """Return available horizontal swing modes"""
        if self._is_HP or self._is_hc:
            if self._fan_swing_cap is None or self._fan_swing_cap_horiz is None:
                return None
            elif extract_capability(self._fan_swing_cap) == []:
                return None
            elif "fullHorizontal" in extract_capability(self._fan_swing_cap):
                return FULL_SWING + extract_capability_full(self._fan_swing_cap_horiz)
            else:
                return extract_capability_full(self._fan_swing_cap_horiz)
        else:
            return None

    def set_fan_mode(self, speed: str) -> None:
        """Set new fan mode."""
        if speed is None:
            return
        self._client.set_fan_mode(self._id, speed)
        self._fan_speed = speed

    def set_swing_mode(self, swing: str) -> None:
        """Set new vertical swing mode."""
        if swing is None:
            return
        else:
            self._client.set_swing_vertical(self._id, swing)
            self._fan_swing_vert = swing

    def set_swing_horizontal_mode(self, swing: str) -> None:
        """Set new horizontal swing mode."""
        if swing is None:
            return
        else:
            self._client.set_swing_horizontal(self._id, swing)
            self._fan_swing_horiz = swing

    def turn_on(self) -> None:
        """Turn the thermostat to HVACMode.heat on."""
        self._client.set_setpoint_mode(self._id, HVACMode.HEAT, self._is_wifi)
        self._operation_mode = HVACMode.HEAT

    def turn_off(self) -> None:
        """Turn the thermostat to HVACMode.off."""
        self._client.set_setpoint_mode(self._id, HVACMode.OFF, self._is_wifi)
        self._operation_mode = HVACMode.OFF

    def set_temperature(self, **kwargs):
        """Set new target temperature."""
        temperature = kwargs.get(ATTR_TEMPERATURE)
        if temperature is None:
            return
        self._client.set_temperature(self._id, temperature)
        self._target_temp = temperature

    def set_second_display(self, value):
        """Set thermostat second display between outside and setpoint temperature."""
        display = value["display"]
        entity = value["id"]
        if display == "outsideTemperature":
            display_name = "Outside"
        else:
            display_name = "Setpoint"
        self._client.set_second_display(entity, display)
        self._display2 = display_name

    def set_backlight(self, value):
        """Set thermostat backlight «auto» = off when idle / on when active or «on» = always on."""
        """Work differently for zigbee and wifi devices."""
        level = value["level"]
        device = value["type"]
        entity = value["id"]
        if level == "on":
            if device == "wifi":
                level_command = "alwaysOn"
            else:
                level_command = "always"
            level_name = "On"
        elif level == "bedroom":
            level_command = "bedroom"
            level_name = "bedroom"
        else:
            if device == "wifi":
                level_command = "onUserAction"
            else:
                level_command = "onActive"
            level_name = "Auto"
        self._client.set_backlight(entity, level_command, device)
        self._backlight = level_name

    def set_keypad_lock(self, value):
        """Lock or unlock device's keypad, locked = Locked, unlocked = Unlocked."""
        lock = value["lock"]
        entity = value["id"]
        if lock == "locked" and self._is_wifi:
            lock = "lock"
        elif lock == "partiallyLocked" and self._is_wifi:
            lock = "partialLock"
        else:
            if self._is_wifi:
                lock = "unlock"
        self._client.set_keypad_lock(entity, lock, self._is_wifi)
        self._keypad = lock

    def set_time_format(self, value):
        """Set time format 12h or 24h."""
        time = value["time"]
        entity = value["id"]
        if time == 12:
            time_commande = "12h"
        else:
            time_commande = "24h"
        self._client.set_time_format(entity, time_commande)
        self._time_format = time_commande

    def set_temperature_format(self, value):
        """Set temperature format, celsius or fahrenheit."""
        temp = value["temp"]
        entity = value["id"]
        self._client.set_temperature_format(entity, temp)
        self._temperature_format = temp

    def set_air_floor_mode(self, value):
        """Switch temperature control between floor and ambiant sensor."""
        mode = value["mode"]
        entity = value["id"]
        self._client.set_air_floor_mode(entity, mode)
        self._floor_mode = mode

    def set_setpoint_max(self, value):
        """Set maximum setpoint temperature."""
        temp = value["temp"]
        entity = value["id"]
        self._client.set_setpoint_max(entity, temp)
        self._max_temp = temp

    def set_setpoint_min(self, value):
        """Set minimum setpoint temperature."""
        temp = value["temp"]
        entity = value["id"]
        self._client.set_setpoint_min(entity, temp)
        self._min_temp = temp

    def set_cool_setpoint_max(self, value):
        """Set maximum cooling setpoint temperature."""
        temp = value["temp"]
        entity = value["id"]
        self._client.set_cool_setpoint_max(entity, temp)
        self._cool_max = temp

    def set_cool_setpoint_min(self, value):
        """Set minimum cooling setpoint temperature."""
        temp = value["temp"]
        entity = value["id"]
        self._client.set_cool_setpoint_min(entity, temp)
        self._cool_min = temp

    def set_floor_air_limit(self, value):
        """Set maximum temperature air limit for floor thermostat."""
        temp = value["temp"]
        entity = value["id"]
        if temp == 0:
            status = "off"
        else:
            status = "on"
        self._client.set_floor_air_limit(entity, status, temp)
        self._floor_air_limit = temp

    def set_early_start(self, value):
        """Set early heating on/off for wifi thermostat."""
        start = value["start"]
        entity = value["id"]
        self._client.set_early_start(entity, start)
        self._early_start = start

    def set_hvac_dr_options(self, value):
        """Set thermostat DR options for Eco Sinope."""
        entity = value["id"]
        dr = value["dractive"]
        optout = value["optout"]
        setpoint = value["setpoint"]
        self._client.set_hvac_dr_options(entity, dr, optout, setpoint)
        self._drstatus_active = dr
        self._drstatus_optout = optout
        self._drstatus_setpoint = setpoint

    def set_hvac_dr_setpoint(self, value):
        """Set thermostat DR setpoint values for Eco Sinope."""
        entity = value["id"]
        status = value["status"]
        val = value["val"]
        self._client.set_hvac_dr_setpoint(entity, status, val)
        self._drsetpoint_status = status
        self._drsetpoint_value = val

    def set_hvac_mode(self, hvac_mode):
        """Set new hvac mode."""
        if hvac_mode == HVACMode.OFF:
            self._client.set_setpoint_mode(self._id, HVACMode.OFF, self._is_wifi)
        elif hvac_mode in [HVACMode.HEAT, MODE_MANUAL]:
            self._client.set_setpoint_mode(self._id, hvac_mode, self._is_wifi)
        elif hvac_mode == HVACMode.AUTO:
            self._client.set_setpoint_mode(self._id, HVACMode.AUTO, self._is_wifi)
        elif hvac_mode == MODE_AUTO_BYPASS:
            if self._operation_mode == HVACMode.AUTO:
                self._client.set_setpoint_mode(
                    self._id, MODE_AUTO_BYPASS, self._is_wifi
                )
        else:
            _LOGGER.error("Unable to set hvac mode: %s.", hvac_mode)
        self._operation_mode = hvac_mode
        self.update()

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

    def turn_em_heat_on(self):
        """Turn emergency heater on."""
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
        entity = value["id"]
        status = value["status"]
        val = value["val"]
        self._client.set_auxiliary_load(entity, status, val)
        self._load2_status = status
        self._load2 = val

    def set_aux_cycle_output(self, value):
        """Set low voltage thermostats auxiliary cycle status and length."""
        entity = value["id"]
        status = value["status"]
        val = value["val"]
        length = [v for k, v in HA_TO_NEVIWEB_PERIOD.items() if k == val][0]
        self._client.set_aux_cycle_output(entity, status, length)
        self._cycle_length_output2_status = status
        self._cycle_length_output2_value = length

    def set_cycle_output(self, value):
        """Set low voltage thermostats main cycle output length."""
        entity = value["id"]
        val = value["val"]
        length = [v for k, v in HA_TO_NEVIWEB_PERIOD.items() if k == val][0]
        self._client.set_aux_cycle_output(entity, length)
        self._cycle_length = length

    def set_pump_protection(self, value):
        """Set pump protection value."""
        entity = value["id"]
        status = value["status"]
        self._client.set_pump_protection(entity, status, self._is_low_wifi)
        self._pump_protec_status = status
        self._pump_protec_duration = 60
        self._pump_protec_period = 1

    def set_sensor_type(self, value):
        """Set sensor type."""
        entity = value["id"]
        tipe = value["type"]
        self._client.set_sensor_type(entity, tipe)
        self._floor_sensor_type = tipe

    def set_floor_limit(self, value):
        """Set maximum/minimum floor setpoint temperature."""
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
        self._client.set_floor_limit(entity, temp, limit, wifi)
        if limit == "low":
            self._floor_min = temp if temp != 0 else None
            self._floor_min_status = "on"
        else:
            self._floor_max = temp if temp != 0 else None
            self._floor_max_status = "on"

    def set_activation(self, value):
        """Activate or deactivate neviweb polling for a missing device."""
        action = value["active"]
        self._activ = action

    def set_heat_pump_operation_limit(self, value):
        """Set minimum temperature for heat pump operation."""
        temp = value["temp"]
        entity = value["id"]
        if temp < self._balance_pt_low:
            temp = self._balance_pt_low
        self._client.set_heat_pump_limit(entity, temp)
        self._balance_pt = temp

    def set_heat_lockout_temperature(self, value):
        """Set maximum outside temperature limit to allow heat device operation."""
        temp = value["temp"]
        entity = value["id"]
        self._client.set_heat_lockout(entity, temp)
        self._heat_lockout_temp = temp

    def set_cool_lockout_temperature(self, value):
        """Set minimum outside temperature limit to allow cooling device operation."""
        temp = value["temp"]
        entity = value["id"]
        self._client.set_cool_lockout(entity, temp)
        self._cool_lock_temp = temp

    def set_display_config(self, value):
        """Set display on/off for heat pump."""
        display = value["display"]
        entity = value["id"]
        self._client.set_hp_display(entity, display)
        self._display_conf = display

    def set_sound_config(self, value):
        """Set sound on/off for heat pump."""
        sound = value["sound"]
        entity = value["id"]
        self._client.set_hp_sound(entity, sound)
        self._sound_conf = sound

    def set_hc_second_display(self, value):
        """Set second display value for TH1134ZB-HC."""
        display = value["display"]
        entity = value["id"]
        self._client.set_hc_display(entity, display)
        self._display2 = display

    def set_language(self, value):
        """Set display language value for TH1134ZB-HC."""
        lang = value["lang"]
        entity = value["id"]
        self._client.set_language(entity, lang)
        self._language = lang

    def set_aux_heat_min_time_on(self, value):
        """Set auxiliary heating minimum time on for TH6500WF and TH6250WF."""
        time = value["time"]
        entity = value["id"]
        self._client.set_aux_heat_time_on(entity, time)
        self._aux_heat_time_on = time

    def set_cool_min_time(self, value):
        """Set minimum cooling time on for TH6500WF and TH6250WF."""
        time = value["time"]
        entity = value["id"]
        state = value["state"]
        self._client.set_cool_time(entity, time, state)
        if state == "on":
            self._cool_min_time_on = time
        else:
            self._cool_min_time_off = time

    def do_stat(self, start):
        """Get device energy statistic."""
        if (
            start - self._energy_stat_time > STAT_INTERVAL
            and self._energy_stat_time != 0
        ):
            device_hourly_stats = self._client.get_device_hourly_stats(self._id)
            #            _LOGGER.debug("Energy data for %s (SKU: %s): %s, size = %s", self._name, self._sku, device_hourly_stats, len(device_hourly_stats))
            if device_hourly_stats is not None and len(device_hourly_stats) > 1:
                n = len(device_hourly_stats)-2
                self._hour_kwh = device_hourly_stats[n]["period"] / 1000
                self._current_hour_kwh = device_hourly_stats[n+1]["period"] / 1000
            else:
                self._hour_kwh = 0
                self._current_hour_kwh = 0
                _LOGGER.warning("Got None for device_hourly_stats")
            device_daily_stats = self._client.get_device_daily_stats(self._id)
            #            _LOGGER.warning("%s device_daily_stats = %s", self._name, device_daily_stats)
            if device_daily_stats is not None and len(device_daily_stats) > 1:
                n = len(device_daily_stats)-2
                self._today_kwh = device_daily_stats[n]["period"] / 1000
                self._current_today_kwh = device_daily_stats[n+1]["period"] / 1000
            else:
                self._today_kwh = 0
                self._current_today_kwh = 0
                _LOGGER.warning("Got None for device_daily_stats")
            device_monthly_stats = self._client.get_device_monthly_stats(self._id)
            #            _LOGGER.warning("%s device_monthly_stats = %s", self._name, device_monthly_stats)
            if device_monthly_stats is not None and len(device_monthly_stats) > 1:
                n = len(device_monthly_stats)-2
                self._month_kwh = device_monthly_stats[n]["period"] / 1000
                self._current_month_kwh = device_monthly_stats[n+1]["period"] / 1000
            else:
                self._month_kwh = 0
                self._current_month_kwh = 0
                _LOGGER.warning("Got None for device_monthly_stats")
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
                    _LOGGER.warning(
                        "Error code set1 updated: %s", str(device_error_code["raw"])
                    )
                    self._energy_stat_time = time.time()
                if self._energy_stat_time == 0:
                    self._energy_stat_time = start

    def log_error(self, error_data):
        """Send error message to LOG."""
        if error_data == "USRSESSEXP":
            _LOGGER.warning("Session expired... reconnecting...")
            if NOTIFY == "notification" or NOTIFY == "both":
                self.notify_ha(
                    "Warning: Got USRSESSEXP error, Neviweb session expired. "
                    + "Set your scan_interval parameter to less than 10 "
                    + "minutes to avoid this... Reconnecting..."
                )
            self._client.reconnect()
        elif error_data == "ACCDAYREQMAX":
            _LOGGER.warning("Maximun daily request reached...Reduce polling frequency.")
        elif error_data == "TimeoutError":
            _LOGGER.warning("Timeout error detected...Retry later.")
        elif error_data == "MAINTENANCE":
            _LOGGER.warning("Access blocked for maintenance...Retry later.")
            self.notify_ha(
                "Warning: Neviweb access temporary blocked for maintenance..."
                + "Retry later."
            )
            self._client.reconnect()
        elif error_data == "ACCSESSEXC":
            _LOGGER.warning(
                "Maximun session number reached...Close other connections "
                + "and try again."
            )
            self.notify_ha(
                "Warning: Maximun Neviweb session number reached..."
                + "Close other connections and try again."
            )
            self._client.reconnect()
        elif error_data == "DVCATTRNSPTD":
            _LOGGER.warning(
                "Device attribute not supported for %s (id: %s): %s...(SKU: %s)",
                self._name,
                str(self._id),
                error_data,
                self._sku,
            )
        elif error_data == "DVCACTNSPTD":
            _LOGGER.warning(
                "Device action not supported for %s...(id: %s, SKU: %s) "
                + "Report to maintainer.",
                self._name,
                str(self._id),
                self._sku,
            )
        elif error_data == "DVCCOMMTO":
            _LOGGER.warning(
                "Device Communication Timeout... The device %s (id: %s) "
                + "did not respond to the server within the prescribed delay."
                + " (SKU: %s)",
                self._name,
                str(self._id),
                self._sku,
            )
        elif error_data == "SVCERR":
            _LOGGER.warning(
                "Service error, device not available retry later %s: %s..."
                + "(id: %s, SKU: %s)",
                self._name,
                error_data,
                str(self._id),
                self._sku,
            )
        elif error_data == "DVCBUSY":
            _LOGGER.warning(
                "Device busy can't reach (neviweb update ?), retry later %s "
                + "(id: %s): %s...(SKU: %s)",
                self._name,
                str(self._id),
                error_data,
                self._sku,
            )
        elif error_data == "DVCUNVLB":
            _LOGGER.warning("NOTIFY value: %s, (SKU: %s)", NOTIFY, self._sku)
            if NOTIFY == "logging" or NOTIFY == "both":
                _LOGGER.warning(
                    "Device %s (id: %s) is disconected from Neviweb: %s..."
                    + "(SKU: %s)",
                    self._name,
                    str(self._id),
                    error_data,
                    self._sku,
                )
                _LOGGER.warning(
                    "This device %s is de-activated and won't be updated "
                    + "for 20 minutes.",
                    self._name,
                )
                _LOGGER.warning(
                    "You can re-activate device %s with "
                    + "service.neviweb130_set_activation or wait 20 minutes "
                    + "for update to restart or just restart HA.",
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
            self._activ = False
            self._snooze = time.time()
        elif error_data == "DVCERR":
            _LOGGER.warning(
                "Device error for %s (id: %s), service already activ: %s..."
                + "(SKU: %s)",
                self._name,
                str(self._id),
                error_data,
                self._sku,
            )
        elif error_data == "SVCUNAUTH":
            _LOGGER.warning(
                "Service not authorised for device %s (id: %s): %s...(SKU: %s)",
                self._name,
                str(self._id),
                error_data,
                self._sku,
            )
        else:
            _LOGGER.warning(
                "Unknown error for %s (id: %s): %s...(SKU: %s) Report to"
                + " maintainer.",
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

    def __init__(self, data, device_info, name, sku, firmware):
        """Initialize."""
        self._name = name
        self._sku = sku
        self._firmware = firmware
        self._client = data.neviweb130_client
        self._id = device_info["id"]
        self._device_model = device_info["signature"]["model"]
        self._device_model_cfg = device_info["signature"]["modelCfg"]
        self._hour_kwh = 0
        self._today_kwh = 0
        self._month_kwh = 0
        self._current_hour_kwh = 0
        self._current_today_kwh = 0
        self._current_month_kwh = 0
        self._drstatus_active = "off"
        self._drstatus_optout = "off"
        self._drstatus_setpoint = "off"
        self._drstatus_abs = "off"
        self._drstatus_rel = "off"
        self._drsetpoint_status = "off"
        self._drsetpoint_value = 0
        self._cold_load_pickup = None
        self._heat_lockout_temp = None
        self._min_temp = 5
        self._max_temp = 30
        self._cur_temp = None
        self._cur_temp_before = None
        self._target_temp = None
        self._operation_mode = None
        self._occupancy = None
        self._temperature_format = UnitOfTemperature.CELSIUS
        self._time_format = "24h"
        self._temp_display_value = None
        self._display2 = None
        self._heat_level = 0
        self._keypad = None
        self._backlight = None
        self._cycle_length = 0
        self._wattage = 0
        self._error_code = None
        self._is_gen2 = device_info["signature"]["model"] in DEVICE_MODEL_HEAT_G2
        self._is_wifi = False
        self._is_wifi_lite = False
        self._is_wifi_floor = False
        self._is_low_wifi = False
        self._is_double = False
        self._is_floor = False
        self._is_hc = False
        self._is_HC = False
        self._is_HP = False
        self._is_low_voltage = False
        self._energy_stat_time = time.time() - 1500
        self._snooze = 0
        self._activ = True
        _LOGGER.debug("Setting up %s: %s", self._name, device_info)

    def update(self):
        if self._activ:
            GEN2_ATTRIBUTES = [
                ATTR_ROOM_TEMP_DISPLAY,
                ATTR_WATTAGE,
                ATTR_DISPLAY2,
                ATTR_KEYPAD,
                ATTR_BACKLIGHT,
                ATTR_SYSTEM_MODE,
                ATTR_CYCLE,
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
            device_data = self._client.get_device_attributes(
                self._id, UPDATE_ATTRIBUTES + GEN2_ATTRIBUTES
            )
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
                    self._time_format = device_data[ATTR_TIME]
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
                    if ATTR_CYCLE in device_data:
                        self._cycle_length = device_data[ATTR_CYCLE]
                    self._operation_mode = device_data[ATTR_SYSTEM_MODE]
                    self._wattage = device_data[ATTR_WATTAGE]
                elif device_data["errorCode"] == "ReadTimeout":
                    _LOGGER.warning(
                        "A timeout occur during data update. Device %s do not respond. Check your network... (%s)",
                        self._name,
                        device_data,
                    )
                else:
                    _LOGGER.warning(
                        "Error in updating device %s: (%s)", self._name, device_data
                    )
            else:
                self.log_error(device_data["error"]["code"])
            if self._sku != "FLP55" and self._sku != "True Comfort":
                self.do_stat(start)
            self.get_sensor_error_code(start)
        else:
            if time.time() - self._snooze > SNOOZE_TIME:
                self._activ = True
                if NOTIFY == "notification" or NOTIFY == "both":
                    self.notify_ha(
                        "Warning: Neviweb Device update restarted for "
                        + self._name
                        + ", Sku: "
                        + self._sku
                    )

    @property
    def extra_state_attributes(self):
        """Return the state attributes."""
        data = {}
        data.update(
            {
                "wattage": self._wattage,
                "cycle_length": self._cycle_length,
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
                "hourly_kwh": self._hour_kwh,
                "daily_kwh": self._today_kwh,
                "monthly_kwh": self._month_kwh,
                "current_hour_kwh": self._current_hour_kwh,
                "current_today_kwh": self._current_today_kwh,
                "current_month_kwh": self._current_month_kwh,
                "sku": self._sku,
                "device_model": str(self._device_model),
                "device_model_cfg": self._device_model_cfg,
                "firmware": self._firmware,
                "activation": self._activ,
                "id": str(self._id),
            }
        )
        return data


class Neviweb130FloorThermostat(Neviweb130Thermostat):
    """Implementation of Neviweb TH1300ZB thermostat."""

    def __init__(self, data, device_info, name, sku, firmware):
        """Initialize."""
        self._name = name
        self._sku = sku
        self._firmware = firmware
        self._client = data.neviweb130_client
        self._id = device_info["id"]
        self._device_model = device_info["signature"]["model"]
        self._device_model_cfg = device_info["signature"]["modelCfg"]
        self._hour_kwh = 0
        self._today_kwh = 0
        self._month_kwh = 0
        self._current_hour_kwh = 0
        self._current_today_kwh = 0
        self._current_month_kwh = 0
        self._drstatus_active = "off"
        self._drstatus_optout = "off"
        self._drstatus_setpoint = "off"
        self._drstatus_abs = "off"
        self._drstatus_rel = "off"
        self._drsetpoint_status = "off"
        self._drsetpoint_value = 0
        self._cur_temp = None
        self._cur_temp_before = None
        self._target_temp = None
        self._operation_mode = None
        self._occupancy = None
        self._min_temp = 5
        self._max_temp = 30
        self._temperature_format = UnitOfTemperature.CELSIUS
        self._time_format = "24h"
        self._temp_display_status = None
        self._temp_display_value = None
        self._display2 = None
        self._heat_level = 0
        self._keypad = None
        self._backlight = None
        self._cycle_length = 0
        self._cycle_length_output2_status = "off"
        self._rssi = None
        self._wattage = 0
        self._gfci_status = None
        self._floor_mode = None
        self._em_heat = "off"
        self._aux_cycle_length = 0
        self._floor_air_limit = None
        self._floor_air_limit_status = None
        self._floor_sensor_type = None
        self._floor_max = None
        self._floor_max_status = "off"
        self._floor_min = None
        self._floor_min_status = "off"
        self._load2 = 0
        self._load2_status = None
        self._error_code = None
        self._gfci_alert = None
        self._is_floor = device_info["signature"]["model"] in DEVICE_MODEL_FLOOR
        self._is_wifi = False
        self._is_wifi_lite = False
        self._is_wifi_floor = False
        self._is_low_wifi = False
        self._is_double = False
        self._is_gen2 = False
        self._is_hc = False
        self._is_HC = False
        self._is_HP = False
        self._is_low_voltage = False
        self._energy_stat_time = time.time() - 1500
        self._snooze = 0
        self._activ = True
        _LOGGER.debug("Setting up %s: %s", self._name, device_info)

    def update(self):
        if self._activ:
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
                ATTR_CYCLE,
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
            device_data = self._client.get_device_attributes(
                self._id, UPDATE_ATTRIBUTES + FLOOR_ATTRIBUTES
            )
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
                    self._time_format = device_data[ATTR_TIME]
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
                    if ATTR_CYCLE in device_data:
                        self._cycle_length = device_data[ATTR_CYCLE]
                    if ATTR_RSSI in device_data:
                        self._rssi = device_data[ATTR_RSSI]
                    self._operation_mode = device_data[ATTR_SYSTEM_MODE]
                    self._wattage = device_data[ATTR_WATTAGE]
                    self._gfci_status = device_data[ATTR_GFCI_STATUS]
                    self._floor_mode = device_data[ATTR_FLOOR_MODE]
                    self._em_heat = device_data[ATTR_FLOOR_AUX]
                    self._floor_air_limit = device_data[ATTR_FLOOR_AIR_LIMIT]["value"]
                    self._floor_air_limit_status = device_data[ATTR_FLOOR_AIR_LIMIT][
                        "status"
                    ]
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
                    _LOGGER.warning(
                        "Error in updating device %s: (%s)", self._name, device_data
                    )
            else:
                self.log_error(device_data["error"]["code"])
            if self._sku != "FLP55" and self._sku != "True Comfort":
                self.do_stat(start)
            self.get_sensor_error_code(start)
        else:
            if time.time() - self._snooze > SNOOZE_TIME:
                self._activ = True
                if NOTIFY == "notification" or NOTIFY == "both":
                    self.notify_ha(
                        "Warning: Neviweb Device update restarted for "
                        + self._name
                        + ", Sku: "
                        + self._sku
                    )

    @property
    def extra_state_attributes(self):
        """Return the state attributes."""
        data = {}
        data.update(
            {
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
                "cycle_length": self._cycle_length,
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
                "hourly_kwh": self._hour_kwh,
                "daily_kwh": self._today_kwh,
                "monthly_kwh": self._month_kwh,
                "current_hour_kwh": self._current_hour_kwh,
                "current_today_kwh": self._current_today_kwh,
                "current_month_kwh": self._current_month_kwh,
                "rssi": self._rssi,
                "sku": self._sku,
                "device_model": str(self._device_model),
                "device_model_cfg": self._device_model_cfg,
                "firmware": self._firmware,
                "activation": self._activ,
                "id": str(self._id),
            }
        )
        return data


class Neviweb130LowThermostat(Neviweb130Thermostat):
    """Implementation of Neviweb TH1400ZB thermostat."""

    def __init__(self, data, device_info, name, sku, firmware):
        """Initialize."""
        self._name = name
        self._sku = sku
        self._firmware = firmware
        self._client = data.neviweb130_client
        self._id = device_info["id"]
        self._device_model = device_info["signature"]["model"]
        self._device_model_cfg = device_info["signature"]["modelCfg"]
        self._hour_kwh = 0
        self._today_kwh = 0
        self._month_kwh = 0
        self._current_hour_kwh = 0
        self._current_today_kwh = 0
        self._current_month_kwh = 0
        self._drstatus_active = "off"
        self._drstatus_optout = "off"
        self._drstatus_setpoint = "off"
        self._drstatus_abs = "off"
        self._drstatus_rel = "off"
        self._drsetpoint_status = "off"
        self._drsetpoint_value = 0
        self._cur_temp = None
        self._cur_temp_before = None
        self._target_temp = None
        self._operation_mode = None
        self._occupancy = None
        self._min_temp = 5
        self._max_temp = 30
        self._temperature_format = UnitOfTemperature.CELSIUS
        self._time_format = "24h"
        self._backlight = None
        self._keypad = None
        self._display2 = None
        self._temp_display_value = None
        self._heat_level = 0
        self._pump_protec_status = None
        self._pump_protec_duration = None
        self._pump_protec_period = None
        self._pump_protec_period_status = None
        self._floor_sensor_type = None
        self._floor_air_limit = None
        self._floor_air_limit_status = None
        self._floor_max = None
        self._floor_max_status = "off"
        self._floor_min = None
        self._floor_min_status = "off"
        self._cycle_length_output2_value = 0
        self._cycle_length_output2_status = "off"
        self._em_heat = "off"
        self._aux_cycle_length = 0
        self._cycle_length = 0
        self._floor_mode = None
        self._error_code = None
        self._load1 = 0
        self._load2 = 0
        self._load2_status = None
        self._rssi = None
        self._is_low_voltage = device_info["signature"]["model"] in DEVICE_MODEL_LOW
        self._is_wifi = False
        self._is_wifi_lite = False
        self._is_wifi_floor = False
        self._is_low_wifi = False
        self._is_double = False
        self._is_gen2 = False
        self._is_hc = False
        self._is_HC = False
        self._is_HP = False
        self._is_floor = False
        self._energy_stat_time = time.time() - 1500
        self._snooze = 0
        self._activ = True
        _LOGGER.debug("Setting up %s: %s", self._name, device_info)

    def update(self):
        if self._activ:
            LOW_VOLTAGE_ATTRIBUTES = [
                ATTR_ROOM_TEMP_DISPLAY,
                ATTR_KEYPAD,
                ATTR_BACKLIGHT,
                ATTR_SYSTEM_MODE,
                ATTR_CYCLE,
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
            device_data = self._client.get_device_attributes(
                self._id, UPDATE_ATTRIBUTES + LOW_VOLTAGE_ATTRIBUTES
            )
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
                    self._time_format = device_data[ATTR_TIME]
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
                    if ATTR_CYCLE in device_data:
                        self._cycle_length = device_data[ATTR_CYCLE]
                    if ATTR_RSSI in device_data:
                        self._rssi = device_data[ATTR_RSSI]
                    self._operation_mode = device_data[ATTR_SYSTEM_MODE]
                    self._floor_mode = device_data[ATTR_FLOOR_MODE]
                    self._floor_air_limit = device_data[ATTR_FLOOR_AIR_LIMIT]["value"]
                    self._floor_air_limit_status = device_data[ATTR_FLOOR_AIR_LIMIT][
                        "status"
                    ]
                    self._cycle_length_output2_status = device_data[ATTR_CYCLE_OUTPUT2][
                        "status"
                    ]
                    self._cycle_length_output2_value = device_data[ATTR_CYCLE_OUTPUT2][
                        "value"
                    ]
                    self._floor_max = device_data[ATTR_FLOOR_MAX]["value"]
                    self._floor_max_status = device_data[ATTR_FLOOR_MAX]["status"]
                    self._floor_min = device_data[ATTR_FLOOR_MIN]["value"]
                    self._floor_min_status = device_data[ATTR_FLOOR_MIN]["status"]
                    self._pump_protec_status = device_data[ATTR_PUMP_PROTEC_DURATION][
                        "status"
                    ]
                    if device_data[ATTR_PUMP_PROTEC_DURATION]["status"] == "on":
                        self._pump_protec_duration = device_data[
                            ATTR_PUMP_PROTEC_DURATION
                        ]["value"]
                        self._pump_protec_period = device_data[ATTR_PUMP_PROTEC_PERIOD][
                            "value"
                        ]
                        self._pump_protec_period_status = device_data[
                            ATTR_PUMP_PROTEC_PERIOD
                        ]["status"]
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
                    _LOGGER.warning(
                        "Error in updating device %s: (%s)", self._name, device_data
                    )
            else:
                self.log_error(device_data["error"]["code"])
            if self._sku != "FLP55" and self._sku != "True Comfort":
                self.do_stat(start)
            self.get_sensor_error_code(start)
        else:
            if time.time() - self._snooze > SNOOZE_TIME:
                self._activ = True
                if NOTIFY == "notification" or NOTIFY == "both":
                    self.notify_ha(
                        "Warning: Neviweb Device update restarted for "
                        + self._name
                        + ", Sku: "
                        + self._sku
                    )

    @property
    def extra_state_attributes(self):
        """Return the state attributes."""
        data = {}
        data.update(
            {
                "sensor_mode": self._floor_mode,
                "cycle_length": neviweb_to_ha(self._cycle_length),
                "auxiliary_cycle_status": self._cycle_length_output2_status,
                "auxiliary_cycle_value": neviweb_to_ha(
                    self._cycle_length_output2_value
                ),
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
                "hourly_kwh": self._hour_kwh,
                "daily_kwh": self._today_kwh,
                "monthly_kwh": self._month_kwh,
                "current_hour_kwh": self._current_hour_kwh,
                "current_today_kwh": self._current_today_kwh,
                "current_month_kwh": self._current_month_kwh,
                "rssi": self._rssi,
                "sku": self._sku,
                "device_model": str(self._device_model),
                "device_model_cfg": self._device_model_cfg,
                "firmware": self._firmware,
                "activation": self._activ,
                "id": str(self._id),
            }
        )
        return data


class Neviweb130DoubleThermostat(Neviweb130Thermostat):
    """Implementation of Neviweb TH1500ZB thermostat."""

    def __init__(self, data, device_info, name, sku, firmware):
        """Initialize."""
        self._name = name
        self._sku = sku
        self._firmware = firmware
        self._client = data.neviweb130_client
        self._id = device_info["id"]
        self._device_model = device_info["signature"]["model"]
        self._device_model_cfg = device_info["signature"]["modelCfg"]
        self._hour_kwh = 0
        self._today_kwh = 0
        self._month_kwh = 0
        self._current_hour_kwh = 0
        self._current_today_kwh = 0
        self._current_month_kwh = 0
        self._drstatus_active = "off"
        self._drstatus_optout = "off"
        self._drstatus_setpoint = "off"
        self._drstatus_abs = "off"
        self._drstatus_rel = "off"
        self._drsetpoint_status = "off"
        self._drsetpoint_value = 0
        self._cur_temp = None
        self._cur_temp_before = None
        self._target_temp = None
        self._operation_mode = None
        self._occupancy = None
        self._wattage = 0
        self._min_temp = 5
        self._max_temp = 30
        self._heat_level = 0
        self._keypad = None
        self._rssi = None
        self._display2 = None
        self._backlight = None
        self._time_format = "24h"
        self._temperature_format = UnitOfTemperature.CELSIUS
        self._temp_display_value = None
        self._cycle_length = 0
        self._cycle_length_output2_status = "off"
        self._em_heat = "off"
        self._aux_cycle_length = 0
        self._error_code = None
        self._is_double = device_info["signature"]["model"] in DEVICE_MODEL_DOUBLE
        self._is_wifi = False
        self._is_wifi_lite = False
        self._is_wifi_floor = False
        self._is_low_wifi = False
        self._is_low_voltage = False
        self._is_gen2 = False
        self._is_hc = False
        self._is_HC = False
        self._is_HP = False
        self._is_floor = False
        self._energy_stat_time = time.time() - 1500
        self._snooze = 0
        self._activ = True
        _LOGGER.debug("Setting up %s: %s", self._name, device_info)

    def update(self):
        if self._activ:
            DOUBLE_ATTRIBUTES = [
                ATTR_ROOM_TEMP_DISPLAY,
                ATTR_KEYPAD,
                ATTR_BACKLIGHT,
                ATTR_SYSTEM_MODE,
                ATTR_CYCLE,
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
            device_data = self._client.get_device_attributes(
                self._id, UPDATE_ATTRIBUTES + DOUBLE_ATTRIBUTES
            )
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
                    self._time_format = device_data[ATTR_TIME]
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
                    if ATTR_CYCLE in device_data:
                        self._cycle_length = device_data[ATTR_CYCLE]
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
                    _LOGGER.warning(
                        "Error in updating device %s: (%s)", self._name, device_data
                    )
            else:
                self.log_error(device_data["error"]["code"])
            if self._sku != "FLP55" and self._sku != "True Comfort":
                self.do_stat(start)
            self.get_sensor_error_code(start)
        else:
            if time.time() - self._snooze > SNOOZE_TIME:
                self._activ = True
                if NOTIFY == "notification" or NOTIFY == "both":
                    self.notify_ha(
                        "Warning: Neviweb Device update restarted for "
                        + self._name
                        + ", Sku: "
                        + self._sku
                    )

    @property
    def extra_state_attributes(self):
        """Return the state attributes."""
        data = {}
        data.update(
            {
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
                "hourly_kwh": self._hour_kwh,
                "daily_kwh": self._today_kwh,
                "monthly_kwh": self._month_kwh,
                "current_hour_kwh": self._current_hour_kwh,
                "current_today_kwh": self._current_today_kwh,
                "current_month_kwh": self._current_month_kwh,
                "rssi": self._rssi,
                "sku": self._sku,
                "device_model": str(self._device_model),
                "device_model_cfg": self._device_model_cfg,
                "firmware": self._firmware,
                "activation": self._activ,
                "id": str(self._id),
            }
        )
        return data


class Neviweb130WifiThermostat(Neviweb130Thermostat):
    """Implementation of Neviweb TH1123WF, TH1124WF, TH1500WF thermostats."""

    def __init__(self, data, device_info, name, sku, firmware):
        """Initialize."""
        self._name = name
        self._sku = sku
        self._firmware = firmware
        self._client = data.neviweb130_client
        self._id = device_info["id"]
        self._device_model = device_info["signature"]["model"]
        self._device_model_cfg = device_info["signature"]["modelCfg"]
        self._hour_kwh = 0
        self._today_kwh = 0
        self._month_kwh = 0
        self._current_hour_kwh = 0
        self._current_today_kwh = 0
        self._current_month_kwh = 0
        self._drstatus_active = "off"
        self._drstatus_optout = "off"
        self._drstatus_setpoint = "off"
        self._drstatus_abs = "off"
        self._drstatus_rel = "off"
        self._drstatus_onOff = "off"
        self._drsetpoint_status = "off"
        self._drsetpoint_value = 0
        self._cur_temp = None
        self._cur_temp_before = None
        self._room_temp_error = None
        self._target_temp = None
        self._operation_mode = None
        self._occupancy = None
        self._wattage = 0
        self._temp_display_status = None
        self._heat_source_type = None
        self._early_start = "off"
        self._target_temp_away = None
        self._load1 = 0
        self._cycle_length = 0
        self._cycle_length_output2_status = "off"
        self._em_heat = "off"
        self._aux_cycle_length = 0
        self._error_code = None
        self._heat_level = 0
        self._temp_display_value = None
        self._display2 = None
        self._keypad = None
        self._backlight = None
        self._time_format = "24h"
        self._temperature_format = UnitOfTemperature.CELSIUS
        self._min_temp = 5
        self._max_temp = 30
        self._rssi = None
        self._is_wifi = (
            device_info["signature"]["model"] in DEVICE_MODEL_WIFI_FLOOR
            or device_info["signature"]["model"] in DEVICE_MODEL_WIFI
            or device_info["signature"]["model"] in DEVICE_MODEL_LOW_WIFI
            or device_info["signature"]["model"] in DEVICE_MODEL_WIFI_LITE
        )
        self._is_wifi_lite = False
        self._is_double = False
        self._is_wifi_floor = False
        self._is_low_wifi = False
        self._is_low_voltage = False
        self._is_gen2 = False
        self._is_hc = False
        self._is_HC = False
        self._is_HP = False
        self._is_floor = False
        self._energy_stat_time = time.time() - 1500
        self._snooze = 0
        self._activ = True
        _LOGGER.debug("Setting up %s: %s", self._name, device_info)

    def update(self):
        if self._activ:
            WIFI_ATTRIBUTES = [
                ATTR_ROOM_TEMP_DISPLAY,
                ATTR_CYCLE,
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
            device_data = self._client.get_device_attributes(
                self._id, UPDATE_ATTRIBUTES + WIFI_ATTRIBUTES
            )
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
                    self._time_format = device_data[ATTR_TIME]
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
                        self._drstatus_onOff = device_data[ATTR_DRSTATUS]["onOff"]
                    self._heat_level = device_data[ATTR_OUTPUT_PERCENT_DISPLAY][
                        "percent"
                    ]
                    self._heat_source_type = device_data[ATTR_OUTPUT_PERCENT_DISPLAY][
                        "sourceType"
                    ]
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
                    if ATTR_CYCLE in device_data:
                        self._cycle_length = device_data[ATTR_CYCLE]
                    if ATTR_ROOM_TEMP_DISPLAY in device_data:
                        self._temp_display_status = device_data[ATTR_ROOM_TEMP_DISPLAY][
                            "status"
                        ]
                        self._temp_display_value = device_data[ATTR_ROOM_TEMP_DISPLAY][
                            "value"
                        ]
                elif device_data["errorCode"] == "ReadTimeout":
                    _LOGGER.warning(
                        "A timeout occur during data update. Device %s do not respond. Check your network... (%s)",
                        self._name,
                        device_data,
                    )
                else:
                    _LOGGER.warning(
                        "Error in updating device %s: (%s)", self._name, device_data
                    )
            else:
                self.log_error(device_data["error"]["code"])
            if self._sku != "FLP55" and self._sku != "True Comfort":
                self.do_stat(start)
            self.get_sensor_error_code(start)
        else:
            if time.time() - self._snooze > SNOOZE_TIME:
                self._activ = True
                if NOTIFY == "notification" or NOTIFY == "both":
                    self.notify_ha(
                        "Warning: Neviweb Device update restarted for "
                        + self._name
                        + ", Sku: "
                        + self._sku
                    )

    @property
    def extra_state_attributes(self):
        """Return the state attributes."""
        data = {}
        data.update(
            {
                "wattage": self._wattage,
                "occupancy": self._occupancy,
                "temp_display_status": self._temp_display_status,
                "temp_display_error": self._room_temp_error,
                "source_type": self._heat_source_type,
                "early_start": self._early_start,
                "setpoint_away": self._target_temp_away,
                "load_watt_1": self._load1,
                "cycle_length": self._cycle_length,
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
                "eco_onOff": self._drstatus_onOff,
                "eco_setpoint_status": self._drsetpoint_status,
                "eco_setpoint_delta": self._drsetpoint_value,
                "hourly_kwh": self._hour_kwh,
                "daily_kwh": self._today_kwh,
                "monthly_kwh": self._month_kwh,
                "current_hour_kwh": self._current_hour_kwh,
                "current_today_kwh": self._current_today_kwh,
                "current_month_kwh": self._current_month_kwh,
                "rssi": self._rssi,
                "sku": self._sku,
                "device_model": str(self._device_model),
                "device_model_cfg": self._device_model_cfg,
                "firmware": self._firmware,
                "activation": self._activ,
                "id": str(self._id),
            }
        )
        return data


class Neviweb130WifiLiteThermostat(Neviweb130Thermostat):
    """Implementation of Neviweb TH1133WF, TH1133CR, TH1134WF and TH1134CR thermostats."""

    _attr_precision = 1.0
    _attr_target_temperature_step = 1.0

    def __init__(self, data, device_info, name, sku, firmware):
        """Initialize."""
        self._name = name
        self._sku = sku
        self._firmware = firmware
        self._client = data.neviweb130_client
        self._id = device_info["id"]
        self._device_model = device_info["signature"]["model"]
        self._device_model_cfg = device_info["signature"]["modelCfg"]
        self._hour_kwh = 0
        self._today_kwh = 0
        self._month_kwh = 0
        self._current_hour_kwh = 0
        self._current_today_kwh = 0
        self._current_month_kwh = 0
        self._drstatus_active = "off"
        self._drstatus_optout = "off"
        self._drstatus_setpoint = "off"
        self._drstatus_abs = "off"
        self._drstatus_rel = "off"
        self._drstatus_onOff = "off"
        self._drsetpoint_status = "off"
        self._drsetpoint_value = 0
        self._cur_temp = None
        self._cur_temp_before = None
        self._room_temp_error = None
        self._target_temp = None
        self._operation_mode = None
        self._occupancy = None
        self._temp_display_status = None
        self._heat_source_type = None
        self._early_start = "off"
        self._target_temp_away = None
        self._load1 = 0
        self._cycle_length = 0
        self._cycle_length_output2_status = "off"
        self._em_heat = "off"
        self._aux_cycle_length = 0
        self._error_code = None
        self._heat_level = 0
        self._temp_display_value = None
        self._keypad = None
        self._backlight = None
        self._time_format = "24h"
        self._temperature_format = UnitOfTemperature.CELSIUS
        self._min_temp = 5
        self._max_temp = 30
        self._rssi = None
        self._is_wifi = (
            device_info["signature"]["model"] in DEVICE_MODEL_WIFI_FLOOR
            or device_info["signature"]["model"] in DEVICE_MODEL_WIFI
            or device_info["signature"]["model"] in DEVICE_MODEL_LOW_WIFI
            or device_info["signature"]["model"] in DEVICE_MODEL_WIFI_LITE
        )
        self._is_wifi_lite = device_info["signature"]["model"] in DEVICE_MODEL_WIFI_LITE
        self._is_double = False
        self._is_wifi_floor = False
        self._is_low_wifi = False
        self._is_low_voltage = False
        self._is_gen2 = False
        self._is_hc = False
        self._is_HC = False
        self._is_HP = False
        self._is_floor = False
        self._energy_stat_time = time.time() - 1500
        self._snooze = 0
        self._activ = True
        _LOGGER.debug("Setting up %s: %s", self._name, device_info)

    def update(self):
        if self._activ:
            LITE_ATTRIBUTES = [
                ATTR_ROOM_TEMP_DISPLAY,
                ATTR_CYCLE,
                ATTR_OUTPUT1,
                ATTR_WIFI,
                ATTR_WIFI_KEYPAD,
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
                UPDATE_ATTRIBUTES + LITE_ATTRIBUTES,
            )
            device_data = self._client.get_device_attributes(
                self._id, UPDATE_ATTRIBUTES + LITE_ATTRIBUTES
            )
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
                    self._time_format = device_data[ATTR_TIME]
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
                        self._drstatus_onOff = device_data[ATTR_DRSTATUS]["onOff"]
                    self._heat_level = device_data[ATTR_OUTPUT_PERCENT_DISPLAY][
                        "percent"
                    ]
                    self._heat_source_type = device_data[ATTR_OUTPUT_PERCENT_DISPLAY][
                        "sourceType"
                    ]
                    self._operation_mode = device_data[ATTR_SETPOINT_MODE]
                    self._occupancy = device_data[ATTR_OCCUPANCY]
                    self._keypad = device_data[ATTR_WIFI_KEYPAD]
                    self._rssi = device_data[ATTR_WIFI]
                    self._backlight = device_data[ATTR_BACKLIGHT_AUTO_DIM]
                    self._early_start = device_data[ATTR_EARLY_START]
                    self._target_temp_away = device_data[ATTR_ROOM_SETPOINT_AWAY]
                    self._load1 = device_data[ATTR_OUTPUT1]
                    if ATTR_CYCLE in device_data:
                        self._cycle_length = device_data[ATTR_CYCLE]
                    if ATTR_ROOM_TEMP_DISPLAY in device_data:
                        self._temp_display_status = device_data[ATTR_ROOM_TEMP_DISPLAY][
                            "status"
                        ]
                        self._temp_display_value = device_data[ATTR_ROOM_TEMP_DISPLAY][
                            "value"
                        ]
                elif device_data["errorCode"] == "ReadTimeout":
                    _LOGGER.warning(
                        "A timeout occur during data update. Device %s do not respond. Check your network... (%s)",
                        self._name,
                        device_data,
                    )
                else:
                    _LOGGER.warning(
                        "Error in updating device %s: (%s)", self._name, device_data
                    )
            else:
                self.log_error(device_data["error"]["code"])
            if self._sku != "TH1133WF" and self._sku != "TH1133CR":
                self.do_stat(start)
            self.get_sensor_error_code(start)
        else:
            if time.time() - self._snooze > SNOOZE_TIME:
                self._activ = True
                if NOTIFY == "notification" or NOTIFY == "both":
                    self.notify_ha(
                        "Warning: Neviweb Device update restarted for "
                        + self._name
                        + ", Sku: "
                        + self._sku
                    )

    @property
    def extra_state_attributes(self):
        """Return the state attributes."""
        data = {}
        data.update(
            {
                "occupancy": self._occupancy,
                "temp_display_status": self._temp_display_status,
                "temp_display_error": self._room_temp_error,
                "source_type": self._heat_source_type,
                "early_start": self._early_start,
                "setpoint_away": self._target_temp_away,
                "load_watt_1": self._load1,
                "cycle_length": self._cycle_length,
                "error_code": self._error_code,
                "heat_level": self._heat_level,
                "pi_heating_demand": self._heat_level,
                "temp_display_value": self._temp_display_value,
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
                "eco_onOff": self._drstatus_onOff,
                "eco_setpoint_status": self._drsetpoint_status,
                "eco_setpoint_delta": self._drsetpoint_value,
                "hourly_kwh": self._hour_kwh,
                "daily_kwh": self._today_kwh,
                "monthly_kwh": self._month_kwh,
                "current_hour_kwh": self._current_hour_kwh,
                "current_today_kwh": self._current_today_kwh,
                "current_month_kwh": self._current_month_kwh,
                "rssi": self._rssi,
                "sku": self._sku,
                "device_model": str(self._device_model),
                "device_model_cfg": self._device_model_cfg,
                "firmware": self._firmware,
                "activation": self._activ,
                "id": str(self._id),
            }
        )
        return data


class Neviweb130LowWifiThermostat(Neviweb130Thermostat):
    """Implementation of Neviweb TH1400WF thermostat."""

    def __init__(self, data, device_info, name, sku, firmware):
        """Initialize."""
        self._name = name
        self._sku = sku
        self._firmware = firmware
        self._client = data.neviweb130_client
        self._id = device_info["id"]
        self._device_model = device_info["signature"]["model"]
        self._device_model_cfg = device_info["signature"]["modelCfg"]
        self._hour_kwh = 0
        self._today_kwh = 0
        self._month_kwh = 0
        self._current_hour_kwh = 0
        self._current_today_kwh = 0
        self._current_month_kwh = 0
        self._drstatus_active = "off"
        self._drstatus_optout = "off"
        self._drstatus_setpoint = "off"
        self._drstatus_abs = "off"
        self._drstatus_rel = "off"
        self._drsetpoint_status = "off"
        self._drsetpoint_value = 0
        self._cur_temp = None
        self._cur_temp_before = None
        self._target_temp = None
        self._operation_mode = None
        self._occupancy = None
        self._wattage = 0
        self._min_temp = 5
        self._max_temp = 30
        self._target_temp_away = None
        self._heat_level = 0
        self._heat_source_type = None
        self._floor_mode = None
        self._floor_sensor_type = None
        self._em_heat = "off"
        self._aux_cycle_length = 0
        self._cycle_length_output2_status = "off"
        self._early_start = "off"
        self._keypad = None
        self._load1 = 0
        self._load2 = 0
        self._rssi = None
        self._display2 = None
        self._backlight = None
        self._time_format = "24h"
        self._floor_air_limit = None
        self._floor_air_limit_status = None
        self._floor_max = None
        self._floor_max_status = "off"
        self._floor_min = None
        self._floor_min_status = "off"
        self._temperature_format = UnitOfTemperature.CELSIUS
        self._temp_display_status = None
        self._temp_display_value = None
        self._cycle_length = 0
        self._aux_cycle_length = 0
        self._pump_protec_status = None
        self._pump_protec_duration = None
        self._pump_protec_period = None
        self._pump_duration_value = None
        self._error_code = None
        self._is_wifi = (
            device_info["signature"]["model"] in DEVICE_MODEL_WIFI_FLOOR
            or device_info["signature"]["model"] in DEVICE_MODEL_WIFI
            or device_info["signature"]["model"] in DEVICE_MODEL_LOW_WIFI
            or device_info["signature"]["model"] in DEVICE_MODEL_WIFI_LITE
        )
        self._is_wifi_lite = False
        self._is_low_wifi = device_info["signature"]["model"] in DEVICE_MODEL_LOW_WIFI
        self._is_double = False
        self._is_low_voltage = False
        self._is_gen2 = False
        self._is_hc = False
        self._is_HC = False
        self._is_HP = False
        self._is_floor = False
        self._is_wifi_floor = False
        self._energy_stat_time = time.time() - 1500
        self._snooze = 0
        self._activ = True
        _LOGGER.debug("Setting up %s: %s", self._name, device_info)

    def update(self):
        if self._activ:
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
                ATTR_AUX_CYCLE,
                ATTR_CYCLE,
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
            device_data = self._client.get_device_attributes(
                self._id, UPDATE_ATTRIBUTES + LOW_WIFI_ATTRIBUTES
            )
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
                    self._time_format = device_data[ATTR_TIME]
                    self._temp_display_value = device_data[ATTR_ROOM_TEMP_DISPLAY][
                        "value"
                    ]
                    self._temp_display_status = device_data[ATTR_ROOM_TEMP_DISPLAY][
                        "status"
                    ]
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
                    self._heat_level = device_data[ATTR_OUTPUT_PERCENT_DISPLAY][
                        "percent"
                    ]
                    self._heat_source_type = device_data[ATTR_OUTPUT_PERCENT_DISPLAY][
                        "sourceType"
                    ]
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
                    self._aux_cycle_length = device_data[ATTR_AUX_CYCLE]
                    self._cycle_length = device_data[ATTR_CYCLE]
                    self._floor_max = device_data[ATTR_FLOOR_MAX]["value"]
                    self._floor_max_status = device_data[ATTR_FLOOR_MAX]["status"]
                    self._floor_min = device_data[ATTR_FLOOR_MIN]["value"]
                    self._floor_min_status = device_data[ATTR_FLOOR_MIN]["status"]
                    self._floor_air_limit = device_data[ATTR_FLOOR_AIR_LIMIT]["value"]
                    self._floor_air_limit_status = device_data[ATTR_FLOOR_AIR_LIMIT][
                        "status"
                    ]
                    self._pump_protec_status = device_data[ATTR_PUMP_PROTEC]["status"]
                    if device_data[ATTR_PUMP_PROTEC]["status"] == "on":
                        self._pump_protec_period = device_data[ATTR_PUMP_PROTEC][
                            "frequency"
                        ]
                        self._pump_protec_duration = device_data[ATTR_PUMP_PROTEC][
                            "duration"
                        ]
                    if ATTR_PUMP_PROTEC_DURATION in device_data:
                        self._pump_duration_value = device_data[
                            ATTR_PUMP_PROTEC_DURATION
                        ]
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
                    _LOGGER.warning(
                        "Error in updating device %s: (%s)", self._name, device_data
                    )
            else:
                self.log_error(device_data["error"]["code"])
            if self._sku != "FLP55" and self._sku != "True Comfort":
                self.do_stat(start)
            self.get_sensor_error_code(start)
        else:
            if time.time() - self._snooze > SNOOZE_TIME:
                self._activ = True
                if NOTIFY == "notification" or NOTIFY == "both":
                    self.notify_ha(
                        "Warning: Neviweb Device update restarted for "
                        + self._name
                        + ", Sku: "
                        + self._sku
                    )

    @property
    def extra_state_attributes(self):
        """Return the state attributes."""
        data = {}
        data.update(
            {
                "sensor_mode": self._floor_mode,
                "floor_sensor_type": self._floor_sensor_type,
                "load_watt": self._wattage,
                "auxiliary_cycle_length": self._aux_cycle_length,
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
                "hourly_kwh": self._hour_kwh,
                "daily_kwh": self._today_kwh,
                "monthly_kwh": self._month_kwh,
                "current_hour_kwh": self._current_hour_kwh,
                "current_today_kwh": self._current_today_kwh,
                "current_month_kwh": self._current_month_kwh,
                "rssi": self._rssi,
                "sku": self._sku,
                "device_model": str(self._device_model),
                "device_model_cfg": self._device_model_cfg,
                "firmware": self._firmware,
                "activation": self._activ,
                "id": str(self._id),
            }
        )
        return data


class Neviweb130WifiFloorThermostat(Neviweb130Thermostat):
    """Implementation of Neviweb TH1300WF, TH1325WF, TH1310WF and SRM40 thermostat."""

    def __init__(self, data, device_info, name, sku, firmware):
        """Initialize."""
        self._name = name
        self._sku = sku
        self._firmware = firmware
        self._client = data.neviweb130_client
        self._id = device_info["id"]
        self._device_model = device_info["signature"]["model"]
        self._device_model_cfg = device_info["signature"]["modelCfg"]
        self._hour_kwh = 0
        self._today_kwh = 0
        self._month_kwh = 0
        self._current_hour_kwh = 0
        self._current_today_kwh = 0
        self._current_month_kwh = 0
        self._drstatus_active = "off"
        self._drstatus_optout = "off"
        self._drstatus_setpoint = "off"
        self._drstatus_abs = "off"
        self._drstatus_rel = "off"
        self._drsetpoint_status = "off"
        self._drsetpoint_value = 0
        self._cur_temp = None
        self._cur_temp_before = None
        self._target_temp = None
        self._operation_mode = None
        self._occupancy = None
        self._wattage = 0
        self._min_temp = 5
        self._max_temp = 30
        self._target_temp_away = None
        self._heat_level = 0
        self._heat_source_type = None
        self._gfci_status = None
        self._gfci_alert = None
        self._floor_mode = None
        self._floor_sensor_type = None
        self._em_heat = "off"
        self._aux_cycle_length = 0
        self._cycle_length_output2_status = "off"
        self._early_start = "off"
        self._keypad = None
        self._load1 = 0
        self._load2 = 0
        self._rssi = None
        self._display2 = None
        self._backlight = None
        self._time_format = "24h"
        self._floor_air_limit = None
        self._floor_air_limit_status = None
        self._floor_max = None
        self._floor_max_status = "off"
        self._floor_min = None
        self._floor_min_status = "off"
        self._temperature_format = UnitOfTemperature.CELSIUS
        self._error_code = None
        self._is_wifi_floor = (
            device_info["signature"]["model"] in DEVICE_MODEL_WIFI_FLOOR
        )
        self._is_wifi = (
            device_info["signature"]["model"] in DEVICE_MODEL_WIFI_FLOOR
            or device_info["signature"]["model"] in DEVICE_MODEL_WIFI
            or device_info["signature"]["model"] in DEVICE_MODEL_LOW_WIFI
            or device_info["signature"]["model"] in DEVICE_MODEL_WIFI_LITE
        )
        self._is_wifi_lite = False
        self._is_double = False
        self._is_low_voltage = False
        self._is_gen2 = False
        self._is_hc = False
        self._is_HC = False
        self._is_HP = False
        self._is_floor = False
        self._is_low_wifi = False
        self._energy_stat_time = time.time() - 1500
        self._snooze = 0
        self._activ = True
        _LOGGER.debug("Setting up %s: %s", self._name, device_info)

    def update(self):
        if self._activ:
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
            device_data = self._client.get_device_attributes(
                self._id, UPDATE_ATTRIBUTES + WIFI_FLOOR_ATTRIBUTES
            )
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
                    self._time_format = device_data[ATTR_TIME]
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
                    self._heat_level = device_data[ATTR_OUTPUT_PERCENT_DISPLAY][
                        "percent"
                    ]
                    self._heat_source_type = device_data[ATTR_OUTPUT_PERCENT_DISPLAY][
                        "sourceType"
                    ]
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
                        self._floor_air_limit = device_data[ATTR_FLOOR_AIR_LIMIT][
                            "value"
                        ]
                        self._floor_air_limit_status = device_data[
                            ATTR_FLOOR_AIR_LIMIT
                        ]["status"]
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
                    _LOGGER.warning(
                        "Error in updating device %s: (%s)", self._name, device_data
                    )
            else:
                self.log_error(device_data["error"]["code"])
            if self._sku != "FLP55" and self._sku != "True Comfort":
                self.do_stat(start)
            self.get_sensor_error_code(start)
        else:
            if time.time() - self._snooze > SNOOZE_TIME:
                self._activ = True
                if NOTIFY == "notification" or NOTIFY == "both":
                    self.notify_ha(
                        "Warning: Neviweb Device update restarted for "
                        + self._name
                        + ", Sku: "
                        + self._sku
                    )

    @property
    def extra_state_attributes(self):
        """Return the state attributes."""
        data = {}
        data.update(
            {
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
                "hourly_kwh": self._hour_kwh,
                "daily_kwh": self._today_kwh,
                "monthly_kwh": self._month_kwh,
                "current_hour_kwh": self._current_hour_kwh,
                "current_today_kwh": self._current_today_kwh,
                "current_month_kwh": self._current_month_kwh,
                "rssi": self._rssi,
                "sku": self._sku,
                "device_model": str(self._device_model),
                "device_model_cfg": self._device_model_cfg,
                "firmware": self._firmware,
                "activation": self._activ,
                "id": str(self._id),
            }
        )
        return data


class Neviweb130HcThermostat(Neviweb130Thermostat):
    """Implementation of Neviweb TH1134ZB-HC thermostat."""

    def __init__(self, data, device_info, name, sku, firmware):
        """Initialize."""
        self._name = name
        self._sku = sku
        self._firmware = firmware
        self._client = data.neviweb130_client
        self._id = device_info["id"]
        self._device_model = device_info["signature"]["model"]
        self._device_model_cfg = device_info["signature"]["modelCfg"]
        self._hour_kwh = 0
        self._today_kwh = 0
        self._month_kwh = 0
        self._current_hour_kwh = 0
        self._current_today_kwh = 0
        self._current_month_kwh = 0
        self._drstatus_active = "off"
        self._drstatus_optout = "off"
        self._drstatus_setpoint = "off"
        self._drstatus_abs = "off"
        self._drstatus_rel = "off"
        self._drsetpoint_status = "off"
        self._drsetpoint_value = 0
        self._cur_temp = None
        self._cur_temp_before = None
        self._target_temp = None
        self._operation_mode = None
        self._occupancy = None
        self._wattage = 0
        self._min_temp = 5
        self._max_temp = 30
        self._temperature_format = UnitOfTemperature.CELSIUS
        self._time_format = "24h"
        self._backlight = None
        self._keypad = None
        self._display2 = None
        self._temp_display_status = None
        self._temp_display_value = None
        self._heat_level = 0
        self._rssi = None
        self._target_cool = None
        self._cool_min = None
        self._cool_max = None
        self._cycle_length = 0
        self._cycle_length_output2_status = "off"
        self._aux_cycle_length = 0
        self._HC_device = None
        self._language = None
        self._model = None
        self._fan_speed = None
        self._fan_swing_vert = None
        self._fan_swing_horiz = None
        self._fan_cap = None
        self._fan_swing_cap = None
        self._fan_swing_cap_vert = None
        self._fan_swing_cap_horiz = None
        self._display_cap = None
        self._display_conf = None
        self._sound_cap = None
        self._sound_conf = None
        self._balance_pt = None
        self._heat_lock_temp = None
        self._cool_lock_temp = None
        self._avail_mode = None
        self._error_code = None
        self._is_hc = device_info["signature"]["model"] in DEVICE_MODEL_HC
        self._is_HC = False
        self._is_HP = False
        self._is_double = False
        self._is_low_voltage = False
        self._is_gen2 = False
        self._is_wifi = False
        self._is_wifi_lite = False
        self._is_wifi_floor = False
        self._is_floor = False
        self._is_low_wifi = False
        self._energy_stat_time = time.time() - 1500
        self._snooze = 0
        self._activ = True
        _LOGGER.debug("Setting up %s: %s", self._name, device_info)

    def update(self):
        if self._activ:
            HC_ATTRIBUTES = [
                ATTR_DISPLAY2,
                ATTR_RSSI,
                ATTR_COOL_SETPOINT,
                ATTR_COOL_SETPOINT_MIN,
                ATTR_COOL_SETPOINT_MAX,
                ATTR_SYSTEM_MODE,
                ATTR_CYCLE,
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
            device_data = self._client.get_device_attributes(
                self._id, UPDATE_ATTRIBUTES + HC_ATTRIBUTES
            )
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
                    self._time_format = device_data[ATTR_TIME]
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
                    self._cycle_length = device_data[ATTR_CYCLE]
                    self._target_cool = device_data[ATTR_COOL_SETPOINT]
                    self._cool_min = device_data[ATTR_COOL_SETPOINT_MIN]
                    self._cool_max = device_data[ATTR_COOL_SETPOINT_MAX]
                    self._HC_device = device_data[ATTR_HC_DEV]
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
                    _LOGGER.warning(
                        "Error in updating device %s: (%s)", self._name, device_data
                    )
            else:
                self.log_error(device_data["error"]["code"])
            if self._sku != "FLP55" and self._sku != "True Comfort":
                self.do_stat(start)
            self.get_sensor_error_code(start)
        else:
            if time.time() - self._snooze > SNOOZE_TIME:
                self._activ = True
                if NOTIFY == "notification" or NOTIFY == "both":
                    self.notify_ha(
                        "Warning: Neviweb Device update restarted for "
                        + self._name
                        + ", Sku: "
                        + self._sku
                    )

    @property
    def extra_state_attributes(self):
        """Return the state attributes."""
        data = {}
        data.update(
            {
                "wattage": self._wattage,
                "error_code": self._error_code,
                "cool setpoint min": self._cool_min,
                "cool setpoint max": self._cool_max,
                "cool setpoint": self._target_cool,
                "cycle_length": self._cycle_length,
                "hc_device": self._HC_device,
                "language": self._language,
                "model": self._model,
                "fan_speed": self._fan_speed,
                "fan_swing_vertical": self._fan_swing_vert,
                "fan_swing_horizontal": self._fan_swing_horiz,
                "fan_capability": self._fan_cap,
                "fan_swing_capability": extract_capability(self._fan_swing_cap),
                "fan_swing_capability_vertical": extract_capability_full(
                    self._fan_swing_cap_vert
                ),
                "fan_swing_capability_horizontal": extract_capability_full(
                    self._fan_swing_cap_horiz
                ),
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
                "hourly_kwh": self._hour_kwh,
                "daily_kwh": self._today_kwh,
                "monthly_kwh": self._month_kwh,
                "current_hour_kwh": self._current_hour_kwh,
                "current_today_kwh": self._current_today_kwh,
                "current_month_kwh": self._current_month_kwh,
                "rssi": self._rssi,
                "sku": self._sku,
                "device_model": str(self._device_model),
                "device_model_cfg": self._device_model_cfg,
                "firmware": self._firmware,
                "activation": self._activ,
                "id": str(self._id),
            }
        )
        return data


class Neviweb130HPThermostat(Neviweb130Thermostat):
    """Implementation of Neviweb HP6000ZB-GE, HP6000ZB-MA and HP6000ZB-HS heat pump interfaces thermostats."""

    def __init__(self, data, device_info, name, sku, firmware):
        """Initialize."""
        self._name = name
        self._sku = sku
        self._firmware = firmware
        self._client = data.neviweb130_client
        self._id = device_info["id"]
        self._device_model = device_info["signature"]["model"]
        self._device_model_cfg = device_info["signature"]["modelCfg"]
        self._drstatus_active = "off"
        self._drstatus_optout = "off"
        self._drstatus_setpoint = "off"
        self._drstatus_abs = "off"
        self._drstatus_rel = "off"
        self._drsetpoint_status = "off"
        self._drsetpoint_value = 0
        self._cur_temp = None
        self._cur_temp_before = None
        self._target_temp = None
        self._operation_mode = None
        self._min_temp = 16
        self._max_temp = 30
        self._temperature_format = UnitOfTemperature.CELSIUS
        self._keypad = None
        self._heat_level = None
        self._occupancy = None
        self._rssi = None
        self._target_cool = None
        self._cool_min = None
        self._cool_max = None
        self._model = None
        self._fan_speed = None
        self._fan_swing_vert = None
        self._fan_swing_horiz = None
        self._fan_cap = None
        self._fan_swing_cap = None
        self._fan_swing_cap_vert = None
        self._fan_swing_cap_horiz = None
        self._balance_pt = None
        self._balance_pt_low = None
        self._balance_pt_high = None
        self._heat_lock_temp = None
        self._cool_lock_temp = None
        self._avail_mode = None
        self._display_cap = None
        self._display_conf = None
        self._sound_cap = None
        self._sound_conf = None
        self._error_code = None
        self._is_HP = device_info["signature"]["model"] in DEVICE_MODEL_HEAT_PUMP
        self._is_hc = False
        self._is_HC = False
        self._is_double = False
        self._is_low_voltage = False
        self._is_gen2 = False
        self._is_wifi = False
        self._is_wifi_lite = False
        self._is_wifi_floor = False
        self._is_floor = False
        self._is_low_wifi = False
        self._energy_stat_time = time.time() - 1500
        self._snooze = 0
        self._activ = True
        _LOGGER.debug("Setting up %s: %s", self._name, device_info)

    def update(self):
        if self._activ:
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
                    self._target_temp = device_data[ATTR_ROOM_SETPOINT]
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
                    self._operation_mode = device_data[ATTR_SYSTEM_MODE]
                    if ATTR_RSSI in device_data:
                        self._rssi = device_data[ATTR_RSSI]
                    self._fan_speed = device_data[ATTR_FAN_SPEED]
                    self._fan_swing_vert = device_data[ATTR_FAN_SWING_VERT]
                    self._fan_cap = device_data[ATTR_FAN_CAP]
                    self._avail_mode = device_data[ATTR_AVAIL_MODE]
                    if ATTR_FAN_SWING_HORIZ in device_data:
                        self._fan_swing_horiz = device_data[ATTR_FAN_SWING_HORIZ]
                        self._fan_swing_cap = device_data[ATTR_FAN_SWING_CAP]
                        self._fan_swing_cap_horiz = device_data[
                            ATTR_FAN_SWING_CAP_HORIZ
                        ]
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
                    _LOGGER.warning(
                        "Error in updating device %s: (%s)", self._name, device_data
                    )
            else:
                self.log_error(device_data["error"]["code"])
            self.get_sensor_error_code(start)
        else:
            if time.time() - self._snooze > SNOOZE_TIME:
                self._activ = True
                if NOTIFY == "notification" or NOTIFY == "both":
                    self.notify_ha(
                        "Warning: Neviweb Device update restarted for "
                        + self._name
                        + ", Sku: "
                        + self._sku
                    )

    @property
    def extra_state_attributes(self):
        """Return the state attributes."""
        data = {}
        data.update(
            {
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
                    "fan_swing_capability_vertical": extract_capability_full(
                        self._fan_swing_cap_vert
                    ),
                    "fan_swing_capability_horizontal": extract_capability_full(
                        self._fan_swing_cap_horiz
                    ),
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
                "rssi": self._rssi,
                "sku": self._sku,
                "device_model": str(self._device_model),
                "device_model_cfg": self._device_model_cfg,
                "firmware": self._firmware,
                "activation": self._activ,
                "id": str(self._id),
            }
        )
        return data


class Neviweb130HeatCoolThermostat(Neviweb130Thermostat):
    """Implementation of Neviweb TH6500WF, TH6510WF, TH6250WF, TH6250WF-PRO heat cool thermostats."""

    def __init__(self, data, device_info, name, sku, firmware):
        """Initialize."""
        self._name = name
        self._sku = sku
        self._firmware = firmware
        self._client = data.neviweb130_client
        self._id = device_info["id"]
        self._device_model = device_info["signature"]["model"]
        self._device_model_cfg = device_info["signature"]["modelCfg"]
        self._drstatus_active = "off"
        self._drstatus_optout = "off"
        self._drstatus_setpoint = "off"
        self._drstatus_abs = "off"
        self._drstatus_rel = "off"
        self._drsetpoint_status = "off"
        self._drsetpoint_value = 0
        self._cur_temp = None
        self._cur_temp_before = None
        self._target_temp = None
        self._operation_mode = None
        self._min_temp = 5
        self._max_temp = 30
        self._temperature_format = UnitOfTemperature.CELSIUS
        self._time_format = "24h"
        self._heat_level = 0
        self._heat_level_source_type = None
        self._rssi = None
        self._keypad = None
        self._backlight = None
        self._backlight_auto_dim = None
        self._early_start = None
        self._target_temp_away = None
        self._cool_target_temp_away = None
        self._heatcool_setpoint_delta = None
        self._language = None
        self._heat_source_type = None
        self._aux_heat_source_type = None
        self._target_cool = None
        self._cool_min = 16
        self._cool_max = 30
        self._cool_min_time_on = None
        self._cool_min_time_off = None
        self._dual_status = None
        self._fan_filter_remain = None
        self._fan_speed = None
        self._balance_pt = -30
        self._occupancy = None
        self._cycle = None
        self._aux_cycle = None
        self._cool_cycle_length = 0
        self._humid_display = None
        self._humid_setpoint = None
        self._humidifier_type = None
        self._heat_inst_type = None
        self._heat_lock_temp = None
        self._cool_lock_temp = None
        self._heat_cool = None
        self._temp_offset_heat = None
        self._heat_interstage_delay = None
        self._cool_interstage_delay = None
        self._aux_heat_time_on = None
        self._aux_heat_start_delay = None
        self._valve_polarity = None
        self._error_code = None
        self._temp_display_status = None
        self._temp_display_value = None
        self._output_connect_state = None
        self._is_HC = device_info["signature"]["model"] in DEVICE_MODEL_HEAT_COOL
        self._is_hc = False
        self._is_HP = False
        self._is_double = False
        self._is_low_voltage = False
        self._is_gen2 = False
        self._is_wifi = True
        self._is_wifi_lite = False
        self._is_wifi_floor = False
        self._is_floor = False
        self._is_low_wifi = False
        self._energy_stat_time = time.time() - 1500
        self._snooze = 0
        self._activ = True
        _LOGGER.debug("Setting up %s: %s", self._name, device_info)

    def update(self):
        if self._activ:
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
                ATTR_VALVE_POLARITY,
                ATTR_HUMIDIFIER_TYPE,
                ATTR_HUMID_SETPOINT,
                ATTR_COOL_CYCLE_LENGTH,
                ATTR_CYCLE,
                ATTR_AUX_CYCLE,
                ATTR_HEATCOOL_SETPOINT_MIN_DELTA,
                ATTR_TEMP_OFFSET_HEAT,
                ATTR_HUMID_DISPLAY,
                ATTR_DUAL_STATUS,
                ATTR_EARLY_START,
                ATTR_ROOM_SETPOINT_AWAY,
                ATTR_COOL_SETPOINT_AWAY,
                ATTR_FAN_FILTER_REMAIN,
                ATTR_AUX_HEAT_TIMEON,
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
                    ATTR_COOL_INTERSTAGE_MIN_DELAY,
                    ATTR_DRSETPOINT,
                    ATTR_DRSTATUS,
                ]
            else:
                HC_EXTRA = []
            """Get the latest data from Neviweb and update the state."""
            start = time.time()
            _LOGGER.debug(
                "Updated attributes for %s: %s",
                self._name,
                UPDATE_HEAT_COOL_ATTRIBUTES + HC_ATTRIBUTES + HC_EXTRA,
            )
            device_data = self._client.get_device_attributes(
                self._id, UPDATE_HEAT_COOL_ATTRIBUTES + HC_ATTRIBUTES + HC_EXTRA
            )
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
                    self._target_cool = device_data[ATTR_COOL_SETPOINT]
                    self._cool_min = device_data[ATTR_COOL_SETPOINT_MIN]
                    self._cool_max = device_data[ATTR_COOL_SETPOINT_MAX]
                    self._heatcool_setpoint_delta = device_data[
                        ATTR_HEATCOOL_SETPOINT_MIN_DELTA
                    ]
                    self._temperature_format = device_data[ATTR_TEMP]
                    self._time_format = device_data[ATTR_TIME]
                    self._heat_level = device_data[ATTR_OUTPUT_PERCENT_DISPLAY][
                        "percent"
                    ]
                    self._heat_level_source_type = device_data[
                        ATTR_OUTPUT_PERCENT_DISPLAY
                    ]["sourceType"]
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
                    if ATTR_ROOM_TEMP_DISPLAY in device_data:
                        self._temp_display_status = device_data[ATTR_ROOM_TEMP_DISPLAY][
                            "status"
                        ]
                        self._temp_display_value = device_data[ATTR_ROOM_TEMP_DISPLAY][
                            "value"
                        ]
                    self._heat_cool = device_data[ATTR_HEAT_COOL]
                    self._language = device_data[ATTR_LANGUAGE]
                    self._occupancy = device_data[ATTR_OCCUPANCY]
                    self._keypad = device_data[ATTR_WIFI_KEYPAD]
                    if ATTR_BACK_LIGHT in device_data:
                        self._backlight = device_data[ATTR_BACK_LIGHT]
                    self._backlight_auto_dim = device_data[ATTR_BACKLIGHT_AUTO_DIM]
                    self._early_start = device_data[ATTR_EARLY_START]
                    self._target_temp_away = device_data[ATTR_ROOM_SETPOINT_AWAY]
                    self._cool_target_temp_away = device_data[ATTR_COOL_SETPOINT_AWAY]
                    self._valve_polarity = device_data[ATTR_VALVE_POLARITY]
                    self._heat_lock_temp = device_data[ATTR_HEAT_LOCK_TEMP]
                    self._cool_lock_temp = device_data[ATTR_COOL_LOCK_TEMP]
                    self._balance_pt = device_data[ATTR_BALANCE_PT]
                    self._humid_display = device_data[ATTR_HUMID_DISPLAY]
                    self._humid_setpoint = device_data[ATTR_HUMID_SETPOINT]
                    self._humidifier_type = device_data[ATTR_HUMIDIFIER_TYPE]
                    self._cycle = device_data[ATTR_CYCLE]
                    self._aux_cycle = device_data[ATTR_AUX_CYCLE]
                    self._cool_cycle_length = device_data[ATTR_COOL_CYCLE_LENGTH]
                    self._temp_offset_heat = device_data[ATTR_TEMP_OFFSET_HEAT]
                    self._aux_heat_time_on = device_data[ATTR_AUX_HEAT_TIMEON]
                    self._aux_heat_start_delay = device_data[ATTR_AUX_HEAT_START_DELAY]
                    if ATTR_HEAT_INTERSTAGE_MIN_DELAY in device_data:
                        self._heat_interstage_delay = device_data[
                            ATTR_HEAT_INTERSTAGE_MIN_DELAY
                        ]
                        self._cool_interstage_delay = device_data[
                            ATTR_COOL_INTERSTAGE_MIN_DELAY
                        ]
                    self._dual_status = device_data[ATTR_DUAL_STATUS]
                    self._cool_min_time_on = device_data[ATTR_COOL_MIN_TIME_ON]
                    self._cool_min_time_off = device_data[ATTR_COOL_MIN_TIME_OFF]
                    if ATTR_HEAT_INSTALL_TYPE in device_data:
                        self._heat_inst_type = device_data[ATTR_HEAT_INSTALL_TYPE]
                    self._output_connect_state = device_data[ATTR_OUTPUT_CONNECT_STATE]
                elif device_data["errorCode"] == "ReadTimeout":
                    _LOGGER.warning(
                        "A timeout occur during data update. Device %s do not respond. Check your network... (%s)",
                        self._name,
                        device_data,
                    )
                else:
                    _LOGGER.warning(
                        "Error in updating device %s: (%s)", self._name, device_data
                    )
            else:
                self.log_error(device_data["error"]["code"])
            self.get_sensor_error_code(start)
        else:
            if time.time() - self._snooze > SNOOZE_TIME:
                self._activ = True
                if NOTIFY == "notification" or NOTIFY == "both":
                    self.notify_ha(
                        "Warning: Neviweb Device update restarted for "
                        + self._name
                        + ", Sku: "
                        + self._sku
                    )

    @property
    def extra_state_attributes(self):
        """Return the state attributes."""
        data = {}
        data.update(
            {
                "error_code": self._error_code,
                "operation modes": self._operation_mode,
                "cool setpoint": self._target_cool,
                "cool setpoint min": self._cool_min,
                "cool setpoint max": self._cool_max,
                "setpoint_max": self._max_temp,
                "setpoint_min": self._min_temp,
                "temperature_format": self._temperature_format,
                "time_format": self._time_format,
                "keypad": lock_to_ha(self._keypad),
                "fan_speed": self._fan_speed,
                "backlight": self._backlight,
                "backlight-auto_dim": self._backlight_auto_dim,
                "early_start": self._early_start,
                "target_temp_away": self._target_temp_away,
                "cool_target_temp_away": self._cool_target_temp_away,
                "heat_cool_setpoint_delta": self._heatcool_setpoint_delta,
                "language": self._language,
                "occupancy": self._occupancy,
                "heat_source_type": self._heat_source_type,
                "heat_level_source_type": self._heat_level_source_type,
                "aux_heat_source_type": self._aux_heat_source_type,
                "fan_filter_remain": self._fan_filter_remain,
                "cycle": self._cycle,
                "aux_cycle": self._aux_cycle,
                "cool_cycle_length": self._cool_cycle_length,
                "humid_display": self._humid_display,
                "humid_setpoint": self._humid_setpoint,
                "humidifier_type": self._humidifier_type,
                "heat_cool": self._heat_cool,
                "temp_offset_heat": self._temp_offset_heat,
                "cool_min_time_on": self._cool_min_time_on,
                "cool_min_time_off": self._cool_min_time_off,
                "heat_installation_type": self._heat_inst_type,
                "aux_heat_time_on": self._aux_heat_time_on,
                "aux_heat_start_delay": self._aux_heat_start_delay,
                "valve_polarity": self._valve_polarity,
                "temp_display_status": self._temp_display_status,
                "temp_display_value": self._temp_display_value,
                "dual_status": self._dual_status,
                "balance_point": self._balance_pt,
                "heat_lock_temp": self._heat_lock_temp,
                "cool_lock_temp": self._cool_lock_temp,
                "output_connect_state": self._output_connect_state,
                "rssi": self._rssi,
                "sku": self._sku,
                "device_model": str(self._device_model),
                "device_model_cfg": self._device_model_cfg,
                "firmware": self._firmware,
                "activation": self._activ,
                "id": str(self._id),
            }
        )
        if self._device_model == 6727:
            data.update(
                {
                    "heat_interstage_delay": self._heat_interstage_delay,
                    "cool_interstage_delay": self._cool_interstage_delay,
                    "eco_status": self._drstatus_active,
                    "eco_optOut": self._drstatus_optout,
                    "eco_setpoint": self._drstatus_setpoint,
                    "eco_power_relative": self._drstatus_rel,
                    "eco_power_absolute": self._drstatus_abs,
                    "eco_setpoint_status": self._drsetpoint_status,
                    "eco_setpoint_delta": self._drsetpoint_value,
                }
            )
        return data
