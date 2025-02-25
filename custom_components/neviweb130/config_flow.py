"""Config flow for neviweb130 integration"""

from __future__ import annotations

import aiofiles
import aiohttp
from datetime import timedelta
#import json
import logging
import os
import re
import voluptuous as vol

from typing import Any, Dict, Optional

from homeassistant import config_entries, core, exceptions
from homeassistant.config_entries import ConfigFlow
from homeassistant.const import (
    CONF_USERNAME,
    CONF_PASSWORD,
    CONF_SCAN_INTERVAL,
)
from homeassistant.core import callback
from homeassistant.data_entry_flow import FlowResult
from homeassistant.exceptions import HomeAssistantError
from homeassistant.helpers import selector, config_validation as cv

from .coordinator import (
    Neviweb130Client, 
    PyNeviweb130Error,
)
from . import (
    async_migrate_unique_ids,
    async_shutdown,
)
from .const import (
    DOMAIN,
    CONF_NETWORK,
    CONF_NETWORK2,
    CONF_NETWORK3,
    CONF_HOMEKIT_MODE,
    CONF_STAT_INTERVAL,
    CONF_NOTIFY,
)

from .schema import (
    CONFIG_SCHEMA,
    HOMEKIT_MODE,
    NOTIFY,
    PLATFORMS,
    SCAN_INTERVAL,
    STAT_INTERVAL,
    VERSION,
)

_LOGGER = logging.getLogger(__name__)
HOST = "https://neviweb.com"
LOGIN_URL = "{}/api/login".format(HOST)

FLOW_SCHEMA = vol.Schema({
        vol.Required(CONF_USERNAME): cv.string,
        vol.Required(CONF_PASSWORD): cv.string,
        vol.Optional(CONF_NETWORK, default="_"): cv.string,
        vol.Optional(CONF_NETWORK2, default="_"): cv.string,
        vol.Optional(CONF_NETWORK3, default="_"): cv.string,
        vol.Optional(CONF_SCAN_INTERVAL, default=SCAN_INTERVAL):
            vol.Coerce(int,
                selector.NumberSelector(
                    selector.NumberSelectorConfig(
                        min=300,
                        max=600,
                        unit_of_measurement="s",
                        mode=selector.NumberSelectorMode.BOX,
                    )
                ),
            ),
        vol.Optional(CONF_HOMEKIT_MODE, default=HOMEKIT_MODE):
            cv.boolean,
        vol.Optional(CONF_STAT_INTERVAL, default=STAT_INTERVAL):
            vol.All(vol.Coerce(int), vol.Range(min=300, max=1800)),
        vol.Optional(CONF_NOTIFY, default=NOTIFY):
            vol.In(["nothing","logging","notification","both"])
})

async def async_validate_email(user: str) -> bool: 
    """Validate the username as email."""
    try:
        vol.Email()(user)
        return True
    except vol.Invalid:
        errors["email"] = "invalid_email"
        return False

async def async_test_connect(self, user: str, passw: str) -> bool:
    """Validate Neviweb connection with suplied parameters."""
    _LOGGER.debug("Timeout %s", self._timeout) 
    data = {"username": user, "password": passw, "interface": "neviweb", "stayConnected": 0}
    session = await create_session()
    try:
        async with session.post(LOGIN_URL, json=data, cookies = None, allow_redirects=False, timeout = 30) as response:
            _LOGGER.debug("Validate login status: %s", response.status)
    except aiohttp.ClientError as e:
        raise PyNeviweb130Error("Cannot submit test login form... Check your network or firewall.") from e
        await session.close()
        return False
    if response.status != 200:
        _LOGGER.debug("Login status: %s", response.json())
        raise CannotConnect("Cannot log in to Neviweb")
        await session.close()
        return False
    await session.close()
    return True

#async def async_validate_input(data, hass: core.HomeAssistant, cookies, timeout) -> None:
async def async_validate_input(self, data: dict[str, Any]) -> Dict[str, Any]:
    """Validate the user input configuration."""
    user = data.get(CONF_USERNAME)
    passw = data.get(CONF_PASSWORD)
    net = data.get(CONF_NETWORK)
    net2 = data.get(CONF_NETWORK2)
    net3 = data.get(CONF_NETWORK3)
    homekit = data.get(CONF_HOMEKIT_MODE)
    scan = data.get(CONF_SCAN_INTERVAL)
    stat = data.get(CONF_STAT_INTERVAL)
    notif = data.get(CONF_NOTIFY)

    if not await async_validate_email(user):
        raise InvalidUserEmail(repr(exc)) from exc

    if not await async_test_connect(self, user, passw):
        _LOGGER.debug("Error in Neviweb test connection, check email and password...")
        raise CannotConnect(repr(exc)) from exc
        return False
    else:
        _LOGGER.debug("Test of Neviweb connection successful...")

    return {
        CONF_USERNAME: user,
        CONF_PASSWORD: passw,
        CONF_NETWORK: net,
        CONF_NETWORK2: net2,
        CONF_NETWORK3: net3,
        CONF_HOMEKIT_MODE: homekit,
        CONF_SCAN_INTERVAL: scan,
        CONF_STAT_INTERVAL: stat,
        CONF_NOTIFY: notif,
    }


