"""Source-entity capability inspection and strategy recommendation."""

from __future__ import annotations

import logging
from dataclasses import dataclass, field
from enum import StrEnum
from typing import Any

from homeassistant.components.binary_sensor import BinarySensorDeviceClass
from homeassistant.core import HomeAssistant
from homeassistant.helpers import entity_registry as er

from .const import StrategyMode

_LOGGER = logging.getLogger(__name__)

# String values of occupancy/presence device classes for fast comparison.
_OCCUPANCY_DC = str(BinarySensorDeviceClass.OCCUPANCY)
_PRESENCE_DC = str(BinarySensorDeviceClass.PRESENCE)
_MOTION_DC = str(BinarySensorDeviceClass.MOTION)


class CapabilityConfidence(StrEnum):
    """Certainty level of a detected capability."""

    CONFIRMED = "confirmed"   # directly observed from metadata or state
    INFERRED = "inferred"     # derived indirectly; may be wrong
    UNKNOWN = "unknown"       # no evidence found


@dataclass(frozen=True)
class CapabilityFinding:
    """One detected capability with its confidence and reason for diagnostics."""

    present: bool
    confidence: CapabilityConfidence
    rationale: str = ""


@dataclass(frozen=True)
class SensorCapabilities:
    """Immutable capability profile of a source entity."""

    current_state: CapabilityFinding = field(
        default_factory=lambda: CapabilityFinding(False, CapabilityConfidence.UNKNOWN)
    )
    motion_state: CapabilityFinding = field(
        default_factory=lambda: CapabilityFinding(False, CapabilityConfidence.UNKNOWN)
    )
    occupancy_state: CapabilityFinding = field(
        default_factory=lambda: CapabilityFinding(False, CapabilityConfidence.UNKNOWN)
    )
    presence_state: CapabilityFinding = field(
        default_factory=lambda: CapabilityFinding(False, CapabilityConfidence.UNKNOWN)
    )
    start_event: CapabilityFinding = field(
        default_factory=lambda: CapabilityFinding(False, CapabilityConfidence.UNKNOWN)
    )
    end_event: CapabilityFinding = field(
        default_factory=lambda: CapabilityFinding(False, CapabilityConfidence.UNKNOWN)
    )
    event_only: CapabilityFinding = field(
        default_factory=lambda: CapabilityFinding(False, CapabilityConfidence.UNKNOWN)
    )
    continuous_state: CapabilityFinding = field(
        default_factory=lambda: CapabilityFinding(False, CapabilityConfidence.UNKNOWN)
    )
    can_recheck: CapabilityFinding = field(
        default_factory=lambda: CapabilityFinding(False, CapabilityConfidence.UNKNOWN)
    )
    exposes_duration: CapabilityFinding = field(
        default_factory=lambda: CapabilityFinding(False, CapabilityConfidence.UNKNOWN)
    )
    # Overall confidence in all findings combined (0–1)
    confidence: float = 0.0
    # Sibling occupancy/presence entity on the same device, if found
    sibling_occupancy_entity: str | None = None


@dataclass(frozen=True)
class SourceSnapshot:
    """Point-in-time view of a source entity used by the capability inspector."""

    entity_id: str
    state: str | None
    attributes: dict[str, Any]
    device_class: str | None
    domain: str
    # Device ID, if the entity belongs to a device
    device_id: str | None = None
    # All entity IDs on the same device
    sibling_entity_ids: tuple[str, ...] = ()


@dataclass(frozen=True)
class CapabilitySummary:
    """Serialisable snapshot consumed by config_flow and diagnostics."""

    entity_id: str
    capabilities: SensorCapabilities
    recommended_strategy: StrategyMode
    # Human-readable lines for the config-flow preview and diagnostics
    preview_lines: tuple[str, ...]


# ---------------------------------------------------------------------------
# Snapshot builder
# ---------------------------------------------------------------------------


async def build_source_snapshot(
    hass: HomeAssistant, entity_id: str
) -> SourceSnapshot:
    """Build a SourceSnapshot for *entity_id* from live HA registry and state."""
    ent_reg = er.async_get(hass)
    entry = ent_reg.async_get(entity_id)
    state_obj = hass.states.get(entity_id)

    state = state_obj.state if state_obj else None
    attributes: dict[str, Any] = dict(state_obj.attributes) if state_obj else {}
    domain = entity_id.split(".")[0]
    device_class: str | None = None
    device_id: str | None = None
    sibling_ids: tuple[str, ...] = ()

    if entry:
        device_class = entry.device_class or entry.original_device_class
        device_id = entry.device_id

    # Fall back to live state attribute when registry has no device_class.
    if not device_class:
        device_class = attributes.get("device_class")

    if device_id:
        sibling_ids = tuple(
            e.entity_id
            for e in er.async_entries_for_device(ent_reg, device_id)
            if e.entity_id != entity_id
        )

    return SourceSnapshot(
        entity_id=entity_id,
        state=state,
        attributes=attributes,
        device_class=device_class,
        domain=domain,
        device_id=device_id,
        sibling_entity_ids=sibling_ids,
    )


