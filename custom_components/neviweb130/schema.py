"""Schema for config entry and services."""

from __future__ import annotations

from datetime import timedelta

import voluptuous as vol
from homeassistant.const import ATTR_ENTITY_ID, CONF_PASSWORD, CONF_SCAN_INTERVAL, CONF_USERNAME
from homeassistant.helpers import config_validation as cv

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
    ATTR_BLUE,
    ATTR_CLOSE_VALVE,
    ATTR_COLD_LOAD_PICKUP_REMAIN_TIME,
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
    ATTR_GREEN,
    ATTR_HEAT_LOCK_TEMP,
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
    ATTR_RED,
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
    ATTR_TYPE,
    ATTR_VALUE,
    ATTR_WATER_TEMP_MIN,
    CONF_HOMEKIT_MODE,
    CONF_IGNORE_MIWI,
    CONF_NETWORK,
    CONF_NETWORK2,
    CONF_NETWORK3,
    CONF_NOTIFY,
    CONF_STAT_INTERVAL,
    DOMAIN,
)

"""Default parameters values."""

SCAN_INTERVAL = timedelta(seconds=540)
HOMEKIT_MODE = False
STAT_INTERVAL = 1800
IGNORE_MIWI = False
NOTIFY = "both"

REVERSING_VALVE_POLARITY = ["cooling", "heating"]
MIN_TIME = {120, 180, 240, 300, 600}
WIFI_CYCLE = {600, 900, 1200, 1500}
TANK_VALUE = {"40 gal", "50 gal", "60 gal", "80 gal"}
CONTROLLED_VALUE = {
    "Hot water heater",
    "Pool pump",
    "Electric vehicle charger",
    "Other",
}
FLOW_MODEL = {"FS4220", "FS4221", "No flow meter"}
FLOW_DURATION = {
    "15 min",
    "30 min",
    "45 min",
    "60 min",
    "75 min",
    "90 min",
    "3 h",
    "6 h",
    "12 h",
    "24 h",
}
DELAY = {
    "off",
    "1 min",
    "2 min",
    "5 min",
    "10 min",
    "15 min",
    "30 min",
    "1 h",
    "2 h",
    "3 h",
}
TANK_HEIGHT = {23, 24, 35, 38, 47, 48, 50}
LOW_FUEL_LEVEL = {0, 10, 20, 30}
WATER_TEMP = {0, 45, 46, 47, 48, 49, 50, 51, 52, 53, 54, 55}
POWER_TIMER = {0, 60, 120, 300, 600, 900, 1800, 3600, 7200, 10800}
FAN_SPEED = ["high", "medium", "low", "auto", "off"]
WIFI_FAN_SPEED = ["auto", "on"]
FAN_CAPABILITY = {"low", "med", "high", "auto"}
FAN_SWING_CAPABILITY = {
    "fullHorizontal",
    "autoHorizontal",
    "fullVertical",
    "autoVertical",
}
DISPLAY_CAPABILITY = {"enable", "disable"}
SOUND_CAPABILITY = {"enable", "disable"}
SWING_CAPABILITY_VERTICAL = {
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
}
SWING_CAPABILITY_HORIZONTAL = {
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
}
FULL_SWING = ["swingFullRange"]
FULL_SWING_OFF = ["off"]
AUX_HEATING = {"Electric": "hvacElectrique", "Fossil": "hvacGaz"}
HEAT_INSTALL_TYPE = ["addOn", "conventional"]
ACCESSORY = [
    "none",
    "humOnHeat",
    "humOnFan",
    "dehum",
    "airExchanger",
]
AIR_EX_MIN_TIME_ON = ["Off", "20 min", "40 min", "Continuous"]

