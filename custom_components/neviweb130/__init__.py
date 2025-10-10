"""Sinopé GT130 Zigbee and Wi-Fi support."""

from __future__ import annotations

import logging
from datetime import timedelta

import voluptuous as vol
from homeassistant import config_entries
from homeassistant.config_entries import ConfigEntry
from homeassistant.const import CONF_SCAN_INTERVAL, CONF_USERNAME, EVENT_HOMEASSISTANT_STOP
from homeassistant.core import HomeAssistant, callback
from homeassistant.helpers import config_validation as cv
from homeassistant.helpers import entity_registry as er
from homeassistant.helpers.typing import ConfigType

from .const import CONF_HOMEKIT_MODE, CONF_IGNORE_MIWI, CONF_NOTIFY, CONF_STAT_INTERVAL, DOMAIN, STARTUP_MESSAGE
from .coordinator import Neviweb130Client, async_setup_coordinator
from .devices import load_devices, save_devices
from .schema import HOMEKIT_MODE as DEFAULT_HOMEKIT_MODE
from .schema import IGNORE_MIWI as DEFAULT_IGNORE_MIWI
from .schema import NOTIFY as DEFAULT_NOTIFY
from .schema import PLATFORMS
from .schema import SCAN_INTERVAL as DEFAULT_SCAN_INTERVAL
from .schema import STAT_INTERVAL as DEFAULT_STAT_INTERVAL

SCAN_INTERVAL = DEFAULT_SCAN_INTERVAL
CONFIG_SCHEMA = cv.config_entry_only_config_schema(DOMAIN)

_LOGGER = logging.getLogger(__name__)


async def async_setup(hass: HomeAssistant, config: ConfigType) -> bool:
    """import neviweb130 integration from YAML if it exists."""
    _LOGGER.info(STARTUP_MESSAGE)

    neviweb130_config: ConfigType | None = config.get(DOMAIN)
    _LOGGER.debug("Config found: %s", neviweb130_config)
    hass.data.setdefault(DOMAIN, {})

    if not neviweb130_config:
        return True
    else:
        # Convert CONF_SCAN_INTERVAL timedelta object to seconds
        scan_interval = neviweb130_config.get(CONF_SCAN_INTERVAL)
        _LOGGER.debug("The scan interval config = %s", scan_interval)
        if isinstance(scan_interval, timedelta):
            neviweb130_config[CONF_SCAN_INTERVAL] = int(scan_interval.total_seconds())

    # Only import if we haven't before.
    config_entry = _async_find_matching_config_entry(hass)
    _LOGGER.debug("Previous Entry found = %s", config_entry)
    if not config_entry:
        hass.async_create_task(
            hass.config_entries.flow.async_init(
                DOMAIN,
                context={"source": config_entries.SOURCE_IMPORT},
                data=dict(neviweb130_config),
            )
        )
        return True

    # Update the entry based on the YAML configuration, in case it changed.
    hass.config_entries.async_update_entry(config_entry, data=dict(neviweb130_config))
    return True


async def async_shutdown(hass: HomeAssistant, event=None):
    """Handle Home Assistant shutdown."""
    _LOGGER.info("Shutting down Neviweb130 custom component")

    conf_dir = hass.data[DOMAIN]["conf_dir"]
    if not conf_dir:
        _LOGGER.error("conf_dir is missing during shutdown — data will not be saved.")
        return

    data = hass.data[DOMAIN].get("device_dict", {})

    if conf_dir:
        await save_devices(conf_dir, data)
        _LOGGER.info("Energy stat data saved")
    else:
        _LOGGER.warning("No conf_dir found during shutdown.")

    if DOMAIN in hass.data and "coordinator" in hass.data[DOMAIN]:
        _LOGGER.info("Stopping coordinator")
        await hass.data[DOMAIN]["coordinator"].stop()


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


async def async_migrate_unique_ids(hass):
    """Migrate numeric unique_ids to string in the entity registry."""
    registry = er.async_get(hass)

    for entity_id, entity in registry.entities.items():
        if entity.platform == "neviweb130" and isinstance(entity.unique_id, int):
            new_unique_id = str(entity.unique_id)
            _LOGGER.info(
                "Migrating unique_id for %s from %s to %s",
                entity_id,
                entity.unique_id,
                new_unique_id,
            )
            registry.async_update_entity(entity_id, new_unique_id=new_unique_id)