# ---------------------------------------------------------------------------
# Evidence pipeline
# ---------------------------------------------------------------------------


def inspect_capabilities(
    hass: HomeAssistant, snapshot: SourceSnapshot
) -> SensorCapabilities:
    """Derive SensorCapabilities from a SourceSnapshot.

    Conservative rule: return UNKNOWN rather than inventing capability evidence.
    """
    dc = snapshot.device_class
    domain = snapshot.domain
    state = snapshot.state
    attrs = snapshot.attributes

    # --- current_state ---
    has_state = state is not None and state not in ("unavailable", "unknown")
    current_state = CapabilityFinding(
        present=has_state,
        confidence=CapabilityConfidence.CONFIRMED if has_state else CapabilityConfidence.CONFIRMED,
        rationale="entity state is readable and not unavailable/unknown" if has_state
        else "entity state unavailable or unknown",
    )

    # --- occupancy_state / presence_state ---
    is_occupancy_dc = dc == _OCCUPANCY_DC
    is_presence_dc = dc == _PRESENCE_DC
    occupancy_state = CapabilityFinding(
        present=is_occupancy_dc,
        confidence=CapabilityConfidence.CONFIRMED if is_occupancy_dc else CapabilityConfidence.UNKNOWN,
        rationale="device_class=occupancy" if is_occupancy_dc else "",
    )
    presence_state = CapabilityFinding(
        present=is_presence_dc,
        confidence=CapabilityConfidence.CONFIRMED if is_presence_dc else CapabilityConfidence.UNKNOWN,
        rationale="device_class=presence" if is_presence_dc else "",
    )

    # --- motion_state ---
    is_motion_dc = dc == _MOTION_DC
    motion_state = CapabilityFinding(
        present=is_motion_dc and domain == "binary_sensor",
        confidence=CapabilityConfidence.CONFIRMED if is_motion_dc else CapabilityConfidence.UNKNOWN,
        rationale="device_class=motion on binary_sensor" if is_motion_dc else "",
    )

    # --- continuous_state: binary_sensor that stays ON while condition holds ---
    is_continuous = domain == "binary_sensor" and has_state
    continuous_state = CapabilityFinding(
        present=is_continuous,
        confidence=CapabilityConfidence.CONFIRMED if is_continuous
        else CapabilityConfidence.UNKNOWN,
        rationale="binary_sensor has readable continuous ON/OFF state" if is_continuous else "",
    )

    # --- can_recheck: source has a queryable state we can read during decay ---
    can_recheck = CapabilityFinding(
        present=has_state and domain == "binary_sensor",
        confidence=CapabilityConfidence.CONFIRMED if (has_state and domain == "binary_sensor")
        else CapabilityConfidence.UNKNOWN,
        rationale="binary_sensor state is re-queryable" if (has_state and domain == "binary_sensor")
        else "",
    )

    # --- event_only: domain is event (no persistent state) ---
    is_event_only = domain == "event"
    event_only = CapabilityFinding(
        present=is_event_only,
        confidence=CapabilityConfidence.CONFIRMED if is_event_only else CapabilityConfidence.UNKNOWN,
        rationale="entity is an event entity with no persistent state" if is_event_only else "",
    )

    # --- start/end events (inferred for binary sensors) ---
    start_event = CapabilityFinding(
        present=is_motion_dc or is_event_only,
        confidence=CapabilityConfidence.INFERRED if is_motion_dc else (
            CapabilityConfidence.CONFIRMED if is_event_only else CapabilityConfidence.UNKNOWN
        ),
        rationale="inferred ON→transition as motion start" if is_motion_dc else (
            "event entity fires start events" if is_event_only else ""
        ),
    )
    end_event = CapabilityFinding(
        present=is_motion_dc,
        confidence=CapabilityConfidence.INFERRED if is_motion_dc else CapabilityConfidence.UNKNOWN,
        rationale="inferred OFF→transition as motion end" if is_motion_dc else "",
    )

    # --- exposes_duration: source attribute carries a duration or occupancy-time ---
    duration_attrs = {"duration", "occupancy_duration", "time_in_state", "occupancy_time"}
    exposes_dur = bool(duration_attrs.intersection(attrs.keys()))
    exposes_duration = CapabilityFinding(
        present=exposes_dur,
        confidence=CapabilityConfidence.CONFIRMED if exposes_dur else CapabilityConfidence.UNKNOWN,
        rationale=f"attribute(s) {duration_attrs.intersection(attrs.keys())} found" if exposes_dur
        else "",
    )

    # --- sibling occupancy entity on same device ---
    sibling_occupancy: str | None = None
    if snapshot.sibling_entity_ids:
        ent_reg_sib = er.async_get(hass)
        for sib_id in snapshot.sibling_entity_ids:
            if not sib_id.startswith("binary_sensor."):
                continue
            sib_entry = ent_reg_sib.async_get(sib_id)
            if sib_entry:
                sib_dc = sib_entry.device_class or sib_entry.original_device_class
                if sib_dc in (_OCCUPANCY_DC, _PRESENCE_DC):
                    sibling_occupancy = sib_id
                    break

    # --- overall confidence ---
    confirmed_count = sum(
        1
        for f in (
            current_state, motion_state, occupancy_state, presence_state,
            continuous_state, can_recheck, event_only,
        )
        if f.confidence == CapabilityConfidence.CONFIRMED
    )
    overall_confidence = round(confirmed_count / 7, 2)

    return SensorCapabilities(
        current_state=current_state,
        motion_state=motion_state,
        occupancy_state=occupancy_state,
        presence_state=presence_state,
        start_event=start_event,
        end_event=end_event,
        event_only=event_only,
        continuous_state=continuous_state,
        can_recheck=can_recheck,
        exposes_duration=exposes_duration,
        confidence=overall_confidence,
        sibling_occupancy_entity=sibling_occupancy,
    )


