# Korad / Tenma Programmable PSU

## Status

**TO BE CONFIRMED**

An initial single-output driver exists at:

```text
tiab/drivers/serial/korad_tenma_psu.py
```

The implementation is derived from practical LabLogBook records. Fresh bench
confirmation is still required for serial settings, line termination, reply
formatting and current hardware behaviour.

The default configuration currently assumes 9600 baud, 8 data bits, no parity,
1 stop bit, no flow control and LF termination. Every assumption is
configurable in the Instrument Library.

## Previously recorded compatible models

| Manufacturer | Model | Output rating | Supplier part number | Recorded status |
|---|---|---:|---|---|
| Tenma | 72-2535 | 30 V, 3 A, single output | Farnell 2445411 | Not yet tested |
| Tenma | 72-2540 | 30 V, 5 A, single output | Farnell 2445412 | LabLogBook commands worked |
| Tenma | 72-2545 | 60 V, 2 A, single output | Farnell 2445413 | Not yet tested |
| Tenma | 72-2550 | 60 V, 3 A, single output | Farnell 2445414 | Not yet tested |
| Tenma | 72-2930 | 30 V, 10 A, single output | Farnell 2543064 | Not yet tested |
| Tenma | 72-2940 | 60 V, 5 A, single output | Farnell 2543067 | Not yet tested |
| Korad | KA3005P | 30 V, 5 A, single output | DigiKey 2260-KA3005P-ND | LabLogBook commands worked |
| Korad | KA3305P | 30 V, 5 A dual output, plus 5 V, 5 A output | DigiKey 2260-KA3305P-ND | Not yet tested; multi-output unsupported |
| Korad | KA6003P | 60 V, 3 A, single output | DigiKey 2260-KA6003P-ND | LabLogBook commands worked |

## Implemented commands

| Driver operation | Command |
|---|---|
| Identify | `*IDN?` |
| Output off/on | `OUT0` / `OUT1` |
| Set voltage | `VSET1:<value>` |
| Read voltage setpoint | `VSET1?` |
| Read actual voltage | `VOUT1?` |
| Set current | `ISET1:<value>` |
| Read current setpoint | `ISET1?` |
| Read actual current | `IOUT1?` |
| OVP off/on | `OVP0` / `OVP1` |
| OCP off/on | `OCP0` / `OCP1` |

The OCP enable command is implemented as `OCP1`; this must be confirmed on the
bench because the original notes contained an inconsistent `OVP1` entry in the
OCP row.

## Safety

`safe_state()` commands the PSU output OFF. This does not replace fixture-level
protection, emergency isolation or verification that the PSU accepted the
command.
