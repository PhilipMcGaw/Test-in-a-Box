"""
Seeit USBB-RELAY08 driver.

Protocol (serial, 9600 baud, one byte per command):
  - 'P'  -> request board ID (device replies with 1 byte identifying board/channel count)
  - 'Q'  -> switch device into "command mode"
  - single byte bitmask sets all relay states at once: bit=0 -> relay ON,
    bit=1 -> relay OFF, bit0 = relay 1 (LSB), up to bit7 = relay 8.

This command set is adapted from the open-source community driver for the
SeeIT USB-Relay4/8 family (chrysh/SeeIT_USB_Relay on GitHub) — the vendor
doesn't publish a public protocol doc, so treat the exact byte values as a
starting point and confirm against your actual unit before relying on it
for anything safety-critical.

Each relay is exposed as its own digital-output position ("relay1".."relay8")
so it fits the same write(position_id, value)/read(position_id) interface as
every other driver.
"""

from __future__ import annotations

import time
from typing import Any, Optional

from .base import CapabilityDescriptor, Driver, Position, PositionKind
from .registry import register_driver

try:
    import serial
except ImportError:  # pragma: no cover
    serial = None

NUM_CHANNELS = 8
GET_BOARD_ID = b"P"
SET_CMD_MODE = b"Q"


@register_driver("seeit_relay08")
class SeeitRelay08Driver(Driver):
    def __init__(self, device_id: str, serial_port: str, on_event=None,
                 baudrate: int = 9600):
        super().__init__(device_id, on_event)
        self._port_name = serial_port
        self._baudrate = baudrate
        self._port = None
        # bit=0 -> ON, bit=1 -> OFF; start all-off (0xFF)
        self._state_mask = 0xFF

    def connect(self) -> None:
        if serial is None:
            raise RuntimeError(
                "pyserial is not installed. `pip install pyserial` to talk "
                "to the Seeit relay board."
            )
        self._port = serial.Serial(self._port_name, self._baudrate, timeout=1)
        self._port.write(GET_BOARD_ID)
        time.sleep(0.2)
        self._port.read(1)  # board id byte — currently unused, just drains the reply
        self._port.write(SET_CMD_MODE)
        time.sleep(0.2)
        self._connected = True

    def close(self) -> None:
        if self._port is not None:
            self._port.close()
        self._connected = False

    def capabilities(self) -> CapabilityDescriptor:
        positions = [
            Position(id=f"relay{i}", label=f"Relay {i}", kind=PositionKind.OUTPUT_DIGITAL)
            for i in range(1, NUM_CHANNELS + 1)
        ]
        return CapabilityDescriptor(
            device_type="seeit_relay08",
            device_id=self.device_id,
            display_name="Seeit USBB-RELAY08",
            positions=positions,
        )

    def _channel_index(self, position_id: str) -> int:
        if not position_id.startswith("relay"):
            raise KeyError(f"{self.device_id}: no such position '{position_id}'")
        idx = int(position_id[len("relay"):])
        if not (1 <= idx <= NUM_CHANNELS):
            raise KeyError(f"{self.device_id}: relay index out of range: {idx}")
        return idx - 1  # zero-based bit position

    def write(self, position_id: str, value: Any) -> None:
        """value is truthy for ON, falsy for OFF."""
        bit = self._channel_index(position_id)
        if value:
            self._state_mask &= ~(1 << bit) & 0xFF   # clear bit -> ON
        else:
            self._state_mask |= (1 << bit)            # set bit -> OFF
        self._port.write(bytes([self._state_mask]))
        self._emit(position_id, bool(value), None, event_type="state")

    def read(self, position_id: str) -> Any:
        """Read back last-known commanded state (board has no readback line)."""
        bit = self._channel_index(position_id)
        is_on = not (self._state_mask & (1 << bit))
        self._emit(position_id, is_on, None, event_type="measurement")
        return is_on

    def all_off(self) -> None:
        self._state_mask = 0xFF
        self._port.write(bytes([self._state_mask]))
        self._emit(None, "all_off", None, event_type="state")
