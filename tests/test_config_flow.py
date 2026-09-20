"""Tests for config flow helpers and contracts."""

from __future__ import annotations

from unittest.mock import MagicMock

from custom_components.occupancy_duration.config_flow import (
    build_entry_data,
    build_entry_options,
    source_change_requires_reset,
    validate_stage_payload,
)
from custom_components.occupancy_duration.const import (
    CONF_DEFAULT_HALF_LIFE,
    CONF_END_GRACE,
    CONF_END_THRESHOLD,
    CONF_NAME,
    CONF_RESTORE_SESSION,
    CONF_SOURCE_ENTITY,
    CONF_SOURCE_REVISION,
    CONF_STAGE_HALF_LIFE,
    CONF_STAGE_ID,
    CONF_STAGE_MAX_DURATION,
    CONF_STAGE_MIN_DURATION,
    CONF_STAGE_NAME,
    CONF_STAGES,
    CONF_STRATEGY,
)


def test_build_entry_data_happy_path() -> None:
    data = build_entry_data(name="Bathroom", source_entity="binary_sensor.bathroom_motion")
    assert data == {
        CONF_NAME: "Bathroom",
        CONF_SOURCE_ENTITY: "binary_sensor.bathroom_motion",
        CONF_SOURCE_REVISION: 1,
    }


def test_build_entry_options_happy_path() -> None:
    stages = [{CONF_STAGE_ID: "short", CONF_STAGE_NAME: "Short", CONF_STAGE_MIN_DURATION: 0, CONF_STAGE_MAX_DURATION: 60, CONF_STAGE_HALF_LIFE: 30}]
    options = build_entry_options(
        strategy="auto",
        default_half_life=60,
        end_threshold=5,
        end_grace=15,
        restore_session=True,
        stages=stages,
    )
    assert options[CONF_STRATEGY] == "auto"
    assert options[CONF_DEFAULT_HALF_LIFE] == 60
    assert options[CONF_END_THRESHOLD] == 5
    assert options[CONF_END_GRACE] == 15
    assert options[CONF_RESTORE_SESSION] is True
    assert options[CONF_STAGES] == stages


def test_validate_stage_payload_accepts_valid_stage() -> None:
    stage = validate_stage_payload(
        {
            CONF_STAGE_ID: "short",
            CONF_STAGE_NAME: "Short",
            CONF_STAGE_MIN_DURATION: 0,
            CONF_STAGE_MAX_DURATION: 60,
            CONF_STAGE_HALF_LIFE: 30,
        },
        [],
    )
    assert stage[CONF_STAGE_ID] == "short"
    assert stage[CONF_STAGE_MAX_DURATION] == 60


def test_validate_stage_payload_accepts_selector_float_values() -> None:
    stage = validate_stage_payload(
        {
            CONF_STAGE_ID: "short",
            CONF_STAGE_NAME: "Short",
            CONF_STAGE_MIN_DURATION: 0.0,
            CONF_STAGE_MAX_DURATION: 60.0,
            CONF_STAGE_HALF_LIFE: 30.0,
        },
        [],
    )
    assert stage[CONF_STAGE_MIN_DURATION] == 0
    assert stage[CONF_STAGE_MAX_DURATION] == 60
    assert stage[CONF_STAGE_HALF_LIFE] == 30


def test_validate_stage_payload_rejects_inverted_range() -> None:
    try:
        validate_stage_payload(
            {
                CONF_STAGE_ID: "bad",
                CONF_STAGE_NAME: "Bad",
                CONF_STAGE_MIN_DURATION: 60,
                CONF_STAGE_MAX_DURATION: 30,
                CONF_STAGE_HALF_LIFE: 30,
            },
            [],
        )
    except ValueError as err:
        assert str(err) == "invalid_stage_range"
    else:
        raise AssertionError("expected invalid_stage_range")


def test_validate_stage_payload_rejects_overlap() -> None:
    existing = [
        {
            CONF_STAGE_ID: "short",
            CONF_STAGE_NAME: "Short",
            CONF_STAGE_MIN_DURATION: 0,
            CONF_STAGE_MAX_DURATION: 60,
            CONF_STAGE_HALF_LIFE: 30,
        }
    ]
    try:
        validate_stage_payload(
            {
                CONF_STAGE_ID: "medium",
                CONF_STAGE_NAME: "Medium",
                CONF_STAGE_MIN_DURATION: 30,
                CONF_STAGE_MAX_DURATION: 120,
                CONF_STAGE_HALF_LIFE: 60,
            },
            existing,
        )
    except ValueError as err:
        assert str(err) == "stage_overlap"
    else:
        raise AssertionError("expected stage_overlap")


