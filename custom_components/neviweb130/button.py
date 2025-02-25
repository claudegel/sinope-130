"""
Support for Neviweb buttons connected via GT130 ZigBee.
"""

from __future__ import annotations

import logging
from dataclasses import dataclass

from homeassistant.components.button import ButtonEntity, ButtonEntityDescription
from homeassistant.core import HomeAssistant
from homeassistant.config_entries import ConfigEntry
from homeassistant.helpers.update_coordinator import (
    CoordinatorEntity,
    DataUpdateCoordinator,
)
from homeassistant.helpers.entity_platform import AddEntitiesCallback

from .const import DOMAIN
from .attributes import (
    ALL_MODEL,
    CLIMATE_MODEL,
    LIGHT_MODEL,
    VALVE_MODEL,
)

_LOGGER = logging.getLogger(__name__)

@dataclass(frozen=True, kw_only=True)
class Neviweb130ButtonEntityDescription(ButtonEntityDescription):
    """Class describing Neviweb130 Button entities."""

    data_key: str


DEVICE_BUTTON_TYPES = Neviweb130ButtonEntityDescription(
    key="reset_filter", #nom du bouton
    translation_key="reset_filter", #pour traduction
    entity_category=EntityCategory.CONFIG, #pour mettre dans diagnostic
    data_key="filter_clean", #attribute name
)


async def async_setup_entry(
    hass: HomeAssistant,
    entry: ConfigEntry,
    async_add_entities: AddEntitiesCallback,
    discovery_info=None,
) -> None:
    """Set up the Neviweb button."""
    data = hass.data[DOMAIN][entry.entry_id]

    if 'neviweb130_client' not in data:
        _LOGGER.error("Neviweb130 client initialization failed.")
        return

    entities = []
    for gateway_data in [
        data['neviweb130_client'].gateway_data,
        data['neviweb130_client'].gateway_data2,
        data['neviweb130_client'].gateway_data3
    ]:
        if gateway_data is not None and gateway_data != "_":
            for device_info in gateway_data:
                if "signature" in device_info and "model" in device_info["signature"]:
                    model = device_info["signature"]["model"]
                    device_id = str(device_info["id"])
                    device_type = None
                    if model in CLIMATE_MODEL or model in LIGHT_MODEL or model in VALVE_MODEL or model in SWITCH_MODEL:
                        if model in CLIMATE_MODEL:
                            device_type = "climate"
                        elif model in LIGHT_MODEL:
                            device_type = "light"
                        elif model in VALVE_MODEL:
                            device_type = "valve"
                        
                        for attribute in DEVICE_ATTRIBUTES.get(device_type, []):
                            _LOGGER.debug(f"Adding button: {device_info['name']} {attribute}")
                            entities.append(
                                Neviweb130DeviceAttributeButton(data['coordinator'], device_info, attribute, Neviweb130ButtonEntityDescription)
                            )

    async_add_entities(entities, True)


class Neviweb130DeviceAttributeButton(CoordinatorEntity, ButtonEntity):
    """Representation of a specific Neviweb130 button."""

    entity_description: Neviweb130ButtonEntityDescription

    def __init__(self, coordinator: DataUpdateCoordinator, device: dict, attribute: str):
        """Initialize the button."""
        super().__init__(coordinator)
        self._device = device
        self._device_name = device_name
        self._master_device_id = device["id"]
        self._attribute = attribute
        self._attr_name = f"{device.get('name')} {attribute.replace('_', ' ').capitalize()}"
        self._attr_unique_id = f"{device.get('id')}_{attribute}"
        self.entity_description = entity_description

    async def async_press(self) -> None:
        """Handle the button press."""
        # Implement the button press action here
        await self.async_send(self._master_device_id, key=self.entity_description.data_key, value=True)
        _LOGGER.info(f"Button {self._attr_name} pressed.")

    async def async_update(self):
        """Fetch new state data for the select entity."""
        await self.coordinator.async_request_refresh()
        self._device = self.coordinator.data
        self.async_write_ha_state()
