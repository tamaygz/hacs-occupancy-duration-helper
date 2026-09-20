"""Config flow for the Occupancy Duration Helper integration."""

from __future__ import annotations

from typing import Any

import voluptuous as vol
from homeassistant.config_entries import ConfigEntry, ConfigFlow, OptionsFlowWithReload
from homeassistant.core import callback
from homeassistant.helpers.selector import (
    BooleanSelector,
    EntitySelector,
    EntitySelectorConfig,
    NumberSelector,
    NumberSelectorConfig,
    NumberSelectorMode,
    SelectOptionDict,
    SelectSelector,
    SelectSelectorConfig,
    TextSelector,
    TextSelectorConfig,
    TextSelectorType,
)

from .capability import CapabilitySummary, async_inspect_entity
from .const import (
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
    DEFAULT_END_GRACE,
    DEFAULT_END_THRESHOLD,
    DEFAULT_HALF_LIFE,
    DEFAULT_NAME,
    DEFAULT_RESTORE_SESSION,
    DEFAULT_SOURCE_REVISION,
    DOMAIN,
    StrategyMode,
)

STAGE_ADD_ANOTHER = "add_another"
STAGE_ADD_STAGES = "add_stages"
STAGE_CLEAR_ALL = "clear_all_stages"
STAGE_DONE = "done_adding_stages"

# Maps raw strategy enum values to human-readable labels for UI display.
_STRATEGY_LABELS: dict[str, str] = {
    StrategyMode.AUTO.value: "Automatic",
    StrategyMode.NATIVE_OCCUPANCY.value: "Native occupancy",
    StrategyMode.CONTINUOUS_MOTION.value: "Continuous motion",
    StrategyMode.EVENT_ONLY.value: "Event-only motion",
    StrategyMode.HYBRID.value: "Hybrid occupancy + motion",
}


def _suggested_options(config_entry: ConfigEntry, key: str, default: Any) -> Any:
    if key in config_entry.options:
        return config_entry.options[key]
    return config_entry.data.get(key, default)


def build_entry_data(
    *,
    name: str,
    source_entity: str,
    source_revision: int = DEFAULT_SOURCE_REVISION,
) -> dict[str, Any]:
    """Return config-entry data for setup identity fields."""
    return {
        CONF_NAME: name,
        CONF_SOURCE_ENTITY: source_entity,
        CONF_SOURCE_REVISION: source_revision,
    }


def build_entry_options(
    *,
    strategy: str,
    default_half_life: int,
    end_threshold: int,
    end_grace: int,
    restore_session: bool,
    stages: list[dict[str, Any]],
) -> dict[str, Any]:
    """Return config-entry options for runtime tuning fields."""
    return {
        CONF_STRATEGY: strategy,
        CONF_DEFAULT_HALF_LIFE: default_half_life,
        CONF_END_THRESHOLD: end_threshold,
        CONF_END_GRACE: end_grace,
        CONF_RESTORE_SESSION: restore_session,
        CONF_STAGES: stages,
    }


