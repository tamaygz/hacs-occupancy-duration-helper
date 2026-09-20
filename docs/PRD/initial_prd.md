# Occupancy Duration Helper — Product Requirements Document

**Working name:** Occupancy Duration Helper  
**Author:** @tamaygz
**Repo:** hacs-occupancy-duration-helper
**Type:** Home Assistant HACS custom integration  
**Status:** Product / architecture proposal  
**Primary goal:** Turn heterogeneous motion/activity signals into a persistent, queryable interaction session with reliable duration and configurable activity stages.

---

## 1. Product Summary

Occupancy Duration Helper is a Home Assistant custom integration distributed through HACS.

It solves a common limitation of motion sensors: **motion is not the same thing as occupancy, and motion ending is not necessarily the end of an interaction**.

The integration creates an abstraction between raw sensor behavior and automations:

> **Sensor evidence → persistent interaction session → duration → stage → end**

A user adds an Occupancy Duration Helper from the Home Assistant UI, selects a motion/activity sensor, and optionally defines duration stages such as:

- 0–60 seconds → Short
- 60–180 seconds → Medium
- 180+ seconds → Long

The integration continuously evaluates what the selected sensor is actually capable of and adapts its session logic accordingly.

This sensor-capability awareness is a core product feature.

Instead of assuming that every motion sensor behaves like a binary `on/off` PIR, the integration should inspect the entity and device metadata and determine, where possible:

- whether the sensor exposes occupancy/presence information
- whether it has explicit motion start/end semantics
- whether it is edge-triggered/event-based
- whether it remains `on` while motion continues
- whether it exposes additional attributes or entities that can be used as evidence
- whether the integration can actively re-check the source while a session is decaying
- whether the source is currently still detecting activity

The helper then chooses the most appropriate behavior rather than blindly applying one decay algorithm.

---

# 2. Problem

Home Assistant provides many motion, occupancy, and presence sensors, but they have very different semantics.

Examples:

### Sensor A — classic PIR

```text
motion detected → ON
motion stopped  → OFF
```

An OFF event does not necessarily mean the person left. A person can remain stationary in a bathroom.

### Sensor B — event-only motion detector

```text
motion detected → event
```

There may be no meaningful OFF state at all.

### Sensor C — occupancy-aware sensor

```text
occupancy = detected
occupancy = clear
```

The sensor may already perform its own persistence and stationary-person detection.

### Sensor D — mmWave presence sensor

It may report presence continuously even when no movement occurs.

### Sensor E — sensor with duration/occupancy attributes

Some devices expose additional information such as occupancy duration or not-occupied duration.

A generic "motion starts timer, motion ends timer" implementation therefore produces unreliable interaction durations.

---

# 3. Product Principles

## 3.1 Motion is evidence, not necessarily occupancy

The integration must not equate:

```text
motion OFF = person left
```

Instead, motion contributes evidence to a session.

---

## 3.2 Duration is wall-clock session duration

Duration starts when the interaction session begins.

```text
duration = now - session_started_at
```

Motion stopping must not reset the duration.

New motion must reinforce an existing session rather than restart it.

---

## 3.3 Sensor semantics matter

The integration should first understand the selected source.

A sensor that explicitly reports occupancy should be treated differently from an edge-triggered motion event source.

---

## 3.4 Never decay blindly

When the integration is in a decay/uncertain state, it should re-evaluate the source whenever possible.

If the source is still actively detecting the relevant condition, the integration should **not decay the session merely because a previous event has aged out**.

Examples:

- PIR binary sensor is still `on` → do not decay.
- Occupancy sensor still reports occupied → do not decay.
- Presence sensor still reports presence → do not decay.
- Event-only source has no current-state signal → decay according to configured event semantics.
- Source exposes a richer occupancy signal → prefer it over inferred motion state.

This is an important reliability mechanism.

---

# 4. Core User Experience

## 4.1 Create helper

Home Assistant:

**Settings → Devices & services → Add Integration → Occupancy Duration Helper**

