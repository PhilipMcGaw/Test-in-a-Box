"""
DUT-to-position mapping.

A position is identified by ``(device_id, position_id)``, for example:

    ("relay1", "relay3")
    ("psu1", "voltage")

Before a run starts, the operator assigns each DUT to the positions that will
be used during the test.

Once the run begins, the mapping is locked so every engineering result remains
associated with the correct DUT throughout the run.
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
    """Thread-safe mapping from instrument positions to DUT identifiers."""

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
        """
        Assign a DUT to an instrument position.

        Raises:
            RuntimeError: If the mapping has already been locked.
            ValueError: If any identifier is empty.
        """
        device_id = device_id.strip()
        position_id = position_id.strip()
        dut_uid = dut_uid.strip()

        if not device_id:
            raise ValueError("device_id must not be empty")
        if not position_id:
            raise ValueError("position_id must not be empty")
        if not dut_uid:
            raise ValueError("dut_uid must not be empty")

        with self._lock:
            if self._locked:
                raise RuntimeError(
                    "mapping is locked for this run — "
                    "DUTs do not move positions mid-run"
                )

            self._map[PositionRef(device_id, position_id)] = dut_uid

    def clear(self) -> None:
        """
        Remove every mapping.

        This may only be called before the mapping has been locked.
        """
        with self._lock:
            if self._locked:
                raise RuntimeError("mapping is locked for this run")

            self._map.clear()

    def lock(self) -> None:
        """Prevent any further modification to the mapping."""
        with self._lock:
            self._locked = True

    def dut_for(
        self,
        device_id: str,
        position_id: str | None,
    ) -> str | None:
        """
        Return the DUT assigned to an instrument position.

        Returns:
            The DUT identifier, or ``None`` if the position is unmapped.
        """
        if position_id is None:
            return None

        with self._lock:
            return self._map.get(
                PositionRef(device_id, position_id)
            )

    def duts(self) -> set[str]:
        """Return the set of mapped DUT identifiers."""
        with self._lock:
            return set(self._map.values())

    def as_dict(self) -> dict[str, str]:
        """
        Return the mapping in a serialisable form.

        Example:

            {
                "relay1:relay3": "DUT_A",
                "psu1:voltage": "DUT_B",
            }
        """
        with self._lock:
            return {
                f"{ref.device_id}:{ref.position_id}": dut_uid
                for ref, dut_uid in self._map.items()
            }

    def __len__(self) -> int:
        """Return the number of mapped instrument positions."""
        with self._lock:
            return len(self._map)

    def __repr__(self) -> str:
        with self._lock:
            return (
                f"DutMapping("
                f"{len(self._map)} positions, "
                f"locked={self._locked})"
            )
