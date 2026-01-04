"""Update entity for Neviweb130 integration."""

import datetime
import logging

from homeassistant.components.update import UpdateEntity, UpdateEntityFeature

from homeassistant.config_entries import ConfigEntry
from homeassistant.core import HomeAssistant
from homeassistant.helpers.entity_platform import AddEntitiesCallback

from .const import DEFAULTS, DOMAIN
from .helpers import build_update_summary

_LOGGER = logging.getLogger(__name__)


def get_entry_data(entry: ConfigEntry, key: str) -> str:
    if key not in entry.data:
        _LOGGER.info("Using default fallback for %s", key)
    return entry.data.get(key, DEFAULTS[key])


def migrate_entry_data(entry: ConfigEntry) -> None:
    for key, default in DEFAULTS.items():
        if key not in entry.data:
            entry.data[key] = default
            _LOGGER.info("Injected default for missing key '%s'", key)


async def async_setup_entry(
    hass: HomeAssistant,
    entry: ConfigEntry,
    async_add_entities: AddEntitiesCallback,
) -> None:
    """Set up Neviweb130 update entity."""

    # Minimal migration : inject default values if absents
    migrate_entry_data(entry)

    async_add_entities([Neviweb130UpdateEntity(hass, entry)])


class Neviweb130UpdateEntity(UpdateEntity):
    """Representation of a Neviweb130 update entity."""

    def __init__(self, hass: HomeAssistant, entry: ConfigEntry) -> None:
        self.hass = hass
        self.entry = entry
        self._attr_name = "Neviweb130 Update"
        self._attr_unique_id = f"{DOMAIN}_{entry.entry_id}_update"

        # Declare supported fonctionality
        self._attr_supported_features = (
            UpdateEntityFeature.INSTALL
            | UpdateEntityFeature.BACKUP
            | UpdateEntityFeature.RELEASE_NOTES
        )

        # Force restart advertising
        self._attr_requires_restart = True

        # Stock version info in config entry
        self._installed_version = get_entry_data(entry, "current_version")
        self._latest_version = get_entry_data(entry, "available_version")

        notes = hass.data[DOMAIN].get("release_notes", DEFAULTS["release_notes"])
        self._release_summary = build_update_summary(
            self._installed_version,
            self._latest_version,
            notes,
        )


    @property
    def installed_version(self) -> str:
        return self._installed_version

    @property
    def latest_version(self) -> str:
        return self._latest_version

    @property
    def release_summary(self) -> str:
        return self._release_summary

    async def async_install(self, version: str | None, backup: bool, **kwargs) -> None:
        """Install update and make backup if selected."""
        if backup:
            await self._do_backup()
        await self._do_update(version)

    async def _do_backup(self) -> None:
        """Backup before update."""
        # Start snapshot of home assistant
        snapshot_name = f"Neviweb130-{self.latest_version}-{datetime.datetime.now().strftime('%Y%m%d-%H%M%S')}"

        try:
            await self.hass.services.async_call(
                "hassio",
                "snapshot_partial",
                {
                    "name": snapshot_name,
                    "folders": ["config"],
                },
                blocking=True,
            )
            _LOGGER.info("Partial snapshot '%s' triggered successfully", snapshot_name)

            # Check snapshot is listed
            backups = await self.hass.services.async_call(
                "hassio",
                "backups",
                {},
                blocking=True,
                return_response=True,
            ) 

            if backups and "data" in backups and "backups" in backups["data"]:
                found = any(b["name"] == snapshot_name for b in backups["data"]["backups"])
                if found:
                    _LOGGER.info("Partial snapshot '%s' confirmed in Supervisor backups", snapshot_name)
                else:
                    _LOGGER.warning("Partial snapshot '%s' not found in Supervisor backups!", snapshot_name)
            else:
                _LOGGER.error("Unable to verify snapshot listing in Supervisor")

        except Exception as err:
            _LOGGER.error("Partial snapshot '%s' failed: %s", snapshot_name, err)

    async def _do_update(self, version: str | None) -> None:
        """Do update."""
        try:
            # TODO: implement actual update logic (API call, file download, etc.)
            _LOGGER.info("Updating Neviweb130 to version %s", version)
        except Exception as err:
            _LOGGER.error("Update fail: %s", err)
