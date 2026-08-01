"""
Aim-TTi bench PSU driver — serial / USB virtual COM port.

Uses Aim-TTi's standard remote command set (RS232/USB, 9600 baud, 8N1),
confirmed against the official CPX400 series instruction manual. The same
command set is shared across most Aim-TTi bench PSUs (CPX400 series,
QL series, PL series, MX series, etc.) — <n> is the output number (1, or
1/2 for dual-output models).

Commands used here:
  V<n> <value>   set output <n> voltage
  I<n> <value>   set output <n> current limit
  OP<n> <0|1>    set output <n> on/off
  V<n>?          query set voltage      -> "V<n> <value>"
  I<n>?          query set current      -> "I<n> <value>"
  V<n>O?         query actual voltage   -> "<value>V"
  I<n>O?         query actual current   -> "<value>A"
  OP<n>?         query output state     -> "<0|1>"
  *IDN?          identify the instrument, used at connect() to confirm it's alive

Every command is terminated with LF (0x0A); the instrument terminates
every response with CR LF (0x0D 0x0A) — pyserial's readline() handles
that correctly using its default line-ending.
"""

from __future__ import annotations

import time
from typing import Any

from .base import CapabilityDescriptor, Driver, Position, PositionKind
from .registry import register_driver

try:
    import serial
except ImportError:  # pragma: no cover
    serial = None


@register_driver("aimtti_psu")
class AimTtiPsuDriver(Driver):
    def __init__(self, device_id: str, serial_port: str, on_event=None,
                 num_channels: int = 1, baudrate: int = 9600):
        super().__init__(device_id, on_event)
        self._port_name = serial_port
        self._baudrate = baudrate
        self._num_channels = num_channels
        self._port = None

    def connect(self) -> None:
        if serial is None:
            raise RuntimeError(
                "pyserial is not installed. `pip install pyserial` to talk "
                "to the Aim-TTi PSU."
            )
        self._port = serial.Serial(
            self._port_name, self._baudrate, timeout=2,
            bytesize=8, parity="N", stopbits=1,
        )
        # confirm it's actually there and talking before we call it connected
        idn = self._query_raw("*IDN?")
        if not idn:
            raise RuntimeError(
                f"{self.device_id}: no response to *IDN? on {self._port_name} — "
                "check the COM port and that the PSU is powered on."
            )
        self._connected = True

    def close(self) -> None:
        if self._port is not None:
            self._port.close()
        self._connected = False

    def capabilities(self) -> CapabilityDescriptor:
        positions = []
        for ch in range(1, self._num_channels + 1):
            positions.extend([
                Position(f"v{ch}", f"Set Voltage (ch{ch})", PositionKind.OUTPUT_ANALOG, "V"),
                Position(f"i{ch}", f"Set Current Limit (ch{ch})", PositionKind.OUTPUT_ANALOG, "A"),
                Position(f"output{ch}", f"Output Enable (ch{ch})", PositionKind.OUTPUT_DIGITAL),
                Position(f"v{ch}_meas", f"Measured Voltage (ch{ch})", PositionKind.INPUT_ANALOG, "V"),
                Position(f"i{ch}_meas", f"Measured Current (ch{ch})", PositionKind.INPUT_ANALOG, "A"),
            ])
        return CapabilityDescriptor(
            device_type="aimtti_psu",
            device_id=self.device_id,
            display_name="Aim-TTi PSU",
            positions=positions,
        )

    # -- low-level serial helpers ----------------------------------------
    def _write_raw(self, command: str) -> None:
        self._port.write((command + "\n").encode("ascii"))

    def _query_raw(self, command: str) -> str:
        self._port.reset_input_buffer()
        self._write_raw(command)
        response = self._port.readline().decode("ascii", errors="replace").strip()
        return response

    # -- Driver interface --------------------------------------------------
    def write(self, position_id: str, value: Any) -> None:
        if position_id.startswith("v") and not position_id.endswith("_meas"):
            ch = int(position_id[1:])
            self._write_raw(f"V{ch} {float(value)}")
        elif position_id.startswith("i") and not position_id.endswith("_meas"):
            ch = int(position_id[1:])
            self._write_raw(f"I{ch} {float(value)}")
        elif position_id.startswith("output"):
            ch = int(position_id[len("output"):])
            self._write_raw(f"OP{ch} {1 if value else 0}")
        else:
            raise KeyError(f"{self.device_id}: no such writable position '{position_id}'")
        self._emit(position_id, value, None, event_type="state")

    def read(self, position_id: str) -> Any:
        if position_id.endswith("_meas"):
            base = position_id[:-len("_meas")]
            if base.startswith("v"):
                ch = int(base[1:])
                raw = self._query_raw(f"V{ch}O?")
                value = _parse_trailing_unit(raw, "V")
                unit = "V"
            elif base.startswith("i"):
                ch = int(base[1:])
                raw = self._query_raw(f"I{ch}O?")
                value = _parse_trailing_unit(raw, "A")
                unit = "A"
            else:
                raise KeyError(f"{self.device_id}: no such position '{position_id}'")
        elif position_id.startswith("v"):
            ch = int(position_id[1:])
            raw = self._query_raw(f"V{ch}?")
            value = _parse_leading_label(raw)
            unit = "V"
        elif position_id.startswith("i"):
            ch = int(position_id[1:])
            raw = self._query_raw(f"I{ch}?")
            value = _parse_leading_label(raw)
            unit = "A"
        elif position_id.startswith("output"):
            ch = int(position_id[len("output"):])
            raw = self._query_raw(f"OP{ch}?")
            value = bool(int(raw.strip()))
            unit = None
        else:
            raise KeyError(f"{self.device_id}: no such position '{position_id}'")
        self._emit(position_id, value, unit, event_type="measurement")
        return value

    def query(self, raw_command: str) -> str:
        return self._query_raw(raw_command)


def _parse_trailing_unit(raw: str, unit_suffix: str) -> float:
    """Parse a response like '5.123V' or '0.500A' -> 5.123 / 0.5"""
    raw = raw.strip()
    if raw.endswith(unit_suffix):
        raw = raw[: -len(unit_suffix)]
    return float(raw)


def _parse_leading_label(raw: str) -> float:
    """Parse a response like 'V1 5.000' or 'I1 0.500' -> 5.0 / 0.5"""
    parts = raw.strip().split()
    return float(parts[-1])
