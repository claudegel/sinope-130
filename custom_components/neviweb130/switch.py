"""
Support for Neviweb switch connected to GT130 Zigbee.
Multi-Controller connected to GT130
model 2180 = Multi controller for sedna valve MC3100ZB

Load controller connected to GT130 or Wi-Fi
Support for Neviweb switch connected via GT130 Zigbee.
model 2506 = load controller device, RM3250ZB, 50A, Zigbee
model 346 = load controller device, RM3250WF, 50A, Wi-Fi
model 2151 = Calypso load controller for water heater, RM3500ZB 20,8A, Zigbee
model 2152 = Calypso load controller for water heater, RM3500WF 20,8A, Wi-Fi
model 339 = Calypso load controller for water heater, RM3510WF 20,8A, Wi-Fi
model 2610 = wall outlet, SP2610ZB
model 2600 = portable plug, SP2600ZB

Multi controller connected to Sedna valve
model 2181 = Multi controller for sedna valve MC3100ZB connected sedna valve

Load controller connected to Sedna valve
model 25062 = load controller device, RM3250ZB-VA, 50A, Zigbee

Outlet and plug connected to Sedna valve
model 26102 = wall outlet, SP2610ZB
model 26002 = portable plug, SP2600ZB

For more details about this platform, please refer to the documentation at
https://www.sinopetech.com/en/support/#api
"""

from __future__ import annotations

import logging
import time
from datetime import date, datetime, timezone
from threading import Lock
from typing import override

from homeassistant.components.persistent_notification import DOMAIN as PN_DOMAIN
from homeassistant.components.recorder.models import StatisticMeanType
from homeassistant.components.sensor import SensorStateClass
from homeassistant.components.switch import SwitchDeviceClass, SwitchEntity
from homeassistant.const import ATTR_ENTITY_ID
from homeassistant.core import ServiceCall
from homeassistant.exceptions import ServiceValidationError

from . import NOTIFY
from . import SCAN_INTERVAL as scan_interval
from . import STAT_INTERVAL
from .const import (
    ATTR_ACTIVE,
    ATTR_AWAY_ACTION,
    ATTR_BATT_INFO,
    ATTR_BATT_PERCENT_NORMAL,
    ATTR_BATT_STATUS_NORMAL,
    ATTR_BATTERY_STATUS,
    ATTR_BATTERY_VOLTAGE,
    ATTR_COLD_LOAD_PICKUP_REMAIN_TIME,
    ATTR_COLD_LOAD_PICKUP_STATUS,
    ATTR_COLD_LOAD_PICKUP_TEMP,
    ATTR_CONTROLLED_DEVICE,
    ATTR_DELAY,
    ATTR_DR_PROTEC_STATUS,
    ATTR_DR_WATER_TEMP_TIME,
    ATTR_DRACTIVE,
    ATTR_DRSTATUS,
    ATTR_ERROR_CODE_SET1,
    ATTR_EXT_TEMP,
    ATTR_INPUT2_STATUS,
    ATTR_INPUT_1_OFF_DELAY,
    ATTR_INPUT_1_ON_DELAY,
    ATTR_INPUT_2_OFF_DELAY,
    ATTR_INPUT_2_ON_DELAY,
    ATTR_INPUT_NUMBER,
    ATTR_INPUT_STATUS,
    ATTR_KEYPAD,
    ATTR_LEAK_CLOSURE_CONFIG,
    ATTR_LEG_PROTEC_STATUS,
    ATTR_LOW_TEMP_STATUS,
    ATTR_MIN_WATER_TEMP,
    ATTR_NAME_1,
    ATTR_NAME_2,
    ATTR_ONOFF,
    ATTR_ONOFF2,
    ATTR_ONOFF_NUM,
    ATTR_OPTOUT,
    ATTR_OUTPUT_NAME_1,
    ATTR_OUTPUT_NAME_2,
    ATTR_REL_HUMIDITY,
    ATTR_ROOM_TEMPERATURE,
    ATTR_RSSI,
    ATTR_STATUS,
    ATTR_SYSTEM_MODE,
    ATTR_TANK_SIZE,
    ATTR_TEMP_ALERT,
    ATTR_TIME,
    ATTR_TIMER,
    ATTR_TIMER2,
    ATTR_VALUE,
    ATTR_WATER_LEAK_ALARM_STATUS,
    ATTR_WATER_LEAK_DISCONNECTED_STATUS,
    ATTR_WATER_LEAK_STATUS,
    ATTR_WATER_TANK_ON,
    ATTR_WATER_TEMP_MIN,
    ATTR_WATER_TEMP_PROTECT,
    ATTR_WATER_TEMP_TIME,
    ATTR_WATER_TEMPERATURE,
    ATTR_WATT_TIME_ON,
    ATTR_WATTAGE,
    ATTR_WATTAGE_INSTANT,
    ATTR_WIFI,
    ATTR_WIFI_KEYPAD,
    ATTR_WIFI_WATT_NOW,
    ATTR_WIFI_WATTAGE,
    DOMAIN,
    MODE_OFF,
    SERVICE_SET_ACTIVATION,
    SERVICE_SET_CONTROL_ONOFF,
    SERVICE_SET_CONTROLLED_DEVICE,
    SERVICE_SET_INPUT_OUTPUT_NAMES,
    SERVICE_SET_LOAD_DR_OPTIONS,
    SERVICE_SET_LOW_TEMP_PROTECTION,
    SERVICE_SET_ON_OFF_INPUT_DELAY,
    SERVICE_SET_REMAINING_TIME,
    SERVICE_SET_SWITCH_KEYPAD_LOCK,
    SERVICE_SET_SWITCH_TEMP_ALERT,
    SERVICE_SET_SWITCH_TIMER,
    SERVICE_SET_SWITCH_TIMER_2,
    SERVICE_SET_TANK_SIZE,
    STATE_KEYPAD_STATUS,
    STATE_WATER_LEAK,
    VERSION,
)
from .helpers import translate_error
from .schema import (
    SET_ACTIVATION_SCHEMA,
    SET_CONTROL_ONOFF_SCHEMA,
    SET_CONTROLLED_DEVICE_SCHEMA,
    SET_INPUT_OUTPUT_NAMES_SCHEMA,
    SET_LOAD_DR_OPTIONS_SCHEMA,
    SET_LOW_TEMP_PROTECTION_SCHEMA,
    SET_ON_OFF_INPUT_DELAY_SCHEMA,
    SET_REMAINING_TIME_SCHEMA,
    SET_SWITCH_KEYPAD_LOCK_SCHEMA,
    SET_SWITCH_TEMP_ALERT_SCHEMA,
    SET_SWITCH_TIMER_2_SCHEMA,
    SET_SWITCH_TIMER_SCHEMA,
    SET_TANK_SIZE_SCHEMA,
)

_LOGGER = logging.getLogger(__name__)

SNOOZE_TIME = 1200
SCAN_INTERVAL = scan_interval

UPDATE_ATTRIBUTES = [ATTR_ONOFF]

HA_TO_NEVIWEB_SIZE = {"40 gal": 40, "50 gal": 50, "60 gal": 60, "80 gal": 80}

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
}

HA_TO_NEVIWEB_CONTROLLED = {
    "Hot water heater": "hotWaterHeater",
    "Pool pump": "poolPump",
    "Electric vehicle charger": "electricVehicleCharger",
    "Other": "other",
}

SWITCH_TYPES: dict[str, tuple[str, SwitchDeviceClass]] = {
    "power": ("mdi:switch", SwitchDeviceClass.SWITCH),
    "outlet": ("mdi:power-plug", SwitchDeviceClass.OUTLET),
    "control": ("mdi:alarm", SwitchDeviceClass.SWITCH),
}

