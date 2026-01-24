"""Config flow for neviweb130 integration"""

from __future__ import annotations

# import json
import logging
import os
from typing import Any, cast

import aiofiles
import aiohttp
import voluptuous as vol
from homeassistant import config_entries, exceptions
from homeassistant.config_entries import ConfigFlow, ConfigFlowResult
from homeassistant.const import CONF_PASSWORD, CONF_SCAN_INTERVAL, CONF_USERNAME
from homeassistant.core import Event, HomeAssistant, callback
from homeassistant.data_entry_flow import FlowResult
from homeassistant.helpers import selector
from homeassistant.helpers import config_validation as cv
from homeassistant.helpers.translation import async_get_translations

from . import LOG_PATH, async_migrate_unique_ids, async_shutdown
from .const import (
    CONF_HOMEKIT_MODE,
    CONF_IGNORE_MIWI,
    CONF_NETWORK,
    CONF_NETWORK2,
    CONF_NETWORK3,
    CONF_NOTIFY,
    CONF_PREFIX,
    CONF_REQUEST_LIMIT,
    CONF_STAT_INTERVAL,
    CONF_UPDATE_INTERVAL,
    DEFAULT_REQUEST_LIMIT,
    DEFAULT_UPDATE_INTERVAL,
    DOMAIN,
    STARTUP_MESSAGE,
)
from .coordinator import PyNeviweb130Error
from .helpers import async_notify_critical, async_notify_once_or_update, async_notify_throttled, expose_log_file, normalize_yaml_config
from .schema import HOMEKIT_MODE, IGNORE_MIWI, NOTIFY, PREFIX, SCAN_INTERVAL, STAT_INTERVAL

_LOGGER = logging.getLogger(__name__)

HOST = "https://neviweb.com"
LOGIN_URL = f"{HOST}/api/login"

FLOW_SCHEMA = vol.Schema(
    {
        vol.Optional(CONF_PREFIX, default=PREFIX): cv.string,
        vol.Required(CONF_USERNAME): cv.string,
        vol.Required(CONF_PASSWORD): cv.string,
        vol.Optional(CONF_NETWORK, default=""): cv.string,
        vol.Optional(CONF_NETWORK2, default=""): cv.string,
        vol.Optional(CONF_NETWORK3, default=""): cv.string,
        vol.Optional(CONF_SCAN_INTERVAL, default=SCAN_INTERVAL): vol.All(vol.Coerce(int), vol.Range(min=300, max=600)),
        vol.Optional(CONF_HOMEKIT_MODE, default=HOMEKIT_MODE): cv.boolean,
        vol.Optional(CONF_IGNORE_MIWI, default=IGNORE_MIWI): cv.boolean,
        vol.Optional(CONF_STAT_INTERVAL, default=STAT_INTERVAL): vol.All(vol.Coerce(int), vol.Range(min=300, max=1800)),
        vol.Optional(CONF_NOTIFY, default=NOTIFY): vol.In(["nothing", "logging", "notification", "both"]),
    }
)


async def async_validate_email(user: str | None) -> None:
    """Validate the username as email."""
    if user is None:
        raise InvalidUserEmail("Empty user.")

    try:
        vol.Email()(user)
    except vol.Invalid as exc:
        raise InvalidUserEmail(f"Invalid email format: {user}") from exc


async def async_test_connect(user: str | None, passwd: str | None) -> None:
    """Validate Neviweb connection with supplied parameters."""
    data = {
        "username": user,
        "password": passwd,
        "interface": "neviweb",
        "stayConnected": 0,
    }

    timeout = aiohttp.ClientTimeout(total=30)
    _LOGGER.debug("Using timeout: %s", timeout.total)

    async with aiohttp.ClientSession() as session:
        try:
            async with session.post(
                LOGIN_URL,
                json=data,
                cookies=None,
                allow_redirects=False,
                timeout=timeout,
           ) as response:
                _LOGGER.debug("Validate login status: %s", response.status)
                if response.status != 200:
                    raise CannotConnect("Cannot log in to Neviweb")
        except aiohttp.ClientError as e:
            raise PyNeviweb130Error("Cannot submit test login form... Check your network or firewall.") from e


