"""
Support for Neviweb attributes binary sensors for devices connected via GT130 and Wi-Fi devices.
"""

from __future__ import annotations

import logging
from dataclasses import dataclass
from typing import Callable, Final, Optional

from homeassistant.components.binary_sensor import (
    BinarySensorDeviceClass,
    BinarySensorEntity,
    BinarySensorEntityDescription,
)
from homeassistant.config_entries import ConfigEntry
from homeassistant.const import EntityCategory
from homeassistant.core import HomeAssistant
from homeassistant.helpers import device_registry as dr
from homeassistant.helpers.device_registry import DeviceInfo
from homeassistant.helpers.entity_platform import AddEntitiesCallback
from homeassistant.helpers.update_coordinator import CoordinatorEntity

from .const import DOMAIN, FULL_MODEL, MODEL_ATTRIBUTES, SIGNAL_EVENTS_CHANGED
from .coordinator import Neviweb130Coordinator
from .helpers import NamingHelper

_LOGGER = logging.getLogger(__name__)


def static_icon(on_icon: str, off_icon: str) -> Callable[[bool, dict | None, str | None], str]:
    """Return icon_fn function compatible for Neviweb130BinarySensorEntityDescription."""
    return lambda is_on, *_: on_icon if is_on else off_icon


@dataclass(frozen=True)
class Neviweb130BinarySensorEntityDescription(BinarySensorEntityDescription):
    """Describes Sensibo Motion binary sensor entity."""

    is_on_fn: Callable[[dict, str], bool] | None = None
    icon_fn: Callable[[bool, dict | None, str | None], str] | None = None
    on_icon: str = "mdi:checkbox-marked"
    off_icon: str = "mdi:checkbox-blank-outline"
    signal: Optional[str] = None


BINARY_SENSOR_TYPES: Final[tuple[Neviweb130BinarySensorEntityDescription, ...]] = (
    #  Valve attributes
    Neviweb130BinarySensorEntityDescription(
        key="valve_temp_alert",
        device_class=BinarySensorDeviceClass.PROBLEM,
        translation_key="temp_alert",
        entity_category=EntityCategory.DIAGNOSTIC,
        is_on_fn=lambda data, attr: str(data[attr]).lower() in {"low"},
        icon_fn=static_icon("mdi:thermometer-alert", "mdi:thermometer"),
    ),
    Neviweb130BinarySensorEntityDescription(
        key="water_leak_status",
        device_class=BinarySensorDeviceClass.MOISTURE,
        translation_key="leak_status",
        entity_category=EntityCategory.DIAGNOSTIC,
        is_on_fn=lambda data, attr: str(data[attr]).lower() in {"water", "leak", "flowmeter", "probe"},
        icon_fn=static_icon("mdi:pipe-leak", "mdi:pipe"),
    ),
    #  Switch attributes
    Neviweb130BinarySensorEntityDescription(
        key="battery_status",
        device_class=BinarySensorDeviceClass.BATTERY,
        translation_key="battery_status",
        entity_category=EntityCategory.DIAGNOSTIC,
        is_on_fn=lambda data, attr: str(data[attr]).lower() in {"low"},
        icon_fn=static_icon("mdi:battery-80", "mdi:battery-alert-variant-outline"),
    ),
    Neviweb130BinarySensorEntityDescription(
        key="gauge_error",
        name="Gauge disconected",
        device_class=BinarySensorDeviceClass.PROBLEM,
        translation_key="gauge_error",
        is_on_fn=lambda data, attr: data.get(attr) == -2,
        icon_fn=static_icon("mdi:alert", "mdi:gauge"),
        signal=SIGNAL_EVENTS_CHANGED,
        entity_category=EntityCategory.DIAGNOSTIC,
    ),
    Neviweb130BinarySensorEntityDescription(
        key="low_temp_status",
        device_class=BinarySensorDeviceClass.BATTERY,
        translation_key="low_temp_status",
        entity_category=EntityCategory.DIAGNOSTIC,
        is_on_fn=lambda data, attr: bool(data.get(attr)),
        icon_fn=static_icon("mdi:thermometer-lines", "mdi:thermometer"),
    ),
    #  Real Sensor attributes
    Neviweb130BinarySensorEntityDescription(
        key="leak_status",
        device_class=BinarySensorDeviceClass.MOISTURE,
        translation_key="leak_status",
        entity_category=EntityCategory.DIAGNOSTIC,
        is_on_fn=lambda data, attr: str(data[attr]).lower() in {"water", "leak", "probe"},
        icon_fn=static_icon("mdi:pipe-leak", "mdi:pipe"),
    ),
    Neviweb130BinarySensorEntityDescription(
        key="refuel_status",
        device_class=BinarySensorDeviceClass.TAMPER,
        translation_key="refuel_status",
        entity_category=EntityCategory.DIAGNOSTIC,
        is_on_fn=lambda data, attr: str(data[attr]).lower() in {"refueled"},
        icon_fn=static_icon("mdi:propane-tank", "mdi:propane-tank-outline"),
    ),
    Neviweb130BinarySensorEntityDescription(
        key="level_status",
        device_class=BinarySensorDeviceClass.PROBLEM,
        translation_key="level_status",
        entity_category=EntityCategory.DIAGNOSTIC,
        is_on_fn=lambda data, attr: str(data[attr]).lower() in {"low"},
        icon_fn=static_icon("mdi:propane-tank-outline", "mdi:propane-tank"),
    ),
    Neviweb130BinarySensorEntityDescription(
        key="gateway_status",
        device_class=BinarySensorDeviceClass.CONNECTIVITY,
        translation_key="gateway_status",
        entity_category=EntityCategory.DIAGNOSTIC,
        is_on_fn=lambda data, attr: str(data[attr]).lower() in {"online"},
        icon_fn=static_icon("mdi:router-wireless", "mdi:router-off"),
        signal=SIGNAL_EVENTS_CHANGED,
    ),
    #  Thermostat attributes
    Neviweb130BinarySensorEntityDescription(
        key="is_heating",
        device_class=BinarySensorDeviceClass.HEAT,
        translation_key="heating",
        entity_category=EntityCategory.DIAGNOSTIC,
        is_on_fn=lambda data, attr: bool(data.get(attr)),
        icon_fn=static_icon("mdi:thermometer-lines", "mdi:thermometer"),
    ),
    Neviweb130BinarySensorEntityDescription(
        key="is_em_heat",
        device_class=BinarySensorDeviceClass.HEAT,
        translation_key="em_heating",
        entity_category=EntityCategory.DIAGNOSTIC,
        is_on_fn=lambda data, attr: bool(data.get(attr)),
        icon_fn=static_icon("mdi:thermometer-lines", "mdi:thermometer"),
    ),
    Neviweb130BinarySensorEntityDescription(
        key="emergency_heat_allowed",
        device_class=BinarySensorDeviceClass.HEAT,
        translation_key="emergency_heat_allowed",
        entity_category=EntityCategory.DIAGNOSTIC,
        is_on_fn=lambda data, attr: bool(data.get(attr)),
        icon_fn=static_icon("mdi:thermometer-lines", "mdi:thermometer"),
    ),
    #  All devices attributes
    Neviweb130BinarySensorEntityDescription(
        key="activation",
        device_class=BinarySensorDeviceClass.CONNECTIVITY,
        on_icon="mdi:cloud-download",
        off_icon="mdi:cloud-off-outline",
        translation_key="activation",
        entity_category=EntityCategory.DIAGNOSTIC,
        is_on_fn=lambda data, attr: bool(data.get(attr)),
    ),
)


