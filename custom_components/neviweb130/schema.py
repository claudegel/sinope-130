"""Schema for config entry and services."""

from __future__ import annotations

from datetime import timedelta

import voluptuous as vol
from homeassistant.components.climate.const import HVACMode
from homeassistant.const import ATTR_ENTITY_ID, CONF_PASSWORD, CONF_SCAN_INTERVAL, CONF_USERNAME, Platform
from homeassistant.helpers import config_validation as cv
from homeassistant.helpers import selector

from .const import (
    ATTR_ACCESSORY_TYPE,
    ATTR_ACTIVE,
    ATTR_AIR_EX_MIN_TIME_ON,
    ATTR_AUX_HEAT_MIN_TIME_OFF,
    ATTR_AUX_HEAT_MIN_TIME_ON,
    ATTR_AUX_HEAT_SOURCE_TYPE,
    ATTR_AUX_OPTIM,
    ATTR_BACKLIGHT,
    ATTR_BALANCE_PT,
    ATTR_BATT_ALERT,
    ATTR_BATTERY_TYPE,
    ATTR_CLOSE_VALVE,
    ATTR_COLD_LOAD_PICKUP_REMAIN_TIME,
    ATTR_COLOR,
    ATTR_CONF_CLOSURE,
    ATTR_COOL_LOCK_TEMP,
    ATTR_COOL_MIN_TIME_OFF,
    ATTR_COOL_MIN_TIME_ON,
    ATTR_COOL_SETPOINT_AWAY,
    ATTR_COOL_SETPOINT_MAX,
    ATTR_COOL_SETPOINT_MIN,
    ATTR_DISPLAY2,
    ATTR_DISPLAY_CONF,
    ATTR_DRACTIVE,
    ATTR_EARLY_START,
    ATTR_FAN_FILTER_REMAIN,
    ATTR_FAN_SPEED,
    ATTR_FAN_SPEED_OPTIM,
    ATTR_FLOOR_AIR_LIMIT,
    ATTR_FLOOR_MAX,
    ATTR_FLOOR_MIN,
    ATTR_FLOOR_MODE,
    ATTR_FLOOR_SENSOR,
    ATTR_FLOW_ALARM1_PERIOD,
    ATTR_FLOW_ALARM_TIMER,
    ATTR_FLOW_MODEL_CONFIG,
    ATTR_FUEL_ALERT,
    ATTR_FUEL_PERCENT_ALERT,
    ATTR_GAUGE_TYPE,
    ATTR_HEAT_LOCK_TEMP,
    ATTR_HEAT_LOCKOUT_TEMP,
    ATTR_HEAT_MIN_TIME_OFF,
    ATTR_HEAT_MIN_TIME_ON,
    ATTR_HEATCOOL_SETPOINT_MIN_DELTA,
    ATTR_HUMIDITY_SETPOINT_MODE,
    ATTR_INTENSITY_MIN,
    ATTR_KEY_DOUBLE_UP,
    ATTR_KEYPAD,
    ATTR_LANGUAGE,
    ATTR_LEAK_ALERT,
    ATTR_LED_OFF_INTENSITY,
    ATTR_LED_ON_INTENSITY,
    ATTR_LIGHT_WATTAGE,
    ATTR_MODE,
    ATTR_NAME_1,
    ATTR_NAME_2,
    ATTR_ONOFF,
    ATTR_ONOFF_NUM,
    ATTR_OPTOUT,
    ATTR_OUTPUT_NAME_1,
    ATTR_OUTPUT_NAME_2,
    ATTR_PHASE_CONTROL,
    ATTR_POLARITY,
    ATTR_POWER_SUPPLY,
    ATTR_REFUEL,
    ATTR_ROOM_SETPOINT_AWAY,
    ATTR_ROOM_SETPOINT_MAX,
    ATTR_ROOM_SETPOINT_MIN,
    ATTR_SETPOINT,
    ATTR_SETPOINT_MODE,
    ATTR_SOUND_CONF,
    ATTR_STATE,
    ATTR_STATUS,
    ATTR_TANK_HEIGHT,
    ATTR_TANK_TYPE,
    ATTR_TEMP,
    ATTR_TEMP_ALERT,
    ATTR_TEMP_OFFSET_HEAT,
    ATTR_TIME,
    ATTR_TIME_FORMAT,
    ATTR_TIMER,
    ATTR_TIMER2,
    ATTR_TRIGGER_ALARM,
    ATTR_VALUE,
    ATTR_WATER_TEMP_MIN,
    CONF_HOMEKIT_MODE,
    CONF_IGNORE_MIWI,
    CONF_NETWORK,
    CONF_NETWORK2,
    CONF_NETWORK3,
    CONF_NOTIFY,
    CONF_PREFIX,
    CONF_STAT_INTERVAL,
    DOMAIN,
)

"""Default parameters values."""

SCAN_INTERVAL = 420  # seconds
HOMEKIT_MODE = False
STAT_INTERVAL = 1800
IGNORE_MIWI = False
NOTIFY = "both"
PREFIX = "default"

PLATFORMS = [
    Platform.CLIMATE,
    Platform.LIGHT,
    Platform.SENSOR,
    Platform.SWITCH,
    Platform.VALVE,
    Platform.BINARY_SENSOR,
    Platform.BUTTON,
    Platform.NUMBER,
    Platform.SELECT,
    Platform.UPDATE,
]

HA_TO_NEVIWEB_CONTROLLED = {
    "Hot water heater": "hotWaterHeater",
    "Pool pump": "poolPump",
    "Electric vehicle charger": "electricVehicleCharger",
    "Other": "other",
}