IMPLEMENTED_WIFI_WATER_HEATER_LOAD_MODEL = [2152, 339]
IMPLEMENTED_WATER_HEATER_LOAD_MODEL = [2151]
IMPLEMENTED_ZB_DEVICE_CONTROL = [2180]
IMPLEMENTED_SED_DEVICE_CONTROL = [2181]
IMPLEMENTED_WALL_DEVICES = [2600, 2610]
IMPLEMENTED_SED_WALL_DEVICES =[26002, 26102]
IMPLEMENTED_LOAD_DEVICES = [2506]
IMPLEMENTED_SED_LOAD_DEVICES = [25062]
IMPLEMENTED_WIFI_LOAD_DEVICES = [346]
IMPLEMENTED_DEVICE_MODEL = (
    IMPLEMENTED_LOAD_DEVICES
    + IMPLEMENTED_SED_LOAD_DEVICES
    + IMPLEMENTED_WALL_DEVICES
    + IMPLEMENTED_SED_WALL_DEVICES
    + IMPLEMENTED_ZB_DEVICE_CONTROL
    + IMPLEMENTED_SED_DEVICE_CONTROL
    + IMPLEMENTED_WATER_HEATER_LOAD_MODEL
    + IMPLEMENTED_WIFI_WATER_HEATER_LOAD_MODEL
    + IMPLEMENTED_WIFI_LOAD_DEVICES
)


