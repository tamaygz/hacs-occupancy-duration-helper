---
goal: Define the testing, CI, issue intake, validation, and release process for Occupancy Duration Helper
version: 1.0
date_created: 2026-09-20
last_updated: 2026-09-20
owner: tamaysgz
status: 'Planned'
tags: [process, ci, tests, release, validation]
---

![Status: Planned](https://img.shields.io/badge/status-Planned-blue)

# Quality, Validation, And Release Plan

## Section 1 - Requirements & Constraints

- **REQ-001**: Create a complete `tests/` scaffold with `__init__.py`, `conftest.py`, and the PRD-required test modules for capability, session, decay, stage, config flow, sensors, and restore behavior.
- **REQ-002**: Add a validation workflow in `.github/workflows/validate.yml` that checks Python syntax, JSON validity, manifest validity, translation consistency, test execution, and HACS validation where practical.
- **REQ-003**: Add GitHub issue templates for bug reports and feature requests in `.github/ISSUE_TEMPLATE/` with the data fields mandated by the PRD.
- **REQ-004**: Define a release path based on GitHub Releases with initial version `v0.1.0` and manifest-version synchronization.
- **REQ-005**: Prepare an optional `.github/workflows/release.yml` or equivalent documented release procedure sized to the repository's maturity.
- **REQ-006**: Encode the PRD HACS-readiness checklist as an executable validation gate rather than an informal note.
- **REQ-007**: Keep the workflow implementation aligned with current Home Assistant and HACS tooling rather than obsolete templates.
- **CON-001**: Release readiness depends on every functional plan completing and passing its own tests.
- **CON-002**: The repository currently has no `.github/` directory and no test suite, so the entire quality system is greenfield.
- **PAT-001**: Prefer narrow, deterministic checks over broad best-effort workflows so failures remain actionable for less capable follow-on agents.

## Section 2 - Implementation Steps

### Implementation Phase 1 - Test Harness Scaffold

- **GOAL-001**: Establish the project test structure and shared fixtures.

| Task | Description | Completed | Date |
|---|---|---|---|
| TASK-001 | Create `tests/__init__.py` and `tests/conftest.py` with Home Assistant custom-component fixtures, mock config entries, and source-entity helpers used across all test modules. |  |  |
| TASK-002 | Create the PRD-required test files `tests/test_capability.py`, `tests/test_session.py`, `tests/test_decay.py`, `tests/test_stage.py`, `tests/test_config_flow.py`, `tests/test_sensor.py`, and `tests/test_restore.py`. |  |  |
| TASK-003 | Document how test modules map to the implementation plans so follow-on agents keep coverage aligned with the design. |  |  |

### Implementation Phase 2 - Validation Workflow

- **GOAL-002**: Automate repository checks expected by Home Assistant and HACS.

| Task | Description | Completed | Date |
|---|---|---|---|
| TASK-004 | Create `.github/workflows/validate.yml` with jobs for Python syntax or lint checks, JSON validation, manifest validation, translation consistency, pytest execution, and HACS repository validation. |  |  |
| TASK-005 | Integrate current Home Assistant validation tooling such as Hassfest where appropriate for a custom integration repository. |  |  |
| TASK-006 | Integrate current HACS validation tooling or action support so repository structure and metadata are checked on push and pull request. |  |  |

### Implementation Phase 3 - Issue Intake And Project Hygiene

- **GOAL-003**: Ensure user reports contain enough structured data to debug the integration.

| Task | Description | Completed | Date |
|---|---|---|---|
| TASK-007 | Create `.github/ISSUE_TEMPLATE/bug_report.yml` requesting Home Assistant version, integration version, source entity, source device or integration, detected capabilities, selected strategy, expected behavior, actual behavior, diagnostics, and relevant logs. |  |  |
| TASK-008 | Create `.github/ISSUE_TEMPLATE/feature_request.yml` requesting problem statement, desired behavior, automation or use-case example, and why current behavior is insufficient. |  |  |

### Implementation Phase 4 - Release Contract

- **GOAL-004**: Make `v0.1.0` a reproducible, validated release milestone.

| Task | Description | Completed | Date |
|---|---|---|---|
| TASK-009 | Define and document the release checklist that blocks `v0.1.0` until manifest version, tests, HACS validation, README, brand assets, and GitHub Issues state all pass. |  |  |
| TASK-010 | Create `.github/workflows/release.yml` if automation is chosen, or document a manual release process with explicit version-bump and verification steps if not. |  |  |
| TASK-011 | Add a manifest-version sync check in workflow logic or release documentation so `custom_components/occupancy_duration/manifest.json` always matches the GitHub release version. |  |  |

### Implementation Phase 5 - Final HACS Readiness Gate

- **GOAL-005**: Encode the PRD definition of done as an operational gate.

| Task | Description | Completed | Date |
|---|---|---|---|
| TASK-012 | Convert the PRD HACS validation checklist into a tracked checklist in repository documentation or workflow output so agents can verify readiness item by item. |  |  |
| TASK-013 | Validate that the repository passes the public-repo, release, metadata, README, branding, config-flow, unload, and restore expectations before any HACS default-repository submission is considered. |  |  |

## Section 3 - Alternatives

- **ALT-001**: Use only manual testing before release - Rejected because the PRD explicitly demands a structured test suite and CI validation.
- **ALT-002**: Publish tags without GitHub Releases - Rejected because HACS distribution and the PRD both prefer or require full releases, not tags alone.
- **ALT-003**: Reuse outdated third-party templates without verifying current tooling - Rejected because the user explicitly asked for plans validated against current Home Assistant and HACS guidance.

## Section 4 - Dependencies

- **DEP-001**: [./infrastructure-repository-hacs-and-branding-1.md](./infrastructure-repository-hacs-and-branding-1.md) - Provides metadata, README, brand assets, and packaging inputs needed for validation.
- **DEP-002**: [./feature-capability-and-strategy-1.md](./feature-capability-and-strategy-1.md) - Supplies the capability test surface.
- **DEP-003**: [./feature-session-and-decay-engine-1.md](./feature-session-and-decay-engine-1.md) - Supplies session and decay test behavior.
- **DEP-004**: [./feature-config-and-options-flow-1.md](./feature-config-and-options-flow-1.md) - Supplies flow tests and translation checks.
- **DEP-005**: [./feature-entities-persistence-and-observability-1.md](./feature-entities-persistence-and-observability-1.md) - Supplies entity, restore, and diagnostics test behavior.
- **DEP-006**: [https://www.hacs.xyz/docs/publish/include/](https://www.hacs.xyz/docs/publish/include/) - Current default-repository submission gates and automated checks.
- **DEP-007**: [https://www.hacs.xyz/docs/publish/integration/](https://www.hacs.xyz/docs/publish/integration/) - Current HACS integration repository requirements.

## Section 5 - Files

- **FILE-001**: `tests/__init__.py` - created - Initialize the test package.
- **FILE-002**: `tests/conftest.py` - created - Provide shared Home Assistant and config-entry fixtures.
- **FILE-003**: `tests/test_capability.py` - created - Verify capability detection.
- **FILE-004**: `tests/test_session.py` - created - Verify session transitions.
- **FILE-005**: `tests/test_decay.py` - created - Verify decay behavior.
- **FILE-006**: `tests/test_stage.py` - created - Verify stage behavior.
- **FILE-007**: `tests/test_config_flow.py` - created - Verify setup, reconfigure, and options flows.
- **FILE-008**: `tests/test_sensor.py` - created - Verify entities and attributes.
- **FILE-009**: `tests/test_restore.py` - created - Verify restore and diagnostics behavior.
- **FILE-010**: `.github/workflows/validate.yml` - created - Run quality and metadata checks.
- **FILE-011**: `.github/workflows/release.yml` - created or omitted with documented manual alternative - Define release execution.
- **FILE-012**: `.github/ISSUE_TEMPLATE/bug_report.yml` - created - Structure bug reports.
- **FILE-013**: `.github/ISSUE_TEMPLATE/feature_request.yml` - created - Structure feature requests.

## Section 6 - Testing

- **TEST-001**: The full `tests/` tree exists and matches the PRD-required module list.
- **TEST-002**: `.github/workflows/validate.yml` runs successfully on a branch with valid metadata and a passing test suite.
- **TEST-003**: HACS validation passes without ignores before `v0.1.0` is released.
- **TEST-004**: GitHub issue templates render the required fields and do not request secrets.
- **TEST-005**: The release process prevents a version mismatch between `manifest.json` and the GitHub release version.

## Section 7 - Risks & Assumptions

- **RISK-001**: HACS and Home Assistant validation tooling changes over time - Mitigation: pin the planning assumptions to current docs and re-check workflow actions when implementation starts.
- **RISK-002**: Release automation can add complexity before the project is stable - Mitigation: allow a manual release path if the workflow would be more brittle than useful for `v0.1.0`.
- **ASSUMPTION-001**: The repository owner intends to publish full GitHub Releases rather than distributing directly from the default branch only.
- **ASSUMPTION-002**: The project will use GitHub Actions as the primary CI runner.

## Section 8 - Related Specifications / Further Reading

- [../PRD/initial_hacs_setup.md](../PRD/initial_hacs_setup.md) - Source for CI, tests, issue templates, release, and HACS validation requirements.
- [../PRD/initial_prd.md](../PRD/initial_prd.md) - Source for acceptance criteria and edge-case test coverage.
- [https://www.hacs.xyz/docs/publish/include/](https://www.hacs.xyz/docs/publish/include/) - Current default-repository validation gates.
- [https://www.hacs.xyz/docs/publish/integration/](https://www.hacs.xyz/docs/publish/integration/) - Current HACS integration repository requirements.
- [https://github.com/jpawlowski/hacs.integration_blueprint](https://github.com/jpawlowski/hacs.integration_blueprint) - Reference for up-to-date custom-integration CI and release structure.