# Example 2 – QL355P Voltage Readback

## Status

Ready for bench testing.

## Purpose

Demonstrates how a measurement value is:

1. read from an instrument;
2. stored in a Blockly variable;
3. logged with an engineering label;
4. checked against a tolerance.

## Hardware

- Aim-TTi / Thurlby Thandar QL355P

## Procedure

1. Set the PSU to 10 V.
2. Set the current limit to 3 A.
3. Enable the output.
4. Wait for 1 second.
5. Read measured voltage into `measured_voltage`.
6. Log `Measured voltage`.
7. Assert that the measured voltage is within 0.2 V of 10 V.
8. Disable the output.

## Expected behaviour

The measured voltage is written to the run CSV. The assertion records PASS when
the measured voltage is between 9.8 V and 10.2 V. A failed assertion stops the
procedure, after which the server applies the PSU safe state.