def validate_stage_payload(
    stage: dict[str, Any],
    existing_stages: list[dict[str, Any]],
) -> dict[str, Any]:
    """Validate one stage against existing stage definitions."""
    raw_min_duration = stage[CONF_STAGE_MIN_DURATION]
    if not isinstance(raw_min_duration, (int, str)):
        raise ValueError("invalid_stage_range")
    min_duration = int(raw_min_duration)

    raw_max_duration = stage.get(CONF_STAGE_MAX_DURATION)
    max_duration: int | None
    if raw_max_duration in ("", None):
        max_duration = None
    elif not isinstance(raw_max_duration, (int, str)):
        raise ValueError("invalid_stage_range")
    elif int(raw_max_duration) <= min_duration:
        raise ValueError("invalid_stage_range")
    else:
        max_duration = int(raw_max_duration)

    raw_half_life = stage.get(CONF_STAGE_HALF_LIFE)
    if raw_half_life in ("", None):
        half_life: int | None = None
    elif not isinstance(raw_half_life, (int, str)):
        raise ValueError("invalid_stage_range")
    else:
        half_life = int(raw_half_life)

    normalised = {
        CONF_STAGE_ID: str(stage[CONF_STAGE_ID]).strip(),
        CONF_STAGE_NAME: str(stage[CONF_STAGE_NAME]).strip(),
        CONF_STAGE_MIN_DURATION: min_duration,
        CONF_STAGE_MAX_DURATION: max_duration,
        CONF_STAGE_HALF_LIFE: half_life,
    }

    if not normalised[CONF_STAGE_ID] or not normalised[CONF_STAGE_NAME]:
        raise ValueError("invalid_stage_range")

    for existing in existing_stages:
        existing_min = existing[CONF_STAGE_MIN_DURATION]
        existing_max = existing.get(CONF_STAGE_MAX_DURATION)
        new_min = normalised[CONF_STAGE_MIN_DURATION]
        new_max = normalised[CONF_STAGE_MAX_DURATION]
        if existing_max is None:
            # Existing stage is open-ended: covers [existing_min, ∞).
            # New stage overlaps unless it ends at or before existing_min.
            if new_max is None or new_max > existing_min:
                raise ValueError("stage_overlap")
        elif new_min < existing_max and (new_max is None or new_max > existing_min):
            raise ValueError("stage_overlap")

    return normalised


def source_change_requires_reset(config_entry: ConfigEntry, new_source_entity: str) -> tuple[bool, int]:
    """Return whether changing source should bump the source revision."""
    old_source = config_entry.data.get(CONF_SOURCE_ENTITY)
    revision = int(config_entry.data.get(CONF_SOURCE_REVISION, DEFAULT_SOURCE_REVISION))
    if old_source == new_source_entity:
        return False, revision
    return True, revision + 1


def _strategy_selector() -> SelectSelector:
    # label uses human-readable name so the selector is intelligible without translations loaded.
    return SelectSelector(
        SelectSelectorConfig(
            options=[
                SelectOptionDict(value=mode.value, label=_STRATEGY_LABELS[mode.value])
                for mode in StrategyMode
            ],
            translation_key="strategy",
        )
    )


def _entity_selector() -> EntitySelector:
    return EntitySelector(
        EntitySelectorConfig(
            domain=["binary_sensor", "sensor", "event"],
            multiple=False,
        )
    )


def _capability_summary_text(summary: CapabilitySummary) -> str:
    return "\n".join(summary.preview_lines)


