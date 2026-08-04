"""
Per-DUT CSV logger.

One CSV file is created per DUT for each run:

    run_<run_id>_DUT_<uid>.csv

All files share the same row schema so future report generation can process
them consistently.

Equipment-level events with no DUT mapping fall through to an ``unassigned``
file rather than being dropped, so no engineering event silently disappears.

Run-level metadata is stored separately in:

    run_<run_id>_metadata.csv
"""

from __future__ import annotations

import csv
import threading
from pathlib import Path
from typing import Any, TextIO

from ..drivers.base import LogEvent
from .mapping import DutMapping

FIELDNAMES = [
    "timestamp",
    "device_id",
    "position",
    "channel",
    "value",
    "unit",
    "event_type",
]

METADATA_FIELDNAMES = [
    "timestamp",
    "key",
    "value",
]


class CsvRunLogger:
    """Thread-safe CSV logger that routes events to one file per DUT."""

    def __init__(
        self,
        run_id: str,
        mapping: DutMapping,
        output_dir: str = "./runs",
    ) -> None:
        self.run_id = run_id
        self.mapping = mapping
        self.output_dir = Path(output_dir) / run_id
        self.output_dir.mkdir(parents=True, exist_ok=True)

        self._writers: dict[str, csv.DictWriter] = {}
        self._files: dict[str, TextIO] = {}
        self._metadata_file: TextIO | None = None
        self._metadata_writer: csv.DictWriter | None = None

        self._lock = threading.RLock()
        self._closed = False

    def _writer_for(self, dut_uid: str) -> csv.DictWriter:
        """
        Return the writer for a DUT, creating the file and header if required.

        The caller must hold ``self._lock``.
        """
        if self._closed:
            raise RuntimeError("CSV logger is closed")

        if dut_uid not in self._writers:
            path = self.output_dir / f"run_{self.run_id}_DUT_{dut_uid}.csv"
            is_new = not path.exists()

            handle = path.open(
                "a",
                newline="",
                encoding="utf-8",
            )
            writer = csv.DictWriter(handle, fieldnames=FIELDNAMES)

            if is_new:
                writer.writeheader()
                handle.flush()

            self._files[dut_uid] = handle
            self._writers[dut_uid] = writer

        return self._writers[dut_uid]

    def _run_metadata_writer(self) -> csv.DictWriter:
        """
        Return the run-metadata writer, creating the file if required.

        The caller must hold ``self._lock``.
        """
        if self._closed:
            raise RuntimeError("CSV logger is closed")

        if self._metadata_writer is None:
            path = self.output_dir / f"run_{self.run_id}_metadata.csv"
            is_new = not path.exists()

            handle = path.open(
                "a",
                newline="",
                encoding="utf-8",
            )
            writer = csv.DictWriter(
                handle,
                fieldnames=METADATA_FIELDNAMES,
            )

            if is_new:
                writer.writeheader()
                handle.flush()

            self._metadata_file = handle
            self._metadata_writer = writer

        return self._metadata_writer

    def handle_event(self, event: LogEvent) -> None:
        """Route one driver or script event to the appropriate DUT CSV."""
        dut_uid = (
            self.mapping.dut_for(event.device_id, event.position)
            or "unassigned"
        )

        with self._lock:
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

    def record_metadata(
        self,
        dut_uid: str,
        label: str,
        value: Any,
    ) -> None:
        """Record operator-entered metadata against a specific DUT."""
        with self._lock:
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

    def record_run_metadata(
        self,
        key: str,
        value: Any,
    ) -> None:
        """Record one metadata item that applies to the whole run."""
        with self._lock:
            writer = self._run_metadata_writer()
            writer.writerow({
                "timestamp": LogEvent.now(),
                "key": key,
                "value": value,
            })

            assert self._metadata_file is not None
            self._metadata_file.flush()

    def record_run_metadata_many(
        self,
        metadata: dict[str, Any],
    ) -> None:
        """Record several run-level metadata values."""
        for key, value in metadata.items():
            self.record_run_metadata(key, value)

    def record_direct(
        self,
        dut_uid: str,
        label: str,
        value: Any,
    ) -> None:
        """Backwards-compatible alias for :meth:`record_metadata`."""
        self.record_metadata(dut_uid, label, value)

    def close(self) -> None:
        """Flush and close all files. Safe to call more than once."""
        with self._lock:
            if self._closed:
                return

            for handle in self._files.values():
                try:
                    handle.flush()
                finally:
                    handle.close()

            if self._metadata_file is not None:
                try:
                    self._metadata_file.flush()
                finally:
                    self._metadata_file.close()

            self._writers.clear()
            self._files.clear()
            self._metadata_writer = None
            self._metadata_file = None
            self._closed = True

    def __enter__(self) -> "CsvRunLogger":
        return self

    def __exit__(self, exc_type, exc, traceback) -> None:
        self.close()
