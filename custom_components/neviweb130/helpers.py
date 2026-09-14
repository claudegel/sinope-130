"""Helpers for debugging and logger setup in neviweb130"""

import asyncio
import datetime
import logging
import os
import shutil
from logging.handlers import RotatingFileHandler
from requests.exceptions import RequestException

import aiohttp
from homeassistant.core import HomeAssistant
from homeassistant.helpers.storage import Store
from homeassistant.util import dt as dt_util

from .const import DOMAIN
from .exceptions import SilentAttributeIgnoreError

_LOGGER = logging.getLogger(__name__)

REQUEST_STORE_VERSION = 1
REQUEST_STORE_KEY = f"{DOMAIN}_request_count"

# ─────────────────────────────────────────────
# SECTION LOGGER SETUP
# ─────────────────────────────────────────────


def setup_logger(
    name: str,
    log_path: str,
    level: str = "INFO",
    max_bytes: int = 2 * 1024 * 1024,
    backup_count: int = 2,
    reset_on_start: bool = True,
):
    if reset_on_start and os.path.exists(log_path):
        clear_log_file(log_path)

    logger = logging.getLogger(name)
    numeric_level = getattr(logging, level.upper(), logging.WARNING)
    logger.setLevel(numeric_level)

    handler = RotatingFileHandler(log_path, maxBytes=max_bytes, backupCount=backup_count, encoding="utf-8")
    handler.setLevel(numeric_level)
    formatter = logging.Formatter(
        "%(asctime)s.%(msecs)03d %(levelname)s [%(name)s] %(message)s", datefmt="%Y-%m-%d %H:%M:%S"
    )
    handler.setFormatter(formatter)

    # Delete hold handlers on same file
    logger.handlers = [
        h for h in logger.handlers if not (isinstance(h, RotatingFileHandler) and h.baseFilename == log_path)
    ]
    logger.addHandler(handler)
    logger.propagate = False

    logger.debug("Logger initialized early at level %s", level.upper())


def clear_log_file(log_path: str):
    if not os.path.exists(log_path):
        return

    try:
        with open(log_path, "w", encoding="utf-8") as f:
            f.write("")
    except (OSError, PermissionError) as err:
        print(f"Failed to clear log file: {err}")


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
    except (OSError, PermissionError) as err:
        _LOGGER.warning("Cannot expose log file: %s", err)
        return None

    _LOGGER.debug("Log file copied to %s", www_path)
    hass.loop.create_task(_delete_file_later(www_path, expire_after))
    return www_path


async def _delete_file_later(path: str, delay: int):
    """Wait for delay seconds then delete the file if it exists."""
    await asyncio.sleep(delay)

    if not os.path.exists(path):
        return

    try:
        os.remove(path)
        _LOGGER.info("Log file deleted after %s seconds : %s", delay, path)
    except (OSError, PermissionError) as err:
        _LOGGER.warning("Error during log file delete process : %s", err)


# ─────────────────────────────────────────────
# Updater section
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


async def fetch_release_notes(version: str) -> tuple[str, str] | None:
    # We put back the "v" because GitHub still use vX.Y.Z
    tag = f"v{version}" if not version.startswith("v") else version
    url = f"https://api.github.com/repos/claudegel/sinope-130/releases/tags/{tag}"

    async with aiohttp.ClientSession() as session, session.get(url) as resp:
        if resp.status != 200:
            _LOGGER.warning("Failed to fetch release notes for %s: HTTP %s", tag, resp.status)
            return None

        data = await resp.json()
        title = (data.get("name") or "").strip()
        body = (data.get("body") or "").strip()
        _LOGGER.debug("Raw release notes for %s (len=%d): %r", tag, len(body), body)
        return title, body


