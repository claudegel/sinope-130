"""
Support for Neviweb light switch/dimmer connected to GT130 Zigbee.
model 2121 = light switch SW2500ZB
model 2121 = light switch SW2500ZB-G2
model 2131 = light dimmer DM2500ZB
model 2131 = light dimmer DM2500ZB-G2
model 2132 = light dimmer DM2550ZB
model 2132 = light dimmer DM2550ZB-G2
For more details about this platform, please refer to the documentation at
https://www.sinopetech.com/en/support/#api
"""

from __future__ import annotations

import logging
import time
from datetime import date, datetime, timezone

from homeassistant.components.light import ATTR_BRIGHTNESS, ATTR_BRIGHTNESS_PCT, ColorMode, LightEntity
from homeassistant.components.persistent_notification import DOMAIN as PN_DOMAIN
from homeassistant.const import ATTR_ENTITY_ID

from . import NOTIFY
from . import SCAN_INTERVAL as scan_interval
from . import STAT_INTERVAL
from .const import (
    ATTR_ACTIVE,
    ATTR_BLUE,
    ATTR_ERROR_CODE_SET1,
    ATTR_GREEN,
    ATTR_INTENSITY,
    ATTR_INTENSITY_MIN,
    ATTR_KEY_DOUBLE_UP,
    ATTR_KEYPAD,
    ATTR_LED_OFF_COLOR,
    ATTR_LED_OFF_INTENSITY,
    ATTR_LED_ON_COLOR,
    ATTR_LED_ON_INTENSITY,
    ATTR_LIGHT_WATTAGE,
    ATTR_ONOFF,
    ATTR_PHASE_CONTROL,
    ATTR_RED,
    ATTR_RSSI,
    ATTR_STATE,
    ATTR_TIMER,
    ATTR_WATTAGE_INSTANT,
    DOMAIN,
    MODE_OFF,
    SERVICE_SET_ACTIVATION,
    SERVICE_SET_KEY_DOUBLE_UP,
    SERVICE_SET_LED_INDICATOR,
    SERVICE_SET_LED_OFF_INTENSITY,
    SERVICE_SET_LED_ON_INTENSITY,
    SERVICE_SET_LIGHT_KEYPAD_LOCK,
    SERVICE_SET_LIGHT_MIN_INTENSITY,
    SERVICE_SET_LIGHT_TIMER,
    SERVICE_SET_PHASE_CONTROL,
    SERVICE_SET_WATTAGE,
)
from .schema import (
    SET_ACTIVATION_SCHEMA,
    SET_KEY_DOUBLE_UP_SCHEMA,
    SET_LED_INDICATOR_SCHEMA,
    SET_LED_OFF_INTENSITY_SCHEMA,
    SET_LED_ON_INTENSITY_SCHEMA,
    SET_LIGHT_KEYPAD_LOCK_SCHEMA,
    SET_LIGHT_MIN_INTENSITY_SCHEMA,
    SET_LIGHT_TIMER_SCHEMA,
    SET_PHASE_CONTROL_SCHEMA,
    SET_WATTAGE_SCHEMA,
    VERSION,
)

_LOGGER = logging.getLogger(__name__)

DEFAULT_NAME = f"{DOMAIN} light"
DEFAULT_NAME_2 = f"{DOMAIN} light 2"
DEFAULT_NAME_3 = f"{DOMAIN} light 3"
SNOOZE_TIME = 1200
SCAN_INTERVAL = scan_interval

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
    ATTR_RSSI,
]

DEVICE_MODEL_DIMMER = [2131]
DEVICE_MODEL_NEW_DIMMER = [2132]
DEVICE_MODEL_LIGHT = [2121]
IMPLEMENTED_DEVICE_MODEL = DEVICE_MODEL_LIGHT + DEVICE_MODEL_DIMMER + DEVICE_MODEL_NEW_DIMMER


