# LAB-DCH 30-665 Enable Timing v4

Manual commissioning showed that the instrument can reach 12 V with a much
longer pause after `SB,S` than the earlier driver used.

The driver now uses:

```text
SB,S
wait 5 s
SB,R
wait 2 s
verify SB + MU
```

If the first enable does not produce a physical output, the driver sends
one additional `SB,R`, waits another 2 s, and verifies again.

This means the second enable is now a fallback rather than an unconditional
part of every enable sequence.

Existing high-resolution TX/RX and STATUS/STB tracing is retained.