class OccupancyDurationConfigFlow(ConfigFlow, domain=DOMAIN):
    """Handle the Occupancy Duration Helper config flow."""

    VERSION = 1
    MINOR_VERSION = 1

    def __init__(self) -> None:
        self._name = DEFAULT_NAME
        self._source_entity: str | None = None
        self._strategy = StrategyMode.AUTO.value
        self._default_half_life = DEFAULT_HALF_LIFE
        self._end_threshold = DEFAULT_END_THRESHOLD
        self._end_grace = DEFAULT_END_GRACE
        self._restore_session = DEFAULT_RESTORE_SESSION
        self._stages: list[dict[str, Any]] = []
        self._capability_summary: CapabilitySummary | None = None

    @staticmethod
    @callback
    def async_get_options_flow(config_entry: ConfigEntry) -> OptionsFlowWithReload:
        return OccupancyDurationOptionsFlow(config_entry)

    def _current_entries_for_source(self, source_entity: str) -> list[ConfigEntry]:
        return [
            entry
            for entry in self._async_current_entries()
            if entry.data.get(CONF_SOURCE_ENTITY) == source_entity
        ]

    def is_matching(self, other_flow: ConfigFlow) -> bool:
        """Return whether another in-progress flow targets the same source entity."""
        if not isinstance(other_flow, OccupancyDurationConfigFlow):
            return False
        self_src = self._source_entity
        other_src = getattr(other_flow, "_source_entity", None)
        # Only match when both flows have selected an entity (None != None is false-positive).
        return self_src is not None and self_src == other_src

    async def async_step_user(self, user_input: dict[str, Any] | None = None):
        errors: dict[str, str] = {}

        if user_input is not None:
            name = user_input[CONF_NAME].strip()
            source_entity = user_input[CONF_SOURCE_ENTITY]

            if self._current_entries_for_source(source_entity):
                errors[CONF_SOURCE_ENTITY] = "source_already_configured"
            else:
                self._name = name
                self._source_entity = source_entity
                self._capability_summary = await async_inspect_entity(self.hass, source_entity)
                return await self.async_step_capability_preview()

        data_schema = vol.Schema(
            {
                vol.Required(CONF_NAME, default=self._name): TextSelector(
                    TextSelectorConfig(type=TextSelectorType.TEXT)
                ),
                vol.Required(CONF_SOURCE_ENTITY): _entity_selector(),
            }
        )
        return self.async_show_form(step_id="user", data_schema=data_schema, errors=errors)

    async def async_step_capability_preview(self, user_input: dict[str, Any] | None = None):
        if self._capability_summary is None:
            return await self.async_step_user()

        if user_input is not None:
            return await self.async_step_strategy()

        return self.async_show_form(
            step_id="capability_preview",
            data_schema=vol.Schema({}),
            description_placeholders={
                "summary": _capability_summary_text(self._capability_summary),
                "strategy": _STRATEGY_LABELS.get(
                    self._capability_summary.recommended_strategy.value,
                    self._capability_summary.recommended_strategy.value,
                ),
            },
        )

    async def async_step_strategy(self, user_input: dict[str, Any] | None = None):
        if user_input is not None:
            self._strategy = user_input[CONF_STRATEGY]
            return await self.async_step_decay()

        recommended = (
            self._capability_summary.recommended_strategy.value
            if self._capability_summary is not None
            else StrategyMode.AUTO.value
        )
        data_schema = vol.Schema(
            {
                vol.Required(CONF_STRATEGY, default=recommended): _strategy_selector(),
            }
        )
        return self.async_show_form(step_id="strategy", data_schema=data_schema)

    async def async_step_decay(self, user_input: dict[str, Any] | None = None):
        if user_input is not None:
            self._default_half_life = int(user_input[CONF_DEFAULT_HALF_LIFE])
            self._end_threshold = int(user_input[CONF_END_THRESHOLD])
            self._end_grace = int(user_input[CONF_END_GRACE])
            self._restore_session = bool(user_input[CONF_RESTORE_SESSION])
            add_stages = bool(user_input[STAGE_ADD_STAGES])
            if add_stages:
                return await self.async_step_stage()

            return self._create_entry()

        data_schema = vol.Schema(
            {
                vol.Required(CONF_DEFAULT_HALF_LIFE, default=self._default_half_life): NumberSelector(
                    NumberSelectorConfig(min=1, max=3600, mode=NumberSelectorMode.BOX)
                ),
                vol.Required(CONF_END_THRESHOLD, default=self._end_threshold): NumberSelector(
                    NumberSelectorConfig(min=0, max=100, mode=NumberSelectorMode.SLIDER)
                ),
                vol.Required(CONF_END_GRACE, default=self._end_grace): NumberSelector(
                    NumberSelectorConfig(min=0, max=600, mode=NumberSelectorMode.BOX)
                ),
                vol.Required(CONF_RESTORE_SESSION, default=self._restore_session): BooleanSelector(),
                vol.Required(STAGE_ADD_STAGES, default=False): BooleanSelector(),
            }
        )
        return self.async_show_form(step_id="decay", data_schema=data_schema)

    async def async_step_stage(self, user_input: dict[str, Any] | None = None):
        errors: dict[str, str] = {}

        if user_input is not None:
            try:
                stage = validate_stage_payload(user_input, self._stages)
            except ValueError as err:
                errors["base"] = str(err)
            else:
                self._stages.append(stage)
                if bool(user_input[STAGE_ADD_ANOTHER]):
                    return await self.async_step_stage()
                return self._create_entry()

        data_schema = vol.Schema(
            {
                vol.Required(CONF_STAGE_ID): TextSelector(TextSelectorConfig(type=TextSelectorType.TEXT)),
                vol.Required(CONF_STAGE_NAME): TextSelector(TextSelectorConfig(type=TextSelectorType.TEXT)),
                vol.Required(CONF_STAGE_MIN_DURATION): NumberSelector(
                    NumberSelectorConfig(min=0, max=86400, mode=NumberSelectorMode.BOX)
                ),
                vol.Optional(CONF_STAGE_MAX_DURATION): NumberSelector(
                    NumberSelectorConfig(min=1, max=86400, mode=NumberSelectorMode.BOX)
                ),
                vol.Optional(CONF_STAGE_HALF_LIFE): NumberSelector(
                    NumberSelectorConfig(min=1, max=86400, mode=NumberSelectorMode.BOX)
                ),
                vol.Required(STAGE_ADD_ANOTHER, default=False): BooleanSelector(),
            }
        )
        return self.async_show_form(step_id="stage", data_schema=data_schema, errors=errors)

    async def async_step_reconfigure(self, user_input: dict[str, Any] | None = None):
        config_entry = self._get_reconfigure_entry()
        errors: dict[str, str] = {}

        if user_input is not None:
            source_entity = user_input[CONF_SOURCE_ENTITY]
            conflicting = [
                entry
                for entry in self._current_entries_for_source(source_entity)
                if entry.entry_id != config_entry.entry_id
            ]
            if conflicting:
                errors[CONF_SOURCE_ENTITY] = "source_already_configured"
            else:
                _, revision = source_change_requires_reset(config_entry, source_entity)
                return self.async_update_reload_and_abort(
                    config_entry,
                    data_updates=build_entry_data(
                        name=user_input[CONF_NAME].strip(),
                        source_entity=source_entity,
                        source_revision=revision,
                    ),
                    reason="reconfigure_successful",
                )

        data_schema = vol.Schema(
            {
                vol.Required(CONF_NAME, default=config_entry.title): TextSelector(
                    TextSelectorConfig(type=TextSelectorType.TEXT)
                ),
                vol.Required(
                    CONF_SOURCE_ENTITY,
                    default=config_entry.data.get(CONF_SOURCE_ENTITY),
                ): _entity_selector(),
            }
        )
        return self.async_show_form(step_id="reconfigure", data_schema=data_schema, errors=errors)

    def _create_entry(self):
        if not self._source_entity:
            raise RuntimeError("_create_entry called before source_entity was set")
        options = build_entry_options(
            strategy=self._strategy,
            default_half_life=self._default_half_life,
            end_threshold=self._end_threshold,
            end_grace=self._end_grace,
            restore_session=self._restore_session,
            stages=self._stages,
        )
        return self.async_create_entry(
            title=self._name,
            data=build_entry_data(name=self._name, source_entity=self._source_entity),
            options=options,
        )