async def async_setup_platform(
    hass,
    config,
    async_add_entities,
    discovery_info=None,
) -> None:
    """Set up the neviweb light."""
    data = hass.data[DOMAIN]

    entities = []
    for device_info in data.neviweb130_client.gateway_data:
        if (
            "signature" in device_info
            and "model" in device_info["signature"]
            and device_info["signature"]["model"] in IMPLEMENTED_DEVICE_MODEL
        ):
            device_name = "{} {}".format(DEFAULT_NAME, device_info["name"])
            device_sku = device_info["sku"]
            device_firmware = "{}.{}.{}".format(
                device_info["signature"]["softVersion"]["major"],
                device_info["signature"]["softVersion"]["middle"],
                device_info["signature"]["softVersion"]["minor"],
            )
            if device_info["signature"]["model"] in DEVICE_MODEL_LIGHT:
                entities.append(Neviweb130Light(data, device_info, device_name, device_sku, device_firmware))
            elif device_info["signature"]["model"] in DEVICE_MODEL_DIMMER:
                entities.append(Neviweb130Dimmer(data, device_info, device_name, device_sku, device_firmware))
            elif device_info["signature"]["model"] in DEVICE_MODEL_NEW_DIMMER:
                entities.append(Neviweb130NewDimmer(data, device_info, device_name, device_sku, device_firmware))
    for device_info in data.neviweb130_client.gateway_data2:
        if (
            "signature" in device_info
            and "model" in device_info["signature"]
            and device_info["signature"]["model"] in IMPLEMENTED_DEVICE_MODEL
        ):
            device_name = "{} {}".format(DEFAULT_NAME_2, device_info["name"])
            device_sku = device_info["sku"]
            device_firmware = "{}.{}.{}".format(
                device_info["signature"]["softVersion"]["major"],
                device_info["signature"]["softVersion"]["middle"],
                device_info["signature"]["softVersion"]["minor"],
            )
            if device_info["signature"]["model"] in DEVICE_MODEL_LIGHT:
                entities.append(Neviweb130Light(data, device_info, device_name, device_sku, device_firmware))
            elif device_info["signature"]["model"] in DEVICE_MODEL_DIMMER:
                entities.append(Neviweb130Dimmer(data, device_info, device_name, device_sku, device_firmware))
            elif device_info["signature"]["model"] in DEVICE_MODEL_NEW_DIMMER:
                entities.append(Neviweb130NewDimmer(data, device_info, device_name, device_sku, device_firmware))
    for device_info in data.neviweb130_client.gateway_data3:
        if (
            "signature" in device_info
            and "model" in device_info["signature"]
            and device_info["signature"]["model"] in IMPLEMENTED_DEVICE_MODEL
        ):
            device_name = "{} {}".format(DEFAULT_NAME_3, device_info["name"])
            device_sku = device_info["sku"]
            device_firmware = "{}.{}.{}".format(
                device_info["signature"]["softVersion"]["major"],
                device_info["signature"]["softVersion"]["middle"],
                device_info["signature"]["softVersion"]["minor"],
            )
            if device_info["signature"]["model"] in DEVICE_MODEL_LIGHT:
                entities.append(Neviweb130Light(data, device_info, device_name, device_sku, device_firmware))
            elif device_info["signature"]["model"] in DEVICE_MODEL_DIMMER:
                entities.append(Neviweb130Dimmer(data, device_info, device_name, device_sku, device_firmware))
            elif device_info["signature"]["model"] in DEVICE_MODEL_NEW_DIMMER:
                entities.append(Neviweb130NewDimmer(data, device_info, device_name, device_sku, device_firmware))

    async_add_entities(entities, True)

    def set_light_keypad_lock_service(service):
        """Lock/unlock keypad device."""
        entity_id = service.data[ATTR_ENTITY_ID]
        for light in entities:
            if light.entity_id == entity_id:
                value = {"id": light.unique_id, "lock": service.data[ATTR_KEYPAD]}
                light.set_keypad_lock(value)
                light.schedule_update_ha_state(True)
                break

    def set_light_timer_service(service):
        """Set timer for light device."""
        entity_id = service.data[ATTR_ENTITY_ID]
        for light in entities:
            if light.entity_id == entity_id:
                value = {"id": light.unique_id, "time": service.data[ATTR_TIMER]}
                light.set_timer(value)
                light.schedule_update_ha_state(True)
                break

    def set_led_indicator_service(service):
        """Set led color and intensity for light indicator."""
        entity_id = service.data[ATTR_ENTITY_ID]
        for light in entities:
            if light.entity_id == entity_id:
                value = {
                    "id": light.unique_id,
                    "state": service.data[ATTR_STATE],
                    "red": service.data[ATTR_RED],
                    "green": service.data[ATTR_GREEN],
                    "blue": service.data[ATTR_BLUE],
                }
                light.set_led_indicator(value)
                light.schedule_update_ha_state(True)
                break

    def set_led_on_intensity_service(service):
        """Set led on intensity for light indicator."""
        entity_id = service.data[ATTR_ENTITY_ID]
        for light in entities:
            if light.entity_id == entity_id:
                value = {
                    "id": light.unique_id,
                    "led_on": service.data[ATTR_LED_ON_INTENSITY],
                }
                light.set_led_on_intensity(value)
                light.schedule_update_ha_state(True)
                break

    def set_led_off_intensity_service(service):
        """Set led off intensity for light indicator."""
        entity_id = service.data[ATTR_ENTITY_ID]
        for light in entities:
            if light.entity_id == entity_id:
                value = {
                    "id": light.unique_id,
                    "led_off": service.data[ATTR_LED_OFF_INTENSITY],
                }
                light.set_led_off_intensity(value)
                light.schedule_update_ha_state(True)
                break

    def set_light_min_intensity_service(service):
        """Set dimmer light minimum intensity."""
        entity_id = service.data[ATTR_ENTITY_ID]
        for light in entities:
            if light.entity_id == entity_id:
                value = {
                    "id": light.unique_id,
                    "intensity": service.data[ATTR_INTENSITY_MIN],
                }
                light.set_light_min_intensity(value)
                light.schedule_update_ha_state(True)
                break

    def set_wattage_service(service):
        """Set watt load for light device."""
        entity_id = service.data[ATTR_ENTITY_ID]
        for light in entities:
            if light.entity_id == entity_id:
                value = {
                    "id": light.unique_id,
                    "watt": service.data[ATTR_LIGHT_WATTAGE],
                }
                light.set_wattage(value)
                light.schedule_update_ha_state(True)
                break

    def set_phase_control_service(service):
        """Change phase control mode for dimmer device."""
        entity_id = service.data[ATTR_ENTITY_ID]
        for light in entities:
            if light.entity_id == entity_id:
                value = {
                    "id": light.unique_id,
                    "phase": service.data[ATTR_PHASE_CONTROL],
                }
                light.set_phase_control(value)
                light.schedule_update_ha_state(True)
                break

    def set_activation_service(service):
        """Activate or deactivate Neviweb polling for missing device."""
        entity_id = service.data[ATTR_ENTITY_ID]
        for switch in entities:
            if switch.entity_id == entity_id:
                value = {"id": switch.unique_id, "active": service.data[ATTR_ACTIVE]}
                switch.set_activation(value)
                switch.schedule_update_ha_state(True)
                break

    def set_key_double_up_service(service):
        """Change key double up action for dimmer device."""
        entity_id = service.data[ATTR_ENTITY_ID]
        for light in entities:
            if light.entity_id == entity_id:
                value = {
                    "id": light.unique_id,
                    "double": service.data[ATTR_KEY_DOUBLE_UP],
                }
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
        SERVICE_SET_LED_ON_INTENSITY,
        set_led_on_intensity_service,
        schema=SET_LED_ON_INTENSITY_SCHEMA,
    )

    hass.services.async_register(
        DOMAIN,
        SERVICE_SET_LED_OFF_INTENSITY,
        set_led_off_intensity_service,
        schema=SET_LED_OFF_INTENSITY_SCHEMA,
    )

    hass.services.async_register(
        DOMAIN,
        SERVICE_SET_LIGHT_MIN_INTENSITY,
        set_light_min_intensity_service,
        schema=SET_LIGHT_MIN_INTENSITY_SCHEMA,
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


class Neviweb130Light(LightEntity):
    """Implementation of a neviweb light, SW2500ZB, SW2500ZB-G2."""

    def __init__(self, data, device_info, name, sku, firmware):
        """Initialize."""
        _LOGGER.debug("Setting up %s: %s", name, device_info)
        self._name = name
        self._sku = sku
        self._firmware = firmware
        self._client = data.neviweb130_client
        self._id = device_info["id"]
        self._device_model = device_info["signature"]["model"]
        self._device_model_cfg = device_info["signature"]["modelCfg"]
        self._is_light = device_info["signature"]["model"] in DEVICE_MODEL_LIGHT
        self._is_dimmable = (
            device_info["signature"]["model"] in DEVICE_MODEL_DIMMER
            or device_info["signature"]["model"] in DEVICE_MODEL_NEW_DIMMER
        )
        self._is_new_dimmable = device_info["signature"]["model"] in DEVICE_MODEL_NEW_DIMMER
        self._active = True
        self._brightness_pct = 0
        self._daily_kwh_count = 0
        self._double_up = None
        self._energy_stat_time = time.time() - 1500
        self._error_code = None
        self._hour_kwh = 0
        self._hourly_kwh_count = 0
        self._intensity_min = 600
        self._keypad = "Unlocked"
        self._led_off = "0,0,0,0"
        self._led_off_intensity = None
        self._led_on = "0,0,0,0"
        self._led_on_intensity = None
        self._mark = None
        self._marker = None
        self._month_kwh = 0
        self._monthly_kwh_count = 0
        self._onoff = None
        self._phase_control = None
        self._rssi = None
        self._snooze = 0.0
        self._timer = 0
        self._today_kwh = 0
        self._total_kwh_count = 0
        self._wattage = 0
        self._wattage_status = None

    def update(self):
        if self._active:
            """Get the latest data from neviweb and update the state."""
            WATT_ATTRIBUTE = [ATTR_LIGHT_WATTAGE, ATTR_ERROR_CODE_SET1]
            start = time.time()
            device_data = self._client.get_device_attributes(self._id, UPDATE_ATTRIBUTES + WATT_ATTRIBUTE)
            end = time.time()
            elapsed = round(end - start, 3)
            _LOGGER.debug("Updating %s (%s sec): %s", self._name, elapsed, device_data)
            if "error" not in device_data:
                if "errorCode" not in device_data:
                    self._onoff = device_data[ATTR_ONOFF]
                    self._wattage = device_data[ATTR_LIGHT_WATTAGE]["value"]
                    self._wattage_status = device_data[ATTR_LIGHT_WATTAGE]["status"]
                    if ATTR_ERROR_CODE_SET1 in device_data and len(device_data[ATTR_ERROR_CODE_SET1]) > 0:
                        if device_data[ATTR_ERROR_CODE_SET1]["raw"] != 0:
                            self._error_code = device_data[ATTR_ERROR_CODE_SET1]["raw"]
                            self.notify_ha(
                                "Warning: Neviweb Device error code detected: "
                                + str(device_data[ATTR_ERROR_CODE_SET1]["raw"])
                                + " for device: "
                                + self._name
                                + ", Sku: "
                                + self._sku
                            )
                    self._keypad = device_data[ATTR_KEYPAD]
                    self._timer = device_data[ATTR_TIMER]
                    self._rssi = device_data[ATTR_RSSI]
                    self._led_on = (
                        str(device_data[ATTR_LED_ON_INTENSITY])
                        + ","
                        + str(device_data[ATTR_LED_ON_COLOR]["red"])
                        + ","
                        + str(device_data[ATTR_LED_ON_COLOR]["green"])
                        + ","
                        + str(device_data[ATTR_LED_ON_COLOR]["blue"])
                    )
                    self._led_off = (
                        str(device_data[ATTR_LED_OFF_INTENSITY])
                        + ","
                        + str(device_data[ATTR_LED_OFF_COLOR]["red"])
                        + ","
                        + str(device_data[ATTR_LED_OFF_COLOR]["green"])
                        + ","
                        + str(device_data[ATTR_LED_OFF_COLOR]["blue"])
                    )
                else:
                    _LOGGER.warning("Error in updating device %s: (%s)", self._name, device_data)
            else:
                self.log_error(device_data["error"]["code"])
            self.do_stat(start)
        else:
            if time.time() - self._snooze > SNOOZE_TIME:
                self._active = True
                if NOTIFY == "notification" or NOTIFY == "both":
                    self.notify_ha("Warning: Neviweb Device update restarted for " + self._name + ", Sku: " + self._sku)

    @property
    def supported_color_modes(self):
        """Return the list of supported colorMode features."""
        if self._is_dimmable:
            return {ColorMode.BRIGHTNESS}
        return {ColorMode.ONOFF}

    @property
    def color_mode(self):
        """Set ColorMode."""
        if self._is_dimmable:
            return ColorMode.BRIGHTNESS
        return ColorMode.ONOFF

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
        data.update(
            {
                "wattage": self._wattage,
                "wattage_status": self._wattage_status,
                "error_code": self._error_code,
                "onOff": self._onoff,
                "keypad": lock_to_ha(self._keypad),
                "timer": self._timer,
                "led_on": self._led_on,
                "led_off": self._led_off,
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
                "rssi": self._rssi,
                "firmware": self._firmware,
                "activation": self._active,
                "id": str(self._id),
            }
        )
        return data

    @property
    def brightness(self):
        """Return intensity of light."""
        return brightness_from_percentage(self._brightness_pct)

    @property
    def is_on(self):  # need to change this for neviweb130
        """Return true if device is on."""
        return self._onoff != MODE_OFF

    # For the turn_on and turn_off functions, we would normally check if
    # the requested state is different from the actual state to issue the
    # command. But since we update the state every 6 minutes, there is good
    # chance that the current stored state doesn't match with real device
    # state. So we force the set_brightness each time.

    def turn_on(self, **kwargs):
        """Turn the light on."""
        if not self.is_on:
            if self._brightness_pct == 0:
                self._brightness_pct = 5
            self._client.set_light_onoff(self._id, "on", self._brightness_pct)
        if ATTR_BRIGHTNESS in kwargs and self.brightness != kwargs[ATTR_BRIGHTNESS]:
            brightness_pct = brightness_to_percentage(round(kwargs[ATTR_BRIGHTNESS]))
            self._client.set_brightness(self._id, brightness_pct)
            self._brightness_pct = brightness_pct
        self._onoff = "on"

    def turn_off(self, **kwargs):
        """Turn the light off."""
        self._client.set_onoff(self._id, "off")
        self._onoff = MODE_OFF

    def set_phase_control(self, value):
        """Change phase control parameter, reverse or forward."""
        self._client.set_phase(value["id"], value["phase"])
        self._phase_control = value["phase"]

    def set_keypad_lock(self, value):
        """Lock, unlock or partially lock device's keypad,
        lock = locked, unlock = unlocked, partiallyLocked = partial lock."""
        self._client.set_keypad_lock(value["id"], value["lock"], False)
        self._keypad = value["lock"]

    def set_timer(self, value):
        """Set device timer, 0 = off, 1 to 255 = timer length."""
        self._client.set_timer(value["id"], value["time"])
        self._timer = value["time"]

    def set_led_indicator(self, value):
        """Set led indicator color and intensity,
        based on RGB red, green, blue colors (0-255) and intensity from 0 to 100."""
        self._client.set_led_indicator(value["id"], value["state"], value["red"], value["green"], value["blue"])
        rgb = f"{value['red']},{value['green']},{value['blue']}"
        if value["state"] == 0:
            self._led_off = rgb
        else:
            self._led_on = rgb

    def set_led_on_intensity(self, value):
        """Set led indicator on intensity from 0 to 100."""
        self._client.set_led_on_intensity(value["id"], value["led_on"])
        self._led_on_intensity = value["led_on"]

    def set_led_off_intensity(self, value):
        """Set led indicator off intensity from 0 to 100."""
        self._client.set_led_off_intensity(value["id"], value["led_off"])
        self._led_off_intensity = value["led_off"]

    def set_light_min_intensity(self, value):
        """Set dimmer light minimum intensity from 1 to 3000."""
        self._client.set_light_min_intensity(value["id"], value["intensity"])
        self._intensity_min = value["intensity"]

    def set_wattage(self, value):
        """Set light device watt load."""
        self._client.set_wattage(value["id"], value["watt"])
        self._wattage = value["watt"]

    def set_activation(self, value):
        """Activate or deactivate neviweb polling for a missing device."""
        self._active = value["active"]

    def set_key_double_up(self, value):
        """Change key double up action."""
        self._client.set_double_up(value["id"], value["double"])
        self._double_up = value["double"]

    def do_stat(self, start):
        """Get device energy statistic."""
        if start - self._energy_stat_time > STAT_INTERVAL and self._energy_stat_time != 0:
            today = date.today()
            current_month = today.month
            current_day = today.day
            device_monthly_stats = self._client.get_device_monthly_stats(self._id)
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
                dt_month = datetime.fromisoformat(device_monthly_stats[n - 1]["date"][:-1] + "+00:00").astimezone(
                    timezone.utc
                )
                _LOGGER.debug("stat month = %s", dt_month.month)
            else:
                self._month_kwh = 0
                _LOGGER.warning("%s Got None for device_monthly_stats", self._name)
            device_daily_stats = self._client.get_device_daily_stats(self._id)
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
                _LOGGER.warning("%s Got None for device_daily_stats", self._name)
            device_hourly_stats = self._client.get_device_hourly_stats(self._id)
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
                _LOGGER.warning("%s Got None for device_hourly_stats", self._name)
            if self._total_kwh_count == 0:
                self._total_kwh_count = round(
                    self._monthly_kwh_count + self._daily_kwh_count + self._hourly_kwh_count,
                    3,
                )
                # async_add_data(self._id, self._total_kwh_count, self._marker)
                # self.async_write_ha_state()
                self._mark = self._marker
            else:
                if self._marker != self._mark:
                    self._total_kwh_count += round(self._hour_kwh, 3)
                    # save_data(self._id, self._total_kwh_count, self._marker)
                    self._mark = self._marker
            # _LOGGER.debug("Device dict updated: %s", device_dict)
            self._energy_stat_time = time.time()
        if self._energy_stat_time == 0:
            self._energy_stat_time = start

    def log_error(self, error_data):
        """Send error message to LOG."""
        if error_data == "USRSESSEXP":
            _LOGGER.warning("Session expired... reconnecting...")
            if NOTIFY == "notification" or NOTIFY == "both":
                self.notify_ha(
                    "Warning: Got USRSESSEXP error, Neviweb session expired. "
                    + "Set your scan_interval parameter to less than 10 "
                    + "minutes to avoid this... Reconnecting..."
                )
            self._client.reconnect()
        elif error_data == "ACCDAYREQMAX":
            _LOGGER.warning("Maximum daily request reached...Reduce polling frequency.")
        elif error_data == "TimeoutError":
            _LOGGER.warning("Timeout error detected...Retry later.")
        elif error_data == "MAINTENANCE":
            _LOGGER.warning("Access blocked for maintenance...Retry later.")
            self.notify_ha("Warning: Neviweb access temporary blocked for maintenance...Retry later.")
            self._client.reconnect()
        elif error_data == "ACCSESSEXC":
            _LOGGER.warning("Maximum session number reached...Close other connections and try again.")
            self.notify_ha("Warning: Maximum Neviweb session number reached...Close other connections and try again.")
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
                "Device action not supported for %s (id: %s)... (SKU: %s) Report to maintainer.",
                self._name,
                str(self._id),
                self._sku,
            )
        elif error_data == "DVCCOMMTO":
            _LOGGER.warning(
                "Device Communication Timeout for %s (id: %s)... The device "
                + "did not respond to the server within the prescribed delay."
                + "(SKU: %s)",
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
                    "This device %s is de-activated and won't be updated for 20 minutes.",
                    self._name,
                )
                _LOGGER.warning(
                    "You can re-activate device %s with "
                    + "service.neviweb130_set_activation or wait 20 minutes "
                    + "for update to restart or just restart HA.",
                    self._name,
                )
            if NOTIFY == "notification" or NOTIFY == "both":
                self.notify_ha(
                    "Warning: Received message from Neviweb, device disconnected..."
                    + "Check your log... Neviweb update will be halted for 20 "
                    + "minutes for "
                    + self._name
                    + ", id: "
                    + str(self._id)
                    + ", Sku: "
                    + self._sku
                )
            self._active = False
            self._snooze = time.time()
        else:
            _LOGGER.warning(
                "Unknown error for %s (id: %s): %s... (SKU: %s) Report to maintainer.",
                self._name,
                str(self._id),
                error_data,
                self._sku,
            )

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


