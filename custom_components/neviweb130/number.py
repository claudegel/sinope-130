"""
Support for Neviweb attributes numbers for devices connected via GT130 and Wi-Fi devices.
"""

from __future__ import annotations

import logging
from dataclasses import dataclass
from typing import Final, override

from homeassistant.components.number import NumberEntity, NumberEntityDescription
from homeassistant.components.number.const import NumberDeviceClass, NumberMode
from homeassistant.config_entries import ConfigEntry
from homeassistant.const import PERCENTAGE, EntityCategory, UnitOfTemperature, UnitOfTime
from homeassistant.core import HomeAssistant
from homeassistant.helpers import device_registry as dr
from homeassistant.helpers.device_registry import DeviceInfo
from homeassistant.helpers.entity_platform import AddEntitiesCallback
from homeassistant.helpers.update_coordinator import CoordinatorEntity

from .const import ALL_MODEL, DOMAIN, MODEL_ATTRIBUTES, RISKY_ATTRIBUTES
from .coordinator import Neviweb130Coordinator
from .helpers import create_risky_issue, NamingHelper

_LOGGER = logging.getLogger(__name__)


@dataclass(frozen=True)
class Neviweb130NumberEntityDescription(NumberEntityDescription):
    """Class describing Neviweb130 number entities."""

    data_key: str | None = None


