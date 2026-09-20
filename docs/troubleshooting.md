# Troubleshooting

Use this guide when the helper is installed but its behavior does not match the room.

## First Checks

Before changing settings, confirm three things:

1. The source entity is the one you actually want.
2. The detected strategy in diagnostics matches the real behavior of the sensor.
3. The helper entities are the ones your automations are using.

Download diagnostics from the integration page if you need to confirm the detected capability summary and selected strategy.

## Sessions End Too Quickly

Likely causes:

- half-life is too short for the room
- the source was detected as the wrong strategy
- the sensor itself goes quiet for long gaps

What to try:

1. Increase the default half-life.
2. Check diagnostics to confirm whether the integration chose `Continuous motion`, `Native occupancy`, `Event-only`, or `Hybrid`.
3. If auto-detection is wrong, set a manual strategy and test again.
4. If you use stages, make sure later stages are not using a shorter half-life than intended.

## Sessions Never End

Likely causes:

- half-life is too long
- end threshold is too low
- a presence-oriented source keeps reporting activity

What to try:

1. Reduce half-life.
2. Raise the end threshold.
3. Check whether the source entity remains active even when the room is empty.
4. If a combined sensor over-reports occupancy, compare results with another available source entity.

## Duration Resets Unexpectedly

This normally points to a new session being created instead of the existing one staying alive.

Check:

1. Whether the source entity changed in reconfigure.
2. Whether Home Assistant restarted and restore was disabled.
3. Whether the underlying source briefly became unavailable or changed semantics.

If the issue persists, collect diagnostics and open an issue with the session timestamps.

## Stage Never Changes

Likely causes:

- no stages are configured
- the session never stays open long enough to reach the next stage
- stage ranges overlap or were defined differently than expected

What to try:

1. Confirm that `sensor.<name>_stage` exists.
2. Review each stage's minimum and maximum duration.
3. Increase half-life if the session keeps ending before the next stage boundary.

## The Wrong Source Was Chosen

Some devices expose several related entities. The best choice is usually the one with the clearest occupancy semantics, not necessarily the noisiest one.

Use this order when picking a source:

1. explicit occupancy or presence state
2. continuous on/off motion state
3. event-only activity source

If you switch the source entity, use reconfigure rather than only editing options.

## Automations Still Behave Like Raw Motion

Common cause:

- the automation still points at the original sensor instead of the helper entities

What to do:

1. Use `binary_sensor.<name>_occupancy` for presence-style on/off logic.
2. Use `sensor.<name>_duration` for time thresholds.
3. Use `sensor.<name>_stage` for short/medium/long logic.

## Restart Recovery Does Not Match Expectations

If you expect active sessions to survive a Home Assistant restart, enable restore in the integration options.

If restore is already enabled but behavior still looks wrong, verify:

1. the integration loaded cleanly after restart
2. the source entity was available again
3. the restored session still matched the current source state