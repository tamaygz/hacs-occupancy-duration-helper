"""Tests for capability detection and strategy recommendation."""

from __future__ import annotations

from unittest.mock import MagicMock, patch

from homeassistant.components.binary_sensor import BinarySensorDeviceClass

from custom_components.occupancy_duration.capability import (
    CapabilityConfidence,
    SourceSnapshot,
    build_capability_summary,
    inspect_capabilities,
    recommend_strategy,
    resolve_strategy,
)
from custom_components.occupancy_duration.const import StrategyMode


# ---------------------------------------------------------------------------
# Helpers
# ---------------------------------------------------------------------------


def _snapshot(
    entity_id: str = "binary_sensor.test",
    state: str | None = "on",
    domain: str = "binary_sensor",
    device_class: str | None = None,
    attributes: dict | None = None,
    device_id: str | None = None,
    sibling_entity_ids: tuple[str, ...] = (),
) -> SourceSnapshot:
    return SourceSnapshot(
        entity_id=entity_id,
        state=state,
        attributes=attributes or {},
        device_class=device_class,
        domain=domain,
        device_id=device_id,
        sibling_entity_ids=sibling_entity_ids,
    )


def _hass() -> MagicMock:
    hass = MagicMock()
    hass.states.get = MagicMock(return_value=None)
    return hass


# ---------------------------------------------------------------------------
# Strategy recommendation
# ---------------------------------------------------------------------------


def test_motion_binary_sensor_gets_continuous_motion_strategy() -> None:
    caps = inspect_capabilities(
        _hass(),
        _snapshot(device_class=str(BinarySensorDeviceClass.MOTION)),
    )
    assert recommend_strategy(caps) == StrategyMode.CONTINUOUS_MOTION


def test_occupancy_binary_sensor_gets_native_occupancy_strategy() -> None:
    caps = inspect_capabilities(
        _hass(),
        _snapshot(device_class=str(BinarySensorDeviceClass.OCCUPANCY)),
    )
    assert recommend_strategy(caps) == StrategyMode.NATIVE_OCCUPANCY


def test_presence_binary_sensor_gets_native_occupancy_strategy() -> None:
    caps = inspect_capabilities(
        _hass(),
        _snapshot(device_class=str(BinarySensorDeviceClass.PRESENCE)),
    )
    assert recommend_strategy(caps) == StrategyMode.NATIVE_OCCUPANCY


def test_event_entity_gets_event_only_strategy() -> None:
    caps = inspect_capabilities(
        _hass(),
        _snapshot(entity_id="event.motion", state=None, domain="event", device_class=None),
    )
    assert recommend_strategy(caps) == StrategyMode.EVENT_ONLY


def test_sibling_occupancy_with_motion_gets_hybrid_strategy() -> None:
    """Motion entity on same device as occupancy sibling → HYBRID."""
    snap = _snapshot(
        entity_id="binary_sensor.motion_detector",
        device_class=str(BinarySensorDeviceClass.MOTION),
        device_id="device_123",
        sibling_entity_ids=("binary_sensor.occupancy_sensor",),
    )

    sibling_entry = MagicMock()
    sibling_entry.device_class = str(BinarySensorDeviceClass.OCCUPANCY)
    sibling_entry.original_device_class = None

    with patch(
        "custom_components.occupancy_duration.capability.er.async_get"
    ) as mock_er:
        reg = MagicMock()
        reg.async_get.return_value = sibling_entry
        mock_er.return_value = reg

        caps = inspect_capabilities(_hass(), snap)

    assert caps.sibling_occupancy_entity == "binary_sensor.occupancy_sensor"
    assert recommend_strategy(caps) == StrategyMode.HYBRID


# ---------------------------------------------------------------------------
# Capability findings
# ---------------------------------------------------------------------------


def test_unavailable_source_has_no_current_state() -> None:
    caps = inspect_capabilities(
        _hass(),
        _snapshot(state="unavailable"),
    )
    assert caps.current_state.present is False
    assert caps.current_state.confidence == CapabilityConfidence.CONFIRMED


def test_unknown_state_has_no_current_state() -> None:
    caps = inspect_capabilities(_hass(), _snapshot(state="unknown"))
    assert caps.current_state.present is False


def test_event_entity_marked_event_only() -> None:
    caps = inspect_capabilities(
        _hass(),
        _snapshot(entity_id="event.x", state=None, domain="event"),
    )
    assert caps.event_only.present is True
    assert caps.event_only.confidence == CapabilityConfidence.CONFIRMED


def test_duration_attribute_detected() -> None:
    caps = inspect_capabilities(
        _hass(),
        _snapshot(attributes={"occupancy_duration": 120}),
    )
    assert caps.exposes_duration.present is True
    assert caps.exposes_duration.confidence == CapabilityConfidence.CONFIRMED


# ---------------------------------------------------------------------------
# Override preservation
# ---------------------------------------------------------------------------


def test_manual_strategy_override_beats_recommendation() -> None:
    """Explicit non-AUTO override wins even when recommendation differs."""
    caps = inspect_capabilities(
        _hass(),
        _snapshot(device_class=str(BinarySensorDeviceClass.OCCUPANCY)),
    )
    assert recommend_strategy(caps) == StrategyMode.NATIVE_OCCUPANCY
    assert resolve_strategy(caps, "event_only") == StrategyMode.EVENT_ONLY


def test_auto_override_falls_through_to_recommendation() -> None:
    caps = inspect_capabilities(
        _hass(),
        _snapshot(device_class=str(BinarySensorDeviceClass.OCCUPANCY)),
    )
    assert resolve_strategy(caps, StrategyMode.AUTO) == StrategyMode.NATIVE_OCCUPANCY


def test_none_override_falls_through_to_recommendation() -> None:
    caps = inspect_capabilities(
        _hass(),
        _snapshot(device_class=str(BinarySensorDeviceClass.MOTION)),
    )
    assert resolve_strategy(caps, None) == StrategyMode.CONTINUOUS_MOTION


# ---------------------------------------------------------------------------
# Summary contract
# ---------------------------------------------------------------------------


def test_capability_summary_entity_id_and_strategy() -> None:
    snap = _snapshot(
        entity_id="binary_sensor.hall_motion",
        device_class=str(BinarySensorDeviceClass.MOTION),
    )
    caps = inspect_capabilities(_hass(), snap)
    recommended = recommend_strategy(caps)
    summary = build_capability_summary("binary_sensor.hall_motion", caps, recommended)

    assert summary.entity_id == "binary_sensor.hall_motion"
    assert summary.recommended_strategy == StrategyMode.CONTINUOUS_MOTION
    assert any("Recommended strategy" in line for line in summary.preview_lines)


def test_capability_summary_mentions_strategy_in_preview() -> None:
    snap = _snapshot(device_class=str(BinarySensorDeviceClass.OCCUPANCY))
    caps = inspect_capabilities(_hass(), snap)
    summary = build_capability_summary(snap.entity_id, caps, recommend_strategy(caps))

    assert any("native_occupancy" in line for line in summary.preview_lines)


# ---------------------------------------------------------------------------
# Confidence
# ---------------------------------------------------------------------------


def test_confidence_higher_for_known_device_class() -> None:
    """Sensor with a recognised device class has higher confidence than one without."""
    caps_known = inspect_capabilities(
        _hass(),
        _snapshot(device_class=str(BinarySensorDeviceClass.MOTION)),
    )
    caps_unknown = inspect_capabilities(
        _hass(),
        _snapshot(device_class=None, domain="sensor"),
    )
    assert caps_known.confidence > caps_unknown.confidence
