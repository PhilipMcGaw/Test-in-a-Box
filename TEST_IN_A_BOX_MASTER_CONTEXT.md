# Test in a Box — Master Context

> **Role of this file:** Compact, persistent project context for humans and AI assistants working on Test in a Box (TIAB).
>
> **Verified against:** GitHub repository ZIP supplied by the user on 7 August 2026.
>
> **Repository version:** `0.1.0-alpha` (unreleased).
>
> **Authority rule:** Current code + physical bench evidence > changelog/current roadmap > this file > older documentation/chat recollection.
>
> **Maintenance rule:** Update this file whenever a significant architecture decision, physical validation result, release milestone, safety behaviour, deployment mechanism, or roadmap priority changes.

---

## 1. One-paragraph project definition

**Test in a Box (TIAB)** is an engineering validation platform for rapidly automating one-off and evolving electrical and environmental laboratory tests while retaining enough structure for those tests to be repeatable, traceable, maintainable and understandable.

The initial target is R&D/engineering validation rather than production test. Engineers create procedures visually using Blockly; TIAB executes them through hardware-abstraction drivers, maps results to DUTs, and preserves measurement, instrument, configuration, procedure and software provenance.

The project is intended to reduce bespoke test-control applications without trying to replace engineering judgement.

---

## 2. The problem TIAB solves

Engineering validation benches commonly become combinations of:

- one-off Python/scripts;
- instrument-specific control code;
- spreadsheets;
- manual procedures;
- ad-hoc data files;
- undocumented setup knowledge.

These can work, but become difficult to reproduce, maintain, extend and hand to another engineer.

TIAB provides a common framework for:

- repeatable automated procedures;
- multiple DUTs using the same procedure;
- different laboratory instruments behind a common abstraction;
- measurement and event capture;
- pass/fail assertions where appropriate;
- traceability of the software, procedure, configuration and instruments used;
- visual test development without requiring a custom Python application for every test.

---

## 3. Project priorities

The recorded project priority order is:

1. **Reliability**
2. **Traceability**
3. **Repeatability**
4. **Simplicity**
5. **Extensibility**

Practical implications:

- Treat “implemented”, “simulator tested” and “physically bench tested” as different states.
- Record observed behaviour rather than assumptions.
- Preserve software/configuration/procedure/instrument identity for runs.
- Keep deployment reproducible.
- Prefer clear engineering workflows over unnecessary abstraction.
- Blockly is for **using instruments in tests**; Engineering Tools are for **developing, commissioning and validating instrument support**.

---

## 4. What TIAB is — and is not

### TIAB is

- an engineering validation platform;
- a laboratory test automation framework;
- a visual procedure builder backed by Python execution;
- a hardware-abstraction framework;
- a repeatability and traceability tool;
- initially focused on electrical and environmental validation.

### For v0.1, TIAB is deliberately not

- a replacement for engineering judgement;
- a requirements-management tool;
- a wiring-diagram editor;
- an EMC compliance package;
- a calibration-management system;
- an MES;
- a production-line platform;
- a complete NI TestStand replacement;
- a general-purpose visual programming language.

Do not expand v0.1 merely to satisfy one of these adjacent use cases.

---

## 5. v0.1 objective

Version 0.1 exists to prove the **overall architecture** by automating a complete real electrical or environmental validation test **without bespoke control software**.

Success means an engineer can:

1. configure available laboratory hardware;
2. create a test procedure in Blockly;
3. execute it;
4. monitor execution;
5. record useful engineering data;
6. repeat it across multiple DUTs;

without writing a custom Python application.

The immediate milestone is not feature completeness. It is proving a useful end-to-end engineering validation workflow.

---

## 6. Current repository status

Repository `VERSION`:

```text
0.1.0-alpha
```

The changelog describes this release as **unreleased**.

The current codebase contains substantially more functionality than the first reconstructed master-context draft implied, including:

- Instrument Library UI/workflow code;
- machine-readable run manifests;
- Markdown run summaries;
- software/configuration/mapping/procedure provenance hashes;
- portable Windows bootstrap;
- Updater V2;
- shared version/build identity;
- relay Blockly blocks;
- serial COM-port discovery;
- LAB-DCH support and validation sequences;
- Protocol Explorer UI (implementation exists even though roadmap engineering-tool completion still needs reconciliation).

