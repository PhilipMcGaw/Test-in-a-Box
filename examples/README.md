# Examples

These examples demonstrate engineering workflows rather than individual
software features.

Start with the examples in numerical order.

| Example | Status | Purpose |
|---|---|---|
| [01 – QL355P Basic Output](01-QL355P-Basic-Output/) | Bench tested | Basic control of a real Aim-TTi QL355P. |
| [02 – QL355P Voltage Readback](02-QL355P-Voltage-Readback/) | Ready to try | Read, store, log and check a measured voltage. |
| [03 – Relay Basic Control](03-Relay-Basic-Control/) | Planned | Basic Seeit relay control. |
| [04 – Voltage Sweep](04-Voltage-Sweep/) | Planned | Sweep a PSU setpoint and log measurements. |
| [05 – Relay Pickup Test](05-Relay-Pickup-Test/) | Planned | Determine a relay pickup or release point. |
| [06 – TO-1800 TC2 Pickup and Hold](06-TO-1800-TC2-Pickup-and-Hold/) | Planned | A complete real engineering validation procedure. |

## Loading an example

Copy the example's `workspace.json` into:

```text
webapp/sequences/
```

Rename it to a descriptive sequence name if required, restart Test in a Box,
then load it from the Sequence list.

Examples refer to logical device IDs. If your configured instrument uses a
different ID, select the appropriate instrument position in the Blockly block
before running the procedure.

Always verify wiring, current limits and safe states before energising real
hardware.
