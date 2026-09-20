"""Tests for occupancy score decay behavior."""

from __future__ import annotations

from custom_components.occupancy_duration.decay import (
    apply_exponential_decay,
    evaluate_decay,
    reinforce_score,
    resolve_half_life,
)
from custom_components.occupancy_duration.stage import DurationStage


def test_apply_exponential_decay_reduces_score_over_time() -> None:
    decayed = apply_exponential_decay(100.0, elapsed_seconds=60, half_life_seconds=60)
    assert decayed == 50.0


def test_reinforce_score_caps_at_max() -> None:
    assert reinforce_score(95.0) == 100.0
    assert reinforce_score(5.0, authoritative=True) == 100.0


def test_active_source_prevents_decay() -> None:
    result = evaluate_decay(
        40.0,
        elapsed_seconds=120,
        source_currently_active=True,
        authoritative_active=False,
        default_half_life=60.0,
    )
    assert result.decayed is False
    assert result.reinforced is True
    assert result.score > 40.0


def test_inactive_source_decays() -> None:
    result = evaluate_decay(
        80.0,
        elapsed_seconds=60,
        source_currently_active=False,
        authoritative_active=False,
        default_half_life=60.0,
    )
    assert result.decayed is True
    assert result.reinforced is False
    assert result.score == 40.0


def test_stage_specific_half_life_is_used() -> None:
    stage = DurationStage("long", "Long", 180, None, 180)
    assert resolve_half_life(60.0, stage) == 180


def test_event_only_style_decay_uses_default_half_life() -> None:
    result = evaluate_decay(
        100.0,
        elapsed_seconds=60,
        source_currently_active=False,
        authoritative_active=False,
        default_half_life=120.0,
        stage=None,
    )
    assert result.applied_half_life == 120.0
    assert result.score == apply_exponential_decay(100.0, 60, 120.0)