NUMBER_TYPES: Final[tuple[Neviweb130NumberEntityDescription, ...]] = (
    #  Climate attributes
    Neviweb130NumberEntityDescription(
        key="cool_lockout_temp",
        icon="mdi:thermometer",
        device_class=NumberDeviceClass.TEMPERATURE,
        mode=NumberMode.AUTO,
        native_min_value=0,
        native_max_value=30,
        native_step=1,
        translation_key="cool_lockout_temp",
        native_unit_of_measurement=UnitOfTemperature.CELSIUS,
    ),
    Neviweb130NumberEntityDescription(
        key="heat_lockout_temp",
        icon="mdi:thermometer",
        device_class=NumberDeviceClass.TEMPERATURE,
        mode=NumberMode.AUTO,
        native_min_value=10,
        native_max_value=30,
        native_step=1,
        translation_key="heat_lockout_temp",
        native_unit_of_measurement=UnitOfTemperature.CELSIUS,
    ),
    Neviweb130NumberEntityDescription(
        key="min_temp",
        icon="mdi:thermometer",
        device_class=NumberDeviceClass.TEMPERATURE,
        mode=NumberMode.AUTO,
        native_min_value=5,
        native_max_value=26,
        native_step=1,
        translation_key="min_temp",
        native_unit_of_measurement=UnitOfTemperature.CELSIUS,
    ),
    Neviweb130NumberEntityDescription(
        key="max_temp",
        icon="mdi:thermometer",
        device_class=NumberDeviceClass.TEMPERATURE,
        mode=NumberMode.AUTO,
        native_min_value=8,
        native_max_value=36,
        native_step=1,
        translation_key="max_temp",
        native_unit_of_measurement=UnitOfTemperature.CELSIUS,
    ),
    Neviweb130NumberEntityDescription(
        key="min_cool_temp",
        icon="mdi:thermometer",
        device_class=NumberDeviceClass.TEMPERATURE,
        mode=NumberMode.AUTO,
        native_min_value=16,
        native_max_value=30,
        native_step=1,
        translation_key="min_cool_temp",
        native_unit_of_measurement=UnitOfTemperature.CELSIUS,
    ),
    Neviweb130NumberEntityDescription(
        key="max_cool_temp",
        icon="mdi:thermometer",
        device_class=NumberDeviceClass.TEMPERATURE,
        mode=NumberMode.AUTO,
        native_min_value=16,
        native_max_value=30,
        native_step=1,
        translation_key="max_cool_temp",
        native_unit_of_measurement=UnitOfTemperature.CELSIUS,
    ),
    Neviweb130NumberEntityDescription(
        key="floor_setpoint_min",
        icon="mdi:thermometer",
        device_class=NumberDeviceClass.TEMPERATURE,
        mode=NumberMode.AUTO,
        native_min_value=5,
        native_max_value=26,
        native_step=1,
        translation_key="floor_min_temp",
        native_unit_of_measurement=UnitOfTemperature.CELSIUS,
    ),
    Neviweb130NumberEntityDescription(
        key="floor_setpoint_max",
        icon="mdi:thermometer",
        device_class=NumberDeviceClass.TEMPERATURE,
        mode=NumberMode.AUTO,
        native_min_value=10,
        native_max_value=36,
        native_step=1,
        translation_key="floor_max_temp",
        native_unit_of_measurement=UnitOfTemperature.CELSIUS,
    ),
    Neviweb130NumberEntityDescription(
        key="setpoint_away",
        icon="mdi:thermometer",
        device_class=NumberDeviceClass.TEMPERATURE,
        mode=NumberMode.AUTO,
        native_min_value=5,
        native_max_value=30,
        native_step=1,
        translation_key="setpoint_away",
        native_unit_of_measurement=UnitOfTemperature.CELSIUS,
    ),
    Neviweb130NumberEntityDescription(
        key="cool_setpoint_away",
        icon="mdi:thermometer",
        device_class=NumberDeviceClass.TEMPERATURE,
        mode=NumberMode.AUTO,
        native_min_value=10,
        native_max_value=30,
        native_step=1,
        translation_key="cool_setpoint_away",
        native_unit_of_measurement=UnitOfTemperature.CELSIUS,
    ),
    Neviweb130NumberEntityDescription(
        key="fan_filter_remain",
        icon="mdi:thermometer",
        device_class=NumberDeviceClass.DURATION,
        mode=NumberMode.AUTO,
        native_min_value=1,
        native_max_value=12,
        native_step=1,
        translation_key="fan_filter_remain",
        native_unit_of_measurement=UnitOfTime.SECONDS,
    ),
    #  Light attributes
    Neviweb130NumberEntityDescription(
        key="brightness",
        icon="mdi:light_bulb",
        device_class=NumberDeviceClass.POWER_FACTOR,
        mode=NumberMode.SLIDER,
        native_min_value=0,
        native_max_value=100,
        native_step=1,
        translation_key="brightness",
        native_unit_of_measurement=PERCENTAGE,
    ),
    Neviweb130NumberEntityDescription(
        key="intensity_min",
        icon="mdi:lightbulb-on-10",
        device_class=NumberDeviceClass.POWER_FACTOR,
        mode=NumberMode.BOX,
        native_min_value=10,
        native_max_value=3000,
        native_step=1,
        translation_key="intensity_min",
        native_unit_of_measurement=PERCENTAGE,
    ),
    Neviweb130NumberEntityDescription(
        key="led_on_intensity",
        icon="mdi:lightbulb-on",
        device_class=NumberDeviceClass.POWER_FACTOR,
        mode=NumberMode.AUTO,
        native_min_value=10,
        native_max_value=100,
        native_step=1,
        translation_key="led_on_intensity",
        native_unit_of_measurement=PERCENTAGE,
    ),
    Neviweb130NumberEntityDescription(
        key="led_off_intensity",
        icon="mdi:lightbulb-off",
        device_class=NumberDeviceClass.POWER_FACTOR,
        mode=NumberMode.AUTO,
        native_min_value=10,
        native_max_value=100,
        native_step=1,
        translation_key="led_off_intensity",
        native_unit_of_measurement=PERCENTAGE,
    ),
    #  Switch attributes
    Neviweb130NumberEntityDescription(
        key="water_remaining_time",
        icon="mdi:backup-restore",
        device_class=NumberDeviceClass.DURATION,
        mode=NumberMode.AUTO,
        native_min_value=0,
        native_max_value=65535,
        native_step=900,
        translation_key="water_remaining_time",
        native_unit_of_measurement=UnitOfTime.SECONDS,
    ),
    #  Valve attributes
)


def get_attributes_for_model(model):
    return MODEL_ATTRIBUTES.get(model, {}).get("number", [])


