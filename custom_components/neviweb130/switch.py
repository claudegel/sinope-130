"""
Support for Neviweb switch connected via GT130 ZigBee.
Multi-Controller
model 2180 = Multi controller for sedna valve MC3100ZB connected to GT130
model 2181 = Multi controller for sedna valve MC3100ZB connected sedna valve

load controler
Support for Neviweb switch connected via GT130 ZigBee.
model 2506 = load controller device, RM3250ZB, 50A, Zigbee
model 346 = load controller device, RM3250WF, 50A, wifi
model 2151 = Calypso load controller for water heater, RM3500ZB 20,8A, Zigbee
model 2152 = Calypso load controller for water heater, RM3500WF 20,8A, wifi
model 2152 = Calypso load controller for water heater, RM3510WF 20,8A, wifi
model 2610 = wall outlet, SP2610ZB
model 2600 = portable plug, SP2600ZB

For more details about this platform, please refer to the documentation at  
https://www.sinopetech.com/en/support/#api
"""

from __future__ import annotations

import logging

#import voluptuous as vol
import time

import custom_components.neviweb130 as neviweb130

from .schema import VERSION

from homeassistant.components.switch import (
    SwitchDeviceClass,
    SwitchEntity,
)

from homeassistant.const import (
    ATTR_ENTITY_ID,
    UnitOfEnergy,
    UnitOfTemperature,
    UnitOfVolume,
)
from homeassistant.core import HomeAssistant
from homeassistant.config_entries import ConfigEntry
from homeassistant.helpers.update_coordinator import (
    CoordinatorEntity,
    DataUpdateCoordinator,
)
from homeassistant.helpers import (
    config_validation as cv,
    device_registry as dr,
    discovery,
    entity_component,
    entity_platform,
    entity_registry,
    service,
)

from homeassistant.components.binary_sensor import BinarySensorDeviceClass
from homeassistant.components.persistent_notification import DOMAIN as PN_DOMAIN

from datetime import (
    date,
    datetime,
    timedelta,
    timezone,
)
from homeassistant.helpers.icon import icon_for_battery_level

from .const import (ATTR_ACTIVE, ATTR_AWAY_ACTION, ATTR_BATT_INFO,
                    ATTR_BATT_PERCENT_NORMAL, ATTR_BATT_STATUS_NORMAL,
                    ATTR_BATTERY_STATUS, ATTR_BATTERY_VOLTAGE,
                    ATTR_COLD_LOAD_PICKUP_REMAIN_TIME,
                    ATTR_COLD_LOAD_PICKUP_STATUS, ATTR_COLD_LOAD_PICKUP_TEMP,
                    ATTR_CONTROLLED_DEVICE, ATTR_DELAY, ATTR_DR_PROTEC_STATUS,
                    ATTR_DR_WATER_TEMP_TIME, ATTR_DRACTIVE, ATTR_DRSTATUS,
                    ATTR_ERROR_CODE_SET1, ATTR_EXT_TEMP, ATTR_INPUT_STATUS,
                    ATTR_INPUT_1_ON_DELAY, ATTR_INPUT_2_ON_DELAY,
                    ATTR_INPUT_1_OFF_DELAY, ATTR_INPUT_2_OFF_DELAY,
                    ATTR_INPUT2_STATUS, ATTR_KEYPAD, ATTR_LEAK_CLOSURE_CONFIG,
                    ATTR_LEG_PROTEC_STATUS, ATTR_LOW_TEMP_STATUS,
                    ATTR_MIN_WATER_TEMP, ATTR_NAME_1, ATTR_NAME_2,
                    ATTR_OCCUPANCY_SENSOR_DELAY, ATTR_ONOFF, ATTR_ONOFF2,
                    ATTR_ONOFF_NUM, ATTR_OPTOUT, ATTR_OUTPUT_NAME_1,
                    ATTR_OUTPUT_NAME_2, ATTR_POWER_SUPPLY, ATTR_REL_HUMIDITY,
                    ATTR_ROOM_TEMPERATURE, ATTR_RSSI, ATTR_STATUS,
                    ATTR_SYSTEM_MODE, ATTR_TANK_SIZE, ATTR_TIMER, ATTR_TIMER2,
                    ATTR_VALUE, ATTR_WATER_LEAK_ALARM_STATUS,
                    ATTR_WATER_LEAK_DISCONECTED_STATUS, ATTR_WATER_LEAK_STATUS,
                    ATTR_WATER_TANK_ON, ATTR_WATER_TEMP_MIN,
                    ATTR_WATER_TEMP_PROTEC, ATTR_WATER_TEMP_TIME,
                    ATTR_WATER_TEMPERATURE, ATTR_WATT_TIME_ON, ATTR_WATTAGE,
                    ATTR_WATTAGE_INSTANT, ATTR_WIFI, ATTR_WIFI_WATT_NOW,
                    ATTR_WIFI_WATTAGE, DOMAIN, MODE_AUTO, MODE_MANUAL,
                    MODE_OFF, SERVICE_SET_ACTIVATION, SERVICE_SET_CONTROL_ONOFF,
                    SERVICE_SET_CONTROLLED_DEVICE,
                    SERVICE_SET_INPUT_OUTPUT_NAMES,
                    SERVICE_SET_LOAD_DR_OPTIONS,
                    SERVICE_SET_LOW_TEMP_PROTECTION,
                    SERVICE_SET_ON_OFF_INPUT_DELAY, SERVICE_SET_REMAINING_TIME,
                    SERVICE_SET_SWITCH_KEYPAD_LOCK, SERVICE_SET_SWITCH_TIMER,
                    SERVICE_SET_SWITCH_TIMER_2, SERVICE_SET_TANK_SIZE,
                    STATE_KEYPAD_STATUS)
from .coordinator import Neviweb130Client, Neviweb130Coordinator
from .devices import device_dict, save_devices
from .schema import (SET_ACTIVATION_SCHEMA, SET_CONTROL_ONOFF_SCHEMA,
                     SET_CONTROLLED_DEVICE_SCHEMA,
                     SET_INPUT_OUTPUT_NAMES_SCHEMA, SET_LOAD_DR_OPTIONS_SCHEMA,
                     SET_LOW_TEMP_PROTECTION_SCHEMA,
                     SET_ON_OFF_INPUT_DELAY_SCHEMA, SET_REMAINING_TIME_SCHEMA,
                     SET_SWITCH_KEYPAD_LOCK_SCHEMA, SET_SWITCH_TIMER_2_SCHEMA,
                     SET_SWITCH_TIMER_SCHEMA, SET_TANK_SIZE_SCHEMA, VERSION)

_LOGGER = logging.getLogger(__name__)

DEFAULT_NAME = "neviweb130 switch"
DEFAULT_NAME_2 = "neviweb130 switch 2"
DEFAULT_NAME_3 = "neviweb130 switch 3"
SNOOZE_TIME = 1200

UPDATE_ATTRIBUTES = [ATTR_ONOFF]

HA_TO_NEVIWEB_SIZE = {
    "40 gal": 40,
    "50 gal": 50,
    "60 gal": 60,
    "80 gal": 80
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
    "24 h": 86400
}

HA_TO_NEVIWEB_CONTROLLED = {
    "Hot water heater": "hotWaterHeater",
    "Pool pump": "poolPump",
    "Eletric vehicle charger": "eletricVehicleCharger",
    "Other": "other"
}

SWITCH_TYPES = {
    "power": ["mdi:switch", SwitchDeviceClass.SWITCH],
    "outlet": ["mdi:power-plug", SwitchDeviceClass.OUTLET],
    "control": ["mdi:alarm", SwitchDeviceClass.SWITCH],
}

SUPPORTED_WIFI_MODES = [
    MODE_AUTO,
    MODE_MANUAL,
    MODE_OFF,
]

IMPLEMENTED_WIFI_WATER_HEATER_LOAD_MODEL = [2152]
IMPLEMENTED_WATER_HEATER_LOAD_MODEL = [2151]
IMPLEMENTED_ZB_DEVICE_CONTROL = [2180]
IMPLEMENTED_SED_DEVICE_CONTROL = [2181]
IMPLEMENTED_WALL_DEVICES = [2600, 2610]
IMPLEMENTED_LOAD_DEVICES = [2506]
IMPLEMENTED_WIFI_LOAD_DEVICES = [346]
IMPLEMENTED_DEVICE_MODEL = (
    IMPLEMENTED_LOAD_DEVICES
    + IMPLEMENTED_WALL_DEVICES
    + IMPLEMENTED_ZB_DEVICE_CONTROL
    + IMPLEMENTED_SED_DEVICE_CONTROL
    + IMPLEMENTED_WATER_HEATER_LOAD_MODEL
    + IMPLEMENTED_WIFI_WATER_HEATER_LOAD_MODEL
    + IMPLEMENTED_WIFI_LOAD_DEVICES
)


