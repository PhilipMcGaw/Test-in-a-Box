"""
Base classes every hardware driver implements.

The whole point of this layer: a new instrument = a new subclass of Driver
plus a CapabilityDescriptor. The Blockly toolbox (added later) will read
CapabilityDescriptor.positions to auto-generate blocks, and the runner will
call the same handful of methods regardless of what's actually plugged in.
"""

from __future__ import annotations

from abc import ABC, abstractmethod
from dataclasses import dataclass, field
from datetime import datetime, timezone
from enum import Enum
from typing import Any, Callable, Optional


class PositionKind(str, Enum):
    """What kind of thing a position on a device represents."""
    OUTPUT_ANALOG = "output_analog"      # e.g. PSU channel voltage/current setpoint
    OUTPUT_DIGITAL = "output_digital"    # e.g. relay channel on/off
    INPUT_ANALOG = "input_analog"        # e.g. TC-08/ADC channel reading
    INPUT_DIGITAL = "input_digital"      # e.g. relay readback, digital sense line


@dataclass
class Position:
    """A single addressable point on a device (a channel, relay, etc.)."""
    id: str                      # e.g. "ch1" — unique within the device
    label: str                   # human-readable, e.g. "Channel 1"
    kind: PositionKind
    unit: Optional[str] = None   # e.g. "V", "A", "degC", None for digital


@dataclass
class CapabilityDescriptor:
    """
    Describes what a connected device instance can do. The registry and
    (later) the Blockly toolbox generator read this to know what blocks/
    fields to offer for a given device_id.
    """
    device_type: str             # e.g. "psu", "seeit_relay08", "pico_tc08", "scpi"
    device_id: str               # unique instance id, e.g. "psu1"
    display_name: str
    positions: list[Position] = field(default_factory=list)

    def position(self, position_id: str) -> Position:
        for p in self.positions:
            if p.id == position_id:
                return p
        raise KeyError(f"{self.device_id}: no such position '{position_id}'")


@dataclass
class LogEvent:
    """One row of data — a measurement or a script-level log/assert event."""
    timestamp: str
    device_id: str
    position: Optional[str]
    channel: Optional[str]
    value: Any
    unit: Optional[str]
    event_type: str               # "measurement" | "log" | "assert" | "state"

    @staticmethod
    def now() -> str:
        return datetime.now(timezone.utc).isoformat()


class Driver(ABC):
    """
    Common interface for every piece of test equipment.

    Concrete drivers implement connect/close and the read/write primitives
    that make sense for that device. `capabilities()` is what the rest of
    the app introspects — everything else is driver-specific detail hidden
    behind write()/read()/query().
    """

    def __init__(self, device_id: str, on_event: Optional[Callable[[LogEvent], None]] = None):
        self.device_id = device_id
        self._on_event = on_event
        self._connected = False

    # -- lifecycle -----------------------------------------------------
    @abstractmethod
    def connect(self) -> None:
        ...

    @abstractmethod
    def close(self) -> None:
        ...

    @property
    def connected(self) -> bool:
        return self._connected

    def set_event_sink(self, on_event: Optional[Callable[["LogEvent"], None]]) -> None:
        """Point this driver's logging at a new run's logger without reconnecting."""
        self._on_event = on_event

    # -- introspection ---------------------------------------------------
    @abstractmethod
    def capabilities(self) -> CapabilityDescriptor:
        ...

    # -- generic read/write (drivers override what's relevant) -----------
    def write(self, position_id: str, value: Any) -> None:
        raise NotImplementedError(f"{self.device_id}: write() not supported")

    def read(self, position_id: str) -> Any:
        raise NotImplementedError(f"{self.device_id}: read() not supported")

    def query(self, raw_command: str) -> str:
        raise NotImplementedError(f"{self.device_id}: query() not supported")

    # -- event emission (used by write/read to feed the CSV logger) ------
    def _emit(self, position_id: Optional[str], value: Any, unit: Optional[str],
               event_type: str = "measurement") -> None:
        if self._on_event is None:
            return
        evt = LogEvent(
            timestamp=LogEvent.now(),
            device_id=self.device_id,
            position=position_id,
            channel=position_id,
            value=value,
            unit=unit,
            event_type=event_type,
        )
        self._on_event(evt)

    def __enter__(self):
        self.connect()
        return self

    def __exit__(self, exc_type, exc, tb):
        self.close()
