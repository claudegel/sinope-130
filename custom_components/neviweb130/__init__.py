"""Sinopé GT130 Zigbee and Wi-Fi support."""

from __future__ import annotations

import logging
import os
from datetime import timedelta
from functools import partial
from typing import cast

from homeassistant import config_entries
from homeassistant.config_entries import ConfigEntry
from homeassistant.const import CONF_SCAN_INTERVAL, CONF_USERNAME, EVENT_HOMEASSISTANT_STOP
from homeassistant.core import HomeAssistant, callback
from homeassistant.exceptions import ConfigEntryError
from homeassistant.helpers import config_validation as cv
from homeassistant.helpers import device_registry as dr
from homeassistant.helpers import entity_registry as er
from homeassistant.helpers.device_registry import DeviceEntry
from homeassistant.helpers.typing import ConfigType

from .const import (
    CONF_HOMEKIT_MODE,
    CONF_IGNORE_MIWI,
    CONF_NOTIFY,
    CONF_PREFIX,
    CONF_REQUEST_LIMIT,
    CONF_SAFE_MODE,
    CONF_STAT_INTERVAL,
    DEFAULT_REQUEST_LIMIT,
    DOMAIN,
    STARTUP_MESSAGE,
    VERSION,
)
from .coordinator import Neviweb130Client, async_setup_coordinator
from .devices import load_devices, save_devices
from .helpers import (
    DailyRequestCounter,
    async_notify_once_or_update,
    check_weather_icons_folder,
    extract_log_options,
    normalize_yaml_config,
    sanitize_entry_data,
    setup_logger,
    translate_error,
    update_logger_config,
    update_logger_level,
)

# Exposed for Home Assistant YAML validation.
from .schema import CONFIG_SCHEMA  # noqa: F401
from .schema import HOMEKIT_MODE as DEFAULT_HOMEKIT_MODE
from .schema import IGNORE_MIWI as DEFAULT_IGNORE_MIWI
from .schema import NOTIFY as DEFAULT_NOTIFY
from .schema import PLATFORMS
from .schema import PREFIX as DEFAULT_PREFIX
from .schema import SAFE_MODE as DEFAULT_SAFE_MODE
from .schema import SCAN_INTERVAL_SCHEMA as DEFAULT_SCAN_INTERVAL
from .schema import STAT_INTERVAL as DEFAULT_STAT_INTERVAL
from .session_manager import SessionManager

LOG_PATH = os.path.abspath(os.path.join(os.path.dirname(__file__), "../../neviweb130_log.txt"))
_LOGGER = logging.getLogger(__name__)

SCAN_INTERVAL: timedelta = timedelta(seconds=DEFAULT_SCAN_INTERVAL)


async def async_setup(hass: HomeAssistant, config: ConfigType) -> bool:
    """Import neviweb130 integration from YAML if it exists."""

    neviweb130_config: ConfigType | None = config.get(DOMAIN)
    hass.data.setdefault(DOMAIN, {})

    if neviweb130_config is None:
        return True

    # Inform the user that a configuration was detected in configuration.yaml
    msg = await translate_error(hass, "yaml_config_detected")
    _LOGGER.info(msg)
    await async_notify_once_or_update(
        hass,
        msg,
        title=f"Neviweb130 integration {VERSION}",
        notification_id="neviweb130_config_detected",
    )

    _LOGGER.info("Neviweb130 YAML configuration found, starting automatic import...")

    # Normalize scan_interval
    scan_interval = neviweb130_config.get(CONF_SCAN_INTERVAL)
    if isinstance(scan_interval, timedelta):
        neviweb130_config[CONF_SCAN_INTERVAL] = int(scan_interval.total_seconds())
    elif isinstance(scan_interval, str):
        neviweb130_config[CONF_SCAN_INTERVAL] = int(cv.time_period_str(scan_interval).total_seconds())
    elif isinstance(scan_interval, (int, float)):
        neviweb130_config[CONF_SCAN_INTERVAL] = int(scan_interval)
    else:
        _LOGGER.warning("Unexpected type for scan_interval: %s", type(scan_interval))
        neviweb130_config[CONF_SCAN_INTERVAL] = DEFAULT_SCAN_INTERVAL

    _LOGGER.warning(
        "YAML import: starting SOURCE_IMPORT with keys: %s",
        list(neviweb130_config.keys()),
    )

    accounts, global_options, _ = normalize_yaml_config(dict(neviweb130_config))

    for acc in accounts:
        data = {
            **acc,
            **global_options,
        }

        _LOGGER.info(
            "YAML import: starting account import: prefix=%s, username=%s",
            acc["prefix"],
            acc["username"],
        )

        hass.async_create_task(
            hass.config_entries.flow.async_init(
                DOMAIN,
                context={"source": config_entries.SOURCE_IMPORT},
                data=data,
            )
        )

    return True


