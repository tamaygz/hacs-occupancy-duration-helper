# Initial HACS Setup — Occupancy Duration Helper

**Repository:** `tamaysgz/hacs-occupancy-duration-helper`  
**Integration:** Occupancy Duration Helper  
**Repository type:** Home Assistant custom integration distributed through HACS  
**Audience:** Coding agent implementing the initial repository/HACS structure

> This document is an implementation checklist. Follow the current Home Assistant custom-integration conventions and HACS expectations rather than copying obsolete HACS templates.

## 1. Target repository structure

Create the repository with this structure:

```text
hacs-occupancy-duration-helper/
├── .github/
│   ├── ISSUE_TEMPLATE/
│   │   ├── bug_report.yml
│   │   └── feature_request.yml
│   └── workflows/
│       ├── validate.yml
│       └── release.yml                 # optional for initial implementation
├── custom_components/
│   └── occupancy_duration/
│       ├── __init__.py
│       ├── manifest.json
│       ├── config_flow.py
│       ├── const.py
│       ├── capability.py
│       ├── session.py
│       ├── decay.py
│       ├── stage.py
│       ├── storage.py
│       ├── coordinator.py
│       ├── sensor.py
│       ├── binary_sensor.py
│       ├── diagnostics.py
│       ├── strings.json
│       ├── translations/
│       │   └── en.json
│       └── brand/
│           ├── icon.png
│           ├── icon@2x.png
│           ├── logo.png
│           └── logo@2x.png
├── README.md
├── LICENSE
├── hacs.json
├── pyproject.toml
└── initial_hacs_setup.md
```

Not every file above is mandatory for HACS itself. The structure intentionally separates:
- files required for a functioning Home Assistant integration,
- HACS/repository metadata,
- quality/CI files,
- branding.

Do not create empty implementation files merely to satisfy the tree. Create each file when its functionality is implemented.

---

# 2. Integration domain

Use:

```text
occupancy_duration
```

The domain is permanent once released, so do not rename it casually.

The Home Assistant integration directory must therefore be:

```text
custom_components/occupancy_duration/
```

Home Assistant requires the integration directory name to match the integration domain. The minimum integration contains `manifest.json` and `__init__.py`.

Reference:
- Home Assistant integration file structure:
  https://developers.home-assistant.io/docs/creating_integration_file_structure/

---

# 3. `manifest.json`

Create:

```text
custom_components/occupancy_duration/manifest.json
```

Initial shape:

```json
{
  "domain": "occupancy_duration",
  "name": "Occupancy Duration Helper",
  "codeowners": [
    "@tamaysgz"
  ],
  "config_flow": true,
  "documentation": "https://github.com/tamaysgz/hacs-occupancy-duration-helper",
  "issue_tracker": "https://github.com/tamaysgz/hacs-occupancy-duration-helper/issues",
  "iot_class": "local_push",
  "version": "0.1.0"
}
```

### Important manifest rules

- `domain` must be `occupancy_duration`.
- `name` should be the user-facing integration name.
- `codeowners` must contain `@tamaysgz`.
- `config_flow: true` because setup is UI-driven.
- `documentation` should point to the project's documentation/README until there is a dedicated documentation site.
- `issue_tracker` should point to GitHub Issues.
- `iot_class` should describe the actual implementation. Because this integration primarily listens to Home Assistant entities and maintains local state, `local_push` is an appropriate starting point if the implementation is event-driven. Revisit this if the implementation becomes primarily polling-based.
- `version` must be a valid integration version and must be updated for releases.

Do not add Python `requirements` unless the integration genuinely needs third-party Python packages.

Do not add `dependencies` or `after_dependencies` unless there is a concrete Home Assistant integration dependency.

Home Assistant's manifest documentation:
https://developers.home-assistant.io/docs/creating_integration_manifest/

---

# 4. `__init__.py`

Create:

```text
custom_components/occupancy_duration/__init__.py
```

Responsibilities:

- define integration setup/unload
- forward config entries to the relevant platforms
- register/unregister listeners
- initialize persistent storage/session state
- cleanly unload a config entry

The implementation should follow current Home Assistant config-entry patterns.

Do not put the session algorithm directly into `__init__.py`.

---

# 5. Config flow

Create:

```text
custom_components/occupancy_duration/config_flow.py
```

The integration must be configured entirely through the Home Assistant UI.

Initial flow:

```text
Name
  ↓
Source entity
  ↓
Capability inspection
  ↓
Detected sensor capabilities
  ↓
Recommended strategy
  ↓
Basic decay settings
  ↓
Optional duration stages
  ↓
Create config entry
```

