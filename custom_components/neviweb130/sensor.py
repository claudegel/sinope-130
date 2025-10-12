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
model xxx = gateway GT4220WF, GT4220WF-M for mesh valve network.
For more details about this platform, please refer to the documentation at
https://www.sinopetech.com/en/support/#api
"""

from __future__ import annotations

import logging
import time
from dataclasses import dataclass
from datetime import datetime
from typing import Any, Callable, override

from homeassistant.components.binary_sensor import BinarySensorDeviceClass
from homeassistant.components.persistent_notification import DOMAIN as PN_DOMAIN
from homeassistant.components.sensor import SensorDeviceClass, SensorEntity, SensorEntityDescription, SensorStateClass
from homeassistant.config_entries import ConfigEntry
from homeassistant.const import (
    ATTR_ENTITY_ID,
    PERCENTAGE,
    SIGNAL_STRENGTH_DECIBELS_MILLIWATT,
    UnitOfEnergy,
    UnitOfTemperature,
    UnitOfVolume,
)
from homeassistant.core import HomeAssistant
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
    ATTR_STATUS,
    ATTR_TANK_HEIGHT,
    ATTR_TANK_PERCENT,
    ATTR_TANK_TYPE,
    ATTR_TEMP_ALERT,
    ATTR_WATER_LEAK_STATUS,
    DOMAIN,
    FULL_MODEL,
    MODEL_ATTRIBUTES,
    SERVICE_SET_ACTIVATION,
    SERVICE_SET_BATTERY_ALERT,
    SERVICE_SET_BATTERY_TYPE,
    SERVICE_SET_FUEL_ALERT,
    SERVICE_SET_GAUGE_TYPE,
    SERVICE_SET_LOW_FUEL_ALERT,
    SERVICE_SET_NEVIWEB_STATUS,
    SERVICE_SET_REFUEL_ALERT,
    SERVICE_SET_SENSOR_ALERT,
    SERVICE_SET_TANK_HEIGHT,
    SERVICE_SET_TANK_TYPE,
    SIGNAL_EVENTS_CHANGED,
    STATE_WATER_LEAK,
)
from .coordinator import Neviweb130Client, Neviweb130Coordinator
from .schema import (
    SET_ACTIVATION_SCHEMA,
    SET_BATTERY_ALERT_SCHEMA,
    SET_BATTERY_TYPE_SCHEMA,
    SET_FUEL_ALERT_SCHEMA,
    SET_GAUGE_TYPE_SCHEMA,
    SET_LOW_FUEL_ALERT_SCHEMA,
    SET_NEVIWEB_STATUS_SCHEMA,
    SET_REFUEL_ALERT_SCHEMA,
    SET_SENSOR_ALERT_SCHEMA,
    SET_TANK_HEIGHT_SCHEMA,
    SET_TANK_TYPE_SCHEMA,
    VERSION,
)

_LOGGER = logging.getLogger(__name__)

DEFAULT_NAME = f"{DOMAIN} sensor"
DEFAULT_NAME_2 = f"{DOMAIN} sensor 2"
DEFAULT_NAME_3 = f"{DOMAIN} sensor 3"
SNOOZE_TIME = 1200

UPDATE_ATTRIBUTES = [ATTR_BATTERY_VOLTAGE, ATTR_BATTERY_STATUS]

IMPLEMENTED_GATEWAY = [130]
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

SENSOR_TYPE: dict[str, list[BinarySensorDeviceClass | str | None]] = {
    "leak": [None, None, BinarySensorDeviceClass.MOISTURE],
    "level": [PERCENTAGE, None, SensorStateClass.MEASUREMENT],
    "gateway": [None, None, BinarySensorDeviceClass.CONNECTIVITY],
}

# Define attributes to be monitored for each device type


@dataclass(frozen=True)
class Neviweb130SensorEntityDescription(SensorEntityDescription):
    """Describes an attribute sensor entity."""

    value_fn: Callable[[Any], Any] | None = None
    signal: str = ""
    icon: str | None = None
    state_class: str | None = "measurement"
    device_class: SensorDeviceClass | None = None
    native_unit_of_measurement: str | None = None


SENSOR_TYPES: tuple[Neviweb130SensorEntityDescription, ...] = (
    # Common attributes
    Neviweb130SensorEntityDescription(
        key="rssi",
        device_class=SensorDeviceClass.SIGNAL_STRENGTH,
        state_class="measurement",
        translation_key="rssi",
        value_fn=lambda data: data["rssi"],
        signal=SIGNAL_EVENTS_CHANGED,
        native_unit_of_measurement=SIGNAL_STRENGTH_DECIBELS_MILLIWATT,
        icon="mdi:wifi",
    ),
    Neviweb130SensorEntityDescription(
        key="total_kwh_count",
        device_class=SensorDeviceClass.ENERGY,
        state_class="total_increasing",
        translation_key="total_kwh_count",
        value_fn=lambda data: data["total_kwh_count"],
        signal=SIGNAL_EVENTS_CHANGED,
        native_unit_of_measurement=UnitOfEnergy.KILO_WATT_HOUR,
        icon="mdi:lightning-bolt",
    ),
    Neviweb130SensorEntityDescription(
        key="monthly_kwh_count",
        device_class=SensorDeviceClass.ENERGY,
        state_class="total",
        translation_key="monthly_kwh_count",
        value_fn=lambda data: data["monthly_kwh_count"],
        signal=SIGNAL_EVENTS_CHANGED,
        native_unit_of_measurement=UnitOfEnergy.KILO_WATT_HOUR,
        icon="mdi:lightning-bolt",
    ),
    Neviweb130SensorEntityDescription(
        key="daily_kwh_count",
        device_class=SensorDeviceClass.ENERGY,
        state_class="total",
        translation_key="daily_kwh_count",
        value_fn=lambda data: data["daily_kwh_count"],
        signal=SIGNAL_EVENTS_CHANGED,
        native_unit_of_measurement=UnitOfEnergy.KILO_WATT_HOUR,
        icon="mdi:lightning-bolt",
    ),
    Neviweb130SensorEntityDescription(
        key="hourly_kwh_count",
        device_class=SensorDeviceClass.ENERGY,
        state_class="total",
        translation_key="hourly_kwh_count",
        value_fn=lambda data: data["hourly_kwh_count"],
        signal=SIGNAL_EVENTS_CHANGED,
        native_unit_of_measurement=UnitOfEnergy.KILO_WATT_HOUR,
        icon="mdi:lightning-bolt",
    ),
    # Climate attributes
    Neviweb130SensorEntityDescription(
        key="pi_heating_demand",
        device_class=SensorDeviceClass.POWER_FACTOR,
        state_class="measurement",
        translation_key="pi_heating_demand",
        value_fn=lambda data: data["pi_heating_demand"],
        signal=SIGNAL_EVENTS_CHANGED,
        native_unit_of_measurement=PERCENTAGE,
        icon="mdi:thermometer",
    ),
    Neviweb130SensorEntityDescription(
        key="current_temperature",
        device_class=SensorDeviceClass.TEMPERATURE,
        state_class="measurement",
        translation_key="current_temperature",
        value_fn=lambda data: data["current_temperature"],
        signal=SIGNAL_EVENTS_CHANGED,
        native_unit_of_measurement=UnitOfTemperature.CELSIUS,
        icon="mdi:thermometer",
    ),
    # Valve attributes
    Neviweb130SensorEntityDescription(
        key="total_flow_count",
        device_class=SensorDeviceClass.ENERGY,
        state_class="total_increasing",
        translation_key="total_flow_count",
        value_fn=lambda data: data["total_flow_count"],
        signal=SIGNAL_EVENTS_CHANGED,
        native_unit_of_measurement=UnitOfVolume.LITERS,
        icon="mdi:lightning-bolt",
    ),
    Neviweb130SensorEntityDescription(
        key="monthly_flow_count",
        device_class=SensorDeviceClass.ENERGY,
        state_class="total",
        translation_key="monthly_flow_count",
        value_fn=lambda data: data["monthly_flow_count"],
        signal=SIGNAL_EVENTS_CHANGED,
        native_unit_of_measurement=UnitOfVolume.LITERS,
        icon="mdi:lightning-bolt",
    ),
    Neviweb130SensorEntityDescription(
        key="daily_flow_count",
        device_class=SensorDeviceClass.ENERGY,
        state_class="total",
        translation_key="daily_flow_count",
        value_fn=lambda data: data["daily_flow_count"],
        signal=SIGNAL_EVENTS_CHANGED,
        native_unit_of_measurement=UnitOfVolume.LITERS,
        icon="mdi:lightning-bolt",
    ),
    Neviweb130SensorEntityDescription(
        key="hourly_flow_count",
        device_class=SensorDeviceClass.ENERGY,
        state_class="total",
        translation_key="hourly_flow_count",
        value_fn=lambda data: data["hourly_flow_count"],
        signal=SIGNAL_EVENTS_CHANGED,
        native_unit_of_measurement=UnitOfVolume.LITERS,
        icon="mdi:lightning-bolt",
    ),
    # Sensor
    Neviweb130SensorEntityDescription(
        key="gateway_status",
        device_class=SensorDeviceClass.ENERGY,
        state_class="measurement",
        translation_key="gateway_status",
        value_fn=lambda data: data["gateway_status"],
        signal=SIGNAL_EVENTS_CHANGED,
        native_unit_of_measurement=None,
        icon="mdi:lightning-bolt",
    ),
)


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


def create_physical_sensors(data, coordinator):
    entities = []

    for gateway_data, default_name in [
        (data["neviweb130_client"].gateway_data, DEFAULT_NAME),
        (data["neviweb130_client"].gateway_data2, DEFAULT_NAME_2),
        (data["neviweb130_client"].gateway_data3, DEFAULT_NAME_3),
    ]:
        if not gateway_data or gateway_data == "_":
            continue

        for device_info in gateway_data:
            model = device_info["signature"]["model"]
            device_name = f"{default_name} {device_info['name']}"
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
                    )
                coordinator.register_device(device)
                entities.append(device)

    return entities


def create_attribute_sensors(hass, entry, data, coordinator, device_registry):
    entities = []

    _LOGGER.debug("Keys dans coordinator.data : %s", list(coordinator.data.keys()))

    for gateway_data, default_name in [
        (data["neviweb130_client"].gateway_data, DEFAULT_NAME),
        (data["neviweb130_client"].gateway_data2, DEFAULT_NAME_2),
        (data["neviweb130_client"].gateway_data3, DEFAULT_NAME_3),
    ]:
        if not gateway_data or gateway_data == "_":
            continue

        for device_info in gateway_data:
            model = device_info["signature"]["model"]
            if model not in FULL_MODEL:  # ALL_MODEL
                continue

            device_id = str(device_info["id"])
            if device_id not in coordinator.data:
                _LOGGER.warning("Device %s pas encore dans coordinator.data", device_id)

            device_name = f"{default_name} {device_info['name']}"
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

    entities = []

    # Add sensors
    entities += create_physical_sensors(data, coordinator)
    await coordinator.async_config_entry_first_refresh()

    if not coordinator.data:
        _LOGGER.debug("Pas de coordinator")
        await coordinator.async_config_entry_first_refresh()

    # Add attribute sensors for each device type
    entities += create_attribute_sensors(hass, entry, data, coordinator, device_registry)

    async_add_entities(entities)
    hass.async_create_task(coordinator.async_request_refresh())

    def set_sensor_alert_service(service):
        """Set different alert and action for water leak sensor."""
        entity_id = service.data[ATTR_ENTITY_ID]
        for sensor in entities:
            if sensor.entity_id == entity_id:
                value = {
                    "id": sensor.unique_id,
                    "leak": service.data[ATTR_LEAK_ALERT],
                    "temp": service.data[ATTR_TEMP_ALERT],
                    "batt": service.data[ATTR_BATT_ALERT],
                    "close": service.data[ATTR_CONF_CLOSURE],
                }
                sensor.async_set_sensor_alert(value)
                sensor.schedule_update_ha_state(True)
                break

    def set_battery_type_service(service):
        """Set battery type for water leak sensor."""
        entity_id = service.data[ATTR_ENTITY_ID]
        for sensor in entities:
            if sensor.entity_id == entity_id:
                value = {
                    "id": sensor.unique_id,
                    "type": service.data[ATTR_BATTERY_TYPE],
                }
                sensor.async_set_battery_type(value)
                sensor.schedule_update_ha_state(True)
                break

    def set_tank_type_service(service):
        """Set tank type for fuel tank."""
        entity_id = service.data[ATTR_ENTITY_ID]
        for sensor in entities:
            if sensor.entity_id == entity_id:
                value = {
                    "id": sensor.unique_id,
                    "type": service.data[ATTR_TANK_TYPE],
                }
                sensor.async_set_tank_type(value)
                sensor.schedule_update_ha_state(True)
                break

    def set_gauge_type_service(service):
        """Set gauge type for propane tank."""
        entity_id = service.data[ATTR_ENTITY_ID]
        for sensor in entities:
            if sensor.entity_id == entity_id:
                value = {
                    "id": sensor.unique_id,
                    "gauge": service.data[ATTR_GAUGE_TYPE],
                }
                sensor.async_set_gauge_type(value)
                sensor.schedule_update_ha_state(True)
                break

    def set_low_fuel_alert_service(service):
        """Set low fuel alert on tank, propane or oil."""
        entity_id = service.data[ATTR_ENTITY_ID]
        for sensor in entities:
            if sensor.entity_id == entity_id:
                value = {
                    "id": sensor.unique_id,
                    "low": service.data[ATTR_FUEL_PERCENT_ALERT],
                }
                sensor.async_set_low_fuel_alert(value)
                sensor.schedule_update_ha_state(True)
                break

    def set_tank_height_service(service):
        """Set tank height for oil tank."""
        entity_id = service.data[ATTR_ENTITY_ID]
        for sensor in entities:
            if sensor.entity_id == entity_id:
                value = {
                    "id": sensor.unique_id,
                    "height": service.data[ATTR_TANK_HEIGHT],
                }
                sensor.async_set_tank_height(value)
                sensor.schedule_update_ha_state(True)
                break

    def set_fuel_alert_service(service):
        """Set fuel alert for LM4110-ZB."""
        entity_id = service.data[ATTR_ENTITY_ID]
        for sensor in entities:
            if sensor.entity_id == entity_id:
                value = {
                    "id": sensor.unique_id,
                    "fuel": service.data[ATTR_FUEL_ALERT],
                }
                sensor.async_set_fuel_alert(value)
                sensor.schedule_update_ha_state(True)
                break

    def set_refuel_alert_service(service):
        """Set refuel alert for LM4110-ZB."""
        entity_id = service.data[ATTR_ENTITY_ID]
        for sensor in entities:
            if sensor.entity_id == entity_id:
                value = {
                    "id": sensor.unique_id,
                    "refuel": service.data[ATTR_REFUEL],
                }
                sensor.set_refuel_alert(value)
                sensor.schedule_update_ha_state(True)
                break

    def set_battery_alert_service(service):
        """Set battery alert for LM4110-ZB."""
        entity_id = service.data[ATTR_ENTITY_ID]
        for sensor in entities:
            if sensor.entity_id == entity_id:
                value = {
                    "id": sensor.unique_id,
                    "batt": service.data[ATTR_BATT_ALERT],
                }
                sensor.async_set_battery_alert(value)
                sensor.schedule_update_ha_state(True)
                break

    def set_activation_service(service):
        """Activate or deactivate Neviweb polling for missing device."""
        entity_id = service.data[ATTR_ENTITY_ID]
        for sensor in entities:
            if sensor.entity_id == entity_id:
                value = {
                    "id": sensor.unique_id,
                    "active": service.data[ATTR_ACTIVE],
                }
                sensor.set_activation(value)
                sensor.schedule_update_ha_state(True)
                break

    def set_neviweb_status_service(service):
        """Set Neviweb global status, home or away."""
        entity_id = service.data[ATTR_ENTITY_ID]
        for sensor in entities:
            if sensor.entity_id == entity_id:
                value = {
                    "id": sensor.unique_id,
                    "mode": service.data[ATTR_MODE],
                }
                sensor.async_set_neviweb_status(value)
                sensor.schedule_update_ha_state(True)
                break

    hass.services.async_register(
        DOMAIN,
        SERVICE_SET_SENSOR_ALERT,
        set_sensor_alert_service,
        schema=SET_SENSOR_ALERT_SCHEMA,
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


def voltage_to_percentage(voltage, type_val):
    """Convert voltage level from volt to percentage."""
    if type_val == "alkaline":
        return int((min(voltage, 3.0) - 2.0) / (3.0 - 2.0) * 100)
    else:
        return int((min(voltage, 3.0) - 2.2) / (3.0 - 2.2) * 100)


def convert(sampling):
    sample = str(sampling)
    date = datetime.fromtimestamp(int(sample[0:-3]))
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
    """Implementation of a Neviweb sensor."""

    def __init__(self, data, device_info, name, device_type, sku, firmware, coordinator):
        """Initialize."""
        super().__init__(coordinator)
        self._device = device_info
        self._name = name
        self._sku = sku
        self._firmware = firmware
        self._client = data["neviweb130_client"]
        self._notify = data["notify"]
        self._id = str(device_info["id"])
        self._device_model = device_info["signature"]["model"]
        self._device_model_cfg = device_info["signature"]["modelCfg"]
        self._hard_rev = device_info["signature"]["hardRev"]
        self._identifier = device_info["identifier"]
        self._device_type = device_type
        self._cur_temp = None
        self._battery_voltage = None
        self._battery_status = None
        self._temp_status = None
        self._battery_type = "alkaline"
        self._leak_status: str = ""
        self._leak_alert = None
        self._temp_alert = None
        self._battery_alert = None
        self._fuel_alert = None
        self._fuel_percent_alert = None
        self._closure_action = None
        self._rssi = None
        self._angle = None
        self._sampling = None
        self._tank_type = None
        self._tank_height = None
        self._tank_percent: str = ""
        self._gauge_type = None
        self._batt_percent_normal = None
        self._batt_status_normal = None
        self._error_code = None
        self._is_leak = (
            device_info["signature"]["model"] in IMPLEMENTED_SENSOR_MODEL
            or device_info["signature"]["model"] in IMPLEMENTED_NEW_SENSOR_MODEL
        )
        self._is_connected = device_info["signature"]["model"] in IMPLEMENTED_CONNECTED_SENSOR
        self._is_new_connected = device_info["signature"]["model"] in IMPLEMENTED_NEW_CONNECTED_SENSOR
        self._is_new_leak = device_info["signature"]["model"] in IMPLEMENTED_NEW_SENSOR_MODEL
        self._is_monitor = device_info["signature"]["model"] in IMPLEMENTED_TANK_MONITOR
        self._is_gateway = device_info["signature"]["model"] in IMPLEMENTED_GATEWAY
        self._snooze: float = 0.0
        self._active = True
        self._attr_device_info = DeviceInfo(
            identifiers={(DOMAIN, self._id)},
            name=self._name,
            manufacturer="claudegel",
            model=self._device_model,
            sw_version=self._firmware,
            hw_version=self._hard_rev,
            serial_number=self._identifier,
            configuration_url="https://www.sinopetech.com/support",
        )
        _LOGGER.debug("Setting up %s: %s", self._name, device_info)

    async def async_update(self):
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
                NEW_LEAK_ATTRIBUTE = [ATTR_ERROR_CODE_SET1]
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
                                    await self.async_notify_ha(
                                        "Warning: Neviweb Device error code detected: "
                                        + str(device_data[ATTR_ERROR_CODE_SET1]["raw"])
                                        + " for device: "
                                        + self._name
                                        + ", Sku: "
                                        + self._sku
                                    )
                    self._battery_voltage = device_data[ATTR_BATTERY_VOLTAGE]
                    if ATTR_RSSI in device_data:
                        self._rssi = device_data[ATTR_RSSI]
                    if device_data[ATTR_WATER_LEAK_STATUS] == "probe":
                        await self.async_notify_ha(
                            "Warning: Neviweb Device error code detected: "
                            + device_data[ATTR_WATER_LEAK_STATUS]
                            + " for device: "
                            + self._name
                            + ", Sku: "
                            + self._sku
                            + ", Leak sensor disconnected"
                        )
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
                    await self.async_notify_ha(
                        "Warning: Neviweb Device update restarted for " + self._name + ", Sku: " + self._sku
                    )

    @property
    def unique_id(self) -> str:
        """Return unique ID based on Neviweb device ID."""
        return self._id

    @property
    def id(self) -> str:
        """Alias pour DataUpdateCoordinator."""
        return self._id

    @property
    def name(self):
        """Return the name of the sensor."""
        return self._name

    @property
    def icon(self):
        """Return the icon to use in the frontend."""
        device_info = SENSOR_TYPE.get(self._device_type)
        if device_info is None:
            return None

        return device_info[1]

    @property
    def device_class(self):
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
            return self.extra_state_attributes.get("rssi")
        return None

    @property
    def extra_state_attributes(self):
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
            data.update({"error_code": self._error_code})
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

    async def async_set_sensor_alert(self, value):
        """Set water leak sensor alert and action."""
        leak = value["leak"]
        batt = value["batt"]
        temp = value["temp"]
        close = value["close"]
        entity = value["id"]
        await self._client.async_set_sensor_alert(entity, leak, batt, temp, close)
        self._leak_alert = True if leak == 1 else False
        self._temp_alert = True if temp == 1 else False
        self._battery_alert = True if batt == 1 else False
        self._closure_action = close

    async def async_set_battery_type(self, value):
        """Set battery type, alkaline or lithium for water leak sensor."""
        batt = value["type"]
        entity = value["id"]
        await self._client.async_set_battery_type(entity, batt)
        self._battery_type = batt

    def set_activation(self, value):
        """Activate or deactivate neviweb polling for a missing device."""
        action = value["active"]
        self._active = action

    async def async_notify_ha(
        self,
        msg: str,
        title: str = "Neviweb130 integration " + VERSION,
    ):
        """Notify user via HA web frontend."""
        await self.hass.services.call(
            PN_DOMAIN,
            "create",
            service_data={
                "title": title,
                "message": msg,
            },
            blocking=False,
        )
        return True

    async def async_log_error(self, error_data):
        """Send error message to LOG."""
        if error_data == "USRSESSEXP":
            _LOGGER.warning("Session expired... reconnecting...")
            if self._notify == "notification" or self._notify == "both":
                await self.async_notify_ha(
                    "Warning: Got USRSESSEXP error, Neviweb session expired. "
                    + "Set your scan_interval parameter to less than 10 "
                    + "minutes to avoid this... Reconnecting..."
                )
            await self._client.async_reconnect()
        elif error_data == "ACCDAYREQMAX":
            _LOGGER.warning("Maximum daily request reached...Reduce polling frequency.")
        elif error_data == "TimeoutError":
            _LOGGER.warning("Timeout error detected...Retry later.")
        elif error_data == "MAINTENANCE":
            _LOGGER.warning("Access blocked for maintenance...Retry later.")
            await self.async_notify_ha("Warning: Neviweb access temporary blocked for maintenance... Retry later.")
            await self._client.async_reconnect()
        elif error_data == "ACCSESSEXC":
            _LOGGER.warning("Maximum session number reached...Close other connections and try again.")
            await self.async_notify_ha(
                "Warning: Maximum Neviweb session number reached...Close other connections and try again."
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
                "Device action not supported for %s (id: %s)... (SKU: %s). Report to maintainer.",
                self._name,
                self._id,
                self._sku,
            )
        elif error_data == "DVCCOMMTO":
            _LOGGER.warning(
                "Device Communication Timeout for %s (id: %s)... The device "
                + "did not respond to the server within the prescribed delay."
                + "(SKU: %s)",
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
                    "This device %s is de-activated and won't be updated for 20 minutes.",
                    self._name,
                )
                _LOGGER.warning(
                    "You can re-activate device %s with "
                    + "service.neviweb130_set_activation or wait 20 minutes "
                    + "for update to restart or just restart HA.",
                    self._name,
                )
            if self._notify == "notification" or self._notify == "both":
                await self.async_notify_ha(
                    "Warning: Received message from Neviweb, device "
                    + "disconnected... Check your log... Neviweb update will "
                    + "be halted for 20 minutes for "
                    + self._name
                    + ", id: "
                    + self._id
                    + ", Sku: "
                    + self._sku
                )
            self._active = False
            self._snooze = time.time()
        else:
            _LOGGER.warning(
                "Unknown error for %s (id: %s): %s...(SKU: %s) Report to maintainer.",
                self._name,
                self._id,
                error_data,
                self._sku,
            )


class Neviweb130ConnectedSensor(Neviweb130Sensor):
    """Implementation of a Neviweb sensor connected to Sedna valve."""

    def __init__(self, data, device_info, name, device_type, sku, firmware, coordinator):
        """Initialize."""
        super().__init__(data, device_info, name, device_type, sku, firmware, coordinator)

        self._cur_temp = None
        self._battery_voltage = None
        self._battery_status = None
        self._temp_status = None
        self._battery_type = "alkaline"
        self._leak_status = ""
        self._leak_alert = None
        self._temp_alert = None
        self._battery_alert = None
        self._fuel_alert = None
        self._fuel_percent_alert = None
        self._closure_action = None
        self._rssi = None
        self._angle = None
        self._sampling = None
        self._tank_type = None
        self._tank_height = None
        self._tank_percent = ""
        self._gauge_type = None
        self._batt_percent_normal = None
        self._batt_status_normal = None
        self._is_connected = device_info["signature"]["model"] in IMPLEMENTED_CONNECTED_SENSOR
        self._is_new_connected = device_info["signature"]["model"] in IMPLEMENTED_NEW_CONNECTED_SENSOR
        self._is_leak = True
        self._is_monitor = False
        self._is_gateway = False
        self._snooze = 0
        self._active = True
        _LOGGER.debug("Setting up %s: %s", self._name, device_info)

    async def async_update(self):
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
                    ATTR_BATT_PERCENT_NORMAL,
                    ATTR_BATT_STATUS_NORMAL,
                    ATTR_CONF_CLOSURE,
                ]
            else:
                LEAK_ATTRIBUTE = []
            if self._is_connected:
                CONNECTED_ATTRIBUTE = [ATTR_RSSI]
            else:
                CONNECTED_ATTRIBUTE = []

            """Get the latest data from Neviweb and update the state."""
            start = time.time()
            device_data = await self._client.async_get_device_attributes(
                self._id,
                UPDATE_ATTRIBUTES + LEAK_ATTRIBUTE + CONNECTED_ATTRIBUTE,
            )
            #            device_daily_stats = await self._client.async_get_device_daily_stats(self._id)
            end = time.time()
            elapsed = round(end - start, 3)
            _LOGGER.debug("Updating %s (%s sec): %s", self._name, elapsed, device_data)

            if "error" not in device_data or device_data is not None:
                if "errorCode" not in device_data:
                    if self._is_leak or self._is_connected:
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
                        self._closure_action = device_data[ATTR_CONF_CLOSURE]
                    self._battery_voltage = device_data[ATTR_BATTERY_VOLTAGE]
                    if ATTR_RSSI in device_data:
                        self._rssi = device_data[ATTR_RSSI]
                    if device_data[ATTR_WATER_LEAK_STATUS] == "probe":
                        await self.async_notify_ha(
                            "Warning: Neviweb Device error code detected: "
                            + device_data[ATTR_WATER_LEAK_STATUS]
                            + " for device: "
                            + self._name
                            + ", id: "
                            + self._id
                            + ", Sku: "
                            + self._sku
                            + ", Leak sensor disconnected"
                        )
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
                    await self.async_notify_ha(
                        "Warning: Neviweb Device update restarted for " + self._name + ", Sku: " + self._sku
                    )

    @property
    def extra_state_attributes(self):
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
                "closure_action": self._closure_action,
            }
        )
        if self._is_connected:
            data.update({"rssi": self._rssi})
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

    def __init__(self, data, device_info, name, device_type, sku, firmware, coordinator):
        """Initialize."""
        super().__init__(data, device_info, name, device_type, sku, firmware, coordinator)

        self._snooze = 0
        self._angle = None
        self._sampling = None
        self._tank_percent: str = ""
        self._tank_type = None
        self._tank_height = None
        self._gauge_type = None
        self._fuel_alert = None
        self._refuel = False
        self._fuel_percent_alert = None
        self._battery_alert = None
        self._battery_voltage = None
        self._error_code = None
        self._rssi = None
        self._is_monitor = device_info["signature"]["model"] in IMPLEMENTED_TANK_MONITOR
        self._is_lte_monitor = device_info["signature"]["model"] in IMPLEMENTED_LTE_TANK_MONITOR
        self._active = True
        _LOGGER.debug("Setting up %s: %s", self._name, device_info)

    async def async_update(self):
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
                        await self.async_notify_ha(
                            "Warning: Tank monitor gauge disconnected: "
                            + " for device: "
                            + self._name
                            + ", id: "
                            + self._id
                            + ", Sku: "
                            + self._sku
                        )
                    self._sampling = device_data[ATTR_ANGLE][ATTR_SAMPLING]
                    self._tank_percent = device_data[ATTR_TANK_PERCENT]
                    self._tank_type = device_data[ATTR_TANK_TYPE]
                    self._tank_height = device_data[ATTR_TANK_HEIGHT]
                    self._gauge_type = device_data[ATTR_GAUGE_TYPE]
                    self._battery_voltage = device_data[ATTR_BATTERY_VOLTAGE]
                    if self._is_monitor:
                        self._fuel_alert = device_data[ATTR_FUEL_ALERT]
                        self._refuel = device_data[ATTR_REFUEL]
                        self._fuel_percent_alert = device_data[ATTR_FUEL_PERCENT_ALERT]
                        self._battery_alert = device_data[ATTR_BATT_ALERT]
                        if ATTR_RSSI in device_data:
                            self._rssi = device_data[ATTR_RSSI]
                        if ATTR_ERROR_CODE_SET1 in device_data and len(device_data[ATTR_ERROR_CODE_SET1]) > 0:
                            if device_data[ATTR_ERROR_CODE_SET1]["raw"] != 0:
                                self._error_code = device_data[ATTR_ERROR_CODE_SET1]["raw"]
                                await self.async_notify_ha(
                                    "Warning: Neviweb Device error code detected: "
                                    + str(device_data[ATTR_ERROR_CODE_SET1]["raw"])
                                    + " for device: "
                                    + self._name
                                    + ", id: "
                                    + self._id
                                    + ", Sku: "
                                    + self._sku
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
                    await self.async_notify_ha(
                        "Warning: Neviweb Device update restarted for " + self._name + ", Sku: " + self._sku
                    )

    @property
    def level_status(self):
        """Return current sensor fuel level status."""
        if self._fuel_alert:
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
    def gauge_angle(self):
        """Return gauge angle."""
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
    def extra_state_attributes(self):
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
                    "fuel_percent_alert": ("Off" if self._fuel_percent_alert == 0 else self._fuel_percent_alert),
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
        gauge = str(value["gauge"])
        await self._client.async_set_gauge_type(value["id"], gauge)
        self._gauge_type = gauge

    async def async_set_low_fuel_alert(self, value):
        """Set low fuel alert limit LM4110-ZB sensor."""
        await self._client.async_set_low_fuel_alert(value["id"], value["low"])
        self._fuel_percent_alert = value["low"]

    async def async_set_refuel_alert(self, value):
        """Set refuel alert for LM4110-ZB sensor True/False."""
        await self._client.async_set_refuel_alert(value["id"], value["refuel"])
        self._refuel = value["refuel"]

    async def async_set_tank_height(self, value):
        """Set low fuel alert LM4110-ZB sensor."""
        await self._client.async_set_tank_height(value["id"], value["height"])
        self._tank_height = value["height"]

    async def async_set_fuel_alert(self, value):
        """Set low fuel alert LM4110-ZB sensor."""
        await self._client.async_set_fuel_alert(value["id"], value["fuel"])
        self._fuel_alert = value["fuel"]

    async def async_set_battery_alert(self, value):
        """Set low battery alert LM4110-ZB sensor."""
        await self._client.async_set_battery_alert(value["id"], value["batt"])
        self._battery_alert = value["batt"]


class Neviweb130GatewaySensor(Neviweb130Sensor):
    """Implementation of a Neviweb gateway sensor, GT130."""

    def __init__(
        self,
        data,
        device_info,
        name,
        device_type,
        sku,
        firmware,
        location,
        coordinator,
    ):
        """Initialize."""
        super().__init__(
            data=data,
            device_info=device_info,
            name=name,
            device_type=device_type,
            sku=sku,
            firmware=firmware,
            coordinator=coordinator,
        )
        self._location = location
        self._active = True
        self._snooze = 0
        self._gateway_status: str = ""
        self._occupancyMode = None
        self._is_gateway = device_info["signature"]["model"] in IMPLEMENTED_GATEWAY
        _LOGGER.debug("Setting up %s: %s", self._name, device_info)

    async def async_update(self):
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
            self._occupancyMode = neviweb_status[ATTR_OCCUPANCY]
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
        """Return the state of the gateway."""
        return self._occupancyMode

    @property
    def location(self):
        """Return Neviweb location ID."""
        return self._location

    @property
    def extra_state_attributes(self):
        """Return the state attributes."""
        data = {}
        data.update(
            {
                "gateway_status": self._gateway_status,
                "neviweb_occupancyMode": self._occupancyMode,
                "sku": self._sku,
                "device_model": str(self._device_model),
                "device_model_cfg": self._device_model_cfg,
                "firmware": self._firmware,
                "activation": "Active" if self._active else "Inactive",
                "device_type": self._device_type,
                "neviweb_location": str(self._location),
                "id": self._id,
            }
        )
        return data

    async def async_set_neviweb_status(self, value):
        """Set Neviweb global mode away or home"""
        mode = value["mode"]
        entity = value["id"]
        await self._client.async_post_neviweb_status(entity, str(self._location), mode)
        self._occupancyMode = mode


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
    def extra_state_attributes(self):
        """Return the state attributes of the sensor."""
        return {"device_id": self._attr_unique_id}
