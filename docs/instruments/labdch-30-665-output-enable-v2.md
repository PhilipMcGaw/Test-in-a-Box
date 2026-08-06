# LAB-DCH 30-665 Output Enable v2

Run reports showed that the first characterised implementation completed
its `SB,S` / `SB,R` sequence but `MU` remained at `0.00 V`.

Version 2 therefore verifies the physical output rather than trusting
`SB,R` alone:

1. Read `MODE`; select `MODE,UI` only when required.
2. Read the programmed voltage with `UA`.
3. Send `SB,S`.
4. Wait for the configurable standby dwell.
5. Send `SB,R`.
6. Wait for output settling.
7. Read both `SB` and `MU`.
8. Retry `SB,R` when the power stage has not energised.
9. Raise a clear driver error if the physical output still remains off.

Defaults:

```text
Standby dwell:      2.0 s
Enable settle time: 1.0 s
Enable attempts:    2
```

The driver accepts the default values even when an existing configuration
file does not yet contain these new fields.
