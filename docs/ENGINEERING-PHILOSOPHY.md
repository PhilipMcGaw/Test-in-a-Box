# Engineering Philosophy

## Introduction

Test in a Box is not simply a collection of hardware drivers or a visual
programming environment.

It is an engineering tool intended to reduce the amount of bespoke software
required to automate electrical and environmental validation tests.

Every design decision should support that goal.

---

# Engineering Before Software

The software should support the engineer.

It should not require the engineer to think like a software developer.

A typical engineering workflow is:

1. Read the specification.
2. Clarify the objectives.
3. Select suitable instrumentation.
4. Design the physical test setup.
5. Write the engineering procedure.
6. Automate the procedure.

Test in a Box begins at the final step.

---

# Engineering Intent

Test procedures should describe **what** the engineer wants to happen.

They should not describe how an individual instrument performs that action.

Good:

```text
Set chamber temperature to 40 °C

Apply 12 V to the coil

Measure current

Wait 5 seconds
```

Not:

```text
Send SCPI command

Open COM7

Write VOLT 12

Read serial response
```

Hardware communication belongs in the driver.

Engineering intent belongs in the procedure.

---

# Hardware Independence

A test procedure should not depend on:

- COM port numbers;
- VISA resource strings;
- USB addresses;
- manufacturer-specific commands.

Instead it should depend on logical engineering concepts such as:

- Power Supply
- Environmental Chamber
- Relay Controller
- Data Acquisition
- Temperature Logger

Changing laboratory equipment should not require the test procedure to be
rewritten.

---

# Parameters

Values that are likely to change should be defined once.

Examples include:

- Chamber temperature.
- Soak time.
- Supply voltage.
- Current limit.
- Ramp rate.

The procedure should reference the parameter rather than repeating literal
values throughout the sequence.

---

# Engineering Units

Every parameter and measurement should have an explicit engineering unit.

Examples include:

- 40 °C
- 3600 s
- 9 V
- 0.2 V/s
- 0.373 mΩ

Units improve readability and reduce the likelihood of engineering mistakes.

---

# Characterisation and Validation

Not every engineering test has pass/fail criteria.

Many R&D activities simply characterise the behaviour of a DUT.

Examples include:

- Contact resistance.
- Holding voltage.
- Pickup voltage.
- Temperature rise.
- Current consumption.

The absence of acceptance criteria is a valid engineering workflow.

Test in a Box should support both:

- informational measurements;
- evaluated measurements.

Neither should be treated as a second-class feature.

---

# Mock-First Development

Where practical, every capability used by demonstrations should have a mock
implementation.

Mock drivers allow:

- development without laboratory hardware;
- automated testing;
- demonstration of the framework;
- contribution by engineers without access to specialist equipment.

---

# Honest Driver Status

Drivers should always state their current validation status.

Suitable descriptions include:

- Demo
- Simulated
- Bench Tested
- Production Proven

The documentation should never imply that hardware has been validated when it
has not.

---

# Reproducibility

The objective is to preserve the engineering procedure rather than the physical
bench configuration.

A saved test should retain:

- procedure;
- parameters;
- engineering units;
- logical hardware roles;
- DUT information.

It should not permanently depend upon:

- COM port assignments;
- USB addresses;
- temporary laboratory configurations.

---

# Simplicity

Version 0.1 should remain focused on replacing real engineering workflows.

Features that do not directly contribute towards that objective should normally
be deferred until a later release.

---

# Design Decisions

Whenever a new feature is proposed, ask:

> Does this help an engineer automate a real validation test more effectively?

If the answer is **no**, the feature should normally be deferred.

---

# Guiding Principle

The purpose of Test in a Box is not to replace engineering judgement.

Its purpose is to allow engineers to spend more time understanding their test
results and less time writing bespoke automation software.