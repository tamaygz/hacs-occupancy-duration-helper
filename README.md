# Occupancy Duration Helper

[![GitHub Release][releases-shield]][releases]
[![hacs][hacs-shield]][hacs]
[![License][license-shield]](LICENSE)

:pushpin: [HASS Community Thread](https://community.home-assistant.io/t/occupancy-duration-helper-finally-poop-in-peace/1025758)

Occupancy Duration Helper is a Home Assistant custom integration that turns motion and presence signals into persistent occupancy sessions with duration tracking, configurable stages, and adaptive decay.

It grew out of practical bathroom automations in my own home: I wanted to play music on the toilet, but only when actually pooping, so a fade-in starts only when a longer visit reaches the configured long stage. I also wanted music and ventilation while showering, but not when someone only enters briefly to wash their hands. This integration makes those use cases easy by listening to a motion sensor and tracking the session over time according to the configured stage profile.

<img width="1109" height="702" alt="image" src="https://github.com/user-attachments/assets/5dcb33a5-00eb-4e6b-8f88-d1688f52dc03" />

## Quick Start

[![Open your Home Assistant instance and add this repository in HACS][hacs-repository-badge]][hacs-repository-url]

1. Click the HACS button above to add this repository.
2. In HACS, download **Occupancy Duration Helper**.
3. Restart Home Assistant.
4. Go to **Settings → Devices & services → Add Integration**.
5. Search for **Occupancy Duration Helper** and complete the setup flow.

<details>
  <summary>Manual installation</summary>

1. Download or clone this repository.
2. Copy `custom_components/occupancy_duration` to:
   ```
   /config/custom_components/occupancy_duration
   ```
3. Restart Home Assistant.
4. Go to **Settings → Devices & services → Add Integration**.
5. Search for **Occupancy Duration Helper** and complete the setup flow.

</details>

---

## What It Does

Standard motion sensors measure whether motion *is happening right now*. They do not measure how long a space has been occupied, and a single clear signal (motion sensor turning OFF) may not mean the person has actually left.

**Occupancy Duration Helper** bridges this gap by:

1. Inspecting your source sensor to understand its actual capabilities (continuous ON/OFF, event-only, explicit occupancy, mmWave presence, etc.)
2. Starting a persistent **occupancy session** the moment evidence of activity arrives
3. Keeping the session alive as long as the sensor confirms continued activity — without restarting the clock on every new event
4. Applying **configurable exponential decay** only when the sensor genuinely goes inactive
5. Exposing the result as native Home Assistant entities for use in automations and dashboards

The integration does not treat `motion OFF` as `person left`. It treats motion as *evidence* of occupancy and evaluates that evidence continuously.

---

## Features

- **Sensor capability detection** — inspects each source and adapts behavior automatically for PIR, mmWave, event-only, and explicit occupancy sensors
- **Persistent sessions** — duration starts when an interaction begins and runs continuously until the session is closed
- **Adaptive decay** — score-based exponential decay with configurable half-life; decay is suppressed while the source still shows activity
- **Dynamic source re-check** — during a decaying session the integration re-reads the source to prevent premature closure
- **Configurable duration stages** — define Short / Medium / Long (or any custom stages) with per-stage decay rates
- **Automatic strategy selection** — chooses the most appropriate behavior for your sensor type with a UI override option
- **Session persistence** — active sessions survive Home Assistant restarts
- **Full UI configuration** — set up and reconfigure entirely from Settings → Devices & services
- **Diagnostic export** — download a full capability and session report from the Home Assistant UI

---

## How It Works

```
Source sensor
     │
     ▼
Capability inspection
     │
     ▼
Strategy selection  ←──── User override (optional)
     │
     ▼
Occupancy session engine
  ┌──────────────────────────────────────┐
  │  IDLE → ACTIVE → DECAYING → ENDING  │
  │              ↑___────┘              │
  │                                      │
  │  score(t) = score₀ × 2^(-t / T½)   │
  └──────────────────────────────────────┘
     │
     ▼
Duration sensor · Occupancy binary sensor · Stage sensor
```

### Strategy modes

| Mode | Used when |
|---|---|
| Native occupancy | Source explicitly reports occupied / clear |
| Continuous motion | Source is a binary ON/OFF motion sensor |
| Event-only | Source fires events with no persistent state |
| Hybrid | Source exposes both motion and occupancy |
| Auto (default) | Integration selects from the above automatically |

---

## Requirements / Compatibility

- **Home Assistant** ≥ 2026.3.0
- **Python** ≥ 3.14 (included with supported Home Assistant installations)
- No third-party Python packages required

---

## Installation

### HACS (recommended)

1. Click the HACS button in [Quick Start](#quick-start) to add this repository.
2. Open HACS and download **Occupancy Duration Helper**.
3. Restart Home Assistant if prompted.
4. Go to **Settings → Devices & services → Add Integration** and search for **Occupancy Duration Helper**.

### Manual

1. Download or clone this repository.
2. Copy the `custom_components/occupancy_duration` folder into:
   ```
   /config/custom_components/occupancy_duration
   ```
3. Restart Home Assistant.
4. Go to **Settings → Devices & services → Add Integration** and search for **Occupancy Duration Helper**.

---

## Configuration

Add the integration from the UI. The setup flow asks for:

1. **Name** — used to name the entities
2. **Source entity** — any motion, occupancy, or presence binary sensor / sensor / event entity
3. **Capability preview** — detected sensor behavior is shown; choose whether to accept the recommendation
4. **Sensor strategy** — normally selected automatically; override here for special cases
5. **Decay settings** — pick Fast / Normal / Slow or enter a custom half-life in seconds
6. **End threshold** — activity score below which the session moves to ending state (default 5)
7. **End grace** — seconds to remain in ending state before closing (default 15)
8. **Duration stages** (optional) — define named ranges with per-stage decay rates

### Reconfigure

To change the **name** or **source entity**, use the **Reconfigure** option on the integration page.

To change **strategy, decay settings, stages, or restore behavior**, use the **Configure** (options) button.

---

## Sensor Capabilities

The integration inspects each source sensor before creating a session. The capability summary is visible in the config flow and in the diagnostics export.

| Capability | What it means |
|---|---|
| Current state available | The source has a readable state that can be queried between events |
| Motion ON/OFF | The source uses binary semantics where ON means motion is happening |
| Occupancy state | The source explicitly reports occupied / clear |
| Presence state | The source explicitly reports presence / absence |
| Event-only | The source fires events but has no readable persistent state |
| Re-check during decay | The integration can query the source while decaying to prevent premature closure |

When multiple signals are available (e.g. a device with both motion and occupancy entities), the integration prefers the more semantically authoritative one.

---

## Duration Stages

Stages let you attach meaning to how long the space has been occupied. Example:

| Stage | Duration | Decay half-life |
|---|---|---|
| Short | 0 – 60 s | 30 s |
| Medium | 60 – 180 s | 60 s |
| Long | 180 s+ | 180 s |

Stages are monotonic: once a session reaches **Long**, it does not return to **Medium** even if motion stops. The stage represents *elapsed interaction time*, not motion intensity.

---

## Entities

### Duration sensor

```
sensor.<name>_duration
```

State: seconds (integer, wall-clock duration since session started)

| Attribute | Value |
|---|---|
| `active` | `true` while session is open |
| `started_at` | ISO 8601 timestamp |
| `last_activity_at` | ISO 8601 timestamp |
| `stage` | Current stage name or `none` |
| `session_state` | `idle` / `active` / `decaying` / `ending` / `closed` |
| `score` | Activity score 0–100 |

### Occupancy binary sensor

```
binary_sensor.<name>_occupancy
```

Device class: `occupancy`. ON while a session is open, OFF when idle.

### Stage sensor

```
sensor.<name>_stage
```

State: current stage name (e.g. `short`, `medium`, `long`). Only created when stages are configured.

---

## Automation Examples

### Trigger when a bathroom visit becomes a long session

```yaml
trigger:
  - platform: state
    entity_id: sensor.bathroom_stage
    to: long
action:
  - service: notify.mobile_app
    data:
      message: "Long bathroom visit detected"
```

### Turn off the light only when occupancy is truly gone

```yaml
trigger:
  - platform: state
    entity_id: binary_sensor.bathroom_occupancy
    to: "off"
action:
  - service: light.turn_off
    target:
      entity_id: light.bathroom
```

---

## Troubleshooting

**Session ends too quickly**
→ Check the detected strategy in Diagnostics. If the source is continuous (ON while motion occurs), the session should not decay while the sensor is ON. A strategy mismatch can cause premature closure.

**Session never ends**
→ Increase the end threshold or reduce the decay half-life for the last stage.

**Duration resets unexpectedly**
→ This should not happen. Open a [GitHub issue][issues] with a diagnostics download attached.

**Integration not loading after restart**
→ Check Home Assistant logs for errors from the `occupancy_duration` domain.

---

## Diagnostics

Download a full diagnostic report from **Settings → Devices & services → Occupancy Duration Helper → Download diagnostics**.

The helper also exposes diagnostic-category entities in Home Assistant for score, strategy, and session timestamps.

The report includes:
- Source entity and current state
- Detected capabilities with confidence levels
- Selected strategy and why it was chosen
- Current session state, score, stage, and timestamps
- Decay configuration

This file does not include secrets or sensitive credentials.

---

## Documentation

Additional short guides live in [docs/README.md](./docs/README.md):

- [Configuration Guide](./docs/configuration-guide.md)
- [Automation Recipes](./docs/automation-recipes.md)
- [Troubleshooting](./docs/troubleshooting.md)

---

## Development

Requirements: Python 3.14, pip.

```sh
git clone https://github.com/tamaygz/hacs-occupancy-duration-helper
cd hacs-occupancy-duration-helper
pip install -e ".[dev]"
pytest
```

Linting and formatting:

```sh
python -m ruff check .
python -m ruff format .
python -m mypy custom_components tests
```

### Validation and release checklist

Before publishing a release:

1. Run the shared validation tasks locally or via CI.
2. Ensure `custom_components/occupancy_duration/manifest.json` and `pyproject.toml` match the intended GitHub release version.
3. Replace the placeholder brand assets in `custom_components/occupancy_duration/brand/` with real artwork.
4. Confirm README, diagnostics, config flow, unload, and restore behavior still match the current implementation.
5. Publish a full GitHub Release, not only a tag.
6. Use `.github/workflows/release.yml` so version bumps, the release commit, the tag, and the GitHub Release stay in sync.

---

## Contributing

Issues and pull requests are welcome at <https://github.com/tamaygz/hacs-occupancy-duration-helper/issues>.

Please include a diagnostics download when reporting bugs.

---

## License

MIT — see [LICENSE](LICENSE).

---

[releases-shield]: https://img.shields.io/github/release/tamaygz/hacs-occupancy-duration-helper.svg?style=flat-square
[releases]: https://github.com/tamaygz/hacs-occupancy-duration-helper/releases
[hacs-shield]: https://img.shields.io/badge/HACS-Default-41BDF5.svg?style=flat-square
[hacs]: https://hacs.xyz
[hacs-repository-badge]: https://my.home-assistant.io/badges/hacs_repository.svg
[hacs-repository-url]: https://my.home-assistant.io/redirect/hacs_repository/?owner=tamaygz&repository=hacs-occupancy-duration-helper&category=integration
[license-shield]: https://img.shields.io/github/license/tamaygz/hacs-occupancy-duration-helper.svg?style=flat-square
[issues]: https://github.com/tamaygz/hacs-occupancy-duration-helper/issues
occupancy decay
presence timeout
PIR
mmWave
automation
sensor helper
custom integration
custom component
