# Results and Traceability

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

Version 0.1 records measurement data using CSV.

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

# Planned Run Metadata

In addition to measurement data, each test run should record information such
as:

- Run identifier.
- Project.
- DUT identifier.
- Test case.
- Test name.
- Start time.
- End time.
- Duration.
- Software version.

This information should describe the test rather than the individual
measurements.

---

# Instrument Traceability

Where practical, Test in a Box should automatically record instrument identity.

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

In addition to CSV data, Version 0.1 aims to generate a simple Markdown summary
containing:

- Project.
- Test case.
- DUT.
- Start time.
- Finish time.
- Duration.
- Instrument identity.
- Generated result files.

The Markdown summary is intended to provide a human-readable overview of the
run.

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