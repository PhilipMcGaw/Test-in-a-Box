"""
Pico ADC-20/24 (PicoLog High-Resolution Data Logger) driver.

Uses the picosdk PicoHRDL wrapper. Exposes each analog input channel as an
input_analog position in volts. The ADC-20 has 8 single-ended / 4
differential channels, ADC-24 has 16/8 — pass `num_channels` to match your
unit.
"""

from __future__ import annotations

from ctypes import c_int16, c_int32, byref, create_string_buffer
from typing import Any

from .base import CapabilityDescriptor, Driver, Position, PositionKind
from .registry import register_driver
from ..runtime import prepare_vendor_runtime

prepare_vendor_runtime("pico")

try:
    from picosdk.picohrdl import picohrdl as hrdl
except ImportError:  # pragma: no cover
    hrdl = None


def decode_digital_inputs(value: int) -> dict[str, bool]:
    """Decode the ADC-24 four-bit digital port, least-significant bit first."""
    return {
        f"d{pin}": bool(int(value) & (1 << (pin - 1)))
        for pin in range(1, 5)
    }


@register_driver("pico_adc")
class PicoAdcDriver(Driver):
    def __init__(
        self,
        device_id: str,
        on_event=None,
        model: str = "auto",
        num_channels: int = 8,
        voltage_range: int = 0,
        conversion_time: int = 0,
    ):
        super().__init__(device_id, on_event)
        self._model = str(model).strip().lower()
        if self._model not in {"auto", "adc20", "adc24"}:
            raise ValueError("model must be 'auto', 'adc20' or 'adc24'")
        self._num_channels = num_channels
        self._voltage_range = int(voltage_range)
        self._conversion_time = int(conversion_time)
        self._handle = None

    def connect(self) -> None:
        if hrdl is None:
            raise RuntimeError(
                "picosdk is not installed, or the official Pico ADC-20/24 Windows "
                "runtime is unavailable. Run bootstrap.bat to download "
                "the offline PicoSDK installer, then have an administrator "
                "install it once on this machine."
            )
        self._handle = hrdl._openUnit_()
        if self._handle <= 0:
            raise RuntimeError(f"{self.device_id}: failed to open ADC unit")
        if self._model == "auto":
            variant = self._read_unit_info(
                hrdl.PICO_INFO["PICO_VARIANT_INFO"]
            ).upper().replace("-", "")
            if "ADC24" in variant or variant == "24":
                self._model = "adc24"
                if self._num_channels == 8:
                    self._num_channels = 16
            elif "ADC20" in variant or variant == "20":
                self._model = "adc20"
                if self._num_channels == 8:
                    self._num_channels = 8
            else:
                raise RuntimeError(
                    f"{self.device_id}: unable to identify Pico ADC variant "
                    f"({variant or 'unknown'})"
                )
        for ch in range(1, self._num_channels + 1):
            status = hrdl._setAnalogInChannel_(
                self._handle,
                ch,
                1,
                self._voltage_range,
                1,
            )
            if status != 1:
                raise RuntimeError(
                    f"{self.device_id}: failed to enable ADC channel {ch}"
                )
        if self._model == "adc24":
            status = hrdl._setDigitalIOChannel_(self._handle, 0, 0, 15)
            if status != 1:
                raise RuntimeError(
                    f"{self.device_id}: failed to enable ADC-24 digital inputs"
                )
        self._connected = True

    def close(self) -> None:
        if self._handle:
            hrdl._closeUnit_(self._handle)
        self._connected = False

    def identify(self) -> dict[str, str]:
        """Return the Pico batch/serial identity for this connected unit."""
        if not self._handle:
            return {}
        serial = self._read_unit_info(
            hrdl.PICO_INFO["PICO_BATCH_AND_SERIAL"]
        )
        if not serial:
            return {}
        return {
            "manufacturer": "Pico Technology",
            "model": self._model.upper(),
            "serial": serial,
            "idn": f"Pico Technology,{self._model.upper()},{serial}",
        }

    def _read_unit_info(self, info_type: int) -> str:
        buffer = create_string_buffer(256)
        length = hrdl._getUnitInfo_(
            self._handle,
            buffer,
            len(buffer),
            info_type,
        )
        if length <= 0:
            return ""
        return buffer.value.decode("ascii", errors="replace").strip()

    def capabilities(self) -> CapabilityDescriptor:
        positions = [
            Position(id=f"ch{i}", label=f"ADC Channel {i}",
                     kind=PositionKind.INPUT_ANALOG, unit="V")
            for i in range(1, self._num_channels + 1)
        ]
        if self._model == "adc24":
            positions.extend(
                Position(
                    id=f"d{i}",
                    label=f"Digital Input {i}",
                    kind=PositionKind.INPUT_DIGITAL,
                )
                for i in range(1, 5)
            )
        return CapabilityDescriptor(
            device_type="pico_adc",
            device_id=self.device_id,
            display_name=f"Pico {self._model.upper()}",
            positions=positions,
        )

    def read(self, position_id: str) -> Any:
        if position_id.startswith("d"):
            if self._model != "adc24":
                raise ValueError(
                    f"{self.device_id}: digital inputs are only available on ADC-24"
                )
            pin = int(position_id[1:])
            if pin not in range(1, 5):
                raise ValueError(f"{self.device_id}: invalid digital input {pin}")
            digital_value = self.read_digital_port()
            value = decode_digital_inputs(digital_value)[f"d{pin}"]
            self._emit(position_id, value, None, event_type="measurement")
            return value

        if not position_id.startswith("ch"):
            raise ValueError(f"{self.device_id}: invalid ADC position {position_id!r}")
        ch = int(position_id[len("ch"):])
        overflow = c_int16()
        raw_millivolts = c_int32()
        status = hrdl._getSingleValue_(
            self._handle,
            ch,
            self._voltage_range,
            self._conversion_time,
            1,
            byref(overflow),
            byref(raw_millivolts),
        )
        if status != 1:
            raise RuntimeError(
                f"{self.device_id}: ADC read failed for channel {ch}"
            )
        value = raw_millivolts.value / 1000.0
        self._emit(position_id, value, "V", event_type="measurement")
        return value

    def read_digital_port(self) -> int:
        """Read the ADC-24 four-bit digital input port."""
        if self._model != "adc24":
            raise RuntimeError("digital inputs are only available on ADC-24")
        overflow = c_int16()
        raw_value = c_int32()
        status = hrdl._getSingleValue_(
            self._handle,
            0,
            self._voltage_range,
            self._conversion_time,
            1,
            byref(overflow),
            byref(raw_value),
        )
        if status != 1:
            raise RuntimeError(f"{self.device_id}: ADC-24 digital read failed")
        return raw_value.value & 0x0F
