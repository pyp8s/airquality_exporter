#!/usr/bin/env python3
# pylint: disable=line-too-long, missing-function-docstring, logging-fstring-interpolation
# pylint: disable=too-many-locals, broad-except, too-many-arguments, raise-missing-from
# pylint: disable=import-error
"""

  Configuration file

"""

import os
import sys
import json
import logging
from logging.handlers import WatchedFileHandler

CONFIG_FILENAME = os.environ.get("CONFIG_FILENAME", "config.json")

try:
    with open(CONFIG_FILENAME, "r", encoding="utf-8") as config_fh:
        config_dict = json.loads(config_fh.read())
except Exception as e:
    print(f"Can't read config file '{CONFIG_FILENAME}' ({e.__class__.__name__}): {e}")
    sys.exit(1)

LOG_FILENAME = config_dict.get('log_filename', "common.log")
LOG_LEVEL = getattr(logging, str(config_dict.get("log_level", "INFO")).upper())

APP_NAME = "Air Quality Exporter"
ENV_NAME = config_dict.get('env_name', "local")
VERSION = os.environ.get('APP_VERSION', '0.0.0')

METRICS = config_dict.get('metrics', {})

METRICS_LISTEN_ADDRESS = METRICS.get('listen_address', "0.0.0.0")
METRICS_LISTEN_PORT = METRICS.get('listen_port', 19001)

PROVIDERS = config_dict.get('providers', [])

logging.root.handlers = []
logging.basicConfig(
    level=LOG_LEVEL,
    format="%(asctime)s level=%(levelname)s function=%(name)s.%(funcName)s %(message)s",
    handlers=[
        WatchedFileHandler(filename=LOG_FILENAME),
        logging.StreamHandler()
    ]
)
