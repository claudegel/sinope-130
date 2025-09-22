"""Constants for neviweb130 component."""

import json
import pathlib

# Base component constants, some loaded directly from the manifest
_LOADER_PATH = pathlib.Path(__loader__.path)
_MANIFEST_PATH = _LOADER_PATH.parent / "manifest.json"
with pathlib.Path.open(_MANIFEST_PATH, encoding="Latin1") as json_file:
    data = json.load(json_file)
NAME = f"{data['name']}"
DOMAIN = f"{data['domain']}"
VERSION = f"{data['version']}"
ISSUE_URL = f"{data['issue_tracker']}"
REQUIRE = "2025.1.1"
DOC_URL = f"{data['documentation']}"

STARTUP_MESSAGE = f"""
-------------------------------------------------------------------
{NAME} ({DOMAIN})
Version: {VERSION}
Requirement: Home Assistant minimum version {REQUIRE}
This is a custom integration!
If you have any issues with this you need to open an issue here:
{ISSUE_URL}
Documentation: {DOC_URL}
If not done yet you can delete config in configuration.yaml.
-------------------------------------------------------------------
"""

CONF_NETWORK = "network"
CONF_NETWORK2 = "network2"
CONF_NETWORK3 = "network3"
CONF_HOMEKIT_MODE = "homekit_mode"
CONF_IGNORE_MIWI = "ignore_miwi"
CONF_STAT_INTERVAL = "stat_interval"
CONF_NOTIFY = "notify"