def test_validate_stage_payload_accepts_open_ended_last_stage() -> None:
    existing = [
        {
            CONF_STAGE_ID: "short",
            CONF_STAGE_NAME: "Short",
            CONF_STAGE_MIN_DURATION: 0,
            CONF_STAGE_MAX_DURATION: 180,
            CONF_STAGE_HALF_LIFE: None,
        }
    ]
    stage = validate_stage_payload(
        {
            CONF_STAGE_ID: "long",
            CONF_STAGE_NAME: "Long",
            CONF_STAGE_MIN_DURATION: 180,
            CONF_STAGE_MAX_DURATION: None,
            CONF_STAGE_HALF_LIFE: None,
        },
        existing,
    )
    assert stage[CONF_STAGE_ID] == "long"
    assert stage[CONF_STAGE_MAX_DURATION] is None


def test_validate_stage_payload_rejects_overlap_with_open_ended_existing() -> None:
    existing = [
        {
            CONF_STAGE_ID: "long",
            CONF_STAGE_NAME: "Long",
            CONF_STAGE_MIN_DURATION: 180,
            CONF_STAGE_MAX_DURATION: None,
            CONF_STAGE_HALF_LIFE: None,
        }
    ]
    try:
        validate_stage_payload(
            {
                CONF_STAGE_ID: "overlap",
                CONF_STAGE_NAME: "Overlap",
                CONF_STAGE_MIN_DURATION: 200,
                CONF_STAGE_MAX_DURATION: 300,
                CONF_STAGE_HALF_LIFE: None,
            },
            existing,
        )
    except ValueError as err:
        assert str(err) == "stage_overlap"
    else:
        raise AssertionError("expected stage_overlap")


def test_validate_stage_payload_rejects_new_open_ended_overlapping_existing_open_ended() -> None:
    existing = [
        {
            CONF_STAGE_ID: "long",
            CONF_STAGE_NAME: "Long",
            CONF_STAGE_MIN_DURATION: 180,
            CONF_STAGE_MAX_DURATION: None,
            CONF_STAGE_HALF_LIFE: None,
        }
    ]
    try:
        validate_stage_payload(
            {
                CONF_STAGE_ID: "wider",
                CONF_STAGE_NAME: "Wider",
                CONF_STAGE_MIN_DURATION: 0,
                CONF_STAGE_MAX_DURATION: None,
                CONF_STAGE_HALF_LIFE: None,
            },
            existing,
        )
    except ValueError as err:
        assert str(err) == "stage_overlap"
    else:
        raise AssertionError("expected stage_overlap")


def test_source_change_requires_reset_when_source_changes() -> None:
    config_entry = MagicMock()
    config_entry.data = {
        CONF_SOURCE_ENTITY: "binary_sensor.old",
        CONF_SOURCE_REVISION: 2,
    }
    changed, revision = source_change_requires_reset(config_entry, "binary_sensor.new")
    assert changed is True
    assert revision == 3


def test_source_change_does_not_bump_revision_when_unchanged() -> None:
    config_entry = MagicMock()
    config_entry.data = {
        CONF_SOURCE_ENTITY: "binary_sensor.same",
        CONF_SOURCE_REVISION: 4,
    }
    changed, revision = source_change_requires_reset(config_entry, "binary_sensor.same")
    assert changed is False
    assert revision == 4


def test_strategy_override_persists_in_runtime_options_contract() -> None:
    options = build_entry_options(
        strategy="event_only",
        default_half_life=60,
        end_threshold=5,
        end_grace=15,
        restore_session=True,
        stages=[],
    )
    assert options[CONF_STRATEGY] == "event_only"


def test_options_contract_does_not_mutate_setup_identity_fields() -> None:
    options = build_entry_options(
        strategy="auto",
        default_half_life=60,
        end_threshold=5,
        end_grace=15,
        restore_session=True,
        stages=[],
    )
    assert CONF_NAME not in options
    assert CONF_SOURCE_ENTITY not in options