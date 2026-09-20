"""Shared entity metadata helpers for the Occupancy Duration Helper."""

from __future__ import annotations

import re

from homeassistant.config_entries import ConfigEntry
from homeassistant.helpers.device_registry import DeviceEntryType, DeviceInfo
from homeassistant.util import slugify

from .const import DOMAIN

ENTITY_OBJECT_SUFFIXES: dict[str, str] = {
    "duration": "sensor",
    "stage": "sensor",
    "activity_score": "sensor",
    "sensor_strategy": "sensor",
    "last_activity": "sensor",
    "session_started": "sensor",
    "occupancy": "binary_sensor",
}

_LEGACY_OBJECT_ID_RE = re.compile(r"^(?P<object_id>[a-z0-9_]+?)(?:_\d+)?$")


def build_device_info(entry: ConfigEntry) -> DeviceInfo:
    """Return shared device metadata for one helper instance."""
    return DeviceInfo(
        identifiers={(DOMAIN, entry.entry_id)},
        entry_type=DeviceEntryType.SERVICE,
        manufacturer="Occupancy Duration Helper",
        model="Occupancy Session Helper",
        name=entry.title,
    )


def build_suggested_object_id(entry: ConfigEntry, object_suffix: str) -> str:
    """Return a stable, instance-specific suggested object id."""
    return f"{slugify(entry.title)}_{object_suffix}"


def build_entity_id(entry: ConfigEntry, entity_domain: str, object_suffix: str) -> str:
    """Return the preferred entity_id for one helper entity."""
    return f"{entity_domain}.{build_suggested_object_id(entry, object_suffix)}"


def is_legacy_entity_id(entity_id: str, entity_domain: str, object_suffix: str) -> bool:
    """Return whether *entity_id* still uses the old global object-id scheme."""
    if not entity_id.startswith(f"{entity_domain}."):
        return False

    object_id = entity_id.removeprefix(f"{entity_domain}.")
    match = _LEGACY_OBJECT_ID_RE.fullmatch(object_id)
    if match is None:
        return False
    return match.group("object_id") == object_suffix