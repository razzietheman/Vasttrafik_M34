"""DataUpdateCoordinator for Västtrafik M34."""
from __future__ import annotations

from datetime import datetime, timedelta, timezone
import logging
from typing import Any

from aiohttp import ClientError, ClientSession

from homeassistant.config_entries import ConfigEntry
from homeassistant.core import HomeAssistant
from homeassistant.helpers.storage import Store
from homeassistant.helpers.update_coordinator import DataUpdateCoordinator, UpdateFailed
from homeassistant.util import dt as dt_util

from .const import (
    API_BASE,
    CONF_AUTH_KEY,
    CONF_DIRECTION_FILTER,
    CONF_EXCLUDE_CANCELLED,
    CONF_LINE_FILTER,
    CONF_MAX_PER_LINE,
    CONF_STATION_GID,
    CONF_TIME_SPAN_MINUTES,
    CONF_UPDATE_INTERVAL,
    DEFAULT_CACHE_MAX_AGE_MINUTES,
    DEFAULT_EXCLUDE_CANCELLED,
    DEFAULT_MAX_PER_LINE,
    DEFAULT_TIME_SPAN_MINUTES,
    DEFAULT_UPDATE_INTERVAL,
    DOMAIN,
    TOKEN_URL,
)

_LOGGER = logging.getLogger(__name__)

# Fields that describe the actual departure (not the minute-by-minute countdown).
_STABLE_FIELDS = (
    "line",
    "destination",
    "planned_time",
    "estimated_time",
    "track",
    "is_cancelled",
    "is_realtime",
    "transport_mode",
)


def _aware(value: datetime | None) -> datetime | None:
    """Return a timezone-aware datetime.

    The API normally returns RFC 3339 timestamps with an offset. If a naive
    timestamp is received, it is interpreted as local time rather than UTC so
    that we do not introduce a 1-2 hour error during the Swedish summer.
    """
    if value is None:
        return None
    if value.tzinfo is None:
        return value.replace(tzinfo=dt_util.DEFAULT_TIME_ZONE)
    return value


