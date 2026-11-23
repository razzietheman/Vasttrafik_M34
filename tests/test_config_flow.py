"""Tests for the Västtrafik M34 config flow."""
from __future__ import annotations

from unittest.mock import AsyncMock, MagicMock, patch

import pytest
from homeassistant import config_entries
from homeassistant.data_entry_flow import FlowResultType
from pytest_homeassistant_custom_component.common import MockConfigEntry

from custom_components.vasttrafik_m34.config_flow import (
    InvalidAuth,
    search_stations,
)
from custom_components.vasttrafik_m34.const import DOMAIN

STATIONS = [
    {"gid": "9021014001960000", "name": "Centralstationen, Göteborg"},
    {"gid": "9021014001950000", "name": "Centralhållplatsen, Göteborg"},
]


@pytest.fixture
def mocked_api():
    """Patch token validation and station search."""
    with (
        patch(
            "custom_components.vasttrafik_m34.config_flow.get_access_token",
            new=AsyncMock(return_value="token"),
        ),
        patch(
            "custom_components.vasttrafik_m34.config_flow.search_stations",
            new=AsyncMock(return_value=STATIONS),
        ),
        patch(
            "custom_components.vasttrafik_m34.async_setup_entry",
            new=AsyncMock(return_value=True),
        ),
    ):
        yield


async def test_full_flow(hass, mocked_api):
    """The three-step flow creates an entry with default options."""
    result = await hass.config_entries.flow.async_init(
        DOMAIN, context={"source": config_entries.SOURCE_USER}
    )
    assert result["type"] is FlowResultType.FORM
    assert result["step_id"] == "user"

    result = await hass.config_entries.flow.async_configure(
        result["flow_id"], {"auth_key": "abc"}
    )
    assert result["step_id"] == "station"

    result = await hass.config_entries.flow.async_configure(
        result["flow_id"], {"station_name": "Central"}
    )
    assert result["step_id"] == "select_station"

    result = await hass.config_entries.flow.async_configure(
        result["flow_id"], {"station": STATIONS[0]["gid"]}
    )
    assert result["type"] is FlowResultType.CREATE_ENTRY
    assert result["data"]["auth_key"] == "abc"
    assert result["options"]["time_span_minutes"] == 90
    assert result["options"]["max_per_line"] == 4


async def test_invalid_auth(hass):
    """A 401 from the token endpoint is shown as invalid_auth."""
    with patch(
        "custom_components.vasttrafik_m34.config_flow.get_access_token",
        new=AsyncMock(side_effect=InvalidAuth),
    ):
        result = await hass.config_entries.flow.async_init(
            DOMAIN, context={"source": config_entries.SOURCE_USER}
        )
        result = await hass.config_entries.flow.async_configure(
            result["flow_id"], {"auth_key": "wrong"}
        )

    assert result["type"] is FlowResultType.FORM
    assert result["errors"] == {"base": "invalid_auth"}


async def test_duplicate_entry(hass, mocked_api):
    """The same stop cannot be added twice."""
    existing = MockConfigEntry(
        domain=DOMAIN,
        data={"auth_key": "abc", "station_gid": STATIONS[0]["gid"]},
        unique_id=f"vasttrafik_{STATIONS[0]['gid']}",
    )
    existing.add_to_hass(hass)

    result = await hass.config_entries.flow.async_init(
        DOMAIN, context={"source": config_entries.SOURCE_USER}
    )
    result = await hass.config_entries.flow.async_configure(
        result["flow_id"], {"auth_key": "abc"}
    )
    result = await hass.config_entries.flow.async_configure(
        result["flow_id"], {"station_name": "Central"}
    )
    result = await hass.config_entries.flow.async_configure(
        result["flow_id"], {"station": STATIONS[0]["gid"]}
    )

    assert result["type"] is FlowResultType.ABORT
    assert result["reason"] == "already_configured"


async def test_reauth(hass):
    """A reauth flow updates the stored key."""
    entry = MockConfigEntry(
        domain=DOMAIN,
        data={
            "auth_key": "old",
            "station_gid": STATIONS[0]["gid"],
            "station_name": STATIONS[0]["name"],
        },
        unique_id=f"vasttrafik_{STATIONS[0]['gid']}",
    )
    entry.add_to_hass(hass)

    result = await hass.config_entries.flow.async_init(
        DOMAIN,
        context={
            "source": config_entries.SOURCE_REAUTH,
            "entry_id": entry.entry_id,
        },
    )
    assert result["step_id"] == "reauth_confirm"

    with patch(
        "custom_components.vasttrafik_m34.config_flow.get_access_token",
        new=AsyncMock(return_value="token"),
    ):
        result = await hass.config_entries.flow.async_configure(
            result["flow_id"], {"auth_key": "new"}
        )

    assert result["type"] is FlowResultType.ABORT
    assert result["reason"] == "reauth_successful"
    assert entry.data["auth_key"] == "new"


async def test_search_stations_accepts_list_response(hass):
    """A list-shaped API response is handled without an AttributeError."""
    response = MagicMock()
    response.status = 200
    response.json = AsyncMock(return_value=[{"gid": "123", "name": "Central"}])
    context = MagicMock()
    context.__aenter__ = AsyncMock(return_value=response)
    context.__aexit__ = AsyncMock(return_value=False)

    session = MagicMock()
    session.get = MagicMock(return_value=context)

    with patch(
        "custom_components.vasttrafik_m34.config_flow.async_get_clientsession",
        return_value=session,
    ):
        stations = await search_stations(hass, "token", "Central")

    assert stations == [{"gid": "123", "name": "Central"}]
