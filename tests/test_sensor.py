"""Tests for the Västtrafik M34 sensors."""
from __future__ import annotations

from datetime import timedelta
from unittest.mock import MagicMock

import pytest
from homeassistant.util import dt as dt_util
from pytest_homeassistant_custom_component.common import MockConfigEntry

from custom_components.vasttrafik_m34.const import DOMAIN
from custom_components.vasttrafik_m34.coordinator import (
    VasttrafikDataUpdateCoordinator,
)
from custom_components.vasttrafik_m34.sensor import (
    VasttrafikM34Sensor,
    VasttrafikMinutesUntilSensor,
    VasttrafikNextDepartureSensor,
)

STATION_GID = "9021014001960000"


@pytest.fixture
def sensor_setup(hass):
    """Return an entry, coordinator and populated sensor data."""
    entry = MockConfigEntry(
        domain=DOMAIN,
        data={
            "auth_key": "key",
            "station_gid": STATION_GID,
            "station_name": "Central",
        },
        options={},
        unique_id=f"vasttrafik_{STATION_GID}",
    )
    entry.add_to_hass(hass)
    coordinator = VasttrafikDataUpdateCoordinator(hass, entry, MagicMock())

    now = dt_util.utcnow()
    coordinator.data = {
        "departures": [
            {
                "line": "Buss 6",
                "destination": "Resecentrum via Stallsiken",
                "departure_time": "07:18",
                "relative_time": "3 min",
                "minutes_until": 3,
                "delay_minutes": 0,
                "track": "A",
                "is_realtime": True,
                "is_cancelled": False,
                "transport_mode": "bus",
                "estimated_time": (now + timedelta(minutes=3)).isoformat(),
            }
        ],
        "last_update": now.isoformat(),
        "from_cache": False,
    }
    return entry, coordinator


def test_text_state_and_attributes(sensor_setup):
    """The text sensor keeps the full destination and exposes next_* attributes."""
    entry, coordinator = sensor_setup
    sensor = VasttrafikM34Sensor(coordinator, entry, "Central", STATION_GID)

    assert sensor.native_value == (
        "kl. 07:18 (3 min) → Resecentrum via Stallsiken"
    )
    attrs = sensor.extra_state_attributes
    assert attrs["next_line"] == "Buss 6"
    assert attrs["next_track"] == "A"
    assert attrs["next_minutes_until"] == 3
    assert attrs["departure_count"] == 1


def test_timestamp_sensor(sensor_setup):
    """The timestamp sensor returns a timezone-aware datetime."""
    _, coordinator = sensor_setup
    sensor = VasttrafikNextDepartureSensor(coordinator, "Central", STATION_GID)
    value = sensor.native_value
    assert value is not None
    assert value.tzinfo is not None


def test_minutes_sensor(sensor_setup):
    """The numeric sensor returns the countdown."""
    _, coordinator = sensor_setup
    sensor = VasttrafikMinutesUntilSensor(coordinator, "Central", STATION_GID)
    assert sensor.native_value == 3


def test_unique_ids(sensor_setup):
    """All three entities have distinct stable unique IDs."""
    entry, coordinator = sensor_setup
    ids = {
        VasttrafikM34Sensor(coordinator, entry, "Central", STATION_GID).unique_id,
        VasttrafikNextDepartureSensor(coordinator, "Central", STATION_GID).unique_id,
        VasttrafikMinutesUntilSensor(coordinator, "Central", STATION_GID).unique_id,
    }
    assert len(ids) == 3
