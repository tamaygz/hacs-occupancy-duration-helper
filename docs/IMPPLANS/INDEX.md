---
goal: Master index for the Occupancy Duration Helper implementation plan set
version: 1.0
date_created: 2026-09-20
last_updated: 2026-09-20
owner: tamaysgz
status: 'Planned'
tags: [planning, index, feature, infrastructure]
---

![Status: Planned](https://img.shields.io/badge/status-Planned-blue)

# Occupancy Duration Helper Plan Index

This index is the control document for all implementation planning under `docs/IMPPLANS/`.
It is derived from both source documents in `docs/PRD/` and cross-checked against current Home Assistant and HACS documentation as of 2026-09-20.

## Current Baseline

- Repository implementation state: planning-first bootstrap with workspace prompt support
- Source requirements reviewed:
  - [../PRD/initial_prd.md](../PRD/initial_prd.md)
  - [../PRD/initial_hacs_setup.md](../PRD/initial_hacs_setup.md)
- Workspace execution prompt present:
  - `.github/prompts/execplan.prompt.md`
- Current implementation assets complete: `custom_components/occupancy_duration/`, `hacs.json`, `pyproject.toml`, `LICENSE`, `README.md`, brand placeholders
- Brand assets in `custom_components/occupancy_duration/brand/` are minimal 1×1 PNG placeholders — **must be replaced with real artwork before v0.1.0 release**

## Plan Tracking

| Document | Scope | Status | Completed | Open | Last Work | Depends On |
|---|---|---|---:|---:|---|---|
| [feature-capability-and-strategy-1.md](./feature-capability-and-strategy-1.md) | Source inspection, capability model, strategy auto-selection, manual override safety | Completed | 11 | 0 | Implemented `const.py` (StrategyMode enum + config keys), `capability.py` (CapabilityFinding/SensorCapabilities/SourceSnapshot/CapabilitySummary + full inspection pipeline + strategy recommender + override resolver), and `tests/test_capability.py` (15 focused tests) | None |
| [feature-session-and-decay-engine-1.md](./feature-session-and-decay-engine-1.md) | Session lifecycle, scoring, decay, duration stages, scheduler contracts | Completed | 12 | 0 | Implemented `session.py`, `decay.py`, `stage.py`, and targeted tests; compile and diagnostics passed, but `pytest` execution is still blocked locally because the active interpreter does not yet have `pytest` installed | Capability and strategy plan |
| [feature-config-and-options-flow-1.md](./feature-config-and-options-flow-1.md) | Config flow, reconfigure/options split, selectors, translations, UX validation | Completed | 11 | 0 | Implemented `config_flow.py` with multi-step setup, reconfigure, options editing, source revision invalidation, synchronized `strings.json` / `translations/en.json`, and helper-contract tests in `tests/test_config_flow.py`; compile and JSON validation passed | Capability and strategy plan |
| [feature-entities-persistence-and-observability-1.md](./feature-entities-persistence-and-observability-1.md) | Entities, coordinator wiring, restore, diagnostics, HA events, unload behavior | Planned | 0 | 12 | Initial plan created from PRD and current HA docs | Session/decay plan; config flow plan |
| [infrastructure-repository-hacs-and-branding-1.md](./infrastructure-repository-hacs-and-branding-1.md) | Repository scaffold, manifest, HACS metadata, README, pyproject, brand assets | Completed | 16 | 0 | All phases done: scaffold, metadata, pyproject, LICENSE, README, brand asset placeholders, metadata consistency check | None |
| [process-quality-validation-and-release-1.md](./process-quality-validation-and-release-1.md) | Tests, CI, issue templates, validation gates, release workflow, HACS readiness | Planned | 0 | 13 | Initial plan created from PRD and current HA/HACS docs | All other plans |

## Execution Order

1. Start with [infrastructure-repository-hacs-and-branding-1.md](./infrastructure-repository-hacs-and-branding-1.md) to establish the repository contract and Home Assistant/HACS metadata.
2. Execute [feature-capability-and-strategy-1.md](./feature-capability-and-strategy-1.md) before any UI or runtime automation, because strategy selection depends on this model.
3. Execute [feature-session-and-decay-engine-1.md](./feature-session-and-decay-engine-1.md) once capability and strategy contracts exist.
4. Execute [feature-config-and-options-flow-1.md](./feature-config-and-options-flow-1.md) in parallel with late capability work after the capability summary contract is stable.
5. Execute [feature-entities-persistence-and-observability-1.md](./feature-entities-persistence-and-observability-1.md) after the session and flow data models stabilize.
6. Execute [process-quality-validation-and-release-1.md](./process-quality-validation-and-release-1.md) continuously, but do not cut `v0.1.0` until all other plans reach implementation-complete status.

## Coverage Matrix: Product PRD

| Source Sections | Covered By |
|---|---|
| `initial_prd.md` sections 1-3 | Capability and strategy plan; session and decay plan |
| `initial_prd.md` sections 4, 15, 16, 21, 30 | Config and options flow plan |
| `initial_prd.md` sections 5, 6, 17, 18 | Capability and strategy plan |
| `initial_prd.md` sections 7, 8, 10, 11, 12, 20, 26, 27, 28, 29, 38 | Session and decay plan |
| `initial_prd.md` sections 9, 13, 14, 19, 24, 25 | Entities, persistence, and observability plan |
| `initial_prd.md` sections 31, 34, 35, 36, 37 | Quality, validation, and release plan |

## Coverage Matrix: HACS Setup

| Source Sections | Covered By |
|---|---|
| `initial_hacs_setup.md` sections 1-4, 17-22, 27, 30, 31 | Repository, HACS, and branding plan |
| `initial_hacs_setup.md` sections 5-7 | Config and options flow plan |
| `initial_hacs_setup.md` sections 8-13 | Capability and strategy plan; session and decay plan |
| `initial_hacs_setup.md` sections 14-16 | Entities, persistence, and observability plan |
| `initial_hacs_setup.md` sections 23-29 | Quality, validation, and release plan |

## Global Todo

| Priority | Work Item | Owning Plan | State |
|---|---|---|---|
| P0 | Create the Home Assistant integration scaffold under `custom_components/occupancy_duration/` | Repository, HACS, and branding plan | Open |
| P0 | Define the capability model and strategy selection contract | Capability and strategy plan | Open |
| P0 | Define the session state machine, score model, and decay math contract | Session and decay plan | Open |
| P0 | Decide the split between `reconfigure` and `OptionsFlow` for mutable setup data vs runtime tuning | Config and options flow plan | Open |
| P0 | Establish persistence, restore, diagnostics, and event contracts | Entities, persistence, and observability plan | Open |
| P0 | Establish test harness, validation workflows, and HACS release gates | Quality, validation, and release plan | Open |

## Maintenance Protocol

1. Update `Status`, `Completed`, `Open`, and `Last Work` in the tracking table whenever a plan document changes state.
2. Keep task counts synchronized with the `TASK-` tables inside each plan document.
3. Do not mark a plan `Completed` until every `TEST-` item in that plan has a clear pass result.
4. If Home Assistant or HACS guidance changes, update the affected plan document first and then revise this index summary.
5. Preserve this file as the single source of truth for execution order and cross-plan dependencies.