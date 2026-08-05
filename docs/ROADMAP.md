# Roadmap

## Current alpha capability

The current alpha includes:

- ✅ Local FastAPI web application
- ✅ Blockly test-procedure editor
- ✅ Configure Devices interface
- ✅ Instrument Library
- ✅ Driver-based hardware abstraction
- ✅ Driver-level instrument discovery
- ✅ Mock instruments
- ✅ Sequence save and load
- ✅ DUT-to-position mapping
- ✅ Run, pause, resume, step and stop controls
- ✅ Per-DUT CSV result logging
- ✅ Run metadata
  - host name
  - logged-in user
  - operating system
  - Python version
  - connected instrument identity
- ✅ Engineering examples
- ✅ Bench-tested Aim-TTi PSU driver
- ✅ Bench-tested EA PS 2000 B driver
  - output-enable validation remains outstanding
- ✅ Native Windows Seeit USBB relay support
- ✅ Portable vendor DLL support
- ✅ Portable Windows bootstrap
  - automatic WinPython download
  - SHA-256 verification
  - GitHub API rate-limit avoidance
  - automatic dependency installation
  - project-folder creation
  - vendor-component checks
  - installation verification
  - clear completion summary and optional launch

---

# Version 0.1 — Current milestone

The objective of Version 0.1 is to demonstrate a complete engineering
validation workflow using multiple physical instrument classes.

## Blockly

- ✅ PSU blocks
- ✅ Generic instrument blocks
- ✅ Relay blocks
- ⬜ Electronic-load blocks
- ⬜ Temperature blocks

## Drivers

- ✅ Aim-TTi PSU — bench tested
- 🟡 EA PS 2000 B — bench tested; output-enable validation outstanding
- 🟡 Korad / Tenma PSU — driver implemented; bench validation required
- 🟡 KEL103 electronic load — driver implemented; bench validation required
- 🟡 Native Seeit USBB relay — multi-board validation outstanding
- ⬜ Pico TC-08 integration

## Instrument Library

- ✅ Logical hardware roles
- ✅ Instrument discovery
- ✅ Portable driver loading
- ⬜ Validation status shown consistently for every driver

## Test execution

- ⬜ Parameters defined in one place
- ⬜ Explicit engineering units
- ⬜ Progress percentage
- ⬜ Estimated finish time
- ⬜ Current DUT display
- ⬜ Current test-step display
- ⬜ Markdown run summary
- ⬜ Validated safe-state behaviour across all applicable drivers
- ⬜ Stronger pre-run validation

## Engineering validation

- ⬜ Complete real electrical validation procedure
- ⬜ Complete environmental validation procedure
- ⬜ Demonstrate at least two physical instrument classes operating together

---

# Recommended next work

1. Verify EA PS 2000 B output ON/OFF with no DUT connected.
2. Bench-test the Korad / Tenma PSU driver.
3. Bench-test the KEL103 electronic-load driver.
4. Add electronic-load Blockly blocks.
5. Build the first complete electrical validation procedure using multiple
   physical instruments.
6. Complete multi-board native USBB relay validation.

---

# Version 0.2

## Dedicated Engineering Tools menu

These tools support instrument development, driver validation and hardware
commissioning. They should be available from a dedicated top-level
**Engineering Tools** menu, separate from the normal Blockly test-builder
workflow.

### Instrument development

- ⬜ Protocol Explorer
- ⬜ Serial Terminal
- ⬜ Driver Tester
- ⬜ Instrument Identifier
- ⬜ USB Inspector
- ⬜ SCPI Console
- ⬜ Device Commissioning Wizard

### Driver validation

- ⬜ Driver Validation Wizard
- ⬜ Safe-state verifier
- ⬜ Instrument capability explorer
- ⬜ Communication log viewer

### Engineering utilities

- ⬜ CSV viewer
- ⬜ Run log viewer
- ⬜ Metadata inspector
- ⬜ Configuration validator

Blockly remains the place for using instruments in test procedures.
Engineering Tools are for developing, commissioning and validating instrument
support.

## Blockly and procedure reuse

- ⬜ Reusable engineering blocks
- ⬜ Test templates
- ⬜ Procedure library
- ⬜ Richer pass, warning and fail behaviour

## Reports

- ⬜ Better plots
- ⬜ PDF reports
- ⬜ Engineering report templates
- ⬜ Rich run summaries

## Diagnostics

- ⬜ Improved recovery
- ⬜ Better diagnostics
- ⬜ Stronger configuration validation

---

# Longer term

Possible future work includes:

- database storage
- test versioning
- calibration integration
- barcode support
- operator workflows
- production and end-of-line testing
- multi-rig dashboards
- notifications
- andon lights
- plugin architecture
- REST API
- remote execution
- test scheduling
- lab notebook integration

---

# Driver validation status

| Driver | Status |
|---|---|
| Aim-TTi PSU | ✅ Bench tested |
| EA PS 2000 B | 🟡 Bench tested; output-enable validation outstanding |
| Seeit USBB Native | 🟡 Bench tested; multi-board validation outstanding |
| Korad / Tenma PSU | 🟡 Driver implemented; bench validation required |
| KEL103 Electronic Load | 🟡 Driver implemented; bench validation required |
| Pico TC-08 | ⬜ Planned |

---

# Project priorities

Test in a Box is an engineering validation platform. Priorities are:

1. Reliability
2. Traceability
3. Repeatability
4. Simplicity
5. Extensibility

Features should support real engineering workflows before convenience features.
