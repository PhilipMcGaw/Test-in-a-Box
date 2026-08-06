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
