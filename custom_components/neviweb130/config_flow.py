from homeassistant import config_entries

from . import DOMAIN


class DummyFlowHandler(config_entries.ConfigFlow, domain=DOMAIN):
    pass
