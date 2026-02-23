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
from threading import Lock
from typing import Any, Mapping, override

from homeassistant.components.light import ATTR_BRIGHTNESS, ATTR_BRIGHTNESS_PCT, ColorMode, LightEntity
from homeassistant.components.persistent_notification import DOMAIN as PN_DOMAIN
from homeassistant.components.recorder.models import StatisticMeanType
from homeassistant.components.sensor import SensorStateClass
from homeassistant.config_entries import ConfigEntry
from homeassistant.const import ATTR_ENTITY_ID
from homeassistant.core import HomeAssistant, ServiceCall
from homeassistant.exceptions import ServiceValidationError
from homeassistant.helpers import device_registry as dr
from homeassistant.helpers.device_registry import DeviceInfo
from homeassistant.helpers.entity_platform import AddEntitiesCallback
from homeassistant.helpers.update_coordinator import CoordinatorEntity

from .const import (
    ATTR_ACTIVE,
    ATTR_COLOR,
    ATTR_ERROR_CODE_SET1,
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
    ATTR_RSSI,
    ATTR_STATE,
    ATTR_TIME,
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
    VERSION,
)
from .devices import save_devices
from .helpers import (
    async_notify_once_or_update,
    async_notify_throttled,
    async_notify_critical,
    NeviwebEntityHelper,
    NamingHelper,
    translate_error,
)
from .schema import (
    HA_TO_NEVIWEB_TIMER,
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
    color_to_rgb,
    rgb_to_color,
)

_LOGGER = logging.getLogger(__name__)

SNOOZE_TIME = 1200

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