async def async_setup_entry(
    hass: HomeAssistant,
    entry: ConfigEntry,
    async_add_entities: AddEntitiesCallback,
    discovery_info=None,
) -> None:
    """Set up the Neviweb130 switch."""
    data = hass.data[DOMAIN][entry.entry_id]
    scan_interval = data["scan_interval"]
    stat_interval = data["stat_interval"]
    notify = data["notify"]

    if 'neviweb130_client' not in data:
        _LOGGER.error("Neviweb130 client initialization failed.")
        return

    coordinator = hass.data[DOMAIN][entry.entry_id]["coordinator"]

    entities = []
    device_registry = dr.async_get(hass)

    for gateway_data, default_name in [
        (data['neviweb130_client'].gateway_data, DEFAULT_NAME),
        (data['neviweb130_client'].gateway_data2, DEFAULT_NAME_2),
        (data['neviweb130_client'].gateway_data3, DEFAULT_NAME_3)
    ]:
        if gateway_data is not None and gateway_data != "_":
            for device_info in gateway_data:
                if "signature" in device_info and "model" in device_info["signature"]:
                    model = device_info["signature"]["model"]
                    if model in IMPLEMENTED_DEVICE_MODEL:
                        device_name = f'{default_name} {device_info["name"]}'
                        device_sku = device_info["sku"]
                        device_firmware = "{major}.{middle}.{minor}".format(
                            **device_info["signature"]["softVersion"]
                        )
                        if device_info["signature"]["model"] in IMPLEMENTED_WALL_DEVICES:
                            device_type = "outlet"
                            device = Neviweb130Switch(
                                data,
                                device_info,
                                device_name,
                                device_sku,
                                device_firmware,
                                device_type,
                                coordinator,
                            )
                        elif device_info["signature"]["model"] in IMPLEMENTED_LOAD_DEVICES:
                            device_type = "power"
                            device = Neviweb130PowerSwitch(
                                data,
                                device_info,
                                device_name,
                                device_sku,
                                device_firmware,
                                device_type,
                                coordinator,
                            )
                        elif device_info["signature"]["model"] in IMPLEMENTED_WIFI_LOAD_DEVICES:
                            device_type = "power"
                            device = Neviweb130WifiPowerSwitch(
                                data,
                                device_info,
                                device_name,
                                device_sku,
                                device_firmware,
                                device_type,
                                coordinator,
                            )
                        elif device_info["signature"]["model"] in IMPLEMENTED_WATER_HEATER_LOAD_MODEL:
                            device_type = "power"
                            device = Neviweb130TankPowerSwitch(
                                data,
                                device_info,
                                device_name,
                                device_sku,
                                device_firmware,
                                device_type,
                                coordinator,
                            )
                        elif device_info["signature"]["model"] in IMPLEMENTED_WIFI_WATER_HEATER_LOAD_MODEL:
                            device_type = "power"
                            device = Neviweb130WifiTankPowerSwitch(
                                data,
                                device_info,
                                device_name,
                                device_sku,
                                device_firmware,
                                device_type,
                                coordinator,
                            )
                        else:
                            device_type = "control"
                            device = Neviweb130ControlerSwitch(
                                data,
                                device_info,
                                device_name,
                                device_sku,
                                device_firmware,
                                device_type,
                                coordinator,
                            )

                        coordinator.register_device(device)
                        entities.append(device)
                       # _LOGGER.debug("Entities are %s", device)

                    if model in IMPLEMENTED_ZB_DEVICE_CONTROL:
                        device_name = f'{default_name} {device_info["name"]}'
                        device_sku = device_info["sku"]
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
                        device_info = {
                            "identifiers": device_entry.identifiers,
                            "name": device_entry.name,
                            "manufacturer": device_entry.manufacturer,
                            "model": device_entry.model,
                        }
                        _LOGGER.debug("Config entry = %s", device_entry)

                        device_name = f'{default_name} {device_info["name"]}'
                        master_device_name = f'{device_info["name"]}'
                        _LOGGER.debug(
                            "Attribute found for device: %s",
                            master_device_name,
                        )
                        if model in SWITCH_MODEL:
                            attributes_name = [ATTR_ONOFF2]
                            device_type = "control"

                        for attribute in attributes_name:
                            _LOGGER.debug(f"Adding attributes switch : {device_name} {attribute}")
                            entities.append(
                                Neviweb130DeviceAttributeSwitch(
                                    data['neviweb130_client'],
                                    device_info,
                                    device_name,
                                    attribute,
                                    device_entry.id,
                                    device_type,
                                    device_info,
                                    coordinator,
                                )
                            )

    async_add_entities(entities)
    hass.async_create_task(coordinator.async_request_refresh())

    def set_switch_keypad_lock_service(service):
        """Lock/unlock keypad device."""
        entity_id = service.data[ATTR_ENTITY_ID]
        value = {}
        for switch in entities:
            if switch.entity_id == entity_id:
                value = {
                    "id": switch.unique_id,
                    "lock": service.data[ATTR_KEYPAD],
                }
                switch.async_set_keypad_lock(value)
                switch.schedule_update_ha_state(True)
                break

    def set_switch_timer_service(service):
        """Set timer for switch device."""
        entity_id = service.data[ATTR_ENTITY_ID]
        value = {}
        for switch in entities:
            if switch.entity_id == entity_id:
                value = {
                    "id": switch.unique_id,
                    "time": service.data[ATTR_TIMER],
                }
                switch.async_set_timer(value)
                switch.schedule_update_ha_state(True)
                break

    def set_switch_timer2_service(service):
        """Set timer for switch device."""
        entity_id = service.data[ATTR_ENTITY_ID]
        value = {}
        for switch in entities:
            if switch.entity_id == entity_id:
                value = {
                    "id": switch.unique_id,
                    "time": service.data[ATTR_TIMER2],
                }
                switch.async_set_timer2(value)
                switch.schedule_update_ha_state(True)
                break

    def set_load_dr_options_service(service):
        """Set dr mode options for load controler."""
        entity_id = service.data[ATTR_ENTITY_ID]
        value = {}
        for switch in entities:
            if switch.entity_id == entity_id:
                value = {
                    "id": switch.unique_id,
                    "dractive": service.data[ATTR_DRACTIVE],
                    "droptout": service.data[ATTR_OPTOUT],
                    "onoff": service.data[ATTR_ONOFF],
                }
                switch.async_set_load_dr_options(value)
                switch.schedule_update_ha_state(True)
                break

    def set_control_onoff_service(service):
        """Set status of both onoff controler."""
        entity_id = service.data[ATTR_ENTITY_ID]
        value = {}
        for switch in entities:
            if switch.entity_id == entity_id:
                value = {
                    "id": switch.unique_id,
                    "onoff_num": service.data[ATTR_ONOFF_NUM],
                    "status": service.data[ATTR_STATUS],
                }
                switch.async_set_control_onoff(value)
                switch.schedule_update_ha_state(True)
                break

    def set_tank_size_service(service):
        """Set water tank size for RM3500ZB."""
        entity_id = service.data[ATTR_ENTITY_ID]
        value = {}
        for switch in entities:
            if switch.entity_id == entity_id:
                value = {
                    "id": switch.unique_id,
                    "val": service.data[ATTR_VALUE][0],
                }
                switch.async_set_tank_size(value)
                switch.schedule_update_ha_state(True)
                break

    def set_controlled_device_service(service):
        """Set controlled device type for RM3250ZB."""
        entity_id = service.data[ATTR_ENTITY_ID]
        value = {}
        for switch in entities:
            if switch.entity_id == entity_id:
                value = {
                    "id": switch.unique_id,
                    "val": service.data[ATTR_VALUE][0],
                }
                switch.async_set_controlled_device(value)
                switch.schedule_update_ha_state(True)
                break

    def set_low_temp_protection_service(service):
        """Set water tank temperature protection for RM3500ZB."""
        entity_id = service.data[ATTR_ENTITY_ID]
        value = {}
        for switch in entities:
            if switch.entity_id == entity_id:
                value = {
                    "id": switch.unique_id,
                    "val": service.data[ATTR_WATER_TEMP_MIN],
                }
                switch.async_set_low_temp_protection(value)
                switch.schedule_update_ha_state(True)
                break

    def set_input_output_names_service(service):
        """Set names for input 1 and 2, output 1 and 2 for MC3100ZB device."""
        entity_id = service.data[ATTR_ENTITY_ID]
        value = {}
        for switch in entities:
            if switch.entity_id == entity_id:
                value = {
                    "id": switch.unique_id,
                    "input1": service.data[ATTR_NAME_1],
                    "input2": service.data[ATTR_NAME_2],
                    "output1": service.data[ATTR_OUTPUT_NAME_1],
                    "output2": service.data[ATTR_OUTPUT_NAME_2],
                }
                switch.async_set_input_output_names(value)
                switch.schedule_update_ha_state(True)
                break

    def set_activation_service(service):
        """Activate or deactivate Neviweb polling for missing device."""
        entity_id = service.data[ATTR_ENTITY_ID]
        value = {}
        for switch in entities:
            if switch.entity_id == entity_id:
                value = {
                    "id": switch.unique_id,
                    "active": service.data[ATTR_ACTIVE],
                }
                switch.set_activation(value)
                switch.schedule_update_ha_state(True)
                break

    def set_remaining_time_service(service):
        """Set coldLoadPickupRemainingTime value."""
        entity_id = service.data[ATTR_ENTITY_ID]
        value = {}
        for switch in entities:
            if switch.entity_id == entity_id:
                value = {
                    "id": switch.unique_id,
                    "time": service.data[ATTR_COLD_LOAD_PICKUP_REMAIN_TIME],
                }
                switch.async_set_remaining_time(value)
                switch.schedule_update_ha_state(True)
                break

    def set_on_off_input_delay_service(service):
        """Set input 1 or 2 on/off delay for MC3100ZB device."""
        entity_id = service.data[ATTR_ENTITY_ID]
        value = {}
        for switch in entities:
            if switch.entity_id == entity_id:
                value = {
                    "id": switch.unique_id,
                    "inputnumber": service.data[ATTR_INPUT_NUMBER],
                    "onoff": service.data[ATTR_ONOFF],
                    "delay": service.data[ATTR_DELAY][0],
                }
                switch.async_set_on_off_input_delay(value)
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
        SERVICE_SET_LOAD_DR_OPTIONS,
        set_load_dr_options_service,
        schema=SET_LOAD_DR_OPTIONS_SCHEMA,
    )

    hass.services.async_register(
        DOMAIN,
        SERVICE_SET_CONTROL_ONOFF,
        set_control_onoff_service,
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
        SERVICE_SET_INPUT_OUTPUT_NAMES,
        set_input_output_names_service,
        schema=SET_INPUT_OUTPUT_NAMES_SCHEMA,
    )

    hass.services.async_register(
        DOMAIN,
        SERVICE_SET_ACTIVATION,
        set_activation_service,
        schema=SET_ACTIVATION_SCHEMA,
    )

    hass.services.async_register(
        DOMAIN,
        SERVICE_SET_REMAINING_TIME,
        set_remaining_time_service,
        schema=SET_REMAINING_TIME_SCHEMA,
    )

    hass.services.async_register(
        DOMAIN,
        SERVICE_SET_ON_OFF_INPUT_DELAY,
        set_on_off_input_delay_service,
        schema=SET_ON_OFF_INPUT_DELAY_SCHEMA,
    )

def voltage_to_percentage(voltage, num):
    """Convert voltage level from volt to percentage."""
    if num == 2:
        return int((min(voltage, 2.7) - 2.3) / (2.7 - 2.3) * 100)
    else:
        return int((min(voltage, 6.0) - 3.0) / (6.0 - 3.0) * 100)

def alert_to_text(alert, value):
    """Convert numeric alert activation to text."""
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
    """No action", "Close and send", "Close only", "Send only."""
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
    """Convert liters valuer to cubic meter for water flow stat."""
    if value is not None:
        return value / 1000
    else:
        return None

def model_to_HA(value):
    if value == 9887:
        return "FS4221"
    elif value == 4546:
        return "FS4220"
    else:
        return "No flow meter"

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

def remainig_time(time):
    """Convert time countdown for RM3500ZB."""
    if time == 65535:
        return "off"
    return time