HA_TO_NEVIWEB_DELAY = {
    "off": 0,
    "1 min": 60,
    "2 min": 120,
    "5 min": 300,
    "10 min": 600,
    "15 min": 900,
    "30 min": 1800,
    "45 min": 2700,
    "60 min": 3600,
    "75 min": 4500,
    "90 min": 5400,
    "1 h": 3600,
    "2 h": 7200,
    "3 h": 10800,
    "6 h": 21600,
    "12 h": 43200,
    "24 h": 86400,
    "48 h": 172800,
    "1 week": 604800,
}

HA_TO_NEVIWEB_DURATION = {
    "off": 0,
    "15 min": 900,
    "30 min": 1800,
    "45 min": 2700,
    "60 min": 3600,
    "75 min": 4500,
    "90 min": 5400,
    "3 h": 10800,
    "6 h": 21600,
    "12 h": 43200,
    "24 h": 86400,
}

HA_TO_NEVIWEB_FAN_SPEED: dict[str, int] = {
    "off": 0,
    "low": 40,
    "medium": 60,
    "high": 80,
    "auto": 128,
}

HA_TO_NEVIWEB_FAN_SPEED_5: dict[str, int] = {
    "off": 0,
    "low": 20,
    "low-medium": 40,
    "medium": 60,
    "medium-high": 80,
    "high": 100,
    "auto": 128,
}

HA_TO_NEVIWEB_FLOW = {
    "No flow": "No flow meter",
    "FS4220 3/4 inch": "FS4220",
    "FS4221 1 inch": "FS4221",
}

HA_TO_NEVIWEB_GAUGE = {"R3D 5-95": 595, "R3D 10-80": 1080}

HA_TO_NEVIWEB_HEIGHT = {
    "none": 0,
    "23 inch": 23,
    "24 inch": 24,
    "35 inch": 35,
    "38 inch": 38,
    "47 inch": 47,
    "48 inch": 48,
    "50 inch": 50,
}

HA_TO_NEVIWEB_LEVEL = {"off": 0, "10%": 10, "20%": 20, "30%": 30}

HA_TO_NEVIWEB_MODE = {
    HVACMode.OFF: "off",
    HVACMode.HEAT: "heat",
    HVACMode.COOL: "cool",
    HVACMode.AUTO: "auto",
    HVACMode.DRY: "dry",
    HVACMode.FAN_ONLY: "fanOnly",
    HVACMode.HEAT_COOL: "auto",
}

HA_TO_NEVIWEB_OPTION: dict[str, tuple[bool, bool]] = {
    "fermer la valve et envoyer une alerte": (True, True),
    "alerte seulement": (False, True),
    "aucune action": (False, False),
}

HA_TO_NEVIWEB_PERIOD = {
    "off": 0,
    "1 sec": 1,
    "15 sec": 15,
    "5 min": 300,
    "10 min": 600,
    "15 min": 900,
    "20 min": 1200,
    "25 min": 1500,
    "30 min": 1800,
}

HA_TO_NEVIWEB_SIZE = {"40 gal": 40, "50 gal": 50, "60 gal": 60, "80 gal": 80}

HA_TO_NEVIWEB_SUPPLY = {"Battery": "batt", "ACUPS-01": "power", "Battery and ACUPS-01": "both"}

HA_TO_NEVIWEB_TEMPERATURE = {
    "off": 0,
    "45°C": 45,
    "46°C": 46,
    "47°C": 47,
    "48°C": 48,
    "49°C": 49,
    "50°C": 50,
    "51°C": 51,
    "52°C": 52,
    "53°C": 53,
    "54°C": 54,
    "55°C": 55,
}

HA_TO_NEVIWEB_TIMER = {
    "off": 0,
    "1 min": 1,
    "2 min": 2,
    "5 min": 5,
    "10 min": 600,
    "15 min": 900,
    "30 min": 1800,
    "1 hr": 3600,
    "2 hrs": 7200,
    "3 hrs": 10800,
    "6 hrs": 21600,
    "12 hrs": 43200,
    "24 hrs": 86400,
}

PERIOD_VALUE = list(HA_TO_NEVIWEB_PERIOD.keys())

ACCESSORY = [
    "none",
    "humOnHeat",
    "humOnFan",
    "dehum",
    "airExchanger",
]

TH6_MODES_VALUES: dict[str, str] = {
    "heatStage1": "heatStage1RuntimeAndTimestamp",
    "heatStage2": "heatStage2RuntimeAndTimestamp",
    "coolStage1": "coolStage1RuntimeAndTimestamp",
    "coolStage2": "coolStage2RuntimeAndTimestamp",
    "auxHeatStage1": "auxHeatStage1RuntimeAndTimestamp",
    "auxHeatStage2": "auxHeatStage2RuntimeAndTimestamp",
    "fan": "fanRuntimeAndTimestamp",
    "emergencyHeat": "emergencyHeatRuntimeAndTimestamp",
}

