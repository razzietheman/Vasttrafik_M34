"""Sensor platform for Västtrafik M34."""
from __future__ import annotations

from datetime import datetime
from typing import Any

from homeassistant.components.sensor import (
    SensorDeviceClass,
    SensorEntity,
    SensorStateClass,
)
from homeassistant.config_entries import ConfigEntry
from homeassistant.const import UnitOfTime
from homeassistant.core import HomeAssistant
from homeassistant.helpers.device_registry import DeviceEntryType, DeviceInfo
from homeassistant.helpers.entity_platform import AddEntitiesCallback
from homeassistant.helpers.update_coordinator import CoordinatorEntity
from homeassistant.util import dt as dt_util

from .const import (
    ATTR_DEPARTURE_COUNT,
    ATTR_DEPARTURES,
    ATTR_DEPARTURES_JSON,
    ATTR_DIRECTION_FILTER,
    ATTR_LAST_UPDATE,
    ATTR_LINE_FILTER,
    ATTR_NEXT_DELAY_MINUTES,
    ATTR_NEXT_DEPARTURE_TIME,
    ATTR_NEXT_DESTINATION,
    ATTR_NEXT_IS_REALTIME,
    ATTR_NEXT_LINE,
    ATTR_NEXT_MINUTES_UNTIL,
    ATTR_NEXT_TRACK,
    ATTR_STATION_GID,
    ATTR_STATION_NAME,
    CONF_SHOW_DELAY,
    CONF_STATION_GID,
    CONF_STATION_NAME,
    DEFAULT_SHOW_DELAY,
    DOMAIN,
)
from .coordinator import VasttrafikDataUpdateCoordinator


async def async_setup_entry(
    hass: HomeAssistant,
    entry: ConfigEntry,
    async_add_entities: AddEntitiesCallback,
) -> None:
    """Set up Västtrafik sensors from a config entry."""
    coordinator = entry.runtime_data
    station_name = entry.data[CONF_STATION_NAME]
    station_gid = entry.data[CONF_STATION_GID]
    async_add_entities(
        [
            VasttrafikM34Sensor(coordinator, entry, station_name, station_gid),
            VasttrafikNextDepartureSensor(coordinator, station_name, station_gid),
            VasttrafikMinutesUntilSensor(coordinator, station_name, station_gid),
        ]
    )


def _device_info(station_name: str, station_gid: str) -> DeviceInfo:
    """Return device info shared by all entities for one stop area."""
    return DeviceInfo(
        identifiers={(DOMAIN, station_gid)},
        name=station_name,
        manufacturer="Västtrafik",
        model="M34 Departure Monitor",
        entry_type=DeviceEntryType.SERVICE,
        configuration_url="https://www.vasttrafik.se",
    )


def _icon_for_mode(mode: str) -> str:
    """Pick icon from transport mode."""
    mode = (mode or "").lower()
    if mode in ("bus", "buss"):
        return "mdi:bus"
    if mode in ("tram", "spårvagn", "sparvagn"):
        return "mdi:tram"
    if mode in ("train", "tåg", "tag", "rail"):
        return "mdi:train"
    if mode in ("ferry", "boat", "färja"):
        return "mdi:ferry"
    return "mdi:bus-clock"


def _next_departure(
    coordinator: VasttrafikDataUpdateCoordinator,
) -> dict[str, Any] | None:
    """Return the first departure, if any."""
    deps = (coordinator.data or {}).get("departures") or []
    return deps[0] if deps else None