When documentation disagrees, inspect the implementation and recent changelog before assuming an older “planned” statement is still true.

---

## 7. High-level architecture

Conceptually:

```text
Engineering Test Procedure
          |
          v
     Blockly UI
          |
          v
 Generated Python
          |
          v
     Test Runner
      /       \
     v         v
 Drivers    Results /
     |       Provenance
     v
Laboratory Equipment
```

The fundamental separation is:

> The procedure describes **what engineering action should occur**.  
> Drivers determine **how the connected instrument performs it**.

---

## 8. Repository structure

Important current areas include:

```text
tiab/
  runtime.py

  drivers/
    base.py
    registry.py
    catalog.py
    mock.py
    scpi_generic.py
    aimtti_psu.py

    serial/
      ea_ps2000b.py
      kel103_load.py
      korad_tenma_psu.py
      labdch_psu.py
      seeit_relay.py

    usb/
      seeit_relay.py

    pico_adc.py
    pico_tc08.py

  run/
    control.py
    csv_logger.py
    instrument.py
    mapping.py
    provenance.py
    runner.py

  example_scripts/
    demo_test.py

webapp/
  server.py
  config.json
  sequences/
  static/
    index.html
    devices.html
    app.js
    devices.js
    custom_blocks.js
    generators.js
    protocol-explorer.html
    protocol-explorer.js
    supported-devices.html
    about.html
    about.js

bootstrap/
updater/
support/
docs/
tools/
```

Do not assume this list remains complete after future updates.

---

## 9. Driver architecture

Every supported instrument is represented through the driver layer.

Important abstractions include:

- `Driver`
- `CapabilityDescriptor`
- `Position`
- `PositionKind`
- `LogEvent`
- driver registry/factory
- driver-owned discovery/identification where applicable

Typical operations include:

- connect;
- close;
- capabilities;
- read;
- write;
- query;
- identify;
- discover;
- safe state where applicable.

Blockly-generated procedures should not need to understand instrument communication protocols.

### Position model

A position represents an addressable point such as:

- PSU channel;
- relay channel;
- thermocouple channel;
- ADC input.

Position kinds distinguish analog/digital input/output.

---

## 10. Hardware independence and logical roles

The intended architecture is that test procedures should **not** permanently embed:

- COM-port numbers;
- VISA resource strings;
- USB addresses;
- manufacturer-specific commands.

Procedures should refer to engineering/logical roles such as:

- Power Supply;
- Environmental Chamber;
- Relay Controller;
- Data Acquisition;
- Temperature Logger.

Physical hardware is configured separately.

The Instrument Library is intended to connect reusable instrument definitions with the logical hardware required by a procedure.

**Important:** some logical-role/Instrument-Library workflow is still listed as Version 0.1 work, so check the current UI/implementation before assuming the full desired abstraction is complete.

---

## 11. Blockly and test authoring

Blockly is the primary test-procedure authoring environment.

The design intent is that an engineer changes the **test procedure**, not instrument-control source code, for routine test changes.

Current/recovered capabilities include combinations of:

- PSU blocks;
- relay blocks;
- variables;
- waits;
- loops;
- hardware reads/writes;
- logging;
- assertions;
- operator prompts;
- sequence save/load.

Additional block families on the roadmap include:

- electronic loads;
- additional PSU functions;
- temperature.

Blockly must remain focused on engineering actions rather than raw serial/SCPI protocol development.

---

## 12. Generated-code execution and run control

Blockly produces Python that executes against the TIAB runner rather than directly touching hardware.

The execution source is instrumented with checkpoints before generated statements. This enables:

- Run;
- Pause;
- Resume;
- Step;
- Stop.

Loop iteration reporting is also injected into generated execution.

This checkpoint/instrumentation layer is important: do not duplicate pause/stop handling independently in every Blockly block unless the architecture explicitly changes.

Progress reporting exists in the runner/instrumentation architecture, but the v0.1 release checklist still identifies the complete progress display / estimated finish-time experience as unfinished.

---

## 13. DUT mapping

TIAB supports mapping instrument positions/channels to DUT identities.

This is fundamental to multi-DUT testing.

Preserve the relationship between:

- run;
- DUT;
- physical test position;
- instrument;
- instrument channel/position;
- measurement/event.