async def async_setup_platform(
    hass,
    config,
    async_add_entities,
    discovery_info=None,
) -> None:
    """Set up the Neviweb130 switch."""
    data = hass.data[DOMAIN]["data"]

    # Wait for async migration to be done
    await data.migration_done.wait()

    entities: list[Neviweb130Switch] = []

    # Loop through all clients (supports multi-account)
    for client in data.neviweb130_clients:
        default_name = client.default_group_name("switch")
        default_name_2 = client.default_group_name("switch", 2)
        default_name_3 = client.default_group_name("switch", 3)

        # Process gateway_data for this client
        for device_info in client.gateway_data:
            if (
                "signature" in device_info
                and "model" in device_info["signature"]
                and device_info["signature"]["model"] in IMPLEMENTED_DEVICE_MODEL
            ):
                device_name = "{} {}".format(default_name, device_info["name"])
                device_sku = device_info["sku"]
                device_firmware = "{}.{}.{}".format(
                    device_info["signature"]["softVersion"]["major"],
                    device_info["signature"]["softVersion"]["middle"],
                    device_info["signature"]["softVersion"]["minor"],
                )
                if (
                    device_info["signature"]["model"] in IMPLEMENTED_WALL_DEVICES
                    or device_info["signature"]["model"] in IMPLEMENTED_SED_WALL_DEVICES
                ):
                    device_type = "outlet"
                    entities.append(
                        Neviweb130Switch(device_info, device_name, device_sku, device_firmware, device_type, client)
                    )
                elif (
                    device_info["signature"]["model"] in IMPLEMENTED_LOAD_DEVICES
                    or device_info["signature"]["model"] in IMPLEMENTED_SED_LOAD_DEVICES
                ):
                    device_type = "power"
                    entities.append(
                        Neviweb130PowerSwitch(
                            device_info, device_name, device_sku, device_firmware, device_type, client
                        )
                    )
                elif device_info["signature"]["model"] in IMPLEMENTED_WIFI_LOAD_DEVICES:
                    device_type = "power"
                    entities.append(
                        Neviweb130WifiPowerSwitch(
                            device_info, device_name, device_sku, device_firmware, device_type, client
                        )
                    )
                elif device_info["signature"]["model"] in IMPLEMENTED_WATER_HEATER_LOAD_MODEL:
                    device_type = "power"
                    entities.append(
                        Neviweb130TankPowerSwitch(
                            device_info, device_name, device_sku, device_firmware, device_type, client
                        )
                    )
                elif device_info["signature"]["model"] in IMPLEMENTED_WIFI_WATER_HEATER_LOAD_MODEL:
                    device_type = "power"
                    entities.append(
                        Neviweb130WifiTankPowerSwitch(
                            device_info, device_name, device_sku, device_firmware, device_type, client
                        )
                    )
                else:  # IMPLEMENTED_ZB_DEVICE_CONTROL or model in IMPLEMENTED_SED_DEVICE_CONTROL
                    device_type = "control"  
                    entities.append(
                        Neviweb130ControlerSwitch(
                            device_info, device_name, device_sku, device_firmware, device_type, client
                        )
                    )
        for device_info in client.gateway_data2:
            if (
                "signature" in device_info
                and "model" in device_info["signature"]
                and device_info["signature"]["model"] in IMPLEMENTED_DEVICE_MODEL
            ):
                device_name = "{} {}".format(default_name_2, device_info["name"])
                device_sku = device_info["sku"]
                device_firmware = "{}.{}.{}".format(
                    device_info["signature"]["softVersion"]["major"],
                    device_info["signature"]["softVersion"]["middle"],
                    device_info["signature"]["softVersion"]["minor"],
                )
                if (
                    device_info["signature"]["model"] in IMPLEMENTED_WALL_DEVICES
                    or device_info["signature"]["model"] in IMPLEMENTED_SED_WALL_DEVICES
                ):
                    device_type = "outlet"
                    entities.append(
                        Neviweb130Switch(device_info, device_name, device_sku, device_firmware, device_type, client)
                    )
                elif (
                    device_info["signature"]["model"] in IMPLEMENTED_LOAD_DEVICES
                    or device_info["signature"]["model"] in IMPLEMENTED_SED_LOAD_DEVICES
                ):
                    device_type = "power"
                    entities.append(
                        Neviweb130PowerSwitch(
                            device_info, device_name, device_sku, device_firmware, device_type, client
                        )
                    )
                elif device_info["signature"]["model"] in IMPLEMENTED_WIFI_LOAD_DEVICES:
                    device_type = "power"
                    entities.append(
                        Neviweb130WifiPowerSwitch(
                            device_info, device_name, device_sku, device_firmware, device_type, client
                        )
                    )
                elif device_info["signature"]["model"] in IMPLEMENTED_WATER_HEATER_LOAD_MODEL:
                    device_type = "power"
                    entities.append(
                        Neviweb130TankPowerSwitch(
                            device_info, device_name, device_sku, device_firmware, device_type, client
                        )
                    )
                elif device_info["signature"]["model"] in IMPLEMENTED_WIFI_WATER_HEATER_LOAD_MODEL:
                    device_type = "power"
                    entities.append(
                        Neviweb130WifiTankPowerSwitch(
                            device_info, device_name, device_sku, device_firmware, device_type, client
                        )
                    )
                else:  # IMPLEMENTED_ZB_DEVICE_CONTROL or model in IMPLEMENTED_SED_DEVICE_CONTROL
                    device_type = "control"
                    entities.append(
                        Neviweb130ControlerSwitch(
                            device_info, device_name, device_sku, device_firmware, device_type, client
                        )
                    )
        for device_info in client.gateway_data3:
            if (
                "signature" in device_info
                and "model" in device_info["signature"]
                and device_info["signature"]["model"] in IMPLEMENTED_DEVICE_MODEL
            ):
                device_name = "{} {}".format(default_name_3, device_info["name"])
                device_sku = device_info["sku"]
                device_firmware = "{}.{}.{}".format(
                    device_info["signature"]["softVersion"]["major"],
                    device_info["signature"]["softVersion"]["middle"],
                    device_info["signature"]["softVersion"]["minor"],
                )
                if (
                    device_info["signature"]["model"] in IMPLEMENTED_WALL_DEVICES
                    or device_info["signature"]["model"] in IMPLEMENTED_SED_WALL_DEVICES
                ):
                    device_type = "outlet"
                    entities.append(
                        Neviweb130Switch(device_info, device_name, device_sku, device_firmware, device_type, client)
                    )
                elif (
                    device_info["signature"]["model"] in IMPLEMENTED_LOAD_DEVICES
                    or device_info["signature"]["model"] in IMPLEMENTED_SED_LOAD_DEVICES
                ):
                    device_type = "power"
                    entities.append(
                        Neviweb130PowerSwitch(
                            device_info, device_name, device_sku, device_firmware, device_type, client
                        )
                    )
                elif device_info["signature"]["model"] in IMPLEMENTED_WIFI_LOAD_DEVICES:
                    device_type = "power"
                    entities.append(
                        Neviweb130WifiPowerSwitch(
                            device_info, device_name, device_sku, device_firmware, device_type, client
                        )
                    )
                elif device_info["signature"]["model"] in IMPLEMENTED_WATER_HEATER_LOAD_MODEL:
                    device_type = "power"
                    entities.append(
                        Neviweb130TankPowerSwitch(
                            device_info, device_name, device_sku, device_firmware, device_type, client
                        )
                    )
                elif device_info["signature"]["model"] in IMPLEMENTED_WIFI_WATER_HEATER_LOAD_MODEL:
                    device_type = "power"
                    entities.append(
                        Neviweb130WifiTankPowerSwitch(
                            device_info, device_name, device_sku, device_firmware, device_type, client
                        )
                    )
                else:  # IMPLEMENTED_ZB_DEVICE_CONTROL or model in IMPLEMENTED_SED_DEVICE_CONTROL
                    device_type = "control"
                    entities.append(
                        Neviweb130ControlerSwitch(
                            device_info, device_name, device_sku, device_firmware, device_type, client
                        )
                    )

    async_add_entities(entities, True)

    entity_map: dict[str, Neviweb130Switch] | None = None
    _entity_map_lock = Lock()

    def get_switch(service: ServiceCall) -> Neviweb130Switch:
        entity_id = service.data.get(ATTR_ENTITY_ID)
        if entity_id is None:
            msg = translate_error(hass, "missing_parameter", param=ATTR_ENTITY_ID)
            raise ServiceValidationError(msg)

        nonlocal entity_map
        if entity_map is None:
            with _entity_map_lock:
                if entity_map is None:
                    entity_map = {entity.entity_id: entity for entity in entities if entity.entity_id is not None}
                    if len(entity_map) != len(entities):
                        entity_map = None
                        msg = translate_error(hass, "entities_not_ready")
                        raise ServiceValidationError(msg)

        switch = entity_map.get(entity_id)
        if switch is None:
            msg = translate_error(hass, "entity_must_be_domain", entity=entity_id, domain=DOMAIN, platform="switch")
            raise ServiceValidationError(msg)
        return switch

    def set_switch_keypad_lock_service(service: ServiceCall) -> None:
        """Lock/unlock keypad device."""
        switch = get_switch(service)
        value = {"id": switch.unique_id, "lock": service.data[ATTR_KEYPAD]}
        switch.set_keypad_lock(value)
        switch.schedule_update_ha_state(True)

    def set_switch_timer_service(service: ServiceCall) -> None:
        """Set timer for switch device."""
        switch = get_switch(service)
        value = {"id": switch.unique_id, ATTR_TIME: service.data[ATTR_TIMER]}
        switch.set_timer(value)
        switch.schedule_update_ha_state(True)

    def set_switch_timer2_service(service: ServiceCall) -> None:
        """Set timer for switch device."""
        switch = get_switch(service)
        value = {"id": switch.unique_id, ATTR_TIME: service.data[ATTR_TIMER2]}
        switch.set_timer2(value)
        switch.schedule_update_ha_state(True)

    def set_switch_temp_alert_service(service: ServiceCall) -> None:
        """Set low temperature alert for switch device MC3100ZB."""
        switch = get_switch(service)
        value = {"id": switch.unique_id, "alert": service.data[ATTR_TEMP_ALERT]}
        switch.set_temp_alert(value)
        switch.schedule_update_ha_state(True)

    def set_load_dr_options_service(service: ServiceCall) -> None:
        """Set dr mode options for load controller."""
        switch = get_switch(service)
        value = {
            "id": switch.unique_id,
            "dractive": service.data[ATTR_DRACTIVE],
            "droptout": service.data[ATTR_OPTOUT],
            "onoff": service.data[ATTR_ONOFF],
        }
        switch.set_load_dr_options(value)
        switch.schedule_update_ha_state(True)

    def set_control_onoff_service(service: ServiceCall) -> None:
        """Set status of both onoff controller."""
        switch = get_switch(service)
        value = {
            "id": switch.unique_id,
            "onoff_num": service.data[ATTR_ONOFF_NUM],
            "status": service.data[ATTR_STATUS],
        }
        switch.set_control_onoff(value)
        switch.schedule_update_ha_state(True)

    def set_tank_size_service(service: ServiceCall) -> None:
        """Set water tank size for RM3500ZB."""
        switch = get_switch(service)
        value = {"id": switch.unique_id, "val": service.data[ATTR_VALUE][0]}
        switch.set_tank_size(value)
        switch.schedule_update_ha_state(True)

    def set_controlled_device_service(service: ServiceCall) -> None:
        """Set controlled device type for RM3250ZB."""
        switch = get_switch(service)
        value = {"id": switch.unique_id, "val": service.data[ATTR_VALUE][0]}
        switch.set_controlled_device(value)
        switch.schedule_update_ha_state(True)

    def set_low_temp_protection_service(service: ServiceCall) -> None:
        """Set water tank temperature protection for RM3500ZB."""
        switch = get_switch(service)
        value = {
            "id": switch.unique_id,
            "val": service.data[ATTR_WATER_TEMP_MIN],
        }
        switch.set_low_temp_protection(value)
        switch.schedule_update_ha_state(True)

    def set_input_output_names_service(service: ServiceCall) -> None:
        """Set names for input 1 and 2, output 1 and 2 for MC3100ZB device."""
        switch = get_switch(service)
        value = {
            "id": switch.unique_id,
            "input1": service.data[ATTR_NAME_1],
            "input2": service.data[ATTR_NAME_2],
            "output1": service.data[ATTR_OUTPUT_NAME_1],
            "output2": service.data[ATTR_OUTPUT_NAME_2],
        }
        switch.set_input_output_names(value)
        switch.schedule_update_ha_state(True)

    def set_activation_service(service: ServiceCall) -> None:
        """Activate or deactivate Neviweb polling for missing device."""
        switch = get_switch(service)
        value = {"id": switch.unique_id, "active": service.data[ATTR_ACTIVE]}
        switch.set_activation(value)
        switch.schedule_update_ha_state(True)

    def set_remaining_time_service(service: ServiceCall) -> None:
        """Set coldLoadPickupRemainingTime value."""
        switch = get_switch(service)
        value = {
            "id": switch.unique_id,
            ATTR_TIME: service.data[ATTR_COLD_LOAD_PICKUP_REMAIN_TIME],
        }
        switch.set_remaining_time(value)
        switch.schedule_update_ha_state(True)

    def set_on_off_input_delay_service(service: ServiceCall) -> None:
        """Set input 1 or 2 on/off delay for MC3100ZB device."""
        switch = get_switch(service)
        value = {
            "id": switch.unique_id,
            "input_number": service.data[ATTR_INPUT_NUMBER],
            "onoff": service.data[ATTR_ONOFF],
            "delay": service.data[ATTR_DELAY][0],
        }
        switch.set_on_off_input_delay(value)
        switch.schedule_update_ha_state(True)

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
        SERVICE_SET_SWITCH_TEMP_ALERT,
        set_switch_temp_alert_service,
        schema=SET_SWITCH_TEMP_ALERT_SCHEMA,
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
    """ "No action", "Close and send", "Close only", "Send only." """
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
    return None


def remaining_time(time_val):
    """Convert time countdown for RM3500ZB."""
    if time_val == 65535:
        return "off"
    return time_val