class Neviweb130ConfigFlow(ConfigFlow, domain=DOMAIN):
    """Sinope Neviweb130 config flow."""

    VERSION = 1
    CONNECTION_CLASS = config_entries.CONN_CLASS_CLOUD_POLL
    
    hass: HomeAssistant

    data: Optional[Dict[str, Any]]

    def __init__(self) -> None:
        """Initialise Neviweb130 config flow."""
        self.username = None
        self.password = None
        self.network = None
        self.network2 = None
        self.network3 = None
        self.scan_interval = 480
        self.homekit_mode = False
        self.stat_interval = 1800
        self.notify = "both"
        self._cookies = None
        self._timeout = 30

    async def async_step_user(self, user_input: Optional[Dict[str, Any]] = None
    ) -> FlowResult:
        """Invoked when a user initiates a flow via the user interface."""
        # Only a single instance of the integration
        if self._async_current_entries():
            return self.async_abort(reason="single_instance_allowed")

        errors: Dict[str, any] = {}

        if user_input is None:
            return self.async_show_form(
                step_id="user", data_schema=FLOW_SCHEMA, errors=errors
            )

        if user_input is not None:
            try:
#                info = await async_validate_input(user_input, self.hass, self._cookies, self._timeout)
                info = await async_validate_input(self, user_input)
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
                user_input[CONF_USERNAME] = info[CONF_USERNAME]
                user_input[CONF_PASSWORD] = info[CONF_PASSWORD]
                user_input[CONF_NETWORK] = info[CONF_NETWORK]
                user_input[CONF_NETWORK2] = info[CONF_NETWORK2]
                user_input[CONF_NETWORK3] = info[CONF_NETWORK3]
                user_input[CONF_HOMEKIT_MODE] = info[CONF_HOMEKIT_MODE]
                user_input[CONF_SCAN_INTERVAL] = info[CONF_SCAN_INTERVAL]
                user_input[CONF_STAT_INTERVAL] = info[CONF_STAT_INTERVAL]
                user_input[CONF_NOTIFY] = info[CONF_NOTIFY]
 
            self.data = user_input
            
            return self.async_create_entry(title="Sinope Neviweb130", data=self.data)
 
        return self.async_show_form(
            step_id="user", data_schema=FLOW_SCHEMA, errors=errors
        )

    async def async_step_import(self, user_input=None):
        """Import neviweb130 config from configuration.yaml."""
        return await self.async_step_user(user_input)

    async def async_step_reconfigure(self, user_input: Optional[dict[str, Any]] = None
    ) -> FlowResult:
        """Add reconfigure step to allow to reconfigure a config entry."""
        errors: dict[str, str] = {}
        
        reconfigure_entry: config_entries.ConfigEntry[Any] = (
            self._get_reconfigure_entry()
        )
        # Ensure user_input is a dictionary
