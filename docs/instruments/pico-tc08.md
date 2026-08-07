# Pico TC-08

## Driver

The driver type is:

```text
pico_tc08
```

The driver uses the official `picosdk` Python wrapper and the PicoSDK
`usbtc08.dll` runtime.

## Exposed positions

The TC-08 exposes nine temperature input positions:

| Position | Description | Unit |
|---|---|---|
| `internal_temperature` | TC-08 internal temperature transducer | `degC` |
| `ch1` … `ch8` | External thermocouple channels | `degC` |

External channels default to thermocouple type K. Channel types can be
provided through the driver's `tc_types` configuration.

## Runtime setup

The `picosdk` Python package must be installed in the Python environment used
by Test in a Box. The project also supports a local runtime directory for
testing:

```text
vendor/pico/runtime/usbtc08.dll
```

The Pico DLL is vendor software and is not distributed with Test in a Box.
Any local copy used for development or validation must be obtained and
licensed separately.

## Reading data

The driver uses the PicoSDK single-read API. A read returns Celsius values and
emits a measurement event for CSV logging. `read_all()` returns the internal
temperature and all configured external channels.

## Current validation

The driver has been exercised against a connected physical TC-08 using a
locally supplied PicoSDK DLL. The unit opened successfully and returned
values for the internal transducer and channels 1–8.

This is a current bench probe, not a claim of production-proven status.
Further validation should cover configured thermocouple types, disconnected
or invalid channels, overflow handling, repeated reads, and the full Blockly
workflow.