class Neviweb130Switch(SwitchEntity):
    """Implementation of a Neviweb switch, SP2600ZB and SP2610ZB."""

    def __init__(self, device_info, name, sku, firmware, device_type, client):
        """Initialize."""
        _LOGGER.debug("Setting up %s: %s", name, device_info)
        self._attr_state_class = SensorStateClass.TOTAL
        self._attr_unit_class = "energy"
        self._attr_statistic_mean_type = StatisticMeanType.ARITHMETIC

        self._name = name
        self._sku = sku
        self._firmware = firmware
        self._client = client
        self._id = str(device_info["id"])
        self._device_model = device_info["signature"]["model"]
        self._device_model_cfg = device_info["signature"]["modelCfg"]
        self._device_type = device_type
        self._is_wall = device_info["signature"]["model"] in IMPLEMENTED_WALL_DEVICES
        self._is_sedna_wall = device_info["signature"]["model"] in IMPLEMENTED_SED_WALL_DEVICES
        self._is_load = device_info["signature"]["model"] in IMPLEMENTED_LOAD_DEVICES
        self._is_wifi_load = device_info["signature"]["model"] in IMPLEMENTED_WIFI_LOAD_DEVICES
        self._is_sedna_load = device_info["signature"]["model"] in IMPLEMENTED_SED_LOAD_DEVICES
        self._is_tank_load = device_info["signature"]["model"] in IMPLEMENTED_WATER_HEATER_LOAD_MODEL
        self._is_wifi_tank_load = device_info["signature"]["model"] in IMPLEMENTED_WIFI_WATER_HEATER_LOAD_MODEL
        self._is_zb_control = device_info["signature"]["model"] in IMPLEMENTED_ZB_DEVICE_CONTROL
        self._is_sedna_control = device_info["signature"]["model"] in IMPLEMENTED_SED_DEVICE_CONTROL
        self._active = True
        self._battery_voltage = 0
        self._cold_load_remaining_time = 0
        self._controlled_device = None
        self._cur_temp = None
        self._current_power_w = 0
        self._daily_kwh_count = 0
        self._drstatus_active = "off"
        self._drstatus_onoff = "off"
        self._drstatus_optout = "off"
        self._energy_stat_time = time.time() - 1500
        self._hour_kwh = 0
        self._hourly_kwh_count = 0
        self._input_1_off_delay = 0
        self._input_1_on_delay = 0
        self._input_2_off_delay = 0
        self._input_2_on_delay = 0
        self._input_name_1 = "Not set"
        self._input_name_2 = "Not set"
        self._keypad = None
        self._mark = 0
        self._marker: int | None = None
        self._month_kwh = 0
        self._monthly_kwh_count = 0
        self._onoff = None
        self._onoff2 = None
        self._output_name_1 = "Not set"
        self._output_name_2 = "Not set"
        self._room_temp = None
        self._snooze = 0.0
        self._tank_size = None
        self._temp_alert = None
        self._timer = 0
        self._timer2 = 0
        self._today_kwh = 0
        self._total_kwh_count = 0
        self._water_temp_min = None

    def update(self):
        if self._active:
            if self._is_wall:
                LOAD_ATTRIBUTES = [ATTR_WATTAGE_INSTANT]
            else:
                LOAD_ATTRIBUTES = []
            """Get the latest data from Neviweb and update the state."""
            start = time.time()
            device_data = self._client.get_device_attributes(self._id, UPDATE_ATTRIBUTES + LOAD_ATTRIBUTES)
            end = time.time()
            elapsed = round(end - start, 3)
            _LOGGER.debug("Updating %s (%s sec): %s", self._name, elapsed, device_data)
            if "error" not in device_data:
                if "errorCode" not in device_data:
                    if self._is_wall:
                        self._current_power_w = device_data[ATTR_WATTAGE_INSTANT]
                    self._onoff = device_data[ATTR_ONOFF]
                else:
                    _LOGGER.warning("Error reading device %s: (%s)", self._name, device_data)
            else:
                self.log_error(device_data["error"]["code"])
            if self._is_wall:
                self.do_stat(start)
        else:
            if time.time() - self._snooze > SNOOZE_TIME:
                self._active = True
                if NOTIFY == "notification" or NOTIFY == "both":
                    self.notify_ha(translate_error(self.hass, "update_restarted", name=self._name, sku=self._sku))

    @property
    @override
    def unique_id(self) -> str:
        """Return unique ID based on Neviweb device ID."""
        return self._client.scoped_unique_id(self._id)

    @property
    @override
    def name(self) -> str:
        """Return the name of the switch."""
        return self._name

    @property
    @override
    def icon(self) -> str | None:
        """Return the icon to use in the frontend."""
        device_info = SWITCH_TYPES.get(self._device_type)
        if device_info is None:
            return None

        return device_info[0]

    @property
    @override
    def device_class(self) -> SwitchDeviceClass | None:
        """Return the device class of this entity."""
        device_info = SWITCH_TYPES.get(self._device_type)
        if device_info is None:
            return None

        return device_info[1]

    @property
    def is_on(self):
        """Return current operation i.e. ON, OFF."""
        return self._onoff != MODE_OFF

    def turn_on(self, **kwargs):
        """Turn the device on."""
        self._client.set_onoff(self._id, "on")
        self._onoff = "on"

    def turn_off(self, **kwargs):
        """Turn the device off."""
        self._client.set_onoff(self._id, "off")
        self._onoff = MODE_OFF

    @property
    def keypad_status(self):
        """Return current keypad status, unlocked, locked or partially locked."""
        if self._keypad is not None:
            return lock_to_ha(self._keypad)
        return False

    @property
    def current_temperature(self):
        """Return the current controller temperature."""
        if self._is_zb_control or self._is_sedna_control or self._is_tank_load:
            return self._room_temp
        else:
            return self._cur_temp

    @property
    def extra_state_attributes(self):
        """Return the extra state attributes."""
        data = {}
        data.update(
            {
                "onOff": self._onoff
            }
        )
        if self._is_wall:
            data.update(
                {
                    "wattage_instant": self._current_power_w,
                    "total_kwh_count": self._total_kwh_count,
                    "monthly_kwh_count": self._monthly_kwh_count,
                    "daily_kwh_count": self._daily_kwh_count,
                    "hourly_kwh_count": self._hourly_kwh_count,
                    "hourly_kwh": self._hour_kwh,
                    "daily_kwh": self._today_kwh,
                    "monthly_kwh": self._month_kwh,
                    "last_energy_stat_update": self._mark,
                }
            )
        data.update(
            {
                "sku": self._sku,
                "device_model": str(self._device_model),
                "device_model_cfg": self._device_model_cfg,
                "firmware": self._firmware,
                "activation": self._active,
                "device_type": self._device_type,
                "id": self._id,
            }
        )
        return data

    @property
    def battery_voltage(self):
        """Return the current battery voltage of the controller in %."""
        return voltage_to_percentage(self._battery_voltage, 2 if self._is_zb_control or self._is_sedna_control else 4)

    @property
    def is_standby(self):
        """Return true if device is in standby."""
        return self._current_power_w == 0

    def set_control_onoff(self, value):
        """Set onOff or onOff2 to on or off"""
        self._client.set_control_onoff(value["id"], value["onoff_num"], value["status"])
        if value["onoff_num"] == 1:
            self._onoff = value["status"]
        else:
            self._onoff2 = value["status"]

    def set_keypad_lock(self, value):
        """Lock or unlock device's keypad, lock = locked, unlock = unlocked, partiallyLocked - partial lock."""
        if self._is_wifi_load or self._is_wifi_tank_load:
            self._client.set_keypad_lock(value["id"], value["lock"], True)
        else:
            self._client.set_keypad_lock(value["id"], value["lock"], False)
        self._keypad = value["lock"]

    def set_timer(self, value):
        """Set device timer, 0 = off, 1 to 255 = timer length."""
        self._client.set_timer(value["id"], value[ATTR_TIME])
        self._timer = value[ATTR_TIME]

    def set_timer2(self, value):
        """Set device timer 2 for Multi controller, 0 = off, 1 to 255 = timer length."""
        self._client.set_timer2(value["id"], value[ATTR_TIME])
        self._timer2 = value[ATTR_TIME]

    def set_temp_alert(self, value):
        """Set low temperature alert on/off for MC3100ZB."""
        self._client.set_switch_temp_alert(value["id"], value["alert"])
        self._temp_alert = value["alert"]

    def set_load_dr_options(self, value):
        """Set load controller Éco Sinopé attributes."""
        self._client.set_load_dr_options(value["id"], value["onoff"], value["droptout"], value["dractive"])
        self._drstatus_active = value["dractive"]
        self._drstatus_optout = value["droptout"]
        self._drstatus_onoff = value["onoff"]

    def set_tank_size(self, value):
        """Set water tank size for RM3500ZB Calypso controller."""
        val = value["val"]
        size = [v for k, v in HA_TO_NEVIWEB_SIZE.items() if k == val][0]
        self._client.set_tank_size(value["id"], size)
        self._tank_size = size

    def set_controlled_device(self, value):
        """Set device name controlled by RM3250ZB load controller."""
        val = value["val"]
        type_val = [v for k, v in HA_TO_NEVIWEB_CONTROLLED.items() if k == val][0]
        self._client.set_controlled_device(value["id"], type_val)
        self._controlled_device = type_val

    def set_low_temp_protection(self, value):
        """Set water temperature protection for Calypso."""
        self._client.set_low_temp_protection(value["id"], value["val"])
        self._water_temp_min = value["val"]

    def set_activation(self, value):
        """Activate or deactivate neviweb polling for a missing device."""
        self._active = value["active"]

    def set_remaining_time(self, value):
        """Set coldLoadPickupRemainingTime value."""
        self._client.set_remaining_time(value["id"], value[ATTR_TIME])
        self._cold_load_remaining_time = value[ATTR_TIME]

    def set_on_off_input_delay(self, value):
        """Set input 1 or 2 on/off delay in seconds."""
        val = value["delay"]
        delay = [v for k, v in HA_TO_NEVIWEB_DELAY.items() if k == val][0]
        self._client.set_on_off_input_delay(value["id"], delay, value["onoff"], value["input_number"])
        if value["input_number"] == 1:
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

    def set_input_output_names(self, value):
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
        self._client.set_input_output_names(value["id"], in_1, in_2, out_1, out_2)
        self._input_name_1 = in_1
        self._input_name_2 = in_2
        self._output_name_1 = out_1
        self._output_name_2 = out_2

    def do_stat(self, start):
        """Get device energy statistic."""
        if start - self._energy_stat_time > STAT_INTERVAL and self._energy_stat_time != 0:
            today = date.today()
            current_month = today.month
            current_day = today.day
            device_monthly_stats = self._client.get_device_monthly_stats(self._id, False)
            #            _LOGGER.warning("%s device_monthly_stats = %s", self._name, device_monthly_stats)
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
                msg = translate_error(self.hass, "no_stat", param="monthly", name=self._name)
                _LOGGER.warning(msg)
            device_daily_stats = self._client.get_device_daily_stats(self._id, False)
            #            _LOGGER.debug("%s device_daily_stats = %s", self._name, device_daily_stats)
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
                msg = translate_error(self.hass, "no_stat", param="daily", name=self._name)
                _LOGGER.warning(msg)
            device_hourly_stats = self._client.get_device_hourly_stats(self._id, False)
            #            _LOGGER.debug("%s device_hourly_stats = %s", self._name, device_hourly_stats)
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
                msg = translate_error(self.hass, "no_stat", param="hourly", name=self._name)
                _LOGGER.warning(msg)
            if self._total_kwh_count == 0:
                self._total_kwh_count = round(
                    self._monthly_kwh_count + self._daily_kwh_count + self._hourly_kwh_count,
                    3,
                )
                # async_add_data(self._id, self._total_kwh_count, self._marker)
                # self.async_write_ha_state()
                self._mark = self._marker if self._marker is not None else 0
            else:
                if self._marker != self._mark:
                    self._total_kwh_count += round(self._hour_kwh, 3)
                    # save_data(self._id, self._total_kwh_count, self._marker)
                    self._mark = self._marker if self._marker is not None else 0
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
                    "Set your scan_interval parameter to less than 10 minutes to avoid this... Reconnecting..."
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
                "Device action not supported for %s (id: %s)... (SKU: %s) Report to maintainer",
                self._name,
                str(self._id),
                self._sku,
            )
        elif error_data == "DVCCOMMTO":
            _LOGGER.warning(
                "Device Communication Timeout for %s (id: %s)... The device "
                + "did not respond to the server within the prescribed delay"
                + " (SKU: %s)",
                self._name,
                str(self._id),
                self._sku,
            )
        elif error_data == "SVCERR":
            _LOGGER.warning(
                "Service error, device not available retry later %s (id: %s): %s... (SKU: %s)",
                self._name,
                str(self._id),
                error_data,
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
                msg = translate_error(self.hass, "update_stopped", name=self._name, id=self._id, sku=self._sku)
                self.notify_ha(msg)
            self._active = False
            self._snooze = time.time()
        else:
            msg = translate_error(
                self.hass,
                "unknown_error",
                name=self._name,
                id=self._id,
                sku=self._sku,
                data=error_data
            )
            _LOGGER.warning(msg)

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


class Neviweb130PowerSwitch(Neviweb130Switch):
    """Implementation of a Neviweb power controller switch, RM3250ZB connected to GT130 or Sedna."""

    def __init__(self, device_info, name, sku, firmware, device_type, client):
        """Initialize."""
        super().__init__(device_info, name, sku, firmware, device_type, client)
        self._error_code = None
        self._rssi = None
        self._wattage = 0

    def update(self):
        if self._active:
            if self._is_load:
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
            else:
                LOAD_ATTRIBUTES = []
            """Get the latest data from Neviweb and update the state."""
            start = time.time()
            device_data = self._client.get_device_attributes(self._id, UPDATE_ATTRIBUTES + LOAD_ATTRIBUTES)
            end = time.time()
            elapsed = round(end - start, 3)
            _LOGGER.debug("Updating %s (%s sec): %s", self._name, elapsed, device_data)
            if "error" not in device_data:
                if "errorCode" not in device_data:
                    self._onoff = device_data[ATTR_ONOFF]
                    if not self._is_sedna_load:
                        self._current_power_w = device_data[ATTR_WATTAGE_INSTANT]
                        self._wattage = device_data[ATTR_WATTAGE]
                        self._keypad = STATE_KEYPAD_STATUS if device_data[ATTR_KEYPAD] == STATE_KEYPAD_STATUS else "locked"
                        self._timer = device_data[ATTR_TIMER]
                        if ATTR_DRSTATUS in device_data:
                            self._drstatus_active = device_data[ATTR_DRSTATUS][ATTR_DRACTIVE]
                            self._drstatus_optout = device_data[ATTR_DRSTATUS][ATTR_OPTOUT]
                            self._drstatus_onoff = device_data[ATTR_DRSTATUS][ATTR_ONOFF]
                        if ATTR_ERROR_CODE_SET1 in device_data and len(device_data[ATTR_ERROR_CODE_SET1]) > 0:
                            if device_data[ATTR_ERROR_CODE_SET1]["raw"] != 0:
                                self._error_code = device_data[ATTR_ERROR_CODE_SET1]["raw"]
                                msg = translate_error(
                                    self.hass,
                                    "error_code",
                                    code=device_data[ATTR_ERROR_CODE_SET1]["raw"],
                                    message="",
                                    name=self._name,
                                    id=self._id,
                                    sku=self._sku
                                )
                                self.notify_ha(msg)
                        else:
                            self._error_code = 0
                        if ATTR_RSSI in device_data:
                            self._rssi = device_data[ATTR_RSSI]
                        self._controlled_device = device_data[ATTR_CONTROLLED_DEVICE]
                else:
                    _LOGGER.warning("Error in reading device %s: (%s)", self._name, device_data)
            else:
                self.log_error(device_data["error"]["code"])
            if self._is_load:
                self.do_stat(start)
        else:
            if time.time() - self._snooze > SNOOZE_TIME:
                self._active = True
                if NOTIFY == "notification" or NOTIFY == "both":
                    self.notify_ha(translate_error(self.hass, "update_restarted", name=self._name, sku=self._sku))

    @property
    def extra_state_attributes(self):
        """Return the extra state attributes."""
        data = {}
        data.update(
            {
                "onOff": self._onoff
            }
        )
        if not self._is_sedna_load:
            data.update(
                {
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
                    "rssi": self._rssi,
                }
            )
        data.update(
            {
                "sku": self._sku,
                "device_model": str(self._device_model),
                "device_model_cfg": self._device_model_cfg,
                "firmware": self._firmware,
                "activation": self._active,
                "device_type": self._device_type,
                "id": self._id,
            }
        )

        return data


class Neviweb130WifiPowerSwitch(Neviweb130Switch):
    """Implementation of a Neviweb power controller switch, RM3250WF."""

    def __init__(self, device_info, name, sku, firmware, device_type, client):
        """Initialize."""
        super().__init__(device_info, name, sku, firmware, device_type, client)
        self._error_code = None
        self._wattage = 0
        self._wifirssi = None

    def update(self):
        if self._active:
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
            device_data = self._client.get_device_attributes(self._id, UPDATE_ATTRIBUTES + LOAD_ATTRIBUTES)
            end = time.time()
            elapsed = round(end - start, 3)
            _LOGGER.debug("Updating %s (%s sec): %s", self._name, elapsed, device_data)
            if "error" not in device_data:
                if "errorCode" not in device_data:
                    self._onoff = device_data[ATTR_ONOFF]
                    self._current_power_w = device_data[ATTR_WATTAGE_INSTANT]
                    self._wattage = device_data[ATTR_WIFI_WATTAGE]
                    self._keypad = (
                        STATE_KEYPAD_STATUS if device_data[ATTR_WIFI_KEYPAD] == STATE_KEYPAD_STATUS else "locked"
                    )
                    if ATTR_DRSTATUS in device_data:
                        self._drstatus_active = device_data[ATTR_DRSTATUS][ATTR_DRACTIVE]
                        self._drstatus_optout = device_data[ATTR_DRSTATUS][ATTR_OPTOUT]
                        self._drstatus_onoff = device_data[ATTR_DRSTATUS][ATTR_ONOFF]
                    if ATTR_ERROR_CODE_SET1 in device_data and len(device_data[ATTR_ERROR_CODE_SET1]) > 0:
                        if device_data[ATTR_ERROR_CODE_SET1]["raw"] != 0:
                            self._error_code = device_data[ATTR_ERROR_CODE_SET1]["raw"]
                            msg = translate_error(
                                self.hass,
                                "error_code",
                                code=str(device_data[ATTR_ERROR_CODE_SET1]["raw"]),
                                message="",
                                name=self._name,
                                id=self._id,
                                sku=self._sku
                            )
                            self.notify_ha(msg)
                    else:
                        self._error_code = 0
                    if ATTR_WIFI in device_data:
                        self._wifirssi = device_data[ATTR_WIFI]
                    self._controlled_device = device_data[ATTR_CONTROLLED_DEVICE]
                else:
                    _LOGGER.warning("Error in reading device %s: (%s)", self._name, device_data)
            else:
                self.log_error(device_data["error"]["code"])
            self.do_stat(start)
        else:
            if time.time() - self._snooze > SNOOZE_TIME:
                self._active = True
                if NOTIFY == "notification" or NOTIFY == "both":
                    self.notify_ha(translate_error(self.hass, "update_restarted", name=self._name, sku=self._sku))

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
                "activation": self._active,
                "device_type": self._device_type,
                "id": self._id,
            }
        )
        return data


