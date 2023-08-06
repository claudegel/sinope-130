"""
Support for Neviweb door lock connected via GT130.
model 7000 = door lock ZigBee

For more details about this platform, please refer to the documentation at  
https://www.sinopetech.com/en/support/#api
"""
import logging

import voluptuous as vol
import time

import custom_components.neviweb130 as neviweb130
from . import (SCAN_INTERVAL, STAT_INTERVAL)

from homeassistant.const import (
    ATTR_CODE,
    ATTR_CODE_FORMAT,
    ATTR_ENTITY_ID,
    SERVICE_LOCK,
    SERVICE_OPEN,
    SERVICE_UNLOCK,
    STATE_JAMMED,
    STATE_LOCKED,
    STATE_LOCKING,
    STATE_UNLOCKED,
    STATE_UNLOCKING,
)

from homeassistant.helpers import (
    config_validation as cv,
    discovery,
    service,
    entity_platform,
    entity_component,
    entity_registry,
    device_registry,
)

from homeassistant.helpers.typing import HomeAssistantType

from datetime import timedelta
from homeassistant.helpers.event import track_time_interval
from homeassistant.helpers.icon import icon_for_battery_level
from .const import (
    DOMAIN,
    ATTR_BATTERY_VOLTAGE,
    ATTR_BATTERY_STATUS,
    ATTR_LOCK_STATUS,
    ATTR_DOOR_STATE,
    ATTR_RELOCK_TIME,
    ATTR_WRONG_CODE,
    ATTR_DISABLE_TIME,
    ATTR_LANGUAGE,
    ATTR_SOUND,
    ATTR_USER,
    ATTR_MAX_PIN,
    ATTR_MIN_PIN,
    MODE_AUTO,
    MODE_MANUAL,
    MODE_OFF,
    STATE_KEYPAD_STATUS,
)

_LOGGER = logging.getLogger(__name__)

DEFAULT_NAME = 'neviweb130 lock'
DEFAULT_NAME_2 = 'neviweb130 lock 2'

UPDATE_ATTRIBUTES = []

HA_TO_NEVIWEB_DELAY = {
    "15 min": 900,
    "30 min": 1800,
    "45 min": 2700,
    "60 min": 3600,
    "75 min": 4500,
    "90 min": 5400,
    "3 h": 10800,
    "6 h": 21600,
    "12 h": 43200,
    "24 h": 86400
}

SWITCH_TYPES = {
    "sensor": ["mdi:alarm", BinarySensorDeviceClass.PROBLEM],
}

IMPLEMENTED_DOOR_LOCK = [7000]
IMPLEMENTED_DEVICE_MODEL = IMPLEMENTED_DOOR_LOCK

async def async_setup_platform(
    hass,
    config,
    async_add_entities,
    discovery_info=None,
):
    """Set up the Neviweb130 lock."""
    data = hass.data[DOMAIN]

    entities = []
    for device_info in data.neviweb130_client.gateway_data:
        if "signature" in device_info and \
            "model" in device_info["signature"] and \
            device_info["signature"]["model"] in IMPLEMENTED_DEVICE_MODEL:
            device_name = '{} {}'.format(DEFAULT_NAME, device_info["name"])
            device_sku = device_info["sku"]
            entities.append(Neviweb130Lock(data, device_info, device_name, device_sku))
    for device_info in data.neviweb130_client.gateway_data2:
        if "signature" in device_info and \
            "model" in device_info["signature"] and \
            device_info["signature"]["model"] in IMPLEMENTED_DEVICE_MODEL:
            device_name = '{} {}'.format(DEFAULT_NAME_2, device_info["name"])
            device_sku = device_info["sku"]
            entities.append(Neviweb130Lock(data, device_info, device_name, device_sku))

    async_add_entities(entities, True)

def voltage_to_percentage(voltage, num):
    """Convert voltage level from volt to percentage."""
    if num == 2:
        return int((min(voltage,2.7)-2.3)/(2.7-2.3) * 100)
    else:
        return int((min(voltage,6.0)-3.0)/(6.0-3.0) * 100)

def alert_to_text(alert, value):
    """Convert numeric alert activation to text"""
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

def neviweb_to_ha_delay(value):
    keys = [k for k, v in HA_TO_NEVIWEB_DELAY.items() if v == value]
    if keys:
        return keys[0]
    return None

