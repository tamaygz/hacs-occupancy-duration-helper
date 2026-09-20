"""Tests for persistence, restore, and diagnostics helpers."""

from __future__ import annotations

from datetime import UTC, datetime
from unittest.mock import MagicMock

from custom_components.occupancy_duration.coordinator import build_runtime_snapshot
from custom_components.occupancy_duration.const import StrategyMode
from custom_components.occupancy_duration.session import SessionState, start_session
from custom_components.occupancy_duration.storage import deserialize_session, serialize_session


def test_session_serialization_round_trip() -> None:
    session = start_session(datetime(2026, 9, 20, 20, 0, tzinfo=UTC)).session
    restored = deserialize_session(serialize_session(session))
    assert restored == session


def test_unavailable_source_restore_keeps_existing_session_data() -> None:
    session = start_session(datetime(2026, 9, 20, 20, 0, tzinfo=UTC)).session
    restored = deserialize_session(serialize_session(session))
    assert restored is not None
    assert restored.state == SessionState.ACTIVE


def test_runtime_snapshot_contains_restore_and_decay_settings() -> None:
    summary = MagicMock()
    summary.preview_lines = ("Current state available   ✓",)
    snapshot = build_runtime_snapshot(
        entry_id="entry-id",
        source_entity="binary_sensor.motion",
        source_revision=1,
        capability_summary=summary,
        strategy=StrategyMode.AUTO,
        session=None,
        source_state="unknown",
        restore_session=True,
        default_half_life=60,
        end_threshold=5,
        end_grace=15,
        stages=(),
        last_transition_reason="source unavailable during restore; preserved prior session",
    )
    assert snapshot.restore_session is True
    assert snapshot.default_half_life == 60
    assert snapshot.end_threshold == 5
    assert snapshot.end_grace == 15