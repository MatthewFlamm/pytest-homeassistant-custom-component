"""Fixtures for testing."""
import pytest

# `pytester` is not enabled by default. test_deprecation.py needs it: the thing
# under test is a fixture that fails the test around it, so proving it works
# means running a real pytest with a real ini file and reading the outcome.
pytest_plugins = ["pytester"]

from pytest_homeassistant_custom_component.syrupy import HomeAssistantSnapshotExtension
from syrupy.assertion import SnapshotAssertion


@pytest.fixture
def snapshot(snapshot: SnapshotAssertion) -> SnapshotAssertion:
    """Return snapshot assertion fixture with the Home Assistant extension."""
    return snapshot.use_extension(HomeAssistantSnapshotExtension)


@pytest.fixture(autouse=True)
def auto_enable_custom_integrations(enable_custom_integrations):
    yield
    