The setup flow asks for:

1. Name
2. Source entity
3. Automatically detected sensor capabilities
4. Behavior / interpretation mode
5. Default decay configuration
6. End threshold / grace period
7. Optional duration stages

The integration should make the default configuration usable without requiring users to understand decay mathematics.

---

# 5. Automatic Sensor Capability Detection

This is a first-class subsystem.

## 5.1 Capability inspection

When a source entity is selected, the integration inspects the available Home Assistant entity/device information.

Possible evidence sources include:

- entity domain
- device class
- current state
- state attributes
- supported features
- device/entity registry metadata
- related entities belonging to the same device
- event entities
- trigger/event semantics where discoverable
- known platform/device integration metadata
- occupancy/presence-specific attributes
- duration-related attributes

The integration should not rely solely on the entity name.

For example, `binary_sensor.bathroom_motion` may expose different semantics from another entity with the same device class.

---

## 5.2 Capability model

Internally, the integration should normalize the discovered behavior into a capability model.

Example:

```python
SensorCapabilities(
    supports_current_state=True,
    supports_motion_state=True,
    supports_occupancy_state=True,
    supports_presence_state=False,
    supports_start_event=True,
    supports_end_event=True,
    event_only=False,
    state_is_continuous=True,
    can_recheck_during_decay=True,
    exposes_duration=False,
    confidence=0.92,
)
```

Not every capability will be known with certainty.

The model should distinguish:

- **confirmed**
- **inferred**
- **unknown**

The UI can expose this as a diagnostic summary.

---

## 5.3 Capability priority

When multiple signals are available, the integration should prefer the most semantically meaningful signal.

Suggested priority:

1. Explicit occupancy/presence
2. Explicit continuous presence detection
3. Current motion state
4. Motion start/end events
5. Event-only motion detection
6. Generic state changes

This avoids treating a low-level motion signal as more authoritative than a device's own occupancy determination.

---

# 6. Sensor Strategy Modes

The integration should automatically choose a strategy from detected capabilities.

Users may override the strategy in Advanced settings.

### Mode A — Native occupancy

If the source provides reliable occupancy/presence:

```text
occupied → session active
not occupied → session ends
```

The duration helper primarily mirrors the sensor's occupancy semantics.

Decay is normally unnecessary for determining occupancy, although optional end grace can still be applied.

---

### Mode B — Continuous motion state

For a sensor such as:

```text
ON  = currently detecting motion
OFF = currently not detecting motion
```

Behavior:

```text
ON  → start/reinforce session
OFF → enter decay
```

During decay:

```text
if source becomes ON:
    stop decay
    reinforce session
else:
    continue decay
```

If the source remains ON, no decay should occur.

---

### Mode C — Event-only motion

For:

```text
motion detected → event
```

there is no reliable current-state query.

Behavior:

```text
event → start/reinforce session
no event → decay according to configured half-life
```

The UI should clearly tell the user that the source cannot be actively re-checked.

---

### Mode D — Hybrid / richer device

If a device exposes both motion and occupancy:

```text
motion → activity evidence
occupancy → session truth
```

The occupancy signal should normally control session termination while motion reinforces activity.

---

# 7. Dynamic Re-check During Decay

This is one of the defining features of the integration.

When a session has stopped receiving activity events, the helper enters a **DECAYING** state.

Before applying decay, it should determine whether the source currently indicates continued activity.

Conceptually:

```text
DECAY TICK
    ↓
Can source be queried?
    ↓
YES ──→ source still active?
           ├── YES → do not decay / reinforce
           └── NO  → decay
    ↓
NO
    ↓
Apply configured event-only decay
```

This prevents a common failure:

```text
motion event
↓
sensor remains ON
↓
event timestamp becomes old
↓
algorithm assumes inactivity
↓
session decays incorrectly
```

For continuous-state sensors, the current state is authoritative whenever available.

---

# 8. Session State Machine

The session state should be explicit.

