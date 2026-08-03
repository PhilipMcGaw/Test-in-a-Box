# MVP v0.1

## Goal

Version 0.1 proves that a real electrical or environmental validation test can
be configured, authored, run and logged without writing another bespoke Python
program.

## In scope

### Hardware setup

- Configure communication settings in the GUI.
- Connect and disconnect instruments.
- Save reusable hardware definitions in a hardware library.
- Add unknown hardware through a capability and command-map workflow.
- Provide simple manual controls or a mimic panel for commissioning.
- Capture `*IDN?` or the closest available equivalent.

### Test authoring

- Blockly-based visual procedures.
- Variables or test parameters defined in one place.
- Explicit engineering units.
- Loops, waits, simple set/read operations, logging and assertions.
- Logical instrument roles rather than fixed COM ports or model names.

### Execution

- Run, pause, step and stop.
- Progress percentage and progress bar.
- Estimated finish time.
- Current DUT and current step.
- Safe output shutdown when a run is stopped or fails.

### Results

- CSV output.
- Markdown text summary.
- Per-DUT files where appropriate.
- Run metadata including instrument identity.
- Informational measurements that do not require pass/fail limits.

### Development

- Mock support for each driver or capability used by examples.
- A no-hardware demonstration.

## Out of scope

- PDF reports and result databases.
- Standards, requirements and calibration management.
- Approval workflows and electronic signatures.
- Production operator, barcode or MES integration.
- Andon tower lights.
- Advanced statistics and event detection.
- Automatic recovery after a PC restart.
- Wiring-diagram creation.
- A plugin marketplace.

## Completion criterion

Version 0.1 is complete when a real validation test can be configured, built in
Blockly, run against one or more DUTs, monitored in the GUI, logged to CSV,
summarised in Markdown, and repeated without rewriting the framework.
