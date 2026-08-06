# LAB-DCH 30-665 Debug Patch

This patch adds console-level serial tracing and verifies the PSU output
state after an enable/disable command.

The expected enable sequence is:

```text
MODE,UI
SB,R
SB
```

The final response should be `SB,R`. A response of `SB,S` now produces an
explicit driver error rather than reporting success.
