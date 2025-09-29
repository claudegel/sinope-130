"""
Support for Neviweb ZigBee valve connected via GT130 and Wi-Fi valves.

Water valves
model 3150 = VA4201WZ, sedna valve 1 inch via Wi-Fi
model 3150 = VA4200WZ, sedna valve 3/4 inch via Wi-Fi
model 3151 = VA4200ZB, sedna valve 3/4 inch via GT130, ZigBee
model 3153 = VA4220ZB, sedna 2e generation 3/4 inch, ZigBee
model 3150 = VA4220WZ, sedna 2e gen 3/4 inch
model 3155 = ACT4220WF-M, sedna multi-residential master valve 2e gen 3/4 inch, Wi-Fi
model 31532 = ACT4220ZB-M, sedna multi-residential slave valve 2e gen 3/4 inch, ZigBee
model 3150 = VA4220WF, sedna 2e generation 3/4 inch, Wi-Fi
model 3150 = VA4221WZ, sedna 2e gen 1 inch
model 3150 = VA4221WF, sedna 2e generation 1 inch, Wi-Fi
model 3155 = ACT4221WF-M, sedna multi-residential master valve 2e gen. 1 inch, Wi-Fi
model 31532 = ACT4221ZB-M, sedna multi-residential slave valve 2e gen. 1 inch, ZigBee

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

from homeassistant.components.binary_sensor import BinarySensorDeviceClass
from homeassistant.components.persistent_notification import DOMAIN as PN_DOMAIN
from homeassistant.components.valve import ValveDeviceClass, ValveEntity, ValveEntityFeature
from homeassistant.config_entries import ConfigEntry
from homeassistant.const import ATTR_ENTITY_ID
from homeassistant.core import HomeAssistant
from homeassistant.helpers import device_registry as dr
from homeassistant.helpers.device_registry import DeviceInfo
from homeassistant.helpers.entity_platform import AddEntitiesCallback
from homeassistant.helpers.update_coordinator import CoordinatorEntity

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
    ATTR_FLOW_ALARM1_LENGHT,
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
)
from .devices import device_dict, save_devices
from .schema import (
    SET_ACTIVATION_SCHEMA,
    SET_FLOW_ALARM_DISABLE_TIMER_SCHEMA,
    SET_FLOW_METER_DELAY_SCHEMA,
    SET_FLOW_METER_MODEL_SCHEMA,
    SET_FLOW_METER_OPTIONS_SCHEMA,
    SET_POWER_SUPPLY_SCHEMA,
    SET_VALVE_ALERT_SCHEMA,
    SET_VALVE_TEMP_ALERT_SCHEMA,
    VERSION,
)

_LOGGER = logging.getLogger(__name__)

DEFAULT_NAME = "neviweb130 valve"
DEFAULT_NAME_2 = "neviweb130 valve 2"
DEFAULT_NAME_3 = "neviweb130 valve 3"
SNOOZE_TIME = 1200

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

VALVE_TYPES = {
    "flow": ["mdi:pipe-valve", BinarySensorDeviceClass.MOISTURE],
    "valve": ["mdi:pipe-valve", ValveDeviceClass.WATER],
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


async def async_setup_entry(
    hass: HomeAssistant,
    entry: ConfigEntry,
    async_add_entities: AddEntitiesCallback,
    discovery_info=None,
) -> None:
    """Set up the Neviweb130 valve."""
    data = hass.data[DOMAIN][entry.entry_id]
    # data["scan_interval"]
    # data["stat_interval"]
    # data["notify"]

    if "neviweb130_client" not in data:
        _LOGGER.error("Neviweb130 client initialization failed.")
        return

    coordinator = hass.data[DOMAIN][entry.entry_id]["coordinator"]

    entities = []
    dr.async_get(hass)

    for gateway_data, default_name in [
        (data["neviweb130_client"].gateway_data, DEFAULT_NAME),
        (data["neviweb130_client"].gateway_data2, DEFAULT_NAME_2),
        (data["neviweb130_client"].gateway_data3, DEFAULT_NAME_3),
    ]:
        if gateway_data is not None and gateway_data != "_":
            for device_info in gateway_data:
                if "signature" in device_info and "model" in device_info["signature"]:
                    model = device_info["signature"]["model"]
                    if model in IMPLEMENTED_DEVICE_MODEL:
                        device_name = f'{default_name} {device_info["name"]}'
                        device_sku = device_info["sku"]
                        device_firmware = "{major}.{middle}.{minor}".format(**device_info["signature"]["softVersion"])
                        if device_info["signature"]["model"] in IMPLEMENTED_ZB_VALVE_MODEL:
                            device_type = "valve"
                            device = Neviweb130Valve(
                                data,
                                device_info,
                                device_name,
                                device_sku,
                                device_firmware,
                                device_type,
                                coordinator,
                            )
                        elif device_info["signature"]["model"] in IMPLEMENTED_WIFI_VALVE_MODEL:
                            device_type = "valve"
                            device = Neviweb130WifiValve(
                                data,
                                device_info,
                                device_name,
                                device_sku,
                                device_firmware,
                                device_type,
                                coordinator,
                            )
                        elif device_info["signature"]["model"] in IMPLEMENTED_ZB_MESH_VALVE_MODEL:
                            device_type = "flow"
                            device = Neviweb130MeshValve(
                                data,
                                device_info,
                                device_name,
                                device_sku,
                                device_firmware,
                                device_type,
                                coordinator,
                            )
                        else:
                            device_type = "flow"
                            device = Neviweb130WifiMeshValve(
                                data,
                                device_info,
                                device_name,
                                device_sku,
                                device_firmware,
                                device_type,
                                coordinator,
                            )

                        coordinator.register_device(device)
                        entities.append(device)
                        _LOGGER.debug("Entities are %s", entities)

    async_add_entities(entities)
    hass.async_create_task(coordinator.async_request_refresh())

    def set_valve_alert_service(service):
        """Set alert for water valve."""
        entity_id = service.data[ATTR_ENTITY_ID]
        for valve in entities:
            if valve.entity_id == entity_id:
                value = {
                    "id": valve.unique_id,
                    "batt": service.data[ATTR_BATT_ALERT],
                }
                valve.async_set_valve_alert(value)
                valve.schedule_update_ha_state(True)
                break

    def set_valve_temp_alert_service(service):
        """Set alert for water valve temperature location."""
        entity_id = service.data[ATTR_ENTITY_ID]
        for valve in entities:
            if valve.entity_id == entity_id:
                value = {
                    "id": valve.unique_id,
                    "temp": service.data[ATTR_TEMP_ALERT],
                }
                valve.async_set_valve_temp_alert(value)
                valve.schedule_update_ha_state(True)
                break

    def set_flow_meter_model_service(service):
        """Set the flow meter model connected to water valve."""
        entity_id = service.data[ATTR_ENTITY_ID]
        for valve in entities:
            if valve.entity_id == entity_id:
                value = {
                    "id": valve.unique_id,
                    "model": service.data[ATTR_FLOW_MODEL_CONFIG][0],
                }
                valve.async_set_flow_meter_model(value)
                valve.schedule_update_ha_state(True)
                break

    def set_flow_meter_delay_service(service):
        """Set the flow meter delay before alert is turned on."""
        entity_id = service.data[ATTR_ENTITY_ID]
        for valve in entities:
            if valve.entity_id == entity_id:
                value = {
                    "id": valve.unique_id,
                    "delay": service.data[ATTR_FLOW_ALARM1_PERIOD][0],
                }
                valve.async_set_flow_meter_delay(value)
                valve.schedule_update_ha_state(True)
                break

    def set_flow_meter_options_service(service):
        """Set the flow meter options when leak is detected."""
        entity_id = service.data[ATTR_ENTITY_ID]
        for valve in entities:
            if valve.entity_id == entity_id:
                value = {
                    "id": valve.unique_id,
                    "alarm": service.data[ATTR_TRIGGER_ALARM],
                    "close": service.data[ATTR_CLOSE_VALVE],
                }
                valve.async_set_flow_meter_options(value)
                valve.schedule_update_ha_state(True)
                break

    def set_power_supply_service(service):
        """Set power supply type for water valve."""
        entity_id = service.data[ATTR_ENTITY_ID]
        for valve in entities:
            if valve.entity_id == entity_id:
                value = {
                    "id": valve.unique_id,
                    "supply": service.data[ATTR_POWER_SUPPLY],
                }
                valve.async_set_power_supply(value)
                valve.schedule_update_ha_state(True)
                break

    def set_activation_service(service):
        """Activate or deactivate Neviweb polling for missing device."""
        entity_id = service.data[ATTR_ENTITY_ID]
        for valve in entities:
            if valve.entity_id == entity_id:
                value = {
                    "id": valve.unique_id,
                    "active": service.data[ATTR_ACTIVE],
                }
                valve.set_activation(value)
                valve.schedule_update_ha_state(True)
                break

    def set_flow_alarm_disable_timer_service(service):
        """Set alert for water valve temperature location."""
        entity_id = service.data[ATTR_ENTITY_ID]
        for valve in entities:
            if valve.entity_id == entity_id:
                value = {
                    "id": valve.unique_id,
                    "timer": service.data[ATTR_FLOW_ALARM_TIMER],
                }
                valve.async_set_flow_alarm_disable_timer(value)
                valve.schedule_update_ha_state(True)
                break

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
    """ "No action", "Close and send", "Close only", "Send only"."""
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


def retrieve_data(id, data):
    """Retrieve device stat data from device_dict."""
    device_data = device_dict.get(id)
    if device_data:
        if data == 1:
            return device_data[1]
        else:
            return device_data[2]
    else:
        # Set defaults if device not found
        if data == 1:
            return 0
        else:
            return None


def save_data(id, data, mark):
    """Save stat data for one device in the device_dict."""
    entry = device_dict.get(id)
    if entry is None:
        _LOGGER.warning(f"Device id {id} not found in device_dict!")
        return
    if not isinstance(entry, list) or len(entry) < 3:
        _LOGGER.warning(f"Device entry for {id} is not a valid list: {entry}")
        return
    _LOGGER.debug(f"Device {id} data before update: {entry}")
    entry[1] = data
    entry[2] = mark
    _LOGGER.debug(f"Device {id} data updated: {entry}")
    # Optionally trigger save_devices here


async def async_add_data(id, data, mark):
    """Add new device stat data in the device_dict."""
    if id in device_dict:
        _LOGGER.debug("Device already exist in device_dict %s", id)
        save_data(id, data, mark)
        return
    device_dict[id] = [id, data, mark]
    await save_devices(data)  # Persist changes
    _LOGGER.debug("Data added for %s", id)


class Neviweb130Valve(CoordinatorEntity, ValveEntity):
    """Implementation of a Neviweb valve."""

    def __init__(self, data, device_info, name, sku, firmware, device_type, coordinator):
        """Initialize."""
        super().__init__(coordinator)
        self._device = device_info
        self._name = name
        self._sku = sku
        self._firmware = firmware
        self._client = data["neviweb130_client"]
        self._stat_interval = data["stat_interval"]
        self._notify = data["notify"]
        self._id = str(device_info["id"])
        self._device_model = device_info["signature"]["model"]
        self._device_model_cfg = device_info["signature"]["modelCfg"]
        self._hard_rev = device_info["signature"]["hardRev"]
        self._identifier = device_info["identifier"]
        self._device_type = device_type
        self._total_kwh_count: float | None = None
        self._monthly_kwh_count: float = 0
        self._daily_kwh_count: float = 0
        self._hourly_kwh_count: float = 0
        self._hour_kwh = None
        self._today_kwh = None
        self._month_kwh = None
        self._marker = None
        self._mark = None
        self._water_leak_status = None
        self._is_zb_control = None
        self._is_sedna_control = None
        self._flowmeter_multiplier = None
        self._energy_stat_time = None
        self._onoff = None
        self._reports_position = False
        self._valve_status = None
        self._battery_voltage = 0
        self._battery_status = None
        self._battery_alert = 0
        self._batt_percent_normal = None
        self._batt_status_normal = None
        self._power_supply = None
        self._temp_alert = None
        self._rssi = None
        self._is_zb_valve = device_info["signature"]["model"] in IMPLEMENTED_ZB_VALVE_MODEL
        self._is_wifi_valve = device_info["signature"]["model"] in IMPLEMENTED_WIFI_VALVE_MODEL
        self._is_zb_mesh_valve = device_info["signature"]["model"] in IMPLEMENTED_ZB_MESH_VALVE_MODEL
        self._is_wifi_mesh_valve = device_info["signature"]["model"] in IMPLEMENTED_WIFI_MESH_VALVE_MODEL
        self._snooze: float = 0.0
        self._flowmeter_opt_alarm = None
        self._activ = True
        self._flowmeter_opt_action = None
        self._flowmeter_threshold = None
        self._flowmeter_alarm_length = None
        self._flowmeter_model = None
        self._flowmeter_timer = None
        self._flowmeter_alert_delay = None
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
        if self._activ:
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
            device_data = await self._client.async_get_device_attributes(self._id, UPDATE_ATTRIBUTES + LOAD_ATTRIBUTES)
            end = time.time()
            elapsed = round(end - start, 3)
            device_alert = None
            if self._is_zb_valve or self._is_zb_mesh_valve:
                device_alert = await self._client.async_get_device_alert(self._id)
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
                    self.async_write_ha_state()
                else:
                    _LOGGER.warning(
                        "Error in reading device %s: (%s)",
                        self._name,
                        device_data,
                    )
            else:
                await self.async_log_error(device_data["error"]["code"])
        else:
            if time.time() - self._snooze > SNOOZE_TIME:
                self._activ = True
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
        """Return the name of the valve."""
        return self._name

    @property
    def icon(self):
        """Return the icon to use in the frontend."""
        device_info = VALVE_TYPES.get(self._device_type)
        if device_info is None:
            return None

        return device_info[0]

    @property
    def device_class(self):
        """Return the device class of this entity."""
        device_type = VALVE_TYPES.get(self._device_type)
        if device_type is None:
            return None

        return device_type[1]

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

    async def async_open_valve(self, **kwargs):
        """Open the valve."""
        if self._is_wifi_valve or self._is_wifi_mesh_valve:
            await self._client.async_set_valve_onoff(self._id, 100)
            self._valve_status = "open"
        else:
            await self._client.async_set_onoff(self._id, "on")
            if self._is_zb_valve or self._is_zb_mesh_valve:
                self._valve_status = "open"
        self._onoff = "on"

    async def async_close_valve(self, **kwargs):
        """Close the valve."""
        if self._is_wifi_valve or self._is_wifi_mesh_valve:
            await self._client.async_set_valve_onoff(self._id, 0)
            self._valve_status = "closed"
        else:
            await self._client.async_set_onoff(self._id, "off")
            if self._is_zb_valve or self._is_zb_mesh_valve:
                self._valve_status = "closed"
        self._onoff = MODE_OFF

    @property
    def valve_status(self):
        """Return current valve status, open or closed."""
        return self._valve_status is not None

    @property
    def rssi(self):
        if self._rssi is not None:
            return self._rssi
        return None

    @property
    def total_flow_count(self):
        if self._total_kwh_count is not None:
            return self._total_kwh_count
        return None

    @property
    def monthly_flow_count(self):
        if self._monthly_kwh_count is not None:
            return self._monthly_kwh_count
        return None

    @property
    def daily_flow_count(self):
        if self._daily_kwh_count is not None:
            return self._daily_kwh_count
        return None

    @property
    def hourly_flow_count(self):
        if self._hourly_kwh_count is not None:
            return self._hourly_kwh_count
        return None

    @property
    def flowmeter_timer(self):
        if self._flowmeter_timer is not None:
            return self._flowmeter_timer
        return None

    @property
    def temp_alert(self):
        if self._temp_alert is not None:
            return self._temp_alert
        return None

    @property
    def water_leak_status(self):
        if self._water_leak_status is not None:
            return self._water_leak_status
        return None

    @property
    def battery_status(self):
        if self._battery_status is not None:
            return self._battery_status
        return None

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
                "power_supply": self._power_supply,
                "battery_alert": alert_to_text(self._battery_alert, "bat"),
                "temperature_alert": alert_to_text(self._temp_alert, "temp"),
                "battery_percent_normalized": self._batt_percent_normal,
                "battery_status_normalized": self._batt_status_normal,
                "sku": self._sku,
                "device_model": str(self._device_model),
                "device_model_cfg": self._device_model_cfg,
                "firmware": self._firmware,
                "activation": self._activ,
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
        return voltage_to_percentage(self._battery_voltage, 2 if self._is_zb_control or self._is_sedna_control else 4)

    async def async_set_valve_alert(self, value):
        """Set valve batt alert action."""
        if self._is_zb_valve or self._is_zb_mesh_valve:
            if value["batt"] == "true":
                batt = 1
            else:
                batt = 0
        else:
            batt = value["batt"]
        entity = value["id"]
        await self._client.async_set_valve_alert(entity, batt)
        self._battery_alert = batt

    async def async_set_valve_temp_alert(self, value):
        """Set valve temperature alert action."""
        temp = value["temp"]
        entity = value["id"]
        await self._client.async_set_valve_temp_alert(entity, temp)
        self._temp_alert = temp

    async def async_set_flow_meter_model(self, value):
        """Set water valve flow meter model connected."""
        model = value["model"]
        entity = value["id"]
        await self._client.async_set_flow_meter_model(entity, model)
        self._flowmeter_model = model

    async def async_set_flow_alarm_disable_timer(self, value):
        """Set flowmeter alarm action disabled timer, for valves with flowmeter."""
        entity = value["id"]
        timer = value["timer"]
        await self._client.async_set_flow_alarm_timer(entity, timer)
        self._flowmeter_timer = timer

    async def async_set_flow_meter_delay(self, value):
        """Set water valve flow meter delay before alert."""
        val = value["delay"]
        delay = [v for k, v in HA_TO_NEVIWEB_DELAY.items() if k == val][0]
        entity = value["id"]
        await self._client.async_set_flow_meter_delay(entity, delay)
        self._flowmeter_alert_delay = val

    async def async_set_power_supply(self, value):
        """Set water valve power supply type."""
        match value["supply"]:
            case "batt":
                sup = "batteries"
            case "power":
                sup = "acups-01"
            case _:
                sup = "both"
        entity = value["id"]
        await self._client.async_set_power_supply(entity, sup)
        self._power_supply = sup

    async def async_set_flow_meter_options(self, value):
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
        entity = value["id"]
        await self._client.async_set_flow_meter_options(entity, alarm, action, length, threshold)
        self._flowmeter_opt_alarm = alarm
        self._flowmeter_opt_action = action
        self._flowmeter_threshold = threshold
        self._flowmeter_alarm_length = length

    def set_activation(self, value):
        """Activate or deactivate neviweb polling for a missing device."""
        action = value["active"]
        self._activ = action

    async def async_do_stat(self, start):
        """Get device flow statistic."""
        if self._flowmeter_multiplier != 0:
            if start - self._energy_stat_time > self._stat_interval and self._energy_stat_time != 0:
                today = date.today()
                current_month = today.month
                current_day = today.day
                device_monthly_stats = await self._client.async_get_device_monthly_stats(self._id)
                #                _LOGGER.debug("%s device_monthly_stats = %s", self._name, device_monthly_stats)
                if device_monthly_stats is not None and len(device_monthly_stats) > 1:
                    n = len(device_monthly_stats)
                    monthly_kwh_count = 0
                    k = 0
                    while k < n:
                        monthly_kwh_count += device_monthly_stats[k]["period"] / 100
                        k += 1
                    self._monthly_kwh_count = round(monthly_kwh_count, 2)
                    self._month_kwh = round(device_monthly_stats[n - 1]["period"] / 100, 2)
                    dt_month = datetime.fromisoformat(device_monthly_stats[n - 1]["date"][:-1] + "+00:00").astimezone(
                        timezone.utc
                    )
                    _LOGGER.debug("stat month = %s", dt_month.month)
                else:
                    self._month_kwh = 0
                    _LOGGER.warning("%s Got None for device_monthly_stats", self._name)
                device_daily_stats = await self._client.async_get_device_daily_stats(self._id)
                #                _LOGGER.debug("%s device_daily_stats = %s", self._name, device_daily_stats)
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
                            daily_kwh_count += device_daily_stats[k]["period"] / 100
                        k += 1
                    self._daily_kwh_count = round(daily_kwh_count, 2)
                    self._today_kwh = round(device_daily_stats[n - 1]["period"] / 100, 2)
                    dt_day = datetime.fromisoformat(device_daily_stats[n - 1]["date"][:-1].replace("Z", "+00:00"))
                    _LOGGER.debug("stat day = %s", dt_day.day)
                else:
                    self._today_kwh = 0
                    _LOGGER.warning("%s Got None for device_daily_stats", self._name)
                device_hourly_stats = await self._client.async_get_device_hourly_stats(self._id)
                #                _LOGGER.debug("%s device_hourly_stats = %s", self._name, device_hourly_stats)
                if device_hourly_stats is not None and len(device_hourly_stats) > 1:
                    n = len(device_hourly_stats)
                    hourly_kwh_count = 0
                    k = 0
                    while k < n:
                        if (
                            datetime.fromisoformat(device_hourly_stats[k]["date"][:-1].replace("Z", "+00:00")).day
                            == current_day
                        ):
                            hourly_kwh_count += device_hourly_stats[k]["period"] / 100
                        k += 1
                    self._hourly_kwh_count = round(hourly_kwh_count, 2)
                    self._hour_kwh = round(device_hourly_stats[n - 1]["period"] / 100, 2)
                    self._marker = device_hourly_stats[n - 1]["date"]
                    dt_hour = datetime.strptime(
                        device_hourly_stats[n - 1]["date"],
                        "%Y-%m-%dT%H:%M:%S.%fZ",
                    )
                    _LOGGER.debug("stat hour = %s", dt_hour.hour)
                else:
                    self._hour_kwh = 0
                    _LOGGER.warning("%s Got None for device_hourly_stats", self._name)
                if self._total_kwh_count is None:
                    self._total_kwh_count = round(
                        self._monthly_kwh_count + self._daily_kwh_count + self._hourly_kwh_count,
                        3,
                    )
                    await async_add_data(self._id, self._total_kwh_count, self._marker)
                    self._mark = self._marker
                else:
                    if self._marker != self._mark:
                        self._total_kwh_count += round(self._hour_kwh, 3)
                        save_data(self._id, self._total_kwh_count, self._marker)
                        self._mark = self._marker
                _LOGGER.debug("Device dict updated: %s", device_dict)
                self.async_write_ha_state()
                self._energy_stat_time = time.time()
            if self._energy_stat_time == 0:
                self._energy_stat_time = start
        else:
            self._hour_kwh = 0
            self._today_kwh = 0
            self._month_kwh = 0

    async def async_log_error(self, error_data):
        """Send error message to LOG."""
        if error_data == "USRSESSEXP":
            _LOGGER.warning("Session expired... reconnecting...")
            if self._notify == "notification" or self._notify == "both":
                await self.async_notify_ha(
                    "Warning: Got USRSESSEXP error, Neviweb session expired. "
                    + "Set your scan_interval parameter to less than 10 minutes "
                    + "to avoid this... Reconnecting..."
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
                "Device attribute not supported for %s (id: %s): %s... (SKU: %s)",
                self._name,
                self._id,
                error_data,
                self._sku,
            )
        elif error_data == "DVCACTNSPTD":
            _LOGGER.warning(
                "Device action not supported for %s (id: %s)... (SKU: %s) Report to maintainer.",
                self._name,
                self._id,
                self._sku,
            )
        elif error_data == "DVCCOMMTO":
            _LOGGER.warning(
                "Device Communication Timeout for %s (id: %s)... The device "
                + "did not respond to the server within the prescribed delay. "
                + "(SKU: %s)",
                self._name,
                self._id,
                self._sku,
            )
        elif error_data == "SVCERR":
            _LOGGER.warning(
                "Service error, device not available retry later %s (id: %s): %s... (SKU: %s)",
                self._name,
                self._id,
                error_data,
                self._sku,
            )
        elif error_data == "DVCBUSY":
            _LOGGER.warning(
                "Device busy can't reach (neviweb update ?), retry later %s (id: %s): %s... (SKU: %s)",
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
            self._activ = False
            self._snooze = time.time()
        else:
            _LOGGER.warning(
                "Unknown error for %s (id: %s): %s... (SKU: %s) Report to maintainer.",
                self._name,
                self._id,
                error_data,
                self._sku,
            )

    async def async_notify_ha(self, msg: str, title: str = "Neviweb130 integration " + VERSION):
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


class Neviweb130WifiValve(Neviweb130Valve):
    """Implementation of a Neviweb Wi-Fi valve, VA4200WZ, VA4201WZ, VA4220WZ, VA4221WZ, VA4220WF, VA4221WF."""

    def __init__(self, data, device_info, name, sku, firmware, device_type, coordinator):
        """Initialize."""
        super().__init__(data, device_info, name, sku, firmware, device_type, coordinator)
        self._device = device_info
        self._name = name
        self._sku = sku
        self._firmware = firmware
        self._client = data["neviweb130_client"]
        self._stat_interval = data["stat_interval"]
        self._notify = data["notify"]
        self._id = str(device_info["id"])
        self._device_model = device_info["signature"]["model"]
        self._device_model_cfg = device_info["signature"]["modelCfg"]
        self._hard_rev = device_info["signature"]["hardRev"]
        self._identifier = device_info["identifier"]
        self._device_type = device_type
        self._total_kwh_count = retrieve_data(self._id, 1)
        self._monthly_kwh_count = 0
        self._daily_kwh_count = 0
        self._hourly_kwh_count = 0
        self._hour_kwh = 0
        self._today_kwh = 0
        self._month_kwh = 0
        self._marker = None
        self._mark = retrieve_data(self._id, 2)
        self._onoff = None
        self._reports_position = False
        self._rssi = None
        self._valve_status = None
        self._battery_voltage = 0
        self._battery_status = None
        self._power_supply = None
        self._valve_closure = None
        self._battery_alert = 0
        self._batt_percent_normal = None
        self._batt_status_normal = None
        self._temp_alert = None
        self._flowmeter_multiplier = 0
        self._flowmeter_offset = 0
        self._flowmeter_divisor = 1
        self._flowmeter_model = None
        self._stm8Error_motorJam = None
        self._stm8Error_motorPosition = None
        self._stm8Error_motorLimit = None
        self._motor_target = None
        self._valve_info_status = None
        self._valve_info_cause = None
        self._valve_info_id = None
        self._occupancy_delay = None
        self._water_leak_status = None
        self._flowmeter_opt_alarm_1 = None
        self._flowmeter_opt_action_1 = None
        self._flowmeter_opt_flow_min_1 = 1
        self._flowmeter_opt_duration_1 = 0
        self._flowmeter_opt_observationPeriod_1 = 0
        self._flowmeter_opt_alarm_2 = None
        self._flowmeter_opt_action_2 = None
        self._flowmeter_opt_flow_min_2 = 1
        self._flowmeter_opt_duration_2 = 0
        self._flowmeter_opt_observationPeriod_2 = 0
        self._temp_action_low = None
        self._batt_action_low = None
        self._away_action = None
        self._is_wifi_valve = device_info["signature"]["model"] in IMPLEMENTED_WIFI_VALVE_MODEL
        self._is_wifi_mesh_valve = False
        self._is_zb_valve = False
        self._is_zb_mesh_valve = False
        self._energy_stat_time = time.time() - 1500
        self._snooze = 0
        self._activ = True
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
        if self._activ:
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
            device_data = await self._client.async_get_device_attributes(self._id, UPDATE_ATTRIBUTES + LOAD_ATTRIBUTES)
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
                            await self.async_notify_ha(
                                "Warning: Neviweb Device error detected: "
                                + device_data[ATTR_WATER_LEAK_STATUS]
                                + " for device: "
                                + self._name
                                + ", Sku: "
                                + self._sku
                            )
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
                    self.async_write_ha_state()
                else:
                    _LOGGER.warning(
                        "Error in reading device %s: (%s)",
                        self._name,
                        device_data,
                    )
            else:
                await self.async_log_error(device_data["error"]["code"])
            await self.async_do_stat(start)
        else:
            if time.time() - self._snooze > SNOOZE_TIME:
                self._activ = True
                if self._notify == "notification" or self._notify == "both":
                    await self.async_notify_ha(
                        "Warning: Neviweb Device update restarted for " + self._name + ", Sku: " + self._sku
                    )

    @property
    def extra_state_attributes(self):
        """Return the extra state attributes."""
        data = {}
        data.update(
            {
                "temperature_alert": self._temp_alert,
                "battery_level": voltage_to_percentage(self._battery_voltage, 4),
                "battery_voltage": self._battery_voltage,
                "battery_status": self._battery_status,
                "power_supply": self._power_supply,
                "valve_closure_source": self._valve_closure,
                "battery_alert": self._battery_alert,
                "motor_target_position": self._motor_target,
                "water_leak_status": self._water_leak_status,
                "valve_status": self._valve_info_status,
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
                "activation": self._activ,
                "device_type": self._device_type,
                "id": self._id,
            }
        )
        return data


class Neviweb130MeshValve(Neviweb130Valve):
    """Implementation of a Neviweb mesh valve VA4220ZB and ACT4220ZB-M."""

    def __init__(self, data, device_info, name, sku, firmware, device_type, coordinator):
        """Initialize."""
        super().__init__(data, device_info, name, sku, firmware, device_type, coordinator)
        self._device = device_info
        self._name = name
        self._sku = sku
        self._firmware = firmware
        self._client = data["neviweb130_client"]
        self._stat_interval = data["stat_interval"]
        self._notify = data["notify"]
        self._id = str(device_info["id"])
        self._device_model = device_info["signature"]["model"]
        self._device_model_cfg = device_info["signature"]["modelCfg"]
        self._hard_rev = device_info["signature"]["hardRev"]
        self._identifier = device_info["identifier"]
        self._device_type = device_type
        self._total_kwh_count = retrieve_data(self._id, 1)
        self._monthly_kwh_count = 0
        self._daily_kwh_count = 0
        self._hourly_kwh_count = 0
        self._hour_kwh = 0
        self._today_kwh = 0
        self._month_kwh = 0
        self._marker = None
        self._mark = retrieve_data(self._id, 2)
        self._onoff = None
        self._reports_position = False
        self._valve_status = None
        self._battery_voltage = 0
        self._battery_status = None
        self._batt_percent_normal = None
        self._batt_status_normal = None
        self._power_supply = None
        self._battery_alert = 0
        self._rssi = None
        self._flowmeter_multiplier = 0
        self._flowmeter_offset = 0
        self._flowmeter_divisor = 1
        self._flowmeter_model = None
        self._flowmeter_timer = 0
        self._flowmeter_threshold = 1
        self._flowmeter_alarm_length = 0
        self._flowmeter_alert_delay = 0
        self._flowmeter_opt_alarm = None
        self._flowmeter_opt_action = None
        self._flowmeter_enabled = None
        self._stm8Error_motorJam = None
        self._stm8Error_motorPosition = None
        self._stm8Error_motorLimit = None
        self._error_code = None
        self._water_leak_status = None
        self._is_zb_mesh_valve = device_info["signature"]["model"] in IMPLEMENTED_ZB_MESH_VALVE_MODEL
        self._is_wifi_valve = False
        self._is_wifi_mesh_valve = False
        self._is_zb_valve = False
        self._energy_stat_time = time.time() - 1500
        self._snooze = 0
        self._activ = True
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
        if self._activ:
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
                ATTR_FLOW_ALARM1_LENGHT,
                ATTR_FLOW_ALARM1_OPTION,
                ATTR_FLOW_ENABLED,
                ATTR_BATT_STATUS_NORMAL,
                ATTR_BATT_PERCENT_NORMAL,
                ATTR_ERROR_CODE_SET1,
            ]
            """Get the latest data from Neviweb and update the state."""
            start = time.time()
            device_data = await self._client.async_get_device_attributes(self._id, UPDATE_ATTRIBUTES + LOAD_ATTRIBUTES)
            end = time.time()
            elapsed = round(end - start, 3)
            device_alert = None
            if self._is_zb_valve or self._is_zb_mesh_valve:
                device_alert = await self._client.async_get_device_alert(self._id)
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
                        await self.async_notify_ha(
                            "Warning: Neviweb Device error detected: "
                            + device_data[ATTR_WATER_LEAK_STATUS]
                            + " for device: "
                            + self._name
                            + ", Sku: "
                            + self._sku
                        )
                    if ATTR_FLOW_ALARM_TIMER in device_data:
                        self._flowmeter_timer = device_data[ATTR_FLOW_ALARM_TIMER]
                        if self._flowmeter_timer == 0:
                            self._flowmeter_threshold = device_data[ATTR_FLOW_THRESHOLD]
                            self._flowmeter_alert_delay = device_data[ATTR_FLOW_ALARM1_PERIOD]
                            self._flowmeter_alarm_length = device_data[ATTR_FLOW_ALARM1_LENGHT]
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
                            await self.async_notify_ha(
                                "Warning: Neviweb Device error code detected: "
                                + str(device_data[ATTR_ERROR_CODE_SET1]["raw"])
                                + " for device: "
                                + self._name
                                + ", Sku: "
                                + self._sku
                            )
                            _LOGGER.warning(
                                "Error code set1 updated: %s",
                                str(device_data[ATTR_ERROR_CODE_SET1]["raw"]),
                            )
                    else:
                        self._error_code = 0
                    self.async_write_ha_state()
                else:
                    _LOGGER.warning(
                        "Error reading device %s: (%s)",
                        self._name,
                        device_data,
                    )
            else:
                await self.async_log_error(device_data["error"]["code"])
            await self.async_do_stat(start)
        else:
            if time.time() - self._snooze > SNOOZE_TIME:
                self._activ = True
                if self._notify == "notification" or self._notify == "both":
                    await self.async_notify_ha(
                        "Warning: Neviweb Device update restarted for " + self._name + ", Sku: " + self._sku
                    )

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
                "battery_percent_normalized": self._batt_percent_normal,
                "battery_status_normalized": self._batt_status_normal,
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
                "activation": self._activ,
                "device_type": self._device_type,
                "id": self._id,
            }
        )
        return data


class Neviweb130WifiMeshValve(Neviweb130Valve):
    """Implementation of a Neviweb Wi-Fi mesh valve, ACT4220WF-M, ACT4221WF-M."""

    def __init__(self, data, device_info, name, sku, firmware, device_type, coordinator):
        """Initialize."""
        super().__init__(data, device_info, name, sku, firmware, device_type, coordinator)
        self._device = device_info
        self._name = name
        self._sku = sku
        self._firmware = firmware
        self._client = data["neviweb130_client"]
        self._stat_interval = data["stat_interval"]
        self._notify = data["notify"]
        self._id = str(device_info["id"])
        self._device_model = device_info["signature"]["model"]
        self._device_model_cfg = device_info["signature"]["modelCfg"]
        self._hard_rev = device_info["signature"]["hardRev"]
        self._identifier = device_info["identifier"]
        self._device_type = device_type
        self._total_kwh_count = retrieve_data(self._id, 1)
        self._monthly_kwh_count = 0
        self._daily_kwh_count = 0
        self._hourly_kwh_count = 0
        self._hour_kwh = 0
        self._today_kwh = 0
        self._month_kwh = 0
        self._marker = None
        self._mark = retrieve_data(self._id, 2)
        self._onoff = None
        self._reports_position = False
        self._valve_status = None
        self._battery_voltage = 0
        self._battery_status = None
        self._power_supply = None
        self._flow_alarm_1 = None
        self._flow_alarm_2 = None
        self._flowmeter_multiplier = 0
        self._flowmeter_offset = 0
        self._flowmeter_divisor = 1
        self._flowmeter_model = None
        self._flowmeter_timer = 0
        self._flowmeter_threshold = 1
        self._flowmeter_alarm_length = 0
        self._flowmeter_alert_delay = 0
        self._flowmeter_opt_alarm = None
        self._flowmeter_opt_action = None
        self._stm8Error_motorJam = None
        self._stm8Error_motorPosition = None
        self._stm8Error_motorLimit = None
        self._motor_target = None
        self._valve_info_status = None
        self._valve_info_cause = None
        self._valve_info_id = None
        self._water_leak_status = None
        self._temp_alert = None
        self._temp_action_low = None
        self._batt_action_low = None
        self._rssi = None
        self._is_wifi_mesh_valve = device_info["signature"]["model"] in IMPLEMENTED_WIFI_MESH_VALVE_MODEL
        self._is_wifi_valve = False
        self._is_zb_valve = False
        self._is_zb_mesh_valve = False
        self._energy_stat_time = time.time() - 1500
        self._snooze = 0
        self._activ = True
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
        if self._activ:
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
                ATTR_FLOW_ALARM1_LENGHT,
                ATTR_FLOW_ALARM1_OPTION,
                ATTR_FLOW_ALARM1,
                ATTR_FLOW_ALARM2,
                ATTR_TEMP_ACTION_LOW,
                ATTR_BATT_ACTION_LOW,
            ]
            """Get the latest data from Neviweb and update the state."""
            start = time.time()
            device_data = await self._client.async_get_device_attributes(self._id, UPDATE_ATTRIBUTES + LOAD_ATTRIBUTES)
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
                        await self.async_notify_ha(
                            "Warning: Neviweb Device error detected: "
                            + device_data[ATTR_WATER_LEAK_STATUS]
                            + " for device: "
                            + self._name
                            + ", Sku: "
                            + self._sku
                        )
                    if ATTR_FLOW_ALARM_TIMER in device_data:
                        self._flowmeter_timer = device_data[ATTR_FLOW_ALARM_TIMER]
                        if self._flowmeter_timer == 0:
                            self._flowmeter_threshold = device_data[ATTR_FLOW_THRESHOLD]
                            self._flowmeter_alert_delay = device_data[ATTR_FLOW_ALARM1_PERIOD]
                            self._flowmeter_alarm_length = device_data[ATTR_FLOW_ALARM1_LENGHT]
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
                    self.async_write_ha_state()
                else:
                    _LOGGER.warning(
                        "Error in reading device %s: (%s)",
                        self._name,
                        device_data,
                    )
            else:
                await self.async_log_error(device_data["error"]["code"])
        else:
            if time.time() - self._snooze > SNOOZE_TIME:
                self._activ = True
                if self._notify == "notification" or self._notify == "both":
                    await self.async_notify_ha(
                        "Warning: Neviweb Device update restarted for " + self._name + ", Sku: " + self._sku
                    )

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
                "battery_level": voltage_to_percentage(self._battery_voltage, 4),
                "battery_voltage": self._battery_voltage,
                "battery_status": self._battery_status,
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
                "activation": self._activ,
                "device_type": self._device_type,
                "id": self._id,
            }
        )
        return data
