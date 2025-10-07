import json
import logging
import os
from typing import Any

import aiofiles

_LOGGER = logging.getLogger(__name__)
device_dict: dict[Any, Any] = {}


async def load_devices(conf_dir: str):
    device_dict.clear()
    conf_file = os.path.join(conf_dir, "neviweb130.json")

    if not os.path.exists(conf_file):
        # File does not exist, create an empty file
        async with aiofiles.open(conf_file, "w") as f:
            pass  # creates an empty file
        return

    if os.path.exists(conf_file):
        async with aiofiles.open(conf_file, "r") as f:
            async for line in f:
                device = json.loads(line)
                device_dict[device[0]] = device

    _LOGGER.debug("Loading device: %s", device_dict)


async def save_devices(conf_dir: str, data):
    """Saving devices energy data to file neviweb130.json"""
    conf_file = os.path.join(conf_dir, "neviweb130.json")
    _LOGGER.info("Saving energy stat data %s to CONF_FILE %s", data, conf_file)
    async with aiofiles.open(conf_file, "w") as f:
        for device in data.values():
            await f.write(json.dumps(device) + "\n")
