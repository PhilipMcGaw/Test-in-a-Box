"""
LAB-DCH 30-665 programmable PSU driver over RS232.

Protocol summary:

- 9600 baud, 8-N-1, no flow control;
- null-modem cable;
- commands terminated by CR or LF;
- commands are case-insensitive.

The driver uses LF termination and exposes the standard Test in a Box PSU
capabilities, so the existing PSU Blockly blocks and commissioning controls
work without a model-specific Blockly implementation.
"""

from __future__ import annotations

import contextlib
import re
import threading
import time
from typing import Any

from ..base import CapabilityDescriptor, Driver, Position, PositionKind
from ..registry import register_driver

try:
    import serial
except ImportError:  # pragma: no cover
    serial = None


_NUMERIC_RESPONSE = re.compile(
    r"^[A-Z*?]+,\s*([-+]?(?:\d+(?:\.\d*)?|\.\d+))\s*([A-Z]*)$",
    re.IGNORECASE,
)


@register_driver("labdch_30_665")
class LabDch30665Driver(Driver):
    """Driver for the LAB-DCH 30-665 RS232 power supply."""

    def __init__(
        self,
        device_id: str,
        serial_port: str,
        on_event=None,
        baudrate: int = 9600,
        timeout: float = 2.0,
        minimum_interval: float = 0.05,
        remote_on_connect: bool = True,
        local_on_close: bool = True,
        command_terminator: str = "\\n",
    ) -> None:
        super().__init__(device_id, on_event)

        self._port_name = str(serial_port)
        self._baudrate = int(baudrate)
        self._timeout = float(timeout)
        self._minimum_interval = max(0.0, float(minimum_interval))
        self._remote_on_connect = bool(remote_on_connect)
        self._local_on_close = bool(local_on_close)
        self._terminator = _decode_terminator(command_terminator)

        self._port = None
        self._io_lock = threading.RLock()
        self._last_command_time = 0.0
        self._identity: dict[str, str] = {}

    # ------------------------------------------------------------------
    # Lifecycle
    # ------------------------------------------------------------------

    def connect(self) -> None:
        if self.connected:
            return

        if serial is None:
            raise RuntimeError(
                "pyserial is not installed. Run bootstrap.bat before using "
                "the LAB-DCH 30-665 driver."
            )

        port = serial.Serial(
            port=self._port_name,
            baudrate=self._baudrate,
            bytesize=8,
            parity="N",
            stopbits=1,
            timeout=self._timeout,
            write_timeout=self._timeout,
            xonxoff=False,
            rtscts=False,
            dsrdtr=False,
        )
        self._port = port

        try:
            if self._remote_on_connect:
                self._write_raw("GTR")

            idn = self._query_identification()
            firmware = ""

            with contextlib.suppress(Exception):
                firmware = self._query_raw("*OPT?")

            self._identity = _parse_identity(idn, firmware)
            self._connected = True
        except Exception:
            with contextlib.suppress(Exception):
                port.close()
            self._port = None
            self._connected = False
            raise

    def close(self) -> None:
        if self._port is None:
            self._connected = False
            return

        if self.connected and self._local_on_close:
            with contextlib.suppress(Exception):
                self._write_raw("GTL")

        with contextlib.suppress(Exception):
            self._port.close()

        self._port = None
        self._connected = False

    def safe_state(self) -> None:
        """Disable the PSU output without changing its programmed setpoints."""
        if not self.connected:
            return

        self._write_raw("SB,S")
        self._emit("output", False, None, event_type="state")

    # ------------------------------------------------------------------
    # Identity and capabilities
    # ------------------------------------------------------------------

    def identify(self) -> dict[str, str]:
        self._require_connected()

        idn = self._query_identification()
        firmware = ""

        with contextlib.suppress(Exception):
            firmware = self._query_raw("*OPT?")

        self._identity = _parse_identity(idn, firmware)
        return dict(self._identity)

    def capabilities(self) -> CapabilityDescriptor:
        return CapabilityDescriptor(
            device_type="labdch_30_665",
            device_id=self.device_id,
            display_name="LAB-DCH 30-665 PSU",
            positions=[
                Position(
                    "voltage_set",
                    "Voltage Setpoint",
                    PositionKind.OUTPUT_ANALOG,
                    "V",
                ),
                Position(
                    "current_set",
                    "Current Limit",
                    PositionKind.OUTPUT_ANALOG,
                    "A",
                ),
                Position(
                    "output",
                    "Output Enabled",
                    PositionKind.OUTPUT_DIGITAL,
                ),
                Position(
                    "voltage_actual",
                    "Measured Voltage",
                    PositionKind.INPUT_ANALOG,
                    "V",
                ),
                Position(
                    "current_actual",
                    "Measured Current",
                    PositionKind.INPUT_ANALOG,
                    "A",
                ),
                Position(
                    "ovp",
                    "Over-voltage Protection",
                    PositionKind.OUTPUT_ANALOG,
                    "V",
                ),
            ],
        )

    # ------------------------------------------------------------------
    # Generic driver operations
    # ------------------------------------------------------------------

    def write(self, position_id: str, value: Any) -> None:
        self._require_connected()

        if position_id == "voltage_set":
            numeric = _non_negative(value, "voltage")
            self._write_raw(f"UA,{numeric:g}")
            self._emit(position_id, numeric, "V", event_type="state")
            return

        if position_id == "current_set":
            numeric = _non_negative(value, "current")
            self._write_raw(f"IA,{numeric:g}")
            self._emit(position_id, numeric, "A", event_type="state")
            return

        if position_id == "output":
            enabled = _as_bool(value)
            self._write_raw("SB,R" if enabled else "SB,S")
            self._emit(position_id, enabled, None, event_type="state")
            return

        if position_id == "ovp":
            numeric = _non_negative(value, "OVP")
            self._write_raw(f"OVP,{numeric:g}")
            self._emit(position_id, numeric, "V", event_type="state")
            return

        raise KeyError(
            f"{self.device_id}: position {position_id!r} is not writable"
        )

    def read(self, position_id: str) -> Any:
        self._require_connected()

        if position_id == "voltage_set":
            value = _parse_numeric(self._query_raw("UA"), "UA", "V")
            unit = "V"
        elif position_id == "current_set":
            value = _parse_numeric(self._query_raw("IA"), "IA", "A")
            unit = "A"
        elif position_id == "voltage_actual":
            value = _parse_numeric(self._query_raw("MU"), "MU", "V")
            unit = "V"
        elif position_id == "current_actual":
            value = _parse_numeric(self._query_raw("MI"), "MI", "A")
            unit = "A"
        elif position_id == "ovp":
            value = _parse_numeric(self._query_raw("OVP"), "OVP", "V")
            unit = "V"
        elif position_id == "output":
            value = _parse_output_state(self._query_raw("SB"))
            unit = None
        else:
            raise KeyError(
                f"{self.device_id}: position {position_id!r} is not readable"
            )

        self._emit(position_id, value, unit, event_type="measurement")
        return value

    def query(self, raw_command: str) -> str:
        """Send a raw query for diagnostics and commissioning."""
        self._require_connected()
        return self._query_raw(raw_command)

    # ------------------------------------------------------------------
    # Additional model-specific operations
    # ------------------------------------------------------------------

    def enter_remote(self) -> None:
        self._write_raw("GTR")

    def return_local(self) -> None:
        self._write_raw("GTL")

    def lock_front_panel(self) -> None:
        self._write_raw("LLO")

    def read_mode(self) -> str:
        return self._query_raw("MODE")

    def set_mode(self, mode: str) -> None:
        normalised = str(mode).strip().upper()
        if normalised not in {"UI", "UIP", "UIR", "PVSIM"}:
            raise ValueError(
                "mode must be one of UI, UIP, UIR or PVSIM"
            )
        self._write_raw(f"MODE,{normalised}")

    def read_status(self) -> str:
        return self._query_raw("STATUS")

    def read_interface_status(self) -> str:
        return self._query_raw("*STB?")

    # ------------------------------------------------------------------
    # Serial helpers
    # ------------------------------------------------------------------

    def _require_connected(self) -> None:
        if not self.connected or self._port is None:
            raise RuntimeError(
                f"{self.device_id}: LAB-DCH PSU is not connected"
            )

    def _require_port(self) -> None:
        if self._port is None:
            raise RuntimeError(
                f"{self.device_id}: serial port is not open"
            )

    def _wait_for_command_slot(self) -> None:
        elapsed = time.monotonic() - self._last_command_time
        remaining = self._minimum_interval - elapsed
        if remaining > 0:
            time.sleep(remaining)

    def _write_raw(self, command: str) -> None:
        with self._io_lock:
            self._require_port()
            self._wait_for_command_slot()

            payload = command.encode("ascii") + self._terminator
            self._port.write(payload)
            self._port.flush()
            self._last_command_time = time.monotonic()

    def _query_raw(self, command: str) -> str:
        with self._io_lock:
            self._require_port()
            self._wait_for_command_slot()

            self._port.reset_input_buffer()
            payload = command.encode("ascii") + self._terminator
            self._port.write(payload)
            self._port.flush()
            self._last_command_time = time.monotonic()

            response = self._port.readline().decode(
                "ascii",
                errors="replace",
            ).strip()

            if not response:
                raise TimeoutError(
                    f"{self.device_id}: no response to {command!r} on "
                    f"{self._port_name}; verify the COM port, null-modem "
                    "cable and 9600 8-N-1 settings."
                )

            return response

    def _query_identification(self) -> str:
        try:
            return self._query_raw("*IDN?")
        except Exception as first_error:
            try:
                return self._query_raw("ID")
            except Exception:
                raise first_error


