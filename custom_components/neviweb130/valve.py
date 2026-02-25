"""
Support for Neviweb Zigbee valve connected via GT130 and Wi-Fi valves.

Water valves
model 3150 = VA4201WZ, sedna valve 1 inch via Wi-Fi
model 3150 = VA4200WZ, sedna valve 3/4 inch via Wi-Fi
model 3151 = VA4200ZB, sedna valve 3/4 inch via GT130, Zigbee
model 3153 = VA4220ZB, sedna 2e generation 3/4 inch, Zigbee
model 3150 = VA4220WZ, sedna 2e gen 3/4 inch
model 3155 = ACT4220WF-M, sedna multi-residential master valve 2e gen 3/4 inch, Wi-Fi
model 31532 = ACT4220ZB-M, sedna multi-residential slave valve 2e gen 3/4 inch, Zigbee
model 3150 = VA4220WF, sedna 2e generation 3/4 inch, Wi-Fi
model 3150 = VA4221WZ, sedna 2e gen 1 inch
model 3150 = VA4221WF, sedna 2e generation 1 inch, Wi-Fi
model 3155 = ACT4221WF-M, sedna multi-residential master valve 2e gen. 1 inch, Wi-Fi
model 31532 = ACT4221ZB-M, sedna multi-residential slave valve 2e gen. 1 inch, Zigbee

Flow sensors
FS4220 flow sensor 3/4 inch connected to sedna valve second gen
FS4221 flow sensor 1 inch connected to sedna valve second gen

For more details about this platform, please refer to the documentation at
https://www.sinopetech.com/en/support/#api
"""

from __future__ import annotations

import logging
import time
from datetime import date, datetime, timezone
from enum import StrEnum
from threading import Lock
from typing import cast, override

from homeassistant.components.persistent_notification import DOMAIN as PN_DOMAIN
from homeassistant.components.recorder.models import StatisticMeanType
from homeassistant.components.sensor import SensorDeviceClass
from homeassistant.components.valve import ValveDeviceClass, ValveEntity, ValveEntityFeature
from homeassistant.const import ATTR_ENTITY_ID
from homeassistant.core import ServiceCall
from homeassistant.exceptions import ServiceValidationError

from . import NOTIFY
from . import SCAN_INTERVAL as scan_interval
from . import STAT_INTERVAL
from .const import (
    ATTR_ACTIVE,
    ATTR_AWAY_ACTION,
    ATTR_BATT_ACTION_LOW,
    ATTR_BATT_ALERT,
    ATTR_BATT_PERCENT_NORMAL,
    ATTR_BATT_STATUS_NORMAL,
    ATTR_BATTERY_STATUS,
    ATTR_BATTERY_VOLTAGE,
    ATTR_CLOSE_VALVE,
    ATTR_ERROR_CODE_SET1,
    ATTR_FLOW_ALARM1,
    ATTR_FLOW_ALARM1_LENGTH,
    ATTR_FLOW_ALARM1_OPTION,
    ATTR_FLOW_ALARM1_PERIOD,
    ATTR_FLOW_ALARM2,
    ATTR_FLOW_ALARM_TIMER,
    ATTR_FLOW_ENABLED,
    ATTR_FLOW_METER_CONFIG,
    ATTR_FLOW_MODEL_CONFIG,
    ATTR_FLOW_THRESHOLD,
    ATTR_MOTOR_POS,
    ATTR_MOTOR_TARGET,
    ATTR_OCCUPANCY_SENSOR_DELAY,
    ATTR_ONOFF,
    ATTR_POWER_SUPPLY,
    ATTR_RSSI,
    ATTR_STM8_ERROR,
    ATTR_TEMP_ACTION_LOW,
    ATTR_TEMP_ALARM,
    ATTR_TEMP_ALERT,
    ATTR_TRIGGER_ALARM,
    ATTR_VALVE_CLOSURE,
    ATTR_VALVE_INFO,
    ATTR_WATER_LEAK_STATUS,
    ATTR_WIFI,
    DOMAIN,
    MODE_AUTO,
    MODE_MANUAL,
    MODE_OFF,
    SERVICE_SET_ACTIVATION,
    SERVICE_SET_FLOW_ALARM_DISABLE_TIMER,
    SERVICE_SET_FLOW_METER_DELAY,
    SERVICE_SET_FLOW_METER_MODEL,
    SERVICE_SET_FLOW_METER_OPTIONS,
    SERVICE_SET_POWER_SUPPLY,
    SERVICE_SET_VALVE_ALERT,
    SERVICE_SET_VALVE_TEMP_ALERT,
    STATE_VALVE_STATUS,
    VERSION,
)
from .helpers import file_exists, translate_error
from .schema import (
    SET_ACTIVATION_SCHEMA,
    SET_FLOW_ALARM_DISABLE_TIMER_SCHEMA,
    SET_FLOW_METER_DELAY_SCHEMA,
    SET_FLOW_METER_MODEL_SCHEMA,
    SET_FLOW_METER_OPTIONS_SCHEMA,
    SET_POWER_SUPPLY_SCHEMA,
    SET_VALVE_ALERT_SCHEMA,
    SET_VALVE_TEMP_ALERT_SCHEMA,
)

_LOGGER = logging.getLogger(__name__)

SNOOZE_TIME = 1200
SCAN_INTERVAL = scan_interval

SUPPORT_FLAGS = ValveEntityFeature.OPEN | ValveEntityFeature.CLOSE

UPDATE_ATTRIBUTES = [ATTR_ONOFF]

HA_TO_NEVIWEB_DELAY = {
    "off": 0,
    "1 min": 60,
    "2 min": 120,
    "5 min": 300,
    "10 min": 600,
    "15 min": 900,
    "30 min": 1800,
    "45 min": 2700,
    "60 min": 3600,
    "75 min": 4500,
    "90 min": 5400,
    "1 h": 3600,
    "2 h": 7200,
    "3 h": 10800,
    "6 h": 21600,
    "12 h": 43200,
    "24 h": 86400,
    "48 h": 172800,
    "1 week": 604800,
}

VALVE_TYPES: dict[str, tuple[str, StrEnum, str | None, str | None, StatisticMeanType | None]] = {
    "flow": ("mdi:pipe-valve", SensorDeviceClass.WATER, None, "volume_flow_rate", StatisticMeanType.ARITHMETIC),
    "valve": ("mdi:pipe-valve", ValveDeviceClass.WATER, None, None, None),
}

SUPPORTED_WIFI_MODES = [
    MODE_AUTO,
    MODE_MANUAL,
    MODE_OFF,
]

IMPLEMENTED_WIFI_MESH_VALVE_MODEL = [3155]
IMPLEMENTED_ZB_MESH_VALVE_MODEL = [3153, 31532]
IMPLEMENTED_WIFI_VALVE_MODEL = [3150]
IMPLEMENTED_ZB_VALVE_MODEL = [3151]

IMPLEMENTED_DEVICE_MODEL = (
    IMPLEMENTED_WIFI_VALVE_MODEL
    + IMPLEMENTED_ZB_VALVE_MODEL
    + IMPLEMENTED_WIFI_MESH_VALVE_MODEL
    + IMPLEMENTED_ZB_MESH_VALVE_MODEL
)