class OccupancyDurationOptionsFlow(OptionsFlowWithReload):
    """Manage runtime options for the Occupancy Duration Helper integration."""

    def __init__(self, config_entry: ConfigEntry) -> None:
        self._config_entry = config_entry
        self._stages: list[dict[str, Any]] = list(config_entry.options.get(CONF_STAGES, []))

    def _stages_summary(self) -> str:
        if not self._stages:
            return "None configured"
        lines = []
        for s in self._stages:
            name = s.get(CONF_STAGE_NAME) or s.get(CONF_STAGE_ID, "?")
            min_d = s.get(CONF_STAGE_MIN_DURATION, 0)
            max_d = s.get(CONF_STAGE_MAX_DURATION)
            max_str = f"{max_d}s" if max_d else "\u221e"
            lines.append(f"\u2022 {name}: {min_d}\u2013{max_str}")
        return "\n".join(lines)

    async def async_step_init(self, user_input: dict[str, Any] | None = None):
        errors: dict[str, str] = {}

        if user_input is not None:
            if user_input.get(STAGE_CLEAR_ALL):
                self._stages = []
            if user_input.get(STAGE_ADD_STAGES):
                return await self.async_step_stage()
            return self.async_create_entry(
                data=build_entry_options(
                    strategy=user_input[CONF_STRATEGY],
                    default_half_life=int(user_input[CONF_DEFAULT_HALF_LIFE]),
                    end_threshold=int(user_input[CONF_END_THRESHOLD]),
                    end_grace=int(user_input[CONF_END_GRACE]),
                    restore_session=bool(user_input[CONF_RESTORE_SESSION]),
                    stages=self._stages,
                )
            )

        data_schema = vol.Schema(
            {
                vol.Required(
                    CONF_STRATEGY,
                    default=_suggested_options(self._config_entry, CONF_STRATEGY, StrategyMode.AUTO.value),
                ): _strategy_selector(),
                vol.Required(
                    CONF_DEFAULT_HALF_LIFE,
                    default=_suggested_options(self._config_entry, CONF_DEFAULT_HALF_LIFE, DEFAULT_HALF_LIFE),
                ): NumberSelector(NumberSelectorConfig(min=1, max=3600, mode=NumberSelectorMode.BOX)),
                vol.Required(
                    CONF_END_THRESHOLD,
                    default=_suggested_options(self._config_entry, CONF_END_THRESHOLD, DEFAULT_END_THRESHOLD),
                ): NumberSelector(NumberSelectorConfig(min=0, max=100, mode=NumberSelectorMode.SLIDER)),
                vol.Required(
                    CONF_END_GRACE,
                    default=_suggested_options(self._config_entry, CONF_END_GRACE, DEFAULT_END_GRACE),
                ): NumberSelector(NumberSelectorConfig(min=0, max=600, mode=NumberSelectorMode.BOX)),
                vol.Required(
                    CONF_RESTORE_SESSION,
                    default=_suggested_options(self._config_entry, CONF_RESTORE_SESSION, DEFAULT_RESTORE_SESSION),
                ): BooleanSelector(),
                vol.Required(STAGE_ADD_STAGES, default=False): BooleanSelector(),
                vol.Required(STAGE_CLEAR_ALL, default=False): BooleanSelector(),
            }
        )
        return self.async_show_form(
            step_id="init",
            data_schema=data_schema,
            errors=errors,
            description_placeholders={"current_stages": self._stages_summary()},
        )

    async def async_step_stage(self, user_input: dict[str, Any] | None = None):
        errors: dict[str, str] = {}

        if user_input is not None:
            if user_input.get(STAGE_DONE):
                return await self.async_step_init()
            try:
                stage = validate_stage_payload(user_input, self._stages)
            except ValueError as err:
                errors["base"] = str(err)
            else:
                self._stages.append(stage)
                if bool(user_input[STAGE_ADD_ANOTHER]):
                    return await self.async_step_stage()
                return await self.async_step_init()

        data_schema = vol.Schema(
            {
                vol.Required(CONF_STAGE_ID): TextSelector(TextSelectorConfig(type=TextSelectorType.TEXT)),
                vol.Required(CONF_STAGE_NAME): TextSelector(TextSelectorConfig(type=TextSelectorType.TEXT)),
                vol.Required(CONF_STAGE_MIN_DURATION): NumberSelector(
                    NumberSelectorConfig(min=0, max=86400, mode=NumberSelectorMode.BOX)
                ),
                vol.Optional(CONF_STAGE_MAX_DURATION): NumberSelector(
                    NumberSelectorConfig(min=1, max=86400, mode=NumberSelectorMode.BOX)
                ),
                vol.Optional(CONF_STAGE_HALF_LIFE): NumberSelector(
                    NumberSelectorConfig(min=1, max=86400, mode=NumberSelectorMode.BOX)
                ),
                vol.Required(STAGE_ADD_ANOTHER, default=False): BooleanSelector(),
                vol.Required(STAGE_DONE, default=False): BooleanSelector(),
            }
        )
        return self.async_show_form(step_id="stage", data_schema=data_schema, errors=errors)