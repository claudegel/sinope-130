"""Helpers for debugging and logger setup in neviweb130"""

from __future__ import annotations

import asyncio
import datetime
import logging
import os
import re
import shutil
import time
from dataclasses import dataclass
from typing import Any, Callable

from homeassistant.components.persistent_notification import DOMAIN as PN_DOMAIN
from homeassistant.components.recorder.models import StatisticMeanType
from homeassistant.components.sensor import SensorDeviceClass, SensorEntityDescription, SensorStateClass
from homeassistant.const import UnitOfTime
from homeassistant.helpers.storage import Store
from homeassistant.util import dt as dt_util
from logging.handlers import RotatingFileHandler
from .const import SIGNAL_EVENTS_CHANGED, VERSION

_LOGGER = logging.getLogger(__name__)

REQUEST_STORE_VERSION = 1
REQUEST_STORE_KEY = "neviweb130_daily_requests"

NETWORK_MAP = {
    1: "network",
    2: "network2",
    3: "network3",
}

# ─────────────────────────────────────────────
# SECTION LOGGER SETUP
# ─────────────────────────────────────────────


def setup_logger(
    name: str,
    log_path: str,
    level: str = "INFO",
    max_bytes: int = 2 * 1024 * 1024,
    backup_count: int = 2,
    reset_on_start: bool = True
):
    if reset_on_start and os.path.exists(log_path):
        clear_log_file(log_path)

    logger = logging.getLogger(name)
    numeric_level = getattr(logging, level.upper(), logging.WARNING)
    logger.setLevel(numeric_level)

    handler = RotatingFileHandler(
        log_path,
        maxBytes=max_bytes,
        backupCount=backup_count,
        encoding="utf-8"
    )
    handler.setLevel(numeric_level)
    formatter = logging.Formatter(
        "%(asctime)s.%(msecs)03d %(levelname)s [%(name)s] %(message)s",
        datefmt="%Y-%m-%d %H:%M:%S"
    )
    handler.setFormatter(formatter)

    # Delete hold handlers on same file
    logger.handlers = [
        h for h in logger.handlers
        if not (isinstance(h, RotatingFileHandler) and h.baseFilename == log_path)
    ]
    logger.addHandler(handler)
    logger.propagate = False

    logger.debug("Logger initialized early at level %s", level.upper())


def clear_log_file(log_path: str):
    if os.path.exists(log_path):
        try:
            with open(log_path, "w", encoding="utf-8") as f:
                f.write("")
        except Exception as e:
            print(f"Failed to clear log file: {e}")


def extract_log_options(entry):
    options = entry.options
    return {
        "log_level": options.get("log_level", "warning"),
        "log_max_bytes": options.get("log_max_bytes", 2 * 1024 * 1024),
        "log_backup_count": options.get("log_backup_count", 2),
        "log_reset_on_start": options.get("log_reset_on_start", True),
    }


def update_logger_level(name: str, level: str):
    logger = logging.getLogger(name)
    numeric_level = getattr(logging, level.upper(), logging.WARNING)
    logger.setLevel(numeric_level)
    for h in logger.handlers:
        h.setLevel(numeric_level)
    logger.debug("Logger level updated to %s", level.upper())


def update_logger_config(name: str, log_path: str, level: str, max_bytes: int, backup_count: int):
    logger = logging.getLogger(name)
    numeric_level = getattr(logging, level.upper(), logging.WARNING)
    logger.setLevel(numeric_level)

    updated = False
    for h in logger.handlers:
        if isinstance(h, RotatingFileHandler) and os.path.samefile(h.baseFilename, log_path):
            h.setLevel(numeric_level)
            h.maxBytes = max_bytes
            h.backupCount = backup_count
            logger.debug("Logger handler updated : max_bytes=%s, backup_count=%s", max_bytes, backup_count)
            updated = True

    if not updated:
        logger.warning("No handler updated — check log path or level")

    logger.debug("Logger config updated to level %s", level.upper())


def expose_log_file(hass, log_path: str, public_name: str = "neviweb130.log", expire_after: int = 1800) -> str | None:
    """Copy log file to /config/www for browser download with forced filename."""
    www_dir = hass.config.path("www")
    os.makedirs(www_dir, exist_ok=True)

    www_path = os.path.join(www_dir, public_name)

    try:
        shutil.copy2(log_path, www_path)
        _LOGGER.debug("Log file copied to %s", www_path)

        # Schedule deletion
        hass.loop.create_task(_delete_file_later(www_path, expire_after))
        return www_path
    except Exception as e:
        _LOGGER.warning("Cannot expose log file: %s", e)
        return None


