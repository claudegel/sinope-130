"""
Support for Neviweb sensors connected via GT130 Zigbee.
model 5051 = WL4200, WL4200C and WL4200S water leak detector connected to GT130.
model 5053 = WL4200C, perimeter cable water leak detector connected to GT130 (will be removed).
model 5050 = WL4200, WL4210 and WL4200S, water leak detector connected to Sedna valve.
model 5052 = WL4200C, perimeter cable water leak detector connected to sedna 2 gen.
model 4210 = WL4210, WL4210S connected to GT130.
model 42102 = WL4210, WL4210S connected to sedna valve.
model 5056 = LM4110-ZB, level monitor.
model 5055 = LM4110-LTE, level monitor, multiples tanks.
model 130 = gateway GT130.
model 3156 = gateway GT4220WF, GT4220WF-M for mesh valve network.
For more details about this platform, please refer to the documentation at
https://www.sinopetech.com/en/support/#api
"""

from __future__ import annotations

import datetime
import logging
import os
import time
from dataclasses import dataclass
from threading import Lock
from typing import Any, Mapping, override

from homeassistant.components.binary_sensor import BinarySensorDeviceClass
from homeassistant.components.persistent_notification import DOMAIN as PN_DOMAIN
from homeassistant.components.recorder.models import StatisticMeanType
from homeassistant.components.sensor import SensorDeviceClass, SensorEntity, SensorStateClass
from homeassistant.config_entries import ConfigEntry
from homeassistant.const import (
    ATTR_ENTITY_ID,
    CONF_NAME,
    EntityCategory,
    PERCENTAGE,
    SIGNAL_STRENGTH_DECIBELS_MILLIWATT,
    UnitOfEnergy,
    UnitOfTemperature,
    UnitOfVolume,
)
from homeassistant.core import HomeAssistant, ServiceCall
from homeassistant.exceptions import ServiceValidationError
from homeassistant.helpers import device_registry as dr
from homeassistant.helpers.device_registry import DeviceInfo
from homeassistant.helpers.entity_platform import AddEntitiesCallback
from homeassistant.helpers.update_coordinator import CoordinatorEntity

from .const import (
    ATTR_ACTIVE,
    ATTR_ANGLE,
    ATTR_BATT_ALERT,
    ATTR_BATT_PERCENT_NORMAL,
    ATTR_BATT_STATUS_NORMAL,
    ATTR_BATTERY_STATUS,
    ATTR_BATTERY_TYPE,
    ATTR_BATTERY_VOLTAGE,
    ATTR_CONF_CLOSURE,
    ATTR_ERROR_CODE_SET1,
    ATTR_FUEL_ALERT,
    ATTR_FUEL_PERCENT_ALERT,
    ATTR_GAUGE_TYPE,
    ATTR_LEAK_ALERT,
    ATTR_MODE,
    ATTR_OCCUPANCY,
    ATTR_REFUEL,
    ATTR_ROOM_TEMP_ALARM,
    ATTR_ROOM_TEMPERATURE,
    ATTR_RSSI,
    ATTR_SAMPLING,
    ATTR_SENSOR_TYPE,
    ATTR_STATUS,
    ATTR_TANK_HEIGHT,
    ATTR_TANK_PERCENT,
    ATTR_TANK_TYPE,
    ATTR_TEMP_ALERT,
    ATTR_WATER_LEAK_STATUS,
    CONF_PREFIX,
    DOMAIN,
    FULL_MODEL,
    MODEL_ATTRIBUTES,
    RUNTIME_COMPATIBLE_MODELS,
    RUNTIME_PREFIXES,
    SERVICE_SET_ACTIVATION,
    SERVICE_SET_BATTERY_ALERT,
    SERVICE_SET_BATTERY_TYPE,
    SERVICE_SET_FUEL_ALERT,
    SERVICE_SET_GAUGE_TYPE,
    SERVICE_SET_LOW_FUEL_ALERT,
    SERVICE_SET_NEVIWEB_STATUS,
    SERVICE_SET_REFUEL_ALERT,
    SERVICE_SET_SENSOR_CLOSURE_ACTION,
    SERVICE_SET_SENSOR_LEAK_ALERT,
    SERVICE_SET_SENSOR_TEMP_ALERT,
    SERVICE_SET_TANK_HEIGHT,
    SERVICE_SET_TANK_TYPE,
    SIGNAL_EVENTS_CHANGED,
    STATE_WATER_LEAK,
    TH6_MODES_VALUES,
    VERSION,
)
from .coordinator import Neviweb130Client, Neviweb130Coordinator
from .helpers import (
    async_notify_critical,
    async_notify_once_or_update,
    async_notify_throttled,
    generate_runtime_count_attributes,
    generate_runtime_sensor_descriptions,
    NamingHelper,
    Neviweb130SensorEntityDescription,
)
from .schema import (
    HA_TO_NEVIWEB_GAUGE,
    HA_TO_NEVIWEB_HEIGHT,
    HA_TO_NEVIWEB_LEVEL,
    PREFIX,
    SET_ACTIVATION_SCHEMA,
    SET_BATTERY_ALERT_SCHEMA,
    SET_BATTERY_TYPE_SCHEMA,
    SET_FUEL_ALERT_SCHEMA,
    SET_GAUGE_TYPE_SCHEMA,
    SET_LOW_FUEL_ALERT_SCHEMA,
    SET_NEVIWEB_STATUS_SCHEMA,
    SET_REFUEL_ALERT_SCHEMA,
    SET_SENSOR_CLOSURE_ACTION_SCHEMA,
    SET_SENSOR_LEAK_ALERT_SCHEMA,
    SET_SENSOR_TEMP_ALERT_SCHEMA,
    SET_TANK_HEIGHT_SCHEMA,
    SET_TANK_TYPE_SCHEMA,
)

_LOGGER = logging.getLogger(__name__)

SNOOZE_TIME = 1200

UPDATE_ATTRIBUTES = [ATTR_BATTERY_VOLTAGE, ATTR_BATTERY_STATUS]

IMPLEMENTED_GATEWAY = [130, 3156]
IMPLEMENTED_TANK_MONITOR = [5056]
IMPLEMENTED_LTE_TANK_MONITOR = [5055]
IMPLEMENTED_SENSOR_MODEL = [5051, 5053]
IMPLEMENTED_NEW_SENSOR_MODEL = [4210]
IMPLEMENTED_NEW_CONNECTED_SENSOR = [42102]
IMPLEMENTED_CONNECTED_SENSOR = [5050, 5052]
IMPLEMENTED_DEVICE_MODEL = (
    IMPLEMENTED_SENSOR_MODEL
    + IMPLEMENTED_TANK_MONITOR
    + IMPLEMENTED_LTE_TANK_MONITOR
    + IMPLEMENTED_CONNECTED_SENSOR
    + IMPLEMENTED_GATEWAY
    + IMPLEMENTED_NEW_SENSOR_MODEL
    + IMPLEMENTED_NEW_CONNECTED_SENSOR
)

SENSOR_TYPE: dict[
    str, tuple[str | None, str | None, BinarySensorDeviceClass | SensorStateClass, str | None, StatisticMeanType | None]
] = {
    "leak": (None, None, BinarySensorDeviceClass.MOISTURE, None, None),
    "level": (PERCENTAGE, None, SensorStateClass.MEASUREMENT, "percentage", StatisticMeanType.ARITHMETIC),
    "gateway": (None, None, BinarySensorDeviceClass.CONNECTIVITY, None, None),
}

# Define attributes to be monitored for each device type

