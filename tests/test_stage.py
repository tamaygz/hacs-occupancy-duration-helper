"""Tests for duration stage resolution."""

from __future__ import annotations

from custom_components.occupancy_duration.stage import (
    DurationStage,
    get_stage_by_id,
    resolve_stage,
    validate_stages,
)


def _stages() -> list[DurationStage]:
    return [
        DurationStage("short", "Short", 0, 60, 30),
        DurationStage("medium", "Medium", 60, 180, 60),
        DurationStage("long", "Long", 180, None, 180),
    ]


def test_validate_stages_accepts_ordered_non_overlapping_ranges() -> None:
    validate_stages(_stages())


def test_validate_stages_rejects_overlap() -> None:
    stages = [
        DurationStage("short", "Short", 0, 60, 30),
        DurationStage("medium", "Medium", 30, 180, 60),
    ]
    try:
        validate_stages(stages)
    except ValueError as err:
        assert "overlap" in str(err)
    else:
        raise AssertionError("expected overlap validation failure")


def test_resolve_stage_matches_duration_bucket() -> None:
    short_stage = resolve_stage(10, _stages())
    medium_stage = resolve_stage(90, _stages())
    long_stage = resolve_stage(240, _stages())

    assert short_stage is not None and short_stage.id == "short"
    assert medium_stage is not None and medium_stage.id == "medium"
    assert long_stage is not None and long_stage.id == "long"


def test_stage_progression_is_monotonic() -> None:
    stages = _stages()
    progressed = resolve_stage(200, stages, current_stage_id="medium")
    preserved = resolve_stage(20, stages, current_stage_id="long")

    assert progressed is not None and progressed.id == "long"
    assert preserved is not None and preserved.id == "long"


def test_get_stage_by_id_returns_expected_stage() -> None:
    stage = get_stage_by_id("medium", _stages())
    assert stage is not None
    assert stage.name == "Medium"