CYCLE_LENGTH_VALUES: dict[str, int] = {
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

"""Config schema."""

CONFIG_SCHEMA = vol.Schema(
    {
        DOMAIN: vol.Schema(
            {
                vol.Required(CONF_USERNAME): cv.string,
                vol.Required(CONF_PASSWORD): cv.string,
                vol.Optional(CONF_NETWORK): cv.string,
                vol.Optional(CONF_NETWORK2): cv.string,
                vol.Optional(CONF_NETWORK3): cv.string,
                vol.Optional(CONF_SCAN_INTERVAL, default=SCAN_INTERVAL): cv.time_period,
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

SET_SECOND_DISPLAY_SCHEMA = vol.Schema(
    {
        vol.Required(ATTR_ENTITY_ID): cv.entity_id,
        vol.Required(ATTR_DISPLAY2): vol.In(["exteriorTemperature", "setpoint", "default"]),
    }
)

SET_BACKLIGHT_SCHEMA = vol.Schema(
    {
        vol.Required(ATTR_ENTITY_ID): cv.entity_id,
        vol.Required(ATTR_BACKLIGHT): vol.In(["auto", "on", "bedroom"]),
    }
)

SET_CLIMATE_KEYPAD_LOCK_SCHEMA = vol.Schema(
    {
        vol.Required(ATTR_ENTITY_ID): cv.entity_id,
        vol.Required(ATTR_KEYPAD): vol.In(["locked", "unlocked", "partiallyLocked"]),
    }
)

SET_EM_HEAT_SCHEMA = vol.Schema(
    {
        vol.Required(ATTR_ENTITY_ID): cv.entity_id,
        vol.Required(ATTR_VALUE): vol.In(["on", "off"]),
    }
)

SET_TIME_FORMAT_SCHEMA = vol.Schema(
    {
        vol.Required(ATTR_ENTITY_ID): cv.entity_id,
        vol.Required(ATTR_TIME_FORMAT): vol.All(vol.Coerce(int), vol.In([12, 24])),
    }
)

SET_TEMPERATURE_FORMAT_SCHEMA = vol.Schema(
    {
        vol.Required(ATTR_ENTITY_ID): cv.entity_id,
        vol.Required(ATTR_TEMP): vol.In(["celsius", "fahrenheit"]),
    }
)

SET_SETPOINT_MAX_SCHEMA = vol.Schema(
    {
        vol.Required(ATTR_ENTITY_ID): cv.entity_id,
        vol.Required(ATTR_ROOM_SETPOINT_MAX): vol.All(vol.Coerce(float), vol.Range(min=6, max=30)),
    }
)

SET_SETPOINT_MIN_SCHEMA = vol.Schema(
    {
        vol.Required(ATTR_ENTITY_ID): cv.entity_id,
        vol.Required(ATTR_ROOM_SETPOINT_MIN): vol.All(vol.Coerce(float), vol.Range(min=5, max=29)),
    }
)

SET_FLOOR_AIR_LIMIT_SCHEMA = vol.Schema(
    {
        vol.Required(ATTR_ENTITY_ID): cv.entity_id,
        vol.Required(ATTR_FLOOR_AIR_LIMIT): vol.All(vol.Coerce(float), vol.Range(min=0, max=36)),
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
        vol.Optional(ATTR_DRACTIVE): vol.In(["on", "off"]),
        vol.Optional(ATTR_OPTOUT): vol.In(["on", "off"]),
        vol.Optional(ATTR_SETPOINT): vol.In(["on", "off"]),
        vol.Optional(ATTR_AUX_OPTIM): vol.In(["on", "off"]),
        vol.Optional(ATTR_FAN_SPEED_OPTIM): vol.In(["on", "off"]),
    }
)

SET_HVAC_DR_SETPOINT_SCHEMA = vol.Schema(
    {
        vol.Required(ATTR_ENTITY_ID): cv.entity_id,
        vol.Required(ATTR_STATUS): vol.In(["on", "off"]),
        vol.Required(ATTR_VALUE): vol.All(vol.Coerce(float), vol.Range(min=-10, max=10)),
    }
)

SET_COOL_SETPOINT_MAX_SCHEMA = vol.Schema(
    {
        vol.Required(ATTR_ENTITY_ID): cv.entity_id,
        vol.Required(ATTR_COOL_SETPOINT_MAX): vol.All(vol.Coerce(float), vol.Range(min=16, max=36)),
    }
)

SET_COOL_SETPOINT_MIN_SCHEMA = vol.Schema(
    {
        vol.Required(ATTR_ENTITY_ID): cv.entity_id,
        vol.Required(ATTR_COOL_SETPOINT_MIN): vol.All(vol.Coerce(float), vol.Range(min=15, max=35)),
    }
)

SET_ROOM_SETPOINT_AWAY_SCHEMA = vol.Schema(
    {
        vol.Required(ATTR_ENTITY_ID): cv.entity_id,
        vol.Required(ATTR_ROOM_SETPOINT_AWAY): vol.All(vol.Coerce(int), vol.Range(min=10, max=30)),
    }
)

SET_COOL_SETPOINT_AWAY_SCHEMA = vol.Schema(
    {
        vol.Required(ATTR_ENTITY_ID): cv.entity_id,
        vol.Required(ATTR_COOL_SETPOINT_AWAY): vol.All(vol.Coerce(int), vol.Range(min=15, max=35)),
    }
)

SET_AUXILIARY_LOAD_SCHEMA = vol.Schema(
    {
        vol.Required(ATTR_ENTITY_ID): cv.entity_id,
        vol.Required(ATTR_STATUS): vol.In(["on", "off"]),
        vol.Required(ATTR_VALUE): vol.All(vol.Coerce(int), vol.Range(min=0, max=4000)),
    }
)

SET_AUX_CYCLE_OUTPUT_SCHEMA = vol.Schema(
    {
        vol.Required(ATTR_ENTITY_ID): cv.entity_id,
        vol.Required(ATTR_VALUE): vol.In(CYCLE_LENGTH_VALUES.keys()),
    }
)

SET_CYCLE_OUTPUT_SCHEMA = vol.Schema(
    {
        vol.Required(ATTR_ENTITY_ID): cv.entity_id,
        vol.Required(ATTR_VALUE): vol.In(CYCLE_LENGTH_VALUES.keys()),
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
        vol.Required(ATTR_FLOOR_MIN): vol.All(vol.Coerce(float), vol.Range(min=0, max=34)),
    }
)

SET_FLOOR_LIMIT_HIGH_SCHEMA = vol.Schema(
    {
        vol.Required(ATTR_ENTITY_ID): cv.entity_id,
        vol.Required(ATTR_FLOOR_MAX): vol.All(vol.Coerce(float), vol.Range(min=0, max=36)),
    }
)

SET_ACTIVATION_SCHEMA = vol.Schema(
    {
        vol.Required(ATTR_ENTITY_ID): cv.entity_id,
        vol.Required(ATTR_ACTIVE): vol.In([True, False]),
    }
)

SET_SENSOR_TYPE_SCHEMA = vol.Schema(
    {
        vol.Required(ATTR_ENTITY_ID): cv.entity_id,
        vol.Required(ATTR_FLOOR_SENSOR): vol.In(["10k", "12k"]),
    }
)

SET_HEAT_PUMP_OPERATION_LIMIT_SCHEMA = vol.Schema(
    {
        vol.Required(ATTR_ENTITY_ID): cv.entity_id,
        vol.Required(ATTR_BALANCE_PT): vol.All(vol.Coerce(int), vol.Range(min=-30, max=0)),
    }
)

SET_HEAT_INSTALLATION_TYPE_SCHEMA = vol.Schema(
    {
        vol.Required(ATTR_ENTITY_ID): cv.entity_id,
        vol.Required(ATTR_TYPE): vol.In(HEAT_INSTALL_TYPE),
    }
)

SET_COOL_LOCKOUT_TEMPERATURE_SCHEMA = vol.Schema(
    {
        vol.Required(ATTR_ENTITY_ID): cv.entity_id,
        vol.Required(ATTR_COOL_LOCK_TEMP): vol.All(
            lambda v: int(v) if v != "off" else None, vol.Any(None, vol.Range(min=10, max=30))
        ),
    }
)

SET_HEAT_LOCKOUT_TEMPERATURE_SCHEMA = vol.Schema(
    {
        vol.Required(ATTR_ENTITY_ID): cv.entity_id,
        vol.Required(ATTR_HEAT_LOCK_TEMP): vol.All(
            lambda v: int(v) if v != "off" else None, vol.Any(None, vol.Range(min=10, max=30))
        ),
    }
)

SET_DISPLAY_CONFIG_SCHEMA = vol.Schema(
    {
        vol.Required(ATTR_ENTITY_ID): cv.entity_id,
        vol.Required(ATTR_DISPLAY_CONF): vol.All(cv.ensure_list, [vol.In(DISPLAY_CAPABILITY)]),
    }
)

SET_SOUND_CONFIG_SCHEMA = vol.Schema(
    {
        vol.Required(ATTR_ENTITY_ID): cv.entity_id,
        vol.Required(ATTR_SOUND_CONF): vol.All(cv.ensure_list, [vol.In(SOUND_CAPABILITY)]),
    }
)

SET_HC_SECOND_DISPLAY_SCHEMA = vol.Schema(
    {
        vol.Required(ATTR_ENTITY_ID): cv.entity_id,
        vol.Required(ATTR_DISPLAY2): vol.In(["exteriorTemperature", "setpoint", "none"]),
    }
)

SET_LANGUAGE_SCHEMA = vol.Schema(
    {
        vol.Required(ATTR_ENTITY_ID): cv.entity_id,
        vol.Required(ATTR_LANGUAGE): vol.In(["en", "fr"]),
    }
)

SET_REVERSING_VALVE_POLARITY_SCHEMA = vol.Schema(
    {
        vol.Required(ATTR_ENTITY_ID): cv.entity_id,
        vol.Required(ATTR_POLARITY): vol.In(REVERSING_VALVE_POLARITY),
    }
)

SET_MIN_TIME_ON_SCHEMA = vol.Schema(
    {
        vol.Required(ATTR_ENTITY_ID): cv.entity_id,
        vol.Optional(ATTR_HEAT_MIN_TIME_ON): vol.In(MIN_TIME),
        vol.Optional(ATTR_AUX_HEAT_MIN_TIME_ON): vol.In(MIN_TIME),
        vol.Optional(ATTR_COOL_MIN_TIME_ON): vol.In(MIN_TIME),
        vol.Optional(ATTR_AIR_EX_MIN_TIME_ON): vol.In(AIR_EX_MIN_TIME_ON),
    }
)

SET_MIN_TIME_OFF_SCHEMA = vol.Schema(
    {
        vol.Required(ATTR_ENTITY_ID): cv.entity_id,
        vol.Optional(ATTR_HEAT_MIN_TIME_OFF): vol.In(MIN_TIME),
        vol.Optional(ATTR_AUX_HEAT_MIN_TIME_OFF): vol.In(MIN_TIME),
        vol.Optional(ATTR_COOL_MIN_TIME_OFF): vol.In(MIN_TIME),
    }
)

SET_HEAT_INTERSTAGE_DELAY_SCHEMA = vol.Schema(
    {
        vol.Required(ATTR_ENTITY_ID): cv.entity_id,
        vol.Required(ATTR_TIME): vol.Range(min=1, max=60),
    }
)

SET_COOL_INTERSTAGE_DELAY_SCHEMA = vol.Schema(
    {
        vol.Required(ATTR_ENTITY_ID): cv.entity_id,
        vol.Required(ATTR_TIME): vol.Range(min=1, max=60),
    }
)

SET_AUX_HEAT_START_DELAY_SCHEMA = vol.Schema(
    {
        vol.Required(ATTR_ENTITY_ID): cv.entity_id,
        vol.Required(ATTR_TIME): vol.Range(min=0.5, max=8.0),
    }
)

SET_ACCESSORY_TYPE_SCHEMA = vol.Schema(
    {
        vol.Required(ATTR_ENTITY_ID): cv.entity_id,
        vol.Required(ATTR_ACCESSORY_TYPE): vol.In(ACCESSORY),
    }
)

SET_SCHEDULE_MODE_SCHEMA = vol.Schema(
    {
        vol.Required(ATTR_ENTITY_ID): cv.entity_id,
        vol.Required(ATTR_SETPOINT_MODE): vol.In(["auto", "manual"]),
    }
)

SET_HEATCOOL_SETPOINT_DELTA_SCHEMA = vol.Schema(
    {
        vol.Required(ATTR_ENTITY_ID): cv.entity_id,
        vol.Required(ATTR_HEATCOOL_SETPOINT_MIN_DELTA): vol.All(vol.Coerce(int), vol.Range(min=1, max=5)),
    }
)

SET_FAN_FILTER_REMINDER_SCHEMA = vol.Schema(
    {
        vol.Required(ATTR_ENTITY_ID): cv.entity_id,
        vol.Required(ATTR_FAN_FILTER_REMAIN): vol.All(vol.Coerce(int), vol.Range(min=1, max=12)),
    }
)

SET_TEMPERATURE_OFFSET_SCHEMA = vol.Schema(
    {
        vol.Required(ATTR_ENTITY_ID): cv.entity_id,
        vol.Required(ATTR_TEMP_OFFSET_HEAT): vol.All(vol.Coerce(int), vol.Range(min=-2, max=2)),
    }
)

SET_AUX_HEATING_SOURCE_SCHEMA = vol.Schema(
    {
        vol.Required(ATTR_ENTITY_ID): cv.entity_id,
        vol.Required(ATTR_AUX_HEAT_SOURCE_TYPE): vol.In(AUX_HEATING.keys()),
    }
)

SET_FAN_SPEED_SCHEMA = vol.Schema(
    {
        vol.Required(ATTR_ENTITY_ID): cv.entity_id,
        vol.Required(ATTR_FAN_SPEED): vol.In(["On", "Auto"]),
    }
)

SET_HUMIDITY_SETPOINT_MODE_SCHEMA = vol.Schema(
    {
        vol.Required(ATTR_ENTITY_ID): cv.entity_id,
        vol.Required(ATTR_HUMIDITY_SETPOINT_MODE): vol.In(["defog", "manual"]),
    }
)

SET_HEAT_DISSIPATION_TIME_SCHEMA = vol.Schema(
    {
        vol.Required(ATTR_ENTITY_ID): cv.entity_id,
        vol.Required(ATTR_TIME): vol.Range(min=0, max=5),
    }
)

SET_COOL_DISSIPATION_TIME_SCHEMA = vol.Schema(
    {
        vol.Required(ATTR_ENTITY_ID): cv.entity_id,
        vol.Required(ATTR_TIME): vol.Range(min=0, max=5),
    }
)

SET_CLIMATE_NEVIWEB_STATUS_SCHEMA = vol.Schema(
    {
        vol.Required(ATTR_ENTITY_ID): cv.entity_id,
        vol.Required(ATTR_MODE): vol.In(["home", "away"]),
    }
)

"""light schema."""

SET_LIGHT_KEYPAD_LOCK_SCHEMA = vol.Schema(
    {
        vol.Required(ATTR_ENTITY_ID): cv.entity_id,
        vol.Required(ATTR_KEYPAD): vol.In(["locked", "unlocked", "partiallyLocked"]),
    }
)

SET_LIGHT_TIMER_SCHEMA = vol.Schema(
    {
        vol.Required(ATTR_ENTITY_ID): cv.entity_id,
        vol.Required(ATTR_TIMER): vol.All(vol.Coerce(int), vol.Range(min=0, max=10800)),
    }
)

SET_LED_INDICATOR_SCHEMA = vol.Schema(
    {
        vol.Required(ATTR_ENTITY_ID): cv.entity_id,
        vol.Required(ATTR_STATE): vol.All(vol.Coerce(int), vol.Range(min=0, max=1)),
        vol.Required(ATTR_RED): vol.All(vol.Coerce(int), vol.Range(min=0, max=255)),
        vol.Required(ATTR_GREEN): vol.All(vol.Coerce(int), vol.Range(min=0, max=255)),
        vol.Required(ATTR_BLUE): vol.All(vol.Coerce(int), vol.Range(min=0, max=255)),
    }
)

SET_LED_ON_INTENSITY_SCHEMA = vol.Schema(
    {
        vol.Required(ATTR_ENTITY_ID): cv.entity_id,
        vol.Required(ATTR_LED_ON_INTENSITY): vol.All(vol.Coerce(int), vol.Range(min=0, max=100)),
    }
)

SET_LED_OFF_INTENSITY_SCHEMA = vol.Schema(
    {
        vol.Required(ATTR_ENTITY_ID): cv.entity_id,
        vol.Required(ATTR_LED_OFF_INTENSITY): vol.All(vol.Coerce(int), vol.Range(min=0, max=100)),
    }
)

SET_LIGHT_MIN_INTENSITY_SCHEMA = vol.Schema(
    {
        vol.Required(ATTR_ENTITY_ID): cv.entity_id,
        vol.Required(ATTR_INTENSITY_MIN): vol.All(vol.Coerce(int), vol.Range(min=10, max=3000)),
    }
)

SET_WATTAGE_SCHEMA = vol.Schema(
    {
        vol.Required(ATTR_ENTITY_ID): cv.entity_id,
        vol.Required(ATTR_LIGHT_WATTAGE): vol.All(vol.Coerce(int), vol.Range(min=0, max=1800)),
    }
)

SET_PHASE_CONTROL_SCHEMA = vol.Schema(
    {
        vol.Required(ATTR_ENTITY_ID): cv.entity_id,
        vol.Required(ATTR_PHASE_CONTROL): vol.In(["reverse", "forward"]),
    }
)

SET_KEY_DOUBLE_UP_SCHEMA = vol.Schema(
    {
        vol.Required(ATTR_ENTITY_ID): cv.entity_id,
        vol.Required(ATTR_KEY_DOUBLE_UP): vol.In(["On", "Off"]),
    }
)

""""Switch schema."""

SET_SWITCH_KEYPAD_LOCK_SCHEMA = vol.Schema(
    {
        vol.Required(ATTR_ENTITY_ID): cv.entity_id,
        vol.Required(ATTR_KEYPAD): vol.In(["locked", "unlocked", "partiallyLocked"]),
    }
)

SET_SWITCH_TIMER_SCHEMA = vol.Schema(
    {
        vol.Required(ATTR_ENTITY_ID): cv.entity_id,
        vol.Required(ATTR_TIMER): vol.All(vol.Coerce(int), vol.Range(min=0, max=10800)),
    }
)

SET_SWITCH_TIMER_2_SCHEMA = vol.Schema(
    {
        vol.Required(ATTR_ENTITY_ID): cv.entity_id,
        vol.Required(ATTR_TIMER2): vol.All(vol.Coerce(int), vol.Range(min=0, max=10800)),
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
        vol.Required(ATTR_ONOFF_NUM): vol.All(vol.Coerce(int), vol.Range(min=1, max=2)),
    }
)

SET_TANK_SIZE_SCHEMA = vol.Schema(
    {
        vol.Required(ATTR_ENTITY_ID): cv.entity_id,
        vol.Required(ATTR_VALUE): vol.All(cv.ensure_list, [vol.In(TANK_VALUE)]),
    }
)

SET_CONTROLLED_DEVICE_SCHEMA = vol.Schema(
    {
        vol.Required(ATTR_ENTITY_ID): cv.entity_id,
        vol.Required(ATTR_VALUE): vol.All(cv.ensure_list, [vol.In(CONTROLLED_VALUE)]),
    }
)

SET_LOW_TEMP_PROTECTION_SCHEMA = vol.Schema(
    {
        vol.Required(ATTR_ENTITY_ID): cv.entity_id,
        vol.Required(ATTR_WATER_TEMP_MIN): vol.All(cv.ensure_list, [vol.In(WATER_TEMP)]),
    }
)

SET_INPUT_OUTPUT_NAMES_SCHEMA = vol.Schema(
    {
        vol.Required(ATTR_ENTITY_ID): cv.entity_id,
        vol.Optional(ATTR_NAME_1, default=None): vol.All(str, vol.Length(min=0, max=10)),
        vol.Optional(ATTR_NAME_2, default=None): vol.All(str, vol.Length(min=0, max=10)),
        vol.Optional(ATTR_OUTPUT_NAME_1, default=None): vol.All(str, vol.Length(min=0, max=10)),
        vol.Optional(ATTR_OUTPUT_NAME_2, default=None): vol.All(str, vol.Length(min=0, max=10)),
    }
)

SET_REMAINING_TIME_SCHEMA = vol.Schema(
    {
        vol.Required(ATTR_ENTITY_ID): cv.entity_id,
        vol.Required(ATTR_COLD_LOAD_PICKUP_REMAIN_TIME): vol.All(vol.Coerce(int), vol.Range(min=0, max=65535)),
    }
)

SET_ON_OFF_INPUT_DELAY_SCHEMA = vol.Schema(
    {
        vol.Required(ATTR_ENTITY_ID): cv.entity_id,
        vol.Required("input_number"): vol.In([1, 2]),
        vol.Required("onoff"): vol.In(["on", "off"]),
        vol.Required("delay"): vol.All(cv.ensure_list, [vol.In(DELAY)]),
    }
)

"""Sensor schema."""

SET_SENSOR_ALERT_SCHEMA = vol.Schema(
    {
        vol.Required(ATTR_ENTITY_ID): cv.entity_id,
        vol.Required(ATTR_LEAK_ALERT): vol.All(vol.Coerce(int), vol.Range(min=0, max=1)),
        vol.Required(ATTR_BATT_ALERT): vol.All(vol.Coerce(int), vol.Range(min=0, max=1)),
        vol.Required(ATTR_TEMP_ALERT): vol.All(vol.Coerce(int), vol.Range(min=0, max=1)),
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
        vol.Required(ATTR_GAUGE_TYPE): vol.All(vol.Coerce(int), vol.In([595, 1080])),
    }
)

SET_LOW_FUEL_ALERT_SCHEMA = vol.Schema(
    {
        vol.Required(ATTR_ENTITY_ID): cv.entity_id,
        vol.Required(ATTR_FUEL_PERCENT_ALERT): vol.All(vol.Coerce(int), vol.In(LOW_FUEL_LEVEL)),
    }
)

SET_REFUEL_ALERT_SCHEMA = vol.Schema(
    {
        vol.Required(ATTR_ENTITY_ID): cv.entity_id,
        vol.Required(ATTR_REFUEL): vol.In([True, False]),
    }
)

SET_TANK_HEIGHT_SCHEMA = vol.Schema(
    {
        vol.Required(ATTR_ENTITY_ID): cv.entity_id,
        vol.Required(ATTR_TANK_HEIGHT): vol.All(vol.Coerce(int), vol.In(TANK_HEIGHT)),
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

SET_NEVIWEB_STATUS_SCHEMA = vol.Schema(
    {
        vol.Required(ATTR_ENTITY_ID): cv.entity_id,
        vol.Required(ATTR_MODE): vol.In(["home", "away"]),
    }
)

"""Valve schema."""

SET_POWER_SUPPLY_SCHEMA = vol.Schema(
    {
        vol.Required(ATTR_ENTITY_ID): cv.entity_id,
        vol.Required(ATTR_POWER_SUPPLY): vol.In(["batt", "power", "both"]),
    }
)

SET_FLOW_METER_MODEL_SCHEMA = vol.Schema(
    {
        vol.Required(ATTR_ENTITY_ID): cv.entity_id,
        vol.Required(ATTR_FLOW_MODEL_CONFIG): vol.All(cv.ensure_list, [vol.In(FLOW_MODEL)]),
    }
)

SET_FLOW_METER_DELAY_SCHEMA = vol.Schema(
    {
        vol.Required(ATTR_ENTITY_ID): cv.entity_id,
        vol.Required(ATTR_FLOW_ALARM1_PERIOD): vol.All(cv.ensure_list, [vol.In(FLOW_DURATION)]),
    }
)

SET_FLOW_METER_OPTIONS_SCHEMA = vol.Schema(
    {
        vol.Required(ATTR_ENTITY_ID): cv.entity_id,
        vol.Required(ATTR_TRIGGER_ALARM): vol.In(["on", "off"]),
        vol.Required(ATTR_CLOSE_VALVE): vol.In(["on", "off"]),
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
        vol.Required(ATTR_TEMP_ALERT): vol.All(vol.Coerce(int), vol.Range(min=0, max=1)),
    }
)

SET_FLOW_ALARM_DISABLE_TIMER_SCHEMA = vol.Schema(
    {
        vol.Required(ATTR_ENTITY_ID): cv.entity_id,
        vol.Required(ATTR_FLOW_ALARM_TIMER): vol.All(vol.Coerce(int), vol.Range(min=0, max=86400)),
    }
)