Operator-entered metadata such as serial numbers can be associated with a DUT.

Do not simplify logging in a way that makes later DUT attribution ambiguous.

---

## 14. Results and provenance

CSV remains the primary measurement/event output.

Typical event fields include:

```text
timestamp
device_id
position
channel
value
unit
event_type
```

TIAB also now implements run-level provenance.

A run can create:

```text
run_<run_id>_metadata.csv
run_<run_id>_manifest.json
run_<run_id>_summary.md
```

The manifest records information including:

- run ID/status/times/duration;
- TIAB software identity;
- updater channel/ref/commit where available;
- downloaded archive SHA-256 where managed by Updater V2;
- Python version;
- complete configuration snapshot and SHA-256;
- DUT mapping snapshot and SHA-256;
- generated procedure source and SHA-256;
- configured instruments;
- captured instrument identities.

The Markdown summary is the human-readable view of the same provenance.

### Important documentation discrepancy

Some older docs still describe Markdown summaries and structured provenance as future Version 0.1 work. The **current source code and changelog show that manifest and Markdown-summary generation are implemented**.

What remains is validation/completion of the desired end-to-end v0.1 reporting workflow, not creation of the basic report mechanism from scratch.

---

## 15. Instrument identity

Where practical, TIAB records instrument identity automatically.

For SCPI equipment this is commonly `*IDN?`; other drivers can use the appropriate equivalent.

Desired traceability includes, where available:

- manufacturer;
- model;
- serial number;
- firmware;
- driver;
- full identity string.

Instrument identity belongs in run provenance, not hard-coded into a test procedure.

---

## 16. Safety architecture

Automated test software can energise DUTs, enable PSU outputs, switch relays and apply loads. Safe-state handling is therefore architectural.

The base/driver ecosystem includes `safe_state()` support, and the web server has a central mechanism that attempts to return connected devices to their safe state.

Current applicable drivers with safe-state implementations include several PSU/load/relay drivers.

Principles:

1. Stop/error/shutdown paths must consider the **physical** state, not only software state.
2. A failed safe-state command must be reported; do not silently claim the bench is safe.
3. Safe-state semantics are device/application dependent.
4. Relay “open” is not universally synonymous with “safe”.
5. Physical validation is required.
6. Safe-state behaviour across applicable drivers remains a v0.1 validation item.

---

## 17. Deployment philosophy

TIAB is local-first.

The application is a local FastAPI web application, normally served on:

```text
http://127.0.0.1:8765
```

The web application and Blockly UI are cross-platform in principle.

Core testing should not unnecessarily require:

- cloud infrastructure;
- internet access during normal execution;
- administrator rights.

### Windows

Windows is a major target because engineering PCs may be locked down.

The repository now includes:

- portable dependency/bootstrap scripts;
- automatic WinPython setup;
- startup scripts;
- updater tooling.

No-admin operation remains an important design constraint.

### Cross-platform

Current documentation describes:

- FastAPI/Blockly/mock hardware as supported on Windows/Linux/macOS;
- generic SCPI via PyVISA/PyVISA-py as cross-platform;
- many serial drivers as expected to be portable but not necessarily bench-tested on every OS;
- vendor-native Seeit USBB support as Windows-only.

Do not describe “expected” cross-platform hardware support as bench-tested.

---

## 18. Updating and build identity

The repository contains an Updater V2 and shared build/version metadata.

Recovered completed updater/version work includes:

- Stable / Development / Rollback actions;
- automatic bootstrap after update;
- managed-update state;
- archive hash;
- shared `/api/version` endpoint;
- dynamic About page;
- startup version banner;
- `VERSION` / `BUILD.json` integration;
- consistent software identity in run reports.

Traceability of the exact software build used for a run is an intentional feature, not incidental metadata.

---

## 19. Hardware status — use these labels carefully

Use the following vocabulary:

- **Implemented** — code exists.
- **Simulator tested** — exercised against simulation/protocol model.
- **Bench tested** — confirmed on physical hardware.
- **Expected** — architecture/transport suggests it should work, but it has not been bench tested.
- **Not supported** — known platform/vendor limitation.

Never collapse these categories.

### Thurlby Thandar / Aim-TTi QL355P

**Bench tested on physical hardware** according to current roadmap/platform documentation.