async def _delete_file_later(path: str, delay: int):
    """Wait for delay seconds then delete the file if it exists."""
    await asyncio.sleep(delay)
    try:
        if os.path.exists(path):
            os.remove(path)
            _LOGGER.info("Log file deleted after %s seconds : %s", delay, path)
    except Exception as e:
        _LOGGER.warning("Error during log file delete process : %s", e)

# ─────────────────────────────────────────────
# Clean entry section
# ─────────────────────────────────────────────


def sanitize_entry_data(data: dict, hidden_keys: tuple = ("username", "password")) -> dict:
    def mask(value):
        if isinstance(value, str) and "@" in value:
            name, domain = value.split("@", 1)
            return name[:2] + "***@" + domain
        return "***"

    return {
        k: (mask(v) if k in hidden_keys else v)
        for k, v in data.items()
    }

# ─────────────────────────────────────────────
# Debug coordinator section
# ─────────────────────────────────────────────

_LOGGER = logging.getLogger(__name__)


def debug_coordinator(coordinator, device_id=None, device_name=None):
    import pprint

    _LOGGER.debug("Coordinator class: %s", type(coordinator))
    _LOGGER.debug("Available attributes: %s", dir(coordinator._devices))
    _LOGGER.debug("Available clients: %s", dir(coordinator.client))
    _LOGGER.debug("Available data: %s", dir(coordinator.data.values))
    for attr in ["data", "_devices", "update_interval"]:
        value = getattr(coordinator, attr, "<inconnu>")
        try:
            _LOGGER.debug("%s: %s", attr, value)
        except Exception as e:
            _LOGGER.warning("Can't show %s: %s", attr, e)

    _LOGGER.debug("Coordinator data (data):")
    for dev_id, dev_obj in coordinator.data.items():
        _LOGGER.debug("[%s] %s", dev_id, getattr(dev_obj, "name", "??"))

    # Targetted inspection
    target_device = None
    _LOGGER.debug("device_id  = %s", device_id)
    _LOGGER.debug("device_name  = %s", device_name)
    if device_id and device_id in coordinator.data:
        target_device = coordinator.data[device_id]
    elif device_name:
        for dev in coordinator.data.values():
            if getattr(dev, "name", None) == device_name:
                target_device = dev
                break

    if target_device:
        _LOGGER.debug(
            "Targetted device (%s):\n%s",
            getattr(target_device, "name", "inconnu"),
            pprint.pformat(vars(target_device)),
        )
    else:
        _LOGGER.warning(
            "Device not found with ID '%s' or name '%s'",
            device_id,
            device_name,
        )

# ─────────────────────────────────────────────
# Update section
# ─────────────────────────────────────────────


def has_breaking_changes(notes: str | None) -> bool:
    """Detect breaking changes in release notes."""
    if not notes:
        return False

    text = notes.lower()

    keywords = [
        "breaking change",
        "breaking changes",
        "## breaking",
        "### breaking",
        "⚠️ breaking",
        ":warning:",
        "not backward compatible",
        "requires manual changes",
        "requires configuration update",
        "requires reconfiguration",
        "this update requires",
        "this change requires",
    ]

    return any(k in text for k in keywords)


def extract_notes_for_version(changelog: str, version: str) -> str:
    """Return version notes from CHANGELOG.md on github."""
    lines = changelog.splitlines()
    capture = False
    notes = []
    pattern = rf"\[{re.escape(version)}\]"
    for line in lines:
        stripped = line.strip()
        if re.search(pattern, stripped):
            capture = True
            continue
        if capture:
            if stripped.startswith("[v"):
                break
            if stripped:
                notes.append(stripped)
    return "\n".join(notes).strip() or f"Notes not found for {version}"


def build_update_summary(installed: str, latest: str, notes: str) -> str:
    """Build a full update summary for Neviweb130 V2."""
    base_url = "https://github.com/claudegel/sinope-130"

    release_link = f"{base_url}/releases/tag/v{latest}"
    compare_link = f"{base_url}/compare/v{installed}...v{latest}"

    return (
        f"### Update Summary\n\n"
        f"**Installed:** {installed}\n"
        f"**Available:** {latest}\n\n"
        f"[View Release Notes]({release_link})\n"
        f"[Compare Versions]({compare_link})\n\n"
        f"### Version Notes\n{notes}"
    )