class VasttrafikM34Sensor(
    CoordinatorEntity[VasttrafikDataUpdateCoordinator], SensorEntity
):
    """Textual departure sensor for one stop area."""

    _attr_has_entity_name = True
    _attr_name = None

    def __init__(
        self,
        coordinator: VasttrafikDataUpdateCoordinator,
        entry: ConfigEntry,
        station_name: str,
        station_gid: str,
    ) -> None:
        """Initialize sensor."""
        super().__init__(coordinator)
        self._entry = entry
        self._station_name = station_name
        self._station_gid = station_gid
        self._attr_unique_id = f"vasttrafik_{station_gid}"
        self._attr_device_info = _device_info(station_name, station_gid)

    @property
    def icon(self) -> str:
        """Icon from next departure transport mode."""
        dep = _next_departure(self.coordinator)
        return _icon_for_mode(dep.get("transport_mode", "")) if dep else "mdi:bus-clock"

    @property
    def native_value(self) -> str | None:
        """State: next departure in compact form."""
        data = self.coordinator.data
        if not data:
            return None

        deps = data.get("departures") or []
        if not deps:
            return "Inga avgångar"

        dep = deps[0]
        show_delay = self._entry.options.get(CONF_SHOW_DELAY, DEFAULT_SHOW_DELAY)
        state = f"kl. {dep.get('departure_time', '?')} ({dep.get('relative_time', '?')})"

        # Visa destination bara om man inte redan filtrerat på riktning
        if not (self.coordinator.direction_filter or "").strip():
            dest = dep.get("destination") or ""
            short_dest = dest.split(",")[0].strip() if dest else ""
            if short_dest:
                state = f"{state} → {short_dest}"

        delay = int(dep.get("delay_minutes") or 0)
        if show_delay and delay > 0:
            state = f"{state} · +{delay} min"
        elif show_delay and delay < 0:
            state = f"{state} · {delay} min"

        return state

    @property
    def extra_state_attributes(self) -> dict[str, Any]:
        """Return attributes including next_* and full departure lists."""
        data = self.coordinator.data
        if not data:
            return {}

        deps = data.get("departures") or []
        show_delay = self._entry.options.get(CONF_SHOW_DELAY, DEFAULT_SHOW_DELAY)

        # Legacy human-readable strings
        departure_list: list[str] = []
        for dep in deps[:15]:
            delay = int(dep.get("delay_minutes") or 0)
            delay_str = ""
            if show_delay and delay > 0:
                delay_str = f" (+{delay})"
            elif show_delay and delay < 0:
                delay_str = f" ({delay})"
            cancelled = " [INSTÄLLD]" if dep.get("is_cancelled") else ""
            track = dep.get("track") or ""
            track_str = f" Läge {track}" if track else ""
            departure_list.append(
                f"{dep.get('line', '?')} → {dep.get('destination', '?')} - "
                f"{dep.get('departure_time', '?')} ({dep.get('relative_time', '?')})"
                f"{delay_str}{track_str}{cancelled}"
            )

        attrs: dict[str, Any] = {
            ATTR_STATION_NAME: self._station_name,
            ATTR_STATION_GID: self._station_gid,
            ATTR_DEPARTURE_COUNT: len(deps),
            ATTR_DEPARTURES: departure_list,
            ATTR_DEPARTURES_JSON: deps[:20],
            ATTR_LAST_UPDATE: data.get("last_update"),
            ATTR_DIRECTION_FILTER: self.coordinator.direction_filter or None,
            ATTR_LINE_FILTER: self.coordinator.line_filter or None,
            "from_cache": bool(data.get("from_cache")),
            "cache_reason": data.get("cache_reason"),
        }

        nxt = deps[0] if deps else None
        attrs.update(
            {
                ATTR_NEXT_LINE: nxt.get("line") if nxt else None,
                ATTR_NEXT_DESTINATION: nxt.get("destination") if nxt else None,
                ATTR_NEXT_DEPARTURE_TIME: nxt.get("departure_time") if nxt else None,
                ATTR_NEXT_MINUTES_UNTIL: nxt.get("minutes_until") if nxt else None,
                ATTR_NEXT_TRACK: (nxt.get("track") or None) if nxt else None,
                ATTR_NEXT_DELAY_MINUTES: nxt.get("delay_minutes", 0) if nxt else 0,
                ATTR_NEXT_IS_REALTIME: nxt.get("is_realtime", False) if nxt else False,
            }
        )

        return attrs


class VasttrafikNextDepartureSensor(
    CoordinatorEntity[VasttrafikDataUpdateCoordinator], SensorEntity
):
    """Timestamp sensor for the next departure."""

    _attr_has_entity_name = True
    _attr_name = "Nästa avgång"
    _attr_device_class = SensorDeviceClass.TIMESTAMP
    _attr_icon = "mdi:clock-outline"

    def __init__(
        self,
        coordinator: VasttrafikDataUpdateCoordinator,
        station_name: str,
        station_gid: str,
    ) -> None:
        """Initialize sensor."""
        super().__init__(coordinator)
        self._attr_unique_id = f"vasttrafik_{station_gid}_next_departure"
        self._attr_device_info = _device_info(station_name, station_gid)

    @property
    def native_value(self) -> datetime | None:
        """Return the estimated (or planned) departure time."""
        dep = _next_departure(self.coordinator)
        if not dep:
            return None
        value = dt_util.parse_datetime(dep.get("estimated_time") or "")
        if value is None:
            return None
        if value.tzinfo is None:
            return value.replace(tzinfo=dt_util.DEFAULT_TIME_ZONE)
        return value


class VasttrafikMinutesUntilSensor(
    CoordinatorEntity[VasttrafikDataUpdateCoordinator], SensorEntity
):
    """Numeric countdown sensor for the next departure."""

    _attr_has_entity_name = True
    _attr_name = "Minuter till nästa avgång"
    _attr_native_unit_of_measurement = UnitOfTime.MINUTES
    _attr_state_class = SensorStateClass.MEASUREMENT
    _attr_icon = "mdi:timer-outline"

    def __init__(
        self,
        coordinator: VasttrafikDataUpdateCoordinator,
        station_name: str,
        station_gid: str,
    ) -> None:
        """Initialize sensor."""
        super().__init__(coordinator)
        self._attr_unique_id = f"vasttrafik_{station_gid}_minutes_until"
        self._attr_device_info = _device_info(station_name, station_gid)

    @property
    def native_value(self) -> int | None:
        """Return minutes until the next departure."""
        dep = _next_departure(self.coordinator)
        if not dep:
            return None
        value = dep.get("minutes_until")
        return int(value) if value is not None else None
