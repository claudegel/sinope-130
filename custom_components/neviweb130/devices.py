import json
import os
import aiofiles
import logging

_LOGGER = logging.getLogger(__name__)

CONFDIR = "/config/.storage/"

CONF_FILE = CONFDIR + "neviweb130.json"
device_dict = {}

async def load_devices():
    global device_dict
    device_dict.clear()
    if not os.path.exists(CONF_FILE):
        # File does not exist, create an empty file
        async with aiofiles.open(CONF_FILE, 'w') as f:
            pass  # creates an empty file
        return

    if os.path.exists(CONF_FILE):
        async with aiofiles.open(CONF_FILE, 'r') as f:
            async for line in f:
                device = json.loads(line)
                device_dict[device[0]] = device

    _LOGGER.debug("Loading device: %s", device_dict)

async def save_devices(data):
    _LOGGER.info("Saving energy stat data %s to CONF_FILE %s", data, CONF_FILE)
    async with aiofiles.open(CONF_FILE, 'w') as f:
        for device in data.values():
            await f.write(json.dumps(device) + "\n")
