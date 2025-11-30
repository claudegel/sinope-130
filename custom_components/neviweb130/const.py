"""Constants for neviweb130 component."""

import json
import pathlib

# Base component constants, some loaded directly from the manifest
_LOADER_PATH = pathlib.Path(__loader__.path)  # type: ignore
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
If not done yet you can delete or comment out config in configuration.yaml.
-------------------------------------------------------------------
"""

CONF_HOMEKIT_MODE = "homekit_mode"
CONF_IGNORE_MIWI = "ignore_miwi"
CONF_NETWORK = "network"
CONF_NETWORK2 = "network2"
CONF_NETWORK3 = "network3"
CONF_NOTIFY = "notify"
CONF_STAT_INTERVAL = "stat_interval"

ATTR_ACCESSORY_TYPE = "accessoryType"
ATTR_ACTIVE = "active"
ATTR_AIR_ACTIVATION_TEMP = "airCurtainActivationTemperature"
ATTR_AIR_CONFIG = "airCurtainConfig"
ATTR_AIR_EX_MIN_TIME_ON = "airExchangerMinTimeOn"
ATTR_AIR_MAX_POWER_TEMP = "airCurtainMaxPowerTemperature"
ATTR_ALERT = "alert"
ATTR_ANGLE = "angle"
ATTR_AUX_CYCLE_LENGTH = "auxCycleLength"
ATTR_AUX_HEAT_MIN_TIME_OFF = "auxHeatMinTimeOff"
ATTR_AUX_HEAT_MIN_TIME_ON = "auxHeatMinTimeOn"
ATTR_AUX_HEAT_SOURCE_TYPE = "auxHeatSourceType"
ATTR_AUX_HEAT_START_DELAY = "auxHeatStartDelay"
ATTR_AUX_INTERSTAGE_DELAY = "auxInterstageDelay"
ATTR_AUX_INTERSTAGE_MIN_DELAY = "auxInterstageMinDelay"
ATTR_AUX_OPTIM = "auxOptim"
ATTR_AVAIL_MODE = "availableMode"
ATTR_AWAY_ACTION = "awayAction"
ATTR_BACKLIGHT = "backlightAdaptive"
ATTR_BACK_LIGHT = "backlight"
ATTR_BACKLIGHT_AUTO_DIM = "backlightAutoDim"
ATTR_BALANCE_PT = "balancePoint"
ATTR_BALANCE_PT_TEMP_HIGH = "balancePointTempHigh"
ATTR_BALANCE_PT_TEMP_LOW = "balancePointTempLow"
ATTR_BATTERY_STATUS = "batteryStatus"
ATTR_BATTERY_TYPE = "batteryType"
ATTR_BATTERY_VOLTAGE = "batteryVoltage"
ATTR_BATT_ACTION_LOW = "batteryActionLow"
ATTR_BATT_ALERT = "alertLowBatt"
ATTR_BATT_INFO = "displayBatteryInfo"
ATTR_BATT_PERCENT_NORMAL = "batteryPercentNormalized"
ATTR_BATT_STATUS_NORMAL = "batteryStatusNormalized"
ATTR_BLUE = "blue"
ATTR_CLOSE_VALVE = "closeValve"
ATTR_COLD_LOAD_PICKUP = "coldLoadPickup"
ATTR_COLD_LOAD_PICKUP_REMAIN_TIME = "coldLoadPickupRemainingTime"
ATTR_COLD_LOAD_PICKUP_STATUS = "coldLoadPickupStatus"
ATTR_COLD_LOAD_PICKUP_TEMP = "coldLoadPickupTemperature"
ATTR_COLOR = "color"
ATTR_CONF_CLOSURE = "cfgValveClosure"
ATTR_CONTROLLED_DEVICE = "controlledDevice"
ATTR_COOL_CYCLE_LENGTH = "coolCycleLength"
ATTR_COOL_INTERSTAGE_DELAY = "coolInterstageDelay"
ATTR_COOL_INTERSTAGE_MIN_DELAY = "coolInterstageMinDelay"
ATTR_COOL_LOCK_TEMP = "coolLockoutTemperature"
ATTR_COOL_MIN_TIME_OFF = "coolMinTimeOff"
ATTR_COOL_MIN_TIME_ON = "coolMinTimeOn"
ATTR_COOL_PURGE_TIME = "coolPurgeTime"
ATTR_COOL_SETPOINT = "coolSetpoint"
ATTR_COOL_SETPOINT_AWAY = "coolSetpointAway"
ATTR_COOL_SETPOINT_MAX = "coolSetpointMax"
ATTR_COOL_SETPOINT_MIN = "coolSetpointMin"
ATTR_CYCLE_LENGTH = "cycleLength"
ATTR_CYCLE_OUTPUT2 = "cycleLengthOutput2"  # status on/off, value (second)
ATTR_DELAY = "delay"
ATTR_DISPLAY2 = "config2ndDisplay"
ATTR_DISPLAY_CAP = "displayCapability"
ATTR_DISPLAY_CONF = "displayConfig"
ATTR_DRACCESORYCONF = "drAccessoryConfig"
ATTR_DRACTIVE = "drActive"
ATTR_DRAIR_CURT_CONF = "drAirCurtainConfig"
ATTR_DRAUXCONF = "drAuxConfig"
ATTR_DRFANCONF = "drFanSpeedConfig"
ATTR_DRSETPOINT = "drSetpoint"
ATTR_DRSTATUS = "drStatus"
ATTR_DR_AUX_CONF = "drAuxConfig"
ATTR_DR_FAN_SPEED_CONF = "drFanSpeedConfig"
ATTR_DR_PROTEC_STATUS = "drProtectionLegStatus"
ATTR_DR_WATER_TEMP_TIME = "drConfigWaterTempTime"
ATTR_DUAL_STATUS = "dualEnergyStatus"
ATTR_EARLY_START = "earlyStartCfg"
ATTR_ERROR_CODE_SET1 = "errorCodeSet1"
ATTR_EXT_TEMP = "externalTemperature"
ATTR_FAN_CAP = "fanCapabilities"
ATTR_FAN_FILTER_REMAIN = "fanFilterReminderPeriod"
ATTR_FAN_SPEED = "fanSpeed"
ATTR_FAN_SPEED_OPTIM = "fanSpeedOptim"
ATTR_FAN_SWING_CAP = "fanSwingCapabilities"
ATTR_FAN_SWING_CAP_HORIZ = "fanSwingCapabilityHorizontal"
ATTR_FAN_SWING_CAP_VERT = "fanSwingCapabilityVertical"
ATTR_FAN_SWING_HORIZ = "fanSwingHorizontal"
ATTR_FAN_SWING_VERT = "fanSwingVertical"
ATTR_FLOOR_AIR_LIMIT = "floorMaxAirTemperature"
ATTR_FLOOR_AUX = "auxHeatConfig"
ATTR_FLOOR_MAX = "floorLimitHigh"
ATTR_FLOOR_MIN = "floorLimitLow"
ATTR_FLOOR_MODE = "airFloorMode"
ATTR_FLOOR_OUTPUT1 = "loadWattOutput1"  # status on/off, value=xx
ATTR_FLOOR_OUTPUT2 = "loadWattOutput2"  # status on/off, value=xx
ATTR_FLOOR_SENSOR = "floorSensorType"
ATTR_FLOW_ALARM1 = "flowMeterAlarm1Config"
ATTR_FLOW_ALARM1_LENGTH = "alarm1Length"
ATTR_FLOW_ALARM1_OPTION = "alarm1Options"
ATTR_FLOW_ALARM1_PERIOD = "alarm1Period"
ATTR_FLOW_ALARM2 = "flowMeterAlarm2Config"
ATTR_FLOW_ALARM_TIMER = "flowMeterAlarmDisableTimer"
ATTR_FLOW_ENABLED = "flowMeterEnabled"
ATTR_FLOW_METER_CONFIG = "flowMeterMeasurementConfig"
ATTR_FLOW_MODEL_CONFIG = "FlowModel"
ATTR_FLOW_THRESHOLD = "alarm1FlowThreshold"
ATTR_FUEL_ALERT = "alertLowFuel"
ATTR_FUEL_PERCENT_ALERT = "alertLowFuelPercent"
ATTR_GAUGE_TYPE = "gaugeType"
ATTR_GFCI_ALERT = "alertGfci"
ATTR_GFCI_STATUS = "gfciStatus"
ATTR_GREEN = "green"
ATTR_HC_DEV = "hcDevice"
ATTR_HC_LOCK_STATUS = "heatCoolLockoutStatus"
ATTR_HEATCOOL_SETPOINT_MIN_DELTA = "heatCoolSetpointMinDelta"
ATTR_HEAT_COOL = "heatCoolMode"
ATTR_HEAT_INSTALL_TYPE = "HeatInstallationType"
ATTR_HEAT_INTERSTAGE_DELAY = "heatInterstageDelay"
ATTR_HEAT_INTERSTAGE_MIN_DELAY = "heatInterstageMinDelay"
ATTR_HEAT_LOCKOUT_TEMP = "heatLockoutTemp"
ATTR_HEAT_LOCK_TEMP = "heatLockoutTemperature"
ATTR_HEAT_MIN_TIME_OFF = "heatMinTimeOff"
ATTR_HEAT_MIN_TIME_ON = "heatMinTimeOn"
ATTR_HEAT_PURGE_TIME = "heatPurgeTime"
ATTR_HEAT_SOURCE_TYPE = "heatSourceType"
ATTR_HUMIDITY = "humidity"
ATTR_HUMIDITY_DISPLAY = "humidityDisplay"
ATTR_HUMIDITY_SETPOINT = "humiditySetpoint"
ATTR_HUMIDITY_SETPOINT_MODE = "humiditySetpointMode"
ATTR_HUMIDITY_SETPOINT_OFFSET = "humiditySetpointOffset"
ATTR_INPUT2_STATUS = "input2Status"
ATTR_INPUT_1_OFF_DELAY = "inputOffDebounceDelay"
ATTR_INPUT_1_ON_DELAY = "inputOnDebounceDelay"
ATTR_INPUT_2_OFF_DELAY = "inputOffDebounceDelay2"
ATTR_INPUT_2_ON_DELAY = "inputOnDebounceDelay2"
ATTR_INPUT_NUMBER = "input_number"
ATTR_INPUT_STATUS = "inputStatus"
ATTR_INTENSITY = "intensity"
ATTR_INTENSITY_MIN = "intensityMin"
ATTR_INTERLOCK_HC_MODE = "interlockMasterHeatCoolMode"
ATTR_INTERLOCK_ID = "interlockUniqueId"
ATTR_INTERLOCK_PARTNER = "interlockPartnerActive"
ATTR_KEYPAD = "lockKeypad"
ATTR_KEY_DOUBLE_UP = "configKeyDoubleUp"
ATTR_LANGUAGE = "language"
ATTR_LEAK_ALERT = "alertWaterLeak"
ATTR_LEAK_CLOSURE_CONFIG = "waterLeakClosureConfig"
ATTR_LED_OFF_COLOR = "statusLedOffColor"
ATTR_LED_OFF_INTENSITY = "statusLedOffIntensity"
ATTR_LED_ON_COLOR = "statusLedOnColor"
ATTR_LED_ON_INTENSITY = "statusLedOnIntensity"
ATTR_LEG_PROTEC_STATUS = "legProtectionStatus"
ATTR_LIGHT_WATTAGE = "loadWattOutput1"  # status on/off, value=xx
ATTR_LOW_TEMP_STATUS = "alertLowTempStatus"
ATTR_MIN_WATER_TEMP = "minWaterTankTemperature"
ATTR_MODE = "mode"
ATTR_MODEL = "model"
ATTR_MOTOR_POS = "motorPosition"
ATTR_MOTOR_TARGET = "motorTargetPosition"
ATTR_NAME_1 = "input1name"
ATTR_NAME_2 = "input2name"
ATTR_OCCUPANCY = "occupancyMode"
ATTR_OCCUPANCY_SENSOR_DELAY = "occupancySensorUnoccupiedDelay"
ATTR_ONOFF = "onOff"
ATTR_ONOFF2 = "onOff2"
ATTR_ONOFF_NUM = "onOff_num"
ATTR_OPTOUT = "optOut"
ATTR_OUTPUT1 = "loadWattOutput1"
ATTR_OUTPUT_CONNECT_STATE = "bulkOutputConnectedState"
ATTR_OUTPUT_NAME_1 = "output1name"
ATTR_OUTPUT_NAME_2 = "output2name"
ATTR_OUTPUT_PERCENT_DISPLAY = "outputPercentDisplay"
ATTR_PHASE_CONTROL = "phaseControl"
ATTR_POLARITY = "polarity"
ATTR_POWER_MODE = "powerMode"
ATTR_POWER_SUPPLY = "backupPowerSupply"
ATTR_PUMP_PROTEC = "pumpProtection"  # status on/off, duration, frequency
ATTR_PUMP_PROTEC_DURATION = "pumpProtectDuration"  # status on/off, value
ATTR_PUMP_PROTEC_PERIOD = "pumpProtectPeriod"  # status on/off, value
ATTR_RED = "red"
ATTR_REFUEL = "alertRefuel"
ATTR_REL_HUMIDITY = "relativeHumidity"
ATTR_REVERSING_VALVE_POLARITY = "reversingValvePolarity"
ATTR_ROOM_SETPOINT = "roomSetpoint"
ATTR_ROOM_SETPOINT_AWAY = "roomSetpointAway"
ATTR_ROOM_SETPOINT_MAX = "roomSetpointMax"
ATTR_ROOM_SETPOINT_MIN = "roomSetpointMin"
ATTR_ROOM_TEMPERATURE = "roomTemperature"
ATTR_ROOM_TEMP_ALARM = "roomTemperatureAlarmStatus"
ATTR_ROOM_TEMP_DISPLAY = "roomTemperatureDisplay"
ATTR_RSSI = "rssi"
ATTR_SAMPLING = "samplingTime"
ATTR_SENSOR_TYPE = "sensorType"
ATTR_SETPOINT = "setpoint"
ATTR_SETPOINT_MODE = "setpointMode"
ATTR_SIGNATURE = "signature"
ATTR_SOUND_CAP = "soundCapability"
ATTR_SOUND_CONF = "soundConfig"
ATTR_STATE = "state"
ATTR_STATUS = "status"
ATTR_STM8_ERROR = "stm8Error"
ATTR_SYSTEM_MODE = "systemMode"
ATTR_SYSTEM_MODE_AVAIL = "systemModeAvailability"
ATTR_TANK_HEIGHT = "tankHeight"
ATTR_TANK_PERCENT = "tankPercent"
ATTR_TANK_SIZE = "tankSize"
ATTR_TANK_TYPE = "tankType"
ATTR_TEMP = "temperatureFormat"
ATTR_TEMPERATURE = "temperature"
ATTR_TEMP_ACTION_LOW = "temperatureActionLow"
ATTR_TEMP_ALARM = "temperatureAlarmStatus"
ATTR_TEMP_ALERT = "alertLowTemp"
ATTR_TEMP_OFFSET_HEAT = "temperatureOffsetHeat"
ATTR_TIME = "time"
ATTR_TIMER = "powerTimer"
ATTR_TIMER2 = "powerTimer2"
ATTR_TIME_FORMAT = "timeFormat"
ATTR_TRIGGER_ALARM = "triggerAlarm"
ATTR_TYPE = "type"
ATTR_VALUE = "value"
ATTR_VALVE_CLOSURE = "valveClosureSource"  # source
ATTR_VALVE_INFO = "valveInfo"
ATTR_WATER_LEAK_ALARM_STATUS = "waterleakDetectionAlarmStatus"
ATTR_WATER_LEAK_DISCONNECTED_STATUS = "waterleakDisconnectedAlarmStatus"
ATTR_WATER_LEAK_STATUS = "waterLeakStatus"
ATTR_WATER_TANK_ON = "waterTankTimeOn"
ATTR_WATER_TEMPERATURE = "waterTemperature"
ATTR_WATER_TEMP_MIN = "drConfigWaterTempMin"
ATTR_WATER_TEMP_PROTEC = "waterTempProtectionType"
ATTR_WATER_TEMP_TIME = "waterTempTime"
ATTR_WATTAGE = "loadConnected"
ATTR_WATTAGE_INSTANT = "wattageInstant"
ATTR_WATTAGE_OVERRIDE = "wattageOverride"
ATTR_WATT_TIME_ON = "drWTTimeOn"
ATTR_WIFI = "wifiRssi"
ATTR_WIFI_KEYPAD = "keyboardLock"
ATTR_WIFI_WATTAGE = "loadWatt"  # value
ATTR_WIFI_WATT_NOW = "loadWattNow"

SIGNAL_EVENTS_CHANGED = f"{DOMAIN}_events_changed"

MODE_AUTO = "auto"
MODE_AUTO_BYPASS = "autoBypass"
MODE_AWAY = "away"
MODE_EM_HEAT = "emergencyHeat"
MODE_HOME = "home"
MODE_MANUAL = "manual"
MODE_OFF = "off"

STATE_KEYPAD_STATUS = "unlocked"
STATE_VALVE_STATUS = "open"
STATE_WATER_LEAK = "water"

SERVICE_SET_ACCESSORY_TYPE = "set_accessory_type"
SERVICE_SET_ACTIVATION = "set_activation"
SERVICE_SET_AIR_FLOOR_MODE = "set_air_floor_mode"
SERVICE_SET_AUXILIARY_LOAD = "set_auxiliary_load"
SERVICE_SET_AUX_CYCLE_OUTPUT = "set_aux_cycle_output"
SERVICE_SET_AUX_HEATING_SOURCE = "set_aux_heating_source"
SERVICE_SET_BACKLIGHT = "set_backlight"
SERVICE_SET_BATTERY_ALERT = "set_battery_alert"
SERVICE_SET_BATTERY_TYPE = "set_battery_type"
SERVICE_SET_CLIMATE_KEYPAD_LOCK = "set_climate_keypad_lock"
SERVICE_SET_CLIMATE_NEVIWEB_STATUS = "set_climate_neviweb_status"
SERVICE_SET_CONTROLLED_DEVICE = "set_controlled_device"
SERVICE_SET_CONTROL_ONOFF = "set_control_onoff"
SERVICE_SET_COOL_DISSIPATION_TIME = "set_cool_dissipation_time"
SERVICE_SET_COOL_INTERSTAGE_DELAY = "set_cool_interstage_delay"
SERVICE_SET_COOL_LOCKOUT_TEMPERATURE = "set_cool_lockout_temperature"
SERVICE_SET_COOL_SETPOINT_AWAY = "set_cool_setpoint_away"
SERVICE_SET_COOL_SETPOINT_MAX = "set_cool_setpoint_max"
SERVICE_SET_COOL_SETPOINT_MIN = "set_cool_setpoint_min"
SERVICE_SET_CYCLE_OUTPUT = "set_cycle_output"
SERVICE_SET_DISPLAY_CONFIG = "set_display_config"
SERVICE_SET_EARLY_START = "set_early_start"
SERVICE_SET_EM_HEAT = "set_em_heat"
SERVICE_SET_FAN_FILTER_REMINDER = "set_fan_filter_reminder"
SERVICE_SET_FAN_SPEED = "set_fan_speed"
SERVICE_SET_FLOOR_AIR_LIMIT = "set_floor_air_limit"
SERVICE_SET_FLOOR_LIMIT_HIGH = "set_floor_limit_high"
SERVICE_SET_FLOOR_LIMIT_LOW = "set_floor_limit_low"
SERVICE_SET_FLOW_ALARM_DISABLE_TIMER = "set_flow_alarm_disable_timer"
SERVICE_SET_FLOW_METER_DELAY = "set_flow_meter_delay"
SERVICE_SET_FLOW_METER_MODEL = "set_flow_meter_model"
SERVICE_SET_FLOW_METER_OPTIONS = "set_flow_meter_options"
SERVICE_SET_FUEL_ALERT = "set_fuel_alert"
SERVICE_SET_GAUGE_TYPE = "set_gauge_type"
SERVICE_SET_HC_SECOND_DISPLAY = "set_hc_second_display"
SERVICE_SET_HEATCOOL_SETPOINT_DELTA = "set_heatcool_setpoint_delta"
SERVICE_SET_HEAT_DISSIPATION_TIME = "set_heat_dissipation_time"
SERVICE_SET_HEAT_INTERSTAGE_DELAY = "set_heat_interstage_delay"
SERVICE_SET_HEAT_LOCKOUT_TEMPERATURE = "set_heat_lockout_temperature"
SERVICE_SET_HEAT_PUMP_OPERATION_LIMIT = "set_heat_pump_operation_limit"
SERVICE_SET_HUMIDITY_SETPOINT_MODE = "set_humidity_mode"
SERVICE_SET_HVAC_DR_OPTIONS = "set_hvac_dr_options"
SERVICE_SET_HVAC_DR_SETPOINT = "set_hvac_dr_setpoint"
SERVICE_SET_INPUT_OUTPUT_NAMES = "set_input_output_names"
SERVICE_SET_KEY_DOUBLE_UP = "set_key_double_up"
SERVICE_SET_LANGUAGE = "set_language"
SERVICE_SET_LED_INDICATOR = "set_led_indicator"
SERVICE_SET_LED_OFF_INTENSITY = "set_led_off_intensity"
SERVICE_SET_LED_ON_INTENSITY = "set_led_on_intensity"
SERVICE_SET_LIGHT_KEYPAD_LOCK = "set_light_keypad_lock"
SERVICE_SET_LIGHT_MIN_INTENSITY = "set_light_min_intensity"
SERVICE_SET_LIGHT_TIMER = "set_light_timer"
SERVICE_SET_LOAD_DR_OPTIONS = "set_load_dr_options"
SERVICE_SET_LOW_FUEL_ALERT = "set_low_fuel_alert"
SERVICE_SET_LOW_TEMP_PROTECTION = "set_low_temp_protection"
SERVICE_SET_MIN_TIME_OFF = "set_min_time_off"
SERVICE_SET_MIN_TIME_ON = "set_min_time_on"
SERVICE_SET_NEVIWEB_STATUS = "set_neviweb_status"
SERVICE_SET_ON_OFF_INPUT_DELAY = "set_on_off_input_delay"
SERVICE_SET_PHASE_CONTROL = "set_phase_control"
SERVICE_SET_POWER_SUPPLY = "set_power_supply"
SERVICE_SET_PUMP_PROTECTION = "set_pump_protection"
SERVICE_SET_REFUEL_ALERT = "set_refuel_alert"
SERVICE_SET_REMAINING_TIME = "set_remaining_time"
SERVICE_SET_REVERSING_VALVE_POLARITY = "set_reversing_valve_polarity"
SERVICE_SET_ROOM_SETPOINT_AWAY = "set_room_setpoint_away"
SERVICE_SET_SCHEDULE_MODE = "set_schedule_mode"
SERVICE_SET_SECOND_DISPLAY = "set_second_display"
SERVICE_SET_SENSOR_CLOSURE_ACTION = "set_sensor_closure_action"
SERVICE_SET_SENSOR_LEAK_ALERT = "set_sensor_leak_alert"
SERVICE_SET_SENSOR_TEMP_ALERT = "set_sensor_temp_alert"
SERVICE_SET_SENSOR_TYPE = "set_sensor_type"
SERVICE_SET_SETPOINT_MAX = "set_setpoint_max"
SERVICE_SET_SETPOINT_MIN = "set_setpoint_min"
SERVICE_SET_SOUND_CONFIG = "set_sound_config"
SERVICE_SET_SWITCH_KEYPAD_LOCK = "set_switch_keypad_lock"
SERVICE_SET_SWITCH_POWER_TIMER = "set_switch_power_timer"
SERVICE_SET_SWITCH_TIMER = "set_switch_timer"
SERVICE_SET_SWITCH_TIMER_2 = "set_switch_timer2"
SERVICE_SET_TANK_HEIGHT = "set_tank_height"
SERVICE_SET_TANK_SIZE = "set_tank_size"
SERVICE_SET_TANK_TYPE = "set_tank_type"
SERVICE_SET_TEMPERATURE_FORMAT = "set_temperature_format"
SERVICE_SET_TEMPERATURE_OFFSET = "set_temperature_offset"
SERVICE_SET_TIME_FORMAT = "set_time_format"
SERVICE_SET_VALVE_ALERT = "set_valve_alert"
SERVICE_SET_VALVE_TEMP_ALERT = "set_valve_temp_alert"
SERVICE_SET_WATTAGE = "set_wattage"
SERVICE_SET_WIFI_CLIMATE_KEYPAD_LOCK = "set_wifi_climate_keypad_lock"

CLIMATE_MODEL = [
    300,
    336,
    350,
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
    6731,
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
FULL_MODEL = CLIMATE_MODEL + LIGHT_MODEL + SWITCH_MODEL + VALVE_MODEL + SENSOR_MODEL

# list attributes available for each device model
MODEL_ATTRIBUTES = {
    # thermostats
    300: {  # TH1123ZB-G2 3000W, TH1124ZB-G2 4000W
        "sensor": [
            ATTR_RSSI,
            "current_temperature",
            "daily_kwh_count",
            "hourly_kwh_count",
            "monthly_kwh_count",
            "pi_heating_demand",
            "total_kwh_count",
            "wattage",
        ],
        "number": [
            "max_temp",
            "min_temp",
        ],
        "select": [
            "backlight",
            "cycle_length",
            "keypad_status",
            "occupancy_mode",
            "second_display",
            "temp_format",
            "time_format",
        ],
        "binary_sensor": [
            "activation",
            "is_heating",
        ],
        "button": [],
        "switch": [],
    },
    336: {  # TH1133WF, TH1133CR, TH1134WF, TH1134CR
        "sensor": [
            ATTR_RSSI,
            "current_temperature",
            "pi_heating_demand",
        ],
        "number": [
            "max_temp",
            "min_temp",
            "setpoint_away",
        ],
        "select": [
            "backlight",
            "cycle_length",
            "early_start",
            "occupancy_mode",
            "temp_format",
            "wifi_keypad",
        ],
        "binary_sensor": ["activation"],
        "button": [],
        "switch": [],
    },
    350: {  # TH1143WF, TH1144WF color screen
        "sensor": [
            ATTR_RSSI,
            "current_temperature",
            "daily_kwh_count",
            "hourly_kwh_count",
            "monthly_kwh_count",
            "pi_heating_demand",
            "total_kwh_count",
            "wattage",
        ],
        "number": [
            "max_temp",
            "min_temp",
            "setpoint_away",
        ],
        "select": [
            "backlight",
            "early_start",
            "language",
            "occupancy_mode",
            "temp_format",
            "time_format",
            "wifi_keypad",
        ],
        "binary_sensor": [
            "activation",
            "is_heating",
        ],
        "button": [],
        "switch": [],
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
            "floor_setpoint_max",
            "floor_setpoint_min",
            "max_temp",
            "min_temp",
        ],
        "select": [
            "backlight",
            "keypad_status",
            "occupancy_mode",
            "second_display",
            "sensor_mode",
            "temp_format",
            "time_format",
        ],
        "binary_sensor": [
            "activation",
            "is_heating",
        ],
        "button": [],
        "switch": [],
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
            "wattage",
        ],
        "number": [
            "floor_setpoint_max",
            "floor_setpoint_min",
            "max_temp",
            "min_temp",
            "setpoint_away",
        ],
        "select": [
            "backlight",
            "early_start",
            "occupancy_mode",
            "second_display",
            "sensor_mode",
            "temp_format",
            "time_format",
            "wifi_keypad",
        ],
        "binary_sensor": [
            "activation",
            "is_heating",
        ],
        "button": [],
        "switch": [],
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
            "wattage",
        ],
        "number": [
            "floor_setpoint_max",
            "floor_setpoint_min",
            "max_temp",
            "min_temp",
            "setpoint_away",
        ],
        "select": [
            "backlight",
            "early_start",
            "lv_cycle_length",
            "lv_cycle_length",
            "occupancy_mode",
            "second_display",
            "sensor_mode",
            "temp_format",
            "time_format",
            "wifi_keypad",
        ],
        "binary_sensor": [
            "activation",
            "is_heating",
        ],
        "button": [],
        "switch": [],
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
            "wattage",
        ],
        "number": [
            "max_temp",
            "min_temp",
            "setpoint_away",
        ],
        "select": [
            "backlight",
            "early_start",
            "occupancy_mode",
            "second_display",
            "temp_format",
            "time_format",
            "wifi_cycle_length",
            "wifi_keypad",
        ],
        "binary_sensor": [
            "activation",
            "is_heating",
        ],
        "button": [],
        "switch": [],
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
            "wattage",
        ],
        "number": [
            "max_temp",
            "min_temp",
        ],
        "select": [
            "aux_cycle_length",
            "backlight",
            "cycle_length",
            "keypad_status",
            "occupancy_mode",
            "second_display",
            "temp_format",
            "time_format",
        ],
        "binary_sensor": [
            "activation",
            "is_heating",
        ],
        "button": [],
        "switch": [],
    },
    1124: {  # TH1124ZB 4000W, OTH4000-ZB
        "sensor": [
            ATTR_RSSI,
            "current_temperature",
            "daily_kwh_count",
            "hourly_kwh_count",
            "monthly_kwh_count",
            "pi_heating_demand",
            "total_kwh_count",
            "wattage",
        ],
        "number": [
            "max_temp",
            "min_temp",
        ],
        "select": [
            "aux_cycle_length",
            "backlight",
            "cycle_length",
            "keypad_status",
            "occupancy_mode",
            "second_display",
            "temp_format",
            "time_format",
        ],
        "binary_sensor": [
            "activation",
            "is_heating",
        ],
        "button": [],
        "switch": [],
    },
    1510: {  # TH1123WF 3000W, TH1124WF 4000W
        "sensor": [
            ATTR_RSSI,
            "current_temperature",
            "daily_kwh_count",
            "hourly_kwh_count",
            "monthly_kwh_count",
            "pi_heating_demand",
            "total_kwh_count",
            "wattage",
        ],
        "number": [
            "max_temp",
            "min_temp",
            "setpoint_away",
        ],
        "select": [
            "backlight",
            "cycle_length",
            "early_start",
            "occupancy_mode",
            "second_display",
            "temp_format",
            "time_format",
            "wifi_keypad",
        ],
        "binary_sensor": [
            "activation",
            "is_heating",
        ],
        "button": [],
        "switch": [],
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
            "wattage",
        ],
        "number": [
            "max_temp",
            "min_temp",
        ],
        "select": [
            "aux_cycle_length",
            "backlight",
            "cycle_length",
            "hc_second_display",
            "keypad_status",
            "language",
            "occupancy_mode",
            "temp_format",
            "time_format",
        ],
        "binary_sensor": [
            "activation",
            "is_heating",
        ],
        "button": [],
        "switch": [],
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
            "cool_setpoint_away",
            "fan_filter_remain",
            "max_cool_temp",
            "min_cool_temp",
            "max_temp",
            "min_temp",
            "setpoint_away",
        ],
        "select": [
            "backlight",
            "early_start",
            "language",
            "occupancy_mode",
            "temp_format",
            "time_format",
            "pro_aux_cycle_length",
            "wifi_cycle",
            "wifi_keypad",
        ],
        "binary_sensor": ["activation"],
        "button": [],
        "switch": [],
    },
    6730: {  # TH6250WF
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
            "cool_setpoint_away",
            "fan_filter_remain",
            "max_cool_temp",
            "max_temp",
            "min_cool_temp",
            "min_temp",
        ],
        "select": [
            "backlight",
            "early_start",
            "language",
            "occupancy_mode",
            "temp_format",
            "time_format",
            "wifi_aux_cycle_length",
            "wifi_cycle",
            "wifi_keypad",
        ],
        "binary_sensor": ["activation"],
        "button": [],
        "switch": [],
    },
    6731: {  # TH6250WF-PRO
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
            "cool_setpoint_away",
            "fan_filter_remain",
            "max_cool_temp",
            "max_temp",
            "min_cool_temp",
            "min_temp",
        ],
        "select": [
            "backlight",
            "early_start",
            "language",
            "occupancy_mode",
            "temp_format",
            "time_format",
            "pro_aux_cycle_length",
            "wifi_cycle",
            "wifi_keypad",
        ],
        "binary_sensor": ["activation"],
        "button": [],
        "switch": [],
    },
    6810: {  # HP6000ZB-GE
        "sensor": [
            ATTR_RSSI,
            "occupancy_mode",
        ],
        "number": [
            "max_temp",
            "min_temp",
        ],
        "select": ["keypad_status"],
        "binary_sensor": ["activation"],
        "button": [],
        "switch": [],
    },
    6811: {  # HP6000ZB-MA
        "sensor": [
            ATTR_RSSI,
            "occupancy_mode",
        ],
        "number": [
            "max_temp",
            "min_temp",
        ],
        "select": ["keypad_status"],
        "binary_sensor": ["activation"],
        "button": [],
        "switch": [],
    },
    6812: {  # HP6000ZB-HS
        "sensor": [
            ATTR_RSSI,
            "occupancy_mode",
        ],
        "number": [
            "max_temp",
            "min_temp",
        ],
        "select": ["keypad_status"],
        "binary_sensor": ["activation"],
        "button": [],
        "switch": [],
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
            "wattage",
        ],
        "number": [
            "floor_setpoint_max",
            "floor_setpoint_min",
            "max_temp",
            "min_temp",
        ],
        "select": [
            "aux_cycle_length",
            "backlight",
            "keypad_status",
            "lv_cycle_length",
            "occupancy_mode",
            "second_display",
            "sensor_mode",
            "temp_format",
            "time_format",
        ],
        "binary_sensor": [
            "activation",
            "is_heating",
        ],
        "button": [],
        "switch": [],
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
            "wattage",
        ],
        "number": [
            "max_temp",
            "min_temp",
        ],
        "select": [
            "aux_cycle_length",
            "backlight",
            "cycle_length",
            "keypad_status",
            "occupancy_mode",
            "second_display",
            "temp_format",
            "time_format",
        ],
        "binary_sensor": [
            "activation",
            "is_heating",
        ],
        "button": [],
        "switch": [],
    },
    # Lights
    2121: {  # SW2500ZB, SW2500ZB-G2
        "sensor": [
            ATTR_RSSI,
            "daily_kwh_count",
            "hourly_kwh_count",
            "monthly_kwh_count",
            "total_kwh_count",
            "wattage",
        ],
        "number": [
            "brightness",
            "intensity_min",
            "led_off_intensity",
            "led_on_intensity",
        ],
        "select": [
            "keypad",
            "led_off_color",
            "led_on_color",
            "light_timer",
        ],
        "binary_sensor": ["activation"],
        "button": [],
        "switch": [],
    },
    2131: {  # DM2500ZB, DM2500ZB-G2
        "sensor": [
            ATTR_RSSI,
            "daily_kwh_count",
            "hourly_kwh_count",
            "monthly_kwh_count",
            "total_kwh_count",
            "wattage",
        ],
        "number": [
            "brightness",
            "intensity_min",
            "led_off_intensity",
            "led_on_intensity",
        ],
        "select": [
            "keypad",
            "led_off_color",
            "led_on_color",
            "light_timer",
        ],
        "binary_sensor": ["activation"],
        "button": [],
        "switch": [],
    },
    2132: {  # DM2550ZB, DM2550ZB-G2
        "sensor": [
            ATTR_RSSI,
            "daily_kwh_count",
            "hourly_kwh_count",
            "monthly_kwh_count",
            "total_kwh_count",
            "wattage",
        ],
        "number": [
            "brightness",
            "intensity_min",
            "led_off_intensity",
            "led_on_intensity",
        ],
        "select": [
            "keypad",
            "led_off_color",
            "led_on_color",
            "light_timer",
            "phase_control",
        ],
        "binary_sensor": ["activation"],
        "button": [],
        "switch": [],
    },
    # Switch
    346: {  # RM3250WF, 50A, Wi-Fi
        "sensor": [
            ATTR_RSSI,
            "daily_kwh_count",
            "hourly_kwh_count",
            "monthly_kwh_count",
            "total_kwh_count",
            "wattage",
        ],
        "number": [],
        "select": ["switch_keypad"],
        "binary_sensor": ["activation"],
        "button": [],
        "switch": [],
    },
    2151: {  # RM3500ZB 20,8A, Zigbee
        "sensor": [
            ATTR_RSSI,
            "daily_kwh_count",
            "hourly_kwh_count",
            "monthly_kwh_count",
            "total_kwh_count",
            "wattage",
        ],
        "number": ["water_remaining_time"],
        "select": [
            "tank_size",
            "heater_temp_min",
        ],
        "binary_sensor": [
            "activation",
            "water_leak_status",
        ],
        "button": [],
        "switch": [],
    },
    2152: {  # RM3500WF 20,8A, Wi-Fi, RM3510WF 20,8A, Wi-Fi
        "sensor": [
            ATTR_RSSI,
            "daily_kwh_count",
            "hourly_kwh_count",
            "monthly_kwh_count",
            "total_kwh_count",
            "wattage",
        ],
        "number": ["water_remaining_time"],
        "select": [
            "tank_size",
            "heater_temp_min",
        ],
        "binary_sensor": [
            "activation",
            "water_leak_status",
        ],
        "button": [],
        "switch": [],
    },
    2180: {  # MC3100ZB connected to GT130
        "sensor": [
            ATTR_RSSI,
            "room_humidity",
        ],
        "number": [],
        "select": [
            "timer",
            "timer2",
        ],
        "binary_sensor": [
            "activation",
            "low_temp_status",
        ],
        "button": [],
        "switch": [
            "alert_temp",
            "onoff2",
        ],
    },
    2181: {  # MC3100ZB connected to Sedna valve
        "sensor": [
            ATTR_RSSI,
            "room_humidity",
        ],
        "number": [],
        "select": [
            "timer",
            "timer2",
        ],
        "binary_sensor": [
            "activation",
            "low_temp_status",
        ],
        "button": [],
        "switch": [
            "alert_temp",
            "onoff2",
        ],
    },
    2506: {  # RM3250ZB, 50A, Zigbee
        "sensor": [
            ATTR_RSSI,
            "daily_kwh_count",
            "hourly_kwh_count",
            "monthly_kwh_count",
            "total_kwh_count",
            "wattage",
        ],
        "number": [],
        "select": [
            "power_timer",
            "switch_keypad",
        ],
        "binary_sensor": ["activation"],
        "button": [],
        "switch": [],
    },
    2600: {  # SP2600ZB
        "sensor": [
            ATTR_RSSI,
            "daily_kwh_count",
            "hourly_kwh_count",
            "monthly_kwh_count",
            "total_kwh_count",
            "wattage",
        ],
        "number": [],
        "select": [],
        "binary_sensor": ["activation"],
        "button": [],
        "switch": [],
    },
    2610: {  # SP2610ZB
        "sensor": [
            ATTR_RSSI,
            "daily_kwh_count",
            "hourly_kwh_count",
            "monthly_kwh_count",
            "total_kwh_count",
            "wattage",
        ],
        "number": [],
        "select": [],
        "binary_sensor": ["activation"],
        "button": [],
        "switch": [],
    },
    # Valves
    3150: {  # VA4201WZ, VA4200WZ, VA4220WZ, VA4220WF, VA4221WZ, VA4221WF
        "sensor": [ATTR_RSSI],
        "number": [],
        "select": [],
        "binary_sensor": ["activation"],
        "button": [],
        "switch": [],
    },
    3151: {  # VA4200ZB
        "sensor": [ATTR_RSSI],
        "number": [],
        "select": [],
        "binary_sensor": ["activation"],
        "button": [],
        "switch": [],
    },
    3153: {  # VA4220ZB 2e gen
        "sensor": [
            ATTR_RSSI,
            "daily_kwh_count",
            "hourly_kwh_count",
            "monthly_kwh_count",
            "total_kwh_count",
        ],
        "number": [],
        "select": [
            "flowmeter_timer",
            "flow_duration",
            "flow_meter",
            "power_supply",
        ],
        "binary_sensor": [
            "activation",
            "battery_status",
            "valve_temp_alert",
            "water_leak_status",
        ],
        "button": [],
        "switch": [
            "temperature_alert",
            "valve_alert",
        ],
    },
    3155: {  # ACT4221WF-M, ACT4220WF-M
        "sensor": [
            ATTR_RSSI,
            "daily_kwh_count",
            "hourly_kwh_count",
            "monthly_kwh_count",
            "total_kwh_count",
        ],
        "number": [],
        "select": [
            "flowmeter_timer",
            "flow_duration",
            "flow_meter",
            "power_supply",
        ],
        "binary_sensor": [
            "activation",
            "battery_status",
            "valve_temp_alert",
            "water_leak_status",
        ],
        "button": [],
        "switch": [
            "temperature_alert",
            "valve_alert",
        ],
    },
    31532: {  # ACT4221ZB-M, ACT4220ZB-M
        "sensor": [
            ATTR_RSSI,
            "daily_kwh_count",
            "hourly_kwh_count",
            "monthly_kwh_count",
            "total_kwh_count",
        ],
        "number": [],
        "select": [
            "flowmeter_timer",
            "flow_duration",
            "flow_meter",
            "power_supply",
        ],
        "binary_sensor": [
            "activation",
            "battery_status",
            "valve_temp_alert",
            "water_leak_status",
        ],
        "button": [],
        "switch": [
            "temperature_alert",
            "valve_alert",
        ],
    },
    # sensors
    130: {  # GT130
        "sensor": [],
        "number": [],
        "select": ["occupancy_mode"],
        "binary_sensor": [
            "activation",
            "gateway_status",
        ],
        "button": [],
        "switch": [],
    },
    4210: {  # WL4210, WL4210S connected to GT130
        "sensor": [
            ATTR_RSSI,
            "current_temperature",
        ],
        "number": [],
        "select": ["batt_type"],
        "binary_sensor": [
            "activation",
            "battery_status",
            "leak_status",
        ],
        "button": [],
        "switch": [
            "batt_alert",
            "leak_alert",
            "temp_alert",
        ],
    },
    5050: {  # WL4200, WL4210 and WL4200S,
        "sensor": [
            ATTR_RSSI,
            "current_temperature",
        ],
        "number": [],
        "select": ["batt_type"],
        "binary_sensor": [
            "activation",
            "battery_status",
            "leak_status",
        ],
        "button": [],
        "switch": [
            "action_close",
            "batt_alert",
            "leak_alert",
            "temp_alert",
        ],
    },
    5051: {  # WL4200, WL4200C and WL4200S
        "sensor": [
            ATTR_RSSI,
            "current_temperature",
        ],
        "number": [],
        "select": ["batt_type"],
        "binary_sensor": [
            "activation",
            "battery_status",
            "leak_status",
        ],
        "button": [],
        "switch": [
            "batt_alert",
            "leak_alert",
            "temp_alert",
        ],
    },
    5052: {  # WL4200C, perimeter cable water leak detector connected to Sedna
        "sensor": [
            ATTR_RSSI,
            "current_temperature",
        ],
        "number": [],
        "select": ["batt_type"],
        "binary_sensor": [
            "activation",
            "battery_status",
            "leak_status",
        ],
        "button": [],
        "switch": [
            "action_close",
            "batt_alert",
            "leak_alert",
            "temp_alert",
        ],
    },
    5053: {  # WL4200C, perimeter cable water leak detector connected to GT130
        "sensor": [
            ATTR_RSSI,
            "current_temperature",
        ],
        "number": [],
        "select": ["batt_type"],
        "binary_sensor": [
            "activation",
            "battery_status",
            "leak_status",
        ],
        "button": [],
        "switch": [
            "batt_alert",
            "leak_alert",
            "temp_alert",
        ],
    },
    5055: {  # LM4110-LTE
        "sensor": [ATTR_RSSI],
        "number": ["gauge_angle"],
        "select": ["gauge_type"],
        "binary_sensor": [
            "activation",
            "battery_status",
            "gauge_error",
            "level_status",
        ],
        "button": [],
        "switch": [],
    },
    5056: {  # LM4110-ZB
        "sensor": [
            ATTR_RSSI,
            "battery_level",
            "battery_voltage",
            "gauge_angle",
        ],
        "number": ["gauge_angle"],
        "select": [
            "gauge_type",
            "low_fuel_alert",
            "tank_height",
            "tank_type",
        ],
        "binary_sensor": [
            "activation",
            "battery_status",
            "gauge_error",
            "level_status",
            "refuel_status",
        ],
        "button": [],
        "switch": [
            "batt_alert",
            "fuel_alert",
            "refuel_alert",
        ],
    },
    42102: {  # WL4210, WL4210S connected to sedna valve
        "sensor": [
            ATTR_RSSI,
            "current_temperature",
        ],
        "number": [],
        "select": ["batt_type"],
        "binary_sensor": [
            "activation",
            "battery_status",
            "leak_status",
        ],
        "button": [],
        "switch": [
            "action_close",
            "batt_alert",
            "leak_alert",
            "temp_alert",
        ],
    },
}

# Managed device attributes by alphabetical order
EXPOSED_ATTRIBUTES = [
    "action_close",
    "activation",
    "alert_temp",
    "aux_cycle_length",
    "backlight",
    "batt_alert",
    "batt_type",
    "battery_level",
    "battery_status",
    "battery_voltage",
    "brightness",
    "cool_setpoint_away",
    "current_temperature",
    "cycle_length",
    "daily_flow_count",
    "daily_kwh_count",
    "early_start",
    "fan_filter_remain",
    "floor_setpoint_max",
    "floor_setpoint_min",
    "flow_duration",
    "flow_meter",
    "flowmeter_timer",
    "fuel_alert",
    "gateway_status",
    "gauge_angle",
    "gauge_error",
    "gauge_type",
    "hc_second_display",
    "heater_temp_min",
    "hourly_flow_count",
    "hourly_kwh_count",
    "intensity_min",
    "is_heating",
    "keypad",
    "keypad_status",
    "language",
    "leak_alert",
    "leak_status",
    "led_off_color",
    "led_off_intensity",
    "led_on_color",
    "led_on_intensity",
    "level_status",
    "light_timer",
    "location",
    "low_fuel_alert",
    "low_temp_status",
    "lv_cycle_length",
    "max_cool_temp",
    "max_temp",
    "min_cool_temp",
    "min_temp",
    "monthly_flow_count",
    "monthly_kwh_count",
    "occupancy_mode",
    "phase_control",
    "pi_heating_demand",
    "power_supply",
    "power_timer",
    "pro_aux_cycle_length",
    "refuel_alert",
    "refuel_status",
    "room_humidity",
    "rssi",
    "second_display",
    "sensor_mode",
    "setpoint_away",
    "switch_keypad",
    "tank_height",
    "tank_size",
    "tank_type",
    "temperature_alert",
    "temp_alert",
    "temp_format",
    "time_format",
    "timer",
    "timer2",
    "total_flow_count",
    "total_kwh_count",
    "valve_alert",
    "valve_temp_alert",
    "wattage",
    "water_leak_status",
    "water_remaining_time",
    "wifi_aux_cycle_length",
    "wifi_cycle",
    "wifi_keypad",
    # Constants
    "is_HC",
    "is_HP",
    "is_WHP",
    "is_wifi",
    "is_wifi_floor",
    "is_zb_valve",
    "is_zb_mesh_valve",
    "sku",
    # ... etc.
]
