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
model 336 = thermostat TH1133WF 3000W (Wi-Fi lite)
model 348 = thermostat TH1133CR Sinopé Evo 3000W (Wi-Fi lite)
model 336 = thermostat TH1134WF 3000W (Wi-Fi lite)
model 348 = thermostat TH1134CR Sinopé Evo 3000W (Wi-Fi lite)
model 343 = thermostat THEWF01 (Wi-Fi lite)
model 350 = thermostat TH1143WF 3000W (Wi-Fi) two wires connection, color screen
model 350 = thermostat TH1144WF 4000W (Wi-Fi) two wires connection, color screen
model 738 = thermostat TH1300WF 3600W, TH1325WF, TH1310WF, SRM40, True Comfort (sku: PS120_240WF)
    (wifi floor), no energy stat for True Comfort
model 739 = thermostat TH1400WF low voltage (Wi-Fi)
model 742 = thermostat TH1500WF double pole thermostat (Wi-Fi)
model 6727 = thermostat TH6500WF heat/cool (Wi-Fi)
model 6727 = thermostat TH6510WF heat/cool (Wi-Fi)
model 6730 = thermostat TH6250WF heat/cool (Wi-Fi)
model 6731 = thermostat TH6250WF-PRO keat/cool (Wi-Fi)
model xxxx = thermostat THE-WF (stripped Wi-Fi)

Support for Flextherm Wi-Fi thermostat
model 738 = Thermostat Flextherm concerto connect FLP55 (wifi floor),
    (sku: FLP55), no energy stats

Support for heat pump interfaces
model 6810 = HP6000ZB-GE for Ouellet heat pump with Gree connector
model 6811 = HP6000ZB-MA for Ouellet Convectair heat pump with Midea connector
model 6812 = HP6000ZB-HS for Hisense, Haxxair and Zephyr heat pump

Support for Wi-Fi heat pump interfaces
model 6813 = HP6000WF-MA for Ouellet Convectair heat pump with Midea connector
model 6814 = HP6000WF-XX for Hisense, Haxxair and Zephyr heat pump
model xxxx = HP6000WF-XX for Ouellet heat pump with Gree connector

