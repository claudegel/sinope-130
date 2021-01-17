"""Constants for neviweb130 component."""

DOMAIN = "neviweb130"
CONF_NETWORK = 'network'

ATTR_SIGNATURE = "signature"
ATTR_POWER_MODE = "powerMode"
ATTR_ONOFF = "onOff"
ATTR_INTENSITY = "intensity"
ATTR_WATTAGE = "loadConnected"
ATTR_WATTAGE_INSTANT = "wattageInstant"
ATTR_WATTAGE_OVERRIDE = "wattageOverride"
ATTR_SETPOINT_MODE = "setpointMode"
ATTR_ROOM_SETPOINT = "roomSetpoint"
ATTR_ROOM_TEMPERATURE = "roomTemperature"
ATTR_OUTPUT_PERCENT_DISPLAY = "outputPercentDisplay"
ATTR_ROOM_SETPOINT_MIN = "roomSetpointMin"
ATTR_ROOM_SETPOINT_MAX = "roomSetpointMax"
ATTR_GFCI_STATUS = "gfciStatus"
ATTR_WATER_LEAK_STATUS = "waterLeakStatus"
ATTR_BATTERY_VOLTAGE = "batteryVoltage"
ATTR_BATTERY_STATUS = "batteryStatus"
ATTR_LEVEL_STATUS = "tankLevelPercent"
ATTR_FLOOR_MODE = "airFloorMode"
ATTR_FLOOR_OUTPUT2 = "loadWattOutput2"
ATTR_FLOOR_AUX = "auxHeatConfig"
ATTR_FLOOR_MAX = "floorMaxAirTemperature"
ATTR_KEYPAD = "lockKeypad"
ATTR_OCCUPANCY = "occupancyMode"
ATTR_WIFI_FLOOR_OUTPUT1 = "loadWattOutput1" #status on/off, value=xx
ATTR_LIGHT_WATTAGE = "loadWattOutput1" #status on/off, value=xx
ATTR_WIFI_WATTAGE = "loadWatt"
ATTR_WIFI = "wifiRssi"
ATTR_WIFI_DISPLAY2 = "config2ndDisplay"
ATTR_WIFI_KEYPAD = "keyboardLock"
ATTR_TIMER = "powerTimer"
ATTR_DRSTATUS = "drStatus"
ATTR_BACKLIGHT = "backlightAdaptive"
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
ATTR_ROOM_TEMP_ALARM = "roomTemperatureAlarmStatus"
ATTR_VALVE_CLOSURE = "valveClosureSource" #source
ATTR_LEAK_ALERT = "alertWaterLeak"
ATTR_BATT_ALERT = "alertLowBatt"
ATTR_TEMP_ALERT = "alertLowTemp"
ATTR_CONF_CLOSURE = "cfgValveClosure"
ATTR_MOTOR_TARGET = "motorTargetPosition"

MODE_AUTO = "auto"
MODE_AUTO_BYPASS = "autoBypass"
MODE_MANUAL = "manual"
MODE_AWAY = "away"
MODE_OFF = "off"

STATE_WATER_LEAK = "water"
STATE_VALVE_STATUS = "open"
STATE_KEYPAD_STATUS = "unlocked"

SERVICE_SET_LED_INDICATOR = "set_led_indicator"
SERVICE_SET_KEYPAD_LOCK = "set_keypad_lock"
SERVICE_SET_TIMER = "set_timer"
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