async def async_setup_platform(
    hass,
    config,
    async_add_entities,
    discovery_info=None,
) -> None:
    """Set up the Neviweb130 valve."""
    data = hass.data[DOMAIN]["data"]

    # Wait for async migration to be done
    await data.migration_done.wait()

    entities: list[Neviweb130Valve] = []

    # Loop through all clients (supports multi-account)
    for client in data.neviweb130_clients:
        default_name = client.default_group_name("valve")
        default_name_2 = client.default_group_name("valve", 2)
        default_name_3 = client.default_group_name("valve", 3)

        # Process gateway_data for this client
        for device_info in client.gateway_data:
            if (
                "signature" in device_info
                and "model" in device_info["signature"]
                and device_info["signature"]["model"] in IMPLEMENTED_DEVICE_MODEL
            ):
                device_name = "{} {}".format(default_name, device_info["name"])
                device_sku = device_info["sku"]
                device_firmware = "{}.{}.{}".format(
                    device_info["signature"]["softVersion"]["major"],
                    device_info["signature"]["softVersion"]["middle"],
                    device_info["signature"]["softVersion"]["minor"],
                )
                if device_info["signature"]["model"] in IMPLEMENTED_ZB_VALVE_MODEL:
                    device_type = "valve"
                    entities.append(
                        Neviweb130Valve(device_info, device_name, device_sku, device_firmware, device_type, client)
                    )
                elif device_info["signature"]["model"] in IMPLEMENTED_WIFI_VALVE_MODEL:
                    device_type = "valve"
                    entities.append(
                        Neviweb130WifiValve(device_info, device_name, device_sku, device_firmware, device_type, client)
                    )
                elif device_info["signature"]["model"] in IMPLEMENTED_ZB_MESH_VALVE_MODEL:
                    device_type = "flow"
                    entities.append(
                        Neviweb130MeshValve(device_info, device_name, device_sku, device_firmware, device_type, client)
                    )
                else:
                    device_type = "flow"
                    entities.append(
                        Neviweb130WifiMeshValve(
                            device_info, device_name, device_sku, device_firmware, device_type, client
                        )
                    )
        for device_info in client.gateway_data2:
            if (
                "signature" in device_info
                and "model" in device_info["signature"]
                and device_info["signature"]["model"] in IMPLEMENTED_DEVICE_MODEL
            ):
                device_name = "{} {}".format(default_name_2, device_info["name"])
                device_sku = device_info["sku"]
                device_firmware = "{}.{}.{}".format(
                    device_info["signature"]["softVersion"]["major"],
                    device_info["signature"]["softVersion"]["middle"],
                    device_info["signature"]["softVersion"]["minor"],
                )
                if device_info["signature"]["model"] in IMPLEMENTED_ZB_VALVE_MODEL:
                    device_type = "valve"
                    entities.append(
                        Neviweb130Valve(device_info, device_name, device_sku, device_firmware, device_type, client)
                    )
                elif device_info["signature"]["model"] in IMPLEMENTED_WIFI_VALVE_MODEL:
                    device_type = "valve"
                    entities.append(
                        Neviweb130WifiValve(device_info, device_name, device_sku, device_firmware, device_type, client)
                    )
                elif device_info["signature"]["model"] in IMPLEMENTED_ZB_MESH_VALVE_MODEL:
                    device_type = "flow"
                    entities.append(
                        Neviweb130MeshValve(device_info, device_name, device_sku, device_firmware, device_type, client)
                    )
                else:
                    device_type = "flow"
                    entities.append(
                        Neviweb130WifiMeshValve(
                            device_info, device_name, device_sku, device_firmware, device_type, client
                        )
                    )
        for device_info in client.gateway_data3:
            if (
                "signature" in device_info
                and "model" in device_info["signature"]
                and device_info["signature"]["model"] in IMPLEMENTED_DEVICE_MODEL
            ):
                device_name = "{} {}".format(default_name_3, device_info["name"])
                device_sku = device_info["sku"]
                device_firmware = "{}.{}.{}".format(
                    device_info["signature"]["softVersion"]["major"],
                    device_info["signature"]["softVersion"]["middle"],
                    device_info["signature"]["softVersion"]["minor"],
                )
                if device_info["signature"]["model"] in IMPLEMENTED_ZB_VALVE_MODEL:
                    device_type = "valve"
                    entities.append(
                        Neviweb130Valve(device_info, device_name, device_sku, device_firmware, device_type, client)
                    )
                elif device_info["signature"]["model"] in IMPLEMENTED_WIFI_VALVE_MODEL:
                    device_type = "valve"
                    entities.append(
                        Neviweb130WifiValve(device_info, device_name, device_sku, device_firmware, device_type, client)
                    )
                elif device_info["signature"]["model"] in IMPLEMENTED_ZB_MESH_VALVE_MODEL:
                    device_type = "flow"
                    entities.append(
                        Neviweb130MeshValve(device_info, device_name, device_sku, device_firmware, device_type, client)
                    )
                else:
                    device_type = "flow"
                    entities.append(
                        Neviweb130WifiMeshValve(
                            device_info, device_name, device_sku, device_firmware, device_type, client
                        )
                    )

    async_add_entities(entities, True)

    entity_map: dict[str, Neviweb130Valve] | None = None
    _entity_map_lock = Lock()

    def get_valve(service: ServiceCall) -> Neviweb130Valve:
        entity_id = service.data.get(ATTR_ENTITY_ID)
        if entity_id is None:
            msg = translate_error(hass, "missing_parameter", param=ATTR_ENTITY_ID)
            raise ServiceValidationError(msg)

        nonlocal entity_map
        if entity_map is None:
            with _entity_map_lock:
                if entity_map is None:
                    entity_map = {entity.entity_id: entity for entity in entities if entity.entity_id is not None}
                    if len(entity_map) != len(entities):
                        entity_map = None
                        msg = translate_error(hass, "entities_not_ready")
                        raise ServiceValidationError(msg)

        valve = entity_map.get(entity_id)
        if valve is None:
            msg = translate_error(hass, "entity_must_be_domain", entity=entity_id, domain=DOMAIN, platform="valve")
            raise ServiceValidationError(msg)
        return valve

    def set_valve_alert_service(service: ServiceCall) -> None:
        """Set alert for water valve."""
        valve = get_valve(service)
        value = {
            "id": valve.unique_id,
            "batt": service.data[ATTR_BATT_ALERT],
        }
        valve.set_valve_alert(value)
        valve.schedule_update_ha_state(True)

    def set_valve_temp_alert_service(service: ServiceCall) -> None:
        """Set alert for water valve temperature location."""
        valve = get_valve(service)
        value = {
            "id": valve.unique_id,
            "temp": service.data[ATTR_TEMP_ALERT],
        }
        valve.set_valve_temp_alert(value)
        valve.schedule_update_ha_state(True)

    def set_flow_meter_model_service(service: ServiceCall) -> None:
        """Set the flow meter model connected to water valve."""
        valve = get_valve(service)
        value = {
            "id": valve.unique_id,
            "model": service.data[ATTR_FLOW_MODEL_CONFIG][0],
        }
        valve.set_flow_meter_model(value)
        valve.schedule_update_ha_state(True)

    def set_flow_meter_delay_service(service: ServiceCall) -> None:
        """Set the flow meter delay before alert is turned on."""
        valve = get_valve(service)
        value = {
            "id": valve.unique_id,
            "delay": service.data[ATTR_FLOW_ALARM1_PERIOD][0],
        }
        valve.set_flow_meter_delay(value)
        valve.schedule_update_ha_state(True)

    def set_flow_meter_options_service(service: ServiceCall) -> None:
        """Set the flow meter options when leak is detected."""
        valve = get_valve(service)
        value = {
            "id": valve.unique_id,
            "alarm": service.data[ATTR_TRIGGER_ALARM],
            "close": service.data[ATTR_CLOSE_VALVE],
        }
        valve.set_flow_meter_options(value)
        valve.schedule_update_ha_state(True)

    def set_power_supply_service(service: ServiceCall) -> None:
        """Set power supply type for water valve."""
        valve = get_valve(service)
        value = {
            "id": valve.unique_id,
            "supply": service.data[ATTR_POWER_SUPPLY],
        }
        valve.set_power_supply(value)
        valve.schedule_update_ha_state(True)

    def set_activation_service(service: ServiceCall) -> None:
        """Activate or deactivate Neviweb polling for missing device."""
        valve = get_valve(service)
        value = {
            "id": valve.unique_id,
            "active": service.data[ATTR_ACTIVE],
        }
        valve.set_activation(value)
        valve.schedule_update_ha_state(True)

    def set_flow_alarm_disable_timer_service(service: ServiceCall) -> None:
        """Set alert for water valve temperature location."""
        valve = get_valve(service)
        value = {
            "id": valve.unique_id,
            "timer": service.data[ATTR_FLOW_ALARM_TIMER],
        }
        valve.set_flow_alarm_disable_timer(value)
        valve.schedule_update_ha_state(True)

    hass.services.async_register(
        DOMAIN,
        SERVICE_SET_VALVE_ALERT,
        set_valve_alert_service,
        schema=SET_VALVE_ALERT_SCHEMA,
    )

    hass.services.async_register(
        DOMAIN,
        SERVICE_SET_VALVE_TEMP_ALERT,
        set_valve_temp_alert_service,
        schema=SET_VALVE_TEMP_ALERT_SCHEMA,
    )

    hass.services.async_register(
        DOMAIN,
        SERVICE_SET_FLOW_METER_MODEL,
        set_flow_meter_model_service,
        schema=SET_FLOW_METER_MODEL_SCHEMA,
    )

    hass.services.async_register(
        DOMAIN,
        SERVICE_SET_FLOW_METER_DELAY,
        set_flow_meter_delay_service,
        schema=SET_FLOW_METER_DELAY_SCHEMA,
    )

    hass.services.async_register(
        DOMAIN,
        SERVICE_SET_FLOW_METER_OPTIONS,
        set_flow_meter_options_service,
        schema=SET_FLOW_METER_OPTIONS_SCHEMA,
    )

    hass.services.async_register(
        DOMAIN,
        SERVICE_SET_POWER_SUPPLY,
        set_power_supply_service,
        schema=SET_POWER_SUPPLY_SCHEMA,
    )

    hass.services.async_register(
        DOMAIN,
        SERVICE_SET_FLOW_ALARM_DISABLE_TIMER,
        set_flow_alarm_disable_timer_service,
        schema=SET_FLOW_ALARM_DISABLE_TIMER_SCHEMA,
    )

    hass.services.async_register(
        DOMAIN,
        SERVICE_SET_ACTIVATION,
        set_activation_service,
        schema=SET_ACTIVATION_SCHEMA,
    )