class VasttrafikDataUpdateCoordinator(DataUpdateCoordinator[dict[str, Any]]):
    """Fetch departures from Västtrafik API v4."""

    def __init__(
        self,
        hass: HomeAssistant,
        entry: ConfigEntry,
        session: ClientSession,
    ) -> None:
        """Initialize coordinator."""
        options = entry.options
        interval = options.get(CONF_UPDATE_INTERVAL, DEFAULT_UPDATE_INTERVAL)
        super().__init__(
            hass,
            _LOGGER,
            name=DOMAIN,
            update_interval=timedelta(seconds=interval),
            config_entry=entry,
        )
        self.entry = entry
        self.session = session
        self._access_token: str | None = None
        self._token_expires_at: datetime | None = None
        self._last_good: dict[str, Any] | None = None
        self._last_cache_write: datetime | None = None
        self._cache_max_age = timedelta(minutes=DEFAULT_CACHE_MAX_AGE_MINUTES)
        self._store = Store(hass, 1, f"{DOMAIN}.{entry.entry_id}")

    @property
    def station_gid(self) -> str:
        return self.entry.data[CONF_STATION_GID]

    @property
    def auth_key(self) -> str:
        return self.entry.data[CONF_AUTH_KEY]

    @property
    def direction_filter(self) -> str:
        return (self.entry.options.get(CONF_DIRECTION_FILTER) or "").strip()

    @property
    def line_filter(self) -> str:
        return (self.entry.options.get(CONF_LINE_FILTER) or "").strip()

    @property
    def exclude_cancelled(self) -> bool:
        return self.entry.options.get(
            CONF_EXCLUDE_CANCELLED, DEFAULT_EXCLUDE_CANCELLED
        )

    async def async_load_cache(self) -> None:
        """Restore last successful departures after HA restart."""
        try:
            data = await self._store.async_load()
        except Exception:  # noqa: BLE001
            _LOGGER.exception("Could not load Västtrafik cache")
            return
        if not isinstance(data, dict) or data.get("departures") is None:
            return

        cached_at = dt_util.parse_datetime(data.get("cached_at") or "")
        if cached_at is not None:
            if cached_at.tzinfo is None:
                cached_at = cached_at.replace(tzinfo=timezone.utc)
            self._last_cache_write = cached_at

        self._last_good = data
        _LOGGER.info(
            "Restored Västtrafik cache (%s departures, saved %s)",
            len(data.get("departures") or []),
            data.get("cached_at"),
        )

    async def async_save_cache(self, payload: dict[str, Any]) -> None:
        """Persist last good payload to disk."""
        now = dt_util.utcnow()
        try:
            await self._store.async_save(
                {
                    **payload,
                    "cached_at": now.isoformat(),
                }
            )
            self._last_cache_write = now
        except Exception:  # noqa: BLE001
            _LOGGER.exception("Could not save Västtrafik cache")

    async def _get_access_token(self) -> str:
        """Get or refresh OAuth2 access token."""
        now = dt_util.utcnow()
        if (
            self._access_token
            and self._token_expires_at
            and now < self._token_expires_at
        ):
            return self._access_token

        headers = {
            "Authorization": f"Basic {self.auth_key}",
            "Content-Type": "application/x-www-form-urlencoded",
        }
        try:
            async with self.session.post(
                TOKEN_URL,
                headers=headers,
                data={"grant_type": "client_credentials"},
                timeout=15,
            ) as response:
                if response.status != 200:
                    text = await response.text()
                    _LOGGER.error("Token request failed: %s - %s", response.status, text)
                    raise UpdateFailed(f"Failed to get access token: {response.status}")

                result = await response.json()
                token = result.get("access_token")
                if not token:
                    raise UpdateFailed("No access token in token response")
                self._access_token = token
                expires_in = int(result.get("expires_in", 86400))
                # Refresh 5 minutes before expiry
                self._token_expires_at = now + timedelta(
                    seconds=max(expires_in - 300, 60)
                )
                return self._access_token
        except ClientError as ex:
            raise UpdateFailed(f"Network error getting token: {ex}") from ex

    def _parse_departure(self, departure: dict[str, Any]) -> dict[str, Any] | None:
        """Parse one departure object from API."""
        service_journey = departure.get("serviceJourney") or {}
        line_obj = service_journey.get("line") or {}

        planned_time = departure.get("plannedTime")
        estimated_time = departure.get("estimatedTime")
        effective_time = estimated_time or planned_time
        if not effective_time:
            return None

        delay_minutes = 0
        if estimated_time and planned_time:
            try:
                planned_dt = _aware(dt_util.parse_datetime(planned_time))
                estimated_dt = _aware(dt_util.parse_datetime(estimated_time))
                if planned_dt and estimated_dt:
                    delay_minutes = int(
                        round((estimated_dt - planned_dt).total_seconds() / 60)
                    )
            except (TypeError, ValueError):
                delay_minutes = 0

        track = ""
        stop_point = departure.get("stopPoint") or {}
        platform = stop_point.get("platform")
        if platform:
            track = str(platform)
        elif departure.get("platform"):
            track = str(departure["platform"])

        line_name = line_obj.get("name") or line_obj.get("designation") or "?"
        direction = service_journey.get("direction") or ""
        transport_mode = (line_obj.get("transportMode") or "").lower()

        is_cancelled = bool(departure.get("isCancelled", False))

        return {
            "line": line_name,
            "line_designation": line_obj.get("designation") or "",
            "destination": direction,
            "planned_time": planned_time or "",
            "estimated_time": effective_time,
            "delay_minutes": delay_minutes,
            "track": track,
            "is_cancelled": is_cancelled,
            "is_realtime": estimated_time is not None,
            "transport_mode": transport_mode,
        }

    def _apply_filters(self, departures: list[dict[str, Any]]) -> list[dict[str, Any]]:
        """Apply direction/line/cancelled filters and drop past departures."""
        now = dt_util.now()
        direction_f = self.direction_filter.lower()
        line_f = self.line_filter.lower()
        result: list[dict[str, Any]] = []

        for dep in departures:
            if self.exclude_cancelled and dep.get("is_cancelled"):
                continue

            if direction_f and direction_f not in (dep.get("destination") or "").lower():
                continue

            if line_f:
                line = (dep.get("line") or "").lower()
                designation = (dep.get("line_designation") or "").lower()
                if line_f not in line and line_f not in designation:
                    continue

            try:
                dt = _aware(dt_util.parse_datetime(dep["estimated_time"]))
                if dt is None:
                    continue
                seconds = (dt - now).total_seconds()
                # Keep departures that are just about to leave; drop older ones.
                if seconds < -60:
                    continue
                minutes = max(0, int(seconds // 60))
                relative = "Nu" if minutes == 0 else f"{minutes} min"
                departure_hhmm = dt.strftime("%H:%M")
            except (TypeError, ValueError, KeyError):
                continue

            result.append(
                {
                    **dep,
                    "departure_time": departure_hhmm,
                    "relative_time": relative,
                    "minutes_until": minutes,
                }
            )

        result.sort(key=lambda d: d.get("minutes_until", 9999))
        return result

    @staticmethod
    def _signature(departures: list[dict[str, Any]]) -> tuple[tuple[Any, ...], ...]:
        """Stable signature used to avoid writing unchanged data to disk."""
        return tuple(
            tuple(dep.get(key) for key in _STABLE_FIELDS) for dep in departures
        )

    def _cached_or_fail(self, reason: str) -> dict[str, Any]:
        """Return recent last-good data, re-filtered, or raise UpdateFailed."""
        if self._last_good is None:
            raise UpdateFailed(reason)

        cached_at = dt_util.parse_datetime(self._last_good.get("cached_at") or "")
        if cached_at is None:
            cached_at = dt_util.utcnow() - self._cache_max_age - timedelta(seconds=1)
        elif cached_at.tzinfo is None:
            cached_at = cached_at.replace(tzinfo=timezone.utc)

        if dt_util.utcnow() - cached_at > self._cache_max_age:
            self._last_good = None
            raise UpdateFailed(f"{reason}; cached departures are too old")

        _LOGGER.warning(
            "Västtrafik temporary failure (%s) – using cached departures", reason
        )
        cached = dict(self._last_good)
        cached["departures"] = self._apply_filters(
            list(self._last_good.get("departures") or [])
        )
        cached["from_cache"] = True
        cached["cache_reason"] = reason
        return cached

    async def _async_update_data(self) -> dict[str, Any]:
        """Fetch departures from API; keep recent last-good on transient failures."""
        try:
            token = await self._get_access_token()
        except UpdateFailed as ex:
            return self._cached_or_fail(str(ex))

        options = self.entry.options
        time_span = options.get(CONF_TIME_SPAN_MINUTES, DEFAULT_TIME_SPAN_MINUTES)
        max_per_line = options.get(CONF_MAX_PER_LINE, DEFAULT_MAX_PER_LINE)

        headers = {"Authorization": f"Bearer {token}"}
        params = {
            "timeSpanInMinutes": time_span,
            "maxDeparturesPerLineAndDirection": max_per_line,
            "limit": 50,
        }
        url = f"{API_BASE}/stop-areas/{self.station_gid}/departures"

        try:
            async with self.session.get(
                url, headers=headers, params=params, timeout=20
            ) as response:
                if response.status == 401:
                    self._access_token = None
                    self._token_expires_at = None
                    return self._cached_or_fail("Access token expired, will retry")

                if response.status != 200:
                    body = await response.text()
                    # 5xx / backend blips are common – warning + cache, not error storm
                    log = _LOGGER.warning if response.status >= 500 else _LOGGER.error
                    log(
                        "Departures request failed: %s - %s",
                        response.status,
                        body[:300],
                    )
                    return self._cached_or_fail(
                        f"Failed to get departures: {response.status}"
                    )

                payload = await response.json()
        except ClientError as ex:
            return self._cached_or_fail(f"Network error: {ex}")
        except TimeoutError as ex:
            return self._cached_or_fail(f"Timeout: {ex}")

        raw: list[dict[str, Any]] = []
        for item in payload.get("results") or []:
            parsed = self._parse_departure(item)
            if parsed:
                raw.append(parsed)

        filtered = self._apply_filters(raw)

        result = {
            "departures": filtered,
            "last_update": dt_util.now().isoformat(),
            "raw_count": len(raw),
            "from_cache": False,
        }
        previous = self._last_good
        self._last_good = result

        needs_save = (
            previous is None
            or self._signature(previous.get("departures") or [])
            != self._signature(filtered)
            or self._last_cache_write is None
            or dt_util.utcnow() - self._last_cache_write >= self._cache_max_age
        )
        if needs_save:
            await self.async_save_cache(result)
        return result
