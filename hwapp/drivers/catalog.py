"""
Metadata about each registered driver type, for the "Configure Devices"
GUI: what category of front-panel visual to draw (psu / relay / daq /
generic), a friendly label, and which config fields to show when someone
drags one onto the canvas.

This is presentation metadata only — it doesn't affect how drivers
connect or run. Add an entry here when you add a new driver type if you
want it to show up nicely in the devices canvas; if you skip it, the
type still works everywhere else, it just won't be draggable from the
sidebar there.
"""

from __future__ import annotations

DEVICE_CATALOG = {
    "mock_psu": {
        "label": "Mock PSU",
        "category": "psu",
        "fields": [],
    },
    "aimtti_psu": {
        "label": "Aim-TTi PSU",
        "category": "psu",
        "fields": [
            {"name": "serial_port", "label": "COM Port", "type": "text", "default": "COM5"},
            {"name": "num_channels", "label": "Channels", "type": "number", "default": 1},
        ],
    },
    "scpi": {
        "label": "Generic SCPI Instrument",
        "category": "generic",
        "fields": [
            {"name": "command_map_path", "label": "Command Map File", "type": "text",
             "default": "drivers_config/my_instrument.json"},
        ],
    },
    "seeit_relay08": {
        "label": "Seeit USBB-RELAY08",
        "category": "relay",
        "fields": [
            {"name": "serial_port", "label": "COM Port", "type": "text", "default": "COM5"},
        ],
    },
    "mock_relay": {
        "label": "Mock Relay",
        "category": "relay",
        "fields": [
            {"name": "num_channels", "label": "Channels", "type": "number", "default": 8},
        ],
    },
    "pico_tc08": {
        "label": "Pico TC-08",
        "category": "daq",
        "fields": [],
    },
    "pico_adc": {
        "label": "Pico ADC-20/24",
        "category": "daq",
        "fields": [
            {"name": "num_channels", "label": "Channels", "type": "number", "default": 8},
        ],
    },
}
