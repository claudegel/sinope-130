"""Update entity for Neviweb130 integration."""

import datetime
import hashlib
import logging
import os
import re
import shutil
import tempfile
import zipfile
import markdown
from datetime import timedelta
from typing import Any

import aiohttp
from homeassistant.components.update import UpdateEntity, UpdateEntityFeature
from homeassistant.config_entries import ConfigEntry
from homeassistant.core import HomeAssistant
from homeassistant.helpers.entity_platform import AddEntitiesCallback
from homeassistant.helpers.event import async_track_time_interval

from .const import (
    DOMAIN,
    VERSION,
    CONF_UPDATE_INTERVAL,
    DEFAULT_UPDATE_INTERVAL,
)
from .helpers import build_update_summary, has_breaking_changes

_LOGGER = logging.getLogger(__name__)

DEFAULTS = {
    "current_version": f"v{VERSION}",
    "available_version": None,
    "release_notes": "No release notes available (default fallback).",
    "release_title": "",
}

VALID_ASSET_PATTERN = re.compile(r"^sinope-130-(v[\w\.\-]+)\.(zip|sha256)$")

def compute_sha256(file_path: str) -> str:
    sha256 = hashlib.sha256()
    with open(file_path, "rb") as f:
        for chunk in iter(lambda: f.read(8192), b""):
            sha256.update(chunk)
    return sha256.hexdigest()


def filter_valid_assets(assets, expected_version):
    valid_assets = []
    for asset in assets:
        name = asset.get("name", "")
        match = VALID_ASSET_PATTERN.match(name)
        if not match:
            continue

        version = match.group(1)
        if version != expected_version:
            continue

        valid_assets.append(asset)

    return valid_assets


def normalize_version(version: str | None) -> str | None:
    if version is None:
        return None
    if not version.startswith("v"):
        return f"v{version}"
    return version


def get_entry_data(entry: ConfigEntry, key: str) -> str:
    if key not in entry.data:
        _LOGGER.debug("Using default fallback for %s", key)
    return entry.data.get(key, DEFAULTS[key])


async def async_setup_entry(
    hass: HomeAssistant,
    entry: ConfigEntry,
    async_add_entities: AddEntitiesCallback,
) -> None:

    entity = Neviweb130UpdateEntity(hass, entry)
    async_add_entities([entity])

    # Dynamic Scheduler based on option
    interval_str = entry.options.get(CONF_UPDATE_INTERVAL, DEFAULT_UPDATE_INTERVAL)
    hours = int(interval_str.replace("h", ""))
    interval = timedelta(hours=hours)

    async def _scheduled_check(now):
        await entity.async_check_for_updates()

    async_track_time_interval(hass, _scheduled_check, interval)


