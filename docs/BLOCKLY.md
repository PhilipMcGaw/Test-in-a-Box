# Why Blockly

Blockly was selected because many validation procedures consist of one action
after another, with loops around repeated operations.

A visual form makes it easier to understand the whole procedure, move steps when
the setup changes, review nested loops and keep engineering intent separate from
implementation details.

```text
Set chamber temperature
Wait for chamber and DUT soak
For each starting voltage
    For each DUT
        Apply voltage
        Wait
        Measure
        Log results
Return hardware to a safe state
```

Blocks should not contain `VOLT 12` or `COM7`. They request a capability from a
logical instrument role.

Python remains appropriate for drivers and framework code. Blockly is the
authoring interface for the procedure.