The flow should use Home Assistant selectors rather than free-form entity IDs where possible.

## Source selector

Use an entity selector that can select relevant:
- binary sensors
- sensors
- event-like sources where supported

Do not unnecessarily restrict the user to `binary_sensor` if the architecture supports occupancy/presence entities.

## Capability preview

After selecting a source, display detected information such as:

```text
Current state: Available
Motion state: ON/OFF
Occupancy state: Not detected
Continuous state: Yes
Event-only: No
Re-check during decay: Yes

Recommended strategy:
Continuous motion + adaptive decay
```

The capability inspector must not silently change an explicit user override.

---

# 6. `strings.json` and translations

Create:

```text
custom_components/occupancy_duration/strings.json
custom_components/occupancy_duration/translations/en.json
```

All user-facing config-flow strings should live in the standard Home Assistant translation structure.

At minimum cover:

- config flow title
- source selection
- strategy
- decay
- end threshold
- end grace
- stages
- validation errors
- capability summary
- options flow

Keep `strings.json` as the source structure and keep `translations/en.json` synchronized according to current Home Assistant conventions.

Do not hard-code user-facing config-flow text in Python.

---

# 7. Options flow

The integration should support changing configuration after initial setup.

Implement options for:

```text
Source entity
Strategy
Default half-life
End threshold
End grace
Restore session
Stages
```

If changing the source invalidates an existing session, handle that explicitly and safely.

A source change must not accidentally create a session from a stale old source state without processing the new source semantics.

---

# 8. Capability detection

Create:

```text
custom_components/occupancy_duration/capability.py
```

This is a core part of the product.

The module should inspect the selected entity and, where safely possible, related entities/device metadata.

Model something similar to:

```python
@dataclass
class SensorCapabilities:
    current_state: bool
    motion_state: bool
    occupancy_state: bool
    presence_state: bool
    start_event: bool
    end_event: bool
    event_only: bool
    continuous_state: bool
    can_recheck: bool
    exposes_duration: bool
    confidence: float
```

The detector should distinguish:

```text
confirmed
inferred
unknown
```

Do not infer capabilities merely from an entity name such as `*_motion`.

Prefer:
1. explicit state semantics
2. entity/device metadata
3. related entities from the same device
4. known integration/platform behavior
5. conservative inference

The detector must never claim a capability that cannot actually be used by the runtime.

---

# 9. Runtime strategy

The runtime should select among concepts such as:

```text
AUTO
NATIVE_OCCUPANCY
CONTINUOUS_MOTION
EVENT_ONLY
HYBRID
```

Automatic strategy selection should use the capability model.

Example:

```text
explicit occupancy
    → native occupancy

continuous ON/OFF motion
    → continuous motion + decay

event-only source
    → event-only decay

motion + occupancy
    → hybrid
```

Users can explicitly override the strategy.

Automatic detection must not overwrite a manual override.

---

# 10. Session engine

Create:

```text
custom_components/occupancy_duration/session.py
```

The session engine owns:

```text
session_id
started_at
last_activity_at
last_active_signal_at
ended_at
score
stage
state
```

States:

```text
IDLE
ACTIVE
DECAYING
ENDING
CLOSED
```

Required semantic behavior:

```text
activity detected
    → start session if none exists

activity detected during existing session
    → reinforce session
    → DO NOT reset started_at

activity stops
    → potentially enter DECAYING

activity returns during DECAYING
    → ACTIVE
    → preserve started_at

score below threshold
    → ENDING

grace expires
    → CLOSED
```

The session duration must always be:

```text
now - started_at
```

while the session is open.

---

# 11. Dynamic source re-check

This is a key implementation requirement.

During decay, the integration must determine whether the source can currently confirm continued activity.

For a continuously readable source:

```text
source = ON
    → do not decay

source = OFF
    → apply decay
```

For explicit occupancy:

```text
occupied
    → keep active

not occupied
    → allow end/decay semantics
```

For event-only sources:

```text
no current state
    → do not pretend that OFF exists
    → use configured event-based decay
```

Avoid polling sources that cannot meaningfully provide a current state.

Use event-driven updates wherever possible.

---

# 12. Decay engine

Create:

```text
custom_components/occupancy_duration/decay.py
```

Preferred model:

```text
score(t) = score0 * 2^(-t / half_life)
```

Use elapsed wall-clock time rather than decrementing the score at fixed increments.

Inputs:

```text
current score
last meaningful activity
current stage
current sensor state
half-life
end threshold
```

Important:

**Do not decay simply because the last event is old if the sensor's current state still says it is active.**

---

# 13. Duration stages

Create:

