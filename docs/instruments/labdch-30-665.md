# LAB-DCH 30-665 RS232 Power Supply

## Connection

| Parameter | Value |
|---|---|
| Baud | 9600 |
| Data bits | 8 |
| Parity | None |
| Stop bits | 1 |
| Flow control | None |
| Cable | Null modem |

Commands are terminated with LF by default. The terminator is configurable
as LF, CR or CRLF.

## Test in a Box support

The driver type is:

```text
labdch_30_665
```

It exposes:

- voltage setpoint;
- current limit;
- output enable;
- measured voltage;
- measured current;
- over-voltage protection.

These capabilities are automatically picked up by the existing PSU Blockly
blocks:

- Set PSU voltage;
- Set PSU current limit;
- PSU output;
- Read PSU voltage;
- Read PSU current;
- Ramp PSU voltage.

No model-specific Blockly block is required.

## Startup and safe state

By default the driver sends `GTR` when connecting and `GTL` when closing.
Safe state sends `SB,S`, which disables the output without changing the
programmed voltage/current settings.

## Additional protocol access

The driver also provides raw query support and model-specific methods for:

- front-panel lock (`LLO`);
- mode read/write (`MODE`);
- device status (`STATUS`);
- interface status (`*STB?`);
- firmware (`*OPT?`).

## Validation status

The implementation is based on the supplied quick reference and remains
unverified until tested against physical hardware.

## Serial trace and output verification

The driver can print every LAB-DCH command and response to the application
console. This is enabled by default while the driver is being commissioned.

Example:

```text
[LAB-DCH:Bench PSU] TX: GTR
[LAB-DCH:Bench PSU] TX: MODE,UI
[LAB-DCH:Bench PSU] TX: SB,R
[LAB-DCH:Bench PSU] TX: SB
[LAB-DCH:Bench PSU] RX: SB,R
```

When output enable is requested, the driver can:

1. send `MODE,UI`;
2. send `SB,R`;
3. query `SB`;
4. raise a clear error if the readback remains `SB,S`.

Configure Devices exposes switches for serial tracing, UI-mode selection and
output-state verification. These can be disabled after hardware commissioning
if quieter console output is preferred.