class Neviweb130TankPowerSwitch(Neviweb130Switch):
    """Implementation of a Neviweb water heater power controller switch, RM3500ZB."""

    def __init__(self, device_info, name, sku, firmware, device_type, client):
        """Initialize."""
        super().__init__(device_info, name, sku, firmware, device_type, client)
        self._cold_load_status = None
        self._consumption = None
        self._consumption_time = None
        self._drstatus_optout_reason = "off"
        self._error_code = None
        self._rssi = None
        self._temperature = None
        self._water_leak_status = None
        self._water_temp = None
        self._water_temp_protect = None
        self._water_temp_time = None
        self._watt_time_on = None
        self._wattage = 0

    def update(self):
        if self._active:
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
                ATTR_WATER_TEMP_PROTECT,
            ]
            """Get the latest data from Neviweb and update the state."""
            start = time.time()
            device_data = self._client.get_device_attributes(self._id, UPDATE_ATTRIBUTES + LOAD_ATTRIBUTES)
            end = time.time()
            elapsed = round(end - start, 3)
            _LOGGER.debug("Updating %s (%s sec): %s", self._name, elapsed, device_data)
            if "error" not in device_data:
                if "errorCode" not in device_data:
                    self._onoff = device_data[ATTR_ONOFF]
                    if ATTR_WATER_LEAK_STATUS in device_data:
                        if device_data[ATTR_WATER_LEAK_STATUS] == "probe":
                            msg = translate_error(
                                self.hass,
                                "error_code",
                                code=device_data[ATTR_WATER_LEAK_STATUS],
                                message="Leak sensor disconnected",
                                name=self._name,
                                id=self._id,
                                sku=self._sku
                            )
                            self.notify_ha(msg)
                            self._water_leak_status = device_data[ATTR_WATER_LEAK_STATUS]
                        else:
                            self._water_leak_status = (
                                STATE_WATER_LEAK if device_data[ATTR_WATER_LEAK_STATUS] == STATE_WATER_LEAK else "ok"
                            )
                    self._water_temp = device_data[ATTR_ROOM_TEMPERATURE]
                    if ATTR_ERROR_CODE_SET1 in device_data and len(device_data[ATTR_ERROR_CODE_SET1]) > 0:
                        if device_data[ATTR_ERROR_CODE_SET1]["raw"] != 0:
                            self._error_code = device_data[ATTR_ERROR_CODE_SET1]["raw"]
                            message = None
                            match self._error_code:
                                case 32:
                                    message = "Temperature sensor disconnected"
                                case 64:
                                    message = "Leak sensor disconnected"
                            msg = translate_error(
                                self.hass,
                                "error_code",
                                code=str(device_data[ATTR_ERROR_CODE_SET1]["raw"]),
                                message=message,
                                name=self._name,
                                id=self._id,
                                sku=self._sku
                            )
                            self.notify_ha(msg)
                    else:
                        self._error_code = 0
                    self._wattage = device_data[ATTR_WATTAGE]
                    self._current_power_w = device_data[ATTR_WATTAGE_INSTANT]
                    self._cold_load_status = device_data[ATTR_COLD_LOAD_PICKUP_STATUS]
                    self._cold_load_remaining_time = device_data[ATTR_COLD_LOAD_PICKUP_REMAIN_TIME]
                    self._rssi = device_data[ATTR_RSSI]
                    self._tank_size = device_data[ATTR_TANK_SIZE]
                    if ATTR_DRSTATUS in device_data:
                        self._drstatus_active = device_data[ATTR_DRSTATUS][ATTR_DRACTIVE]
                        self._drstatus_optout = device_data[ATTR_DRSTATUS][ATTR_OPTOUT]
                        self._drstatus_onoff = device_data[ATTR_DRSTATUS][ATTR_ONOFF]
                        self._drstatus_optout_reason = device_data[ATTR_DRSTATUS]["optOutReason"]
                    self._water_temp_min = device_data[ATTR_WATER_TEMP_MIN]
                    self._water_temp_protect = device_data[ATTR_WATER_TEMP_PROTECT]
                    self._watt_time_on = device_data[ATTR_WATT_TIME_ON]
                    self._water_temp_time = device_data[ATTR_DR_WATER_TEMP_TIME]
                    if ATTR_DR_PROTEC_STATUS in device_data:
                        self._temperature = device_data[ATTR_DR_PROTEC_STATUS]["temperature"]
                        self._consumption = device_data[ATTR_DR_PROTEC_STATUS]["consumption"]
                        self._consumption_time = device_data[ATTR_DR_PROTEC_STATUS]["consumptionOverTime"]
                else:
                    _LOGGER.warning("Error in reading device %s: (%s)", self._name, device_data)
            else:
                self.log_error(device_data["error"]["code"])
            self.do_stat(start)
        else:
            if time.time() - self._snooze > SNOOZE_TIME:
                self._active = True
                if NOTIFY == "notification" or NOTIFY == "both":
                    self.notify_ha(translate_error(self.hass, "update_restarted", name=self._name, sku=self._sku))

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
                "cold_load_remaining_time": remaining_time(self._cold_load_remaining_time),
                "tank_size": neviweb_to_ha(self._tank_size),
                "eco_status": self._drstatus_active,
                "eco_optOut": self._drstatus_optout,
                "eco_onoff": self._drstatus_onoff,
                "eco_optout_reason": self._drstatus_optout_reason,
                "water_temp_min": self._water_temp_min,
                "water_time_on": self._watt_time_on,
                "water_temp_time": self._water_temp_time,
                "water_temp_protection_type": self._water_temp_protect,
                "protection_Temperature": self._temperature,
                "protection_Consumption": self._consumption,
                "protection_consumption_overtime": self._consumption_time,
                "error_code": self._error_code,
                "rssi": self._rssi,
                "sku": self._sku,
                "device_model": str(self._device_model),
                "device_model_cfg": self._device_model_cfg,
                "firmware": self._firmware,
                "activation": self._active,
                "device_type": self._device_type,
                "id": self._id,
            }
        )
        return data


