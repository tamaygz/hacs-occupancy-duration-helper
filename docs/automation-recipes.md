# Automation Recipes

These examples focus on patterns that fit occupancy sessions better than raw motion automations.

## Turn Lights Off Only When Occupancy Truly Ends

Use the helper's occupancy binary sensor instead of the raw motion sensor.

```yaml
alias: Bathroom lights off when occupancy ends
trigger:
  - platform: state
    entity_id: binary_sensor.bathroom_occupancy
    to: "off"
action:
  - service: light.turn_off
    target:
      entity_id: light.bathroom
```

Why this works:

- short motion gaps do not turn the light off immediately
- the helper closes only after decay and grace are complete

## Trigger A Different Scene For Longer Visits

Use the stage sensor when you care about duration, not just presence.

```yaml
alias: Office focused scene after medium occupancy
trigger:
  - platform: state
    entity_id: sensor.office_stage
    to: medium
action:
  - service: scene.turn_on
    target:
      entity_id: scene.office_focus
```

## Escalate A Long Bathroom Session

```yaml
alias: Alert on long bathroom session
trigger:
  - platform: state
    entity_id: sensor.bathroom_stage
    to: long
action:
  - service: notify.mobile_app_phone
    data:
      message: Bathroom occupancy has been long for this room.
```

## Keep A Fan Running Until The Session Really Ends

```yaml
alias: Bathroom fan follows occupancy helper
trigger:
  - platform: state
    entity_id: binary_sensor.bathroom_occupancy
action:
  - choose:
      - conditions:
          - condition: state
            entity_id: binary_sensor.bathroom_occupancy
            state: "on"
        sequence:
          - service: fan.turn_on
            target:
              entity_id: fan.bathroom
    default:
      - service: fan.turn_off
        target:
          entity_id: fan.bathroom
```

## Use Duration As A Condition

The duration sensor is useful when a rule should depend on how long the room has been occupied.

```yaml
alias: Only speak reminder after 10 minutes
trigger:
  - platform: numeric_state
    entity_id: sensor.laundry_room_duration
    above: 600
condition:
  - condition: state
    entity_id: binary_sensor.laundry_room_occupancy
    state: "on"
action:
  - service: tts.speak
    target:
      entity_id: tts.home_assistant_cloud
    data:
      media_player_entity_id: media_player.laundry_room_speaker
      message: Laundry has been occupied for over ten minutes.
```

## Pattern Guidance

Use the helper entity that matches the decision you are making:

- Use `binary_sensor.<name>_occupancy` for on/off automations.
- Use `sensor.<name>_stage` for behavior that changes by visit length.
- Use `sensor.<name>_duration` for numeric thresholds and dashboards.

Avoid mixing the raw source sensor and the helper in the same automation unless you are deliberately comparing them.