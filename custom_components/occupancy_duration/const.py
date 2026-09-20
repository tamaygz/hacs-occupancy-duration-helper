"""Constants for the Occupancy Duration Helper integration."""

from __future__ import annotations

from enum import StrEnum

DOMAIN = "occupancy_duration"

# Config/options keys
CONF_SOURCE_ENTITY = "source_entity"
CONF_STRATEGY = "strategy"
CONF_DEFAULT_HALF_LIFE = "default_half_life"
CONF_END_THRESHOLD = "end_threshold"
CONF_END_GRACE = "end_grace"
CONF_RESTORE_SESSION = "restore_session"
CONF_STAGES = "stages"

# Stage config sub-keys
CONF_STAGE_ID = "id"
CONF_STAGE_NAME = "name"
CONF_STAGE_MIN_DURATION = "min_duration"
CONF_STAGE_MAX_DURATION = "max_duration"
CONF_STAGE_HALF_LIFE = "half_life"

# Defaults
DEFAULT_HALF_LIFE = 60  # seconds
DEFAULT_END_THRESHOLD = 5  # score percentage
DEFAULT_END_GRACE = 15  # seconds
DEFAULT_RESTORE_SESSION = True

# Score bounds
SCORE_MAX = 100.0
SCORE_MIN = 0.0
SCORE_ACTIVITY_INCREMENT = 20.0  # added on each motion/activity event


class StrategyMode(StrEnum):
    """Sensor interpretation strategy for the session engine."""

    AUTO = "auto"
    NATIVE_OCCUPANCY = "native_occupancy"
    CONTINUOUS_MOTION = "continuous_motion"
    EVENT_ONLY = "event_only"
    HYBRID = "hybrid"
