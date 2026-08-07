# LAB-DCH 30-665 Driver Trace v1

The LAB-DCH output-enable path now emits a high-resolution diagnostic trace.

Each event includes:

- elapsed milliseconds since the enable sequence began;
- elapsed milliseconds since the previous event;
- TX/RX direction;
- waits;
- enable-attempt number;
- `SB` state;
- measured `MU` voltage.

Example:

```text
[LAB-DCH-ENABLE:labdch_30_665_1] +00000 ms (+0000) BEGIN: output enable sequence
[LAB-DCH-ENABLE:labdch_30_665_1] +00020 ms (+0020) TX: UA
[LAB-DCH-ENABLE:labdch_30_665_1] +00035 ms (+0015) RX: UA,12.00V
```

A persistent copy is written by default to:

```text
logs/labdch_trace.log
```

## Test procedure

1. Run **LAB-DCH Smoke Test**.
2. Copy the LAB-DCH enable trace from the console or trace log.
3. Use Protocol Explorer in connected-instrument mode.
4. Manually repeat the successful/expected sequence.
5. Compare command order and timing.