def build_update_summary(installed: str, latest: str, notes: str) -> str:
    """Build a full update summary for Neviweb130 V1."""
    if not installed or not latest:
        return "You are running the latest available version."

    base_url = "https://github.com/claudegel/sinope-130"
    tag_installed = f"v{installed}" if not installed.startswith("v") else installed
    tag_latest = f"v{latest}" if not latest.startswith("v") else latest

    # Link to compare between new version and latest
    compare_link = f"{base_url}/compare/{tag_installed}...{tag_latest}"

    safe_notes = str(notes or "").strip()
    section = ""

    if "## What's Changed" in safe_notes:
        after = safe_notes.split("## What's Changed", 1)[1]
        if "##" in after:
            after = after.split("##", 1)[0]
        cleaned_lines = []
        for line in after.splitlines():
            if " in https" in line:
                line = line.split(" in https", 1)[0].rstrip()
                cleaned_lines.append(line)
        section = "## What's Changed\n" + "\n".join(cleaned_lines).strip()
    else:
        section = "No 'What's Changed' section found."
    _LOGGER.debug("Release notes = %s", section)

    if not safe_notes:
        safe_notes = f"## Version {latest}\n\nNo release notes available."

    return f"Available versions :\n- [{tag_installed} -> {tag_latest}]({compare_link})\n\n{section}"


# ─────────────────────────────────────────────
# SECTION DAILY REQUEST COUNTER
# ─────────────────────────────────────────────


def init_request_counter(hass):
    """Initialise the persistent store for request counter data."""
    store: Store = Store(hass, REQUEST_STORE_VERSION, REQUEST_STORE_KEY)

    # Load data
    future = asyncio.run_coroutine_threadsafe(store.async_load(), hass.loop)
    data = future.result()

    if not data:
        data = {
            "date": dt_util.now().date().isoformat(),
            "count": 0,
        }

        future = asyncio.run_coroutine_threadsafe(store.async_save(data), hass.loop)
        future.result()

    hass.data[DOMAIN]["request_store"] = store
    hass.data[DOMAIN]["request_data"] = data


def increment_request_counter(hass):
    """Increase counter by one."""
    data = hass.data[DOMAIN]["request_data"]
    today = dt_util.now().date().isoformat()

    # Reset if day change
    if data["date"] != today:
        data["date"] = today
        data["count"] = 0

    data["count"] += 1

    # Persistent saving
    future = asyncio.run_coroutine_threadsafe(
        hass.data[DOMAIN]["request_store"].async_save(data),
        hass.loop,
    )
    future.result()

    return data["count"]


def get_daily_request_count(hass):
    """Return the daily request count."""
    return hass.data[DOMAIN]["request_data"]["count"]


# ─────────────────────────────────────────────
# SECTION NOTIFICATION
# ─────────────────────────────────────────────


async def async_notify_ha(hass: HomeAssistant, msg: str, title: str = "Neviweb130 integration") -> None:
    await hass.services.async_call(
        "persistent_notification",
        "create",
        {
            "title": title,
            "message": msg,
        },
    )


def notify_ha(hass: HomeAssistant, msg: str, title: str = "Neviweb130 integration") -> None:
    asyncio.run_coroutine_threadsafe(
        async_notify_ha(hass, msg, title),
        hass.loop,
    )


# ─────────────────────────────────────────────
# Validate icone availability
# ─────────────────────────────────────────────


def file_exists(hass, path: str) -> bool:
    """Return True if a /local/ file exists."""
    local_path = path.replace("/local/", "www/")
    full_path = os.path.join(hass.config.path(), local_path)

    try:
        return os.path.isfile(full_path)
    except (OSError, PermissionError):
        return False


# ─────────────────────────────────────────────
# Translate error messages
# ─────────────────────────────────────────────


def translate_error(hass, key: str, **placeholders):
    """Translate an error message using cached translations (sync)."""

    if not hass.data[DOMAIN].get("ready"):
        return None

    cache = hass.data[DOMAIN].get("translation_cache")

    if cache is None:
        return None

    full_key = f"component.neviweb130.config.error.{key}"
    msg = cache.get(full_key)

    if msg:
        return msg.format(**placeholders)

    _LOGGER.warning(
        "Missing translation for key '%s' (%s) in neviweb130 (%s).",
        key,
        full_key,
        hass.config.language,
    )

    return f"[Missing translation: {key}]"


def translated_or_default(hass, key, default, **placeholders):
    """Return default message in case translation_cache is not loaded."""
    msg = translate_error(hass, key, **placeholders)
    return msg or default


# ─────────────────────────────────────────────
# Testing devices attributes one by one to spot invalid attributes
# ─────────────────────────────────────────────


UNSUPPORTED_ATTRS: dict[str, set[str]] = {}