For more details about this platform, please refer to the documentation at
https://www.sinopetech.com/en/support/#api
"""

from __future__ import annotations

import asyncio
import logging
import time
from datetime import date, datetime, timezone
from threading import Lock
from typing import Any, Mapping, override

from homeassistant.components.climate import ClimateEntity, ClimateEntityFeature
from homeassistant.components.climate.const import (
    ATTR_TARGET_TEMP_HIGH,
    ATTR_TARGET_TEMP_LOW,
    PRESET_AWAY,
    PRESET_BOOST,
    PRESET_HOME,
    PRESET_NONE,
    HVACAction,
    HVACMode,
)
from homeassistant.components.persistent_notification import DOMAIN as PN_DOMAIN
from homeassistant.components.recorder.models import StatisticMeanType
from homeassistant.components.sensor import SensorDeviceClass, SensorStateClass
from homeassistant.config_entries import ConfigEntry
from homeassistant.const import ATTR_ENTITY_ID, ATTR_TEMPERATURE, UnitOfTemperature
from homeassistant.core import HomeAssistant, ServiceCall
from homeassistant.exceptions import HomeAssistantError, ServiceValidationError
from homeassistant.helpers import device_registry as dr
from homeassistant.helpers.device_registry import DeviceInfo
from homeassistant.helpers.entity_platform import AddEntitiesCallback
from homeassistant.helpers.update_coordinator import CoordinatorEntity
import homeassistant.util.dt as dt_util

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
    ATTR_INTERLOCK_HC_MODE,
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
    ATTR_SYSTEM_MODE_AVAIL,
    ATTR_TEMP,
    ATTR_TEMP_OFFSET_HEAT,
    ATTR_TIME,
    ATTR_TIME_FORMAT,
    ATTR_TYPE,
    ATTR_VALUE,
    ATTR_WATTAGE,
    ATTR_WIFI,
    ATTR_WIFI_KEYPAD,
    ATTR_WIFI_WATTAGE,
    DOMAIN,
    EXPOSED_ATTRIBUTES,
    MODE_AUTO_BYPASS,
    MODE_EM_HEAT,
    MODE_MANUAL,
    RUNTIME_PREFIXES,
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
    TH6_MODES_VALUES,
    VERSION,
)
from .devices import save_devices
from .helpers import (
    async_notify_once_or_update,
    async_notify_throttled,
    async_notify_critical,
    generate_runtime_count_attributes,
    init_runtime_attributes,
    NeviwebEntityHelper,
    NamingHelper,
    update_runtime_stats,
    runtime_attributes_dict,
)
from .schema import (
    AUX_HEATING,
    FAN_SPEED,
    FULL_SWING,
    FULL_SWING_OFF,
    HA_TO_NEVIWEB_FAN_SPEED,
    HA_TO_NEVIWEB_FAN_SPEED_5,
    HA_TO_NEVIWEB_MODE,
    HA_TO_NEVIWEB_PERIOD,
    HP_FAN_SPEED,
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
    WIFI_FAN_SPEED,
)

_LOGGER = logging.getLogger(__name__)

# Add runtime attribute
for prefix in RUNTIME_PREFIXES:
    runtime_attrs = generate_runtime_count_attributes(TH6_MODES_VALUES, prefix)
    for attr in runtime_attrs:
        if attr not in EXPOSED_ATTRIBUTES:
            EXPOSED_ATTRIBUTES.append(attr)


NEVIWEB_TO_HA_MODE = {v: k for k, v in HA_TO_NEVIWEB_MODE.items()}

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

SNOOZE_TIME = 1200

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
    ATTR_DRSETPOINT,
    ATTR_DRSTATUS,
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
    HVACMode.HEAT,
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

SUPPORTED_HVAC_HC_MODES: list[HVACMode] = [
    HVACMode.AUTO,
    HVACMode.COOL,
    HVACMode.HEAT,
    HVACMode.OFF,
    MODE_EM_HEAT,
]

SUPPORTED_HVAC_HP_MODES: list[HVACMode] = [
    HVACMode.COOL,
    HVACMode.DRY,
    HVACMode.FAN_ONLY,
    HVACMode.HEAT,
    HVACMode.OFF,
]

SUPPORTED_HVAC_WHP_MODES: list[HVACMode] = [
    HVACMode.HEAT_COOL,
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

PRESET_h_c_MODES = [
    PRESET_HOME,
    PRESET_AWAY,
]

DEVICE_MODEL_LOW = [7372]
DEVICE_MODEL_LOW_WIFI = [739]
DEVICE_MODEL_FLOOR = [737]
DEVICE_MODEL_WIFI_FLOOR = [738]
DEVICE_MODEL_WIFI = [1510, 742]
DEVICE_MODEL_WIFI_LITE = [336, 343, 348]
DEVICE_MODEL_COLOR_WIFI = [350]
DEVICE_MODEL_HEAT = [1123, 1124]
DEVICE_MODEL_DOUBLE = [7373]
DEVICE_MODEL_HEAT_G2 = [300]
DEVICE_MODEL_HC = [1512]
DEVICE_MODEL_HEAT_PUMP = [6810, 6811, 6812]
DEVICE_MODEL_WIFI_HEAT_PUMP = [6813, 6814]
DEVICE_MODEL_HEAT_COOL = [6727, 6730, 6731]
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
    + DEVICE_MODEL_WIFI_HEAT_PUMP
)


async def async_setup_entry(
    hass: HomeAssistant,
    entry: ConfigEntry,
    async_add_entities: AddEntitiesCallback,
    discovery_info=None,
) -> None:
    """Set up the neviweb130 thermostats."""
    data = hass.data[DOMAIN][entry.entry_id]

    data["conf_dir"] = hass.data[DOMAIN]["conf_dir"]
    data["device_dict"] = hass.data[DOMAIN]["device_dict"]
    config_prefix = data["prefix"]

    #    _LOGGER.debug("data climate = %s", hass.data[DOMAIN][entry.entry_id])
    #    _LOGGER.debug("Network data = %s", data['neviweb130_client'])

    if "neviweb130_client" not in data:
        _LOGGER.error("Neviweb130 client initialization failed.")
        return

    coordinator = hass.data[DOMAIN][entry.entry_id]["coordinator"]

    device_registry = dr.async_get(hass)

    platform = __name__.split(".")[-1] # "climate"
    naming = NamingHelper(domain=DOMAIN, prefix=config_prefix)

    entities: list[Neviweb130Thermostat] = []
    for index, gateway_data in enumerate([
        data["neviweb130_client"].gateway_data,
        data["neviweb130_client"].gateway_data2,
        data["neviweb130_client"].gateway_data3,
    ], start=1):

#        default_name = build_default_name(
#            domain=DOMAIN,
#            platform="climate",
#            prefix=config_prefix,  # "default" or "other"
#            index=index,
#        )
        default_name = naming.default_name(platform, index)
        if gateway_data is not None and gateway_data != "_":
            for device_info in gateway_data:
                if "signature" in device_info and "model" in device_info["signature"]:
                    model = device_info["signature"]["model"]
                    if model in IMPLEMENTED_DEVICE_MODEL:
                        device_name = naming.device_name(platform, index, device_info)
                        device_sku = device_info["sku"]
                        location_id = device_info["location$id"]
                        device_firmware = "{major}.{middle}.{minor}".format(
                            **device_info["signature"]["softVersion"]
                        )
                        # Ensure the device is registered in the device registry
                        device_entry = device_registry.async_get_or_create(
                            config_entry_id=entry.entry_id,
                            identifiers={(DOMAIN, str(device_info["id"]))},
                            name=device_name,
                            manufacturer="claudegel",
                            model=device_info["signature"]["model"],
                            sw_version=device_firmware,
                        )

                        if device_info["signature"]["model"] in DEVICE_MODEL_HEAT:
                            device = Neviweb130Thermostat(
                                data,
                                device_info,
                                device_name,
                                device_sku,
                                device_firmware,
                                location_id,
                                coordinator,
                                entry,
                            )
                        elif device_info["signature"]["model"] in DEVICE_MODEL_HEAT_G2:
                            device = Neviweb130G2Thermostat(
                                data,
                                device_info,
                                device_name,
                                device_sku,
                                device_firmware,
                                location_id,
                                coordinator,
                                entry,
                            )
                        elif device_info["signature"]["model"] in DEVICE_MODEL_FLOOR:
                            device = Neviweb130FloorThermostat(
                                data,
                                device_info,
                                device_name,
                                device_sku,
                                device_firmware,
                                location_id,
                                coordinator,
                                entry,
                            )
                        elif device_info["signature"]["model"] in DEVICE_MODEL_LOW:
                            device = Neviweb130LowThermostat(
                                data,
                                device_info,
                                device_name,
                                device_sku,
                                device_firmware,
                                location_id,
                                coordinator,
                                entry,
                            )
                        elif device_info["signature"]["model"] in DEVICE_MODEL_DOUBLE:
                            device = Neviweb130DoubleThermostat(
                                data,
                                device_info,
                                device_name,
                                device_sku,
                                device_firmware,
                                location_id,
                                coordinator,
                                entry,
                            )
                        elif device_info["signature"]["model"] in DEVICE_MODEL_WIFI:
                            _LOGGER.debug("Device id = %s", device_entry.id)
                            device = Neviweb130WifiThermostat(
                                data,
                                device_info,
                                device_name,
                                device_sku,
                                device_firmware,
                                location_id,
                                coordinator,
                                entry,
                            )
                        elif device_info["signature"]["model"] in DEVICE_MODEL_WIFI_LITE:
                            device = Neviweb130WifiLiteThermostat(
                                data,
                                device_info,
                                device_name,
                                device_sku,
                                device_firmware,
                                location_id,
                                coordinator,
                                entry,
                            )
                        elif device_info["signature"]["model"] in DEVICE_MODEL_COLOR_WIFI:
                            device = Neviweb130ColorWifiThermostat(
                                data,
                                device_info,
                                device_name,
                                device_sku,
                                device_firmware,
                                location_id,
                                coordinator,
                                entry,
                            )
                        elif device_info["signature"]["model"] in DEVICE_MODEL_LOW_WIFI:
                            device = Neviweb130LowWifiThermostat(
                                data,
                                device_info,
                                device_name,
                                device_sku,
                                device_firmware,
                                location_id,
                                coordinator,
                                entry,
                            )
                        elif device_info["signature"]["model"] in DEVICE_MODEL_WIFI_FLOOR:
                            device = Neviweb130WifiFloorThermostat(
                                data,
                                device_info,
                                device_name,
                                device_sku,
                                device_firmware,
                                location_id,
                                coordinator,
                                entry,
                            )
                        elif device_info["signature"]["model"] in DEVICE_MODEL_HC:
                            device = Neviweb130HcThermostat(
                                data,
                                device_info,
                                device_name,
                                device_sku,
                                device_firmware,
                                location_id,
                                coordinator,
                                entry,
                            )
                        elif device_info["signature"]["model"] in DEVICE_MODEL_HEAT_PUMP:
                            device = Neviweb130HPThermostat(
                                data,
                                device_info,
                                device_name,
                                device_sku,
                                device_firmware,
                                location_id,
                                coordinator,
                                entry,
                            )
                        elif device_info["signature"]["model"] in DEVICE_MODEL_WIFI_HEAT_PUMP:
                            device = Neviweb130WifiHPThermostat(
                                data,
                                device_info,
                                device_name,
                                device_sku,
                                device_firmware,
                                location_id,
                                coordinator,
                                entry,
                            )
                        else:  # DEVICE_MODEL_HEAT_COOL
                            device = Neviweb130HeatCoolThermostat(
                                data,
                                device_info,
                                device_name,
                                device_sku,
                                device_firmware,
                                location_id,
                                coordinator,
                                entry,
                            )

                        _LOGGER.warning("Device registered = %s", device_info["id"])
                        entities.append(device)
                        coordinator.register_device(device)

    async_add_entities(entities, True)
    hass.async_create_task(coordinator.async_request_refresh())

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

    async def set_second_display_service(service: ServiceCall) -> None:
        """Set to outside or setpoint temperature display for Wi-Fi thermostats."""
        thermostat = get_thermostat(service)
        value = {"id": thermostat.unique_id, "display": service.data[ATTR_DISPLAY2]}
        await thermostat.async_set_second_display(value)
        thermostat.async_schedule_update_ha_state(True)
        hass.async_create_task(coordinator.async_request_refresh())

    async def set_backlight_service(service: ServiceCall) -> None:
        """Set backlight always on or auto."""
        thermostat = get_thermostat(service)
        value = {
            "id": thermostat.unique_id,
            "type": service.data[ATTR_TYPE],
            "level": service.data[ATTR_BACKLIGHT],
        }
        await thermostat.async_set_backlight(value)
        thermostat.async_schedule_update_ha_state(True)
        hass.async_create_task(coordinator.async_request_refresh())

    async def set_climate_keypad_lock_service(service: ServiceCall) -> None:
        """Lock/unlock keypad device."""
        thermostat = get_thermostat(service)
        value = {"id": thermostat.unique_id, "lock": service.data[ATTR_KEYPAD]}
        await thermostat.async_set_keypad_lock(value)
        thermostat.async_schedule_update_ha_state(True)
        hass.async_create_task(coordinator.async_request_refresh())

    async def set_time_format_service(service: ServiceCall) -> None:
        """Set time format 12h or 24h."""
        thermostat = get_thermostat(service)

        # List of devices class that don't support this service
        unsupported_classes = (
            Neviweb130WifiLiteThermostat,
            Neviweb130HPThermostat,
            Neviweb130WifiHPThermostat,
        )

        if isinstance(thermostat, unsupported_classes):
            raise ServiceValidationError(f"Entity {thermostat.entity_id} do not support time format")

        value = {"id": thermostat.unique_id, ATTR_TIME: service.data[ATTR_TIME_FORMAT]}
        await thermostat.async_set_time_format(value)
        thermostat.async_schedule_update_ha_state(True)
        hass.async_create_task(coordinator.async_request_refresh())

    async def set_temperature_format_service(service: ServiceCall) -> None:
        """Set temperature format, celsius or fahrenheit."""
        thermostat = get_thermostat(service)
        value = {"id": thermostat.unique_id, "temp": service.data[ATTR_TEMP]}
        await thermostat.async_set_temperature_format(value)
        thermostat.async_schedule_update_ha_state(True)
        hass.async_create_task(coordinator.async_request_refresh())

    async def set_setpoint_max_service(service: ServiceCall) -> None:
        """Set maximum setpoint for device."""
        thermostat = get_thermostat(service)
        value = {"id": thermostat.unique_id, "temp": service.data[ATTR_ROOM_SETPOINT_MAX]}
        await thermostat.async_set_setpoint_max(value)
        thermostat.async_schedule_update_ha_state(True)
        hass.async_create_task(coordinator.async_request_refresh())

    async def set_setpoint_min_service(service: ServiceCall) -> None:
        """Set minimum setpoint for device."""
        thermostat = get_thermostat(service)
        value = {"id": thermostat.unique_id, "temp": service.data[ATTR_ROOM_SETPOINT_MIN]}
        await thermostat.async_set_setpoint_min(value)
        thermostat.async_schedule_update_ha_state(True)
        hass.async_create_task(coordinator.async_request_refresh())

    async def set_floor_air_limit_service(service: ServiceCall) -> None:
        """Set minimum setpoint for device."""
        thermostat = get_thermostat(service)
        value = {"id": thermostat.unique_id, "temp": service.data[ATTR_FLOOR_AIR_LIMIT]}
        await thermostat.async_set_floor_air_limit(value)
        thermostat.async_schedule_update_ha_state(True)
        hass.async_create_task(coordinator.async_request_refresh())

    async def set_early_start_service(service: ServiceCall) -> None:
        """Set early heating on/off for Wi-Fi thermostat."""
        thermostat = get_thermostat(service)
        value = {"id": thermostat.unique_id, "start": service.data[ATTR_EARLY_START]}
        await thermostat.async_set_early_start(value)
        thermostat.async_schedule_update_ha_state(True)
        hass.async_create_task(coordinator.async_request_refresh())

    async def set_air_floor_mode_service(service: ServiceCall) -> None:
        """Switch between ambient or floor temperature sensor."""
        thermostat = get_thermostat(service)
        value = {"id": thermostat.unique_id, "mode": service.data[ATTR_FLOOR_MODE]}
        await thermostat.async_set_air_floor_mode(value)
        thermostat.async_schedule_update_ha_state(True)
        hass.async_create_task(coordinator.async_request_refresh())

    async def set_hvac_dr_options_service(service: ServiceCall) -> None:
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
        await thermostat.async_set_hvac_dr_options(value)
        thermostat.async_schedule_update_ha_state(True)
        hass.async_create_task(coordinator.async_request_refresh())

    async def set_hvac_dr_setpoint_service(service: ServiceCall) -> None:
        """Set options for hvac dr setpoint in Eco Sinope."""
        thermostat = get_thermostat(service)
        value = {
            "id": thermostat.unique_id,
            "status": service.data[ATTR_STATUS],
            "val": service.data[ATTR_VALUE],
        }
        await thermostat.async_set_hvac_dr_setpoint(value)
        thermostat.async_schedule_update_ha_state(True)
        hass.async_create_task(coordinator.async_request_refresh())

    async def set_auxiliary_load_service(service: ServiceCall) -> None:
        """Set options for auxiliary heating."""
        thermostat = get_thermostat(service)
        value = {
            "id": thermostat.unique_id,
            "status": service.data[ATTR_STATUS],
            "val": service.data[ATTR_VALUE],
        }
        await thermostat.async_set_auxiliary_load(value)
        thermostat.async_schedule_update_ha_state(True)
        hass.async_create_task(coordinator.async_request_refresh())

    async def set_aux_cycle_output_service(service: ServiceCall) -> None:
        """Set options for auxiliary cycle length for low voltage thermostats."""
        thermostat = get_thermostat(service)
        val = service.data.get(ATTR_VALUE)
        if val is None:
            raise ServiceValidationError(f"Missing required parameter: {ATTR_VALUE}")
        value = {"id": thermostat.unique_id, "val": val}
        await thermostat.async_set_aux_cycle_output(value)
        thermostat.async_schedule_update_ha_state(True)
        hass.async_create_task(coordinator.async_request_refresh())

    async def set_cycle_output_service(service: ServiceCall) -> None:
        """Set options for main cycle length for low voltage thermostats."""
        thermostat = get_thermostat(service)
        value = {"id": thermostat.unique_id, "val": service.data[ATTR_VALUE]}
        await thermostat.async_set_cycle_output(value)
        thermostat.async_schedule_update_ha_state(True)
        hass.async_create_task(coordinator.async_request_refresh())

    async def set_pump_protection_service(service: ServiceCall) -> None:
        """Set status of pump protection for low voltage thermostats."""
        thermostat = get_thermostat(service)
        value = {
            "id": thermostat.unique_id,
            "status": service.data[ATTR_STATUS],
        }
        await thermostat.async_set_pump_protection(value)
        thermostat.async_schedule_update_ha_state(True)
        hass.async_create_task(coordinator.async_request_refresh())

    async def set_cool_setpoint_max_service(service: ServiceCall) -> None:
        """Set maximum cooling setpoint for device."""
        thermostat = get_thermostat(service)
        value = {
            "id": thermostat.unique_id,
            "temp": service.data[ATTR_COOL_SETPOINT_MAX],
        }
        await thermostat.async_set_cool_setpoint_max(value)
        thermostat.async_schedule_update_ha_state(True)
        hass.async_create_task(coordinator.async_request_refresh())

    async def set_cool_setpoint_min_service(service: ServiceCall) -> None:
        """Set minimum cooling setpoint for device."""
        thermostat = get_thermostat(service)
        value = {
            "id": thermostat.unique_id,
            "temp": service.data[ATTR_COOL_SETPOINT_MIN],
        }
        await thermostat.async_set_cool_setpoint_min(value)
        thermostat.async_schedule_update_ha_state(True)
        hass.async_create_task(coordinator.async_request_refresh())

    async def set_room_setpoint_away_service(service: ServiceCall) -> None:
        """Set away heating setpoint."""
        thermostat = get_thermostat(service)
        value = {
            "id": thermostat.unique_id,
            "temp": service.data[ATTR_ROOM_SETPOINT_AWAY],
        }
        await thermostat.async_set_room_setpoint_away(value)
        thermostat.async_schedule_update_ha_state(True)
        hass.async_create_task(coordinator.async_request_refresh())

    async def set_cool_setpoint_away_service(service: ServiceCall) -> None:
        """Set away cooling setpoint."""
        thermostat = get_thermostat(service)
        if not isinstance(thermostat, Neviweb130HeatCoolThermostat):
            raise HomeAssistantError(f"Entity {thermostat.entity_id} is not a Neviweb130HeatCoolThermostat")
        value = {
            "id": thermostat.unique_id,
            "temp": service.data[ATTR_COOL_SETPOINT_AWAY],
        }
        await thermostat.async_set_cool_setpoint_away(value)
        thermostat.async_schedule_update_ha_state(True)
        hass.async_create_task(coordinator.async_request_refresh())

    async def set_floor_limit_high_service(service: ServiceCall) -> None:
        """Set maximum floor heating limit for floor device."""
        thermostat = get_thermostat(service)
        value = {
            "id": thermostat.unique_id,
            "level": service.data[ATTR_FLOOR_MAX],
            "limit": "high",
        }
        await thermostat.async_set_floor_limit(value)
        thermostat.async_schedule_update_ha_state(True)
        hass.async_create_task(coordinator.async_request_refresh())

    async def set_floor_limit_low_service(service: ServiceCall) -> None:
        """Set minimum floor heating limit for floor device."""
        thermostat = get_thermostat(service)
        value = {
            "id": thermostat.unique_id,
            "level": service.data[ATTR_FLOOR_MIN],
            "limit": "low",
        }
        await thermostat.async_set_floor_limit(value)
        thermostat.async_schedule_update_ha_state(True)
        hass.async_create_task(coordinator.async_request_refresh())

    async def set_activation_service(service: ServiceCall) -> None:
        """Activate or deactivate Neviweb polling for missing device."""
        thermostat = get_thermostat(service)
        value = {"id": thermostat.unique_id, "active": service.data[ATTR_ACTIVE]}
        await thermostat.async_set_activation(value)
        thermostat.async_schedule_update_ha_state(True)
        hass.async_create_task(coordinator.async_request_refresh())

    async def set_sensor_type_service(service: ServiceCall) -> None:
        """Set floor sensor type."""
        thermostat = get_thermostat(service)
        value = {"id": thermostat.unique_id, "type": service.data[ATTR_FLOOR_SENSOR]}
        await thermostat.async_set_sensor_type(value)
        thermostat.async_schedule_update_ha_state(True)
        hass.async_create_task(coordinator.async_request_refresh())

    async def set_em_heat_service(service: ServiceCall) -> None:
        """Set emergency heat on/off for thermostats."""
        thermostat = get_thermostat(service)
        if service.data[ATTR_VALUE] == "on":
            await thermostat.async_turn_em_heat_on()
        else:
            await thermostat.async_turn_em_heat_off()
        thermostat.async_schedule_update_ha_state(True)
        hass.async_create_task(coordinator.async_request_refresh())

    async def set_heat_pump_operation_limit_service(service: ServiceCall) -> None:
        """Set minimum temperature for heat pump device operation."""
        thermostat = get_thermostat(service)
        value = {
            "id": thermostat.unique_id,
            "temp": service.data[ATTR_BALANCE_PT],
        }
        await thermostat.async_set_heat_pump_operation_limit(value)
        thermostat.async_schedule_update_ha_state(True)
        hass.async_create_task(coordinator.async_request_refresh())

    async def set_heat_lockout_temperature_service(service: ServiceCall) -> None:
        """Set maximum outside temperature limit to allow heating device operation."""
        # Work differently for G2 thermostats
        thermostat = get_thermostat(service)
        temp = ( service.data.get(ATTR_HEAT_LOCK_TEMP) or service.data.get(ATTR_HEAT_LOCKOUT_TEMP) )
        value = {"id": thermostat.unique_id, "temp": temp}
        await thermostat.async_set_heat_lockout_temperature(value)
        thermostat.async_schedule_update_ha_state(True)
        hass.async_create_task(coordinator.async_request_refresh())

    async def set_cool_lockout_temperature_service(service: ServiceCall) -> None:
        """Set minimum outside temperature limit to allow cooling device operation."""
        thermostat = get_thermostat(service)
        value = {"id": thermostat.unique_id, "temp": service.data[ATTR_COOL_LOCK_TEMP]}
        await thermostat.async_set_cool_lockout_temperature(value)
        thermostat.async_schedule_update_ha_state(True)
        hass.async_create_task(coordinator.async_request_refresh())

    async def set_display_config_service(service: ServiceCall) -> None:
        """Set display on/off for heat pump."""
        thermostat = get_thermostat(service)
        value = {
            "id": thermostat.unique_id,
            "display": service.data[ATTR_DISPLAY_CONF],
        }
        await thermostat.async_set_display_config(value)
        thermostat.async_schedule_update_ha_state(True)
        hass.async_create_task(coordinator.async_request_refresh())

    async def set_sound_config_service(service: ServiceCall) -> None:
        """Set sound on/off for heat pump."""
        thermostat = get_thermostat(service)
        value = {
            "id": thermostat.unique_id,
            "sound": service.data[ATTR_SOUND_CONF],
        }
        await thermostat.async_set_sound_config(value)
        thermostat.async_schedule_update_ha_state(True)
        hass.async_create_task(coordinator.async_request_refresh())

    async def set_hc_second_display_service(service: ServiceCall) -> None:
        """Set second display for TH1134ZB-HC thermostat."""
        thermostat = get_thermostat(service)
        value = {
            "id": thermostat.unique_id,
            "display": service.data[ATTR_DISPLAY2],
        }
        await thermostat.async_set_hc_second_display(value)
        thermostat.async_schedule_update_ha_state(True)
        hass.async_create_task(coordinator.async_request_refresh())

    async def set_language_service(service: ServiceCall) -> None:
        """Set display language for TH1134ZB-HC thermostat."""
        thermostat = get_thermostat(service)
        value = {
            "id": thermostat.unique_id,
            "lang": service.data[ATTR_LANGUAGE],
        }
        await thermostat.async_set_language(value)
        thermostat.async_schedule_update_ha_state(True)
        hass.async_create_task(coordinator.async_request_refresh())

    async def set_reversing_valve_polarity(service: ServiceCall) -> None:
        """Set minimum time the device is on before letting be off again (run-on time)
        for TH6500WF and TH6250WF thermostats."""
        thermostat = get_thermostat(service)
        if not isinstance(thermostat, Neviweb130HeatCoolThermostat):
            raise ServiceValidationError(f"Entity {thermostat.entity_id} must be a {DOMAIN} heat-cool thermostat")
        await thermostat.async_set_reversing_valve_polarity(service.data)
        thermostat.async_schedule_update_ha_state(True)
        hass.async_create_task(coordinator.async_request_refresh())

    async def set_min_time_on_service(service: ServiceCall) -> None:
        """Set minimum time the device is on before letting be off again (run-on time)
        for TH6500WF and TH6250WF thermostats."""
        thermostat = get_thermostat(service)
        if not isinstance(thermostat, Neviweb130HeatCoolThermostat):
            raise ServiceValidationError(f"Entity {thermostat.entity_id} must be a {DOMAIN} heat-cool thermostat")
        value = {
            "id": thermostat.unique_id,
            ATTR_TIME: service.data[ATTR_AUX_HEAT_MIN_TIME_ON],
        }
        await thermostat.async_set_min_time_on(value)
        thermostat.async_schedule_update_ha_state(True)
        hass.async_create_task(coordinator.async_request_refresh())

    async def set_min_time_off_service(service: ServiceCall) -> None:
        """Set minimum time the device is off before letting it be on again (cooldown time)
        for TH6500WF and TH6250WF thermostats."""
        thermostat = get_thermostat(service)
        if not isinstance(thermostat, Neviweb130HeatCoolThermostat):
            raise ServiceValidationError(f"Entity {thermostat.entity_id} must be a {DOMAIN} heat-cool thermostat")
        await thermostat.async_set_min_time_off(service.data)
        thermostat.schedule_update_ha_state(True)
        hass.async_create_task(coordinator.async_request_refresh())

    async def set_heat_interstage_delay(service: ServiceCall) -> None:
        """Set minimum time the device is heating before letting it increment the heater stage
        for TH6500WF and TH6250WF thermostats."""
        thermostat = get_thermostat(service)
        if not isinstance(thermostat, Neviweb130HeatCoolThermostat):
            raise ServiceValidationError(f"Entity {thermostat.entity_id} must be a {DOMAIN} heat-cool thermostat")
        await thermostat.async_set_heat_interstage_delay(service.data)
        thermostat.async_schedule_update_ha_state(True)
        hass.async_create_task(coordinator.async_request_refresh())

    async def set_cool_interstage_delay(service: ServiceCall) -> None:
        """Set minimum time the device is cooling before letting it increment the cooler stage
        for TH6500WF and TH6250WF thermostats."""
        thermostat = get_thermostat(service)
        if not isinstance(thermostat, Neviweb130HeatCoolThermostat):
            raise ServiceValidationError(f"Entity {thermostat.entity_id} must be a {DOMAIN} heat-cool thermostat")
        await thermostat.async_set_cool_interstage_delay(service.data)
        thermostat.async_schedule_update_ha_state(True)
        hass.async_create_task(coordinator.async_request_refresh())

    async def set_accessory_type_service(service: ServiceCall) -> None:
        """Set TH6500WF accessory (humidifier, dehumidifier, air exchanger) type."""
        thermostat = get_thermostat(service)
        if not isinstance(thermostat, Neviweb130HeatCoolThermostat):
            raise ServiceValidationError(f"Entity {thermostat.entity_id} must be a {DOMAIN} heat-cool thermostat")
        value = {"id": thermostat.unique_id, "type": service.data[ATTR_ACCESSORY_TYPE]}
        await thermostat.async_set_accessory_type(value)
        thermostat.async_schedule_update_ha_state(True)
        hass.async_create_task(coordinator.async_request_refresh())

    async def set_schedule_mode_service(service: ServiceCall) -> None:
        """Set TH6500WF, TH6250WF schedule mode, manual or auto."""
        thermostat = get_thermostat(service)
        if not isinstance(thermostat, Neviweb130HeatCoolThermostat):
            raise ServiceValidationError(f"Entity {thermostat.entity_id} must be a {DOMAIN} heat-cool thermostat")
        value = {
            "id": thermostat.unique_id,
            "mode": service.data[ATTR_SETPOINT_MODE],
        }
        await thermostat.async_set_schedule_mode(value)
        thermostat.async_schedule_update_ha_state(True)
        hass.async_create_task(coordinator.async_request_refresh())

    async def set_heatcool_setpoint_delta_service(service: ServiceCall) -> None:
        """Set TH6500WF, TH6250WF delta temperature between heating and cooling setpoint."""
        thermostat = get_thermostat(service)
        if not isinstance(thermostat, Neviweb130HeatCoolThermostat):
            raise ServiceValidationError(f"Entity {thermostat.entity_id} must be a {DOMAIN} heat-cool thermostat")
        value = {
            "id": thermostat.unique_id,
            "level": service.data[ATTR_HEATCOOL_SETPOINT_MIN_DELTA],
        }
        await thermostat.async_set_heatcool_setpoint_delta(value)
        thermostat.async_schedule_update_ha_state(True)
        hass.async_create_task(coordinator.async_request_refresh())

    async def set_fan_filter_reminder_service(service: ServiceCall) -> None:
        """Set TH6500WF, TH6250WF fan filter reminder period from 1 to 12 month."""
        thermostat = get_thermostat(service)
        value = {
            "id": thermostat.unique_id,
            "month": service.data[ATTR_FAN_FILTER_REMAIN],
        }
        await thermostat.async_set_fan_filter_reminder(value)
        thermostat.async_schedule_update_ha_state(True)
        hass.async_create_task(coordinator.async_request_refresh())

    async def set_temperature_offset_service(service: ServiceCall) -> None:
        """Set TH6500WF, TH6250WF temperature sensor offset from -2 to 2°C with a 0.5°C increment."""
        thermostat = get_thermostat(service)
        if not isinstance(thermostat, Neviweb130HeatCoolThermostat):
            raise ServiceValidationError(f"Entity {thermostat.entity_id} must be a {DOMAIN} heat-cool thermostat")
        value = {
            "id": thermostat.unique_id,
            "temp": service.data[ATTR_TEMP_OFFSET_HEAT],
        }
        await thermostat.async_set_temperature_offset(value)
        thermostat.async_schedule_update_ha_state(True)
        hass.async_create_task(coordinator.async_request_refresh())

    async def set_aux_heating_source_service(service: ServiceCall) -> None:
        """Set TH6500WF, TH6250WF auxiliary heating device."""
        thermostat = get_thermostat(service)
        if not isinstance(thermostat, Neviweb130HeatCoolThermostat):
            raise ServiceValidationError(f"Entity {thermostat.entity_id} must be a {DOMAIN} heat-cool thermostat")
        value = {
            "id": thermostat.unique_id,
            ATTR_AUX_HEAT_SOURCE_TYPE: service.data[ATTR_AUX_HEAT_SOURCE_TYPE],
        }
        await thermostat.async_set_aux_heating_source(value)
        thermostat.async_schedule_update_ha_state(True)
        hass.async_create_task(coordinator.async_request_refresh())

    async def set_fan_speed_service(service: ServiceCall) -> None:
        """Set TH6500WF, TH6250WF fan speed, On or Auto."""
        thermostat = get_thermostat(service)
        if not isinstance(thermostat, Neviweb130HeatCoolThermostat):
            raise ServiceValidationError(f"Entity {thermostat.entity_id} must be a {DOMAIN} heat-cool thermostat")
        value = {
            "id": thermostat.unique_id,
            "speed": service.data[ATTR_FAN_SPEED],
        }
        await thermostat.async_set_fan_speed(value)
        thermostat.async_schedule_update_ha_state(True)
        hass.async_create_task(coordinator.async_request_refresh())

    async def set_humidity_mode_service(service: ServiceCall) -> None:
        """Set TH6500WF, TH6250WF fan speed, On or Auto."""
        thermostat = get_thermostat(service)
        if not isinstance(thermostat, Neviweb130HeatCoolThermostat):
            raise ServiceValidationError(f"Entity {thermostat.entity_id} must be a {DOMAIN} heat-cool thermostat")
        value = {
            "id": thermostat.unique_id,
            "mode": service.data[ATTR_HUMIDITY_SETPOINT_MODE],
        }
        await thermostat.async_set_humidity_mode(value)
        thermostat.async_schedule_update_ha_state(True)
        hass.async_create_task(coordinator.async_request_refresh())

    async def set_heat_dissipation_time_service(service: ServiceCall) -> None:
        """Set TH6500WF, TH6250WF fan speed, On or Auto."""
        thermostat = get_thermostat(service)
        if not isinstance(thermostat, Neviweb130HeatCoolThermostat):
            raise ServiceValidationError(f"Entity {thermostat.entity_id} must be a {DOMAIN} heat-cool thermostat")
        value = {
            "id": thermostat.unique_id,
            ATTR_TIME: service.data[ATTR_TIME] * 60,
        }
        await thermostat.async_set_heat_dissipation_time(value)
        thermostat.async_schedule_update_ha_state(True)
        hass.async_create_task(coordinator.async_request_refresh())

    async def set_cool_dissipation_time_service(service: ServiceCall) -> None:
        """Set TH6500WF, TH6250WF fan speed, On or Auto."""
        thermostat = get_thermostat(service)
        if not isinstance(thermostat, Neviweb130HeatCoolThermostat):
            raise ServiceValidationError(f"Entity {thermostat.entity_id} must be a {DOMAIN} heat-cool thermostat")
        value = {
            "id": thermostat.unique_id,
            ATTR_TIME: service.data[ATTR_TIME] * 60,
        }
        await thermostat.async_set_cool_dissipation_time(value)
        thermostat.async_schedule_update_ha_state(True)
        hass.async_create_task(coordinator.async_request_refresh())

    async def set_climate_neviweb_status_service(service: ServiceCall) -> None:
        """Set Neviweb global occupancy status per location, home or away."""
        thermostat = get_thermostat(service)
        value = {"id": thermostat.unique_id, "mode": service.data[ATTR_MODE]}
        await thermostat.async_set_climate_neviweb_status(value)
        thermostat.async_schedule_update_ha_state(True)
        hass.async_create_task(coordinator.async_request_refresh())

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
    """Transform numerical value from neviweb to string"""
    last = ""
    for k, v in sorted(HA_TO_NEVIWEB_PERIOD.items(), key=lambda x: x[1]):
        last = k
        if value <= v:
            return k
    return last


def neviweb_to_ha_fan(value: int, model: int) -> str:
    """Return fanSpeed value for model 6813 or 6814."""
    if model == 6813:
        mapping = HA_TO_NEVIWEB_FAN_SPEED
    elif model == 6814:
        mapping = HA_TO_NEVIWEB_FAN_SPEED_5
    else:
        raise ValueError(f"model not supported: {model}")

    last = ""
    for k, v in sorted(mapping.items(), key=lambda x: x[1]):
        last = k
        if value <= v:
            return k
    return last


def neviweb_to_ha_mode(mode: str) -> HVACMode:
    """Convert Neviweb mode string to HVACMode for HP6000WF-xx thermostats."""
    hvac = NEVIWEB_TO_HA_MODE.get(mode)
    if hvac is None:
        raise ValueError(f"Unknown Neviweb HVAC mode: {mode}")
    return hvac


def temp_format_to_ha(value):
    if value == "celsius":
        return UnitOfTemperature.CELSIUS
    else:
        return UnitOfTemperature.FAHRENHEIT


def lock_to_ha(lock):
    """Convert keypad lock state to better description."""
    match lock:
        case "locked":
            return "locked"
        case "lock":
            return "locked"
        case "partiallyLocked":
            return "tamper protection"
        case "partialLock":
            return "tamper protection"
    return "unlocked"


def backlight_to_ha(back):
    """Convert backlight value received from Neviweb to HA values."""
    match back:
        case "alwaysOn":
            return "on"
        case "onUserAction":
            return "auto"
        case "always":
            return "on"
        case "onActive":
            return "auto"
    return back


def extract_capability_full(cap):
    """Extract swing capability which are True for each HP device and add genegal capability."""
    value = {i for i in cap if cap[i] is True}
    return FULL_SWING_OFF + sorted(value)


def extract_capability(cap):
    """Extract capability which are True for each HP device."""
    value = {i for i in cap if cap[i] is True}
    return sorted(value)


def retrieve_data(id, device_dict, data):
    """Retrieve device stat data from device_dict."""
    device_data = device_dict.get(id)
    if device_data:
        _LOGGER.debug("Retrieve data for %s = $s", id, device_data)
        if data == 1:
            return device_data[1]
        else:
            return device_data[2]
    else:
        # Set defaults if device not found
        if data == 1:
            _LOGGER.debug("Retrieve data for %s not found", id)
            return 0
        else:
            return None


async def save_data(id, device_dict, data, mark, conf_dir):
    """Save stat data for one device in the device_dict."""
    entry = device_dict.get(id)
    if entry is None or not isinstance(entry, list) or len(entry) < 3:
        _LOGGER.warning(f"Invalid entry for {id}: {entry}")
        return
    _LOGGER.debug(f"Device {id} data before update: {entry}")
    entry[1] = data
    entry[2] = mark
    await save_devices(conf_dir, device_dict)
    _LOGGER.debug(f"Device {id} data updated: {entry}")


async def async_add_data(conf_dir, device_dict, id, data, mark):
    """Add new device stat data in the device_dict."""
    if id in device_dict:
        _LOGGER.debug("Device already exist in device_dict %s", id)
        await save_data(id, device_dict, data, mark, conf_dir)
        return
    device_dict[id] = [id, data, mark]
    await save_devices(conf_dir, device_dict)  # Persist changes
    _LOGGER.debug("Data added for %s", id)


class Neviweb130Thermostat(CoordinatorEntity, ClimateEntity):
    """Implementation of Neviweb TH1123ZB, TH1124ZB thermostat."""

    _enable_turn_on_off_backwards_compatibility = False
    _attr_temperature_unit = UnitOfTemperature.CELSIUS
    _attr_precision = 0.1
    _attr_target_temperature_step = 0.5

    def __init__(self, data, device_info, name, sku, firmware, location, coordinator, entry):
        """Initialize."""
        super().__init__(coordinator)
        _LOGGER.debug("Setting up %s: %s", name, device_info)
        self._attr_state_class = SensorStateClass.TOTAL
        self._attr_unit_class = "energy"
        self._attr_statistic_mean_type = StatisticMeanType.ARITHMETIC

        self._conf_dir = data["conf_dir"]
        self._device_dict = data["device_dict"]
        self._device = device_info
        self._name = name
        self._location = str(location)
        self._sku = sku
        self._firmware = firmware
        self._client = data["neviweb130_client"]
        self._homekit_mode = data["homekit_mode"]
        self._stat_interval = data["stat_interval"]
        self._notify = data["notify"]
        self._prefix = data["prefix"]
        self._ignore_miwi = data["ignore_miwi"]
        self._entry = entry
        self._id = str(device_info["id"])
        self._device_model = device_info["signature"]["model"]
        self._device_model_cfg = device_info["signature"]["modelCfg"]
        self._hard_rev = device_info["signature"]["hardRev"]
        self._identifier = device_info["identifier"]
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
            or device_info["signature"]["model"] in DEVICE_MODEL_WIFI_HEAT_PUMP
        )
        self._is_wifi_lite = device_info["signature"]["model"] in DEVICE_MODEL_WIFI_LITE
        self._is_low_voltage = device_info["signature"]["model"] in DEVICE_MODEL_LOW
        self._is_low_wifi = device_info["signature"]["model"] in DEVICE_MODEL_LOW_WIFI
        self._is_HP = device_info["signature"]["model"] in DEVICE_MODEL_HEAT_PUMP
        self._is_WHP = device_info["signature"]["model"] in DEVICE_MODEL_WIFI_HEAT_PUMP
        self._is_color_wifi = device_info["signature"]["model"] in DEVICE_MODEL_COLOR_WIFI
        self._active: bool = True
        self._active_errors = set()
        self._aux_cycle_length = 0
        self._avail_mode = None
        self._backlight = None
        self._balance_pt = None
        self._balance_pt_high = None
        self._balance_pt_low = None
        self._cool_lockout_temp = None
        self._cool_max: float | None = 36
        self._cool_min: float | None = 15
        self._cur_temp = None
        self._cur_temp_before = None
        self._cycle_length: str | None = None
        self._cycle_length_output2_status: str | None = "off"
        self._cycle_length_output2_value: str | None = None
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
        self._em_heat = None
        self._energy_stat_time = time.time() - 1500
        self._error_code = 0
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
        self._heat_cool: HVACMode | str | None = None
        self._heat_level: int | None = 0
        self._heat_lockout_temp = None
        self._hour_kwh = 0
        self._hourly_kwh_count = 0
        self._keypad: str | None = None
        self._language = None
        self._load2 = None
        self._load2_status = None
        self._lv_aux_cycle_length: str | None = None
        self._lv_cycle_length: str | None = None
        self._mark = retrieve_data(self._id, self._device_dict, 2)
        self._marker = None
        self._max_temp: float = 30
        self._min_temp: float = 5
        self._month_kwh = 0
        self._monthly_kwh_count = 0
        self._occupancy = "home"
        self._occupancy_mode = "home"
        self._operation_mode = None
        self._pump_protec_duration = None
        self._pump_protec_period = None
        self._pump_protec_status = "off"
        self._rssi = None
        self._snooze: float = 0.0
        self._sound_conf = None
        self._target_cool = 21.5
        self._target_temp = 20.0
        self._target_temp_away = None
        self._temp_display_value = None
        self._temperature = None
        self._temperature_format = "celsius"
        self._time_format = "24h"
        self._today_kwh = 0
        self._total_kwh_count = retrieve_data(self._id, self._device_dict, 1)
        self._wattage = 0
        self._weather_icon = None
        self._wifi_aux_cycle_length: str | None = None
        self._wifi_cycle_length: str | None = None

        self._attr_device_info = DeviceInfo(
            identifiers={(DOMAIN, self._id)},
            name=f"{self._prefix} {self._name}" if self._prefix else self._name,
            manufacturer="claudegel",
            model=self._device_model,
            sw_version=self._firmware,
            hw_version=self._hard_rev,
            serial_number=self._identifier,
            configuration_url="https://www.sinopetech.com/support",
        )

    async def async_update(self) -> None:
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
            device_data = await self._client.async_get_device_attributes(
                self._id,
                UPDATE_ATTRIBUTES + HEAT_ATTRIBUTES + FIRMWARE_SPECIAL,
            )
            neviweb_status = await self._client.async_get_neviweb_status(self._location)
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
                    self._backlight = backlight_to_ha(device_data[ATTR_BACKLIGHT])
                    if ATTR_CYCLE_LENGTH in device_data:
                        self._cycle_length = neviweb_to_ha(device_data[ATTR_CYCLE_LENGTH])
                    if ATTR_RSSI in device_data:
                        self._rssi = device_data[ATTR_RSSI]
                    self._operation_mode = device_data[ATTR_SYSTEM_MODE]
                    if not self._is_low_voltage:
                        self._wattage = device_data[ATTR_WATTAGE]
                    self.async_write_ha_state()
                elif device_data["errorCode"] == "ReadTimeout":
                    _LOGGER.warning(
                        "A timeout occur during data update. Device %s do not respond. Check your network... (%s)",
                        self._name,
                        device_data,
                    )
                else:
                    _LOGGER.warning("Error in updating device %s: (%s)", self._name, device_data)
            else:
                await self.async_log_error(device_data["error"]["code"])
            self._occupancy_mode = neviweb_status[ATTR_OCCUPANCY]
            await self.async_do_stat(start)
            await self.async_get_sensor_error_code()
            await self.async_get_weather()
        else:
            if time.time() - self._snooze > SNOOZE_TIME:
                self._active = True
                if self._notify == "notification" or self._notify == "both":
                    await async_notify_once_or_update(
                        self.hass,
                        "Warning: Neviweb Device update restarted for " + self._name + ", Sku: " + self._sku,
                        title=f"Neviweb130 integration {VERSION}",
                        notification_id=f"neviweb130_update_restarted",
                    )

    @property
    @override
    def unique_id(self) -> str:
        """Return unique ID based on Neviweb130 device ID."""
        return f"{self._entry.entry_id}_{self._id}"

    @property
    def id(self) -> str:
        """Alias pour DataUpdateCoordinator."""
        return self._id

    @property
    def sku(self) -> str:
        """Return device sku."""
        return self._sku

    @property
    @override
    def name(self):
        """Return the name of the thermostat."""
        if self._prefix:
            return f"{self._prefix} {self._name}"
        return self._name

    @property
    @override
    def temperature_unit(self) -> UnitOfTemperature:
        """Return the unit of measurement of this entity, if any."""
        # Will always send Celsius values even if it's configured to display in Fahrenheit
        return UnitOfTemperature.CELSIUS

    @property
    def unit_of_measurement(self):
        """Return the unit of measurement of this entity, if any."""
        return temp_format_to_ha(self._temperature_format)

    @property
    @override
    def device_class(self):
        """Return the device class of this entity."""
        return SensorDeviceClass.TEMPERATURE

    @property
    def location(self):
        """Return Neviweb location ID."""
        return self._location

    @property
    def occupancy_mode(self):
        """Return the status of Neviweb, Home or Away."""
        return self._occupancy_mode

    @property
    def rssi(self):
        if self._rssi is not None:
            return self._rssi
        return None

    @property
    def language(self):
        if self._language is not None:
            return self._language
        return None

    @property
    def total_kwh_count(self):
        if self._total_kwh_count is not None:
            return self._total_kwh_count
        return None

    @property
    def monthly_kwh_count(self):
        if self._monthly_kwh_count is not None:
            return self._monthly_kwh_count
        return None

    @property
    def daily_kwh_count(self):
        if self._daily_kwh_count is not None:
            return self._daily_kwh_count
        return None

    @property
    def hourly_kwh_count(self):
        if self._hourly_kwh_count is not None:
            return self._hourly_kwh_count
        return None

    @property
    def keypad_status(self):
        if self._keypad is not None:
            return self._keypad
        return None

    @property
    def backlight(self):
        if self._backlight is not None:
            return self._backlight
        return None

    @property
    def time_format(self):
        return self._time_format

    @property
    def temp_format(self):
        return self._temperature_format

    @property
    def second_display(self):
        return self._display2

    @property
    def wattage(self):
        return self._wattage

    @property
    def cycle_length(self):
        return self._cycle_length

    @property
    def heat_lockout_temp(self):
        return self._heat_lockout_temp

    @property
    def cool_lockout_temp(self):
        return self._cool_lockout_temp

    @property
    def lv_aux_cycle_length(self):
        return self._lv_aux_cycle_length

    @property
    def lv_cycle_length(self):
        return self._lv_cycle_length

    @property
    def wifi_cycle_length(self):
        return self._wifi_cycle_length

    @property
    def wifi_aux_cycle_length(self):
        return self._wifi_aux_cycle_length

    @property
    def sensor_mode(self):
        return self._floor_mode

    @property
    def early_start(self):
        return self._early_start

    @property
    def floor_setpoint_max(self):
        return self._floor_max

    @property
    def floor_setpoint_min(self):
        return self._floor_min

    @property
    def setpoint_away(self):
        return self._target_temp_away

    @property
    def activation(self) -> bool:
        """Return True if entity is active."""
        return bool(self._active)

    @property
    def is_heating(self) -> bool:
        """Return True if heat_level is > 0."""
        return self._heat_level is not None and self._heat_level > 0

    @property
    def is_wifi(self) -> bool:
        """Return True if device is a Wi-Fi device."""
        return self._is_wifi

    @property
    def is_gen2(self) -> bool:
        """Return True if device is a TH1123ZB-G2 or TH1124ZB-G2."""
        return self._is_gen2

    @property
    def is_wifi_floor(self) -> bool:
        """Return True if device is a Wi-Fi floor device."""
        return self._is_wifi_floor

    @property
    def is_HC(self) -> bool:
        """Return True if device is a Wi-Fi heat/cool device."""
        return self._is_HC

    @property
    def is_WHP(self) -> bool:
        """Return True if device is a Wi-Fi heat pump device."""
        return self._is_WHP

    @property
    def is_HP(self) -> bool:
        """Return True if device is a Zigbee heat pump device."""
        return self._is_HP

    @property
    def is_HC_like(self) -> bool:
        """Return True if device is a Zigbee heat pump device, HC or WHP."""
        return self._is_HC_like

    @property
    def is_color_wifi(self) -> bool:
        """Return True if device is a Wi-Fi TH1143WF or TH1144WF device."""
        return self._is_color_wifi

    @property
    @override
    def extra_state_attributes(self)  -> Mapping[str, Any]:
        """Return the state attributes."""
        data = {}
        data.update(
            {
                "wattage": self._wattage,
                "cycle_length": self._cycle_length,
                "neviweb_occupancy_mode": self._occupancy_mode,
                "error_code": self._error_code,
                "heat_level": self._heat_level,
                "pi_heating_demand": self._heat_level,
                "icon_type": self.icon_type,
                "temp_display_value": self._temp_display_value,
                "second_display": self._display2,
                "keypad": self._keypad,
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
    def pi_heating_demand(self) -> int | None:
        """Heating demand."""
        return self._heat_level

    @property
    def icon_type(self) -> str:
        """Select icon based on pi_heating_demand value."""
        prefix = "floor" if (self._is_floor or self._is_wifi_floor) else "heat"

        if self.hvac_mode == HVACMode.OFF:
            return f"/local/neviweb130/{prefix}-off.png"

        thresholds = [
            (1,  "-0"),
            (21, "-1"),
            (41, "-2"),
            (61, "-3"),
            (81, "-4"),
        ]

        demand = self.pi_heating_demand
        for limit, suffix in thresholds:
            if demand < limit:
                return f"/local/neviweb130/{prefix}{suffix}.png"

        return f"/local/neviweb130/{prefix}-5.png"

    @property
    @override
    def supported_features(self):
        """Return the list of supported features."""
        if self._is_floor or self._is_wifi_floor or self._is_low_wifi or self._is_low_voltage:
            return SUPPORT_AUX_FLAGS
        elif self._is_HP or self._is_WHP:
            return SUPPORT_HP_FLAGS
        elif self._is_HC:
            return SUPPORT_HC_FLAGS
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
        elif self._lv_aux_cycle_length != "off":
            return True
        else:
            return False

    @property
    @override
    def target_temperature_low(self) -> float:
        """Return the minimum heating temperature."""
        return self._min_temp

    @property
    @override
    def target_temperature_high(self) -> float:
        """Return the maximum heating temperature."""
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
    def temperature_unit(self):
        """Return the unit of measurement."""
        return UnitOfTemperature.CELSIUS

    @property
    def weather_icon(self) -> int:
        return self._weather_icon

    @property
    @override
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
        elif self._operation_mode == MODE_EM_HEAT:
                return MODE_EM_HEAT
        else:
            return HVACMode.HEAT

    @property
    @override
    def hvac_modes(self):
        """Return the list of available operation modes."""
        if self._is_wifi_lite:
            return SUPPORTED_HVAC_WIFI_LITE_MODES
        elif self._is_WHP:
            return SUPPORTED_HVAC_WHP_MODES
        elif self._is_wifi:
            return SUPPORTED_HVAC_WIFI_MODES
        elif self._is_h_c:
            if self._avail_mode == "heatingOnly":
                return SUPPORTED_HVAC_HEAT_MODES
            elif self._avail_mode == "coolingOnly":
                return SUPPORTED_HVAC_COOL_MODES
            else:
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
    @override
    def preset_mode(self):
        """Return current preset mode."""
        if self._occupancy == PRESET_HOME:
            return PRESET_NONE
        elif self._occupancy == PRESET_AWAY:
            return PRESET_AWAY
        else:
            return PRESET_NONE

    @property
    @override
    def preset_modes(self):
        """Return available preset modes."""
        if self._is_h_c:
            return PRESET_h_c_MODES
        elif self._is_wifi:
            return PRESET_WIFI_MODES
        elif self._is_HP or self._is_WHP:
            return PRESET_HP_MODES
        else:
            return PRESET_MODES

    @property
    @override
    def hvac_action(self) -> str | HVACAction | None:  # type: ignore[override]
        """Return current HVAC action."""
        if self._operation_mode == HVACMode.OFF:
            return HVACAction.OFF
        elif self._operation_mode == HVACMode.COOL:
            return HVACAction.COOLING
        elif self._operation_mode == HVACMode.FAN_ONLY:
            return HVACAction.FAN
        elif self._operation_mode == HVACMode.DRY:
            return HVACAction.DRYING
        elif not self._homekit_mode and self._operation_mode == MODE_AUTO_BYPASS:
            if self._heat_level == 0:
                return f"{HVACAction.IDLE.value} ({MODE_AUTO_BYPASS})"
            else:
                return f"{HVACAction.HEATING.value} ({MODE_AUTO_BYPASS})"
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
            or self._operation_mode == HVACMode.FAN_ONLY
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
        elif self._is_WHP:
            return HP_FAN_SPEED
        else:
            return None

    @property
    @override
    def swing_mode(self) -> str | None:
        """Return the fan vertical swing setting."""
        if self._is_HP or self._is_WHP or self._is_h_c:
            return self._fan_swing_vert
        return None

    @property
    @override
    def swing_modes(self) -> list[str] | None:
        """Return availables vertical swing modes."""
        if self._is_HP or self._is_WHP or self._is_h_c:
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
        if self._is_HP or self._is_WHP or self._is_h_c:
            return self._fan_swing_horiz
        return None

    @property
    @override
    def swing_horizontal_modes(self) -> list[str] | None:
        """Return available horizontal swing modes"""
        if self._is_HP or self._is_WHP or self._is_h_c:
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

    @property
    def _is_HC_like(self) -> bool:
        """Return True if device must be managed as HC."""
        return self._is_HC or self._is_WHP

    async def async_set_fan_mode(self, speed: str) -> None:
        """Set new fan mode."""
        if speed is None:
            return

        await self._client.async_set_fan_mode(self._id, speed, self._device_model)
        self._fan_speed = speed

    async def async_set_swing_mode(self, swing: str) -> None:
        """Set new vertical swing mode."""
        if swing is None:
            return
        else:
            await self._client.async_set_swing_vertical(self._id, swing)
            self._fan_swing_vert = swing

    async def async_set_swing_horizontal_mode(self, swing: str) -> None:
        """Set new horizontal swing mode."""
        if swing is None:
            return
        else:
            await self._client.async_set_swing_horizontal(self._id, swing)
            self._fan_swing_horiz = swing

    async def async_turn_on(self) -> None:
        """Turn the thermostat to HVACMode.HEAT."""
        await self._client.async_set_setpoint_mode(self._id, HVACMode.HEAT, self._is_wifi, self._is_HC)
        self._operation_mode = HVACMode.HEAT

    async def async_turn_off(self) -> None:
        """Turn the thermostat to HVACMode.off."""
        await self._client.async_set_setpoint_mode(self._id, HVACMode.OFF, self._is_wifi, self._is_HC)
        self._operation_mode = HVACMode.OFF

    async def async_set_temperature(self, **kwargs: Any) -> None:
        """Set new target temperature."""
        temperature = kwargs.get(ATTR_TEMPERATURE)
        if temperature is None:
            return
        temperature = min(temperature, self._max_temp)
        temperature = max(temperature, self._min_temp)

        success = await self._client.async_set_temperature(self._id, temperature)

        if success:
            # Local update
            self._target_temp = temperature
            self.async_write_ha_state()
            # Coordinator refresh
            await self._delayed_refresh()

    async def async_set_second_display(self, value):
        """Set thermostat second display between outside and setpoint temperature."""
        if value["display"] == "outsideTemperature":
            display_name = "Outside"
        else:
            display_name = "Setpoint"
        await self._client.async_set_second_display(value["id"], value["display"])
        self._display2 = display_name

    async def async_set_backlight(self, value):
        """Set thermostat backlight «auto» = off when idle / on when active or «on» = always on."""
        """Work differently for Zigbee and Wi-Fi devices."""
        is_wifi = self._is_wifi or self._is_low_wifi or self._is_wifi_lite or self._is_wifi_floor
        await self._client.async_set_backlight(value["id"], value["level"], is_wifi)
        self._backlight = value["level"]

    async def async_set_keypad_lock(self, value):
        """Lock or unlock device's keypad, locked = Locked, unlocked = Unlocked."""
        if value["lock"] == "partiallyLocked" and self._is_HP:
            raise ValueError("Mode 'partiallyLocked' is not available for model HP6000.")

        await self._client.async_set_keypad_lock(value["id"], value["lock"], self._is_wifi)
        self._keypad = value["lock"]

    async def async_set_time_format(self, value):
        """Set time format 12h or 24h."""
        if value[ATTR_TIME] == 12:
            time_commande = "12h"
        else:
            time_commande = "24h"
        await self._client.async_set_time_format(value["id"], time_commande)
        self._time_format = time_commande

    async def async_set_temperature_format(self, value):
        """Set temperature format, celsius or fahrenheit."""
        await self._client.async_set_temperature_format(value["id"], value["temp"])
        self._temperature_format = value["temp"]

    async def async_set_air_floor_mode(self, value):
        """Switch temperature control between floor and ambient sensor."""
        await self._client.async_set_air_floor_mode(value["id"], value["mode"])
        self._floor_mode = value["mode"]

    async def async_set_setpoint_max(self, value):
        """Set maximum setpoint temperature."""
        await self._client.async_set_setpoint_max(value["id"], value["temp"])
        self._max_temp = value["temp"]

    async def async_set_setpoint_min(self, value):
        """Set minimum setpoint temperature."""
        await self._client.async_set_setpoint_min(value["id"], value["temp"])
        self._min_temp = value["temp"]

    async def async_set_room_setpoint_away(self, value):
        """Set device away heating setpoint."""
        await self._client.async_set_room_setpoint_away(value["id"], value["temp"])
        self._target_temp_away = value["temp"]

    async def async_set_cool_setpoint_max(self, value):
        """Set maximum cooling setpoint temperature."""
        await self._client.async_set_cool_setpoint_max(value["id"], value["temp"])
        self._cool_max = value["temp"]

    async def async_set_cool_setpoint_min(self, value):
        """Set minimum cooling setpoint temperature."""
        await self._client.async_set_cool_setpoint_min(value["id"], value["temp"])
        self._cool_min = value["temp"]

    async def async_set_floor_air_limit(self, value):
        """Set maximum temperature air limit for floor thermostat."""
        if value["temp"] == 0:
            status = "off"
        else:
            status = "on"
        await self._client.async_set_floor_air_limit(value["id"], status, value["temp"])
        self._floor_air_limit = value["temp"]

    async def async_set_early_start(self, value):
        """Set early heating on/off for Wi-Fi thermostat."""
        await self._client.async_set_early_start(value["id"], value["start"])
        self._early_start = value["start"]

    async def async_set_hvac_dr_options(self, value):
        """Set thermostat DR options for Eco Sinope."""
        await self._client.async_set_hvac_dr_options(
            value["id"], value["dractive"], value["optout"], value["setpoint"]
        )
        self._drstatus_active = value["dractive"]
        self._drstatus_optout = value["optout"]
        self._drstatus_setpoint = value["setpoint"]

    async def async_set_hvac_dr_setpoint(self, value):
        """Set thermostat DR setpoint values for Eco Sinope."""
        await self._client.async_set_hvac_dr_setpoint(value["id"], value["status"], value["val"])
        self._drsetpoint_status = value["status"]
        self._drsetpoint_value = value["val"]

    @override
    async def async_set_hvac_mode(self, hvac_mode):
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
            await self._client.async_set_setpoint_mode(self._id, hvac_mode, self._is_wifi, self._is_HC_like)

        elif hvac_mode == HVACMode.AUTO:
            await self._client.async_set_setpoint_mode(self._id, hvac_mode, self._is_wifi, self._is_HC_like)

        elif hvac_mode == HVACMode.HEAT_COOL:
            await self._client.async_set_setpoint_mode(self._id, hvac_mode, self._is_wifi, self._is_HC_like)

        elif hvac_mode == MODE_AUTO_BYPASS:
            if self._operation_mode == HVACMode.AUTO:
                await self._client.async_set_setpoint_mode(self._id, hvac_mode, self._is_wifi, self._is_HC_like)

        else:
            _LOGGER.error("Unable to set hvac mode: %s.", hvac_mode)

        self._operation_mode = hvac_mode
        # Wait before update to avoid getting old data from Neviweb
        await self._delayed_refresh()

    @override
    async def async_set_preset_mode(self, preset_mode):
        """Activate a preset."""
        if preset_mode == self.preset_mode:
            return
        if preset_mode == PRESET_AWAY:
            await self._client.async_set_occupancy_mode(self._id, PRESET_AWAY, self._is_wifi)
        elif preset_mode == PRESET_HOME:
            await self._client.async_set_occupancy_mode(self._id, PRESET_HOME, self._is_wifi)
        elif preset_mode == PRESET_NONE:
            await self._client.async_set_occupancy_mode(self._id, PRESET_NONE, self._is_wifi)
            # Re-apply current hvac_mode without any preset
            self.set_hvac_mode(self.hvac_mode)
        else:
            _LOGGER.error("Unable to set preset mode: %s.", preset_mode)
        self._occupancy = preset_mode

    async def async_turn_em_heat_on(self):
        """Turn emergency heater on."""
        if self._is_low_voltage:
            value = "on"
            low = "voltage"
            sec = self._cycle_length_output2_value
            self._cycle_length_output2_status = "on"
        elif self._is_low_wifi:
            value = ""
            low = "wifi"
            sec = self._lv_aux_cycle_length
        else:
            value = "slave"
            sec = "off"
            low = "floor"
            self._em_heat = "slave"
        await self._client.async_set_em_heat(self._id, value, low, sec)

    async def async_turn_em_heat_off(self):
        """Turn emergency heater off."""
        if self._is_low_voltage:
            low = "voltage"
            self._cycle_length_output2_status = "off"
            sec = self._cycle_length_output2_value
        elif self._is_low_wifi:
            low = "wifi"
            self._lv_aux_cycle_length = "off"
            sec = "off"
        else:
            low = "floor"
            self._em_heat = "off"
            sec = "off"
        await self._client.async_set_em_heat(self._id, "off", low, sec)

    async def async_set_auxiliary_load(self, value):
        """Set thermostat auxiliary output status and load."""
        await self._client.async_set_auxiliary_load(value["id"], value["status"], value["val"])
        self._load2_status = value["status"]
        self._load2 = value["val"]

    async def async_set_aux_cycle_output(self, value):
        """Set low voltage thermostats auxiliary cycle status and length."""
        is_wifi = self._is_low_wifi or (self._is_wifi and self._is_HC)
        if is_wifi and value["val"] == "off":
            raise ServiceValidationError(f"Entity {self.entity_id} does not support value 'off'")
        await self._client.async_set_aux_cycle_output(value["id"], value["val"], is_wifi)
        if is_wifi:
            self._lv_aux_cycle_length = value["val"]
        elif value["val"] != "off":
            self._cycle_length_output2_status = "on"
            self._cycle_length_output2_value = value["val"]
        else:
            # Leaving self._cycle_length_output2_value to the old value on purpose
            self._cycle_length_output2_status = "off"

    async def async_set_cycle_output(self, value):
        """Set low voltage thermostats main cycle output length."""
        if value["val"] == "off":
            raise ServiceValidationError(f"Entity {self.entity_id} does not support value 'off'")
        await self._client.async_set_cycle_output(value["id"], value["val"], self._is_HC)
        self._cycle_length = value["val"]

    async def async_set_pump_protection(self, value):
        """Set pump protection value."""
        await self._client.async_set_pump_protection(value["id"], value["status"], self._is_low_wifi)
        self._pump_protec_status = value["status"]
        self._pump_protec_duration = 60
        self._pump_protec_period = 1

    async def async_set_sensor_type(self, value):
        """Set sensor type."""
        await self._client.async_set_sensor_type(value["id"], value["type"])
        self._floor_sensor_type = value["type"]

    async def async_set_floor_limit(self, value):
        """Set maximum/minimum floor setpoint temperature."""
        if value["limit"] == "low":
            if 0 < value["level"] < 5:
                value["level"] = 5
        else:
            if 0 < value["level"] < 7:
                value["level"] = 7
        await self._client.async_set_floor_limit(value["id"], value["level"], value["limit"], self._is_wifi_floor)
        if value["limit"] == "low":
            self._floor_min = value["level"] if value["level"] != 0 else None
            self._floor_min_status = "on"
        else:
            self._floor_max = value["level"] if value["level"] != 0 else None
            self._floor_max_status = "on"

    async def async_set_activation(self, value):
        """Activate (True) or deactivate (False) Neviweb polling for a missing device."""
        self._active = value["active"]

    async def async_set_heat_pump_operation_limit(self, value):
        """Set minimum temperature for heat pump operation."""
        if value["temp"] < self._balance_pt_low:
            value["temp"] = self._balance_pt_low
        await self._client.async_set_heat_pump_limit(value["id"], value["temp"])
        self._balance_pt = value["temp"]

    async def async_set_heat_lockout_temperature(self, value):
        """Set maximum outside temperature limit to allow heat device operation."""
        await self._client.async_set_heat_lockout(value["id"], value["temp"], self._is_gen2)
        self._heat_lockout_temp = value["temp"]

    async def async_set_cool_lockout_temperature(self, value):
        """Set minimum outside temperature limit to allow cooling device operation."""
        await self._client.async_set_cool_lockout(value["id"], value["temp"])
        self._cool_lockout_temp = value["temp"]

    async def async_set_display_config(self, value):
        """Set display on/off for heat pump."""
        await self._client.async_set_hp_display(value["id"], value["display"])
        self._display_conf = value["display"]

    async def async_set_sound_config(self, value):
        """Set sound on/off for heat pump."""
        await self._client.async_set_hp_sound(value["id"], value["sound"])
        self._sound_conf = value["sound"]

    async def async_set_hc_second_display(self, value):
        """Set second display value for TH1134ZB-HC."""
        await self._client.async_set_hc_display(value["id"], value["display"])
        self._display2 = value["display"]

    async def async_set_language(self, value):
        """Set display language value for TH1134ZB-HC."""
        await self._client.async_set_language(value["id"], value["lang"])
        self._language = value["lang"]

    async def async_get_weather(self):
        """Get weather temperature for my location."""
        weather = await self._client.async_get_weather()
        self._temperature = weather["temperature"]
        self._weather_icon = weather["icon"]

    async def async_set_climate_neviweb_status(self, value):
        """Set Neviweb global occupancy mode, away or home"""
        await self._client.async_post_neviweb_status(self._location, value["mode"])
        self._occupancy_mode = value["mode"]

    async def _delayed_refresh(self, delay: float = 2.0) -> None:
        """Push immediate state and schedule a delayed refresh via coordinator."""
        # Push l’état local immédiatement vers l’UI
        self.async_write_ha_state()

        # Attendre un peu pour laisser Neviweb appliquer le changement
        await asyncio.sleep(delay)

        # Rafraîchir via le coordinator
        await self.coordinator.async_request_refresh()

    async def async_do_stat(self, start):
        """Get device energy statistic."""
        if start - self._energy_stat_time > self._stat_interval and self._energy_stat_time != 0:
            today = date.today()
            current_month = today.month
            current_day = today.day
            if not self._is_HC:
                device_monthly_stats = await self._client.async_get_device_monthly_stats(self._id, False)
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
                device_daily_stats = await self._client.async_get_device_daily_stats(self._id, False)
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
                device_hourly_stats = await self._client.async_get_device_hourly_stats(self._id, False)
                _LOGGER.debug(
                    "%s device hourly stat (SKU: %s): %s, size = %s",
                    self._name,
                    self._sku,
                    device_hourly_stats,
                    len(device_hourly_stats),
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
                    await async_add_data(self._conf_dir, self._device_dict, self._id, self._total_kwh_count, self._marker)
                    self._mark = self._marker
                else:
                    if self._marker != self._mark:
                        self._total_kwh_count += round(self._hour_kwh, 3)
                        await save_data(self._id, self._device_dict, self._total_kwh_count, self._marker, self._conf_dir)
                        self._mark = self._marker
                _LOGGER.debug("Device dict updated: %s", self._device_dict)
                self._energy_stat_time = time.time()
            else:
                device_hourly_stats = self._client.get_device_hourly_stats(self._id, True)
                _LOGGER.debug(
                    "%s device hourly stats (SKU: %s): %s, size = %s",
                    self._name,
                    self._sku,
                    device_hourly_stats,
                    len(device_hourly_stats),
                )
                stats_map = {
                    "hourly": device_hourly_stats,
                    "daily": device_daily_stats,
                    "monthly": device_monthly_stats,
                }
                # Get the hourly stats
                for prefix in RUNTIME_PREFIXES:
                    if prefix in stats_map:
                        update_runtime_stats(self, stats_map[prefix], TH6_MODES_VALUES, prefix)

        if self._energy_stat_time == 0:
            self._energy_stat_time = start

    async def async_get_sensor_error_code(self):
        """Get device sensor error code."""
        device_error_code = await self._client.async_get_device_sensor_error(self._id)
        raw_code = device_error_code.get("raw", 0) if device_error_code else 0

        # Message list
        error_messages = {
            1048576: "External sensor disconnected (not implemented),",
        }

        if raw_code == 0:
            if self._active_errors:
                await async_notify_once_or_update(
                    self.hass,
                    f"All errors resolved for device {self._name}, ID: {self._id}, Sku: {self._sku}",
                    title=f"Neviweb130 integration {VERSION}",
                    notification_id=f"neviweb130_error_resolved",
                )
                _LOGGER.info("All errors resolved: %s", self._active_errors)
                self._active_errors.clear()
            return

        # If we receive a new error code
        if raw_code not in self._active_errors:
            # Default message if code is unknown
            error_message = error_messages.get(self._error_code, "Unknown error")

            # Send notification
            await async_notify_critical(
                self.hass,
                f"Warning: Neviweb Device error code detected: {raw_code} "
                f"({error_message}) for device: {self._name}, "
                f"ID: {self._id}, Sku: {self._sku}",
                title=f"Neviweb130 integration {VERSION}",
                notification_id="neviweb130_error_code",
            )
            self._active_errors.add(raw_code)

        # Save last error code
        self._error_code = raw_code

    async def async_log_error(self, error_data):
        """Send error message to LOG."""
        if error_data == "USRSESSEXP":
            _LOGGER.warning("Session expired... Reconnecting...")
            if self._notify == "notification" or self._notify == "both":
                await async_notify_once_or_update(
                    self.hass,
                    "Warning: Got USRSESSEXP error, Neviweb session expired. "
                    + "Set your scan_interval parameter to less than 10 "
                    + "minutes to avoid this... Reconnecting...",
                    title=f"Neviweb130 integration {VERSION}",
                    notification_id="neviweb130_reconnect",
                )
            await self._client.async_reconnect()
        elif error_data == "ACCDAYREQMAX":
            _LOGGER.warning("Maximum daily request reached... Reduce polling frequency")
        elif error_data == "TimeoutError":
            _LOGGER.warning("Timeout error detected... Retry later")
        elif error_data == "MAINTENANCE":
            _LOGGER.warning("Access blocked for maintenance... Retry later")
            await async_notify_once_or_update(
                self.hass,
                "Warning: Neviweb access temporary blocked for maintenance... Retry later",
                title=f"Neviweb130 integration {VERSION}",
                notification_id="neviweb130_access_error",
            )
            await self._client.async_reconnect()
        elif error_data == "ACCSESSEXC":
            await async_notify_critical(
                self.hass,
                "Warning: Maximum Neviweb session number reached... Close other connections and try again",
                title=f"Neviweb130 integration {VERSION}",
                notification_id="neviweb130_session_error",
            )
            await self._client.async_reconnect()
        elif error_data == "DVCATTRNSPTD":
            _LOGGER.warning(
                "Device attribute not supported for %s (id: %s): %s...(SKU: %s)",
                self._name,
                self._id,
                error_data,
                self._sku,
            )
        elif error_data == "DVCACTNSPTD":
            _LOGGER.warning(
                "Device action not supported for %s (id: %s)...(SKU: %s) Report to maintainer",
                self._name,
                self._id,
                self._sku,
            )
        elif error_data == "DVCCOMMTO":
            _LOGGER.warning(
                "Device Communication Timeout... The device %s (id: %s) "
                + "did not respond to the server within the prescribed delay"
                + " (SKU: %s)",
                self._name,
                self._id,
                self._sku,
            )
        elif error_data == "SVCERR":
            _LOGGER.warning(
                "Service error, device not available retry later %s (id: %s): %s...(SKU: %s)",
                self._name,
                self._id,
                error_data,
                self._sku,
            )
        elif error_data == "DVCBUSY":
            _LOGGER.warning(
                "Device busy can't reach (neviweb update ?), retry later %s (id: %s): %s...(SKU: %s)",
                self._name,
                self._id,
                error_data,
                self._sku,
            )
        elif error_data == "DVCUNVLB":
            _LOGGER.warning(
                "NOTIFY value: %s, (SKU: %s)",
                self._notify,
                self._sku,
            )
            if self._notify == "logging" or self._notify == "both":
                _LOGGER.warning(
                    "Device %s (id: %s) is disconnected from Neviweb: %s... (SKU: %s)",
                    self._name,
                    self._id,
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
            if self._notify == "notification" or self._notify == "both":
                await async_notify_once_or_update(
                    self.hass,
                    "Warning: Received message from Neviweb, device "
                    + "disconnected... Check your log... Neviweb update will "
                    + "be halted for 20 minutes for "
                    + self._name
                    + ", id: "
                    + self._id
                    + ", Sku: "
                    + self._sku,
                    title=f"Neviweb130 integration {VERSION}",
                    notification_id="neviweb130_device_error",
                )
            self._active = False
            self._snooze = time.time()
        elif error_data == "DVCERR":
            _LOGGER.warning(
                "Device error for %s (id: %s), service already active: %s... (SKU: %s)",
                self._name,
                self._id,
                error_data,
                self._sku,
            )
        elif error_data == "SVCUNAUTH":
            _LOGGER.warning(
                "Service not authorised for device %s (id: %s): %s... (SKU: %s)",
                self._name,
                self._id,
                error_data,
                self._sku,
            )
        else:
            _LOGGER.warning(
                "Unknown error for %s (id: %s): %s... (SKU: %s) Report to maintainer",
                self._name,
                self._id,
                error_data,
                self._sku,
            )


class Neviweb130G2Thermostat(Neviweb130Thermostat):
    """Implementation of Neviweb TH1123ZB-G2, TH1124ZB-G2 thermostats."""

    def __init__(self, data, device_info, name, sku, firmware, location, coordinator, entry):
        """Initialize."""
        super().__init__(data, device_info, name, sku, firmware, location, coordinator, entry)
        self._cold_load_pickup = None

    @override
    async def async_update(self) -> None:
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
            device_data = await self._client.async_get_device_attributes(self._id, UPDATE_ATTRIBUTES + GEN2_ATTRIBUTES)
            neviweb_status = await self._client.async_get_neviweb_status(self._location)
            end = time.time()
            elapsed = round(end - start, 3)
            _LOGGER.debug("Updating %s (%s sec): %s", self._name, elapsed, device_data)
            _LOGGER.debug("Neviweb status = %s", neviweb_status)

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
                    self._backlight = backlight_to_ha(device_data[ATTR_BACKLIGHT])
                    if ATTR_CYCLE_LENGTH in device_data:
                        self._cycle_length = neviweb_to_ha(device_data[ATTR_CYCLE_LENGTH])
                    self._operation_mode = device_data[ATTR_SYSTEM_MODE]
                    self._wattage = device_data[ATTR_WATTAGE]
                    self.async_write_ha_state()
                elif device_data["errorCode"] == "ReadTimeout":
                    _LOGGER.warning(
                        "A timeout occur during data update. Device %s do not respond. Check your network... (%s)",
                        self._name,
                        device_data,
                    )
                else:
                    _LOGGER.warning(
                        "Error in updating device %s: (%s)",
                        self._name,
                        device_data,
                    )
            else:
                await self.async_log_error(device_data["error"]["code"])
            self._occupancy_mode = neviweb_status[ATTR_OCCUPANCY]
            await self.async_do_stat(start)
            await self.async_get_sensor_error_code()
            await self.async_get_weather()
        else:
            if time.time() - self._snooze > SNOOZE_TIME:
                self._active = True
                if self._notify == "notification" or self._notify == "both":
                    await async_notify_once_or_update(
                        self.hass,
                        "Warning: Neviweb Device update restarted for " + self._name + ", Sku: " + self._sku,
                        title=f"Neviweb130 integration {VERSION}",
                        notification_id=f"neviweb130_update_restarted",
                    )

    @property
    @override
    def extra_state_attributes(self)  -> Mapping[str, Any]:
        """Return the state attributes."""
        data = {}
        data.update(
            {
                "wattage": self._wattage,
                "cycle_length": self._cycle_length,
                "neviweb_occupancy_mode": self._occupancy_mode,
                "error_code": self._error_code,
                "heat_level": self._heat_level,
                "pi_heating_demand": self._heat_level,
                "icon_type": self.icon_type,
                "temp_display_value": self._temp_display_value,
                "second_display": self._display2,
                "keypad": self._keypad,
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
    """Implementation of Neviweb TH1300ZB thermostat."""

    def __init__(self, data, device_info, name, sku, firmware, location, coordinator, entry):
        """Initialize."""
        super().__init__(data, device_info, name, sku, firmware, location, coordinator, entry)
        self._floor_air_limit_status = None
        self._floor_max_status = "off"
        self._floor_min_status = "off"
        self._gfci_alert = None
        self._gfci_status = None
        self._load2 = 0

    @override
    async def async_update(self) -> None:
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
            device_data = await self._client.async_get_device_attributes(self._id, UPDATE_ATTRIBUTES + FLOOR_ATTRIBUTES)
            neviweb_status = await self._client.async_get_neviweb_status(self._location)
            end = time.time()
            elapsed = round(end - start, 3)
            _LOGGER.debug("Updating %s (%s sec): %s", self._name, elapsed, device_data)
            _LOGGER.debug("Neviweb status = %s", neviweb_status)

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
                    self._backlight = backlight_to_ha(device_data[ATTR_BACKLIGHT])
                    if ATTR_CYCLE_LENGTH in device_data:
                        self._cycle_length = neviweb_to_ha(device_data[ATTR_CYCLE_LENGTH])
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
                    self.async_write_ha_state()
                elif device_data["errorCode"] == "ReadTimeout":
                    _LOGGER.warning(
                        "A timeout occur during data update. Device %s do not respond. Check your network... (%s)",
                        self._name,
                        device_data,
                    )
                else:
                    _LOGGER.warning(
                        "Error in updating device %s: (%s)",
                        self._name,
                        device_data,
                    )
            else:
                await self.async_log_error(device_data["error"]["code"])
            self._occupancy_mode = neviweb_status[ATTR_OCCUPANCY]
            await self.async_do_stat(start)
            await self.async_get_sensor_error_code()
            await self.async_get_weather()
        else:
            if time.time() - self._snooze > SNOOZE_TIME:
                self._active = True
                if self._notify == "notification" or self._notify == "both":
                    await async_notify_once_or_update(
                        self.hass,
                        "Warning: Neviweb Device update restarted for " + self._name + ", Sku: " + self._sku,
                        title=f"Neviweb130 integration {VERSION}",
                        notification_id=f"neviweb130_update_restarted",
                    )

    @property
    @override
    def extra_state_attributes(self)  -> Mapping[str, Any]:
        """Return the state attributes."""
        data = {}
        data.update(
            {
                "wattage": self._wattage,
                "neviweb_occupancy_mode": self._occupancy_mode,
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
                "icon_type": self.icon_type,
                "cycle_length": self._cycle_length,
                "temp_display_value": self._temp_display_value,
                "second_display": self._display2,
                "keypad": self._keypad,
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
    """Implementation of Neviweb TH1400ZB low voltage thermostat."""

    def __init__(self, data, device_info, name, sku, firmware, location, coordinator, entry):
        """Initialize."""
        super().__init__(data, device_info, name, sku, firmware, location, coordinator, entry)
        self._floor_air_limit_status = "off"
        self._floor_max_status = "off"
        self._floor_min_status = "off"
        self._load1 = 0
        self._load1_status = "off"
        self._load2 = 0
        self._pump_protec_period_status = "off"

    @override
    async def async_update(self) -> None:
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
            device_data = await self._client.async_get_device_attributes(
                self._id, UPDATE_ATTRIBUTES + LOW_VOLTAGE_ATTRIBUTES
            )
            neviweb_status = await self._client.async_get_neviweb_status(self._location)
            end = time.time()
            elapsed = round(end - start, 3)
            _LOGGER.debug("Updating %s (%s sec): %s", self._name, elapsed, device_data)
            _LOGGER.debug("Neviweb status = %s", neviweb_status)

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
                    self._backlight = backlight_to_ha(device_data[ATTR_BACKLIGHT])
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
                        self._lv_cycle_length = neviweb_to_ha(device_data[ATTR_CYCLE_LENGTH])
                    if ATTR_RSSI in device_data:
                        self._rssi = device_data[ATTR_RSSI]
                    self._operation_mode = device_data[ATTR_SYSTEM_MODE]
                    self._floor_mode = device_data[ATTR_FLOOR_MODE]
                    self._floor_air_limit = device_data[ATTR_FLOOR_AIR_LIMIT]["value"]
                    self._floor_air_limit_status = device_data[ATTR_FLOOR_AIR_LIMIT]["status"]
                    self._cycle_length_output2_status = device_data[ATTR_CYCLE_OUTPUT2]["status"]
                    self._cycle_length_output2_value = (
                        neviweb_to_ha(device_data[ATTR_CYCLE_OUTPUT2]["value"])
                        if device_data[ATTR_CYCLE_OUTPUT2]["value"] is not None
                        else 0
                    )
                    self._floor_max = device_data[ATTR_FLOOR_MAX]["value"]
                    self._floor_max_status = device_data[ATTR_FLOOR_MAX]["status"]
                    self._floor_min = device_data[ATTR_FLOOR_MIN]["value"]
                    self._floor_min_status = device_data[ATTR_FLOOR_MIN]["status"]
                    self._pump_protec_status = device_data[ATTR_PUMP_PROTEC_DURATION]["status"]
                    self._pump_protec_duration = device_data[ATTR_PUMP_PROTEC_DURATION]["value"]
                    self._pump_protec_period = device_data[ATTR_PUMP_PROTEC_PERIOD]["value"]
                    self._pump_protec_period_status = device_data[ATTR_PUMP_PROTEC_PERIOD]["status"]
                    self._floor_sensor_type = device_data[ATTR_FLOOR_SENSOR]
                    if ATTR_FLOOR_OUTPUT1 in device_data:
                        self._load1_status = device_data[ATTR_FLOOR_OUTPUT1]["status"]
                        if device_data[ATTR_FLOOR_OUTPUT1]["status"] == "on":
                            self._load1 = device_data[ATTR_FLOOR_OUTPUT1]["value"]
                    if ATTR_FLOOR_OUTPUT2 in device_data:
                        self._load2_status = device_data[ATTR_FLOOR_OUTPUT2]["status"]
                        if device_data[ATTR_FLOOR_OUTPUT2]["status"] == "on":
                            self._load2 = device_data[ATTR_FLOOR_OUTPUT2]["value"]
                    self.async_write_ha_state()
                elif device_data["errorCode"] == "ReadTimeout":
                    _LOGGER.warning(
                        "A timeout occur during data update. Device %s do not respond. Check your network... (%s)",
                        self._name,
                        device_data,
                    )
                else:
                    _LOGGER.warning(
                        "Error updating device %s: (%s)",
                        self._name,
                        device_data,
                    )
            else:
                await self.async_log_error(device_data["error"]["code"])
            self._occupancy_mode = neviweb_status[ATTR_OCCUPANCY]
            await self.async_do_stat(start)
            await self.async_get_sensor_error_code()
            await self.async_get_weather()
        else:
            if time.time() - self._snooze > SNOOZE_TIME:
                self._active = True
                if self._notify == "notification" or self._notify == "both":
                    await async_notify_once_or_update(
                        self.hass,
                        "Warning: Neviweb Device update restarted for " + self._name + ", Sku: " + self._sku,
                        title=f"Neviweb130 integration {VERSION}",
                        notification_id=f"neviweb130_update_restarted",
                    )

    @property
    @override
    def extra_state_attributes(self)  -> Mapping[str, Any]:
        """Return the state attributes."""
        data = {}
        data.update(
            {
                "sensor_mode": self._floor_mode,
                "cycle_length": self._lv_cycle_length,
                "neviweb_occupancy_mode": self._occupancy_mode,
                "auxiliary_cycle_status": self._cycle_length_output2_status,
                "auxiliary_cycle_value": self._cycle_length_output2_value,
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
                "icon_type": self.icon_type,
                "temp_display_value": self._temp_display_value,
                "second_display": self._display2,
                "keypad": self._keypad,
                "backlight": self._backlight,
                "time_format": self._time_format,
                "temperature_format": self._temperature_format,
                "setpoint_max": self._max_temp,
                "setpoint_min": self._min_temp,
                "cycle_length_output": self._load1,
                "cycle_length_output_2": self._load2,
                "cycle_length_output_status": self._load1_status,
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
    async def async_update(self) -> None:
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
            #            _LOGGER.debug(
            #                "Updated attributes for %s: %s",
            #                self._name,
            #                UPDATE_ATTRIBUTES + DOUBLE_ATTRIBUTES,
            #            )
            device_data = await self._client.async_get_device_attributes(
                self._id, UPDATE_ATTRIBUTES + DOUBLE_ATTRIBUTES
            )
            neviweb_status = await self._client.async_get_neviweb_status(self._location)
            end = time.time()
            elapsed = round(end - start, 3)
            _LOGGER.debug("Updating %s (%s sec): %s", self._name, elapsed, device_data)
            _LOGGER.debug("Neviweb status = %s", neviweb_status)

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
                    self._backlight = backlight_to_ha(device_data[ATTR_BACKLIGHT])
                    if ATTR_CYCLE_LENGTH in device_data:
                        self._cycle_length = neviweb_to_ha(device_data[ATTR_CYCLE_LENGTH])
                    if ATTR_RSSI in device_data:
                        self._rssi = device_data[ATTR_RSSI]
                    self._operation_mode = device_data[ATTR_SYSTEM_MODE]
                    self._wattage = device_data[ATTR_WATTAGE]
                    self.async_write_ha_state()
                elif device_data["errorCode"] == "ReadTimeout":
                    _LOGGER.warning(
                        "A timeout occur during data update. Device %s do not respond. Check your network... (%s)",
                        self._name,
                        device_data,
                    )
                else:
                    _LOGGER.warning(
                        "Error in updating device %s: (%s)",
                        self._name,
                        device_data,
                    )
            else:
                await self.async_log_error(device_data["error"]["code"])
            self._occupancy_mode = neviweb_status[ATTR_OCCUPANCY]
            await self.async_do_stat(start)
            await self.async_get_sensor_error_code()
            await self.async_get_weather()
        else:
            if time.time() - self._snooze > SNOOZE_TIME:
                self._active = True
                if self._notify == "notification" or self._notify == "both":
                    await async_notify_once_or_update(
                        self.hass,
                        "Warning: Neviweb Device update restarted for " + self._name + ", Sku: " + self._sku,
                        title=f"Neviweb130 integration {VERSION}",
                        notification_id=f"neviweb130_update_restarted",
                    )

    @property
    @override
    def extra_state_attributes(self)  -> Mapping[str, Any]:
        """Return the state attributes."""
        data = {}
        data.update(
            {
                "wattage": self._wattage,
                "cycle_length": self._cycle_length,
                "neviweb_occupancy_mode": self._occupancy_mode,
                "error_code": self._error_code,
                "heat_level": self._heat_level,
                "pi_heating_demand": self._heat_level,
                "icon_type": self.icon_type,
                "temp_display_value": self._temp_display_value,
                "second_display": self._display2,
                "keypad": self._keypad,
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

    def __init__(self, data, device_info, name, sku, firmware, location, coordinator, entry):
        """Initialize."""
        super().__init__(data, device_info, name, sku, firmware, location, coordinator, entry)
        self._early_start = "off"
        self._heat_source_type = None
        self._load1 = 0
        self._room_temp_error = None
        self._room_temp_error = None
        self._target_temp_away = None
        self._temp_display_status = None

    @override
    async def async_update(self) -> None:
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
            device_data = await self._client.async_get_device_attributes(self._id, UPDATE_ATTRIBUTES + WIFI_ATTRIBUTES)
            neviweb_status = await self._client.async_get_neviweb_status(self._location)
            end = time.time()
            elapsed = round(end - start, 3)
            _LOGGER.debug("Updating %s (%s sec): %s", self._name, elapsed, device_data)
            _LOGGER.debug("Neviweb status = %s", neviweb_status)

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
                        self._drstatus_onOff = device_data[ATTR_DRSTATUS]["onOff"]
                    self._heat_level = device_data[ATTR_OUTPUT_PERCENT_DISPLAY]["percent"]
                    self._heat_source_type = device_data[ATTR_OUTPUT_PERCENT_DISPLAY]["sourceType"]
                    self._operation_mode = device_data[ATTR_SETPOINT_MODE]
                    self._occupancy = device_data[ATTR_OCCUPANCY]
                    self._keypad = lock_to_ha(device_data[ATTR_WIFI_KEYPAD])
                    self._rssi = device_data[ATTR_WIFI]
                    self._backlight = backlight_to_ha(device_data[ATTR_BACKLIGHT_AUTO_DIM])
                    self._early_start = device_data[ATTR_EARLY_START]
                    self._target_temp_away = device_data[ATTR_ROOM_SETPOINT_AWAY]
                    self._load1 = device_data[ATTR_FLOOR_OUTPUT1]
                    if ATTR_WIFI_WATTAGE in device_data:
                        self._wattage = device_data[ATTR_WIFI_WATTAGE]["value"]
                    if ATTR_CYCLE_LENGTH in device_data:
                        self._cycle_length = neviweb_to_ha(device_data[ATTR_CYCLE_LENGTH])
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
                    _LOGGER.warning(
                        "Error in updating device %s: (%s)",
                        self._name,
                        device_data,
                    )
            else:
                await self.async_log_error(device_data["error"]["code"])
            self._occupancy_mode = neviweb_status[ATTR_OCCUPANCY]
            await self.async_do_stat(start)
            await self.async_get_sensor_error_code()
            await self.async_get_weather()
        else:
            if time.time() - self._snooze > SNOOZE_TIME:
                self._active = True
                if self._notify == "notification" or self._notify == "both":
                    await async_notify_once_or_update(
                        self.hass,
                        "Warning: Neviweb Device update restarted for " + self._name + ", Sku: " + self._sku,
                        title=f"Neviweb130 integration {VERSION}",
                        notification_id=f"neviweb130_update_restarted",
                    )

    @property
    @override
    def extra_state_attributes(self)  -> Mapping[str, Any]:
        """Return the state attributes."""
        data = {}
        data.update(
            {
                "wattage": self._wattage,
                "occupancy": self._occupancy,
                "neviweb_occupancy_mode": self._occupancy_mode,
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
                "icon_type": self.icon_type,
                "temp_display_value": self._temp_display_value,
                "second_display": self._display2,
                "keypad": self._keypad,
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
                "total_kwh_count": self._total_kwh_count,
                "monthly_kwh_count": self._monthly_kwh_count,
                "daily_kwh_count": self._daily_kwh_count,
                "hourly_kwh_count": self._hourly_kwh_count,
                "hourly_kwh": self._hour_kwh,
                "daily_kwh": self._today_kwh,
                "monthly_kwh": self._month_kwh,
                "last_energy_stat_update": self._mark,
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
    """Implementation of Neviweb TH1133WF, TH1133CR, TH1134WF, TH1134CR and THEWF01 thermostats."""

    _attr_precision = 1.0
    _attr_target_temperature_step = 1.0

    def __init__(self, data, device_info, name, sku, firmware, location, coordinator, entry):
        """Initialize."""
        super().__init__(data, device_info, name, sku, firmware, location, coordinator, entry)
        self._early_start = "off"
        self._heat_source_type = None
        self._load1 = 0
        self._room_temp_error = None
        self._target_temp_away = None
        self._temp_display_status = None
        self._interlock_id = None
        self._interlock_partner = None

    @override
    async def async_update(self) -> None:
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
            device_data = await self._client.async_get_device_attributes(
                self._id, UPDATE_LITE_ATTRIBUTES + LITE_ATTRIBUTES
            )
            neviweb_status = await self._client.async_get_neviweb_status(self._location)
            end = time.time()
            elapsed = round(end - start, 3)
            _LOGGER.debug("Updating %s (%s sec): %s", self._name, elapsed, device_data)
            _LOGGER.debug("Neviweb status = %s", neviweb_status)

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
                        self._drstatus_onOff = device_data[ATTR_DRSTATUS]["onOff"]
                    self._heat_level = device_data[ATTR_OUTPUT_PERCENT_DISPLAY]["percent"]
                    self._heat_source_type = device_data[ATTR_OUTPUT_PERCENT_DISPLAY]["sourceType"]
                    self._operation_mode = device_data[ATTR_SETPOINT_MODE]
                    self._occupancy = device_data[ATTR_OCCUPANCY]
                    self._keypad = lock_to_ha(device_data[ATTR_WIFI_KEYPAD])
                    self._rssi = device_data[ATTR_WIFI]
                    self._backlight = backlight_to_ha(device_data[ATTR_BACKLIGHT_AUTO_DIM])
                    self._early_start = device_data[ATTR_EARLY_START]
                    self._target_temp_away = device_data[ATTR_ROOM_SETPOINT_AWAY]
                    self._load1 = device_data[ATTR_OUTPUT1]
                    if ATTR_CYCLE_LENGTH in device_data:
                        self._wifi_cycle_length = neviweb_to_ha(device_data[ATTR_CYCLE_LENGTH])
                    if ATTR_ROOM_TEMP_DISPLAY in device_data:
                        self._temp_display_status = device_data[ATTR_ROOM_TEMP_DISPLAY]["status"]
                        self._temp_display_value = device_data[ATTR_ROOM_TEMP_DISPLAY]["value"]
                    if ATTR_INTERLOCK_ID in device_data:
                        self._interlock_id = device_data[ATTR_INTERLOCK_ID]
                        self._interlock_partner = device_data[ATTR_INTERLOCK_PARTNER]
                    self.async_write_ha_state()
                elif device_data["errorCode"] == "ReadTimeout":
                    _LOGGER.warning(
                        "A timeout occur during data update. Device %s do not respond. Check your network... (%s)",
                        self._name,
                        device_data,
                    )
                else:
                    _LOGGER.warning(
                        "Error in updating device %s: (%s)",
                        self._name,
                        device_data,
                    )
            else:
                await self.async_log_error(device_data["error"]["code"])
            self._occupancy_mode = neviweb_status[ATTR_OCCUPANCY]
            if (
                self._sku != "TH1133WF"
                and self._sku != "TH1133CR"
                and self._sku != "TH1134WF"
                and self._sku != "TH1134CR"
            ):
                await self.async_do_stat(start)
            await self.async_get_sensor_error_code()
            await self.async_get_weather()
        else:
            if time.time() - self._snooze > SNOOZE_TIME:
                self._active = True
                if self._notify == "notification" or self._notify == "both":
                    await async_notify_once_or_update(
                        self.hass,
                        "Warning: Neviweb Device update restarted for " + self._name + ", Sku: " + self._sku,
                        title=f"Neviweb130 integration {VERSION}",
                        notification_id=f"neviweb130_update_restarted",
                    )

    @property
    @override
    def extra_state_attributes(self)  -> Mapping[str, Any]:
        """Return the state attributes."""
        data = {}
        data.update(
            {
                "occupancy": self._occupancy,
                "neviweb_occupancy_mode": self._occupancy_mode,
                "temp_display_status": self._temp_display_status,
                "temp_display_error": self._room_temp_error,
                "source_type": self._heat_source_type,
                "early_start": self._early_start,
                "setpoint_away": self._target_temp_away,
                "load_watt_1": self._load1,
                "cycle_length": self._wifi_cycle_length,
                "error_code": self._error_code,
                "heat_level": self._heat_level,
                "pi_heating_demand": self._heat_level,
                "icon_type": self.icon_type,
                "temp_display_value": self._temp_display_value,
                "keypad": self._keypad,
                "backlight": self._backlight,
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
                "total_kwh_count": self._total_kwh_count,
                "monthly_kwh_count": self._monthly_kwh_count,
                "daily_kwh_count": self._daily_kwh_count,
                "hourly_kwh_count": self._hourly_kwh_count,
                "hourly_kwh": self._hour_kwh,
                "daily_kwh": self._today_kwh,
                "monthly_kwh": self._month_kwh,
                "last_energy_stat_update": self._mark,
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

    def __init__(self, data, device_info, name, sku, firmware, location, coordinator, entry):
        """Initialize."""
        super().__init__(data, device_info, name, sku, firmware, location, coordinator, entry)
        self._early_start = "off"
        self._heat_source_type = None
        self._load1 = 0
        self._room_temp_error = None
        self._target_temp_away = None
        self._temp_display_status = None

    @override
    async def async_update(self) -> None:
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
                    self._keypad = lock_to_ha(device_data[ATTR_WIFI_KEYPAD])
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
            await self.async_do_stat(start)
            await self.async_get_sensor_error_code()
            await self.async_get_weather()
        else:
            if time.time() - self._snooze > SNOOZE_TIME:
                self._active = True
                if NOTIFY == "notification" or NOTIFY == "both":
                    await async_notify_once_or_update(
                        self.hass,
                        "Warning: Neviweb Device update restarted for " + self._name + ", Sku: " + self._sku,
                        title=f"Neviweb130 integration {VERSION}",
                        notification_id=f"neviweb130_update_restarted",
                    )

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
                "icon_type": self.icon_type,
                "temp_display_value": self._temp_display_value,
                "keypad": self._keypad,
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

    def __init__(self, data, device_info, name, sku, firmware, location, coordinator, entry):
        """Initialize."""
        super().__init__(data, device_info, name, sku, firmware, location, coordinator, entry)
        self._early_start = "off"
        self._floor_air_limit_status = None
        self._floor_max_status = "off"
        self._floor_min_status = "off"
        self._heat_source_type = None
        self._load1 = 0
        self._load2 = 0
        self._pump_duration_value = None
        self._room_temp_error = None
        self._target_temp_away = None
        self._temp_display_status = None

    @override
    async def async_update(self) -> None:
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
            device_data = await self._client.async_get_device_attributes(
                self._id, UPDATE_ATTRIBUTES + LOW_WIFI_ATTRIBUTES
            )
            neviweb_status = await self._client.async_get_neviweb_status(self._location)
            end = time.time()
            elapsed = round(end - start, 3)
            _LOGGER.debug("Updating %s (%s sec): %s", self._name, elapsed, device_data)
            _LOGGER.debug("Neviweb status = %s", neviweb_status)

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
                    self._keypad = lock_to_ha(device_data[ATTR_WIFI_KEYPAD])
                    self._rssi = device_data[ATTR_WIFI]
                    self._wattage = device_data[ATTR_WIFI_WATTAGE]
                    self._backlight = backlight_to_ha(device_data[ATTR_BACKLIGHT_AUTO_DIM])
                    self._early_start = device_data[ATTR_EARLY_START]
                    self._target_temp_away = device_data[ATTR_ROOM_SETPOINT_AWAY]
                    self._load1 = device_data[ATTR_FLOOR_OUTPUT1]
                    self._floor_mode = device_data[ATTR_FLOOR_MODE]
                    self._floor_sensor_type = device_data[ATTR_FLOOR_SENSOR]
                    self._lv_aux_cycle_length = neviweb_to_ha(device_data[ATTR_AUX_CYCLE_LENGTH])
                    self._lv_cycle_length = neviweb_to_ha(device_data[ATTR_CYCLE_LENGTH])
                    self._floor_max = device_data[ATTR_FLOOR_MAX]["value"]
                    self._floor_max_status = device_data[ATTR_FLOOR_MAX]["status"]
                    self._floor_min = device_data[ATTR_FLOOR_MIN]["value"]
                    self._floor_min_status = device_data[ATTR_FLOOR_MIN]["status"]
                    self._floor_air_limit = device_data[ATTR_FLOOR_AIR_LIMIT]["value"]
                    self._floor_air_limit_status = device_data[ATTR_FLOOR_AIR_LIMIT]["status"]
                    self._pump_protec_status = device_data[ATTR_PUMP_PROTEC]["status"]
                    if device_data[ATTR_PUMP_PROTEC]["status"] == "on":
                        self._pump_protec_period = device_data[ATTR_PUMP_PROTEC]["frequency"]
                        self._pump_protec_duration = device_data[ATTR_PUMP_PROTEC]["duration"]
                    if ATTR_PUMP_PROTEC_DURATION in device_data:
                        self._pump_duration_value = device_data[ATTR_PUMP_PROTEC_DURATION]
                    if ATTR_FLOOR_AUX in device_data:
                        self._em_heat = device_data[ATTR_FLOOR_AUX]
                    self._load2 = device_data[ATTR_FLOOR_OUTPUT2]
                    self.async_write_ha_state()
                elif device_data["errorCode"] == "ReadTimeout":
                    _LOGGER.warning(
                        "A timeout occur during data update. Device %s do not respond. Check your network... (%s)",
                        self._name,
                        device_data,
                    )
                else:
                    _LOGGER.warning(
                        "Error in updating device %s: (%s)",
                        self._name,
                        device_data,
                    )
            else:
                await self.async_log_error(device_data["error"]["code"])
            self._occupancy_mode = neviweb_status[ATTR_OCCUPANCY]
            await self.async_do_stat(start)
            await self.async_get_sensor_error_code()
            await self.async_get_weather()
        else:
            if time.time() - self._snooze > SNOOZE_TIME:
                self._active = True
                if self._notify == "notification" or self._notify == "both":
                    await async_notify_once_or_update(
                        self.hass,
                        "Warning: Neviweb Device update restarted for " + self._name + ", Sku: " + self._sku,
                        title=f"Neviweb130 integration {VERSION}",
                        notification_id=f"neviweb130_update_restarted",
                    )

    @property
    @override
    def extra_state_attributes(self) -> Mapping[str, Any]:
        """Return the state attributes."""
        data = {}
        data.update(
            {
                "sensor_mode": self._floor_mode,
                "neviweb_occupancy_mode": self._occupancy_mode,
                "floor_sensor_type": self._floor_sensor_type,
                "temp_display_error": self._room_temp_error,
                "load_watt": self._wattage,
                "auxiliary_cycle_length": self._lv_aux_cycle_length,
                "cycle_length": self._lv_cycle_length,
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
                "icon_type": self.icon_type,
                "keypad": self._keypad,
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
    """Implementation of Neviweb TH1300WF, TH1325WF, TH1310WF, SRM40 and True Comfort thermostat."""

    def __init__(self, data, device_info, name, sku, firmware, location, coordinator, entry):
        """Initialize."""
        super().__init__(data, device_info, name, sku, firmware, location, coordinator, entry)
        self._early_start = "off"
        self._floor_air_limit_status = None
        self._floor_max_status = "off"
        self._floor_min_status = "off"
        self._gfci_alert = None
        self._gfci_status = None
        self._heat_source_type = None
        self._load1 = 0
        self._load2 = 0
        self._room_temp_error = None
        self._target_temp_away = None

    @override
    async def async_update(self) -> None:
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
            device_data = await self._client.async_get_device_attributes(
                self._id, UPDATE_ATTRIBUTES + WIFI_FLOOR_ATTRIBUTES
            )
            neviweb_status = await self._client.async_get_neviweb_status(self._location)
            end = time.time()
            elapsed = round(end - start, 3)
            _LOGGER.debug("Updating %s (%s sec): %s", self._name, elapsed, device_data)
            _LOGGER.debug("Neviweb status = %s", neviweb_status)

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
                    self._heat_level = device_data[ATTR_OUTPUT_PERCENT_DISPLAY]["percent"]
                    self._heat_source_type = device_data[ATTR_OUTPUT_PERCENT_DISPLAY]["sourceType"]
                    self._operation_mode = device_data[ATTR_SETPOINT_MODE]
                    self._occupancy = device_data[ATTR_OCCUPANCY]
                    self._keypad = lock_to_ha(device_data[ATTR_WIFI_KEYPAD])
                    self._rssi = device_data[ATTR_WIFI]
                    self._wattage = device_data[ATTR_WIFI_WATTAGE]
                    self._backlight = backlight_to_ha(device_data[ATTR_BACKLIGHT_AUTO_DIM])
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
                    self.async_write_ha_state()
                elif device_data["errorCode"] == "ReadTimeout":
                    _LOGGER.warning(
                        "A timeout occur during data update. Device %s do not respond. Check your network... (%s)",
                        self._name,
                        device_data,
                    )
                else:
                    _LOGGER.warning(
                        "Error in updating device %s: (%s)",
                        self._name,
                        device_data,
                    )
            else:
                await self.async_log_error(device_data["error"]["code"])
            self._occupancy_mode = neviweb_status[ATTR_OCCUPANCY]
            if self._sku != "FLP55" and self._sku != "PS120_240WF":
                await self.async_do_stat(start)
            await self.async_get_sensor_error_code()
            await self.async_get_weather()
        else:
            if time.time() - self._snooze > SNOOZE_TIME:
                self._active = True
                if self._notify == "notification" or self._notify == "both":
                    await async_notify_once_or_update(
                        self.hass,
                        "Warning: Neviweb Device update restarted for " + self._name + ", Sku: " + self._sku,
                        title=f"Neviweb130 integration {VERSION}",
                        notification_id=f"neviweb130_update_restarted",
                    )

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
                "temp_display_error": self._room_temp_error,
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
                "icon_type": self.icon_type,
                "second_display": self._display2,
                "keypad": self._keypad,
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

    def __init__(self, data, device_info, name, sku, firmware, location, coordinator, entry):
        """Initialize."""
        super().__init__(data, device_info, name, sku, firmware, location, coordinator, entry)
        self._cool_max = 30
        self._cool_min = 16
        self._display_cap = None
        self._fan_cap = None
        self._hc_device = None
        self._model = None
        self._sound_cap = None

    @override
    async def async_update(self) -> None:
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
            #  _LOGGER.debug("Updated attributes for %s: %s", self._name, UPDATE_ATTRIBUTES + HC_ATTRIBUTES)
            device_data = await self._client.async_get_device_attributes(self._id, UPDATE_ATTRIBUTES + HC_ATTRIBUTES)
            neviweb_status = await self._client.async_get_neviweb_status(self._location)
            end = time.time()
            elapsed = round(end - start, 3)
            _LOGGER.debug("Updating %s (%s sec): %s", self._name, elapsed, device_data)
            _LOGGER.debug("Neviweb status = %s", neviweb_status)

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
                    self._backlight = backlight_to_ha(device_data[ATTR_BACKLIGHT_AUTO_DIM])
                    if ATTR_RSSI in device_data:
                        self._rssi = device_data[ATTR_RSSI]
                    self._wattage = device_data[ATTR_WATTAGE]
                    self._cycle_length = neviweb_to_ha(device_data[ATTR_CYCLE_LENGTH])
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
                    self._heat_lockout_temp = device_data[ATTR_HEAT_LOCK_TEMP]
                    self._cool_lockout_temp = device_data[ATTR_COOL_LOCK_TEMP]
                    self._avail_mode = device_data[ATTR_AVAIL_MODE]
                    self._display_cap = device_data[ATTR_DISPLAY_CAP]
                    self._display_conf = device_data[ATTR_DISPLAY_CONF]
                    self._sound_cap = device_data[ATTR_SOUND_CAP]
                    self._sound_conf = device_data[ATTR_SOUND_CONF]
                    self.async_write_ha_state()
                elif device_data["errorCode"] == "ReadTimeout":
                    _LOGGER.warning(
                        "A timeout occur during data update. Device %s do not respond. Check your network... (%s)",
                        self._name,
                        device_data,
                    )
                else:
                    _LOGGER.warning(
                        "Error in updating device %s: (%s)",
                        self._name,
                        device_data,
                    )
            else:
                await self.async_log_error(device_data["error"]["code"])
            self._occupancy_mode = neviweb_status[ATTR_OCCUPANCY]
            await self.async_do_stat(start)
            await self.async_get_sensor_error_code()
            await self.async_get_weather()
        else:
            if time.time() - self._snooze > SNOOZE_TIME:
                self._active = True
                if self._notify == "notification" or self._notify == "both":
                    await async_notify_once_or_update(
                        self.hass,
                        "Warning: Neviweb Device update restarted for " + self._name + ", Sku: " + self._sku,
                        title=f"Neviweb130 integration {VERSION}",
                        notification_id=f"neviweb130_update_restarted",
                    )

    @property
    def hc_second_display(self):
        return self._display2

    @property
    @override
    def extra_state_attributes(self) -> Mapping[str, Any]:
        """Return the state attributes."""
        data = {}
        data.update(
            {
                "wattage": self._wattage,
                "error_code": self._error_code,
                "neviweb_occupancy_mode": self._occupancy_mode,
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
                "fan_swing_capability_vertical": extract_capability_full(self._fan_swing_cap_vert),
                "fan_swing_capability_horizontal": extract_capability_full(self._fan_swing_cap_horiz),
                "display_conf": self._display_conf,
                "display_capability": extract_capability(self._display_cap),
                "sound_conf": self._sound_conf,
                "sound_capability": extract_capability(self._sound_cap),
                "balance_point": self._balance_pt,
                "heat_lock_temp": self._heat_lockout_temp,
                "cool_lock_temp": self._cool_lockout_temp,
                "available_mode": self._avail_mode,
                "heat_level": self._heat_level,
                "pi_heating_demand": self._heat_level,
                "icon_type": self.icon_type,
                "temp_display_value": self._temp_display_value,
                "second_display": self._display2,
                "keypad": self._keypad,
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

    def __init__(self, data, device_info, name, sku, firmware, location, coordinator, entry):
        """Initialize."""
        super().__init__(data, device_info, name, sku, firmware, location, coordinator, entry)
        self._cool_max = 30
        self._cool_min = 16
        self._display_cap = None
        self._fan_cap = None
        self._model = None
        self._sound_cap = None

    @override
    async def async_update(self) -> None:
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

            device_data = await self._client.async_get_device_attributes(
                self._id,
                UPDATE_HP_ATTRIBUTES + HP_ATTRIBUTES + NEW_HP_ATTRIBUTES,
            )
            neviweb_status = await self._client.async_get_neviweb_status(self._location)
            end = time.time()
            elapsed = round(end - start, 3)
            _LOGGER.debug("Updating %s (%s sec): %s", self._name, elapsed, device_data)
            _LOGGER.debug("Neviweb status = %s", neviweb_status)

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
                        self._heat_lockout_temp = device_data[ATTR_HEAT_LOCK_TEMP]
                        self._cool_lockout_temp = device_data[ATTR_COOL_LOCK_TEMP]
                    if ATTR_BALANCE_PT_TEMP_LOW in device_data:
                        self._balance_pt_low = device_data[ATTR_BALANCE_PT_TEMP_LOW]
                        self._balance_pt_high = device_data[ATTR_BALANCE_PT_TEMP_HIGH]
                    if ATTR_DISPLAY_CONF in device_data:
                        self._display_conf = device_data[ATTR_DISPLAY_CONF]
                        self._display_cap = device_data[ATTR_DISPLAY_CAP]
                        self._sound_conf = device_data[ATTR_SOUND_CONF]
                        self._sound_cap = device_data[ATTR_SOUND_CAP]
                    self.async_write_ha_state()
                elif device_data["errorCode"] == "ReadTimeout":
                    _LOGGER.warning(
                        "A timeout occur during data update. Device %s do not respond. Check your network... (%s)",
                        self._name,
                        device_data,
                    )
                else:
                    _LOGGER.warning(
                        "Error in updating device %s: (%s)",
                        self._name,
                        device_data,
                    )
            else:
                await self.async_log_error(device_data["error"]["code"])
            self._occupancy_mode = neviweb_status[ATTR_OCCUPANCY]
            await self.async_get_sensor_error_code()
            await self.async_get_weather()
        else:
            if time.time() - self._snooze > SNOOZE_TIME:
                self._active = True
                if self._notify == "notification" or self._notify == "both":
                    await async_notify_once_or_update(
                        self.hass,
                        "Warning: Neviweb Device update restarted for " + self._name + ", Sku: " + self._sku,
                        title=f"Neviweb130 integration {VERSION}",
                        notification_id=f"neviweb130_update_restarted",
                    )

    @property
    @override
    def extra_state_attributes(self) -> Mapping[str, Any]:
        """Return the state attributes."""
        data = {}
        data.update(
            {
                "heat_pump_model": self._model,
                "error_code": self._error_code,
                "neviweb_occupancy_mode": self._occupancy_mode,
                "operation modes": self._operation_mode,
                "cool setpoint min": self._cool_min,
                "cool setpoint max": self._cool_max,
                "setpoint_max": self._max_temp,
                "setpoint_min": self._min_temp,
                "temperature_format": self._temperature_format,
                "keypad": self._keypad,
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
                    #  "min_heat_pump_limit_temp": self._balance_pt_low,
                    #  "max_heat_pump_limit_temp": self._balance_pt_high,
                    "heat_lock_temp": self._heat_lockout_temp,
                    "cool_lock_temp": self._cool_lockout_temp,
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


class Neviweb130WifiHPThermostat(Neviweb130Thermostat):
    """Implementation of Neviweb HP6000WF-MA and HP6000WF-GE Wi-Fi heat pump interfaces thermostats."""

    def __init__(self, data, device_info, name, sku, firmware, location, coordinator, entry):
        """Initialize."""
        super().__init__(data, device_info, name, sku, firmware, location, coordinator, entry)
        self._cool_max = 31
        self._cool_min = 16
        self._cool_target_temp_away = None
        self._display_cap = None
        self._fan_cap = None
        self._heat_cool = None
        self._interlock_id = None
        self._system_mode_avail = None
        self._model = None
        self._room_temp_error = None
        self._sound_cap = None

    @override
    async def async_update(self) -> None:
        if self._active:
            WHP_ATTRIBUTES = [
                ATTR_BALANCE_PT,
                ATTR_COOL_LOCK_TEMP,
                ATTR_COOL_SETPOINT,
                ATTR_COOL_SETPOINT_AWAY,
                ATTR_DISPLAY_CAP,
                ATTR_DISPLAY_CONF,
                ATTR_DRSETPOINT,
                ATTR_DRSTATUS,
                ATTR_FAN_CAP,
                ATTR_FAN_SPEED,
                ATTR_FAN_SWING_CAP,
                ATTR_FAN_SWING_CAP_HORIZ,
                ATTR_FAN_SWING_CAP_VERT,
                ATTR_FAN_SWING_HORIZ,
                ATTR_FAN_SWING_VERT,
                ATTR_HEAT_COOL,
                ATTR_HEAT_LOCK_TEMP,
                ATTR_INTERLOCK_ID,
                ATTR_MODEL,
                ATTR_OCCUPANCY,
                ATTR_ROOM_SETPOINT_AWAY,
                ATTR_ROOM_TEMP_DISPLAY,
                ATTR_SETPOINT_MODE,
                ATTR_SOUND_CAP,
                ATTR_SOUND_CONF,
                ATTR_SYSTEM_MODE_AVAIL,
                ATTR_WIFI,
                ATTR_WIFI_KEYPAD,
            ]

            """Get the latest data from Neviweb and update the state."""
            start = time.time()
            _LOGGER.debug("Updated attributes for %s: %s", self._name, UPDATE_HP_ATTRIBUTES + WHP_ATTRIBUTES)
            device_data = await self._client.async_get_device_attributes(self._id, UPDATE_HP_ATTRIBUTES + WHP_ATTRIBUTES)
            neviweb_status = await self._client.async_get_neviweb_status(self._location)
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
                    if self._room_temp_error is not None:
                        await async_notify_critical(
                            self.hass,
                            f"Warning: Neviweb Device temperature error code detected: {self._room_temp_error} "
                            f"for device: {self._name}, ID: {self._id}, Sku: {self._sku}",
                            title=f"Neviweb130 integration {VERSION}",
                            notification_id=f"neviweb130_sensor_error",
                        )
                    self._operation_mode = device_data[ATTR_SETPOINT_MODE]
                    self._heat_cool = neviweb_to_ha_mode(device_data[ATTR_HEAT_COOL])
                    self._target_temp = (
                        float(device_data[ATTR_COOL_SETPOINT])
                        if self._heat_cool == "cool"
                        else float(device_data[ATTR_ROOM_SETPOINT])
                    )
                    self._temp_display_value = device_data[ATTR_ROOM_TEMP_DISPLAY]["value"]
                    self._temp_display_status = device_data[ATTR_ROOM_TEMP_DISPLAY]["status"]
                    self._min_temp = device_data[ATTR_ROOM_SETPOINT_MIN]
                    self._max_temp = device_data[ATTR_ROOM_SETPOINT_MAX]
                    self._target_temp_away = device_data[ATTR_ROOM_SETPOINT_AWAY]
                    self._target_cool = device_data[ATTR_COOL_SETPOINT]
                    self._cool_min = device_data[ATTR_COOL_SETPOINT_MIN]
                    self._cool_max = device_data[ATTR_COOL_SETPOINT_MAX]
                    self._cool_target_temp_away = device_data[ATTR_COOL_SETPOINT_AWAY]
                    self._temperature_format = device_data[ATTR_TEMP]
                    if ATTR_OCCUPANCY in device_data:
                        self._occupancy = device_data[ATTR_OCCUPANCY]
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
                        self._drstatus_onoff = device_data[ATTR_DRSTATUS]["onOff"]
                    self._keypad = lock_to_ha(device_data[ATTR_WIFI_KEYPAD])
                    if ATTR_WIFI in device_data:
                        self._rssi = device_data[ATTR_WIFI]
                    self._fan_speed = neviweb_to_ha_fan(device_data[ATTR_FAN_SPEED], self._device_model)
                    self._fan_swing_vert = device_data[ATTR_FAN_SWING_VERT]
                    self._fan_cap = device_data[ATTR_FAN_CAP]
                    self._system_mode_avail = device_data[ATTR_SYSTEM_MODE_AVAIL]
                    if ATTR_FAN_SWING_HORIZ in device_data:
                        self._fan_swing_horiz = device_data[ATTR_FAN_SWING_HORIZ]
                        self._fan_swing_cap = device_data[ATTR_FAN_SWING_CAP]
                        self._fan_swing_cap_horiz = device_data[ATTR_FAN_SWING_CAP_HORIZ]
                        self._fan_swing_cap_vert = device_data[ATTR_FAN_SWING_CAP_VERT]
                        self._balance_pt = device_data[ATTR_BALANCE_PT]
                        self._heat_lockout_temp = device_data[ATTR_HEAT_LOCK_TEMP]
                        self._cool_lockout_temp = device_data[ATTR_COOL_LOCK_TEMP]
                    if ATTR_DISPLAY_CONF in device_data:
                        self._display_conf = device_data[ATTR_DISPLAY_CONF]
                        self._display_cap = device_data[ATTR_DISPLAY_CAP]
                        self._sound_conf = device_data[ATTR_SOUND_CONF]
                        self._sound_cap = device_data[ATTR_SOUND_CAP]
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
                await self.async_log_error(device_data["error"]["code"])
            self._occupancy_mode = neviweb_status[ATTR_OCCUPANCY]
            await self.async_get_sensor_error_code()
            await self.async_get_weather()
        else:
            if time.time() - self._snooze > SNOOZE_TIME:
                self._active = True
                if self._notify == "notification" or self._notify == "both":
                    await async_notify_once_or_update(
                        self.hass,
                        "Warning: Neviweb Device update restarted for " + self._name + ", Sku: " + self._sku,
                        title=f"Neviweb130 integration {VERSION}",
                        notification_id=f"neviweb130_update_restarted",
                    )

    @property
    @override
    def is_on(self) -> bool:
        """Return True if mode = HVACMode.HEAT or HVACMode.COOL."""
        return (
            self._heat_cool == HVACMode.HEAT
            or self._heat_cool == HVACMode.COOL
            or self._heat_cool == HVACMode.HEAT_COOL
            or self._heat_cool == HVACMode.DRY
            or self._heat_cool == HVACMode.FAN_ONLY
        )

    @property
    @override
    def hvac_mode(self) -> HVACMode:
        """Return current HVAC mode."""
        mode = self._heat_cool

        # If Neviweb return an unknown mode
        if mode not in (
            HVACMode.OFF,
            HVACMode.HEAT_COOL,
            HVACMode.COOL,
            HVACMode.DRY,
            HVACMode.FAN_ONLY,
            HVACMode.HEAT,
        ):
            return HVACMode.HEAT

        return mode

    @property
    @override
    def hvac_action(self) -> HVACAction | None:
        """Return current HVAC action."""
        mode = self.hvac_mode
        temp = self.current_temperature

        if temp is None:
            return HVACAction.IDLE

        if mode == HVACMode.OFF:
            return HVACAction.OFF
        if mode == HVACMode.COOL:
            if temp > self.target_temperature_high:
                return HVACAction.COOLING
            return HVACAction.IDLE
        if mode == HVACMode.HEAT:
            if temp < self.target_temperature_low:
                return HVACAction.HEATING
            return HVACAction.IDLE
        if mode == HVACMode.DRY:
            return HVACAction.DRYING
        if mode == HVACMode.FAN_ONLY:
            return HVACAction.FAN
        if mode == HVACMode.HEAT_COOL:
            if temp < self.target_temperature_low:
                return HVACAction.HEATING
            if temp > self.target_temperature_high:
                return HVACAction.COOLING
            return HVACAction.IDLE

        return HVACAction.IDLE

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

        # Default temp
        temp = self._target_temp

        # If HVACMode.heat, apply target_temperature_low
        if self.hvac_mode == HVACMode.HEAT and self._target_temp is not None:
            temp = self.target_temperature_low

        # If HVACMode.cool, apply target_temperature_high
        elif self.hvac_mode == HVACMode.COOL:
            temp = self.target_temperature_high

        # If HVACMode.heatCool, apply target_temperature_low
        elif self.hvac_mode in (HVACMode.HEAT_COOL, HVACMode.AUTO):
            temp = self.target_temperature_low

        # Other modes
        else:
            temp = self._target_temp

        # if temp is None → return None
        if temp is None:
            return None

        # Apply limit
        if temp < self._min_temp:
            return self._min_temp
        if temp > self._max_temp:
            return self._max_temp

        return temp

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

    @override
    async def async_turn_on(self) -> None:
        """Turn the thermostat to HVACMode.HEAT."""
        self._heat_cool = HVACMode.HEAT
        await self._client.async_set_setpoint_mode(self._id, self._heat_cool, self._is_wifi, self._is_WHP)

    @override
    async def async_turn_off(self) -> None:
        """Turn the thermostat to HVACMode.OFF."""
        self._heat_cool = HVACMode.OFF
        await self._client.async_set_setpoint_mode(self._id, self._heat_cool, self._is_wifi, self._is_WHP)

    @override
    async def async_set_hvac_mode(self, hvac_mode: HVACMode) -> None:
        """Set new hvac mode."""
        await self._client.async_set_setpoint_mode(self._id, hvac_mode, self._is_wifi, self._is_WHP)

        self._heat_cool = hvac_mode if hvac_mode != HVACMode.HEAT_COOL else HVACMode.AUTO

        # Reset the preset to the occupancy
        self.async_set_preset_mode(self._occupancy)

        # Wait before update to avoid getting old data from Neviweb
        await self._delayed_refresh()

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
                "temp_display_status": self._temp_display_status,
                "temp_display_value": self._temp_display_value,
                "temp_display_error": self._room_temp_error,
                "keypad": self._keypad,
                "fan_speed": self._fan_speed,
                "fan_swing_vertical": self._fan_swing_vert,
                "fan_capability": self._fan_cap,
                "modes_availables": self._system_mode_avail,
                "heat_pump_limit_temp": self._balance_pt,
                "min_heat_pump_limit_temp": self._balance_pt_low,
                "max_heat_pump_limit_temp": self._balance_pt_high,
                "heat_lock_temp": self._heat_lockout_temp,
                "cool_lock_temp": self._cool_lockout_temp,
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
                "eco_onOff": self._drstatus_onoff,
                "eco_setpoint_status": self._drsetpoint_status,
                "eco_setpoint_delta": self._drsetpoint_value,
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

    def __init__(self, data, device_info, name, sku, firmware, location, coordinator, entry):
        """Initialize."""
        super().__init__(data, device_info, name, sku, firmware, location, coordinator, entry)
        self._accessory_type = "none"
        self._air_curt_activation_temp = None
        self._air_curt_activation_temp = None
        self._air_curt_conf = None
        self._air_curt_max_temp = None
        self._air_ex_min_time_on = None
        self._air_min_time_on = 0
        self._aux_heat_min_time_off = None
        self._aux_heat_min_time_on = None
        self._aux_heat_source_type = None
        self._aux_heat_start_delay = None
        self._aux_interstage_delay = None
        self._aux_interstage_min_delay = None
        self._reversing_valve_polarity = "cooling"
        self._backlight_auto_dim = None
        self._balance_pt = -15
        self._cool_cycle_length = None
        self._cool_interstage_delay = None
        self._cool_interstage_min_delay = None
        self._cool_max = 36
        self._cool_min = 16
        self._cool_min_time_off = None
        self._cool_min_time_on = None
        self._cool_purge_time = 0
        self._cool_target_temp = None
        self._cool_target_temp_away = None
        self._dr_accessory_conf = None
        self._dr_air_curt_conf = None
        self._dr_aux_config = None
        self._dr_fan_speed_conf = None
        self._dual_status = None
        self._fan_filter_remain = None
        self._heat_cool = None
        self._heat_inst_type = None
        self._heat_interstage_delay = None
        self._heat_interstage_min_delay = None
        self._heat_level_source_type = "heating"
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
        self._interlock_hc_mode = None
        self._interlock_id = None
        self._interlock_partner = None
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
        self._preset_before = None
        self._room_temp_error = None
        self._temp_display_status = None
        self._temp_offset_heat = None
        self._wifi_aux_cycle = None
        self._wifi_cycle = None
        for prefix in RUNTIME_PREFIXES:
            init_runtime_attributes(self, TH6_MODES_VALUES, prefix)

    @override
    async def async_update(self) -> None:
        if self._active:
            HC_ATTRIBUTES = [
                ATTR_AUX_CYCLE_LENGTH,
                ATTR_AUX_HEAT_MIN_TIME_ON,
                ATTR_AUX_HEAT_SOURCE_TYPE,
                ATTR_AUX_HEAT_START_DELAY,
                ATTR_BACK_LIGHT,
                ATTR_BACKLIGHT_AUTO_DIM,
                ATTR_BALANCE_PT,
                ATTR_CYCLE_LENGTH,
                ATTR_COOL_CYCLE_LENGTH,
                ATTR_COOL_LOCK_TEMP,
                ATTR_COOL_MIN_TIME_OFF,
                ATTR_COOL_MIN_TIME_ON,
                ATTR_COOL_SETPOINT_AWAY,
                ATTR_DUAL_STATUS,
                ATTR_EARLY_START,
                ATTR_FAN_FILTER_REMAIN,
                ATTR_FAN_SPEED,
                ATTR_HEAT_COOL,
                ATTR_HEATCOOL_SETPOINT_MIN_DELTA,
                ATTR_HEAT_INSTALLATION_TYPE,
                ATTR_HEAT_LOCK_TEMP,
                ATTR_HEAT_SOURCE_TYPE,
                ATTR_HUMIDITY_DISPLAY,
                ATTR_HUMIDITY_SETPOINT,
                ATTR_LANGUAGE,
                ATTR_OCCUPANCY,
                ATTR_OUTPUT_CONNECT_STATE,
                ATTR_REVERSING_VALVE_POLARITY,
                ATTR_ROOM_SETPOINT_AWAY,
                ATTR_SETPOINT_MODE,
                ATTR_TEMP_OFFSET_HEAT,
                ATTR_WIFI_KEYPAD,
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
                ]
            else:
                HC_EXTRA = []
            if self._firmware == "4.2.0" or self._firmware == "4.2.1" or self._firmware == "4.3.0":
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
                    HC_43 = [ATTR_INTERLOCK_ID, ATTR_INTERLOCK_HC_MODE, ATTR_INTERLOCK_PARTNER]
                else:
                    HC_43 = []
            else:
                HC_SPECIAL_FIRMWARE = []
                HC_43 = []

            """Get the latest data from Neviweb and update the state."""
            start = time.time()
            _LOGGER.debug(
                "Updated attributes for %s: %s",
                self._name,
                UPDATE_HEAT_COOL_ATTRIBUTES + HC_ATTRIBUTES + HC_EXTRA + HC_SPECIAL_FIRMWARE + HC_43,
            )
            device_data = await self._client.async_get_device_attributes(
                self._id,
                UPDATE_HEAT_COOL_ATTRIBUTES + HC_ATTRIBUTES + HC_EXTRA + HC_SPECIAL_FIRMWARE + HC_43,
            )
            neviweb_status = await self._client.async_get_neviweb_status(self._location)
            end = time.time()
            elapsed = round(end - start, 3)
            _LOGGER.debug("Updating %s (%s sec): %s", self._name, elapsed, device_data)
            _LOGGER.debug("Neviweb status = %s", neviweb_status)

            if "error" not in device_data:
                if "errorCode" not in device_data:
                    self._cur_temp_before = self._cur_temp
                    self._cur_temp = (
                        float(device_data[ATTR_ROOM_TEMPERATURE]["value"])
                        if device_data[ATTR_ROOM_TEMPERATURE]["value"] is not None
                        else self._cur_temp_before
                    )
                    self._room_temp_error = device_data[ATTR_ROOM_TEMPERATURE]["error"]
                    if self._room_temp_error is not None:
                        await async_notify_critical(
                            self.hass,
                            f"Warning: Neviweb Device temperature error code detected: {self._room_temp_error} "
                            f"for device: {self._name}, ID: {self._id}, Sku: {self._sku}",
                            title=f"Neviweb130 integration {VERSION}",
                            notification_id=f"neviweb130_sensor_error",
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
                    self._fan_speed = device_data[ATTR_FAN_SPEED]
                    self._fan_filter_remain = device_data[ATTR_FAN_FILTER_REMAIN]
                    if ATTR_ROOM_TEMP_DISPLAY in device_data:
                        self._temp_display_status = device_data[ATTR_ROOM_TEMP_DISPLAY]["status"]
                        self._temp_display_value = device_data[ATTR_ROOM_TEMP_DISPLAY]["value"]
                    self._language = device_data[ATTR_LANGUAGE]
                    if ATTR_OCCUPANCY in device_data:
                        self._occupancy = device_data[ATTR_OCCUPANCY]
                    self._keypad = lock_to_ha(device_data[ATTR_WIFI_KEYPAD])
                    if ATTR_BACK_LIGHT in device_data:
                        self._backlight = backlight_to_ha(device_data[ATTR_BACK_LIGHT])
                    self._backlight_auto_dim = device_data[ATTR_BACKLIGHT_AUTO_DIM]
                    self._early_start = device_data[ATTR_EARLY_START]
                    self._target_temp_away = device_data[ATTR_ROOM_SETPOINT_AWAY]
                    self._cool_target_temp_away = device_data[ATTR_COOL_SETPOINT_AWAY]
                    self._reversing_valve_polarity = device_data[ATTR_REVERSING_VALVE_POLARITY]
                    self._heat_lockout_temp = device_data[ATTR_HEAT_LOCK_TEMP]
                    self._cool_lockout_temp = device_data[ATTR_COOL_LOCK_TEMP]
                    self._balance_pt = device_data[ATTR_BALANCE_PT]
                    self._humidity_display = device_data[ATTR_HUMIDITY_DISPLAY]
                    self._humidity_setpoint = device_data[ATTR_HUMIDITY_SETPOINT]
                    self._wifi_cycle = neviweb_to_ha(device_data[ATTR_CYCLE_LENGTH])
                    self._wifi_aux_cycle = neviweb_to_ha(device_data[ATTR_AUX_CYCLE_LENGTH])
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
                    if self._firmware == "4.2.0" or self._firmware == "4.2.1" or self._firmware == "4.3.0":
                        accessory_type = [
                            str(accessory_type).removesuffix("Standalone")
                            for accessory_type, value in device_data[ATTR_ACCESSORY_TYPE].items()
                            if value
                        ]
                        self._accessory_type = accessory_type[0] if accessory_type else "none"
                        self._humidity_setpoint_offset = device_data[ATTR_HUMIDITY_SETPOINT_OFFSET]
                        self._humidity_setpoint_mode = device_data[ATTR_HUMID_SETPOINT_MODE]
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
                            self._interlock_hc_mode = device_data[ATTR_INTERLOCK_HC_MODE]
                            self._interlock_partner = device_data[ATTR_INTERLOCK_PARTNER]
                    self.async_write_ha_state()
                elif device_data["errorCode"] == "ReadTimeout":
                    _LOGGER.warning(
                        "A timeout occurred during data update. Device %s do not respond. Check your network... (%s)",
                        self._name,
                        device_data,
                    )
                else:
                    _LOGGER.warning("Error in updating device %s: (%s)", self._name, device_data)
            else:
                await self.async_log_error(device_data["error"]["code"])
            self._occupancy_mode = neviweb_status[ATTR_OCCUPANCY]
            await self.async_do_stat(start)
            await self.async_get_sensor_error_code()
            await self.async_get_weather()
        else:
            if time.time() - self._snooze > SNOOZE_TIME:
                self._active = True
                if self._notify == "notification" or self._notify == "both":
                    await async_notify_once_or_update(
                        self.hass,
                        "Warning: Neviweb Device update restarted for " + self._name + ", Sku: " + self._sku,
                        title=f"Neviweb130 integration {VERSION}",
                        notification_id=f"neviweb130_update_restarted",
                    )

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
    def hvac_action(self) -> HVACAction | None:
        """Return current HVAC action."""
        if self.hvac_mode == HVACMode.OFF:
            return HVACAction.OFF
        if self._heat_cool == HVACMode.COOL:
            return HVACAction.COOLING
        if self._heat_cool == HVACMode.HEAT:
            if self._heat_level == 0:
                return HVACAction.IDLE
            return HVACAction.HEATING
        if self._heat_cool in (HVACMode.HEAT_COOL, HVACMode.AUTO):
            if self._heat_level_source_type in ("heating", "auxHeating"):
                if self._heat_level == 0:
                    return HVACAction.IDLE
                return HVACAction.HEATING
            if self._heat_level_source_type == "cooling":
                return HVACAction.COOLING
        return None

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

    @property
    def emergency_heat_allowed(self) -> bool:
        return self._em_heat_allowed()

    @override
    async def async_turn_on(self) -> None:
        """Turn the thermostat to HVACMode.HEAT_COOL."""
        self._heat_cool = HVACMode.AUTO
        await self._client.async_set_setpoint_mode(self._id, self._heat_cool, self._is_wifi, self._is_HC)

    @override
    async def async_turn_off(self) -> None:
        """Turn the thermostat to HVACMode.OFF."""
        self._heat_cool = HVACMode.OFF
        await self._client.async_set_setpoint_mode(self._id, self._heat_cool, self._is_wifi, self._is_HC)

    @override
    async def async_set_hvac_mode(self, hvac_mode: HVACMode) -> None:
        """Set new hvac mode."""
        await self._client.async_set_setpoint_mode(self._id, hvac_mode, self._is_wifi, self._is_HC)

        self._heat_cool = hvac_mode if hvac_mode != HVACMode.HEAT_COOL else HVACMode.AUTO

        # Reset the preset to the occupancy
        self.async_set_preset_mode(self._occupancy)

        # Wait before update to avoid getting old data from Neviweb
        await self._delayed_refresh()

    def _em_heat_allowed(self) -> bool:
        """Check if device configuration allow turning on emergency heat. 'addOn' or 'conventional'."""
        if self._heat_installation_type == "conventional":
            return True
        return self._temperature < self._balance_pt

    @override
    async def async_set_preset_mode(self, preset_mode: str) -> None:
        """Activate a preset, including BOOST which maps to emergency heat."""

        # --- BOOST = Emergency Heat ---
        if preset_mode == PRESET_BOOST:
            if not self._em_heat_allowed():
                # Condition not met → cannot activate PRESET_BOOST
                await async_notify_critical(
                    self.hass,
                    "Warning: Cannot activate BOOST (emergency heat) due to device configuration. "
                    f"Condition not met for {self._name}, Sku: {self._sku}",
                    title=f"Neviweb130 integration {VERSION}",
                    notification_id="neviweb130_em_heat_error",
                )
                return

            # Mode Conventional → always allowed
            self._heat_cool = MODE_EM_HEAT
            await self._client.async_set_setpoint_mode(self._id, self._heat_cool, self._is_wifi, self._is_HC)
            return

        # --- Others presets (Home, Away) ---
        self._occupancy = preset_mode
        await self._client.async_set_occupancy_mode(self._id, self._occupancy, self._is_wifi)

        if self._heat_cool == MODE_EM_HEAT:
            self.set_hvac_mode(HVACMode.HEAT)

    @override
    async def async_turn_em_heat_on(self):
        """Set emergency heat 'on' depending on installation type and outdoor temperature."""
        self._preset_before = self.preset_mode

        # --- Mode Conventional : always allowed ---
        if not self._em_heat_allowed():
            # --- Condition not met : cannot turn on em_heat ---
            self.preset_mode = self._preset_before
            await async_notify_critical(
                self.hass,
                "Warning: Cannot activate BOOST (emergency heat) due to device configuration. "
                f"Condition not met for {self._name}, Sku: {self._sku}",
                title=f"Neviweb130 integration {VERSION}",
                notification_id="neviweb130_em_heat_error",
            )
            return

        self._heat_cool = MODE_EM_HEAT
        await self._client.async_set_setpoint_mode(self._id, self._heat_cool, self._is_wifi, self._is_HC)
        self.set_hvac_mode(HVACMode.HEAT)

    @override
    async def async_turn_em_heat_off(self):
        """Set emergency heat off."""
        self._heat_cool = HVACMode.HEAT
        await self._client.async_set_setpoint_mode(self._id, self._heat_cool, self._is_wifi, self._is_HC)
        if self._preset_before in PRESET_HC_MODES:
            self._occupancy = self._preset_before
            await self._client.async_set_occupancy_mode(self._id, self._occupancy, self._is_wifi)

    @override
    async def async_set_temperature(self, **kwargs: Any) -> None:
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
                await self._client.async_set_temperature(self._id, temperature_low)
                self._target_temp = temperature_low

        if temperature_high is not None:
            temperature_high = min(temperature_high, self._cool_max)
            if self.hvac_mode == HVACMode.HEAT_COOL:
                temperature_high = max(temperature_high, self._target_temp + self._heatcool_setpoint_delta)
            else:
                temperature_high = max(temperature_high, self._cool_min)

            if self._target_cool != temperature_high:
                await self._client.async_set_cool_temperature(self._id, temperature_high)
                self._target_cool = temperature_high
        await self._delayed_refresh()

    async def async_set_min_time_on(self, value):
        """Set minimum time the device is on before letting be off again (run-on time)"""
        heat_min_time_on = value.get(ATTR_HEAT_MIN_TIME_ON)
        cool_min_time_on = value.get(ATTR_COOL_MIN_TIME_ON)
        aux_heat_min_time_on = value.get(ATTR_AUX_HEAT_MIN_TIME_ON)
        air_ex_min_time_on = value.get(ATTR_AIR_EX_MIN_TIME_ON)

        if heat_min_time_on is not None:
            await self._client.async_set_heat_min_time_on(self.unique_id, heat_min_time_on)
            self._heat_min_time_on = heat_min_time_on
        if cool_min_time_on is not None:
            await self._client.async_set_cool_min_time_on(self.unique_id, cool_min_time_on)
            self._cool_min_time_on = cool_min_time_on
        if aux_heat_min_time_on is not None:
            await self._client.async_set_aux_heat_min_time_on(self.unique_id, aux_heat_min_time_on)
            self._aux_heat_min_time_on = aux_heat_min_time_on
        if air_ex_min_time_on is not None:
            await self._client.async_set_air_ex_min_time_on(self.unique_id, air_ex_min_time_on)
            self._air_ex_min_time_on = air_ex_min_time_on

    async def async_set_reversing_valve_polarity(self, value):
        """Set minimum time the device is on before letting be off again (run-on time)"""
        polarity = value[ATTR_POLARITY]
        await self._client.async_set_reversing_valve_polarity(self.unique_id, polarity)
        self._reversing_valve_polarity = polarity

    async def async_set_min_time_off(self, value):
        """Set minimum time the device is off before letting it be on again (cooldown time)"""
        heat_min_time_off = value.get(ATTR_HEAT_MIN_TIME_OFF)
        cool_min_time_off = value.get(ATTR_COOL_MIN_TIME_OFF)
        aux_heat_min_time_off = value.get(ATTR_AUX_HEAT_MIN_TIME_OFF)

        if heat_min_time_off is not None:
            await self._client.async_set_heat_min_time_off(self.unique_id, heat_min_time_off)
            self._heat_min_time_off = heat_min_time_off
        if cool_min_time_off is not None:
            await self._client.async_set_cool_min_time_off(self.unique_id, cool_min_time_off)
            self._cool_min_time_off = cool_min_time_off
        if aux_heat_min_time_off is not None:
            await self._client.async_set_aux_heat_min_time_off(self.unique_id, aux_heat_min_time_off)
            self._aux_heat_min_time_off = aux_heat_min_time_off

    async def async_set_heat_interstage_delay(self, value):
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
            await self._client.async_set_heat_interstage_min_delay(self.unique_id, time_val * 60)
            await self._client.async_set_heat_interstage_delay(self.unique_id, time_val * 60 * 2)
        if has_multiple_aux_stages:
            await self._client.async_set_aux_interstage_min_delay(self.unique_id, time_val * 60)
            await self._client.async_set_aux_interstage_delay(self.unique_id, time_val * 60 * 2)

    async def async_set_cool_interstage_delay(self, value):
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

        await self._client.async_set_cool_interstage_min_delay(self.unique_id, time_val * 60)
        await self._client.async_set_cool_interstage_delay(self.unique_id, time_val * 60 * 2)

    async def async_set_aux_heating_source(self, value):
        """Set auxiliary heating device."""
        equip = AUX_HEATING.get(value[ATTR_AUX_HEAT_SOURCE_TYPE])
        if equip is None:
            raise ServiceValidationError(
                f"Invalid value for {ATTR_AUX_HEAT_SOURCE_TYPE}, must be one of {AUX_HEATING.keys()}"
            )

        await self._client.async_set_aux_heating_source(value["id"], equip)
        self._aux_heat_source_type = equip

    async def async_set_fan_speed(self, value):
        """Set fan speed On or Auto."""
        await self._client.async_set_fan_mode(value["id"], value["speed"], self._device_model)
        self._fan_speed = value["speed"]

    @override
    async def async_set_humidity(self, humidity: int | None = None, **kwargs: Any) -> None:
        """Set new target humidity %."""
        if humidity is None:
            humidity = kwargs.get("humidity")
        if humidity is None:
            return

        if self._humidity_setpoint_mode == "defog":
            await self._client.async_set_humidity_offset(self._id, humidity, self._is_HC)
            self._humidity_setpoint_offset = humidity
        else:
            await self._client.async_set_humidity(self._id, humidity)
            self._humidity_setpoint = humidity

    async def async_set_accessory_type(self, value):
        """Set accessory (humidifier, dehumidifier, air exchanger) type for TH6500WF."""
        await self._client.async_set_accessory_type(value["id"], value["type"])
        self._accessory_type = value["type"]

    async def async_set_schedule_mode(self, value):
        """Set schedule mode, manual or auto."""
        await self._client.async_set_schedule_mode(value["id"], value["mode"], self._is_HC)
        self._operation_mode = value["mode"]

    async def async_set_heatcool_setpoint_delta(self, value):
        """Set delta temperature between heating and cooling setpoint from 1 to 5°C."""
        await self._client.async_set_heatcool_delta(value["id"], value["level"], self._is_HC)
        self._heatcool_setpoint_delta = value["level"]

    async def async_set_cool_setpoint_away(self, value):
        """Set device away cooling setpoint."""
        await self._client.async_set_cool_setpoint_away(value["id"], value["temp"], self._is_HC)
        self._cool_target_temp_away = value["temp"]

    async def async_set_cool_dissipation_time(self, value):
        """Set device cool dissipation time."""
        await self._client.async_set_cool_dissipation_time(value["id"], value[ATTR_TIME], self._is_HC)
        self._heat_purge_time = value[ATTR_TIME]

    async def async_set_heat_dissipation_time(self, value):
        """Set device heat dissipation time."""
        await self._client.async_set_heat_dissipation_time(value["id"], value[ATTR_TIME], self._is_HC)
        self._cool_purge_time = value[ATTR_TIME]

    async def async_set_fan_filter_reminder(self, value):
        """Set fan filter reminder period from 1 to 12 month."""
        await self._client.async_set_fan_filter_reminder(value["id"], value["month"], self._is_HC)
        self._fan_filter_remain = value["month"]

    async def async_set_temperature_offset(self, value):
        """Set thermostat sensor offset from -2 to 2°C with a 0.5°C increment."""
        await self._client.async_set_temperature_offset(value["id"], value["temp"], self._is_HC)
        self._temp_offset_heat = value["temp"]

    async def async_set_humidity_mode(self, value):
        """Set thermostat humidity setpoint mode, defog or manual"""
        await self._client.async_set_humidity_mode(value["id"], value["mode"], self._is_HC)
        self._humidity_setpoint_mode = value["mode"]

    async def async_set_hvac_dr_options(self, value):
        """Set thermostat DR options for Eco Sinope."""
        aux_conf = value.get(ATTR_AUX_OPTIM)
        fan_speed_config = value.get(ATTR_FAN_SPEED_OPTIM)
        if aux_conf is None and fan_speed_config is None:
            raise ServiceValidationError(
                f"Missing required parameter: either {ATTR_AUX_OPTIM} or {ATTR_FAN_SPEED_OPTIM} must be set"
            )
        await self._client.async_set_hvac_dr_options(value["id"], aux_conf=aux_conf, fan_speed_conf=fan_speed_config)
        if aux_conf is not None:
            self._dr_aux_config = "activated" if aux_conf == "on" else "deactivated"
        if fan_speed_config is not None:
            # Not a typo: Disabled is really sending "on" (allow fan to be always on when the optim is disabled)
            self._dr_fan_speed_conf = "auto" if fan_speed_config == "on" else "on"

    @property
    def fan_filter_remain(self) -> int | None:
        """Set fan filter reminder period from 1 to 12 month."""
        return self._fan_filter_remain

    @property
    def cool_setpoint_away(self):
        return self._cool_target_temp_away

    @property
    def wifi_aux_cycle_length(self):
        """For TH6250WF."""
        if self._sku == "TH6250WF":
            return self._wifi_aux_cycle
        return None

    @property
    def pro_aux_cycle_length(self):
        """For TH6250WF-PRO, TH6500WF and TH6510WF."""
        if self._sku != "TH6250WF_PRO" or self._sku != "TH6500WF" or self._sku != "TH6510WF":
            return self._wifi_aux_cycle
        return None

    @property
    @override
    def extra_state_attributes(self)  -> Mapping[str, Any]:
        """Return the state attributes."""
        data = {}
        data.update(
            {
                "eco_status": self._drstatus_active,
                "eco_optout": self._drstatus_optout,
                "eco_setpoint": self._drstatus_setpoint,
                "eco_power_relative": self._drstatus_rel,
                "eco_power_absolute": self._drstatus_abs,
                "eco_setpoint_status": self._drsetpoint_status,
                "eco_setpoint_delta": self._drsetpoint_value,
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
                "keypad": self._keypad,
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
                "sensor_temp_offset": self._temp_offset_heat,
                "cycle": self._wifi_cycle,
                "aux_cycle": self._wifi_aux_cycle,
                "cool_cycle_length": self._cool_cycle_length,
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
                "temp_display_error": self._room_temp_error,
                "dual_status": self._dual_status,
                "balance_point": self._balance_pt,
                "heat_lock_temp": self._heat_lockout_temp,
                "cool_lock_temp": self._cool_lockout_temp,
                "output_connect_state": self._output_connect_state,
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
        if self._device_model == 6727:
            data.update(
                {
                    "heat_interstage_min_delay": self._aux_interstage_min_delay,
                    "aux_interstage_min_delay": self._aux_interstage_min_delay,
                    "heat_interstage_delay": self._heat_interstage_delay,
                    "aux_interstage_delay": self._aux_interstage_delay,
                    "cool_interstage_min_delay": self._cool_interstage_min_delay,
                    "cool_interstage_delay": self._cool_interstage_delay,
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
                    "interlock_hc_mode": self._interlock_hc_mode,
                    "interlock_partner": self._interlock_partner,
                }
            )
        for prefix in RUNTIME_PREFIXES:
            data.update(runtime_attributes_dict(self, TH6_MODES_VALUES, prefix))

        return data