def create_attribute_numbers(hass, entry, data, coordinator, device_registry):
    entities = []
    client = data["neviweb130_client"]

    config_prefix = data["prefix"]
    platform = __name__.split(".")[-1] # "number"
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
            if model not in ALL_MODEL:
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

    if "neviweb130_client" not in data:
        _LOGGER.error("Neviweb130 client initialization failed.")
        return

    coordinator = data["coordinator"]

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
        "brightness": lambda self, value: self._client.async_set_brightness(self._id, value),
        "intensity_min": lambda self, value: self._client.async_set_light_min_intensity(self._id, value),
        "cool_lockout_temp": lambda self, value: self._client.async_set_cool_lockout_temp(
            self._id, value, self.is_gen2
        ),
        "cool_setpoint_away": lambda self, value: self._client.async_set_cool_setpoint_away(self._id, value),
        "heat_lockout_temp": lambda self, value: self._client.async_set_heat_lockout_temp(
            self._id, value, self.is_gen2
        ),
        "led_on_intensity": lambda self, value: self._client.async_set_led_on_intensity(self._id, value),
        "led_off_intensity": lambda self, value: self._client.async_set_led_off_intensity(self._id, value),
        "fan_filter_remain": lambda self, value: self._client.async_set_fan_filter_reminder(
            self._id, value, self.is_HC
        ),
        "floor_setpoint_max": lambda self, value: self._client.async_set_floor_limit(
            self._id, value, "high", self.is_wifi_floor
        ),
        "floor_setpoint_min": lambda self, value: self._client.async_set_floor_limit(
            self._id, value, "low", self.is_wifi_floor
        ),
        "max_cool_temp": lambda self, value: self._client.async_set_cool_setpoint_max(self._id, value),
        "min_cool_temp": lambda self, value: self._client.async_set_cool_setpoint_min(self._id, value),
        "max_temp": lambda self, value: self._client.async_set_setpoint_max(self._id, value),
        "min_temp": lambda self, value: self._client.async_set_setpoint_min(self._id, value),
        "water_remaining_time": lambda self, value: self._client.async_set_remaining_time(self._id, value),
        "setpoint_away": lambda self, value: self._client.async_set_room_setpoint_away(self._id, value),
        # ...
    }

    def __init__(
        self,
        client,
        device: dict,
        device_name: str,
        attribute: str,
        device_id: str,
        attr_info: DeviceInfo,
        coordinator,
        entity_description: Neviweb130NumberEntityDescription,
    ):
        """Initialize the number entity."""
        super().__init__(coordinator)
        self._client = client
        self._device = device
        self._id = str(device.get("id"))
        self._attribute = attribute
        self._native_value: float | None = None
        self._attr_unique_id = f"{self._id}_{attribute}"
        self._attr_device_info = attr_info
        self.entity_description = entity_description
        self._attr_icon = entity_description.icon
        self._attr_device_class = entity_description.device_class
        self._attr_translation_key = entity_description.translation_key
        if entity_description.native_min_value is not None:
            self._attr_native_min_value = entity_description.native_min_value
        if entity_description.native_max_value is not None:
            self._attr_native_max_value = entity_description.native_max_value
        if entity_description.native_step is not None:
            self._attr_native_step = entity_description.native_step
        if entity_description.mode is not None:
            self._attr_mode = entity_description.mode

    @property
    def unique_id(self):
        """Return a unique ID."""
        return self._attr_unique_id

    @property
    def is_HC(self):
        """Return True if device is a HC device"""
        device_obj = self.coordinator.data.get(self._id)
        return device_obj.get("is_HC", False) if device_obj else False

    @property
    def is_gen2(self):
        """Return True if device is a TH1124ZB-G2 or TH1123ZB-G2 device"""
        device_obj = self.coordinator.data.get(self._id)
        return device_obj.get("is_gen2", False) if device_obj else False

    @property
    def is_wifi(self):
        """Return True if device is a Wi-Fi device"""
        device_obj = self.coordinator.data.get(self._id)
        return device_obj.get("is_wifi", False) if device_obj else False

    @property
    def is_wifi_floor(self):
        """Return True if device is a Wi-Fi floor device"""
        device_obj = self.coordinator.data.get(self._id)
        return device_obj.get("is_wifi_floor", False) if device_obj else False

    @property
    def native_value(self) -> float | None:
        """Return the current value."""
        device_obj = self.coordinator.data.get(self._id)
        if device_obj and self._attribute in device_obj:
            return device_obj[self._attribute]
        else:
            _LOGGER.warning(
                "AttributeNumber: %s attribute %s not found for device: %s.",
                self._attr_unique_id,
                self._attribute,
                self._id,
            )
            return None

    @property
    def extra_state_attributes(self) -> dict:
        """Return the state attributes of the number."""
        return {"device_id": self._attr_unique_id}

    @override
    async def async_set_native_value(self, value: float) -> None:
        """Change the selected number value."""
        attribute = self._attribute

        # Fire an issue if attribut is risky
        if attribute in RISKY_ATTRIBUTES:
            create_risky_issue(self.hass, self.entity_id, attribute, value)

        handler = self._ATTRIBUTE_METHODS.get(self._attribute)

        if handler:
            success = await handler(self, value)
            if success:
                self._native_value = value
                self._device[self._attribute] = value
                self.async_write_ha_state()
                await self.coordinator.async_request_refresh()
            else:
                _LOGGER.warning(
                    "Failed to update attribute '%s' with value '%s'",
                    self._attribute,
                    value,
                )
        else:
            _LOGGER.warning("No handler for number attribute: %s", self._attribute)