SENSOR_TYPES: tuple[Neviweb130SensorEntityDescription, ...] = (
    #  Common attributes
    Neviweb130SensorEntityDescription(
        key="rssi",
        device_class=SensorDeviceClass.SIGNAL_STRENGTH,
        state_class=SensorStateClass.MEASUREMENT,
        translation_key="rssi",
        value_fn=lambda data: data["rssi"],
        signal=SIGNAL_EVENTS_CHANGED,
        native_unit_of_measurement=SIGNAL_STRENGTH_DECIBELS_MILLIWATT,
        unit_class="signal_strength",
        mean_type=StatisticMeanType.ARITHMETIC,
        icon="mdi:wifi",
    ),
    Neviweb130SensorEntityDescription(
        key="total_kwh_count",
        device_class=SensorDeviceClass.ENERGY,
        state_class=SensorStateClass.TOTAL_INCREASING,
        translation_key="total_kwh_count",
        value_fn=lambda data: data["total_kwh_count"],
        signal=SIGNAL_EVENTS_CHANGED,
        native_unit_of_measurement=UnitOfEnergy.KILO_WATT_HOUR,
        unit_class="energy",
        mean_type=StatisticMeanType.ARITHMETIC,
        icon="mdi:lightning-bolt",
    ),
    Neviweb130SensorEntityDescription(
        key="monthly_kwh_count",
        device_class=SensorDeviceClass.ENERGY,
        state_class=SensorStateClass.TOTAL,
        translation_key="monthly_kwh_count",
        value_fn=lambda data: data["monthly_kwh_count"],
        signal=SIGNAL_EVENTS_CHANGED,
        native_unit_of_measurement=UnitOfEnergy.KILO_WATT_HOUR,
        unit_class="energy",
        mean_type=StatisticMeanType.ARITHMETIC,
        icon="mdi:lightning-bolt",
    ),
    Neviweb130SensorEntityDescription(
        key="daily_kwh_count",
        device_class=SensorDeviceClass.ENERGY,
        state_class=SensorStateClass.TOTAL,
        translation_key="daily_kwh_count",
        value_fn=lambda data: data["daily_kwh_count"],
        signal=SIGNAL_EVENTS_CHANGED,
        native_unit_of_measurement=UnitOfEnergy.KILO_WATT_HOUR,
        unit_class="energy",
        mean_type=StatisticMeanType.ARITHMETIC,
        icon="mdi:lightning-bolt",
    ),
    Neviweb130SensorEntityDescription(
        key="hourly_kwh_count",
        device_class=SensorDeviceClass.ENERGY,
        state_class=SensorStateClass.TOTAL,
        translation_key="hourly_kwh_count",
        value_fn=lambda data: data["hourly_kwh_count"],
        signal=SIGNAL_EVENTS_CHANGED,
        native_unit_of_measurement=UnitOfEnergy.KILO_WATT_HOUR,
        unit_class="energy",
        mean_type=StatisticMeanType.ARITHMETIC,
        icon="mdi:lightning-bolt",
    ),
    Neviweb130SensorEntityDescription(
        key="wattage",
        device_class=SensorDeviceClass.ENERGY,
        state_class=SensorStateClass.TOTAL,
        translation_key="wattage",
        value_fn=lambda data: data["wattage"],
        signal=SIGNAL_EVENTS_CHANGED,
        native_unit_of_measurement=UnitOfEnergy.WATT_HOUR,
        unit_class="energy",
        mean_type=StatisticMeanType.ARITHMETIC,
        icon="mdi:lightning-bolt",
    ),
    #  Climate attributes
    Neviweb130SensorEntityDescription(
        key="pi_heating_demand",
        device_class=SensorDeviceClass.POWER_FACTOR,
        state_class=SensorStateClass.MEASUREMENT,
        translation_key="pi_heating_demand",
        value_fn=lambda data: data["pi_heating_demand"],
        signal=SIGNAL_EVENTS_CHANGED,
        native_unit_of_measurement=PERCENTAGE,
        unit_class="percentage",
        mean_type=StatisticMeanType.ARITHMETIC,
        icon="mdi:thermometer",
    ),
    Neviweb130SensorEntityDescription(
        key="current_temperature",
        device_class=SensorDeviceClass.TEMPERATURE,
        state_class=SensorStateClass.MEASUREMENT,
        translation_key="current_temperature",
        value_fn=lambda data: data["current_temperature"],
        signal=SIGNAL_EVENTS_CHANGED,
        native_unit_of_measurement=UnitOfTemperature.CELSIUS,
        unit_class="temperature",
        mean_type=StatisticMeanType.ARITHMETIC,
        icon="mdi:thermometer",
    ),
    #  Valve attributes
    Neviweb130SensorEntityDescription(
        key="total_flow_count",
        device_class=SensorDeviceClass.WATER,
        state_class=SensorStateClass.TOTAL_INCREASING,
        translation_key="total_flow_count",
        value_fn=lambda data: data["total_flow_count"],
        signal=SIGNAL_EVENTS_CHANGED,
        native_unit_of_measurement=UnitOfVolume.LITERS,
        unit_class="volume",
        mean_type=StatisticMeanType.NONE,
        icon="mdi:lightning-bolt",
    ),
    Neviweb130SensorEntityDescription(
        key="monthly_flow_count",
        device_class=SensorDeviceClass.WATER,
        state_class=SensorStateClass.TOTAL,
        translation_key="monthly_flow_count",
        value_fn=lambda data: data["monthly_flow_count"],
        signal=SIGNAL_EVENTS_CHANGED,
        native_unit_of_measurement=UnitOfVolume.LITERS,
        unit_class="volume",
        mean_type=StatisticMeanType.NONE,
        icon="mdi:lightning-bolt",
    ),
    Neviweb130SensorEntityDescription(
        key="daily_flow_count",
        device_class=SensorDeviceClass.WATER,
        state_class=SensorStateClass.TOTAL,
        translation_key="daily_flow_count",
        value_fn=lambda data: data["daily_flow_count"],
        signal=SIGNAL_EVENTS_CHANGED,
        native_unit_of_measurement=UnitOfVolume.LITERS,
        unit_class="volume",
        mean_type=StatisticMeanType.NONE,
        icon="mdi:lightning-bolt",
    ),
    Neviweb130SensorEntityDescription(
        key="hourly_flow_count",
        device_class=SensorDeviceClass.WATER,
        state_class=SensorStateClass.TOTAL,
        translation_key="hourly_flow_count",
        value_fn=lambda data: data["hourly_flow_count"],
        signal=SIGNAL_EVENTS_CHANGED,
        native_unit_of_measurement=UnitOfVolume.LITERS,
        unit_class="volume",
        mean_type=StatisticMeanType.NONE,
        icon="mdi:lightning-bolt",
    ),
    #  Real sensor attributes
    Neviweb130SensorEntityDescription(
        key="gauge_angle",
        device_class=None,
        state_class=SensorStateClass.MEASUREMENT_ANGLE,
        translation_key="gauge_angle",
        value_fn=lambda data: data["gauge_angle"],
        signal=SIGNAL_EVENTS_CHANGED,
        native_unit_of_measurement="°",
        unit_class="angle",
        mean_type=StatisticMeanType.ARITHMETIC,
        entity_category=EntityCategory.DIAGNOSTIC,
        icon="mdi:gauge",
    ),
    #  Switch attributes
    Neviweb130SensorEntityDescription(
        key="room_humidity",
        device_class=SensorDeviceClass.HUMIDITY,
        state_class="measurement",
        translation_key="humidity",
        value_fn=lambda data: data["room_humidity"],
        signal=SIGNAL_EVENTS_CHANGED,
        native_unit_of_measurement=PERCENTAGE,
        entity_category=EntityCategory.DIAGNOSTIC,
        unit_class="humidity",
        mean_type=StatisticMeanType.ARITHMETIC,
        icon="mdi:water-percent",
    ),
)

# Add runtime-generated sensor descriptions
for prefix in RUNTIME_PREFIXES:
    runtime_desc = generate_runtime_sensor_descriptions(TH6_MODES_VALUES, prefix)
    SENSOR_TYPES = (*SENSOR_TYPES, *runtime_desc)


def get_attributes_for_model(model):
    return MODEL_ATTRIBUTES.get(model, {}).get("sensor", [])


def determine_device_type(model):
    if model in IMPLEMENTED_SENSOR_MODEL or model in IMPLEMENTED_NEW_SENSOR_MODEL:
        return "leak"
    elif model in IMPLEMENTED_TANK_MONITOR or model in IMPLEMENTED_LTE_TANK_MONITOR:
        return "level"
    elif model in IMPLEMENTED_CONNECTED_SENSOR or model in IMPLEMENTED_NEW_CONNECTED_SENSOR:
        return "leak"
    return "gateway"


def get_sensor_class(model):
    if model in IMPLEMENTED_SENSOR_MODEL or model in IMPLEMENTED_NEW_SENSOR_MODEL:
        return Neviweb130Sensor
    elif model in IMPLEMENTED_CONNECTED_SENSOR or model in IMPLEMENTED_NEW_CONNECTED_SENSOR:
        return Neviweb130ConnectedSensor
    elif model in IMPLEMENTED_TANK_MONITOR or model in IMPLEMENTED_LTE_TANK_MONITOR:
        return Neviweb130TankSensor
    elif model in IMPLEMENTED_GATEWAY:
        return Neviweb130GatewaySensor
    return None


# TH6xxxWF group
for model in RUNTIME_COMPATIBLE_MODELS["TH6"]:
    if model in MODEL_ATTRIBUTES:
        for prefix in RUNTIME_PREFIXES:
            attrs = generate_runtime_count_attributes(TH6_MODES_VALUES, prefix)
            MODEL_ATTRIBUTES[model]["sensor"].extend(
                a for a in attrs if a not in MODEL_ATTRIBUTES[model]["sensor"]
            )