def retreive_data(id, data):
    """Retreive device stat data from device_dict."""
    device_data = device_dict.get(id)
    if device_data:
        if data == 1:
            return device_data[1]
        else:
            return device_data[2]
    else:
        # Set defaults if device not found
        if data == 1:
            return 0
        else:
            return None

def save_data(id, data, mark):
    """Save stat data for one device in the device_dict."""
    device_dict[id][1] = data
    device_dict[id][2] = mark

async def async_add_data(id, data, mark):
    """Add new device stat data in the device_dict."""
    if id in device_dict:
        _LOGGER.debug("Device already exist in device_dict %s", id)
        return
    device_dict[id] = [id, data, mark]
    await save_devices()  # Persist changes
    _LOGGER.debug("Data added for %s", id)


class Neviweb130Switch(CoordinatorEntity, SwitchEntity):
    """Implementation of a Neviweb switch, SP2600ZB and SP2610ZB."""

    def __init__(self, data, device_info, name, sku, firmware, device_type, coordinator):
        """Initialize."""
        super().__init__(coordinator)
        self._device = device_info
        self._name = name
        self._sku = sku
        self._firmware = firmware
        self._client = data['neviweb130_client']
        self._notify = data["notify"]
        self._stat_interval = data["stat_interval"]
        self._id = str(device_info["id"])
        self._device_model = device_info["signature"]["model"]
        self._device_model_cfg = device_info["signature"]["modelCfg"]
        self._device_type = device_type
        self._total_kwh_count = retreive_data(self._id, 1)
        self._monthly_kwh_count = 0
        self._daily_kwh_count = 0
        self._hourly_kwh_count = 0
        self._hour_kwh = 0
        self._today_kwh = 0
        self._month_kwh = 0
        self._marker = None
        self._mark = retreive_data(self._id, 2)
        self._current_power_w = 0
        self._onoff = None
        self._is_wall = device_info["signature"]["model"] in \
            IMPLEMENTED_WALL_DEVICES
        self._is_load = device_info["signature"]["model"] in \
            IMPLEMENTED_LOAD_DEVICES
        self._is_wifi_load = (
            device_info["signature"]["model"] in IMPLEMENTED_WIFI_LOAD_DEVICES
        )
        self._is_tank_load = (
            device_info["signature"]["model"]
            in IMPLEMENTED_WATER_HEATER_LOAD_MODEL
        )
        self._is_wifi_tank_load = (
            device_info["signature"]["model"]
            in IMPLEMENTED_WIFI_WATER_HEATER_LOAD_MODEL
        )
        self._is_zb_control = (
            device_info["signature"]["model"] in IMPLEMENTED_ZB_DEVICE_CONTROL
        )
        self._is_sedna_control = (
            device_info["signature"]["model"] in IMPLEMENTED_SED_DEVICE_CONTROL
        )
        self._energy_stat_time = time.time() - 1500
        self._snooze = 0
        self._activ = True
        self._attr_device_info = {
            "identifiers": {(DOMAIN, self._id)},
            "name": self._name,
            "manufacturer": "claudegel",
            "model": self._device_model,
            "sw_version": self._firmware,
        }
        _LOGGER.debug("Setting up %s: %s", self._name, device_info)

    async def async_update(self):
        if self._activ:
            LOAD_ATTRIBUTES = [ATTR_WATTAGE_INSTANT]
            """Get the latest data from Neviweb and update the state."""
            start = time.time()
            device_data = await self._client.async_get_device_attributes(
                self._id, UPDATE_ATTRIBUTES + LOAD_ATTRIBUTES
            )
            end = time.time()
            elapsed = round(end - start, 3)
            _LOGGER.debug(
                "Updating %s (%s sec): %s", self._name, elapsed, device_data)

            if "error" not in device_data:
                if "errorCode" not in device_data:
                    self._current_power_w = device_data[ATTR_WATTAGE_INSTANT]
                    self._onoff = device_data[ATTR_ONOFF]
                    self.async_write_ha_state()
                else:
                    _LOGGER.warning(
                        "Error reading device %s: (%s)", self._name, device_data
                    )
            else:
                await self.async_log_error(device_data["error"]["code"])
            await self.async_do_stat(start)
        else:
            if time.time() - self._snooze > SNOOZE_TIME:
                self._activ = True
                if self._notify == "notification" or self._notify == "both":
                    await self.async_notify_ha(
                        "Warning: Neviweb Device update restarted for "
                        + self._name
                        + ", Sku: "
                        + self._sku
                    )

    @property
    def unique_id(self) -> str:
        """Return unique ID based on Neviweb device ID."""
        return self._id

    @property
    def id(self) -> str:
        """Alias pour DataUpdateCoordinator."""
        return self._id

    @property
    def name(self):
        """Return the name of the switch."""
        return self._name

    @property
    def icon(self):
        """Return the icon to use in the frontend."""
        try:
            return SWITCH_TYPES.get(self._device_type)[0]
        except TypeError:
            return None

    @property
    def device_class(self):
        """Return the device class of this entity."""
        return SWITCH_TYPES.get(self._device_type)[1]

    @property
    def is_on(self):
        """Return current operation i.e. ON, OFF."""
        return self._onoff != MODE_OFF

    async def async_turn_on(self, **kwargs):
        """Turn the device on."""
        await self._client.async_set_onoff(self._id, "on")
        self._onoff = "on"

    async def async_turn_off(self, **kwargs):
        """Turn the device off."""
        await self._client.async_set_onoff(self._id, "off")
        self._onoff = MODE_OFF

    @property
    def keypad_status(self):
        """Return current keypad status, unlocked, locked or partially locked."""
        if self._keypad is not None:
            return lock_to_ha(self._keypad)
        return False

    @property
    def current_temperature(self):
        """Return the current controler temperature."""
        if self._is_zb_control or self._is_sedna_control or self._is_tank_load:
            return self._room_temp
        else:
            return self._cur_temp

    @property
    def rssi(self):
        if self._rssi is not None:
            return self.extra_state_attributes.get("rssi")
        return None

    @property
    def total_kwh_count(self):
        if self._total_kwh_count is not None:
            return self.extra_state_attributes.get("total_kwh_count")
        return None

    @property
    def monthly_kwh_count(self):
        if self._monthly_kwh_count is not None:
            return self.extra_state_attributes.get("monthly_kwh_count")
        return None

    @property
    def daily_kwh_count(self):
        if self._daily_kwh_count is not None:
            return self.extra_state_attributes.get("daily_kwh_count")
        return None

    @property
    def hourly_kwh_count(self):
        if self._hourly_kwh_count is not None:
            return self.extra_state_attributes.get("hourly_kwh_count")
        return None

    @property
    def extra_state_attributes(self):
        """Return the extra state attributes."""
        data = {}
        data.update(
            {
                "onOff": self._onoff,
                "wattage_instant": self._current_power_w,
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
                "activation": self._activ,
                "device_type": self._device_type,
                "id": self._id,
            }
        )
        return data

    @property
    def battery_voltage(self):
        """Return the current battery voltage of the controller in %."""
        if self._is_zb_control or self._is_sedna_control:
            type = 2
        else:
            type = 4
        return voltage_to_percentage(self._battery_voltage, type)

    @property
    def is_standby(self):
        """Return true if device is in standby."""
        return self._current_power_w == 0

    async def async_set_control_onoff(self, value):
        """Set onOff or onOff2 to on or off"""
        entity = value["id"]
        onoff_no = value["onoff_num"]
        status = value["status"]
        await self._client.async_set_control_onoff(
            entity, onoff_no, status)
        if onoff_no == 1:
            self._onoff = status
        else:
            self._onoff2 = status

    async def async_set_keypad_lock(self, value):
        """Lock or unlock device's keypad, lock = locked, unlock = unlocked, partiallyLocked - partial lock."""
        lock = value["lock"]
        entity = value["id"]
        if self._is_wifi_load or self._is_wifi_tank_load:
            await self._client.async_set_keypad_lock(entity, lock, True)
        else:
            await self._client.async_set_keypad_lock(entity, lock, False)
        self._keypad = lock

    async def async_set_timer(self, value):
        """Set device timer, 0 = off, 1 to 255 = timer length."""
        time = value["time"]
        entity = value["id"]
        await self._client.async_set_timer(
            entity, time)
        self._timer = time

    async def async_set_timer2(self, value):
        """Set device timer 2 for Multi controller, 0 = off, 1 to 255 = timer length."""
        time = value["time"]
        entity = value["id"]
        await self._client.async_set_timer2(
            entity, time)
        self._timer2 = time

    async def async_set_load_dr_options(self, value):
        """Set load controler Éco Sinopé attributes."""
        entity = value["id"]
        onoff = value["onoff"]
        optout = value["droptout"]
        dr = value["dractive"]
        await self._client.async_set_load_dr_options(
            entity, onoff, optout, dr)
        self._drstatus_active = dr
        self._drstatus_optout = optout
        self._drstatus_onoff = onoff

    async def async_set_tank_size(self, value):
        """Set water tank size for RM3500ZB Calypso controler."""
        entity = value["id"]
        val = value["val"]
        size = [v for k, v in HA_TO_NEVIWEB_SIZE.items() if k == val][0]
        await self._client.async_set_tank_size(
            entity, size)
        self._tank_size = size

    async def async_set_controlled_device(self, value):
        """Set device name controlled by RM3250ZB load controler."""
        entity = value["id"]
        val = value["val"]
        tipe = [v for k, v in HA_TO_NEVIWEB_CONTROLLED.items() if k == val][0]
        await self._client.async_set_controlled_device(
            entity, tipe)
        self._controlled_device = tipe

    async def async_set_low_temp_protection(self, value):
        """Set water temperature protection for Calypso."""
        temp = value["val"]
        entity = value["id"]
        await self._client.async_set_low_temp_protection(
            entity, temp)
        self._water_temp_min = temp

    def set_activation(self, value):
        """Activate or deactivate neviweb polling for a missing device."""
        action = value["active"]
        self._activ = action

    async def async_set_remaining_time(self, value):
        """Set coldLoadPickupRemainingTime value."""
        time = value["time"]
        entity = value["id"]
        await self._client.async_set_remaining_time(entity, time)
        self._cold_load_remaining_time = time

    async def async_set_on_off_input_delay(self, value):
        """Set input 1 or 2 on/off delay in seconds."""
        entity = value["id"]
        val = value["delay"]
        onoff = value["onoff"]
        inputnumber = value["inputnumber"]
        delay = [v for k, v in HA_TO_NEVIWEB_DELAY.items() if k == val][0]
        await self._client.async_set_on_off_input_delay(
            entity, delay, onoff, inputnumber
        )
        if inputnumber == 1:
            match value["onoff"]:
                case "on":
                    self._input_1_on_delay = delay
                case _:
                    self._input_1_off_delay = delay
        else:
            match value["onoff"]:
                case "on":
                    self._input_2_on_delay = delay
                case _:
                    self._input_2_off_delay = delay

    async def async_set_input_output_names(self, value):
        """Set names for input 1 and 2, output 1 and 2 for MC3100ZB device."""
        if len(value["input1"]) > 0:
            in_1 = value["input1"]
        else:
            in_1 = ""
        if len(value["input2"]) > 0:
            in_2 = value["input2"]
        else:
            in_2 = ""
        if len(value["output1"]) > 0:
            out_1 = value["output1"]
        else:
            out_1 = ""
        if len(value["output2"]) > 0:
            out_2 = value["output2"]
        else:
            out_2 = ""
        entity = value["id"]
        await self._client.async_set_input_output_names(
            entity, in_1, in_2, out_1, out_2
        )
        self._input_name_1 = in_1
        self._input_name_2 = in_2
        self._output_name_1 = out_1
        self._output_name_2 = out_2

    async def async_do_stat(self, start):
        """Get device energy statistic."""
        if (
            start - self._energy_stat_time > self._stat_interval
            and self._energy_stat_time != 0
        ):
            today = date.today()
            current_month = today.month
            current_day = today.day
            device_monthly_stats = await self._client.async_get_device_monthly_stats(self._id)
            #            _LOGGER.debug("%s device_monthly_stats = %s", self._name, device_monthly_stats)
            if device_monthly_stats is not None and len(device_monthly_stats) > 1:
                n = len(device_monthly_stats)
                monthly_kwh_count = 0
                k = 0
                while k < n:
                    monthly_kwh_count += device_monthly_stats[k]["period"] / 1000
                    k += 1
                self._monthly_kwh_count = round(monthly_kwh_count, 3)
                self._month_kwh = round(device_monthly_stats[n - 1]["period"] / 1000, 3)
                dt_month = datetime.fromisoformat(device_monthly_stats[n - 1]["date"][:-1] + '+00:00').astimezone(timezone.utc)
                _LOGGER.debug("stat month = %s", dt_month.month)
            else:
                self._month_kwh = 0
                _LOGGER.warning("%s Got None for device_monthly_stats", self._name)
            device_daily_stats = await self._client.async_get_device_daily_stats(self._id)
            #            _LOGGER.debug("%s device_daily_stats = %s", self._name, device_daily_stats)
            if device_daily_stats is not None and len(device_daily_stats) > 1:
                n = len(device_daily_stats)
                daily_kwh_count = 0
                k = 0
                while k < n:
                    if datetime.fromisoformat(device_daily_stats[k]["date"][:-1] + '+00:00').astimezone(timezone.utc).month == current_month:
                        daily_kwh_count += device_daily_stats[k]["period"] / 1000
                    k += 1
                self._daily_kwh_count = round(daily_kwh_count, 3)
                self._today_kwh = round(device_daily_stats[n - 1]["period"] / 1000, 3)
                dt_day = datetime.fromisoformat(device_daily_stats[n - 1]["date"][:-1].replace('Z', '+00:00'))
                _LOGGER.debug("stat day = %s", dt_day.day)
            else:
                self._today_kwh = 0
                _LOGGER.warning("%s Got None for device_daily_stats", self._name)
            device_hourly_stats = await self._client.async_get_device_hourly_stats(self._id)
            #            _LOGGER.debug("%s device_hourly_stats = %s", self._name, device_hourly_stats)
            if device_hourly_stats is not None and len(device_hourly_stats) > 1:
                n = len(device_hourly_stats)
                hourly_kwh_count = 0
                k = 0
                while k < n:
                    if datetime.fromisoformat(device_hourly_stats[k]["date"][:-1].replace('Z', '+00:00')).day == current_day:
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
                self._total_kwh_count = round(self._monthly_kwh_count + self._daily_kwh_count + self._hourly_kwh_count, 3)
                await async_add_data(self._id, self._total_kwh_count, self._marker)
                self._mark = self._marker
            else:
                if self._marker != self._mark:
                    self._total_kwh_count += round(self._hour_kwh, 3)
                    save_data(self._id, self._total_kwh_count, self._marker)
                    self._mark = self._marker
            _LOGGER.debug("Device dict updated: %s", device_dict)
            self.async_write_ha_state()
            self._energy_stat_time = time.time()
        if self._energy_stat_time == 0:
            self._energy_stat_time = start

    async def async_log_error(self, error_data):
        """Send error message to LOG."""
        if error_data == "USRSESSEXP":
            _LOGGER.warning("Session expired... reconnecting...")
            if self._notify == "notification" or self._notify == "both":
                await self.async_notify_ha(
                    "Warning: Got USRSESSEXP error, Neviweb session expired. "
                    + "Set your scan_interval parameter to less than 10 "
                    + "minutes to avoid this... Reconnecting..."
                )
            await self._client.async_reconnect()
        elif error_data == "ACCDAYREQMAX":
            _LOGGER.warning("Maximun daily request reached...Reduce polling frequency.")
        elif error_data == "TimeoutError":
            _LOGGER.warning("Timeout error detected...Retry later.")
        elif error_data == "MAINTENANCE":
            _LOGGER.warning("Access blocked for maintenance...Retry later.")
            await self.async_notify_ha(
                "Warning: Neviweb access temporary blocked for maintenance..."
                + "Retry later."
            )
            await self._client.async_reconnect()
        elif error_data == "ACCSESSEXC":
            _LOGGER.warning(
                "Maximun session number reached...Close other connections "
                + "and try again."
            )
            await self.async_notify_ha(
                "Warning: Maximun Neviweb session number reached...Close "
                + "other connections and try again."
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
                "Device action not supported for %s (id: %s)...(SKU: %s) "
                + "Report to maintainer.",
                self._name,
                self._id,
                self._sku,
            )
        elif error_data == "DVCCOMMTO":
            _LOGGER.warning(
                "Device Communication Timeout for %s (id: %s)... The device "
                + "did not respond to the server within the prescribed delay. "
                + "(SKU: %s)",
                self._name,
                self._id,
                self._sku,
            )
        elif error_data == "SVCERR":
            _LOGGER.warning(
                "Service error, device not available retry later %s (id: %s): "
                + "%s...(SKU: %s)",
                self._name,
                self._id,
                error_data,
                self._sku,
            )
        elif error_data == "DVCBUSY":
            _LOGGER.warning(
                "Device busy can't reach (neviweb update ?), retry later %s ("
                + "id: %s): %s...(SKU: %s)",
                self._name,
                self._id,
                error_data,
                self._sku,
            )
        elif error_data == "DVCUNVLB":
            if self._notify == "logging" or self._notify == "both":
                _LOGGER.warning(
                    "Device %s (id: %s) is disconected from Neviweb: %s..."
                    + "(SKU: %s)",
                    self._name,
                    self._id,
                    error_data,
                    self._sku,
                )
                _LOGGER.warning(
                    "This device %s is de-activated and won't be updated for "
                    + "20 minutes.",
                    self._name,
                )
                _LOGGER.warning(
                    "You can re-activate device %s with "
                    + "service.neviweb130_set_activation or wait 20 minutes "
                    + "for update to restart or just restart HA.",
                    self._name,
                )
            if self._notify == "notification" or self._notify == "both":
                await self.async_notify_ha(
                    "Warning: Received message from Neviweb, device "
                    + "disconnected... Check your log... Neviweb update will "
                    + "be halted for 20 minutes for "
                    + self._name
                    + ", id: "
                    + self._id
                    + ", Sku: "
                    + self._sku
                )
            self._activ = False
            self._snooze = time.time()
        else:
            _LOGGER.warning(
                "Unknown error for %s (id: %s): %s...(SKU: %s) Report to "
                + "aintainer.",
                self._name,
                self._id,
                error_data,
                self._sku,
            )

    async def async_notify_ha(self, msg: str, title: str = "Neviweb130 integration "+VERSION):
        """Notify user via HA web frontend."""
        await self.hass.services.call(
            PN_DOMAIN,
            "create",
            service_data={
                "title": title,
                "message": msg,
            },
            blocking=False,
        )
        return True