# ---------------------------------------------------------------------------
# Strategy recommendation engine
# ---------------------------------------------------------------------------


def recommend_strategy(caps: SensorCapabilities) -> StrategyMode:
    """Return the safest strategy mode given detected capabilities.

    Priority order (from PRD §5.3):
      1. Explicit occupancy/presence   → NATIVE_OCCUPANCY
      2. Sibling occupancy + motion    → HYBRID
      3. Continuous ON/OFF motion      → CONTINUOUS_MOTION
      4. Event-only                    → EVENT_ONLY
      5. Fallback                      → EVENT_ONLY (conservative: assume no state)
    """
    if caps.occupancy_state.present or caps.presence_state.present:
        return StrategyMode.NATIVE_OCCUPANCY

    if caps.sibling_occupancy_entity and caps.motion_state.present:
        return StrategyMode.HYBRID

    if caps.continuous_state.present and caps.motion_state.present:
        return StrategyMode.CONTINUOUS_MOTION

    if caps.event_only.present:
        return StrategyMode.EVENT_ONLY

    # Readable binary sensor without an explicit motion device class.
    if caps.continuous_state.present:
        return StrategyMode.CONTINUOUS_MOTION

    return StrategyMode.EVENT_ONLY


def resolve_strategy(
    caps: SensorCapabilities,
    user_override: str | None,
) -> StrategyMode:
    """Return the effective strategy, respecting explicit user overrides.

    A non-AUTO override is never replaced by automatic detection.
    """
    if user_override and user_override != StrategyMode.AUTO:
        try:
            return StrategyMode(user_override)
        except ValueError:
            _LOGGER.warning(
                "Unknown strategy override %r; falling back to auto detection",
                user_override,
            )
    return recommend_strategy(caps)


# ---------------------------------------------------------------------------
# Summary builder (consumed by config_flow and diagnostics)
# ---------------------------------------------------------------------------


def _yn(finding: CapabilityFinding) -> str:
    if finding.present:
        return f"✓ ({finding.confidence.value})"
    if finding.confidence == CapabilityConfidence.UNKNOWN:
        return "✗ (not detected)"
    return "✗"


def build_capability_summary(
    entity_id: str,
    caps: SensorCapabilities,
    recommended: StrategyMode,
) -> CapabilitySummary:
    """Build a human-readable summary for the config-flow preview and diagnostics."""
    lines = (
        f"Current state available   {_yn(caps.current_state)}",
        f"Motion ON/OFF             {_yn(caps.motion_state)}",
        f"Occupancy state           {_yn(caps.occupancy_state)}",
        f"Presence state            {_yn(caps.presence_state)}",
        f"Continuous state          {_yn(caps.continuous_state)}",
        f"Event-only                {_yn(caps.event_only)}",
        f"Re-check during decay     {_yn(caps.can_recheck)}",
        f"Exposes duration attr     {_yn(caps.exposes_duration)}",
        *(
            (f"Sibling occupancy entity  {caps.sibling_occupancy_entity}",)
            if caps.sibling_occupancy_entity
            else ()
        ),
        "",
        f"Recommended strategy:     {recommended.value}",
        f"Overall confidence:       {caps.confidence:.0%}",
    )
    return CapabilitySummary(
        entity_id=entity_id,
        capabilities=caps,
        recommended_strategy=recommended,
        preview_lines=lines,
    )


# ---------------------------------------------------------------------------
# Main public entry point
# ---------------------------------------------------------------------------


async def async_inspect_entity(
    hass: HomeAssistant,
    entity_id: str,
    user_strategy_override: str | None = None,
) -> CapabilitySummary:
    """Full capability inspection pipeline for *entity_id*.

    Returns a CapabilitySummary ready for the config-flow preview and diagnostics.
    """
    snapshot = await build_source_snapshot(hass, entity_id)
    caps = inspect_capabilities(hass, snapshot)
    strategy = resolve_strategy(caps, user_strategy_override)
    return build_capability_summary(entity_id, caps, strategy)