```text
custom_components/occupancy_duration/stage.py
```

Example:

```yaml
stages:
  - id: short
    name: Short
    min_duration: 0
    max_duration: 60
    decay_half_life: 30

  - id: medium
    name: Medium
    min_duration: 60
    max_duration: 180
    decay_half_life: 60

  - id: long
    name: Long
    min_duration: 180
    max_duration: null
    decay_half_life: 180
```

Stage progression is monotonic:

```text
NONE → SHORT → MEDIUM → LONG
```

The stage must not itself end a session.

Duration determines the stage.

The session score determines whether the session remains active.

---

# 14. Persistence

Create:

```text
custom_components/occupancy_duration/storage.py
```

Persist enough information to restore an active/decaying session:

```text
session_id
started_at
last_activity_at
last_active_signal_at
score
stage
state
```

Use Home Assistant's supported storage/config-entry mechanisms rather than inventing an arbitrary file format.

On restart:

1. Load persisted session.
2. Re-detect/revalidate source capabilities.
3. Inspect the source's current state if available.
4. Calculate wall-clock elapsed duration.
5. Recalculate decay where appropriate.
6. Continue, end, or restore according to the configured policy.

Do not interpret source unavailability as equivalent to "not occupied."

---

# 15. Entity platforms

Implement:

```text
sensor.py
binary_sensor.py
```

## Duration sensor

Entity:

```text
sensor.<name>_duration
```

State:

```text
seconds
```

Use the appropriate Home Assistant unit/device class for duration.

Suggested attributes:

```yaml
active: true
started_at: ...
last_activity_at: ...
stage: long
session_state: decaying
score: 72
```

Avoid duplicating values in attributes when Home Assistant has a native entity state for the same information.

## Occupancy entity

Entity:

```text
binary_sensor.<name>_occupancy
```

Device class:

```text
occupancy
```

## Stage entity

Only create when stages are configured:

```text
sensor.<name>_stage
```

Example:

```text
short
medium
long
```

---

# 16. Diagnostics

Create:

```text
custom_components/occupancy_duration/diagnostics.py
```

Diagnostics should help explain:

```text
source entity
detected capabilities
selected strategy
current source state
session state
score
stage
last activity
decay configuration
```

Do not include sensitive data unnecessarily.

Follow Home Assistant diagnostics conventions.

---

# 17. Integration icon and logo

As of Home Assistant 2026.3, custom integrations can ship their own brand assets directly in:

```text
custom_components/occupancy_duration/brand/
```

This is now preferred for a custom integration instead of submitting custom integration branding to the central `home-assistant/brands` repository.

Reference:
https://developers.home-assistant.io/blog/2026/02/24/brands-proxy-api/

Create:

```text
brand/
├── icon.png
├── icon@2x.png
├── logo.png
└── logo@2x.png
```

## Icon

Required characteristics:

- PNG
- square
- `256x256` normal
- `512x512` @2x
- transparent background preferred
- tightly cropped
- recognizable at small size

## Logo

Preferred:

- landscape orientation
- shortest side between 128–256 px for normal
- shortest side between 256–512 px for @2x

Dark variants are optional:

```text
dark_icon.png
dark_icon@2x.png
dark_logo.png
dark_logo@2x.png
```

If dark variants are not needed, omit them.

Do not use Home Assistant's logo or branding in the integration artwork.

Reference:
https://developers.home-assistant.io/docs/core/integration/brand_images/

Important 2026+ rule:

Do **not** create a PR to `home-assistant/brands/custom_integrations` for this custom integration. Local `brand/` assets are the current mechanism for custom integrations.

---

# 18. HACS metadata — `hacs.json`

Create at repository root:

```text
hacs.json
```

Keep this minimal.

Suggested initial content:

```json
{
  "name": "Occupancy Duration Helper",
  "homeassistant": "2024.1.0"
}
```

The exact minimum/maximum Home Assistant compatibility should reflect the implementation's actual supported versions. Prefer the newest realistic minimum version if the integration relies on modern APIs.

Do not add obsolete HACS metadata simply because old templates contain it.

Before release, validate `hacs.json` against the current HACS schema/documentation.

The HACS integration repository itself contains `hacs.json` and is a useful reference for current HACS repository conventions:
https://github.com/hacs/integration

---

# 19. README.md

Create a user-oriented README.

Required sections:

```text
# Occupancy Duration Helper

Short description

## What it does

## Features

## How it works

## Installation
### HACS
### Manual

## Configuration

## Sensor capabilities

## Duration stages

## Entities

## Automation examples

## Troubleshooting

## Diagnostics

## Requirements / compatibility

## Development

## Contributing

## License
```

