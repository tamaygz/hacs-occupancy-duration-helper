"""Tests for entity-facing helper contracts."""

from __future__ import annotations

from datetime import UTC, datetime
from unittest.mock import MagicMock

from custom_components.occupancy_duration.binary_sensor import OccupancyBinarySensor
from custom_components.occupancy_duration.sensor import OccupancyDurationSensor, OccupancyDurationStageSensor
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
            stage=stage,
            state=session.state,
        )
    coordinator.data = MagicMock(session=session)
    return coordinator


def test_duration_sensor_exposes_expected_attributes() -> None:
    coordinator = _coordinator_with_session(stage="medium")
    entry = MagicMock(entry_id="entry-id")
    sensor = OccupancyDurationSensor(coordinator, entry)

    attrs = sensor.extra_state_attributes
    assert attrs["active"] is True
    assert attrs["stage"] == "medium"
    assert attrs["session_state"] == SessionState.ACTIVE.value
    assert attrs["score"] == 100.0


def test_occupancy_binary_sensor_reflects_open_session() -> None:
    coordinator = _coordinator_with_session()
    entry = MagicMock(entry_id="entry-id")
    sensor = OccupancyBinarySensor(coordinator, entry)
    assert sensor.is_on is True


def test_stage_sensor_returns_stage_name() -> None:
    coordinator = _coordinator_with_session(stage="long")
    entry = MagicMock(entry_id="entry-id")
    sensor = OccupancyDurationStageSensor(coordinator, entry)
    assert sensor.native_value == "long"