"""
Constants used by Home Assistant components.

This file is originally from homeassistant/core and modified by pytest-homeassistant-custom-component.
"""
from __future__ import annotations

from enum import StrEnum
from typing import Final

APPLICATION_NAME: Final = "HomeAssistant"
MAJOR_VERSION: Final = 2023
MINOR_VERSION: Final = 11
PATCH_VERSION: Final = "3"
__short_version__: Final = f"{MAJOR_VERSION}.{MINOR_VERSION}"
__version__: Final = f"{__short_version__}.{PATCH_VERSION}"
REQUIRED_PYTHON_VER: Final[tuple[int, int, int]] = (3, 11, 0)
REQUIRED_NEXT_PYTHON_VER: Final[tuple[int, int, int]] = (3, 11, 0)
