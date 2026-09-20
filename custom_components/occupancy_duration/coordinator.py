"""Runtime coordinator and in-memory state for occupancy sessions."""

from __future__ import annotations

from dataclasses import dataclass, replace
from datetime import UTC, datetime
import logging
from typing import Any

from homeassistant.config_entries import ConfigEntry
from homeassistant.const import STATE_HOME, STATE_ON, STATE_UNAVAILABLE, STATE_UNKNOWN
from homeassistant.core import CALLBACK_TYPE, Event, HomeAssistant, callback
from homeassistant.helpers.event import async_track_state_change_event
from homeassistant.helpers.update_coordinator import DataUpdateCoordinator

from .capability import CapabilitySummary, async_inspect_entity
from .const import (
    CONF_DEFAULT_HALF_LIFE,
    CONF_END_GRACE,
    CONF_END_THRESHOLD,
    CONF_RESTORE_SESSION,
    CONF_SOURCE_ENTITY,
    CONF_SOURCE_REVISION,
    CONF_STAGES,
    CONF_STRATEGY,
    DEFAULT_END_GRACE,
    DEFAULT_END_THRESHOLD,
    DEFAULT_HALF_LIFE,
    DEFAULT_RESTORE_SESSION,
    EVENT_SESSION_ENDED,
    EVENT_SESSION_STAGE_CHANGED,
    EVENT_SESSION_STARTED,
    StrategyMode,
)
from .session import (
    OccupancySession,
    SessionEvaluationInput,
    SessionState,
    SessionTransition,
    activity_detected,
    decay_tick,
    grace_expired,
    source_became_inactive,
)
from .stage import DurationStage
from .storage import SessionStore


ACTIVE_STATE_VALUES = {STATE_ON, STATE_HOME, "occupied", "detected", "present"}
_LOGGER = logging.getLogger(__name__)


@dataclass(frozen=True, slots=True)
class RuntimeSnapshot:
    """Authoritative runtime state shared by entities, diagnostics, and storage."""

    entry_id: str
    source_entity: str
    source_revision: int
    capability_summary: CapabilitySummary
    strategy: StrategyMode
    session: OccupancySession | None
    source_state: str | None
    restore_session: bool
    default_half_life: int
    end_threshold: int
    end_grace: int
    stages: tuple[DurationStage, ...]
    last_transition_reason: str = ""


def build_runtime_snapshot(
    *,
    entry_id: str,
    source_entity: str,
    source_revision: int,
    capability_summary: CapabilitySummary,
    strategy: StrategyMode,
    session: OccupancySession | None,
    source_state: str | None,
    restore_session: bool,
    default_half_life: int,
    end_threshold: int,
    end_grace: int,
    stages: tuple[DurationStage, ...],
    last_transition_reason: str = "",
) -> RuntimeSnapshot:
    return RuntimeSnapshot(
        entry_id=entry_id,
        source_entity=source_entity,
        source_revision=source_revision,
        capability_summary=capability_summary,
        strategy=strategy,
        session=session,
        source_state=source_state,
        restore_session=restore_session,
        default_half_life=default_half_life,
        end_threshold=end_threshold,
        end_grace=end_grace,
        stages=stages,
        last_transition_reason=last_transition_reason,
    )


