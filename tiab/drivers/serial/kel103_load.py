"""
KEL103 programmable electronic load driver.

Status: TO BE CONFIRMED ON CURRENT HARDWARE.

This initial implementation is based on engineering LabLogBook records. Most of
the listed normal-operation SCPI commands were previously tested, but the
current repository driver still requires fresh bench confirmation of:

- baud rate (currently assumed to be 9600);
- 8-N-1 serial framing;
- command and reply termination;
- exact reply formatting;
- behaviour of ``:MEAS?``.

``:MEAS?`` is deliberately not implemented because its meaning is not known.

Default communication assumptions, all configurable:

- 9600 baud;
- 8 data bits;
- no parity;
- 1 stop bit;
- no flow control;
- LF command and reply termination.
"""

from __future__ import annotations

import contextlib
import threading
from typing import Any

from ..base import CapabilityDescriptor, Driver, Position, PositionKind
from ..registry import register_driver

try:
    import serial
except ImportError:  # pragma: no cover
    serial = None


VALID_MODES = {
    "VOLT": "VOLT",
    "CV": "VOLT",
    "CURR": "CURR",
    "CC": "CURR",
    "RES": "RES",
    "CR": "RES",
    "POW": "POW",
    "CP": "POW",
}


def _decode_terminator(value: str) -> bytes:
    return value.encode("utf-8").decode("unicode_escape").encode("ascii")


def _parse_idn(response: str) -> dict[str, str]:
    parts = [part.strip() for part in response.split(",")]
    return {
        "manufacturer": parts[0] if len(parts) > 0 else "",
        "model": parts[1] if len(parts) > 1 else "",
        "serial": parts[2] if len(parts) > 2 else "",
        "firmware": parts[3] if len(parts) > 3 else "",
        "idn": response.strip(),
        "driver": "kel103_load",
    }


def _parse_number(response: str, suffixes: tuple[str, ...]) -> float:
    text = response.strip().upper()
    for suffix in suffixes:
        if text.endswith(suffix):
            text = text[: -len(suffix)].strip()
            break
    return float(text)


