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
from pathlib import Path
import re
import threading
import time
from typing import Any

from ..base import (
    CapabilityDescriptor,
    DiscoveredInstrument,
    Driver,
    Position,
    PositionKind,
)
from ..registry import register_driver
from .common import decode_terminator

try:
    import serial
    from serial.tools import list_ports
except ImportError:  # pragma: no cover
    serial = None
    list_ports = None


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
        trace_serial: bool = True,
        select_ui_mode_on_enable: bool = True,
        verify_output_state: bool = True,
        output_standby_delay: float = 5.0,
        output_settle_delay: float = 2.0,
        output_enable_attempts: int = 2,
        verify_output_voltage: bool = True,
        output_verify_timeout: float = 4.0,
        output_verify_interval: float = 0.25,
        output_verify_ratio: float = 0.8,
        output_second_enable_delay: float = 2.0,
        enable_trace: bool = True,
        enable_trace_path: str = "logs/labdch_trace.log",
        trace_status_registers: bool = True,
    ) -> None:
        super().__init__(device_id, on_event)

        self._port_name = str(serial_port)
        self._baudrate = int(baudrate)
        self._timeout = float(timeout)
        self._minimum_interval = max(0.0, float(minimum_interval))
        self._remote_on_connect = bool(remote_on_connect)
        self._local_on_close = bool(local_on_close)
        self._terminator = _decode_terminator(command_terminator)
        self._trace_serial = bool(trace_serial)
        self._select_ui_mode_on_enable = bool(select_ui_mode_on_enable)
        self._verify_output_state = bool(verify_output_state)
        self._output_standby_delay = max(
            0.0,
            float(output_standby_delay),
        )
        self._output_settle_delay = max(
            0.0,
            float(output_settle_delay),
        )
        self._output_enable_attempts = max(
            1,
            int(output_enable_attempts),
        )
        self._verify_output_voltage = bool(verify_output_voltage)
        self._output_verify_timeout = max(
            0.1,
            float(output_verify_timeout),
        )
        self._output_verify_interval = max(
            0.05,
            float(output_verify_interval),
        )
        self._output_verify_ratio = min(
            1.0,
            max(0.1, float(output_verify_ratio)),
        )
        self._output_second_enable_delay = max(
            0.0,
            float(output_second_enable_delay),
        )
        self._enable_trace = bool(enable_trace)
        self._enable_trace_path = str(enable_trace_path)
        self._trace_status_registers = bool(trace_status_registers)
        self._enable_trace_started = 0.0
        self._enable_trace_previous = 0.0

        self._port = None
        self._io_lock = threading.RLock()
        self._last_command_time = 0.0
        self._identity: dict[str, str] = {}

    @classmethod
    def discover(cls, **kwargs: Any) -> list[DiscoveredInstrument]:
        """
        Find LAB-DCH supplies by probing the currently enumerated COM ports.

        Protocol knowledge stays in the driver: each candidate is opened using
        the configured serial settings, then identified with *IDN? and the
        documented ID fallback.
        """
        if serial is None or list_ports is None:
            return []

        probe_kwargs = dict(kwargs)
        probe_kwargs.pop("serial_port", None)
        probe_kwargs["trace_serial"] = False
        probe_kwargs["local_on_close"] = True

        results: list[DiscoveredInstrument] = []

        for port in sorted(
            list_ports.comports(),
            key=lambda item: item.device,
        ):
            probe = cls(
                device_id=f"probe:{port.device}",
                serial_port=port.device,
                on_event=None,
                **probe_kwargs,
            )

            try:
                probe.connect()
                identity = probe.identify()

                model = identity.get("model", "").strip()
                idn = identity.get("idn", "").strip().upper()

                if "LAB-DCH" not in idn and "LAB-DCH" not in model.upper():
                    continue

                display_parts = [
                    port.device,
                    identity.get("manufacturer", "").strip(),
                    model,
                ]
                display_name = " — ".join(
                    part for part in display_parts if part
                )

                results.append(
                    DiscoveredInstrument(
                        driver_type="labdch_30_665",
                        selector=port.device,
                        display_name=display_name,
                        manufacturer=identity.get("manufacturer", ""),
                        model=model,
                        serial=identity.get("serial", ""),
                        transport="RS232",
                        connection=port.device,
                        metadata={
                            "firmware": identity.get("firmware", ""),
                            "idn": identity.get("idn", ""),
                            "port_description": port.description or "",
                            "hardware_id": port.hwid or "",
                        },
                    )
                )
            except Exception:
                # A failed probe simply means that this port is busy,
                # incompatible, or not responding with the LAB-DCH protocol.
                continue
            finally:
                with contextlib.suppress(Exception):
                    probe.close()

        return results

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

            if enabled:
                self._enable_output_stage()
            else:
                self._write_raw("SB,S")
                self._wait_seconds(self._output_settle_delay)

                if self._verify_output_state:
                    actual = _parse_output_state(self._query_raw("SB"))
                    if actual:
                        raise RuntimeError(
                            f"{self.device_id}: output disable was requested, "
                            "but SB readback still reports enabled"
                        )

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

    def write_command(self, raw_command: str) -> None:
        """Send a raw write-only command without waiting for a response."""
        self._require_connected()
        self._write_raw(raw_command)

    def _wait_seconds(self, seconds: float) -> None:
        if seconds > 0:
            time.sleep(seconds)

    def _ensure_ui_mode(self) -> None:
        if not self._select_ui_mode_on_enable:
            return

        current_mode = self._query_raw("MODE").strip().upper()
        if current_mode == "MODE,UI":
            return

        self._write_raw("MODE,UI")
        self._wait_seconds(self._output_settle_delay)

        confirmed_mode = self._query_raw("MODE").strip().upper()
        if confirmed_mode != "MODE,UI":
            raise RuntimeError(
                f"{self.device_id}: could not select UI mode; "
                f"MODE readback was {confirmed_mode!r}"
            )

    def _enable_output_stage(self) -> None:
        """
        Energise the physical output using the timing observed to work manually.

        The primary sequence is:
            SB,S
            long standby dwell
            SB,R
            settle
            verify SB + MU

        A second SB,R is sent only when the first enable did not produce a
        physical output. This mirrors the successful manual commissioning
        sequence while avoiding unnecessary duplicate enables.
        """
        self._start_enable_trace()

        try:
            self._ensure_ui_mode()

            target_voltage = _parse_numeric(
                self._query_raw("UA"),
                "UA",
                "V",
            )
            self._trace_enable_event(
                "INFO",
                f"target_voltage={target_voltage:g} V",
            )

            self._trace_status_snapshot("before-standby")

            self._write_raw("SB,S")
            self._trace_enable_event(
                "WAIT",
                f"standby dwell {self._output_standby_delay:.3f} s",
            )
            self._wait_seconds(self._output_standby_delay)

            self._trace_status_snapshot("after-standby")

            measured_voltage = 0.0
            state_enabled = False

            for attempt in range(1, self._output_enable_attempts + 1):
                self._trace_enable_event(
                    "INFO",
                    f"enable attempt {attempt}/{self._output_enable_attempts}",
                )
                self._write_raw("SB,R")

                settle = (
                    self._output_settle_delay
                    if attempt == 1
                    else self._output_second_enable_delay
                )

                self._trace_enable_event(
                    "WAIT",
                    f"enable settle {settle:.3f} s",
                )
                self._wait_seconds(settle)

                self._trace_status_snapshot(
                    f"after-enable-attempt-{attempt}"
                )

                deadline = time.monotonic() + self._output_verify_timeout
                poll_number = 0

                while True:
                    poll_number += 1

                    state_enabled = _parse_output_state(
                        self._query_raw("SB")
                    )
                    measured_voltage = _parse_numeric(
                        self._query_raw("MU"),
                        "MU",
                        "V",
                    )

                    status = ""
                    stb = ""
                    if self._trace_status_registers:
                        status, stb = self._trace_status_snapshot(
                            f"attempt={attempt} poll={poll_number}"
                        )

                    self._trace_enable_event(
                        "STATE",
                        (
                            f"attempt={attempt} "
                            f"poll={poll_number} "
                            f"SB={'R' if state_enabled else 'S'} "
                            f"MU={measured_voltage:g} V"
                            + (f" {status} {stb}" if status or stb else "")
                        ),
                    )

                    if self._output_is_energised(
                        target_voltage,
                        measured_voltage,
                        state_enabled,
                    ):
                        self._stop_enable_trace(
                            (
                                f"success attempt={attempt} "
                                f"target={target_voltage:g} V "
                                f"measured={measured_voltage:g} V "
                                f"SB={'R' if state_enabled else 'S'}"
                            )
                        )
                        return

                    if time.monotonic() >= deadline:
                        break

                    self._trace_enable_event(
                        "WAIT",
                        (
                            f"verify poll interval "
                            f"{self._output_verify_interval:.3f} s"
                        ),
                    )
                    self._wait_seconds(self._output_verify_interval)

                if attempt < self._output_enable_attempts:
                    self._trace_enable_event(
                        "INFO",
                        "first enable did not energise output; retrying SB,R",
                    )

            message = (
                f"{self.device_id}: output-enable sequence completed but the "
                f"power stage did not energise; target={target_voltage:g} V, "
                f"measured={measured_voltage:g} V, SB="
                f"{'R' if state_enabled else 'S'}"
            )
            self._stop_enable_trace(
                (
                    f"failure target={target_voltage:g} V "
                    f"measured={measured_voltage:g} V "
                    f"SB={'R' if state_enabled else 'S'}"
                )
            )
            raise RuntimeError(message)

        except Exception as exc:
            if self._enable_trace_started > 0:
                self._stop_enable_trace(
                    f"exception {type(exc).__name__}: {exc}"
                )
            raise

    def _output_is_energised(
        self,
        target_voltage: float,
        measured_voltage: float,
        state_enabled: bool,
    ) -> bool:
        if self._verify_output_state and not state_enabled:
            return False

        if not self._verify_output_voltage:
            return True

        # A zero-volt setpoint cannot be verified by MU. SB readback is the
        # only meaningful check in that case.
        if abs(target_voltage) < 0.05:
            return state_enabled

        minimum_expected = max(
            0.05,
            abs(target_voltage) * self._output_verify_ratio,
        )
        return abs(measured_voltage) >= minimum_expected

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

    def _trace(self, direction: str, payload: str) -> None:
        if not self._trace_serial:
            return

        print(
            f"[LAB-DCH:{self.device_id}] {direction}: {payload}",
            flush=True,
        )

        if self._enable_trace_started > 0:
            self._trace_enable_event(direction, payload)

    def _trace_enable_event(self, direction: str, payload: str) -> None:
        if not self._enable_trace:
            return

        now = time.monotonic()
        elapsed_ms = int((now - self._enable_trace_started) * 1000)
        delta_ms = int((now - self._enable_trace_previous) * 1000)
        self._enable_trace_previous = now

        line = (
            f"+{elapsed_ms:05d} ms "
            f"(+{delta_ms:04d}) "
            f"{direction}: {payload}"
        )

        print(
            f"[LAB-DCH-ENABLE:{self.device_id}] {line}",
            flush=True,
        )

        try:
            path = Path(self._enable_trace_path)
            if not path.is_absolute():
                path = Path.cwd() / path
            path.parent.mkdir(parents=True, exist_ok=True)

            with path.open("a", encoding="utf-8", newline="\n") as handle:
                handle.write(
                    f"{time.strftime('%Y-%m-%d %H:%M:%S')} "
                    f"{self.device_id} {line}\n"
                )
        except Exception as exc:
            print(
                f"[LAB-DCH-ENABLE:{self.device_id}] "
                f"trace-file write failed: {exc}",
                flush=True,
            )

    def _trace_status_snapshot(self, label: str) -> tuple[str, str]:
        if not self._trace_status_registers:
            return "", ""

        status = self._query_raw("STATUS")
        stb = self._query_raw("*STB?")
        self._trace_enable_event(
            "REGS",
            f"{label} {status} {stb}",
        )
        return status, stb

    def _start_enable_trace(self) -> None:
        if not self._enable_trace:
            self._enable_trace_started = 0.0
            self._enable_trace_previous = 0.0
            return

        now = time.monotonic()
        self._enable_trace_started = now
        self._enable_trace_previous = now

        self._trace_enable_event(
            "BEGIN",
            "output enable sequence",
        )

    def _stop_enable_trace(self, outcome: str) -> None:
        if self._enable_trace_started <= 0:
            return

        self._trace_enable_event("END", outcome)
        self._enable_trace_started = 0.0
        self._enable_trace_previous = 0.0

    def _write_raw(self, command: str) -> None:
        with self._io_lock:
            self._require_port()
            self._wait_for_command_slot()

            self._trace("TX", command)
            payload = command.encode("ascii") + self._terminator
            self._port.write(payload)
            self._port.flush()
            self._last_command_time = time.monotonic()

    def _query_raw(self, command: str) -> str:
        with self._io_lock:
            self._require_port()
            self._wait_for_command_slot()

            self._port.reset_input_buffer()
            self._trace("TX", command)
            payload = command.encode("ascii") + self._terminator
            self._port.write(payload)
            self._port.flush()
            self._last_command_time = time.monotonic()

            response = self._port.readline().decode(
                "ascii",
                errors="replace",
            ).strip()

            self._trace("RX", response or "<timeout>")

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

    return decode_terminator(decoded)


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
