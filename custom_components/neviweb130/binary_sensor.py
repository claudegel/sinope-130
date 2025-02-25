"""
Support for Neviweb binary sensors connected via GT130 ZigBee.
"""

from __future__ import annotations

import logging

from dataclasses import dataclass

from homeassistant.components.binary_sensor import (
    BinarySensorDeviceClass,
    BinarySensorEntity,
    BinarySensorEntityDescription,
)
from homeassistant.core import HomeAssistant
from homeassistant.config_entries import ConfigEntry
from homeassistant.helpers.update_coordinator import (
    CoordinatorEntity,
    DataUpdateCoordinator,
)
from homeassistant.helpers.entity_platform import AddEntitiesCallback
from homeassistant.helpers import device_registry as dr

from .const import DOMAIN

from .attributes import (
    ALL_MODEL,
    CLIMATE_MODEL,
    LIGHT_MODEL,
    SWITCH_MODEL,
    VALVE_MODEL,
)

DEFAULT_NAME = 'neviweb130 binary_sensor'
DEFAULT_NAME_2 = 'neviweb130 binary_sensor 2'
DEFAULT_NAME_3 = 'neviweb130 binary_sensor 3'

_LOGGER = logging.getLogger(__name__)

@dataclass(frozen=True, kw_only=True)
class Neviweb130DeviceBinarySensorEntityDescription(BinarySensorEntityDescription):
    """Describes Sensibo Motion binary sensor entity."""

    value_fn: Callable[[], bool | None]


TEMP_ALARM_DESCRIPTION = Neviweb130DeviceBinarySensorEntityDescription(
    key=ATTR_TEMP_ALARM,
    translation_key="temp_alarm",
    device_class=BinarySensorDeviceClass.PROBLEM,
    value_fn=lambda data: data.temp_alarm,
)

WATER_LEAK_STATUS_DESCRIPTION = Neviweb130DeviceBinarySensorEntityDescription(
    key=ATTR_WATER_LEAK_STATUS,
    translation_key="leak_status",
    device_class=BinarySensorDeviceClass.PROBLEM,
    value_fn=lambda data: data.leak_status,
)

DEVICE_SENSOR_TYPES: tuple[Neviweb130DeviceBinarySensorEntityDescription, ...] = (
    TEMP_ALARM_DESCRIPTION,
    WATER_LEAK_STATUS_DESCRIPTION,
)


async def async_setup_entry(
    hass: HomeAssistant,
    entry: ConfigEntry,
    async_add_entities: AddEntitiesCallback,
    discovery_info=None,
) -> None:
    """Set up the Neviweb binary sensor."""
    data = hass.data[DOMAIN][entry.entry_id]

    if 'neviweb130_client' not in data:
        _LOGGER.error("Neviweb130 client initialization failed.")
        return

    entities = []
    device_registry = dr.async_get(hass)
    
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
                        _LOGGER.debug("Config entry = %s", device_entry)
                        _LOGGER.debug("Attribute found for device: %s", master_device_name)
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
                            entities.append(Neviweb130DeviceAttributeBinarySensor(data['coordinator'], device_info, device_name, attribute, device_entry.id))

    async_add_entities(entities, True)


class Neviweb130DeviceAttributeBinarySensor(CoordinatorEntity, BinarySensorEntity):
    """Representation of a specific Neviweb130 binary sensor."""

    entity_description: Neviweb130DeviceBinarySensorEntityDescription

    def __init__(self, coordinator: DataUpdateCoordinator, device: dict, device_name: str, attribute: str, device_id: str):
        """Initialize the binary sensor."""
        super().__init__(coordinator)
        self._device = device
        self._device_name = device_name
        self._master_device_id = device["id"]
        self._attribute = attribute
        self._attr_name = f"{device_name} {attribute.replace('_', ' ').capitalize()}"
        self._attr_unique_id = f"{device.get('id')}_{attribute}"

    @property
    def is_on(self):
        """Return true if the binary sensor is on."""
#        return self._device.get(self._attribute) == "on"  # Adjust the condition
        return self.entity_description.value_fn(self.device_data)

#    async def async_update(self):
#        """Fetch new state data for the select entity."""
#        await self.coordinator.async_request_refresh()
#        self._device = self.coordinator.data
#        self.async_write_ha_state()
