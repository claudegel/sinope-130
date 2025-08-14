"""Helpers function to help debug neviweb130"""

import logging
import os
import json

_LOGGER = logging.getLogger(__name__)

DEBUG_FILE_PATH = "neviweb130_debug.txt"  # dans /config

def debug_coordinator(coordinator, device_id=None, device_name=None):
    import pprint

    _LOGGER.debug("Coordinator class: %s", type(coordinator))
    _LOGGER.debug("Attributs disponibles: %s", dir(coordinator._devices))
    _LOGGER.debug("Client disponible: %s", dir(coordinator.client))
    _LOGGER.debug("Data disponible: %s", dir(coordinator.data.values))
    # Log des attributs simples sans risques de récursion
    for attr in ["data", "_devices", "update_interval"]:
        value = getattr(coordinator, attr, "<inconnu>")
        try:
            _LOGGER.debug("%s: %s", attr, value)
        except Exception as e:
            _LOGGER.warning("Impossible d'afficher %s: %s", attr, e)

    _LOGGER.debug("Données du coordinator (data):")
    for dev_id, dev_obj in coordinator.data.items():
        _LOGGER.debug("[%s] %s", dev_id, getattr(dev_obj, "name", "??"))

    # Inspection ciblée
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
        _LOGGER.debug("Device ciblé (%s):\n%s", 
                      getattr(target_device, "name", "inconnu"), 
                      pprint.pformat(vars(target_device)))
    else:
        _LOGGER.warning("Device non trouvé avec ID '%s' ou nom '%s'", device_id, device_name)


def write_debug_file(hass, content: dict):
    config_path = hass.config.path(DEBUG_FILE_PATH)
    try:
        with open(config_path, "w", encoding="utf-8") as file:
            json.dump(content, file, indent=2, ensure_ascii=False)
        _LOGGER.info("Fichier de debug écrit : %s", config_path)
    except Exception as e:
        _LOGGER.error("Impossible d'écrire le fichier de debug : %s", e)
