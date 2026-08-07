# Serial Driver Patching

This directory contains serial instrument drivers used by Test in a Box.

## Shared serial helper

`common.py` contains small helpers shared by serial drivers. The current
shared helper is:

```python
from .common import decode_terminator

terminator = decode_terminator(r"\r\n")
```

`decode_terminator()` converts configured escape text such as `\n`, `\r`,
and `\r\n` into the byte sequence sent to an instrument.

## Adding or patching a serial driver

Keep the following responsibilities inside the driver:

- instrument-specific baud rate and serial settings;
- command and response formats;
- identity parsing;
- numeric and status parsing;
- capability definitions;
- safe-state behaviour;
- protocol timing and retries required by the instrument.

Use the shared helper for common terminator decoding rather than duplicating
the escape-sequence conversion in a driver.

Example:

```python
from .common import decode_terminator

self._command_terminator = decode_terminator(command_terminator)
self._reply_terminator = decode_terminator(reply_terminator)
```

## Device-specific validation

The helper does not validate an instrument protocol. A driver must still
validate values when its protocol has stricter requirements. For example, a
driver may limit terminators to LF, CR, or CRLF before passing the value to the
shared decoder.

Do not move protocol behaviour into `common.py` merely because two devices
currently use similar commands. Shared code belongs there only when the
behaviour is transport-level and has the same meaning for every caller.

## Verification after a patch

From the repository root:

```text
python -m compileall -q tiab webapp
python -m tiab.example_scripts.demo_test
```

Physical-driver changes also require validation against the relevant
instrument before describing the driver as bench-tested.