AIR_EX_MIN_TIME_ON = ["Off", "20 min", "40 min", "Continuous"]
AUX_HEATING = {"Electric": "hvacElectrique", "Fossil": "hvacGaz"}
BACKLIGHT_LIST = ["auto", "on", "bedroom"]
BATT_TYPE_LIST = ["alkaline", "lithium"]
COLOR_LIST = ["lime", "amber", "fuchsia", "perle", "blue", "red", "orange", "green"]
CONTROLLED_VALUE = list(HA_TO_NEVIWEB_CONTROLLED.keys())
DELAY = [
    label for label, seconds in HA_TO_NEVIWEB_DELAY.items()
    if seconds <= 10800
]
DISPLAY_CAPABILITY = ["enable", "disable"]
DISPLAY_LIST = ["exteriorTemperature", "setpoint", "default"]
FAN_CAPABILITY = ["low", "med", "high", "auto"]
FAN_SPEED = ["high", "medium", "low", "auto", "off"]
FAN_SWING_CAPABILITY = ["fullHorizontal", "autoHorizontal", "fullVertical", "autoVertical"]
FLOOR_MODE = ["airByFloor", "roomByFloor", "floor"]
FLOW_DURATION = list(HA_TO_NEVIWEB_DURATION.keys())
FLOW_MODEL = list(HA_TO_NEVIWEB_FLOW.keys())
FLOW_OPTION = list(HA_TO_NEVIWEB_OPTION.keys())
FUEL_LIST = ["propane", "oil"]
FULL_SWING = ["swingFullRange"]
FULL_SWING_OFF = ["off"]
GAUGE_LIST = list(HA_TO_NEVIWEB_GAUGE.keys())
HC_DISPLAY_LIST = ["exteriorTemperature", "setpoint", "none"]
HP_FAN_SPEED = ["high", "medium", "low", "auto"]
HUMIDIFIER_TYPE = ["none", "steam", "flowthrough"]
INSTALL_TYPE = ["addOn", "Conventional"]
LANGUAGE_LIST = ["fr", "en"]
LOCK_LIST = ["locked", "unlocked", "partiallyLocked"]
LOW_FUEL_LEVEL = list(HA_TO_NEVIWEB_LEVEL.keys())
LV_AUX_CYCLE = ["off", "15 sec", "5 min", "10 min", "15 min", "20 min", "25 min", "30 min"]
LV_CYCLE = ["15 sec", "5 min", "10 min", "15 min", "20 min", "25 min", "30 min"]
MIN_TIME = [120, 180, 240, 300, 600]
OCCUPANCY_LIST = ["home", "away"]
ON_OFF = ["off", "on"]
PHASE_LIST = ["reverse", "forward"]
POWER_TIMER_LIST = list(HA_TO_NEVIWEB_TIMER.keys())
# for TH6250WF-PRO, TH6500WF and TH6510WF
PRO_AUX_CYCLE = ["off", "1 sec", "15 sec", "10 min", "15 min", "20 min", "25 min"]
REVERSING_VALVE_POLARITY = ["cooling", "heating"]
SCHEDULE_LIST = ["auto", "manual"]
SENSOR_LIST = ["10k", "12k"]
STD_CYCLE = ["15 sec", "15 min"]
SOUND_CAPABILITY = ["enable", "disable"]
SUPPLY_LIST = list(HA_TO_NEVIWEB_SUPPLY.keys())
SWING_CAPABILITY_HORIZONTAL = [
    "swingFullRange",
    "off",
    "fixedRegion1",
    "fixedRegion2",
    "fixedRegion3",
    "fixedRegion4",
    "fixedRegion5",
    "fixedRegion6",
    "fixedRegion7",
    "fixedRegion8",
    "swingRegion1",
    "swingRegion2",
    "swingRegion3",
    "swingRegion3",
    "swingRegion5",
    "swingRegion6",
    "swingRegion7",
    "swingRegion8",
]
SWING_CAPABILITY_VERTICAL = [
    "swingFullRange",
    "off",
    "fixedRegion1",
    "fixedRegion2",
    "fixedRegion3",
    "fixedRegion4",
    "fixedRegion5",
    "fixedRegion6",
    "fixedRegion7",
    "fixedRegion8",
    "swingRegion1",
    "swingRegion2",
    "swingRegion3",
    "swingRegion3",
    "swingRegion5",
    "swingRegion6",
    "swingRegion7",
    "swingRegion8",
]
TANK_HEIGHT = list(HA_TO_NEVIWEB_HEIGHT.keys())
TANK_VALUE = list(HA_TO_NEVIWEB_SIZE.keys())
TEMP_LIST = ["celsius", "fahrenheit"]
TIME_LIST = ["24h", "12h"]
TIMER_LIST = [
    label for label, seconds in HA_TO_NEVIWEB_TIMER.items()
    if seconds <= 10800
]
TRUE_LIST = [True, False]
WATER_TEMP = list(HA_TO_NEVIWEB_TEMPERATURE.keys())
WIFI_CYCLE = ["10 min", "15 min", "20 min", "25 min"]
WIFI_FAN_SPEED = ["auto", "on"]


def is_valid_remaining_time(value: int) -> int:
    if value == 65535:
        return value
    if value % 900 != 0:
        raise vol.Invalid("Value must be a multiple of 900 or equal to 65535.")
    return value


def color_to_rgb(color):
    """Convert color to rgb tuple. (red,green,blue)"""
    match color:
        case "lime":
            return "220,255,10"
        case "amber":
            return "75,10,0"
        case "fuchsia":
            return "165,0,10"
        case "perle":
            return "255,255,100"
        case "blue":
            return "0,255,255"
        case "red":
            return "255,0,0"
        case "orange":
            return "255,165,0"
        case "green":
            return "0,255,0"
        case _:
            return None


def rgb_to_color(rgb):
    """Convert rgb tuple to color. (red,green,blue)"""
    match rgb:
        case "220,255,10":
            return "lime"
        case "75,10,0":
            return "amber"
        case "165,0,10":
            return "fuchsia"
        case "255,255,100":
            return "perle"
        case "0,255,255":
            return "blue"
        case "255,0,0":
            return "red"
        case "255,165,0":
            return "orange"
        case _:
            return None