async def async_setup_entry(
    hass: HomeAssistant,
    entry: ConfigEntry,
    async_add_entities: AddEntitiesCallback,
    discovery_info=None,
) -> None:
    """Set up the neviweb130 light."""
    data = hass.data[DOMAIN][entry.entry_id]

    data["conf_dir"] = hass.data[DOMAIN]["conf_dir"]
    data["device_dict"] = hass.data[DOMAIN]["device_dict"]
    config_prefix = data["prefix"]

    if "neviweb130_client" not in data:
        _LOGGER.error("Neviweb130 client initialization failed.")
        return

    coordinator = hass.data[DOMAIN][entry.entry_id]["coordinator"]

    device_registry = dr.async_get(hass)

    platform = __name__.split(".")[-1] # "light"
    naming = NamingHelper(domain=DOMAIN, prefix=config_prefix)

    entities: list[Neviweb130Light] = []
    for index, gateway_data in enumerate([
        data["neviweb130_client"].gateway_data,
        data["neviweb130_client"].gateway_data2,
        data["neviweb130_client"].gateway_data3,
    ], start=1):

        default_name = naming.default_name(platform, index)
        if gateway_data is not None and gateway_data != "_":
            for device_info in gateway_data:
                if "signature" in device_info and "model" in device_info["signature"]:
                    model = device_info["signature"]["model"]
                    if model in IMPLEMENTED_DEVICE_MODEL:
                        device_name = naming.device_name(platform, index, device_info)
                        device_sku = device_info["sku"]
                        device_firmware = "{major}.{middle}.{minor}".format(
                            **device_info["signature"]["softVersion"]
                        )
                        # Ensure the device is registered in the device registry
                        device_registry.async_get_or_create(
                            config_entry_id=entry.entry_id,
                            identifiers={(DOMAIN, str(device_info["id"]))},
                            name=device_name,
                            manufacturer="claudegel",
                            model=device_info["signature"]["model"],
                            sw_version=device_firmware,
                        )
                        device = None
                        if device_info["signature"]["model"] in DEVICE_MODEL_LIGHT:
                            device = Neviweb130Light(
                                data,
                                device_info,
                                device_name,
                                device_sku,
                                device_firmware,
                                coordinator,
                                entry,
                            )
                        elif device_info["signature"]["model"] in DEVICE_MODEL_DIMMER:
                            device = Neviweb130Dimmer(
                                data,
                                device_info,
                                device_name,
                                device_sku,
                                device_firmware,
                                coordinator,
                                entry,
                            )
                        elif device_info["signature"]["model"] in DEVICE_MODEL_NEW_DIMMER:
                            device = Neviweb130NewDimmer(
                                data,
                                device_info,
                                device_name,
                                device_sku,
                                device_firmware,
                                coordinator,
                                entry,
                            )

                        _LOGGER.warning("Device registered = %s", device_info["id"])
                        entities.append(device)
                        coordinator.register_device(device)

    async_add_entities(entities, True)
    hass.async_create_task(coordinator.async_request_refresh())

    entity_map: dict[str, Neviweb130Light] | None = None
    _entity_map_lock = Lock()

    def get_light(service: ServiceCall) -> Neviweb130Light:
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

        light = entity_map.get(entity_id)
        if light is None:
            msg = translate_error(hass, "entity_must_be_domain", entity=entity_id, domain=DOMAIN, platform="light")
            raise ServiceValidationError(msg)
        return light

    async def set_light_keypad_lock_service(service: ServiceCall) -> None:
        """Lock/unlock keypad device."""
        light = get_light(service)
        value = {"id": light.unique_id, "lock": service.data[ATTR_KEYPAD]}
        await light.async_set_keypad_lock(value)
        light.async_schedule_update_ha_state(True)
        hass.async_create_task(coordinator.async_request_refresh())

    async def set_light_timer_service(service: ServiceCall) -> None:
        """Set timer for light device."""
        light = get_light(service)
        value = {"id": light.unique_id, ATTR_TIME: service.data[ATTR_TIMER]}
        await light.async_set_timer(value)
        light.async_schedule_update_ha_state(True)
        hass.async_create_task(coordinator.async_request_refresh())

    async def set_led_indicator_service(service: ServiceCall) -> None:
        """Set led color and intensity for light indicator."""
        light = get_light(service)
        value = {
            "id": light.unique_id,
            "state": service.data[ATTR_STATE],
            "color": service.data[ATTR_COLOR],
        }
        await light.async_set_led_indicator(value)
        light.async_schedule_update_ha_state(True)
        hass.async_create_task(coordinator.async_request_refresh())

    async def set_led_on_intensity_service(service: ServiceCall) -> None:
        """Set led on intensity for light indicator."""
        light = get_light(service)
        value = {
            "id": light.unique_id,
            "led_on": service.data[ATTR_LED_ON_INTENSITY],
        }
        await light.async_set_led_on_intensity(value)
        light.async_schedule_update_ha_state(True)
        hass.async_create_task(coordinator.async_request_refresh())

    async def set_led_off_intensity_service(service: ServiceCall) -> None:
        """Set led off intensity for light indicator."""
        light = get_light(service)
        value = {
            "id": light.unique_id,
            "led_off": service.data[ATTR_LED_OFF_INTENSITY],
        }
        await light.async_set_led_off_intensity(value)
        light.async_schedule_update_ha_state(True)
        hass.async_create_task(coordinator.async_request_refresh())

    async def set_light_min_intensity_service(service: ServiceCall) -> None:
        """Set dimmer light minimum intensity."""
        light = get_light(service)
        value = {
            "id": light.unique_id,
            "intensity": service.data[ATTR_INTENSITY_MIN],
        }
        await light.async_set_light_min_intensity(value)
        light.async_schedule_update_ha_state(True)
        hass.async_create_task(coordinator.async_request_refresh())

    async def set_wattage_service(service: ServiceCall) -> None:
        """Set watt load for light device."""
        light = get_light(service)
        value = {
            "id": light.unique_id,
            "watt": service.data[ATTR_LIGHT_WATTAGE],
        }
        await light.async_set_wattage(value)
        light.async_schedule_update_ha_state(True)
        hass.async_create_task(coordinator.async_request_refresh())

    async def set_phase_control_service(service: ServiceCall) -> None:
        """Change phase control mode for dimmer device."""
        light = get_light(service)
        value = {
            "id": light.unique_id,
            "phase": service.data[ATTR_PHASE_CONTROL],
        }
        await light.async_set_phase_control(value)
        light.async_schedule_update_ha_state(True)
        hass.async_create_task(coordinator.async_request_refresh())

    async def set_activation_service(service: ServiceCall) -> None:
        """Activate or deactivate Neviweb polling for missing device."""
        light = get_light(service)
        value = {
            "id": light.unique_id,
            "active": service.data[ATTR_ACTIVE],
        }
        await light.async_set_activation(value)
        light.async_schedule_update_ha_state(True)
        hass.async_create_task(coordinator.async_request_refresh())

    async def set_key_double_up_service(service: ServiceCall) -> None:
        """Change key double up action for dimmer device."""
        light = get_light(service)
        value = {
            "id": light.unique_id,
            "double": service.data[ATTR_KEY_DOUBLE_UP],
        }
        await light.async_set_key_double_up(value)
        light.async_schedule_update_ha_state(True)
        hass.async_create_task(coordinator.async_request_refresh())

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


