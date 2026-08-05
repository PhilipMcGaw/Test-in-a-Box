# EA PS 2000 B — 2020 TFT Models

## Validation status

**TO BE CONFIRMED**

Identification has been confirmed on an EA PS 2084-05 B connected through its
front USB virtual COM port. The remaining read and control operations are
provided with a bench-test utility and must be verified before the Instrument
Library status is changed to `bench_tested`.

## Driver

```text
tiab/drivers/serial/ea_ps2000b.py
```

The driver uses the manufacturer's documented SCPI interface.

## Interface behaviour

- The front USB connection creates a virtual COM port.
- Conventional serial settings are ignored by the USB driver.
- USB does not require a command terminator.
- LF is supported and is used as the reply terminator.
- At least 50 ms is allowed between transmissions.
- Monitoring is available without remote control.
- Setpoint and output changes require remote control.

## Implemented operations

| Driver operation | SCPI command |
|---|---|
| Identify | `*IDN?` |
| Enter/leave remote | `SYST:LOCK ON` / `SYST:LOCK OFF` |
| Read remote owner | `SYST:LOCK:OWN?` |
| Set/read output | `OUTP ON`, `OUTP OFF`, `OUTP?` |
| Set/read voltage | `VOLT <value>`, `VOLT?` |
| Read measured voltage | `MEAS:VOLT?` |
| Set/read current | `CURR <value>`, `CURR?` |
| Read measured current | `MEAS:CURR?` |
| Read measured power | `MEAS:POW?` |
| Read all actual values | `MEAS:ARR?` |
| Read nominal ratings | `SYST:NOM:VOLT?`, `SYST:NOM:CURR?`, `SYST:NOM:POW?` |
| Read errors | `SYST:ERR?`, `SYST:ERR:ALL?` |

## Bench testing

Run the read-only test first:

```bat
python\python.exe tools\test_ea_ps2000b.py --port COM9
```

After reviewing the output, run the cautious control test with the output kept
OFF:

```bat
python\python.exe tools\test_ea_ps2000b.py --port COM9 --control-test --test-voltage 1.0 --test-current 0.1
```

The control test records and restores the existing voltage and current
setpoints. It keeps the output OFF throughout.

Do not run the control test with a DUT connected unless the proposed setpoints
and fixture state have been confirmed safe.

## Safe state

`safe_state()` attempts to:

1. switch the DC output OFF;
2. leave remote-control mode.

Software safe-state handling does not replace fixture-level protection,
emergency isolation or verification of the physical output.
