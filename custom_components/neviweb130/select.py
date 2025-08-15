"""
Support for Neviweb attributes select for devices connected via GT130 and wifi devices.
"""

from __future__ import annotations

import logging

from dataclasses import dataclass
from typing import Callable, Any, Optional, Final

from homeassistant.components.select import (
    SelectEntity,
    SelectEntityDescription,
)
from homeassistant.components.select.const import SelectDeviceClass
from homeassistant.const import ATTR_FRIENDLY_NAME
from homeassistant.core import HomeAssistant
from homeassistant.config_entries import ConfigEntry
from homeassistant.helpers import device_registry as dr
from homeassistant.helpers.update_coordinator import (
    CoordinatorEntity,
    DataUpdateCoordinator,
)
from homeassistant.helpers.entity_platform import AddEntitiesCallback

from .attributes import (
    ALL_MODEL,
    CLIMATE_MODEL,
    LIGHT_MODEL,
    SWITCH_MODEL,
    VALVE_MODEL,
)
from .const import (
    DOMAIN,
    ATTR_BACKLIGHT,
    ATTR_KEYPAD,
    ATTR_LED_ON_COLOR,
    ATTR_LED_OFF_COLOR,
)

from .helpers import debug_coordinator
from .light import color_to_rgb, rgb_to_color

DEFAULT_NAME = 'neviweb130 select'
DEFAULT_NAME_2 = 'neviweb130 select 2'
DEFAULT_NAME_3 = 'neviweb130 select 3'

_LOGGER = logging.getLogger(__name__)

@dataclass(frozen=True)
class Neviweb130SelectEntityDescription(SelectEntityDescription):
    """Class describing Neviweb130 select entities."""

    data_key: Optional[str] = None

SELECT_TYPES: Final[tuple[Neviweb130SelectEntityDescription, ...]] = (
    Neviweb130SelectEntityDescription(
        key=ATTR_KEYPAD,
        icon="mdi:dialpad",
        translation_key="keypad_lock",
        options_list=["locked", "unlocked", "partiallyLocked"],
    ),
    Neviweb130SelectEntityDescription(
        key=ATTR_LED_ON_COLOR,
        icon="mdi:palette",
        translation_key="led_on_color",
        options_list=["lime", "amber", "fushia", "perle", "blue", "red", "orange", "green"],
    ),
    Neviweb130SelectEntityDescription(
        key=ATTR_LED_OFF_COLOR,
        icon="mdi:palette-outline",
        translation_key="led_off_color",
        options_list=["lime", "amber", "fushia", "perle", "blue", "red", "orange", "green"],
    ),
    Neviweb130SelectEntityDescription(
        key=ATTR_BACKLIGHT,
        icon="mdi:fullscreen",
        translation_key="backlight",
        options_list=["auto", "on", "bedroom"],
    ),
)

def get_attributes_for_model(model):
    if model in CLIMATE_MODEL:
        return [ATTR_KEYPAD, ATTR_BACKLIGHT]
    elif model in LIGHT_MODEL:
        return [ATTR_KEYPAD, ATTR_LED_ON_COLOR, ATTR_LED_OFF_COLOR]
    elif model in SWITCH_MODEL:
        return [ATTR_KEYPAD]
    elif model in VALVE_MODEL:
        return [ATTR_KEYPAD]
    return []

def create_attribute_selects(hass, entry, data, coordinator, device_registry):
    entities = []
    client = data['neviweb130_client']

    _LOGGER.debug("Keys dans coordinator.data : %s", list(coordinator.data.keys()))

    for gateway_data, default_name in [
        (client.gateway_data, DEFAULT_NAME),
        (client.gateway_data2, DEFAULT_NAME_2),
        (client.gateway_data3, DEFAULT_NAME_3)
    ]:
        if not gateway_data or gateway_data == "_":
            continue

        for device_info in gateway_data:
            model = device_info["signature"]["model"]
            if model not in ALL_MODEL:
                continue

            device_id = str(device_info["id"])
            if device_id not in coordinator.data:
                _LOGGER.warning("Device %s pas encore dans coordinator.data", device_id)

            device_name = f"{default_name} {device_info['name']}"
            device_entry = device_registry.async_get_or_create(
                config_entry_id=entry.entry_id,
                identifiers={(DOMAIN, device_id)},
                manufacturer="claudegel",
                name=device_name,
                model=model,
                sw_version="{major}.{middle}.{minor}".format(
                    **device_info["signature"]["softVersion"]
                ),
            )

            attributes_name = get_attributes_for_model(model)
            for attribute in attributes_name:
                for desc in SELECT_TYPES:
                    if desc.key == attribute:
                        entities.append(
                            Neviweb130DeviceAttributeNumber(
                                client=client,
                                device=device_info,
                                device_name=device_name,
                                attribute=attribute,
                                device_id=device_id,
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

    if 'neviweb130_client' not in data:
        _LOGGER.error("Neviweb130 client initialization failed.")
        return

    coordinator = data["coordinator"]

    device_type = None
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
        ATTR_KEYPAD: lambda self, option: self._client.async_set_keypad_lock(self._id, option, self.is_wifi),
        ATTR_LED_ON_COLOR: lambda self, option: self._client.async_set_led_indicator(self._id, 1, color_to_rgb(option)),
        ATTR_LED_OFF_COLOR: lambda self, option: self._client.async_set_led_indicator(self._id, 0, color_to_rgb(option)),
        ATTR_BACKLIGHT: lambda self, option: self._client.async_set_backlight(self._id, option, self.is_wifi),
        # ...
    }

    def __init__(
        self,
        client,
        device: dict,
        device_name: str,
        attribute: str,
        device_id: str,
        attr_info: dict,
        coordinator,
        entity_description: Neviweb130SelectEntityDescription,
    ):
        """Initialize the select entity."""
        super().__init__(coordinator)
        self._client = client
        self._device = device
        self._id = str(device.get('id'))
        self._attribute = attribute
        self._attr_unique_id = f"{self._id}_{attribute}"
        self._attr_device_info = attr_info
        self.entity_description = entity_description
        self._attr_icon = entity_description.icon
        self._attr_translation_key = entity_description.translation_key
        self._attr_options = entity_description.options_list

    @property
    def unique_id(self):
        """Return a unique ID."""
        return self._attr_unique_id

    @property
    def is_wifi(self):
        """Return True if device is a wifi device"""
        device_obj = self.coordinator.data.get(self._id)
        return device_obj.get("is_wifi", False) if device_obj else False

    @property
    def current_option(self):
        """Return the current selected option."""
        device_obj = self.coordinator.data.get(self._id)
        if device_obj and self._attribute in device_obj:
            return device_obj[self._attribute]
        else:
            _LOGGER.warning(
                "AttributeSelect: %s attribute %s not found for device: %s.",
                self._attr_unique_id, self._attribute, self._id
            )
            return None

    @property
    def extra_state_attributes(self):
        """Return the state attributes of the select."""
        return {"device_id": self._attr_unique_id}

    async def async_select_option(self, option: str) -> None:
        """Change the selected select option."""
        handler = self._ATTRIBUTE_METHODS.get(self._attribute)
        if handler:
            await handler(self, option)
        else:
            _LOGGER.warning("No handler for select attribute: %s", self._attribute)
        self._device[self._attribute] = option
        self.async_write_ha_state()
