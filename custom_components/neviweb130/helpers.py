"""Helpers for debugging and logger setup in neviweb130"""

import asyncio
import datetime
import json
import logging
import os
import shutil
from logging.handlers import RotatingFileHandler

import aiohttp
from homeassistant.core import HomeAssistant
from homeassistant.helpers.storage import Store
from homeassistant.helpers.translation import async_get_translations

from .const import DOMAIN

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
    if os.path.exists(log_path):
        try:
            with open(log_path, "w", encoding="utf-8") as f:
                f.write("")
        except Exception as e:
            print(f"Failed to clear log file: {e}")


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

    async with aiohttp.ClientSession() as session:
        async with session.get(url) as resp:
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
            "date": datetime.date.today().isoformat(),
            "count": 0,
        }
        future = asyncio.run_coroutine_threadsafe(store.async_save(data), hass.loop)
        future.result()

    hass.data[DOMAIN]["request_store"] = store
    hass.data[DOMAIN]["request_data"] = data


def increment_request_counter(hass):
    """Increase counter by one."""
    data = hass.data[DOMAIN]["request_data"]
    today = datetime.date.today().isoformat()

    # Reset if day change
    if data["date"] != today:
        data["date"] = today
        data["count"] = 0

    data["count"] += 1

    # Persistent saving
    future = asyncio.run_coroutine_threadsafe(hass.data[DOMAIN]["request_store"].async_save(data), hass.loop)
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
    try:
        local_path = path.replace("/local/", "www/")
        full_path = os.path.join(hass.config.path(), local_path)
        return os.path.isfile(full_path)
    except Exception:
        return False


# ─────────────────────────────────────────────
# Translate error messages
# ─────────────────────────────────────────────


def translate_error(hass, key: str, **placeholders):
    """Translate an error message using HA translation system (sync wrapper)."""

    async def _async_translate():
        translations = await async_get_translations(
            hass,
            hass.config.language,
            "neviweb130",
        )

        full_key = f"component.neviweb130.error.{key.lower()}"
        msg = translations.get(full_key)

        if msg:
            return msg.format(**placeholders)

        return key

    # Run async translation safely from sync context
    return asyncio.run_coroutine_threadsafe(_async_translate(), hass.loop).result()