def voltage_to_percentage(voltage, num):
    """Convert voltage level from volt to percentage."""
    if num == 2:
        return int((min(voltage, 2.7) - 2.3) / (2.7 - 2.3) * 100)
    else:
        return int((min(voltage, 6.0) - 3.0) / (6.0 - 3.0) * 100)


def alert_to_text(alert, value):
    """Convert numeric alert activation to text."""
    if alert == 1:
        match value:
            case "bat":
                return "Active"
            case "temp":
                return "Active"
    else:
        match value:
            case "bat":
                return "Off"
            case "temp":
                return "Off"

    return None


def neviweb_to_ha_delay(value):
    """Convert Neviweb values to HA values."""
    keys = [k for k, v in HA_TO_NEVIWEB_DELAY.items() if v == value]
    if keys:
        return keys[0]
    return None


def trigger_close(action, alarm):
    """ "No action", "Close and send", "Close only", "Send only." """
    if action:
        if alarm:
            return "Close and send"
        else:
            return "Close only"
    else:
        if alarm:
            return "Send only"
        else:
            return "No action"


def L_2_sqm(value):
    """Convert liters valuer to cubic meter for water flow stat."""
    if value is not None:
        return round(value / 1000, 5)
    else:
        return None


def model_to_HA(value):
    if value == 9887:
        return "FS4221"
    elif value == 4546:
        return "FS4220"
    else:
        return "No flow meter"