def neviweb_to_ha_timer(value: int) -> str:
    """Transform numerical value from neviweb to string"""
    last = "unknown"
    for k, v in sorted(HA_TO_NEVIWEB_TIMER.items(), key=lambda x: x[1]):
        last = k
        if value <= v:
            return k
    return last


def lock_to_ha(lock):
    """Convert keypad lock state to better description."""
    match lock:
        case "locked":
            return "locked"
        case "lock":
            return "locked"
        case "unlocked":
            return "unlocked"
        case "unlock":
            return "unlocked"
        case "partiallyLocked":
            return "tamper protection"
        case "partialLock":
            return "tamper protection"
    return None


def retrieve_data(id, device_dict, data):
    """Retrieve device stat data from device_dict."""
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


class Neviweb130Light(CoordinatorEntity, LightEntity):
    """Implementation of a neviweb light, SW2500ZB, SW2500ZB-G2."""

    def __init__(self, data, device_info, name, sku, firmware, coordinator, entry):
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
        self._sku = sku
        self._firmware = firmware
        self._client = data["neviweb130_client"]
        self._stat_interval = data["stat_interval"]
        self._notify = data["notify"]
        self._prefix = data["prefix"]
        self._entry = entry
        self._id = str(device_info["id"])
        self._device_model = device_info["signature"]["model"]
        self._device_model_cfg = device_info["signature"]["modelCfg"]
        self._hard_rev = device_info["signature"]["hardRev"]
        self._identifier = device_info["identifier"]
        self._is_light = device_info["signature"]["model"] in DEVICE_MODEL_LIGHT
        self._is_dimmable = (
            device_info["signature"]["model"] in DEVICE_MODEL_DIMMER
            or device_info["signature"]["model"] in DEVICE_MODEL_NEW_DIMMER
        )
        self._is_new_dimmable = device_info["signature"]["model"] in DEVICE_MODEL_NEW_DIMMER
        self._active: bool = True
        self._brightness_pct = 0
        self._daily_kwh_count = 0
        self._double_up = None
        self._energy_stat_time = time.time() - 1500
        self._error_code = None
        self._hour_kwh = 0
        self._hourly_kwh_count = 0
        self._intensity_min = None
        self._keypad = None
        self._led_off_color = "0,0,0"
        self._led_off_intensity = 20
        self._led_on_color = "0,0,0"
        self._led_on_intensity = 50
        self._mark = retrieve_data(self._id, self._device_dict, 2)
        self._marker = None
        self._month_kwh = 0
        self._monthly_kwh_count = 0
        self._onoff = None
        self._phase_control = None
        self._rssi = None
        self._snooze: float = 0.0
        self._timer: str | None = "off"
        self._today_kwh = 0
        self._total_kwh_count = retrieve_data(self._id, self._device_dict, 1)
        self._wattage = 0
        self._wattage_status = None

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
            """Get the latest data from neviweb and update the state."""
            WATT_ATTRIBUTE = [
                ATTR_LIGHT_WATTAGE,
                ATTR_ERROR_CODE_SET1,
            ]
            start = time.time()
            device_data = await self._client.async_get_device_attributes(self._id, UPDATE_ATTRIBUTES + WATT_ATTRIBUTE)
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
                            msg = translate_error(
                                self.hass,
                                "error_code",
                                code=str(device_data[ATTR_ERROR_CODE_SET1]["raw"]),
                                message="",
                                name=self._name,
                                id=self._id,
                                sku=self._sku
                            )
                            await self.async_notify_critical(
                                self.hass,
                                msg,
                                title=f"Neviweb130 integration {VERSION}",
                                notification_id="neviweb130_error_code",
                            )
                    self._keypad = lock_to_ha(device_data[ATTR_KEYPAD])
                    self._timer = neviweb_to_ha_timer(device_data[ATTR_TIMER])
                    self._rssi = device_data[ATTR_RSSI]
                    self._led_on_color = (
                        str(device_data[ATTR_LED_ON_COLOR]["red"])
                        + ","
                        + str(device_data[ATTR_LED_ON_COLOR]["green"])
                        + ","
                        + str(device_data[ATTR_LED_ON_COLOR]["blue"])
                    )
                    self._led_off_color = (
                        str(device_data[ATTR_LED_OFF_COLOR]["red"])
                        + ","
                        + str(device_data[ATTR_LED_OFF_COLOR]["green"])
                        + ","
                        + str(device_data[ATTR_LED_OFF_COLOR]["blue"])
                    )
                    self._led_on_intensity = device_data[ATTR_LED_ON_INTENSITY]
                    self._led_off_intensity = device_data[ATTR_LED_OFF_INTENSITY]
                    self.async_write_ha_state()
                else:
                    _LOGGER.warning(
                        "Error in updating device %s: (%s)",
                        self._name,
                        device_data,
                    )
            else:
                await self.async_log_error(device_data["error"]["code"])
            await self.async_do_stat(start)
        else:
            if time.time() - self._snooze > SNOOZE_TIME:
                self._active = True
                if self._notify == "notification" or self._notify == "both":
                    msg = translate_error(self.hass, "update_restarted", name=self._name, sku=self._sku)
                    await async_notify_once_or_update(
                        self.hass,
                        msg,
                        title=f"Neviweb130 integration {VERSION}",
                        notification_id=f"neviweb130_update_restarted",
                    )

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
    @override
    def unique_id(self) -> str:
        """Return unique ID based on Neviweb device ID."""
        return f"{self._entry.entry_id}_{self._id}"

    @property
    @override
    def id(self) -> str:
        """Alias for DataUpdateCoordinator."""
        return self._id

    @property
    @override
    def name(self):
        """Return the name of the light."""
        if self._prefix:
            return f"{self._prefix} {self._name}"
        return self._name

    @property
    @override
    def device_class(self):
        """Return the device class of this entity."""
        return "light"

    @property
    def rssi(self):
        if self._rssi is not None:
            return self._rssi
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
    def led_on_intensity(self):
        if self._led_on_intensity is not None:
            return self._led_on_intensity
        return None

    @property
    def led_off_intensity(self):
        if self._led_off_intensity is not None:
            return self._led_off_intensity
        return None

    @property
    def intensity_min(self):
        if self._intensity_min is not None:
            return self._intensity_min
        return None

    @property
    def light_timer(self):
        if self._timer is not None:
            return self._timer
        return None

    @property
    def keypad(self):
        if self._keypad is not None:
            return lock_to_ha(self._keypad)
        return None

    @property
    def led_on_color(self):
        if self._led_on_color != "0,0,0":
            return rgb_to_color(self._led_on_color)
        return "0,0,0"

    @property
    def led_off_color(self):
        if self._led_off_color != "0,0,0":
            return rgb_to_color(self._led_off_color)
        return "0,0,0"

    @property
    def wattage(self):
        return self._wattage

    @property
    def activation(self) -> bool:
        return bool(self._active)

    @property
    @override
    def extra_state_attributes(self)  -> Mapping[str, Any]:
        """Return the state attributes."""
        data = {}
        data.update(
            {
                "wattage": self._wattage,
                "wattage_status": self._wattage_status,
                "error_code": self._error_code,
                "onOff": self._onoff,
                "keypad": self._keypad,
                "timer": self._timer,
                "led_on_value": self._led_on_color,
                "led_off_value": self._led_off_color,
                "led_on_color": rgb_to_color(self._led_on_color),
                "led_off_color": rgb_to_color(self._led_off_color),
                "led_on_intensity": self._led_on_intensity,
                "led_off_intensity": self._led_off_intensity,
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
                "id": self._id,
            }
        )
        return data

    @property
    def brightness(self):
        """Return intensity of light."""
        return brightness_from_percentage(self._brightness_pct)

    @property
    def is_on(self) -> bool:  # need to change this for neviweb130
        """Return true if device is on."""
        return self._onoff != MODE_OFF

    async def async_turn_on(self, **kwargs):
        """Turn the light on."""
        if not self.is_on:
            if self._brightness_pct == 0:
                self._brightness_pct = 5
            await self._client.async_set_light_onoff(self._id, "on", self._brightness_pct)
        if ATTR_BRIGHTNESS in kwargs and self.brightness != kwargs[ATTR_BRIGHTNESS]:
            brightness_pct = brightness_to_percentage(round(kwargs.get(ATTR_BRIGHTNESS, 255)))
            await self._client.async_set_brightness(self._id, brightness_pct)
            self._brightness_pct = brightness_pct
        self._onoff = "on"

    async def async_turn_off(self, **kwargs):
        """Turn the light off."""
        await self._client.async_set_onoff(self._id, "off")
        self._onoff = MODE_OFF

    async def async_set_phase_control(self, value):
        """Change phase control parameter, reverse or forward."""
        await self._client.async_set_phase(value["id"], value["phase"])
        self._phase_control = value["phase"]

    async def async_set_keypad_lock(self, value):
        """Lock, unlock or partially lock device's keypad,
        lock = locked, unlock = unlocked, partiallyLocked = partial lock."""
        await self._client.async_set_keypad_lock(value["id"], value["lock"], False)
        self._keypad = value["lock"]

    async def async_set_timer(self, value):
        """Set device timer, 0 = off, 1 min up to 3 hrs = timer length converted in seconds."""
        await self._client.async_set_timer(value["id"], value[ATTR_TIME])
        self._timer = value[ATTR_TIME]

    async def async_set_led_indicator(self, value):
        """Set led indicator color, 
        base on RGB red, green, blue color (0-255) for on and off state."""
        color = color_to_rgb(value["color"])
        await self._client.async_set_led_indicator(value["id"], value["state"], color)
        if value["state"] == 0:
            self._led_off_color = color
        else:
            self._led_on_color = color

    async def async_set_led_on_intensity(self, value):
        """Set led indicator on intensity from 0 to 100."""
        await self._client.async_set_led_on_intensity(value["id"], value["led_on"])
        self._led_on_intensity = value["led_on"]

    async def async_set_led_off_intensity(self, value):
        """Set led indicator off intensity from 0 to 100."""
        await self._client.async_set_led_off_intensity(value["id"], value["led_off"])
        self._led_off_intensity = value["led_off"]

    async def async_set_light_min_intensity(self, value):
        """Set dimmer light minimum intensity from 1 to 3000."""
        await self._client.async_set_light_min_intensity(value["id"], value["intensity"])
        self._intensity_min = value["intensity"]

    async def async_set_wattage(self, value):
        """Set light device watt load."""
        await self._client.async_set_wattage(value["id"], value["watt"])
        self._wattage = value["watt"]

    async def async_set_activation(self, value):
        """Activate (True) or deactivate (False) Neviweb polling for a missing device."""
        self._active = value["active"]

    async def async_set_key_double_up(self, value):
        """Change key double up action."""
        await self._client.async_set_double_up(value["id"], value["double"])
        self._double_up = value["double"]

    async def async_do_stat(self, start):
        """Get device energy statistic."""
        if start - self._energy_stat_time > self._stat_interval and self._energy_stat_time != 0:
            today = date.today()
            current_month = today.month
            current_day = today.day
            device_monthly_stats = await self._client.async_get_device_monthly_stats(self._id, False)
            # _LOGGER.debug("%s device_monthly_stats = %s", self._name, device_monthly_stats)
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
            device_daily_stats = await self._client.async_get_device_daily_stats(self._id, False)
            # _LOGGER.debug("%s device_daily_stats = %s", self._name, device_daily_stats)
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
            device_hourly_stats = await self._client.async_get_device_hourly_stats(self._id, False)
            # _LOGGER.debug("%s device_hourly_stats = %s", self._name, device_hourly_stats)
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
                await async_add_data(
                    self._conf_dir,
                    self._device_dict,
                    self._id,
                    self._total_kwh_count,
                    self._marker,
                )
                self.async_write_ha_state()
                self._mark = self._marker
            else:
                if self._marker != self._mark:
                    self._total_kwh_count += round(self._hour_kwh, 3)
                    await save_data(self._id, self._device_dict, self._total_kwh_count, self._marker, self._conf_dir)
                    self._mark = self._marker
            _LOGGER.debug("Device dict updated: %s", self._device_dict)
            self._energy_stat_time = time.time()
        if self._energy_stat_time == 0:
            self._energy_stat_time = start

    async def async_log_error(self, error_data):
        """Send error message to LOG."""
        if error_data == "USRSESSEXP":
            _LOGGER.warning("Session expired... Reconnecting...")
            if self._notify == "notification" or self._notify == "both":
                msg = translate_error(self.hass, "usr_session")
                await async_notify_once_or_update(
                    self.hass,
                    msg,
                    title=f"Neviweb130 integration {VERSION}",
                    notification_id="neviweb130_reconnect",
                )
            await self._client.async_reconnect()
        elif error_data == "ACCDAYREQMAX":
            _LOGGER.warning("Maximum daily request reached... Reduce polling frequency")
        elif error_data == "TimeoutError":
            _LOGGER.warning("Timeout error detected... Retry later")
        elif error_data == "MAINTENANCE":
            msg = translate_error(self.hass, "maintenance")
            await async_notify_critical(
                self.hass,
                msg,
                title=f"Neviweb130 integration {VERSION}",
                notification_id="neviweb130_access_error",
            )
            await self._client.async_reconnect()
        elif error_data == "ACCSESSEXC":
            msg = translate_error(self.hass, "access_limit")
            _LOGGER.warning(msg)
            await async_notify_once_or_update(
                self.hass,
                msg,
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
                "Device Communication Timeout for %s (id: %s)... The device "
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
                msg = translate_error(self.hass, "update_stopped", name=self._name, id=self._id, sku=self._sku)
                await async_notify_once_or_update(
                    self.hass,
                    msg,
                    title=f"Neviweb130 integration {VERSION}",
                    notification_id="neviweb130_device_error",
                )
            self._active = False
            self._snooze = time.time()
        else:
            _LOGGER.warning(
                "Unknown error for %s (id: %s): %s...(SKU: %s) Report to maintainer",
                self._name,
                self._id,
                error_data,
                self._sku,
            )


class Neviweb130Dimmer(Neviweb130Light):
    """Implementation of a neviweb dimmer, DM2500ZB, DM2500ZB-G2."""

    @override
    async def async_update(self) -> None:
        if self._active:
            """Get the latest data from neviweb and update the state."""
            WATT_ATTRIBUTE = [ATTR_LIGHT_WATTAGE, ATTR_ERROR_CODE_SET1]
            start = time.time()
            device_data = await self._client.async_get_device_attributes(self._id, UPDATE_ATTRIBUTES + WATT_ATTRIBUTE)
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
                            msg = translate_error(
                                self.hass,
                                "error_code",
                                code=str(device_data[ATTR_ERROR_CODE_SET1]["raw"]),
                                message="",
                                name=self._name,
                                id=self._id,
                                sku=self._sku
                            )
                            await async_notify_critical(
                                self.hass,
                                msg,
                                title=f"Neviweb130 integration {VERSION}",
                                notification_id="neviweb130_error_code",
                            )
                    self._keypad = lock_to_ha(device_data[ATTR_KEYPAD])
                    self._timer = neviweb_to_ha_timer(device_data[ATTR_TIMER])
                    self._rssi = device_data[ATTR_RSSI]
                    self._led_on_color = (
                        str(device_data[ATTR_LED_ON_COLOR]["red"])
                        + ","
                        + str(device_data[ATTR_LED_ON_COLOR]["green"])
                        + ","
                        + str(device_data[ATTR_LED_ON_COLOR]["blue"])
                    )
                    self._led_off_color = (
                        str(device_data[ATTR_LED_OFF_COLOR]["red"])
                        + ","
                        + str(device_data[ATTR_LED_OFF_COLOR]["green"])
                        + ","
                        + str(device_data[ATTR_LED_OFF_COLOR]["blue"])
                    )
                    self._led_on_intensity = device_data[ATTR_LED_ON_INTENSITY]
                    self._led_off_intensity = device_data[ATTR_LED_OFF_INTENSITY]
                    self.async_write_ha_state()
                else:
                    _LOGGER.warning(
                        "Error reading device %s: (%s)",
                        self._name,
                        device_data,
                    )
            else:
                await self.async_log_error(device_data["error"]["code"])
            await self.async_do_stat(start)
        else:
            if time.time() - self._snooze > SNOOZE_TIME:
                self._active = True
                if self._notify == "notification" or self._notify == "both":
                    msg = translate_error(self.hass, "update_restarted", name=self._name, sku=self._sku)
                    await async_notify_once_or_update(
                        self.hass,
                        msg,
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
                ATTR_BRIGHTNESS_PCT: self._brightness_pct,
                "minimum_intensity": self._intensity_min,
                "error_code": self._error_code,
                "wattage": self._wattage,
                "wattage_status": self._wattage_status,
                "onOff": self._onoff,
                "keypad": self._keypad,
                "timer": self._timer,
                "led_on_color": self._led_on_color,
                "led_off_color": self._led_off_color,
                "led_on_intensity": self._led_on_intensity,
                "led_off_intensity": self._led_off_intensity,
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
                "id": self._id,
            }
        )
        return data


