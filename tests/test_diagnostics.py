"""Test the Simple Integration diagnostics."""

from syrupy.assertion import SnapshotAssertion

from homeassistant.core import HomeAssistant

from pytest_homeassistant_custom_component.common import MockConfigEntry
from pytest_homeassistant_custom_component.components.diagnostics import get_diagnostics_for_config_entry
from pytest_homeassistant_custom_component.typing import ClientSessionGenerator

from custom_components.simple_integration.const import DOMAIN

# Fields to exclude from snapshot as they change each run
TO_EXCLUDE = {
    "id",
    "device_id",
    "via_device_id",
    "last_updated",
    "last_changed",
    "last_reported",
    "created_at",
    "modified_at",
    "entry_id",
}


def limit_diagnostic_attrs(prop, path) -> bool:
    """Mark attributes to exclude from diagnostic snapshot."""
    return prop in TO_EXCLUDE


async def test_entry_diagnostics(
    hass: HomeAssistant,
    hass_client: ClientSessionGenerator,
    snapshot: SnapshotAssertion,
) -> None:
    """Test config entry diagnostics."""

    entry = MockConfigEntry(domain=DOMAIN, data={"name": "simple config",})
    entry.add_to_hass(hass)
    await hass.config_entries.async_setup(entry.entry_id)
    await hass.async_block_till_done()

    assert await get_diagnostics_for_config_entry(
        hass, hass_client, entry
    ) == snapshot(exclude=limit_diagnostic_attrs)