async def async_shutdown(hass: HomeAssistant, event=None):
    """Handle Home Assistant shutdown."""
    _LOGGER.info("Shutting down Neviweb130 custom component")

    domain_data = hass.data.get(DOMAIN)
    if not domain_data:
        _LOGGER.warning("DOMAIN not found in hass.data during shutdown — nothing to save.")
        return

    conf_dir = domain_data.get("conf_dir")
    if not conf_dir:
        _LOGGER.error("conf_dir is missing during shutdown — data will not be saved.")
        return

    data = domain_data.get("device_dict", {})
    await save_devices(conf_dir, data)
    _LOGGER.info("Energy stat data saved")

    if "coordinator" in domain_data:
        _LOGGER.info("Stopping coordinator")
        await domain_data["coordinator"].stop()


@callback
def _async_find_matching_config_entry(hass):
    for entry in hass.config_entries.async_entries(DOMAIN):
        if entry.source == config_entries.SOURCE_IMPORT:
            return entry

    return None


async def async_remove_entry(hass, entry) -> None:
    """Handle removal of an entry."""
    # Ensure the platform is unloaded before removing the entry
    await async_unload_entry(hass, entry)
    _LOGGER.info(f"Successfully removed entry for {DOMAIN}")


def _legacy_device_id(unique_id: str, account_id: str | None) -> str | None:
    """Return the Neviweb device id of a pre-V2 unique_id, or None if it is not one.

    Pre-V2 formats:
    - "<device_id>": legacy single-account configuration
    - "<account_id>_<device_id>": multi-account (accounts:) or prefixed single account
    """
    if unique_id.isdigit():
        return unique_id
    account, sep, device_id = unique_id.partition("_")
    if sep and account == account_id and device_id.isdigit():
        return device_id
    return None


async def async_migrate_unique_ids(hass: HomeAssistant, entry: ConfigEntry, client: Neviweb130Client) -> None:
    """Migrate pre-V2 unique_ids to the V2 format and attach them to this config entry.

    V2 uses f"{entry.entry_id}_{device_id}". Without this migration, HA creates new
    entities (often with a "_2" suffix) and the old ones become orphans, losing their
    entity_id, area and customizations.

    Must run after the client has logged in and loaded the gateways, so only the orphans
    of this entry's Neviweb account and devices are migrated (multi-account safe).
    """
    registry = er.async_get(hass)
    device_registry = dr.async_get(hass)

    account_id = client._account  # Neviweb account id, set at login
    device_ids = {
        str(device["id"])
        for gateway_data in (client.gateway_data, client.gateway_data2, client.gateway_data3)
        if gateway_data and gateway_data != "_"
        for device in gateway_data
    }

    for reg_entry in list(registry.entities.values()):
        if reg_entry.platform != DOMAIN:
            continue

        old_unique_id = str(reg_entry.unique_id)

        # Already owned by a config entry, just make sure the unique_id is a string
        if reg_entry.config_entry_id is not None:
            if isinstance(reg_entry.unique_id, int):
                registry.async_update_entity(reg_entry.entity_id, new_unique_id=old_unique_id)
            continue

        # Orphan: migrate it only if it belongs to one of this entry's devices
        device_id = _legacy_device_id(old_unique_id, account_id)
        if device_id is None or device_id not in device_ids:
            continue

        new_unique_id = f"{entry.entry_id}_{device_id}"

        # A V2 entity may already exist if V2 was started before this fix.
        # Keep the legacy one, it holds the user's entity_id, area and settings.
        if duplicate := registry.async_get_entity_id(reg_entry.domain, DOMAIN, new_unique_id):
            _LOGGER.info("Removing duplicate %s, replaced by legacy %s", duplicate, reg_entry.entity_id)
            registry.async_remove(duplicate)

        _LOGGER.info(
            "Migrating unique_id for %s from %s to %s",
            reg_entry.entity_id,
            old_unique_id,
            new_unique_id,
        )

        # The V2 main entity represents its device (no name of its own), so HA expects the area
        # on the device and raises a repair if it is set on the entity. Move the legacy area to
        # the device, creating it now with the same identifiers the platforms use; they will
        # fill in its name, model, etc. If the device already has another area, leave both as is.
        area_update = {}
        if reg_entry.area_id:
            device = device_registry.async_get_or_create(
                config_entry_id=entry.entry_id,
                identifiers={(DOMAIN, device_id)},
            )
            if device.area_id is None:
                _LOGGER.info("Moving area %s from %s to its device", reg_entry.area_id, reg_entry.entity_id)
                device_registry.async_update_device(device.id, area_id=reg_entry.area_id)
                area_update["area_id"] = None
            elif device.area_id == reg_entry.area_id:
                area_update["area_id"] = None

        registry.async_update_entity(
            reg_entry.entity_id,
            new_unique_id=new_unique_id,
            config_entry_id=entry.entry_id,
            **area_update,
        )