def get_attributes_for_model(model):
    return MODEL_ATTRIBUTES.get(model, {}).get("binary_sensor", [])


def create_attribute_binary_sensors(hass, entry, data, coordinator, device_registry):
    entities = []
    client = data["neviweb130_client"]

    config_prefix = data["prefix"]
    platform = __name__.split(".")[-1] # "binary_sensor"
    naming = NamingHelper(domain=DOMAIN, prefix=config_prefix)

    _LOGGER.debug("Keys dans coordinator.data : %s", list(coordinator.data.keys()))

    for index, gateway_data in enumerate([
        data["neviweb130_client"].gateway_data,
        data["neviweb130_client"].gateway_data2,
        data["neviweb130_client"].gateway_data3,
    ], start=1):

        default_name = naming.default_name(platform, index)
        if not gateway_data or gateway_data == "_":
            continue

        for device_info in gateway_data:
            model = device_info["signature"]["model"]
            if model not in FULL_MODEL:
                continue

            device_id = str(device_info["id"])
            if device_id not in coordinator.data:
                _LOGGER.warning("Device %s not yet in coordinator.data", device_id)

            device_name = naming.device_name(platform, index, device_info)
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

    entities = create_attribute_binary_sensors(hass, entry, data, coordinator, device_registry)

    async_add_entities(entities)
    hass.async_create_task(coordinator.async_request_refresh())


class Neviweb130DeviceAttributeBinarySensor(CoordinatorEntity[Neviweb130Coordinator], BinarySensorEntity):
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
        attr_info: DeviceInfo,
        coordinator,
        entity_description: Neviweb130BinarySensorEntityDescription,
    ):
        """Initialize the binary sensor."""
        super().__init__(coordinator)
        self._client = client
        self._device = device
        self.entity_description: Neviweb130BinarySensorEntityDescription = entity_description
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
    def icon(self) -> str | None:
        """Return the icon to use in the frontend, if any."""

        # Priority to icon_fn if defined
        if self.entity_description.icon_fn:
            try:
                device_obj = self.coordinator.data.get(self._id)
                return self.entity_description.icon_fn(self.is_on, device_obj, self._attribute)
            except Exception as exc:
                _LOGGER.warning("icon_fn error for %s: %s", self._attr_unique_id, exc)

        # Falback to Get icons from entity description
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
                return self.entity_description.is_on_fn(device_obj, self._attribute)
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
