---
goal: Define entity exposure, persistence, restore behavior, diagnostics, and events for Occupancy Duration Helper
version: 1.0
date_created: 2026-09-20
last_updated: 2026-09-20
owner: tamaysgz
status: 'Planned'
tags: [feature, entities, persistence, diagnostics, events]
---

![Status: Planned](https://img.shields.io/badge/status-Planned-blue)

# Entities, Persistence, And Observability Plan

## Section 1 - Requirements & Constraints

- **REQ-001**: Expose a duration sensor in `custom_components/occupancy_duration/sensor.py` with a numeric duration state and session metadata attributes.
- **REQ-002**: Expose an occupancy binary sensor in `custom_components/occupancy_duration/binary_sensor.py` using the Home Assistant `occupancy` device class.
- **REQ-003**: Expose a stage sensor only when stages are configured.
- **REQ-004**: Wire all runtime updates through config-entry lifecycle management in `custom_components/occupancy_duration/__init__.py` and `custom_components/occupancy_duration/coordinator.py`.
- **REQ-005**: Persist enough session state in `custom_components/occupancy_duration/storage.py` to restore active or decaying sessions across Home Assistant restarts.
- **REQ-006**: On restore, re-detect capabilities, inspect current source state when possible, recalculate elapsed wall-clock time, and resume or close the session safely.
- **REQ-007**: Export diagnostics in `custom_components/occupancy_duration/diagnostics.py` covering source, capabilities, strategy, state, score, stage, last activity, and decay settings.
- **REQ-008**: Emit Home Assistant events for session start, stage change, and session end with stable payload fields.
- **REQ-009**: Clean unload must stop listeners, release coordinator resources, and remove config-entry data without leaving stale entities behind.
- **CON-001**: The entity layer depends on stable contracts from the capability, session, and config-flow plans; it must not redefine those models.
- **CON-002**: Source unavailability must not be treated as equivalent to explicit inactivity during restore or steady-state runtime.

## Section 2 - Implementation Steps

### Implementation Phase 1 - Lifecycle And Coordinator Contracts

- **GOAL-001**: Establish the runtime shell that owns config-entry setup, unload, and entity synchronization.

| Task | Description | Completed | Date |
|---|---|---|---|
| TASK-001 | Create `custom_components/occupancy_duration/__init__.py` with `async_setup_entry`, `async_unload_entry`, and config-entry listener registration for platforms and runtime services. |  |  |
| TASK-002 | Create `custom_components/occupancy_duration/coordinator.py` with a coordinator or shared runtime manager that bridges source updates, session evaluation, persistence, and entity refresh signals. |  |  |
| TASK-003 | Define the in-memory entry state container in `custom_components/occupancy_duration/coordinator.py` so entities, diagnostics, and storage read the same authoritative runtime snapshot. |  |  |

### Implementation Phase 2 - Entity Platforms

- **GOAL-002**: Surface the session model as native Home Assistant entities.

| Task | Description | Completed | Date |
|---|---|---|---|
| TASK-004 | Create `custom_components/occupancy_duration/sensor.py` with the duration sensor and conditional stage sensor, including unique IDs and attributes aligned with PRD requirements. |  |  |
| TASK-005 | Create `custom_components/occupancy_duration/binary_sensor.py` with the occupancy binary sensor using `device_class=occupancy` and runtime state derived from the session model. |  |  |
| TASK-006 | Decide whether optional diagnostic entities belong in `sensor.py` or a later dedicated platform and document that decision in code comments or module structure without exposing them by default. |  |  |

### Implementation Phase 3 - Persistence And Restore

- **GOAL-003**: Persist and restore sessions safely across restarts and source instability.

| Task | Description | Completed | Date |
|---|---|---|---|
| TASK-007 | Create `custom_components/occupancy_duration/storage.py` using Home Assistant supported storage mechanisms to serialize `session_id`, timestamps, score, stage, and state per config entry. |  |  |
| TASK-008 | Implement restore orchestration in `custom_components/occupancy_duration/__init__.py` or `custom_components/occupancy_duration/coordinator.py` that re-detects capabilities and recalculates session state before entities are refreshed. |  |  |
| TASK-009 | Implement source-unavailable handling in `custom_components/occupancy_duration/storage.py` and `custom_components/occupancy_duration/coordinator.py` so restore does not incorrectly close sessions when state cannot be read. |  |  |

### Implementation Phase 4 - Diagnostics And Events

- **GOAL-004**: Make the integration explainable and automation-friendly.

| Task | Description | Completed | Date |
|---|---|---|---|
| TASK-010 | Create `custom_components/occupancy_duration/diagnostics.py` returning a sanitized diagnostics payload with source, capability, strategy, session, and decay information. |  |  |
| TASK-011 | Emit `occupancy_duration_started`, `occupancy_duration_stage_changed`, and `occupancy_duration_ended` from coordinator or session transition hooks with stable payload fields. |  |  |
| TASK-012 | Create `tests/test_sensor.py` and `tests/test_restore.py` covering entity creation, attribute correctness, restore behavior, unavailable-source handling, diagnostics shape, and event emission order. |  |  |

## Section 3 - Alternatives

- **ALT-001**: Persist session state in an arbitrary root-level file - Rejected because the PRD requires supported Home Assistant storage mechanisms.
- **ALT-002**: Expose stage only as a duration-sensor attribute - Rejected because the PRD explicitly calls for a dedicated stage sensor when stages are configured.
- **ALT-003**: Treat source unavailability as an OFF or clear state - Rejected because the PRD explicitly forbids that interpretation.

## Section 4 - Dependencies

- **DEP-001**: [./feature-capability-and-strategy-1.md](./feature-capability-and-strategy-1.md) - Provides capability and strategy state included in diagnostics and restore.
- **DEP-002**: [./feature-session-and-decay-engine-1.md](./feature-session-and-decay-engine-1.md) - Provides the session model and transition semantics exposed by entities.
- **DEP-003**: [./feature-config-and-options-flow-1.md](./feature-config-and-options-flow-1.md) - Provides persisted config shape and source-change invalidation behavior.
- **DEP-004**: [../PRD/initial_prd.md](../PRD/initial_prd.md) - Source for entities, events, diagnostics, and restore requirements.
- **DEP-005**: [../PRD/initial_hacs_setup.md](../PRD/initial_hacs_setup.md) - Source for persistence, diagnostics, and platform file expectations.

## Section 5 - Files

- **FILE-001**: `custom_components/occupancy_duration/__init__.py` - created - Implement config-entry setup, unload, and restore hooks.
- **FILE-002**: `custom_components/occupancy_duration/coordinator.py` - created - Implement the shared runtime and entity update bridge.
- **FILE-003**: `custom_components/occupancy_duration/sensor.py` - created - Implement duration and stage sensors.
- **FILE-004**: `custom_components/occupancy_duration/binary_sensor.py` - created - Implement the occupancy binary sensor.
- **FILE-005**: `custom_components/occupancy_duration/storage.py` - created - Implement session persistence and restore helpers.
- **FILE-006**: `custom_components/occupancy_duration/diagnostics.py` - created - Implement sanitized diagnostics export.
- **FILE-007**: `tests/test_sensor.py` - created - Verify entity state and attributes.
- **FILE-008**: `tests/test_restore.py` - created - Verify restore, diagnostics, and event behavior.

## Section 6 - Testing

- **TEST-001**: `tests/test_sensor.py` verifies duration sensor state, occupancy binary-sensor state, and conditional stage-sensor creation.
- **TEST-002**: `tests/test_restore.py` verifies that an active session with a still-active source restores without decaying.
- **TEST-003**: `tests/test_restore.py` verifies that an unavailable source during restore does not immediately close the session.
- **TEST-004**: Diagnostics output contains all required sections and excludes unrelated secrets or sensitive data.
- **TEST-005**: Event listeners observe start, stage-change, and end events in the expected order with complete payload keys.

## Section 7 - Risks & Assumptions

- **RISK-001**: Event emission can drift from the true transition point if fired from the wrong layer - Mitigation: emit events directly from transition-confirmation hooks instead of from UI or entity code.
- **RISK-002**: Restore ordering can briefly expose stale entity state during startup - Mitigation: delay first entity refresh until restore and source revalidation finish.
- **ASSUMPTION-001**: Home Assistant storage helpers used by custom integrations remain available in the targeted minimum version.
- **ASSUMPTION-002**: A single coordinator or runtime manager per config entry is sufficient for MVP-scale performance.

## Section 8 - Related Specifications / Further Reading

- [../PRD/initial_prd.md](../PRD/initial_prd.md) - Source for entity, persistence, diagnostics, and event requirements.
- [../PRD/initial_hacs_setup.md](../PRD/initial_hacs_setup.md) - Source for platform, persistence, and diagnostics file expectations.
- [https://github.com/jpawlowski/hacs.integration_blueprint](https://github.com/jpawlowski/hacs.integration_blueprint) - Reference for coordinator, diagnostics, and modern custom-integration structure.