"""
Need to be changed
Support for Neviweb light switch/dimmer connected to GT130 ZigBee.
model 2121 = light switch SW2500ZB
model 2121 = light switch SW2500ZB-G2
model 2131 = light dimmer DM2500ZB
model 2131 = light dimmer DM2500ZB-G2
model 2132 = light dimmer DM2550ZB
model 2132 = light dimmer DM2550ZB-G2
For more details about this platform, please refer to the documentation at
https://www.sinopetech.com/en/support/#api
"""
import logging

import voluptuous as vol
import time

import custom_components.neviweb130 as neviweb130
from . import (SCAN_INTERVAL, STAT_INTERVAL)
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
from homeassistant.components.persistent_notification import DOMAIN as PN_DOMAIN

from datetime import timedelta
from homeassistant.helpers.event import track_time_interval
from .const import (
    DOMAIN,
    ATTR_INTENSITY,
    ATTR_INTENSITY_MIN,
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
    ATTR_PHASE_CONTROL,
    ATTR_KEY_DOUBLE_UP,
    ATTR_ERROR_CODE_SET1,
    MODE_AUTO,
    MODE_MANUAL,
    MODE_OFF,
    SERVICE_SET_LED_INDICATOR,
    SERVICE_SET_LIGHT_KEYPAD_LOCK,
    SERVICE_SET_LIGHT_TIMER,
    SERVICE_SET_PHASE_CONTROL,
    SERVICE_SET_WATTAGE,
    SERVICE_SET_ACTIVATION,
    SERVICE_SET_KEY_DOUBLE_UP,
)

_LOGGER = logging.getLogger(__name__)

DEFAULT_NAME = 'neviweb130 light'
DEFAULT_NAME_2 = 'neviweb130 light 2'

UPDATE_ATTRIBUTES = [
    ATTR_INTENSITY,
    ATTR_INTENSITY_MIN,
    ATTR_ONOFF,
    ATTR_KEYPAD,
    ATTR_TIMER,
    ATTR_LED_ON_INTENSITY,
    ATTR_LED_OFF_INTENSITY,
    ATTR_LED_ON_COLOR,
    ATTR_LED_OFF_COLOR,
]

DEVICE_MODEL_DIMMER = [2131]
DEVICE_MODEL_NEW_DIMMER = [2132]
DEVICE_MODEL_LIGHT = [2121]
IMPLEMENTED_DEVICE_MODEL = DEVICE_MODEL_LIGHT + DEVICE_MODEL_DIMMER + DEVICE_MODEL_NEW_DIMMER

