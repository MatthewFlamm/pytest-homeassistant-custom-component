"""
Constants used by Home Assistant components.

This file is originally from homeassistant/core and modified by pytest-homeassistant-custom-component.
"""
from typing import TYPE_CHECKING, Final
MAJOR_VERSION: Final = 2025
MINOR_VERSION: Final = 4
PATCH_VERSION: Final = "1"
__short_version__: Final = f"{MAJOR_VERSION}.{MINOR_VERSION}"
__version__: Final = f"{__short_version__}.{PATCH_VERSION}"