async def async_migrate_device_models(hass):
    """Migrate numeric device model to string in the device registry."""
    device_registry = dr.async_get(hass)

    # Iterate directly over device entries (future-proof)
    for device in cast(list[DeviceEntry], device_registry.devices):
        # device.identifiers is a set of tuples
        if not any(ident[0] == DOMAIN for ident in device.identifiers):
            continue

        # device.model may be int → must become str
        if isinstance(device.model, int):
            new_model = str(device.model)
            _LOGGER.info(
                "Migrating device model for %s from %s to %s",
                device.id,
                device.model,
                new_model,
            )

            device_registry.async_update_device(
                device.id,
                model=new_model,
            )


async def async_unload_entry(hass, entry):
    """Unload a config entry."""
    unload_ok = await hass.config_entries.async_unload_platforms(entry, PLATFORMS)

    if unload_ok:
        hass.data[DOMAIN].pop(entry.entry_id)

    return unload_ok


async def async_migrate_entry(hass: HomeAssistant, config_entry: ConfigEntry) -> bool:
    """Migrate old entry."""
    return False


def parse_scan_interval(scan_interval):
    """Parse a scan interval in seconds or in the format HH:MM:SS to a timedelta object."""
    if isinstance(scan_interval, int):
        return timedelta(seconds=scan_interval)
    elif isinstance(scan_interval, str):
        h, m, s = map(int, scan_interval.split(":"))
        return timedelta(hours=h, minutes=m, seconds=s)
    else:
        raise ValueError("Invalid scan interval format")


def get_scan_interval(entry: ConfigEntry) -> timedelta:
    """Get the scan interval from the configuration entry or use the default."""
    scan_interval = entry.data.get(CONF_SCAN_INTERVAL, DEFAULT_SCAN_INTERVAL)
    _LOGGER.debug(
        "Parse result = %s from %s",
        parse_scan_interval(scan_interval),
        scan_interval,
    )
    return parse_scan_interval(scan_interval)


