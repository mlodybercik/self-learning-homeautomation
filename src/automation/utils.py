import typing as t
import os
from pathlib import Path
import json
import logging
import logging.config

LOGGING_CONFIG_LOCATION = os.environ.get("LOGGING_CONFIG_LOCATION", False)
LOGGING_LEVEL = os.environ.get("LOGGING_LEVEL", "DEBUG").upper()

logger_set_up: bool = False

def get_logger(name: str, level: t.Optional[str] = None) -> logging.Logger:
    global logger_set_up
    logging_level = LOGGING_LEVEL

    if not logger_set_up:
        path = Path(LOGGING_CONFIG_LOCATION if LOGGING_CONFIG_LOCATION else __file__).parent / "logging.json"
        if not path.absolute().exists():
            raise ValueError(f"logging config doesn't exist '{path}'")

        with open(path) as file:
            logging.config.dictConfig(json.loads(file.read()))

    if level:
        logging_level = level

    logger = logging.getLogger(name)
    logger.setLevel(logging_level)
    return logger