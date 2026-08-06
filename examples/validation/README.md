# Instrument Validation Sequences

## LAB-DCH Smoke Test

`labdch_smoke_test.json` is a short release-regression check. It:

- disables the output;
- sets OVP to 36 V;
- sets the current limit to 1 A;
- sets 12 V;
- enables the output;
- checks measured voltage is within 12 V ± 0.3 V;
- disables the output;
- checks the measured output falls below 0.3 V.

## LAB-DCH Driver Validation

`labdch_driver_validation.json` performs a no-load sweep at:

```text
1 V
5 V
12 V
24 V
30 V
```

It checks each point to ±0.3 V, disables the output between points, then
performs three 12 V output cycles.

## Required configuration

Both workspaces currently target the configured device ID:

```text
labdch_30_665_1
```

If the PSU has a different device name, use Configure Devices to rename it
to `labdch_30_665_1`, or edit each block's selected instrument after loading.

## Safety

These procedures are intended for an unloaded LAB-DCH 30-665.

- Confirm the output is safe to energise up to 30 V.
- Disconnect sensitive DUTs.
- Do not use the full validation sequence with an unknown load.
- Test in a Box applies driver safe state after a successful, stopped, or
  failed run, but the operator remains responsible for a safe bench setup.
