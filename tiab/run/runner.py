"""
Run context that generated test scripts execute against.

A Blockly-generated script (or, for now, a hand-written Python script like
example_scripts/demo_test.py) gets one of these and calls its methods
instead of touching drivers directly. That's the seam where the future
Blockly Python code-generator plugs in — every block just needs to emit a
call to one of these methods.

Handles:
  - resolving device_id -> driver instance
  - routing every read/write through the CSV logger (via the driver's
    on_event callback) so nothing needs to log manually
  - a live console (stdout for now; swap for a WebSocket emit later)
  - simple assertions for pass/fail reporting
"""

from __future__ import annotations

import sys
import time
from datetime import datetime, timezone
from typing import Any, Callable, Optional

from ..drivers.base import Driver, LogEvent
from ..drivers.registry import create_driver
from .csv_logger import CsvRunLogger
from .mapping import DutMapping


_MISSING = object()


class AssertionFailure(Exception):
    pass


class TestRunner:
    def __init__(self, run_id: str, mapping: DutMapping, output_dir: str = "./runs",
                 console: Optional[Callable[[str], None]] = None):
        self.run_id = run_id
        self.mapping = mapping
        self.logger = CsvRunLogger(run_id, mapping, output_dir)
        self.console = console or (lambda msg: print(msg, file=sys.stdout, flush=True))
        self.devices: dict[str, Driver] = {}

    # -- device setup ----------------------------------------------------
    def add_device(self, device_type: str, device_id: str, **kwargs) -> Driver:
        driver = create_driver(device_type, device_id, on_event=self.logger.handle_event, **kwargs)
        driver.connect()
        self.devices[device_id] = driver
        self._say(f"[connect] {device_id} ({device_type}) connected")
        return driver

    @classmethod
    def for_existing_devices(cls, run_id: str, mapping: DutMapping,
                              devices: dict[str, Driver], output_dir: str = "./runs",
                              console: Optional[Callable[[str], None]] = None) -> "TestRunner":
        """
        Build a runner around devices that are already connected (typical for
        the web app, where devices stay connected across many runs rather
        than being reconnected each time). Rebinds each driver's event sink
        to this run's CSV logger.
        """
        instance = cls(run_id, mapping, output_dir, console)
        instance.devices = devices
        for driver in devices.values():
            driver.set_event_sink(instance.logger.handle_event)
        return instance

    def release_devices(self) -> None:
        """Detach from shared devices without closing them (they outlive this run)."""
        for driver in self.devices.values():
            driver.set_event_sink(None)
        self.devices = {}
        self.logger.close()

    def lock_mapping(self) -> None:
        self.mapping.lock()
        self._say(f"[setup] DUT mapping locked: {self.mapping.as_dict()}")

    # -- the methods a generated script calls ------------------------------
    def set(self, device_id: str, position_id: str, value: Any) -> None:
        self.devices[device_id].write(position_id, value)
        self._say(f"[set] {device_id}.{position_id} = {value}")

    def get(self, device_id: str, position_id: str) -> Any:
        value = self.devices[device_id].read(position_id)
        self._say(f"[get] {device_id}.{position_id} -> {value}")
        return value

    def wait(self, seconds: float) -> None:
        self._say(f"[wait] {seconds}s")
        time.sleep(seconds)

    def log(
        self,
        label: str,
        value: Any = _MISSING,
        unit: Optional[str] = None,
        device_id: Optional[str] = None,
        position_id: Optional[str] = None,
    ) -> None:
        """
        Record a script-level note or a labelled engineering value.

        ``log("note")`` preserves the original message-only behaviour.

        ``log("Measured voltage", measured_voltage)`` records the label in the
        position/channel columns and the measurement in the value column.
        """
        if value is _MISSING:
            self._say(f"[log] {label}")
            event_position = position_id
            event_value = label
        else:
            suffix = f" {unit}" if unit else ""
            self._say(f"[log] {label} = {value}{suffix}")
            event_position = position_id or label
            event_value = value

        self.logger.handle_event(LogEvent(
            timestamp=LogEvent.now(),
            device_id=device_id or "script",
            position=event_position,
            channel=event_position,
            value=event_value,
            unit=unit,
            event_type="log",
        ))

    def assert_that(self, condition: bool, message: str,
                     device_id: Optional[str] = None, position_id: Optional[str] = None) -> None:
        status = "PASS" if condition else "FAIL"
        self._say(f"[assert:{status}] {message}")
        self.logger.handle_event(LogEvent(
            timestamp=LogEvent.now(), device_id=device_id or "script",
            position=position_id, channel=position_id,
            value=f"{status}: {message}", unit=None, event_type="assert",
        ))
        if not condition:
            raise AssertionFailure(message)

    def record_metadata(self, dut_uid: str, label: str, value) -> None:
        """Record an operator-entered value (serial number, ID, etc.) directly against a DUT."""
        self._say(f"[metadata] {label} (DUT {dut_uid}) = {value}")
        self.logger.record_metadata(dut_uid, label, value)

    # -- teardown ----------------------------------------------------------
    def finish(self) -> None:
        for device_id, driver in self.devices.items():
            try:
                driver.close()
            except Exception as exc:  # noqa: BLE001 - best-effort teardown
                self._say(f"[warn] error closing {device_id}: {exc}")
        self.logger.close()
        self._say(f"[done] run {self.run_id} finished at {datetime.now(timezone.utc).isoformat()}")

    def _say(self, message: str) -> None:
        self.console(message)

    def __enter__(self):
        return self

    def __exit__(self, exc_type, exc, tb):
        self.finish()