# ─────────────────────────────────────────────
# Normalize yaml config import
# ─────────────────────────────────────────────


def normalize_yaml_config(yaml_config: dict) -> tuple[list[dict], dict, bool]:
    """
    Normalize YAML configuration for Neviweb130.

    Returns:
        accounts: list of normalized accounts
        global_options: dict of global options
    """

    is_legacy = False

    # --- Detection legacy vs V2 ---
    if "accounts" in yaml_config:
        raw_accounts = yaml_config["accounts"]
    else:
        # Compatibility legacy → convert to V2
        is_legacy = True
        raw_accounts = [{
            "username": yaml_config.get("username"),
            "password": yaml_config.get("password"),
            "network": yaml_config.get("network"),
            "network2": yaml_config.get("network2"),
            "network3": yaml_config.get("network3"),
            "location": yaml_config.get("location"),
            "location2": yaml_config.get("location2"),
            "location3": yaml_config.get("location3"),
            "prefix": "default",
        }]

    # --- Accounts normalization ---
    accounts = []
    seen_prefixes = set()
    seen_credentials = set()

    for idx, acc in enumerate(raw_accounts):

        username = acc.get("username")
        password = acc.get("password")

        # Validate username and password
        if not username or not password:
            raise HomeAssistantError(
                f"Neviweb130 YAML import error: username and password are required "
                f"for account index {idx} (prefix={acc.get('prefix','?')})."
            )

        # Automatic prefix
        prefix = acc.get("prefix")
        if not prefix:
            prefix = "default" if idx == 0 else f"default{idx+1}"

        # Validate prefix are different
        if prefix in seen_prefixes:
            raise HomeAssistantError(
                f"Neviweb130 YAML import error: duplicate prefix '{prefix}' detected."
            )
        seen_prefixes.add(prefix)

        # Validate credential are different
        cred_key = (username.lower().strip(), password)
        if cred_key in seen_credentials:
            raise HomeAssistantError(
                f"Neviweb130 YAML import error: duplicate account detected for username '{username}'."
            )
        seen_credentials.add(cred_key)

        # Synonymes network/location, empty if missing
        network = acc.get("network") or acc.get("location") or ""
        network2 = acc.get("network2") or acc.get("location2") or ""
        network3 = acc.get("network3") or acc.get("location3") or ""

        accounts.append({
            "username": username,
            "password": password,
            "prefix": prefix,
            "network": network,
            "network2": network2,
            "network3": network3,
        })

    # --- Global options ---
    scan = yaml_config.get("scan_interval", 420)
    stat = yaml_config.get("stat_interval", 1800)

    # --- Validation scan_interval ---
    if not (300 <= scan <= 600):
        raise HomeAssistantError(
            f"Neviweb130 YAML import error: scan_interval must be between 300 and 600 seconds (got {scan})."
        )

    # --- Validation stat_interval ---
    if not (1000 <= stat <= 2000):
        raise HomeAssistantError(
            f"Neviweb130 YAML import error: stat_interval must be between 1000 and 2000 seconds (got {stat})."
        )

    # --- Validation notify ---
    valid_notify_values = {"both", "logging", "nothing", "notification"}

    notify = yaml_config.get("notify", "both")  # default value

    if notify not in valid_notify_values:
        raise HomeAssistantError(
            f"Neviweb130 YAML import error: notify must be one of "
            f"{', '.join(valid_notify_values)} (got '{notify}')."
        )


    global_options = {
        "scan_interval": scan,
        "homekit_mode": yaml_config.get("homekit_mode", False),
        "ignore_miwi": yaml_config.get("ignore_miwi", False),
        "stat_interval": stat,
        "notify": notify,
    }

    return accounts, global_options, is_legacy


