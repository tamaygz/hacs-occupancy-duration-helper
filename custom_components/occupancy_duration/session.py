"""Occupancy session state machine and coordinator-facing evaluation contract."""

from __future__ import annotations

from dataclasses import dataclass, replace
from datetime import UTC, datetime, timedelta
from enum import StrEnum
from uuid import uuid4

from .const import DEFAULT_END_GRACE, DEFAULT_END_THRESHOLD, SCORE_MAX
from .decay import DecayResult, evaluate_decay, reinforce_score
from .stage import DurationStage, resolve_stage


class SessionState(StrEnum):
    """Explicit occupancy-session lifecycle states."""

    IDLE = "idle"
    ACTIVE = "active"
    DECAYING = "decaying"
    ENDING = "ending"
    CLOSED = "closed"


@dataclass(frozen=True, slots=True)
class OccupancySession:
    """Immutable occupancy session state."""

    id: str
    started_at: datetime
    last_activity_at: datetime
    last_active_signal_at: datetime | None
    ended_at: datetime | None
    score: float
    decay_anchor_at: datetime | None
    decay_anchor_score: float | None
    stage: str | None
    state: SessionState

    @property
    def active(self) -> bool:
        """Return whether the session is still open."""
        return self.state in {
            SessionState.ACTIVE,
            SessionState.DECAYING,
            SessionState.ENDING,
        }

    def duration_seconds(self, now: datetime) -> float:
        """Return the wall-clock session duration."""
        return max(0.0, (now - self.started_at).total_seconds())


@dataclass(frozen=True, slots=True)
class SessionTransition:
    """One state-machine step and its result."""

    session: OccupancySession
    previous_state: SessionState
    reason: str
    changed: bool = True
    decay_result: DecayResult | None = None


@dataclass(frozen=True, slots=True)
class SessionEvaluationInput:
    """Coordinator-facing input bundle for a single decay-tick evaluation."""

    now: datetime
    source_currently_active: bool
    authoritative_active: bool
    elapsed_since_last_activity: float
    default_half_life: float
    end_threshold: float = DEFAULT_END_THRESHOLD
    end_grace_seconds: int = DEFAULT_END_GRACE
    stages: tuple[DurationStage, ...] = ()


def _utc_now() -> datetime:
    return datetime.now(UTC)


def _resolve_stage_id(
    session: OccupancySession,
    now: datetime,
    stages: tuple[DurationStage, ...],
) -> str | None:
    stage = resolve_stage(session.duration_seconds(now), list(stages), session.stage)
    return stage.id if stage else session.stage


def start_session(
    now: datetime | None = None,
    *,
    score: float = SCORE_MAX,
    stage_id: str | None = None,
    session_id: str | None = None,
) -> SessionTransition:
    """Create a new ACTIVE session."""
    current_time = now or _utc_now()
    session = OccupancySession(
        id=session_id or str(uuid4()),
        started_at=current_time,
        last_activity_at=current_time,
        last_active_signal_at=current_time,
        ended_at=None,
        score=score,
        decay_anchor_at=None,
        decay_anchor_score=None,
        stage=stage_id,
        state=SessionState.ACTIVE,
    )
    return SessionTransition(
        session=session,
        previous_state=SessionState.IDLE,
        reason="activity detected; new session started",
    )


def activity_detected(
    session: OccupancySession | None,
    now: datetime,
    *,
    authoritative: bool = False,
    stages: tuple[DurationStage, ...] = (),
) -> SessionTransition:
    """Start or reinforce a session without resetting started_at."""
    if session is None or session.state in {SessionState.CLOSED, SessionState.IDLE}:
        return start_session(now, score=SCORE_MAX if authoritative else reinforce_score(0.0))

    updated = replace(
        session,
        last_activity_at=now,
        last_active_signal_at=now,
        score=reinforce_score(session.score, authoritative=authoritative),
        decay_anchor_at=None,
        decay_anchor_score=None,
        stage=_resolve_stage_id(session, now, stages),
        state=SessionState.ACTIVE,
        ended_at=None,
    )
    return SessionTransition(
        session=updated,
        previous_state=session.state,
        reason="activity detected; existing session reinforced",
    )


