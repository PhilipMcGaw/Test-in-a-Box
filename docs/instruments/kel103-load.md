# KEL103 Programmable Electronic Load

## Status

**TO BE CONFIRMED**

An initial driver exists at:

```text
tiab/drivers/serial/kel103_load.py
```

The implementation is derived from practical LabLogBook records. Most listed
normal-operation commands had previously been tested, but fresh confirmation is
still required for serial settings, line termination, reply formatting and
current hardware behaviour.

The default configuration currently assumes 9600 baud, 8 data bits, no parity,
1 stop bit, no flow control and LF termination. Every assumption is
configurable in the Instrument Library.

## Implemented commands

| Driver operation | Command |
|---|---|
| Identify | `*IDN?` |
| Input off/on | `:INP OFF` / `:INP ON` |
| CV mode | `:FUNC VOLT` |
| CC mode | `:FUNC CURR` |
| CR mode | `:FUNC RES` |
| CP mode | `:FUNC POW` |
| Read mode | `:FUNC?` |
| Set/read CV | `:VOLT <value>V` / `:VOLT?` |
| Measure voltage | `:MEAS:VOLT?` |
| Set/read CC | `:CURR <value>A` / `:CURR?` |
| Measure current | `:MEAS:CURR?` |
| Set/read CR | `:RES <value>OHM` / `:RES?` |
| Set/read CP | `:POW <value>W` / `:POW?` |
| Measure power | `:MEAS:POW?` |
| Read status | `:STAT?` |

## Deliberately unsupported

`:\u200bMEAS?` is not implemented because the LabLogBook records do not confirm
what it returns. It should remain unsupported until tested and understood.

## Safety

`safe_state()` commands the electronic-load input OFF. This does not replace
fixture-level protection or verification that the load accepted the command.
