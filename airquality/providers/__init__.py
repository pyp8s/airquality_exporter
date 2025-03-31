#!/usr/bin/env python3
# pylint: disable=line-too-long, missing-function-docstring, logging-fstring-interpolation
# pylint: disable=too-many-locals, broad-except, too-many-arguments, raise-missing-from
# pylint: disable=import-error,f-string-without-interpolation
"""

  Providers

"""

import pkgutil
import importlib.util

providers = {}

for item in pkgutil.iter_modules(["providers",]):
    _loader = pkgutil.find_loader(f"providers.{item.name}")
    if _loader:
        providers[item.name] = _loader.load_module()
