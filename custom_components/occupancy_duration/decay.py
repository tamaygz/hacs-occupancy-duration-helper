"""Score decay helpers for occupancy sessions."""

from __future__ import annotations

from dataclasses import dataclass

from .const import SCORE_ACTIVITY_INCREMENT, SCORE_MAX, SCORE_MIN
from .stage import DurationStage


@dataclass(frozen=True, slots=True)
class DecayResult:
    """Outcome of a decay evaluation."""

    score: float
    decayed: bool
    reinforced: bool
    applied_half_life: float
    reason: str


def clamp_score(score: float) -> float:
    """Clamp a score to the configured range."""
    return max(SCORE_MIN, min(SCORE_MAX, score))


def apply_exponential_decay(
    score0: float,
    elapsed_seconds: float,
    half_life_seconds: float,
) -> float:
    """Apply restart-safe exponential decay using elapsed wall-clock time."""
    if half_life_seconds <= 0:
        raise ValueError("half_life_seconds must be greater than zero")
    if elapsed_seconds <= 0:
        return clamp_score(score0)

    decayed_score = score0 * (0.5 ** (elapsed_seconds / half_life_seconds))
    return clamp_score(decayed_score)


def reinforce_score(score: float, authoritative: bool = False) -> float:
    """Reinforce activity score.

    Explicit occupancy/presence signals are authoritative and jump directly to
    max score. Motion/event evidence increments up to the configured maximum.
    """
    if authoritative:
        return SCORE_MAX
    return clamp_score(score + SCORE_ACTIVITY_INCREMENT)


def resolve_half_life(
    default_half_life: float,
    stage: DurationStage | None,
) -> float:
    """Resolve the active half-life for the current stage."""
    if stage and stage.decay_half_life is not None:
        return stage.decay_half_life
    return default_half_life


def evaluate_decay(
    score: float,
    elapsed_seconds: float,
    *,
    source_currently_active: bool,
    authoritative_active: bool = False,
    default_half_life: float,
    stage: DurationStage | None = None,
) -> DecayResult:
    """Evaluate one decay tick.

    If the source is still active, decay is suppressed and score is reinforced.
    Otherwise the score decays using the resolved half-life.
    """
    half_life = resolve_half_life(default_half_life, stage)

    if source_currently_active:
        return DecayResult(
            score=reinforce_score(score, authoritative=authoritative_active),
            decayed=False,
            reinforced=True,
            applied_half_life=half_life,
            reason="source still active",
        )

    return DecayResult(
        score=apply_exponential_decay(score, elapsed_seconds, half_life),
        decayed=True,
        reinforced=False,
        applied_half_life=half_life,
        reason="source inactive; decay applied",
    )