def build_import_summary(accounts: list[dict], global_options: dict, is_legacy: bool) -> str:
    """Build a human-readable summary of the YAML import."""

    lines = []

    if is_legacy:
        lines.append("YAML configuration detected with legacy format (only one Neviweb account).")
    else:
        lines.append(f"YAML configuration detected with new multi accounts ({len(accounts)} neviweb accounts).")

    lines.append("")

    for acc in accounts:
        lines.append(f"- Account « {acc['prefix']} » :")
        lines.append(f"    • User name : {acc['username']}")
        if acc.get("network"):
            lines.append(f"    • Network / Location 1 : {acc['network']}")
        if acc.get("network2"):
            lines.append(f"    • Network2 / Location 2 : {acc['network2']}")
        if acc.get("network3"):
            lines.append(f"    • Network3 / Location 3 : {acc['network3']}")
        lines.append("")

    lines.append("")
    lines.append("Global options applied :")
    for key, value in global_options.items():
        lines.append(f"    • {key}: {value}")

    return "\n".join(lines)


# ─────────────────────────────────────────────
# Notification to HA
# ─────────────────────────────────────────────


async def async_notify_ha(hass, msg: str, title: str = None, notification_id: str = None):
    """Send a persistent notification to the HA frontend."""

    if title is None:
        title = f"Neviweb130 integration {VERSION}"

    data = {
        "title": title,
        "message": msg,
    }
    if notification_id:
        data["notification_id"] = notification_id

    await hass.services.call(
        PN_DOMAIN,
        "create",
        data,
        blocking=False,
    )

async def async_notify_once_or_update(hass, msg: str, title: str = None, notification_id: str = None):
    """ Send a persistent notification only once, or update it if it already exists.

    - If the notification does not exist → create it
    - If it exists → update it with the new message/title
    """

    if notification_id is None:
        raise ValueError("async_notify_once_or_update requires a notification_id")

    entity_id = f"{PN_DOMAIN}.{notification_id}"
    existing = hass.states.get(entity_id)

    # If notification exist, update it
    if existing:
        await async_notify_ha(
            hass,
            msg,
            title=title,
            notification_id=notification_id,
        )
        return "updated"

    # Or → we create it
    await async_notify_ha(
        hass,
        msg,
        title=title,
        notification_id=notification_id,
    )
    return "created"


async def async_notify_throttled(
    hass,
    msg: str,
    *,
    title: str = None,
    notification_id: str,
    min_interval: int = 3600,
):
    """
    Send a persistent notification, but throttled.

    - If the notification was sent less than `min_interval` seconds ago → ignore
    - Otherwise → send it and update the timestamp

    Args:
        hass: Home Assistant instance
        msg: message to send
        title: optional title
        notification_id: unique ID for throttling
        min_interval: minimum seconds between notifications
    """

    if notification_id is None:
        raise ValueError("async_notify_throttled requires a notification_id")

    # Internal storage for throtteling
    throttles = hass.data.setdefault(NEVIWEB_DOMAIN, {}).setdefault("notify_throttle", {})

    now = time.time()
    last_time = throttles.get(notification_id, 0)

    # Too soon → just ignore
    if now - last_time < min_interval:
        return "throttled"

    # Or → we send and update timestamp
    throttles[notification_id] = now

    await async_notify_ha(
        hass,
        msg,
        title=title,
        notification_id=notification_id,
    )

    return "sent"


async def async_notify_critical(hass, msg: str, title: str, notification_id: str):
    """
    Always notify the user, regardless of notify settings.
    Critical notifications cannot be disabled.
    """
    # Always log error
    _LOGGER.error(msg)

    # Always send a persistent notification
    await async_notify_once_or_update(
        hass,
        msg,
        title=title,
        notification_id=notification_id,
    )


# ─────────────────────────────────────────────
# Devices default_name
# ─────────────────────────────────────────────


