"""Update entity for Neviweb130 integration."""

import datetime
import hashlib
import logging
import os
import re
import shutil
import tempfile
import zipfile
from datetime import timedelta
from typing import Any

import aiohttp
from awesomeversion import AwesomeVersion
from homeassistant.components.update import UpdateEntity, UpdateEntityFeature
from homeassistant.core import HomeAssistant
from homeassistant.helpers.entity_platform import AddEntitiesCallback
from homeassistant.helpers.event import async_track_time_interval

from .const import DOMAIN
from .helpers import build_update_summary, has_breaking_changes

_LOGGER = logging.getLogger(__name__)

VALID_ASSET_PATTERN = re.compile(r"^sinope-130-(v[\w\.\-]+)\.(zip|sha256)$")


def compute_sha256(file_path: str) -> str:
    """Compute SHA256 hash of a file."""
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


async def async_setup_platform(
    hass: HomeAssistant,
    config: dict[str, Any],
    async_add_entities: AddEntitiesCallback,
    discovery_info: dict[str, Any] | None = None,
) -> None:
    """Setup update platform."""
    _LOGGER.debug("async_setup_platform CALLED for update platform")

    data = hass.data[DOMAIN]["data"]

    if data is None:
        _LOGGER.error("Neviweb130 data not initialized — update entity not created")
        return

    entity = Neviweb130UpdateEntity(hass, data)
    hass.data[DOMAIN]["update_entity"] = entity
    async_add_entities([entity], True)

    now = datetime.datetime.now()
    entity._last_check = now.isoformat()
    entity._next_check = (now + timedelta(hours=6)).isoformat()
    entity._last_update_success = now.isoformat()
    entity._update_status = "idle"
    entity.async_write_ha_state()

    async def scheduled_check(now: datetime.datetime) -> None:
        await entity.async_check_for_updates()
        now = datetime.datetime.now()
        entity._last_check = now.isoformat()
        entity._next_check = (now + timedelta(hours=6)).isoformat()
        entity._last_update_success = now.isoformat()
        entity._update_status = "idle"
        entity.async_write_ha_state()

    _LOGGER.debug("Scheduler registered for Neviweb130 update")

    async_track_time_interval(
        hass,
        scheduled_check,
        timedelta(hours=6),
    )


