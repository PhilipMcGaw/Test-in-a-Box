"""
Instrument Library metadata for the Configure Devices interface.

This module describes the laboratory instruments that can be added from the
GUI. It contains presentation and configuration metadata only; driver creation
and registration remain the responsibility of ``registry.py``.

Each entry identifies:

- the driver type used internally;
- the engineering category shown to the user;
- the fields required to configure the instrument;
- the current validation status;
- a short description of the supported hardware.

The public name ``INSTRUMENT_LIBRARY`` reflects the terminology used throughout
the Test in a Box documentation. ``DEVICE_CATALOG`` remains as a compatibility
alias for existing code.
"""

from __future__ import annotations

from typing import Final

VALIDATION_STATUSES: Final[dict[str, str]] = {
    "demo": "Mock implementation only",
    "simulated": "Tested against a simulator or protocol implementation",
    "bench_tested": "Confirmed on physical hardware",
    "production_proven": "Used successfully during real engineering work",
    "unverified": "Implemented but not yet confirmed on physical hardware",
}

INSTRUMENT_LIBRARY: Final[dict[str, dict]] = {
    "mock_psu": {
        "label": "Mock PSU",
        "manufacturer": "Test in a Box",
        "instrument_category": "Power Supply",
        "category": "psu",
        "default_role": "Power Supply",
        "fields": [],
        "description": (
            "A simulated programmable power supply with no physical hardware. "
            "Useful for developing and testing procedures before real equipment "
            "is connected."
        ),
        "status": "demo",
        "status_description": VALIDATION_STATUSES["demo"],
    },
    "aimtti_psu": {
        "label": "Aim-TTi PSU",
        "manufacturer": "Aim-TTi",
        "instrument_category": "Power Supply",
        "category": "psu",
        "default_role": "Power Supply",
        "fields": [
            {
                "name": "serial_port",
                "label": "COM Port",
                "type": "text",
                "default": "COM5",
            },
            {
                "name": "num_channels",
                "label": "Channels",
                "type": "number",
                "default": 1,
            },
        ],
        "description": (
            "Aim-TTi bench power supplies using the manufacturer's serial remote "
            "command set. Intended for CPX, QL, PL, MX and related models over "
            "USB virtual COM port or RS232, without requiring NI-VISA."
        ),
        "status": "bench_tested",
        "status_description": (
            "Confirmed on a physical Thurlby Thandar QL355P for identification, "
            "voltage and current setpoints, output enable, output disable and "
            "Blockly-generated timed execution."
        ),
    },
    "scpi": {
        "label": "Generic SCPI Instrument",
        "manufacturer": "Generic",
        "instrument_category": "Generic Instrument",
        "category": "generic",
        "default_role": "Laboratory Instrument",
        "fields": [
            {
                "name": "command_map_path",
                "label": "Command Map File",
                "type": "text",
                "default": "drivers_config/my_instrument.json",
            },
        ],
        "description": (
            "A configurable SCPI instrument reached through PyVISA/NI-VISA over "
            "USB-TMC, LAN/VXI-11, GPIB or serial. New instruments can be added "
            "with a JSON command map rather than a dedicated Python driver."
        ),
        "status": "simulated",
        "status_description": (
            "The generic driver has been tested; each instrument command map "
            "must be validated against the intended hardware."
        ),
    },
    "seeit_relay08": {
        "label": "Seeit USBB-RELAY08",
        "manufacturer": "Seeit",
        "instrument_category": "Relay Controller",
        "category": "relay",
        "default_role": "Relay Controller",
        "fields": [
            {
                "name": "serial_port",
                "label": "COM Port",
                "type": "text",
                "default": "COM5",
            },
        ],
        "description": (
            "Eight-channel USB relay board. The serial protocol is based on a "
            "community implementation for the same board family because no "
            "public vendor protocol document has been identified."
        ),
        "status": "unverified",
        "status_description": VALIDATION_STATUSES["unverified"],
    },
    "mock_relay": {
        "label": "Mock Relay",
        "manufacturer": "Test in a Box",
        "instrument_category": "Relay Controller",
        "category": "relay",
        "default_role": "Relay Controller",
        "fields": [
            {
                "name": "num_channels",
                "label": "Channels",
                "type": "number",
                "default": 8,
            },
        ],
        "description": (
            "A simulated relay controller with no physical hardware. Useful for "
            "building and testing procedures before a real relay interface is "
            "connected."
        ),
        "status": "demo",
        "status_description": VALIDATION_STATUSES["demo"],
    },
    "pico_tc08": {
        "label": "Pico TC-08",
        "manufacturer": "Pico Technology",
        "instrument_category": "Temperature Logger",
        "category": "daq",
        "default_role": "Temperature Logger",
        "fields": [],
        "description": (
            "Pico Technology TC-08 eight-channel thermocouple data logger using "
            "the official PicoSDK Python wrapper. Requires PicoSDK to be "
            "installed."
        ),
        "status": "unverified",
        "status_description": VALIDATION_STATUSES["unverified"],
    },
    "pico_adc": {
        "label": "Pico ADC-20/24",
        "manufacturer": "Pico Technology",
        "instrument_category": "Data Acquisition",
        "category": "daq",
        "default_role": "Data Acquisition",
        "fields": [
            {
                "name": "num_channels",
                "label": "Channels",
                "type": "number",
                "default": 8,
            },
        ],
        "description": (
            "Pico Technology ADC-20 and ADC-24 high-resolution data loggers "
            "using the official PicoSDK PicoHRDL wrapper."
        ),
        "status": "unverified",
        "status_description": VALIDATION_STATUSES["unverified"],
    },
}

# Backwards-compatible name used by the current web server and GUI.
DEVICE_CATALOG = INSTRUMENT_LIBRARY