class Neviweb130NewDimmer(Neviweb130Light):
    """Implementation of a neviweb new dimmer DM2550ZB, DM2550ZB-G2."""

    @override
    async def async_update(self) -> None:
        if self._active:
            """Get the latest data from neviweb and update the state."""
            WATT_ATTRIBUTE = [
                ATTR_PHASE_CONTROL,
                ATTR_KEY_DOUBLE_UP,
                ATTR_WATTAGE_INSTANT,
                ATTR_ERROR_CODE_SET1,
            ]
            start = time.time()
            device_data = await self._client.async_get_device_attributes(self._id, UPDATE_ATTRIBUTES + WATT_ATTRIBUTE)
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
                    self._keypad = lock_to_ha(device_data[ATTR_KEYPAD])
                    self._wattage = device_data[ATTR_WATTAGE_INSTANT]
                    self._timer = neviweb_to_ha_timer(device_data[ATTR_TIMER])
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
                            await self.async_notify_critical(
                                self.hass,
                                msg,
                                title=f"Neviweb130 integration {VERSION}",
                                notification_id="neviweb130_error_code",
                            )
                    self._rssi = device_data[ATTR_RSSI]
                    self._led_on_color = (
                        str(device_data[ATTR_LED_ON_COLOR]["red"])
                        + ","
                        + str(device_data[ATTR_LED_ON_COLOR]["green"])
                        + ","
                        + str(device_data[ATTR_LED_ON_COLOR]["blue"])
                    )
                    self._led_off_color = (
                        str(device_data[ATTR_LED_OFF_COLOR]["red"])
                        + ","
                        + str(device_data[ATTR_LED_OFF_COLOR]["green"])
                        + ","
                        + str(device_data[ATTR_LED_OFF_COLOR]["blue"])
                    )
                    self._led_on_intensity = device_data[ATTR_LED_ON_INTENSITY]
                    self._led_off_intensity = device_data[ATTR_LED_OFF_INTENSITY]
                    self.async_write_ha_state()
                else:
                    _LOGGER.warning(
                        "Error reading device %s: (%s)",
                        self._name,
                        device_data,
                    )
            else:
                await self.async_log_error(device_data["error"]["code"])
            await self.async_do_stat(start)
        else:
            if time.time() - self._snooze > SNOOZE_TIME:
                self._active = True
                if self._notify == "notification" or self._notify == "both":
                    msg = translate_error(self.hass, "update_restarted", name=self._name, sku=self._sku)
                    await async_notify_once_or_update(
                        self.hass,
                        msg,
                        title=f"Neviweb130 integration {VERSION}",
                        notification_id=f"neviweb130_update_restarted",
                    )

    @property
    def phase_control(self):
        """Set dimmer DM2550ZB, DM2550ZB-G2 phace, reverse, forward."""
        return self._phase_control

    @property
    @override
    def extra_state_attributes(self)  -> Mapping[str, Any]:
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
                "keypad": self._keypad,
                "timer": self._timer,
                "led_on_color": self._led_on_color,
                "led_off_color": self._led_off_color,
                "led_on_intensity": self._led_on_intensity,
                "led_off_intensity": self._led_off_intensity,
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
                "id": self._id,
            }
        )
        return data
