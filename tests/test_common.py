"""Tests changes to common module."""
from pytest_homeassistant_custom_component.common import load_fixture


def test_load_fixture():
    data = load_fixture("test_data.json")
    
