# Engineering Results

## Introduction

The purpose of Test in a Box is not simply to automate laboratory equipment.

Its purpose is to produce engineering results that are:

- repeatable;
- traceable;
- understandable;
- reusable.

A successful test should leave sufficient information for another engineer to
understand:

- what was tested;
- how it was tested;
- which equipment was used;
- what measurements were recorded;
- how the results were obtained.

---

# Design Principles

## Preserve Engineering Evidence

Results should provide sufficient information to understand the engineering
behaviour of the DUT.

The recorded data should remain useful even years after the original test was
performed.

---

## Preserve Intent

The important information is:

- the engineering procedure;
- the measured values;
- the engineering units;
- the instrument identity.

Temporary laboratory details such as COM port assignments should not become
part of the permanent engineering record.

---

## Engineering Units

Every recorded measurement should include an explicit engineering unit.

Examples:

- V
- A
- °C
- mΩ
- s

Units should never rely upon external documentation or assumptions.

---

# Current Output

The current alpha records measurement and event data using CSV.

Each measurement currently contains information including:

```text
timestamp
device_id
position
channel
value
unit
event_type
```

CSV remains the primary machine-readable output format.

---

# Current Run Metadata

In addition to measurement data, the current alpha creates a separate
`run_<run_id>_metadata.csv` file containing:

- Run identifier and UTC start time.
- Computer hostname.
- Logged-in operating-system user.
- Operating-system name, release, version, build and machine architecture.
- Python version.
- Instrument identity returned by each connected driver, where available.

The run manifest and Markdown summary record the run start and finish times,
duration, final status, software identity, configuration, DUT mapping,
generated procedure and configured instruments. Project and test-case fields
remain areas for further result-summary work.

This information should describe the test rather than the individual
measurements.

---

# Instrument Traceability

Where practical, Test in a Box automatically records instrument identity at
the start of each run.

For SCPI instruments this normally includes:

```text
*IDN?
```

or the closest equivalent provided by the driver.

Where available, the following information should be recorded:

- Manufacturer.
- Model.
- Serial number.
- Firmware version.
- Driver.
- Full identity string.

This information improves traceability while remaining independent of the test
procedure itself.

---

# Informational Measurements

Many engineering tests simply collect information.

Examples include:

- Contact resistance.
- Pickup voltage.
- Holding voltage.
- Temperature rise.

These measurements may not have acceptance criteria.

This is a valid engineering workflow.

---

# Evaluated Measurements

Other tests compare recorded measurements against engineering requirements.

Future versions may support:

- Pass
- Warning
- Fail

using configurable engineering limits.

Version 0.1 only requires sufficient information to support this in the future.

---

# One File Per DUT

Where practical, each DUT should have its own result file.

This makes it easier to:

- investigate failures;
- compare samples;
- archive results;
- rerun analysis.

---

# Markdown Summary

In addition to CSV data, the current alpha generates a simple Markdown summary
containing:

- Run identifier, status, start time, finish time and duration.
- Test in a Box and updater identity.
- Configuration, DUT mapping and procedure SHA-256 hashes.
- Configured instruments and captured identity, where available.
- Manifest and run-metadata file names.

The Markdown summary provides a human-readable overview of the run. The
reporting workflow still requires validation and acceptance as part of the
Version 0.1 release milestone.

---

# Future Development

Future versions may include:

- Graph generation.
- PDF reports.
- Statistical analysis.
- Historical comparison.
- Result databases.

These items are intentionally outside the Version 0.1 milestone.

---

# Guiding Principle

The objective is not simply to automate the test.

The objective is to preserve sufficient engineering evidence that another
engineer can understand the results without needing access to the original test
bench.

---

# Run Manifest and Software Provenance

Each run now creates:

```text
run_<run_id>_manifest.json
run_<run_id>_summary.md
```

The manifest records:

- Test in a Box version;
- updater channel, ref and commit identity;
- downloaded source-archive SHA-256, when managed by Updater V2;
- Python version;
- complete configuration snapshot and SHA-256;
- DUT mapping snapshot and SHA-256;
- generated procedure source and SHA-256;
- connected instrument identities;
- start time, finish time and final run status.

The Markdown summary provides a concise human-readable view of the same
provenance.

This allows a result to identify the exact software, configuration, mapping,
procedure and instrument setup used to produce it.
