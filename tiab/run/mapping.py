"""
DUT-to-position mapping.

A position is identified by ``(device_id, position_id)``. Before a run starts,
the operator assigns DUT identifiers to the positions used by the procedure.
The mapping is then locked for the duration of the run.
"""

from __future__ import annotations

import threading
from dataclasses import dataclass


@dataclass(frozen=True)
class PositionRef:
    """Unique reference to a position on an instrument."""

    device_id: str
    position_id: str


class DutMapping:
    """Thread-safe DUT-to-position mapping."""

    def __init__(self) -> None:
        self._map: dict[PositionRef, str] = {}
        self._locked = False
        self._lock = threading.RLock()

    @property
    def locked(self) -> bool:
        """Return True once the mapping has been locked for a run."""
        with self._lock:
            return self._locked

    def assign(
        self,
        device_id: str,
        position_id: str,
        dut_uid: str,
    ) -> None:
        """Assign a DUT to an instrument position."""
        with self._lock:
            if self._locked:
                raise RuntimeError(
                    "mapping is locked for this run - "
                    "DUTs do not move positions mid-run"
                )

            self._map[PositionRef(device_id, position_id)] = dut_uid

    def clear(self) -> None:
        """Remove all mappings before the mapping has been locked."""
        with self._lock:
            if self._locked:
                raise RuntimeError("mapping is locked for this run")
            self._map.clear()

    def lock(self) -> None:
        """Prevent further changes to the mapping."""
        with self._lock:
            self._locked = True

    def dut_for(
        self,
        device_id: str,
        position_id: str | None,
    ) -> str | None:
        """Return the DUT assigned to a position, or None if unmapped."""
        if position_id is None:
            return None

        with self._lock:
            return self._map.get(PositionRef(device_id, position_id))

    def duts(self) -> set[str]:
        """Return the set of mapped DUT identifiers."""
        with self._lock:
            return set(self._map.values())

    def as_dict(self) -> dict[str, str]:
        """Return a serialisable representation of the mapping."""
        with self._lock:
            return {
                f"{ref.device_id}:{ref.position_id}": dut_uid
                for ref, dut_uid in self._map.items()
            }

    def __repr__(self) -> str:
        with self._lock:
            return (
                f"DutMapping({len(self._map)} positions, "
                f"locked={self._locked})"
            )
