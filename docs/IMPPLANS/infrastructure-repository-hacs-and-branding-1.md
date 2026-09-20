---
goal: Establish the repository scaffold, Home Assistant metadata, HACS metadata, documentation, and brand assets
version: 1.0
date_created: 2026-09-20
last_updated: 2026-09-20
owner: tamaysgz
status: 'In progress'
tags: [infrastructure, hacs, repository, branding, documentation]
---

![Status: In progress](https://img.shields.io/badge/status-In%20progress-yellow)

# Repository, HACS, And Branding Plan

## Section 1 - Requirements & Constraints

- **REQ-001**: Create the repository scaffold required for a Home Assistant custom integration under `custom_components/occupancy_duration/`.
- **REQ-002**: Create `custom_components/occupancy_duration/manifest.json` with the required custom-integration fields: `domain`, `name`, `codeowners`, `config_flow`, `documentation`, `issue_tracker`, `iot_class`, and `version`.
- **REQ-003**: Add `integration_type` to `manifest.json` and set it explicitly to `helper`, because the integration behaves as a Home Assistant helper rather than a hardware hub.
- **REQ-004**: Create root-level `hacs.json` with the minimum supported Home Assistant version and no obsolete HACS fields.
- **REQ-005**: Create `pyproject.toml` with a reproducible development dependency set sized for a Home Assistant custom integration.
- **REQ-006**: Create a user-facing `README.md` covering installation, configuration, behavior, entities, diagnostics, compatibility, development, contributing, and licensing.
- **REQ-007**: Create `LICENSE` at the repository root before any release or HACS submission.
- **REQ-008**: Provide local brand assets in `custom_components/occupancy_duration/brand/` using the 2026.3+ custom-integration mechanism.
- **REQ-009**: Keep documentation and metadata aligned with the canonical repository URLs in the PRD.
- **CON-001**: The implementation is greenfield; the repository currently lacks `custom_components/`, `hacs.json`, `pyproject.toml`, `LICENSE`, and all branding assets.
- **CON-002**: The PRD forbids obsolete branding flow through `home-assistant/brands/custom_integrations`; only local `brand/` assets are valid for this project.
- **GUD-001**: Keep `manifest.json` free of unnecessary Python requirements or inter-integration dependencies until real code proves they are needed.
- **GUD-002**: The repository compatibility floor is aligned to Home Assistant `2026.3.0` and Python `3.14`, because local custom-integration brand assets and the active development toolchain depend on that baseline.

## Section 2 - Implementation Steps

### Implementation Phase 1 - Repository Scaffold And Core Metadata

- **GOAL-001**: Create the baseline repository structure so Home Assistant and HACS can discover the integration.

| Task | Description | Completed | Date |
|---|---|---|---|
| TASK-001 | Create `custom_components/occupancy_duration/` with placeholder module ownership reserved for `__init__.py`, `manifest.json`, `config_flow.py`, `const.py`, `capability.py`, `session.py`, `decay.py`, `stage.py`, `storage.py`, `coordinator.py`, `sensor.py`, `binary_sensor.py`, `diagnostics.py`, `strings.json`, and `translations/en.json`. | ✅ | 2026-09-20 |
| TASK-002 | Create `custom_components/occupancy_duration/manifest.json` with `domain`, `name`, `codeowners`, `config_flow`, `documentation`, `issue_tracker`, `iot_class`, `integration_type`, and `version`. | ✅ | 2026-09-20 |
| TASK-003 | Create root-level `hacs.json` with the integration name and minimum Home Assistant version only, unless later HACS validation demands additional fields. | ✅ | 2026-09-20 |

### Implementation Phase 2 - Development Scaffold

- **GOAL-002**: Make the repository reproducible for implementation and validation work.

| Task | Description | Completed | Date |
|---|---|---|---|
| TASK-004 | Create `pyproject.toml` with project metadata, Python version constraints, and development dependency groups for Home Assistant, pytest, `pytest-homeassistant-custom-component`, Ruff, and optional static analysis. | ✅ | 2026-09-20 |
| TASK-005 | Create `LICENSE` at the repository root using the license choice approved for the project owner. | ✅ | 2026-09-20 |
| TASK-006 | Reserve `tests/` ownership in `pyproject.toml` and repository documentation so later plans can attach the full test suite cleanly. | ✅ | 2026-09-20 |

### Implementation Phase 3 - Documentation Contract

- **GOAL-003**: Publish repository-facing guidance that matches the product behavior and installation model.

| Task | Description | Completed | Date |
|---|---|---|---|
| TASK-007 | Rewrite `README.md` into the user-oriented structure required by the PRD, including HACS and manual installation instructions that copy only `custom_components/occupancy_duration`. |  |  |
| TASK-008 | Document the integration differentiator in `README.md`: capability-aware occupancy sessions with adaptive decay rather than naive motion timers. |  |  |
| TASK-009 | Document repository URLs, issue tracker, release expectations, compatibility floor, diagnostics, and development workflow in `README.md`. |  |  |

### Implementation Phase 4 - Local Brand Assets

- **GOAL-004**: Make the integration visually valid for Home Assistant 2026.3+ and HACS validation.

| Task | Description | Completed | Date |
|---|---|---|---|
| TASK-010 | Create `custom_components/occupancy_duration/brand/icon.png` and `custom_components/occupancy_duration/brand/icon@2x.png` with the required square sizes and transparent-background preference. |  |  |
| TASK-011 | Create `custom_components/occupancy_duration/brand/logo.png` and `custom_components/occupancy_duration/brand/logo@2x.png` with the required landscape proportions. |  |  |
| TASK-012 | Validate that all brand assets avoid Home Assistant official branding and remain legible at small sizes. |  |  |

### Implementation Phase 5 - Metadata Consistency Check

- **GOAL-005**: Align the repository contract with current Home Assistant and HACS expectations before CI is added.

| Task | Description | Completed | Date |
|---|---|---|---|
| TASK-013 | Verify that `manifest.json`, `hacs.json`, `README.md`, and brand assets reference the same integration name, domain, repository URL, and compatibility floor. |  |  |
| TASK-014 | Record any deviation from the PRD caused by updated upstream guidance, such as the explicit `integration_type: helper` recommendation, directly in documentation comments or plan updates. |  |  |

### Implementation Phase 6 - Workspace Hygiene And Local Tooling

- **GOAL-006**: Add repository-local ignore rules and editor tasks that support custom-integration development without introducing user-specific clutter.

| Task | Description | Completed | Date |
|---|---|---|---|
| TASK-015 | Create a root-level `.gitignore` tailored to a Home Assistant custom integration, including Python caches, Home Assistant runtime state, local config data, and committed `.vscode/tasks.json` exceptions. | ✅ | 2026-09-20 |
| TASK-016 | Create `.vscode/tasks.json` with local tasks for compile, test, coverage, lint, format, type-check, and Hassfest validation aligned with custom-integration workflows. | ✅ | 2026-09-20 |

## Section 3 - Alternatives

- **ALT-001**: Omit `integration_type` and rely on the Home Assistant default - Rejected because current manifest guidance recommends setting the correct type explicitly and `helper` matches the product.
- **ALT-002**: Add runtime `requirements` or `dependencies` preemptively - Rejected because the PRD explicitly says not to add them without demonstrated need.
- **ALT-003**: Submit custom branding to the central brands repository - Rejected because Home Assistant 2026.3+ supports local `brand/` assets for custom integrations and the PRD forbids the obsolete flow.

## Section 4 - Dependencies

- **DEP-001**: [../PRD/initial_hacs_setup.md](../PRD/initial_hacs_setup.md) - Source for repository structure, manifest, HACS metadata, README, branding, and compatibility notes.
- **DEP-002**: [../PRD/initial_prd.md](../PRD/initial_prd.md) - Source for user-facing README behavior and architecture references.
- **DEP-003**: `https://developers.home-assistant.io/docs/creating_integration_manifest/` - Current manifest guidance, including explicit `integration_type` recommendations.
- **DEP-004**: `https://developers.home-assistant.io/docs/creating_integration_file_structure/` - Current integration directory and `brand/` placement guidance.
- **DEP-005**: `https://developers.home-assistant.io/docs/core/integration/brand_images/` - Current custom-integration brand-asset guidance.
- **DEP-006**: `https://www.hacs.xyz/docs/publish/integration/` - Current HACS repository structure and manifest requirements.

## Section 5 - Files

- **FILE-001**: `custom_components/occupancy_duration/manifest.json` - created - Define Home Assistant integration metadata.
- **FILE-002**: `custom_components/occupancy_duration/__init__.py` - created - Reserve the integration entry point.
- **FILE-003**: `hacs.json` - created - Define minimal HACS metadata.
- **FILE-004**: `pyproject.toml` - created - Define Python project metadata and development dependencies.
- **FILE-005**: `README.md` - modified - Replace placeholder content with the required user-facing guide.
- **FILE-006**: `LICENSE` - created - Add the project license.
- **FILE-007**: `custom_components/occupancy_duration/brand/icon.png` - created - Add the standard icon asset.
- **FILE-008**: `custom_components/occupancy_duration/brand/icon@2x.png` - created - Add the high-resolution icon asset.
- **FILE-009**: `custom_components/occupancy_duration/brand/logo.png` - created - Add the standard logo asset.
- **FILE-010**: `custom_components/occupancy_duration/brand/logo@2x.png` - created - Add the high-resolution logo asset.
- **FILE-011**: `.gitignore` - created - Ignore Home Assistant runtime artifacts, Python caches, and uncommitted editor state.
- **FILE-012**: `.vscode/tasks.json` - created - Provide workspace tasks for local validation and development.

## Section 6 - Testing

- **TEST-001**: `manifest.json` is valid JSON and contains the required custom-integration keys plus explicit `integration_type: helper`.
- **TEST-002**: `hacs.json` is valid JSON and contains the expected integration name and minimum Home Assistant version.
- **TEST-003**: `README.md` contains all PRD-required sections and the manual installation path points to `/config/custom_components/occupancy_duration` only.
- **TEST-004**: All four required brand files exist in `custom_components/occupancy_duration/brand/` and are valid PNG assets.
- **TEST-005**: Repository metadata documents the same domain, integration name, issue tracker, and release links across `manifest.json`, `hacs.json`, and `README.md`.
- **TEST-006**: `.gitignore` exists, ignores Home Assistant runtime artifacts, and preserves `.vscode/tasks.json` for sharing.
- **TEST-007**: `.vscode/tasks.json` parses as valid VS Code task JSON and defines compile, test, lint, format, type-check, and Hassfest tasks.

## Section 7 - Risks & Assumptions

- **RISK-001**: The minimum Home Assistant version may need to move upward once implementation chooses newer APIs - Mitigation: keep the compatibility floor provisional until actual code dependencies are known.
- **RISK-002**: Branding work can block HACS readiness if deferred too long - Mitigation: create brand assets before CI and HACS validation are finalized.
- **ASSUMPTION-001**: The project will stay a custom integration and does not need Home Assistant Core submission rules.
- **ASSUMPTION-002**: The repository owner will confirm the final OSS license choice before release.

## Section 8 - Related Specifications / Further Reading

- [../PRD/initial_hacs_setup.md](../PRD/initial_hacs_setup.md) - Source for scaffold, branding, metadata, and README requirements.
- [../PRD/initial_prd.md](../PRD/initial_prd.md) - Source for user-facing behavior that README must explain.
- [https://developers.home-assistant.io/docs/creating_integration_manifest/](https://developers.home-assistant.io/docs/creating_integration_manifest/) - Current manifest guidance.
- [https://developers.home-assistant.io/docs/core/integration/brand_images/](https://developers.home-assistant.io/docs/core/integration/brand_images/) - Current custom-integration branding guidance.
- [https://developers.home-assistant.io/blog/2026/02/24/brands-proxy-api/](https://developers.home-assistant.io/blog/2026/02/24/brands-proxy-api/) - 2026.3 update for local brand assets.
- [https://www.hacs.xyz/docs/publish/integration/](https://www.hacs.xyz/docs/publish/integration/) - Current HACS integration repository requirements.