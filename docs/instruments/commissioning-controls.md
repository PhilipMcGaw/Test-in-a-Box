# PSU Commissioning Controls

The Configure Devices page now provides live PSU commissioning controls
after **Save & Reconnect**.

Supported controls are derived from driver capabilities and cover Aim-TTi,
EA PS 2000 B, Korad/Tenma and compatible future PSU drivers:

- voltage setpoint with **Apply**;
- current setpoint with **Apply**;
- output ON/OFF;
- measured voltage;
- measured current;
- measured power when exposed by the driver;
- Aim-TTi range selection when supported.

Pressing Enter in a setpoint field also applies the value. Output enable is
never automatic. Driver-side limits and validation remain authoritative.