"""Config schema."""

CONFIG_SCHEMA = vol.Schema(
    {
        DOMAIN: vol.Schema(
            {
                vol.Optional(CONF_PREFIX, default=PREFIX): cv.string,
                vol.Required(CONF_USERNAME): cv.string,
                vol.Required(CONF_PASSWORD): cv.string,
                vol.Optional(CONF_NETWORK, default="_"): cv.string,
                vol.Optional(CONF_NETWORK2, default="_"): cv.string,
                vol.Optional(CONF_NETWORK3, default="_"): cv.string,
                vol.Optional(CONF_SCAN_INTERVAL, default=SCAN_INTERVAL): selector.NumberSelector(
                    selector.NumberSelectorConfig(
                        min=300,
                        max=600,
                        unit_of_measurement="s",
                        mode=selector.NumberSelectorMode.BOX,
                    )
                ),
                vol.Optional(CONF_HOMEKIT_MODE, default=HOMEKIT_MODE): cv.boolean,
                vol.Optional(CONF_IGNORE_MIWI, default=IGNORE_MIWI): cv.boolean,
                vol.Optional(CONF_STAT_INTERVAL, default=STAT_INTERVAL): vol.All(
                    vol.Coerce(int), vol.Range(min=300, max=1800)
                ),
                vol.Optional(CONF_NOTIFY, default=NOTIFY): vol.In(["both", "logging", "nothing", "notification"]),
            }
        )
    },
    extra=vol.ALLOW_EXTRA,
)

"""Climate schema."""

SET_SECOND_DISPLAY_SCHEMA = vol.Schema({
        vol.Required(ATTR_ENTITY_ID): cv.entity_id,
        vol.Required(ATTR_DISPLAY2): vol.In(DISPLAY_LIST),
    })

SET_BACKLIGHT_SCHEMA = vol.Schema({
        vol.Required(ATTR_ENTITY_ID): cv.entity_id,
        vol.Required(ATTR_BACKLIGHT): vol.In(BACKLIGHT_LIST),
    })

SET_CLIMATE_KEYPAD_LOCK_SCHEMA = vol.Schema({
        vol.Required(ATTR_ENTITY_ID): cv.entity_id,
        vol.Required(ATTR_KEYPAD): vol.In(LOCK_LIST),
    })

SET_EM_HEAT_SCHEMA = vol.Schema({
        vol.Required(ATTR_ENTITY_ID): cv.entity_id,
        vol.Required(ATTR_VALUE): vol.In(ON_OFF),
    })

SET_TIME_FORMAT_SCHEMA = vol.Schema({
        vol.Required(ATTR_ENTITY_ID): cv.entity_id,
        vol.Required(ATTR_TIME_FORMAT): vol.In(TIME_LIST),
    })

SET_TEMPERATURE_FORMAT_SCHEMA = vol.Schema({
        vol.Required(ATTR_ENTITY_ID): cv.entity_id,
        vol.Required(ATTR_TEMP): vol.In(TEMP_LIST),
    })

SET_SETPOINT_MAX_SCHEMA = vol.Schema({
        vol.Required(ATTR_ENTITY_ID): cv.entity_id,
        vol.Required(ATTR_ROOM_SETPOINT_MAX): vol.All(vol.Coerce(float), vol.Range(min=6, max=30)),
    })

SET_SETPOINT_MIN_SCHEMA = vol.Schema({
        vol.Required(ATTR_ENTITY_ID): cv.entity_id,
        vol.Required(ATTR_ROOM_SETPOINT_MIN): vol.All(vol.Coerce(float), vol.Range(min=5, max=29)),
    })

SET_FLOOR_AIR_LIMIT_SCHEMA = vol.Schema({
        vol.Required(ATTR_ENTITY_ID): cv.entity_id,
        vol.Required(ATTR_FLOOR_AIR_LIMIT): vol.All(vol.Coerce(float), vol.Range(min=0, max=36)),
    })

SET_EARLY_START_SCHEMA = vol.Schema({
        vol.Required(ATTR_ENTITY_ID): cv.entity_id,
        vol.Required(ATTR_EARLY_START): vol.In(ON_OFF),
    })

SET_AIR_FLOOR_MODE_SCHEMA = vol.Schema({
        vol.Required(ATTR_ENTITY_ID): cv.entity_id,
        vol.Required(ATTR_FLOOR_MODE): vol.In(FLOOR_MODE),
    })

SET_HVAC_DR_OPTIONS_SCHEMA = vol.Schema({
        vol.Required(ATTR_ENTITY_ID): cv.entity_id,
        vol.Required(ATTR_DRACTIVE): vol.In(ON_OFF),
        vol.Required(ATTR_OPTOUT): vol.In(ON_OFF),
        vol.Required(ATTR_SETPOINT): vol.In(ON_OFF),
        vol.Optional(ATTR_AUX_OPTIM): vol.In(ON_OFF),
        vol.Optional(ATTR_FAN_SPEED_OPTIM): vol.In(ON_OFF),
    })

SET_HVAC_DR_SETPOINT_SCHEMA = vol.Schema({
        vol.Required(ATTR_ENTITY_ID): cv.entity_id,
        vol.Required(ATTR_STATUS): vol.In(ON_OFF),
        vol.Required(ATTR_VALUE): vol.All(vol.Coerce(float), vol.Range(min=-10, max=10)),
    })

