"""
Per-DUT CSV logger.

One CSV file per DUT per run: run_<run_id>_DUT_<uid>.csv, all sharing the
same row schema so the report generator can treat every file identically.
Equipment-level events with no DUT mapping (e.g. a global log message, or
a device with no position) fall through to an "unassigned" file rather
than being dropped, so nothing silently disappears.
"""

from __future__ import annotations

import csv
from pathlib import Path

from ..drivers.base import LogEvent
from .mapping import DutMapping

FIELDNAMES = ["timestamp", "device_id", "position", "channel", "value", "unit", "event_type"]


class CsvRunLogger:
    def __init__(self, run_id: str, mapping: DutMapping, output_dir: str = "./runs"):
        self.run_id = run_id
        self.mapping = mapping
        self.output_dir = Path(output_dir) / run_id
        self.output_dir.mkdir(parents=True, exist_ok=True)
        self._writers: dict[str, csv.DictWriter] = {}
        self._files: dict[str, "TextIO"] = {}

    def _writer_for(self, dut_uid: str) -> csv.DictWriter:
        if dut_uid not in self._writers:
            path = self.output_dir / f"run_{self.run_id}_DUT_{dut_uid}.csv"
            is_new = not path.exists()
            f = open(path, "a", newline="")
            writer = csv.DictWriter(f, fieldnames=FIELDNAMES)
            if is_new:
                writer.writeheader()
            self._files[dut_uid] = f
            self._writers[dut_uid] = writer
        return self._writers[dut_uid]

    def handle_event(self, event: LogEvent) -> None:
        dut_uid = self.mapping.dut_for(event.device_id, event.position) or "unassigned"
        writer = self._writer_for(dut_uid)
        writer.writerow({
            "timestamp": event.timestamp,
            "device_id": event.device_id,
            "position": event.position,
            "channel": event.channel,
            "value": event.value,
            "unit": event.unit,
            "event_type": event.event_type,
        })
        self._files[dut_uid].flush()

    def record_direct(self, dut_uid: str, label: str, value) -> None:
        """
        Write a row straight to a specific DUT's CSV without going through
        device/position mapping — used for operator-entered metadata
        (serial numbers, IDs) that isn't tied to a hardware channel.
        """
        writer = self._writer_for(dut_uid)
        writer.writerow({
            "timestamp": LogEvent.now(),
            "device_id": "operator_input",
            "position": label,
            "channel": None,
            "value": value,
            "unit": None,
            "event_type": "metadata",
        })
        self._files[dut_uid].flush()

    def close(self) -> None:
        for f in self._files.values():
            f.close()

    def __enter__(self):
        return self

    def __exit__(self, exc_type, exc, tb):
        self.close()
