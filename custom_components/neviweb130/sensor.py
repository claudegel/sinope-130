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
from datetime import datetime
from threading import Lock
from typing import Any, override

from homeassistant.components.binary_sensor import BinarySensorDeviceClass
from homeassistant.components.persistent_notification import DOMAIN as PN_DOMAIN
from homeassistant.components.recorder.models import StatisticMeanType
from homeassistant.components.sensor import SensorStateClass
from homeassistant.const import ATTR_ENTITY_ID, PERCENTAGE
from homeassistant.core import ServiceCall
from homeassistant.exceptions import ServiceValidationError
from homeassistant.helpers.entity import Entity

from . import NOTIFY
from . import SCAN_INTERVAL as scan_interval
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
    DOMAIN,
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
    STATE_WATER_LEAK,
    VERSION,
)
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
)

_LOGGER = logging.getLogger(__name__)

DEFAULT_NAME = f"{DOMAIN} sensor"
DEFAULT_NAME_2 = f"{DOMAIN} sensor 2"
DEFAULT_NAME_3 = f"{DOMAIN} sensor 3"
SNOOZE_TIME = 1200
SCAN_INTERVAL = scan_interval

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

SENSOR_TYPES: dict[
    str,
    tuple[
        str | None,
        str | None,
        BinarySensorDeviceClass | SensorStateClass,
        str | None,
        StatisticMeanType | None
    ]
] = {
    "leak": (None, None, BinarySensorDeviceClass.MOISTURE, None, None),
    "level": (
        PERCENTAGE,
        None,
        SensorStateClass.MEASUREMENT,
        "percentage",
        StatisticMeanType.ARITHMETIC
    ),
    "gateway": (None, None, BinarySensorDeviceClass.CONNECTIVITY, None, None),
}