SET_COOL_SETPOINT_MAX_SCHEMA = vol.Schema({
        vol.Required(ATTR_ENTITY_ID): cv.entity_id,
        vol.Required(ATTR_COOL_SETPOINT_MAX): vol.All(vol.Coerce(float), vol.Range(min=16, max=36)),
    })

SET_COOL_SETPOINT_MIN_SCHEMA = vol.Schema({
        vol.Required(ATTR_ENTITY_ID): cv.entity_id,
        vol.Required(ATTR_COOL_SETPOINT_MIN): vol.All(vol.Coerce(float), vol.Range(min=15, max=35)),
    })

SET_ROOM_SETPOINT_AWAY_SCHEMA = vol.Schema({
        vol.Required(ATTR_ENTITY_ID): cv.entity_id,
        vol.Required(ATTR_ROOM_SETPOINT_AWAY): vol.All(vol.Coerce(float), vol.Range(min=10, max=30)),
    })

SET_COOL_SETPOINT_AWAY_SCHEMA = vol.Schema({
        vol.Required(ATTR_ENTITY_ID): cv.entity_id,
        vol.Required(ATTR_COOL_SETPOINT_AWAY): vol.All(vol.Coerce(float), vol.Range(min=15, max=35)),
    })

SET_AUXILIARY_LOAD_SCHEMA = vol.Schema({
        vol.Required(ATTR_ENTITY_ID): cv.entity_id,
        vol.Required(ATTR_STATUS): vol.In(ON_OFF),
        vol.Required(ATTR_VALUE): vol.All(vol.Coerce(int), vol.Range(min=0, max=4000)),
    })

SET_AUX_CYCLE_OUTPUT_SCHEMA = vol.Schema({
        vol.Required(ATTR_ENTITY_ID): cv.entity_id,
        vol.Required(ATTR_VALUE): vol.In(PERIOD_VALUE),
    })

SET_CYCLE_OUTPUT_SCHEMA = vol.Schema({
        vol.Required(ATTR_ENTITY_ID): cv.entity_id,
        vol.Required(ATTR_VALUE): vol.In(PERIOD_VALUE),
    })

SET_PUMP_PROTECTION_SCHEMA = vol.Schema({
        vol.Required(ATTR_ENTITY_ID): cv.entity_id,
        vol.Required(ATTR_STATUS): vol.In(ON_OFF),
    })

SET_FLOOR_LIMIT_LOW_SCHEMA = vol.Schema({
        vol.Required(ATTR_ENTITY_ID): cv.entity_id,
        vol.Required(ATTR_FLOOR_MIN): vol.All(vol.Coerce(float), vol.Range(min=0, max=34)),
    })

SET_FLOOR_LIMIT_HIGH_SCHEMA = vol.Schema({
        vol.Required(ATTR_ENTITY_ID): cv.entity_id,
        vol.Required(ATTR_FLOOR_MAX): vol.All(vol.Coerce(float), vol.Range(min=0, max=36)),
    })

SET_ACTIVATION_SCHEMA = vol.Schema({
        vol.Required(ATTR_ENTITY_ID): cv.entity_id,
        vol.Required(ATTR_ACTIVE): vol.In(TRUE_LIST),
    })

SET_SENSOR_TYPE_SCHEMA = vol.Schema({
        vol.Required(ATTR_ENTITY_ID): cv.entity_id,
        vol.Required(ATTR_FLOOR_SENSOR): vol.In(SENSOR_LIST),
    })

SET_HEAT_PUMP_OPERATION_LIMIT_SCHEMA = vol.Schema({
        vol.Required(ATTR_ENTITY_ID): cv.entity_id,
        vol.Required(ATTR_BALANCE_PT): vol.All(vol.Coerce(int), vol.Range(min=-30, max=0)),
    })

SET_COOL_LOCKOUT_TEMPERATURE_SCHEMA = vol.Schema({
        vol.Required(ATTR_ENTITY_ID): cv.entity_id,
        vol.Required(ATTR_COOL_LOCK_TEMP): vol.All(
            lambda v: int(v) if v != "off" else None, vol.Any(None, vol.Range(min=0, max=30))
        ),
    })

SET_HEAT_LOCKOUT_TEMPERATURE_SCHEMA = vol.Schema({
        vol.Required(ATTR_ENTITY_ID): cv.entity_id,
        vol.Required(vol.Any(ATTR_HEAT_LOCK_TEMP, ATTR_HEAT_LOCKOUT_TEMP)): vol.All(
            lambda v: int(v) if v != "off" else None,
            vol.Any(None, vol.Range(min=10, max=30))
        ),
    })

SET_DISPLAY_CONFIG_SCHEMA = vol.Schema({
        vol.Required(ATTR_ENTITY_ID): cv.entity_id,
        vol.Required(ATTR_DISPLAY_CONF): vol.In(DISPLAY_CAPABILITY),
    })

SET_SOUND_CONFIG_SCHEMA = vol.Schema({
        vol.Required(ATTR_ENTITY_ID): cv.entity_id,
        vol.Required(ATTR_SOUND_CONF): vol.In(SOUND_CAPABILITY),
    })

SET_HC_SECOND_DISPLAY_SCHEMA = vol.Schema({
        vol.Required(ATTR_ENTITY_ID): cv.entity_id,
        vol.Required(ATTR_DISPLAY2): vol.In(HC_DISPLAY_LIST),
    })

