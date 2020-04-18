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
from homeassistant.components.light import (Light, ATTR_BRIGHTNESS,
    ATTR_BRIGHTNESS_PCT, SUPPORT_BRIGHTNESS)
from datetime import timedelta
from .const import (DOMAIN, ATTR_INTENSITY, ATTR_ONOFF,
    MODE_AUTO, MODE_MANUAL, MODE_OFF)

_LOGGER = logging.getLogger(__name__)

DEFAULT_NAME = 'neviweb130 light'

UPDATE_ATTRIBUTES = [ATTR_INTENSITY, ATTR_ONOFF]

DEVICE_MODEL_DIMMER = [2131]
DEVICE_MODEL_LIGHT = [2121]
IMPLEMENTED_DEVICE_MODEL = DEVICE_MODEL_LIGHT + DEVICE_MODEL_DIMMER

async def async_setup_platform(hass, config, async_add_entities, discovery_info=None):
    """Set up the neviweb light."""
    data = hass.data[DOMAIN]
    
    devices = []
    for device_info in data.neviweb130_client.gateway_data:
        if "signature" in device_info and \
            "model" in device_info["signature"] and \
            device_info["signature"]["model"] in IMPLEMENTED_DEVICE_MODEL:
            device_name = '{} {} {}'.format(DEFAULT_NAME, 
                "dimmer" if device_info["signature"]["model"] in DEVICE_MODEL_DIMMER 
                else "light", device_info["name"])
            devices.append(Neviweb130Light(data, device_info, device_name))

    async_add_entities(devices, True)

def brightness_to_percentage(brightness):
    """Convert brightness from absolute 0..255 to percentage."""
    return int((brightness * 100.0) / 255.0)

def brightness_from_percentage(percent):
    """Convert percentage to absolute value 0..255."""
    return int((percent * 255.0) / 100.0)

class Neviweb130Light(Light):
    """Implementation of a neviweb light."""

    def __init__(self, data, device_info, name):
        """Initialize."""
        self._name = name
        self._client = data.neviweb130_client
        self._id = device_info["id"]
        self._brightness_pct = 0
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
    def brightness(self):
        """Return intensity of light"""
        return brightness_from_percentage(self._brightness_pct)

    @property
    def is_on(self): ## need to change this for neviweb130
        """Return true if device is on."""
        if self._is_dimmable:
            return self._brightness_pct != 0
        return self._onOff != MODE_OFF

    # For the turn_on and turn_off functions, we would normally check if the
    # the requested state is different from the actual state to issue the 
    # command. But since we update the state every 6 minutes, there is good
    # chance that the current stored state doesn't match with real device 
    # state. So we force the set_brightness each time.
    def turn_on(self, **kwargs):
        """Turn the light on."""
        brightness_pct = 100
        if kwargs.get(ATTR_BRIGHTNESS):
            brightness_pct = \
                brightness_to_percentage(int(kwargs.get(ATTR_BRIGHTNESS)))
        if self._is_dimmable:
            brightness_pct = 101 # Sets the light to last known brightness.
        self._client.set_brightness(self._id, brightness_pct)

    def turn_off(self, **kwargs):
        """Turn the light off."""
        if self._is_dimmable:
            self._client.set_brightness(self._id, 0)
        else:
            self._client.set_onOff(self._id, "off")

    @property
    def device_state_attributes(self):
        """Return the state attributes."""
        data = {}
        if self._is_dimmable and self._brightness_pct:
            data = {ATTR_BRIGHTNESS_PCT: self._brightness_pct}
        data.update({'onOff': self._onOff,
                     'id': self._id})
        return data
