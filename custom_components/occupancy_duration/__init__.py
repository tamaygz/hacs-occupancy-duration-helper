"""Occupancy Duration Helper integration."""

from __future__ import annotations

import logging

from homeassistant.config_entries import ConfigEntry
from homeassistant.core import HomeAssistant
from homeassistant.helpers import entity_registry as er
from homeassistant.helpers.entity_registry import RegistryEntryDisabler

from .const import DATA_COORDINATOR, DOMAIN, PLATFORMS
from .coordinator import OccupancyDurationCoordinator
from .entity import ENTITY_OBJECT_SUFFIXES, build_entity_id, is_legacy_entity_id

_LOGGER = logging.getLogger(__name__)
_DIAGNOSTIC_OBJECT_SUFFIXES = (
    "activity_score",
    "sensor_strategy",
    "last_activity",
    "session_started",
)


async def async_setup_entry(hass: HomeAssistant, entry: ConfigEntry) -> bool:
    """Set up Occupancy Duration Helper from a config entry."""
    _async_migrate_legacy_entity_ids(hass, entry)
    _async_enable_diagnostic_entities(hass, entry)

    coordinator = OccupancyDurationCoordinator(hass, entry)
    await coordinator.async_initialize()

    hass.data.setdefault(DOMAIN, {})[entry.entry_id] = {DATA_COORDINATOR: coordinator}
    await hass.config_entries.async_forward_entry_setups(entry, PLATFORMS)
    entry.async_on_unload(entry.add_update_listener(_async_update_listener))
    return True


async def async_unload_entry(hass: HomeAssistant, entry: ConfigEntry) -> bool:
    """Unload an Occupancy Duration Helper config entry."""
    unload_ok = await hass.config_entries.async_unload_platforms(entry, PLATFORMS)
    runtime = hass.data.get(DOMAIN, {}).get(entry.entry_id)
    if runtime:
        coordinator = runtime[DATA_COORDINATOR]
        await coordinator.async_shutdown()
        hass.data[DOMAIN].pop(entry.entry_id, None)
    return unload_ok


async def _async_update_listener(hass: HomeAssistant, entry: ConfigEntry) -> None:
    """Reload the entry when options change."""
    await hass.config_entries.async_reload(entry.entry_id)


def _async_migrate_legacy_entity_ids(hass: HomeAssistant, entry: ConfigEntry) -> None:
    """Rename pre-device-era entity ids to instance-specific ids."""
    ent_reg = er.async_get(hass)

    for object_suffix, entity_domain in ENTITY_OBJECT_SUFFIXES.items():
        unique_id = f"{entry.entry_id}_{object_suffix}"
        current_entity_id = ent_reg.async_get_entity_id(entity_domain, DOMAIN, unique_id)
        if current_entity_id is None:
            continue

        if not is_legacy_entity_id(current_entity_id, entity_domain, object_suffix):
            continue

        preferred_entity_id = build_entity_id(entry, entity_domain, object_suffix)
        if current_entity_id == preferred_entity_id:
            continue
        if ent_reg.async_get(preferred_entity_id) is not None:
            _LOGGER.warning(
                "Cannot migrate %s to %s because the target entity_id already exists",
                current_entity_id,
                preferred_entity_id,
            )
            continue

        try:
            ent_reg.async_update_entity(current_entity_id, new_entity_id=preferred_entity_id)
        except ValueError:
            _LOGGER.warning(
                "Failed to migrate %s to %s",
                current_entity_id,
                preferred_entity_id,
                exc_info=True,
            )


def _async_enable_diagnostic_entities(hass: HomeAssistant, entry: ConfigEntry) -> None:
    """Re-enable diagnostic entities that older versions created as disabled."""
    ent_reg = er.async_get(hass)

    for object_suffix in _DIAGNOSTIC_OBJECT_SUFFIXES:
        entity_domain = ENTITY_OBJECT_SUFFIXES[object_suffix]
        entity_id = ent_reg.async_get_entity_id(
            entity_domain,
            DOMAIN,
            f"{entry.entry_id}_{object_suffix}",
        )
        if entity_id is None:
            continue

        entry_record = ent_reg.async_get(entity_id)
        if entry_record is None or entry_record.disabled_by != RegistryEntryDisabler.INTEGRATION:
            continue

        ent_reg.async_update_entity(entity_id, disabled_by=None)