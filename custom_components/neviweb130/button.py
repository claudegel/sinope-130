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
                        if model in CLIMATE_MODEL:
                            device_type = "climate"
                            attributes_name = []
                        elif model in LIGHT_MODEL:
                            device_type = "light"
                            attributes_name = []
                        elif model in VALVE_MODEL:
                            device_type = "valve"
                            attributes_name = []

                        for attribute in DEVICE_ATTRIBUTES.get(device_type, []):
                            _LOGGER.debug(f"Adding button: {device_info['name']} {attribute}")
                            entities.append(
                                Neviweb130DeviceAttributeButton(
                                    data['coordinator'],
                                    device_info,
                                    device_name,
                                    attribute,
                                  #  Neviweb130ButtonEntityDescription,
                                    device_entry.id,
                                    attr_info,
                                )
                            )

    async_add_entities(entities, True)


class Neviweb130DeviceAttributeButton(CoordinatorEntity, ButtonEntity):
    """Representation of a specific Neviweb130 button."""

    entity_description: Neviweb130ButtonEntityDescription

    def __init__(
        self,
        coordinator: DataUpdateCoordinator,
        device: dict,
        device_name: str,
        attribute: str,
        device_id: str,
        attr_info: dict,
    ):
        """Initialize the button."""
#        super().__init__(coordinator)
        self._device = device
        self._attribute = attribute
        self._device_name = device_name
        self._device_id = device_id
        self._state = None
        self._attr_name = f"{self._attribute.replace('_', ' ').capitalize()}"
        self._attr_unique_id = f"{self._device.get('id')}_{attribute}"
        self._attr_device_info = attr_info
        self._attr_friendly_name = f"{self._device.get("friendly_name")} {attribute.replace('_', ' ').capitalize()}"
        self._icon = None

    @property
    def name(self):
        """Return the name of the sensor."""
        return self._attr_name

    @property
    def unique_id(self):
        """Return a unique ID."""
        _LOGGER.debug("Device id = %s", self._device_id)
        _LOGGER.debug("Unique id = %s", self._attr_unique_id)
        return self._attr_unique_id

    @property
    def state(self):
        """Return the state of the sensor."""
        _LOGGER.debug(
            "Device %s with attribute %s have State = %s",
            self._device,
            self._attribute,
            self._state,
        )
        return state = self._device.get(self._attribute)

    @property
    def icon(self):
        """Return the icon to use in the frontend, if any."""
        return self._icon

    @property
    def extra_state_attributes(self):
        """Return the state attributes of the sensor."""
        return {
            "device_name": self._attr_name,
            ATTR_FRIENDLY_NAME: self._attr_friendly_name,
            "device_id": self._attr_unique_id,
        }

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
