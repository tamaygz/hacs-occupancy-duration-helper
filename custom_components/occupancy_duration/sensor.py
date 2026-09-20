"""Sensor entities for occupancy duration and stage exposure."""

from __future__ import annotations

from datetime import UTC, datetime

from homeassistant.components.sensor import SensorDeviceClass, SensorEntity
from homeassistant.config_entries import ConfigEntry
from homeassistant.const import UnitOfTime
from homeassistant.core import HomeAssistant
from homeassistant.helpers.entity_platform import AddConfigEntryEntitiesCallback
from homeassistant.helpers.update_coordinator import CoordinatorEntity

from .coordinator import OccupancyDurationCoordinator, RuntimeSnapshot
from .const import (
    ATTR_ACTIVE,
    ATTR_LAST_ACTIVITY_AT,
    ATTR_SCORE,
    ATTR_SESSION_STATE,
    ATTR_STAGE,
    ATTR_STARTED_AT,
    DATA_COORDINATOR,
    DOMAIN,
)
from .coordinator import OccupancyDurationCoordinator, RuntimeSnapshot

PARALLEL_UPDATES = 0


async def async_setup_entry(
    hass: HomeAssistant,
    entry: ConfigEntry,
    async_add_entities: AddConfigEntryEntitiesCallback,
) -> None:
    coordinator = hass.data[DOMAIN][entry.entry_id][DATA_COORDINATOR]
    entities: list[SensorEntity] = [OccupancyDurationSensor(coordinator, entry)]
    if coordinator.data and coordinator.data.stages:
        entities.append(OccupancyDurationStageSensor(coordinator, entry))
    async_add_entities(entities)


class OccupancyBaseEntity(CoordinatorEntity[OccupancyDurationCoordinator]):
    """Shared entity behavior for occupancy helper coordinator entities."""

    _attr_has_entity_name = True

    @property
    def available(self) -> bool:
        return self.coordinator.data is not None


class OccupancyDurationSensor(OccupancyBaseEntity, SensorEntity):
    """Expose current open-session duration."""

    _attr_name = "Duration"
    _attr_device_class = SensorDeviceClass.DURATION
    _attr_native_unit_of_measurement = UnitOfTime.SECONDS
    _unrecorded_attributes = frozenset({ATTR_STARTED_AT, ATTR_LAST_ACTIVITY_AT})

    def __init__(self, coordinator: OccupancyDurationCoordinator, entry: ConfigEntry) -> None:
        super().__init__(coordinator)
        self._attr_unique_id = f"{entry.entry_id}_duration"

    @property
    def native_value(self) -> int | None:
        data: RuntimeSnapshot | None = self.coordinator.data
        session = data.session if data is not None else None
        if session is None or not session.active:
            return 0
        return int(session.duration_seconds(datetime.now(UTC)))

    @property
    def extra_state_attributes(self) -> dict[str, object]:
        data: RuntimeSnapshot | None = self.coordinator.data
        session = data.session if data is not None else None
        return {
            ATTR_ACTIVE: bool(session and session.active),
            ATTR_STARTED_AT: session.started_at.isoformat() if session else None,
            ATTR_LAST_ACTIVITY_AT: session.last_activity_at.isoformat() if session else None,
            ATTR_STAGE: session.stage if session else None,
            ATTR_SESSION_STATE: session.state.value if session else "idle",
            ATTR_SCORE: session.score if session else 0,
        }


class OccupancyDurationStageSensor(OccupancyBaseEntity, SensorEntity):
    """Expose the current stage for an open session."""

    _attr_name = "Stage"

    def __init__(self, coordinator: OccupancyDurationCoordinator, entry: ConfigEntry) -> None:
        super().__init__(coordinator)
        self._attr_unique_id = f"{entry.entry_id}_stage"

    @property
    def native_value(self) -> str | None:
        data: RuntimeSnapshot | None = self.coordinator.data
        session = data.session if data is not None else None
        return session.stage if session else None