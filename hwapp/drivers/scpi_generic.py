"""
Generic SCPI driver.

Works with any SCPI instrument reachable via PyVISA (USB-TMC, LAN/VXI-11,
GPIB, serial-over-USB...). Adding a new SCPI instrument to the app does NOT
require a new driver class — you write a small "command map" describing the
instrument's positions and the SCPI strings they map to (see
scpi_command_map.example.json), and pass it as `command_map_path`.

If pyvisa isn't installed, this module still imports fine — connect() will
raise a clear error instead of an ImportError at import time, so the rest of
the app (mock drivers, CSV logging, the runner) can be developed/tested
without VISA installed.
"""

from __future__ import annotations

import json
import re
from pathlib import Path
from typing import Any, Optional

from .base import CapabilityDescriptor, Driver, Position, PositionKind
from .registry import register_driver

try:
    import pyvisa
except ImportError:  # pragma: no cover - exercised only when pyvisa missing
    pyvisa = None


_KIND_MAP = {
    "output_analog": PositionKind.OUTPUT_ANALOG,
    "output_digital": PositionKind.OUTPUT_DIGITAL,
    "input_analog": PositionKind.INPUT_ANALOG,
    "input_digital": PositionKind.INPUT_DIGITAL,
}


@register_driver("scpi")
class ScpiGenericDriver(Driver):
    """
    command_map JSON shape:
    {
      "display_name": "Rohde & Schwarz HMP4040",
      "resource": "USB0::0x0AAD::0x0197::123456::INSTR",
      "positions": [
        {"id": "voltage", "label": "Set Voltage", "kind": "output_analog",
         "unit": "V", "write": "VOLT {value}", "read": "VOLT?"},
        {"id": "current", "label": "Set Current", "kind": "output_analog",
         "unit": "A", "write": "CURR {value}", "read": "CURR?"},
        {"id": "output", "label": "Output Enable", "kind": "output_digital",
         "unit": null, "write": "OUTP {value}", "read": "OUTP?"}
      ]
    }
    `value` in "write" templates is substituted with str(value) passed to write().
    """

    def __init__(self, device_id: str, command_map_path: str, on_event=None,
                 resource_override: Optional[str] = None):
        super().__init__(device_id, on_event)
        self._map_path = Path(command_map_path)
        self._config = json.loads(self._map_path.read_text())
        self._resource = resource_override or self._config["resource"]
        self._inst = None
        self._rm = None

    def connect(self) -> None:
        if pyvisa is None:
            raise RuntimeError(
                "pyvisa is not installed. `pip install pyvisa pyvisa-py` "
                "(or a vendor VISA runtime) to talk to real SCPI instruments."
            )
        self._rm = pyvisa.ResourceManager()
        self._inst = self._rm.open_resource(self._resource)
        self._connected = True

    def close(self) -> None:
        if self._inst is not None:
            self._inst.close()
        if self._rm is not None:
            self._rm.close()
        self._connected = False

    def capabilities(self) -> CapabilityDescriptor:
        positions = [
            Position(
                id=p["id"],
                label=p["label"],
                kind=_KIND_MAP[p["kind"]],
                unit=p.get("unit"),
            )
            for p in self._config["positions"]
        ]
        return CapabilityDescriptor(
            device_type="scpi",
            device_id=self.device_id,
            display_name=self._config.get("display_name", self.device_id),
            positions=positions,
        )

    def _position_config(self, position_id: str) -> dict:
        for p in self._config["positions"]:
            if p["id"] == position_id:
                return p
        raise KeyError(f"{self.device_id}: no such position '{position_id}'")

    def write(self, position_id: str, value: Any) -> None:
        cfg = self._position_config(position_id)
        template = cfg["write"]
        cmd = template.format(value=value)
        self._inst.write(cmd)
        self._emit(position_id, value, cfg.get("unit"), event_type="state")

    def read(self, position_id: str) -> Any:
        cfg = self._position_config(position_id)
        raw = self._inst.query(cfg["read"]).strip()
        value = _coerce_numeric(raw)
        self._emit(position_id, value, cfg.get("unit"), event_type="measurement")
        return value

    def query(self, raw_command: str) -> str:
        return self._inst.query(raw_command).strip()


def _coerce_numeric(raw: str):
    if re.fullmatch(r"[-+]?\d+", raw):
        return int(raw)
    try:
        return float(raw)
    except ValueError:
        return raw