class Neviweb130WifiTankPowerSwitch(Neviweb130Switch):
    """Implementation of a Neviweb Wi-Fi power controller switch, RM3500WF."""

    def __init__(self, device_info, name, sku, firmware, device_type, client):
        """Initialize."""
        super().__init__(device_info, name, sku, firmware, device_type, client)
        self._away_action = None
        self._away_payload = None
        self._cold_load_status = None
        self._cold_load_temp = None
        self._drstatus_power_abs = "off"
        self._drstatus_power_rel = "off"
        self._drstatus_setpoint = "off"
        self._error_code = None
        self._leg_status_consumption = None
        self._leg_status_over_time = None
        self._leg_status_temp = None
        self._mode = None
        self._rssi = None
        self._water_leak_closure_conf = None
        self._water_leak_disconnected_status = None
        self._water_leak_status = None
        self._water_tank_on = None
        self._water_temp = None
        self._water_temp_protect = None
        self._water_temp_time = None
        self._wattage = 0

    def update(self):
        if self._active:
            LOAD_ATTRIBUTES = [
                ATTR_WATER_LEAK_ALARM_STATUS,
                ATTR_WATER_TEMPERATURE,
                ATTR_WATER_LEAK_DISCONNECTED_STATUS,
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
                ATTR_WATER_TEMP_PROTECT,
            ]
            """Get the latest data from Neviweb and update the state."""
            start = time.time()
            device_data = self._client.get_device_attributes(self._id, UPDATE_ATTRIBUTES + LOAD_ATTRIBUTES)
            end = time.time()
            elapsed = round(end - start, 3)
            _LOGGER.debug("Updating %s (%s sec): %s", self._name, elapsed, device_data)
            if "error" not in device_data:
                if "errorCode" not in device_data:
                    self._onoff = device_data[ATTR_ONOFF]
                    self._water_leak_status = device_data[ATTR_WATER_LEAK_ALARM_STATUS]
                    if device_data[ATTR_WATER_LEAK_DISCONNECTED_STATUS] == "probe":
                        msg = translate_error(
                            self.hass,
                            "error_code",
                            code=device_data[ATTR_WATER_LEAK_DISCONNECTED_STATUS],
                            message="Leak sensor disconnected",
                            name=self._name,
                            id=self._id,
                            sku=self._sku
                        )
                        self.notify_ha(msg)
                    else:
                        self._water_leak_disconnected_status = device_data[ATTR_WATER_LEAK_DISCONNECTED_STATUS]
                    self._water_temp = device_data[ATTR_WATER_TEMPERATURE]
                    if ATTR_ERROR_CODE_SET1 in device_data and len(device_data[ATTR_ERROR_CODE_SET1]) > 0:
                        if device_data[ATTR_ERROR_CODE_SET1]["raw"] != 0:
                            self._error_code = device_data[ATTR_ERROR_CODE_SET1]["raw"]
                            message = None
                            match self._error_code:
                                case 32:
                                    message = "Temperature sensor disconnected"
                                case 64:
                                    message = "Leak sensor disconnected"
                            msg = translate_error(
                                self.hass,
                                "error_code",
                                code=str(device_data[ATTR_ERROR_CODE_SET1]["raw"]),
                                message=message,
                                name=self._name,
                                id=self._id,
                                sku=self._sku
                            )
                            self.notify_ha(msg)
                    else:
                        self._error_code = 0
                    if ATTR_DRSTATUS in device_data:
                        self._drstatus_active = device_data[ATTR_DRSTATUS][ATTR_DRACTIVE]
                        self._drstatus_optout = device_data[ATTR_DRSTATUS][ATTR_OPTOUT]
                        self._drstatus_onoff = device_data[ATTR_DRSTATUS][ATTR_ONOFF]
                        self._drstatus_power_abs = device_data[ATTR_DRSTATUS]["powerAbsolute"]
                        self._drstatus_power_rel = device_data[ATTR_DRSTATUS]["powerRelative"]
                        self._drstatus_setpoint = device_data[ATTR_DRSTATUS]["setpoint"]
                    self._current_power_w = device_data[ATTR_WIFI_WATT_NOW]["value"]
                    self._wattage = device_data[ATTR_WIFI_WATTAGE]["value"]
                    self._cold_load_status = device_data[ATTR_COLD_LOAD_PICKUP_STATUS]
                    self._cold_load_temp = device_data[ATTR_COLD_LOAD_PICKUP_TEMP]
                    self._cold_load_remaining_time = device_data[ATTR_COLD_LOAD_PICKUP_REMAIN_TIME]
                    self._rssi = device_data[ATTR_WIFI]
                    self._mode = device_data[ATTR_SYSTEM_MODE]
                    self._tank_size = device_data[ATTR_TANK_SIZE]
                    self._away_action = device_data[ATTR_AWAY_ACTION]["action"]
                    self._away_payload = device_data[ATTR_AWAY_ACTION]["actionPayload"]
                    self._leg_status_temp = device_data[ATTR_LEG_PROTEC_STATUS]["temperature"]
                    self._leg_status_consumption = device_data[ATTR_LEG_PROTEC_STATUS]["consumption"]
                    self._leg_status_over_time = device_data[ATTR_LEG_PROTEC_STATUS]["consumptionOverTime"]
                    self._water_temp_min = device_data[ATTR_MIN_WATER_TEMP]
                    self._water_tank_on = device_data[ATTR_WATER_TANK_ON]
                    self._water_temp_time = device_data[ATTR_WATER_TEMP_TIME]
                    self._water_temp_protect = device_data[ATTR_WATER_TEMP_PROTECT]
                    self._water_leak_closure_conf = device_data[ATTR_LEAK_CLOSURE_CONFIG]
                else:
                    _LOGGER.warning("Error in reading device %s: (%s)", self._name, device_data)
            else:
                self.log_error(device_data["error"]["code"])
            self.do_stat(start)
        else:
            if time.time() - self._snooze > SNOOZE_TIME:
                self._active = True
                if NOTIFY == "notification" or NOTIFY == "both":
                    self.notify_ha(translate_error(self.hass, "update_restarted", name=self._name, sku=self._sku))

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
                "water_leak_disconect_status": self._water_leak_disconnected_status,
                "water_leak_closure_config": self._water_leak_closure_conf,
                "water_temperature": self._water_temp,
                "cold_load_pickup_status": self._cold_load_status,
                "cold_load_remaining_time": remaining_time(self._cold_load_remaining_time),
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
                "water_temp_protection_type": self._water_temp_protect,
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
                "activation": self._active,
                "device_type": self._device_type,
                "id": self._id,
            }
        )
        return data


