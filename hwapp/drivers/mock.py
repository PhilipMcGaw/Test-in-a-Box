"""
Mock drivers with no real hardware dependency — for developing/testing the
run manager, DUT mapping, and CSV logging before wiring up physical gear.
"""

from __future__ import annotations

import random
from typing import Any

from .base import CapabilityDescriptor, Driver, Position, PositionKind
from .registry import register_driver


@register_driver("mock_psu")
class MockPsuDriver(Driver):
    def __init__(self, device_id: str, on_event=None):
        super().__init__(device_id, on_event)
        self._voltage = 0.0
        self._output_on = False

    def connect(self) -> None:
        self._connected = True

    def close(self) -> None:
        self._connected = False

    def capabilities(self) -> CapabilityDescriptor:
        return CapabilityDescriptor(
            device_type="mock_psu",
            device_id=self.device_id,
            display_name="Mock PSU",
            positions=[
                Position("voltage", "Set Voltage", PositionKind.OUTPUT_ANALOG, "V"),
                Position("output", "Output Enable", PositionKind.OUTPUT_DIGITAL),
            ],
        )

    def write(self, position_id: str, value: Any) -> None:
        if position_id == "voltage":
            self._voltage = float(value)
            self._emit(position_id, self._voltage, "V", event_type="state")
        elif position_id == "output":
            self._output_on = bool(value)
            self._emit(position_id, self._output_on, None, event_type="state")
        else:
            raise KeyError(position_id)

    def read(self, position_id: str) -> Any:
        if position_id == "voltage":
            # simulate a little measurement noise around the setpoint
            value = self._voltage + random.uniform(-0.02, 0.02) if self._output_on else 0.0
            self._emit(position_id, value, "V", event_type="measurement")
            return value
        if position_id == "output":
            self._emit(position_id, self._output_on, None, event_type="measurement")
            return self._output_on
        raise KeyError(position_id)


@register_driver("mock_relay")
class MockRelayDriver(Driver):
    def __init__(self, device_id: str, on_event=None, num_channels: int = 8):
        super().__init__(device_id, on_event)
        self._num_channels = num_channels
        self._state = {i: False for i in range(1, num_channels + 1)}

    def connect(self) -> None:
        self._connected = True

    def close(self) -> None:
        self._connected = False

    def capabilities(self) -> CapabilityDescriptor:
        return CapabilityDescriptor(
            device_type="mock_relay",
            device_id=self.device_id,
            display_name="Mock Relay",
            positions=[
                Position(f"relay{i}", f"Relay {i}", PositionKind.OUTPUT_DIGITAL)
                for i in range(1, self._num_channels + 1)
            ],
        )

    def write(self, position_id: str, value: Any) -> None:
        ch = int(position_id[len("relay"):])
        self._state[ch] = bool(value)
        self._emit(position_id, bool(value), None, event_type="state")

    def read(self, position_id: str) -> Any:
        ch = int(position_id[len("relay"):])
        value = self._state[ch]
        self._emit(position_id, value, None, event_type="measurement")
        return value