ATTR_ALERT = "alert"
ATTR_SIGNATURE = "signature"
ATTR_POWER_MODE = "powerMode"
ATTR_MODE = "mode"
ATTR_ONOFF = "onOff"
ATTR_ONOFF2 = "onOff2"
ATTR_INTENSITY = "intensity"
ATTR_INTENSITY_MIN = "intensityMin"
ATTR_WATTAGE = "loadConnected"
ATTR_WATTAGE_INSTANT = "wattageInstant"
ATTR_WATTAGE_OVERRIDE = "wattageOverride"
ATTR_SETPOINT_MODE = "setpointMode"
ATTR_ROOM_SETPOINT = "roomSetpoint"
ATTR_ROOM_SETPOINT_AWAY = "roomSetpointAway"
ATTR_ROOM_TEMPERATURE = "roomTemperature"
ATTR_OUTPUT_PERCENT_DISPLAY = "outputPercentDisplay"
ATTR_ROOM_SETPOINT_MIN = "roomSetpointMin"
ATTR_ROOM_SETPOINT_MAX = "roomSetpointMax"
ATTR_GFCI_STATUS = "gfciStatus"
ATTR_GFCI_ALERT = "alertGfci"
ATTR_WATER_LEAK_STATUS = "waterLeakStatus"
ATTR_WATER_LEAK_ALARM_STATUS = "waterleakDetectionAlarmStatus"
ATTR_WATER_LEAK_DISCONECTED_STATUS = "waterleakDisconnectedAlarmStatus"
ATTR_POWER_SUPPLY = "backupPowerSupply"
ATTR_BATTERY_VOLTAGE = "batteryVoltage"
ATTR_BATTERY_STATUS = "batteryStatus"
ATTR_BATTERY_TYPE = "batteryType"
ATTR_FLOOR_MODE = "airFloorMode"
ATTR_FLOOR_OUTPUT2 = "loadWattOutput2"  # status on/off, value=xx
ATTR_FLOOR_AUX = "auxHeatConfig"
ATTR_KEYPAD = "lockKeypad"
ATTR_OCCUPANCY = "occupancyMode"
ATTR_FLOOR_OUTPUT1 = "loadWattOutput1"  # status on/off, value=xx
ATTR_LIGHT_WATTAGE = "loadWattOutput1"  # status on/off, value=xx
ATTR_OUTPUT1 = "loadWattOutput1"
ATTR_WIFI_WATTAGE = "loadWatt"  # value
ATTR_WIFI_WATT_NOW = "loadWattNow"
ATTR_WIFI = "wifiRssi"
ATTR_RSSI = "rssi"
ATTR_DISPLAY2 = "config2ndDisplay"
ATTR_WIFI_KEYPAD = "keyboardLock"
ATTR_TIMER = "powerTimer"
ATTR_TIMER2 = "powerTimer2"
ATTR_DRSTATUS = "drStatus"
ATTR_BACKLIGHT = "backlightAdaptive"
ATTR_BACKLIGHT_AUTO_DIM = "backlightAutoDim"
ATTR_LED_ON_INTENSITY = "statusLedOnIntensity"
ATTR_LED_OFF_INTENSITY = "statusLedOffIntensity"
ATTR_LED_ON_COLOR = "statusLedOnColor"
ATTR_LED_OFF_COLOR = "statusLedOffColor"
ATTR_STATE = "state"
ATTR_RED = "red"
ATTR_GREEN = "green"
ATTR_BLUE = "blue"
ATTR_TIME = "timeFormat"
ATTR_TEMP = "temperatureFormat"
ATTR_MOTOR_POS = "motorPosition"
ATTR_TEMP_ALARM = "temperatureAlarmStatus"
ATTR_LOW_TEMP_STATUS = "alertLowTempStatus"
ATTR_TEMPERATURE = "temperature"
ATTR_WATER_TEMPERATURE = "waterTemperature"
ATTR_ROOM_TEMP_ALARM = "roomTemperatureAlarmStatus"
ATTR_VALVE_CLOSURE = "valveClosureSource"  # source
ATTR_LEAK_ALERT = "alertWaterLeak"
ATTR_BATT_ALERT = "alertLowBatt"
ATTR_TEMP_ALERT = "alertLowTemp"
ATTR_FUEL_ALERT = "alertLowFuel"
ATTR_REFUEL = "alertRefuel"
ATTR_FUEL_PERCENT_ALERT = "alertLowFuelPercent"
ATTR_CONF_CLOSURE = "cfgValveClosure"
ATTR_MOTOR_TARGET = "motorTargetPosition"
ATTR_FLOOR_AIR_LIMIT = "floorMaxAirTemperature"
ATTR_FLOOR_MAX = "floorLimitHigh"
ATTR_FLOOR_MIN = "floorLimitLow"
ATTR_ROOM_TEMP_DISPLAY = "roomTemperatureDisplay"
ATTR_EARLY_START = "earlyStartCfg"
ATTR_FLOOR_SENSOR = "floorSensorType"
ATTR_AUX_CYCLE = "auxCycleLength"
ATTR_CYCLE = "cycleLength"
ATTR_CYCLE_OUTPUT2 = "cycleLengthOutput2"  # status on/off, value (second)
ATTR_PUMP_PROTEC = "pumpProtection"  # status on/off, duration, frequency
ATTR_PUMP_PROTEC_DURATION = "pumpProtectDuration"  # status on/off, value
ATTR_PUMP_PROTEC_PERIOD = "pumpProtectPeriod"  # status on/off, value
ATTR_TYPE = "type"
ATTR_PHASE_CONTROL = "phaseControl"
ATTR_SYSTEM_MODE = "systemMode"
ATTR_DRSETPOINT = "drSetpoint"
ATTR_DRACTIVE = "drActive"
ATTR_OPTOUT = "optOut"
ATTR_SETPOINT = "setpoint"
ATTR_INPUT_STATUS = "inputStatus"
ATTR_INPUT2_STATUS = "input2Status"
ATTR_EXT_TEMP = "externalTemperature"
ATTR_REL_HUMIDITY = "relativeHumidity"
ATTR_STATUS = "status"
ATTR_ERROR_CODE_SET1 = "errorCodeSet1"
ATTR_FLOW_METER_CONFIG = "flowMeterMeasurementConfig"
ATTR_VALVE_INFO = "valveInfo"
ATTR_STM8_ERROR = "stm8Error"
ATTR_TANK_SIZE = "tankSize"
ATTR_CONTROLLED_DEVICE = "controlledDevice"
ATTR_COLD_LOAD_PICKUP_STATUS = "coldLoadPickupStatus"
ATTR_KEY_DOUBLE_UP = "configKeyDoubleUp"
ATTR_ANGLE = "angle"
ATTR_SAMPLING = "samplingTime"
ATTR_TANK_TYPE = "tankType"
ATTR_TANK_HEIGHT = "tankHeight"
ATTR_TANK_PERCENT = "tankPercent"
ATTR_GAUGE_TYPE = "gaugeType"
ATTR_COOL_SETPOINT = "coolSetpoint"
ATTR_COOL_SETPOINT_MIN = "coolSetpointMin"
ATTR_COOL_SETPOINT_MAX = "coolSetpointMax"
ATTR_WATER_TEMP_MIN = "drConfigWaterTempMin"
ATTR_MIN_WATER_TEMP = "minWaterTankTemperature"
ATTR_WATT_TIME_ON = "drWTTimeOn"
ATTR_DR_WATER_TEMP_TIME = "drConfigWaterTempTime"
ATTR_WATER_TEMP_TIME = "waterTempTime"
ATTR_FLOW_ALARM1 = "flowMeterAlarm1Config"
ATTR_FLOW_ALARM2 = "flowMeterAlarm2Config"
ATTR_AWAY_ACTION = "awayAction"
ATTR_FLOW_ENABLED = "flowMeterEnabled"
ATTR_FLOW_MODEL_CONFIG = "FlowModel"
ATTR_FLOW_ALARM_TIMER = "flowMeterAlarmDisableTimer"
ATTR_FLOW_THRESHOLD = "alarm1FlowThreshold"
ATTR_FLOW_ALARM1_LENGHT = "alarm1Length"
ATTR_FLOW_ALARM1_PERIOD = "alarm1Period"
ATTR_FLOW_ALARM1_OPTION = "alarm1Options"
ATTR_DR_PROTEC_STATUS = "drProtectionLegStatus"
ATTR_LEG_PROTEC_STATUS = "legProtectionStatus"
ATTR_COLD_LOAD_PICKUP_REMAIN_TIME = "coldLoadPickupRemainingTime"
ATTR_COLD_LOAD_PICKUP_TEMP = "coldLoadPickupTemperature"
ATTR_TEMP_ACTION_LOW = "temperatureActionLow"
ATTR_BATT_ACTION_LOW = "batteryActionLow"
ATTR_NAME_1 = "input1name"
ATTR_NAME_2 = "input2name"
ATTR_OUTPUT_NAME_1 = "output1name"
ATTR_OUTPUT_NAME_2 = "output2name"
ATTR_WATER_TANK_ON = "waterTankTimeOn"
ATTR_HEAT_LOCK_TEMP = "heatLockoutTemperature"
ATTR_COOL_LOCK_TEMP = "coolLockoutTemperature"
ATTR_AVAIL_MODE = "availableMode"
ATTR_FAN_SPEED = "fanSpeed"
ATTR_FAN_CAP = "fanCapabilities"
ATTR_FAN_SWING_VERT = "fanSwingVertical"
ATTR_FAN_SWING_HORIZ = "fanSwingHorizontal"
ATTR_FAN_SWING_CAP = "fanSwingCapabilities"
ATTR_FAN_SWING_CAP_HORIZ = "fanSwingCapabilityHorizontal"
ATTR_FAN_SWING_CAP_VERT = "fanSwingCapabilityVertical"
ATTR_DISPLAY_CONF = "displayConfig"
ATTR_DISPLAY_CAP = "displayCapability"
ATTR_MODEL = "model"
ATTR_SOUND_CONF = "soundConfig"
ATTR_SOUND_CAP = "soundCapability"
ATTR_LANGUAGE = "language"
ATTR_MODE = "mode"
ATTR_HC_DEV = "hcDevice"
ATTR_BALANCE_PT = "balancePoint"
ATTR_BALANCE_PT_TEMP_LOW = "balancePointTempLow"
ATTR_BALANCE_PT_TEMP_HIGH = "balancePointTempHigh"
ATTR_BATT_PERCENT_NORMAL = "batteryPercentNormalized"
ATTR_BATT_STATUS_NORMAL = "batteryStatusNormalized"
ATTR_BATT_INFO = "displayBatteryInfo"
ATTR_INPUT_1_ON_DELAY = "inputOnDebounceDelay"
ATTR_INPUT_2_ON_DELAY = "inputOnDebounceDelay2"
ATTR_INPUT_1_OFF_DELAY = "inputOffDebounceDelay"
ATTR_INPUT_2_OFF_DELAY = "inputOffDebounceDelay2"
ATTR_VALUE = "value"
ATTR_ACTIVE = "active"
ATTR_ONOFF_NUM = "onOff_num"
ATTR_CLOSE_VALVE = "closeValve"
ATTR_TRIGGER_ALARM = "triggerAlarm"
ATTR_DELAY = "delay"
ATTR_INPUT_NUMBER = "input_number"
ATTR_COLD_LOAD_PICKUP = "coldLoadPickup"
ATTR_HEAT_LOCKOUT_TEMP = "heatLockoutTemp"
ATTR_OCCUPANCY_SENSOR_DELAY = "occupancySensorUnoccupiedDelay"
ATTR_LEAK_CLOSURE_CONFIG = "waterLeakClosureConfig"
ATTR_HUMID_DISPLAY = "humidityDisplay"
ATTR_HUMID_SETPOINT = "humiditySetpoint"
ATTR_DUAL_STATUS = "dualEnergyStatus"
ATTR_HEAT_SOURCE_TYPE = "heatSourceType"
ATTR_AUX_HEAT_SOURCE_TYPE = "auxHeatSourceType"
ATTR_COOL_SETPOINT_AWAY = "coolSetpointAway"
ATTR_FAN_FILTER_REMAIN = "fanFilterReminderPeriod"
ATTR_AUX_HEAT_TIMEON = "auxHeatMinTimeOn"
ATTR_AUX_HEAT_START_DELAY = "auxHeatStartDelay"
ATTR_HEAT_INTERSTAGE_MIN_DELAY = "heatInterstageMinDelay"
ATTR_COOL_INTERSTAGE_MIN_DELAY = "coolInterstageMinDelay"
ATTR_BACK_LIGHT = "backlight"
ATTR_HEAT_COOL = "heatCoolMode"
ATTR_VALVE_POLARITY = "reversingValvePolarity"
ATTR_HUMIDIFIER_TYPE = "humidifierType"
ATTR_COOL_CYCLE_LENGTH = "coolCycleLength"
ATTR_HEATCOOL_SETPOINT_MIN_DELTA = "heatCoolSetpointMinDelta"
ATTR_TEMP_OFFSET_HEAT = "temperatureOffsetHeat"
ATTR_COOL_MIN_TIME_ON = "coolMinTimeOn"
ATTR_COOL_MIN_TIME_OFF = "coolMinTimeOff"
ATTR_WATER_TEMP_PROTEC = "waterTempProtectionType"
ATTR_OUTPUT_CONNECT_STATE = "bulkOutputConnectedState"
ATTR_HEAT_INSTALL_TYPE = "HeatInstallationType"
ATTR_HUMIDITY = "humidity"
ATTR_ACCESSORY_TYPE = "accessoryType"
ATTR_HUMID_SETPOINT_OFFSET = "humiditySetpointOffset"
ATTR_HUMID_SETPOINT_MODE = "humiditySetpointMode"
ATTR_AIR_EX_MIN_TIME_ON = "airExchangerMinTimeOn"
ATTR_HC_LOCK_STATUS = "heatCoolLockoutStatus"
ATTR_DRAUXCONF = "drAuxConfig"
ATTR_DRFANCONF = "drFanSpeedConfig"
ATTR_DRACCESORYCONF = "drAccessoryConfig"
ATTR_DRAIR_CURT_CONF = "drAirCurtainConfig"
ATTR_INTERLOCK_ID = "interlockUniqueId"
ATTR_HEAT_PURGE_TIME = "heatPurgeTime"
ATTR_COOL_PURGE_TIME = "coolPurgeTime"
ATTR_AIR_CONFIG = "airCurtainConfig"
ATTR_AIR_ACTIVATION_TEMP = "airCurtainActivationTemperature"
ATTR_AIR_MAX_POWER_TEMP = "airCurtainMaxPowerTemperature"
ATTR_AUX_HEAT_MIN_TIMEOFF = "auxHeatMinTimeOff"
ATTR_HEAT_MIN_TIME_ON = "heatMinTimeOn"
ATTR_HEAT_MIN_TIME_OFF = "heatMinTimeOff"
ATTR_COLOR = "color"