async def async_validate_input(data: dict[str, Any]) -> dict[str, Any]:
    """Validate the user input configuration."""
    prefi = data.get(CONF_PREFIX)
    user: str | None = data.get(CONF_USERNAME)
    passwd: str | None = data.get(CONF_PASSWORD)
    net = data.get(CONF_NETWORK)
    net2 = data.get(CONF_NETWORK2)
    net3 = data.get(CONF_NETWORK3)
    homekit = data.get(CONF_HOMEKIT_MODE)
    ignore = data.get(CONF_IGNORE_MIWI)
    scan = data.get(CONF_SCAN_INTERVAL)
    stat = data.get(CONF_STAT_INTERVAL)
    notif = data.get(CONF_NOTIFY)

    await async_validate_email(user)

    try:
        await async_test_connect(user, passwd)
        _LOGGER.debug("Test of Neviweb connection successful...")
    except CannotConnect as exc:
        _LOGGER.debug("Error in Neviweb test connection, check email and password...")
        raise CannotConnect(str(exc)) from exc
    except PyNeviweb130Error as exc:
        _LOGGER.debug("Network error during Neviweb test connection")
        raise exc

    return {
        CONF_PREFIX: prefi,
        CONF_USERNAME: user,
        CONF_PASSWORD: passwd,
        CONF_NETWORK: net,
        CONF_NETWORK2: net2,
        CONF_NETWORK3: net3,
        CONF_HOMEKIT_MODE: homekit,
        CONF_IGNORE_MIWI: ignore,
        CONF_SCAN_INTERVAL: scan,
        CONF_STAT_INTERVAL: stat,
        CONF_NOTIFY: notif,
    }


