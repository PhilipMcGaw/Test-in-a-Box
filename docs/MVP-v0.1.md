# MVP v0.1

## Purpose

Version 0.1 exists to prove that Test in a Box can automate a real electrical
or environmental validation test without requiring bespoke control software.

The goal of Version 0.1 is not to provide every planned feature.

The goal is to prove the overall architecture.

---

# Success Criteria

Version 0.1 is considered successful when an engineer can:

1. Configure the available laboratory hardware.
2. Create a test procedure using Blockly.
3. Execute that procedure.
4. Monitor progress while the test is running.
5. Record useful engineering data.
6. Repeat the same procedure on multiple DUTs.

without writing a custom Python application.

---

# Included in Version 0.1

## Hardware

- Device configuration through the GUI.
- Saved hardware definitions.
- Generic SCPI support.
- Native drivers for supported hardware.
- Mock drivers for development.
- Manual controls for commissioning.
- Instrument identification (`*IDN?` where available).

---

## Test Authoring

- Blockly editor.
- Variables / test parameters.
- Engineering units.
- Loops.
- Waits.
- Hardware read/write blocks.
- Logging.
- Assertions.

---

## Execution

- Run.
- Pause.
- Resume.
- Step.
- Stop.
- Current test step.
- Current DUT.
- Progress indicator.
- Estimated finish time.

---

## Results

- CSV logging.
- One result file per DUT.
- Run metadata.
- Instrument identity.
- Markdown summary.

---

# Explicitly Out of Scope

The following are deliberately **not** part of Version 0.1.

## Reporting

- PDF reports.
- Graph generation.
- Statistical analysis.

---

## Management

- Standards management.
- Requirements management.
- Calibration tracking.
- Approval workflows.
- Electronic signatures.

---

## Production

- Barcode readers.
- Operator login.
- MES integration.
- End-of-line testing.
- Multi-rig supervision.

---

## Notifications

- Teams.
- Email.
- MQTT.
- Tower lights.

---

# Current Focus

The immediate objective is to automate real engineering validation work.

The first milestone is successfully replacing manual or bespoke software for a
complete electrical or environmental validation test.

Future work should only be considered once this milestone has been achieved.

---

# Design Principles

Version 0.1 follows the principles defined in:

- VISION.md
- ENGINEERING-PHILOSOPHY.md

In particular:

- Tests express engineering intent.
- Drivers implement hardware communication.
- Parameters use explicit engineering units.
- Hardware is configured separately from the test procedure.
- The software supports both informational and evaluated measurements.

---

# Release Checklist

Before Version 0.1 can be released, the following must be demonstrated:

- [ ] Mock demonstration completed.
- [ ] PSU-only demonstration completed.
- [ ] At least two different instrument classes successfully used.
- [ ] At least one complete real engineering validation test automated.
- [ ] Hardware configuration through the GUI.
- [ ] Blockly-based test authoring.
- [ ] Test execution controls (Run, Pause, Resume, Step and Stop).
- [ ] Progress display with estimated finish time.
- [ ] CSV result logging.
- [ ] Markdown run summary.
- [ ] Documentation reviewed and updated.

Once all items have been completed, Version 0.1 may be tagged and released.