class Neviweb130Lock(LockEntity):
    """Implementation of a Neviweb door lock."""

    def __init__(self, data, device_info, name, sku):
        """Initialize."""
        self._name = name
        self._sku = sku
        self._client = data.neviweb130_client
        self._id = device_info["id"]
        self._is_door = device_info["signature"]["model"] in \
            IMPLEMENTED_DOOR_LOCK
        self._battery_voltage = 0
        self._battery_status = None
        self._timer = 0
        self._keypad = None
        self._battery_alert = None
        self._rssi = None
        self._batt_action_low = None
        self._lock_status = None
        self._door_state = None
        self._relock_time = None
        self._wrong_code = None
        self._disable_time = None
        self._language = "fr"
        self._sound = None
        self._user = None
        self._max_pin = None
        self._min_pin = None
        _LOGGER.debug("Setting up %s: %s", self._name, device_info)

    def update(self):
        DOOR_ATTRIBUTE = []
        """Get the latest data from Neviweb and update the state."""
        start = time.time()
        device_data = self._client.get_device_attributes(self._id,
            UPDATE_ATTRIBUTES + DOOR_ATTRIBUTE)
        end = time.time()
        elapsed = round(end - start, 3)
        if "error" not in device_data:
            if "errorCode" not in device_data:
                if self._is_door:
  
            else:
                _LOGGER.warning("Error in reading device %s: (%s)", self._name, device_data)
        elif device_data["error"]["code"] == "USRSESSEXP":
            _LOGGER.warning("Session expired... reconnecting...")
            self._client.reconnect()
        elif device_data["error"]["code"] == "ACCSESSEXC":
            _LOGGER.warning("Maximun session number reached...Close other connections and try again.")
            self._client.reconnect()
        elif device_data["error"]["code"] == "DVCACTNSPTD":
            _LOGGER.warning("Device action not supported... Report to maintainer.")
        elif device_data["error"]["code"] == "DVCCOMMTO":
            _LOGGER.warning("Device Communication Timeout... The device did not respond to the server within the prescribed delay.")
        else:
            _LOGGER.warning("Unknown error for %s: %s... Report to maintainer.", self._name, device_data)

    @property
    def unique_id(self):
        """Return unique ID based on Neviweb device ID."""
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
        """Return current operation i.e. ON, OFF """
        if self._is_zb_control:
            if self._onOff != MODE_OFF or self._onOff2 != MODE_OFF:
                return True
            else:
                return False
        else:
            return self._onOff != MODE_OFF

    def turn_on(self, **kwargs):
        """Turn the device on."""
        if self._is_wifi_valve or self._is_wifi_mesh_valve:
            self._client.set_valve_onOff(self._id, 100)
            self._valve_status = "open"
        else:
            self._client.set_onOff(self._id, "on")
            if self._is_zb_valve or self._is_zb_mesh_valve:
                self._valve_status = "open"
        self._onOff = "on"

    def turn_off(self, **kwargs):
        """Turn the device off."""
        if self._is_wifi_valve or self._is_wifi_mesh_valve:
            self._client.set_valve_onOff(self._id, 0)
            self._valve_status = "closed"
        else:
            self._client.set_onOff(self._id, "off")
            if self._is_zb_valve or self._is_zb_mesh_valve:
                self._valve_status = "closed"
        self._onOff = MODE_OFF

    @property  
    def valve_status(self):
        """Return current valve status, open or closed"""
        return self._valve_status != None

    @property  
    def keypad_status(self):
        """Return current keypad status, unlocked or locked"""
        return self._keypad_status != None

    @property
    def extra_state_attributes(self):
        """Return the extra state attributes."""
        data = {}
        if self._is_door:
            data = {'onOff': self._onOff,
                   }
        data.update({'sku': self._sku,
                    'device_type': self._device_type,
                    'id': self._id})
        return data

    @property
    def battery_voltage(self):
        """Return the current battery voltage of the valve in %."""
        if self._is_zb_control or self._is_sedna_control:
            type = 2
        else:
            type = 4
        return voltage_to_percentage(self._battery_voltage, type)

    def set_keypad_lock(self, value):
        """Lock or unlock device's keypad, lock = locked, unlock = unlocked"""
        lock = value["lock"]
        entity = value["id"]
        if lock == "locked":
            lock_name = "Locked"
        else:
            lock_name = "Unlocked"
        self._client.set_keypad_lock(
            entity, lock, False)
        self._keypad = lock_name

    def set_timer(self, value):
        """Set device timer, 0 = off, 1 to 255 = timer length"""
        time = value["time"]
        entity = value["id"]
        self._client.set_timer(
            entity, time)
        self._timer = time