Blockly control of a physical QL355P has been demonstrated.

### Seeit USBB native USB relay

**Bench tested on Windows.**

Implementation uses the vendor `usb_relay_device.dll` through `ctypes`.

Important constraints:

- Windows only;
- Python/DLL architecture must match;
- DLL can live under `vendor/seeit/`;
- DLL is not currently distributed while redistribution permission is being confirmed;
- one/two/four/eight-channel family support exists in the native driver;
- enumeration/discovery exists.

#### Multiple identical boards

Some boards can expose identical factory serial numbers and `NOTHING` as DLL device path.

TIAB can select the live enumeration node using selectors such as:

```text
index:1
index:2
```

This is useful for current bench work but **not a stable permanent identity mechanism** because enumeration order can change with USB topology/restarts.

Final multi-board validation remains outstanding.

### Seeit serial relay

A serial-driver path exists separately from the native USB implementation.

Do not confuse the two.

### EA PS 2000 B

Driver exists.

**Output-enable validation remains outstanding** according to the current changelog/roadmap.

Do not claim full physical output-control validation until confirmed.

### Korad/Tenma PSU

Driver exists.

Current bench validation is required/outstanding.

### KEL103 electronic load

Driver exists.

Current bench validation is required/outstanding.

### Pico TC-08 / ADC-20/24

Driver implementations exist and depend on PicoSDK.

Physical/integration status must be checked before making a strong support claim.

### LAB-DCH 30-665

A serial RS232 driver has been implemented from the supplied protocol reference.

Current repository includes:

- capability-based PSU Blockly compatibility;
- output-off safe state;
- driver-owned COM-port discovery;
- `*IDN?` with `ID` fallback;
- smoke-test workspace;
- no-load driver-validation workspace;
- voltage sweep and repeated output-cycle regression checks;
- output-enable polling/verification logic;
- discharge polling;
- standby dwell and retry logic.

**Physical hardware bench validation / rerun items remain explicitly open in the roadmap.**

Do not treat the existence of detailed validation logic as proof that the latest version has passed the physical bench.

---

## 20. Instrument discovery

Discovery is driver-owned where practical.

Completed/recovered work includes:

- Windows COM-port drop-down;
- USB/serial description metadata;
- driver-specific identity filtering;
- driver-selected `*IDN?`, `ID` or equivalent;
- blocking serial probing while a test run is active;
- LAB-DCH COM-port discovery;
- friendly catalogue-label default device names;
- separation of internal driver type from visible device name.

Still-planned work includes:

- stronger multi-board native USB relay handling;
- improved COM discovery;
- more automatic instrument identification.

---

## 21. Instrument Library

The Instrument Library is intended to make hardware definitions reusable and keep procedures independent of bench-specific addresses.

A procedure should ask for a capability/logical role; configuration should decide which physical instrument satisfies it.

When extending this area:

- keep connection details out of procedures;
- preserve friendly visible names separately from internal driver types;
- allow reusable definitions;
- retain instrument identity/provenance;
- do not let the library become a requirements or calibration-management system in v0.1.

---

## 22. Engineering Tools boundary

Engineering Tools are intentionally separate from the normal Blockly workflow.

Envisioned tools include:

- Protocol Explorer;
- Serial Terminal;
- Driver Tester;
- Instrument Identifier;
- USB Inspector;
- SCPI Console;
- Device Commissioning Wizard;
- Driver Validation Wizard;
- safe-state verifier;
- capability explorer;
- communication log viewer;
- CSV/run log viewer;
- metadata inspector;
- configuration validator.

A Protocol Explorer UI is present in the current repository, but roadmap completion state should be reconciled before describing the full Engineering Tools suite as delivered.

Guiding boundary:

> **Blockly:** use instruments to perform engineering tests.  
> **Engineering Tools:** develop, debug, identify, commission and validate instrument support.

---

## 23. Current v0.1 release checklist

The repository's MVP document currently records:

- [ ] Mock demonstration completed
- [x] PSU-only demonstration completed
- [ ] At least two different instrument classes successfully used
- [ ] At least one complete real engineering validation test automated
- [x] Hardware configuration through GUI
- [x] Blockly-based test authoring
- [x] Run/Pause/Resume/Step/Stop
- [ ] Progress display with estimated finish time
- [x] CSV result logging
- [ ] Markdown run summary
- [ ] Documentation reviewed and updated