class NamingHelper:
    def __init__(self, domain: str, prefix: str):
        self.domain = domain
        self.prefix = prefix

    def default_name(self, platform: str, index: int) -> str:
        """
        Build default_name for each bridge, for given platform.

    - If prefix == "default":
        Keep legacy logic :
            DEFAULT_NAME = f"{DOMAIN} climate"
            DEFAULT_NAME_2 = f"{DOMAIN} climate 2"
            DEFAULT_NAME_3 = f"{DOMAIN} climate 3"
    - If prefix != "default":
        V2 logic applied :
            DEFAULT_NAME = f"{DOMAIN} {prefix} {network}"
            DEFAULT_NAME_2 = f"{DOMAIN} {prefix} {network2}"
            DEFAULT_NAME_3 = f"{DOMAIN} {prefix} {network3}"

    Args:
        domain (str): DOMAIN name.
        platform (str): climate, light, switch, etc.
        prefix (str): Prefix defined in config (default or other).
        index (int): 1, 2 or 3 ,bridge number.

    Returns:
        str: default_name built.
        """
        network = NETWORK_MAP[index]

        if self.prefix == "default":
            # Legacy logic applied
            suffix = "" if index == 1 else f" {index}"
            return f"{self.domain} {platform}{suffix}"

        # V2 logic
        return f"{self.domain} {self.prefix} {network}"

    def device_name(self, platform: str, index: int, device_info: dict) -> str:
        """
        Build complete device name.
        """
        base = self.default_name(platform, index)
        return f"{base} {device_info['name']}"

    def entity_name(self, platform: str, index: int, device_info: dict, attribute: str) -> str:
        """
        Construct entity name
        """
        base = self.device_name(platform, index, device_info)
        return f"{base} {attribute}"


# ─────────────────────────────────────────────
# Devive methode refresh
# ─────────────────────────────────────────────


class NeviwebEntityHelper:
    async def apply_and_refresh(self, update_coro, **local_updates):
        """
        Execute a client update coroutine, update local attributes,
        write HA state, and refresh the coordinator.
        """
        success = await update_coro

        if success:
            # Mise à jour locale
            for attr, value in local_updates.items():
                setattr(self, attr, value)

            # Mise à jour immédiate dans Home Assistant
            self.async_write_ha_state()

            # Rafraîchissement global via le coordinator
            await self.coordinator.async_request_refresh()

        return success


class DailyRequestCounter:
    def __init__(self, hass):
        self.hass = hass
        self.store: Store = Store(hass, REQUEST_STORE_VERSION, REQUEST_STORE_KEY)
        self.data: dict[str, int | str] = {
            "date": datetime.date.today().isoformat(),
            "count": 0,
        }

    async def async_load(self):
        stored = await self.store.async_load()
        if stored:
            self.data = stored
        else:
            await self.store.async_save(self.data)

    async def async_increment(self) -> int:
        today = datetime.date.today().isoformat()

        if self.data["date"] != today:
            self.data["date"] = today
            self.data["count"] = 0

        self.data["count"] += 1
        await self.store.async_save(self.data)
        return self.data["count"]

    def get_count(self) -> int:
        return self.data["count"]


# ─────────────────────────────────────────────
# Runtime attributes
# ─────────────────────────────────────────────


@dataclass(frozen=True)
class Neviweb130SensorEntityDescription(SensorEntityDescription):
    """Describes an attribute sensor entity."""

    value_fn: Callable[[Any], Any] | None = None
    signal: str = ""
    icon: str | None = None
    state_class: str | None = "measurement"
    device_class: SensorDeviceClass | None = None
    native_unit_of_measurement: str | None = None
    unit_class: str | None = None
    mean_type: StatisticMeanType | None = None


def init_runtime_attributes(obj, modes: dict[str, str], prefix: str) -> None:
    """Initialize runtime statistics attributes dynamically."""
    for mode in modes:
        setattr(obj, f"_{mode}_{prefix}_total_count", 0)
        setattr(obj, f"_{mode}_{prefix}_count", 0)
        setattr(obj, f"_{mode}_{prefix}_last_timestamp", None)
        setattr(obj, f"_{mode}_{prefix}_last_timestamp_local", None)


def runtime_attributes_dict(obj, modes: dict[str, str], prefix: str) -> dict[str, any]:
    """Return a dict of runtime attributes for extra_state_attributes."""
    data = {}
    for mode in modes:
        data[f"{mode}_{prefix}_total_count"] = getattr(obj, f"_{mode}_{prefix}_total_count")
        data[f"{mode}_{prefix}_count"] = getattr(obj, f"_{mode}_{prefix}_count")
        data[f"{mode}_{prefix}_last_timestamp"] = getattr(obj, f"_{mode}_{prefix}_last_timestamp")
        data[f"{mode}_{prefix}_last_timestamp_local"] = getattr(obj, f"_{mode}_{prefix}_last_timestamp_local")
    return data


def generate_runtime_count_attributes(modes: dict[str, str], prefix: str) -> list[str]:
    """Generate only the runtime count attributes for EXPOSED_ATTRIBUTES."""
    attrs = []
    for mode in modes:
        attrs.append(f"{mode}_{prefix}_total_count")
        attrs.append(f"{mode}_{prefix}_count")
    return attrs