def source_became_inactive(
    session: OccupancySession,
    now: datetime | None = None,
) -> SessionTransition:
    """Move an open session into DECAYING when source activity stops."""
    if session.state in {SessionState.CLOSED, SessionState.IDLE}:
        return SessionTransition(
            session=session,
            previous_state=session.state,
            reason="inactive signal ignored for closed/idle session",
            changed=False,
        )

    updated = replace(
        session,
        state=SessionState.DECAYING,
        decay_anchor_at=now or _utc_now(),
        decay_anchor_score=session.score,
    )
    return SessionTransition(
        session=updated,
        previous_state=session.state,
        reason="source no longer active; session decaying",
    )


def decay_tick(
    session: OccupancySession,
    evaluation: SessionEvaluationInput,
) -> SessionTransition:
    """Evaluate one decay tick for an existing session."""
    if evaluation.source_currently_active:
        if session.state == SessionState.ACTIVE:
            updated = replace(
                session,
                stage=_resolve_stage_id(session, evaluation.now, evaluation.stages),
                decay_anchor_at=None,
                decay_anchor_score=None,
            )
            return SessionTransition(
                session=updated,
                previous_state=session.state,
                reason="source still active; session heartbeat",
                changed=updated != session,
                decay_result=DecayResult(
                    score=updated.score,
                    decayed=False,
                    reinforced=False,
                    applied_half_life=evaluation.default_half_life,
                    reason="source still active",
                ),
            )

        updated = replace(
            session,
            last_activity_at=evaluation.now,
            last_active_signal_at=evaluation.now,
            score=reinforce_score(session.score, authoritative=evaluation.authoritative_active),
            decay_anchor_at=None,
            decay_anchor_score=None,
            stage=_resolve_stage_id(session, evaluation.now, evaluation.stages),
            state=SessionState.ACTIVE,
            ended_at=None,
        )
        return SessionTransition(
            session=updated,
            previous_state=session.state,
            reason="source active during decay tick; session reinforced",
            decay_result=DecayResult(
                score=updated.score,
                decayed=False,
                reinforced=True,
                applied_half_life=evaluation.default_half_life,
                reason="source still active",
            ),
        )

    decay_anchor_at = session.decay_anchor_at or session.last_active_signal_at or session.last_activity_at
    decay_anchor_score = (
        session.decay_anchor_score if session.decay_anchor_score is not None else session.score
    )
    decay_result = evaluate_decay(
        decay_anchor_score,
        max(0.0, (evaluation.now - decay_anchor_at).total_seconds()),
        source_currently_active=evaluation.source_currently_active,
        authoritative_active=evaluation.authoritative_active,
        default_half_life=evaluation.default_half_life,
        stage=resolve_stage(
            session.duration_seconds(evaluation.now),
            list(evaluation.stages),
            session.stage,
        ),
    )

    next_state = (
        SessionState.ENDING
        if decay_result.score <= evaluation.end_threshold
        else SessionState.DECAYING
    )
    updated = replace(
        session,
        score=decay_result.score,
        decay_anchor_at=decay_anchor_at,
        decay_anchor_score=decay_anchor_score,
        stage=_resolve_stage_id(session, evaluation.now, evaluation.stages),
        state=next_state,
    )
    return SessionTransition(
        session=updated,
        previous_state=session.state,
        reason=(
            "score below threshold; session entering ending state"
            if next_state == SessionState.ENDING
            else "source inactive; decay applied"
        ),
        decay_result=decay_result,
    )


def grace_expired(
    session: OccupancySession,
    now: datetime,
    *,
    end_grace_seconds: int = DEFAULT_END_GRACE,
) -> SessionTransition:
    """Close an ENDING session once its grace window has elapsed."""
    if session.state != SessionState.ENDING:
        return SessionTransition(
            session=session,
            previous_state=session.state,
            reason="grace-expiry check ignored outside ending state",
            changed=False,
        )

    # Use last_activity_at as the anchor for grace expiry.
    expires_at = session.last_activity_at + timedelta(seconds=end_grace_seconds)
    if now < expires_at:
        return SessionTransition(
            session=session,
            previous_state=session.state,
            reason="ending grace still active",
            changed=False,
        )

    updated = replace(session, state=SessionState.CLOSED, ended_at=now)
    return SessionTransition(
        session=updated,
        previous_state=session.state,
        reason="ending grace expired; session closed",
    )
