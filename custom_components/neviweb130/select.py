"""
Support for Neviweb attributes select for devices connected via GT130 and Wi-Fi devices.
"""

from __future__ import annotations

import logging
from dataclasses import dataclass
from typing import Final

from homeassistant.components.select import SelectEntity, SelectEntityDescription
from homeassistant.config_entries import ConfigEntry
from homeassistant.const import EntityCategory
from homeassistant.core import HomeAssistant
from homeassistant.helpers import device_registry as dr
from homeassistant.helpers.device_registry import DeviceInfo
from homeassistant.helpers.entity_platform import AddEntitiesCallback
from homeassistant.helpers.update_coordinator import CoordinatorEntity

from .const import ALL_MODEL, DOMAIN, MODEL_ATTRIBUTES
from .coordinator import Neviweb130Client, Neviweb130Coordinator
from .schema import (
    BACKLIGHT_LIST,
    COLOR_LIST,
    DISPLAY_LIST,
    FLOOR_MODE,
    HC_DISPLAY_LIST,
    LANGUAGE_LIST,
    LOCK_LIST,
    LV_AUX_CYCLE,
    LV_CYCLE,
    OCCUPANCY_LIST,
    ON_OFF,
    STD_CYCLE,
    TANK_VALUE,
    TEMP_LIST,
    TIME_LIST,
    WIFI_AUX_CYCLE,
    WIFI_CYCLE,
)

DEFAULT_NAME = f"{DOMAIN} select"
DEFAULT_NAME_2 = f"{DOMAIN} select 2"
DEFAULT_NAME_3 = f"{DOMAIN} select 3"

_LOGGER = logging.getLogger(__name__)


@dataclass(frozen=True)
class Neviweb130SelectEntityDescription(SelectEntityDescription):
    """Class describing Neviweb130 select entities."""

    data_key: str | None = None


SELECT_TYPES: Final[tuple[Neviweb130SelectEntityDescription, ...]] = (
    #  Common attributes
    Neviweb130SelectEntityDescription(
        key="keypad",
        icon="mdi:dialpad",
        translation_key="keypad_lock",
        options=LOCK_LIST,
    ),
    #  Light attributes
    Neviweb130SelectEntityDescription(
        key="led_on_color",
        icon="mdi:palette",
        translation_key="led_on_color",
        options=COLOR_LIST,
    ),
    Neviweb130SelectEntityDescription(
        key="led_off_color",
        icon="mdi:palette-outline",
        translation_key="led_off_color",
        options=COLOR_LIST,
    ),
    #  Thermostat attributes
    Neviweb130SelectEntityDescription(
        key="backlight",
        icon="mdi:fullscreen",
        translation_key="backlight",
        options=BACKLIGHT_LIST,
    ),
    Neviweb130SelectEntityDescription(
        key="keypad_status",
        icon="mdi:dialpad",
        translation_key="keypad_lock",
        options=LOCK_LIST,
    ),
    Neviweb130SelectEntityDescription(
        key="language",
        icon="mdi:projector-screen-outline",
        translation_key="language",
        options=LANGUAGE_LIST,
    ),
    Neviweb130SelectEntityDescription(
        key="occupancy_mode",
        icon="mdi:home",
        translation_key="occupancy_mode",
        options=OCCUPANCY_LIST,
    ),
    Neviweb130SelectEntityDescription(
        key="time_format",
        icon="mdi:camera-timer",
        translation_key="time_format",
        options=TIME_LIST,
    ),
    Neviweb130SelectEntityDescription(
        key="temp_format",
        icon="mdi:thermometer",
        translation_key="temp_format",
        options=TEMP_LIST,
    ),
    Neviweb130SelectEntityDescription(
        key="second_display",
        icon="mdi:fullscreen",
        translation_key="second_display",
        options=DISPLAY_LIST,
    ),
    Neviweb130SelectEntityDescription(
        key="hc_second_display",
        icon="mdi:fullscreen",
        translation_key="second_display",
        options=HC_DISPLAY_LIST,
    ),
    Neviweb130SelectEntityDescription(
        key="cycle_length",
        icon="mdi:reload",
        translation_key="cycle_length",
        options=STD_CYCLE,
    ),
    Neviweb130SelectEntityDescription(
        key="aux_cycle_length",
        icon="mdi:reload",
        translation_key="aux_cycle_length",
        options=LV_AUX_CYCLE,
    ),
    Neviweb130SelectEntityDescription(
        key="lv_cycle_length",
        icon="mdi:reload",
        translation_key="cycle_length",
        options=LV_CYCLE,
    ),
    Neviweb130SelectEntityDescription(
        key="wifi_cycle_length",
        icon="mdi:reload",
        translation_key="aux_cycle_length",
        options=WIFI_CYCLE,
    ),
    Neviweb130SelectEntityDescription(
        key="wifi_aux_cycle_length",
        icon="mdi:reload",
        translation_key="aux_cycle_length",
        options=WIFI_AUX_CYCLE,
    ),
    Neviweb130SelectEntityDescription(
        key="sensor_mode",
        icon="mdi:home-modern",
        translation_key="sensor_mode",
        options=FLOOR_MODE,
    ),
    Neviweb130SelectEntityDescription(
        key="early_start",
        icon="mdi:selection-off",
        translation_key="early_start",
        options=ON_OFF,
    ),
    #  switch attributes
    Neviweb130SelectEntityDescription(
        key="tank_size",
        icon="mdi:cup-water",
        translation_key="tank_size",
        options=TANK_VALUE,
    ),
)