async def async_unload_entry(hass, entry):
    """Unload a config entry."""
    unload_ok = await hass.config_entries.async_forward_entry_unload(entry, "climate")
    unload_ok = unload_ok and await hass.config_entries.async_forward_entry_unload(entry, "light")
    unload_ok = unload_ok and await hass.config_entries.async_forward_entry_unload(entry, "switch")
    unload_ok = unload_ok and await hass.config_entries.async_forward_entry_unload(entry, "sensor")
    unload_ok = unload_ok and await hass.config_entries.async_forward_entry_unload(entry, "valve")
    unload_ok = unload_ok and await hass.config_entries.async_forward_entry_unload(entry, "binary_sensor")
    unload_ok = unload_ok and await hass.config_entries.async_forward_entry_unload(entry, "button")
    unload_ok = unload_ok and await hass.config_entries.async_forward_entry_unload(entry, "number")
    unload_ok = unload_ok and await hass.config_entries.async_forward_entry_unload(entry, "select")

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
    scan_interval = entry.data.get(CONF_SCAN_INTERVAL, DEFAULT_SCAN_INTERVAL.total_seconds())
    _LOGGER.debug(
        "Parse result = %s from %s",
        parse_scan_interval(scan_interval),
        scan_interval,
    )
    return parse_scan_interval(scan_interval)


async def async_setup_entry(hass: HomeAssistant, entry: ConfigEntry) -> bool:
    """Set up neviweb130 from a config entry."""
    _LOGGER.debug("The entry_id = %s", entry.data)

    # Register the event listener for Home Assistant stop event
    hass.bus.async_listen_once(EVENT_HOMEASSISTANT_STOP, async_shutdown)

    if entry.unique_id is None:
        _LOGGER.warning("Config entry has no unique_id.")
        new_unique_id = entry.data.get(CONF_USERNAME, "").strip().lower()
        if new_unique_id:
            hass.config_entries.async_update_entry(entry, unique_id=new_unique_id)
            _LOGGER.info("Migrated config entry to unique_id: %s", new_unique_id)

    # Detect .storage path
    conf_dir = hass.config.path(".storage")
    hass.data.setdefault(DOMAIN, {})
    hass.data[DOMAIN]["conf_dir"] = conf_dir

    # Load saved devices data
    device_dict = await load_devices(conf_dir)
    hass.data[DOMAIN]["device_dict"] = device_dict

    # Call async_migrate_unique_ids before setting up devices
    _LOGGER.info("Migrating neviweb130 unique_id to string...")
    await async_migrate_unique_ids(hass)

    username: str | None = entry.data.get("username")
    password: str | None = entry.data.get("password")
    network: str | None = entry.data.get("network")
    network2: str | None = entry.data.get("network2")
    network3: str | None = entry.data.get("network3")

    if username is None:
        raise TypeError("username is None")
    if password is None:
        raise TypeError("password is None")

    global SCAN_INTERVAL
    SCAN_INTERVAL = get_scan_interval(entry)
    _LOGGER.debug("Setting scan interval to: %s", SCAN_INTERVAL)

    homekit_mode = entry.data.get(CONF_HOMEKIT_MODE, DEFAULT_HOMEKIT_MODE)
    _LOGGER.debug("Setting Homekit mode to: %s", homekit_mode)

    ignore_miwi = entry.data.get(CONF_IGNORE_MIWI, DEFAULT_IGNORE_MIWI)
    _LOGGER.debug("Setting ignore miwi mode to: %s", ignore_miwi)

    stat_interval = entry.data.get(CONF_STAT_INTERVAL, DEFAULT_STAT_INTERVAL)
    _LOGGER.debug("Setting stat interval to: %s", stat_interval)

    notify = entry.data.get(CONF_NOTIFY, DEFAULT_NOTIFY)
    _LOGGER.debug("Setting notification method to: %s", notify)

    client = Neviweb130Client(hass, ignore_miwi, username, password, network, network2, network3)
    initialized_coordinator = await async_setup_coordinator(hass, client, SCAN_INTERVAL)

    hass.data[DOMAIN][entry.entry_id] = {
        "coordinator": initialized_coordinator,
        "neviweb130_client": initialized_coordinator.client,
        "scan_interval": SCAN_INTERVAL,
        "homekit_mode": homekit_mode,
        "ignore_miwi": ignore_miwi,
        "stat_interval": stat_interval,
        "notify": notify,
    }

    await hass.config_entries.async_forward_entry_setups(entry, PLATFORMS)

    return True