def create_physical_sensors(data, coordinator):
    entities: list[Neviweb130Sensor] = []

    config_prefix = data["prefix"]
    platform = __name__.split(".")[-1] # "sensor"
    naming = NamingHelper(domain=DOMAIN, prefix=config_prefix)

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
            device_name = naming.device_name(platform, index, device_info)
            device_type = determine_device_type(model)

            device_class = get_sensor_class(model)
            if device_class:
                if device_class == Neviweb130GatewaySensor:
                    device = device_class(
                        data,
                        device_info,
                        device_name,
                        device_type,
                        device_info["sku"],
                        "{major}.{middle}.{minor}".format(**device_info["signature"]["softVersion"]),
                        device_info["location$id"],
                        coordinator,
                        entry,
                    )
                else:
                    device = device_class(
                        data,
                        device_info,
                        device_name,
                        device_type,
                        device_info["sku"],
                        "{major}.{middle}.{minor}".format(**device_info["signature"]["softVersion"]),
                        coordinator,
                        entry,
                    )

                _LOGGER.warning("Device registered = %s", device_info["id"])
                entities.append(device)
                coordinator.register_device(device)

    return entities


def create_attribute_sensors(hass, entry, data, coordinator, device_registry):
    entities: list[Neviweb130Sensor] = []

    _LOGGER.debug("Keys dans coordinator.data : %s", list(coordinator.data.keys()))

    config_prefix = data["prefix"]
    platform = __name__.split(".")[-1] # "sensor"
    naming = NamingHelper(domain=DOMAIN, prefix=config_prefix)

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
            if model not in FULL_MODEL:  # ALL_MODEL
                continue

            device_id = str(device_info["id"])
            if device_id not in coordinator.data:
                _LOGGER.warning("Device %s pas encore dans coordinator.data", device_id)

