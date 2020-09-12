"""
Mock utilities that are async aware.

This file is originally from homeassistant/core and modified by pytest-homeassistant-custom-component.
"""
import sys

if sys.version_info[:2] < (3, 8):
    from asynctest.mock import *  # noqa

    AsyncMock = CoroutineMock  # noqa: F405
else:
    from unittest.mock import *  # noqa
