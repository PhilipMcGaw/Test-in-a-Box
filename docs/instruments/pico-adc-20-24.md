# Pico ADC-20 / ADC-24

## Driver

The driver type is:

```text
pico_adc
```

Select the model explicitly with `adc20` or `adc24`.

When a unit is connected, the driver captures the Pico batch/serial identity.
That identity is written to run metadata and the run manifest, allowing
multiple configured ADC units to be distinguished in reports.

## Analogue inputs

Analogue positions are exposed as `ch1` onward and return volts. The number
of analogue channels is controlled by `num_channels`.

## ADC-24 digital inputs

When the model is `adc24`, the driver additionally exposes:

| Position | Description | Value |
|---|---|---|
| `d1` | Digital input 1 | Boolean |
| `d2` | Digital input 2 | Boolean |
| `d3` | Digital input 3 | Boolean |
| `d4` | Digital input 4 | Boolean |

The driver configures all four pins as inputs. It does not configure or drive
any digital outputs.

The four input states are read from the PicoSDK digital port and logged as
measurement events. `read_digital_port()` is also available when the combined
four-bit port value is required.

## Runtime setup

The `picosdk` Python package and PicoHRDL runtime are required. For local
testing, the runtime DLL may be placed at:

```text
vendor/pico/runtime/picohrdl.dll
```

The vendor DLL is not distributed with Test in a Box.

## Validation

An ADC-24 was opened successfully with all four digital inputs enabled. The
initial read returned raw value `0`, corresponding to:

```text
d1 = False
d2 = False
d3 = False
d4 = False
```

This confirms the read path and input configuration. Further validation with
each input driven high and low remains required.

## Current identity probe

The connected Pico unit returned batch/serial identity:

```text
13198/046
```

The identity was read through PicoSDK and is not a manually assigned label.
