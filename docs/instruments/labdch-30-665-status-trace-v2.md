# LAB-DCH 30-665 Status Trace v2

This diagnostic patch keeps the existing output-enable sequence and adds
automatic `STATUS` and `*STB?` snapshots.

Snapshots are taken:

- before standby;
- after standby;
- after the first `SB,R`;
- after the second `SB,R`;
- during every `SB` / `MU` verification poll.

Example trace entries:

```text
REGS: after-first-enable STATUS,.... STB,....
STATE: poll=1 SB=R MU=0.65 V STATUS,.... STB,....
STATE: poll=2 SB=R MU=0.05 V STATUS,.... STB,....
```

This is intended to reveal which status bit changes when measured output
voltage rises briefly and then collapses.

The persistent log remains:

```text
logs/labdch_trace.log
```
