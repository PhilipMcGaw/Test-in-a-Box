# Future Ideas

This document records ideas that may be useful in future versions of
**Test in a Box**.

Adding an item here **does not** mean it will be implemented.

The purpose of this document is simply to capture ideas so they are not lost
while keeping Version 0.1 focused.

Items should normally only move from this document into active development once
they directly support the current project goals.

---

# User Interface

## Operator Dashboard

A simplified execution screen intended for technicians rather than test authors.

Potential features:

- Large progress display.
- Estimated finish time.
- Current DUT.
- Current test step.
- Warning and failure counts.
- Overall system status.

---

## Multiple Test Rigs

A dashboard showing multiple running systems.

Example:

```text
Rig 1
Running
Estimated Finish 15:42

Rig 2
Waiting for Operator

Rig 3
Complete
```

---

## Dark Mode

Optional alternative user interface theme.

---

# Hardware

## Additional Instrument Drivers

Potential future drivers include:

- Oscilloscopes.
- Electronic loads.
- CAN interfaces.
- Battery cyclers.
- Environmental chambers.
- Digital multimeters.
- Programmable electronic loads.
- PLC interfaces.

---

## Hardware Discovery

Automatic discovery of supported instruments where practical.

---

## Hardware Capability Profiles

Drivers describe supported capabilities rather than requiring Blockly to know
about individual instruments.

---

# Test Authoring

## Additional Blockly Blocks

Potential blocks include:

- Voltage ramps.
- Temperature sweeps.
- Stability detection.
- Parameter sweeps.
- Retry logic.
- Conditional execution.
- Advanced loops.

---

## Blockly Search

Search toolbox blocks by name.

---

## Reusable Procedures

Support calling one Blockly procedure from another.

---

# Results

## Graphs

Automatic generation of engineering graphs.

Examples:

- Voltage.
- Current.
- Temperature.
- Resistance.

---

## PDF Reports

Generate engineering reports directly from recorded results.

---

## Result Database

Store historical results for later comparison.

---

## Statistical Analysis

Support trend analysis across multiple DUTs.

---

# Evaluation

## Warning Levels

Support:

- Pass
- Warning
- Fail

with configurable actions.

---

## Additional Result Types

Examples:

- Informational measurements.
- Nominal ± tolerance.
- Upper limit.
- Lower limit.
- Acceptable range.

---

## Event Detection

Automatic detection of events such as:

- Relay opening.
- Relay closing.
- Threshold crossings.
- Stability.

---

# Laboratory Integration

## Calibration Information

Associate calibration information with instruments.

---

## Instrument Identity

Expand recorded hardware information beyond `*IDN?`.

---

## Notification Services

Potential integrations:

- Microsoft Teams.
- Email.
- MQTT.

---

## Andon Tower Lights

Support external status indication.

Possible states:

- Ready.
- Running.
- Waiting for Operator.
- Warning.
- Failure.
- Complete.

---

# Production Features

These items are intentionally outside the scope of Version 0.1.

Potential future work includes:

- Barcode readers.
- Operator login.
- Audit trails.
- Recipe management.
- Production workflows.
- End-of-line testing.
- Manufacturing database integration.

---

# Documentation

Potential future improvements:

- Interactive tutorials.
- Video walkthroughs.
- Driver development guide.
- Example validation projects.

---

# General

Potential future improvements:

- Plugin architecture.
- Automatic updates.
- Better diagnostics.
- Improved logging.
- Remote monitoring.
- Multi-user operation.

---

# Rule

Before implementing anything from this document, ask:

> Does this improve an engineer's ability to automate a real validation test?

If the answer is **no**, the idea should normally remain in this document until
Version 1 or later.


## Deliberately Rejected

### Wiring diagrams

The physical wiring diagram remains part of the engineering documentation rather
than Test in a Box.

### Embedded SCPI commands

Blockly should remain hardware-independent.

Instrument-specific communication belongs in drivers.

# Ideas That Were Deliberately Rejected

The following ideas have been discussed during the design of Test in a Box and
were deliberately excluded from the current direction of the project.

This does not necessarily mean they are bad ideas. In many cases they simply
fall outside the scope or philosophy of Test in a Box.

Future contributors should understand the reasoning before proposing these
features again.

## Wiring Diagrams

Test in a Box automates engineering procedures.

Designing the physical wiring remains part of the engineering documentation and
is intentionally outside the scope of the application.

The software assumes the engineer has already designed the physical test rig.

## Instrument-Specific Blockly Blocks

Blockly should remain hardware independent.

A procedure should request engineering actions such as:

- Set Voltage
- Measure Current
- Set Chamber Temperature

rather than manufacturer-specific commands.

Communication with laboratory equipment belongs in drivers.

## Permanent Hardware Configuration

Saved test procedures should not permanently reference COM ports, VISA resource
strings or USB addresses.

Hardware is configured when the test is run.

The procedure records engineering intent rather than the temporary laboratory
configuration.

---

These decisions may be revisited in the future if there is a compelling
engineering reason to do so.

However, new features should not be added simply because they are technically
possible. They should support the overall vision described in `VISION.md`.