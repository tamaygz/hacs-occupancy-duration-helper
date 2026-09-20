"""Tests for integration lifecycle helpers."""

from __future__ import annotations

import importlib
from unittest.mock import AsyncMock, MagicMock, patch

from custom_components.occupancy_duration.const import CONF_STAGES, DOMAIN

integration = importlib.import_module("custom_components.occupancy_duration")
sync_optional_entities = getattr(integration, "_async_sync_optional_entities")


async def test_async_remove_entry_purges_persisted_session() -> None:
    hass = MagicMock()
    entry = MagicMock(entry_id="entry-id")
    store = AsyncMock()

    with patch.object(integration, "SessionStore", return_value=store):
        await integration.async_remove_entry(hass, entry)

    store.async_save_session.assert_awaited_once_with("entry-id", None)


def test_sync_optional_entities_removes_stage_entity_when_stages_disabled() -> None:
    hass = MagicMock()
    entry = MagicMock(entry_id="entry-id")
    entry.options = {CONF_STAGES: []}
    registry = MagicMock()
    registry.async_get_entity_id.return_value = "sensor.helper_stage"

    with patch.object(integration.er, "async_get", return_value=registry):
        sync_optional_entities(hass, entry)

    registry.async_get_entity_id.assert_called_once_with(
        "sensor",
        DOMAIN,
        "entry-id_stage",
    )
    registry.async_remove.assert_called_once_with("sensor.helper_stage")


def test_sync_optional_entities_keeps_stage_entity_when_stages_configured() -> None:
    hass = MagicMock()
    entry = MagicMock(entry_id="entry-id")
    entry.options = {CONF_STAGES: [{"id": "short"}]}
    registry = MagicMock()

    with patch.object(integration.er, "async_get", return_value=registry):
        sync_optional_entities(hass, entry)

    registry.async_get_entity_id.assert_not_called()
    registry.async_remove.assert_not_called()