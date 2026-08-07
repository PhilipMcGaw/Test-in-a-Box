"""
Aim-TTi bench PSU driver using serial or USB virtual COM port.

The driver uses Aim-TTi's standard remote command set over RS232/USB serial,
normally at 9600 baud, 8 data bits, no parity and 1 stop bit.

Commands used:

    V<n> <value>    Set output voltage.
    I<n> <value>    Set output current limit.
    OP<n> <0|1>     Set output state.
    V<n>?           Query configured voltage.
    I<n>?           Query configured current limit.
    V<n>O?          Query measured output voltage.
    I<n>O?          Query measured output current.
    OP<n>?          Query output state.
    *IDN?           Query instrument identity.

Commands are terminated with LF. Responses are read using ``readline()`` and
trimmed of their CR/LF terminator.
"""

from __future__ import annotations

import contextlib
from typing import Any, Optional

from .base import (
    CapabilityDescriptor,
    DiscoveredInstrument,
    Driver,
    Position,
    PositionKind,
)
from .registry import register_driver

try:
    import serial
    from serial.tools import list_ports
except ImportError:  # pragma: no cover
    serial = None
    list_ports = None


@register_driver("aimtti_psu")
class AimTtiPsuDriver(Driver):
    """Driver for Aim-TTi programmable bench power supplies."""

    @classmethod
    def discover(cls, **kwargs) -> list[DiscoveredInstrument]:
        """Find ports whose ``*IDN?`` response identifies an Aim-TTi PSU."""
        if serial is None or list_ports is None:
            return []

        probe_kwargs = dict(kwargs)
        probe_kwargs.pop("serial_port", None)
        results: list[DiscoveredInstrument] = []

        for port in sorted(list_ports.comports(), key=lambda item: item.device):
            probe = cls(
                device_id=f"probe:{port.device}",
                serial_port=port.device,
                on_event=None,
                **probe_kwargs,
            )
            try:
                probe.connect()
                identity = probe.identify()
                manufacturer = identity.get("manufacturer", "").strip()
                model = identity.get("model", "").strip()
                idn = identity.get("idn", "").strip()
                identity_text = f"{manufacturer} {model} {idn}".upper()
                if not (
                    "AIM-TTI" in identity_text
                    or "AIM TTI" in identity_text
                    or "THURLBY THANDAR" in identity_text
                ):
                    continue

                display_name = " — ".join(
                    part for part in (port.device, manufacturer, model) if part
                )
                results.append(
                    DiscoveredInstrument(
                        driver_type="aimtti_psu",
                        selector=port.device,
                        display_name=display_name,
                        manufacturer=manufacturer,
                        model=model,
                        serial=identity.get("serial", ""),
                        transport="RS232/USB serial",
                        connection=port.device,
                        metadata={
                            "firmware": identity.get("firmware", ""),
                            "idn": idn,
                            "port_description": port.description or "",
                            "hardware_id": port.hwid or "",
                        },
                    )
                )
            except Exception:
                continue
            finally:
                with contextlib.suppress(Exception):
                    probe.close()

        return results

    def __init__(
        self,
        device_id: str,
        serial_port: str,
        on_event=None,
        num_channels: int = 1,
        baudrate: int = 9600,
    ) -> None:
        super().__init__(device_id, on_event)

        if num_channels < 1:
            raise ValueError("num_channels must be at least 1")

        self._port_name = serial_port
        self._baudrate = int(baudrate)
        self._num_channels = int(num_channels)
        self._port = None
        self._identity: Optional[dict[str, str]] = None
        self._capabilities = self._build_capabilities()

    # ------------------------------------------------------------------
    # Lifecycle
    # ------------------------------------------------------------------

    def connect(self) -> None:
        """Open the serial connection and verify the instrument responds."""
        if self.connected:
            return

        if serial is None:
            raise RuntimeError(
                "pyserial is not installed. Install it with "
                "`pip install pyserial` to use the Aim-TTi PSU driver."
            )

        port = serial.Serial(
            self._port_name,
            self._baudrate,
            timeout=2,
            bytesize=8,
            parity="N",
            stopbits=1,
        )
        self._port = port

        try:
            identity = self._query_raw("*IDN?")
            if not identity:
                raise RuntimeError(
                    f"{self.device_id}: no response to *IDN? on "
                    f"{self._port_name}; check the COM port and that the "
                    "instrument is powered on."
                )

            self._identity = _parse_idn(identity)
            self._connected = True
            # Rebuild capabilities now that model-specific features are known.
            self._capabilities = self._build_capabilities()

        except Exception:
            with contextlib.suppress(Exception):
                port.close()
            self._port = None
            self._connected = False
            raise

    def close(self) -> None:
        """Close the serial connection. Safe to call more than once."""
        if self._port is not None:
            with contextlib.suppress(Exception):
                self._port.close()

        self._port = None
        self._connected = False

    def safe_state(self) -> None:
        """
        Disable every configured output.

        Each channel is attempted independently so one communication error does
        not prevent the remaining outputs from being switched off.
        """
        if not self.connected:
            return

        failures: list[str] = []

        for channel in range(1, self._num_channels + 1):
            try:
                self._write_raw(f"OP{channel} 0")
                self._emit(
                    f"output{channel}",
                    False,
                    None,
                    event_type="state",
                )
            except Exception as exc:
                failures.append(f"channel {channel}: {exc}")

        if failures:
            raise RuntimeError(
                f"{self.device_id}: failed to disable one or more outputs: "
                + "; ".join(failures)
            )

    # ------------------------------------------------------------------
    # Identification and capabilities
    # ------------------------------------------------------------------

    def identify(self) -> dict[str, str]:
        """Return parsed instrument identity information."""
        self._require_connected()

        identity = self._query_raw("*IDN?")
        self._identity = _parse_idn(identity)
        return dict(self._identity)

    def capabilities(self) -> CapabilityDescriptor:
        return self._capabilities

    def _build_capabilities(self) -> CapabilityDescriptor:
        positions: list[Position] = []

        for channel in range(1, self._num_channels + 1):
            positions.extend([
                Position(
                    f"v{channel}",
                    f"Set Voltage (ch{channel})",
                    PositionKind.OUTPUT_ANALOG,
                    "V",
                ),
                Position(
                    f"i{channel}",
                    f"Set Current Limit (ch{channel})",
                    PositionKind.OUTPUT_ANALOG,
                    "A",
                ),
                Position(
                    f"output{channel}",
                    f"Output Enable (ch{channel})",
                    PositionKind.OUTPUT_DIGITAL,
                ),
                Position(
                    f"v{channel}_meas",
                    f"Measured Voltage (ch{channel})",
                    PositionKind.INPUT_ANALOG,
                    "V",
                ),
                Position(
                    f"i{channel}_meas",
                    f"Measured Current (ch{channel})",
                    PositionKind.INPUT_ANALOG,
                    "A",
                ),
            ])

        # The QL355P provides three selectable operating ranges. RANGE1 is
        # readable and writable, and changing it causes the PSU itself to turn
        # the output off.
        if self._is_ql355p():
            positions.append(
                Position(
                    "range1",
                    "Voltage Range",
                    PositionKind.OUTPUT_ANALOG,
                )
            )

        return CapabilityDescriptor(
            device_type="aimtti_psu",
            device_id=self.device_id,
            display_name="Aim-TTi PSU",
            positions=positions,
        )

    def _is_ql355p(self) -> bool:
        """Return True when the connected instrument identifies as a QL355P."""
        if not self._identity:
            return False

        return self._identity.get("model", "").strip().upper() == "QL355P"

    # ------------------------------------------------------------------
    # Low-level serial helpers
    # ------------------------------------------------------------------

    def _require_port_open(self) -> None:
        if self._port is None:
            raise RuntimeError(
                f"{self.device_id}: serial port is not open"
            )

    def _require_connected(self) -> None:
        if not self.connected or self._port is None:
            raise RuntimeError(
                f"{self.device_id}: instrument is not connected"
            )

    def _write_raw(self, command: str) -> None:
        self._require_port_open()
        self._port.write((command + "\n").encode("ascii"))

    def _query_raw(self, command: str) -> str:
        self._require_port_open()

        self._port.reset_input_buffer()
        self._write_raw(command)

        response = (
            self._port.readline()
            .decode("ascii", errors="replace")
            .strip()
        )

        if not response:
            raise TimeoutError(
                f"{self.device_id}: no response to {command!r}"
            )

        return response

    # ------------------------------------------------------------------
    # Driver interface
    # ------------------------------------------------------------------

    def write(self, position_id: str, value: Any) -> None:
        self._require_connected()

        if position_id == "range1":
            if not self._is_ql355p():
                raise KeyError(
                    f"{self.device_id}: voltage range selection is not "
                    "available for this instrument"
                )

            range_value = _normalise_ql355p_range(value)
            self._write_raw(f"RANGE1 {range_value}")

            # The QL355P disables its output when the range is changed.
            self._emit("range1", range_value, None, event_type="state")
            self._emit("output1", False, None, event_type="state")
            return

        if position_id.startswith("v") and not position_id.endswith("_meas"):
            channel = self._parse_channel(position_id, "v")
            numeric_value = float(value)
            self._write_raw(f"V{channel} {numeric_value}")
            self._emit(position_id, numeric_value, "V", event_type="state")
            return

        if position_id.startswith("i") and not position_id.endswith("_meas"):
            channel = self._parse_channel(position_id, "i")
            numeric_value = float(value)
            self._write_raw(f"I{channel} {numeric_value}")
            self._emit(position_id, numeric_value, "A", event_type="state")
            return

        if position_id.startswith("output"):
            channel = self._parse_channel(position_id, "output")
            enabled = bool(value)
            self._write_raw(f"OP{channel} {1 if enabled else 0}")
            self._emit(position_id, enabled, None, event_type="state")
            return

        raise KeyError(
            f"{self.device_id}: no such writable position "
            f"{position_id!r}"
        )

    def read(self, position_id: str) -> Any:
        self._require_connected()

        if position_id == "range1":
            if not self._is_ql355p():
                raise KeyError(
                    f"{self.device_id}: voltage range selection is not "
                    "available for this instrument"
                )

            raw = self._query_raw("RANGE1?")
            value = _parse_range_response(raw)
            unit = None

        elif position_id.endswith("_meas"):
            base = position_id[:-len("_meas")]

            if base.startswith("v"):
                channel = self._parse_channel(base, "v")
                raw = self._query_raw(f"V{channel}O?")
                value = _parse_trailing_unit(raw, "V")
                unit = "V"

            elif base.startswith("i"):
                channel = self._parse_channel(base, "i")
                raw = self._query_raw(f"I{channel}O?")
                value = _parse_trailing_unit(raw, "A")
                unit = "A"

            else:
                raise KeyError(
                    f"{self.device_id}: no such position {position_id!r}"
                )

        elif position_id.startswith("v"):
            channel = self._parse_channel(position_id, "v")
            raw = self._query_raw(f"V{channel}?")
            value = _parse_leading_label(raw)
            unit = "V"

        elif position_id.startswith("i"):
            channel = self._parse_channel(position_id, "i")
            raw = self._query_raw(f"I{channel}?")
            value = _parse_leading_label(raw)
            unit = "A"

        elif position_id.startswith("output"):
            channel = self._parse_channel(position_id, "output")
            raw = self._query_raw(f"OP{channel}?")

            try:
                value = bool(int(raw.strip()))
            except ValueError as exc:
                raise ValueError(
                    f"{self.device_id}: invalid output-state response "
                    f"{raw!r}"
                ) from exc

            unit = None

        else:
            raise KeyError(
                f"{self.device_id}: no such position {position_id!r}"
            )

        self._emit(
            position_id,
            value,
            unit,
            event_type="measurement",
        )
        return value

    def query(self, raw_command: str) -> str:
        """Send a raw instrument query."""
        self._require_connected()
        return self._query_raw(raw_command)

    def _parse_channel(self, position_id: str, prefix: str) -> int:
        suffix = position_id[len(prefix):]

        if not suffix.isdigit():
            raise KeyError(
                f"{self.device_id}: invalid position {position_id!r}"
            )

        channel = int(suffix)

        if channel < 1 or channel > self._num_channels:
            raise KeyError(
                f"{self.device_id}: channel {channel} is outside the "
                f"configured range 1..{self._num_channels}"
            )

        return channel


