"""
Support for Neviweb attributes binary sensors for devices connected via GT130 and wifi devices.
"""

from __future__ import annotations

import logging
from dataclasses import dataclass
from typing import Callable, Final

from homeassistant.components.binary_sensor import (
    BinarySensorDeviceClass, BinarySensorEntity, BinarySensorEntityDescription)
from homeassistant.config_entries import ConfigEntry
from homeassistant.const import EntityCategory
from homeassistant.core import HomeAssistant
from homeassistant.helpers import device_registry as dr
from homeassistant.helpers.entity_platform import AddEntitiesCallback
from homeassistant.helpers.update_coordinator import CoordinatorEntity

from .const import (DOMAIN, FULL_MODEL, MODEL_ATTRIBUTES)
from .coordinator import Neviweb130Coordinator

DEFAULT_NAME = "neviweb130 binary_sensor"
DEFAULT_NAME_2 = "neviweb130 binary_sensor 2"
DEFAULT_NAME_3 = "neviweb130 binary_sensor 3"

_LOGGER = logging.getLogger(__name__)


@dataclass(frozen=True)
class Neviweb130BinarySensorEntityDescription(BinarySensorEntityDescription):
    """Describes Sensibo Motion binary sensor entity."""

    is_on_fn: Callable[[dict, str], bool | None] = None
    on_icon: str = "mdi:checkbox-marked"
    off_icon: str = "mdi:checkbox-blank-outline"


BINARY_SENSOR_TYPES: Final[
    tuple[Neviweb130BinarySensorEntityDescription, ...]
] = (
    # Valve attributes
    Neviweb130BinarySensorEntityDescription(
        key="temp_alert",
        device_class=BinarySensorDeviceClass.PROBLEM,
        on_icon="mdi:thermometer-alert",
        off_icon="mdi:thermometer",
        translation_key="temp_alert",
        entity_category=EntityCategory.DIAGNOSTIC,
        is_on_fn=lambda data, attr: str(data[attr]).lower() in {"low"},
    ),
    Neviweb130BinarySensorEntityDescription(
        key="water_leak_status",
        device_class=BinarySensorDeviceClass.PROBLEM,
        on_icon="mdi:pipe-leak",
        off_icon="mdi:pipe",
        translation_key="leak_status",
        entity_category=EntityCategory.DIAGNOSTIC,
        is_on_fn=lambda data, attr: str(data[attr]).lower()
        in {"water", "leak", "flowmeter", "probe"},
    ),
    # Switch attributes
    Neviweb130BinarySensorEntityDescription(
        key="battery_status",
        device_class=BinarySensorDeviceClass.PROBLEM,
        on_icon="mdi:battery-80",
        off_icon="mdi:battery-alert-variant-outline",
        translation_key="battery_status",
        entity_category=EntityCategory.DIAGNOSTIC,
        is_on_fn=lambda data, attr: str(data[attr]).lower() in {"low"},
    ),
    # Real Sensor attributes
    Neviweb130BinarySensorEntityDescription(
        key="leak_status",
        device_class=BinarySensorDeviceClass.PROBLEM,
        on_icon="mdi:pipe-leak",
        off_icon="mdi:pipe",
        translation_key="leak_status",
        entity_category=EntityCategory.DIAGNOSTIC,
        is_on_fn=lambda data, attr: str(data[attr]).lower()
        in {"water", "leak", "probe"},
    ),
    Neviweb130BinarySensorEntityDescription(
        key="refuel_status",
        device_class=BinarySensorDeviceClass.PROBLEM,
        on_icon="mdi:propane-tank",
        off_icon="mdi:propane-tank-outline",
        translation_key="refuel_status",
        entity_category=EntityCategory.DIAGNOSTIC,
        is_on_fn=lambda data, attr: str(data[attr]).lower() in {"refueled"},
    ),
    Neviweb130BinarySensorEntityDescription(
        key="level_status",
        device_class=BinarySensorDeviceClass.PROBLEM,
        on_icon="mdi:propane-tank-outline",
        off_icon="mdi:propane-tank",
        translation_key="level_status",
        entity_category=EntityCategory.DIAGNOSTIC,
        is_on_fn=lambda data, attr: str(data[attr]).lower() in {"low"},
    ),
)


