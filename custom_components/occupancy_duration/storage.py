"""Persistence helpers for occupancy sessions."""

from __future__ import annotations

import logging
from datetime import datetime
from typing import Any

from homeassistant.core import HomeAssistant
from homeassistant.helpers.storage import Store

from .const import STORAGE_KEY, STORAGE_VERSION
from .session import OccupancySession, SessionState

_LOGGER = logging.getLogger(__name__)


def serialize_session(session: OccupancySession | None) -> dict[str, Any] | None:
    """Serialize a session to storage-safe primitives."""
    if session is None:
        return None
    return {
        "id": session.id,
        "started_at": session.started_at.isoformat(),
        "last_activity_at": session.last_activity_at.isoformat(),
        "last_active_signal_at": session.last_active_signal_at.isoformat() if session.last_active_signal_at else None,
        "ended_at": session.ended_at.isoformat() if session.ended_at else None,
        "score": session.score,
        "decay_anchor_at": session.decay_anchor_at.isoformat() if session.decay_anchor_at else None,
        "decay_anchor_score": session.decay_anchor_score,
        "stage": session.stage,
        "state": session.state.value,
    }


def deserialize_session(payload: dict[str, Any] | None) -> OccupancySession | None:
    """Deserialize a session from persisted data."""
    if not payload:
        return None
    try:
        return OccupancySession(
            id=payload["id"],
            started_at=datetime.fromisoformat(payload["started_at"]),
            last_activity_at=datetime.fromisoformat(payload["last_activity_at"]),
            last_active_signal_at=(
                datetime.fromisoformat(payload["last_active_signal_at"])
                if payload.get("last_active_signal_at")
                else None
            ),
            ended_at=(
                datetime.fromisoformat(payload["ended_at"])
                if payload.get("ended_at")
                else None
            ),
            score=float(payload["score"]),
            decay_anchor_at=(
                datetime.fromisoformat(payload["decay_anchor_at"])
                if payload.get("decay_anchor_at")
                else None
            ),
            decay_anchor_score=(
                float(payload["decay_anchor_score"])
                if payload.get("decay_anchor_score") is not None
                else None
            ),
            stage=payload.get("stage"),
            state=SessionState(payload["state"]),
        )
    except (KeyError, ValueError) as exc:
        _LOGGER.warning("Discarding malformed persisted session: %s", exc)
        return None


class SessionStore:
    """Persist sessions per config entry using Home Assistant storage."""

    def __init__(self, hass: HomeAssistant) -> None:
        self._store: Store[dict[str, Any]] = Store(hass, STORAGE_VERSION, STORAGE_KEY)

    async def async_load_session(self, entry_id: str) -> OccupancySession | None:
        payload = await self._store.async_load() or {}
        return deserialize_session(payload.get(entry_id))

    async def async_save_session(self, entry_id: str, session: OccupancySession | None) -> None:
        # Single load → mutate → save to avoid separate round-trips.
        payload = await self._store.async_load() or {}
        serialised = serialize_session(session)
        if serialised is None:
            payload.pop(entry_id, None)
        else:
            payload[entry_id] = serialised
        await self._store.async_save(payload)