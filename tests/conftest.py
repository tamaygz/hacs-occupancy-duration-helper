"""Shared pytest fixtures for the Occupancy Duration Helper integration."""

from __future__ import annotations

from unittest.mock import MagicMock

import pytest


@pytest.fixture
def enable_custom_integrations() -> bool:
    """Enable loading custom integrations in pytest-homeassistant-custom-component."""
    return True


@pytest.fixture
def mock_config_entry() -> MagicMock:
    """Return a simple mock config entry for helper-contract tests."""
    entry = MagicMock()
    entry.entry_id = "test-entry-id"
    entry.title = "Occupancy Duration"
    entry.data = {}
    entry.options = {}
    return entry


@pytest.fixture
def mock_source_entity() -> str:
    """Return a representative source entity ID used across tests."""
    return "binary_sensor.test_motion"