class Neviweb130PowerSwitch(Neviweb130Switch):
    """Implementation of a Neviweb power controler switch, RM3250ZB."""

    def __init__(self, data, device_info, name, sku, firmware, device_type, coordinator):
        """Initialize."""
        super().__init__(data, device_info, name, sku, firmware, device_type, coordinator)
        self._device = device_info
        self._name = name
        self._sku = sku
        self._firmware = firmware
        self._client = data["neviweb130_client"]
        self._notify = data["notify"]
        self._stat_interval = data["stat_interval"]
        self._id = str(device_info["id"])
        self._device_model = device_info["signature"]["model"]
        self._device_model_cfg = device_info["signature"]["modelCfg"]
        self._device_type = device_type
        self._current_power_w = 0
        self._wattage = 0
        self._total_kwh_count = retreive_data(self._id, 1)
        self._monthly_kwh_count = 0
        self._daily_kwh_count = 0
        self._hourly_kwh_count = 0
        self._hour_kwh = 0
        self._today_kwh = 0
        self._month_kwh = 0
        self._marker = None
        self._mark = retreive_data(self._id, 2)
        self._onoff = None
        self._timer = 0
        self._keypad = None
        self._drstatus_active = "off"
        self._drstatus_optout = "off"
        self._drstatus_onoff = "off"
        self._rssi = None
        self._error_code = None
        self._controlled_device = None
        self._is_wifi_load = (
            device_info["signature"]["model"] in IMPLEMENTED_WIFI_LOAD_DEVICES
        )
        self._is_load = (
            device_info["signature"]["model"] in IMPLEMENTED_LOAD_DEVICES
        )
        self._energy_stat_time = time.time() - 1500
        self._snooze = 0
        self._activ = True
        self._attr_device_info = {
            "identifiers": {(DOMAIN, self._id)},
            "name": self._name,
            "manufacturer": "claudegel",
            "model": self._device_model,
            "sw_version": self._firmware,
        }
        _LOGGER.debug("Setting up %s: %s", self._name, device_info)

    async def async_update(self):
        if self._activ:
            LOAD_ATTRIBUTES = [
                ATTR_WATTAGE,
                ATTR_WATTAGE_INSTANT,
                ATTR_TIMER,
                ATTR_KEYPAD,
                ATTR_DRSTATUS,
                ATTR_RSSI,
                ATTR_CONTROLLED_DEVICE,
                ATTR_ERROR_CODE_SET1,
            ]
            """Get the latest data from Neviweb and update the state."""
            start = time.time()
            device_data = await self._client.async_get_device_attributes(
                self._id, UPDATE_ATTRIBUTES + LOAD_ATTRIBUTES
            )
            end = time.time()
            elapsed = round(end - start, 3)
            _LOGGER.debug(
                "Updating %s (%s sec): %s", self._name, elapsed, device_data)

            if "error" not in device_data:
                if "errorCode" not in device_data:
                    self._onoff = device_data[ATTR_ONOFF]
                    self._current_power_w = device_data[ATTR_WATTAGE_INSTANT]
                    self._wattage = device_data[ATTR_WATTAGE]
                    self._keypad = STATE_KEYPAD_STATUS if \
                        device_data[ATTR_KEYPAD] == STATE_KEYPAD_STATUS else "locked" 
                    self._timer = device_data[ATTR_TIMER]
                    if ATTR_DRSTATUS in device_data:
                        self._drstatus_active = device_data[ATTR_DRSTATUS][
                            ATTR_DRACTIVE
                        ]
                        self._drstatus_optout = device_data[ATTR_DRSTATUS][ATTR_OPTOUT]
                        self._drstatus_onoff = device_data[ATTR_DRSTATUS][ATTR_ONOFF]
                    if (
                        ATTR_ERROR_CODE_SET1 in device_data
                        and len(device_data[ATTR_ERROR_CODE_SET1]) > 0
                    ):
                        if device_data[ATTR_ERROR_CODE_SET1]["raw"] != 0:
                            self._error_code = device_data[ATTR_ERROR_CODE_SET1]["raw"]
                            await self.async_notify_ha(
                                "Warning: Neviweb Device error code detected: "
                                + str(device_data[ATTR_ERROR_CODE_SET1]["raw"])
                                + " for device: "
                                + self._name
                                + ", Sku: "
                                + self._sku
                            )
                    if ATTR_RSSI in device_data:
                        self._rssi = device_data[ATTR_RSSI]
                    self._controlled_device = device_data[ATTR_CONTROLLED_DEVICE]
                    self.async_write_ha_state()
                else:
                    _LOGGER.warning(
                        "Error in reading device %s: (%s)", self._name, device_data
                    )
            else:
                await self.async_log_error(device_data["error"]["code"])
            await self.async_do_stat(start)
        else:
            if time.time() - self._snooze > SNOOZE_TIME:
                self._activ = True
                if self._notify == "notification" or self._notify == "both":
                    await self.async_notify_ha(
                        "Warning: Neviweb Device update restarted for "
                        + self._name
                        + ", Sku: "
                        + self._sku
                    )

    @property
    def extra_state_attributes(self):
        """Return the extra state attributes."""
        data = {}
        data.update(
            {
                "onOff": self._onoff,
                "controlled_device": neviweb_to_ha_controlled(
                    self._controlled_device
                ),
                "wattage": self._wattage,
                "wattage_instant": self._current_power_w,
                "total_kwh_count": self._total_kwh_count,
                "monthly_kwh_count": self._monthly_kwh_count,
                "daily_kwh_count": self._daily_kwh_count,
                "hourly_kwh_count": self._hourly_kwh_count,
                "hourly_kwh": self._hour_kwh,
                "daily_kwh": self._today_kwh,
                "monthly_kwh": self._month_kwh,
                "last_energy_stat_update": self._mark,
                "keypad": lock_to_ha(self._keypad),
                "timer": self._timer,
                "eco_status": self._drstatus_active,
                "eco_optOut": self._drstatus_optout,
                "eco_onoff": self._drstatus_onoff,
                "error_code": self._error_code,
                "rssi": self._rssi,
                "sku": self._sku,
                "device_model": str(self._device_model),
                "device_model_cfg": self._device_model_cfg,
                "firmware": self._firmware,
                "activation": self._activ,
                "device_type": self._device_type,
                "id": self._id,
            }
        )
        return data


