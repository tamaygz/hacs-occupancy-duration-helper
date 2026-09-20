"""Sensor entities for occupancy duration and stage exposure."""

from __future__ import annotations

from datetime import UTC, datetime

from homeassistant.components.sensor import SensorDeviceClass, SensorEntity, SensorStateClass
from homeassistant.config_entries import ConfigEntry
from homeassistant.const import UnitOfTime
from homeassistant.core import HomeAssistant
from homeassistant.helpers.entity import EntityCategory
from homeassistant.helpers.entity_platform import AddConfigEntryEntitiesCallback
from homeassistant.helpers.update_coordinator import CoordinatorEntity

from .coordinator import OccupancyDurationCoordinator, RuntimeSnapshot
from .const import (
    ATTR_ACTIVE,
    ATTR_IDLE_DURATION,
    ATTR_LAST_ACTIVITY_AT,
    ATTR_SCORE,
    ATTR_SESSION_STATE,
    ATTR_SOURCE_ENTITY,
    ATTR_STAGE,
    ATTR_STARTED_AT,
    DATA_COORDINATOR,
    DOMAIN,
)
from .entity import build_device_info, build_suggested_object_id

PARALLEL_UPDATES = 0


def _stage_value(session) -> str:
    """Return a stable public stage value for states and attributes."""
    if session is None or session.stage is None:
        return "none"
    return session.stage


async def async_setup_entry(
    hass: HomeAssistant,
    entry: ConfigEntry,
    async_add_entities: AddConfigEntryEntitiesCallback,
) -> None:
    coordinator = hass.data[DOMAIN][entry.entry_id][DATA_COORDINATOR]
    entities: list[SensorEntity] = [
        OccupancyDurationSensor(coordinator, entry),
        OccupancyActivityScoreSensor(coordinator, entry),
        OccupancyStrategySensor(coordinator, entry),
        OccupancyLastActivitySensor(coordinator, entry),
        OccupancySessionStartedSensor(coordinator, entry),
    ]
    if coordinator.data and coordinator.data.stages:
        entities.append(OccupancyDurationStageSensor(coordinator, entry))
    async_add_entities(entities)


class OccupancyBaseEntity(CoordinatorEntity[OccupancyDurationCoordinator]):
    """Shared entity behavior for occupancy helper coordinator entities."""

    _attr_has_entity_name = True
    _attr_should_poll = False

    def __init__(
        self,
        coordinator: OccupancyDurationCoordinator,
        entry: ConfigEntry,
        object_suffix: str,
    ) -> None:
        super().__init__(coordinator)
        self._attr_device_info = build_device_info(entry)
        self._attr_suggested_object_id = build_suggested_object_id(entry, object_suffix)


class OccupancyDurationSensor(OccupancyBaseEntity, SensorEntity):
    """Expose current open-session duration."""

    _attr_name = "Duration"
    _attr_device_class = SensorDeviceClass.DURATION
    _attr_native_unit_of_measurement = UnitOfTime.SECONDS
    _unrecorded_attributes = frozenset({ATTR_STARTED_AT, ATTR_LAST_ACTIVITY_AT})

    def __init__(self, coordinator: OccupancyDurationCoordinator, entry: ConfigEntry) -> None:
        super().__init__(coordinator, entry, "duration")
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
        now = datetime.now(UTC)
        idle = (
            int((now - session.last_activity_at).total_seconds())
            if session and not session.active
            else 0
        )
        return {
            ATTR_ACTIVE: bool(session and session.active),
            ATTR_STARTED_AT: session.started_at.isoformat() if session else None,
            ATTR_LAST_ACTIVITY_AT: session.last_activity_at.isoformat() if session else None,
            ATTR_STAGE: _stage_value(session),
            ATTR_SESSION_STATE: session.state.value if session else "idle",
            ATTR_SCORE: round(session.score, 1) if session else 0,
            ATTR_SOURCE_ENTITY: data.source_entity if data is not None else None,
            ATTR_IDLE_DURATION: idle,
        }


