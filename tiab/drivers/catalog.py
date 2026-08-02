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
        "description": "A simulated power supply with no real hardware — useful for building "
                        "and testing sequences before real equipment is connected.",
        "status": "demo only",
    },
    "aimtti_psu": {
        "label": "Aim-TTi PSU",
        "category": "psu",
        "fields": [
            {"name": "serial_port", "label": "COM Port", "type": "text", "default": "COM5"},
            {"name": "num_channels", "label": "Channels", "type": "number", "default": 1},
        ],
        "description": "Aim-TTi bench power supplies (CPX400 series, QL series, PL series, "
                        "MX series, and others sharing the same remote command set), connected "
                        "over USB (virtual COM port) or RS232 — no VISA/NI-VISA required. "
                        "Supports voltage/current set + readback and output on/off, per channel "
                        "for dual-output models.",
        "status": "tested against a protocol-accurate simulator; not yet confirmed on physical hardware",
    },
    "scpi": {
        "label": "Generic SCPI Instrument",
        "category": "generic",
        "fields": [
            {"name": "command_map_path", "label": "Command Map File", "type": "text",
             "default": "drivers_config/my_instrument.json"},
        ],
        "description": "Any SCPI instrument reachable via PyVISA/NI-VISA (USB-TMC, LAN/VXI-11, "
                        "GPIB, serial). Add a new instrument by writing a small JSON command "
                        "map (see scpi_command_map.example.json) — no new code required.",
        "status": "core driver tested; each instrument's command map needs its own confirmation",
    },
    "seeit_relay08": {
        "label": "Seeit USBB-RELAY08",
        "category": "relay",
        "fields": [
            {"name": "serial_port", "label": "COM Port", "type": "text", "default": "COM5"},
        ],
        "description": "8-channel USB relay board from Seeit. Serial commands adapted from an "
                        "open-source community driver for the same board family (no public "
                        "vendor protocol document exists).",
        "status": "not yet confirmed against physical hardware",
    },
    "mock_relay": {
        "label": "Mock Relay",
        "category": "relay",
        "fields": [
            {"name": "num_channels", "label": "Channels", "type": "number", "default": 8},
        ],
        "description": "A simulated relay board with no real hardware — useful for building "
                        "and testing sequences before real equipment is connected.",
        "status": "demo only",
    },
    "pico_tc08": {
        "label": "Pico TC-08",
        "category": "daq",
        "fields": [],
        "description": "Pico Technology TC-08 8-channel thermocouple data logger, via the "
                        "official picosdk Python wrapper. Requires PicoSDK to be installed "
                        "alongside PicoScope/PicoLog.",
        "status": "not yet confirmed against physical hardware",
    },
    "pico_adc": {
        "label": "Pico ADC-20/24",
        "category": "daq",
        "fields": [
            {"name": "num_channels", "label": "Channels", "type": "number", "default": 8},
        ],
        "description": "Pico Technology ADC-20/24 High-Resolution Data Logger, via the "
                        "official picosdk PicoHRDL wrapper.",
        "status": "not yet confirmed against physical hardware",
    },
}
