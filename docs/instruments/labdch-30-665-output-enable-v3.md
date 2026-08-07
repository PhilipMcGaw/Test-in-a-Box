# LAB-DCH 30-665 Output Enable v3

Output enable is now verified by polling the measured output voltage rather
than relying on one fixed settle delay.

After each `SB,R` the driver polls:

```text
SB
MU
```

until either:

- measured voltage reaches the configured fraction of the target; or
- the verification timeout expires.

Defaults:

```text
Standby dwell:       2.0 s
Initial settle:      1.0 s
Verify timeout:      4.0 s
Verify poll interval 0.25 s
Verify target ratio: 0.8
Enable attempts:     2
```

This was introduced after a validation run reached 1 V successfully but
only 0.5 V when enabling a 5 V setpoint, despite `SB` already reporting
`SB,R`.