### Reconciliation note

The source code/changelog show Markdown summary generation is implemented, while the MVP checklist still leaves it unchecked.

Therefore interpret the unchecked item as **not yet fully validated/accepted for the v0.1 milestone**, rather than “no Markdown summary code exists.”

This type of discrepancy should be cleaned up before release.

---

## 24. Remaining v0.1 themes

Current roadmap identifies these remaining themes:

- reusable Instrument Library workflow completion;
- central parameters;
- explicit engineering units;
- logical hardware roles;
- progress percentage / ETA;
- current DUT / current test step presentation;
- validated Markdown run summary;
- validated safe-state behaviour;
- final multiple-identical-USBB-board validation;
- complete real electrical/environmental validation procedure;
- at least two different physical instrument classes together.

These are higher priority than speculative long-term features.

---

## 25. v0.2 / post-v0.1 direction

Nearer-term engineering workflow work includes:

- EA PS 2000 B output-on validation;
- Korad/Tenma bench test;
- KEL103 bench test;
- Pico TC-08 integration;
- electronic-load blocks;
- more PSU blocks;
- temperature blocks;
- discovery improvements.

After v0.1, desired improvements include:

- better reports/plots;
- reusable engineering blocks;
- richer pass/warning/fail behaviour;
- stronger pre-run validation;
- improved recovery/diagnostics;
- more drivers.

---

## 26. Long-term ideas — not current scope

Possible future capabilities include:

- database storage;
- test versioning;
- calibration integration;
- operator workflows;
- barcode support;
- multi-rig dashboards;
- notifications;
- andon/tower lights;
- production/end-of-line features;
- plugin architecture;
- REST API;
- remote execution;
- dashboards;
- scheduling;
- lab-notebook integration;
- PDF reports;
- statistical analysis.

Do not allow these to distract from proving v0.1 on a complete real validation test.

---

## 27. Engineering-results philosophy

The objective is not merely to make instruments move.

A useful run should leave enough evidence that another engineer can later understand:

- what was tested;
- how it was tested;
- which procedure was used;
- which configuration/mapping was used;
- which equipment was used;
- what software produced the result;
- what measurements/events occurred.

Engineering units should be explicit.

Temporary connection details such as a COM-port number should not become the conceptual identity of an instrument in the permanent engineering record.

Both are valid:

- **informational measurements** with no acceptance criterion;
- **evaluated measurements** with assertions/limits.

Do not force every engineering measurement into pass/fail semantics.

---

## 28. Guardrails for future design decisions

Unless explicitly changed by a recorded decision:

1. **Reliability before cleverness.**
2. **Traceability is a core feature.**
3. **Local-first core operation.**
4. **No-admin-friendly Windows deployment.**
5. **Hardware-specific communication stays behind drivers.**
6. **Procedures express engineering intent.**
7. **Bench configuration is separate from procedure intent.**
8. **Explicit engineering units.**
9. **Mock-first where practical.**
10. **Simulator success is not bench validation.**
11. **Multi-DUT attribution must remain unambiguous.**
12. **Safe-state behaviour must be physically considered.**
13. **Do not silently swallow safety failures.**
14. **Avoid premature cloud/database/plugin infrastructure.**
15. **Engineering Tools must not clutter the normal test-authoring workflow.**
16. **Do not turn TIAB into a general-purpose visual language.**
17. **Prioritise the complete real validation milestone over feature accumulation.**

---

## 29. Terminology

**TIAB** — Test in a Box.

**DUT** — Device Under Test.

**EUT** — Equipment Under Test.

**Driver** — device-specific implementation behind the common TIAB hardware abstraction.

**Capability** — an engineering function exposed by a driver.

**Position** — addressable instrument point/channel.

**Logical hardware role** — procedure-level requirement such as “Power Supply”, independent of physical connection details.

**Instrument Library** — reusable hardware/instrument definitions that map engineering requirements to physical equipment.

**Sequence** — saved Blockly test procedure/workspace.

**Runner** — execution context used by generated procedures.

**Safe state** — deliberately commanded physical state for shutdown/stop/error handling; meaning depends on the instrument and wiring.