The README should clearly communicate the main differentiator:

> The integration does not simply start a timer when motion begins and stop it when motion ends. It detects the source sensor's capabilities and maintains an occupancy session using current sensor state, activity evidence, duration, and adaptive decay.

---

# 20. HACS installation instructions

README should provide:

### HACS

1. Open HACS.
2. Open Integrations.
3. Search for `Occupancy Duration Helper`.
4. Install it.
5. Restart Home Assistant if required.
6. Go to Settings → Devices & services.
7. Add `Occupancy Duration Helper`.

### Manual

Copy:

```text
custom_components/occupancy_duration
```

into:

```text
/config/custom_components/occupancy_duration
```

Then restart Home Assistant.

Do not tell users to install the repository's entire contents into `custom_components`.

---

# 21. GitHub repository metadata

Repository:

```text
tamaysgz/hacs-occupancy-duration-helper
```

Suggested GitHub description:

> Home Assistant custom integration that turns motion and presence sensors into persistent occupancy sessions with duration tracking, configurable stages, and adaptive decay.

Suggested topics:

```text
hacs
hacs-integration
home-assistant
home-assistant-integration
home-assistant-custom-component
home-automation
occupancy
occupancy-detection
occupancy-duration
presence
presence-detection
motion-sensor
motion-detection
smart-home
iot
```

Avoid stuffing unrelated SEO keywords into the repository.

---

# 22. Links

Use these canonical links consistently.

Repository:

```text
https://github.com/tamaysgz/hacs-occupancy-duration-helper
```

Issues:

```text
https://github.com/tamaysgz/hacs-occupancy-duration-helper/issues
```

Releases:

```text
https://github.com/tamaysgz/hacs-occupancy-duration-helper/releases
```

HACS installation URL:

```text
https://github.com/tamaysgz/hacs-occupancy-duration-helper
```

The repository itself is the HACS source; there is no separate HACS definition file hosted elsewhere.

---

# 23. GitHub issue templates

Create:

```text
.github/ISSUE_TEMPLATE/bug_report.yml
.github/ISSUE_TEMPLATE/feature_request.yml
```

Bug report should request:

```text
Home Assistant version
Integration version
Source entity
Source integration/device
Detected capabilities
Selected strategy
Expected behavior
Actual behavior
Diagnostics
Relevant logs
```

Feature request should request:

```text
Problem
Desired behavior
Example automation/use case
Why current behavior is insufficient
```

Do not request users to paste secrets or full Home Assistant configuration files containing credentials.

---

# 24. GitHub Actions / CI

At minimum create validation that checks:

- Python syntax
- JSON validity
- Home Assistant integration manifest
- translations
- basic linting
- test suite
- HACS validation where practical

Recommended workflow:

```text
.github/workflows/validate.yml
```

The agent should prefer current Home Assistant/HACS validation actions rather than pinning obsolete third-party actions from old templates.

A modern integration blueprint can be used as a reference for current CI/development patterns:
https://github.com/jpawlowski/hacs.integration_blueprint

---

# 25. Release strategy

Use GitHub Releases.

Initial release:

```text
v0.1.0
```

Subsequent releases should use semantic versioning:

```text
MAJOR.MINOR.PATCH
```

Examples:

```text
0.1.0 → initial public release
0.2.0 → new backward-compatible feature
0.2.1 → bug fix
1.0.0 → stable API/behavior milestone
```

The integration's `manifest.json` version must match the release version.

HACS can present GitHub releases to users, so publishing releases is recommended.

---

# 26. HACS validation checklist

Before considering the repository HACS-ready:

- [ ] Repository is public.
- [ ] `custom_components/occupancy_duration/` exists.
- [ ] `manifest.json` is valid.
- [ ] `manifest.json` contains a valid domain.
- [ ] `manifest.json` contains a version.
- [ ] `manifest.json` contains code owner.
- [ ] Config flow is implemented and referenced.
- [ ] All runtime files are inside the integration directory.
- [ ] `hacs.json` exists at repository root.
- [ ] README exists.
- [ ] License exists.
- [ ] GitHub Issues are enabled.
- [ ] At least one GitHub release is created before default-repository submission.
- [ ] Integration passes HACS validation.
- [ ] Integration loads without errors in a clean Home Assistant instance.
- [ ] Branding exists under `custom_components/occupancy_duration/brand/`.
- [ ] No obsolete custom-brand PR to `home-assistant/brands` is required.
- [ ] Repository topics are configured.
- [ ] README installation instructions work.
- [ ] Config flow can create an integration entry.
- [ ] Config flow can be edited through Options.
- [ ] Integration unloads cleanly.
- [ ] Restart/restore behavior is tested.

