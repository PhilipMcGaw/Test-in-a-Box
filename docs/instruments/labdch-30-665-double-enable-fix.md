# LAB-DCH 30-665 Double-Enable Fix

High-resolution tracing confirmed that the previous driver sent one
`SB,R`, then only polled `SB` and `MU`. During successful manual bench
testing, the instrument required two `SB,R` commands.

The driver now treats the second enable command as part of the normal
sequence:

```text
MODE / verify UI
UA / read target
SB,S
wait 2.0 s
SB,R
wait 1.0 s
SB,R
wait 1.0 s
poll SB + MU
```

The delay between the two enable commands is configurable with:

```text
output_second_enable_delay
```

Default: `1.0 s`.