SET_LANGUAGE_SCHEMA = vol.Schema({
        vol.Required(ATTR_ENTITY_ID): cv.entity_id,
        vol.Required(ATTR_LANGUAGE): vol.In(LANGUAGE_LIST),
    })

SET_REVERSING_VALVE_POLARITY_SCHEMA = vol.Schema({
        vol.Required(ATTR_ENTITY_ID): cv.entity_id,
        vol.Required(ATTR_POLARITY): vol.In(REVERSING_VALVE_POLARITY),
    })

SET_MIN_TIME_ON_SCHEMA = vol.Schema({
        vol.Required(ATTR_ENTITY_ID): cv.entity_id,
        vol.Optional(ATTR_HEAT_MIN_TIME_ON): vol.In(MIN_TIME),
        vol.Optional(ATTR_AUX_HEAT_MIN_TIME_ON): vol.In(MIN_TIME),
        vol.Optional(ATTR_COOL_MIN_TIME_ON): vol.In(MIN_TIME),
        vol.Optional(ATTR_AIR_EX_MIN_TIME_ON): vol.In(AIR_EX_MIN_TIME_ON),
    })

SET_MIN_TIME_OFF_SCHEMA = vol.Schema({
        vol.Required(ATTR_ENTITY_ID): cv.entity_id,
        vol.Optional(ATTR_HEAT_MIN_TIME_OFF): vol.In(MIN_TIME),
        vol.Optional(ATTR_AUX_HEAT_MIN_TIME_OFF): vol.In(MIN_TIME),
        vol.Optional(ATTR_COOL_MIN_TIME_OFF): vol.In(MIN_TIME),
    })

SET_HEAT_INTERSTAGE_DELAY_SCHEMA = vol.Schema({
        vol.Required(ATTR_ENTITY_ID): cv.entity_id,
        vol.Required(ATTR_TIME): vol.Range(min=1, max=60),
    })

SET_COOL_INTERSTAGE_DELAY_SCHEMA = vol.Schema({
        vol.Required(ATTR_ENTITY_ID): cv.entity_id,
        vol.Required(ATTR_TIME): vol.Range(min=1, max=60),
    })

SET_ACCESSORY_TYPE_SCHEMA = vol.Schema({
        vol.Required(ATTR_ENTITY_ID): cv.entity_id,
        vol.Required(ATTR_ACCESSORY_TYPE): vol.In(ACCESSORY),
    })

SET_SCHEDULE_MODE_SCHEMA = vol.Schema({
        vol.Required(ATTR_ENTITY_ID): cv.entity_id,
        vol.Required(ATTR_SETPOINT_MODE): vol.In(SCHEDULE_LIST),
    })

SET_HEATCOOL_SETPOINT_DELTA_SCHEMA = vol.Schema({
        vol.Required(ATTR_ENTITY_ID): cv.entity_id,
        vol.Required(ATTR_HEATCOOL_SETPOINT_MIN_DELTA): vol.All(vol.Coerce(int), vol.Range(min=1, max=5)),
    })

SET_FAN_FILTER_REMINDER_SCHEMA = vol.Schema({
        vol.Required(ATTR_ENTITY_ID): cv.entity_id,
        vol.Required(ATTR_FAN_FILTER_REMAIN): vol.All(vol.Coerce(int), vol.Range(min=1, max=12)),
    })

SET_TEMPERATURE_OFFSET_SCHEMA = vol.Schema({
        vol.Required(ATTR_ENTITY_ID): cv.entity_id,
        vol.Required(ATTR_TEMP_OFFSET_HEAT): vol.All(vol.Coerce(int), vol.Range(min=-2, max=2)),
    })

SET_AUX_HEATING_SOURCE_SCHEMA = vol.Schema({
        vol.Required(ATTR_ENTITY_ID): cv.entity_id,
        vol.Required(ATTR_AUX_HEAT_SOURCE_TYPE): vol.In(AUX_HEATING.keys()),
    })

SET_FAN_SPEED_SCHEMA = vol.Schema({
        vol.Required(ATTR_ENTITY_ID): cv.entity_id,
        vol.Required(ATTR_FAN_SPEED): vol.In(["On", "Auto"]),
    })

SET_HUMIDITY_SETPOINT_MODE_SCHEMA = vol.Schema({
        vol.Required(ATTR_ENTITY_ID): cv.entity_id,
        vol.Required(ATTR_HUMIDITY_SETPOINT_MODE): vol.In(["defog", "manual"]),
    })

SET_HEAT_DISSIPATION_TIME_SCHEMA = vol.Schema({
        vol.Required(ATTR_ENTITY_ID): cv.entity_id,
        vol.Required(ATTR_TIME): vol.Range(min=0, max=5),
    })

SET_COOL_DISSIPATION_TIME_SCHEMA = vol.Schema({
        vol.Required(ATTR_ENTITY_ID): cv.entity_id,
        vol.Required(ATTR_TIME): vol.Range(min=0, max=5),
    })

SET_CLIMATE_NEVIWEB_STATUS_SCHEMA = vol.Schema({
        vol.Required(ATTR_ENTITY_ID): cv.entity_id,
        vol.Required(ATTR_MODE): vol.In(OCCUPANCY_LIST),
    })

"""light schema."""

SET_LIGHT_KEYPAD_LOCK_SCHEMA = vol.Schema({
        vol.Required(ATTR_ENTITY_ID): cv.entity_id,
        vol.Required(ATTR_KEYPAD): vol.In(LOCK_LIST),
    })

SET_LIGHT_TIMER_SCHEMA = vol.Schema({
        vol.Required(ATTR_ENTITY_ID): cv.entity_id,
        vol.Required(ATTR_TIMER): vol.In(TIMER_LIST),
    })