class Neviweb130UpdateEntity(UpdateEntity):
    """Representation of a Neviweb130 update entity."""

    def __init__(self, hass: HomeAssistant, entry: ConfigEntry) -> None:
        self.hass = hass
        self.entry = entry
        self._attr_name = "Neviweb130 Update"
        self._attr_unique_id = f"{DOMAIN}_{entry.entry_id}_update"

        # Internal state
        self._update_percentage: int | None = None
        self._in_progress: bool = False
        self._last_check: str | None = None
        self._next_check: str | None = None
        self._last_update_success: str | None = None
        self._update_status: str = "idle"
        self._rollback_status: str = "none"
        self._local_backup_dir: str | None = None
        self._target_dir: str = self.hass.config.path("custom_components/neviweb130")

        # Supported features
        self._attr_supported_features = (
            UpdateEntityFeature.INSTALL
            | UpdateEntityFeature.BACKUP
            | UpdateEntityFeature.RELEASE_NOTES
            | UpdateEntityFeature.PROGRESS
        )

        self._attr_requires_restart = True

        # Load versions
        self._installed_version = normalize_version(get_entry_data(entry, "current_version"))
        self._latest_version = normalize_version(get_entry_data(entry, "available_version"))
        self._release_title = get_entry_data(entry, "release_title")
        self._release_notes = get_entry_data(entry, "release_notes")

        # Build summary
        summary = build_update_summary(
            self._installed_version or "",
            self._latest_version or "",
            self._release_notes or "",
        )

        prefix = ""
        if has_breaking_changes(self._release_notes):
            prefix += "🛑 BREAKING CHANGES\n"
        if self._latest_version and any(x in self._latest_version for x in ("b", "beta", "rc")):
            prefix += "🚧 PRE-RELEASE VERSION\n"

        self._release_summary = prefix + summary

    # -----------------------------
    # Properties
    # -----------------------------

    @property
    def installed_version(self) -> str:
        return self._installed_version

    @property
    def latest_version(self) -> str | None:
        return self._latest_version

    @property
    def has_breaking_changes(self) -> bool:
        return has_breaking_changes(self._release_notes)

    @property
    def release_summary(self) -> str:
        try:
            return self._release_summary
        except Exception as err:  # pragma: no cover - defensive
            _LOGGER.error("Error building release_summary: %s", err)
            if self._latest_version and self._installed_version:
                return f"Update available: {self._installed_version} → {self._latest_version}"
            return "Update available, but release notes could not be loaded."

    @property
    def release_url(self) -> str | None:
        if self._latest_version:
            return f"https://github.com/claudegel/sinope-130/releases/tag/{self._latest_version}"
        return None

    @property
    def title(self) -> str:
        base = f"Neviweb130 {self._latest_version or ''}".strip()

        if self._release_title:
            base = f"{base} – {self._release_title}"

        if self._latest_version and any(x in self._latest_version for x in ("b", "beta", "rc")):
            base = f"\U0001f6a7 PRE-RELEASE – {base}"

        if self.has_breaking_changes:
            base = f"\U0001f6d1 BREAKING – {base}"

        return base

    @property
    def update_percentage(self) -> int | None:
        """Return data for progress bar in update."""
        return self._update_percentage

    @property
    def in_progress(self) -> bool:
        return self._in_progress

    @property
    def extra_state_attributes(self):
        attrs = {}
        if self._last_check:
            attrs["last_check"] = self._last_check
        if self._next_check:
            attrs["next_check"] = self._next_check
        if self._last_update_success:
            attrs["last_update_success"] = self._last_update_success
        if self._update_status:
            attrs["update_status"] = self._update_status
        if self._rollback_status:
            attrs["rollback_status"] = self._rollback_status

        # Expose interval
        attrs["check_interval"] = self.entry.options.get(CONF_UPDATE_INTERVAL, DEFAULT_UPDATE_INTERVAL)

        return attrs

    # -----------------------------
    # Release notes
    # -----------------------------

    async def async_release_notes(self) -> str | None:
        if not self._release_notes:
            return "<p>No release notes available.</p>"
        return markdown.markdown(self._release_notes)

    # -----------------------------
    # Update check
    # -----------------------------

    async def async_check_for_updates(self) -> None:
        self._last_check = datetime.datetime.now().isoformat()

        try:
            async with aiohttp.ClientSession() as session:
                async with session.get("https://api.github.com/repos/claudegel/sinope-130/releases") as resp:
                    resp.raise_for_status()
                    releases = await resp.json()

            latest_release = releases[0]
            latest = latest_release.get("tag_name", "").lstrip("v")
            notes = latest_release.get("body", "")
            title = latest_release.get("name", "")

            if not latest:
                _LOGGER.warning("GitHub returned an empty tag_name")
                return

            if normalize_version(latest) == self._latest_version:
                return

            _LOGGER.info("New Neviweb130 version detected: %s", latest)

            self._latest_version = normalize_version(latest)
            self._release_notes = notes
            self._release_title = title

            summary = build_update_summary(
                self._installed_version or "",
                self._latest_version or "",
                notes or "",
            )

            prefix = ""
            if has_breaking_changes(notes):
                prefix += "\U0001f6d1 BREAKING CHANGES\n"
            if any(x in latest for x in ("b", "beta", "rc")):
                prefix += "\U0001f6a7 PRE-RELEASE VERSION\n"

            self._release_summary = prefix + summary

            # Persist in entry.data
            self.hass.config_entries.async_update_entry(
                self.entry,
                data={
                    **self.entry.data,
                    "available_version": latest,
                    "release_notes": notes,
                    "release_title": title,
                },
            )

            self.async_write_ha_state()

        except Exception as err:
            _LOGGER.error("Failed to check for updates: %s", err)

    # -----------------------------
    # Install
    # -----------------------------

    async def async_install(self, version: str | None, backup: bool, **kwargs) -> None:
        if backup:
            await self._do_backup()
        await self._do_update(version)

    async def _do_backup(self) -> None:
        backup_mode = self.entry.options.get("backup_mode", "full")
        folders = self.entry.options.get("backup_folders", [])

        snapshot_name = f"Neviweb130-{self.installed_version}-{datetime.datetime.now().strftime('%Y%m%d-%H%M%S')}"

        try:
            if backup_mode == "full":
                await self.hass.services.async_call(
                    "hassio",
                    "backup_full",
                    {"name": snapshot_name},
                    blocking=True,
                )
                _LOGGER.info("Full backup '%s' triggered successfully", snapshot_name)
            else:
                await self.hass.services.async_call(
                    "hassio",
                    "backup_partial",
                    {"name": snapshot_name, "folders": folders},
                    blocking=True,
                )
                _LOGGER.info("Partial backup '%s' triggered successfully", snapshot_name)

        except Exception as err:
            _LOGGER.error("Snapshot failed: %s", err)

    async def _do_update(self, version: str | None) -> None:
        self._rollback_status = "none"
        self._update_status = "updating"
        self._in_progress = True
        self._update_percentage = 0
        self.async_write_ha_state()

        try:
            # Determine tag
            if version:
                tag = f"v{version}" if not version.startswith("v") else version
            else:
                tag = self._latest_version

            api_url = f"https://api.github.com/repos/claudegel/sinope-130/releases/tags/{tag}"

            async with aiohttp.ClientSession() as session:
                async with session.get(api_url) as resp:
                    resp.raise_for_status()
                    release_data = await resp.json()

            asset_zip = next(
                (a for a in release_data.get("assets", []) if a.get("name", "").endswith(".zip")),
                None,
            )
            asset_sha = next(
                (a for a in release_data.get("assets", []) if a.get("name", "").endswith(".sha256")),
                None,
            )

            if not asset_zip or not asset_sha:
                raise Exception("ZIP or SHA256 asset not found in GitHub release")

            # Download SHA256
            async with aiohttp.ClientSession() as session:
                async with session.get(asset_sha["browser_download_url"]) as resp:
                    resp.raise_for_status()
                    expected_sha256 = (await resp.text()).strip()

            # 1- Download ZIP
            self._update_percentage = 10
            self.async_write_ha_state()

            async with aiohttp.ClientSession() as session:
                async with session.get(asset_zip["browser_download_url"]) as resp:
                    resp.raise_for_status()
                    data = await resp.read()

            # 2- Save to temp file
            self._update_percentage = 30
            self.async_write_ha_state()

            tmp_zip = tempfile.NamedTemporaryFile(delete=False)
            tmp_zip.write(data)
            tmp_zip.close()

            # Validate SHA256
            local_sha256 = compute_sha256(tmp_zip.name)
            expected_sha256 = expected_sha256.strip().split()[0]
            if local_sha256.lower() != expected_sha256.lower():
                _LOGGER.error("SHA256 mismatch! Expected %s but got %s", expected_sha256, local_sha256)

                await self.hass.services.async_call(
                    "persistent_notification",
                    "create",
                    {
                        "title": "Neviweb130 – Update aborted (security check failed)",
                        "message": f"SHA256 mismatch for version {version}.\nUpdate aborted to protect your system.",
                        "notification_id": "neviweb130_update_status",
                    },
                )
                self._in_progress = False
                self._update_percentage = None
                self.async_write_ha_state()

                os.remove(tmp_zip.name)
                raise Exception("SHA256 mismatch")

            # 3- Extract ZIP
            self._update_percentage = 50
            self.async_write_ha_state()

            tmp_dir = tempfile.mkdtemp()
            with zipfile.ZipFile(tmp_zip.name, "r") as zip_ref:
                zip_ref.extractall(tmp_dir)

            # 4- Copy files to custom_components/neviweb130
            self._update_percentage = 80
            self.async_write_ha_state()

            # Always create a local backup for rollback
            backup_dir = tempfile.mkdtemp(prefix="neviweb130_backup_")
            shutil.copytree(self._target_dir, backup_dir, dirs_exist_ok=True)
            self._local_backup_dir = backup_dir
            _LOGGER.info("Local backup created at %s", backup_dir)

            # Remove old version
            shutil.rmtree(self._target_dir)
            os.makedirs(self._target_dir, exist_ok=True)

            # Detect root folder inside extracted ZIP
            entries = os.listdir(tmp_dir)
            if len(entries) == 1 and os.path.isdir(os.path.join(tmp_dir, entries[0])):
                extracted_root = os.path.join(tmp_dir, entries[0])
            else:
                extracted_root = tmp_dir

            # Copy content of extracted_root into target_dir
            for item in os.listdir(extracted_root):
                src = os.path.join(extracted_root, item)
                dst = os.path.join(self._target_dir, item)

                if os.path.isdir(src):
                    shutil.copytree(src, dst, dirs_exist_ok=True)
                else:
                    shutil.copy2(src, dst)

            _LOGGER.info("New version installed successfully into %s", self._target_dir)

            # 5- Cleanup
            self._update_percentage = 95
            self.async_write_ha_state()

            os.remove(tmp_zip.name)
            shutil.rmtree(tmp_dir)

            # Finalize
            self._update_percentage = 100
            self._update_status = "success"
            self._last_update_success = datetime.datetime.now().isoformat()
            self.async_write_ha_state()

            self._installed_version = version or self._latest_version

            # Persist installed version
            self.hass.config_entries.async_update_entry(
                self.entry,
                data={
                    **self.entry.data,
                    "current_version": self._installed_version,
                },
            )

            await self.hass.services.async_call(
                "persistent_notification",
                "create",
                {
                    "title": "Neviweb130 – Update successful",
                    "message": f"Update to version {self._installed_version} was installed successfully.",
                    "notification_id": "neviweb130_update_status",
                },
            )

            await self.hass.services.async_call(
                DOMAIN,
                "reload",
                {},
                blocking=True,
            )

        except Exception as err:
            _LOGGER.error("Update failed: %s", err)
            self._update_status = "failed"
            self._rollback_status = "attempting"
            self.async_write_ha_state()

            await self.hass.services.async_call(
                "persistent_notification",
                "create",
                {
                    "title": "Neviweb130 – Update failed",
                    "message": (
                        f"Update to version {version or self._latest_version} failed.\n"
                        "A rollback was performed and the old version was restored.\n"
                        f"[See update notes]({self.release_url})"
                    ),
                    "notification_id": "neviweb130_update_status",
                },
            )

            try:
                if self._local_backup_dir:
                    if os.path.exists(self._target_dir):
                        shutil.rmtree(self._target_dir)
                    shutil.copytree(self._local_backup_dir, self._target_dir, dirs_exist_ok=True)
                    _LOGGER.warning("Rollback completed successfully")
                    self._rollback_status = "success"
                else:
                    _LOGGER.error("Rollback skipped: no local backup available")
                    self._rollback_status = "skipped"
            except Exception as rb_err:
                _LOGGER.error("Rollback failed: %s", rb_err)
                self._rollback_status = "failed"

        finally:
            self._in_progress = False
            self._update_percentage = None
            self.async_write_ha_state()

            try:
                if self._local_backup_dir and os.path.exists(self._local_backup_dir):
                    shutil.rmtree(self._local_backup_dir)
                    _LOGGER.debug("Local backup directory removed: %s", self._local_backup_dir)
            except Exception:
                _LOGGER.warning("Failed to remove local backup directory: %s", cleanup_err)
