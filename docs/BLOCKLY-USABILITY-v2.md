# Blockly Usability v2

Numeric engineering parameters now accept Blockly value inputs rather than
only fixed fields.

## Wait

The Wait block accepts:

- literal numbers;
- variables;
- arithmetic expressions;
- other blocks that return a number.

Examples generate:

```python
wait(5)
wait(stabilisation_time)
wait(test_duration / 2)
```

## PSU voltage ramp

The following ramp parameters also accept numbers, variables or maths
expressions:

- start voltage;
- end voltage;
- step magnitude;
- dwell time.

The dwell unit remains selectable as milliseconds or seconds.

## Compatibility

Existing saved Wait and PSU Ramp blocks are migrated when a workspace is
loaded. Their former fixed numeric fields are converted into connected
`math_number` shadow blocks, preserving the saved values.