class Neviweb130Dimmer(Neviweb130Light):
    """Implementation of a neviweb dimmer, DM2500ZB, DM2500ZB-G2."""

    def update(self):
        if self._active:
            """Get the latest data from neviweb and update the state."""
            WATT_ATTRIBUTE = [ATTR_LIGHT_WATTAGE, ATTR_ERROR_CODE_SET1]
            start = time.time()
            device_data = self._client.get_device_attributes(self._id, UPDATE_ATTRIBUTES + WATT_ATTRIBUTE)
            end = time.time()
            elapsed = round(end - start, 3)
            _LOGGER.debug("Updating %s (%s sec): %s", self._name, elapsed, device_data)
            if "error" not in device_data:
                if "errorCode" not in device_data:
                    if ATTR_INTENSITY in device_data:
                        self._brightness_pct = (
                            round(device_data[ATTR_INTENSITY]) if device_data[ATTR_INTENSITY] is not None else 0
                        )
                    self._intensity_min = device_data[ATTR_INTENSITY_MIN]
                    self._onoff = device_data[ATTR_ONOFF]
                    self._wattage = device_data[ATTR_LIGHT_WATTAGE]["value"]
                    self._wattage_status = device_data[ATTR_LIGHT_WATTAGE]["status"]
                    if ATTR_ERROR_CODE_SET1 in device_data and len(device_data[ATTR_ERROR_CODE_SET1]) > 0:
                        if device_data[ATTR_ERROR_CODE_SET1]["raw"] != 0:
                            self._error_code = device_data[ATTR_ERROR_CODE_SET1]["raw"]
                            self.notify_ha(
                                "Warning: Neviweb Device error code detected: "
                                + str(device_data[ATTR_ERROR_CODE_SET1]["raw"])
                                + " for device: "
                                + self._name
                                + ", Sku: "
                                + self._sku
                            )
                    self._keypad = device_data[ATTR_KEYPAD]
                    self._timer = device_data[ATTR_TIMER]
                    self._rssi = device_data[ATTR_RSSI]
                    self._led_on = (
                        str(device_data[ATTR_LED_ON_INTENSITY])
                        + ","
                        + str(device_data[ATTR_LED_ON_COLOR]["red"])
                        + ","
                        + str(device_data[ATTR_LED_ON_COLOR]["green"])
                        + ","
                        + str(device_data[ATTR_LED_ON_COLOR]["blue"])
                    )
                    self._led_off = (
                        str(device_data[ATTR_LED_OFF_INTENSITY])
                        + ","
                        + str(device_data[ATTR_LED_OFF_COLOR]["red"])
                        + ","
                        + str(device_data[ATTR_LED_OFF_COLOR]["green"])
                        + ","
                        + str(device_data[ATTR_LED_OFF_COLOR]["blue"])
                    )
                else:
                    _LOGGER.warning("Error reading device %s: (%s)", self._name, device_data)
            else:
                self.log_error(device_data["error"]["code"])
            self.do_stat(start)
        else:
            if time.time() - self._snooze > SNOOZE_TIME:
                self._active = True
                if NOTIFY == "notification" or NOTIFY == "both":
                    self.notify_ha("Warning: Neviweb Device update restarted for " + self._name + ", Sku: " + self._sku)

    @property
    def extra_state_attributes(self):
        """Return the state attributes."""
        data = {}
        data.update(
            {
                ATTR_BRIGHTNESS_PCT: self._brightness_pct,
                "minimum_intensity": self._intensity_min,
                "error_code": self._error_code,
                "wattage": self._wattage,
                "wattage_status": self._wattage_status,
                "onOff": self._onoff,
                "keypad": lock_to_ha(self._keypad),
                "timer": self._timer,
                "led_on": self._led_on,
                "led_off": self._led_off,
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
                "rssi": self._rssi,
                "activation": self._active,
                "id": str(self._id),
            }
        )
        return data


