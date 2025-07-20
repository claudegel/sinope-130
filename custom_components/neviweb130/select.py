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
                        master_device_name = f'{device_info["name"]}'
                        device_sku = device_info["sku"]
                        device_firmware = "{major}.{middle}.{minor}".format(
                            **device_info["signature"]["softVersion"]
                        _LOGGER.debug("device found = %s", device_name)

                        # Ensure the device is registered in the device registry
                        device_entry = device_registry.async_get_or_create(
                            config_entry_id=entry.entry_id,
                            identifiers={(DOMAIN, str(device_info["id"]))},
                            name=device_name,
                            manufacturer="claudegel",
                            model=device_info["signature"]["model"],
                            sw_version=device_firmware,
                        )
                        attr_info = {
                            "identifiers": device_entry.identifiers,
                            "name": device_entry.name,
                            "manufacturer": device_entry.manufacturer,
                            "model": device_entry.model,
                        }
                        _LOGGER.debug("Config entry = %s", device_entry)
                        _LOGGER.debug("Attribute found for device: %s", master_device_name)
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
                            entities.append(
                                Neviweb130DeviceAttributeSelect(
                                    coordinator,
                                    client,
                                    device_info,
                                    device_name,
                                    attribute,
                                    device_entry.id,
                                    attr_info,
                                )
                            )

    async_add_entities(entities, True)


class Neviweb130DeviceAttributeSelect(CoordinatorEntity, SelectEntity):
    """Representation of a specific Neviweb130 select entity."""

    def __init__(
        self,
        coordinator: DataUpdateCoordinator,
        client: Neviweb130Client,
        device: dict,
        device_name: str,
        attribute: str,
        device_id: str,
        device_info: dict,
    ):
        """Initialize the select entity."""
        super().__init__(coordinator)
        self._client = client
        self._device = device
        self._attribute = attribute
        self._device_name = device_name
        self._device_id = device_id
        self._state = None
        self._is_wifi =  None#true or false
        self._device_type =  #wifi or zigbee
        self._attr_name = f"{self._attribute.replace('_', ' ').capitalize()}"
        self._attr_unique_id = f"{self._device.get('id')}_{attribute}"
        self._attr_device_info = device_info
        if self._attribute == ATTR_KEYPAD:
            self._options = ["locked", "unlocked", "partiallyLocked"]
        elif self._attribute == ATTR_LED_ON_COLOR:
            self._options = ["Lime", "Amber", "Fushia", "Perle", "Blue", "Red"]
        elif self._attribute == ATTR_LED_OFF_COLOR:
            self._options = ["Lime", "Amber", "Fushia", "Perle", "Blue", "Red"]
        self._attr_friendly_name = f"{self._device.get("friendly_name")} {attribute.replace('_', ' ').capitalize()}"
        self._icon = None

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
