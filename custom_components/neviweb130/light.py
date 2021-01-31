"""
Need to be changed
Support for Neviweb light switch/dimmer connected to GT130 ZigBee.
model 2121 = light switch SW2500ZB
model 2131 = light dimmer DM2500ZB
For more details about this platform, please refer to the documentation at  
https://www.sinopetech.com/en/support/#api
"""
import logging

import voluptuous as vol
import time

import custom_components.neviweb130 as neviweb130
from . import (SCAN_INTERVAL)
from homeassistant.components.light import (
    LightEntity,
    ATTR_BRIGHTNESS,
    ATTR_BRIGHTNESS_PCT,
    SUPPORT_BRIGHTNESS,
)

from homeassistant.const import (
    ATTR_ENTITY_ID,
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
from .const import (
    DOMAIN,
    ATTR_INTENSITY,
    ATTR_ONOFF,
    ATTR_LIGHT_WATTAGE,
    ATTR_KEYPAD,
    ATTR_TIMER,
    ATTR_LED_ON_INTENSITY,
    ATTR_LED_OFF_INTENSITY,
    ATTR_LED_ON_COLOR,
    ATTR_LED_OFF_COLOR,
    ATTR_STATE,
    ATTR_RED,
    ATTR_GREEN,
    ATTR_BLUE,
    MODE_AUTO,
    MODE_MANUAL,
    MODE_OFF,
    SERVICE_SET_LED_INDICATOR,
    SERVICE_SET_LIGHT_KEYPAD_LOCK,
    SERVICE_SET_LIGHT_TIMER,
    SERVICE_SET_WATTAGE,
)

_LOGGER = logging.getLogger(__name__)

DEFAULT_NAME = 'neviweb130 light'

UPDATE_ATTRIBUTES = [
    ATTR_INTENSITY,
    ATTR_ONOFF,
    ATTR_LIGHT_WATTAGE,
    ATTR_KEYPAD,
    ATTR_TIMER,
    ATTR_LED_ON_INTENSITY,
    ATTR_LED_OFF_INTENSITY,
    ATTR_LED_ON_COLOR,
    ATTR_LED_OFF_COLOR,
]

DEVICE_MODEL_DIMMER = [2131]
DEVICE_MODEL_LIGHT = [2121]
IMPLEMENTED_DEVICE_MODEL = DEVICE_MODEL_LIGHT + DEVICE_MODEL_DIMMER

SET_LIGHT_KEYPAD_LOCK_SCHEMA = vol.Schema(
    {
         vol.Required(ATTR_ENTITY_ID): cv.entity_id,
         vol.Required(ATTR_KEYPAD): cv.string,
    }
)

SET_LIGHT_TIMER_SCHEMA = vol.Schema(
    {
         vol.Required(ATTR_ENTITY_ID): cv.entity_id,
         vol.Required(ATTR_TIMER): vol.All(
             vol.Coerce(int), vol.Range(min=0, max=255)
         ),
    }
)

SET_LED_INDICATOR_SCHEMA = vol.Schema(
    {
         vol.Required(ATTR_ENTITY_ID): cv.entity_id,
         vol.Required(ATTR_STATE): vol.All(
             vol.Coerce(int), vol.Range(min=0, max=1)
         ),
         vol.Required(ATTR_INTENSITY): vol.All(
             vol.Coerce(int), vol.Range(min=0, max=100)
         ),
         vol.Required(ATTR_RED): vol.All(
             vol.Coerce(int), vol.Range(min=0, max=255)
         ),
         vol.Required(ATTR_GREEN): vol.All(
             vol.Coerce(int), vol.Range(min=0, max=255)
         ),
         vol.Required(ATTR_BLUE): vol.All(
             vol.Coerce(int), vol.Range(min=0, max=255)
         ),
    }
)

SET_WATTAGE_SCHEMA = vol.Schema(
    {
         vol.Required(ATTR_ENTITY_ID): cv.entity_id,
         vol.Required(ATTR_LIGHT_WATTAGE): vol.All(
             vol.Coerce(int), vol.Range(min=0, max=1800)
         ),
    }
)

async def async_setup_platform(
    hass,
    config,
    async_add_entities,
    discovery_info=None,
):
    """Set up the neviweb light."""
    data = hass.data[DOMAIN]
    
    entities = []
    for device_info in data.neviweb130_client.gateway_data:
        if "signature" in device_info and \
            "model" in device_info["signature"] and \
            device_info["signature"]["model"] in IMPLEMENTED_DEVICE_MODEL:
            device_name = '{} {} {}'.format(DEFAULT_NAME, 
                "dimmer" if device_info["signature"]["model"] in DEVICE_MODEL_DIMMER 
                else "light", device_info["name"])
            entities.append(Neviweb130Light(data, device_info, device_name))

    async_add_entities(entities, True)

    def set_light_keypad_lock_service(service):
        """ lock/unlock keypad device"""
        entity_id = service.data[ATTR_ENTITY_ID]
        value = {}
        for light in entities:
            if light.entity_id == entity_id:
                value = {"id": light.unique_id, "lock": service.data[ATTR_KEYPAD]}
                light.set_keypad_lock(value)
                light.schedule_update_ha_state(True)
                break

    def set_light_timer_service(service):
        """ set timer for light device"""
        entity_id = service.data[ATTR_ENTITY_ID]
        value = {}
        for light in entities:
            if light.entity_id == entity_id:
                value = {"id": light.unique_id, "time": service.data[ATTR_TIMER]}
                light.set_timer(value)
                light.schedule_update_ha_state(True)
                break

    def set_led_indicator_service(service):
        """ set led color and intensity for light indicator """
        entity_id = service.data[ATTR_ENTITY_ID]
        value = {}
        for light in entities:
            if light.entity_id == entity_id:
                value = {"id": light.unique_id, "state": service.data[ATTR_STATE], "intensity": service.data[ATTR_INTENSITY], "red": service.data[ATTR_RED], "green": service.data[ATTR_GREEN], "blue": service.data[ATTR_BLUE]}
                light.set_led_indicator(value)
                light.schedule_update_ha_state(True)
                break

    def set_wattage_service(service):
        """ set watt load for light device"""
        entity_id = service.data[ATTR_ENTITY_ID]
        value = {}
        for light in entities:
            if light.entity_id == entity_id:
                value = {"id": light.unique_id, "watt": service.data[ATTR_LIGHT_WATTAGE]}
                light.set_wattage(value)
                light.schedule_update_ha_state(True)
                break

    hass.services.async_register(
        DOMAIN,
        SERVICE_SET_LIGHT_KEYPAD_LOCK,
        set_light_keypad_lock_service,
        schema=SET_LIGHT_KEYPAD_LOCK_SCHEMA,
    )

    hass.services.async_register(
        DOMAIN,
        SERVICE_SET_LIGHT_TIMER,
        set_light_timer_service,
        schema=SET_LIGHT_TIMER_SCHEMA,
    )

    hass.services.async_register(
        DOMAIN,
        SERVICE_SET_LED_INDICATOR,
        set_led_indicator_service,
        schema=SET_LED_INDICATOR_SCHEMA,
    )

    hass.services.async_register(
        DOMAIN,
        SERVICE_SET_WATTAGE,
        set_wattage_service,
        schema=SET_WATTAGE_SCHEMA,
    )

def brightness_to_percentage(brightness):
    """Convert brightness from absolute 0..255 to percentage."""
    return int((brightness * 100.0) / 255.0)

def brightness_from_percentage(percent):
    """Convert percentage to absolute value 0..255."""
    return int((percent * 255.0) / 100.0)

class Neviweb130Light(LightEntity):
    """Implementation of a neviweb light."""

    def __init__(self, data, device_info, name):
        """Initialize."""
        self._name = name
        self._client = data.neviweb130_client
        self._id = device_info["id"]
        self._brightness_pct = 0
        self._keypad = "Unlocked"
        self._timer = 0
        self._led_on = "0,0,0,0"
        self._led_off = "0,0,0,0"
        self._wattage = None
        self._is_dimmable = device_info["signature"]["model"] in \
            DEVICE_MODEL_DIMMER
        self._onOff = None
        _LOGGER.debug("Setting up %s: %s", self._name, device_info)
        
    def update(self):
        """Get the latest data from neviweb and update the state."""
        start = time.time()
        device_data = self._client.get_device_attributes(self._id,
            UPDATE_ATTRIBUTES)
        end = time.time()
        elapsed = round(end - start, 3)
        _LOGGER.debug("Updating %s (%s sec): %s",
            self._name, elapsed, device_data)
        if "error" not in device_data:
            if "errorCode" not in device_data:
                if self._is_dimmable:   
                    self._brightness_pct = device_data[ATTR_INTENSITY] if \
                        device_data[ATTR_INTENSITY] is not None else 0.0
                self._onOff = device_data[ATTR_ONOFF]
                self._wattage = device_data[ATTR_LIGHT_WATTAGE]["value"]
                self._keypad = device_data[ATTR_KEYPAD]
                self._timer = device_data[ATTR_TIMER]
                self._led_on = str(device_data[ATTR_LED_ON_INTENSITY])+","+str(device_data[ATTR_LED_ON_COLOR]["red"])+","+str(device_data[ATTR_LED_ON_COLOR]["green"])+","+str(device_data[ATTR_LED_ON_COLOR]["blue"])
                self._led_off = str(device_data[ATTR_LED_OFF_INTENSITY])+","+str(device_data[ATTR_LED_OFF_COLOR]["red"])+","+str(device_data[ATTR_LED_OFF_COLOR]["green"])+","+str(device_data[ATTR_LED_OFF_COLOR]["blue"])
                return
            _LOGGER.warning("Error in reading device %s: (%s)", self._name, device_data)
            return
        _LOGGER.warning("Cannot update %s: %s", self._name, device_data)   
        
    @property
    def supported_features(self):
        """Return the list of supported features."""
        if self._is_dimmable:
            return SUPPORT_BRIGHTNESS
        return 0
    
    @property
    def unique_id(self):
        """Return unique ID based on Neviweb device ID."""
        return self._id

    @property
    def name(self):
        """Return the name of the light."""
        return self._name

    @property
    def device_class(self):
        """Return the device class of this entity."""
        return "light"

    @property
    def device_state_attributes(self):
        """Return the state attributes."""
        data = {}
        if self._is_dimmable and self._brightness_pct:
            data = {ATTR_BRIGHTNESS_PCT: self._brightness_pct}
        data.update({'onOff': self._onOff,
                     'wattage': self._wattage,
                     'keypad': self._keypad,
                     'timer': self._timer,
                     'led_on': self._led_on,
                     'led_off': self._led_off,
                     'id': self._id})
        return data
    
    @property
    def brightness(self):
        """Return intensity of light"""
        return brightness_from_percentage(self._brightness_pct)

    @property
    def is_on(self): ## need to change this for neviweb130
        """Return true if device is on."""
        return self._onOff != MODE_OFF

    # For the turn_on and turn_off functions, we would normally check if the
    # the requested state is different from the actual state to issue the 
    # command. But since we update the state every 6 minutes, there is good
    # chance that the current stored state doesn't match with real device 
    # state. So we force the set_brightness each time.
    
    def turn_on(self, **kwargs):
        """Turn the light on."""
        if not self.is_on:
            self._client.set_onOff(self._id, "on")
        if ATTR_BRIGHTNESS in kwargs and self.brightness != kwargs[ATTR_BRIGHTNESS]:
            brightness_pct = \
                brightness_to_percentage(int(kwargs.get(ATTR_BRIGHTNESS)))
            self._client.set_brightness(self._id, brightness_pct)
        
    def turn_off(self, **kwargs):
        """Turn the light off."""
        self._client.set_onOff(self._id, "off")

    def set_keypad_lock(self, value):
        """Lock or unlock device's keypad, lock = locked, unlock = unlocked"""
        lock = value["lock"]
        entity = value["id"]
        key = "off"
        if lock == "locked":
            lock_name = "Locked"
        else:
            lock_name = "Unlocked"
        self._client.set_keypad_lock(
            entity, lock, key)
        self._keypad = lock_name

    def set_timer(self, value):
        """Set device timer, 0 = off, 1 to 255 = timer length"""
        time = value["time"]
        entity = value["id"]
        self._client.set_timer(
            entity, time)
        self._timer = time

    def set_led_indicator(self, value):
        """Set led indicator color and intensity, base on RGB red, green, blue color (0-255) and intensity from 0 to 100"""
        state = value["state"]
        entity = value["id"]
        intensity = value["intensity"]
        red = value["red"]
        green = value["green"]
        blue = value["blue"]
        self._client.set_led_indicator(
            entity, state, intensity, red, green, blue)
        if state == 0:
            self._led_off = str(value["intensity"])+","+str(value["red"])+","+str(value["green"])+","+str(value["blue"])
        else:
            self._led_on = str(value["intensity"])+","+str(value["red"])+","+str(value["green"])+","+str(value["blue"])

    def set_wattage(self, value):
        """Set light device watt load """
        watt = value["watt"]
        entity = value["id"]
        self._client.set_wattage(
            entity, watt)
        self._wattage = watt