class Neviweb130ControlerSwitch(Neviweb130Switch):
    """Implementation of a Neviweb multi controller switch, MC3100ZB connected to GT130 or Sedna."""

    def __init__(self, device_info, name, sku, firmware, device_type, client):
        """Initialize."""
        super().__init__(device_info, name, sku, firmware, device_type, client)
        self._batt_info = None
        self._batt_percent_normal = None
        self._batt_status_normal = None
        self._battery_status = None
        self._ext_temp = None
        self._humidity = None
        self._input2_status = None
        self._input_status = None
        self._low_temp_status = None
        self._rssi = None

    def update(self):
        if self._active:
            if self._is_zb_control:
                NAME_ATTRIBUTES = [
                    ATTR_NAME_1,
                    ATTR_NAME_2,
                    ATTR_OUTPUT_NAME_1,
                    ATTR_OUTPUT_NAME_2,
                ]
            else:
                NAME_ATTRIBUTES = [
                    ATTR_NAME_1,
                    ATTR_OUTPUT_NAME_1,
                ]

            LOAD_ATTRIBUTES = []
            if self._is_zb_control:
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
                        ATTR_TEMP_ALERT,
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
            else:
                LOAD_ATTRIBUTES = [
                    ATTR_INPUT_STATUS,
                    ATTR_BATTERY_VOLTAGE,
                    ATTR_BATT_INFO,
                ]

            """Get the latest data from Neviweb and update the state."""
            start = time.time()
            device_data = self._client.get_device_attributes(
                self._id, UPDATE_ATTRIBUTES + LOAD_ATTRIBUTES + NAME_ATTRIBUTES
            )
            end = time.time()
            elapsed = round(end - start, 3)
            _LOGGER.debug("Updating %s (%s sec): %s", self._name, elapsed, device_data)
            if "error" not in device_data:
                if "errorCode" not in device_data:
                    if self._is_zb_control or self._is_sedna_control:
                        self._onoff = device_data[ATTR_ONOFF]
                        self._input_status = device_data[ATTR_INPUT_STATUS]
                        self._battery_voltage = device_data[ATTR_BATTERY_VOLTAGE]
                        if ATTR_BATT_INFO in device_data:
                            self._batt_info = device_data[ATTR_BATT_INFO]
                        self._input_name_1 = device_data[ATTR_NAME_1]
                        self._output_name_1 = device_data[ATTR_OUTPUT_NAME_1]
                    if self._is_zb_control:
                        self._onoff2 = device_data[ATTR_ONOFF2]
                        self._battery_status = device_data[ATTR_BATTERY_STATUS]
                        self._input2_status = device_data[ATTR_INPUT2_STATUS]
                        self._humidity = device_data[ATTR_REL_HUMIDITY]
                        self._room_temp = device_data[ATTR_ROOM_TEMPERATURE]
                        self._ext_temp = device_data[ATTR_EXT_TEMP]
                        self._timer = device_data[ATTR_TIMER]
                        self._timer2 = device_data[ATTR_TIMER2]
                        if ATTR_INPUT_1_ON_DELAY in device_data:
                            self._input_1_on_delay = device_data[ATTR_INPUT_1_ON_DELAY]
                            self._input_2_on_delay = device_data[ATTR_INPUT_2_ON_DELAY]
                            self._input_1_off_delay = device_data[ATTR_INPUT_1_OFF_DELAY]
                            self._input_2_off_delay = device_data[ATTR_INPUT_2_OFF_DELAY]
                        if ATTR_BATT_PERCENT_NORMAL in device_data:
                            self._batt_percent_normal = device_data[ATTR_BATT_PERCENT_NORMAL]
                        if ATTR_BATT_STATUS_NORMAL in device_data:
                            self._batt_status_normal = device_data[ATTR_BATT_STATUS_NORMAL]
                        if ATTR_RSSI in device_data:
                            self._rssi = device_data[ATTR_RSSI]
                        if ATTR_TEMP_ALERT in device_data:
                            self._temp_alert = device_data[ATTR_TEMP_ALERT]
                        if ATTR_LOW_TEMP_STATUS in device_data:
                            self._low_temp_status = device_data[ATTR_LOW_TEMP_STATUS]
                        self._input_name_2 = device_data[ATTR_NAME_2]
                        self._output_name_2 = device_data[ATTR_OUTPUT_NAME_2]
                        if ATTR_DRSTATUS in device_data:
                            self._drstatus_active = device_data[ATTR_DRSTATUS][ATTR_DRACTIVE]
                            self._drstatus_onoff = device_data[ATTR_DRSTATUS][ATTR_ONOFF]
                else:
                    _LOGGER.warning("Error in reading device %s: (%s)", self._name, device_data)
            else:
                self.log_error(device_data["error"]["code"])
        else:
            if time.time() - self._snooze > SNOOZE_TIME:
                self._active = True
                if NOTIFY == "notification" or NOTIFY == "both":
                    self.notify_ha(translate_error(self.hass, "update_restarted", name=self._name, sku=self._sku))

    @property
    def extra_state_attributes(self):
        """Return the extra state attributes."""
        data = {}
        data.update(
            {
                "onOff": self._onoff,
                "input1_status": self._input_status,
                "battery_voltage": self._battery_voltage,
                "battery_display_info": self._batt_info,
                "input1_name": self._input_name_1,
                "output1_name": self._output_name_1,
            }
        )
        if self._is_zb_control:
            data.update(
                {
                    "battery_level": voltage_to_percentage(self._battery_voltage, 2),
                    "battery_status": self._battery_status,
                    "battery_percent_normalized": self._batt_percent_normal,
                    "battery_status_normalized": self._batt_status_normal,
                    "extern_temperature": self._ext_temp,
                    "room_temperature": self._room_temp,
                    "room_humidity": self._humidity,
                    "timer": self._timer,
                    "timer2": self._timer2,
                    "input2_status": self._input2_status,
                    "onOff2": self._onoff2,
                    "eco_status": self._drstatus_active,
                    "eco_onOff": self._drstatus_onoff,
                    "input1_on_delay": neviweb_to_ha_delay(self._input_1_on_delay),
                    "input2_on_delay": neviweb_to_ha_delay(self._input_2_on_delay),
                    "input1_off_delay": neviweb_to_ha_delay(self._input_1_off_delay),
                    "input2_off_delay": neviweb_to_ha_delay(self._input_2_off_delay),
                    "input2_name": self._input_name_2,
                    "output2_name": self._output_name_2,
                    "temp_alert": "active" if self._temp_alert == 5 else "inactive",
                    "low_temp_status": self._low_temp_status,
                    "rssi": self._rssi,
                }
            )
        data.update(
            {
                "sku": self._sku,
                "device_model": str(self._device_model),
                "device_model_cfg": self._device_model_cfg,
                "firmware": self._firmware,
                "activation": self._active,
                "device_type": self._device_type,
                "id": self._id,
            }
        )

        return data
