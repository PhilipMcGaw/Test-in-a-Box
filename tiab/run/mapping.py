"""
DUT-to-position mapping.

A "position" here is (device_id, position_id) — e.g. ("relay1", "relay3")
or ("psu1", "voltage"). At the start of a run the operator assigns a DUT
UID to each position that's in use; that mapping is locked for the whole
run (DUTs don't move positions mid-run), so the runner can resolve
device+position -> DUT UID for every log event without re-checking.
"""

from __future__ import annotations

from dataclasses import dataclass


@dataclass(frozen=True)
class PositionRef:
    device_id: str
    position_id: str


class DutMapping:
    def __init__(self):
        self._map: dict[PositionRef, str] = {}   # position -> dut_uid
        self._locked = False

    def assign(self, device_id: str, position_id: str, dut_uid: str) -> None:
        if self._locked:
            raise RuntimeError(
                "mapping is locked for this run — DUTs don't move positions mid-run"
            )
        self._map[PositionRef(device_id, position_id)] = dut_uid

    def lock(self) -> None:
        self._locked = True

    def dut_for(self, device_id: str, position_id: str | None) -> str | None:
        if position_id is None:
            return None
        return self._map.get(PositionRef(device_id, position_id))

    def duts(self) -> set[str]:
        return set(self._map.values())

    def as_dict(self) -> dict[str, str]:
        """{'device_id:position_id': dut_uid} — handy for saving alongside run metadata."""
        return {f"{ref.device_id}:{ref.position_id}": uid for ref, uid in self._map.items()}