async def async_setup_entry(hass: HomeAssistant, entry: ConfigEntry) -> bool:
    """Set up neviweb130 from a config entry."""
    counter = DailyRequestCounter(hass)
    await counter.async_load()

    log_options = extract_log_options(entry)

    setup_logger(
        hass,
        name="custom_components.neviweb130",
        log_path=LOG_PATH,
        level=log_options["log_level"],
        max_bytes=log_options["log_max_bytes"],
        backup_count=log_options["log_backup_count"],
        reset_on_start=log_options["log_reset_on_start"],
    )

    _LOGGER.warning(STARTUP_MESSAGE)

    update_logger_level("custom_components.neviweb130", log_options["log_level"])

    update_logger_config(
        name="custom_components.neviweb130",
        log_path=LOG_PATH,
        level=log_options["log_level"],
        max_bytes=log_options["log_max_bytes"],
        backup_count=log_options["log_backup_count"],
    )

    sanitized = sanitize_entry_data(entry.data)
    _LOGGER.debug("The entry_id = %s", sanitized)

    # Add safe_mode if not in entry.data
    if CONF_SAFE_MODE not in entry.data:
        new_data = {**entry.data, CONF_SAFE_MODE: DEFAULT_SAFE_MODE}
        hass.config_entries.async_update_entry(entry, data=new_data)
        _LOGGER.debug("Migrated config entry: added safe_mode=%s", DEFAULT_SAFE_MODE)

    # Register the event listener for Home Assistant stop event
    hass.bus.async_listen_once(EVENT_HOMEASSISTANT_STOP, partial(async_shutdown, hass))

    if entry.unique_id is None:
        _LOGGER.warning("Config entry has no unique_id.")
        new_unique_id = entry.data.get(CONF_USERNAME, "").strip().lower()
        if new_unique_id:
            hass.config_entries.async_update_entry(entry, unique_id=new_unique_id)
            _LOGGER.info("Migrated config entry to unique_id: %s", new_unique_id)

    # Detect .storage path
    conf_dir = hass.config.path(".storage")
    hass.data.setdefault(DOMAIN, {})
    hass.data[DOMAIN].setdefault(entry.entry_id, {})
    hass.data[DOMAIN]["conf_dir"] = conf_dir

    # Load saved devices data
    device_dict = await load_devices(conf_dir)
    hass.data[DOMAIN]["device_dict"] = device_dict
    _LOGGER.debug("device_dict = %s", device_dict)

    # Call async_migrate_device_models before setting up devices
    _LOGGER.info("Migrating neviweb130 device models to string...")
    await async_migrate_device_models(hass)

    username: str | None = entry.data.get("username")
    password: str | None = entry.data.get("password")
    network: str | None = entry.data.get("network")
    network2: str | None = entry.data.get("network2")
    network3: str | None = entry.data.get("network3")

    if username is None:
        msg = await translate_error(hass, "username_missing")
        raise ConfigEntryError(msg)

    if password is None:
        msg = await translate_error(hass, "password_missing")
        raise ConfigEntryError(msg)

    global SCAN_INTERVAL
    try:
        SCAN_INTERVAL = get_scan_interval(entry)
    except ValueError:
        msg = await translate_error(hass, "scan_interval_error")
        raise ConfigEntryError(msg)

    _LOGGER.debug("Setting scan interval to: %s", SCAN_INTERVAL)

    homekit_mode = entry.data.get(CONF_HOMEKIT_MODE, DEFAULT_HOMEKIT_MODE)
    _LOGGER.debug("Setting Homekit mode to: %s", homekit_mode)

    ignore_miwi = entry.data.get(CONF_IGNORE_MIWI, DEFAULT_IGNORE_MIWI)
    _LOGGER.debug("Setting ignore miwi mode to: %s", ignore_miwi)

    stat_interval = entry.data.get(CONF_STAT_INTERVAL, DEFAULT_STAT_INTERVAL)
    _LOGGER.debug("Setting stat interval to: %s", stat_interval)

    notify = entry.data.get(CONF_NOTIFY, DEFAULT_NOTIFY)
    _LOGGER.debug("Setting notification method to: %s", notify)

    safe_mode = entry.data.get(CONF_SAFE_MODE, DEFAULT_SAFE_MODE)
    _LOGGER.debug("Setting safe_mode to: %s", safe_mode)

    prefix = entry.options.get(CONF_PREFIX, entry.data.get(CONF_PREFIX, DEFAULT_PREFIX))
    _LOGGER.debug("Setting prefix to: %s", prefix)

    request_limit = entry.options.get(CONF_REQUEST_LIMIT, DEFAULT_REQUEST_LIMIT)
    hass.data[DOMAIN][entry.entry_id]["request_limit"] = request_limit

    session_manager = SessionManager()
    hass.data[DOMAIN][entry.entry_id].update(
        {
            "counter": counter,
            "session": session_manager,
        }
    )

    client = Neviweb130Client(
        hass,
        ignore_miwi,
        username,
        password,
        network,
        network2,
        network3,
        safe_mode=safe_mode,
        config_entry=entry,
        session_manager=session_manager,
        counter=counter,
    )
    initialized_coordinator = await async_setup_coordinator(hass, client, SCAN_INTERVAL)

    # Needs the logged-in client (account id and device list), before setting up the platforms
    _LOGGER.info("Migrating neviweb130 unique_id...")
    await async_migrate_unique_ids(hass, entry, client)

    hass.data[DOMAIN][entry.entry_id].update(
        {
            "coordinator": initialized_coordinator,
            "neviweb130_client": initialized_coordinator.client,
            "scan_interval": SCAN_INTERVAL,
            "homekit_mode": homekit_mode,
            "ignore_miwi": ignore_miwi,
            "stat_interval": stat_interval,
            "notify": notify,
            "safe_mode": safe_mode,
            "prefix": prefix,
        }
    )

    # Check weather and customization icons availability
    hass.async_create_task(check_weather_icons_folder(hass))

    await hass.config_entries.async_forward_entry_setups(entry, PLATFORMS)

    return True
