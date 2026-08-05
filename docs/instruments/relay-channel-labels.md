# Relay Channel Labels

Relay channels can be assigned meaningful engineering labels from the
**Configure Devices** page.

1. Open the relay board's cog menu.
2. Enter names under **Relay channel labels**.
3. Select **Save & Reconnect**.

Labels are stored per configured device:

```json
{
  "device_type": "seeit_usbb_native",
  "device_id": "Relay bank 1",
  "channel_labels": {
    "relay1": "DUT Power",
    "relay2": "Load Enable",
    "relay3": "Cooling Fan"
  }
}
```

The stable position IDs remain `relay1` through `relay8`; only their
display labels change. Existing procedures therefore continue to
address the same physical channels.

Custom labels appear in:

- Configure Devices relay cards;
- relay Blockly dropdowns;
- generic instrument-position lists;
- the `/api/devices` capability response.

Existing configurations without `channel_labels` remain valid. Leaving
a label blank restores the driver's default label.