```text
IDLE
  │
  │ activity / occupancy detected
  ▼
ACTIVE
  │
  │ source no longer actively detecting
  ▼
DECAYING
  │
  ├── activity returns ───────→ ACTIVE
  │
  └── score below threshold
          │
          ▼
       ENDING
          │
          │ grace expires
          ▼
        CLOSED
          │
          ▼
         IDLE
```

Important:

**The duration clock runs from `session_started_at` until the session is closed.**

A transition:

```text
ACTIVE → DECAYING → ACTIVE
```

does not restart the session.

---

# 9. Session Data Model

```python
OccupancySession:
    id
    started_at
    last_activity_at
    last_active_signal_at
    ended_at
    score
    stage
    state
```

Derived values:

```text
duration
idle_duration
time_since_last_motion
current_stage
active
```

Potential future fields:

```text
source_signal
termination_reason
event_count
event_density
sensor_confidence
```

---

# 10. Activity Score

The integration should use a score/confidence concept internally rather than treating duration itself as the occupancy signal.

Example:

```text
0–100
```

Activity can increase the score:

```text
motion detected → score + increment
occupancy detected → score = 100
presence detected → score = 100
```

The score decays when the source no longer reports active detection.

Suggested decay model:

```text
score(t) = score0 × 0.5 ^ (elapsed / half_life)
```

This gives users an intuitive configuration:

> "How long should activity remain plausible?"

Rather than:

> "Subtract 3 every 10 seconds."

---

# 11. Duration Stages

Users may optionally define duration stages.

Example:

| Stage | Duration | Decay |
|---|---:|---:|
| Short | 0–60s | 30s half-life |
| Medium | 60–180s | 60s half-life |
| Long | 180s+ | 180s half-life |

Stages are monotonic during a session:

```text
NONE → SHORT → MEDIUM → LONG
```

A session that has reached LONG should not return to SHORT merely because motion stopped.

The stage represents elapsed interaction time, not instantaneous motion intensity.

---

# 12. Why Stage-Specific Decay Matters

Different interactions have different motion patterns.

Example: bathroom.

### Short interaction

A person enters, uses the sink, and leaves.

The session should disappear relatively quickly after the last detection.

### Long interaction

A person enters and sits on the toilet.

There may be almost no motion for several minutes.

A short decay would incorrectly terminate the session.

Therefore:

```text
short interaction → fast decay
long interaction  → slow decay
```

This is configurable per stage.

---

# 13. Entity Model

The helper should expose native Home Assistant entities.

## Primary entities

### Duration sensor

```text
sensor.<name>_duration
```

State:

```text
seconds
```

Attributes:

```yaml
active: true
started_at: "2026-09-20T21:00:00+02:00"
last_activity_at: "2026-09-20T21:03:12+02:00"
stage: long
state: decaying
score: 71
```

---

### Occupancy binary sensor

```text
binary_sensor.<name>_occupancy
```

States:

```text
on  = session active
off = no session
```

Device class:

```text
occupancy
```

---

### Stage sensor

```text
sensor.<name>_stage
```

Example states:

```text
short
medium
long
```

The stage sensor should only be created when stages are configured.

---

## Optional diagnostic entities

Disabled by default:

```text
sensor.<name>_activity_score
sensor.<name>_idle_duration
sensor.<name>_last_activity
sensor.<name>_session_started
sensor.<name>_sensor_strategy
sensor.<name>_sensor_capability
```

---

# 14. Events

The integration should emit Home Assistant events for important transitions.

### Session started

```text
occupancy_duration_started
```

Payload:

```yaml
entity_id:
session_id:
started_at:
source_entity:
```

### Stage changed

```text
occupancy_duration_stage_changed
```

Payload:

```yaml
entity_id:
session_id:
previous_stage:
new_stage:
duration:
```

### Session ended

```text
occupancy_duration_ended
```

Payload:

```yaml
entity_id:
session_id:
started_at:
ended_at:
duration:
final_stage:
termination_reason:
```

---

# 15. Configuration

