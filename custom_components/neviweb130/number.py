"""
Support for Neviweb numbers connected via GT130 ZigBee.
"""

from __future__ import annotations

import logging
from dataclasses import dataclass

from homeassistant.components.number import (
    NumberEntity,
    NumberEntityDescription,
)
from homeassistant.components.number.const import NumberDeviceClass
from homeassistant.const import ATTR_FRIENDLY_NAME
from homeassistant.core import HomeAssistant
from homeassistant.config_entries import ConfigEntry
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
    VALVE_MODEL,
    SWITCH_MODEL,
)
DEFAULT_NAME = 'neviweb130 number'
DEFAULT_NAME_2 = 'neviweb130 number 2'
DEFAULT_NAME_3 = 'neviweb130 number 3'

_LOGGER = logging.getLogger(__name__)

ATTR_INTENSITY_KEY = "intensity"
ATTR_INTENSITY_MIN_KEY = "intensity_min"


@dataclass(frozen=True, kw_only=True)
class Neviweb130NumberEntityDescription(NumberEntityDescription):
    """Class describing Neviweb130 Button entities."""

    data_key: str

NUMBER_DESCRIPTIONS: Final[tuple[NumberEntityDescription, ...]] = (
    NumberEntityDescription(
        key=ATTR_INTENSITY_KEY,
        name="Intensity",
        icon="mdi:light_bulb",
        native_min_value=50,
        native_max_value=3000,
        native_step=1,
        native_unit_of_measurement=PERCENTAGE,
    ),
    NumberEntityDescription(
        key=ATTR_INTENSITY_MIN_KEY,
        name="Intensity_min",
        icon="mdi:light_bulb",
        native_min_value=10,
        native_max_value=100,
        native_step=1,
        native_unit_of_measurement=PERCENTAGE,
    ),
)


async def async_setup_entry(
    hass: HomeAssistant,
    entry: ConfigEntry,
    async_add_entities: AddEntitiesCallback,
    discovery_info=None,
) -> None:
    """Set up the Neviweb number."""
    data = hass.data[DOMAIN][entry.entry_id]

    if 'neviweb130_client' not in data:
        _LOGGER.error("Neviweb130 client initialization failed.")
        return

    entities = []
    for gateway_data, default_name in [
        (data['neviweb130_client'].gateway_data, DEFAULT_NAME),
        (data['neviweb130_client'].gateway_data2, DEFAULT_NAME_2),
        (data['neviweb130_client'].gateway_data3, DEFAULT_NAME_3)
    ]:
        if gateway_data is not None and gateway_data != "_":
            for device_info in gateway_data:
                if "signature" in device_info and "model" in device_info["signature"]:
                    model = device_info["signature"]["model"]
                    device_id = str(device_info["id"])
                    # Add attribute number for each device type
                    if model in ALL_MODEL:
                        device_name = f'{default_name} {device_info["name"]}'
                        _LOGGER.debug("device found = %s", device_name)
                        if model in CLIMAT_MODEL:
                            attributes_name = []
                        elif model in LIGHT_MODEL:
                            attributes_name = []
                        elif model in SWITCH_MODEL:
                            attributes_name = []
                        elif model in VALVE_MODEL:
                            attributes_name = []

                        for attribute in attributes_name:
                            _LOGGER.debug(f"Adding attributes number for : {device_name} {attribute}")
                            entities.append(Neviweb130DeviceAttributeNumber(data['coordinator'], device_info, device_name, attribute))

    async_add_entities(entities, True)


class Neviweb130DeviceAttributeNumber(CoordinatorEntity, NumberEntity):
    """Representation of a specific Neviweb130 number."""

    entity_description: Neviweb130NumberEntityDescription

    def __init__(self, coordinator: DataUpdateCoordinator, device: dict, device_name: str, attribute: str):
        """Initialize the number."""
        super().__init__(coordinator)
        self._client = client
        self._device = device
        self._device_name = device_name
        self._master_device_id = device["id"]
        self._attribute = attribute
        self._device_type =   # wifi or zigbee
        self._number_name = f"{device_name} {attribute.replace('_', ' ').capitalize()}"
        self._unique_id = f"{device.get('id')}_{attribute}"
        self._number_friendly_name = f"{self._device.get("friendly_name")} {attribute.replace('_', ' ').capitalize()}"

    @property
    def name(self):
        """Return the name of the sensor."""
        return self._number_name

    @property
    def unique_id(self):
        """Return a unique ID."""
        return self._unique_id

    @property
    def value(self) -> float:
        """Return the current value."""
        return self._device.get(self._attribute)

    @property
    def extra_state_attributes(self):
        """Return the state attributes of the number."""
        return {
            "device_name": self._number_name,
            ATTR_FRIENDLY_NAME: self._number_friendly_name,
            "device_id": self._unique_id,
        }

    @property
    def min_value(self) -> float:
        """Return the minimum value."""
        return 5  # Adjust as needed

    @property
    def max_value(self) -> float:
        """Return the maximum value."""
        return 30  # Adjust as needed

    @property
    def step(self) -> float:
        """Return the step."""
        return 1  # Adjust as needed

    async def async_set_value(self, value: float) -> None:
        """Change the selected value."""
        if self._attribute == ATTR_LED_ON_INTENSITY:
            state = 1
            await self._client.async_set_led_indicator(self._master_device_id, state, value, color)
            self._device[self._attribute] = value
        elif self._attribute == ATTR_LED_OFF_INTENSITY:
            state = 0
            await self._client.async_set_led_indicator(self._master_device_id, state, value, color)
            self._device[self._attribute] = value
        elif self._attribute == ATTR_INTENSITY_MIN:
            await self._client.async_set_device_attributes(self._master_device_id, state, value)
            self._device[self._attribute] = value
        elif self._attribute == ATTR_INTENSITY:
            await self._client.async_set_device_attributes(self._master_device_id, state, value)
            self._device[self._attribute] = value
        self.async_write_ha_state()

    async def async_update(self):
        """Fetch new state data for the select entity."""
        await self.coordinator.async_request_refresh()
        self._device = self.coordinator.data
        self.async_write_ha_state()
