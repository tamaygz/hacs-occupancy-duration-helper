"""Tests for shared entity metadata helpers."""

from __future__ import annotations

from unittest.mock import MagicMock

from custom_components.occupancy_duration.entity import (
    build_entity_id,
    build_suggested_object_id,
    is_legacy_entity_id,
)


def test_build_suggested_object_id_uses_helper_title() -> None:
    entry = MagicMock(title="Westwing Toilet Occupancy Duration")

    assert build_suggested_object_id(entry, "duration") == "westwing_toilet_occupancy_duration_duration"


def test_build_entity_id_is_instance_specific() -> None:
    entry = MagicMock(title="Westwing Toilet Occupancy Duration")

    assert (
        build_entity_id(entry, "binary_sensor", "occupancy")
        == "binary_sensor.westwing_toilet_occupancy_duration_occupancy"
    )


def test_is_legacy_entity_id_detects_old_global_names() -> None:
    assert is_legacy_entity_id("sensor.duration", "sensor", "duration") is True
    assert is_legacy_entity_id("sensor.duration_2", "sensor", "duration") is True
    assert is_legacy_entity_id("sensor.bathroom_duration", "sensor", "duration") is False