"""Duration stage models and helpers."""

from __future__ import annotations

from dataclasses import dataclass


@dataclass(frozen=True, slots=True)
class DurationStage:
    """One user-defined duration bucket for an occupancy session."""

    id: str
    name: str
    min_duration: int
    max_duration: int | None
    decay_half_life: float | None = None

    def contains(self, duration_seconds: float) -> bool:
        """Return whether *duration_seconds* belongs to this stage."""
        if duration_seconds < self.min_duration:
            return False
        if self.max_duration is None:
            return True
        return duration_seconds < self.max_duration


def validate_stages(stages: list[DurationStage]) -> None:
    """Validate stage ordering and range sanity.

    Stages may be contiguous or non-overlapping, but they must be ordered by
    increasing minimum duration.
    """
    previous_min: int | None = None
    previous_max: int | None = None

    for stage in stages:
        if stage.min_duration < 0:
            raise ValueError(f"Stage {stage.id!r} cannot have a negative minimum duration")
        if stage.max_duration is not None and stage.max_duration <= stage.min_duration:
            raise ValueError(
                f"Stage {stage.id!r} must have max_duration greater than min_duration"
            )
        if previous_min is not None and stage.min_duration < previous_min:
            raise ValueError("Stages must be ordered by increasing min_duration")
        if previous_max is not None and stage.min_duration < previous_max:
            raise ValueError("Stages must not overlap")

        previous_min = stage.min_duration
        previous_max = stage.max_duration


def resolve_stage(
    duration_seconds: float,
    stages: list[DurationStage],
    current_stage_id: str | None = None,
) -> DurationStage | None:
    """Resolve the current stage for *duration_seconds*.

    Monotonicity is enforced by never returning a stage that appears earlier in
    the configured order than *current_stage_id*.
    """
    if not stages:
        return None

    # validate_stages is O(n) and called on every decode-tick; callers that build
    # stages from persisted config validate once at config load.
    matched: DurationStage | None = None
    for stage in stages:
        if stage.contains(duration_seconds):
            matched = stage
            break

    if matched is None:
        # Duration is before the first stage or in a deliberate gap; return the
        # highest-min stage that does not exceed duration_seconds.
        candidates = [s for s in stages if s.min_duration <= duration_seconds]
        return candidates[-1] if candidates else None

    if current_stage_id is None:
        return matched

    current_index = next(
        (index for index, stage in enumerate(stages) if stage.id == current_stage_id),
        None,
    )
    matched_index = next(
        (index for index, stage in enumerate(stages) if stage.id == matched.id),
        None,
    )

    if current_index is None or matched_index is None:
        return matched

    if matched_index < current_index:
        return stages[current_index]

    return matched


def get_stage_by_id(stage_id: str | None, stages: list[DurationStage]) -> DurationStage | None:
    """Return the configured stage by ID."""
    if stage_id is None:
        return None
    return next((stage for stage in stages if stage.id == stage_id), None)
