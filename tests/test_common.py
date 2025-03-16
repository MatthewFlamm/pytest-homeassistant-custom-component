"""Tests changes to common module."""
import json

from pytest_homeassistant_custom_component.common import (
    load_fixture, 
    load_json_value_fixture,
    load_json_array_fixture,
    load_json_object_fixture
)

def test_load_fixture():
    data = json.loads(load_fixture("test_data.json"))
    assert data == {"test_key": "test_value"}

def test_load_json_value_fixture():
    """Test load_json_value_fixture can load fixture file"""
    data = load_json_value_fixture("test_data.json")
    assert data == {"test_key": "test_value"}

def test_load_json_array_fixture():
    """Test load_json_array_fixture can load fixture file"""
    data = load_json_array_fixture("test_array.json")
    assert data == [{"test_key1": "test_value1"},{"test_key2": "test_value2"}]

def test_load_json_object_fixture():
    """Test load_json_object_fixture can load fixture file"""
    data = load_json_object_fixture("test_data.json")
    assert data == {"test_key": "test_value"}