class Neviweb130NewDimmer(Neviweb130Light):
    """Implementation of a neviweb new dimmer DM2550ZB, DM2550ZB-G2."""

    def update(self):
        if self._active:
            """Get the latest data from neviweb and update the state."""
            WATT_ATTRIBUTE = [
                ATTR_PHASE_CONTROL,
                ATTR_KEY_DOUBLE_UP,
                ATTR_WATTAGE_INSTANT,
                ATTR_ERROR_CODE_SET1,
            ]
            start = time.time()
            device_data = self._client.get_device_attributes(self._id, UPDATE_ATTRIBUTES + WATT_ATTRIBUTE)
            end = time.time()
            elapsed = round(end - start, 3)
            _LOGGER.debug("Updating %s (%s sec): %s", self._name, elapsed, device_data)
            if "error" not in device_data:
                if "errorCode" not in device_data:
                    if ATTR_INTENSITY in device_data:
                        self._brightness_pct = (
                            round(device_data[ATTR_INTENSITY]) if device_data[ATTR_INTENSITY] is not None else 0
                        )
                    self._intensity_min = device_data[ATTR_INTENSITY_MIN]
                    self._phase_control = device_data[ATTR_PHASE_CONTROL]
                    self._double_up = device_data[ATTR_KEY_DOUBLE_UP]
                    self._onoff = device_data[ATTR_ONOFF]
                    self._keypad = device_data[ATTR_KEYPAD]
                    self._wattage = device_data[ATTR_WATTAGE_INSTANT]
                    self._timer = device_data[ATTR_TIMER]
                    if ATTR_ERROR_CODE_SET1 in device_data and len(device_data[ATTR_ERROR_CODE_SET1]) > 0:
                        if device_data[ATTR_ERROR_CODE_SET1]["raw"] != 0:
                            self._error_code = device_data[ATTR_ERROR_CODE_SET1]["raw"]
                            self.notify_ha(
                                "Warning: Neviweb Device error code detected: "
                                + str(device_data[ATTR_ERROR_CODE_SET1]["raw"])
                                + " for device: "
                                + self._name
                                + ", Sku: "
                                + self._sku
                            )
                    self._rssi = device_data[ATTR_RSSI]
                    self._led_on = (
                        str(device_data[ATTR_LED_ON_INTENSITY])
                        + ","
                        + str(device_data[ATTR_LED_ON_COLOR]["red"])
                        + ","
                        + str(device_data[ATTR_LED_ON_COLOR]["green"])
                        + ","
                        + str(device_data[ATTR_LED_ON_COLOR]["blue"])
                    )
                    self._led_off = (
                        str(device_data[ATTR_LED_OFF_INTENSITY])
                        + ","
                        + str(device_data[ATTR_LED_OFF_COLOR]["red"])
                        + ","
                        + str(device_data[ATTR_LED_OFF_COLOR]["green"])
                        + ","
                        + str(device_data[ATTR_LED_OFF_COLOR]["blue"])
                    )
                else:
                    _LOGGER.warning("Error reading device %s: (%s)", self._name, device_data)
            else:
                self.log_error(device_data["error"]["code"])
            self.do_stat(start)
        else:
            if time.time() - self._snooze > SNOOZE_TIME:
                self._active = True
                if NOTIFY == "notification" or NOTIFY == "both":
                    self.notify_ha("Warning: Neviweb Device update restarted for " + self._name + ", Sku: " + self._sku)

    @property
    def extra_state_attributes(self):
        """Return the state attributes."""
        data = {}
        data.update(
            {
                ATTR_BRIGHTNESS_PCT: self._brightness_pct,
                "minimum_intensity": self._intensity_min,
                "error_code": self._error_code,
                "phase_control": self._phase_control,
                "double_up_Action": self._double_up,
                "wattage": self._wattage,
                "onOff": self._onoff,
                "keypad": lock_to_ha(self._keypad),
                "timer": self._timer,
                "led_on": self._led_on,
                "led_off": self._led_off,
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
                "rssi": self._rssi,
                "activation": self._active,
                "id": str(self._id),
            }
        )
        return data
