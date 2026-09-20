"""Tests for occupancy session state transitions."""

from __future__ import annotations

from datetime import UTC, datetime, timedelta

from custom_components.occupancy_duration.session import (
    SessionEvaluationInput,
    SessionState,
    activity_detected,
    decay_tick,
    grace_expired,
    source_became_inactive,
    start_session,
)
from custom_components.occupancy_duration.stage import DurationStage


def _now() -> datetime:
    return datetime(2026, 9, 20, 20, 0, tzinfo=UTC)


def test_activity_starts_session() -> None:
    transition = start_session(_now())
    assert transition.session.state == SessionState.ACTIVE
    assert transition.session.started_at == _now()


def test_reinforcement_does_not_reset_started_at() -> None:
    started = _now()
    session = start_session(started).session
    later = started + timedelta(seconds=90)

    transition = activity_detected(session, later)

    assert transition.session.started_at == started
    assert transition.session.last_activity_at == later
    assert transition.session.state == SessionState.ACTIVE


def test_source_inactive_moves_session_to_decaying() -> None:
    session = start_session(_now()).session
    transition = source_became_inactive(session)
    assert transition.session.state == SessionState.DECAYING


def test_activity_during_decay_returns_to_active() -> None:
    started = _now()
    decaying = source_became_inactive(start_session(started).session).session
    later = started + timedelta(seconds=45)

    transition = activity_detected(decaying, later)

    assert transition.session.state == SessionState.ACTIVE
    assert transition.session.started_at == started


def test_decay_tick_below_threshold_enters_ending() -> None:
    started = _now()
    session = source_became_inactive(start_session(started, score=10.0).session).session
    transition = decay_tick(
        session,
        SessionEvaluationInput(
            now=started + timedelta(seconds=60),
            source_currently_active=False,
            authoritative_active=False,
            elapsed_since_last_activity=60.0,
            default_half_life=60.0,
            end_threshold=5.0,
        ),
    )
    assert transition.session.state == SessionState.ENDING
    assert transition.session.score <= 5.0


def test_grace_expiry_closes_session() -> None:
    started = _now()
    session = start_session(started).session
    ending = decay_tick(
        source_became_inactive(session).session,
        SessionEvaluationInput(
            now=started + timedelta(seconds=120),
            source_currently_active=False,
            authoritative_active=False,
            elapsed_since_last_activity=120.0,
            default_half_life=60.0,
            end_threshold=30.0,
        ),
    ).session

    closed = grace_expired(ending, started + timedelta(seconds=200), end_grace_seconds=15)
    assert closed.session.state == SessionState.CLOSED
    assert closed.session.ended_at == started + timedelta(seconds=200)


def test_new_session_starts_after_closure() -> None:
    first = start_session(_now()).session
    ending = decay_tick(
        source_became_inactive(first).session,
        SessionEvaluationInput(
            now=_now() + timedelta(seconds=300),
            source_currently_active=False,
            authoritative_active=False,
            elapsed_since_last_activity=300.0,
            default_half_life=60.0,
            end_threshold=90.0,
        ),
    ).session
    closed = grace_expired(ending, _now() + timedelta(seconds=400), end_grace_seconds=15).session

    restarted = activity_detected(closed, _now() + timedelta(seconds=500)).session

    assert restarted.id != first.id
    assert restarted.started_at == _now() + timedelta(seconds=500)
    assert restarted.state == SessionState.ACTIVE


def test_stage_progresses_without_regressing_during_reinforcement() -> None:
    stages = (
        DurationStage("short", "Short", 0, 60, 30),
        DurationStage("medium", "Medium", 60, 180, 60),
        DurationStage("long", "Long", 180, None, 180),
    )
    started = _now()
    session = start_session(started).session

    medium = activity_detected(session, started + timedelta(seconds=90), stages=stages).session
    assert medium.stage == "medium"

    long_session = activity_detected(medium, started + timedelta(seconds=240), stages=stages).session
    assert long_session.stage == "long"

    reinforced = activity_detected(long_session, started + timedelta(seconds=245), stages=stages).session
    assert reinforced.stage == "long"