class Neviweb130WifiPowerSwitch(Neviweb130Switch):
    """Implementation of a Neviweb power controler switch, RM3250WF."""

    def __init__(self, data, device_info, name, sku, firmware, device_type, coordinator):
        """Initialize."""
        super().__init__(data, device_info, name, sku, firmware, device_type, coordinator)
        self._device = device_info
        self._name = name
        self._sku = sku
        self._firmware = firmware
        self._client = data["neviweb130_client"]
        self._notify = data["notify"]
        self._stat_interval = data["stat_interval"]
        self._id = str(device_info["id"])
        self._device_model = device_info["signature"]["model"]
        self._device_model_cfg = device_info["signature"]["modelCfg"]
        self._device_type = device_type
        self._current_power_w = 0
        self._wattage = 0
        self._total_kwh_count = retreive_data(self._id, 1)
        self._monthly_kwh_count = 0
        self._daily_kwh_count = 0
        self._hourly_kwh_count = 0
        self._hour_kwh = 0
        self._today_kwh = 0
        self._month_kwh = 0
        self._marker = None
        self._mark = retreive_data(self._id, 2)
        self._onoff = None
        self._timer = 0
        self._keypad = None
        self._drstatus_active = "off"
        self._drstatus_optout = "off"
        self._drstatus_onoff = "off"
        self._wifirssi = None
        self._error_code = None
        self._controlled_device = None
        self._is_wifi_load = (
            device_info["signature"]["model"] in IMPLEMENTED_WIFI_LOAD_DEVICES
        )
        self._energy_stat_time = time.time() - 1500
        self._snooze = 0
        self._activ = True
        self._attr_device_info = {
            "identifiers": {(DOMAIN, self._id)},
            "name": self._name,
            "manufacturer": "claudegel",
            "model": self._device_model,
            "sw_version": self._firmware,
        }
        _LOGGER.debug("Setting up %s: %s", self._name, device_info)

    async def async_update(self):
        if self._activ:
            LOAD_ATTRIBUTES = [
                ATTR_WATTAGE_INSTANT,
                ATTR_WIFI_WATTAGE,
                ATTR_WIFI_KEYPAD,
                ATTR_DRSTATUS,
                ATTR_WIFI,
                ATTR_CONTROLLED_DEVICE,
                ATTR_ERROR_CODE_SET1,
            ]
            """Get the latest data from Neviweb and update the state."""
            start = time.time()
            device_data = await self._client.async_get_device_attributes(
                self._id, UPDATE_ATTRIBUTES + LOAD_ATTRIBUTES
            )
            end = time.time()
            elapsed = round(end - start, 3)
            _LOGGER.debug(
                "Updating %s (%s sec): %s", self._name, elapsed, device_data)
            if "error" not in device_data:
                if "errorCode" not in device_data:
                    self._onoff = device_data[ATTR_ONOFF]
                    self._current_power_w = device_data[ATTR_WATTAGE_INSTANT]
                    self._wattage = device_data[ATTR_WIFI_WATTAGE]
                    self._keypad = (
                        STATE_KEYPAD_STATUS
                        if device_data[ATTR_WIFI_KEYPAD] == STATE_KEYPAD_STATUS
                        else "locked"
                    )
                    if ATTR_DRSTATUS in device_data:
                        self._drstatus_active = device_data[ATTR_DRSTATUS][
                            ATTR_DRACTIVE
                        ]
                        self._drstatus_optout = device_data[ATTR_DRSTATUS][ATTR_OPTOUT]
                        self._drstatus_onoff = device_data[ATTR_DRSTATUS][ATTR_ONOFF]
                    if (
                        ATTR_ERROR_CODE_SET1 in device_data
                        and len(device_data[ATTR_ERROR_CODE_SET1]) > 0
                    ):
                        if device_data[ATTR_ERROR_CODE_SET1]["raw"] != 0:
                            self._error_code = device_data[ATTR_ERROR_CODE_SET1]["raw"]
                            await self.async_notify_ha(
                                "Warning: Neviweb Device error code detected: "
                                + str(device_data[ATTR_ERROR_CODE_SET1]["raw"])
                                + " for device: "
                                + self._name
                                + ", Sku: "
                                + self._sku
                            )
                    else:
                        self._error_code = 0
                    if ATTR_WIFI in device_data:
                        self._wifirssi = device_data[ATTR_WIFI]
                    self._controlled_device = device_data[ATTR_CONTROLLED_DEVICE]
                    self.async_write_ha_state()
                else:
                    _LOGGER.warning(
                        "Error in reading device %s: (%s)", self._name, device_data
                    )
            else:
                await self.async_log_error(device_data["error"]["code"])
            await self.async_do_stat(start)
        else:
            if time.time() - self._snooze > SNOOZE_TIME:
                self._activ = True
                if self._notify == "notification" or self._notify == "both":
                    await self.async_notify_ha(
                        "Warning: Neviweb Device update restarted for "
                        + self._name
                        + ", Sku: "
                        + self._sku
                    )

    @property
    def extra_state_attributes(self):
        """Return the extra state attributes."""
        data = {}
        data.update(
            {
                "onOff": self._onoff,
                "controlled_device": neviweb_to_ha_controlled(self._controlled_device),
                "wattage": self._wattage,
                "wattage_instant": self._current_power_w,
                "total_kwh_count": self._total_kwh_count,
                "monthly_kwh_count": self._monthly_kwh_count,
                "daily_kwh_count": self._daily_kwh_count,
                "hourly_kwh_count": self._hourly_kwh_count,
                "hourly_kwh": self._hour_kwh,
                "daily_kwh": self._today_kwh,
                "monthly_kwh": self._month_kwh,
                "last_energy_stat_update": self._mark,
                "keypad": lock_to_ha(self._keypad),
                "timer": self._timer,
                "eco_status": self._drstatus_active,
                "eco_optOut": self._drstatus_optout,
                "eco_onoff": self._drstatus_onoff,
                "error_code": self._error_code,
                "rssi": self._wifirssi,
                "sku": self._sku,
                "device_model": str(self._device_model),
                "device_model_cfg": self._device_model_cfg,
                "firmware": self._firmware,
                "activation": self._activ,
                "device_type": self._device_type,
                "id": self._id,
            }
        )
        return data


