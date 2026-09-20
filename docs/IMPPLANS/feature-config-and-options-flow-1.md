---
goal: Design the setup, reconfigure, and options user flows for Occupancy Duration Helper
version: 1.0
date_created: 2026-09-20
last_updated: 2026-09-20
owner: tamaysgz
status: 'Completed'
tags: [feature, ui, config-flow, translations, home-assistant]
---

![Status: Completed](https://img.shields.io/badge/status-Completed-brightgreen)

# Config And Options Flow Plan

## Section 1 - Requirements & Constraints

- **REQ-001**: Implement a guided setup flow in `custom_components/occupancy_duration/config_flow.py` that covers name, source entity, capability preview, recommended strategy, decay defaults, end-threshold, end-grace, restore behavior, and optional stages.
- **REQ-002**: Use Home Assistant selectors instead of free-form text wherever possible, including an entity selector for source entities.
- **REQ-003**: Surface capability findings and a recommended strategy before entry creation.
- **REQ-004**: Externalize all user-facing text into `custom_components/occupancy_duration/strings.json` and `custom_components/occupancy_duration/translations/en.json`.
- **REQ-005**: Support post-install editing of configuration while aligning with current Home Assistant guidance: use `reconfigure` for mutable setup data and `OptionsFlow` for runtime tuning.
- **REQ-006**: Prevent invalid stage definitions, overlapping or inverted duration ranges, invalid numeric thresholds, and stale-session reuse after source changes.
- **REQ-007**: Preserve explicit user strategy overrides and surface when auto mode is disabled by user choice.
- **CON-001**: The flow must consume capability summaries from `custom_components/occupancy_duration/capability.py`; it must not duplicate inspection logic inside the UI layer.
- **CON-002**: Current Home Assistant guidance states that non-optional setup data should not be modeled as generic options when `reconfigure` is a better fit.
- **PAT-001**: Keep the first-run flow safe for average users by providing sensible defaults and concise recommendations, while still exposing custom values.

## Section 2 - Implementation Steps

### Implementation Phase 1 - Flow Contract And Storage Schema

- **GOAL-001**: Define what is stored as config-entry data versus options before building UI steps.

| Task | Description | Completed | Date |
|---|---|---|---|
| TASK-001 | Extend `custom_components/occupancy_duration/const.py` with config keys for source entity, strategy mode, default half-life, end-threshold, end-grace, restore policy, and stages. | ✅ | 2026-09-20 |
| TASK-002 | Define a storage split in `custom_components/occupancy_duration/config_flow.py` where required setup identity fields live in config-entry data and runtime-tuning fields live in options. | ✅ | 2026-09-20 |
| TASK-003 | Define stage-schema validation helpers in `custom_components/occupancy_duration/config_flow.py` or a closely related helper module so stage ordering and range correctness are enforced centrally. | ✅ | 2026-09-20 |

### Implementation Phase 2 - Initial Config Flow

- **GOAL-002**: Build the guided first-run flow with selectors and capability previews.

| Task | Description | Completed | Date |
|---|---|---|---|
| TASK-004 | Implement the `user` and follow-on steps in `custom_components/occupancy_duration/config_flow.py` for name and source-entity selection using Home Assistant selectors. | ✅ | 2026-09-20 |
| TASK-005 | Implement a capability-preview step in `custom_components/occupancy_duration/config_flow.py` that reads the exported summary from `custom_components/occupancy_duration/capability.py` and shows the recommended strategy. | ✅ | 2026-09-20 |
| TASK-006 | Implement strategy, decay, threshold, grace, restore, and optional stage-configuration steps in `custom_components/occupancy_duration/config_flow.py`, including sensible defaults and a custom half-life path. | ✅ | 2026-09-20 |

### Implementation Phase 3 - Reconfigure And Options Editing

- **GOAL-003**: Align mutable settings with current Home Assistant UX guidance.

| Task | Description | Completed | Date |
|---|---|---|---|
| TASK-007 | Implement `async_step_reconfigure` in `custom_components/occupancy_duration/config_flow.py` for setup-identity changes such as helper name and source entity, using `async_update_reload_and_abort` on success. | ✅ | 2026-09-20 |
| TASK-008 | Implement `OptionsFlow` in `custom_components/occupancy_duration/config_flow.py` or a dedicated options helper for runtime tuning fields such as strategy override, decay values, restore policy, and stages. | ✅ | 2026-09-20 |
| TASK-009 | Implement source-change handling in the flow layer so existing session state is explicitly invalidated and never silently migrated across different source semantics. | ✅ | 2026-09-20 |

### Implementation Phase 4 - Translations And Tests

- **GOAL-004**: Make the UI translatable and verifiable.

| Task | Description | Completed | Date |
|---|---|---|---|
| TASK-010 | Create `custom_components/occupancy_duration/strings.json` and `custom_components/occupancy_duration/translations/en.json` covering config steps, reconfigure, options, errors, aborts, and capability-summary labels. | ✅ | 2026-09-20 |
| TASK-011 | Create `tests/test_config_flow.py` with cases for happy-path setup, validation errors, source-change handling, manual strategy override persistence, and reconfigure-versus-options behavior. | ✅ | 2026-09-20 |

## Section 3 - Alternatives

- **ALT-001**: Use `SchemaConfigFlowHandler` for the whole flow - Rejected because the PRD requires a multi-step experience with preview, custom validation, and explicit source-change handling.
- **ALT-002**: Store all mutable values in `OptionsFlow` only - Rejected because current Home Assistant guidance recommends `reconfigure` for non-optional setup data.
- **ALT-003**: Hardcode English text in `config_flow.py` - Rejected because both the PRD and Home Assistant conventions require translation-driven UI strings.

## Section 4 - Dependencies

- **DEP-001**: [./feature-capability-and-strategy-1.md](./feature-capability-and-strategy-1.md) - Provides capability summaries and strategy recommendations.
- **DEP-002**: [../PRD/initial_prd.md](../PRD/initial_prd.md) - Defines the required user experience and editing capabilities.
- **DEP-003**: [../PRD/initial_hacs_setup.md](../PRD/initial_hacs_setup.md) - Defines required config-flow, options-flow, and translation coverage.
- **DEP-004**: `https://developers.home-assistant.io/docs/core/integration/config_flow/` - Current guidance for `reconfigure`, `OptionsFlow`, titles, and translations.

## Section 5 - Files

- **FILE-001**: `custom_components/occupancy_duration/config_flow.py` - created - Implement setup, reconfigure, and options editing flows.
- **FILE-002**: `custom_components/occupancy_duration/strings.json` - created - Define config and options translation keys.
- **FILE-003**: `custom_components/occupancy_duration/translations/en.json` - created - Provide synchronized English translations.
- **FILE-004**: `custom_components/occupancy_duration/const.py` - created or modified - Store shared flow keys and defaults.
- **FILE-005**: `tests/test_config_flow.py` - created - Verify the flow contract and validation behavior.

## Section 6 - Testing

- **TEST-001**: `tests/test_config_flow.py` verifies that a user can complete the initial flow with a valid source entity and default settings.
- **TEST-002**: `tests/test_config_flow.py` verifies that invalid stage definitions are rejected with translation-backed error keys.
- **TEST-003**: `tests/test_config_flow.py` verifies that `reconfigure` updates an existing entry and does not create a second entry.
- **TEST-004**: `tests/test_config_flow.py` verifies that `OptionsFlow` changes runtime tuning without mutating source identity fields.
- **TEST-005**: `strings.json` and `translations/en.json` contain synchronized keys for every config, reconfigure, and options step used by the flow.

## Section 7 - Risks & Assumptions

- **RISK-001**: Mixing setup identity fields and runtime tuning fields can lead to confusing UI if stored in the wrong place - Mitigation: define the data/options split before writing forms and test both flows explicitly.
- **RISK-002**: Source-entity changes can accidentally revive stale session state - Mitigation: make source change an explicit invalidation path and verify it in tests.
- **ASSUMPTION-001**: The target Home Assistant version supports the entity selectors needed for the planned source selection experience.
- **ASSUMPTION-002**: Users benefit from a guided staged UI more than from a single dense form.

## Section 8 - Related Specifications / Further Reading

- [../PRD/initial_prd.md](../PRD/initial_prd.md) - Source for the end-user flow, strategy recommendations, and editing needs.
- [../PRD/initial_hacs_setup.md](../PRD/initial_hacs_setup.md) - Source for config flow, translation, and options-flow requirements.
- [https://developers.home-assistant.io/docs/core/integration/config_flow/](https://developers.home-assistant.io/docs/core/integration/config_flow/) - Current guidance for config entries, reconfigure, and translations.