SIGNAL_EVENTS_CHANGED = f"{DOMAIN}_events_changed"

MODE_AUTO = "auto"
MODE_AUTO_BYPASS = "autoBypass"
MODE_MANUAL = "manual"
MODE_AWAY = "away"
MODE_HOME = "home"
MODE_OFF = "off"
MODE_EM_HEAT = "emergencyHeat"

STATE_WATER_LEAK = "water"
STATE_VALVE_STATUS = "open"
STATE_KEYPAD_STATUS = "unlocked"

SERVICE_SET_LED_INDICATOR = "set_led_indicator"
SERVICE_SET_LED_ON_INTENSITY = "set_led_on_intensity"
SERVICE_SET_LED_OFF_INTENSITY = "set_led_off_intensity"
SERVICE_SET_LIGHT_MIN_INTENSITY = "set_light_min_intensity"
SERVICE_SET_CLIMATE_KEYPAD_LOCK = "set_climate_keypad_lock"
SERVICE_SET_LIGHT_KEYPAD_LOCK = "set_light_keypad_lock"
SERVICE_SET_SWITCH_KEYPAD_LOCK = "set_switch_keypad_lock"
SERVICE_SET_LIGHT_TIMER = "set_light_timer"
SERVICE_SET_SWITCH_TIMER = "set_switch_timer"
SERVICE_SET_SWITCH_TIMER_2 = "set_switch_timer2"
SERVICE_SET_SECOND_DISPLAY = "set_second_display"
SERVICE_SET_BACKLIGHT = "set_backlight"
SERVICE_SET_EARLY_START = "set_early_start"
SERVICE_SET_TIME_FORMAT = "set_time_format"
SERVICE_SET_TEMPERATURE_FORMAT = "set_temperature_format"
SERVICE_SET_WATTAGE = "set_wattage"
SERVICE_SET_SETPOINT_MAX = "set_setpoint_max"
SERVICE_SET_SETPOINT_MIN = "set_setpoint_min"
SERVICE_SET_SENSOR_ALERT = "set_sensor_alert"
SERVICE_SET_VALVE_ALERT = "set_valve_alert"
SERVICE_SET_VALVE_TEMP_ALERT = "set_valve_temp_alert"
SERVICE_SET_FLOOR_AIR_LIMIT = "set_floor_air_limit"
SERVICE_SET_AIR_FLOOR_MODE = "set_air_floor_mode"
SERVICE_SET_PHASE_CONTROL = "set_phase_control"
SERVICE_SET_HVAC_DR_OPTIONS = "set_hvac_dr_options"
SERVICE_SET_HVAC_DR_SETPOINT = "set_hvac_dr_setpoint"
SERVICE_SET_LOAD_DR_OPTIONS = "set_load_dr_options"
SERVICE_SET_CONTROL_ONOFF = "set_control_onoff"
SERVICE_SET_AUXILIARY_LOAD = "set_auxiliary_load"
SERVICE_SET_AUX_CYCLE_OUTPUT = "set_aux_cycle_output"
SERVICE_SET_CYCLE_OUTPUT = "set_cycle_output"
SERVICE_SET_BATTERY_TYPE = "set_battery_type"
SERVICE_SET_PUMP_PROTECTION = "set_pump_protection"
SERVICE_SET_TANK_SIZE = "set_tank_size"
SERVICE_SET_CONTROLLED_DEVICE = "set_controlled_device"
SERVICE_SET_COOL_SETPOINT_MAX = "set_cool_setpoint_max"
SERVICE_SET_COOL_SETPOINT_MIN = "set_cool_setpoint_min"
SERVICE_SET_LOW_TEMP_PROTECTION = "set_low_temp_protection"
SERVICE_SET_FLOW_METER_MODEL = "set_flow_meter_model"
SERVICE_SET_FLOW_METER_DELAY = "set_flow_meter_delay"
SERVICE_SET_FLOW_METER_OPTIONS = "set_flow_meter_options"
SERVICE_SET_FLOOR_LIMIT_LOW = "set_floor_limit_low"
SERVICE_SET_FLOOR_LIMIT_HIGH = "set_floor_limit_high"
SERVICE_SET_TANK_TYPE = "set_tank_type"
SERVICE_SET_GAUGE_TYPE = "set_gauge_type"
SERVICE_SET_LOW_FUEL_ALERT = "set_low_fuel_alert"
SERVICE_SET_TANK_HEIGHT = "set_tank_height"
SERVICE_SET_FUEL_ALERT = "set_fuel_alert"
SERVICE_SET_POWER_SUPPLY = "set_power_supply"
SERVICE_SET_BATTERY_ALERT = "set_battery_alert"
SERVICE_SET_INPUT_OUTPUT_NAMES = "set_input_output_names"
SERVICE_SET_ACTIVATION = "set_activation"
SERVICE_SET_KEY_DOUBLE_UP = "set_key_double_up"
SERVICE_SET_SENSOR_TYPE = "set_sensor_type"
SERVICE_SET_REMAINING_TIME = "set_remaining_time"
SERVICE_SET_ON_OFF_INPUT_DELAY = "set_on_off_input_delay"
SERVICE_SET_EM_HEAT = "set_em_heat"
SERVICE_SET_HEAT_PUMP_OPERATION_LIMIT = "set_heat_pump_operation_limit"
SERVICE_SET_COOL_LOCKOUT_TEMPERATURE = "set_cool_lockout_temperature"
SERVICE_SET_HEAT_LOCKOUT_TEMPERATURE = "set_heat_lockout_temperature"
SERVICE_SET_DISPLAY_CONFIG = "set_display_config"
SERVICE_SET_SOUND_CONFIG = "set_sound_config"
SERVICE_SET_HC_SECOND_DISPLAY = "set_hc_second_display"
SERVICE_SET_LANGUAGE = "set_language"
SERVICE_SET_AUX_HEAT_MIN_TIME_ON = "set_aux_heat_min_time_on"
SERVICE_SET_COOL_MIN_TIME_ON = "set_cool_min_time_on"
SERVICE_SET_COOL_MIN_TIME_OFF = "set_cool_min_time_off"
SERVICE_SET_NEVIWEB_STATUS = "set_neviweb_status"
SERVICE_SET_REFUEL_ALERT = "set_refuel_alert"
SERVICE_SET_HUMIDIFIER_TYPE = "set_humidifier_type"
SERVICE_SET_SCHEDULE_MODE = "set_schedule_mode"
SERVICE_SET_FLOW_ALARM_DISABLE_TIMER = "set_flow_alarm_disable_timer"
SERVICE_SET_FAN_FILTER_REMINDER = "set_fan_filter_reminder"

