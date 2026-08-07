# Hardware-Independent Tests

This directory contains tests that can run without laboratory equipment or a
connected Pico device.

## Current coverage

`test_pico_drivers.py` verifies:

- ADC-20 capability exposure with eight analogue channels;
- ADC-24 capability exposure with sixteen analogue and four digital channels;
- ADC-24 digital bitmask decoding;
- TC-08 position ordering, with the internal temperature before channels 1–8.

These tests check the driver model and data interpretation only. They do not
open USB devices, load measurements, or claim physical hardware validation.

## Run the tests

From the repository root:

```text
python -m unittest discover -s tests -v
```

The tests use Python's standard-library `unittest` module and do not add a new
testing framework dependency.
