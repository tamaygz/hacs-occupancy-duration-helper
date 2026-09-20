"""Tests for entity-facing helper contracts."""

from __future__ import annotations

from datetime import UTC, datetime
from unittest.mock import MagicMock

from custom_components.occupancy_duration.binary_sensor import OccupancyBinarySensor
from custom_components.occupancy_duration.const import DOMAIN
from custom_components.occupancy_duration.sensor import (
    OccupancyActivityScoreSensor,
    OccupancyDurationSensor,
    OccupancyDurationStageSensor,
    OccupancyLastActivitySensor,
    OccupancySessionStartedSensor,
    OccupancyStrategySensor,
)
from custom_components.occupancy_duration.session import SessionState, start_session


def _coordinator_with_session(stage: str | None = None):
    coordinator = MagicMock()
    started = datetime(2026, 9, 20, 20, 0, tzinfo=UTC)
    session = start_session(started).session
    if stage is not None:
        session = session.__class__(
            id=session.id,
            started_at=session.started_at,
            last_activity_at=session.last_activity_at,
            last_active_signal_at=session.last_active_signal_at,
            ended_at=session.ended_at,
            score=session.score,
            decay_anchor_at=session.decay_anchor_at,
            decay_anchor_score=session.decay_anchor_score,
            stage=stage,
            state=session.state,
        )
    coordinator.data = MagicMock(session=session)
    return coordinator


def test_duration_sensor_exposes_expected_attributes() -> None:
    coordinator = _coordinator_with_session(stage="medium")
    entry = MagicMock(entry_id="entry-id", title="Bathroom")
    sensor = OccupancyDurationSensor(coordinator, entry)

    attrs = sensor.extra_state_attributes
    assert attrs["active"] is True
    assert attrs["stage"] == "medium"
    assert attrs["session_state"] == SessionState.ACTIVE.value
    assert attrs["score"] == 100.0


def test_occupancy_binary_sensor_reflects_open_session() -> None:
    coordinator = _coordinator_with_session()
    entry = MagicMock(entry_id="entry-id", title="Bathroom")
    sensor = OccupancyBinarySensor(coordinator, entry)
    assert sensor.is_on is True


def test_stage_sensor_returns_stage_name() -> None:
    coordinator = _coordinator_with_session(stage="long")
    entry = MagicMock(entry_id="entry-id", title="Bathroom")
    sensor = OccupancyDurationStageSensor(coordinator, entry)
    assert sensor.native_value == "long"


def test_duration_sensor_reports_none_when_no_stage_is_active() -> None:
    coordinator = _coordinator_with_session()
    entry = MagicMock(entry_id="entry-id", title="Bathroom")
    sensor = OccupancyDurationSensor(coordinator, entry)

    assert sensor.extra_state_attributes["stage"] == "none"


def test_stage_sensor_reports_none_before_a_stage_is_reached() -> None:
    coordinator = _coordinator_with_session()
    entry = MagicMock(entry_id="entry-id", title="Bathroom")
    sensor = OccupancyDurationStageSensor(coordinator, entry)

    assert sensor.native_value == "none"


def test_entities_expose_shared_device_info() -> None:
    coordinator = _coordinator_with_session()
    entry = MagicMock(entry_id="entry-id", title="Bathroom")

    duration = OccupancyDurationSensor(coordinator, entry)
    occupancy = OccupancyBinarySensor(coordinator, entry)

    assert duration.device_info is not None
    assert occupancy.device_info is not None

    assert duration.device_info["identifiers"] == {(DOMAIN, "entry-id")}
    assert occupancy.device_info["identifiers"] == {(DOMAIN, "entry-id")}


def test_diagnostic_sensors_are_enabled_and_populated_by_default() -> None:
    coordinator = _coordinator_with_session(stage="long")
    coordinator.data.strategy = MagicMock(value="continuous_motion")
    entry = MagicMock(entry_id="entry-id", title="Bathroom")

    activity = OccupancyActivityScoreSensor(coordinator, entry)
    strategy = OccupancyStrategySensor(coordinator, entry)
    last_activity = OccupancyLastActivitySensor(coordinator, entry)
    session_started = OccupancySessionStartedSensor(coordinator, entry)

    assert activity.entity_registry_enabled_default is True
    assert strategy.entity_registry_enabled_default is True
    assert last_activity.entity_registry_enabled_default is True
    assert session_started.entity_registry_enabled_default is True
    assert activity.native_value == 100.0
    assert strategy.native_value == "continuous_motion"
    assert last_activity.native_value is not None
    assert session_started.native_value is not None