async def async_setup_platform(
    hass,
    config,
    async_add_entities,
    discovery_info=None,
) -> None:
    """Set up the Neviweb sensor."""
    data = hass.data[DOMAIN]

    # Wait for async migration to be done
    await data.migration_done.wait()

    entities: list[Neviweb130Sensor] = []
    for device_info in data.neviweb130_client.gateway_data:
        if (
            "signature" in device_info
            and "model" in device_info["signature"]
            and device_info["signature"]["model"] in IMPLEMENTED_DEVICE_MODEL
        ):
            device_name = "{} {}".format(DEFAULT_NAME, device_info["name"])
            device_sku = device_info["sku"]
            location_id = device_info["location$id"]
            device_firmware = "{}.{}.{}".format(
                device_info["signature"]["softVersion"]["major"],
                device_info["signature"]["softVersion"]["middle"],
                device_info["signature"]["softVersion"]["minor"],
            )
            if (
                device_info["signature"]["model"] in IMPLEMENTED_SENSOR_MODEL
                or device_info["signature"]["model"] in IMPLEMENTED_NEW_SENSOR_MODEL
            ):
                device_type = "leak"
                entities.append(
                    Neviweb130Sensor(
                        data,
                        device_info,
                        device_name,
                        device_type,
                        device_sku,
                        device_firmware,
                    )
                )
            elif (
                device_info["signature"]["model"] in IMPLEMENTED_CONNECTED_SENSOR
                or device_info["signature"]["model"] in IMPLEMENTED_NEW_CONNECTED_SENSOR
            ):
                device_type = "leak"
                entities.append(
                    Neviweb130ConnectedSensor(
                        data,
                        device_info,
                        device_name,
                        device_type,
                        device_sku,
                        device_firmware,
                    )
                )
            elif (
                device_info["signature"]["model"] in IMPLEMENTED_TANK_MONITOR
                or device_info["signature"]["model"] in IMPLEMENTED_LTE_TANK_MONITOR
            ):
                device_type = "level"
                entities.append(
                    Neviweb130TankSensor(
                        data,
                        device_info,
                        device_name,
                        device_type,
                        device_sku,
                        device_firmware,
                    )
                )
            else:
                device_type = "gateway"
                entities.append(
                    Neviweb130GatewaySensor(
                        data,
                        device_info,
                        device_name,
                        device_type,
                        device_sku,
                        device_firmware,
                        location_id,
                    )
                )
    for device_info in data.neviweb130_client.gateway_data2:
        if (
            "signature" in device_info
            and "model" in device_info["signature"]
            and device_info["signature"]["model"] in IMPLEMENTED_DEVICE_MODEL
        ):
            device_name = "{} {}".format(DEFAULT_NAME_2, device_info["name"])
            device_sku = device_info["sku"]
            location_id = device_info["location$id"]
            device_firmware = "{}.{}.{}".format(
                device_info["signature"]["softVersion"]["major"],
                device_info["signature"]["softVersion"]["middle"],
                device_info["signature"]["softVersion"]["minor"],
            )
            if (
                device_info["signature"]["model"] in IMPLEMENTED_SENSOR_MODEL
                or device_info["signature"]["model"] in IMPLEMENTED_NEW_SENSOR_MODEL
            ):
                device_type = "leak"
                entities.append(
                    Neviweb130Sensor(
                        data,
                        device_info,
                        device_name,
                        device_type,
                        device_sku,
                        device_firmware,
                    )
                )
            elif (
                device_info["signature"]["model"] in IMPLEMENTED_CONNECTED_SENSOR
                or device_info["signature"]["model"] in IMPLEMENTED_NEW_CONNECTED_SENSOR
            ):
                device_type = "leak"
                entities.append(
                    Neviweb130ConnectedSensor(
                        data,
                        device_info,
                        device_name,
                        device_type,
                        device_sku,
                        device_firmware,
                    )
                )
            elif device_info["signature"]["model"] in IMPLEMENTED_TANK_MONITOR:
                device_type = "level"
                entities.append(
                    Neviweb130TankSensor(
                        data,
                        device_info,
                        device_name,
                        device_type,
                        device_sku,
                        device_firmware,
                    )
                )
            else:
                device_type = "gateway"
                entities.append(
                    Neviweb130GatewaySensor(
                        data,
                        device_info,
                        device_name,
                        device_type,
                        device_sku,
                        device_firmware,
                        location_id,
                    )
                )
    for device_info in data.neviweb130_client.gateway_data3:
        if (
            "signature" in device_info
            and "model" in device_info["signature"]
            and device_info["signature"]["model"] in IMPLEMENTED_DEVICE_MODEL
        ):
            device_name = "{} {}".format(DEFAULT_NAME_3, device_info["name"])
            device_sku = device_info["sku"]
            location_id = device_info["location$id"]
            device_firmware = "{}.{}.{}".format(
                device_info["signature"]["softVersion"]["major"],
                device_info["signature"]["softVersion"]["middle"],
                device_info["signature"]["softVersion"]["minor"],
            )
            if (
                device_info["signature"]["model"] in IMPLEMENTED_SENSOR_MODEL
                or device_info["signature"]["model"] in IMPLEMENTED_NEW_SENSOR_MODEL
            ):
                device_type = "leak"
                entities.append(
                    Neviweb130Sensor(
                        data,
                        device_info,
                        device_name,
                        device_type,
                        device_sku,
                        device_firmware,
                    )
                )
            elif (
                device_info["signature"]["model"] in IMPLEMENTED_CONNECTED_SENSOR
                or device_info["signature"]["model"] in IMPLEMENTED_NEW_CONNECTED_SENSOR
            ):
                device_type = "leak"
                entities.append(
                    Neviweb130ConnectedSensor(
                        data,
                        device_info,
                        device_name,
                        device_type,
                        device_sku,
                        device_firmware,
                    )
                )
            elif device_info["signature"]["model"] in IMPLEMENTED_TANK_MONITOR:
                device_type = "level"
                entities.append(
                    Neviweb130TankSensor(
                        data,
                        device_info,
                        device_name,
                        device_type,
                        device_sku,
                        device_firmware,
                    )
                )
            else:
                device_type = "gateway"
                entities.append(
                    Neviweb130GatewaySensor(
                        data,
                        device_info,
                        device_name,
                        device_type,
                        device_sku,
                        device_firmware,
                        location_id,
                    )
                )

    async_add_entities(entities, True)

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

    def set_sensor_alert_service(service: ServiceCall) -> None:
        """Set different alert and action for water leak sensor."""
        sensor = get_sensor(service)
        value = {
            "id": sensor.unique_id,
            "leak": service.data[ATTR_LEAK_ALERT],
            "temp": service.data[ATTR_TEMP_ALERT],
            "batt": service.data[ATTR_BATT_ALERT],
            "close": service.data[ATTR_CONF_CLOSURE],
        }
        sensor.set_sensor_alert(value)
        sensor.schedule_update_ha_state(True)

    def set_battery_type_service(service: ServiceCall) -> None:
        """Set battery type for water leak sensor."""
        sensor = get_sensor(service)
        value = {
            "id": sensor.unique_id,
            "type": service.data[ATTR_BATTERY_TYPE],
        }
        sensor.set_battery_type(value)
        sensor.schedule_update_ha_state(True)

    def set_tank_type_service(service: ServiceCall) -> None:
        """Set tank type for fuel tank."""
        sensor = get_sensor(service)
        if not isinstance(sensor, Neviweb130TankSensor):
            raise ServiceValidationError(f"Entity {sensor.entity_id} cannot be used with this service")
        value = {"id": sensor.unique_id, "type": service.data[ATTR_TANK_TYPE]}
        sensor.set_tank_type(value)
        sensor.schedule_update_ha_state(True)

    def set_gauge_type_service(service: ServiceCall) -> None:
        """Set gauge type for propane tank."""
        sensor = get_sensor(service)
        if not isinstance(sensor, Neviweb130TankSensor):
            raise ServiceValidationError(f"Entity {sensor.entity_id} must be a {DOMAIN} tank sensor")
        value = {"id": sensor.unique_id, "gauge": service.data[ATTR_GAUGE_TYPE]}
        sensor.set_gauge_type(value)
        sensor.schedule_update_ha_state(True)

    def set_low_fuel_alert_service(service: ServiceCall) -> None:
        """Set low fuel alert on tank, propane or oil."""
        sensor = get_sensor(service)
        if not isinstance(sensor, Neviweb130TankSensor):
            raise ServiceValidationError(f"Entity {sensor.entity_id} must be a {DOMAIN} tank sensor")
        value = {
            "id": sensor.unique_id,
            "low": service.data[ATTR_FUEL_PERCENT_ALERT],
        }
        sensor.set_low_fuel_alert(value)
        sensor.schedule_update_ha_state(True)

    def set_tank_height_service(service: ServiceCall) -> None:
        """Set tank height for oil tank."""
        sensor = get_sensor(service)
        if not isinstance(sensor, Neviweb130TankSensor):
            raise ServiceValidationError(f"Entity {sensor.entity_id} is not a Neviweb130TankSensor")
        value = {
            "id": sensor.unique_id,
            "height": service.data[ATTR_TANK_HEIGHT],
        }
        sensor.set_tank_height(value)
        sensor.schedule_update_ha_state(True)

    def set_fuel_alert_service(service: ServiceCall) -> None:
        """Set fuel alert for LM4110-ZB."""
        sensor = get_sensor(service)
        if not isinstance(sensor, Neviweb130TankSensor):
            raise ServiceValidationError(f"Entity {sensor.entity_id} is not a Neviweb130TankSensor")
        value = {"id": sensor.unique_id, "fuel": service.data[ATTR_FUEL_ALERT]}
        sensor.set_fuel_alert(value)
        sensor.schedule_update_ha_state(True)

    def set_refuel_alert_service(service: ServiceCall) -> None:
        """Set refuel alert for LM4110-ZB."""
        sensor = get_sensor(service)
        if not isinstance(sensor, Neviweb130TankSensor):
            raise ServiceValidationError(f"Entity {sensor.entity_id} is not a Neviweb130TankSensor")
        value = {"id": sensor.unique_id, "refuel": service.data[ATTR_REFUEL]}
        sensor.set_refuel_alert(value)
        sensor.schedule_update_ha_state(True)

    def set_battery_alert_service(service: ServiceCall) -> None:
        """Set battery alert for LM4110-ZB."""
        sensor = get_sensor(service)
        if not isinstance(sensor, Neviweb130TankSensor):
            raise ServiceValidationError(f"Entity {sensor.entity_id} is not a Neviweb130TankSensor")
        value = {"id": sensor.unique_id, "batt": service.data[ATTR_BATT_ALERT]}
        sensor.set_battery_alert(value)
        sensor.schedule_update_ha_state(True)

    def set_activation_service(service: ServiceCall) -> None:
        """Activate or deactivate Neviweb polling for missing device."""
        sensor = get_sensor(service)
        value = {"id": sensor.unique_id, "active": service.data[ATTR_ACTIVE]}
        sensor.set_activation(value)
        sensor.schedule_update_ha_state(True)

    def set_neviweb_status_service(service: ServiceCall) -> None:
        """Set Neviweb global status, home or away."""
        sensor = get_sensor(service)
        if not isinstance(sensor, Neviweb130GatewaySensor):
            raise ServiceValidationError(f"Entity {sensor.entity_id} is not a Neviweb130GatewaySensor")
        value = {"id": sensor.unique_id, "mode": service.data[ATTR_MODE]}
        sensor.set_neviweb_status(value)
        sensor.schedule_update_ha_state(True)

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