def get_attributes_for_model(model):
    return MODEL_ATTRIBUTES.get(model, {}).get("binary_sensor", [])


def create_attribute_binary_sensors(
    hass, entry, data, coordinator, device_registry
):
    entities = []
    client = data["neviweb130_client"]

    _LOGGER.debug(
        "Keys dans coordinator.data : %s", list(coordinator.data.keys())
    )

    gateway_datas = [
        (client.gateway_data, DEFAULT_NAME),
        (client.gateway_data2, DEFAULT_NAME_2),
        (client.gateway_data3, DEFAULT_NAME_3),
    ]

    for gateway_data, default_name in gateway_datas:
        if not gateway_data or gateway_data == "_":
            continue

        for device_info in gateway_data:
            model = device_info["signature"]["model"]
            if model not in FULL_MODEL:
                continue

            device_id = str(device_info["id"])
            if device_id not in coordinator.data:
                _LOGGER.warning(
                    "Device %s pas encore dans coordinator.data", device_id
                )

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
                for desc in BINARY_SENSOR_TYPES:
                    if desc.key == attribute:
                        entities.append(
                            Neviweb130DeviceAttributeBinarySensor(
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
    """Set up the Neviweb binary sensor."""
    data = hass.data[DOMAIN][entry.entry_id]

    if "neviweb130_client" not in data:
        _LOGGER.error("Neviweb130 client initialization failed.")
        return

    coordinator = data["coordinator"]
    device_registry = dr.async_get(hass)

    entities = create_attribute_binary_sensors(
        hass, entry, data, coordinator, device_registry
    )

    async_add_entities(entities)
    hass.async_create_task(coordinator.async_request_refresh())


class Neviweb130DeviceAttributeBinarySensor(
    CoordinatorEntity[Neviweb130Coordinator], BinarySensorEntity
):
    """Representation of a specific Neviweb130 binary sensor."""

    _attr_has_entity_name = True
    _attr_should_poll = True

    def __init__(
        self,
        client,
        device: dict,
        device_name: str,
        attribute: str,
        device_id: str,
        attr_info: dict,
        coordinator,
        entity_description: Neviweb130BinarySensorEntityDescription,
    ):
        """Initialize the binary sensor."""
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
        self._attr_translation_key = entity_description.translation_key
        self._attr_device_class = entity_description.device_class
        self._attr_entity_category = entity_description.entity_category

    @property
    def unique_id(self):
        """Return a unique ID."""
        return self._attr_unique_id

    @property
    def icon(self):
        """Return the icon to use in the frontend, if any."""
        # Get icons from entity description
        on_icon = getattr(self.entity_description, "on_icon", None)
        off_icon = getattr(self.entity_description, "off_icon", None)

        if on_icon is None or off_icon is None:
            # Fallback to default icon
            return super().icon

        return on_icon if self.is_on else off_icon

    @property
    def is_on(self):
        """Return true if the binary sensor is on."""
        device_obj = self.coordinator.data.get(self._id)
        if device_obj and self.entity_description.is_on_fn:
            try:
                return self.entity_description.is_on_fn(
                    device_obj, self._attribute
                )
            except Exception as exc:
                _LOGGER.error(
                    "Error evaluating is_on for %s: %s",
                    self._attr_unique_id,
                    exc,
                )
                return None
        _LOGGER.warning(
            "AttributeBinarySensor: %s attribute %s not found for device: %s.",
            self._attr_unique_id,
            self._attribute,
            self._id,
        )
        return None

    @property
    def extra_state_attributes(self):
        """Return the state attributes of the sensor."""
        return {"device_id": self._attr_unique_id}