def get_attributes_for_model(model):
    return MODEL_ATTRIBUTES.get(model, {}).get("select", [])


def create_attribute_selects(hass, entry, data, coordinator, device_registry):
    entities = []
    client = data["neviweb130_client"]

    _LOGGER.debug("Keys in coordinator.data : %s", list(coordinator.data.keys()))

    for gateway_data, default_name in [
        (client.gateway_data, DEFAULT_NAME),
        (client.gateway_data2, DEFAULT_NAME_2),
        (client.gateway_data3, DEFAULT_NAME_3),
    ]:
        if not gateway_data or gateway_data == "_":
            continue

        for device_info in gateway_data:
            model = device_info["signature"]["model"]
            if model not in ALL_MODEL:
                continue

            device_id = str(device_info["id"])
            if device_id not in coordinator.data:
                _LOGGER.warning("Device %s not yet in coordinator.data", device_id)

            device_name = f"{default_name} {device_info['name']}"
            device_entry = device_registry.async_get_or_create(
                config_entry_id=entry.entry_id,
                identifiers={(DOMAIN, device_id)},
                manufacturer="claudegel",
                name=device_name,
                model=model,
                sw_version="{major}.{middle}.{minor}".format(**device_info["signature"]["softVersion"]),
            )

            attributes_name = get_attributes_for_model(model)
            for attribute in attributes_name:
                for desc in SELECT_TYPES:
                    if desc.key == attribute:
                        entities.append(
                            Neviweb130DeviceAttributeSelect(
                                client=client,
                                device=device_info,
                                attribute=attribute,
                                attr_info={
                                    "identifiers": device_entry.identifiers,
                                    "name": device_entry.name,
                                    "manufacturer": device_entry.manufacturer,
                                    "model": device_entry.model,
                                },
                                coordinator=coordinator,
                                entity_description=desc,
                            )
                        )

    return entities


async def async_setup_entry(
    hass: HomeAssistant,
    entry: ConfigEntry,
    async_add_entities: AddEntitiesCallback,
    discovery_info=None,
) -> None:
    """Set up the Neviweb select entities."""
    data = hass.data[DOMAIN][entry.entry_id]

    if "neviweb130_client" not in data:
        _LOGGER.error("Neviweb130 client initialization failed.")
        return

    coordinator = data["coordinator"]

    device_registry = dr.async_get(hass)

    entities = create_attribute_selects(hass, entry, data, coordinator, device_registry)

    async_add_entities(entities)
    hass.async_create_task(coordinator.async_request_refresh())