## Basic configuration

```text
Name
Source sensor
```

The integration automatically detects the source capabilities.

The user sees something like:

```text
Detected sensor behavior

✓ Current state available
✓ Motion ON/OFF
✓ Can be re-checked during decay
✗ Explicit occupancy
✗ Event-only

Selected strategy:
Continuous motion
```

---

## Default decay

Simple UI:

```text
Activity persistence

○ Fast
● Normal
○ Slow
○ Custom
```

Advanced configuration:

```text
Default half-life: 60 seconds
End threshold: 5%
End grace: 15 seconds
```

---

## Duration stages

Optional:

```text
[ + Add duration stage ]

Short       0–60 sec       Fast
Medium     60–180 sec      Normal
Long         180+ sec      Slow
```

Each stage supports:

```text
Name
Minimum duration
Maximum duration
Decay behavior
```

Decay can be:

```text
Inherit default
Fast
Normal
Slow
Custom half-life
```

---

# 16. Automatic Configuration Recommendations

The integration should not merely detect capabilities; it should recommend configuration.

Example:

```text
Your sensor reports continuous occupancy.

Recommended strategy:
Native occupancy

Decay is not required to determine occupancy.
```

Another:

```text
Your sensor reports motion ON/OFF.

Recommended strategy:
Continuous motion + decay

The sensor can be re-checked while decaying, so an ON state will prevent decay.
```

Another:

```text
This source appears to be event-only.

Recommended strategy:
Event-based decay

The integration cannot verify whether the source is still detecting between events.
```

The user can override recommendations.

---

# 17. Related-Entity Discovery

Some devices expose multiple entities.

Example:

```text
Device
├── motion
├── occupancy
├── presence
├── illuminance
└── signal strength
```

When the user selects the motion entity, the integration should inspect sibling entities belonging to the same device.

If an occupancy entity exists, the UI can offer:

```text
We found a related occupancy entity:

binary_sensor.bathroom_occupancy

Use this as the authoritative occupancy signal?
```

This can substantially improve reliability without requiring manual configuration.

The integration must not automatically bind unrelated entities merely because their names look similar.

Device/registry relationships and explicit user selection should be preferred.

---

# 18. Sensor Capability Diagnostics

A diagnostic view should explain why the helper behaves as it does.

Example:

```text
Sensor capability report

Source
  binary_sensor.bathroom_motion

Current state
  ✓ available

Motion state
  ✓ ON/OFF

Occupancy state
  ✗ not available

Start events
  ✓ inferred from ON transition

End events
  ✓ inferred from OFF transition

Continuous re-check
  ✓ available

Selected strategy
  Continuous motion + decay

Current source state
  ON

Decay
  Paused — source is still detecting
```

This makes the system debuggable.

---

# 19. Restore After Home Assistant Restart

The integration should persist enough state to restore active sessions.

Persist:

```text
session_id
started_at
last_activity_at
last_active_signal_at
score
stage
state
```

On restart:

1. Load persisted session.
2. Determine current source state.
3. Re-evaluate sensor capabilities.
4. Calculate elapsed wall-clock time.
5. Recalculate score where appropriate.
6. Resume or close the session.

For a continuously active sensor:

```text
restart
↓
sensor still ON
↓
session remains active
↓
no decay
```

For an event-only source:

```text
restart
↓
no current state available
↓
apply event-based recovery policy
```

Restore behavior should be configurable.

---

# 20. Edge Cases

## Motion stops while person is stationary

Expected:

```text
ACTIVE → DECAYING
```

The session remains alive according to decay.

---

## Motion sensor remains ON

Expected:

```text
ACTIVE
```

No decay should occur merely because the last event is old.

---

## New motion during decay

Expected:

```text
DECAYING → ACTIVE
```

The session start timestamp remains unchanged.

---

## New motion after the score has nearly reached zero

If the session has not yet closed:

```text
DECAYING → ACTIVE
```

If it has already closed:

```text
new session
```

---

## Sensor changes strategy/capability

