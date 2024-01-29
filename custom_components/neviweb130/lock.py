"""
Support for Neviweb door lock connected via GT130.
model 7000 = door lock ZigBee

For more details about this platform, please refer to the documentation at  
https://www.sinopetech.com/en/support/#api
"""

from __future__ import annotations

import logging

import voluptuous as vol
import time

import custom_components.neviweb130 as neviweb130
from . import (SCAN_INTERVAL, STAT_INTERVAL)
from homeassistant.components.lock import (
    LockEntity,
)

from homeassistant.const import (
    ATTR_CODE,
    ATTR_CODE_FORMAT,
    ATTR_ENTITY_ID,
    SERVICE_LOCK,
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
from homeassistant.components.binary_sensor import BinarySensorDeviceClass

from datetime import timedelta
from homeassistant.helpers.event import track_time_interval
from homeassistant.helpers.icon import icon_for_battery_level
from .const import (
    DOMAIN,
    ATTR_BATT_PERCENT_NORMAL,
    ATTR_BATT_STATUS_NORMAL,
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
    STATE_FORCED,
    STATE_UNDEFINED,
    STATE_UNSPECIFIED,
    SERVICE_SET_RELOCK_TIME,
    SERVICE_SET_WRONG_CODE_LIMIT,
    SERVICE_SET_TEMPORARY_DISABLE_TIME,
)

from .schema import (
    DOOR_ALERT,
    RELOCK_TIME,
    WRONG_CODE_LIMIT,
    TEMPORARY_DISABLE,
    SET_RELOCK_TIME_SCHEMA,
    SET_WRONG_CODE_LIMIT_SCHEMA,
    SET_TEMPORARY_DISABLE_TIME_SCHEMA,
)

_LOGGER = logging.getLogger(__name__)

DEFAULT_NAME = 'neviweb130 lock'
DEFAULT_NAME_2 = 'neviweb130 lock 2'

UPDATE_ATTRIBUTES = [ATTR_BATTERY_STATUS]

SWITCH_TYPES = {
    "sensor": ["mdi:lock", BinarySensorDeviceClass.DOOR],
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

    def set_relock_time_service(service):
        """ Set time delay to relock the device"""
        entity_id = service.data[ATTR_ENTITY_ID]
        value = {}
        for lock in entities:
            if lock.entity_id == entity_id:
                value = {"id": lock.unique_id, "time": service.data[ATTR_RELOCK_TIME]}
                lock.set_relock_time(value)
                lock.schedule_update_ha_state(True)
                break

    def set_wrong_code_limit_service(service):
        """ Set the limit for wrong code entered"""
        entity_id = service.data[ATTR_ENTITY_ID]
        value = {}
        for lock in entities:
            if lock.entity_id == entity_id:
                value = {"id": lock.unique_id, "limit": service.data[ATTR_WRONG_CODE]}
                lock.set_wrong_code_limit(value)
                lock.schedule_update_ha_state(True)
                break

    def set_temporary_disable_time_service(service):
        """ Set time in second the lock device is disabled when wrong code is entered"""
        entity_id = service.data[ATTR_ENTITY_ID]
        value = {}
        for lock in entities:
            if lock.entity_id == entity_id:
                value = {"id": lock.unique_id, "time": service.data[ATTR_DISABLE_TIME]}
                lock.set_temporary_disable_time(value)
                lock.schedule_update_ha_state(True)
                break

    hass.services.async_register(
        DOMAIN,
        SERVICE_SET_RELOCK_TIME,
        set_relock_time_service,
        schema=SET_RELOCK_TIME_SCHEMA,
    )

    hass.services.async_register(
        DOMAIN,
        SERVICE_SET_WRONG_CODE_LIMIT,
        set_wrong_code_limit_service,
        schema=SET_WRONG_CODE_LIMIT_SCHEMA,
    )

    hass.services.async_register(
        DOMAIN,
        SERVICE_SET_TEMPORARY_DISABLE_TIME,
        set_temporary_disable_time_service,
        schema=SET_TEMPORARY_DISABLE_TIME_SCHEMA,
    )

def voltage_to_percentage(voltage, num):
    """Convert voltage level from volt to percentage."""
    if num == 2:
        return int((min(voltage,2.7)-2.3)/(2.7-2.3) * 100)
    else:
        return int((min(voltage,6.0)-3.0)/(6.0-3.0) * 100)

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
        self._device_model = device_info["signature"]["model"]
        self._device_model_cfg = device_info["signature"]["modelCfg"]
        self._is_door = device_info["signature"]["model"] in \
            IMPLEMENTED_DOOR_LOCK
        self._battery_voltage = 0
        self._battery_status = None
        self._batt_percent_normal = None
        self._batt_status_normal = None
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
        DOOR_ATTRIBUTES = [ATTR_LOCK_STATUS, ATTR_DOOR_STATE, ATTR_RELOCK_TIME, ATTR_WRONG_CODE, ATTR_DISABLE_TIME, ATTR_LANGUAGE,
                         ATTR_SOUND, ATTR_USER, ATTR_MAX_PIN, ATTR_MIN_PIN, ATTR_BATTERY_STATUS, ATTR_BATT_PERCENT_NORMAL, ATTR_BATT_STATUS_NORMAL]
        """Get the latest data from Neviweb and update the state."""
        start = time.time()
        device_data = self._client.get_device_attributes(self._id,
            UPDATE_ATTRIBUTES + DOOR_ATTRIBUTES)
        end = time.time()
        elapsed = round(end - start, 3)
        if "error" not in device_data:
            if "errorCode" not in device_data:
                self._lock_status = device_data[ATTR_DRSTATUS][ATTR_LOCK_STATUS]
                self._door_state = device_data[ATTR_DRSTATUS][ATTR_DOOR_STATE]
                self._relock_time = device_data[ATTR_DRSTATUS][ATTR_RELOCK_TIME]
                self._wrong_code = device_data[ATTR_DRSTATUS][ATTR_WRONG_CODE]
                self._disable_time = device_data[ATTR_DRSTATUS][ATTR_DISABLE_TIME]
                self._language = device_data[ATTR_DRSTATUS][ATTR_LANGUAGE]
                self._sound = device_data[ATTR_DRSTATUS][ATTR_SOUND]
                self._user = device_data[ATTR_DRSTATUS][ATTR_USER]
                self._max_pin = device_data[ATTR_DRSTATUS][ATTR_MAX_PIN]
                self._min_pin = device_data[ATTR_DRSTATUS][ATTR_MIN_PIN]
                self._battery_status = device_data[ATTR_BATTERY_STATUS]
                if ATTR_BATT_PERCENT_NORMAL in device_data:
                    self._batt_percent_normal = device_data[ATTR_BATT_PERCENT_NORMAL]
                if ATTR_BATT_STATUS_NORMAL in device_data:
                    self._batt_status_normal = device_data[ATTR_BATT_STATUS_NORMAL]
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
    def is_jammed(self) -> bool | None:
        """Return true if the lock is jammed (incomplete locking)."""
        if self._lock_status == STATE_JAMMED:
            return True
        else:
            return False
        
    @property  
    def is_locked(self):
        """Return current door status i.e. locked, unlocked """
        if self._lock_status == STATE_LOCKED:
            return True
        else:
            return False

    def unlock(self, **kwargs):
        """ Unlock the door."""
        self._client.set_lock(self._id, "on")
        self._lock_status = STATE_UNLOCKED

    def lock(self, **kwargs):
        """ Lock the door."""
        self._client.set_lock(self._id, "off")
        self._lock_status = STATE_LOCKED

    @property
    def extra_state_attributes(self):
        """Return the extra state attributes."""
        data = {}
        data.update({'lock_status': self._lock_status,
                    'door_state': self._door_state,
                    'Battery_status': self._battery_status,
                    'Battery_percent_normalized': self._batt_percent_normal,
                    'Battery_status_normalized': self._batt_status_normal,
                    'relock_time': self._relock_time,
                    'wrong_code': self._wrong_code,
                    'disable_time': self._disable_time,
                    'language': self._language,
                    'sound': self._sound,
                    'users': self._user,
                    'max_pin': self._max_pin,
                    'min_pin': self._min_pin,
                    'sku': self._sku,
                    'device_model': str(self._device_model),
                    'device_model_cfg': self._device_model_cfg,
                    'device_type': self._device_type,
                    'id': str(self._id)})
        return data

    @final
    @property
    def state(self) -> str | None:
        """Return the door state."""
        if self.is_jammed:
            return STATE_JAMMED
        if self.is_locked:
            return STATE_LOCKED
        else:
            return STATE_UNLOCKED

    @property
    def battery_voltage(self):
        """Return the current battery voltage of the door lock in %."""
        type = 2
        return voltage_to_percentage(self._battery_voltage, type)

    def set_relock_time(self, value):
        """Set the time before the lock relock"""
        time = value["time"]
        entity = value["id"]
        self._client.set_relock_time(
            entity, time)
        self._relock_time = time

    def set_wrong_code_limit(self, value):
        """Set limit of number of time a wrong code it entered"""
        limit = value["limit"]
        entity = value["id"]
        self._client.set_wrong_code_limit(
            entity, limit)
        self._wrong_code = limit

    def set_temporary_disable_time(self, value):
        """Set time in second the lock device is disabled when wrong code is entered"""
        time = value["time"]
        entity = value["id"]
        self._client.set_temporary_disable_time(
            entity, time)
        self._disable_time = time