#        if user_input is None:
#            user_input = {}

        if user_input is not None:
            try:
                await async_shutdown(self.hass)
                info = await async_validate_input(self, user_input)
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
                user_input[CONF_USERNAME] = info[CONF_USERNAME]
                user_input[CONF_PASSWORD] = info[CONF_PASSWORD]
                user_input[CONF_NETWORK] = info[CONF_NETWORK]
                user_input[CONF_NETWORK2] = info[CONF_NETWORK2]
                user_input[CONF_NETWORK3] = info[CONF_NETWORK3]
                user_input[CONF_HOMEKIT_MODE] = info[CONF_HOMEKIT_MODE]
                user_input[CONF_SCAN_INTERVAL] = info[CONF_SCAN_INTERVAL]
                user_input[CONF_STAT_INTERVAL] = info[CONF_STAT_INTERVAL]
                user_input[CONF_NOTIFY] = info[CONF_NOTIFY]
            self.async_set_unique_id(CONF_USERNAME)
            self._abort_if_unique_id_mismatch()

            if user_input:
                return self.async_update_reload_and_abort(
                    self._get_reconfigure_entry(),
                    data_updates=user_input,
                )

        RECONFIGURE_FLOW_SCHEMA= vol.Schema({
            vol.Required(CONF_USERNAME, default=reconfigure_entry.data[CONF_USERNAME]): cv.string,
            vol.Required(CONF_PASSWORD, default=reconfigure_entry.data[CONF_PASSWORD]): cv.string,
            vol.Optional(CONF_NETWORK, default=reconfigure_entry.data[CONF_NETWORK]): cv.string,
            vol.Optional(CONF_NETWORK2, default=reconfigure_entry.data[CONF_NETWORK2]): cv.string,
            vol.Optional(CONF_NETWORK3, default=reconfigure_entry.data[CONF_NETWORK3]): cv.string,
            vol.Optional(CONF_SCAN_INTERVAL, default=reconfigure_entry.data[CONF_SCAN_INTERVAL]):
                vol.Coerce(int,
                    selector.NumberSelector(
                        selector.NumberSelectorConfig(
                            min=300,
                            max=600,
                            unit_of_measurement="s",
                            mode=selector.NumberSelectorMode.BOX,
                        )
                    ),
                ),
            vol.Optional(CONF_HOMEKIT_MODE, default=reconfigure_entry.data[CONF_HOMEKIT_MODE]):
                cv.boolean,
            vol.Optional(CONF_STAT_INTERVAL, default=reconfigure_entry.data[CONF_STAT_INTERVAL]):
                vol.All(vol.Coerce(int), vol.Range(min=300, max=1800)),
            vol.Optional(CONF_NOTIFY, default=reconfigure_entry.data[CONF_NOTIFY]):
                vol.In(["nothing","logging","notification","both"])
        })

        return self.async_show_form(
            step_id="reconfigure",
            data_schema=RECONFIGURE_FLOW_SCHEMA, errors=errors,
            description_placeholders={
                "title": reconfigure_entry.title,
            },
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
        """Manage the options."""
        if user_input is not None:
            # Set log level based on the user input
            if user_input.get("log_level"):
                self._set_log_level(user_input['log_level'])

            # Process each option separately
            if user_input.get("download_log"):
                await self._trigger_download_log()

            if user_input.get("reload"):
                await self._trigger_reload()

            if user_input.get("migrate"):
                await self._trigger_migration()

            return self.async_create_entry(title="", data=user_input)

        return self.async_show_form(
            step_id="init",
            data_schema=self._get_options_schema(),
            description_placeholders={
                "log_level_changed": "",
                "log_downloaded": "",
                "reloaded": "",
                "entry_migrated": "",
            }
        )

    def _get_options_schema(self):
        options = self._config_entry.options
        log_levels = ["debug", "info", "warning", "error", "critical"]
        return vol.Schema({
            vol.Optional('log_level', default=options.get('log_level', 'info')): vol.In(log_levels),
            vol.Optional('download_log', default=False): bool,
            vol.Optional('reload', default=False): bool,
            vol.Optional("migrate", default=False): bool,
        })

    def _set_log_level(self, log_level):
        """Set the log level for the neviweb130 component."""
        level = getattr(logging, log_level.upper(), logging.INFO)
        _LOGGER.setLevel(level)
        _LOGGER.info("Log level set to %s", log_level)

    async def _trigger_download_log(self):
        """Method to handle log download."""
        try:
            # Implement your log download logic here
            log_content = await self._capture_logs()
            log_path = self.hass.config.path("neviweb130_log.txt")

            async with aiofiles.open(log_path, 'w') as log_file:
                await log_file.write(log_content)

            _LOGGER.info("Log file has been downloaded to %s", log_path)
            # Create a persistent notification
            self.hass.async_create_task(
                self.hass.services.async_call(
                    "persistent_notification",
                    "create",
                    {
                        "title": "Log Downloaded",
                        "message": f"Log file has been downloaded to {log_path}",
                        "notification_id": "neviweb130_log_download"
                    }
                )
            )
        except Exception as e:
            _LOGGER.error("Failed to write log file: %s", e)
            # Create a persistent notification for the error
            await self.hass.services.async_call(
                "persistent_notification",
                "create",
                {
                    "title": "Log Download Failed",
                    "message": f"Failed to write log file: {e}",
                    "notification_id": "neviweb130_log_download_error"
                }
            )

    async def _capture_logs(self):
        """Capture recent logs for writing to a file."""
        log_path = os.path.join(self.hass.config.config_dir, 'home-assistant.log')
        filtered_logs = []
        try:
            async with aiofiles.open(log_path, 'r') as log_file:
                async for line in log_file:
                    if '[custom_components.neviweb130' in line:
                        filtered_logs.append(line)
            return "".join(filtered_logs)
        except Exception as e:
            _LOGGER.error("Error reading log file: %s", e)
            return "Failed to capture logs."


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
                        "message": f"Integration neviweb130 have been reloaded",
                        "notification_id": "neviweb130_reloaded"
                    }
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
                    "notification_id": "neviweb130_reload_error"
                }
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
                    "message": f"Neviweb130 device's unique_id have been migrated from integer values to string values. more details in log.",
                    "notification_id": "neviweb130_migrated"
                }
            )
        )

class InvalidUserEmail(exceptions.HomeAssistantError):
    """Error to indicate invalid email specified."""


class CannotConnect(exceptions.HomeAssistantError):
    """Error to indicate we cannot connect to Neviweb."""


class OsError(exceptions.HomeAssistantError):
    """Error to indicate we cannot send requests to Neviweb."""