SET_LIGHT_KEYPAD_LOCK_SCHEMA = vol.Schema(
    {
        vol.Required(ATTR_ENTITY_ID): cv.entity_id,
        vol.Required(ATTR_KEYPAD): vol.In(["locked", "unlocked", "partiallyLocked"]),
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

SET_PHASE_CONTROL_SCHEMA = vol.Schema(
    {
        vol.Required(ATTR_ENTITY_ID): cv.entity_id,
        vol.Required(ATTR_KEYPAD): vol.In(["reverse", "forward"]),
    }
)

SET_ACTIVATION_SCHEMA = vol.Schema(
    {
        vol.Required(ATTR_ENTITY_ID): cv.entity_id,
        vol.Required("active"): vol.In([True, False]),
    }
)

SET_KEY_DOUBLE_UP_SCHEMA = vol.Schema(
    {
        vol.Required(ATTR_ENTITY_ID): cv.entity_id,
        vol.Required(ATTR_KEY_DOUBLE_UP): vol.In(["On", "Off"]),
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
                "light" if device_info["signature"]["model"] in DEVICE_MODEL_LIGHT 
                else "dimmer", device_info["name"])
            device_sku = device_info["sku"]
            device_firmware = "{}.{}.{}".format(device_info["signature"]["softVersion"]["major"],device_info["signature"]["softVersion"]["middle"],device_info["signature"]["softVersion"]["minor"])
            entities.append(Neviweb130Light(data, device_info, device_name, device_sku, device_firmware))
    for device_info in data.neviweb130_client.gateway_data2:
        if "signature" in device_info and \
            "model" in device_info["signature"] and \
            device_info["signature"]["model"] in IMPLEMENTED_DEVICE_MODEL:
            device_name = '{} {} {}'.format(DEFAULT_NAME_2, 
                "light" if device_info["signature"]["model"] in DEVICE_MODEL_LIGHT 
                else "dimmer", device_info["name"])
            device_sku = device_info["sku"]
            device_firmware = "{}.{}.{}".format(device_info["signature"]["softVersion"]["major"],device_info["signature"]["softVersion"]["middle"],device_info["signature"]["softVersion"]["minor"])
            entities.append(Neviweb130Light(data, device_info, device_name, device_sku, device_firmware))

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

    def set_phase_control_service(service):
        """ Change phase control mode for dimmer device"""
        entity_id = service.data[ATTR_ENTITY_ID]
        value = {}
        for light in entities:
            if light.entity_id == entity_id:
                value = {"id": light.unique_id, "phase": service.data[ATTR_PHASE_CONTROL]}
                light.set_phase_control(value)
                light.schedule_update_ha_state(True)
                break

    def set_activation_service(service):
        """ Activate or deactivate Neviweb polling for missing device """
        entity_id = service.data[ATTR_ENTITY_ID]
        value = {}
        for switch in entities:
            if switch.entity_id == entity_id:
                value = {"id": switch.unique_id, "active": service.data["active"]}
                switch.set_activation(value)
                switch.schedule_update_ha_state(True)
                break

    def set_key_double_up_service(service):
        """ Change key double up action for dimmer device"""
        entity_id = service.data[ATTR_ENTITY_ID]
        value = {}
        for light in entities:
            if light.entity_id == entity_id:
                value = {"id": light.unique_id, "double": service.data[ATTR_KEY_DOUBLE_UP]}
                light.set_key_double_up(value)
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

    hass.services.async_register(
        DOMAIN,
        SERVICE_SET_PHASE_CONTROL,
        set_phase_control_service,
        schema=SET_PHASE_CONTROL_SCHEMA,
    )

    hass.services.async_register(
        DOMAIN,
        SERVICE_SET_ACTIVATION,
        set_activation_service,
        schema=SET_ACTIVATION_SCHEMA,
    )

    hass.services.async_register(
        DOMAIN,
        SERVICE_SET_KEY_DOUBLE_UP,
        set_key_double_up_service,
        schema=SET_KEY_DOUBLE_UP_SCHEMA,
    )

def brightness_to_percentage(brightness):
    """Convert brightness from absolute 0..255 to percentage."""
    return round((brightness * 100.0) / 255.0)

def brightness_from_percentage(percent):
    """Convert percentage to absolute value 0..255."""
    return round((percent * 255.0) / 100.0)

class Neviweb130Light(LightEntity):
    """Implementation of a neviweb light."""

    def __init__(self, data, device_info, name, sku, firmware):
        """Initialize."""
        self._name = name
        self._sku = sku
        self._firmware = firmware
        self._client = data.neviweb130_client
        self._id = device_info["id"]
        self._hour_energy_kwh_count = None
        self._today_energy_kwh_count = None
        self._month_energy_kwh_count = None
        self._hour_kwh = None
        self._today_kwh = None
        self._month_kwh = None
        self._brightness_pct = 0
        self._keypad = "Unlocked"
        self._timer = 0
        self._led_on = "0,0,0,0"
        self._led_off = "0,0,0,0"
        self._phase_control = None
        self._intensity_min = 600
        self._wattage = 0
        self._double_up = None
        self._temp_status = None
        self._energy_stat_time = time.time() - 1500
        self._activ = True
        self._is_dimmable = device_info["signature"]["model"] in \
            DEVICE_MODEL_DIMMER or device_info["signature"]["model"] in DEVICE_MODEL_NEW_DIMMER
        self._is_new_dimmable = device_info["signature"]["model"] in \
            DEVICE_MODEL_NEW_DIMMER
        self._onoff = None
        _LOGGER.debug("Setting up %s: %s", self._name, device_info)

    def update(self):
        if self._activ:
            """Get the latest data from neviweb and update the state."""
            if not self._is_new_dimmable:
                WATT_ATTRIBUTE = [ATTR_LIGHT_WATTAGE, ATTR_ERROR_CODE_SET1]
            else:
                WATT_ATTRIBUTE = [ATTR_PHASE_CONTROL, ATTR_KEY_DOUBLE_UP, ATTR_ERROR_CODE_SET1]
            start = time.time()
            device_data = self._client.get_device_attributes(self._id,
                UPDATE_ATTRIBUTES + WATT_ATTRIBUTE)
            end = time.time()
            elapsed = round(end - start, 3)
            _LOGGER.debug("Updating %s (%s sec): %s",
                self._name, elapsed, device_data)
            if "error" not in device_data:
                if "errorCode" not in device_data:
                    if self._is_dimmable:
                        if ATTR_INTENSITY in device_data:
                            self._brightness_pct = round(device_data[ATTR_INTENSITY]) if \
                                device_data[ATTR_INTENSITY] is not None else 0
                        self._intensity_min = device_data[ATTR_INTENSITY_MIN]
                        if ATTR_PHASE_CONTROL in device_data:
                            self._phase_control = device_data[ATTR_PHASE_CONTROL]
                        if ATTR_KEY_DOUBLE_UP in device_data:
                            self._double_up = device_data[ATTR_KEY_DOUBLE_UP]
                    self._onoff = device_data[ATTR_ONOFF]
                    if not self._is_new_dimmable:
                        self._wattage = device_data[ATTR_LIGHT_WATTAGE]["value"]
#                        self._temp_status = device_data[ATTR_ERROR_CODE_SET1]["temperature"]
                    self._keypad = device_data[ATTR_KEYPAD]
                    self._timer = device_data[ATTR_TIMER]
                    self._led_on = str(device_data[ATTR_LED_ON_INTENSITY])+","+str(device_data[ATTR_LED_ON_COLOR]["red"])+","+str(device_data[ATTR_LED_ON_COLOR]["green"])+","+str(device_data[ATTR_LED_ON_COLOR]["blue"])
                    self._led_off = str(device_data[ATTR_LED_OFF_INTENSITY])+","+str(device_data[ATTR_LED_OFF_COLOR]["red"])+","+str(device_data[ATTR_LED_OFF_COLOR]["green"])+","+str(device_data[ATTR_LED_OFF_COLOR]["blue"])
                else:
                    _LOGGER.warning("Error in reading device %s: (%s)", self._name, device_data)
            elif device_data["error"]["code"] == "USRSESSEXP":
                _LOGGER.warning("Session expired... reconnecting...")
                self._client.reconnect()
            elif device_data["error"]["code"] == "ACCSESSEXC":
                _LOGGER.warning("Maximun session number reached...Close other connections and try again.")
                self.notify_ha(
                    f"Warning: Maximun Neviweb session number reached...Close other connections and try again."
                )
                self._client.reconnect()
            elif device_data["error"]["code"] == "DVCACTNSPTD":
                _LOGGER.warning("Device action not supported for %s...(SKU: %s) Report to maintainer.", self._name, self._sku)
            elif device_data["error"]["code"] == "DVCCOMMTO":
                _LOGGER.warning("Device Communication Timeout for %s... The device did not respond to the server within the prescribed delay. (SKU: %s)", self._name, self._sku)
            elif device_data["error"]["code"] == "SVCERR":
                _LOGGER.warning("Service error, device %s not available, retry later: %s...(SKU: %s)", self._name, device_data, self._sku)
            elif device_data["error"]["code"] == "DVCBUSY":
                _LOGGER.warning("Device busy can't reach (neviweb update ?), retry later %s: %s...(SKU: %s)", self._name, device_data, self._sku)
            elif device_data["error"]["code"] == "DVCUNVLB":
                _LOGGER.warning("Device %s is disconected from Neviweb: %s...(SKU: %s)", self._name, device_data, self._sku)
                _LOGGER.warning("This device %s is de-activated and won't be polled until you put it back on HA and Neviweb.",self._name)
                _LOGGER.warning("Then you will have to re-activate device %s with service.neviweb130_set_activation, or just restart HA.",self._name)
#                self._activ = False
                self.notify_ha(
                    f"Warning: Received message from Neviweb, device disconnected... Check you log... " + self._name
                )
            else:
                _LOGGER.warning("Unknown error for %s: %s...(SKU: %s) Report to maintainer.", self._name, device_data, self._sku)
            if start - self._energy_stat_time > STAT_INTERVAL and self._energy_stat_time != 0:
                device_hourly_stats = self._client.get_device_hourly_stats(self._id)
                if device_hourly_stats is not None and len(device_hourly_stats) > 1:
                    self._hour_energy_kwh_count = device_hourly_stats[1]["counter"] / 1000
                    self._hour_kwh = device_hourly_stats[1]["period"] / 1000
                else:
                    _LOGGER.warning("Got None for device_hourly_stats")
                device_daily_stats = self._client.get_device_daily_stats(self._id)
                if device_daily_stats is not None and len(device_daily_stats) > 1:
                    self._today_energy_kwh_count = device_daily_stats[0]["counter"] / 1000
                    self._today_kwh = device_daily_stats[0]["period"] / 1000
                else:
                    _LOGGER.warning("Got None for device_daily_stats")
                device_monthly_stats = self._client.get_device_monthly_stats(self._id)
                if device_monthly_stats is not None and len(device_monthly_stats) > 1:
                    self._month_energy_kwh_count = device_monthly_stats[0]["counter"] / 1000
                    self._month_kwh = device_monthly_stats[0]["period"] / 1000
                else:
                    _LOGGER.warning("Got None for device_monthly_stats")
                self._energy_stat_time = time.time()
            if self._energy_stat_time == 0:
                self._energy_stat_time = start

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
    def extra_state_attributes(self):
        """Return the state attributes."""
        data = {}
        if self._is_dimmable:
            data = {ATTR_BRIGHTNESS_PCT: self._brightness_pct,
                    'minimum_intensity': self._intensity_min,
                    'Temperature_status': self._temp_status}
        if self._is_new_dimmable:
            data.update({'phase_control': self._phase_control,
                        'Double_up_Action': self._double_up})
        else:
            data.update({'wattage': self._wattage,
                        'Temperature_status': self._temp_status})
        data.update({'onOff': self._onoff,
                     'keypad': self._keypad,
                     'timer': self._timer,
                     'led_on': self._led_on,
                     'led_off': self._led_off,
                     'hourly_kwh_count': self._hour_energy_kwh_count,
                     'daily_kwh_count': self._today_energy_kwh_count,
                     'monthly_kwh_count': self._month_energy_kwh_count,
                     'hourly_kwh': self._hour_kwh,
                     'daily_kwh': self._today_kwh,
                     'monthly_kwh': self._month_kwh,
                     'sku': self._sku,
                     'firmware': self._firmware,
                     'Activation': self._activ,
                     'id': self._id})
        return data

    @property
    def brightness(self):
        """Return intensity of light"""
        return brightness_from_percentage(self._brightness_pct)

    @property
    def is_on(self): ## need to change this for neviweb130
        """Return true if device is on."""
        return self._onoff != MODE_OFF

    # For the turn_on and turn_off functions, we would normally check if the
    # the requested state is different from the actual state to issue the 
    # command. But since we update the state every 6 minutes, there is good
    # chance that the current stored state doesn't match with real device 
    # state. So we force the set_brightness each time.

    def turn_on(self, **kwargs):
        """Turn the light on."""
        if not self.is_on:
            self._client.set_onoff(self._id, "on")
        if ATTR_BRIGHTNESS in kwargs and self.brightness != kwargs[ATTR_BRIGHTNESS]:
            brightness_pct = \
                brightness_to_percentage(round(kwargs.get(ATTR_BRIGHTNESS)))
            self._client.set_brightness(self._id, brightness_pct)
            self._brightness_pct = brightness_pct
        self._onoff = "on"

    def turn_off(self, **kwargs):
        """Turn the light off."""
        self._client.set_onoff(self._id, "off")
        self._brightness_pct = 0
        self._onoff = MODE_OFF

    def set_phase_control(self, value):
        """Change phase control parameter, reverse or forward """
        phase = value["phase"]
        entity = value["id"]
        self._client.set_phase(
            entity, phase)
        self._phase_control = phase

    def set_keypad_lock(self, value):
        """Lock or unlock device's keypad, lock = locked, unlock = unlocked"""
        lock = value["lock"]
        entity = value["id"]
        self._client.set_keypad_lock(
            entity, lock, False)
        self._keypad = lock

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

    def set_activation(self, value):
        """ Activate or deactivate neviweb polling for a missing device """
        action = value["active"]
        self._activ = action

    def set_key_double_up(self, value):
        """Change key double up action """
        double = value["double"]
        entity = value["id"]
        self._client.set_double_up(
            entity, double)
        self._double_up = double

    def notify_ha(self, msg: str, title: str = "Neviweb130 integration"):
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
