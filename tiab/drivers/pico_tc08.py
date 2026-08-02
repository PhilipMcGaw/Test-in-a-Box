"""
Pico TC-08 thermocouple data logger driver.

Uses the official picosdk Python wrappers (`pip install picosdk`, plus the
PicoSDK C driver installed on the machine). Each of the 8 thermocouple
inputs is exposed as an input_analog position ("ch1".."ch8"), all in
degrees C by default.

This mirrors the pattern you were already using with the Node-RED/MQTT
bridge, just moved in-process so readings can be written straight to the
per-DUT CSV instead of round-tripping through a broker.
"""

from __future__ import annotations

from typing import Any

from .base import CapabilityDescriptor, Driver, Position, PositionKind
from .registry import register_driver

try:
    from picosdk.usbtc08 import usbtc08 as tc08
    from picosdk.functions import assert_pico2000_ok  # noqa: F401  (validated at connect time)
except ImportError:  # pragma: no cover
    tc08 = None

NUM_CHANNELS = 8
# Thermocouple type per channel — override per instrument as needed.
DEFAULT_TC_TYPE = "K"


@register_driver("pico_tc08")
class PicoTC08Driver(Driver):
    def __init__(self, device_id: str, on_event=None,
                 tc_types: dict[int, str] | None = None):
        super().__init__(device_id, on_event)
        self._tc_types = tc_types or {i: DEFAULT_TC_TYPE for i in range(1, NUM_CHANNELS + 1)}
        self._handle = None

    def connect(self) -> None:
        if tc08 is None:
            raise RuntimeError(
                "picosdk is not installed, or the PicoSDK driver isn't "
                "present on this machine. `pip install picosdk` and "
                "install PicoSDK from Pico Technology."
            )
        self._handle = tc08.usb_tc08_open_unit()
        if self._handle <= 0:
            raise RuntimeError(f"{self.device_id}: failed to open TC-08 unit")
        for ch, tc_type in self._tc_types.items():
            tc08.usb_tc08_set_channel(self._handle, ch, ord(tc_type))
        self._connected = True

    def close(self) -> None:
        if self._handle:
            tc08.usb_tc08_close_unit(self._handle)
        self._connected = False

    def capabilities(self) -> CapabilityDescriptor:
        positions = [
            Position(id=f"ch{i}", label=f"TC Channel {i}",
                     kind=PositionKind.INPUT_ANALOG, unit="degC")
            for i in range(1, NUM_CHANNELS + 1)
        ]
        return CapabilityDescriptor(
            device_type="pico_tc08",
            device_id=self.device_id,
            display_name="Pico TC-08",
            positions=positions,
        )

    def read(self, position_id: str) -> Any:
        ch = int(position_id[len("ch"):])
        temps = tc08.usb_tc08_get_single(self._handle)
        value = temps[ch]
        self._emit(position_id, value, "degC", event_type="measurement")
        return value

    def read_all(self) -> dict[str, float]:
        temps = tc08.usb_tc08_get_single(self._handle)
        result = {}
        for ch in self._tc_types:
            pos = f"ch{ch}"
            value = temps[ch]
            self._emit(pos, value, "degC", event_type="measurement")
            result[pos] = value
        return result
