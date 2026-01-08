"""Update entity for Neviweb130 integration."""

import datetime
import hashlib
import logging
import os
import shutil
import tempfile
import zipfile
from datetime import timedelta

import aiohttp
from awesomeversion import AwesomeVersion
from homeassistant.components.update import UpdateEntity, UpdateEntityFeature
from homeassistant.config_entries import ConfigEntry
from homeassistant.core import HomeAssistant
from homeassistant.helpers.entity_platform import AddEntitiesCallback
from homeassistant.helpers.event import async_track_time_interval

from .const import DEFAULTS, DOMAIN
from .helpers import build_update_summary, has_breaking_changes

_LOGGER = logging.getLogger(__name__)


def compute_sha256(file_path: str) -> str:
    """Compute SHA256 hash of a file."""
    sha256 = hashlib.sha256()
    with open(file_path, "rb") as f:
        for chunk in iter(lambda: f.read(8192), b""):
            sha256.update(chunk)
    return sha256.hexdigest()


def get_entry_data(entry: ConfigEntry, key: str) -> str:
    if key not in entry.data:
        _LOGGER.info("Using default fallback for %s", key)
    return entry.data.get(key, DEFAULTS[key])


def migrate_entry_data(entry: ConfigEntry) -> None:
    for key, default in DEFAULTS.items():
        if key not in entry.data:
            entry.data[key] = default
            _LOGGER.info("Injected default for missing key '%s'", key)


async def async_setup_platform(hass, config, add_entities, discovery_info=None):
    """Setup update platform for V1 integration (non-config-entry)."""

    data = hass.data[DOMAIN]["data"]

    if data is None:
        _LOGGER.error("Neviweb130 data not initialized — update entity not created")
        return

    # Dummy ConfigEntry-like object
    class DummyEntry:
        def __init__(self, data):
            self.entry_id = "neviweb130_v1"
            self.data = {
                "current_version": getattr(data, "current_version", None),
                "available_version": getattr(data, "available_version", None),
                "release_notes": getattr(data, "release_notes", None),
            }

    dummy = DummyEntry(data)
    add_entities([Neviweb130UpdateEntity(hass, dummy)], True)


async def async_setup_entry(
    hass: HomeAssistant,
    entry: ConfigEntry,
    async_add_entities: AddEntitiesCallback,
) -> None:
    """Set up Neviweb130 update entity."""

    # Minimal migration : inject default values if absents
    migrate_entry_data(entry)

    entity = Neviweb130UpdateEntity(hass, entry)
    async_add_entities([entity])

    # Check for update every 6 hours
    async def scheduled_check(now):
        await entity.async_check_for_updates()

    async_track_time_interval(
        hass,
        scheduled_check,
        timedelta(hours=6),
    )


