# Configuration Guide

Use this guide when the helper is installed but you are not sure how to choose the right settings.

## Recommended Starting Point

For most rooms, start with these defaults:

- Strategy: `Automatic`
- Default half-life: `60` seconds
- End threshold: `5`
- End grace: `15` seconds
- Restore session after restart: enabled

That baseline works well for typical PIR motion sensors and gives the integration enough time to bridge short gaps between events.

## Pick The Right Strategy

### `Automatic`

Use this unless the detected behavior is clearly wrong. The integration will re-evaluate the source and choose the best mode when capabilities change.

### `Native occupancy`

Use this when the source explicitly reports occupied and clear states and those states are already reliable.

Good fit:

- occupancy sensors
- presence sensors with stable occupied/clear reporting

### `Continuous motion`

Use this when the source stays `on` while activity is happening and returns `off` when motion stops.

Good fit:

- standard PIR binary sensors
- motion entities that provide a real on/off state

### `Event-only motion`

Use this when the source produces activity events but does not maintain a usable current state.

Good fit:

- stateless button-like motion events
- integrations where the source cannot be re-checked during decay

### `Hybrid occupancy + motion`

Use this when the device exposes both stronger occupancy semantics and frequent motion updates.

Good fit:

- mmWave devices paired with motion events
- devices that keep presence state but also emit motion bursts

## Tune Decay Without Guessing

Think of half-life as how quickly confidence fades after the last sign of activity.

- `30` seconds: aggressive; rooms clear quickly after activity stops
- `60` seconds: balanced; a good general-purpose default
- `180` seconds: sticky; useful when sensors are sparse or people stay still often

Use these adjustment rules:

- If sessions end too quickly, increase half-life first.
- If sessions linger too long, reduce half-life first.
- If the helper still feels too eager to close, lower the end threshold.
- If it refuses to close, raise the end threshold.

## Choose End Threshold And End Grace

### End threshold

This is the score where the session starts to close.

- Lower threshold: keeps sessions alive longer
- Higher threshold: ends sessions sooner

If you do not have a clear reason to change it, keep `5`.

### End grace

This is a short final window before the session closes completely.

- Short grace: faster off transitions
- Longer grace: more forgiving if one last event arrives late

Try:

- `10-15` seconds for fast rooms like hallways
- `20-30` seconds for rooms where motion updates can be irregular

## When To Add Stages

Stages are useful when you want automations to react differently as a visit gets longer.

Good uses:

- bathrooms where a long stay should trigger ventilation or a notification
- offices where a medium stay can enable a focused scene
- living rooms where longer stays should relax auto-off behavior

Keep stages simple. Three is usually enough:

| Stage | Duration | Why |
|---|---|---|
| Short | `0-60s` | Quick pass-through |
| Medium | `60-180s` | Normal room use |
| Long | `180s+` | Sustained occupancy |

## Room-Based Tuning Recipes

### Hallway or stairwell

- Use shorter half-life such as `30`
- Keep end grace low
- Usually no stages needed

### Bathroom

- Start with half-life `60`
- Add stages if you want different fan or alert behavior
- Keep restore enabled if restarts should not lose a live visit

### Office or study

- Increase half-life to `120` or `180` if people sit still for long periods
- Consider a long stage for comfort automations

### Living room with mmWave or presence

- Prefer `Automatic` or `Hybrid`
- Use a slower half-life if occupants are often still
- Avoid forcing `Continuous motion` unless you know the occupancy signal is weaker