class Neviweb130UpdateEntity(UpdateEntity):
    """Representation of a Neviweb130 update entity."""

    def __init__(self, hass: HomeAssistant, data) -> None:
        self.hass = hass
        self._attr_name = "Neviweb130 Update"
        self._attr_unique_id = "neviweb130_update"

        # From data
        self._installed_version: str = getattr(data, "current_version", "")
        self._latest_version: str = getattr(data, "available_version", "")
        self._release_notes: str = getattr(data, "release_notes", "")
        self._release_title: str = getattr(data, "release_title", "")

        # Prepare values for summary
        installed = self._installed_version or ""
        latest = self._latest_version or ""
        safe_notes = self._release_notes or ""

        # Build base summary
        summary = build_update_summary(installed, latest, safe_notes)

        # Prefix (breaking changes, pre-release)
        prefix = ""
        if has_breaking_changes(safe_notes):
            # 🛑
            prefix += "\U0001f6d1 BREAKING CHANGES\n"
        if latest and any(x in latest for x in ("b", "beta", "rc")):
            # 🚧
            prefix += "\U0001f6a7 PRE-RELEASE VERSION\n"

        self._release_summary: str = prefix + summary

        # Other internal attributes
        self._update_percentage: int | None = None
        self._in_progress: bool = False
        self._last_check: str | None = None
        self._next_check: str | None = None
        self._check_interval: str = "6h"
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
        self._attr_installed_version = installed
        self._attr_latest_version = latest

        _LOGGER.debug("Release summary received in update: %s", self._release_summary)

    @property
    def installed_version(self) -> str | None:
        return self._installed_version

    @property
    def latest_version(self) -> str | None:
        return self._latest_version

    @property
    def has_breaking_changes(self) -> bool:
        if self._release_notes is None:
            return False
        return bool(has_breaking_changes(self._release_notes))

    @property
    def release_summary(self) -> str | None:
        if self._attr_requires_restart and self._installed_version != self._latest_version:
            return self._release_summary
        return None

    async def async_release_notes(self) -> str | None:
        """Return release notes for the update dialog."""
        alert = (
            "\n\n<ha-alert alert-type='error'>You need to restart Home Assistant manually after updating.</ha-alert>"
        )
        return self._release_notes + alert

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

        # Add icon if pre-release
        if self._latest_version and any(x in self._latest_version for x in ("b", "beta", "rc")):
            base = f"\U0001f6a7 PRE-RELEASE – {base}"

        # Add icon if breaking changes
        if self.has_breaking_changes:
            base = f"\U0001f6d1 BREAKING – {base}"

        return base

    @property
    def update_percentage(self) -> int | None:
        """Return data for progress bar in update."""
        return self._update_percentage

    @property
    def in_progress(self) -> bool | None:
        """Return True if update in progress."""
        return self._in_progress

    @property
    def extra_state_attributes(self):
        attrs: dict[str, Any] = {}

        if self._last_check:
            attrs["last_check"] = self._last_check
        if self._next_check:
            attrs["next_check"] = self._next_check
        if self._check_interval:
            attrs["check_interval"] = self._check_interval
        if self._last_update_success:
            attrs["last_update_success"] = self._last_update_success
        if self._update_status:
            attrs["update_status"] = self._update_status
        if self._rollback_status:
            attrs["rollback_status"] = self._rollback_status
        attrs["update_available"] = self._installed_version != self._latest_version

        return attrs

    @property
    def requires_restart(self) -> bool:
        return self._attr_requires_restart

    async def async_check_for_updates(self) -> None:
        """Check GitHub for new releases and update entity state."""
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

            if latest == self._latest_version:
                _LOGGER.debug("No new Neviweb130 update found (latest=%s)", latest)
                return

            _LOGGER.info("New Neviweb130 version detected: %s", latest)

            # Update internal attributes
            self._latest_version = latest
            self._attr_latest_version = latest
            self._release_notes = notes
            self._release_title = title

            installed = self._installed_version or ""
            safe_notes = notes or ""

            summary = build_update_summary(installed, latest, safe_notes)

            prefix = ""
            if self.has_breaking_changes:
                prefix += "\U0001f6d1 BREAKING CHANGES\n"
            if any(x in latest for x in ("b", "beta", "rc")):
                prefix += "\U0001f6a7 PRE-RELEASE VERSION\n"

            self._release_summary = prefix + summary

            self.async_write_ha_state()

        except Exception as err:
            _LOGGER.error("Failed to check for updates: %s", err)

    async def async_install(self, version: str | None, backup: bool, **kwargs: Any) -> None:
        """Install update and make backup if selected."""
        if backup:
            await self._do_backup()
        await self._do_update(version)

    async def _do_backup(self) -> None:
        """Backup before update."""
        snapshot_name = f"Neviweb130-{self.installed_version}-{datetime.datetime.now().strftime('%Y%m%d-%H%M%S')}"

        try:
            await self.hass.services.async_call(
                "hassio",
                "backup_partial",
                {
                    "name": snapshot_name,
                    "folders": ["config"],
                },
                blocking=True,
            )
            _LOGGER.info("Partial backup '%s' triggered successfully", snapshot_name)

        except Exception as err:
            _LOGGER.error("Backup failed: %s", err)

    async def _do_update(self, version: str | None) -> None:
        """Do update."""
        self._rollback_status = "none"
        self._update_status = "updating"
        self._in_progress = True
        self._update_percentage = 0
        self.async_write_ha_state()

        # Validate version is compatible to update
        if version and self._installed_version:
            try:
                if AwesomeVersion(version) < AwesomeVersion(self._installed_version):
                    _LOGGER.error("Refusing downgrade: %s < %s", version, self._installed_version)
                    self._in_progress = False
                    self._update_percentage = None
                    self.async_write_ha_state()
                    return
            except Exception as err:
                _LOGGER.warning("Version comparison failed: %s", err)
                self._in_progress = False
                self._update_percentage = None
                self.async_write_ha_state()
                return

        # Determine tag
        if version:
            tag = f"v{version}" if not version.startswith("v") else version
        else:
            if not self._latest_version:
                _LOGGER.error("No version specified and no latest_version available")
                self._in_progress = False
                self._update_percentage = None
                self.async_write_ha_state()
                return
            tag = f"v{self._latest_version}" if not self._latest_version.startswith("v") else self._latest_version

        _LOGGER.debug("Installing tag: %s", tag)

        api_url = f"https://api.github.com/repos/claudegel/sinope-130/releases/tags/{tag}"

        backup_dir: str | None = None

        try:
            # Fetch release info
            async with aiohttp.ClientSession() as session:
                async with session.get(api_url) as resp:
                    resp.raise_for_status()
                    release_data = await resp.json()

            # Select correct ZIP
            assets = release_data.get("assets", [])
            # Expected version
            expected_version = release_data["tag_name"]
            valid_assets = filter_valid_assets(assets, expected_version)

            asset_zip = next(
                (a for a in valid_assets if a.get("name", "").endswith(".zip")),
                None,
            )

            # Select SHA256 file
            asset_sha = next(
                (a for a in valid_assets if a.get("name", "").endswith(".sha256")),
                None,
            )

            if not asset_zip or not asset_sha:
                raise Exception("ZIP or SHA256 asset not found in GitHub release")

            # Download SHA256
            async with aiohttp.ClientSession() as session:
                async with session.get(asset_sha["browser_download_url"]) as resp:
                    resp.raise_for_status()
                    expected_sha256 = (await resp.text()).strip()

            # 1- Download ZIP file
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

            # Compute local SHA256
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
                return

            # 3- Extract ZIP
            self._update_percentage = 50
            self.async_write_ha_state()

            tmp_dir = tempfile.mkdtemp()
            with zipfile.ZipFile(tmp_zip.name, "r") as zip_ref:
                zip_ref.extractall(tmp_dir)

            _LOGGER.debug("tmp_dir content: %s", os.listdir(tmp_dir))
            _LOGGER.debug("root content: %s", os.listdir(os.path.join(tmp_dir, os.listdir(tmp_dir)[0])))

            # 4- Copy files to custom_components/neviweb130/
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
            root = tmp_dir

            while True:
                entries = os.listdir(root)

                # Si un seul dossier et pas de fichiers → descendre
                if len(entries) == 1:
                    candidate = os.path.join(root, entries[0])
                    if os.path.isdir(candidate):
                        root = candidate
                        continue

                break

            extracted_root = root
            _LOGGER.debug("Root = %s", extracted_root)

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

            # 6- Finalize
            self._update_status = "success"
            self._last_update_success = datetime.datetime.now().isoformat()
            self._update_percentage = 100
            self.async_write_ha_state()

            # Update installed version
            self._installed_version = version or self._latest_version
            self._attr_installed_version = self._installed_version
            self.hass.data[DOMAIN]["data"].current_version = self._installed_version

            if version:
                self._latest_version = version
                self._attr_latest_version = version

            await self.hass.services.async_call(
                "persistent_notification",
                "create",
                {
                    "title": "Neviweb130 – Update successful",
                    "message": (
                        f"Update to version {version or self._latest_version} was installed successfully.\n"
                        f"[See update notes]({self.release_url})"
                    ),
                    "notification_id": "neviweb130_update_status",
                },
            )

            _LOGGER.info("Neviweb130 updated to version %s", version or self._latest_version)

        except Exception as err:
            _LOGGER.error("Update fail: %s", err)
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
            except Exception as cleanup_err:
                _LOGGER.warning("Failed to remove local backup directory: %s", cleanup_err)
