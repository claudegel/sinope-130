"""
Support for Neviweb attributes numbers for devices connected via GT130 and wifi devices.
"""

from __future__ import annotations

import logging

from dataclasses import dataclass
from typing import Callable, Any, Optional, Final
from .helpers import debug_coordinator

from homeassistant.components.number import (
    NumberEntity,
    NumberEntityDescription,
)
from homeassistant.components.number.const import NumberDeviceClass
from homeassistant.const import ATTR_FRIENDLY_NAME, PERCENTAGE
from homeassistant.core import HomeAssistant
from homeassistant.config_entries import ConfigEntry
from homeassistant.helpers import device_registry as dr
from homeassistant.helpers.update_coordinator import (
    CoordinatorEntity,
    DataUpdateCoordinator,
)
from homeassistant.helpers.entity_platform import AddEntitiesCallback

from .const import (
    DOMAIN,
    ATTR_LED_ON_INTENSITY,
    ATTR_LED_OFF_INTENSITY,
    ATTR_INTENSITY,
    ATTR_INTENSITY_MIN,
)
from .attributes import (
    ALL_MODEL,
    CLIMATE_MODEL,
    LIGHT_MODEL,
    SWITCH_MODEL,
    VALVE_MODEL,
)

DEFAULT_NAME = 'neviweb130 number'
DEFAULT_NAME_2 = 'neviweb130 number 2'
DEFAULT_NAME_3 = 'neviweb130 number 3'

_LOGGER = logging.getLogger(__name__)

@dataclass(frozen=True)
class Neviweb130NumberEntityDescription(NumberEntityDescription):
    """Class describing Neviweb130 number entities."""

    data_key: Optional[str] = None

NUMBER_TYPES: Final[tuple[Neviweb130NumberEntityDescription, ...]] = (
    Neviweb130NumberEntityDescription(
        key="intensity",
        icon="mdi:light_bulb",
        mode: NumberMode.SLIDER
        native_min_value=0,
        native_max_value=100,
        native_step=1,
        translation_key="intensity",
        native_unit_of_measurement=PERCENTAGE,
    ),
    Neviweb130NumberEntityDescription(
        key="intensityMin",
        icon="mdi:lightbulb-on-10",
        mode: NumberMode.BOX
        native_min_value=10,
        native_max_value=3000,
        native_step=1,
        translation_key="intensityMin",
        native_unit_of_measurement=PERCENTAGE,
    ),
    Neviweb130NumberEntityDescription(
        key="statusLedOnIntensity",
        icon="mdi:lightbulb-on",
        mode: NumberMode.AUTO
        native_min_value=10,
        native_max_value=100,
        native_step=1,
        translation_key="led_on_intensity",
        native_unit_of_measurement=PERCENTAGE,
    ),
    Neviweb130NumberEntityDescription(
        key="statusLedOffIntensity",
        icon="mdi:lightbulb-off",
        mode: NumberMode.AUTO
        native_min_value=10,
        native_max_value=100,
        native_step=1,
        translation_key="led_off_intensity",
        native_unit_of_measurement=PERCENTAGE,
    ),
)

def get_attributes_for_model(model):
    if model in CLIMATE_MODEL:
        return ["roomSetpointMin", "roomSetpointMax", "heatCoolSetpointMinDelta"]
    elif model in LIGHT_MODEL:
        return ["intensity", "intensityMin", "statusLedOnIntensity", "statusLedOffIntensity"]
    elif model in SWITCH_MODEL:
        return ["powerTimer"]
    elif model in VALVE_MODEL:
        return ["flowMeterAlarmDisableTimer"]
    return []

def create_attribute_numbers(hass, entry, data, coordinator, device_registry):
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
                for desc in NUMBER_TYPES:
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
    """Set up the Neviweb number entities."""
    data = hass.data[DOMAIN][entry.entry_id]

    if 'neviweb130_client' not in data:
        _LOGGER.error("Neviweb130 client initialization failed.")
        return

    coordinator = data["coordinator"]

    device_type = None
    device_registry = dr.async_get(hass)

    entities = create_attribute_numbers(hass, entry, data, coordinator, device_registry)

    async_add_entities(entities)
    hass.async_create_task(coordinator.async_request_refresh())


class Neviweb130DeviceAttributeNumber(CoordinatorEntity[Neviweb130Coordinator], NumberEntity):
    """Representation of a specific Neviweb130 number."""

    _attr_has_entity_name = True
    _attr_should_poll = True
    _attr_entity_category = EntityCategory.CONFIG

    _ATTRIBUTE_METHODS = {
        ATTR_LED_ON_INTENSITY: lambda self, value: self._client.async_set_led_on_intensity(self._id, value),
        ATTR_LED_OFF_INTENSITY: lambda self, value: self._client.async_set_led_off_intensity(self._id, value),
        ATTR_INTENSITY_MIN: lambda self, value: self._client.async_set_light_min_intensity(self._id, value),
        ATTR_INTENSITY: lambda self, value: self._client.async_set_brightness(self._id, value),
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
        entity_description: Neviweb130NumberEntityDescription,
    ):
        """Initialize the number entity."""
        super().__init__(coordinator)
        self._client = client
        self._device = device
        self._id = str(device.get('id'))
        self._attribute = attribute
        self._attr_unique_id = f"{self._id}_{attribute}"
        self._attr_device_info = attr_info
        self.entity_description = entity_description
        self._attr_icon = entity_description.icon
        self._attr_device_class = entity_description.device_class
        self._attr_unit_of_measurement = entity_description.native_unit_of_measurement
        self._attr_translation_key = entity_description.translation_key
        self._attr_native_min_value = entity_description.native_min_value
        self._attr_native_max_value = entity_description.native_max_value
        self._attr_native_step = entity_description.native_step
        self._attr_mode = entity_description.mode

    @property
    def unique_id(self):
        """Return a unique ID."""
        return self._attr_unique_id

    @property
    def native_value(self) -> float | None:
        """Return the current value."""
        device_obj = self.coordinator.data.get(self._id)
        if device_obj and self._attribute in device_obj:
            return device_obj[self._attribute]
        else:
            _LOGGER.warning(
                "AttributeNumber: %s attribute %s not found for device: %s.",
                self._attr_unique_id, self._attribute, self._id
            )
            return None

    @property
    def extra_state_attributes(self):
        """Return the state attributes of the number."""
        return {"device_id": self._attr_unique_id}

    async def async_set_value(self, value: float) -> None:
        """Change the selected number value."""
        handler = self._ATTRIBUTE_METHODS.get(self._attribute)
        if handler:
            await handler(self, value)
        else:
            _LOGGER.warning("No handler for number attribute: %s", self._attribute)
        self._device[self._attribute] = value
        self.async_write_ha_state()