def _normalise_ql355p_range(value: Any) -> int:
    """
    Convert a QL355P range selection to the instrument's numeric code.

    Accepted values:

    - 0 or "15V/5A"
    - 1 or "35V/3A"
    - 2 or "35V/0.5A"
    """
    labels = {
        "15V/5A": 0,
        "15 V / 5 A": 0,
        "35V/3A": 1,
        "35 V / 3 A": 1,
        "35V/0.5A": 2,
        "35 V / 0.5 A": 2,
        "35V/500MA": 2,
        "35 V / 500 MA": 2,
    }

    if isinstance(value, str):
        normalised = value.strip().upper()
        if normalised in labels:
            return labels[normalised]

    try:
        numeric = int(value)
    except (TypeError, ValueError) as exc:
        raise ValueError(
            f"invalid QL355P range {value!r}; expected 0, 1 or 2"
        ) from exc

    if numeric not in (0, 1, 2):
        raise ValueError(
            f"invalid QL355P range {numeric}; expected 0, 1 or 2"
        )

    return numeric


def _parse_range_response(raw: str) -> int:
    """Parse a response such as ``RANGE1 1`` or ``1``."""
    parts = raw.strip().split()

    if not parts:
        raise ValueError("empty range response")

    try:
        value = int(parts[-1])
    except ValueError as exc:
        raise ValueError(
            f"could not parse range response {raw!r}"
        ) from exc

    if value not in (0, 1, 2):
        raise ValueError(
            f"unexpected QL355P range response {raw!r}"
        )

    return value


def _parse_idn(raw: str) -> dict[str, str]:
    """Parse a conventional comma-separated *IDN? response."""
    fields = [field.strip() for field in raw.split(",")]

    return {
        "manufacturer": fields[0] if len(fields) > 0 else "",
        "model": fields[1] if len(fields) > 1 else "",
        "serial": fields[2] if len(fields) > 2 else "",
        "firmware": fields[3] if len(fields) > 3 else "",
        "idn": raw.strip(),
    }


def _parse_trailing_unit(raw: str, unit_suffix: str) -> float:
    """Parse a response such as ``5.123V`` or ``0.500A``."""
    value = raw.strip()

    if value.endswith(unit_suffix):
        value = value[:-len(unit_suffix)]

    try:
        return float(value)
    except ValueError as exc:
        raise ValueError(
            f"could not parse numeric response {raw!r}"
        ) from exc


def _parse_leading_label(raw: str) -> float:
    """Parse a response such as ``V1 5.000`` or ``I1 0.500``."""
    parts = raw.strip().split()

    if not parts:
        raise ValueError("empty instrument response")

    try:
        return float(parts[-1])
    except ValueError as exc:
        raise ValueError(
            f"could not parse numeric response {raw!r}"
        ) from exc