class Neviweb130ConfigFlow(ConfigFlow, domain=DOMAIN):
    """Sinope Neviweb130 config flow."""

    VERSION = 1
    CONNECTION_CLASS = config_entries.CONN_CLASS_CLOUD_POLL

    hass: HomeAssistant

    data: dict[str, Any] | None

    def __init__(self) -> None:
        """Initialise Neviweb130 config flow."""
        _LOGGER.info(STARTUP_MESSAGE)

        self.username = None
        self.password = None
        self.network = None
        self.network2 = None
        self.network3 = None
        self.scan_interval = 480
        self.homekit_mode = False
        self.ignore_miwi = False
        self.stat_interval = 1800
        self.notify = "both"
        self.prefix = ""
        self._cookies = None
        self._timeout = 30

    async def async_step_user(self, user_input: dict[str, Any] | None = None) -> ConfigFlowResult:
        """Invoked when a user initiates a flow via the user interface."""
        # Only a single instance of the integration
        _LOGGER.debug("current_entry number = %s", len(self._async_current_entries()))
        if len(self._async_current_entries()) > 3:
            return cast(ConfigFlowResult, self.async_abort(reason="Max_three_instances_allowed"))

        errors: dict[str, Any] = {}

        if user_input is None:
            return cast(ConfigFlowResult, self.async_show_form(step_id="user", data_schema=FLOW_SCHEMA, errors=errors))

        if user_input is not None:
            info = None
            try:
                info = await async_validate_input(user_input)
            except InvalidUserEmail:
                errors["base"] = "Invalid_User_Email"
            except CannotConnect:
                errors["base"] = "Cannot_Connect"
            except (vol.MultipleInvalid, vol.ValueInvalid):
                errors["base"] = "bad_data_entry"
            except Exception:
                _LOGGER.exception("Unexpected exception")
                errors["base"] = "unknown"
            if info is not None and not errors:
                user_input[CONF_PREFIX] = info[CONF_PREFIX]
                user_input[CONF_USERNAME] = info[CONF_USERNAME]
                user_input[CONF_PASSWORD] = info[CONF_PASSWORD]
                user_input[CONF_NETWORK] = info[CONF_NETWORK]
                user_input[CONF_NETWORK2] = info[CONF_NETWORK2]
                user_input[CONF_NETWORK3] = info[CONF_NETWORK3]
                user_input[CONF_HOMEKIT_MODE] = info[CONF_HOMEKIT_MODE]
                user_input[CONF_IGNORE_MIWI] = info[CONF_IGNORE_MIWI]
                user_input[CONF_SCAN_INTERVAL] = info[CONF_SCAN_INTERVAL]
                user_input[CONF_STAT_INTERVAL] = info[CONF_STAT_INTERVAL]
                user_input[CONF_NOTIFY] = info[CONF_NOTIFY]

            self.data = user_input
            result = await self.async_set_unique_id(user_input[CONF_USERNAME].strip().lower())
            _LOGGER.debug("Configure entry unique_id: %s", result)
            self._abort_if_unique_id_configured(error="already_configured_for_this_user")
            return cast(ConfigFlowResult, self.async_create_entry(title="Sinope Neviweb130", data=self.data))

        return cast(ConfigFlowResult, self.async_show_form(step_id="user", data_schema=FLOW_SCHEMA, errors=errors))


    async def async_step_import(self, user_input=None):
        """Import neviweb130 config from configuration.yaml."""

        yaml_config = user_input or {}

        try:
            accounts, global_options, is_legacy = normalize_yaml_config(yaml_config)
        except HomeAssistantError as exc:
            await async_notify_critical(
                self.hass,
                str(exc),
                "Neviweb130 - Import YAML invalide",
                "neviweb130_yaml_error"
            )
            # Stop the flow
            return self.async_abort(reason="yaml_invalid")

        summary = build_import_summary(accounts, global_options, is_legacy)
        _LOGGER.warning("Neviweb130 YAML import summary:\n\n%s", summary)

        await async_notify_throttled(
            self.hass,
            summary,
            title="Neviweb130 configuration imported in config_flow.",
            notification_id="neviweb130_import",
            min_interval=86400,
        )

        # Create one entry per account
        for acc in accounts:

            # Check if an entry already exist for that prefix
            existing = [
                entry for entry in self._async_current_entries()
                if entry.data.get("prefix") == acc["prefix"]
            ]
            if existing:
                continue

            data = {
                **acc,
                **global_options,
            }

            await self.async_create_entry(
                title=f"Neviweb130 ({acc['prefix']})",
                data=data,
            )

        return self.async_abort(reason="imported")


    async def async_step_reconfigure(self, user_input: dict[str, Any] | None = None) -> FlowResult[Any]:
        """Add reconfigure step to allow to reconfigure a config entry."""

        # get entry
        reconfigure_entry = self._get_reconfigure_entry()
        errors: dict[str, str] = {}

        # If user submitted the form
        if user_input is not None:
            try:
                # validate new config entry
                info = await async_validate_input(user_input)
                # Merge validated values
                user_input.update(info)
                # Close active session
                domain_data = self.hass.data.get(DOMAIN, {})
                entry_data = domain_data.get(reconfigure_entry.entry_id, {})
                session_manager = entry_data.get("session")

                if session_manager:
                    _LOGGER.debug("Closing active Neviweb session before restart")
                    try:
                        await session_manager.close_session()
                    except Exception:
                        _LOGGER.exception("Error while closing Neviweb session")

                await async_shutdown(self.hass)

            except InvalidUserEmail:
                errors["base"] = "Invalid_User_Email"
            except CannotConnect:
                errors["base"] = "Cannot_Connect"
            except (vol.MultipleInvalid, vol.ValueInvalid):
                errors["base"] = "bad_data_entry"
            except Exception:
                _LOGGER.exception("Unexpected exception")
                errors["base"] = "unknown"

            if not errors:
                await self.async_set_unique_id(reconfigure_entry.unique_id)
                self._abort_if_unique_id_mismatch()

                return self.async_update_reload_and_abort(
                    self._get_reconfigure_entry(),
                    data_updates=user_input,
                )

        merged_data = {**reconfigure_entry.data, **reconfigure_entry.options}
        prefix_value = merged_data.get(CONF_PREFIX, "")

        RECONFIGURE_FLOW_SCHEMA = vol.Schema(
            {
                vol.Required(CONF_PREFIX, default=prefix_value): cv.string,
                vol.Required(CONF_USERNAME, default=reconfigure_entry.data[CONF_USERNAME]): cv.string,
                vol.Required(CONF_PASSWORD, default=reconfigure_entry.data[CONF_PASSWORD]): cv.string,
                vol.Optional(CONF_NETWORK, default=reconfigure_entry.data.get(CONF_NETWORK, "")): cv.string,
                vol.Optional(CONF_NETWORK2, default=reconfigure_entry.data.get(CONF_NETWORK2, "")): cv.string,
                vol.Optional(CONF_NETWORK3, default=reconfigure_entry.data.get(CONF_NETWORK3, "")): cv.string,
                vol.Optional(CONF_SCAN_INTERVAL, default=reconfigure_entry.data[CONF_SCAN_INTERVAL]): vol.All(
                    vol.Coerce(int), vol.Range(min=300, max=600)
                ),
                vol.Optional(
                    CONF_HOMEKIT_MODE,
                    default=reconfigure_entry.data.get(CONF_HOMEKIT_MODE, False),
                ): cv.boolean,
                vol.Optional(
                    CONF_IGNORE_MIWI,
                    default=reconfigure_entry.data.get(CONF_IGNORE_MIWI, False),
                ): cv.boolean,
                vol.Optional(
                    CONF_STAT_INTERVAL,
                    default=reconfigure_entry.data[CONF_STAT_INTERVAL],
                ): vol.All(vol.Coerce(int), vol.Range(min=300, max=1800)),
                vol.Optional(CONF_NOTIFY, default=reconfigure_entry.data[CONF_NOTIFY]): vol.In(
                    ["nothing", "logging", "notification", "both"]
                ),
            }
        )

        return self.async_show_form(
            step_id="reconfigure",
            data_schema=RECONFIGURE_FLOW_SCHEMA,
            errors=errors,
            description_placeholders={"title": reconfigure_entry.title},
        )

    @staticmethod
    @callback
    def async_get_options_flow(config_entry):
        return Neviweb130OptionsFlowHandler(config_entry)