---

# 27. Development environment

The agent should create a reproducible development setup.

Recommended:

```text
pyproject.toml
```

Use modern Python tooling appropriate for the Home Assistant version being targeted.

Include development dependencies for:

- Home Assistant
- pytest
- pytest-homeassistant-custom-component
- Ruff
- mypy if useful
- HACS validation tooling where appropriate

Do not unnecessarily add a large dependency stack.

---

# 28. Tests

Create:

```text
tests/
├── __init__.py
├── conftest.py
├── test_capability.py
├── test_session.py
├── test_decay.py
├── test_stage.py
├── test_config_flow.py
├── test_sensor.py
└── test_restore.py
```

Important tests:

### Capability detection

- continuous motion sensor
- event-only sensor
- occupancy sensor
- presence sensor
- unavailable sensor
- related occupancy entity
- unknown semantics

### Decay

- active sensor prevents decay
- inactive sensor decays
- event-only sensor decays
- stage changes decay behavior
- threshold/end grace behavior

### Session

- activity starts session
- activity does not reset start time
- decay enters DECAYING
- activity during decay returns ACTIVE
- session closes correctly
- new session starts after closure

### Restore

- active session restored
- duration continues across restart
- current source state is re-evaluated
- unavailable source does not immediately close session

---

# 29. Agent implementation order

Implement in this order:

## Phase 1 — Repository skeleton

Create:

```text
custom_components/occupancy_duration/
manifest.json
__init__.py
config_flow.py
strings.json
translations/en.json
hacs.json
README.md
LICENSE
```

Verify Home Assistant can discover the integration.

## Phase 2 — Basic helper

Implement:

```text
source selection
session
duration
occupancy binary sensor
```

## Phase 3 — Capability detection

Implement:

```text
capability.py
automatic strategy selection
diagnostics
```

## Phase 4 — Decay

Implement:

```text
decay.py
dynamic source re-check
threshold
grace period
```

## Phase 5 — Stages

Implement:

```text
stage.py
stage sensor
per-stage decay
```

## Phase 6 — Persistence

Implement:

```text
storage.py
restore
restart behavior
```

## Phase 7 — Branding and polish

Add:

```text
brand/icon.png
brand/icon@2x.png
brand/logo.png
brand/logo@2x.png
```

Complete:

```text
README
issue templates
CI
release workflow
```

## Phase 8 — Release

Run all tests and validation.

Create:

```text
v0.1.0
```

Then test installation through HACS using the GitHub repository.

---

# 30. Important compatibility note

This project targets current Home Assistant behavior.

Home Assistant changed custom-integration branding in 2026.3: custom integrations can now ship brand assets directly under their own integration directory. The old requirement to submit custom integration branding to the central brands repository is obsolete for this project.

Therefore, do not blindly copy an older HACS template that instructs the agent to create:

```text
home-assistant/brands/custom_integrations/occupancy_duration/
```

Use:

```text
custom_components/occupancy_duration/brand/
```

instead.

---

# 31. Definition of done

The initial HACS setup is complete when an agent can clone the repository and find:

```text
custom_components/occupancy_duration/
```

with a valid Home Assistant integration that:

1. Loads successfully.
2. Has a valid manifest.
3. Has UI configuration.
4. Has translations.
5. Has local brand assets.
6. Creates the intended entities.
7. Has tests.
8. Has HACS metadata.
9. Has README documentation.
10. Has GitHub issue templates.
11. Has CI validation.
12. Can be packaged/released through GitHub Releases.
13. Can be installed through HACS.
14. Does not depend on obsolete custom-brand repository procedures.

---

# References

Use these as the authoritative sources when implementing or updating the repository:

- Home Assistant integration file structure:
  https://developers.home-assistant.io/docs/creating_integration_file_structure/

- Home Assistant integration manifest:
  https://developers.home-assistant.io/docs/creating_integration_manifest/

- Home Assistant brand images:
  https://developers.home-assistant.io/docs/core/integration/brand_images/

- Home Assistant announcement for custom integration local brand assets:
  https://developers.home-assistant.io/blog/2026/02/24/brands-proxy-api/

- Home Assistant Brands repository:
  https://github.com/home-assistant/brands

- HACS integration repository:
  https://github.com/hacs/integration

- Modern Home Assistant/HACS integration blueprint:
  https://github.com/jpawlowski/hacs.integration_blueprint

The agent should re-check these sources when implementing against a newer Home Assistant/HACS version, because repository requirements and validation tooling can change.
