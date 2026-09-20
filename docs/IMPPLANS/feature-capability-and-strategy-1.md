---
goal: Define source capability inspection and runtime strategy selection for Occupancy Duration Helper
version: 1.0
date_created: 2026-09-20
last_updated: 2026-09-20
owner: tamaysgz
status: 'Completed'
tags: [feature, architecture, home-assistant, capability, strategy]
---

![Status: Completed](https://img.shields.io/badge/status-Completed-brightgreen)

# Capability And Strategy Plan

## Section 1 - Requirements & Constraints

- **REQ-001**: Implement a capability model in `custom_components/occupancy_duration/capability.py` that distinguishes current-state, motion, occupancy, presence, start-event, end-event, event-only, continuous-state, re-check, duration-exposure, and confidence dimensions.
- **REQ-002**: Represent certainty as `confirmed`, `inferred`, or `unknown`; do not collapse all capability findings to plain booleans.
- **REQ-003**: Inspect Home Assistant entity state, attributes, device registry metadata, entity registry metadata, and related entities on the same device before assigning a strategy.
- **REQ-004**: Do not infer capability solely from entity naming patterns such as `*_motion`.
- **REQ-005**: Support runtime strategy modes `AUTO`, `NATIVE_OCCUPANCY`, `CONTINUOUS_MOTION`, `EVENT_ONLY`, and `HYBRID`.
- **REQ-006**: Automatic strategy selection must prefer semantically richer signals in this order: explicit occupancy/presence, continuous presence, readable motion state, motion start/end semantics, event-only motion, generic state changes.
- **REQ-007**: A manual user override stored in config entry data or options must never be silently replaced by auto-detection on reload or restart.
- **REQ-008**: The capability subsystem must emit a structured summary consumable by `config_flow.py`, `diagnostics.py`, and test fixtures.
- **CON-001**: The implementation is greenfield; the plan must define all types and interfaces explicitly because no code contracts exist yet.
- **CON-002**: The selected integration domain is permanently `occupancy_duration`; all strategy and capability code must live under `custom_components/occupancy_duration/`.
- **GUD-001**: Follow current Home Assistant config-entry conventions so the capability summary can be shown in the setup UI without hardcoded strings.
- **PAT-001**: Keep capability inspection deterministic and conservative; false negatives are preferred over false positives when runtime behavior would become incorrect.

## Section 2 - Implementation Steps

### Implementation Phase 1 - Capability Data Model

- **GOAL-001**: Define the static types and value objects that every later workstream will consume.

| Task | Description | Completed | Date |
|---|---|---|---|
| TASK-001 | Create `custom_components/occupancy_duration/capability.py` with `SensorCapabilities`, `CapabilityConfidence`, and `CapabilitySummary` dataclasses or enums covering all PRD-required fields. | ✅ | 2026-09-20 |
| TASK-002 | Create or extend `custom_components/occupancy_duration/const.py` with a `StrategyMode` enum and constant keys used by config flow, diagnostics, and tests. | ✅ | 2026-09-20 |
| TASK-003 | Define an internal source snapshot structure in `custom_components/occupancy_duration/capability.py` that carries entity state, attributes, registry metadata, and sibling-entity candidates in one immutable object. | ✅ | 2026-09-20 |

### Implementation Phase 2 - Evidence Collection Pipeline

- **GOAL-002**: Implement capability inspection without relying on naming heuristics.

| Task | Description | Completed | Date |
|---|---|---|---|
| TASK-004 | Implement a state-and-attribute inspector in `custom_components/occupancy_duration/capability.py` that determines readable current-state, motion, occupancy, presence, and duration-exposure signals. | ✅ | 2026-09-20 |
| TASK-005 | Implement registry-backed sibling discovery in `custom_components/occupancy_duration/capability.py` that only considers entities on the same device as related candidates. | ✅ | 2026-09-20 |
| TASK-006 | Implement confidence resolution rules in `custom_components/occupancy_duration/capability.py` that mark findings as `confirmed`, `inferred`, or `unknown` and record rationale strings for diagnostics. | ✅ | 2026-09-20 |

### Implementation Phase 3 - Strategy Recommendation Engine

- **GOAL-003**: Convert capability findings into a safe strategy recommendation and preserve manual overrides.

| Task | Description | Completed | Date |
|---|---|---|---|
| TASK-007 | Implement `recommend_strategy(...)` in `custom_components/occupancy_duration/capability.py` to map explicit occupancy to `NATIVE_OCCUPANCY`, continuous ON/OFF motion to `CONTINUOUS_MOTION`, event-only sources to `EVENT_ONLY`, and mixed occupancy plus motion sources to `HYBRID`. | ✅ | 2026-09-20 |
| TASK-008 | Implement override-preservation helpers in `custom_components/occupancy_duration/capability.py` or `custom_components/occupancy_duration/const.py` so user-selected strategy wins over auto mode whenever an explicit override exists. | ✅ | 2026-09-20 |
| TASK-009 | Expose a serialized recommendation payload from `custom_components/occupancy_duration/capability.py` for consumption by `custom_components/occupancy_duration/config_flow.py` and `custom_components/occupancy_duration/diagnostics.py`. | ✅ | 2026-09-20 |

### Implementation Phase 4 - Test Coverage And Integration Contracts

- **GOAL-004**: Lock the behavior down with explicit coverage before runtime modules depend on it.

| Task | Description | Completed | Date |
|---|---|---|---|
| TASK-010 | Create `tests/test_capability.py` with fixtures and cases for continuous motion, event-only, explicit occupancy, explicit presence, unavailable sources, related occupancy siblings, and unknown semantics. | ✅ | 2026-09-20 |
| TASK-011 | Add integration-facing contract tests in `tests/test_capability.py` that verify manual override preservation and the exported summary structure used by config flow and diagnostics. | ✅ | 2026-09-20 |

## Section 3 - Alternatives

- **ALT-001**: Infer capability from entity IDs and friendly names first - Rejected because the PRD explicitly forbids name-driven inference and it would produce unsafe runtime claims.
- **ALT-002**: Hard-code vendor or platform profiles before implementing generic inspection - Rejected because the MVP must work across heterogeneous Home Assistant entities, not a short whitelist.
- **ALT-003**: Store only booleans for capabilities - Rejected because later diagnostics and UI requirements depend on a confirmed/inferred/unknown distinction.

## Section 4 - Dependencies

- **DEP-001**: [../PRD/initial_prd.md](../PRD/initial_prd.md) - Defines the product capability model, strategy modes, and selection priorities.
- **DEP-002**: [../PRD/initial_hacs_setup.md](../PRD/initial_hacs_setup.md) - Defines repository-level expectations for `capability.py`, config flow previews, and options editing.
- **DEP-003**: `https://developers.home-assistant.io/docs/core/integration/config_flow/` - Current Home Assistant guidance for setup and reconfigure UI behavior.
- **DEP-004**: `https://developers.home-assistant.io/docs/creating_integration_file_structure/` - Current Home Assistant guidance for where capability-related files belong.

## Section 5 - Files

- **FILE-001**: `custom_components/occupancy_duration/capability.py` - created - Implement the capability model, inspectors, and strategy recommendation engine.
- **FILE-002**: `custom_components/occupancy_duration/const.py` - created or modified - Define strategy enums and shared keys.
- **FILE-003**: `custom_components/occupancy_duration/config_flow.py` - modified - Consume the capability summary and recommendation payload.
- **FILE-004**: `custom_components/occupancy_duration/diagnostics.py` - modified - Expose capability findings and rationale in diagnostics output.
- **FILE-005**: `tests/test_capability.py` - created - Verify capability detection and strategy selection behavior.

## Section 6 - Testing

- **TEST-001**: `tests/test_capability.py` verifies that explicit occupancy outranks readable motion state for the same source or device.
- **TEST-002**: `tests/test_capability.py` verifies that event-only sources are classified without inventing a readable OFF state.
- **TEST-003**: `tests/test_capability.py` verifies that related-entity discovery only proposes sibling entities on the same device.
- **TEST-004**: `tests/test_capability.py` verifies that manual strategy override remains unchanged after re-running recommendation logic.
- **TEST-005**: Diagnostics serialization includes confidence values and rationale text for every non-unknown capability.

## Section 7 - Risks & Assumptions

- **RISK-001**: Related-entity discovery can create false associations if registry data is sparse - Mitigation: restrict matches to same-device entities and require explicit opt-in before making a related occupancy entity authoritative.
- **RISK-002**: Some Home Assistant entities expose ambiguous semantics through generic state strings - Mitigation: resolve ambiguity to `unknown` and let the user override strategy explicitly.
- **ASSUMPTION-001**: Home Assistant registry APIs needed for sibling discovery are available in the targeted minimum Home Assistant version.
- **ASSUMPTION-002**: The integration will accept conservative capability detection even when it means more user confirmation in the config flow.

## Section 8 - Related Specifications / Further Reading

- [../PRD/initial_prd.md](../PRD/initial_prd.md) - Product requirement source for capability inspection and strategy behavior.
- [../PRD/initial_hacs_setup.md](../PRD/initial_hacs_setup.md) - Repository and setup requirement source for capability previews.
- [https://developers.home-assistant.io/docs/core/integration/config_flow/](https://developers.home-assistant.io/docs/core/integration/config_flow/) - Current config flow, reconfigure, and translation guidance.
- [https://github.com/jpawlowski/hacs.integration_blueprint](https://github.com/jpawlowski/hacs.integration_blueprint) - Current custom-integration blueprint patterns aligned with Home Assistant 2026.x.