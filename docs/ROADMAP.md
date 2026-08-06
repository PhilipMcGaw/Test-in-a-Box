# Roadmap

## Current alpha capability

The current alpha includes:

- a local FastAPI web application;
- a Blockly test-procedure editor;
- the Configure Devices interface;
- mock instruments;
- driver-based hardware abstraction;
- run, pause, resume, step and stop controls;
- sequence save and load;
- DUT-to-position mapping;
- per-DUT CSV result logging;
- engineering examples;
- bench-tested control of a physical Thurlby Thandar QL355P;
- native Windows control of physical Seeit USBB relay hardware;
- driver-level instrument discovery;
- run metadata containing host, user, OS, Python and instrument identity.

## Remaining Version 0.1 work

Version 0.1 is intended to add or complete:

- reusable Instrument Library workflows;
- parameters defined in one place;
- explicit engineering units;
- logical hardware roles;
- progress percentage and estimated finish time;
- current DUT and current test step;
- a validated Markdown run summary;
- validated safe-state behaviour across applicable drivers;
- final validation of multiple identical native USBB relay boards in the main application;
- a complete real electrical or environmental validation procedure;
- at least two different physical instrument classes used together.

## After Version 0.1

Planned improvements include:

- better reports and plots;
- reusable engineering blocks;
- richer pass, warning and fail behaviour;
- stronger pre-run validation;
- improved recovery and diagnostics;
- additional instrument drivers.

## Longer term

Possible longer-term work includes:

- database storage;
- test versioning;
- calibration integration;
- operator workflows;
- barcode support;
- multi-rig dashboards;
- notifications;
- andon lights;
- production and end-of-line features.

# Test in a Box Roadmap

## v0.2.0 – Engineering Workflow

### Instrument Drivers
- [ ] Complete EA PS 2000 B output-on validation
- [ ] Bench test Korad/Tenma PSU driver
- [ ] Bench test KEL103 electronic load driver
- [ ] Pico TC-08 integration

### Blockly
- [x] Relay blocks
- [ ] Electronic load blocks
- [ ] Additional PSU blocks
- [ ] Temperature blocks

### Instrument Discovery
- [ ] Multi-board native USB relay support
- [ ] Improved COM-port discovery
- [ ] Automatic instrument identification

## Future Releases

### Dedicated Engineering Tools Menu

These tools support instrument development, driver validation and hardware
commissioning. They should be available from a dedicated top-level
**Engineering Tools** menu so they remain separate from the normal Blockly
test-builder workflow.

#### Instrument Development
- [ ] Protocol Explorer
- [ ] Serial Terminal
- [ ] Driver Tester
- [ ] Instrument Identifier
- [ ] USB Inspector
- [ ] SCPI Console
- [ ] Device Commissioning Wizard

#### Driver Validation
- [ ] Driver Validation Wizard
- [ ] Safe-state verifier
- [ ] Instrument capability explorer
- [ ] Communication log viewer

#### Engineering Utilities
- [ ] CSV viewer
- [ ] Run log viewer
- [ ] Metadata inspector
- [ ] Configuration validator

#### Intended menu structure

```text
Engineering Tools
──────────────────────────
Protocol Explorer
Serial Terminal
Driver Tester
Instrument Identifier
USB Inspector
SCPI Console
Device Commissioning Wizard
Log Viewer
```

Blockly remains the place for using instruments in test procedures.
Engineering Tools are for developing, commissioning and validating instrument
support.

### Reporting
- [ ] PDF report generation
- [ ] Engineering report templates
- [ ] Calibration information

### Documentation
- [ ] Professional diagram set
- [ ] Annotated screenshots
- [ ] Driver development guide
- [ ] Contributor guide

## Long-term Vision

- Plugin architecture
- REST API
- Remote execution
- Dashboard
- Test scheduling
- Lab notebook integration


## Completed deployment and traceability work

- ✅ Updater V2 with Stable, Development and Rollback actions
- ✅ Automatic bootstrap after update
- ✅ Managed-update state and archive hash
- ✅ Test in a Box version recorded in run reports
- ✅ Configuration, DUT mapping and procedure hashes
- ✅ Machine-readable run manifest


## Completed usability improvements

- ✅ Relay channel naming and Blockly labels

## Completed version information work

- ✅ Shared `/api/version` endpoint
- ✅ Dynamic About page
- ✅ Startup version banner
- ✅ VERSION, BUILD.json and update-state integration
- ✅ Run reports and About page use the same software identity


## Validated reporting and version information

- ✅ Startup version banner
- ✅ Dynamic About page and `/api/version`
- ✅ Run metadata CSV
- ✅ Machine-readable run manifest
- ✅ Human-readable Markdown run summary
- ✅ Configuration, mapping and procedure SHA-256 provenance


## Completed Blockly usability work

- ✅ Wait durations accept literals, variables and expressions
- ✅ PSU setpoints accept literals, variables and expressions
- ✅ PSU ramp parameters accept literals, variables and expressions
- ✅ Existing fixed-field Wait and Ramp blocks migrate on load