class OccupancyDurationStageSensor(OccupancyBaseEntity, SensorEntity):
    """Expose the current stage for an open session."""

    _attr_name = "Stage"

    def __init__(self, coordinator: OccupancyDurationCoordinator, entry: ConfigEntry) -> None:
        super().__init__(coordinator, entry, "stage")
        self._attr_unique_id = f"{entry.entry_id}_stage"

    @property
    def native_value(self) -> str | None:
        data: RuntimeSnapshot | None = self.coordinator.data
        session = data.session if data is not None else None
        return _stage_value(session)


class OccupancyActivityScoreSensor(OccupancyBaseEntity, SensorEntity):
    """Diagnostic: exposes the raw activity score (0–100). Disabled by default."""

    _attr_name = "Activity score"
    _attr_native_unit_of_measurement = "%"
    _attr_state_class = SensorStateClass.MEASUREMENT
    _attr_entity_category = EntityCategory.DIAGNOSTIC
    _attr_entity_registry_enabled_default = False

    def __init__(self, coordinator: OccupancyDurationCoordinator, entry: ConfigEntry) -> None:
        super().__init__(coordinator, entry, "activity_score")
        self._attr_unique_id = f"{entry.entry_id}_activity_score"

    @property
    def native_value(self) -> float | None:
        data: RuntimeSnapshot | None = self.coordinator.data
        session = data.session if data is not None else None
        return round(session.score, 1) if session else 0.0


class OccupancyStrategySensor(OccupancyBaseEntity, SensorEntity):
    """Diagnostic: exposes the active sensor strategy. Disabled by default."""

    _attr_name = "Sensor strategy"
    _attr_entity_category = EntityCategory.DIAGNOSTIC
    _attr_entity_registry_enabled_default = False

    def __init__(self, coordinator: OccupancyDurationCoordinator, entry: ConfigEntry) -> None:
        super().__init__(coordinator, entry, "sensor_strategy")
        self._attr_unique_id = f"{entry.entry_id}_sensor_strategy"

    @property
    def native_value(self) -> str | None:
        data: RuntimeSnapshot | None = self.coordinator.data
        return data.strategy.value if data is not None else None


class OccupancyLastActivitySensor(OccupancyBaseEntity, SensorEntity):
    """Diagnostic: timestamp of the last recorded activity. Disabled by default."""

    _attr_name = "Last activity"
    _attr_device_class = SensorDeviceClass.TIMESTAMP
    _attr_entity_category = EntityCategory.DIAGNOSTIC
    _attr_entity_registry_enabled_default = False

    def __init__(self, coordinator: OccupancyDurationCoordinator, entry: ConfigEntry) -> None:
        super().__init__(coordinator, entry, "last_activity")
        self._attr_unique_id = f"{entry.entry_id}_last_activity"

    @property
    def native_value(self) -> datetime | None:
        data: RuntimeSnapshot | None = self.coordinator.data
        session = data.session if data is not None else None
        return session.last_activity_at if session else None


class OccupancySessionStartedSensor(OccupancyBaseEntity, SensorEntity):
    """Diagnostic: timestamp when the current session started. Disabled by default."""

    _attr_name = "Session started"
    _attr_device_class = SensorDeviceClass.TIMESTAMP
    _attr_entity_category = EntityCategory.DIAGNOSTIC
    _attr_entity_registry_enabled_default = False

    def __init__(self, coordinator: OccupancyDurationCoordinator, entry: ConfigEntry) -> None:
        super().__init__(coordinator, entry, "session_started")
        self._attr_unique_id = f"{entry.entry_id}_session_started"

    @property
    def native_value(self) -> datetime | None:
        data: RuntimeSnapshot | None = self.coordinator.data
        session = data.session if data is not None else None
        # Only show a value while the session is open; clear after closure.
        return session.started_at if (session and session.active) else None