class Neviweb130TankPowerSwitch(Neviweb130Switch):
    """Implementation of a Neviweb water heater power controler switch, RM3500ZB."""

    def __init__(self, data, device_info, name, sku, firmware, device_type, coordinator):
        """Initialize."""
        super().__init__(data, device_info, name, sku, firmware, device_type, coordinator)
        self._device = device_info
        self._name = name
        self._sku = sku
        self._firmware = firmware
        self._client = data["neviweb130_client"]
        self._notify = data["notify"]
        self._stat_interval = data["stat_interval"]
        self._id = str(device_info["id"])
        self._device_model = device_info["signature"]["model"]
        self._device_model_cfg = device_info["signature"]["modelCfg"]
        self._device_type = device_type
        self._total_kwh_count = retreive_data(self._id, 1)
        self._monthly_kwh_count = 0
        self._daily_kwh_count = 0
        self._hourly_kwh_count = 0
        self._hour_kwh = 0
        self._today_kwh = 0
        self._month_kwh = 0
        self._marker = None
        self._mark = retreive_data(self._id, 2)
        self._onoff = None
        self._current_power_w = 0
        self._wattage = 0
        self._drstatus_active = "off"
        self._drstatus_optout = "off"
        self._drstatus_onoff = "off"
        self._drstatus_optout_reason = "off"
        self._water_temp = None
        self._water_temp_min = None
        self._water_temp_time = None
        self._water_temp_protec = None
        self._rssi = None
        self._error_code = None
        self._temperature = None
        self._water_leak_status = None
        self._cold_load_status = None
        self._cold_load_remaining_time = 0
        self._tank_size = None
        self._consumption = None
        self._consumption_time = None
        self._watt_time_on = None
        self._is_tank_load = (
            device_info["signature"]["model"] in IMPLEMENTED_WATER_HEATER_LOAD_MODEL
        )
        self._energy_stat_time = time.time() - 1500
        self._snooze = 0
        self._activ = True
        self._attr_device_info = {
            "identifiers": {(DOMAIN, self._id)},
            "name": self._name,
            "manufacturer": "claudegel",
            "model": self._device_model,
            "sw_version": self._firmware,
        }
        _LOGGER.debug("Setting up %s: %s", self._name, device_info)

    async def async_update(self):
        if self._activ:
            LOAD_ATTRIBUTES = [
                ATTR_WATER_LEAK_STATUS,
                ATTR_ROOM_TEMPERATURE,
                ATTR_ERROR_CODE_SET1,
                ATTR_WATTAGE,
                ATTR_WATTAGE_INSTANT,
                ATTR_COLD_LOAD_PICKUP_STATUS,
                ATTR_TANK_SIZE,
                ATTR_WATER_TEMP_MIN,
                ATTR_WATT_TIME_ON,
                ATTR_DR_WATER_TEMP_TIME,
                ATTR_RSSI,
                ATTR_DRSTATUS,
                ATTR_DR_PROTEC_STATUS,
                ATTR_COLD_LOAD_PICKUP_REMAIN_TIME,
                ATTR_WATER_TEMP_PROTEC,
            ]
            """Get the latest data from Neviweb and update the state."""
            start = time.time()
            device_data = await self._client.async_get_device_attributes(
                self._id, UPDATE_ATTRIBUTES + LOAD_ATTRIBUTES
            )
            end = time.time()
            elapsed = round(end - start, 3)
            _LOGGER.debug("Updating %s (%s sec): %s", self._name, elapsed, device_data)

            if "error" not in device_data:
                if "errorCode" not in device_data:
                    self._onoff = device_data[ATTR_ONOFF]
                    if ATTR_WATER_LEAK_STATUS in device_data:
                        self._water_leak_status = device_data[ATTR_WATER_LEAK_STATUS]
                    self._water_temp = device_data[ATTR_ROOM_TEMPERATURE]
                    if (
                        ATTR_ERROR_CODE_SET1 in device_data
                        and len(device_data[ATTR_ERROR_CODE_SET1]) > 0
                    ):
                        if device_data[ATTR_ERROR_CODE_SET1]["raw"] != 0:
                            self._error_code = device_data[ATTR_ERROR_CODE_SET1]["raw"]
                            match self._error_code:
                                case 32:
                                    message = "Temperature sensor disconnected."
                                case 64:
                                    message = "Leak sensor disconnected."
                            await self.async_notify_ha(
                                f"Warning: Neviweb Device error code detected: "
                                + str(device_data[ATTR_ERROR_CODE_SET1]["raw"])
                                + " for device: "
                                + self._name
                                + ", Sku: "
                                + self._sku
                                + ". "
                                + message
                            )
                    else:
                        self._error_code = 0
                    self._wattage = device_data[ATTR_WATTAGE]
                    self._current_power_w = device_data[ATTR_WATTAGE_INSTANT]
                    self._cold_load_status = device_data[ATTR_COLD_LOAD_PICKUP_STATUS]
                    self._cold_load_remaining_time = device_data[
                        ATTR_COLD_LOAD_PICKUP_REMAIN_TIME
                    ]
                    self._rssi = device_data[ATTR_RSSI]
                    self._tank_size = device_data[ATTR_TANK_SIZE]
                    if ATTR_DRSTATUS in device_data:
                        self._drstatus_active = device_data[ATTR_DRSTATUS][
                            ATTR_DRACTIVE
                        ]
                        self._drstatus_optout = device_data[ATTR_DRSTATUS][
                            ATTR_OPTOUT
                        ]
                        self._drstatus_onoff = device_data[ATTR_DRSTATUS][
                            ATTR_ONOFF
                        ]
                        self._drstatus_optout_reason = device_data[ATTR_DRSTATUS][
                            "optOutReason"
                        ]
                    self._water_temp_min = device_data[ATTR_WATER_TEMP_MIN]
                    self._water_temp_protec = device_data[ATTR_WATER_TEMP_PROTEC]
                    self._watt_time_on = device_data[ATTR_WATT_TIME_ON]
                    self._water_temp_time = device_data[ATTR_DR_WATER_TEMP_TIME]
                    if ATTR_DR_PROTEC_STATUS in device_data:
                        self._temperature = device_data[ATTR_DR_PROTEC_STATUS][
                            "temperature"
                        ]
                        self._consumption = device_data[ATTR_DR_PROTEC_STATUS][
                            "consumption"
                        ]
                        self._consumption_time = device_data[ATTR_DR_PROTEC_STATUS][
                            "consumptionOverTime"
                        ]
                    if device_data[ATTR_WATER_LEAK_STATUS] == "probe":
                        await self.async_notify_ha(
                            "Warning: Neviweb Device error code detected: "
                            + device_data[ATTR_WATER_LEAK_STATUS]
                            + " for device: "
                            + self._name
                            + ", Sku: "
                            + self._sku
                            + ", Leak sensor disconnected."
                        )
                    self.async_write_ha_state()
                else:
                    _LOGGER.warning("Error in reading device %s: (%s)", self._name, device_data)
            else:
                await self.async_log_error(device_data["error"]["code"])
            await self.async_do_stat(start)
        else:
            if time.time() - self._snooze > SNOOZE_TIME:
                self._activ = True
                if self._notify == "notification" or self._notify == "both":
                    await self.async_notify_ha(
                        "Warning: Neviweb Device update restarted for "
                        + self._name
                        + ", Sku: "
                        + self._sku
                    )

    @property
    def extra_state_attributes(self):
        """Return the extra state attributes."""
        data = {}
        data.update(
            {
                "onOff": self._onoff,
                "wattage": self._wattage,
                "wattage_instant": self._current_power_w,
                "total_kwh_count": self._total_kwh_count,
                "monthly_kwh_count": self._monthly_kwh_count,
                "daily_kwh_count": self._daily_kwh_count,
                "hourly_kwh_count": self._hourly_kwh_count,
                "hourly_kwh": self._hour_kwh,
                "daily_kwh": self._today_kwh,
                "monthly_kwh": self._month_kwh,
                "last_energy_stat_update": self._mark,
                "water_leak_status": self._water_leak_status,
                "water_temperature": self._water_temp,
                "cold_load_pickup_status": self._cold_load_status,
                "cold_load_remaining_time": remainig_time(
                    self._cold_load_remaining_time
                ),
                "tank_size": neviweb_to_ha(self._tank_size),
                "eco_status": self._drstatus_active,
                "eco_optOut": self._drstatus_optout,
                "eco_onoff": self._drstatus_onoff,
                "eco_optout_reason": self._drstatus_optout_reason,
                "water_temp_min": self._water_temp_min,
                "water_time_on": self._watt_time_on,
                "water_temp_time": self._water_temp_time,
                "water_temp_protection_type": self._water_temp_protec,
                "protection_Temperature": self._temperature,
                "protection_Consumption": self._consumption,
                "protection_consumption_overtime": self._consumption_time,
                "error_code": self._error_code,
                "rssi": self._rssi,
                "sku": self._sku,
                "device_model": str(self._device_model),
                "device_model_cfg": self._device_model_cfg,
                "firmware": self._firmware,
                "activation": self._activ,
                "device_type": self._device_type,
                "id": self._id,
            }
        )
        return data


