"""
Pico ADC-20/24 (PicoLog High-Resolution Data Logger) driver.

Uses the picosdk PicoHRDL wrapper. Exposes each analog input channel as an
input_analog position in volts. The ADC-20 has 8 single-ended / 4
differential channels, ADC-24 has 16/8 — pass `num_channels` to match your
unit.
"""

from __future__ import annotations

from typing import Any

from .base import CapabilityDescriptor, Driver, Position, PositionKind
from .registry import register_driver

try:
    from picosdk.picohrdl import picohrdl as hrdl
except ImportError:  # pragma: no cover
    hrdl = None


@register_driver("pico_adc")
class PicoAdcDriver(Driver):
    def __init__(self, device_id: str, on_event=None, num_channels: int = 8):
        super().__init__(device_id, on_event)
        self._num_channels = num_channels
        self._handle = None

    def connect(self) -> None:
        if hrdl is None:
            raise RuntimeError(
                "picosdk is not installed, or the official Pico ADC-20/24 Windows "
                "runtime is unavailable. Run bootstrap.bat to download "
                "the offline PicoSDK installer, then have an administrator "
                "install it once on this machine."
            )
        self._handle = hrdl.usb_hrdl_open_unit()
        if self._handle <= 0:
            raise RuntimeError(f"{self.device_id}: failed to open ADC unit")
        for ch in range(1, self._num_channels + 1):
            hrdl.usb_hrdl_set_analog_in_channel(self._handle, ch, enabled=1)
        self._connected = True

    def close(self) -> None:
        if self._handle:
            hrdl.usb_hrdl_close_unit(self._handle)
        self._connected = False

    def capabilities(self) -> CapabilityDescriptor:
        positions = [
            Position(id=f"ch{i}", label=f"ADC Channel {i}",
                     kind=PositionKind.INPUT_ANALOG, unit="V")
            for i in range(1, self._num_channels + 1)
        ]
        return CapabilityDescriptor(
            device_type="pico_adc",
            device_id=self.device_id,
            display_name="Pico ADC-20/24",
            positions=positions,
        )

    def read(self, position_id: str) -> Any:
        ch = int(position_id[len("ch"):])
        value = hrdl.usb_hrdl_get_single_value(self._handle, ch)
        self._emit(position_id, value, "V", event_type="measurement")
        return value
