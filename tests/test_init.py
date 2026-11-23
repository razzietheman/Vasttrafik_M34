"""Tests for integration setup and unload."""
from __future__ import annotations

from unittest.mock import AsyncMock, MagicMock, patch

import pytest
from homeassistant.config_entries import ConfigEntryError
from pytest_homeassistant_custom_component.common import MockConfigEntry

from custom_components.vasttrafik_m34 import async_setup_entry, async_unload_entry
from custom_components.vasttrafik_m34.const import DOMAIN


async def test_setup_and_unload(hass):
    """A valid entry is set up with a coordinator in runtime_data."""
    entry = MockConfigEntry(
        domain=DOMAIN,
        data={
            "auth_key": "key",
            "station_gid": "9021014001960000",
            "station_name": "Central",
        },
        unique_id="vasttrafik_9021014001960000",
    )
    entry.add_to_hass(hass)

    with (
        patch(
            "custom_components.vasttrafik_m34.coordinator."
            "VasttrafikDataUpdateCoordinator.async_load_cache",
            new=AsyncMock(),
        ),
        patch(
            "custom_components.vasttrafik_m34.coordinator."
            "VasttrafikDataUpdateCoordinator.async_config_entry_first_refresh",
            new=AsyncMock(),
        ),
        patch(
            "homeassistant.config_entries.ConfigEntries.async_forward_entry_setups",
            new=AsyncMock(),
        ),
        patch(
            "custom_components.vasttrafik_m34.async_get_clientsession",
            return_value=MagicMock(),
        ),
    ):
        assert await async_setup_entry(hass, entry)

    assert entry.runtime_data is not None

    with patch(
        "homeassistant.config_entries.ConfigEntries.async_unload_platforms",
        new=AsyncMock(return_value=True),
    ):
        assert await async_unload_entry(hass, entry)


async def test_missing_data(hass):
    """A malformed entry is rejected."""
    entry = MockConfigEntry(
        domain=DOMAIN,
        data={"station_gid": "9021014001960000"},
    )
    with pytest.raises(ConfigEntryError):
        await async_setup_entry(hass, entry)