#            device_name = f"{default_name} {device_info['name']}"
            device_name = naming.device_name(platform, index, device_info)
            device_entry = device_registry.async_get_or_create(
                config_entry_id=entry.entry_id,
                identifiers={(DOMAIN, str(device_info["id"]))},
                name=device_name,
                manufacturer="claudegel",
                model=model,
                sw_version="{major}.{middle}.{minor}".format(**device_info["signature"]["softVersion"]),
            )

            attributes_name = get_attributes_for_model(model)
            for attribute in attributes_name:
                for desc in SENSOR_TYPES:
                    if desc.key == attribute:
                        entities.append(
                            Neviweb130DeviceAttributeSensor(
                                client=data["neviweb130_client"],
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
    """Set up the Neviweb sensor."""
    data = hass.data[DOMAIN][entry.entry_id]
    # data["scan_interval"]
    # data["notify"]

    if "neviweb130_client" not in data:
        _LOGGER.error("Neviweb130 client initialization failed.")
        return

    coordinator = hass.data[DOMAIN][entry.entry_id]["coordinator"]

    device_registry = dr.async_get(hass)

    entities: list[Neviweb130Sensor] = []

    #  Add sensors
    entities += create_physical_sensors(data, coordinator)
    await coordinator.async_config_entry_first_refresh()

    if not coordinator.data:
        _LOGGER.debug("Pas de coordinator")
        await coordinator.async_config_entry_first_refresh()

    #  Add attribute sensors for each device type
    entities += create_attribute_sensors(hass, entry, data, coordinator, device_registry)

    # Add daily request counter sensor
    counter = data["counter"]
    entities.append(Neviweb130DailyRequestSensor(hass, counter, entry))

    async_add_entities(entities)
    hass.async_create_task(coordinator.async_request_refresh())

    entity_map: dict[str, Neviweb130Sensor] | None = None
    _entity_map_lock = Lock()

    def get_sensor(service: ServiceCall) -> Neviweb130Sensor:
        entity_id = service.data.get(ATTR_ENTITY_ID)
        if entity_id is None:
            raise ServiceValidationError(f"Missing required parameter: {ATTR_ENTITY_ID}")

        nonlocal entity_map
        if entity_map is None:
            with _entity_map_lock:
                if entity_map is None:
                    entity_map = {entity.entity_id: entity for entity in entities if entity.entity_id is not None}
                    if len(entity_map) != len(entities):
                        entity_map = None
                        raise ServiceValidationError("Entities not finished loading, try again shortly")

        sensor = entity_map.get(entity_id)
        if sensor is None:
            raise ServiceValidationError(f"Entity {entity_id} must be a {DOMAIN} sensor")
        return sensor

    async def set_sensor_leak_alert_service(service: ServiceCall) -> None:
        """Set water leak sensor leak alert action."""
        sensor = get_sensor(service)
        value = {"id": sensor.unique_id, "leak": service.data[ATTR_LEAK_ALERT]}
        await sensor.async_set_sensor_leak_alert(value)
        sensor.async_schedule_update_ha_state(True)
        hass.async_create_task(coordinator.async_request_refresh())

    async def set_sensor_temp_alert_service(service: ServiceCall) -> None:
        """Set water leak sensor low temperature alert action."""
        sensor = get_sensor(service)
        value = {"id": sensor.unique_id, "temp": service.data[ATTR_TEMP_ALERT]}
        await sensor.async_set_sensor_temp_alert(value)
        sensor.async_schedule_update_ha_state(True)
        hass.async_create_task(coordinator.async_request_refresh())

    async def set_sensor_closure_action_service(service: ServiceCall) -> None:
        """Set water leak sensor connected to Sedna valve closure action in case of leak alert."""
        sensor = get_sensor(service)
        value = {"id": sensor.unique_id, "close": service.data[ATTR_CONF_CLOSURE]}
        await sensor.async_set_sensor_closure_action(value)
        sensor.async_schedule_update_ha_state(True)
        hass.async_create_task(coordinator.async_request_refresh())

    async def set_battery_type_service(service: ServiceCall) -> None:
        """Set battery type for water leak sensor."""
        sensor = get_sensor(service)
        value = {"id": sensor.unique_id, "type": service.data[ATTR_BATTERY_TYPE]}
        await sensor.async_set_battery_type(value)
        sensor.async_schedule_update_ha_state(True)
        hass.async_create_task(coordinator.async_request_refresh())

    async def set_tank_type_service(service: ServiceCall) -> None:
        """Set tank type for fuel tank."""
        sensor = get_sensor(service)
        if not isinstance(sensor, Neviweb130TankSensor):
            raise ServiceValidationError(f"Entity {sensor.entity_id} cannot be used with this service")
        value = {"id": sensor.unique_id, "type": service.data[ATTR_TANK_TYPE]}
        await sensor.async_set_tank_type(value)
        sensor.async_schedule_update_ha_state(True)
        hass.async_create_task(coordinator.async_request_refresh())

    async def set_gauge_type_service(service: ServiceCall) -> None:
        """Set gauge type for propane tank."""
        sensor = get_sensor(service)
        if not isinstance(sensor, Neviweb130TankSensor):
            raise ServiceValidationError(f"Entity {sensor.entity_id} must be a {DOMAIN} tank sensor")
        value = {"id": sensor.unique_id, "gauge": service.data[ATTR_GAUGE_TYPE]}
        await sensor.async_set_gauge_type(value)
        sensor.async_schedule_update_ha_state(True)
        hass.async_create_task(coordinator.async_request_refresh())

    async def set_low_fuel_alert_service(service: ServiceCall) -> None:
        """Set low fuel alert on tank, propane or oil."""
        sensor = get_sensor(service)
        if not isinstance(sensor, Neviweb130TankSensor):
            raise ServiceValidationError(f"Entity {sensor.entity_id} must be a {DOMAIN} tank sensor")
        value = {"id": sensor.unique_id,"low": service.data[ATTR_FUEL_PERCENT_ALERT]}
        await sensor.async_set_low_fuel_alert(value)
        sensor.async_schedule_update_ha_state(True)
        hass.async_create_task(coordinator.async_request_refresh())

    async def set_tank_height_service(service: ServiceCall) -> None:
        """Set tank height for oil tank."""
        sensor = get_sensor(service)
        if not isinstance(sensor, Neviweb130TankSensor):
            raise ServiceValidationError(f"Entity {sensor.entity_id} is not a Neviweb130TankSensor")
        value = {"id": sensor.unique_id, "height": service.data[ATTR_TANK_HEIGHT]}
        await sensor.async_set_tank_height(value)
        sensor.async_schedule_update_ha_state(True)
        hass.async_create_task(coordinator.async_request_refresh())

    async def set_fuel_alert_service(service: ServiceCall) -> None:
        """Set fuel alert for LM4110-ZB."""
        sensor = get_sensor(service)
        if not isinstance(sensor, Neviweb130TankSensor):
            raise ServiceValidationError(f"Entity {sensor.entity_id} is not a Neviweb130TankSensor")
        value = {"id": sensor.unique_id, "fuel": service.data[ATTR_FUEL_ALERT]}
        await sensor.async_set_fuel_alert(value)
        sensor.async_schedule_update_ha_state(True)
        hass.async_create_task(coordinator.async_request_refresh())

    async def set_refuel_alert_service(service: ServiceCall) -> None:
        """Set refuel alert for LM4110-ZB."""
        sensor = get_sensor(service)
        if not isinstance(sensor, Neviweb130TankSensor):
            raise ServiceValidationError(f"Entity {sensor.entity_id} is not a Neviweb130TankSensor")
        value = {"id": sensor.unique_id, "refuel": service.data[ATTR_REFUEL]}
        await sensor.set_refuel_alert(value)
        sensor.async_schedule_update_ha_state(True)
        hass.async_create_task(coordinator.async_request_refresh())

    async def set_battery_alert_service(service: ServiceCall) -> None:
        """Set battery alert for LM4110-ZB."""
        sensor = get_sensor(service)
        if not isinstance(sensor, Neviweb130TankSensor):
            raise ServiceValidationError(f"Entity {sensor.entity_id} is not a Neviweb130TankSensor")
        value = {"id": sensor.unique_id, "batt": service.data[ATTR_BATT_ALERT]}
        await sensor.async_set_battery_alert(value)
        sensor.async_schedule_update_ha_state(True)
        hass.async_create_task(coordinator.async_request_refresh())

    async def set_activation_service(service: ServiceCall) -> None:
        """Activate or deactivate Neviweb polling for missing device."""
        sensor = get_sensor(service)
        value = {"id": sensor.unique_id, "active": service.data[ATTR_ACTIVE]}
        await sensor.async_set_activation(value)
        sensor.async_schedule_update_ha_state(True)
        hass.async_create_task(coordinator.async_request_refresh())

    async def set_neviweb_status_service(service: ServiceCall) -> None:
        """Set Neviweb global status, home or away."""
        sensor = get_sensor(service)
        value = {"id": sensor.unique_id, "mode": service.data[ATTR_MODE]}
        await sensor.async_set_neviweb_status(value)
        sensor.async_schedule_update_ha_state(True)
        hass.async_create_task(coordinator.async_request_refresh())

    hass.services.async_register(
        DOMAIN,
        SERVICE_SET_SENSOR_LEAK_ALERT,
        set_sensor_leak_alert_service,
        schema=SET_SENSOR_LEAK_ALERT_SCHEMA,
    )

    hass.services.async_register(
        DOMAIN,
        SERVICE_SET_SENSOR_TEMP_ALERT,
        set_sensor_temp_alert_service,
        schema=SET_SENSOR_TEMP_ALERT_SCHEMA,
    )

    hass.services.async_register(
        DOMAIN,
        SERVICE_SET_SENSOR_CLOSURE_ACTION,
        set_sensor_closure_action_service,
        schema=SET_SENSOR_CLOSURE_ACTION_SCHEMA,
    )

    hass.services.async_register(
        DOMAIN,
        SERVICE_SET_BATTERY_TYPE,
        set_battery_type_service,
        schema=SET_BATTERY_TYPE_SCHEMA,
    )

    hass.services.async_register(
        DOMAIN,
        SERVICE_SET_TANK_TYPE,
        set_tank_type_service,
        schema=SET_TANK_TYPE_SCHEMA,
    )

    hass.services.async_register(
        DOMAIN,
        SERVICE_SET_GAUGE_TYPE,
        set_gauge_type_service,
        schema=SET_GAUGE_TYPE_SCHEMA,
    )

    hass.services.async_register(
        DOMAIN,
        SERVICE_SET_LOW_FUEL_ALERT,
        set_low_fuel_alert_service,
        schema=SET_LOW_FUEL_ALERT_SCHEMA,
    )

    hass.services.async_register(
        DOMAIN,
        SERVICE_SET_TANK_HEIGHT,
        set_tank_height_service,
        schema=SET_TANK_HEIGHT_SCHEMA,
    )

    hass.services.async_register(
        DOMAIN,
        SERVICE_SET_FUEL_ALERT,
        set_fuel_alert_service,
        schema=SET_FUEL_ALERT_SCHEMA,
    )

    hass.services.async_register(
        DOMAIN,
        SERVICE_SET_REFUEL_ALERT,
        set_refuel_alert_service,
        schema=SET_REFUEL_ALERT_SCHEMA,
    )

    hass.services.async_register(
        DOMAIN,
        SERVICE_SET_BATTERY_ALERT,
        set_battery_alert_service,
        schema=SET_BATTERY_ALERT_SCHEMA,
    )

    hass.services.async_register(
        DOMAIN,
        SERVICE_SET_ACTIVATION,
        set_activation_service,
        schema=SET_ACTIVATION_SCHEMA,
    )

    hass.services.async_register(
        DOMAIN,
        SERVICE_SET_NEVIWEB_STATUS,
        set_neviweb_status_service,
        schema=SET_NEVIWEB_STATUS_SCHEMA,
    )


def neviweb_to_ha_gauge(value):
    keys = [k for k, v in HA_TO_NEVIWEB_GAUGE.items() if v == value]
    if keys:
        return keys[0]
    return None


def neviweb_to_ha_level(value):
    keys = [k for k, v in HA_TO_NEVIWEB_LEVEL.items() if v == value]
    if keys:
        return keys[0]
    return None


def voltage_to_percentage(voltage, type_val):
    """Convert voltage level from volt to percentage."""
    if type_val == "alkaline":
        return int((min(voltage, 3.0) - 2.0) / (3.0 - 2.0) * 100)
    else:
        return int((min(voltage, 3.0) - 2.2) / (3.0 - 2.2) * 100)


def neviweb_to_ha_height(value):
    keys = [k for k, v in HA_TO_NEVIWEB_HEIGHT.items() if v == value]
    if keys:
        return keys[0]
    return None


def convert(sampling):
    sample = str(sampling)
    date = datetime.datetime.fromtimestamp(int(sample[0:-3]))
    return date


def convert_to_percent(angle, low, high):
    x = angle
    x_min = 110
    if low == 5:
        x_max = 415
        delta = 55
    else:
        x_max = 406
        delta = 46
    if delta <= x <= 70:
        x = delta
    if 0 <= x <= delta:
        x = x + 360
    y = (x - x_min) / (x_max - x_min)
    lower_limit = low
    upper_limit = high
    value_range = upper_limit - lower_limit
    pct = y * value_range + lower_limit
    return round(pct)


class Neviweb130Sensor(CoordinatorEntity, SensorEntity):
    """Implementation of a Neviweb sensor connected to GT130."""

    def __init__(self, data, device_info, name, device_type, sku, firmware, coordinator, entry):
        """Initialize."""
        super().__init__(coordinator)
        _LOGGER.debug("Setting up %s: %s", self._name, device_info)
        self._device = device_info
        self._name = name
        self._sku = sku
        self._firmware = firmware
        self._client = data["neviweb130_client"]
        self._notify = data["notify"]
        self._prefix = data["prefix"]
        self._entry = entry
        self._id = str(device_info["id"])
        self._device_model = device_info["signature"]["model"]
        self._device_model_cfg = device_info["signature"]["modelCfg"]
        self._hard_rev = device_info["signature"]["hardRev"]
        self._identifier = device_info["identifier"]
        self._device_type = device_type
        self._is_leak = (
            device_info["signature"]["model"] in IMPLEMENTED_SENSOR_MODEL
            or device_info["signature"]["model"] in IMPLEMENTED_NEW_SENSOR_MODEL
        )
        self._is_connected = device_info["signature"]["model"] in IMPLEMENTED_CONNECTED_SENSOR
        self._is_new_connected = device_info["signature"]["model"] in IMPLEMENTED_NEW_CONNECTED_SENSOR
        self._is_new_leak = (
            device_info["signature"]["model"] in IMPLEMENTED_NEW_SENSOR_MODEL
            or device_info["signature"]["model"] in IMPLEMENTED_NEW_CONNECTED_SENSOR
        )
        self._is_lte_monitor = device_info["signature"]["model"] in IMPLEMENTED_LTE_TANK_MONITOR
        self._is_monitor = device_info["signature"]["model"] in IMPLEMENTED_TANK_MONITOR
        self._is_gateway = device_info["signature"]["model"] in IMPLEMENTED_GATEWAY
        self._active: bool = True
        self._angle: int | None = None
        self._batt_percent_normal = None
        self._batt_status_normal = None
        self._battery_alert: bool | None = None
        self._battery_status = None
        self._battery_type: str = "alkaline"
        self._battery_voltage = None
        self._closure_action: str | None = None
        self._cur_temp = None
        self._error_code = None
        self._fuel_alert: bool | None = None
        self._fuel_percent_alert: str | None = None
        self._gauge_type: str | None = None
        self._leak_alert: bool | None = None
        self._leak_status: str = ""
        self._rssi = None
        self._sampling = None
        self._sensor_type = None
        self._snooze: float = 0.0
        self._tank_height: str | None = None
        self._tank_percent: str = ""
        self._tank_type: str | None = None
        self._temp_alert: bool | None = None
        self._temp_status = None

        self._attr_device_info = DeviceInfo(
            identifiers={(DOMAIN, self._id)},
            name=f"{self._prefix} {self._name}" if self._prefix else self._name,
            manufacturer="claudegel",
            model=self._device_model,
            sw_version=self._firmware,
            hw_version=self._hard_rev,
            serial_number=self._identifier,
            configuration_url="https://www.sinopetech.com/support",
        )

    async def async_update(self) -> None:
        if self._active:
            if self._is_leak:
                LEAK_ATTRIBUTE = [
                    ATTR_WATER_LEAK_STATUS,
                    ATTR_ROOM_TEMPERATURE,
                    ATTR_ROOM_TEMP_ALARM,
                    ATTR_LEAK_ALERT,
                    ATTR_BATTERY_TYPE,
                    ATTR_BATT_ALERT,
                    ATTR_TEMP_ALERT,
                    ATTR_RSSI,
                    ATTR_BATT_PERCENT_NORMAL,
                    ATTR_BATT_STATUS_NORMAL,
                ]
            else:
                LEAK_ATTRIBUTE = []
            if self._is_new_leak:
                NEW_LEAK_ATTRIBUTE = [ATTR_ERROR_CODE_SET1, ATTR_SENSOR_TYPE]
            else:
                NEW_LEAK_ATTRIBUTE = []

            """Get the latest data from Neviweb and update the state."""
            start = time.time()
            device_data: dict[str, Any] = await self._client.async_get_device_attributes(
                self._id,
                UPDATE_ATTRIBUTES + LEAK_ATTRIBUTE + NEW_LEAK_ATTRIBUTE,
            )
            # device_daily_stats = await self._client.async_get_device_daily_stats(self._id)
            end = time.time()
            elapsed = round(end - start, 3)
            _LOGGER.debug("Updating %s (%s sec): %s", self._name, elapsed, device_data)

            if "error" not in device_data or device_data is not None:
                if "errorCode" not in device_data:
                    if self._is_leak or self._is_new_leak:
                        if device_data[ATTR_WATER_LEAK_STATUS] == "probe":
                            await async_notify_critical(
                                self.hass,
                                f"Warning: Neviweb Device error detected: {device_data[ATTR_WATER_LEAK_STATUS]} "
                                f"for device: {self._name}, id: {self._id}, Sku: {self._sku}, Leak sensor disconnected",
                                title=f"Neviweb130 integration {VERSION}",
                                notification_id="neviweb130_error_code",
                            )
                            self._leak_status = device_data[ATTR_WATER_LEAK_STATUS]
                        else:
                            self._leak_status = (
                                STATE_WATER_LEAK if device_data[ATTR_WATER_LEAK_STATUS] == STATE_WATER_LEAK else "ok"
                            )
                        self._cur_temp = device_data[ATTR_ROOM_TEMPERATURE]
                        self._leak_alert = device_data[ATTR_LEAK_ALERT]
                        self._temp_status = device_data[ATTR_ROOM_TEMP_ALARM]
                        self._temp_alert = device_data[ATTR_TEMP_ALERT]
                        self._battery_alert = device_data[ATTR_BATT_ALERT]
                        if ATTR_BATTERY_STATUS in device_data:
                            self._battery_status = device_data[ATTR_BATTERY_STATUS]
                            self._battery_type = device_data[ATTR_BATTERY_TYPE]
                        if ATTR_BATT_PERCENT_NORMAL in device_data:
                            self._batt_percent_normal = device_data[ATTR_BATT_PERCENT_NORMAL]
                            self._batt_status_normal = device_data[ATTR_BATT_STATUS_NORMAL]
                        if self._is_new_leak:
                            if ATTR_ERROR_CODE_SET1 in device_data and len(device_data[ATTR_ERROR_CODE_SET1]) > 0:
                                if device_data[ATTR_ERROR_CODE_SET1]["raw"] != 0:
                                    self._error_code = device_data[ATTR_ERROR_CODE_SET1]["raw"]
                                    await async_notify_critical(
                                        self.hass,
                                        "Warning: Neviweb Device error code detected: "
                                        + str(device_data[ATTR_ERROR_CODE_SET1]["raw"])
                                        + " for device: "
                                        + self._name
                                        + ", Sku: "
                                        + self._sku,
                                        title=f"Neviweb130 integration {VERSION}",
                                        notification_id="neviweb130_error_code",
                                    )
                            if ATTR_SENSOR_TYPE in device_data:
                                self._sensor_type = device_data[ATTR_SENSOR_TYPE]
                        self._battery_voltage = device_data[ATTR_BATTERY_VOLTAGE]
                        if ATTR_RSSI in device_data:
                            self._rssi = device_data[ATTR_RSSI]
                    self.async_write_ha_state()
                    return
                _LOGGER.warning("Error in reading device %s: (%s)", self._name, device_data)
                return
            elif device_data is not None:
                await self.async_log_error(device_data["error"]["code"])
        else:
            if time.time() - self._snooze > SNOOZE_TIME:
                self._active = True
                if self._notify == "notification" or self._notify == "both":
                    await async_notify_once_or_update(
                        self.hass,
                        "Warning: Neviweb Device update restarted for " + self._name + ", Sku: " + self._sku,
                        title=f"Neviweb130 integration {VERSION}",
                        notification_id=f"neviweb130_update_restarted",
                    )

    @property
    @override
    def unique_id(self) -> str:
        """Return unique ID based on Neviweb device ID."""
        return f"{self._entry.entry_id}_{self._id}"

    @property
    @override
    def id(self) -> str:
        """Alias for DataUpdateCoordinator."""
        return self._id

    @property
    @override
    def name(self):
        """Return the name of the sensor."""
        if self._prefix:
            return f"{self._prefix} {self._name}"
        return self._name

    @property
    @override
    def icon(self) -> str | None:
        """Return the icon to use in the frontend."""
        device_info = SENSOR_TYPE.get(self._device_type)
        if device_info is None:
            return None

        return device_info[1]

    @property
    @override
    def unit_of_measurement(self) -> str | None:
        """Return the unit of measurement of this entity, if any."""
        device_info = SENSOR_TYPE.get(self._device_type)
        if device_info is None:
            return None

        return device_info[0]

    @property
    def unit_class(self) -> str | None:
        device_info = SENSOR_TYPE.get(self._device_type)
        return device_info[3] if device_info else None

    @property
    def statistic_mean_type(self) -> StatisticMeanType | None:
        device_info = SENSOR_TYPE.get(self._device_type)
        return device_info[4] if device_info else None

    @property
    @override
    def device_class(self) -> BinarySensorDeviceClass | SensorStateClass | None:
        """Return the device class of this entity."""
        device_info = SENSOR_TYPE.get(self._device_type)
        if device_info is None:
            return None

        return device_info[2]

    @property
    def current_temperature(self):
        """Return the current sensor temperature."""
        return self._cur_temp

    @property
    def leak_status(self):
        """Return current sensor leak status: 'water' or 'ok'."""
        return self._leak_status is not None

    @property
    def rssi(self):
        if self._rssi is not None:
            return self._rssi
        return None

    @property
    def activation(self) -> bool | None:
        return bool(self._active)

    @property
    def leak_alert(self) -> bool | None:
        return self._leak_alert

    @property
    def temp_alert(self) -> bool | None:
        return self._temp_alert

    @property
    def batt_alert(self) -> bool | None:
        return self._battery_alert

    @property
    def batt_type(self) -> str | None:
        return self._battery_type

    @property
    def action_close(self) -> str | None:
        return self._closure_action

    @property
    def tank_type(self) -> str | None:
        return self._tank_type

    @property
    def tank_height(self) -> str | None:
        return self._tank_height

    @property
    def gauge_type(self) -> str | None:
        return self._gauge_type

    @property
    def sensor_type(self) -> str | None:
        """Define which sensor is attached to device."""
        return self._sensor_type

    @property
    @override
    def extra_state_attributes(self)  -> Mapping[str, Any]:
        """Return the state attributes."""
        data = {}
        data.update(
            {
                "leak_status": self._leak_status,
                "temperature": self._cur_temp,
                "temp_alarm": self._temp_status,
                "temperature_alert": self._temp_alert,
                "leak_alert": self._leak_alert,
                "battery_level": voltage_to_percentage(self._battery_voltage, self._battery_type),
                "battery_voltage": self._battery_voltage,
                "battery_status": self._battery_status,
                "battery_percent_normalized": self._batt_percent_normal,
                "battery_status_normalized": self._batt_status_normal,
                "battery_alert": self._battery_alert,
                "battery_type": self._battery_type,
                "rssi": self._rssi,
            }
        )
        if self._is_new_leak:
            data.update(
                {
                    "error_code": self._error_code,
                    "sensor_type": self._sensor_type,
                }
            )
        data.update(
            {
                "sku": self._sku,
                "device_model": str(self._device_model),
                "device_model_cfg": self._device_model_cfg,
                "firmware": self._firmware,
                "activation": "Active" if self._active else "Inactive",
                "device_type": self._device_type,
                "id": self._id,
            }
        )
        return data

    @property
    def battery_voltage(self):
        """Return the current battery voltage of the sensor in %."""
        return voltage_to_percentage(self._battery_voltage, self._battery_type)

    @property
    def battery_status(self):
        """Return the current battery status."""
        return self._battery_status

    @property
    @override
    def native_value(self) -> str:
        """Return the state of the sensor."""
        return self._leak_status

    async def async_set_sensor_leak_alert(self, value):
        """Set water leak sensor leak alert action."""
        await self._client.async_set_sensor_leak_alert(value["id"], value["leak"])
        self._leak_alert = value["leak"]

    async def async_set_sensor_temp_alert(self, value):
        """Set water leak sensor low temperature alert action."""
        await self._client.async_set_sensor_temp_alert(value["id"], value["temp"])
        self._temp_alert = value["temp"]

    async def async_set_sensor_closure_action(self, value):
        """Set water leak sensor connected to Sedna valve closure action in case of leak alert."""
        await self._client.async_set_sensor_closure_action(value["id"], value["close"])
        self._closure_action = value["close"]

    async def async_set_battery_alert(self, value):
        """Set low battery alert LM4110-ZB sensor."""
        await self._client.async_set_battery_alert(value["id"], value["batt"])
        self._battery_alert = value["batt"]

    async def async_set_battery_type(self, value):
        """Set battery type, alkaline or lithium for water leak sensor."""
        await self._client.async_set_battery_type(value["id"], value["type"])
        self._battery_type = value["type"]

    async def async_set_activation(self, value):
        """Activate (True) or deactivate (False) Neviweb polling for a missing device."""
        self._active = value["active"]

    async def async_log_error(self, error_data):
        """Send error message to LOG."""
        if error_data == "USRSESSEXP":
            _LOGGER.warning("Session expired... Reconnecting...")
            if self._notify == "notification" or self._notify == "both":
                await async_notify_once_or_update(
                    self.hass,
                    "Warning: Got USRSESSEXP error, Neviweb session expired. "
                    + "Set your scan_interval parameter to less than 10 "
                    + "minutes to avoid this... Reconnecting...",
                    title=f"Neviweb130 integration {VERSION}",
                    notification_id="neviweb130_reconnect",
                )
            await self._client.async_reconnect()
        elif error_data == "ACCDAYREQMAX":
            _LOGGER.warning("Maximum daily request reached... Reduce polling frequency")
        elif error_data == "TimeoutError":
            _LOGGER.warning("Timeout error detected... Retry later")
        elif error_data == "MAINTENANCE":
            _LOGGER.warning("Access blocked for maintenance... Retry later")
            await async_notify_once_or_update(
                self.hass,
                "Warning: Neviweb access temporary blocked for maintenance... Retry later",
                title=f"Neviweb130 integration {VERSION}",
                notification_id="neviweb130_access_error",
            )
            await self._client.async_reconnect()
        elif error_data == "ACCSESSEXC":
            await async_notify_critical(
                self.hass,
                "Warning: Maximum Neviweb session number reached... Close other connections and try again",
                title=f"Neviweb130 integration {VERSION}",
                notification_id="neviweb130_session_error",
            )
            await self._client.async_reconnect()
        elif error_data == "DVCATTRNSPTD":
            _LOGGER.warning(
                "Device attribute not supported for %s (id: %s): %s...(SKU: %s)",
                self._name,
                self._id,
                error_data,
                self._sku,
            )
        elif error_data == "DVCACTNSPTD":
            _LOGGER.warning(
                "Device action not supported for %s (id: %s)... (SKU: %s). Report to maintainer",
                self._name,
                self._id,
                self._sku,
            )
        elif error_data == "DVCCOMMTO":
            _LOGGER.warning(
                "Device Communication Timeout for %s (id: %s)... The device "
                + "did not respond to the server within the prescribed delay"
                + " (SKU: %s)",
                self._name,
                self._id,
                self._sku,
            )
        elif error_data == "SVCERR":
            _LOGGER.warning(
                "Service error, device not available retry later %s (id: %s): %s...(SKU: %s)",
                self._name,
                self._id,
                error_data,
                self._sku,
            )
        elif error_data == "DVCBUSY":
            _LOGGER.warning(
                "Device busy can't reach (neviweb update ?), retry later %s (id: %s): %s...(SKU: %s)",
                self._name,
                self._id,
                error_data,
                self._sku,
            )
        elif error_data == "DVCUNVLB":
            if self._notify == "logging" or self._notify == "both":
                _LOGGER.warning(
                    "Device %s (id: %s) is disconnected from Neviweb: %s... (SKU: %s)",
                    self._name,
                    self._id,
                    error_data,
                    self._sku,
                )
                _LOGGER.warning(
                    "This device %s is de-activated and won't be updated for 20 minutes",
                    self._name,
                )
                _LOGGER.warning(
                    "You can re-activate device %s with "
                    + "service.neviweb130_set_activation or wait 20 minutes "
                    + "for update to restart or just restart HA",
                    self._name,
                )
            if self._notify == "notification" or self._notify == "both":
                await async_notify_once_or_update(
                    self.hass,
                    "Warning: Received message from Neviweb, device "
                    + "disconnected... Check your log... Neviweb update will "
                    + "be halted for 20 minutes for "
                    + self._name
                    + ", id: "
                    + self._id
                    + ", Sku: "
                    + self._sku,
                    title=f"Neviweb130 integration {VERSION}",
                    notification_id="neviweb130_device_error",
                )
            self._active = False
            self._snooze = time.time()
        else:
            _LOGGER.warning(
                "Unknown error for %s (id: %s): %s...(SKU: %s) Report to maintainer",
                self._name,
                self._id,
                error_data,
                self._sku,
            )


class Neviweb130ConnectedSensor(Neviweb130Sensor):
    """Implementation of a Neviweb sensor connected to Sedna valve."""

    @override
    async def async_update(self) -> None:
        if self._active:
            if self._is_connected or self._is_new_connected:
                LEAK_ATTRIBUTE = [
                    ATTR_WATER_LEAK_STATUS,
                    ATTR_ROOM_TEMPERATURE,
                    ATTR_ROOM_TEMP_ALARM,
                    ATTR_BATTERY_TYPE,
                    ATTR_BATT_ALERT,
                    ATTR_TEMP_ALERT,
                    ATTR_BATT_PERCENT_NORMAL,
                    ATTR_BATT_STATUS_NORMAL,
                    ATTR_CONF_CLOSURE,
                ]
            else:
                LEAK_ATTRIBUTE = []
            if self._is_new_connected:
                NEW_LEAK_ATTRIBUTE = [ATTR_SENSOR_TYPE]
            else:
                NEW_LEAK_ATTRIBUTE = []

            """Get the latest data from Neviweb and update the state."""
            start = time.time()
            _LOGGER.debug(
                "Updated attributes for %s: %s",
                self._name,
                UPDATE_ATTRIBUTES + LEAK_ATTRIBUTE + NEW_LEAK_ATTRIBUTE,
            )
            device_data = await self._client.async_get_device_attributes(
                self._id,
                UPDATE_ATTRIBUTES + LEAK_ATTRIBUTE + NEW_LEAK_ATTRIBUTE,
            )
            #            device_daily_stats = await self._client.async_get_device_daily_stats(self._id)
            end = time.time()
            elapsed = round(end - start, 3)
            _LOGGER.debug("Updating %s (%s sec): %s", self._name, elapsed, device_data)

            if "error" not in device_data or device_data is not None:
                if "errorCode" not in device_data:
                    if self._is_connected or self._is_new_connected:
                        if device_data[ATTR_WATER_LEAK_STATUS] == "probe":
                            await async_notify_critical(
                                self.hass,
                                f"Warning: Neviweb Device error detected: {device_data[ATTR_WATER_LEAK_STATUS]} "
                                f"for device: {self._name}, id: {self._id}, Sku: {self._sku}, Leak sensor disconnected",
                                title=f"Neviweb130 integration {VERSION}",
                                notification_id=f"neviweb130_sensor_error",
                            )
                            self._leak_status = device_data[ATTR_WATER_LEAK_STATUS]
                        else:
                            self._leak_status = (
                                STATE_WATER_LEAK if device_data[ATTR_WATER_LEAK_STATUS] == STATE_WATER_LEAK else "ok"
                            )
                        self._cur_temp = device_data[ATTR_ROOM_TEMPERATURE]
                        self._temp_status = device_data[ATTR_ROOM_TEMP_ALARM]
                        if ATTR_TEMP_ALERT in device_data:
                            self._temp_alert = device_data[ATTR_TEMP_ALERT]
                        if ATTR_BATT_ALERT in device_data:
                            self._battery_alert = device_data[ATTR_BATT_ALERT]
                        if ATTR_BATTERY_STATUS in device_data:
                            self._battery_status = device_data[ATTR_BATTERY_STATUS]
                            self._battery_type = device_data[ATTR_BATTERY_TYPE]
                        if ATTR_BATT_PERCENT_NORMAL in device_data:
                            self._batt_percent_normal = device_data[ATTR_BATT_PERCENT_NORMAL]
                            self._batt_status_normal = device_data[ATTR_BATT_STATUS_NORMAL]
                        self._closure_action = device_data[ATTR_CONF_CLOSURE]
                        self._battery_voltage = device_data[ATTR_BATTERY_VOLTAGE]
                        if self._is_new_connected:
                            if ATTR_SENSOR_TYPE in device_data:
                                self._sensor_type = device_data[ATTR_SENSOR_TYPE]
                    self.async_write_ha_state()
                    return
                _LOGGER.warning("Error in reading device %s: (%s)", self._name, device_data)
                return
            elif device_data is not None:
                await self.async_log_error(device_data["error"]["code"])
        else:
            if time.time() - self._snooze > SNOOZE_TIME:
                self._active = True
                if self._notify == "notification" or self._notify == "both":
                    await async_notify_once_or_update(
                        self.hass,
                        "Warning: Neviweb Device update restarted for " + self._name + ", Sku: " + self._sku,
                        title=f"Neviweb130 integration {VERSION}",
                        notification_id=f"neviweb130_update_restarted",
                    )

    @property
    @override
    def extra_state_attributes(self)  -> Mapping[str, Any]:
        """Return the state attributes."""
        data = {}
        data.update(
            {
                "leak_status": self._leak_status,
                "temperature": self._cur_temp,
                "temp_alarm": self._temp_status,
                "temperature_alert": self._temp_alert,
                "battery_level": voltage_to_percentage(self._battery_voltage, self._battery_type),
                "battery_voltage": self._battery_voltage,
                "battery_status": self._battery_status,
                "battery_percent_normalized": self._batt_percent_normal,
                "battery_status_normalized": self._batt_status_normal,
                "battery_alert": self._battery_alert,
                "battery_type": self._battery_type,
                "closure_action": self._closure_action,
            }
        )
        if self._is_new_connected:
            data.update(
                {
                    "sensor_type": self._sensor_type,
                }
            )
        data.update(
            {
                "sku": self._sku,
                "device_model": str(self._device_model),
                "device_model_cfg": self._device_model_cfg,
                "firmware": self._firmware,
                "activation": "Active" if self._active else "Inactive",
                "device_type": self._device_type,
                "id": self._id,
            }
        )
        return data


class Neviweb130TankSensor(Neviweb130Sensor):
    """Implementation of a Neviweb tank level sensor LM4110ZB."""

    def __init__(self, data, device_info, name, device_type, sku, firmware, coordinator, entry):
        """Initialize."""
        super().__init__(data, device_info, name, device_type, sku, firmware, coordinator, entry)
        self._refuel = False

    @override
    async def async_update(self) -> None:
        """Update device."""
        if self._active:
            if self._is_monitor:
                MONITOR_ATTRIBUTE = [
                    ATTR_ANGLE,
                    ATTR_TANK_PERCENT,
                    ATTR_TANK_TYPE,
                    ATTR_GAUGE_TYPE,
                    ATTR_TANK_HEIGHT,
                    ATTR_FUEL_ALERT,
                    ATTR_REFUEL,
                    ATTR_BATT_ALERT,
                    ATTR_FUEL_PERCENT_ALERT,
                    ATTR_ERROR_CODE_SET1,
                    ATTR_RSSI,
                ]
            else:
                MONITOR_ATTRIBUTE = [
                    ATTR_ANGLE,
                    ATTR_TANK_PERCENT,
                    ATTR_TANK_TYPE,
                    ATTR_GAUGE_TYPE,
                    ATTR_TANK_HEIGHT,
                ]
            start = time.time()
            device_data = await self._client.async_get_device_attributes(
                self._id, UPDATE_ATTRIBUTES + MONITOR_ATTRIBUTE
            )
            end = time.time()
            elapsed = round(end - start, 3)
            _LOGGER.debug(
                "Updating %s (%s sec): %s",
                self._name,
                elapsed,
                device_data,
            )

            if "error" not in device_data or device_data is not None:
                if "errorCode" not in device_data:
                    self._angle = device_data[ATTR_ANGLE]["value"]
                    if self._angle == -2:
                        await async_notify_critical(
                            self.hass,
                            "Warning: Tank monitor gauge disconnected: "
                            + " for device: "
                            + self._name
                            + ", id: "
                            + self._id
                            + ", Sku: "
                            + self._sku,
                            title=f"Neviweb130 integration {VERSION}",
                            notification_id=f"neviweb130_sensor_error",
                        )
                    self._sampling = device_data[ATTR_ANGLE][ATTR_SAMPLING]
                    self._tank_percent = device_data[ATTR_TANK_PERCENT]
                    self._tank_type = device_data[ATTR_TANK_TYPE]
                    self._tank_height = neviweb_to_ha_height(device_data[ATTR_TANK_HEIGHT])
                    self._gauge_type = neviweb_to_ha_gauge(device_data[ATTR_GAUGE_TYPE])
                    self._battery_voltage = device_data[ATTR_BATTERY_VOLTAGE]
                    if self._is_monitor:
                        self._fuel_alert = device_data[ATTR_FUEL_ALERT]
                        self._refuel = device_data[ATTR_REFUEL]
                        self._fuel_percent_alert = neviweb_to_ha_level(device_data[ATTR_FUEL_PERCENT_ALERT])
                        self._battery_alert = device_data[ATTR_BATT_ALERT]
                        if ATTR_RSSI in device_data:
                            self._rssi = device_data[ATTR_RSSI]
                        if ATTR_ERROR_CODE_SET1 in device_data and len(device_data[ATTR_ERROR_CODE_SET1]) > 0:
                            if device_data[ATTR_ERROR_CODE_SET1]["raw"] != 0:
                                self._error_code = device_data[ATTR_ERROR_CODE_SET1]["raw"]
                                await async_notify_critical(
                                    self.hass,
                                    "Warning: Neviweb Device error code detected: "
                                    + str(device_data[ATTR_ERROR_CODE_SET1]["raw"])
                                    + " for device: "
                                    + self._name
                                    + ", id: "
                                    + self._id
                                    + ", Sku: "
                                    + self._sku,
                                    title=f"Neviweb130 integration {VERSION}",
                                    notification_id="neviweb130_error_code",
                                )
                    self.async_write_ha_state()
                    return
                _LOGGER.warning(
                    "Error in reading device %s: (%s)",
                    self._name,
                    device_data,
                )
                return
            elif device_data is not None:
                await self.async_log_error(device_data["error"]["code"])
        else:
            if time.time() - self._snooze > SNOOZE_TIME:
                self._active = True
                if self._notify == "notification" or self._notify == "both":
                    await async_notify_once_or_update(
                        self.hass,
                        "Warning: Neviweb Device update restarted for " + self._name + ", Sku: " + self._sku,
                        title=f"Neviweb130 integration {VERSION}",
                        notification_id=f"neviweb130_update_restarted",
                    )

    @property
    def level_status(self):
        """Return current sensor fuel level status."""
        if self._tank_percent > self._fuel_percent_alert:
            return "OK"
        else:
            return "Low"

    @property
    def refuel_status(self):
        """Return current sensor refuel status."""
        if self._refuel:
            return "Refueled"
        else:
            return "Normal"

    @property
    def refuel_alert(self) -> bool:
        """Return True if alert is on."""
        return self._refuel

    @property
    def fuel_alert(self) -> bool:
        """Return True if fuel alert is on."""
        return self._fuel_alert

    @property
    def low_fuel_alert(self) -> int:
        """Return low fule alert level."""
        return self._fuel_percent_alert

    @property
    def gauge_angle(self) -> int | None:
        """Return gauge angle."""
        return self._angle

    @property
    def gauge_error(self) -> int | None:
        """Return gauge angle, -2 = disconected, other values = connected."""
        return self._angle

    @property
    def battery_level(self):
        """Return gauge angle."""
        return (voltage_to_percentage(self._battery_voltage, "lithium"),)

    @property
    def battery_voltage(self):
        """Return battery voltage."""
        return self._battery_voltage

    @property
    @override
    def extra_state_attributes(self)  -> Mapping[str, Any]:
        """Return the state attributes."""
        data = {}
        data.update(
            {
                "gauge_angle": self._angle,
                "last_sampling_time": convert(self._sampling),
                "battery_level": voltage_to_percentage(self._battery_voltage, "lithium"),
                "battery_voltage": self._battery_voltage,
                "tank_type": self._tank_type,
                "tank_height": self._tank_height,
                "tank_percent": self._tank_percent,
                "gauge_type": self._gauge_type,
            }
        )
        if self._is_monitor:
            data.update(
                {
                    "battery_alert": self._battery_alert,
                    "fuel_alert": "OK" if self._fuel_alert else "Low",
                    "refuel_alert": "Refueled" if self._refuel else "Normal",
                    "fuel_percent_alert": ("off" if self._fuel_percent_alert == 0 else self._fuel_percent_alert),
                    "error_code": self._error_code,
                    "rssi": self._rssi,
                }
            )
        data.update(
            {
                "sku": self._sku,
                "device_model": str(self._device_model),
                "device_model_cfg": self._device_model_cfg,
                "firmware": self._firmware,
                "activation": "Active" if self._active else "Inactive",
                "device_type": self._device_type,
                "id": self._id,
            }
        )
        return data

    @property
    @override
    def native_value(self) -> str:
        """Return the state of the tank sensor."""
        return self._tank_percent

    async def async_set_tank_type(self, value):
        """Set tank type for LM4110-ZB sensor."""
        await self._client.async_set_tank_type(value["id"], value["type"])
        self._tank_type = value["type"]

    async def async_set_gauge_type(self, value):
        """Set gauge type for LM4110-ZB sensor."""
        await self._client.async_set_gauge_type(value["id"], value["gauge"])
        self._gauge_type = value["gauge"]

    async def async_set_low_fuel_alert(self, value):
        """Set low fuel alert limit LM4110-ZB sensor."""
        await self._client.async_set_low_fuel_alert(value["id"], value["low"])
        self._fuel_percent_alert = value["low"]

    async def async_set_refuel_alert(self, value):
        """Set refuel alert for LM4110-ZB sensor True/False."""
        await self._client.async_set_refuel_alert(value["id"], value["refuel"])
        self._refuel = value["refuel"]

    async def async_set_tank_height(self, value):
        """Set tank height in inches for LM4110-ZB sensor."""
        await self._client.async_set_tank_height(value["id"], value["height"])
        self._tank_height = value["height"]

    async def async_set_fuel_alert(self, value):
        """Set low fuel alert LM4110-ZB sensor."""
        await self._client.async_set_fuel_alert(value["id"], value["fuel"])
        self._fuel_alert = value["fuel"]


class Neviweb130GatewaySensor(Neviweb130Sensor):
    """Implementation of a Neviweb gateway sensor, GT130."""

    def __init__(self, data, device_info, name, device_type, sku, firmware, location, coordinator, entry):
        """Initialize."""
        super().__init__(
            data=data,
            device_info=device_info,
            name=name,
            device_type=device_type,
            sku=sku,
            firmware=firmware,
            coordinator=coordinator,
            entry=entry,
        )
        self._location = str(location)
        self._gateway_status: str = ""
        self._occupancy_mode = "home"

    @override
    async def async_update(self) -> None:
        """Update device."""
        if self._active:
            start = time.time()
            device_status = await self._client.async_get_device_status(self._id)
            neviweb_status = await self._client.async_get_neviweb_status(self._location)
            end = time.time()
            elapsed = round(end - start, 3)
            _LOGGER.debug("Updating %s (%s sec): %s", self._name, elapsed, device_status)
            if "error" not in device_status or device_status is not None:
                if "errorCode" not in device_status:
                    self._gateway_status = device_status[ATTR_STATUS]
                    self.async_write_ha_state()
                else:
                    _LOGGER.warning(
                        "Error in reading device status for %s: (%s)",
                        self._name,
                        device_status,
                    )
            elif device_status is not None:
                await self.async_log_error(device_status["error"]["code"])
            self._occupancy_mode = neviweb_status[ATTR_OCCUPANCY]
            return

    @property
    def gateway_status(self):
        """Return current gateway status: 'online' or 'offline'."""
        return self._gateway_status is not None

    @property
    @override
    def native_value(self) -> str:
        """Return the state of the gateway."""
        return self._gateway_status

    @property
    def occupancy_mode(self):
        """Return the status of Neviweb, Home or Away."""
        return self._occupancy_mode

    @property
    def location(self):
        """Return Neviweb location ID."""
        return self._location

    @property
    @override
    def extra_state_attributes(self)  -> Mapping[str, Any]:
        """Return the state attributes."""
        data = {}
        data.update(
            {
                "gateway_status": self._gateway_status,
                "neviweb_occupancy_mode": self._occupancy_mode,
                "sku": self._sku,
                "device_model": str(self._device_model),
                "device_model_cfg": self._device_model_cfg,
                "firmware": self._firmware,
                "activation": "Active" if self._active else "Inactive",
                "device_type": self._device_type,
                "neviweb_location": self._location,
                "id": self._id,
            }
        )
        return data

    async def async_set_neviweb_status(self, value):
        """Set Neviweb global mode away or home"""
        await self._client.async_post_neviweb_status(self._location, value["mode"])
        self._occupancy_mode = value["mode"]


class Neviweb130DailyRequestSensor(SensorEntity):
    """Daily Neviweb130 request counter sensor."""

    _attr_has_entity_name = True
    _attr_name = "Neviweb130 Daily Requests"
    _attr_icon = "mdi:counter"
    _attr_native_unit_of_measurement = "requests"

    def __init__(self, hass, counter, entry: ConfigEntry):
        self.hass = hass
        self._counter = counter
        self._entry = entry
        self._attr_unique_id = f"{entry.entry_id}_daily_requests"
        self._notified = False

    @property
    def native_value(self):
        """Return the current request count."""
        return self._counter.get_count()

    @property
    def extra_state_attributes(self):
        """Expose date and limit."""
        data = self._counter.data
        limit = self.hass.data[DOMAIN][self._entry.entry_id]["request_limit"]
        return {
            "date": data.get("date"),
            "Neviweb_limit": 30000,
            "safety_limit": limit,
        }

    async def async_update(self):
        """Send notification if we reach the limit."""
        count = self._counter.get_count()
        limit = self.hass.data[DOMAIN][self._entry.entry_id]["request_limit"]

        # Notify when above threshold
        if count > limit and not self._notified:
            self._notified = True

            await async_notify_once_or_update(
                self.hass,
                f"Warning: {count} requests today. Safety limit: {limit}, Daily limit: 30000.",
                title=f"Neviweb130 integration {VERSION}",
                notification_id=f"neviweb130_requests_limit",
            )

        # Reset notification flag if day changed
        today = datetime.date.today().isoformat()
        if self._counter.data.get("date") != today:
            self._notified = False


class Neviweb130DeviceAttributeSensor(CoordinatorEntity[Neviweb130Coordinator], SensorEntity):
    """Representation of a specific Neviweb130 device attribute sensor."""

    _attr_has_entity_name = True
    _attr_should_poll = True

    def __init__(
        self,
        client: Neviweb130Client,
        device: dict,
        device_name: str,
        attribute: str,
        device_id: str,
        attr_info: DeviceInfo,
        coordinator: Neviweb130Coordinator,
        entity_description: Neviweb130SensorEntityDescription,
    ):
        """Initialize the sensor."""
        super().__init__(coordinator)
        self.coordinator = coordinator
        self.entity_description = entity_description
        self._client = client
        self._device = device
        self._id = str(device.get("id"))
        self._device_name = device_name
        self._attribute = entity_description.key
        self._device_id = device_id
        self._attr_unique_id = f"{self._device_id}_{entity_description.key}"
        self._attr_device_info = attr_info
        self._attr_friendly_name = f"{self._device.get('friendly_name')} {attribute.replace('_', ' ').capitalize()}"
        self._attr_icon = entity_description.icon
        self._attr_device_class = entity_description.device_class
        self._attr_state_class = entity_description.state_class
        self._attr_entity_category = entity_description.entity_category

    @property
    def unique_id(self):
        """Return a unique ID."""
        return self._attr_unique_id

    @property
    def device_id(self):
        """Return device_id."""
        return self._device_id

    @property
    @override
    def native_value(self):
        """Return the state of the attribute sensor."""
        device_obj = self.coordinator.data.get(self._id)
        if device_obj and self._attribute in device_obj:
            value = device_obj[self._attribute]
            return value
        else:
            _LOGGER.warning(
                "AttributeSensor: %s attribute %s not found for device: %s.",
                self._attr_unique_id,
                self._attribute,
                self._id,
            )
            return None

    @property
    def extra_state_attributes(self) -> dict:
        """Return the state attributes of the sensor."""
        return {"device_id": self._attr_unique_id}