class Neviweb130OptionsFlowHandler(config_entries.OptionsFlow):
    """Handle options flow for Neviweb130."""

    def __init__(self, config_entry: config_entries.ConfigEntry) -> None:
        self._config_entry = config_entry

    async def async_step_init(self, user_input=None):
        """Entry point: go directly to options."""
        return await self.async_step_options()

    async def async_step_options(self, user_input=None):
        """Manage the options."""
        if user_input is not None:
            # Set log level based on the user input

            new_prefix = user_input.get(CONF_PREFIX)

            error = self._validate_prefix(new_prefix)
            if error:
                return self.async_show_form(
                    step_id="options",
                    data_schema=self._get_options_schema(),
                    errors={CONF_PREFIX: error},
                    description_placeholders={"help": "Click on button ? for help and documentation."},
                )

            # Process each option separately
            if user_input.get("log_level"):
                self._set_log_level(user_input["log_level"])

            if user_input.get("download_log"):
                self._trigger_download_log()

            if user_input.get("reload"):
                await self._trigger_reload()

            if user_input.get("migrate"):
                await self._trigger_migration()

            if "backup_folders" in user_input:
                folders = user_input["backup_folders"].strip()

                # Normalisation : string → liste
                if isinstance(folders, str):
                    folders = [folders]

                error = self._validate_backup_folders(folders)
                if error:
                    key, placeholders = error
                    return self.async_show_form(
                        step_id="options",
                        data_schema=self._get_options_schema(),
                        errors={"backup_folders": key},
                        description_placeholders={
                            **placeholders,
                            "help": "Enter a folder relative to /config"
                        },

                    )

            new_options = {
                **self._config_entry.options,
                **user_input,
            }

            return self.async_create_entry(title="", data=new_options)

        return self.async_show_form(
            step_id="options",
            data_schema=self._get_options_schema(),
            description_placeholders={"help": "Click on button ? for help and documentation."},
        )

    def _get_options_schema(self):
        options = self._config_entry.options
        log_levels = ["debug", "info", "warning", "error", "critical"]

        current_prefix = (
            self._config_entry.options.get(CONF_PREFIX)
            or self._config_entry.data.get(CONF_PREFIX)
            or PREFIX
        )

        return vol.Schema(
            {
                vol.Optional("prefix", default=current_prefix): str,
                vol.Optional("log_level", default=options.get("log_level", "info")): vol.In(log_levels),
                vol.Optional("log_max_bytes", default=options.get("log_max_bytes", 2 * 1024 * 1024)): int,
                vol.Optional("log_backup_count", default=options.get("log_backup_count", 2)): int,
                vol.Optional("log_reset_on_start", default=options.get("log_reset_on_start", True)): bool,
                vol.Optional("download_log", default=False): bool,
                vol.Optional("reload", default=False): bool,
                vol.Optional("migrate", default=False): bool,
                # New option: daily request limit
                vol.Optional(CONF_REQUEST_LIMIT, default=options.get(CONF_REQUEST_LIMIT, DEFAULT_REQUEST_LIMIT)): int,
                # New option for update
                vol.Optional(
                    CONF_UPDATE_INTERVAL,
                    default=options.get(CONF_UPDATE_INTERVAL, DEFAULT_UPDATE_INTERVAL)
                ): vol.In(["1h", "3h", "6h", "12h", "24h"]),
                # New options for backup
                vol.Optional("backup_mode", default=options.get("backup_mode", "full")): vol.In(["full", "partial"]),
                vol.Optional(
                    "backup_folders",
                    default="config"
                ): selector.TextSelector(
                    selector.TextSelectorConfig(
                        multiline=False
                    )
                )
            }
        )

    @staticmethod
    def _set_log_level(log_level):
        """Set the log level for the neviweb130 component."""
        level = getattr(logging, log_level.upper(), logging.INFO)

        # Apply to global logger global
        logger = logging.getLogger("custom_components.neviweb130")
        logger.setLevel(level)

        # Optionnal : confirmation log
        logger.warning("neviweb130 log level set to %s", log_level)

    def _validate_prefix(self, prefix: str) -> str | None:
        """Validate prefix format and uniqueness."""
        prefix = prefix.strip()

        # Minimal format
        if not prefix:
            return "empty_prefix"

        if " " in prefix:
            return "space_not_allowed"

        if not prefix.isascii():
            return "non_ascii_prefix"

        # Unicity : Check other entry
        for entry in self.hass.config_entries.async_entries("neviweb130"):
            if entry.entry_id != self._config_entry.entry_id:
                if entry.data.get("prefix") == prefix or entry.options.get("prefix") == prefix:
                    return "duplicate_prefix"

        return None

    def _trigger_download_log(self):
        """Copy neviweb130_log.txt to config/www to allow user to download it."""
        public_path = expose_log_file(self.hass, LOG_PATH, expire_after=1800)
        if public_path:
            # Create a persistent notification to tell how to download log file and expire after xx seconds
            self.hass.async_create_task(
                self.hass.services.async_call(
                    "persistent_notification",
                    "create",
                    {
                        "title": "Log file ready for download",
                        "message": (
                            "Download log file: "
                            + "<a href='/local/neviweb130.log'  download target='_blank'>click here</a>."
                            + "<br>File will be deleted after 30 minutes"
                        ),
                        "notification_id": "neviweb130_log_ready",
                    },
                )
            )

    async def _trigger_reload(self):
        """Method to handle reloading the integration."""
        await async_shutdown(self.hass)
        try:
            # Unload the existing entry if it's already set up
            if self._config_entry.state == config_entries.ConfigEntryState.LOADED:
                await self.hass.config_entries.async_unload(self._config_entry.entry_id)
                _LOGGER.info("Unloaded existing config entry")

            # Reload the entry
            await self.hass.config_entries.async_setup(self._config_entry.entry_id)
            _LOGGER.info("Integration has been reloaded")

            # Create a persistent notification
            self.hass.async_create_task(
                self.hass.services.async_call(
                    "persistent_notification",
                    "create",
                    {
                        "title": "Integration neviweb130 reloaded",
                        "message": "Integration neviweb130 have been reloaded",
                        "notification_id": "neviweb130_reloaded",
                    },
                )
            )
        except Exception as e:
            _LOGGER.error("Failed to reload integration: %s", e)
            await self.hass.services.async_call(
                "persistent_notification",
                "create",
                {
                    "title": "Reload Failed",
                    "message": f"Failed to reload integration: {e}",
                    "notification_id": "neviweb130_reload_error",
                },
            )

    async def _trigger_migration(self):
        """Method to handle the migration."""
        await async_migrate_unique_ids(self.hass)  # Call the migration function
        _LOGGER.info("Unique_id migration done")
        # Create a persistent notification
        self.hass.async_create_task(
            self.hass.services.async_call(
                "persistent_notification",
                "create",
                {
                    "title": "Unique_id migrated",
                    "message": "Neviweb130 device's unique_id have been migrated from integer values to string values. "
                    "More details in log.",
                    "notification_id": "neviweb130_migrated",
                },
            )
        )

    def _validate_backup_folders(self, folders: list[str]):
        """Validate that each folder exists and is accessible."""
        for folder in folders:
            folder = folder.strip()

            if folder == "config":
                continue

            if not folder:
                return "empty_folder", {}

            if any(c in folder for c in ['*', '?', '<', '>', '|']):
                return "invalid_characters", {}

            full_path = os.path.join(self.hass.config.path(), folder)

            if not os.path.exists(full_path):
                return "folder_not_found", {"folder": folder}

            if not os.path.isdir(full_path):
                return "not_a_directory", {"folder": folder}

            if not os.access(full_path, os.W_OK):
                return "not_writable", {"folder": folder}

        return None


class InvalidUserEmail(exceptions.HomeAssistantError):
    """Error to indicate invalid email specified."""


class CannotConnect(exceptions.HomeAssistantError):
    """Error to indicate we cannot connect to Neviweb."""


class OsError(exceptions.HomeAssistantError):
    """Error to indicate we cannot send requests to Neviweb."""
