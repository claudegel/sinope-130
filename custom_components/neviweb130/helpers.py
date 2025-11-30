"""Helpers for debugging and logger setup in neviweb130"""

import asyncio
import logging
import os
import shutil

from logging.handlers import RotatingFileHandler

_LOGGER = logging.getLogger(__name__)

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
            logger.debug("Logger handler mis à jour : max_bytes=%s, backup_count=%s", max_bytes, backup_count)
            updated = True

    if not updated:
        logger.warning("Aucun handler mis à jour — vérifie le log_path ou l’attachement initial")

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
