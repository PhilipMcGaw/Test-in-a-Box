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
                "type": "serial_port",
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

"ea_ps2000b": {
    "label": "EA PS 2000 B (2020 TFT)",
    "manufacturer": "EA Elektro-Automatik",
    "instrument_category": "Power Supply",
    "category": "psu",
    "default_role": "Power Supply",
    "fields": [
        {
            "name": "serial_port",
            "label": "COM Port",
            "type": "serial_port",
            "default": "COM9",
        },
        {
            "name": "command_terminator",
            "label": "Command Terminator",
            "type": "text",
            "default": "",
        },
        {
            "name": "reply_terminator",
            "label": "Reply Terminator",
            "type": "text",
            "default": "\\n",
        },
        {
            "name": "minimum_interval",
            "label": "Minimum Command Interval (s)",
            "type": "number",
            "default": 0.05,
        },
    ],
    "description": (
        "Native SCPI driver for the 2020 TFT generation of EA PS 2000 B "
        "power supplies over the front USB virtual COM port."
    ),
    "status": "bench_tested",
    "status_description": (
        "Bench tested on a physical EA PS 2084-05 B for identification, "
        "read-only measurements, nominal ratings, remote control, voltage "
        "and current setpoints, output-off control, error reporting and "
        "restoration of the original setpoints. Output-on operation remains "
        "to be confirmed separately."
    ),
},

    "labdch_30_665": {
        "label": "LAB-DCH 30-665 PSU",
        "manufacturer": "LAB-DCH",
        "instrument_category": "Power Supply",
        "category": "psu",
        "default_role": "Power Supply",
        "fields": [
            {
                "name": "serial_port",
                "label": "COM Port",
                "type": "serial_port",
                "default": "COM5",
            },
            {
                "name": "baudrate",
                "label": "Baud Rate",
                "type": "number",
                "default": 9600,
            },
            {
                "name": "timeout",
                "label": "Serial Timeout (s)",
                "type": "number",
                "default": 2.0,
            },
            {
                "name": "minimum_interval",
                "label": "Minimum Command Interval (s)",
                "type": "number",
                "default": 0.05,
            },
            {
                "name": "command_terminator",
                "label": "Command Terminator",
                "type": "text",
                "default": "\\n",
            },
            {
                "name": "remote_on_connect",
                "label": "Enter Remote Mode on Connect",
                "type": "boolean",
                "default": True,
            },
            {
                "name": "local_on_close",
                "label": "Return to Local Mode on Close",
                "type": "boolean",
                "default": True,
            },
            {
                "name": "trace_serial",
                "label": "Trace Serial TX/RX to Console",
                "type": "boolean",
                "default": True,
            },
            {
                "name": "select_ui_mode_on_enable",
                "label": "Select UI Mode Before Output Enable",
                "type": "boolean",
                "default": True,
            },
            {
                "name": "verify_output_state",
                "label": "Verify Output State After Command",
                "type": "boolean",
                "default": True,
            },
            {
                "name": "output_standby_delay",
                "label": "Output Standby Dwell (s)",
                "type": "number",
                "default": 5.0,
            },
            {
                "name": "output_settle_delay",
                "label": "First Enable Settle Time (s)",
                "type": "number",
                "default": 2.0,
            },
            {
                "name": "output_enable_attempts",
                "label": "Output Enable Attempts",
                "type": "number",
                "default": 2,
            },
            {
                "name": "verify_output_voltage",
                "label": "Verify Physical Output Voltage",
                "type": "boolean",
                "default": True,
            },
            {
                "name": "output_verify_timeout",
                "label": "Output Verify Timeout (s)",
                "type": "number",
                "default": 4.0,
            },
            {
                "name": "output_verify_interval",
                "label": "Output Verify Poll Interval (s)",
                "type": "number",
                "default": 0.25,
            },
            {
                "name": "output_verify_ratio",
                "label": "Output Verify Target Ratio",
                "type": "number",
                "default": 0.8,
            },
            {
                "name": "output_second_enable_delay",
                "label": "Retry Enable Settle Time (s)",
                "type": "number",
                "default": 2.0,
            },
            {
                "name": "enable_trace",
                "label": "Trace Output Enable Sequence",
                "type": "boolean",
                "default": True,
            },
            {
                "name": "enable_trace_path",
                "label": "Output Enable Trace Log",
                "type": "text",
                "default": "logs/labdch_trace.log",
            },
            {
                "name": "trace_status_registers",
                "label": "Trace STATUS and STB During Enable",
                "type": "boolean",
                "default": True,
            },
        ],
        "description": (
            "LAB-DCH 30-665 programmable DC power supply over RS232. "
            "Supports voltage/current setpoints, measured voltage/current, "
            "output control, OVP, identification and safe-state output off."
        ),
        "setup_note": (
            "Use a null-modem RS232 cable. Default serial settings are "
            "9600 baud, 8 data bits, no parity, 1 stop bit and no flow control."
        ),
        "status": "unverified",
        "status_description": (
            "Implemented from the supplied LAB-DCH 30-665 RS232 quick "
            "reference and awaiting validation on physical hardware."
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
        "label": "Seeit USB-RELAY08 (Serial)",
        "manufacturer": "Seeit",
        "instrument_category": "Relay Controller",
        "category": "relay",
        "default_role": "Relay Controller",
        "fields": [
            {
                "name": "serial_port",
                "label": "COM Port",
                "type": "serial_port",
                "default": "COM5",
            },
        ],
        "description": (
            "Eight-channel USB-RELAY08 controlled through a Prolific PL2303 "
            "virtual serial COM port at 9600 baud."
        ),
        "setup_note": (
            "Install the PL2303 driver if Windows does not create a COM port, "
            "then select that COM port in Configure Devices."
        ),
        "product_url": (
            "https://seeit.fr/produits.php?produit_ref=USB-RELAY08"
        ),
        "status": "unverified",
        "status_description": VALIDATION_STATUSES["unverified"],
    },
    "seeit_usbb_native": {
        "label": "Seeit USBB Relay (Native USB)",
        "manufacturer": "Seeit",
        "instrument_category": "Relay Controller",
        "category": "relay",
        "default_role": "Relay Controller",
        "fields": [
            {
                "name": "dll_path",
                "label": "Vendor DLL Path",
                "type": "text",
                "default": "usb_relay_device.dll",
            },
            {
                "name": "device_path",
                "label": "Physical Relay Board",
                "type": "discovery",
                "default": "",
                "discovery_driver": "seeit_usbb_native",
                "empty_label": "Scan for connected relay boards",
            },
            {
                "name": "safe_state",
                "label": "Safe State (open_all or close_all)",
                "type": "text",
                "default": "close_all",
            },
        ],
        "description": (
            "One, two, four or eight-channel USBB relay controlled directly "
            "through the vendor-supplied Windows usb_relay_device.dll. This "
            "variant does not use a COM port."
        ),
        "setup_note": (
            "Place the vendor DLL in vendor/seeit, then use Scan for Devices "
            "to select the physical relay board by its unique Windows device "
            "path. Python and the DLL must use matching architectures."
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
