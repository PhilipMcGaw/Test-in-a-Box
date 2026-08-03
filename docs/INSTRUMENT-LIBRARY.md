# Hardware Library

## Introduction

The Hardware Library provides the connection between an engineering test
procedure and the physical laboratory equipment used to perform it.

A test procedure should describe **what** hardware is required rather than
**which specific instrument** is connected.

For example, a procedure should request:

- a programmable power supply;
- an environmental chamber;
- a relay controller;
- a temperature logger;

rather than referencing a particular COM port or manufacturer.

The Hardware Library maps those logical requirements to the instruments
currently available in the laboratory.

---

# Design Principles

The Hardware Library is based on several simple principles.

## Hardware Independence

A test procedure should not depend upon:

- COM port numbers;
- VISA resource strings;
- USB addresses;
- manufacturer-specific commands.

Instead, it should reference logical hardware roles.

Changing a power supply should not require the Blockly procedure to be
rewritten.

---

## Reusable Hardware Definitions

A new instrument should normally only need to be configured once.

After it has been added to the Hardware Library it can be reused by future
projects.

This allows engineering procedures to remain independent of the physical test
bench.

---

## Capability-Based Design

Blockly should request engineering capabilities.

Examples include:

- Set Voltage
- Measure Current
- Enable Output
- Set Temperature
- Read Digital Input

Drivers are responsible for implementing those capabilities for a specific
instrument.

---

# Adding New Hardware

There are two common workflows.

## Existing Hardware Definition

If the instrument already exists in the Hardware Library:

1. Select the required instrument.
2. Configure the current communication settings.
3. Assign the instrument to the required hardware role.
4. Verify communication.
5. Save the project configuration.

No additional driver development should normally be required.

---

## New Hardware

If the instrument has not previously been used:

1. Create a new hardware definition.
2. Select the instrument type.
3. Configure the communication method.
4. Enter the required driver or command-map information.
5. Verify operation using the mimic panel.
6. Save the hardware definition.

Future projects can then reuse the saved definition.

---

# Hardware Roles

The Blockly procedure should reference logical roles.

Typical examples include:

- Coil Power Supply
- Environmental Chamber
- Relay Controller
- Temperature Logger
- Data Acquisition
- Digital Multimeter

The engineer assigns the available laboratory equipment to those roles before
running the test.

---

# Instrument Identity

Where practical, the framework should automatically record instrument identity.

For SCPI instruments this normally includes:

```text
*IDN?
```

or the nearest equivalent for non-SCPI hardware.

Where available, the following information should be recorded:

- Manufacturer.
- Model.
- Serial number.
- Firmware version.
- Driver.
- Connection method.
- Instrument identity string.

This information improves traceability without becoming part of the test
procedure itself.

---

# Driver Status

Every hardware definition should clearly indicate its validation status.

Suggested status values are:

| Status | Meaning |
|--------|---------|
| Demo | Mock implementation only. |
| Simulated | Tested against a protocol simulator. |
| Bench Tested | Confirmed on physical hardware. |
| Production Proven | Successfully used during real engineering validation work. |

Documentation should accurately reflect the current status.

---

# Mock Hardware

Where practical, every supported capability should also provide a mock
implementation.

Mock hardware allows:

- development without laboratory equipment;
- automated testing;
- demonstration of the software;
- driver development;
- community contribution.

---

# Current Hardware

The repository currently includes support for:

- Generic SCPI instruments.
- Aim-TTi programmable power supplies.
- Seeit relay hardware.
- Pico TC-08.
- Pico ADC-20/24.
- Mock hardware.

Additional drivers will be added as real engineering projects require them.

---

# Future Development

Potential future improvements include:

- Automatic instrument discovery.
- Driver version reporting.
- Capability validation.
- Hardware health monitoring.
- Calibration information.
- Additional communication methods.

These items are intentionally outside the core Version 0.1 milestone.