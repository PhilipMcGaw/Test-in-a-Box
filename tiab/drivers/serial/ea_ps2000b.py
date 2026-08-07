"""
EA Elektro-Automatik PS 2000 B (2020 TFT) driver.

This driver uses the SCPI command set documented by EA for the 2020 TFT
generation of PS 2000 B power supplies.

Current validation status: TO BE CONFIRMED on the connected bench unit.

Documented interface behaviour:

- Communication uses the front USB virtual COM port.
- The virtual COM driver ignores conventional UART settings.
- USB does not require a command terminator; LF is supported.
- A minimum interval of 50 ms between transmissions is recommended.
- Read-only monitoring is allowed without remote mode.
- Setpoints and output control require remote mode.

The driver therefore defaults to no command terminator, reads LF-terminated
responses, and enforces a minimum inter-command delay.
"""

from __future__ import annotations

import contextlib
import re
import threading
import time
from typing import Any

from ..base import CapabilityDescriptor, Driver, Position, PositionKind
from ..registry import register_driver
from .common import decode_terminator

try:
    import serial
except ImportError:  # pragma: no cover
    serial = None


_VALUE_RE = re.compile(
    r"^\s*([+-]?(?:\d+(?:\.\d*)?|\.\d+)(?:[eE][+-]?\d+)?)"
)


def _parse_numeric_reply(reply: str) -> float:
    match = _VALUE_RE.match(reply)
    if not match:
        raise ValueError(f"Could not parse numeric instrument reply: {reply!r}")
    return float(match.group(1))


def _parse_bool_reply(reply: str) -> bool:
    value = reply.strip().upper()
    if value in {"1", "ON"}:
        return True
    if value in {"0", "OFF"}:
        return False
    raise ValueError(f"Could not parse boolean instrument reply: {reply!r}")


def _parse_idn(reply: str) -> dict[str, str]:
    parts = [part.strip() for part in reply.split(",")]
    return {
        "manufacturer": parts[0] if len(parts) > 0 else "",
        "model": parts[1] if len(parts) > 1 else "",
        "serial": parts[2] if len(parts) > 2 else "",
        "firmware": parts[3] if len(parts) > 3 else "",
        "user_text": parts[4] if len(parts) > 4 else "",
        "idn": reply.strip(),
        "driver": "ea_ps2000b",
    }