If the source's capabilities change after setup, the integration should re-evaluate them.

For example, if a device begins exposing an occupancy entity:

```text
re-detect capabilities
↓
update recommendation
↓
retain user override if explicitly configured
```

Automatic detection must never silently override an explicit user configuration.

---

## Sensor unavailable

The integration should distinguish:

```text
source inactive
```

from:

```text
source unavailable
```

An unavailable sensor must not automatically be interpreted as:

```text
person left
```

Recommended behavior:

- preserve session temporarily
- expose diagnostic state
- apply configurable unavailable timeout
- optionally terminate after timeout

---

# 21. Manual Strategy Override

Automatic detection should be the default.

Advanced users can select:

```text
Automatic
Native occupancy
Continuous motion
Event-only motion
Hybrid occupancy + motion
```

The UI should explain that manual override disables some automatic assumptions.

---

# 22. Automation Examples

## Toilet interaction

```yaml
condition:
  - condition: state
    entity_id: sensor.toilet_duration_stage
    state: long
```

This can represent a long bathroom interaction without relying on raw motion timing.

---

## Shower detection

```yaml
condition:
  - condition: state
    entity_id: sensor.shower_room_stage
    state: long
```

Combined with humidity:

```text
long occupancy
+
humidity rising
=
strong shower evidence
```

The integration itself should not claim that LONG means "shower". It only exposes the configured duration stage.

---

# 23. Integration with Other Occupancy Systems

The helper should remain independent of systems such as:

- Area Occupancy Detection
- Wasp-in-a-Box
- Magic Areas
- Soft Presence
- mmWave presence sensors
- ESPresense
- room-assistant

It can consume their occupancy/presence entities as sources.

It can also provide session duration to higher-level systems.

Example:

```text
PIR
 ↓
Occupancy Duration Helper
 ↓
duration / stage / occupancy
 ↓
Area Occupancy Detection or automation
```

or:

```text
PIR + mmWave
 ↓
higher-level occupancy system
 ↓
occupancy entity
 ↓
Occupancy Duration Helper
 ↓
session duration
```

This separation is intentional.

---

# 24. Architecture

Suggested package structure:

```text
custom_components/
└── occupancy_duration/
    ├── __init__.py
    ├── manifest.json
    ├── const.py
    ├── config_flow.py
    ├── coordinator.py
    ├── capability.py
    ├── session.py
    ├── decay.py
    ├── stage.py
    ├── storage.py
    ├── sensor.py
    ├── binary_sensor.py
    ├── select.py
    ├── number.py
    ├── diagnostics.py
    └── translations/
        └── en.json
```

---

# 25. Domain Models

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

```python
@dataclass
class OccupancySession:
    id: str
    started_at: datetime
    last_activity_at: datetime
    last_active_signal_at: datetime | None
    ended_at: datetime | None
    score: float
    stage: str | None
    state: SessionState
```

```python
@dataclass
class DurationStage:
    id: str
    name: str
    min_duration: int
    max_duration: int | None
    decay_half_life: float | None
```

---

# 26. Processing Loop

Conceptual algorithm:

```python
async def on_source_update(event):
    if is_authoritative_occupancy_active(event):
        start_or_reinforce_session()
        score = 100
        return

    if is_motion_active(event):
        if session is None:
            start_session()

        score = reinforce(score)
        last_activity_at = now
        last_active_signal_at = now
        state = ACTIVE
        update_stage()


async def decay_tick():
    if session is None:
        return

    source_state = await capability_manager.recheck()

    if source_state.is_authoritatively_active:
        score = reinforce(score)
        state = ACTIVE
        last_active_signal_at = now
        return

    if source_state.is_currently_active:
        score = reinforce(score)
        state = ACTIVE
        last_active_signal_at = now
        return

    score = apply_decay(score, elapsed, current_half_life)

    if score <= end_threshold:
        state = ENDING

    if ending_grace_expired():
        end_session()
```

