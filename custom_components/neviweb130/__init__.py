""" Sinopé GT130 zigbee and wifi support. """

from __future__ import annotations

import logging
from datetime import timedelta
from typing import Optional

import voluptuous as vol

from homeassistant import config_entries
from homeassistant.core import HomeAssistant, callback
from homeassistant.helpers import (
    config_validation as cv,
    entity_registry as er,
)
from homeassistant.helpers.typing import ConfigType
from homeassistant.const import (
    CONF_USERNAME,
    CONF_PASSWORD,
    CONF_SCAN_INTERVAL,
    EVENT_HOMEASSISTANT_STOP,
)
from homeassistant.util import Throttle
from homeassistant.helpers.update_coordinator import DataUpdateCoordinator

from .const import (
    DOMAIN,
    CONF_HOMEKIT_MODE,
    CONF_NETWORK,
    CONF_NETWORK2,
    CONF_NETWORK3,
    CONF_NOTIFY,
    CONF_STAT_INTERVAL,
)

from .schema import (
    CONFIG_SCHEMA,
    HOMEKIT_MODE as DEFAULT_HOMEKIT_MODE,
    NOTIFY as DEFAULT_NOTIFY,
    PLATFORMS,
    SCAN_INTERVAL as DEFAULT_SCAN_INTERVAL,
    STAT_INTERVAL as DEFAULT_STAT_INTERVAL,
    VERSION,
)

from .coordinator import (
    Neviweb130Client,
    async_setup_coordinator,
)

_LOGGER = logging.getLogger(__name__)


async def async_setup(hass: HomeAssistant, config: ConfigType) -> bool:
    """import neviweb130 integration from YAML if exist."""

    # Register the event listener for Home Assistant stop event
    hass.bus.async_listen_once(EVENT_HOMEASSISTANT_STOP, async_shutdown)

    neviweb130_config: Optional[ConfigType] = config.get(DOMAIN)
    _LOGGER.debug("Config found: %s", neviweb130_config)
    hass.data.setdefault(DOMAIN, {})

    if not neviweb130_config:
        return True
    else:
        ## Convert CONF_SCAN_INTERVAL timedelta object to seconds
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

@callback
async def async_shutdown(event):
    """Handle Home Assistant shutdown."""
    _LOGGER.info("Shutting down Neviweb130 custom component")
    coordinator = event.data[DOMAIN]['coordinator']
    await coordinator.stop()

@callback
def _async_find_matching_config_entry(hass):
    for entry in hass.config_entries.async_entries(DOMAIN):
        if entry.source == config_entries.SOURCE_IMPORT:
            return entry

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
            _LOGGER.info("Migrating unique_id for %s from %s to %s", entity_id, entity.unique_id, new_unique_id)
            registry.async_update_entity(entity_id, new_unique_id=new_unique_id)

async def async_unload_entry(hass, entry):
    """Unload a config entry."""
    unload_ok = await hass.config_entries.async_forward_entry_unload(entry, 'climate')
    unload_ok = unload_ok and await hass.config_entries.async_forward_entry_unload(entry, 'light')
    unload_ok = unload_ok and await hass.config_entries.async_forward_entry_unload(entry, 'switch')
    unload_ok = unload_ok and await hass.config_entries.async_forward_entry_unload(entry, 'sensor')
    unload_ok = unload_ok and await hass.config_entries.async_forward_entry_unload(entry, 'valve')

    if unload_ok:
        hass.data[DOMAIN].pop(entry.entry_id)

    return unload_ok

async def async_migrate_entry(hass: HomeAssistant, config_entry: ConfigEntry) -> bool:
    """Migrate old entry."""

def parse_scan_interval(scan_interval):
    """Parse a scan interval in seconds or in the format HH:MM:SS to a timedelta object."""
    if isinstance(scan_interval, int):
        return timedelta(seconds=scan_interval)
    elif isinstance(scan_interval, str):
        h, m, s = map(int, scan_interval.split(':'))
        return timedelta(hours=h, minutes=m, seconds=s)
    else:
        raise ValueError("Invalid scan interval format")

def get_scan_interval(entry: ConfigEntry) -> timedelta:
    """Get the scan interval from the configuration entry or use the default."""
    scan_interval = entry.data.get(CONF_SCAN_INTERVAL, DEFAULT_SCAN_INTERVAL.total_seconds())
    _LOGGER.debug("Parse result = $s", parse_scan_interval(scan_interval))
    return parse_scan_interval(scan_interval)

async def async_setup_entry(hass: HomeAssistant, entry: ConfigEntry) -> bool:
    """Set up neviweb130 from a config entry."""
    _LOGGER.debug("The entry_id = %s", entry.data)

    hass.data.setdefault(DOMAIN, {})

    username = entry.data.get("username")
    password = entry.data.get("password")
    network = entry.data.get("network")
    network2 = entry.data.get("network2")
    network3 = entry.data.get("network3")

    scan_interval = get_scan_interval(entry)
    _LOGGER.debug("Setting scan interval to: %s", scan_interval)

    homekit_mode = entry.data.get(CONF_HOMEKIT_MODE, DEFAULT_HOMEKIT_MODE)
    _LOGGER.debug("Setting Homekit mode to: %s", homekit_mode)

    stat_interval = entry.data.get(CONF_STAT_INTERVAL, DEFAULT_STAT_INTERVAL)
    _LOGGER.debug("Setting stat interval to: %s", stat_interval)

    notify = entry.data.get(CONF_NOTIFY, DEFAULT_NOTIFY)
    _LOGGER.debug("Setting notification method to: %s", notify)

    client = Neviweb130Client(hass, username, password, network, network2, network3)
    coordinator = await async_setup_coordinator(hass, client, scan_interval)

    hass.data[DOMAIN][entry.entry_id] = {
        "coordinator": coordinator,
        "neviweb130_client": coordinator.client,
        "scan_interval": scan_interval,
        "homekit_mode": homekit_mode,
        "stat_interval": stat_interval,
        "notify": notify,
    }

    await hass.config_entries.async_forward_entry_setups(entry, PLATFORMS)

    return True
