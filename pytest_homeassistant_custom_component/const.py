"""
Constants used by Home Assistant components.

This file is originally from homeassistant/core and modified by pytest-homeassistant-custom-component.
"""
from __future__ import annotations

from typing import Final

MAJOR_VERSION: Final = 2021
MINOR_VERSION: Final = 11
PATCH_VERSION: Final = "0b0"
__short_version__: Final = f"{MAJOR_VERSION}.{MINOR_VERSION}"
__version__: Final = f"{__short_version__}.{PATCH_VERSION}"