SET_LED_INDICATOR_SCHEMA = vol.Schema({
        vol.Required(ATTR_ENTITY_ID): cv.entity_id,
        vol.Required(ATTR_STATE): vol.All(vol.Coerce(int), vol.Range(min=0, max=1)),
        vol.Required(ATTR_COLOR): vol.In(COLOR_LIST),
    })

SET_LED_ON_INTENSITY_SCHEMA = vol.Schema({
        vol.Required(ATTR_ENTITY_ID): cv.entity_id,
        vol.Required(ATTR_LED_ON_INTENSITY): vol.All(vol.Coerce(int), vol.Range(min=0, max=100)),
    })

SET_LED_OFF_INTENSITY_SCHEMA = vol.Schema({
        vol.Required(ATTR_ENTITY_ID): cv.entity_id,
        vol.Required(ATTR_LED_OFF_INTENSITY): vol.All(vol.Coerce(int), vol.Range(min=0, max=100)),
    })

SET_LIGHT_MIN_INTENSITY_SCHEMA = vol.Schema({
        vol.Required(ATTR_ENTITY_ID): cv.entity_id,
        vol.Required(ATTR_INTENSITY_MIN): vol.All(vol.Coerce(int), vol.Range(min=10, max=3000)),
    })

SET_WATTAGE_SCHEMA = vol.Schema({
        vol.Required(ATTR_ENTITY_ID): cv.entity_id,
        vol.Required(ATTR_LIGHT_WATTAGE): vol.All(vol.Coerce(int), vol.Range(min=0, max=1800)),
    })

SET_PHASE_CONTROL_SCHEMA = vol.Schema({
        vol.Required(ATTR_ENTITY_ID): cv.entity_id,
        vol.Required(ATTR_PHASE_CONTROL): vol.In(PHASE_LIST),
    })

SET_KEY_DOUBLE_UP_SCHEMA = vol.Schema({
        vol.Required(ATTR_ENTITY_ID): cv.entity_id,
        vol.Required(ATTR_KEY_DOUBLE_UP): vol.In(ON_OFF),
    })

""""Switch schema."""

SET_SWITCH_KEYPAD_LOCK_SCHEMA = vol.Schema({
        vol.Required(ATTR_ENTITY_ID): cv.entity_id,
        vol.Required(ATTR_KEYPAD): vol.In(LOCK_LIST),
    })

SET_SWITCH_TIMER_SCHEMA = vol.Schema({
        vol.Required(ATTR_ENTITY_ID): cv.entity_id,
        vol.Required(ATTR_TIMER): vol.In(TIMER_LIST),
    })

SET_SWITCH_TIMER_2_SCHEMA = vol.Schema({
        vol.Required(ATTR_ENTITY_ID): cv.entity_id,
        vol.Required(ATTR_TIMER2): vol.In(TIMER_LIST),
    })

SET_SWITCH_POWER_TIMER_SCHEMA = vol.Schema({
        vol.Required(ATTR_ENTITY_ID): cv.entity_id,
        vol.Required(ATTR_TIMER): vol.In(POWER_TIMER_LIST),
    })

SET_LOAD_DR_OPTIONS_SCHEMA = vol.Schema({
        vol.Required(ATTR_ENTITY_ID): cv.entity_id,
        vol.Required(ATTR_DRACTIVE): vol.In(ON_OFF),
        vol.Required(ATTR_OPTOUT): vol.In(ON_OFF),
        vol.Required(ATTR_ONOFF): vol.In(ON_OFF),
    })

SET_CONTROL_ONOFF_SCHEMA = vol.Schema({
        vol.Required(ATTR_ENTITY_ID): cv.entity_id,
        vol.Required(ATTR_STATUS): vol.In(ON_OFF),
        vol.Required(ATTR_ONOFF_NUM): vol.All(vol.Coerce(int), vol.Range(min=1, max=2)),
    })

SET_TANK_SIZE_SCHEMA = vol.Schema({
        vol.Required(ATTR_ENTITY_ID): cv.entity_id,
        vol.Required(ATTR_VALUE): vol.In(TANK_VALUE),
    })

SET_CONTROLLED_DEVICE_SCHEMA = vol.Schema({
        vol.Required(ATTR_ENTITY_ID): cv.entity_id,
        vol.Required(ATTR_VALUE): vol.In(CONTROLLED_VALUE),
    })

SET_LOW_TEMP_PROTECTION_SCHEMA = vol.Schema({
        vol.Required(ATTR_ENTITY_ID): cv.entity_id,
        vol.Required(ATTR_WATER_TEMP_MIN): vol.In(WATER_TEMP),
    })

SET_INPUT_OUTPUT_NAMES_SCHEMA = vol.Schema({
        vol.Required(ATTR_ENTITY_ID): cv.entity_id,
        vol.Optional(ATTR_NAME_1, default=None): vol.All(str, vol.Length(min=0, max=10)),
        vol.Optional(ATTR_NAME_2, default=None): vol.All(str, vol.Length(min=0, max=10)),
        vol.Optional(ATTR_OUTPUT_NAME_1, default=None): vol.All(str, vol.Length(min=0, max=10)),
        vol.Optional(ATTR_OUTPUT_NAME_2, default=None): vol.All(str, vol.Length(min=0, max=10)),
    })