**Provenance** — evidence identifying the software, configuration, mapping, procedure and instruments used for a run.

**Bench tested** — confirmed on physical hardware, not merely implemented or simulated.

---

## 30. Instructions for ChatGPT / AI assistants

When working on Test in a Box:

1. Read this file first.
2. If exact current behaviour matters, inspect the relevant current source file.
3. Treat the supplied/current repository as stronger evidence than an old chat.
4. Distinguish implemented / simulator-tested / bench-tested / expected / unsupported.
5. Never invent a hardware validation result.
6. Call out documentation/code inconsistencies rather than choosing silently.
7. Preserve the project priorities and v0.1 scope.
8. Keep hardware communication in drivers.
9. Keep engineering intent in procedures/Blockly.
10. Consider safe-state consequences for execution/control changes.
11. Consider traceability consequences for result/configuration changes.
12. Prefer solutions compatible with local/no-admin engineering PCs.
13. Do not assume Windows-only native drivers are cross-platform.
14. Do not treat an index-selected USB relay as permanently identified hardware.
15. Update this context when a material decision or validation result is confirmed.

For code changes, ask:

- Which architectural layer owns this?
- Does it affect physical safety?
- Does it affect result/provenance traceability?
- Can it be mock-tested?
- Does it introduce unnecessary deployment/admin requirements?
- Is it v0.1-critical or future scope?

---

## 31. Known documentation inconsistencies to watch

The repository contains documents written at different development points.

Known examples:

- Markdown run summary is described as future/uncompleted in some MVP/roadmap text, but implementation exists in `tiab/run/provenance.py` and the changelog lists it as added.
- Protocol Explorer is present in the web UI source while the roadmap still lists Engineering Tools work as future/incomplete.
- Some older driver catalogue/support statements may lag later physical bench results.
- The roadmap contains both “remaining v0.1” and later completed-work appendices, so check recent code/changelog rather than reading only the first section.

Before release, reconcile these documents so support/status claims are consistent.

---

## 32. Historical recovery note

This master context was originally created because the long-running Test in a Box ChatGPT conversation stopped opening.

The first reconstruction used Library copies of README, ROADMAP and source files.

On **7 August 2026**, the user supplied a fresh GitHub repository ZIP. This version of the master context was rebuilt against that repository and should supersede the earlier reconstruction.

The inaccessible chat may still contain rationale or rejected ideas that were never committed to the repository. Treat such missing rationale as **unknown**, not as permission to invent it.

Potential chat-only gaps include:

- reasons behind specific UI choices;
- rejected architecture alternatives;
- detailed bench observations;
- informal prioritisation decisions;
- Fortescue-specific deployment/use-case considerations not committed to public project files.

If any of these are recovered or remembered, add them explicitly with their status/source.

---

## 33. Master-context update log

### 2026-08-07 — repository reconciliation

- Rebuilt master context against user-supplied GitHub repository ZIP.
- Confirmed repository version `0.1.0-alpha`, unreleased.
- Added current driver/file structure.
- Added Updater V2/bootstrap/version provenance.
- Corrected run-report status: manifest and Markdown summary generation are implemented.
- Added LAB-DCH implementation/validation status.
- Added serial discovery/naming work.
- Added current safety architecture and `safe_state()` handling.
- Added current v0.1 checklist and documented status inconsistencies.
- Clarified project priorities, scope boundaries and Engineering Tools separation.
- Retained inaccessible historical chat as a known rationale gap.

---

## 34. Quick start for a new conversation

If this file is supplied to a fresh AI conversation, the working assumption should be:

> We are developing **Test in a Box v0.1.0-alpha**, an engineering validation platform whose immediate goal is to prove an end-to-end real electrical/environmental validation workflow using Blockly-authored procedures and reusable hardware drivers. Reliability, traceability and repeatability outrank feature breadth. Current code already includes the FastAPI/Blockly application, device configuration, Instrument Library work, execution controls, per-DUT CSV results, software/config/procedure provenance, run manifest/Markdown summary, discovery, updater/bootstrap infrastructure, physical QL355P control and physical Windows Seeit USBB relay control. The major remaining milestone is a fully validated real multi-instrument engineering test, together with progress/ETA, workflow completion, safe-state validation and outstanding driver bench validation. Do not confuse implemented drivers with physically validated hardware.