def update_runtime_stats(obj, device_stats: dict, modes: dict[str, str], prefix: str) -> None:
    """Update runtime statistics for a thermostat based on hourly stats."""
    for mode, key in modes.items():
        data = device_stats.get(key, [])

        total_attr = f"_{mode}_{prefix}_total_count"
        time_attr = f"_{mode}_{prefix}_count"
        ts_attr = f"_{mode}_{prefix}_last_timestamp"
        local_ts_attr = f"_{mode}_{prefix}_last_timestamp_local"

        if data and len(data) >= 2:
            last_entry = data[-1]
            prev_entry = data[-2]

            last_value = last_entry["value"]
            prev_value = prev_entry["value"]

            # Convert timestamp UTC → local
            ts_utc = datetime.datetime.strptime(
                last_entry["timestamp"], "%Y-%m-%d %H:%M:%S"
            ).replace(tzinfo=datetime.timezone.utc)
            ts_local = dt_util.as_local(ts_utc)

            # Update only if timestamp changed
            if getattr(obj, ts_attr, None) != last_entry["timestamp"]:
                setattr(obj, total_attr, last_value)
                setattr(obj, time_attr, max(0, last_value - prev_value))
                setattr(obj, ts_attr, last_entry["timestamp"])
                setattr(obj, local_ts_attr, ts_local.isoformat())

        else:
            # Unsupported mode → reset values
            setattr(obj, total_attr, 0)
            setattr(obj, time_attr, 0)


def _runtime_icon_for_mode(mode: str) -> str:
    """Return an appropriate icon based on the runtime mode."""
    if "heat" in mode.lower():
        return "mdi:fire"
    if "cool" in mode.lower():
        return "mdi:snowflake"
    if "fan" in mode.lower():
        return "mdi:fan"
    if "aux" in mode.lower():
        return "mdi:heat-wave"
    if "emergency" in mode.lower():
        return "mdi:alert"
    return "mdi:counter"


def generate_runtime_sensor_descriptions(modes: dict[str, str], prefix: str):
    descriptions = []

    for mode in modes:
        icon = _runtime_icon_for_mode(mode)

        # total count
        key_total = f"{mode}_{prefix}_total_count"
        descriptions.append(
            Neviweb130SensorEntityDescription(
                key=key_total,
                device_class=SensorDeviceClass.DURATION,
                state_class=SensorStateClass.TOTAL_INCREASING,
                translation_key=key_total,
                value_fn=lambda data, k=key_total: data.get(k),
                signal=SIGNAL_EVENTS_CHANGED,
                native_unit_of_measurement=UnitOfTime.MINUTES,
                unit_class="duration",
                mean_type=StatisticMeanType.ARITHMETIC,
                icon=icon,
            )
        )

        # delta count
        key_delta = f"{mode}_{prefix}_count"
        descriptions.append(
            Neviweb130SensorEntityDescription(
                key=key_delta,
                device_class=SensorDeviceClass.DURATION,
                state_class=SensorStateClass.MEASUREMENT,
                translation_key=key_delta,
                value_fn=lambda data, k=key_delta: data.get(k),
                signal=SIGNAL_EVENTS_CHANGED,
                native_unit_of_measurement=UnitOfTime.MINUTES,
                unit_class="duration",
                mean_type=StatisticMeanType.ARITHMETIC,
                icon=icon,
            )
        )

    return descriptions


#await async_notify_throttled(
#    self.hass,
#    "Erreur de communication avec Neviweb. Nouvelle tentative en cours.",
#    title="Neviweb130",
#    notification_id=f"neviweb130_comm_error_{self._prefix}",
#    min_interval=1800,  # max 1 notification par 30 minutes
#)

#await async_notify_once_or_update(
#    self.hass,
#    "Erreur de communication avec Neviweb. Nouvelle tentative en cours.",
#    title=f"Neviweb130 integration {VERSION}",
#    notification_id=f"neviweb130_comm_error_{self._prefix}",
#)

#await async_notify_critical(
#    self.hass,
#    "Neviweb130: Impossible de se connecter depuis 10 minutes.",  # Message
#    "Neviweb130 - Erreur critique",  # Title
#    "neviweb130_connection_error"  # id
#)
