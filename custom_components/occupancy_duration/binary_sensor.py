"""Binary sensor entities for occupancy-session exposure."""

from __future__ import annotations

from typing import cast

from homeassistant.components.binary_sensor import BinarySensorDeviceClass, BinarySensorEntity
from homeassistant.config_entries import ConfigEntry
from homeassistant.core import HomeAssistant
from homeassistant.helpers.entity_platform import AddConfigEntryEntitiesCallback
from homeassistant.helpers.update_coordinator import CoordinatorEntity

from .const import DATA_COORDINATOR, DOMAIN
from .coordinator import OccupancyDurationCoordinator, RuntimeSnapshot

PARALLEL_UPDATES = 0


async def async_setup_entry(
    hass: HomeAssistant,
    entry: ConfigEntry,
    async_add_entities: AddConfigEntryEntitiesCallback,
) -> None:
    coordinator = hass.data[DOMAIN][entry.entry_id][DATA_COORDINATOR]
    async_add_entities([OccupancyBinarySensor(coordinator, entry)])


class OccupancyBinarySensor(CoordinatorEntity[OccupancyDurationCoordinator], BinarySensorEntity):
    """Binary sensor showing whether an occupancy session is open."""

    _attr_has_entity_name = True
    _attr_name = "Occupancy"
    _attr_device_class = BinarySensorDeviceClass.OCCUPANCY

    def __init__(self, coordinator: OccupancyDurationCoordinator, entry: ConfigEntry) -> None:
        super().__init__(coordinator)
        self._attr_unique_id = f"{entry.entry_id}_occupancy"

    @property
    def is_on(self) -> bool:
        data = cast(RuntimeSnapshot | None, self.coordinator.data)
        session = data.session if data is not None else None
        return bool(session and session.active)