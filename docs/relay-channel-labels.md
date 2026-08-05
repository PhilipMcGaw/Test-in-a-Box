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

Stable position IDs remain `relay1` through `relay8`; only the displayed
labels change. Existing procedures therefore continue to address the
same physical channels.

Custom labels appear in the Configure Devices relay cards and in
Blockly relay dropdowns after **Save & Reconnect**.

Leaving a label blank restores the driver's default label.
