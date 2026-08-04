"""
Serial driver for the Seeit USB-RELAY08.

This driver is for the USB-RELAY08 variant that appears in Windows as a
virtual COM port through a Prolific PL2303 USB-to-serial converter.

Protocol used by the current implementation:

- ``P`` requests the board identifier;
- ``Q`` enters command mode;
- one state-mask byte controls all eight relays;
- a cleared bit means relay ON;
- a set bit means relay OFF.

The command set was adapted from a community implementation because a public
vendor protocol document was not available. Confirm the behaviour against the
physical board before relying on it for unattended or safety-related testing.
"""

from __future__ import annotations

import threading
import time
from typing import Any

from ..base import CapabilityDescriptor, Driver, Position, PositionKind
from ..registry import register_driver

try:
    import serial
except ImportError:  # pragma: no cover - optional dependency
    serial = None


NUM_CHANNELS = 8
GET_BOARD_ID = b"P"
SET_COMMAND_MODE = b"Q"
ALL_OFF_MASK = 0xFF


@register_driver("seeit_relay08")
class SeeitRelay08SerialDriver(Driver):
    """Seeit eight-channel relay driver using a virtual serial COM port."""

    def __init__(
        self,
        device_id: str,
        serial_port: str,
        on_event=None,
        baudrate: int = 9600,
    ) -> None:
        super().__init__(device_id, on_event)
        self._port_name = serial_port
        self._baudrate = int(baudrate)
        self._port = None
        self._state_mask = ALL_OFF_MASK
        self._io_lock = threading.RLock()
        self._board_id: int | None = None

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
                self._port_name,
                self._baudrate,
                timeout=1,
            )

            try:
                port.write(GET_BOARD_ID)
                time.sleep(0.2)
                reply = port.read(1)
                self._board_id = reply[0] if reply else None

                port.write(SET_COMMAND_MODE)
                time.sleep(0.2)

                self._port = port
                self._connected = True
            except Exception:
                port.close()
                raise

    def close(self) -> None:
        with self._io_lock:
            if self._port is not None:
                self._port.close()
            self._port = None
            self._connected = False

    def safe_state(self) -> None:
        """Return every relay to the driver's all-off state."""
        self.all_off()

    def identify(self) -> dict[str, str]:
        board_id = (
            str(self._board_id)
            if self._board_id is not None
            else ""
        )
        return {
            "manufacturer": "Seeit",
            "model": "USB-RELAY08",
            "serial": "",
            "firmware": "",
            "idn": f"SEEIT,USB-RELAY08,,SERIAL-{board_id}",
            "transport": "serial",
            "connection": self._port_name,
            "driver": "seeit_relay08",
        }

    def capabilities(self) -> CapabilityDescriptor:
        return CapabilityDescriptor(
            device_type="seeit_relay08",
            device_id=self.device_id,
            display_name="Seeit USB-RELAY08 (Serial)",
            positions=[
                Position(
                    id=f"relay{index}",
                    label=f"Relay {index}",
                    kind=PositionKind.OUTPUT_DIGITAL,
                )
                for index in range(1, NUM_CHANNELS + 1)
            ],
        )

    def write(self, position_id: str, value: Any) -> None:
        """Set one relay. A truthy value means ON."""
        with self._io_lock:
            self._require_connected()
            bit = self._channel_index(position_id)
            requested_state = bool(value)

            if requested_state:
                self._state_mask &= ~(1 << bit) & 0xFF
            else:
                self._state_mask |= 1 << bit

            self._port.write(bytes([self._state_mask]))
            self._emit(
                position_id,
                requested_state,
                None,
                event_type="state",
            )

    def read(self, position_id: str) -> bool:
        """
        Return the last commanded state.

        The serial protocol used here does not provide independent relay
        contact or coil-state feedback.
        """
        with self._io_lock:
            bit = self._channel_index(position_id)
            is_on = not bool(self._state_mask & (1 << bit))
            self._emit(
                position_id,
                is_on,
                None,
                event_type="measurement",
            )
            return is_on

    def all_off(self) -> None:
        with self._io_lock:
            self._require_connected()
            self._state_mask = ALL_OFF_MASK
            self._port.write(bytes([self._state_mask]))
            self._emit(
                None,
                "all_off",
                None,
                event_type="state",
            )

    def _require_connected(self) -> None:
        if not self._connected or self._port is None:
            raise RuntimeError(
                f"{self.device_id}: relay board is not connected"
            )

    def _channel_index(self, position_id: str) -> int:
        if not position_id.startswith("relay"):
            raise KeyError(
                f"{self.device_id}: no such position {position_id!r}"
            )

        suffix = position_id[len("relay"):]
        if not suffix.isdigit():
            raise KeyError(
                f"{self.device_id}: no such position {position_id!r}"
            )

        channel = int(suffix)
        if not 1 <= channel <= NUM_CHANNELS:
            raise KeyError(
                f"{self.device_id}: relay index out of range: {channel}"
            )

        return channel - 1


# Compatibility name used by earlier code and documentation.
SeeitRelay08Driver = SeeitRelay08SerialDriver