CLIMATE_MODEL = [
    300,
    336,
    737,
    738,
    739,
    742,
    1123,
    1124,
    1510,
    1512,
    6727,
    6730,
    6810,
    6811,
    6812,
    7372,
    7373,
]
LIGHT_MODEL = [2121, 2131, 2132]
SWITCH_MODEL = [346, 2151, 2152, 2180, 2181, 2506, 2600, 2610]
VALVE_MODEL = [3150, 3151, 3153, 3155, 31532]
SENSOR_MODEL = [130, 4210, 5050, 5051, 5052, 5053, 5055, 5056, 42102]
ALL_MODEL = CLIMATE_MODEL + LIGHT_MODEL + SWITCH_MODEL + VALVE_MODEL
FULL_MODEL = (
    CLIMATE_MODEL + LIGHT_MODEL + SWITCH_MODEL + VALVE_MODEL + SENSOR_MODEL
)

# list attributs availables for each device model
MODEL_ATTRIBUTES = {
    # thermostats
    300: {  # TH1123ZB-G2 3000W, 4000W
        "sensor": [
            ATTR_RSSI,
            "current_temperature",
            "daily_kwh_count",
            "hourly_kwh_count",
            "monthly_kwh_count",
            "pi_heating_demand",
            "total_kwh_count",
        ],
        "number": [
            "max_temp",
            "min_temp",
        ],
        "select": [
            "backlight",
            "keypad",
        ],
        "binary_sensor": [
            "is_heating",
        ],
        "button": [],
    },
    336: {  # TH1133CR, TH1134WF, TH1134CR
        "sensor": [
            ATTR_RSSI,
            "current_temperature",
            "pi_heating_demand",
        ],
        "number": [
            "max_temp",
            "min_temp",
        ],
        "select": [
            "backlight",
            "keypad",
        ],
        "binary_sensor": [],
        "button": [],
    },
    737: {  # TH1300ZB 3600W, TH1320ZB-04, OTH3600-GA-ZB
        "sensor": [
            ATTR_RSSI,
            "current_temperature",
            "daily_kwh_count",
            "hourly_kwh_count",
            "monthly_kwh_count",
            "pi_heating_demand",
            "total_kwh_count",
        ],
        "number": [
            "max_temp",
            "min_temp",
        ],
        "select": [
            "backlight",
            "keypad",
        ],
        "binary_sensor": [],
        "button": [],
    },
    738: {  # TH1300WF 3600W, TH1325WF, TH1310WF, SRM40, True Comfort, concerto connect FLP55
        "sensor": [
            ATTR_RSSI,
            "current_temperature",
            "daily_kwh_count",
            "hourly_kwh_count",
            "monthly_kwh_count",
            "pi_heating_demand",
            "total_kwh_count",
        ],
        "number": [
            "max_temp",
            "min_temp",
        ],
        "select": [
            "backlight",
            "keypad",
        ],
        "binary_sensor": [],
        "button": [],
    },
    739: {  # TH1400WF low voltage
        "sensor": [
            ATTR_RSSI,
            "current_temperature",
            "daily_kwh_count",
            "hourly_kwh_count",
            "monthly_kwh_count",
            "pi_heating_demand",
            "total_kwh_count",
        ],
        "number": [
            "max_temp",
            "min_temp",
        ],
        "select": [
            "backlight",
            "keypad",
        ],
        "binary_sensor": [],
        "button": [],
    },
    742: {  # TH1500WF double pole
        "sensor": [
            ATTR_RSSI,
            "current_temperature",
            "daily_kwh_count",
            "hourly_kwh_count",
            "monthly_kwh_count",
            "pi_heating_demand",
            "total_kwh_count",
        ],
        "number": [
            "max_temp",
            "min_temp",
        ],
        "select": [
            "backlight",
            "keypad",
        ],
        "binary_sensor": [],
        "button": [],
    },
    1123: {  # TH1123ZB 3000W
        "sensor": [
            ATTR_RSSI,
            "current_temperature",
            "daily_kwh_count",
            "hourly_kwh_count",
            "monthly_kwh_count",
            "pi_heating_demand",
            "total_kwh_count",
        ],
        "number": [
            "max_temp",
            "min_temp",
        ],
        "select": [
            "backlight",
            "keypad",
        ],
        "binary_sensor": [],
        "button": [],
    },
    1124: {  # TH1124ZB 4000W
        "sensor": [
            ATTR_RSSI,
            "current_temperature",
            "daily_kwh_count",
            "hourly_kwh_count",
            "monthly_kwh_count",
            "pi_heating_demand",
            "total_kwh_count",
        ],
        "number": [
            "max_temp",
            "min_temp",
        ],
        "select": [
            "backlight",
            "keypad",
        ],
        "binary_sensor": [],
        "button": [],
    },
    1510: {  # TH1123WF 3000W, 4000W
        "sensor": [
            ATTR_RSSI,
            "current_temperature",
            "daily_kwh_count",
            "hourly_kwh_count",
            "monthly_kwh_count",
            "pi_heating_demand",
            "total_kwh_count",
        ],
        "number": [
            "max_temp",
            "min_temp",
        ],
        "select": [
            "backlight",
            "keypad",
        ],
        "binary_sensor": [],
        "button": [],
    },
    1512: {  # TH1134ZB-HC
        "sensor": [
            ATTR_RSSI,
            "current_temperature",
            "daily_kwh_count",
            "hourly_kwh_count",
            "monthly_kwh_count",
            "pi_heating_demand",
            "total_kwh_count",
        ],
        "number": [
            "max_temp",
            "min_temp",
        ],
        "select": [
            "backlight",
            "keypad",
            "language",
        ],
        "binary_sensor": [],
        "button": [],
    },
    6727: {  # TH6500WF, TH6510WF
        "sensor": [
            ATTR_RSSI,
            "current_temperature",
            "daily_kwh_count",
            "hourly_kwh_count",
            "monthly_kwh_count",
            "pi_heating_demand",
            "total_kwh_count",
        ],
        "number": [
            "fan_filter_remain",
            "max_cool_temp",
            "min_cool_temp",
            "max_temp",
            "min_temp",
        ],
        "select": [
            "backlight",
            "keypad",
            "language",
        ],
        "binary_sensor": [],
        "button": [],
    },
    6730: {  # TH6250WF, TH6250WF-PRO
        "sensor": [
            ATTR_RSSI,
            "current_temperature",
            "daily_kwh_count",
            "hourly_kwh_count",
            "monthly_kwh_count",
            "pi_heating_demand",
            "total_kwh_count",
        ],
        "number": [
            "fan_filter_remain",
            "max_cool_temp",
            "max_temp",
            "min_cool_temp",
            "min_temp",
        ],
        "select": [
            "backlight",
            "keypad",
            "language",
        ],
        "binary_sensor": [],
        "button": [],
    },
    6810: {  # HP6000ZB-GE
        "sensor": [ATTR_RSSI],
        "number": [
            "max_temp",
            "min_temp",
        ],
        "select": ["keypad"],
        "binary_sensor": [],
        "button": [],
    },
    6811: {  # HP6000ZB-MA
        "sensor": [ATTR_RSSI],
        "number": [
            "max_temp",
            "min_temp",
        ],
        "select": ["keypad"],
        "binary_sensor": [],
        "button": [],
    },
    6812: {  # HP6000ZB-HS
        "sensor": [ATTR_RSSI],
        "number": [
            "max_temp",
            "min_temp",
        ],
        "select": ["keypad"],
        "binary_sensor": [],
        "button": [],
    },
    7372: {  # TH1400ZB low voltage, TH1420ZB-01 Nordik
        "sensor": [
            ATTR_RSSI,
            "current_temperature",
            "daily_kwh_count",
            "hourly_kwh_count",
            "monthly_kwh_count",
            "pi_heating_demand",
            "total_kwh_count",
        ],
        "number": [
            "max_temp",
            "min_temp",
        ],
        "select": [
            "backlight",
            "keypad",
        ],
        "binary_sensor": [],
        "button": [],
    },
    7373: {  # TH1500ZB double pole
        "sensor": [
            ATTR_RSSI,
            "current_temperature",
            "daily_kwh_count",
            "hourly_kwh_count",
            "monthly_kwh_count",
            "pi_heating_demand",
            "total_kwh_count",
        ],
        "number": [
            "max_temp",
            "min_temp",
        ],
        "select": [
            "backlight",
            "keypad",
        ],
        "binary_sensor": [],
        "button": [],
    },
    # Lights
    2121: {  # SW2500ZB, SW2500ZB-G2
        "sensor": [
            ATTR_RSSI,
            "daily_kwh_count",
            "hourly_kwh_count",
            "monthly_kwh_count",
            "total_kwh_count",
        ],
        "number": [
            "brightness",
            "intensity_min",
            "light_timer",
            "led_off_intensity",
            "led_on_intensity",
        ],
        "select": [
            "keypad",
            "led_off_color",
            "led_on_color",
        ],
        "binary_sensor": [],
        "button": [],
    },
    2131: {  # DM2500ZB, DM2500ZB-G2
        "sensor": [
            ATTR_RSSI,
            "daily_kwh_count",
            "hourly_kwh_count",
            "monthly_kwh_count",
            "total_kwh_count",
        ],
        "number": [
            "brightness",
            "intensity_min",
            "light_timer",
            "led_off_intensity",
            "led_on_intensity",
        ],
        "select": [
            "keypad",
            "led_off_color",
            "led_on_color",
        ],
        "binary_sensor": [],
        "button": [],
    },
    2132: {  # DM2550ZB, DM2550ZB-G2
        "sensor": [
            ATTR_RSSI,
            "daily_kwh_count",
            "hourly_kwh_count",
            "monthly_kwh_count",
            "total_kwh_count",
        ],
        "number": [
            "brightness",
            "intensity_min",
            "light_timer",
            "led_off_intensity",
            "led_on_intensity",
        ],
        "select": [
            "keypad",
            "led_off_color",
            "led_on_color",
        ],
        "binary_sensor": [],
        "button": [],
    },
    # Switch
    346: {  # RM3250WF, 50A, wifi
        "sensor": [
            ATTR_RSSI,
            "daily_kwh_count",
            "hourly_kwh_count",
            "monthly_kwh_count",
            "total_kwh_count",
        ],
        "number": ["power_timer"],
        "select": ["keypad_status"],
        "binary_sensor": [],
        "button": [],
    },
    2151: {  # RM3500ZB 20,8A, Zigbee
        "sensor": [
            ATTR_RSSI,
            "daily_kwh_count",
            "hourly_kwh_count",
            "monthly_kwh_count",
            "total_kwh_count",
        ],
        "number": [],
        "select": [],
        "binary_sensor": ["water_leak_status"],
        "button": [],
    },
    2152: {  # RM3500WF 20,8A, wifi, RM3510WF 20,8A, wifi
        "sensor": [
            ATTR_RSSI,
            "daily_kwh_count",
            "hourly_kwh_count",
            "monthly_kwh_count",
            "total_kwh_count",
        ],
        "number": [],
        "select": [],
        "binary_sensor": ["water_leak_status"],
        "button": [],
    },
    2180: {  # MC3100ZB connected to GT130
        "sensor": [ATTR_RSSI],
        "number": [
            "timer",
            "timer2",
        ],
        "select": [],
        "binary_sensor": [],
        "button": [],
    },
    2181: {  # MC3100ZB connected to Sedna valve
        "sensor": [ATTR_RSSI],
        "number": [
            "timer",
            "timer2",
        ],
        "select": [],
        "binary_sensor": [],
        "button": [],
    },
    2506: {  # RM3250ZB, 50A, Zigbee
        "sensor": [
            ATTR_RSSI,
            "daily_kwh_count",
            "hourly_kwh_count",
            "monthly_kwh_count",
            "total_kwh_count",
        ],
        "number": ["power_timer"],
        "select": ["keypad_status"],
        "binary_sensor": [],
        "button": [],
    },
    2600: {  # SP2600ZB
        "sensor": [
            ATTR_RSSI,
            "daily_kwh_count",
            "hourly_kwh_count",
            "monthly_kwh_count",
            "total_kwh_count",
        ],
        "number": [],
        "select": [],
        "binary_sensor": [],
        "button": [],
    },
    2610: {  # SP2610ZB
        "sensor": [
            ATTR_RSSI,
            "daily_kwh_count",
            "hourly_kwh_count",
            "monthly_kwh_count",
            "total_kwh_count",
        ],
        "number": [],
        "select": [],
        "binary_sensor": [],
        "button": [],
    },
    # Valves
    3150: {  # VA4201WZ, VA4200WZ, VA4220WZ, VA4220WF, VA4221WZ, VA4221WF
        "sensor": [ATTR_RSSI],
        "number": [],
        "select": [],
        "binary_sensor": [],
        "button": [],
    },
    3151: {  # VA4200ZB
        "sensor": [ATTR_RSSI],
        "number": [],
        "select": [],
        "binary_sensor": [],
        "button": [],
    },
    3153: {  # VA4220ZB 2e gen
        "sensor": [
            ATTR_RSSI,
            "daily_kwh_count",
            "hourly_kwh_count",
            "monthly_kwh_count",
            "total_kwh_count",
        ],
        "number": ["flowmeter_timer"],
        "select": [],
        "binary_sensor": [
            "battery_status",
            "temp_alert",
            "water_leak_status",
        ],
        "button": [],
    },
    3155: {  # ACT4221WF-M, ACT4220WF-M
        "sensor": [
            ATTR_RSSI,
            "daily_kwh_count",
            "hourly_kwh_count",
            "monthly_kwh_count",
            "total_kwh_count",
        ],
        "number": ["flowmeter_timer"],
        "select": [],
        "binary_sensor": [
            "battery_status",
            "temp_alert",
            "water_leak_status",
        ],
        "button": [],
    },
    31532: {  # ACT4221ZB-M, ACT4220ZB-M
        "sensor": [
            ATTR_RSSI,
            "daily_kwh_count",
            "hourly_kwh_count",
            "monthly_kwh_count",
            "total_kwh_count",
        ],
        "number": ["flowmeter_timer"],
        "select": [],
        "binary_sensor": [
            "battery_status",
            "temp_alert",
            "water_leak_status",
        ],
        "button": [],
    },
    # sensors
    130: {  # GT130
        "sensor": ["gateway_status"],
        "number": [],
        "select": ["occupancy_mode"],
        "binary_sensor": [],
        "button": [],
    },
    4210: {  # WL4210, WL4210S connected to GT130
        "sensor": [
            ATTR_RSSI,
            "current_temperature",
        ],
        "number": [],
        "select": [],
        "binary_sensor": [
            "battery_status",
            "leak_status",
        ],
        "button": [],
    },
    5050: {  # WL4200, WL4210 and WL4200S,
        "sensor": [
            ATTR_RSSI,
            "current_temperature",
        ],
        "number": [],
        "select": [],
        "binary_sensor": [
            "battery_status",
            "leak_status",
        ],
        "button": [],
    },
    5051: {  # WL4200, WL4200C and WL4200S
        "sensor": [
            ATTR_RSSI,
            "current_temperature",
        ],
        "number": [],
        "select": [],
        "binary_sensor": [
            "battery_status",
            "leak_status",
        ],
        "button": [],
    },
    5052: {  # WL4200C, perimeter cable water leak detector connected to Sedna
        "sensor": [
            ATTR_RSSI,
            "current_temperature",
        ],
        "number": [],
        "select": [],
        "binary_sensor": [
            "battery_status",
            "leak_status",
        ],
        "button": [],
    },
    5053: {  # WL4200C, perimeter cable water leak detector connected to GT130
        "sensor": [
            ATTR_RSSI,
            "current_temperature",
        ],
        "number": [],
        "select": [],
        "binary_sensor": [
            "battery_status",
            "leak_status",
        ],
        "button": [],
    },
    5055: {  # LM4110-LTE
        "sensor": [ATTR_RSSI],
        "number": [],
        "select": [],
        "binary_sensor": [],
        "button": [],
    },
    5056: {  # LM4110-ZB
        "sensor": [
            ATTR_RSSI,
            "battery_level",
            "battery_voltage",
            "gauge_angle",
        ],
        "number": [],
        "select": [],
        "binary_sensor": [
            "battery_status",
            "level_status",
            "refuel_status",
        ],
        "button": [],
    },
    42102: {  # WL4210, WL4210S connected to sedna valve
        "sensor": [
            ATTR_RSSI,
            "current_temperature",
        ],
        "number": [],
        "select": [],
        "binary_sensor": [
            "battery_status",
            "leak_status",
        ],
        "button": [],
    },
}

# Managed device attributes by alphabetical order
EXPOSED_ATTRIBUTES = [
    "backlight",
    "battery_level",
    "battery_status",
    "battery_voltage",
    "brightness",
    "current_temperature",
    "daily_flow_count",
    "daily_kwh_count",
    "fan_filter_remain",
    "flowmeter_timer",
    "gateway_status",
    "gauge_angle",
    "hourly_flow_count",
    "hourly_kwh_count",
    "intensity_min",
    "keypad",
    "keypad_status",
    "language",
    "leak_status",
    "led_off_color",
    "led_off_intensity",
    "led_on_color",
    "led_on_intensity",
    "level_status",
    "light_timer",
    "max_cool_temp",
    "max_temp",
    "min_cool_temp",
    "min_temp",
    "monthly_flow_count",
    "monthly_kwh_count",
    "occupancy_mode",
    "pi_heating_demand",
    "power_timer",
    "refuel_status",
    "rssi",
    "temp_alert" "timer",
    "timer2",
    "total_flow_count",
    "total_kwh_count",
    "water_leak_status",
    # Constants
    "is_wifi",
    "is_HC",
    "is_HP",
    # ... etc.
]
