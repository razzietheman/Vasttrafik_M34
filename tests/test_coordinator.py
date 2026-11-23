"""Tests for the Västtrafik data coordinator."""
from __future__ import annotations

from datetime import timedelta
from unittest.mock import AsyncMock, MagicMock

import pytest
from homeassistant.helpers.update_coordinator import UpdateFailed
from homeassistant.util import dt as dt_util
from pytest_homeassistant_custom_component.common import MockConfigEntry

from custom_components.vasttrafik_m34.const import DOMAIN
from custom_components.vasttrafik_m34.coordinator import (
    VasttrafikDataUpdateCoordinator,
)

TOKEN_PAYLOAD = {"access_token": "token", "expires_in": 86400}


def _response(status: int = 200, payload: dict | None = None, text: str = "") -> MagicMock:
    response = MagicMock()
    response.status = status
    response.json = AsyncMock(return_value=payload if payload is not None else {})
    response.text = AsyncMock(return_value=text)
    return response


def _context(response: MagicMock) -> MagicMock:
    context = MagicMock()
    context.__aenter__ = AsyncMock(return_value=response)
    context.__aexit__ = AsyncMock(return_value=False)
    return context


@pytest.fixture
def entry() -> MockConfigEntry:
    """Return a config entry with default options."""
    return MockConfigEntry(
        domain=DOMAIN,
        data={
            "auth_key": "key",
            "station_gid": "9021014001960000",
            "station_name": "Central",
        },
        options={},
        unique_id="vasttrafik_9021014001960000",
    )


@pytest.fixture
def coordinator(hass, entry: MockConfigEntry) -> VasttrafikDataUpdateCoordinator:
    """Return a coordinator with a mocked aiohttp session."""
    entry.add_to_hass(hass)
    session = MagicMock()
    session.post = MagicMock(return_value=_context(_response(payload=TOKEN_PAYLOAD)))
    session.get = MagicMock(return_value=_context(_response()))
    instance = VasttrafikDataUpdateCoordinator(hass, entry, session)
    instance.async_save_cache = AsyncMock()
    return instance


async def test_departures_request_parameters(coordinator):
    """The v4 API parameter names and limit are used."""
    now = dt_util.utcnow()
    coordinator.session.get.return_value = _context(
        _response(
            payload={
                "results": [
                    {
                        "serviceJourney": {
                            "line": {"name": "Buss 6", "designation": "6"},
                            "direction": "Chalmers",
                        },
                        "plannedTime": (now + timedelta(minutes=5)).isoformat(),
                        "stopPoint": {"platform": "A"},
                        "isCancelled": False,
                    }
                ]
            }
        )
    )

    result = await coordinator._async_update_data()

    assert result["raw_count"] == 1
    assert result["departures"][0]["line"] == "Buss 6"
    assert result["departures"][0]["track"] == "A"
    params = coordinator.session.get.call_args.kwargs["params"]
    assert params == {
        "timeSpanInMinutes": 90,
        "maxDeparturesPerLineAndDirection": 4,
        "limit": 50,
    }


async def test_cached_data_is_refiltered(coordinator):
    """Cached departures are re-filtered before being returned."""
    now = dt_util.utcnow()
    coordinator._last_good = {
        "departures": [
            {
                "line": "1",
                "estimated_time": (now - timedelta(minutes=10)).isoformat(),
            },
            {
                "line": "2",
                "estimated_time": (now + timedelta(minutes=5)).isoformat(),
            },
        ],
        "cached_at": now.isoformat(),
        "last_update": now.isoformat(),
    }

    cached = coordinator._cached_or_fail("API down")

    assert cached["from_cache"] is True
    assert cached["cache_reason"] == "API down"
    assert [dep["line"] for dep in cached["departures"]] == ["2"]


async def test_old_cache_is_rejected(coordinator):
    """Cached data older than the TTL is not used."""
    coordinator._last_good = {
        "departures": [],
        "cached_at": (dt_util.utcnow() - timedelta(minutes=20)).isoformat(),
    }
    with pytest.raises(UpdateFailed):
        coordinator._cached_or_fail("API down")


async def test_delay_is_rounded(coordinator):
    """A 4 minute 59 second delay is reported as 5 minutes."""
    planned = dt_util.utcnow() + timedelta(minutes=5)
    departure = {
        "serviceJourney": {"line": {"name": "6"}, "direction": "Chalmers"},
        "plannedTime": planned.isoformat(),
        "estimatedTime": (planned + timedelta(seconds=299)).isoformat(),
    }
    parsed = coordinator._parse_departure(departure)
    assert parsed is not None
    assert parsed["delay_minutes"] == 5