class Neviweb130WifiTankPowerSwitch(Neviweb130Switch):
    """Implementation of a Neviweb wifi power controler switch, RM3500WF."""

    def __init__(self, data, device_info, name, sku, firmware, device_type, coordinator):
        """Initialize."""
        super().__init__(data, device_info, name, sku, firmware, device_type, coordinator)
        self._device = device_info
        self._name = name
        self._sku = sku
        self._firmware = firmware
        self._client = data["neviweb130_client"]
        self._notify = data["notify"]
        self._stat_interval = data["stat_interval"]
        self._id = str(device_info["id"])
        self._device_model = device_info["signature"]["model"]
        self._device_model_cfg = device_info["signature"]["modelCfg"]
        self._device_type = device_type
        self._total_kwh_count = retreive_data(self._id, 1)
        self._monthly_kwh_count = 0
        self._daily_kwh_count = 0
        self._hourly_kwh_count = 0
        self._hour_kwh = 0
        self._today_kwh = 0
        self._month_kwh = 0
        self._marker = None
        self._mark = retreive_data(self._id, 2)
        self._onoff = None
        self._wattage = 0
        self._current_power_w = 0
        self._drstatus_active = "off"
        self._drstatus_optout = "off"
        self._drstatus_onoff = "off"
        self._drstatus_power_abs = "off"
        self._drstatus_power_rel = "off"
        self._drstatus_setpoint = "off"
        self._cold_load_status = None
        self._cold_load_remaining_time = 0
        self._cold_load_temp = None
        self._water_temp = None
        self._water_temp_min = None
        self._water_temp_time = None
        self._water_temp_protec = None
        self._water_leak_disconected_status = None
        self._water_leak_closure_conf = None
        self._water_tank_on = None
        self._water_leak_status = None
        self._tank_size = None
        self._rssi = None
        self._error_code = None
        self._leg_status_temp = None
        self._leg_status_consumption = None
        self._leg_status_over_time = None
        self._mode = None
        self._away_action = None
        self._away_payload = None
        self._is_wifi_tank_load = (
            device_info["signature"]["model"]
            in IMPLEMENTED_WIFI_WATER_HEATER_LOAD_MODEL
        )
        self._energy_stat_time = time.time() - 1500
        self._snooze = 0
        self._activ = True
        self._attr_device_info = {
            "identifiers": {(DOMAIN, self._id)},
            "name": self._name,
            "manufacturer": "claudegel",
            "model": self._device_model,
            "sw_version": self._firmware,
        }
        _LOGGER.debug("Setting up %s: %s", self._name, device_info)

    async def async_update(self):
        if self._activ:
            LOAD_ATTRIBUTES = [
                ATTR_WATER_LEAK_ALARM_STATUS,
                ATTR_WATER_TEMPERATURE,
                ATTR_WATER_LEAK_DISCONECTED_STATUS,
                ATTR_ERROR_CODE_SET1,
                ATTR_WIFI_WATTAGE,
                ATTR_WIFI_WATT_NOW,
                ATTR_COLD_LOAD_PICKUP_STATUS,
                ATTR_TANK_SIZE,
                ATTR_MIN_WATER_TEMP,
                ATTR_WATER_TANK_ON,
                ATTR_WATER_TEMP_TIME,
                ATTR_WIFI,
                ATTR_DRSTATUS,
                ATTR_LEG_PROTEC_STATUS,
                ATTR_COLD_LOAD_PICKUP_REMAIN_TIME,
                ATTR_SYSTEM_MODE,
                ATTR_COLD_LOAD_PICKUP_TEMP,
                ATTR_LEAK_CLOSURE_CONFIG,
                ATTR_AWAY_ACTION,
                ATTR_WATER_TEMP_PROTEC,
            ]
            """Get the latest data from Neviweb and update the state."""
            start = time.time()
            device_data = await self._client.async_get_device_attributes(
                self._id, UPDATE_ATTRIBUTES + LOAD_ATTRIBUTES
            )
            end = time.time()
            elapsed = round(end - start, 3)
            _LOGGER.debug("Updating %s (%s sec): %s", self._name, elapsed, device_data)

            if "error" not in device_data:
                if "errorCode" not in device_data:
                    self._onoff = device_data[ATTR_ONOFF]
                    self._water_leak_status = device_data[ATTR_WATER_LEAK_ALARM_STATUS]
                    self._water_leak_disconected_status = device_data[
                        ATTR_WATER_LEAK_DISCONECTED_STATUS
                    ]
                    self._water_temp = device_data[ATTR_WATER_TEMPERATURE]
                    if (
                        ATTR_ERROR_CODE_SET1 in device_data
                        and len(device_data[ATTR_ERROR_CODE_SET1]) > 0
                    ):
                        if device_data[ATTR_ERROR_CODE_SET1]["raw"] != 0:
                            self._error_code = device_data[ATTR_ERROR_CODE_SET1]["raw"]
                            match self._error_code:
                                case 32:
                                    message = "Temperature sensor disconnected."
                                case 64:
                                    message = "Leak sensor disconnected."
                            await self.async_notify_ha(
                                f"Warning: Neviweb Device error code detected: "
                                + str(device_data[ATTR_ERROR_CODE_SET1]["raw"])
                                + " for device: "
                                + self._name
                                + ", Sku: "
                                + self._sku
                                + ". "
                                + message
                            )
                    else:
                        self._error_code = 0
                    if ATTR_DRSTATUS in device_data:
                        self._drstatus_active = device_data[ATTR_DRSTATUS][ATTR_DRACTIVE]
                        self._drstatus_optout = device_data[ATTR_DRSTATUS][ATTR_OPTOUT]
                        self._drstatus_onoff = device_data[ATTR_DRSTATUS][ATTR_ONOFF]
                        self._drstatus_power_abs = device_data[ATTR_DRSTATUS][
                            "powerAbsolute"
                        ]
                        self._drstatus_power_rel = device_data[ATTR_DRSTATUS][
                            "powerRelative"
                        ]
                        self._drstatus_setpoint = device_data[ATTR_DRSTATUS][
                            "setpoint"
                        ]
                    self._current_power_w = device_data[ATTR_WIFI_WATT_NOW][
                        "value"
                    ]
                    self._wattage = device_data[ATTR_WIFI_WATTAGE]["value"]
                    self._cold_load_status = device_data[ATTR_COLD_LOAD_PICKUP_STATUS]
                    self._cold_load_temp = device_data[ATTR_COLD_LOAD_PICKUP_TEMP]
                    self._cold_load_remaining_time = device_data[
                        ATTR_COLD_LOAD_PICKUP_REMAIN_TIME
                    ]
                    self._rssi = device_data[ATTR_WIFI]
                    self._mode = device_data[ATTR_SYSTEM_MODE]
                    self._tank_size = device_data[ATTR_TANK_SIZE]
                    self._away_action = device_data[ATTR_AWAY_ACTION]["action"]
                    self._away_payload = device_data[ATTR_AWAY_ACTION][
                        "actionPayload"
                    ]
                    self._leg_status_temp = device_data[ATTR_LEG_PROTEC_STATUS][
                        "temperature"
                    ]
                    self._leg_status_consumption = device_data[
                        ATTR_LEG_PROTEC_STATUS
                    ]["consumption"]
                    self._leg_status_over_time = device_data[ATTR_LEG_PROTEC_STATUS][
                        "consumptionOverTime"
                    ]
                    self._water_temp_min = device_data[ATTR_MIN_WATER_TEMP]
                    self._water_tank_on = device_data[ATTR_WATER_TANK_ON]
                    self._water_temp_time = device_data[ATTR_WATER_TEMP_TIME]
                    self._water_temp_protec = device_data[ATTR_WATER_TEMP_PROTEC]
                    self._water_leak_closure_conf = device_data[
                        ATTR_LEAK_CLOSURE_CONFIG
                    ]
                    if device_data[ATTR_WATER_LEAK_DISCONECTED_STATUS] == "probe":
                        await self.async_notify_ha(
                            f"Warning: Neviweb Device error code detected: "
                            + device_data[ATTR_WATER_LEAK_DISCONECTED_STATUS]
                            + " for device: "
                            + self._name
                            + ", Sku: "
                            + self._sku
                            + ", Leak sensor disconnected"
                        )
                    self.async_write_ha_state()
                else:
                    _LOGGER.warning("Error in reading device %s: (%s)", self._name, device_data)
            else:
                await self.async_log_error(device_data["error"]["code"])
            await self.async_do_stat(start)
        else:
            if time.time() - self._snooze > SNOOZE_TIME:
                self._activ = True
                if self._notify == "notification" or self._notify == "both":
                    await self.async_notify_ha(
                        f"Warning: Neviweb Device update restarted for "
                        + self._name
                        + ", Sku: "
                        + self._sku
                    )

    @property
    def extra_state_attributes(self):
        """Return the extra state attributes."""
        data = {}
        data.update(
            {
                "onOff": self._onoff,
                "wattage": self._wattage,
                "wattage_instant": self._current_power_w,
                "total_kwh_count": self._total_kwh_count,
                "monthly_kwh_count": self._monthly_kwh_count,
                "daily_kwh_count": self._daily_kwh_count,
                "hourly_kwh_count": self._hourly_kwh_count,
                "hourly_kwh": self._hour_kwh,
                "daily_kwh": self._today_kwh,
                "monthly_kwh": self._month_kwh,
                "last_energy_stat_update": self._mark,
                "water_leak_status": self._water_leak_status,
                "water_leak_disconect_status": self._water_leak_disconected_status,
                "water_leak_closure_config": self._water_leak_closure_conf,
                "water_temperature": self._water_temp,
                "cold_load_pickup_status": self._cold_load_status,
                "cold_load_remaining_time": remainig_time(
                    self._cold_load_remaining_time
                ),
                "cold_load_temperature": self._cold_load_temp,
                "tank_size": neviweb_to_ha(self._tank_size),
                "eco_status": self._drstatus_active,
                "eco_optOut": self._drstatus_optout,
                "eco_onoff": self._drstatus_onoff,
                "eco_setpoint": self._drstatus_setpoint,
                "eco_power_absolute": self._drstatus_power_abs,
                "eco_power_relative": self._drstatus_power_rel,
                "water_temp_min": self._water_temp_min,
                "water_time_on": self._water_tank_on,
                "water_temp_time": self._water_temp_time,
                "water_temp_protection_type": self._water_temp_protec,
                "away_action": self._away_action,
                "away_action_payload": self._away_payload,
                "mode": self._mode,
                "leg_status_temperature": self._leg_status_temp,
                "leg_status_consumption": self._leg_status_consumption,
                "leg_status_consumption_over_time": self._leg_status_over_time,
                "error_code": self._error_code,
                "rssi": self._rssi,
                "sku": self._sku,
                "device_model": str(self._device_model),
                "device_model_cfg": self._device_model_cfg,
                "firmware": self._firmware,
                "activation": self._activ,
                "device_type": self._device_type,
                "id": self._id,
            }
        )
        return data


