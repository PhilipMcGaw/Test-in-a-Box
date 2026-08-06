# Protocol Explorer Write-Only Command Fix

When **Read response** is unchecked, connected-instrument mode now calls the
driver's public `write_command()` method instead of `query()`.

Write-only LAB-DCH commands such as:

```text
OVP,36
UA,12
IA,1
SB,R
SB,S
```

therefore complete immediately and are logged as:

```text
OK   write-only command sent
```

rather than producing a false serial timeout.

Direct serial mode also reports a clearer message when the selected COM
port is already owned by a configured Test in a Box driver.
