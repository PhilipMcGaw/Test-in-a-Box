# COM Port Discovery

Configure Devices now renders every `serial_port` setting as a populated
drop-down rather than a free-text field.

## Refresh COM Ports

**Refresh COM Ports** asks Windows/pyserial for the currently enumerated
serial interfaces and displays:

- COM port;
- Windows description;
- USB manufacturer/product metadata when available.

This scan does not open the ports or send commands.

## Find Compatible Instrument

**Find Compatible Instrument** explicitly probes each COM port using the
selected Test in a Box driver. The driver performs its normal
connect/identify/close sequence, allowing it to use `*IDN?`, `ID`, or a
protocol-specific equivalent.

Only ports that identify successfully are placed in the filtered
drop-down. Failed ports remain available through **Refresh COM Ports**.

Because probing opens ports and may briefly enter remote mode, it is only
performed when the engineer presses the button. It is unavailable while a
test run is active.
