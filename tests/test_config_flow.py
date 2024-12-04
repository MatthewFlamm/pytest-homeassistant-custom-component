"""Test the Simple Integration config flow."""
from unittest.mock import patch

from homeassistant import config_entries, setup
from custom_components.simple_integration.const import DOMAIN
from homeassistant.setup import async_setup_component

from homeassistant.components.application_credentials import (
    ClientCredential,
    async_import_client_credential,
)
CLIENT_ID = "1234"
CLIENT_SECRET = "5678"

async def setup_credentials(hass) -> None:
    """Fixture to setup credentials."""
    assert await async_setup_component(hass, "application_credentials", {})
    await async_import_client_credential(
        hass,
        DOMAIN,
        ClientCredential(CLIENT_ID, CLIENT_SECRET),
    )


async def test_form(hass):
    """Test we get the form."""
    await setup.async_setup_component(hass, "persistent_notification", {})
    await setup_credentials(hass)
    result = await hass.config_entries.flow.async_init(
        DOMAIN, context={"source": config_entries.SOURCE_USER}
    )
    assert result["type"] == "form"
    assert result["errors"] == {}

    with patch(
        "custom_components.simple_integration.async_setup", return_value=True
    ) as mock_setup, patch(
        "custom_components.simple_integration.async_setup_entry",
        return_value=True,
    ) as mock_setup_entry:
        result2 = await hass.config_entries.flow.async_configure(
            result["flow_id"],
            {
                "name": "new_simple_config"
            },
        )

    assert result2["type"] == "create_entry"
    assert result2["title"] == "new_simple_config"
    assert result2["data"] == {
        "name": "new_simple_config",
    }
    await hass.async_block_till_done()
    assert len(mock_setup.mock_calls) == 1
    assert len(mock_setup_entry.mock_calls) == 1
