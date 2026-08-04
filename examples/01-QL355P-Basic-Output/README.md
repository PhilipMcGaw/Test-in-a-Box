# Example 1 – QL355P Basic Output

## Status

Bench tested on a Thurlby Thandar QL355P.

## Purpose

Demonstrates basic control of one Aim-TTi QL355P power supply.

## Hardware

- Aim-TTi / Thurlby Thandar QL355P
- USB or RS232 connection

## Procedure

1. Set the output voltage to 10 V.
2. Set the current limit to 3 A.
3. Enable the output.
4. Wait for 5 seconds.
5. Disable the output.

## Expected behaviour

The PSU output is enabled for five seconds and then disabled.

No DUT is required.

## Safety

Confirm that 10 V and a 3 A current limit are safe for anything connected to
the PSU before running the example. Run it with no load for the first trial.
