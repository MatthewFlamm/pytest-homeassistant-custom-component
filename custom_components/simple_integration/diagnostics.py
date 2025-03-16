"""diagnostics for Simple Integration integration."""

from __future__ import annotations

from typing import Any

from homeassistant.components.diagnostics import async_redact_data
from homeassistant.config_entries import ConfigEntry
from homeassistant.const import (
    CONF_PASSWORD,
    CONF_TOKEN,
    CONF_USERNAME,
)
from homeassistant.core import HomeAssistant

TO_REDACT = {
    CONF_PASSWORD,
    CONF_USERNAME,
    CONF_TOKEN,
}


async def async_get_config_entry_diagnostics(
    hass: HomeAssistant, entry: ConfigEntry
) -> dict[str, Any]:
    """Return diagnostics for a config entry."""

    diagnostic_data: dict[str, Any] = {
        "config_entry": async_redact_data(entry.as_dict(), TO_REDACT),
    }

    return diagnostic_data