The actual implementation should avoid repeatedly resetting timestamps simply because a state is still ON. `last_active_signal_at` should represent meaningful observation/reinforcement, not every scheduler tick.

---

# 27. Decay Model

The preferred model is continuous exponential decay.

```text
score(t) = score0 × 2^(-t / half_life)
```

Advantages:

- smooth behavior
- independent of polling frequency
- easy to explain
- easy to configure
- supports different stage half-lives
- survives Home Assistant restarts

The integration should not use a simplistic:

```text
score -= 1 every 30 seconds
```

unless implemented as an optional compatibility mode.

---

# 28. Polling / Re-check Strategy

The integration should avoid unnecessary polling.

Preferred order:

1. Subscribe to source state changes.
2. Use event-driven updates whenever possible.
3. During decay, schedule lightweight re-checks only when useful.
4. If the source has a current state, inspect it before applying decay.
5. Use a configurable/default decay evaluation interval.

For continuous sensors, a state update to ON should immediately interrupt decay.

For event-only sources, no polling should be performed if there is no meaningful state to query.

---

# 29. Performance Requirements

The integration should support many helpers without creating one high-frequency polling loop per entity.

Use a shared scheduler/coordinator where practical.

Requirements:

- event-driven source handling
- adaptive decay evaluation
- no unnecessary polling while ACTIVE on authoritative occupancy sources
- no busy loops
- efficient state persistence
- safe behavior with dozens/hundreds of helpers

---

# 30. Configuration Storage

Use Home Assistant config entries.

Example:

```yaml
{
  "source_entity": "binary_sensor.bathroom_motion",
  "strategy": "auto",
  "default_half_life": 60,
  "end_threshold": 5,
  "end_grace": 15,
  "restore_session": true,
  "stages": [
    {
      "id": "short",
      "name": "Short",
      "min_duration": 0,
      "max_duration": 60,
      "half_life": 30
    },
    {
      "id": "medium",
      "name": "Medium",
      "min_duration": 60,
      "max_duration": 180,
      "half_life": 60
    },
    {
      "id": "long",
      "name": "Long",
      "min_duration": 180,
      "max_duration": null,
      "half_life": 180
    }
  ]
}
```

---

# 31. MVP Scope

## Required

- HACS installation
- Config flow
- Source entity selection
- Automatic capability inspection
- Automatic strategy selection
- Continuous-state re-check
- Event-only fallback
- Persistent session
- Duration sensor
- Occupancy binary sensor
- Optional duration stages
- Per-stage decay
- End threshold
- End grace
- Restore after restart
- Diagnostics
- Native HA entity/device integration

## Not required for MVP

- Machine learning
- Automatic activity classification such as "shower"
- Multi-person tracking
- Multi-zone tracking
- Camera integration
- Bluetooth triangulation
- Complex sensor fusion
- Automatic semantic interpretation of arbitrary sensor attributes

---

# 32. Future Versions

## V1.1 — Multi-signal helpers

Allow:

```text
PIR       +20
mmWave    +80
Door      +10
Humidity  +15
```

Signals can reinforce or weaken a session.

---

## V1.2 — Activity evidence

Allow configurable evidence rules:

```text
long occupancy
+
humidity increase
=
shower candidate
```

---

## V1.3 — Sensor profiles

Known device integrations can provide explicit capability adapters.

Example:

```text
Xiaomi presence sensor
Everything Presence
AOD
ESPresense
```

---

## V1.4 — Visual session timeline

A dashboard card could show:

```text
00:00 ───── 01:00 ───── 03:00 ───── 05:00
  SHORT        MEDIUM        LONG
     █████████████████████████████
                         ↑
                    last motion
```

---

# 33. Security and Privacy

The integration should operate entirely within Home Assistant.

No cloud service is required.

No sensor data should leave the Home Assistant instance.

The integration should not require access to cameras or external services for its core functionality.

---

# 34. Testing Strategy

Tests should cover:

### Sensor semantics