class Neviweb130Valve(ValveEntity):
    """Implementation of a Neviweb valve."""

    def __init__(self, device_info, name, sku, firmware, device_type, client):
        """Initialize."""
        _LOGGER.debug("Setting up %s: %s", name, device_info)
        self._name = name
        self._sku = sku
        self._firmware = firmware
        self._client = client
        self._id = str(device_info["id"])
        self._device_model = device_info["signature"]["model"]
        self._device_model_cfg = device_info["signature"]["modelCfg"]
        self._device_type = device_type
        self._is_zb_valve = device_info["signature"]["model"] in IMPLEMENTED_ZB_VALVE_MODEL
        self._is_wifi_valve = device_info["signature"]["model"] in IMPLEMENTED_WIFI_VALVE_MODEL
        self._is_zb_mesh_valve = device_info["signature"]["model"] in IMPLEMENTED_ZB_MESH_VALVE_MODEL
        self._is_wifi_mesh_valve = device_info["signature"]["model"] in IMPLEMENTED_WIFI_MESH_VALVE_MODEL
        self._active = True
        self._batt_percent_normal = None
        self._batt_status_normal = None
        self._battery_alert = 0
        self._battery_status = None
        self._battery_voltage = 0
        self._daily_kwh_count = 0
        self._energy_stat_time = time.time() - 1500
        self._flowmeter_alarm_length = 0
        self._flowmeter_alert_delay = 0
        self._flowmeter_model = None
        self._flowmeter_multiplier = 0
        self._flowmeter_opt_action = None
        self._flowmeter_opt_alarm = None
        self._flowmeter_threshold = 1
        self._flowmeter_timer = 0
        self._hour_kwh = 0
        self._hourly_kwh_count = 0
        self._mark = None
        self._marker = None
        self._month_kwh = 0
        self._monthly_kwh_count = 0
        self._onoff = None
        self._power_supply = None
        self._reports_position = False
        self._rssi = None
        self._snooze = 0.0
        self._temp_alert = None
        self._today_kwh = 0
        self._total_kwh_count = 0
        self._valve_status: str | None = None
        self._water_leak_status: str | None = None

    def update(self):
        if self._active:
            LOAD_ATTRIBUTES = [
                ATTR_BATTERY_VOLTAGE,
                ATTR_BATTERY_STATUS,
                ATTR_POWER_SUPPLY,
                ATTR_RSSI,
                ATTR_BATT_PERCENT_NORMAL,
                ATTR_BATT_STATUS_NORMAL,
            ]
            """Get the latest data from Neviweb and update the state."""
            start = time.time()
            device_data = self._client.get_device_attributes(self._id, UPDATE_ATTRIBUTES + LOAD_ATTRIBUTES)
            end = time.time()
            elapsed = round(end - start, 3)
            device_alert = None
            if self._is_zb_valve or self._is_zb_mesh_valve:
                device_alert = self._client.get_device_alert(self._id)
                _LOGGER.debug(
                    "Updating alert for %s (%s sec): %s",
                    self._name,
                    elapsed,
                    device_alert,
                )
            _LOGGER.debug("Updating %s (%s sec): %s", self._name, elapsed, device_data)
            if "error" not in device_data:
                if "errorCode" not in device_data:
                    self._valve_status = STATE_VALVE_STATUS if device_data[ATTR_ONOFF] == "on" else "closed"
                    self._onoff = device_data[ATTR_ONOFF]
                    self._battery_voltage = (
                        device_data[ATTR_BATTERY_VOLTAGE] if device_data[ATTR_BATTERY_VOLTAGE] is not None else 0
                    )
                    self._battery_status = device_data[ATTR_BATTERY_STATUS]
                    self._power_supply = device_data[ATTR_POWER_SUPPLY]
                    if device_alert is not None and ATTR_BATT_ALERT in device_alert:
                        self._battery_alert = device_alert[ATTR_BATT_ALERT]
                    if device_alert is not None and ATTR_TEMP_ALERT in device_alert:
                        self._temp_alert = device_alert[ATTR_TEMP_ALERT]
                    if ATTR_RSSI in device_data:
                        self._rssi = device_data[ATTR_RSSI]
                    if ATTR_BATT_PERCENT_NORMAL in device_data:
                        self._batt_percent_normal = device_data[ATTR_BATT_PERCENT_NORMAL]
                    if ATTR_BATT_STATUS_NORMAL in device_data:
                        self._batt_status_normal = device_data[ATTR_BATT_STATUS_NORMAL]
                else:
                    _LOGGER.warning("Error in reading device %s: (%s)", self._name, device_data)
            else:
                self.log_error(device_data["error"]["code"])
        else:
            if time.time() - self._snooze > SNOOZE_TIME:
                self._active = True
                if NOTIFY == "notification" or NOTIFY == "both":
                    self.notify_ha(translate_error(self.hass, "update_restarted", name=self._name, sku=self._sku))

    @property
    @override
    def unique_id(self) -> str:
        """Return unique ID based on Neviweb device ID."""
        return self._client.scoped_unique_id(self._id)

    @property
    @override
    def name(self) -> str:
        """Return the name of the valve."""
        return self._name

    @property
    @override
    def icon(self) -> str | None:
        """Return the icon to use in the frontend."""
        device_info = VALVE_TYPES.get(self._device_type)
        if device_info is None:
            return None

        return device_info[0]

    @property
    def entity_picture(self) -> str | None:
        """Replace entity picture by valve or leak icon."""
        icon_path = self.icon_type
        if file_exists(self.hass, icon_path):
            return icon_path

        return None

    @property
    @override
    def device_class(self) -> ValveDeviceClass | None:
        """Return the device class of this entity."""
        device_type = VALVE_TYPES.get(self._device_type)
        if device_type is None:
            return None

        return cast(ValveDeviceClass, device_type[1])

    @property
    @override
    def unit_of_measurement(self) -> str | None:
        return VALVE_TYPES.get(self._device_type, (None, None, None, None, None))[2]

    @property
    def unit_class(self) -> str | None:
        return VALVE_TYPES.get(self._device_type, (None, None, None, None, None))[3]

    @property
    def statistic_mean_type(self) -> StatisticMeanType | None:
        return VALVE_TYPES.get(self._device_type, (None, None, None, None, None))[4]

    @property
    def is_open(self):
        """Return current operation i.e. OPEN, CLOSED."""
        return self._onoff != MODE_OFF

    @property
    def is_closed(self):
        """Return current operation i.e. ON, OFF."""
        return self._onoff == MODE_OFF

    @property
    def reports_position(self):
        """Return current position True or False."""
        return self._reports_position

    @property
    def valve_status(self):
        """Return current valve status, open or closed."""
        return self._valve_status is not None

    @property
    def icon_type(self) -> str:
        """Select valve icon based on valve state and leak status."""
        if self._water_leak_status == "water":
            return "/local/neviweb130/leak.png"
        return "/local/neviweb130/valve-open.png" if self.is_open else "/local/neviweb130/valve-close.png"

    @property
    def leak_icon(self) -> str | None:
        """Select icon file based on leak_status value."""
        if self._water_leak_status is not None:
            return "/local/neviweb130/drop.png" if self._water_leak_status == "ok" else "/local/neviweb130/leak.png"
        return None

    @property
    def battery_icon(self) -> str:
        """Return battery icon file based on battery voltage."""
        if self._battery_voltage is None or self._battery_voltage == 0:
            return "/local/neviweb130/battery-unknown.png"

        batt = voltage_to_percentage(self._battery_voltage, 4)
        level = min(batt // 20 + 1, 5)
        return f"/local/neviweb130/battery-{level}.png"

    def open_valve(self, **kwargs):
        """Open the valve."""
        if self._is_wifi_valve or self._is_wifi_mesh_valve:
            self._client.set_valve_onoff(self._id, 100)
            self._valve_status = "open"
        else:
            self._client.set_onoff(self._id, "on")
            if self._is_zb_valve or self._is_zb_mesh_valve:
                self._valve_status = "open"
        self._onoff = "on"

    def close_valve(self, **kwargs):
        """Close the valve."""
        if self._is_wifi_valve or self._is_wifi_mesh_valve:
            self._client.set_valve_onoff(self._id, 0)
            self._valve_status = "closed"
        else:
            self._client.set_onoff(self._id, "off")
            if self._is_zb_valve or self._is_zb_mesh_valve:
                self._valve_status = "closed"
        self._onoff = MODE_OFF

    @property
    def extra_state_attributes(self):
        """Return the extra state attributes."""
        data = {}
        data.update(
            {
                "valve_status": self._valve_status,
                "battery_level": voltage_to_percentage(self._battery_voltage, 4),
                "battery_voltage": self._battery_voltage,
                "battery_status": self._battery_status,
                "battery_icon": self.battery_icon,
                "power_supply": self._power_supply,
                "battery_alert": alert_to_text(self._battery_alert, "bat"),
                "temperature_alert": alert_to_text(self._temp_alert, "temp"),
                "battery_percent_normalized": self._batt_percent_normal,
                "battery_status_normalized": self._batt_status_normal,
                "sku": self._sku,
                "device_model": str(self._device_model),
                "device_model_cfg": self._device_model_cfg,
                "firmware": self._firmware,
                "activation": self._active,
                "device_type": self._device_type,
                "id": self._id,
            }
        )
        return data

    @property
    def supported_features(self):
        """Return the list of supported features."""
        return SUPPORT_FLAGS

    @property
    def battery_voltage(self):
        """Return the current battery voltage of the valve in %."""
        return voltage_to_percentage(self._battery_voltage, 2 if self._is_zb_valve or self._is_zb_mesh_valve else 4)

    def set_valve_alert(self, value):
        """Set valve batt alert action."""
        if self._is_zb_valve or self._is_zb_mesh_valve:
            if value["batt"] == "true":
                batt = 1
            else:
                batt = 0
        else:
            batt = value["batt"]
        self._client.set_valve_alert(value["id"], batt)
        self._battery_alert = batt

    def set_valve_temp_alert(self, value):
        """Set valve temperature alert action."""
        self._client.set_valve_temp_alert(value["id"], value["temp"])
        self._temp_alert = value["temp"]

    def set_flow_meter_model(self, value):
        """Set water valve flow meter model connected."""
        self._client.set_flow_meter_model(value["id"], value["model"])
        self._flowmeter_model = value["model"]

    def set_flow_alarm_disable_timer(self, value):
        """Set flowmeter alarm action disabled timer, for valves with flowmeter."""
        self._client.set_flow_alarm_timer(value["id"], value["timer"])
        self._flowmeter_timer = value["timer"]

    def set_flow_meter_delay(self, value):
        """Set water valve flow meter delay before alert."""
        val = value["delay"]
        delay = [v for k, v in HA_TO_NEVIWEB_DELAY.items() if k == val][0]
        self._client.set_flow_meter_delay(value["id"], delay)
        self._flowmeter_alert_delay = val

    def set_power_supply(self, value):
        """Set water valve power supply type."""
        sup = None
        match value["supply"]:
            case "batt":
                sup = "batteries"
            case "power":
                sup = "acups-01"
            case _:
                sup = "both"
        self._client.set_power_supply(value["id"], sup)
        self._power_supply = sup

    def set_flow_meter_options(self, value):
        """Set water valve flow meter options when leak detected."""
        if value["alarm"] == "on":
            alarm = True
        else:
            alarm = False
        if value["close"] == "on":
            action = True
        else:
            action = False
        if not alarm and not action:
            length = 0
            threshold = 0
        else:
            length = 60
            threshold = 1
        self._client.set_flow_meter_options(value["id"], alarm, action, length, threshold)
        self._flowmeter_opt_alarm = alarm
        self._flowmeter_opt_action = action
        self._flowmeter_threshold = threshold
        self._flowmeter_alarm_length = length

    def set_activation(self, value):
        """Activate or deactivate neviweb polling for a missing device."""
        self._active = value["active"]

    def do_stat(self, start):
        """Get device flow statistic."""
        if self._flowmeter_multiplier != 0:
            if start - self._energy_stat_time > STAT_INTERVAL and self._energy_stat_time != 0:
                today = date.today()
                current_month = today.month
                current_day = today.day
                device_monthly_stats = self._client.get_device_monthly_stats(self._id, False)
                _LOGGER.debug("%s device_monthly_stats = %s", self._name, device_monthly_stats)
                if device_monthly_stats is not None and len(device_monthly_stats) > 1:
                    n = len(device_monthly_stats)
                    monthly_kwh_count = 0
                    k = 0
                    while k < n:
                        monthly_kwh_count += device_monthly_stats[k]["period"]  # / 1000
                        k += 1
                    self._monthly_kwh_count = round(monthly_kwh_count, 2)
                    self._month_kwh = round(device_monthly_stats[n - 1]["period"], 2)
                    dt_month = datetime.fromisoformat(device_monthly_stats[n - 1]["date"][:-1] + "+00:00").astimezone(
                        timezone.utc
                    )
                    _LOGGER.debug("stat month = %s", dt_month.month)
                else:
                    self._month_kwh = 0
                    msg = translate_error(self.hass, "no_stat", param="monthly", name=self._name)
                    _LOGGER.warning(msg)
                device_daily_stats = self._client.get_device_daily_stats(self._id, False)
                _LOGGER.debug("%s device_daily_stats = %s", self._name, device_daily_stats)
                if device_daily_stats is not None and len(device_daily_stats) > 1:
                    n = len(device_daily_stats)
                    daily_kwh_count = 0
                    k = 0
                    while k < n:
                        if (
                            datetime.fromisoformat(device_daily_stats[k]["date"][:-1] + "+00:00")
                            .astimezone(timezone.utc)
                            .month
                            == current_month
                        ):
                            daily_kwh_count += device_daily_stats[k]["period"]  # / 1000
                        k += 1
                    self._daily_kwh_count = round(daily_kwh_count, 2)
                    self._today_kwh = round(device_daily_stats[n - 1]["period"], 2)
                    dt_day = datetime.fromisoformat(device_daily_stats[n - 1]["date"][:-1].replace("Z", "+00:00"))
                    _LOGGER.debug("stat day = %s", dt_day.day)
                else:
                    self._today_kwh = 0
                    msg = translate_error(self.hass, "no_stat", param="daily", name=self._name)
                    _LOGGER.warning(msg)
                device_hourly_stats = self._client.get_device_hourly_stats(self._id, False)
                _LOGGER.debug("%s device_hourly_stats = %s", self._name, device_hourly_stats)
                if device_hourly_stats is not None and len(device_hourly_stats) > 1:
                    n = len(device_hourly_stats)
                    hourly_kwh_count = 0
                    k = 0
                    while k < n:
                        if (
                            datetime.fromisoformat(device_hourly_stats[k]["date"][:-1].replace("Z", "+00:00")).day
                            == current_day
                        ):
                            hourly_kwh_count += device_hourly_stats[k]["period"]  # / 1000
                        k += 1
                    self._hourly_kwh_count = round(hourly_kwh_count, 2)
                    self._hour_kwh = round(device_hourly_stats[n - 1]["period"], 2)
                    self._marker = device_hourly_stats[n - 1]["date"]
                    dt_hour = datetime.strptime(device_hourly_stats[n - 1]["date"], "%Y-%m-%dT%H:%M:%S.%fZ")
                    _LOGGER.debug("stat hour = %s", dt_hour.hour)
                else:
                    self._hour_kwh = 0
                    msg = translate_error(self.hass, "no_stat", param="hourly", name=self._name)
                    _LOGGER.warning(msg)
                if self._total_kwh_count == 0:
                    self._total_kwh_count = round(
                        self._monthly_kwh_count + self._daily_kwh_count + self._hourly_kwh_count,
                        3,
                    )
                    # async_add_data(self._id, self._total_kwh_count, self._marker)
                    # self.async_write_ha_state()
                    self._mark = self._marker
                else:
                    if self._marker != self._mark:
                        self._total_kwh_count += round(self._hour_kwh, 3)
                        # save_data(self._id, self._total_kwh_count, self._marker)
                        self._mark = self._marker
                self._energy_stat_time = time.time()
            if self._energy_stat_time == 0:
                self._energy_stat_time = start
        else:
            self._hour_kwh = 0
            self._today_kwh = 0
            self._month_kwh = 0

    def log_error(self, error_data):
        """Send error message to LOG."""
        if error_data == "USRSESSEXP":
            _LOGGER.warning("Session expired... Reconnecting...")
            if NOTIFY == "notification" or NOTIFY == "both":
                self.notify_ha(
                    "Warning: Got USRSESSEXP error, Neviweb session expired. "
                    + "Set your scan_interval parameter to less than 10 minutes "
                    + "to avoid this... Reconnecting..."
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
                + " (SKU: %s)",
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
                msg = translate_error(self.hass, "update_stopped", name=self._name, id=self._id, sku=self._sku)
                _LOGGER.warning("%s:", error_data, msg)
                _LOGGER.warning(
                    "You can re-activate device %s with "
                    + "service.neviweb130_set_activation or wait 20 minutes "
                    + "for update to restart or just restart HA",
                    self._name,
                )
            if NOTIFY == "notification" or NOTIFY == "both":
                self.notify_ha(msg)
            self._active = False
            self._snooze = time.time()
        else:
            msg = translate_error(
                self.hass, "unknown_error", name=self._name, id=self._id, sku=self._sku, data=error_data
            )
            _LOGGER.warning(msg)

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


class Neviweb130WifiValve(Neviweb130Valve):
    """Implementation of a Neviweb Wi-Fi valve, VA4200WZ, VA4201WZ, VA4220WZ, VA4221WZ, VA4220WF, VA4221WF."""

    def __init__(self, device_info, name, sku, firmware, device_type, client):
        """Initialize."""
        super().__init__(device_info, name, sku, firmware, device_type, client)
        self._away_action = None
        self._batt_action_low = None
        self._flowmeter_divisor = 1
        self._flowmeter_offset = 0
        self._flowmeter_opt_action_1 = None
        self._flowmeter_opt_action_2 = None
        self._flowmeter_opt_alarm_1 = None
        self._flowmeter_opt_alarm_2 = None
        self._flowmeter_opt_duration_1 = 0
        self._flowmeter_opt_duration_2 = 0
        self._flowmeter_opt_flow_min_1 = 1
        self._flowmeter_opt_flow_min_2 = 1
        self._flowmeter_opt_observationPeriod_1 = 0
        self._flowmeter_opt_observationPeriod_2 = 0
        self._motor_target = None
        self._occupancy_delay = None
        self._stm8Error_motorJam = None
        self._stm8Error_motorLimit = None
        self._stm8Error_motorPosition = None
        self._temp_action_low = None
        self._valve_closure = None
        self._valve_info_cause = None
        self._valve_info_id = None
        self._valve_info_status = None
        self._water_leak_status = None

    def update(self):
        if self._active:
            LOAD_ATTRIBUTES = [
                ATTR_WIFI,
                ATTR_MOTOR_POS,
                ATTR_MOTOR_TARGET,
                ATTR_TEMP_ALARM,
                ATTR_VALVE_INFO,
                ATTR_BATTERY_VOLTAGE,
                ATTR_BATTERY_STATUS,
                ATTR_POWER_SUPPLY,
                ATTR_VALVE_CLOSURE,
                ATTR_BATT_ALERT,
                ATTR_STM8_ERROR,
                ATTR_FLOW_METER_CONFIG,
                ATTR_FLOW_ALARM1,
                ATTR_FLOW_ALARM2,
                ATTR_TEMP_ACTION_LOW,
                ATTR_BATT_ACTION_LOW,
                ATTR_OCCUPANCY_SENSOR_DELAY,
                ATTR_BATT_STATUS_NORMAL,
                ATTR_BATT_PERCENT_NORMAL,
                ATTR_WATER_LEAK_STATUS,
                ATTR_AWAY_ACTION,
            ]
            """Get the latest data from Neviweb and update the state."""
            start = time.time()
            device_data = self._client.get_device_attributes(self._id, UPDATE_ATTRIBUTES + LOAD_ATTRIBUTES)
            end = time.time()
            elapsed = round(end - start, 3)
            _LOGGER.debug("Updating %s (%s sec): %s", self._name, elapsed, device_data)
            if "error" not in device_data:
                if "errorCode" not in device_data:
                    self._valve_status = STATE_VALVE_STATUS if device_data[ATTR_MOTOR_POS] == 100 else "closed"
                    self._onoff = "on" if self._valve_status == STATE_VALVE_STATUS else MODE_OFF
                    self._temp_alert = device_data[ATTR_TEMP_ALARM]
                    self._battery_voltage = (
                        device_data[ATTR_BATTERY_VOLTAGE] if device_data[ATTR_BATTERY_VOLTAGE] is not None else 0
                    )
                    self._battery_status = device_data[ATTR_BATTERY_STATUS]
                    self._power_supply = device_data[ATTR_POWER_SUPPLY]
                    self._battery_alert = device_data[ATTR_BATT_ALERT]
                    if ATTR_WATER_LEAK_STATUS in device_data:
                        self._water_leak_status = device_data[ATTR_WATER_LEAK_STATUS]
                        if (
                            self._water_leak_status == "flowMeter"
                            and device_data[ATTR_FLOW_METER_CONFIG]["offset"] != 0
                        ):
                            msg = translate_error(
                                self.hass,
                                "error_code",
                                code=device_data[ATTR_WATER_LEAK_STATUS],
                                message="",
                                name=self._name,
                                id=self._id,
                                sku=self._sku,
                            )
                            self.notify_ha(msg)
                    if ATTR_MOTOR_TARGET in device_data:
                        self._motor_target = device_data[ATTR_MOTOR_TARGET]
                    if ATTR_VALVE_CLOSURE in device_data:
                        self._valve_closure = device_data[ATTR_VALVE_CLOSURE]["source"]
                    if ATTR_VALVE_INFO in device_data:
                        self._valve_info_status = device_data[ATTR_VALVE_INFO]["status"]
                        self._valve_info_cause = device_data[ATTR_VALVE_INFO]["cause"]
                        self._valve_info_id = device_data[ATTR_VALVE_INFO]["identifier"]
                    if ATTR_STM8_ERROR in device_data:
                        self._stm8Error_motorJam = device_data[ATTR_STM8_ERROR]["motorJam"]
                        if "motorPosition" in device_data[ATTR_STM8_ERROR]:
                            self._stm8Error_motorPosition = device_data[ATTR_STM8_ERROR]["motorPosition"]
                        if "motorLimit" in device_data[ATTR_STM8_ERROR]:
                            self._stm8Error_motorLimit = device_data[ATTR_STM8_ERROR]["motorLimit"]
                    if ATTR_FLOW_METER_CONFIG in device_data:
                        self._flowmeter_multiplier = device_data[ATTR_FLOW_METER_CONFIG]["multiplier"]
                        self._flowmeter_offset = device_data[ATTR_FLOW_METER_CONFIG]["offset"]
                        self._flowmeter_divisor = device_data[ATTR_FLOW_METER_CONFIG]["divisor"]
                    if ATTR_FLOW_ALARM1 in device_data:
                        self._flowmeter_opt_alarm_1 = device_data[ATTR_FLOW_ALARM1]["actions"][ATTR_TRIGGER_ALARM]
                        self._flowmeter_opt_action_1 = device_data[ATTR_FLOW_ALARM1]["actions"][ATTR_CLOSE_VALVE]
                        self._flowmeter_opt_flow_min_1 = device_data[ATTR_FLOW_ALARM1]["flowMin"]
                        self._flowmeter_opt_duration_1 = device_data[ATTR_FLOW_ALARM1]["duration"]
                        self._flowmeter_opt_observationPeriod_1 = device_data[ATTR_FLOW_ALARM1]["observationPeriod"]
                    if ATTR_FLOW_ALARM2 in device_data:
                        self._flowmeter_opt_alarm_2 = device_data[ATTR_FLOW_ALARM2]["actions"][ATTR_TRIGGER_ALARM]
                        self._flowmeter_opt_action_2 = device_data[ATTR_FLOW_ALARM2]["actions"][ATTR_CLOSE_VALVE]
                        self._flowmeter_opt_flow_min_2 = device_data[ATTR_FLOW_ALARM2]["flowMin"]
                        self._flowmeter_opt_duration_2 = device_data[ATTR_FLOW_ALARM2]["duration"]
                        self._flowmeter_opt_observationPeriod_2 = device_data[ATTR_FLOW_ALARM2]["observationPeriod"]
                    if ATTR_TEMP_ACTION_LOW in device_data:
                        self._temp_action_low = device_data[ATTR_TEMP_ACTION_LOW]
                    if ATTR_BATT_ACTION_LOW in device_data:
                        self._batt_action_low = device_data[ATTR_BATT_ACTION_LOW]
                    if ATTR_OCCUPANCY_SENSOR_DELAY in device_data:
                        self._occupancy_delay = device_data[ATTR_OCCUPANCY_SENSOR_DELAY]
                    if ATTR_WIFI in device_data:
                        self._rssi = device_data[ATTR_WIFI]
                    if ATTR_BATT_PERCENT_NORMAL in device_data:
                        self._batt_percent_normal = device_data[ATTR_BATT_PERCENT_NORMAL]
                    if ATTR_BATT_STATUS_NORMAL in device_data:
                        self._batt_status_normal = device_data[ATTR_BATT_STATUS_NORMAL]
                    if ATTR_AWAY_ACTION in device_data:
                        self._away_action = device_data[ATTR_AWAY_ACTION]
                else:
                    _LOGGER.warning("Error in reading device %s: (%s)", self._name, device_data)
            else:
                self.log_error(device_data["error"]["code"])
            self.do_stat(start)
        else:
            if time.time() - self._snooze > SNOOZE_TIME:
                self._active = True
                if NOTIFY == "notification" or NOTIFY == "both":
                    self.notify_ha(translate_error(self.hass, "update_restarted", name=self._name, sku=self._sku))

    @property
    def extra_state_attributes(self):
        """Return the extra state attributes."""
        data = {}
        data.update(
            {
                "valve_status": self._valve_status,
                "temperature_alert": self._temp_alert,
                "leak_icon": self.leak_icon,
                "icon_type": self.icon_type,
                "battery_level": voltage_to_percentage(self._battery_voltage, 4),
                "battery_voltage": self._battery_voltage,
                "battery_status": self._battery_status,
                "battery_icon": self.battery_icon,
                "power_supply": self._power_supply,
                "valve_closure_source": self._valve_closure,
                "battery_alert": self._battery_alert,
                "motor_target_position": self._motor_target,
                "water_leak_status": self._water_leak_status,
                "valve_info_status": self._valve_info_status,
                "valve_cause": self._valve_info_cause,
                "valve_info_id": self._valve_info_id,
                "alert_motor_jam": self._stm8Error_motorJam,
                "alert_motor_position": self._stm8Error_motorPosition,
                "alert_motor_limit": self._stm8Error_motorLimit,
                "away_action": self._away_action,
                "flow_meter_alarm_delay_1": neviweb_to_ha_delay(self._flowmeter_opt_observationPeriod_1),
                "flow_meter_alarm_duration_1": neviweb_to_ha_delay(self._flowmeter_opt_duration_1),
                "flow_meter_alarm_flowMin_1": self._flowmeter_opt_flow_min_1,
                "flowmeter_options_1": trigger_close(self._flowmeter_opt_action_1, self._flowmeter_opt_alarm_1),
                "flow_meter_alarm_delay_2": neviweb_to_ha_delay(self._flowmeter_opt_observationPeriod_2),
                "flow_meter_alarm_duration_2": neviweb_to_ha_delay(self._flowmeter_opt_duration_2),
                "flow_meter_alarm_flowMin_2": self._flowmeter_opt_flow_min_2,
                "flowmeter_options_2": trigger_close(self._flowmeter_opt_action_2, self._flowmeter_opt_alarm_2),
                "temp_action_low": self._temp_action_low,
                "batt_action_low": self._batt_action_low,
                "battery_percent_normalized": self._batt_percent_normal,
                "battery_status_normalized": self._batt_status_normal,
                "flow_meter_multiplier": self._flowmeter_multiplier,
                "flow_meter_offset": self._flowmeter_offset,
                "flow_meter_divisor": self._flowmeter_divisor,
                "occupancy_sensor_delay": neviweb_to_ha_delay(self._occupancy_delay),
                "total_flow_count": L_2_sqm(self._total_kwh_count),
                "monthly_flow_count": L_2_sqm(self._monthly_kwh_count),
                "daily_flow_count": L_2_sqm(self._daily_kwh_count),
                "hourly_flow_count": L_2_sqm(self._hourly_kwh_count),
                "hourly_flow": L_2_sqm(self._hour_kwh),
                "daily_flow": L_2_sqm(self._today_kwh),
                "monthly_flow": L_2_sqm(self._month_kwh),
                "last_flow_stat_update": self._mark,
                "rssi": self._rssi,
                "sku": self._sku,
                "device_model": str(self._device_model),
                "device_model_cfg": self._device_model_cfg,
                "firmware": self._firmware,
                "activation": self._active,
                "device_type": self._device_type,
                "id": self._id,
            }
        )
        return data


class Neviweb130MeshValve(Neviweb130Valve):
    """Implementation of a Neviweb mesh valve VA4220ZB and ACT4220ZB-M."""

    def __init__(self, device_info, name, sku, firmware, device_type, client):
        """Initialize."""
        super().__init__(device_info, name, sku, firmware, device_type, client)
        self._error_code = 0
        self._flowmeter_divisor = 1
        self._flowmeter_enabled = None
        self._flowmeter_offset = 0
        self._flowmeter_opt_action = None
        self._stm8Error_motorJam = None
        self._stm8Error_motorLimit = None
        self._stm8Error_motorPosition = None
        self._water_leak_status = None

    def update(self):
        if self._active:
            LOAD_ATTRIBUTES = [
                ATTR_RSSI,
                ATTR_BATTERY_VOLTAGE,
                ATTR_BATTERY_STATUS,
                ATTR_POWER_SUPPLY,
                ATTR_STM8_ERROR,
                ATTR_WATER_LEAK_STATUS,
                ATTR_FLOW_METER_CONFIG,
                ATTR_FLOW_ALARM_TIMER,
                ATTR_FLOW_THRESHOLD,
                ATTR_FLOW_ALARM1_PERIOD,
                ATTR_FLOW_ALARM1_LENGTH,
                ATTR_FLOW_ALARM1_OPTION,
                ATTR_FLOW_ENABLED,
                ATTR_BATT_STATUS_NORMAL,
                ATTR_BATT_PERCENT_NORMAL,
                ATTR_ERROR_CODE_SET1,
            ]
            """Get the latest data from Neviweb and update the state."""
            start = time.time()
            device_data = self._client.get_device_attributes(self._id, UPDATE_ATTRIBUTES + LOAD_ATTRIBUTES)
            end = time.time()
            elapsed = round(end - start, 3)
            device_alert = None
            if self._is_zb_valve or self._is_zb_mesh_valve:
                device_alert = self._client.get_device_alert(self._id)
                _LOGGER.debug(
                    "Updating alert for %s (%s sec): %s",
                    self._name,
                    elapsed,
                    device_alert,
                )
            _LOGGER.debug("Updating %s (%s sec): %s", self._name, elapsed, device_data)
            if "error" not in device_data:
                if "errorCode" not in device_data:
                    self._valve_status = STATE_VALVE_STATUS if device_data[ATTR_ONOFF] == "on" else "closed"
                    self._onoff = device_data[ATTR_ONOFF]
                    self._battery_voltage = (
                        device_data[ATTR_BATTERY_VOLTAGE] if device_data[ATTR_BATTERY_VOLTAGE] is not None else 0
                    )
                    self._battery_status = device_data[ATTR_BATTERY_STATUS]
                    self._power_supply = device_data[ATTR_POWER_SUPPLY]
                    if device_alert is not None and ATTR_BATT_ALERT in device_alert:
                        self._battery_alert = device_alert[ATTR_BATT_ALERT]
                    if ATTR_STM8_ERROR in device_data:
                        self._stm8Error_motorJam = device_data[ATTR_STM8_ERROR]["motorJam"]
                        self._stm8Error_motorLimit = device_data[ATTR_STM8_ERROR]["motorLimit"]
                        self._stm8Error_motorPosition = device_data[ATTR_STM8_ERROR]["motorPosition"]
                    if ATTR_FLOW_METER_CONFIG in device_data:
                        self._flowmeter_multiplier = device_data[ATTR_FLOW_METER_CONFIG]["multiplier"]
                        self._flowmeter_offset = device_data[ATTR_FLOW_METER_CONFIG]["offset"]
                        self._flowmeter_divisor = device_data[ATTR_FLOW_METER_CONFIG]["divisor"]
                        self._flowmeter_model = model_to_HA(self._flowmeter_multiplier)
                    self._water_leak_status = device_data[ATTR_WATER_LEAK_STATUS]
                    if self._water_leak_status == "flowMeter" and device_data[ATTR_FLOW_METER_CONFIG]["offset"] != 0:
                        msg = translate_error(
                            self.hass,
                            "error_code",
                            code=device_data[ATTR_WATER_LEAK_STATUS],
                            message="",
                            name=self._name,
                            id=self._id,
                            sku=self._sku,
                        )
                        self.notify_ha(msg)
                    if ATTR_FLOW_ALARM_TIMER in device_data:
                        self._flowmeter_timer = device_data[ATTR_FLOW_ALARM_TIMER]
                        if self._flowmeter_timer == 0 and ATTR_FLOW_THRESHOLD in device_data:
                            self._flowmeter_threshold = device_data[ATTR_FLOW_THRESHOLD]
                            self._flowmeter_alert_delay = device_data[ATTR_FLOW_ALARM1_PERIOD]
                            self._flowmeter_alarm_length = device_data[ATTR_FLOW_ALARM1_LENGTH]
                            self._flowmeter_opt_alarm = device_data[ATTR_FLOW_ALARM1_OPTION][ATTR_TRIGGER_ALARM]
                            self._flowmeter_opt_action = device_data[ATTR_FLOW_ALARM1_OPTION][ATTR_CLOSE_VALVE]
                    if ATTR_BATT_PERCENT_NORMAL in device_data:
                        self._batt_percent_normal = device_data[ATTR_BATT_PERCENT_NORMAL]
                    if ATTR_BATT_STATUS_NORMAL in device_data:
                        self._batt_status_normal = device_data[ATTR_BATT_STATUS_NORMAL]
                    if ATTR_RSSI in device_data:
                        self._rssi = device_data[ATTR_RSSI]
                    if ATTR_FLOW_ENABLED in device_data:
                        self._flowmeter_enabled = device_data[ATTR_FLOW_ENABLED]
                    if ATTR_ERROR_CODE_SET1 in device_data and len(device_data[ATTR_ERROR_CODE_SET1]) > 0:
                        if device_data[ATTR_ERROR_CODE_SET1]["raw"] != 0:
                            self._error_code = device_data[ATTR_ERROR_CODE_SET1]["raw"]
                            msg = translate_error(
                                self.hass,
                                "error_code",
                                code=str(device_data[ATTR_ERROR_CODE_SET1]["raw"]),
                                message="",
                                name=self._name,
                                id=self._id,
                                sku=self._sku,
                            )
                            self.notify_ha(msg)
                            _LOGGER.warning(
                                "Error code set1 updated: %s",
                                str(device_data[ATTR_ERROR_CODE_SET1]["raw"]),
                            )
                    else:
                        self._error_code = 0
                else:
                    _LOGGER.warning("Error reading device %s: (%s)", self._name, device_data)
            else:
                self.log_error(device_data["error"]["code"])
            self.do_stat(start)
        else:
            if time.time() - self._snooze > SNOOZE_TIME:
                self._active = True
                if NOTIFY == "notification" or NOTIFY == "both":
                    self.notify_ha(translate_error(self.hass, "update_restarted", name=self._name, sku=self._sku))

    @property
    def extra_state_attributes(self):
        """Return the extra state attributes."""
        data = {}
        data.update(
            {
                "battery_level": voltage_to_percentage(self._battery_voltage, 4),
                "battery_voltage": self._battery_voltage,
                "battery_status": self._battery_status,
                "battery_icon": self.battery_icon,
                "battery_percent_normalized": self._batt_percent_normal,
                "battery_status_normalized": self._batt_status_normal,
                "leak_icon": self.leak_icon,
                "icon_type": self.icon_type,
                "power_supply": self._power_supply,
                "alert_motor_jam": self._stm8Error_motorJam,
                "alert_motor_position": self._stm8Error_motorPosition,
                "alert_motor_limit": self._stm8Error_motorLimit,
                "error_code": self._error_code,
                "flow_meter_multiplier": self._flowmeter_multiplier,
                "flow_meter_offset": self._flowmeter_offset,
                "flow_meter_divisor": self._flowmeter_divisor,
                "flow_meter_model": self._flowmeter_model,
                "flow_meter_disable_timer": self._flowmeter_timer,
                "flow_meter_alert_delay": neviweb_to_ha_delay(self._flowmeter_alert_delay),
                "flow_meter_alarm_length": self._flowmeter_alarm_length,
                "flowmeter_options": trigger_close(self._flowmeter_opt_action, self._flowmeter_opt_alarm),
                "flowmeter_enabled": self._flowmeter_enabled,
                "water_leak_status": self._water_leak_status,
                "battery_alert": alert_to_text(self._battery_alert, "bat"),
                "total_flow_count": L_2_sqm(self._total_kwh_count),
                "monthly_flow_count": L_2_sqm(self._monthly_kwh_count),
                "daily_flow_count": L_2_sqm(self._daily_kwh_count),
                "hourly_flow_count": L_2_sqm(self._hourly_kwh_count),
                "hourly_flow": L_2_sqm(self._hour_kwh),
                "daily_flow": L_2_sqm(self._today_kwh),
                "monthly_flow": L_2_sqm(self._month_kwh),
                "last_flow_stat_update": self._mark,
                "rssi": self._rssi,
                "sku": self._sku,
                "device_model": str(self._device_model),
                "device_model_cfg": self._device_model_cfg,
                "firmware": self._firmware,
                "activation": self._active,
                "device_type": self._device_type,
                "id": self._id,
            }
        )
        return data


class Neviweb130WifiMeshValve(Neviweb130Valve):
    """Implementation of a Neviweb Wi-Fi mesh valve, ACT4220WF-M, ACT4221WF-M."""

    def __init__(self, device_info, name, sku, firmware, device_type, client):
        """Initialize."""
        super().__init__(device_info, name, sku, firmware, device_type, client)
        self._batt_action_low = None
        self._flow_alarm_1 = None
        self._flow_alarm_2 = None
        self._flowmeter_divisor = 1
        self._flowmeter_offset = None
        self._motor_target = None
        self._stm8Error_motorJam = None
        self._stm8Error_motorLimit = None
        self._stm8Error_motorPosition = None
        self._temp_action_low = None
        self._valve_info_cause = None
        self._valve_info_id = None
        self._valve_info_status = None
        self._water_leak_status = None

    def update(self):
        if self._active:
            LOAD_ATTRIBUTES = [
                ATTR_MOTOR_POS,
                ATTR_MOTOR_TARGET,
                ATTR_TEMP_ALARM,
                ATTR_VALVE_INFO,
                ATTR_BATTERY_STATUS,
                ATTR_POWER_SUPPLY,
                ATTR_BATTERY_VOLTAGE,
                ATTR_STM8_ERROR,
                ATTR_FLOW_METER_CONFIG,
                ATTR_WATER_LEAK_STATUS,
                ATTR_FLOW_ALARM_TIMER,
                ATTR_FLOW_THRESHOLD,
                ATTR_FLOW_ALARM1_PERIOD,
                ATTR_FLOW_ALARM1_LENGTH,
                ATTR_FLOW_ALARM1_OPTION,
                ATTR_FLOW_ALARM1,
                ATTR_FLOW_ALARM2,
                ATTR_TEMP_ACTION_LOW,
                ATTR_BATT_ACTION_LOW,
            ]
            """Get the latest data from Neviweb and update the state."""
            start = time.time()
            device_data = self._client.get_device_attributes(self._id, UPDATE_ATTRIBUTES + LOAD_ATTRIBUTES)
            end = time.time()
            elapsed = round(end - start, 3)
            _LOGGER.debug("Updating %s (%s sec): %s", self._name, elapsed, device_data)
            if "error" not in device_data:
                if "errorCode" not in device_data:
                    self._valve_status = STATE_VALVE_STATUS if device_data[ATTR_MOTOR_POS] == 100 else "closed"
                    self._onoff = "on" if self._valve_status == STATE_VALVE_STATUS else MODE_OFF
                    self._motor_target = device_data[ATTR_MOTOR_TARGET]
                    self._temp_alert = device_data[ATTR_TEMP_ALARM]
                    if ATTR_VALVE_INFO in device_data:
                        self._valve_info_status = device_data[ATTR_VALVE_INFO]["status"]
                        self._valve_info_cause = device_data[ATTR_VALVE_INFO]["cause"]
                        self._valve_info_id = device_data[ATTR_VALVE_INFO]["identifier"]
                    self._battery_status = device_data[ATTR_BATTERY_STATUS]
                    self._power_supply = device_data[ATTR_POWER_SUPPLY]
                    self._battery_voltage = (
                        device_data[ATTR_BATTERY_VOLTAGE] if device_data[ATTR_BATTERY_VOLTAGE] is not None else 0
                    )
                    if ATTR_STM8_ERROR in device_data:
                        self._stm8Error_motorJam = device_data[ATTR_STM8_ERROR]["motorJam"]
                        self._stm8Error_motorLimit = device_data[ATTR_STM8_ERROR]["motorLimit"]
                        self._stm8Error_motorPosition = device_data[ATTR_STM8_ERROR]["motorPosition"]
                    if ATTR_FLOW_METER_CONFIG in device_data:
                        self._flowmeter_multiplier = device_data[ATTR_FLOW_METER_CONFIG]["multiplier"]
                        self._flowmeter_offset = device_data[ATTR_FLOW_METER_CONFIG]["offset"]
                        self._flowmeter_divisor = device_data[ATTR_FLOW_METER_CONFIG]["divisor"]
                        self._flowmeter_model = model_to_HA(self._flowmeter_multiplier)
                    self._water_leak_status = device_data[ATTR_WATER_LEAK_STATUS]
                    if self._water_leak_status == "flowMeter" and device_data[ATTR_FLOW_METER_CONFIG]["offset"] != 0:
                        msg = translate_error(
                            self.hass,
                            "error_code",
                            code=device_data[ATTR_WATER_LEAK_STATUS],
                            message="",
                            name=self._name,
                            id=self._id,
                            sku=self._sku,
                        )
                        self.notify_ha(msg)
                    if ATTR_FLOW_ALARM_TIMER in device_data:
                        self._flowmeter_timer = device_data[ATTR_FLOW_ALARM_TIMER]
                        if self._flowmeter_timer == 0 and ATTR_FLOW_THRESHOLD in device_data:
                            self._flowmeter_threshold = device_data[ATTR_FLOW_THRESHOLD]
                            self._flowmeter_alert_delay = device_data[ATTR_FLOW_ALARM1_PERIOD]
                            self._flowmeter_alarm_length = device_data[ATTR_FLOW_ALARM1_LENGTH]
                            self._flowmeter_opt_alarm = device_data[ATTR_FLOW_ALARM1_OPTION][ATTR_TRIGGER_ALARM]
                            self._flowmeter_opt_action = device_data[ATTR_FLOW_ALARM1_OPTION][ATTR_CLOSE_VALVE]
                    if ATTR_FLOW_ALARM1 in device_data:
                        self._flow_alarm_1 = device_data[ATTR_FLOW_ALARM1]
                    if ATTR_FLOW_ALARM2 in device_data:
                        self._flow_alarm_2 = device_data[ATTR_FLOW_ALARM2]
                    if ATTR_TEMP_ACTION_LOW in device_data:
                        self._temp_action_low = device_data[ATTR_TEMP_ACTION_LOW]
                    if ATTR_BATT_ACTION_LOW in device_data:
                        self._batt_action_low = device_data[ATTR_BATT_ACTION_LOW]
                else:
                    _LOGGER.warning("Error in reading device %s: (%s)", self._name, device_data)
            else:
                self.log_error(device_data["error"]["code"])
        else:
            if time.time() - self._snooze > SNOOZE_TIME:
                self._active = True
                if NOTIFY == "notification" or NOTIFY == "both":
                    self.notify_ha(translate_error(self.hass, "update_restarted", name=self._name, sku=self._sku))

    @property
    def extra_state_attributes(self):
        """Return the extra state attributes."""
        data = {}
        data.update(
            {
                "motor_target_position": self._motor_target,
                "temperature_alert": self._temp_alert,
                "valve_status": self._valve_info_status,
                "valve_cause": self._valve_info_cause,
                "valve_info_id": self._valve_info_id,
                "leak_icon": self.leak_icon,
                "icon_type": self.icon_type,
                "battery_level": voltage_to_percentage(self._battery_voltage, 4),
                "battery_voltage": self._battery_voltage,
                "battery_status": self._battery_status,
                "battery_icon": self.battery_icon,
                "power_supply": self._power_supply,
                "alert_motor_jam": self._stm8Error_motorJam,
                "alert_motor_position": self._stm8Error_motorPosition,
                "alert_motor_limit": self._stm8Error_motorLimit,
                "flow_alarm1": self._flow_alarm_1,
                "flow_alarm2": self._flow_alarm_2,
                "temp_action_low": self._temp_action_low,
                "batt_action_low": self._batt_action_low,
                "flow_meter_multiplier": self._flowmeter_multiplier,
                "flow_meter_offset": self._flowmeter_offset,
                "flow_meter_divisor": self._flowmeter_divisor,
                "flow_meter_model": self._flowmeter_model,
                "flow_meter_disable_timer": self._flowmeter_timer,
                "flow_meter_alert_delay": neviweb_to_ha_delay(self._flowmeter_alert_delay),
                "flow_meter_alarm_length": self._flowmeter_alarm_length,
                "flowmeter_options": trigger_close(self._flowmeter_opt_action, self._flowmeter_opt_alarm),
                "water_leak_status": self._water_leak_status,
                "total_flow_count": L_2_sqm(self._total_kwh_count),
                "monthly_flow_count": L_2_sqm(self._monthly_kwh_count),
                "daily_flow_count": L_2_sqm(self._daily_kwh_count),
                "hourly_flow_count": L_2_sqm(self._hourly_kwh_count),
                "hourly_flow": L_2_sqm(self._hour_kwh),
                "daily_flow": L_2_sqm(self._today_kwh),
                "monthly_flow": L_2_sqm(self._month_kwh),
                "last_flow_stat_update": self._mark,
                "sku": self._sku,
                "device_model": str(self._device_model),
                "device_model_cfg": self._device_model_cfg,
                "firmware": self._firmware,
                "activation": self._active,
                "device_type": self._device_type,
                "id": self._id,
            }
        )
        return data
