"""
Base classes implemented by every Test in a Box hardware driver.

A new instrument normally consists of:

- a Driver subclass;
- a CapabilityDescriptor;
- one or more Position definitions.

The rest of the application interacts with the same small driver interface
regardless of the physical instrument or communication protocol.
"""

from __future__ import annotations

from abc import ABC, abstractmethod
from dataclasses import dataclass, field
from datetime import datetime, timezone
from enum import Enum
from typing import Any, Callable, Optional


class PositionKind(str, Enum):
    """The type of engineering value represented by a device position."""

    OUTPUT_ANALOG = "output_analog"
    OUTPUT_DIGITAL = "output_digital"
    INPUT_ANALOG = "input_analog"
    INPUT_DIGITAL = "input_digital"


@dataclass(frozen=True)
class Position:
    """A single addressable point on an instrument."""

    id: str
    label: str
    kind: PositionKind
    unit: Optional[str] = None


@dataclass
class CapabilityDescriptor:
    """
    Describe the operations and positions exposed by a connected instrument.

    The web application and Blockly editor use this information to determine
    which controls and fields should be available for a given device instance.
    """

    device_type: str
    device_id: str
    display_name: str
    positions: list[Position] = field(default_factory=list)

    def position(self, position_id: str) -> Position:
        """Return a position by ID, or raise KeyError when it does not exist."""
        for position in self.positions:
            if position.id == position_id:
                return position

        raise KeyError(
            f"{self.device_id}: no such position {position_id!r}"
        )


@dataclass
class LogEvent:
    """One timestamped engineering event recorded during a test run."""

    timestamp: str
    device_id: str
    position: Optional[str]
    channel: Optional[str]
    value: Any
    unit: Optional[str]
    event_type: str

    @staticmethod
    def now() -> str:
        """Return the current UTC time in ISO 8601 format."""
        return datetime.now(timezone.utc).isoformat()


class Driver(ABC):
    """
    Common interface for every item of test equipment.

    Concrete drivers implement connection handling, capability reporting and
    whichever read, write or query operations are appropriate to the
    instrument.

    Instrument-specific communication details remain inside the driver.
    """

    def __init__(
        self,
        device_id: str,
        on_event: Optional[Callable[[LogEvent], None]] = None,
    ) -> None:
        self.device_id = device_id
        self._on_event = on_event
        self._connected = False

    # ------------------------------------------------------------------
    # Lifecycle
    # ------------------------------------------------------------------

    @abstractmethod
    def connect(self) -> None:
        """Connect to the physical or simulated instrument."""

    @abstractmethod
    def close(self) -> None:
        """Close the instrument connection and release associated resources."""

    @property
    def connected(self) -> bool:
        """Return True when the driver considers itself connected."""
        return self._connected

    def safe_state(self) -> None:
        """
        Return the instrument to its defined safe condition.

        The default implementation does nothing because not every instrument
        controls an output. Drivers for power supplies, relay controllers,
        chambers and similar equipment should override this method.

        Safe-state implementations should be best-effort and should avoid
        raising merely because one individual output could not be changed.
        """

    def set_event_sink(
        self,
        on_event: Optional[Callable[[LogEvent], None]],
    ) -> None:
        """
        Redirect driver events to the logger for the current run.

        This allows devices to remain connected while successive test runs use
        different CSV loggers.
        """
        self._on_event = on_event

    # ------------------------------------------------------------------
    # Identification and capabilities
    # ------------------------------------------------------------------

    def identify(self) -> dict[str, str]:
        """
        Return identifying information for the connected instrument.

        Drivers should provide as much information as the hardware supports.
        Common keys are:

        - manufacturer
        - model
        - serial
        - firmware
        - idn

        The default implementation returns an empty dictionary for instruments
        that do not provide identification information.
        """
        return {}

    @abstractmethod
    def capabilities(self) -> CapabilityDescriptor:
        """Return the positions and operations exposed by this instrument."""

    # ------------------------------------------------------------------
    # Generic read, write and query operations
    # ------------------------------------------------------------------

    def write(self, position_id: str, value: Any) -> None:
        """Write a value to an instrument position."""
        raise NotImplementedError(
            f"{self.device_id}: write() not supported"
        )

    def read(self, position_id: str) -> Any:
        """Read the current value from an instrument position."""
        raise NotImplementedError(
            f"{self.device_id}: read() not supported"
        )

    def query(self, raw_command: str) -> str:
        """Send a raw query when the driver explicitly supports it."""
        raise NotImplementedError(
            f"{self.device_id}: query() not supported"
        )

    # ------------------------------------------------------------------
    # Event emission
    # ------------------------------------------------------------------

    def _emit(
        self,
        position_id: Optional[str],
        value: Any,
        unit: Optional[str],
        event_type: str = "measurement",
    ) -> None:
        """Emit a timestamped event to the currently attached run logger."""
        if self._on_event is None:
            return

        event = LogEvent(
            timestamp=LogEvent.now(),
            device_id=self.device_id,
            position=position_id,
            channel=position_id,
            value=value,
            unit=unit,
            event_type=event_type,
        )
        self._on_event(event)

    # ------------------------------------------------------------------
    # Context manager support
    # ------------------------------------------------------------------

    def __enter__(self) -> "Driver":
        self.connect()
        return self

    def __exit__(self, exc_type, exc, traceback) -> None:
        self.close()
