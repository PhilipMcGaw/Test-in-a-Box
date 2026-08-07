"""
Run context that generated test scripts execute against.

A Blockly-generated script calls this class instead of touching drivers
directly. The runner resolves device IDs, routes driver events to the CSV
logger, records run metadata, reports progress to the live console and provides
simple assertion support.
"""

from __future__ import annotations

import getpass
import platform
import socket
import sys
import time
from datetime import datetime, timezone
from pathlib import Path
from typing import Any, Callable, Optional

from ..drivers.base import Driver, LogEvent
from ..drivers.registry import create_driver
from .csv_logger import CsvRunLogger
from .mapping import DutMapping
from .provenance import (
    collect_software_identity,
    sha256_json,
    sha256_text,
    write_run_reports,
)


class AssertionFailure(Exception):
    """Raised when an evaluated test condition fails."""


class TestRunner:
    def __init__(
        self,
        run_id: str,
        mapping: DutMapping,
        output_dir: str = "./runs",
        console: Optional[Callable[[str], None]] = None,
    ) -> None:
        self.run_id = run_id
        self.mapping = mapping
        self.logger = CsvRunLogger(run_id, mapping, output_dir)
        self.console = console or (
            lambda message: print(
                message,
                file=sys.stdout,
                flush=True,
            )
        )
        self.devices: dict[str, Driver] = {}
        self._run_start_utc = datetime.now(timezone.utc).isoformat()
        self._project_root: Path | None = None
        self._configuration_snapshot: dict[str, Any] = {}
        self._generated_code = ""
        self._instrument_identities: dict[str, Any] = {}

        self._record_host_metadata()

    def _record_host_metadata(self) -> None:
        """
        Record traceability information about the computer and user account.

        If a value cannot be obtained, an explanatory placeholder is recorded
        rather than failing the test run.
        """
        def safe_value(getter: Callable[[], str]) -> str:
            try:
                value = getter()
                return value or "unknown"
            except Exception as exc:
                return f"unavailable: {exc}"

        uname = platform.uname()

        metadata = {
            "run_id": self.run_id,
            "run_start_utc": self._run_start_utc,
            "hostname": safe_value(socket.gethostname),
            "logged_in_user": safe_value(getpass.getuser),
            "operating_system": safe_value(platform.system),
            "os_release": safe_value(platform.release),
            "os_version": safe_value(platform.version),
            "os_build": uname.version or "unknown",
            "os_machine": uname.machine or "unknown",
            "os_platform_string": safe_value(platform.platform),
            "python_version": safe_value(platform.python_version),
        }

        self.logger.record_run_metadata_many(metadata)

    # ------------------------------------------------------------------
    # Device setup
    # ------------------------------------------------------------------

    def add_device(
        self,
        device_type: str,
        device_id: str,
        **kwargs: Any,
    ) -> Driver:
        if device_id in self.devices:
            raise ValueError(
                f"device_id {device_id!r} is already registered"
            )

        driver = create_driver(
            device_type,
            device_id,
            on_event=self.logger.handle_event,
            **kwargs,
        )
        driver.connect()
        self.devices[device_id] = driver

        self._say(
            f"[connect] {device_id} ({device_type}) connected"
        )
        return driver

    @classmethod
    def for_existing_devices(
        cls,
        run_id: str,
        mapping: DutMapping,
        devices: dict[str, Driver],
        output_dir: str = "./runs",
        console: Optional[Callable[[str], None]] = None,
    ) -> "TestRunner":
        """
        Build a runner around devices that are already connected.

        This is the normal web-application workflow, where instruments stay
        connected across several test runs.
        """
        instance = cls(
            run_id,
            mapping,
            output_dir,
            console,
        )
        instance.devices = devices

        for driver in devices.values():
            driver.set_event_sink(instance.logger.handle_event)

        instance._record_instrument_identities()
        return instance

    def _record_instrument_identities(self) -> None:
        """Record identity information for every connected instrument."""
        for device_id, driver in self.devices.items():
            try:
                identity = driver.identify()
            except Exception as exc:
                self.logger.record_run_metadata(
                    f"instrument.{device_id}.identity_error",
                    str(exc),
                )
                continue

            if not identity:
                self.logger.record_run_metadata(
                    f"instrument.{device_id}.identity",
                    "not available",
                )
                continue

            self._instrument_identities[device_id] = dict(identity)

            for key, value in identity.items():
                self.logger.record_run_metadata(
                    f"instrument.{device_id}.{key}",
                    value,
                )

    def record_run_provenance(
        self,
        *,
        project_root: str | Path,
        configuration: dict[str, Any],
        generated_code: str,
    ) -> None:
        """Record software identity and immutable run-input hashes."""
        self._project_root = Path(project_root).resolve()
        self._configuration_snapshot = configuration
        self._generated_code = generated_code

        software = collect_software_identity(self._project_root)
        mapping_snapshot = self.mapping.as_dict()

        metadata = {
            "tiab.version": software["version"],
            "tiab.update_channel": software["update_channel"],
            "tiab.update_ref": software["update_ref"],
            "tiab.commit": software["commit"],
            "tiab.archive_sha256": software["archive_sha256"],
            "tiab.updater_version": software["updater_version"],
            "configuration.sha256": sha256_json(configuration),
            "dut_mapping.sha256": sha256_json(mapping_snapshot),
            "procedure.sha256": sha256_text(generated_code),
        }
        self.logger.record_run_metadata_many(metadata)

        write_run_reports(
            output_dir=self.logger.output_dir,
            run_id=self.run_id,
            start_utc=self._run_start_utc,
            finish_utc=None,
            status="running",
            software=software,
            configuration=configuration,
            mapping=mapping_snapshot,
            generated_code=generated_code,
            instruments=self._instrument_identities,
        )

    def finalize_run_provenance(self, status: str) -> None:
        """Finalize the manifest and Markdown summary for this run."""
        finish_utc = datetime.now(timezone.utc).isoformat()
        self.logger.record_run_metadata_many({
            "run_finish_utc": finish_utc,
            "run_status": status,
        })

        if self._project_root is None:
            return

        write_run_reports(
            output_dir=self.logger.output_dir,
            run_id=self.run_id,
            start_utc=self._run_start_utc,
            finish_utc=finish_utc,
            status=status,
            software=collect_software_identity(self._project_root),
            configuration=self._configuration_snapshot,
            mapping=self.mapping.as_dict(),
            generated_code=self._generated_code,
            instruments=self._instrument_identities,
        )

    def release_devices(self) -> None:
        """Detach from shared devices without closing them."""
        for driver in self.devices.values():
            driver.set_event_sink(None)

        self.devices = {}
        self.logger.close()

    def lock_mapping(self) -> None:
        self.mapping.lock()
        self._say(
            f"[setup] DUT mapping locked: {self.mapping.as_dict()}"
        )

    # ------------------------------------------------------------------
    # Methods called by generated scripts
    # ------------------------------------------------------------------

    def set(
        self,
        device_id: str,
        position_id: str,
        value: Any,
    ) -> None:
        self.devices[device_id].write(position_id, value)
        self._say(
            f"[set] {device_id}.{position_id} = {value}"
        )

    def get(
        self,
        device_id: str,
        position_id: str,
    ) -> Any:
        value = self.devices[device_id].read(position_id)
        self._say(
            f"[get] {device_id}.{position_id} -> {value}"
        )
        return value

    def wait(self, seconds: float) -> None:
        self._say(f"[wait] {seconds}s")
        time.sleep(seconds)

    def log(
        self,
        message: str,
        device_id: Optional[str] = None,
        position_id: Optional[str] = None,
    ) -> None:
        self._say(f"[log] {message}")
        self.logger.handle_event(
            LogEvent(
                timestamp=LogEvent.now(),
                device_id=device_id or "script",
                position=position_id,
                channel=position_id,
                value=message,
                unit=None,
                event_type="log",
            )
        )

    def assert_that(
        self,
        condition: bool,
        message: str,
        device_id: Optional[str] = None,
        position_id: Optional[str] = None,
    ) -> None:
        status = "PASS" if condition else "FAIL"
        self._say(f"[assert:{status}] {message}")

        self.logger.handle_event(
            LogEvent(
                timestamp=LogEvent.now(),
                device_id=device_id or "script",
                position=position_id,
                channel=position_id,
                value=f"{status}: {message}",
                unit=None,
                event_type="assert",
            )
        )

        if not condition:
            raise AssertionFailure(message)

    def record_metadata(
        self,
        dut_uid: str,
        label: str,
        value: Any,
    ) -> None:
        """Record an operator-entered value against a DUT."""
        self._say(
            f"[metadata] {label} (DUT {dut_uid}) = {value}"
        )
        self.logger.record_metadata(
            dut_uid,
            label,
            value,
        )

    # ------------------------------------------------------------------
    # Teardown
    # ------------------------------------------------------------------

    def finish(self) -> None:
        for device_id, driver in self.devices.items():
            try:
                driver.close()
            except Exception as exc:
                self._say(
                    f"[warn] error closing {device_id}: {exc}"
                )

        self.logger.close()
        self._say(
            f"[done] run {self.run_id} finished at "
            f"{datetime.now(timezone.utc).isoformat()}"
        )

    def _say(self, message: str) -> None:
        self.console(message)

    def __enter__(self) -> "TestRunner":
        return self

    def __exit__(self, exc_type, exc, traceback) -> None:
        self.finish()