class OccupancyDurationCoordinator(DataUpdateCoordinator[RuntimeSnapshot]):
    """Push-style coordinator for one occupancy helper config entry."""

    def __init__(self, hass: HomeAssistant, entry: ConfigEntry) -> None:
        super().__init__(
            hass,
            logger=_LOGGER,
            name=f"{entry.title} occupancy coordinator",
        )
        self._config_entry_ref: ConfigEntry = entry
        self._unsub_state: CALLBACK_TYPE | None = None
        self._store = SessionStore(hass)

    @property
    def source_entity(self) -> str:
        return str(self._config_entry_ref.data[CONF_SOURCE_ENTITY])

    @property
    def source_revision(self) -> int:
        return int(self._config_entry_ref.data.get(CONF_SOURCE_REVISION, 1))

    @property
    def strategy(self) -> StrategyMode:
        raw = self._config_entry_ref.options.get(CONF_STRATEGY, StrategyMode.AUTO.value)
        return StrategyMode(raw)

    @property
    def stages(self) -> tuple[DurationStage, ...]:
        stage_payloads = self._config_entry_ref.options.get(CONF_STAGES, [])
        return tuple(
            DurationStage(
                id=payload["id"],
                name=payload["name"],
                min_duration=int(payload["min_duration"]),
                max_duration=(
                    int(payload["max_duration"])
                    if payload.get("max_duration") is not None
                    else None
                ),
                decay_half_life=(
                    int(payload["half_life"]) if payload.get("half_life") is not None else None
                ),
            )
            for payload in stage_payloads
        )

    async def async_initialize(self) -> None:
        """Inspect source, restore state, and subscribe to updates."""
        capability_summary = await async_inspect_entity(
            self.hass,
            self.source_entity,
            self._config_entry_ref.options.get(CONF_STRATEGY),
        )
        source_state = self._read_source_state()
        restored = None
        if self._config_entry_ref.options.get(CONF_RESTORE_SESSION, DEFAULT_RESTORE_SESSION):
            restored = await self._store.async_load_session(self._config_entry_ref.entry_id)

        session, reason = self._restore_or_seed_session(
            capability_summary,
            restored,
            source_state,
        )

        self.async_set_updated_data(
            build_runtime_snapshot(
                entry_id=self._config_entry_ref.entry_id,
                source_entity=self.source_entity,
                source_revision=self.source_revision,
                capability_summary=capability_summary,
                strategy=self.strategy,
                session=session,
                source_state=source_state,
                restore_session=bool(self._config_entry_ref.options.get(CONF_RESTORE_SESSION, DEFAULT_RESTORE_SESSION)),
                default_half_life=int(self._config_entry_ref.options.get(CONF_DEFAULT_HALF_LIFE, DEFAULT_HALF_LIFE)),
                end_threshold=int(self._config_entry_ref.options.get(CONF_END_THRESHOLD, DEFAULT_END_THRESHOLD)),
                end_grace=int(self._config_entry_ref.options.get(CONF_END_GRACE, DEFAULT_END_GRACE)),
                stages=self.stages,
                last_transition_reason=reason,
            )
        )
        await self._store.async_save_session(self._config_entry_ref.entry_id, session)

        self._unsub_state = async_track_state_change_event(
            self.hass,
            [self.source_entity],
            self._handle_source_change,
        )

    async def async_shutdown(self) -> None:
        """Detach listeners and persist the latest session snapshot."""
        if self._unsub_state is not None:
            self._unsub_state()
            self._unsub_state = None
        if self.data is not None:
            await self._store.async_save_session(self._config_entry_ref.entry_id, self.data.session)

    def diagnostics_dict(self) -> dict[str, Any]:
        """Return diagnostics-friendly runtime data."""
        if self.data is None:
            return {"ready": False}
        session = self.data.session
        return {
            "ready": True,
            "source_entity": self.data.source_entity,
            "source_revision": self.data.source_revision,
            "source_state": self.data.source_state,
            "strategy": self.data.strategy.value,
            "capability_preview": list(self.data.capability_summary.preview_lines),
            "session": {
                "id": session.id if session else None,
                "started_at": session.started_at.isoformat() if session else None,
                "last_activity_at": session.last_activity_at.isoformat() if session else None,
                "last_active_signal_at": session.last_active_signal_at.isoformat() if session and session.last_active_signal_at else None,
                "ended_at": session.ended_at.isoformat() if session and session.ended_at else None,
                "score": session.score if session else None,
                "stage": session.stage if session else None,
                "state": session.state.value if session else SessionState.IDLE.value,
            },
            "decay": {
                "default_half_life": self.data.default_half_life,
                "end_threshold": self.data.end_threshold,
                "end_grace": self.data.end_grace,
            },
            "last_transition_reason": self.data.last_transition_reason,
        }

    def _read_source_state(self) -> str | None:
        state = self.hass.states.get(self.source_entity)
        return state.state if state else None

    def _source_is_unavailable(self, state: str | None) -> bool:
        return state in (None, STATE_UNAVAILABLE, STATE_UNKNOWN)

    def _source_is_active(self, capability_summary: CapabilitySummary, state: str | None) -> tuple[bool, bool]:
        if self._source_is_unavailable(state):
            return False, False
        normalised = str(state).lower()
        caps = capability_summary.capabilities
        authoritative = caps.occupancy_state.present or caps.presence_state.present
        return normalised in ACTIVE_STATE_VALUES, authoritative

    def _restore_or_seed_session(
        self,
        capability_summary: CapabilitySummary,
        restored: OccupancySession | None,
        source_state: str | None,
    ) -> tuple[OccupancySession | None, str]:
        now = datetime.now(UTC)
        source_active, authoritative = self._source_is_active(capability_summary, source_state)

        if restored is None:
            if source_active:
                return activity_detected(None, now, authoritative=authoritative, stages=self.stages).session, "active source at startup"
            return None, "no restored session"

        if self._source_is_unavailable(source_state):
            return restored, "source unavailable during restore; preserved prior session"

        if source_active:
            transition = activity_detected(restored, now, authoritative=authoritative, stages=self.stages)
            return transition.session, transition.reason

        transition = decay_tick(
            source_became_inactive(restored).session if restored.state == SessionState.ACTIVE else restored,
            SessionEvaluationInput(
                now=now,
                source_currently_active=False,
                authoritative_active=False,
                elapsed_since_last_activity=max(0.0, (now - restored.last_activity_at).total_seconds()),
                default_half_life=int(self._config_entry_ref.options.get(CONF_DEFAULT_HALF_LIFE, DEFAULT_HALF_LIFE)),
                end_threshold=int(self._config_entry_ref.options.get(CONF_END_THRESHOLD, DEFAULT_END_THRESHOLD)),
                end_grace_seconds=int(self._config_entry_ref.options.get(CONF_END_GRACE, DEFAULT_END_GRACE)),
                stages=self.stages,
            ),
        )
        if transition.session.state == SessionState.ENDING:
            closed = grace_expired(
                transition.session,
                now,
                end_grace_seconds=int(self._config_entry_ref.options.get(CONF_END_GRACE, DEFAULT_END_GRACE)),
            )
            if closed.changed:
                return closed.session, closed.reason
        return transition.session, transition.reason

    @callback
    def _handle_source_change(self, event) -> None:
        self.hass.async_create_task(self._async_process_source_change(event))

    async def _async_process_source_change(self, event: Event) -> None:
        if self.data is None:
            return

        new_state_obj = event.data.get("new_state")
        source_state = new_state_obj.state if new_state_obj else None
        source_active, authoritative = self._source_is_active(self.data.capability_summary, source_state)
        now = datetime.now(UTC)
        session = self.data.session

        if self._source_is_unavailable(source_state):
            snapshot = replace(self.data, source_state=source_state, last_transition_reason="source unavailable; session preserved")
            self.async_set_updated_data(snapshot)
            return

        if source_active:
            transition = activity_detected(session, now, authoritative=authoritative, stages=self.data.stages)
        elif session is None:
            snapshot = replace(self.data, source_state=source_state, last_transition_reason="source inactive with no open session")
            self.async_set_updated_data(snapshot)
            return
        else:
            transition = decay_tick(
                source_became_inactive(session).session if session.state == SessionState.ACTIVE else session,
                SessionEvaluationInput(
                    now=now,
                    source_currently_active=False,
                    authoritative_active=False,
                    elapsed_since_last_activity=max(0.0, (now - session.last_activity_at).total_seconds()),
                    default_half_life=self.data.default_half_life,
                    end_threshold=self.data.end_threshold,
                    end_grace_seconds=self.data.end_grace,
                    stages=self.data.stages,
                ),
            )
            if transition.session.state == SessionState.ENDING:
                grace_transition = grace_expired(
                    transition.session,
                    now,
                    end_grace_seconds=self.data.end_grace,
                )
                if grace_transition.changed:
                    transition = grace_transition

        previous_session = self.data.session
        snapshot = replace(
            self.data,
            session=transition.session,
            source_state=source_state,
            last_transition_reason=transition.reason,
        )
        self.async_set_updated_data(snapshot)
        await self._store.async_save_session(self._config_entry_ref.entry_id, transition.session)
        self._emit_events(previous_session, transition)

    def _emit_events(self, previous_session: OccupancySession | None, transition: SessionTransition) -> None:
        current = transition.session
        if previous_session is None and current.active:
            self.hass.bus.async_fire(
                EVENT_SESSION_STARTED,
                {
                    "entity_id": self.source_entity,
                    "session_id": current.id,
                    "started_at": current.started_at.isoformat(),
                    "source_entity": self.source_entity,
                },
            )

        if previous_session and previous_session.stage != current.stage and current.stage is not None:
            self.hass.bus.async_fire(
                EVENT_SESSION_STAGE_CHANGED,
                {
                    "entity_id": self.source_entity,
                    "session_id": current.id,
                    "previous_stage": previous_session.stage,
                    "new_stage": current.stage,
                    "duration": current.duration_seconds(datetime.now(UTC)),
                },
            )

        if current.state == SessionState.CLOSED:
            self.hass.bus.async_fire(
                EVENT_SESSION_ENDED,
                {
                    "entity_id": self.source_entity,
                    "session_id": current.id,
                    "started_at": current.started_at.isoformat(),
                    "ended_at": current.ended_at.isoformat() if current.ended_at else None,
                    "duration": current.duration_seconds(current.ended_at or datetime.now(UTC)),
                    "final_stage": current.stage,
                    "termination_reason": transition.reason,
                },
            )