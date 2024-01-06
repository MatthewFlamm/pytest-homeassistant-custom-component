"""
Test deprecated constants custom integration.

This file is originally from homeassistant/core and modified by pytest-homeassistant-custom-component.
"""

from types import ModuleType
from typing import Any


def import_deprecated_constant(module: ModuleType, constant_name: str) -> Any:
    """Import and return deprecated constant."""
    return getattr(module, constant_name)