class Neviweb130ControlerSwitch(Neviweb130Switch):
    """Implementation of a Neviweb multi controler switch, MC3100ZB connected to GT130 or Sedna."""

    def __init__(self, data, device_info, name, sku, firmware, device_type, coordinator):
        """Initialize."""
        super().__init__(data, device_info, name, sku, firmware, device_type, coordinator)
        self._device = device_info
        self._name = name
        self._sku = sku
        self._firmware = firmware
        self._client = data['neviweb130_client']
        self._notify = data["notify"]
        self._stat_interval = data["stat_interval"]
        self._id = str(device_info["id"])
        self._device_model = device_info["signature"]["model"]
        self._device_model_cfg = device_info["signature"]["modelCfg"]
        self._device_type = device_type
        self._onoff = None
        self._onoff2 = None
        self._battery_voltage = 0
        self._battery_status = None
        self._batt_percent_normal = None
        self._batt_status_normal = None
        self._batt_info = None
        self._timer = 0
        self._timer2 = 0
        self._drstatus_active = "off"
        self._drstatus_onOff = "off"
        self._humidity = None
        self._ext_temp = None
        self._room_temp = None
        self._input_status = None
        self._input2_status = None
        self._rssi = None
        self._input_name_1 = "Not set"
        self._input_name_2 = "Not set"
        self._output_name_1 = "Not set"
        self._output_name_2 = "Not set"
        self._input_1_on_delay = 0
        self._input_2_on_delay = 0
        self._input_1_off_delay = 0
        self._input_2_off_delay = 0
        self._low_temp_status = None
        self._is_zb_control = (
            device_info["signature"]["model"] in IMPLEMENTED_ZB_DEVICE_CONTROL
        )
        self._is_sedna_control = (
            device_info["signature"]["model"] in IMPLEMENTED_SED_DEVICE_CONTROL
        )
        self._snooze = 0
        self._activ = True
        self._attr_device_info = {
            "identifiers": {(DOMAIN, self._id)},
            "name": self._name,
            "manufacturer": "claudegel",
            "model": self._device_model,
            "sw_version": self._firmware,
        }
        _LOGGER.debug("Setting up %s: %s", self._name, device_info)

    async def async_update(self):
        if self._activ:
            if self._is_zb_control:
                NAME_ATTRIBUTES = [
                    ATTR_NAME_1,
                    ATTR_NAME_2,
                    ATTR_OUTPUT_NAME_1,
                    ATTR_OUTPUT_NAME_2,
                ]
            else:
                NAME_ATTRIBUTES = []
            if self._is_zb_control or self._is_sedna_control:
                if self._firmware == "0.1.1":
                    LOAD_ATTRIBUTES = [
                        ATTR_ONOFF2,
                        ATTR_BATTERY_VOLTAGE,
                        ATTR_BATTERY_STATUS,
                        ATTR_EXT_TEMP,
                        ATTR_REL_HUMIDITY,
                        ATTR_INPUT_STATUS,
                        ATTR_INPUT2_STATUS,
                        ATTR_ROOM_TEMPERATURE,
                        ATTR_TIMER,
                        ATTR_TIMER2,
                        ATTR_RSSI,
                        ATTR_BATT_INFO,
                        ATTR_INPUT_1_ON_DELAY,
                        ATTR_INPUT_2_ON_DELAY,
                        ATTR_INPUT_1_OFF_DELAY,
                        ATTR_INPUT_2_OFF_DELAY,
                        ATTR_BATT_PERCENT_NORMAL,
                        ATTR_BATT_STATUS_NORMAL,
                        ATTR_DRSTATUS,
                        ATTR_LOW_TEMP_STATUS,
                    ]
                else:
                    LOAD_ATTRIBUTES = [
                        ATTR_ONOFF2,
                        ATTR_BATTERY_VOLTAGE,
                        ATTR_BATTERY_STATUS,
                        ATTR_EXT_TEMP,
                        ATTR_REL_HUMIDITY,
                        ATTR_INPUT_STATUS,
                        ATTR_INPUT2_STATUS,
                        ATTR_ROOM_TEMPERATURE,
                        ATTR_TIMER,
                        ATTR_TIMER2,
                        ATTR_RSSI,
                    ]
            """Get the latest data from Neviweb and update the state."""
            start = time.time()
            device_data = await self._client.async_get_device_attributes(
                self._id, UPDATE_ATTRIBUTES + LOAD_ATTRIBUTES + NAME_ATTRIBUTES
            )
            end = time.time()
            elapsed = round(end - start, 3)
            _LOGGER.debug(
                "Updating %s (%s sec): %s", self._name, elapsed, device_data)

            if "error" not in device_data:
                if "errorCode" not in device_data:
                    if self._is_zb_control or self._is_sedna_control:
                        self._onoff = device_data[ATTR_ONOFF]
                        self._onoff2 = device_data[ATTR_ONOFF2]
                        self._battery_status = device_data[ATTR_BATTERY_STATUS]
                        self._battery_voltage = device_data[ATTR_BATTERY_VOLTAGE]
                        self._input_status = device_data[ATTR_INPUT_STATUS]
                        self._input2_status = device_data[ATTR_INPUT2_STATUS]
                        self._humidity = device_data[ATTR_REL_HUMIDITY]
                        self._room_temp = device_data[ATTR_ROOM_TEMPERATURE]
                        self._ext_temp = device_data[ATTR_EXT_TEMP]
                        self._timer = device_data[ATTR_TIMER]
                        self._timer2 = device_data[ATTR_TIMER2]
                        if ATTR_BATT_INFO in device_data:
                            self._batt_info = device_data[ATTR_BATT_INFO]
                        if ATTR_INPUT_1_ON_DELAY in device_data:
                            self._input_1_on_delay = device_data[
                                ATTR_INPUT_1_ON_DELAY
                            ]
                            self._input_2_on_delay = device_data[
                                ATTR_INPUT_2_ON_DELAY
                            ]
                            self._input_1_off_delay = device_data[
                                ATTR_INPUT_1_OFF_DELAY
                            ]
                            self._input_2_off_delay = device_data[
                                ATTR_INPUT_2_OFF_DELAY
                            ]
                        if ATTR_BATT_PERCENT_NORMAL in device_data:
                            self._batt_percent_normal = device_data[
                                ATTR_BATT_PERCENT_NORMAL
                            ]
                        if ATTR_BATT_STATUS_NORMAL in device_data:
                            self._batt_status_normal = device_data[
                                ATTR_BATT_STATUS_NORMAL
                            ]
                        if ATTR_RSSI in device_data:
                            self._rssi = device_data[ATTR_RSSI]
                        if ATTR_LOW_TEMP_STATUS in device_data:
                            self._low_temp_status = device_data[
                                ATTR_LOW_TEMP_STATUS
                            ]
                    if self._is_zb_control:
                        self._input_name_1 = device_data[ATTR_NAME_1]
                        self._input_name_2 = device_data[ATTR_NAME_2]
                        self._output_name_1 = device_data[ATTR_OUTPUT_NAME_1]
                        self._output_name_2 = device_data[ATTR_OUTPUT_NAME_2]
                    if ATTR_DRSTATUS in device_data:
                        self._drstatus_active = device_data[ATTR_DRSTATUS][
                            ATTR_DRACTIVE
                        ]
                        self._drstatus_onOff = device_data[ATTR_DRSTATUS][
                            ATTR_ONOFF
                        ]
                    self.async_write_ha_state()
                else:
                    _LOGGER.warning(
                        "Error in reading device %s: (%s)", self._name, device_data
                    )
            else:
                await self.async_log_error(device_data["error"]["code"])
        else:
            if time.time() - self._snooze > SNOOZE_TIME:
                self._activ = True
                if self._notify == "notification" or self._notify == "both":
                    await self.async_notify_ha(
                        "Warning: Neviweb Device update restarted for "
                        + self._name
                        + ", Sku: "
                        + self._sku
                    )

    @property
    def extra_state_attributes(self):
        """Return the extra state attributes."""
        data = {}
        data.update(
            {
                "battery_level": voltage_to_percentage(self._battery_voltage, 2),
                "battery_display_info": self._batt_info,
                "battery_voltage": self._battery_voltage,
                "battery_status": self._battery_status,
                "battery_percent_normalized": self._batt_percent_normal,
                "battery_status_normalized": self._batt_status_normal,
                "extern_temperature": self._ext_temp,
                "room_temperature": self._room_temp,
                "room_humidity": self._humidity,
                "timer": self._timer,
                "timer2": self._timer2,
                "input1_status": self._input_status,
                "input2_status": self._input2_status,
                "onOff": self._onoff,
                "onOff2": self._onoff2,
                "eco_status": self._drstatus_active,
                "eco_onOff": self._drstatus_onOff,
                "input1_on_delay": neviweb_to_ha_delay(self._input_1_on_delay),
                "input2_on_delay": neviweb_to_ha_delay(self._input_2_on_delay),
                "input1_off_delay": neviweb_to_ha_delay(self._input_1_off_delay),
                "input2_off_delay": neviweb_to_ha_delay(self._input_2_off_delay),
                "input1_name": self._input_name_1,
                "input2_name": self._input_name_2,
                "output1_name": self._output_name_1,
                "output2_name": self._output_name_2,
                "low_temp_status": self._low_temp_status,
                "rssi": self._rssi,
                "sku": self._sku,
                "device_model": str(self._device_model),
                "device_model_cfg": self._device_model_cfg,
                "firmware": self._firmware,
                "activation": self._activ,
                "device_type": self._device_type,
                "id": self._id,
            }
        )
        return data


class Neviweb130DeviceAttributeSwitch(CoordinatorEntity[Neviweb130Coordinator], SwitchEntity):
    """Representation of a specific Neviweb130 device attribute switch."""

    _attr_has_entity_name = True
    _attr_should_poll = True

    def __init__(
        self,
        client: Neviweb130Client,
        device: dict,
        device_name: str,
        attribute: str,
        device_id: str,
        device_type: str,
        attr_info: dict,
        coordinator: Neviweb130Coordinator,
        entity_description: Neviweb130SwitchEntityDescription,
    ):
        """Initialize the switch."""
        super().__init__(coordinator)
        self.coordinator = coordinator
        self.entity_description = entity_description
        self._client = client
        self._device = device
        self._id = str(device.get('id'))
        self._device_name = device_name
        self._attribute = entity_description.key
        self._device_id = device_id
        self._device_type = device_type
        self._state = None
        self._attr_unique_id = f"{self._device_id}_{entity_description.key}"
        self._attr_device_info = attr_info
        self._attr_friendly_name = f"{self._device.get("friendly_name")} {attribute.replace('_', ' ').capitalize()}"
        self._attr_icon = entity_description.icon
        self._attr_device_class = entity_description.device_class
        self._attr_unit_of_measurement = entity_description.native_unit_of_measurement
        self._attr_onoff = None

    @property
    def unique_id(self):
        """Return a unique ID."""
        return self._attr_unique_id

    @property
    def device_id(self):
        """Return device_id."""
        return self._device_id

    @property
    def is_on(self):
        """Return True if the switch is on."""
        return self._attr_onoff != MODE_OFF

    @property
    def state(self):
        """Return the state of the switch."""
        device_obj = self.coordinator.data.get(self._id)
        if device_obj and self._attribute in device_obj:
            value = device_obj[self._attribute]
            return value
        else:
            _LOGGER.warning(
                "AttributeSwitch: %s attribute %s not found for device: %s.",
                self._attr_unique_id, self._attribute, self._id
            )
            return None

    @property
    def extra_state_attributes(self):
        """Return the state attributes of the switch."""
        return {"device_id": self._attr_unique_id}

    async def async_turn_on(self, **kwargs):
        """Turn the switch device on."""
        await self._client.async_set_onoff2(self._id, "on")
        self._attr_onoff = "on"

    async def async_turn_off(self, **kwargs):
        """Turn the switch device off."""
        await self._client.async_set_onoff2(self._id, "off")
        self._attr_onoff = MODE_OFF
