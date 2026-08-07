"""
Korad/Tenma programmable PSU family driver.

Status: TO BE CONFIRMED ON CURRENT HARDWARE.

This initial implementation is based on engineering LabLogBook records from
physical Korad and Tenma supplies that share the same command set.

Confirmed previously in the LabLogBook:

- Tenma 72-2540
- Korad KA3005P
- Korad KA6003P

The current repository implementation still requires fresh bench confirmation
of serial settings, line termination and reply formatting before its validation
status can be changed from ``unverified``.

Default communication assumptions, all configurable:

- 9600 baud;
- 8 data bits;
- no parity;
- 1 stop bit;
- no flow control;
- LF command and reply termination.

Only single-output operation is implemented. Multi-output behaviour, including
the Korad KA3305P, is deliberately not inferred.
"""

from __future__ import annotations

import contextlib
import threading
from typing import Any

from ..base import CapabilityDescriptor, Driver, Position, PositionKind
from ..registry import register_driver
from .common import decode_terminator

try:
    import serial
except ImportError:  # pragma: no cover
    serial = None


def _parse_idn(response: str) -> dict[str, str]:
    parts = [part.strip() for part in response.split(",")]
    return {
        "manufacturer": parts[0] if len(parts) > 0 else "",
        "model": parts[1] if len(parts) > 1 else "",
        "serial": parts[2] if len(parts) > 2 else "",
        "firmware": parts[3] if len(parts) > 3 else "",
        "idn": response.strip(),
        "driver": "korad_tenma_psu",
    }


def _parse_number(response: str, suffixes: tuple[str, ...] = ()) -> float:
    text = response.strip().upper()
    for suffix in suffixes:
        if text.endswith(suffix):
            text = text[: -len(suffix)].strip()
            break
    return float(text)


@register_driver("korad_tenma_psu")
class KoradTenmaPsuDriver(Driver):
    """Single-output Korad/Tenma compatible programmable PSU."""

    def __init__(
        self,
        device_id: str,
        serial_port: str,
        on_event=None,
        baudrate: int = 9600,
        timeout: float = 2.0,
        command_terminator: str = "\\n",
        reply_terminator: str = "\\n",
        model_hint: str = "",
        max_voltage: float | None = None,
        max_current: float | None = None,
    ) -> None:
        super().__init__(device_id, on_event)

        self._port_name = serial_port
        self._baudrate = int(baudrate)
        self._timeout = float(timeout)
        self._command_terminator = decode_terminator(command_terminator)
        self._reply_terminator = decode_terminator(reply_terminator)
        self._model_hint = model_hint.strip()
        self._max_voltage = (
            float(max_voltage) if max_voltage is not None else None
        )
        self._max_current = (
            float(max_current) if max_current is not None else None
        )

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
        """Best-effort output disable."""
        if not self._connected:
            return
        self.set_output(False)

    def identify(self) -> dict[str, str]:
        identity = dict(self._identity or {})
        if self._model_hint and not identity.get("model"):
            identity["model"] = self._model_hint
        identity.setdefault("transport", "serial")
        identity.setdefault("connection", self._port_name)
        identity.setdefault("driver", "korad_tenma_psu")
        return identity

    def capabilities(self) -> CapabilityDescriptor:
        return CapabilityDescriptor(
            device_type="korad_tenma_psu",
            device_id=self.device_id,
            display_name=(
                f"Korad/Tenma PSU ({self._model_hint})"
                if self._model_hint
                else "Korad/Tenma Programmable PSU"
            ),
            positions=[
                Position(
                    "voltage_set",
                    "Voltage Setpoint",
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
                    "Current Limit",
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
                    "output",
                    "Output Enabled",
                    PositionKind.OUTPUT_DIGITAL,
                ),
                Position(
                    "ovp",
                    "Over-voltage Protection",
                    PositionKind.OUTPUT_DIGITAL,
                ),
                Position(
                    "ocp",
                    "Over-current Protection",
                    PositionKind.OUTPUT_DIGITAL,
                ),
            ],
        )

    def write(self, position_id: str, value: Any) -> None:
        actions = {
            "voltage_set": self.set_voltage,
            "current_set": self.set_current,
            "output": self.set_output,
            "ovp": self.set_ovp,
            "ocp": self.set_ocp,
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
        }
        try:
            return actions[position_id]()
        except KeyError as exc:
            raise KeyError(
                f"{self.device_id}: position {position_id!r} is not readable"
            ) from exc

    def query(self, raw_command: str) -> str:
        return self._query_raw(raw_command)

    def set_output(self, enabled: Any) -> None:
        state = bool(enabled)
        self._write_raw("OUT1" if state else "OUT0")
        self._emit("output", state, None, event_type="state")

    def set_voltage(self, volts: Any) -> None:
        value = float(volts)
        if value < 0:
            raise ValueError("voltage must not be negative")
        if self._max_voltage is not None and value > self._max_voltage:
            raise ValueError(
                f"requested voltage {value} V exceeds configured model limit "
                f"{self._max_voltage} V"
            )
        self._write_raw(f"VSET1:{value:g}")
        self._emit("voltage_set", value, "V")

    def get_voltage(self) -> float:
        value = _parse_number(self._query_raw("VSET1?"), ("V",))
        self._emit("voltage_set", value, "V")
        return value

    def get_actual_voltage(self) -> float:
        value = _parse_number(self._query_raw("VOUT1?"), ("V",))
        self._emit("voltage_actual", value, "V")
        return value

    def set_current(self, amps: Any) -> None:
        value = float(amps)
        if value < 0:
            raise ValueError("current must not be negative")
        if self._max_current is not None and value > self._max_current:
            raise ValueError(
                f"requested current {value} A exceeds configured model limit "
                f"{self._max_current} A"
            )
        self._write_raw(f"ISET1:{value:g}")
        self._emit("current_set", value, "A")

    def get_current(self) -> float:
        value = _parse_number(self._query_raw("ISET1?"), ("A",))
        self._emit("current_set", value, "A")
        return value

    def get_actual_current(self) -> float:
        value = _parse_number(self._query_raw("IOUT1?"), ("A",))
        self._emit("current_actual", value, "A")
        return value

    def set_ovp(self, enabled: Any) -> None:
        state = bool(enabled)
        self._write_raw("OVP1" if state else "OVP0")
        self._emit("ovp", state, None, event_type="state")

    def set_ocp(self, enabled: Any) -> None:
        state = bool(enabled)
        self._write_raw("OCP1" if state else "OCP0")
        self._emit("ocp", state, None, event_type="state")

    def _require_connected(self) -> None:
        if not self._connected or self._port is None:
            raise RuntimeError(
                f"{self.device_id}: PSU is not connected"
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
                    f"{self.device_id}: PSU serial port is not open"
                )
            self._port.reset_input_buffer()
            payload = command.encode("ascii") + self._command_terminator
            self._port.write(payload)
            self._port.flush()
            reply = self._port.read_until(self._reply_terminator)
            return reply.decode("ascii", errors="replace").strip()
