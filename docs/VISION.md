# Vision

## Why Test in a Box exists

Engineering validation often begins with a specification, a collection of
laboratory instruments and a question that needs answering.

Too often, the software required to automate that test is built from scratch
for each project using a mixture of Python scripts, spreadsheets, vendor
applications and one-off utilities. These solutions can work well for an
individual programme but are often difficult to maintain, reuse and adapt for
future work.

Test in a Box exists to reduce the amount of bespoke software engineers write
when automating **electrical and environmental validation tests**.

The goal is not to replace engineering judgement.

The goal is to make good engineering easier to automate.

---

# The Vision

Test in a Box should allow an engineer to concentrate on the **test procedure**
rather than the software required to execute it.

An engineer should describe:

- what should happen;
- what should be measured;
- what data should be recorded;

while the framework determines how to communicate with the laboratory
equipment.

A test procedure should say:

> Set the chamber temperature to **40 °C**

not

> Send `TEMP 40` over serial port COM7.

Hardware communication belongs in drivers.

Engineering intent belongs in the test procedure.

---

# Engineering First

Test in a Box is being developed around real engineering validation projects.

The software follows the same workflow an engineer would normally use:

1. Read the specification.
2. Clarify any missing requirements.
3. Confirm the required measurements and data resolution.
4. Select appropriate laboratory equipment.
5. Design the physical test setup.
6. Write the engineering test procedure.
7. Automate the execution.

Test in a Box starts at the final step.

It is not intended to replace engineering judgement or the process of designing
a good test.

---

# R&D Before Production

The initial focus is **research and development**.

Many R&D tests are one-off investigations or evolving validation programmes.
Requirements often change as the engineer learns more about the DUT.

Test in a Box is intended to make these tests quicker to automate without
requiring a large upfront investment in software development.

The architecture is designed so that more structured production and end-of-line
testing features can be added later without changing the underlying philosophy.

---

# Hardware Independence

Engineering test procedures should not depend on:

- COM port numbers;
- USB addresses;
- VISA resource strings;
- manufacturer-specific commands.

Instead, they should depend on logical engineering concepts such as:

- Power Supply
- Environmental Chamber
- Relay Controller
- Data Acquisition System

The hardware used to fulfil those roles can change without requiring the test
procedure to be rewritten.

---

# Engineering Units

Parameters and measurements should always use explicit engineering units.

Examples include:

- 40 °C
- 3600 s
- 9 V
- 0.2 V/s
- 0.373 mΩ

Using engineering units improves readability and helps prevent mistakes.

---

# Characterisation and Validation

Not every engineering test has pass/fail criteria.

Some tests simply collect information to better understand the behaviour of a
device.

Test in a Box should support both:

- informational measurements;
- measurements evaluated against defined acceptance criteria.

Neither should be treated as a second-class workflow.

---

# Open Architecture

The architecture is intended to be:

- modular;
- reusable;
- hardware-independent;
- easy to extend.

Support for new laboratory equipment should normally involve writing or
configuring a driver rather than modifying existing test procedures.

---

# Version 0.1

Version 0.1 is considered successful when a complete electrical or
environmental validation test can be:

- configured;
- authored visually;
- executed;
- monitored;
- logged;
- repeated;

without writing bespoke control software.

Version 0.1 deliberately focuses on proving the core workflow rather than
providing every feature that may eventually be desirable.

---

# Looking Forward

As Test in a Box matures it may grow to include:

- richer reporting;
- result visualisation;
- additional hardware support;
- improved evaluation tools;
- production-oriented workflows.

Future features should support the original vision rather than replace it.

Whenever a design decision is made, the first question should be:

> Does this help an engineer automate a real validation test more effectively?

If the answer is no, the feature should be reconsidered.