SET_REMAINING_TIME_SCHEMA = vol.Schema({
        vol.Required(ATTR_ENTITY_ID): cv.entity_id,
        vol.Required(ATTR_COLD_LOAD_PICKUP_REMAIN_TIME): vol.All(
            vol.Coerce(int),
            vol.Range(min=0, max=65535),
            is_valid_remaining_time
        )
    })

SET_ON_OFF_INPUT_DELAY_SCHEMA = vol.Schema({
        vol.Required(ATTR_ENTITY_ID): cv.entity_id,
        vol.Required("input_number"): vol.In([1, 2]),
        vol.Required("onoff"): vol.In(ON_OFF),
        vol.Required("delay"): vol.In(DELAY),
    })

"""Sensor schema."""

SET_SENSOR_CLOSURE_ACTION_SCHEMA = vol.Schema({
        vol.Required(ATTR_ENTITY_ID): cv.entity_id,
        vol.Required(ATTR_CONF_CLOSURE): vol.In(ON_OFF),
    })

SET_SENSOR_LEAK_ALERT_SCHEMA = vol.Schema({
        vol.Required(ATTR_ENTITY_ID): cv.entity_id,
        vol.Required(ATTR_LEAK_ALERT): cv.boolean,
    })

SET_SENSOR_TEMP_ALERT_SCHEMA = vol.Schema({
        vol.Required(ATTR_ENTITY_ID): cv.entity_id,
        vol.Required(ATTR_TEMP_ALERT): cv.boolean,
    })

SET_BATTERY_TYPE_SCHEMA = vol.Schema({
        vol.Required(ATTR_ENTITY_ID): cv.entity_id,
        vol.Required(ATTR_BATTERY_TYPE): vol.In(BATT_TYPE_LIST),
    })

SET_TANK_TYPE_SCHEMA = vol.Schema({
        vol.Required(ATTR_ENTITY_ID): cv.entity_id,
        vol.Required(ATTR_TANK_TYPE): vol.In(FUEL_LIST),
    })

SET_GAUGE_TYPE_SCHEMA = vol.Schema({
        vol.Required(ATTR_ENTITY_ID): cv.entity_id,
        vol.Required(ATTR_GAUGE_TYPE): vol.In(GAUGE_LIST),
    })

SET_LOW_FUEL_ALERT_SCHEMA = vol.Schema({
        vol.Required(ATTR_ENTITY_ID): cv.entity_id,
        vol.Required(ATTR_FUEL_PERCENT_ALERT): vol.In(LOW_FUEL_LEVEL),
    })

SET_REFUEL_ALERT_SCHEMA = vol.Schema({
        vol.Required(ATTR_ENTITY_ID): cv.entity_id,
        vol.Required(ATTR_REFUEL): vol.In(TRUE_LIST),
    })

SET_TANK_HEIGHT_SCHEMA = vol.Schema({
        vol.Required(ATTR_ENTITY_ID): cv.entity_id,
        vol.Required(ATTR_TANK_HEIGHT): vol.In(TANK_HEIGHT),
    })

SET_FUEL_ALERT_SCHEMA = vol.Schema({
        vol.Required(ATTR_ENTITY_ID): cv.entity_id,
        vol.Required(ATTR_FUEL_ALERT): vol.In(TRUE_LIST),
    })

SET_BATTERY_ALERT_SCHEMA = vol.Schema({
        vol.Required(ATTR_ENTITY_ID): cv.entity_id,
        vol.Required(ATTR_BATT_ALERT): vol.In(TRUE_LIST),
    })

SET_NEVIWEB_STATUS_SCHEMA = vol.Schema({
        vol.Required(ATTR_ENTITY_ID): cv.entity_id,
        vol.Required(ATTR_MODE): vol.In(OCCUPANCY_LIST),
    })

"""Valve schema."""

SET_POWER_SUPPLY_SCHEMA = vol.Schema({
        vol.Required(ATTR_ENTITY_ID): cv.entity_id,
        vol.Required(ATTR_POWER_SUPPLY): vol.In(SUPPLY_LIST),
    })

SET_FLOW_METER_MODEL_SCHEMA = vol.Schema({
        vol.Required(ATTR_ENTITY_ID): cv.entity_id,
        vol.Required(ATTR_FLOW_MODEL_CONFIG): vol.In(FLOW_MODEL),
    })

SET_FLOW_METER_DELAY_SCHEMA = vol.Schema({
        vol.Required(ATTR_ENTITY_ID): cv.entity_id,
        vol.Required(ATTR_FLOW_ALARM1_PERIOD): vol.In(FLOW_DURATION),
    })

SET_FLOW_METER_OPTIONS_SCHEMA = vol.Schema({
        vol.Required(ATTR_ENTITY_ID): cv.entity_id,
        vol.Required(ATTR_TRIGGER_ALARM): cv.boolean,
        vol.Required(ATTR_CLOSE_VALVE): cv.boolean,
    })

SET_VALVE_ALERT_SCHEMA = vol.Schema({
        vol.Required(ATTR_ENTITY_ID): cv.entity_id,
        vol.Required(ATTR_BATT_ALERT): cv.boolean,
    })

SET_VALVE_TEMP_ALERT_SCHEMA = vol.Schema({
        vol.Required(ATTR_ENTITY_ID): cv.entity_id,
        vol.Required(ATTR_TEMP_ALERT): cv.boolean,
    })

SET_FLOW_ALARM_DISABLE_TIMER_SCHEMA = vol.Schema({
        vol.Required(ATTR_ENTITY_ID): cv.entity_id,
        vol.Required(ATTR_FLOW_ALARM_TIMER): vol.In(FLOW_DURATION),
    })
