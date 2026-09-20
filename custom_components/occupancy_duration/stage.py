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

    # Single pass: find the matching stage and track the last candidate for the
    # gap/fallback case without a second iteration.
    matched: DurationStage | None = None
    last_eligible: DurationStage | None = None
    current_index: int | None = None

    for index, stage in enumerate(stages):
        if stage.id == current_stage_id:
            current_index = index
        if stage.min_duration <= duration_seconds:
            last_eligible = stage
        if stage.contains(duration_seconds) and matched is None:
            matched = stage

    resolved = matched if matched is not None else last_eligible

    if resolved is None or current_stage_id is None:
        return resolved

    resolved_index = next(
        (i for i, s in enumerate(stages) if s.id == resolved.id),
        None,
    )
    if current_index is not None and resolved_index is not None and resolved_index < current_index:
        return stages[current_index]
    return resolved


def get_stage_by_id(stage_id: str | None, stages: list[DurationStage]) -> DurationStage | None:
    """Return the configured stage by ID."""
    if stage_id is None:
        return None
    return next((stage for stage in stages if stage.id == stage_id), None)