- continuous ON/OFF sensor
- event-only source
- occupancy source
- presence source
- unavailable source
- source with related occupancy entity

### Session behavior

- first activity starts session
- subsequent activity does not restart session
- OFF enters decay
- ON during decay pauses/reverses decay
- stationary occupancy remains active
- threshold enters ENDING
- grace period closes session
- new activity before closure reactivates session
- new activity after closure starts new session

### Duration

- wall-clock duration remains monotonic
- stage transitions happen at configured thresholds
- stage never moves backward during a session

### Restart

- restore active session
- restore decaying session
- restore closed session
- sensor active after restart
- sensor unavailable after restart

### Capability detection

- explicit occupancy wins over motion
- continuous motion recognized
- event-only recognized
- unknown behavior handled safely
- manual override wins over automatic detection

---

# 35. Acceptance Criteria

The MVP is successful when:

1. A user can create a helper entirely from the Home Assistant UI.
2. The integration automatically inspects the selected source.
3. The UI explains what capabilities were detected.
4. The integration selects a sensible strategy automatically.
5. Continuous sensors are actively re-checked during decay.
6. A sensor that is still detecting does not decay merely because an old event is stale.
7. Event-only sensors use event-based decay rather than pretending they have a current state.
8. Duration starts once and remains continuous until session closure.
9. Motion stopping does not immediately end a session.
10. New motion reinforces an existing session without resetting duration.
11. Users can configure duration stages.
12. Users can configure per-stage decay.
13. Sessions survive Home Assistant restarts according to configuration.
14. Sensor unavailability is not treated as occupancy absence.
15. Diagnostics make the helper's decisions understandable.
16. The resulting entities can be used naturally in Home Assistant automations.

---

# 36. Example End-to-End Scenario

Configuration:

```text
Name:
Bathroom Interaction

Source:
binary_sensor.bathroom_motion

Detected capabilities:
✓ current state
✓ motion ON/OFF
✓ continuous state
✓ re-check available
✗ native occupancy
```

Stages:

```text
Short    0–60s      30s half-life
Medium   60–180s    60s half-life
Long     180s+      180s half-life
```

Timeline:

```text
00:00  motion ON
       → session starts
       → stage SHORT

00:45  motion still ON
       → no decay

01:00  stage MEDIUM

02:00  motion OFF
       → enter DECAYING

02:20  sensor checked
       → still OFF
       → decay using MEDIUM rules

03:00  stage becomes LONG

03:10  sensor checked
       → still OFF
       → decay using LONG rules

04:00  motion ON
       → DECAYING → ACTIVE
       → score reinforced
       → duration remains 4 minutes
       → stage remains LONG

05:30  motion OFF
       → decay

Eventually:
       → score below threshold
       → ENDING
       → grace expires
       → session CLOSED
```

The key property is:

> **The helper measures the interaction, not merely the time since the last motion event.**

---

# 37. Product Positioning

Occupancy Duration Helper should be positioned as a **semantic bridge between raw sensors and Home Assistant automations**.

It is not intended to replace motion sensors, presence sensors, or full occupancy systems.

Instead:

```text
Raw sensor
    ↓
Capability-aware interpretation
    ↓
Persistent session
    ↓
Duration + stage + occupancy
    ↓
Automations / higher-level occupancy systems
```

This makes a simple PIR much more useful while still respecting richer sensors when they are available.

---

# 38. Key Design Decision

The central architectural decision is:

> **Do not build a timer around motion events. Build a capability-aware session engine around evidence of occupancy/activity.**

The timer/duration is only one output of that engine.

The engine should know:

- when the session started
- when meaningful activity was last observed
- what the source currently says
- whether the source can be re-checked
- whether occupancy is explicitly reported
- how confident the system is that the interaction continues
- which duration stage has been reached
- how quickly evidence should decay
- when the session can safely be closed

This architecture allows the same helper to work with simple PIR sensors, event-only motion devices, occupancy sensors, mmWave presence sensors, and richer multi-entity devices without forcing every sensor into the same behavioral model.
