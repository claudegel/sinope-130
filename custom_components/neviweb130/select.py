"""
Support for Neviweb select entities connected via GT130 ZigBee.
"""

from __future__ import annotations

import logging

from homeassistant.components.select import SelectEntity
from homeassistant.core import HomeAssistant
from homeassistant.config_entries import ConfigEntry
from homeassistant.helpers.update_coordinator import (
    CoordinatorEntity,
    DataUpdateCoordinator,
)
from homeassistant.helpers.entity_platform import AddEntitiesCallback

from .const import (
    DOMAIN,
    ATTR_BACKLIGHT,
    ATTR_KEYPAD,
    ATTR_LED_ON_COLOR,
    ATTR_LED_OFF_COLOR,
)
from .attributes import DEVICE_ATTRIBUTES, ALL_MODEL, CLIMATE_MODEL, LIGHT_MODEL, VALVE_MODEL
from .attributes import (
    ALL_MODEL,
    CLIMATE_MODEL,
    LIGHT_MODEL,
    VALVE_MODEL,
    SWITCH_MODEL,
)
DEFAULT_NAME = 'neviweb130 select'
DEFAULT_NAME_2 = 'neviweb130 select 2'
DEFAULT_NAME_3 = 'neviweb130 select 3'

_LOGGER = logging.getLogger(__name__)

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

    coordinator = data['coordinator']
    client = data['neviweb130_client']

    entities = []
    for gateway_data in [
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
                            attributes_name = 
                        elif model in LIGHT_MODEL:
                            attributes_name = 
                        elif model in SWITCH_MODEL:
                            attributes_name =
                        elif model in VALVE_MODEL:
                            attributes_name =

                        for attribute in attributes_name:
                            _LOGGER.debug(f"Adding attributes select for : {device_name} {attribute}")
                            entities.append(Neviweb130DeviceAttributeSelect(coordinator, client, device_info, device_name, attribute))

    async_add_entities(entities, True)


class Neviweb130DeviceAttributeSelect(CoordinatorEntity, SelectEntity):
    """Representation of a specific Neviweb130 select entity."""

    def __init__(self, coordinator: DataUpdateCoordinator, client: Neviweb130Client, device: dict, device_name: str, attribute: str):
        """Initialize the select entity."""
        super().__init__(coordinator)
        self._client = client
        self._device = device
        self._device_name = device_name
        self._master_device_id = device["id"]
        self._attribute = attribute
        self._is_wifi =  #true or false
        self._device_type =  #wifi or zigbee
        self._attr_name = f"{device_name} {attribute.replace('_', ' ').capitalize()}"
        self._attr_unique_id = f"{device.get('id')}_{attribute}"
        if self._attribute == ATTR_KEYPAD:
            self._options = ["locked", "unlocked", "partiallyLocked"]
        elif self._attribute == ATTR_LED_ON_COLOR:
            self._options = ["Lime", "Amber", "Fushia", "Perle", "Blue", "Red"]
        elif self._attribute == ATTR_LED_OFF_COLOR:
            self._options = ["Lime", "Amber", "Fushia", "Perle", "Blue", "Red"]

    @property
    def options(self):
        """Return a set of selectable options."""
        return self._options

    @property
    def current_option(self):
        """Return the current selected option."""
        return self._device.get(self._attribute)

    async def async_select_option(self, option: str) -> None:
        """Change the selected option."""
        if self._attribute == ATTR_BACKLIGHT:
            await self._client.async_set_backlight(self._master_device_id, option, self._device_type)
            self._device[self._attribute] = option
        elif self._attribute == ATR_KEYPAD:
            await self._client.async_set_keypad_lock(self._master_device_id, value, self._is_wifi)
            self._device[self._attribute] = value
        self.async_write_ha_state()

    async def async_update(self):
        """Fetch new state data for the select entity."""
        await self.coordinator.async_request_refresh()
        self._device = self.coordinator.data
        self.async_write_ha_state()