@register_driver("ea_ps2000b")
class EaPs2000bDriver(Driver):
    """SCPI driver for 2020 TFT EA PS 2000 B power supplies."""

    def __init__(
        self,
        device_id: str,
        serial_port: str,
        on_event=None,
        timeout: float = 2.0,
        command_terminator: str = "",
        reply_terminator: str = "\n",
        minimum_interval: float = 0.05,
        leave_remote_on_close: bool = False,
    ) -> None:
        super().__init__(device_id, on_event)

        self._port_name = serial_port
        self._timeout = float(timeout)
        self._command_terminator = decode_terminator(command_terminator)
        self._reply_terminator = decode_terminator(reply_terminator)
        self._minimum_interval = max(0.05, float(minimum_interval))
        self._leave_remote_on_close = bool(leave_remote_on_close)

        self._port = None
        self._identity: dict[str, str] | None = None
        self._io_lock = threading.RLock()
        self._last_command_time = 0.0

    # ------------------------------------------------------------------
    # Lifecycle
    # ------------------------------------------------------------------

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
                baudrate=9600,
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
                idn = self._query_raw("*IDN?")
                if not idn:
                    raise RuntimeError(
                        f"{self.device_id}: no response to *IDN? on "
                        f"{self._port_name}"
                    )

                self._identity = _parse_idn(idn)
                self._identity["transport"] = "usb-vcp"
                self._identity["connection"] = self._port_name
                self._connected = True
            except Exception:
                with contextlib.suppress(Exception):
                    port.close()
                self._port = None
                raise

    def close(self) -> None:
        with self._io_lock:
            if self._port is None:
                self._connected = False
                return

            if self._connected:
                with contextlib.suppress(Exception):
                    self.set_output(False)

                if not self._leave_remote_on_close:
                    with contextlib.suppress(Exception):
                        self.leave_remote()

            with contextlib.suppress(Exception):
                self._port.close()

            self._port = None
            self._connected = False

    def safe_state(self) -> None:
        """Disable the DC output and leave remote control when possible."""
        if not self._connected:
            return

        failures: list[str] = []

        try:
            self.set_output(False)
        except Exception as exc:
            failures.append(f"output off failed: {exc}")

        if not self._leave_remote_on_close:
            try:
                self.leave_remote()
            except Exception as exc:
                failures.append(f"leave remote failed: {exc}")

        if failures:
            raise RuntimeError("; ".join(failures))

    # ------------------------------------------------------------------
    # Identification and capabilities
    # ------------------------------------------------------------------

    def identify(self) -> dict[str, str]:
        identity = dict(self._identity or {})
        identity.setdefault("transport", "usb-vcp")
        identity.setdefault("connection", self._port_name)
        identity.setdefault("driver", "ea_ps2000b")
        return identity

    def capabilities(self) -> CapabilityDescriptor:
        return CapabilityDescriptor(
            device_type="ea_ps2000b",
            device_id=self.device_id,
            display_name="EA PS 2000 B (2020 TFT)",
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
                    "Current Setpoint",
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
                    "power_actual",
                    "Measured Power",
                    PositionKind.INPUT_ANALOG,
                    "W",
                ),
                Position(
                    "output",
                    "Output Enabled",
                    PositionKind.OUTPUT_DIGITAL,
                ),
            ],
        )

    # ------------------------------------------------------------------
    # Generic interface
    # ------------------------------------------------------------------

    def write(self, position_id: str, value: Any) -> None:
        actions = {
            "voltage_set": self.set_voltage,
            "current_set": self.set_current,
            "output": self.set_output,
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
            "power_actual": self.get_actual_power,
            "output": self.get_output,
        }
        try:
            return actions[position_id]()
        except KeyError as exc:
            raise KeyError(
                f"{self.device_id}: position {position_id!r} is not readable"
            ) from exc

    def query(self, raw_command: str) -> str:
        return self._query_raw(raw_command)

    # ------------------------------------------------------------------
    # Remote and output control
    # ------------------------------------------------------------------

    def enter_remote(self) -> None:
        self._write_checked("SYST:LOCK ON")
        owner = self.get_remote_owner()
        if owner != "REMOTE":
            raise RuntimeError(
                f"{self.device_id}: remote control was not acquired; "
                f"owner reply was {owner!r}"
            )
        self._emit("remote", True, None, event_type="state")

    def leave_remote(self) -> None:
        self._write_checked("SYST:LOCK OFF")
        self._emit("remote", False, None, event_type="state")

    def get_remote_owner(self) -> str:
        return self._query_raw("SYST:LOCK:OWN?").strip().upper()

    def set_output(self, enabled: Any) -> None:
        state = bool(enabled)
        if state:
            self._ensure_remote()
        self._write_checked(f"OUTP {'ON' if state else 'OFF'}")
        self._emit("output", state, None, event_type="state")

    def get_output(self) -> bool:
        value = _parse_bool_reply(self._query_raw("OUTP?"))
        self._emit("output", value, None)
        return value

    # ------------------------------------------------------------------
    # Voltage, current and power
    # ------------------------------------------------------------------

    def set_voltage(self, volts: Any) -> None:
        value = float(volts)
        if value < 0:
            raise ValueError("voltage must not be negative")
        self._ensure_remote()
        self._write_checked(f"VOLT {value:g}")
        self._emit("voltage_set", value, "V")

    def get_voltage(self) -> float:
        value = _parse_numeric_reply(self._query_raw("VOLT?"))
        self._emit("voltage_set", value, "V")
        return value

    def get_actual_voltage(self) -> float:
        value = _parse_numeric_reply(self._query_raw("MEAS:VOLT?"))
        self._emit("voltage_actual", value, "V")
        return value

    def set_current(self, amps: Any) -> None:
        value = float(amps)
        if value < 0:
            raise ValueError("current must not be negative")
        self._ensure_remote()
        self._write_checked(f"CURR {value:g}")
        self._emit("current_set", value, "A")

    def get_current(self) -> float:
        value = _parse_numeric_reply(self._query_raw("CURR?"))
        self._emit("current_set", value, "A")
        return value

    def get_actual_current(self) -> float:
        value = _parse_numeric_reply(self._query_raw("MEAS:CURR?"))
        self._emit("current_actual", value, "A")
        return value

    def get_actual_power(self) -> float:
        value = _parse_numeric_reply(self._query_raw("MEAS:POW?"))
        self._emit("power_actual", value, "W")
        return value

    def get_actual_values(self) -> dict[str, float]:
        reply = self._query_raw("MEAS:ARR?")
        parts = [part.strip() for part in reply.split(",")]
        if len(parts) != 3:
            raise ValueError(
                f"Unexpected MEAS:ARR? reply: {reply!r}"
            )
        values = {
            "voltage": _parse_numeric_reply(parts[0]),
            "current": _parse_numeric_reply(parts[1]),
            "power": _parse_numeric_reply(parts[2]),
        }
        self._emit("voltage_actual", values["voltage"], "V")
        self._emit("current_actual", values["current"], "A")
        self._emit("power_actual", values["power"], "W")
        return values

    # ------------------------------------------------------------------
    # Device limits and errors
    # ------------------------------------------------------------------

    def get_nominal_voltage(self) -> float:
        return _parse_numeric_reply(
            self._query_raw("SYST:NOM:VOLT?")
        )

    def get_nominal_current(self) -> float:
        return _parse_numeric_reply(
            self._query_raw("SYST:NOM:CURR?")
        )

    def get_nominal_power(self) -> float:
        return _parse_numeric_reply(
            self._query_raw("SYST:NOM:POW?")
        )

    def get_error(self) -> str:
        return self._query_raw("SYST:ERR?")

    def get_all_errors(self) -> str:
        return self._query_raw("SYST:ERR:ALL?")

    # ------------------------------------------------------------------
    # Low-level helpers
    # ------------------------------------------------------------------

    def _ensure_remote(self) -> None:
        if self.get_remote_owner() != "REMOTE":
            self.enter_remote()

    def _require_port(self) -> None:
        if self._port is None:
            raise RuntimeError(
                f"{self.device_id}: serial port is not open"
            )

    def _pace(self) -> None:
        elapsed = time.monotonic() - self._last_command_time
        remaining = self._minimum_interval - elapsed
        if remaining > 0:
            time.sleep(remaining)

    def _write_raw(self, command: str) -> None:
        with self._io_lock:
            self._require_port()
            self._pace()
            self._port.write(
                command.encode("ascii") + self._command_terminator
            )
            self._port.flush()
            self._last_command_time = time.monotonic()

    def _query_raw(self, command: str) -> str:
        with self._io_lock:
            self._require_port()
            self._pace()
            self._port.reset_input_buffer()
            self._port.write(
                command.encode("ascii") + self._command_terminator
            )
            self._port.flush()
            self._last_command_time = time.monotonic()
            reply = self._port.read_until(self._reply_terminator)
            return reply.decode("ascii", errors="replace").strip()

    def _write_checked(self, command: str) -> None:
        self._write_raw(command)
        error = self.get_error()
        if not error.startswith("0,"):
            raise RuntimeError(
                f"{self.device_id}: command {command!r} failed: {error}"
            )
