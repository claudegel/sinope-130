"""
Support for Neviweb attributes buttons for devices connected via GT130 and wifi devices.
"""

from __future__ import annotations

import logging
from dataclasses import dataclass
from typing import Any, Final

from homeassistant.components.button import ButtonDeviceClass, ButtonEntity, ButtonEntityDescription
from homeassistant.config_entries import ConfigEntry
from homeassistant.const import EntityCategory
from homeassistant.core import HomeAssistant
from homeassistant.helpers import device_registry as dr
from homeassistant.helpers.entity_platform import AddEntitiesCallback
from homeassistant.helpers.update_coordinator import CoordinatorEntity

from .const import ALL_MODEL, DOMAIN, MODEL_ATTRIBUTES
from .coordinator import Neviweb130Coordinator

DEFAULT_NAME = "neviweb130 button"
DEFAULT_NAME_2 = "neviweb130 button 2"
DEFAULT_NAME_3 = "neviweb130 button 3"

_LOGGER = logging.getLogger(__name__)


@dataclass(frozen=True)
class Neviweb130ButtonEntityDescription(ButtonEntityDescription):
    """Class describing Neviweb130 Button entities."""

    data_key: str | None = None


BUTTON_TYPES: Final[tuple[Neviweb130ButtonEntityDescription, ...]] = (
    # Climate attributes
    Neviweb130ButtonEntityDescription(
        key="fan_filter_remain",  # nom du bouton
        device_class=ButtonDeviceClass.UPDATE,
        icon="mdi:air-filter",
        translation_key="reset_filter",  # pour traduction
        entity_category=EntityCategory.CONFIG,  # pour mettre dans diagnostic
        data_key="filter_clean",  # attribute name
    ),
)


def get_attributes_for_model(model):
    return MODEL_ATTRIBUTES.get(model, {}).get("button", [])


def create_attribute_buttons(hass, entry, data, coordinator, device_registry):
    entities = []
    client = data["neviweb130_client"]

    _LOGGER.debug("Keys dans coordinator.data : %s", list(coordinator.data.keys()))

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
                _LOGGER.warning("Device %s pas encore dans coordinator.data", device_id)

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
                for desc in BUTTON_TYPES:
                    if desc.key == attribute:
                        entities.append(
                            Neviweb130DeviceAttributeButton(
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
    """Set up the Neviweb button."""
    data = hass.data[DOMAIN][entry.entry_id]

    if "neviweb130_client" not in data:
        _LOGGER.error("Neviweb130 client initialization failed.")
        return

    coordinator = data["coordinator"]
    device_registry = dr.async_get(hass)

    entities = create_attribute_buttons(hass, entry, data, coordinator, device_registry)

    async_add_entities(entities)
    hass.async_create_task(coordinator.async_request_refresh())


class Neviweb130DeviceAttributeButton(CoordinatorEntity[Neviweb130Coordinator], ButtonEntity):
    """Representation of a specific Neviweb130 button."""

    _attr_has_entity_name = True
    _attr_should_poll = True

    _ATTRIBUTE_METHODS: dict[str, Any] = {
        # "fan_filter_remain": lambda self: self._client.async_set_fan_filter_reminder(self._id),
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
        entity_description: Neviweb130ButtonEntityDescription,
    ):
        """Initialize the button."""
        super().__init__(coordinator)
        self._client = client
        self._device = device
        self.entity_description = entity_description
        self._id = str(device.get("id"))
        self._device_name = device_name
        self._device_id = device_id
        self._attribute = attribute
        self._attr_unique_id = f"{self._id}_{attribute}"
        self._attr_device_info = attr_info
        self._attr_icon = entity_description.icon
        self._attr_translation_key = entity_description.translation_key
        self._attr_device_class = entity_description.device_class
        self._attr_entity_category = entity_description.entity_category

    @property
    def unique_id(self):
        """Return a unique ID of the button."""
        return self._attr_unique_id

    @property
    def extra_state_attributes(self):
        """Return the state attributes of the button."""
        return {"device_id": self._attr_unique_id}

    async def async_press(self) -> None:
        """Handle the button press and confirm success."""
        handler = self._ATTRIBUTE_METHODS.get(self._attribute)
        if handler:
            success = await handler(self)
            if success:
                _LOGGER.info(f"Button {self._attr_translation_key} pressed.")
                self.async_write_ha_state()
                await self.coordinator.async_request_refresh()
            else:
                _LOGGER.warning(f"Button press failed for attribute: {self._attr_translation_key}")
        else:
            _LOGGER.warning("No handler for button attribute: %s", self._attribute)
