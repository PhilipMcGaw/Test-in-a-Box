# Development Status

This document describes the current development state of **Test in a Box** and
explains how to interpret the documentation.

The project is under active development and should currently be considered a
**v0.1.0-alpha**.

The overall architecture has been defined, but not every planned capability has
been implemented.

---

# Development Philosophy

Test in a Box is being developed using **real engineering validation projects**
rather than artificial demonstrations.

Features are generally added because they solve a genuine engineering problem
rather than because they are technically interesting.

The immediate focus is creating a practical tool for **electrical and
environmental R&D validation**.

---

# Current Status

The repository already contains:

- A FastAPI-based web application.
- A Blockly-based test authoring interface.
- Device configuration using a graphical interface.
- Hardware abstraction through Python drivers.
- Generic SCPI support.
- Mock hardware for development.
- Run, pause, resume, step and stop execution.
- CSV logging.
- Run metadata containing hostname, logged-in user, OS details, Python version and instrument identity.
- Instrument discovery support for compatible drivers.
- Native Windows Seeit USBB relay control through the vendor DLL.
- DUT mapping.
- Sequence save and load.
- Engineering examples under `examples/`.
- Bench-tested Blockly control of a physical Thurlby Thandar QL355P.
- QL355P identification, voltage setpoint, current-limit setpoint and output
  control.

Several other hardware drivers have been written but are still awaiting
confirmation against physical equipment.

---

# Documentation

The documentation describes both:

- **Current functionality**
- **Agreed v0.1 design goals**

Not every feature described in the documentation is currently implemented.

The definitive scope for version 0.1 is described in:

```text
docs/MVP-v0.1.md
```

---

# Driver Status

## Confirmed physical hardware

The Aim-TTi driver has been bench tested on a physical Thurlby Thandar QL355P.

Confirmed operations:

- `*IDN?` response;
- voltage setpoint;
- current-limit setpoint;
- output enable;
- output disable;
- Blockly-generated timed sequence.

Instrument identity is now written to the run metadata CSV where the driver
provides it.


The Seeit USBB native USB driver has operated physical relay hardware on
Windows. Duplicate-serial multi-board selection uses vendor enumeration
indices and still requires final validation in the main application.

Hardware drivers should always be honest about their validation state.

Typical driver status values are:

| Status | Meaning |
|---------|---------|
| Demo | Mock implementation only. |
| Simulated | Tested against a simulator or protocol implementation. |
| Bench Tested | Confirmed on real hardware. |
| Production Proven | Successfully used during real engineering work. |

No driver should claim to be validated unless it has been confirmed on the
appropriate physical hardware.

---

# Version Numbering

Development versions use the following progression:

```text
v0.1.0-pre-alpha
```

↓

```text
v0.1.0-alpha
```

↓

```text
v0.1.0-beta
```

↓

```text
v0.1.0
```

Version 0.1 is considered complete when a complete electrical or environmental
validation test can be:

1. Configured.
2. Authored in Blockly.
3. Executed.
4. Monitored.
5. Logged.
6. Repeated.

without writing bespoke control software.

---

# Coding Philosophy

Where practical:

- Tests should describe engineering intent.
- Drivers should implement hardware communication.
- Parameters should use explicit engineering units.
- Mock drivers should exist for example capabilities.
- Generated data should never be committed to Git.

---

# Roadmap

Near-term priorities:

- Complete the v0.1 workflow.
- Validate hardware drivers against physical instruments.
- Improve documentation.
- Improve user experience.

Long-term priorities:

- Richer reporting.
- Better result visualisation.
- Production-oriented workflows.
- Additional hardware support.

---

# Contributing

Development is currently being coordinated by the project author.

Bug reports, documentation improvements and practical feedback are very welcome.

Public code contributions are likely to become more formal after the first
stable release.

---

# Project Website

https://philipmcgaw.com/projects/test-in-a-box/

GitHub:

https://github.com/PhilipMcGaw/Test-in-a-Box