def _decode_terminator(value: str) -> bytes:
    text = str(value)

    replacements = {
        "\\r": "\r",
        "\\n": "\n",
        "\\r\\n": "\r\n",
        "CR": "\r",
        "LF": "\n",
        "CRLF": "\r\n",
    }

    decoded = replacements.get(text.upper(), replacements.get(text, text))

    if decoded not in {"\r", "\n", "\r\n"}:
        raise ValueError(
            "command_terminator must be CR, LF, CRLF, \\\\r, \\\\n or \\\\r\\\\n"
        )

    return decoded.encode("ascii")


def _non_negative(value: Any, name: str) -> float:
    numeric = float(value)
    if numeric < 0:
        raise ValueError(f"{name} must not be negative")
    return numeric


def _as_bool(value: Any) -> bool:
    if isinstance(value, str):
        normalised = value.strip().lower()
        if normalised in {"1", "true", "on", "enabled", "enable", "r"}:
            return True
        if normalised in {"0", "false", "off", "disabled", "disable", "s"}:
            return False
        raise ValueError(f"invalid output state {value!r}")

    return bool(value)


def _parse_numeric(response: str, label: str, expected_unit: str) -> float:
    match = _NUMERIC_RESPONSE.match(response.strip())
    if not match:
        raise ValueError(
            f"could not parse {label} response {response!r}"
        )

    unit = match.group(2).upper()
    if unit and unit != expected_unit.upper():
        raise ValueError(
            f"unexpected unit in {label} response {response!r}"
        )

    return float(match.group(1))


def _parse_output_state(response: str) -> bool:
    normalised = response.strip().upper().replace(" ", "")
    if normalised == "SB,R":
        return True
    if normalised == "SB,S":
        return False
    raise ValueError(
        f"could not parse output-state response {response!r}"
    )


def _parse_identity(idn: str, firmware: str) -> dict[str, str]:
    text = idn.strip()
    model = "LAB-DCH 30-665"
    serial_number = ""

    match = re.search(
        r"(?P<model>LAB-DCH\s*30-665).*?S\.?\s*NO\.?\s*:\s*(?P<serial>.+)$",
        text,
        re.IGNORECASE,
    )
    if match:
        model = re.sub(r"\s+", " ", match.group("model")).strip()
        serial_number = match.group("serial").strip()

    return {
        "manufacturer": "LAB-DCH",
        "model": model,
        "serial": serial_number,
        "firmware": firmware.strip(),
        "idn": text,
        "transport": "RS232",
        "connection": "9600 8-N-1, null modem",
        "driver": "labdch_30_665",
    }