def safe_get_device_attributes(
    hass,
    client,
    device_id,
    attributes,
    logger,
    device_sku=None,
    device_model=None,
    firmware=None,
):
    logger.warning("Running update helper")

    filtered_attrs = [attr for attr in attributes if attr not in UNSUPPORTED_ATTRS.get(device_id, set())]

    try:
        result = client.get_device_attributes(device_id, filtered_attrs)

        logger.debug("client result = %s", result)
        # If Neviweb silently ignore → result == {} or incomplete
        if not result or any(attr not in result for attr in filtered_attrs):
            raise SilentAttributeIgnoreError(
                f"Missing attributes: {filtered_attrs} for device {device_id}"
            )

        # Inject UNSUPPORTED_ATTRS with None into the result
        for attr in UNSUPPORTED_ATTRS.get(device_id, set()):
            result[attr] = None

        return result

    except (RequestException, OSError, SilentAttributeIgnoreError) as err:
        # if not a DVCATTRNSPTD → we restart
        if "DVCATTRNSPTD" not in str(err):
            raise

        # here we know it is an unsupported attribute
        model_info = f"Model: {device_model}" if device_model else "Model: unknown"
        fw_info = f"Firmware: {firmware}" if firmware else "Firmware: unknown"
        sku_info = f"SKU: {device_sku}" if device_sku else "SKU: unknown"

        logger.warning(
            "Unsupported or ignored attribute detected for device %s (%s, %s, %s). Testing attributes individually...",
            device_id,
            sku_info,
            model_info,
            fw_info,
        )

        notify_ha(
            hass,
            (
                f"Some attributes requested for device {device_id} are not supported.\n"
                f"{model_info}\n{fw_info}\n{sku_info}\n"
                "Check your logs to identify which attributes failed and report to maintainer."
            ),
            title="Neviweb130: Unsupported attributes detected",
        )

        device_data = {}

        # Test each attributes one by one
        for attr in attributes:
            logger.debug("Testing attribute %s for %s", attr, model_info)
            try:
                result = client.get_device_attributes(device_id, [attr])
                logger.debug("Result for '%s': %s", attr, result)

                # 1. If Neviweb return value
                if result and attr in result:
                    device_data[attr] = result[attr]
                    continue

                # 2. If Neviweb return {} → Attribute is supported but empty → just ignore
                if result == {}:
                    logger.warning(
                        "Attribute '%s' ignored or unsupported for device %s (%s, %s, %s)",
                        attr,
                        device_id,
                        sku_info,
                        model_info,
                        fw_info,
                    )
                    UNSUPPORTED_ATTRS.setdefault(device_id, set()).add(attr)
                    device_data[attr] = None
                    continue

                # 3. If Neviweb return None explicitly we add it to device_data
                if attr in result and result[attr] is None:
                    device_data[attr] = None
                    continue

                # 4. Improbable case : absent attr → log but add nothing
                logger.warning(
                    "Attribute '%s' ignored or unsupported for device %s (%s, %s, %s)",
                    attr,
                    device_id,
                    sku_info,
                    model_info,
                    fw_info,
                )
                continue

            except (RequestException, OSError, SilentAttributeIgnoreError) as err:
                # 5. if we get DVCATTRNSPTD → this attribute is not supported, add None
                if "DVCATTRNSPTD" in str(err):
                    logger.warning(
                        "Attribute '%s' not supported for device %s (%s, %s, %s): %s",
                        attr,
                        device_id,
                        sku_info,
                        model_info,
                        fw_info,
                        err,
                    )

                    if attr not in UNSUPPORTED_ATTRS.get(device_id, set()):
                        logger.warning("Blacklisting unsupported attribute '%s' for device %s", attr, device_id)

                    UNSUPPORTED_ATTRS.setdefault(device_id, set()).add(attr)
                    device_data[attr] = None
                    continue

                # Other network errors / I/O
                logger.error(
                    "Error while fetching attribute '%s' for device %s: %s",
                    attr,
                    device_id,
                    err,
                )
                continue

        # Reinject UNSUPPORTED_ATTRS with None into fallback result
        for attr in UNSUPPORTED_ATTRS.get(device_id, set()):
            if attr not in device_data:
                device_data[attr] = None

        logger.debug("Returned device_data = %s", device_data)
        return device_data


# ─────────────────────────────────────────────
# Add stat validation value received in case of None value
# ─────────────────────────────────────────────


def safe_number(value) -> float:
    """Return a safe numeric value even if Neviweb sends None or invalid data."""
    if value is None:
        return 0.0
    try:
        return float(value)
    except (TypeError, ValueError):
        return 0.0
