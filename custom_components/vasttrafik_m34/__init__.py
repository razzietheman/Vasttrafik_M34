"""The Västtrafik M34 integration."""
from __future__ import annotations

import logging

from homeassistant.config_entries import ConfigEntry
from homeassistant.const import Platform
from homeassistant.core import HomeAssistant
from homeassistant.exceptions import ConfigEntryError
from homeassistant.helpers.aiohttp_client import async_get_clientsession

from .const import CONF_AUTH_KEY, CONF_STATION_GID, DOMAIN
from .coordinator import VasttrafikDataUpdateCoordinator

_LOGGER = logging.getLogger(__name__)

PLATFORMS = [Platform.SENSOR]

type VasttrafikConfigEntry = ConfigEntry[VasttrafikDataUpdateCoordinator]


async def async_setup_entry(hass: HomeAssistant, entry: VasttrafikConfigEntry) -> bool:
    """Set up Västtrafik M34 from a config entry."""
    if CONF_AUTH_KEY not in entry.data or CONF_STATION_GID not in entry.data:
        raise ConfigEntryError("Missing required data in config entry")

    session = async_get_clientsession(hass)
    coordinator = VasttrafikDataUpdateCoordinator(hass, entry, session)
    await coordinator.async_load_cache()
    await coordinator.async_config_entry_first_refresh()

    entry.runtime_data = coordinator
    entry.async_on_unload(entry.add_update_listener(_async_update_listener))

    await hass.config_entries.async_forward_entry_setups(entry, PLATFORMS)
    return True


async def async_unload_entry(hass: HomeAssistant, entry: VasttrafikConfigEntry) -> bool:
    """Unload a config entry."""
    return await hass.config_entries.async_unload_platforms(entry, PLATFORMS)


async def _async_update_listener(hass: HomeAssistant, entry: ConfigEntry) -> None:
    """Handle options update."""
    await hass.config_entries.async_reload(entry.entry_id)