class Neviweb130UpdateEntity(UpdateEntity):
    """Representation of a Neviweb130 update entity."""

    def __init__(self, hass: HomeAssistant, entry: ConfigEntry) -> None:
        self.hass = hass
        self.entry = entry
        self._attr_name = "Neviweb130 Update"
        self._attr_unique_id = f"{DOMAIN}_{entry.entry_id}_update"
        self._update_percentage = None
        self._in_progress = False

        # Declare supported fonctionality
        self._attr_supported_features = (
            UpdateEntityFeature.INSTALL | UpdateEntityFeature.BACKUP | UpdateEntityFeature.RELEASE_NOTES
        )

        # Force restart advertising
        self._attr_requires_restart = True

        # Stock version info in config entry
        self._installed_version = entry.data.get("current_version")
        self._latest_version = entry.data.get("available_version")

        # Release notes
        notes = getattr(hass.data[DOMAIN]["data"], "release_notes", DEFAULTS["release_notes"])
        self._release_title = getattr(hass.data[DOMAIN]["data"], "release_title", "")
        self._release_notes = notes
        self._release_summary = build_update_summary(
            self._installed_version,
            self._latest_version,
            notes,
        )
        prefix = ""
        if self.has_breaking_changes:
            prefix += "\U0001f6d1️ (Breaking changes)\n"
        if self._latest_version and any(x in self._latest_version for x in ("b", "beta", "rc")):
            prefix += "\U0001f6a7 (Pre-release version)\n"

        self._release_summary = prefix + self._release_summary

        _LOGGER.warning("Release summary received in update: %s", self._release_summary)

    @property
    def installed_version(self) -> str:
        return self._installed_version

    @property
    def latest_version(self) -> str:
        if self._latest_version and any(x in self._latest_version for x in ("b", "beta", "rc")):
            return f"\U0001f6a7 (pre-release) {self._latest_version}"
        return self._latest_version

    @property
    def has_breaking_changes(self) -> bool:
        return has_breaking_changes(self._release_notes)

    @property
    def release_summary(self) -> str | None:
        try:
            return self._release_summary

        except Exception as err:
            _LOGGER.error("Error building release_summary: %s", err)
            # Simple fallback
            if self._latest_version and self._installed_version:
                return f"Update available: {self._installed_version} → {self._latest_version}"
            return "Update available, but release notes could not be loaded."

    @property
    def release_notes(self) -> str | None:
        return self._release_notes or ""

    @property
    async def async_release_notes(self) -> str | None:
        return self._release_notes or ""

    @property
    def release_url(self) -> str | None:
        if self._latest_version:
            return f"https://github.com/claudegel/sinope-130/releases/v{self._latest_version}"
        return None

    @property
    def title(self) -> str:
        base = f"Neviweb130 {self._latest_version or ''}".strip()

        # Add release title
        if self._release_title:
            base = f"{base} – {self._release_title}"

        # Add icon pre-release
        if self._latest_version and any(x in self._latest_version for x in ("b", "beta", "rc")):
            base = f"\U0001f6a7 PRE-RELEASE – {base}"

        # Add icon if breaking changes
        if self.has_breaking_changes:
            base = f"\U0001f6d1 BREAKING – {base}"

        return base

    @property
    def update_percentage(self) -> int | None:
        return self._update_percentage

    @property
    def in_progress(self) -> bool | int:
        return self._update_percentage if self._in_progress else False

    async def async_check_for_updates(self):
        """Check GitHub for new releases and update entity state."""

        try:
            async with aiohttp.ClientSession() as session:
                async with session.get("https://api.github.com/repos/claudegel/sinope-130/releases/latest") as resp:
                    resp.raise_for_status()
                    data = await resp.json()

            latest = data.get("tag_name", "").lstrip("v")
            notes = data.get("body", "")
            title = data.get("name", "")

            if latest and latest != self._latest_version:
                _LOGGER.info("New Neviweb130 version detected: %s", latest)

                # Update entry.data
                self.entry.data["available_version"] = latest
                self.hass.data[DOMAIN]["data"].release_notes = notes
                self.hass.data[DOMAIN]["data"].release_title = title
                self._latest_version = latest
                self._release_notes = notes
                self._release_title = title
                self._release_summary = build_update_summary(
                    self._installed_version,
                    self._latest_version,
                    notes,
                )

                prefix = ""
                if self.has_breaking_changes:
                    prefix += "⚠️ (Breaking changes)\n"
                if self._latest_version and any(x in self._latest_version for x in ("b", "beta", "rc")):
                    prefix += "🧪 (Pre-release version)\n"

                self._release_summary = prefix + self._release_summary

                # Reload update entity
                await self.hass.config_entries.async_reload(self.entry.entry_id)

        except Exception as err:
            _LOGGER.error("Failed to check for updates: %s", err)

    async def async_install(self, version: str | None, backup: bool, **kwargs) -> None:
        """Install update and make backup if selected."""
        if backup:
            await self._do_backup()
        await self._do_update(version)

    async def _do_backup(self) -> None:
        """Backup before update."""
        # Start snapshot of home assistant
        snapshot_name = f"Neviweb130-{self.installed_version}-{datetime.datetime.now().strftime('%Y%m%d-%H%M%S')}"

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
        self._in_progress = True
        self._update_percentage = 0
        self.async_write_ha_state()

        # Validate version is compatible to update
        if version and self._installed_version:
            try:
                if AwesomeVersion(version) < AwesomeVersion(self._installed_version):
                    _LOGGER.error("Refusing downgrade: %s < %s", version, self._installed_version)

                    # Return entity to proper state
                    self._in_progress = False
                    self._update_percentage = None
                    self.async_write_ha_state()
                    return

            except Exception as err:
                _LOGGER.warning("Version comparison failed: %s", err)

                # Return entity to proper state
                self._in_progress = False
                self._update_percentage = None
                self.async_write_ha_state()
                return

        tag = f"v{version}" if not version.startswith("v") else version
        url = f"https://github.com/claudegel/sinope-130/archive/refs/tags/{tag}.zip"
        backup_dir = None

        api_url = f"https://api.github.com/repos/claudegel/sinope-130/releases/tags/{tag}"

        try:
            async with aiohttp.ClientSession() as session:
                async with session.get(api_url) as resp:
                    resp.raise_for_status()
                    release_data = await resp.json()

            # Find the asset matching our ZIP
            expected_sha256 = None
            for asset in release_data.get("assets", []):
                if asset["name"].endswith(".zip") and "sha256" in asset:
                    expected_sha256 = asset["sha256"]
                    break

            if not expected_sha256:
                raise Exception("SHA256 not found in GitHub release assets")
        except Exception as err:
            _LOGGER.error("Unable to retrieve SHA256 from GitHub: %s", err)
            # Notification
            await self.hass.services.async_call(
                "persistent_notification",
                "create",
                {
                    "title": "Neviweb130 – Update aborted",
                    "message": (
                        f"Unable to retrieve SHA256 for version {version}.\nUpdate aborted for security reasons."
                    ),
                    "notification_id": "neviweb130_update_status",
                },
            )
            self._in_progress = False
            self._update_percentage = None
            self.async_write_ha_state()
            return

        try:
            # 1- Download ZIP file
            self._update_percentage = 10
            self.async_write_ha_state()

            async with aiohttp.ClientSession() as session:
                async with session.get(url) as resp:
                    resp.raise_for_status()
                    data = await resp.read()

            # 2- Save to temp file
            self._update_percentage = 30
            self.async_write_ha_state()

            tmp_zip = tempfile.NamedTemporaryFile(delete=False)
            tmp_zip.write(data)
            tmp_zip.close()

            # NEW: Compute local SHA256
            local_sha256 = compute_sha256(tmp_zip.name)

            if local_sha256.lower() != expected_sha256.lower():
                _LOGGER.error(
                    "SHA256 mismatch! Expected %s but got %s",
                    expected_sha256,
                    local_sha256,
                )

                await self.hass.services.async_call(
                    "persistent_notification",
                    "create",
                    {
                        "title": "Neviweb130 – Update aborted (security check failed)",
                        "message": (f"SHA256 mismatch for version {version}.\nUpdate aborted to protect your system."),
                        "notification_id": "neviweb130_update_status",
                    },
                )

                # Abort update
                self._in_progress = False
                self._update_percentage = None
                self.async_write_ha_state()

                os.remove(tmp_zip.name)
                return

            # 3- Extract ZIP
            self._update_percentage = 50
            self.async_write_ha_state()

            tmp_dir = tempfile.mkdtemp()
            with zipfile.ZipFile(tmp_zip.name, "r") as zip_ref:
                zip_ref.extractall(tmp_dir)

            # 4- Copy file to neviweb130 custom_component directory
            self._update_percentage = 80
            self.async_write_ha_state()

            extracted_root = os.path.join(tmp_dir, os.listdir(tmp_dir)[0])
            target_dir = os.path.join(self.hass.config.path(), "custom_components", DOMAIN)

            # Backup actual version
            backup_dir = tempfile.mkdtemp(prefix="neviweb130_backup_")
            shutil.copytree(target_dir, backup_dir, dirs_exist_ok=True)

            # Suppress old directory
            shutil.rmtree(target_dir)

            # Copy all files from new version
            shutil.copytree(extracted_root, target_dir, dirs_exist_ok=True)

            # 5- Cleanup
            self._update_percentage = 95
            self.async_write_ha_state()

            os.remove(tmp_zip.name)
            shutil.rmtree(tmp_dir)

            # 6- Finalise
            self._update_percentage = 100
            self.async_write_ha_state()

            await asyncio.sleep(1)
            await self.hass.config_entries.async_reload(self.entry.entry_id)
            await self.hass.services.async_call(
                "persistent_notification",
                "create",
                {
                    "title": "Neviweb130 – Update successful",
                    "message": (
                        f"Update to version {version} was installed successfully.\n"
                        f"[See update notes]({self.release_url})"
                    ),
                    "notification_id": "neviweb130_update_status",
                },
            )

            _LOGGER.info("Neviweb130 updated to version %s", version)

        except Exception as err:
            _LOGGER.error("Update fail: %s", err)
            await self.hass.services.async_call(
                "persistent_notification",
                "create",
                {
                    "title": "Neviweb130 – Update failed",
                    "message": (
                        f"Update to version {version} failed.\n"
                        f"A rollback was performed and the old version was restored.\n"
                        f"[See update notes]({self.release_url})"
                    ),
                    "notification_id": "neviweb130_update_status",
                },
            )

            self._in_progress = False
            self._update_percentage = None
            self.async_write_ha_state()

            # Rollback : restore old version
            try:
                if os.path.exists(target_dir):
                    shutil.rmtree(target_dir)
                shutil.copytree(backup_dir, target_dir, dirs_exist_ok=True)
                _LOGGER.warning("Rollback completed successfully")
            except Exception as rb_err:
                _LOGGER.error("Rollback failed: %s", rb_err)

        finally:
            self._in_progress = False
            self._update_percentage = None
            self.async_write_ha_state()

            # Cleanup du backup
            try:
                if backup_dir:
                    shutil.rmtree(backup_dir)
            except Exception:
                pass