@register_driver("kel103_load")
class Kel103LoadDriver(Driver):
    """KEL103 programmable DC electronic load."""

    def __init__(
        self,
        device_id: str,
        serial_port: str,
        on_event=None,
        baudrate: int = 9600,
        timeout: float = 2.0,
        command_terminator: str = "\\n",
        reply_terminator: str = "\\n",
    ) -> None:
        super().__init__(device_id, on_event)

        self._port_name = serial_port
        self._baudrate = int(baudrate)
        self._timeout = float(timeout)
        self._command_terminator = _decode_terminator(command_terminator)
        self._reply_terminator = _decode_terminator(reply_terminator)

        self._port = None
        self._identity: dict[str, str] | None = None
        self._io_lock = threading.RLock()

    def connect(self) -> None:
        with self._io_lock:
            if self._connected:
                return

            if serial is None:
                raise RuntimeError(
                    "pyserial is not installed. Install it with "
                    "`pip install pyserial`."
                )

            port = serial.Serial(
                port=self._port_name,
                baudrate=self._baudrate,
                timeout=self._timeout,
                write_timeout=self._timeout,
                bytesize=8,
                parity="N",
                stopbits=1,
                xonxoff=False,
                rtscts=False,
                dsrdtr=False,
            )
            self._port = port

            try:
                idn = self._query_raw("*IDN?")
                if not idn:
                    raise RuntimeError(
                        f"{self.device_id}: no response to *IDN? on "
                        f"{self._port_name}. Serial settings and line "
                        "termination are still TO BE CONFIRMED."
                    )
                self._identity = _parse_idn(idn)
                self._identity["connection"] = self._port_name
                self._connected = True
            except Exception:
                with contextlib.suppress(Exception):
                    port.close()
                self._port = None
                raise

    def close(self) -> None:
        with self._io_lock:
            if self._port is not None:
                with contextlib.suppress(Exception):
                    self._port.close()
            self._port = None
            self._connected = False

    def safe_state(self) -> None:
        """Best-effort input disable."""
        if not self._connected:
            return
        self.set_input(False)

    def identify(self) -> dict[str, str]:
        identity = dict(self._identity or {})
        identity.setdefault("transport", "serial")
        identity.setdefault("connection", self._port_name)
        identity.setdefault("driver", "kel103_load")
        return identity

    def capabilities(self) -> CapabilityDescriptor:
        return CapabilityDescriptor(
            device_type="kel103_load",
            device_id=self.device_id,
            display_name="KEL103 Programmable Electronic Load",
            positions=[
                Position(
                    "input",
                    "Input Enabled",
                    PositionKind.OUTPUT_DIGITAL,
                ),
                Position(
                    "voltage_set",
                    "CV Setpoint",
                    PositionKind.OUTPUT_ANALOG,
                    "V",
                ),
                Position(
                    "voltage_actual",
                    "Measured Voltage",
                    PositionKind.INPUT_ANALOG,
                    "V",
                ),
                Position(
                    "current_set",
                    "CC Setpoint",
                    PositionKind.OUTPUT_ANALOG,
                    "A",
                ),
                Position(
                    "current_actual",
                    "Measured Current",
                    PositionKind.INPUT_ANALOG,
                    "A",
                ),
                Position(
                    "resistance_set",
                    "CR Setpoint",
                    PositionKind.OUTPUT_ANALOG,
                    "ohm",
                ),
                Position(
                    "power_set",
                    "CP Setpoint",
                    PositionKind.OUTPUT_ANALOG,
                    "W",
                ),
                Position(
                    "power_actual",
                    "Measured Power",
                    PositionKind.INPUT_ANALOG,
                    "W",
                ),
            ],
        )

    def write(self, position_id: str, value: Any) -> None:
        actions = {
            "input": self.set_input,
            "voltage_set": self.set_voltage,
            "current_set": self.set_current,
            "resistance_set": self.set_resistance,
            "power_set": self.set_power,
        }
        try:
            actions[position_id](value)
        except KeyError as exc:
            raise KeyError(
                f"{self.device_id}: position {position_id!r} is not writable"
            ) from exc

    def read(self, position_id: str) -> Any:
        actions = {
            "voltage_set": self.get_voltage,
            "voltage_actual": self.get_actual_voltage,
            "current_set": self.get_current,
            "current_actual": self.get_actual_current,
            "resistance_set": self.get_resistance,
            "power_set": self.get_power,
            "power_actual": self.get_actual_power,
        }
        try:
            return actions[position_id]()
        except KeyError as exc:
            raise KeyError(
                f"{self.device_id}: position {position_id!r} is not readable"
            ) from exc

    def query(self, raw_command: str) -> str:
        if raw_command.strip().upper() == ":MEAS?":
            raise NotImplementedError(
                ":MEAS? is deliberately unsupported because its behaviour "
                "has not yet been confirmed"
            )
        return self._query_raw(raw_command)

    def set_input(self, enabled: Any) -> None:
        state = bool(enabled)
        self._write_raw(":INP ON" if state else ":INP OFF")
        self._emit("input", state, None, event_type="state")

    def set_mode(self, mode: str) -> None:
        try:
            command_value = VALID_MODES[mode.strip().upper()]
        except KeyError as exc:
            raise ValueError(
                "mode must be one of VOLT/CV, CURR/CC, RES/CR or POW/CP"
            ) from exc
        self._write_raw(f":FUNC {command_value}")
        self._emit("function_mode", command_value, None, event_type="state")

    def get_mode(self) -> str:
        value = self._query_raw(":FUNC?").strip().upper()
        self._emit("function_mode", value, None)
        return value

    def set_voltage(self, volts: Any) -> None:
        value = float(volts)
        if value < 0:
            raise ValueError("voltage must not be negative")
        self._write_raw(f":VOLT {value:g}V")
        self._emit("voltage_set", value, "V")

    def get_voltage(self) -> float:
        value = _parse_number(self._query_raw(":VOLT?"), ("V",))
        self._emit("voltage_set", value, "V")
        return value

    def get_actual_voltage(self) -> float:
        value = _parse_number(self._query_raw(":MEAS:VOLT?"), ("V",))
        self._emit("voltage_actual", value, "V")
        return value

    def set_current(self, amps: Any) -> None:
        value = float(amps)
        if value < 0:
            raise ValueError("current must not be negative")
        self._write_raw(f":CURR {value:g}A")
        self._emit("current_set", value, "A")

    def get_current(self) -> float:
        value = _parse_number(self._query_raw(":CURR?"), ("A",))
        self._emit("current_set", value, "A")
        return value

    def get_actual_current(self) -> float:
        value = _parse_number(self._query_raw(":MEAS:CURR?"), ("A",))
        self._emit("current_actual", value, "A")
        return value

    def set_resistance(self, ohms: Any) -> None:
        value = float(ohms)
        if value < 0:
            raise ValueError("resistance must not be negative")
        self._write_raw(f":RES {value:g}OHM")
        self._emit("resistance_set", value, "ohm")

    def get_resistance(self) -> float:
        value = _parse_number(
            self._query_raw(":RES?"),
            ("OHM", "OHMS"),
        )
        self._emit("resistance_set", value, "ohm")
        return value

    def set_power(self, watts: Any) -> None:
        value = float(watts)
        if value < 0:
            raise ValueError("power must not be negative")
        self._write_raw(f":POW {value:g}W")
        self._emit("power_set", value, "W")

    def get_power(self) -> float:
        value = _parse_number(self._query_raw(":POW?"), ("W",))
        self._emit("power_set", value, "W")
        return value

    def get_actual_power(self) -> float:
        value = _parse_number(self._query_raw(":MEAS:POW?"), ("W",))
        self._emit("power_actual", value, "W")
        return value

    def get_status(self) -> str:
        value = self._query_raw(":STAT?")
        self._emit("status", value, None)
        return value

    def _require_connected(self) -> None:
        if not self._connected or self._port is None:
            raise RuntimeError(
                f"{self.device_id}: electronic load is not connected"
            )

    def _write_raw(self, command: str) -> None:
        with self._io_lock:
            self._require_connected()
            payload = command.encode("ascii") + self._command_terminator
            self._port.write(payload)
            self._port.flush()

    def _query_raw(self, command: str) -> str:
        with self._io_lock:
            if self._port is None:
                raise RuntimeError(
                    f"{self.device_id}: electronic-load serial port is not open"
                )
            self._port.reset_input_buffer()
            payload = command.encode("ascii") + self._command_terminator
            self._port.write(payload)
            self._port.flush()
            reply = self._port.read_until(self._reply_terminator)
            return reply.decode("ascii", errors="replace").strip()