class Neviweb130Sensor(Entity):
    """Implementation of a Neviweb sensor connected to GT130."""

    def __init__(self, data, device_info, name, device_type, sku, firmware):
        """Initialize."""
        _LOGGER.debug("Setting up %s: %s", name, device_info)
        self._name = name
        self._sku = sku
        self._firmware = firmware
        self._client = data.neviweb130_client
        self._id = str(device_info["id"])
        self._device_model = device_info["signature"]["model"]
        self._device_model_cfg = device_info["signature"]["modelCfg"]
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
        self._is_monitor = device_info["signature"]["model"] in IMPLEMENTED_TANK_MONITOR
        self._is_gateway = device_info["signature"]["model"] in IMPLEMENTED_GATEWAY
        self._active = True
        self._angle = None
        self._batt_percent_normal = None
        self._batt_status_normal = None
        self._battery_alert = None
        self._battery_status = None
        self._battery_type = "alkaline"
        self._battery_voltage = None
        self._closure_action = None
        self._cur_temp = None
        self._error_code = None
        self._fuel_alert = None
        self._fuel_percent_alert = None
        self._gauge_type = None
        self._leak_alert = None
        self._leak_status = None
        self._rssi = None
        self._sampling = None
        self._sensor_type = None
        self._snooze = 0.0
        self._tank_height = None
        self._tank_percent = None
        self._tank_type = None
        self._temp_alert = None
        self._temp_status = None

    def update(self):
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
            device_data: dict[str, Any] = self._client.get_device_attributes(
                self._id, UPDATE_ATTRIBUTES + LEAK_ATTRIBUTE + NEW_LEAK_ATTRIBUTE
            )
            #            device_daily_stats = self._client.get_device_daily_stats(self._id)
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
                                    self.notify_ha(
                                        "Warning: Neviweb Device error code detected: "
                                        + str(device_data[ATTR_ERROR_CODE_SET1]["raw"])
                                        + " for device: "
                                        + self._name
                                        + ", Sku: "
                                        + self._sku
                                    )
                            if ATTR_SENSOR_TYPE in device_data:
                                self._sensor_type = device_data[ATTR_SENSOR_TYPE]
                        if device_data[ATTR_WATER_LEAK_STATUS] == "probe":
                            self.notify_ha(
                                "Warning: Neviweb Device error detected: "
                                + device_data[ATTR_WATER_LEAK_STATUS]
                                + " for device: "
                                + self._name
                                + ", Sku: "
                                + self._sku
                                + ", Leak sensor disconnected"
                            )
                    self._battery_voltage = device_data[ATTR_BATTERY_VOLTAGE]
                    if ATTR_RSSI in device_data:
                        self._rssi = device_data[ATTR_RSSI]
                    return
                _LOGGER.warning("Error in reading device %s: (%s)", self._name, device_data)
                return
            elif device_data is not None:
                self.log_error(device_data["error"]["code"])
        else:
            if time.time() - self._snooze > SNOOZE_TIME:
                self._active = True
                if NOTIFY == "notification" or NOTIFY == "both":
                    self.notify_ha("Warning: Neviweb Device update restarted for " + self._name + ", Sku: " + self._sku)

    @property
    @override
    def unique_id(self) -> str:
        """Return unique ID based on Neviweb device ID."""
        return self._id

    @property
    @override
    def name(self) -> str:
        """Return the name of the sensor."""
        return self._name

    @property
    @override
    def icon(self) -> str | None:
        """Return the icon to use in the frontend."""
        device_info = SENSOR_TYPES.get(self._device_type)
        if device_info is None:
            return None

        return device_info[1]

    @property
    @override
    def unit_of_measurement(self) -> str | None:
        """Return the unit of measurement of this entity, if any."""
        device_info = SENSOR_TYPES.get(self._device_type)
        if device_info is None:
            return None

        return device_info[0]

    @property
    def unit_class(self) -> str | None:
        device_info = SENSOR_TYPES.get(self._device_type)
        return device_info[3] if device_info else None

    @property
    def statistic_mean_type(self) -> StatisticMeanType | None:
        device_info = SENSOR_TYPES.get(self._device_type)
        return device_info[4] if device_info else None

    @property
    @override
    def device_class(self) -> BinarySensorDeviceClass | SensorStateClass | None:
        """Return the device class of this entity."""
        device_info = SENSOR_TYPES.get(self._device_type)
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
            data.update({
                "error_code": self._error_code,
                "sensor_type": self._sensor_type,
            })
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
    def state(self):
        """Return the state of the sensor."""
        return self._leak_status

    def set_sensor_alert(self, value):
        """Set water leak sensor alert and action."""
        self._client.set_sensor_alert(value["id"], value["leak"], value["batt"], value["temp"], value["close"])
        self._leak_alert = True if value["leak"] == 1 else False
        self._temp_alert = True if value["temp"] == 1 else False
        self._battery_alert = True if value["batt"] == 1 else False
        self._closure_action = value["close"]

    def set_battery_type(self, value):
        """Set battery type, alkaline or lithium for water leak sensor."""
        self._client.set_battery_type(value["id"], value["type"])
        self._battery_type = value["type"]

    def set_activation(self, value):
        """Activate or deactivate neviweb polling for a missing device."""
        self._active = value["active"]

    def notify_ha(self, msg: str, title: str = "Neviweb130 integration " + VERSION):
        """Notify user via HA web frontend."""
        self.hass.services.call(
            PN_DOMAIN,
            "create",
            service_data={
                "title": title,
                "message": msg,
            },
            blocking=False,
        )
        return True

    def log_error(self, error_data):
        """Send error message to LOG."""
        if error_data == "USRSESSEXP":
            _LOGGER.warning("Session expired... Reconnecting...")
            if NOTIFY == "notification" or NOTIFY == "both":
                self.notify_ha(
                    "Warning: Got USRSESSEXP error, Neviweb session expired. "
                    "Set your scan_interval parameter to less than 10 minutes to avoid this... Reconnecting..."
                )
            self._client.reconnect()
        elif error_data == "ACCDAYREQMAX":
            _LOGGER.warning("Maximum daily request reached... Reduce polling frequency")
        elif error_data == "TimeoutError":
            _LOGGER.warning("Timeout error detected... Retry later")
        elif error_data == "MAINTENANCE":
            _LOGGER.warning("Access blocked for maintenance... Retry later")
            self.notify_ha("Warning: Neviweb access temporary blocked for maintenance... Retry later")
            self._client.reconnect()
        elif error_data == "ACCSESSEXC":
            _LOGGER.warning("Maximum session number reached... Close other connections and try again")
            self.notify_ha("Warning: Maximum Neviweb session number reached... Close other connections and try again")
            self._client.reconnect()
        elif error_data == "DVCATTRNSPTD":
            _LOGGER.warning(
                "Device attribute not supported for %s (id: %s): %s... (SKU: %s)",
                self._name,
                str(self._id),
                error_data,
                self._sku,
            )
        elif error_data == "DVCACTNSPTD":
            _LOGGER.warning(
                "Device action not supported for %s (id: %s)... (SKU: %s) Report to maintainer",
                self._name,
                str(self._id),
                self._sku,
            )
        elif error_data == "DVCCOMMTO":
            _LOGGER.warning(
                "Device Communication Timeout for %s (id: %s)... The device "
                + "did not respond to the server within the prescribed delay"
                + "(SKU: %s)",
                self._name,
                str(self._id),
                self._sku,
            )
        elif error_data == "SVCERR":
            _LOGGER.warning(
                "Service error, device not available retry later %s (id: %s): %s... (SKU: %s)",
                self._name,
                str(self._id),
                error_data,
                self._sku,
            )
        elif error_data == "DVCBUSY":
            _LOGGER.warning(
                "Device busy can't reach (neviweb update ?), retry later %s (id: %s): %s... (SKU: %s)",
                self._name,
                str(self._id),
                error_data,
                self._sku,
            )
        elif error_data == "DVCUNVLB":
            if NOTIFY == "logging" or NOTIFY == "both":
                _LOGGER.warning(
                    "Device %s is disconnected from Neviweb: %s (id: %s)... (SKU: %s)",
                    self._name,
                    str(self._id),
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
            if NOTIFY == "notification" or NOTIFY == "both":
                self.notify_ha(
                    "Warning: Received message from Neviweb, device "
                    + "disconnected... Check your log... Neviweb update will "
                    + "be halted for 20 minutes for "
                    + self._name
                    + ", id: "
                    + str(self._id)
                    + ", Sku: "
                    + self._sku
                )
            self._active = False
            self._snooze = time.time()
        else:
            _LOGGER.warning(
                "Unknown error for %s (id: %s): %s... (SKU: %s) Report to maintainer",
                self._name,
                str(self._id),
                error_data,
                self._sku,
            )


class Neviweb130ConnectedSensor(Neviweb130Sensor):
    """Implementation of a Neviweb sensor connected to Sedna valve."""

    def update(self):
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
            if self._is_new_leak:
                NEW_LEAK_ATTRIBUTE = [ATTR_SENSOR_TYPE]
            else:
                NEW_LEAK_ATTRIBUTE = []
            if self._is_connected:
                CONNECTED_ATTRIBUTE = [ATTR_RSSI]
            else:
                CONNECTED_ATTRIBUTE = []

            """Get the latest data from Neviweb and update the state."""
            start = time.time()
            device_data = self._client.get_device_attributes(
                self._id, UPDATE_ATTRIBUTES + LEAK_ATTRIBUTE + NEW_LEAK_ATTRIBUTE + CONNECTED_ATTRIBUTE
            )
            #            device_daily_stats = self._client.get_device_daily_stats(self._id)
            end = time.time()
            elapsed = round(end - start, 3)
            _LOGGER.debug("Updating %s (%s sec): %s", self._name, elapsed, device_data)
            if "error" not in device_data or device_data is not None:
                if "errorCode" not in device_data:
                    if self._is_leak or self._is_connected or self._is_new_leak:
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
                        self.notify_ha(
                            "Warning: Neviweb Device error detected: "
                            + device_data[ATTR_WATER_LEAK_STATUS]
                            + " for device: "
                            + self._name
                            + ", id: "
                            + str(self._id)
                            + ", Sku: "
                            + self._sku
                            + ", Leak sensor disconnected"
                        )
                    if self._is_new_leak:
                        if ATTR_SENSOR_TYPE in device_data:
                            self._sensor_type = device_data[ATTR_SENSOR_TYPE]
                    return
                _LOGGER.warning("Error in reading device %s: (%s)", self._name, device_data)
                return
            elif device_data is not None:
                self.log_error(device_data["error"]["code"])
        else:
            if time.time() - self._snooze > SNOOZE_TIME:
                self._active = True
                if NOTIFY == "notification" or NOTIFY == "both":
                    self.notify_ha("Warning: Neviweb Device update restarted for " + self._name + ", Sku: " + self._sku)

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
        if self._is_new_leak:
            data.update({"sensor_type": self._sensor_type,})
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

    def __init__(self, data, device_info, name, device_type, sku, firmware):
        """Initialize."""
        super().__init__(data, device_info, name, device_type, sku, firmware)
        self._refuel = False

    def update(self):
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
            device_data = self._client.get_device_attributes(self._id, UPDATE_ATTRIBUTES + MONITOR_ATTRIBUTE)
            end = time.time()
            elapsed = round(end - start, 3)
            _LOGGER.debug("Updating %s (%s sec): %s", self._name, elapsed, device_data)
            if "error" not in device_data or device_data is not None:
                if "errorCode" not in device_data:
                    self._angle = device_data[ATTR_ANGLE]["value"]
                    if self._angle == -2:
                        self.notify_ha(
                            "Warning: Tank monitor gauge disconnected: "
                            + " for device: "
                            + self._name
                            + ", id: "
                            + str(self._id)
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
                                self.notify_ha(
                                    "Warning: Neviweb Device error code detected: "
                                    + str(device_data[ATTR_ERROR_CODE_SET1]["raw"])
                                    + " for device: "
                                    + self._name
                                    + ", id: "
                                    + str(self._id)
                                    + ", Sku: "
                                    + self._sku
                                )
                    return
                _LOGGER.warning("Error in reading device %s: (%s)", self._name, device_data)
                return
            elif device_data is not None:
                self.log_error(device_data["error"]["code"])
        else:
            if time.time() - self._snooze > SNOOZE_TIME:
                self._active = True
                if NOTIFY == "notification" or NOTIFY == "both":
                    self.notify_ha("Warning: Neviweb Device update restarted for " + self._name + ", Sku: " + self._sku)

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
    def state(self):
        """Return the state of the tank sensor."""
        return self._tank_percent

    #        return convert_to_percent(self._angle, 10, 80)

    def set_tank_type(self, value):
        """Set tank type for LM4110-ZB sensor."""
        self._client.set_tank_type(value["id"], value["type"])
        self._tank_type = value["type"]

    def set_gauge_type(self, value):
        """Set gauge type for LM4110-ZB sensor."""
        self._client.set_gauge_type(value["id"], str(value["gauge"]))
        self._gauge_type = str(value["gauge"])

    def set_low_fuel_alert(self, value):
        """Set low fuel alert limit LM4110-ZB sensor."""
        self._client.set_low_fuel_alert(value["id"], value["low"])
        self._fuel_percent_alert = value["low"]

    def set_refuel_alert(self, value):
        """ "Set refuel alert for LM4110-ZB sensor True/False."""
        self._client.set_refuel_alert(value["id"], value["refuel"])
        self._refuel = value["refuel"]

    def set_tank_height(self, value):
        """Set low fuel alert LM4110-ZB sensor."""
        self._client.set_tank_height(value["id"], value["height"])
        self._tank_height = value["height"]

    def set_fuel_alert(self, value):
        """Set low fuel alert LM4110-ZB sensor."""
        self._client.set_fuel_alert(value["id"], value["fuel"])
        self._fuel_alert = value["fuel"]

    def set_battery_alert(self, value):
        """Set low battery alert LM4110-ZB sensor."""
        self._client.set_battery_alert(value["id"], value["batt"])
        self._battery_alert = value["batt"]


class Neviweb130GatewaySensor(Neviweb130Sensor):
    """Implementation of a Neviweb gateway sensor."""

    def __init__(self, data, device_info, name, device_type, sku, firmware, location):
        """Initialize."""
        super().__init__(data, device_info, name, device_type, sku, firmware)
        self._location = str(location)
        self._gateway_status = None
        self._occupancyMode = "home"

    def update(self):
        """Update device."""
        if self._active:
            start = time.time()
            device_status = self._client.get_device_status(self._id)
            neviweb_status = self._client.get_neviweb_status(self._location)
            end = time.time()
            elapsed = round(end - start, 3)
            _LOGGER.debug("Updating %s (%s sec): %s", self._name, elapsed, device_status)
            if "error" not in device_status or device_status is not None:
                if "errorCode" not in device_status:
                    self._gateway_status = device_status[ATTR_STATUS]
                else:
                    _LOGGER.warning(
                        "Error in reading device status for %s: (%s)",
                        self._name,
                        device_status,
                    )
            elif device_status is not None:
                self.log_error(device_status["error"]["code"])
            self._occupancyMode = neviweb_status[ATTR_OCCUPANCY]
            return

    @property
    def gateway_status(self):
        """Return current gateway status: 'online' or 'offline'."""
        return self._gateway_status is not None

    @property
    def state(self):
        """Return the state of the gateway."""
        return self._gateway_status

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

    def set_neviweb_status(self, value):
        """Set Neviweb global occupancy mode, away or home"""
        self._client.post_neviweb_status(self._location, value["mode"])
        self._occupancyMode = value["mode"]