class Neviweb130DeviceAttributeSelect(CoordinatorEntity[Neviweb130Coordinator], SelectEntity):
    """Representation of a specific Neviweb130 select entity."""

    _attr_has_entity_name = True
    _attr_should_poll = True
    _attr_entity_category = EntityCategory.CONFIG

    _ATTRIBUTE_METHODS = {
        "aux_cycle_length": lambda self, option: self._client.async_set_aux_cycle_output(self._id, option),
        "backlight": lambda self, option: self._client.async_set_backlight(self._id, option, self.is_wifi),
        "cycle_length": lambda self, option: self._client.async_set_cycle_output(self._id, option),
        "early_start": lambda self, option: self._client.async_set_early_start(self._id, option),
        "hc_second_display": lambda self, option: self._client.async_set_hc_display(self._id, option),
        "keypad": lambda self, option: self._client.async_set_keypad_lock(self._id, option, self.is_wifi),
        "keypad_status": lambda self, option: self._client.async_set_keypad_lock(self._id, option, self.is_wifi),
        "language": lambda self, option: self._client.async_set_language(self._id, option),
        "led_off_color": lambda self, option: self._client.async_set_led_indicator(self._id, 0, option),
        "led_on_color": lambda self, option: self._client.async_set_led_indicator(self._id, 1, option),
        "lv_cycle_length": lambda self, option: self._client.async_set_cycle_output(self._id, option),
        "occupancy_mode": lambda self, option: self._client.async_post_neviweb_status(self.location, option),
        "second_display": lambda self, option: self._client.async_set_second_display(self._id, option),
        "sensor_mode": lambda self, option: self._client.async_set_air_floor_mode(self._id, option),
        "temp_format": lambda self, option: self._client.async_set_temperature_format(self._id, option),
        "time_format": lambda self, option: self._client.async_set_time_format(self._id, option),
        "tank_size": lambda self, option: self._client.async_set_tank_size(self._id, option),
        "wifi_aux_cycle_length": lambda self, option: self._client.async_set_aux_cycle_output(self._id, option),
        "wifi_cycle_length": lambda self, option: self._client.async_set_aux_cycle_output(self._id, option),
        # ...
    }

    def __init__(
        self,
        client: Neviweb130Client,
        device: dict,
        attribute: str,
        attr_info: DeviceInfo,
        coordinator,
        entity_description: Neviweb130SelectEntityDescription,
    ):
        """Initialize the select entity."""
        super().__init__(coordinator)
        self._client = client
        self._device = device
        self._id = str(device.get("id"))
        self._attribute = attribute
        self._attr_unique_id = f"{self._id}_{attribute}"
        self._attr_device_info = attr_info
        self._current_option: str | None = None
        self.entity_description = entity_description
        self._attr_icon = entity_description.icon
        self._attr_translation_key = entity_description.translation_key
        if entity_description.options is not None:
            self._attr_options = entity_description.options

    @property
    def unique_id(self):
        """Return a unique ID."""
        return self._attr_unique_id

    @property
    def is_wifi(self):
        """Return True if device is a Wi-Fi device"""
        device_obj = self.coordinator.data.get(self._id)
        return device_obj.get("is_wifi", False) if device_obj else False

    @property
    def location(self) -> str | None:
        """Return location id"""
        device_obj = self.coordinator.data.get(self._id)
        loc = device_obj.get("location", None) if device_obj else None
        return str(loc) if loc is not None else none

    @property
    def is_HC(self):
        """Return True if device is a HC device"""
        device_obj = self.coordinator.data.get(self._id)
        return device_obj.get("is_HC", False) if device_obj else False

    @property
    def current_option(self):
        """Return the current selected option."""
        if self.coordinator.data is None:
            return None
        device_obj = self.coordinator.data.get(self._id)
        if device_obj and self._attribute in device_obj:
            return device_obj[self._attribute]
        else:
            _LOGGER.warning(
                "AttributeSelect: %s attribute %s not found for device: %s.",
                self._attr_unique_id,
                self._attribute,
                self._id,
            )
            return None

    @property
    def extra_state_attributes(self):
        """Return the state attributes of the select."""
        return {"device_id": self._attr_unique_id}

    async def async_select_option(self, option: str) -> None:
        """Change the selected select option if Neviweb accepts it."""
        handler = self._ATTRIBUTE_METHODS.get(self._attribute)
        if handler:
            success = await handler(self, option)
            if success:
                self._current_option = option
                self._device[self._attribute] = option
                self.async_write_ha_state()
                await self.coordinator.async_request_refresh()
            else:
                _LOGGER.warning(
                    "Failed to update select attribute '%s' with option '%s'",
                    self._attribute,
                    option,
                )
        else:
            _LOGGER.warning("No handler for select attribute: %s", self._attribute)
