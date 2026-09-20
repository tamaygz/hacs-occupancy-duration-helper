---
goal: Define the occupancy session lifecycle, scoring, decay model, and duration-stage behavior
version: 1.0
date_created: 2026-09-20
last_updated: 2026-09-20
owner: tamaysgz
status: 'Completed'
tags: [feature, runtime, session, decay, stages]
---

![Status: Completed](https://img.shields.io/badge/status-Completed-brightgreen)

# Session And Decay Engine Plan

## Section 1 - Requirements & Constraints

- **REQ-001**: Implement a session state machine in `custom_components/occupancy_duration/session.py` with the states `IDLE`, `ACTIVE`, `DECAYING`, `ENDING`, and `CLOSED`.
- **REQ-002**: Preserve `started_at` across reinforcement and `DECAYING -> ACTIVE` transitions; a session measures wall-clock interaction duration, not time since the last event.
- **REQ-003**: Track `session_id`, `started_at`, `last_activity_at`, `last_active_signal_at`, `ended_at`, `score`, `stage`, and `state` for every open or restorable session.
- **REQ-004**: Use exponential decay in `custom_components/occupancy_duration/decay.py` with a half-life model derived from elapsed wall-clock time.
- **REQ-005**: Never apply decay when the authoritative current source state still indicates activity, occupancy, or presence.
- **REQ-006**: Support per-stage decay behavior defined in `custom_components/occupancy_duration/stage.py`; stages are monotonic and never terminate a session by themselves.
- **REQ-007**: Support end-threshold and end-grace semantics so score below threshold moves to `ENDING`, and grace expiry moves to `CLOSED`.
- **REQ-008**: Design explicit runtime hooks for coordinator-driven tick evaluation without committing this plan to a high-frequency polling loop.
- **CON-001**: The runtime must work for continuous-state, explicit occupancy, and event-only source strategies defined by the capability plan.
- **CON-002**: No existing engine code exists; the plan must establish the domain model, transitions, and edge-case behavior explicitly.
- **PAT-001**: Use deterministic state-transition functions that accept explicit inputs such as `now`, `strategy`, `source_state`, and `stage_profile`.

## Section 2 - Implementation Steps

### Implementation Phase 1 - Session And Stage Domain Model

- **GOAL-001**: Define immutable data structures and transition inputs for session evaluation.

| Task | Description | Completed | Date |
|---|---|---|---|
| TASK-001 | Create `custom_components/occupancy_duration/session.py` with `OccupancySession`, `SessionState`, and explicit transition-result types for start, reinforce, decay, ending, and closure events. | ✅ | 2026-09-20 |
| TASK-002 | Create `custom_components/occupancy_duration/stage.py` with `DurationStage`, monotonic stage resolution helpers, and validation for contiguous or intentionally non-overlapping duration ranges. | ✅ | 2026-09-20 |
| TASK-003 | Extend `custom_components/occupancy_duration/const.py` with shared default values for half-life, end-threshold, end-grace, and score bounds. | ✅ | 2026-09-20 |

### Implementation Phase 2 - Decay Mathematics And Transition Rules

- **GOAL-002**: Implement mathematically stable score evolution and state transitions.

| Task | Description | Completed | Date |
|---|---|---|---|
| TASK-004 | Create `custom_components/occupancy_duration/decay.py` with an exponential decay function that accepts `score0`, `elapsed_seconds`, and `half_life_seconds` and returns a bounded score. | ✅ | 2026-09-20 |
| TASK-005 | Implement strategy-aware decay guards in `custom_components/occupancy_duration/decay.py` so readable active source states pause decay and optionally reinforce score. | ✅ | 2026-09-20 |
| TASK-006 | Implement state-transition helpers in `custom_components/occupancy_duration/session.py` for `activity_detected`, `source_became_inactive`, `decay_tick`, `score_below_threshold`, and `grace_expired`. | ✅ | 2026-09-20 |

### Implementation Phase 3 - Stage-Aware Runtime Evaluation

- **GOAL-003**: Make stage changes and decay behavior consistent for long-running sessions.

| Task | Description | Completed | Date |
|---|---|---|---|
| TASK-007 | Implement stage resolution in `custom_components/occupancy_duration/stage.py` so current duration selects a stage without ever regressing to a lower stage. | ✅ | 2026-09-20 |
| TASK-008 | Implement per-stage half-life selection in `custom_components/occupancy_duration/decay.py` so stage-specific decay overrides the default half-life only for future evaluations. | ✅ | 2026-09-20 |
| TASK-009 | Define a scheduler-facing evaluation contract in `custom_components/occupancy_duration/session.py` for use by `custom_components/occupancy_duration/coordinator.py`, including what inputs are required on each decay tick. | ✅ | 2026-09-20 |

### Implementation Phase 4 - Test Coverage And Edge Cases

- **GOAL-004**: Encode the PRD edge cases as repeatable tests before persistence and entities consume the engine.

| Task | Description | Completed | Date |
|---|---|---|---|
| TASK-010 | Create `tests/test_session.py` with cases covering session start, reinforcement without `started_at` reset, `DECAYING -> ACTIVE`, `ENDING -> CLOSED`, and new-session-after-closure behavior. | ✅ | 2026-09-20 |
| TASK-011 | Create `tests/test_decay.py` with cases covering active-state decay suppression, inactive-state decay application, event-only fallback, threshold transitions, and grace-period closure. | ✅ | 2026-09-20 |
| TASK-012 | Create `tests/test_stage.py` with cases covering monotonic stage progression, per-stage half-life selection, and long-duration stationary occupancy behavior. | ✅ | 2026-09-20 |

## Section 3 - Alternatives

- **ALT-001**: Use fixed decrement ticks instead of an exponential half-life model - Rejected because the PRD explicitly prefers elapsed-time-based decay and restart-safe math.
- **ALT-002**: Restart the session whenever new activity arrives after any decay - Rejected because the product requirement defines duration as continuous until closure.
- **ALT-003**: Let stage boundaries close or reopen sessions - Rejected because stage is descriptive and decay-driven, not the authority for session termination.

## Section 4 - Dependencies

- **DEP-001**: [./feature-capability-and-strategy-1.md](./feature-capability-and-strategy-1.md) - Provides the source strategy contract that the engine must obey.
- **DEP-002**: [../PRD/initial_prd.md](../PRD/initial_prd.md) - Defines the state machine, decay equation, and stage semantics.
- **DEP-003**: [../PRD/initial_hacs_setup.md](../PRD/initial_hacs_setup.md) - Defines file ownership for `session.py`, `decay.py`, and `stage.py`.

## Section 5 - Files

- **FILE-001**: `custom_components/occupancy_duration/session.py` - created - Implement session models and transition logic.
- **FILE-002**: `custom_components/occupancy_duration/decay.py` - created - Implement exponential decay and active-state suppression rules.
- **FILE-003**: `custom_components/occupancy_duration/stage.py` - created - Implement stage models and duration-to-stage resolution.
- **FILE-004**: `custom_components/occupancy_duration/const.py` - created or modified - Store shared runtime defaults and score boundaries.
- **FILE-005**: `custom_components/occupancy_duration/coordinator.py` - created or modified - Consume the runtime evaluation contract.
- **FILE-006**: `tests/test_session.py` - created - Verify state-machine behavior.
- **FILE-007**: `tests/test_decay.py` - created - Verify decay behavior.
- **FILE-008**: `tests/test_stage.py` - created - Verify stage behavior.

## Section 6 - Testing

- **TEST-001**: `tests/test_session.py` verifies that reinforcing activity never resets `started_at` for an open session.
- **TEST-002**: `tests/test_decay.py` verifies that readable active source states prevent decay even when the last event is old.
- **TEST-003**: `tests/test_decay.py` verifies that event-only strategies decay without fabricating a readable OFF state.
- **TEST-004**: `tests/test_stage.py` verifies that a session can progress from `SHORT` to `LONG` without ever returning to a lower stage.
- **TEST-005**: `tests/test_session.py` verifies that a closed session followed by new activity creates a new `session_id` and resets duration correctly.

## Section 7 - Risks & Assumptions

- **RISK-001**: Stage-specific half-life changes can cause unintuitive score jumps if applied retroactively - Mitigation: apply the new half-life only from the next evaluation forward.
- **RISK-002**: Aggressive decay-tick scheduling can become a performance problem when many helpers are active - Mitigation: define a coordinator contract that supports shared or adaptive scheduling.
- **ASSUMPTION-001**: The capability plan will provide a clear strategy mode for each helper before the engine evaluates decay.
- **ASSUMPTION-002**: UTC timestamps will be used internally to avoid daylight-saving and local-time discontinuities.

## Section 8 - Related Specifications / Further Reading

- [../PRD/initial_prd.md](../PRD/initial_prd.md) - Source for session, decay, and stage requirements.
- [../PRD/initial_hacs_setup.md](../PRD/initial_hacs_setup.md) - Source for session-engine, decay-engine, and stage file expectations.
- [./feature-capability-and-strategy-1.md](./feature-capability-and-strategy-1.md) - Required strategy contract dependency.