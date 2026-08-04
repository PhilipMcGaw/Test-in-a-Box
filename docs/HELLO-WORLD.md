# Hello World Examples

## No-hardware example

This is the official first-run example.

```text
Set mock PSU voltage to 5 V
Turn mock output on
Wait 2 seconds
Read and log mock voltage
Turn mock output off
```

It proves that Blockly generates a runnable procedure, the runner executes it,
progress is shown, and CSV plus Markdown output is written.

## PSU-only real-hardware example

A programmable PSU that can read back its own output avoids the need for a DMM.

```text
Connect to PSU
Record instrument identity
Set voltage to 5 V
Set a safe current limit
Turn output on
Wait 5 seconds
Read back and log voltage and current
Turn output off
```

This exercises a real connection, identity capture, commands, logging and safe
shutdown.

---

## Bench-tested QL355P example

A bench-tested Blockly workspace for a physical Thurlby Thandar QL355P is
available here:

[QL355P Basic Output](../examples/01-QL355P-Basic-Output/)

The wider examples index is available at:

[Engineering examples](../examples/README.md)
