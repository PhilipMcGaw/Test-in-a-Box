"""
Local web server for Test in a Box.

Run from the project root with the portable Python environment:

    python -m webapp.server

Then open http://127.0.0.1:8765 in a browser.

The Blockly library, user interface and API are all served locally, so no
internet access is required after the Python dependencies have been installed.

Use the Configure Devices page to select instruments and set their current
connection details. The resulting configuration is stored in config.json next
to this file.
"""

from __future__ import annotations

import ast
import asyncio
import contextlib
import json
import queue
import re
import threading
import time
import traceback
from datetime import datetime, timezone
from pathlib import Path
from typing import Any

from fastapi import FastAPI, WebSocket, WebSocketDisconnect
from fastapi.responses import FileResponse, JSONResponse
from fastapi.staticfiles import StaticFiles
from pydantic import BaseModel, ConfigDict, Field, field_validator, model_validator

# Import every driver module so its registration decorator runs.
import tiab.drivers.aimtti_psu  # noqa: F401
import tiab.drivers.mock  # noqa: F401
import tiab.drivers.scpi_generic  # noqa: F401
import tiab.drivers.seeit_relay  # noqa: F401

try:
    import tiab.drivers.pico_adc  # noqa: F401
    import tiab.drivers.pico_tc08  # noqa: F401
except Exception as exc:
    # PicoSDK is optional. The rest of the application can still run.
    print(f"[startup] Pico drivers not fully available: {exc}")

from tiab.drivers.catalog import DEVICE_CATALOG
from tiab.drivers.registry import create_driver
from tiab.run.control import RunControl, StopRequested
from tiab.run.instrument import instrument_source
from tiab.run.mapping import DutMapping
from tiab.run.runner import AssertionFailure, TestRunner

BASE_DIR = Path(__file__).resolve().parent
CONFIG_PATH = BASE_DIR / "config.json"
RUNS_DIR = BASE_DIR / "runs"
SEQUENCES_DIR = BASE_DIR / "sequences"

RUNS_DIR.mkdir(exist_ok=True)
SEQUENCES_DIR.mkdir(exist_ok=True)

PROMPT_TIMEOUT_SECONDS = 3600.0
CONSOLE_QUEUE_LIMIT = 1000

IDLE_STATES = {"idle", "finished", "stopped", "failed", "error"}
ACTIVE_STATES = {
    "running",
    "pause_requested",
    "paused",
    "step",
    "stop_requested",
}

app = FastAPI()
app.mount("/static", StaticFiles(directory=str(BASE_DIR / "static")), name="static")

_devices: dict[str, Any] = {}
_config: dict[str, Any] = {}

_device_lock = threading.RLock()
_console_lock = threading.Lock()
_console_queues: list[queue.Queue[str]] = []

_run_control = RunControl()
_run_thread_lock = threading.Lock()
_run_thread: threading.Thread | None = None

_prompt_lock = threading.Lock()
_pending_prompts: dict[str, threading.Event] = {}
_prompt_answers: dict[str, str] = {}
_prompt_counter = 0


# ---------------------------------------------------------------------------
# Models
# ---------------------------------------------------------------------------

class DeviceConfigEntry(BaseModel):
    model_config = ConfigDict(extra="forbid")

    device_type: str
    device_id: str
    kwargs: dict[str, Any] = Field(default_factory=dict)
    x: float | None = None
    y: float | None = None

    @field_validator("device_type", "device_id")
    @classmethod
    def non_empty_text(cls, value: str) -> str:
        value = value.strip()
        if not value:
            raise ValueError("must not be empty")
        return value


class MappingEntry(BaseModel):
    model_config = ConfigDict(extra="forbid")

    device_id: str
    position_id: str
    dut_uid: str

    @field_validator("device_id", "position_id", "dut_uid")
    @classmethod
    def non_empty_text(cls, value: str) -> str:
        value = value.strip()
        if not value:
            raise ValueError("must not be empty")
        return value


class ConfigSaveRequest(BaseModel):
    model_config = ConfigDict(extra="forbid")

    devices: list[DeviceConfigEntry]
    mapping: list[MappingEntry] = Field(default_factory=list)

    @model_validator(mode="after")
    def validate_unique_entries(self) -> "ConfigSaveRequest":
        device_ids = [entry.device_id for entry in self.devices]
        if len(device_ids) != len(set(device_ids)):
            raise ValueError("device_id values must be unique")

        unknown_types = sorted({
            entry.device_type
            for entry in self.devices
            if entry.device_type not in DEVICE_CATALOG
        })
        if unknown_types:
            raise ValueError(
                "unknown device type(s): " + ", ".join(unknown_types)
            )

        mapping_keys = [
            (entry.device_id, entry.position_id)
            for entry in self.mapping
        ]
        if len(mapping_keys) != len(set(mapping_keys)):
            raise ValueError(
                "each device_id/position_id pair may only be mapped once"
            )

        known_ids = set(device_ids)
        missing = sorted({
            entry.device_id
            for entry in self.mapping
            if entry.device_id not in known_ids
        })
        if missing:
            raise ValueError(
                "mapping references unknown device_id value(s): "
                + ", ".join(missing)
            )

        return self


class SetPositionRequest(BaseModel):
    model_config = ConfigDict(extra="forbid")

    device_id: str
    position_id: str
    value: Any


class RunRequest(BaseModel):
    model_config = ConfigDict(extra="forbid")

    code: str


class PromptResponse(BaseModel):
    model_config = ConfigDict(extra="forbid")

    prompt_id: str
    value: str


class SequenceSaveRequest(BaseModel):
    model_config = ConfigDict(extra="forbid")

    workspace: dict[str, Any]


# ---------------------------------------------------------------------------
# Console and state helpers
# ---------------------------------------------------------------------------

def _queue_console_message(output_queue: queue.Queue[str], message: str) -> None:
    """Add a console message without allowing a stalled browser to grow forever."""
    try:
        output_queue.put_nowait(message)
        return
    except queue.Full:
        pass

    # Drop the oldest entry and retry once.
    with contextlib.suppress(queue.Empty):
        output_queue.get_nowait()

    with contextlib.suppress(queue.Full):
        output_queue.put_nowait(message)


def _broadcast_console(message: str) -> None:
    with _console_lock:
        for output_queue in tuple(_console_queues):
            _queue_console_message(output_queue, message)


_run_control.on_change = (
    lambda: _broadcast_console(f"__STATE__:{_run_control.state}")
)


def _run_is_active() -> bool:
    with _run_thread_lock:
        thread_alive = _run_thread is not None and _run_thread.is_alive()
    return thread_alive or _run_control.state in ACTIVE_STATES


# ---------------------------------------------------------------------------
# File and configuration helpers
# ---------------------------------------------------------------------------

def _atomic_write_json(path: Path, payload: Any) -> None:
    """Write JSON to a temporary sibling file, then replace the destination."""
    temporary_path = path.with_suffix(path.suffix + ".tmp")

    with temporary_path.open("w", encoding="utf-8", newline="\n") as handle:
        json.dump(payload, handle, indent=2, ensure_ascii=False)
        handle.write("\n")
        handle.flush()

    temporary_path.replace(path)


def _load_config() -> dict[str, Any]:
    try:
        with CONFIG_PATH.open("r", encoding="utf-8") as handle:
            raw_config = json.load(handle)
    except FileNotFoundError as exc:
        raise RuntimeError(f"Configuration file not found: {CONFIG_PATH}") from exc
    except json.JSONDecodeError as exc:
        raise RuntimeError(
            f"Configuration file is not valid JSON: {CONFIG_PATH}: {exc}"
        ) from exc

    # Validate files loaded from disk using the same model as API submissions.
    validated = ConfigSaveRequest.model_validate(raw_config)
    return validated.model_dump(exclude_none=True)


def _safe_sequence_name(name: str) -> str:
    name = name.strip()
    if not name or not re.fullmatch(r"[A-Za-z0-9 _\-]+", name):
        raise ValueError(
            "Sequence names can only contain letters, numbers, spaces, "
            "hyphens and underscores."
        )
    return name


# ---------------------------------------------------------------------------
# Device helpers
# ---------------------------------------------------------------------------

def _connect_devices(config: dict[str, Any]) -> dict[str, Any]:
    devices: dict[str, Any] = {}

    for entry in config.get("devices", []):
        device_id = entry["device_id"]
        device_type = entry["device_type"]
        kwargs = entry.get("kwargs", {})

        try:
            driver = create_driver(
                device_type,
                device_id,
                on_event=None,
                **kwargs,
            )
            driver.connect()
            devices[device_id] = driver
            print(f"[startup] connected {device_id} ({device_type})")
        except Exception as exc:
            print(
                f"[startup] FAILED to connect {device_id} "
                f"({device_type}): {exc}"
            )

    return devices


def _close_devices(devices: dict[str, Any]) -> None:
    for device_id, driver in devices.items():
        try:
            driver.close()
        except Exception as exc:
            print(f"[shutdown] failed to close {device_id}: {exc}")


def _return_devices_to_safe_state(devices: dict[str, Any]) -> None:
    """
    Call an optional safe_state() hook on every driver.

    Drivers that control hazardous or energised equipment should implement
    safe_state(). A future driver-interface update should make this method
    mandatory for applicable instruments.
    """
    for device_id, driver in devices.items():
        safe_state = getattr(driver, "safe_state", None)
        if not callable(safe_state):
            _broadcast_console(
                f"[safety] {device_id}: driver has no safe_state() hook"
            )
            continue

        try:
            safe_state()
            _broadcast_console(f"[safety] {device_id}: safe state applied")
        except Exception as exc:
            _broadcast_console(
                f"[safety] {device_id}: safe-state command failed: {exc!r}"
            )


def _build_mapping(config: dict[str, Any]) -> DutMapping:
    mapping = DutMapping()

    for entry in config.get("mapping", []):
        mapping.assign(
            entry["device_id"],
            entry["position_id"],
            entry["dut_uid"],
        )

    mapping.lock()
    return mapping


# ---------------------------------------------------------------------------
# Operator prompts
# ---------------------------------------------------------------------------

def _ask_operator(label: str, dut_uid: str, runner: TestRunner) -> str:
    """
    Block the execution thread until the operator answers, Stop is pressed,
    or the configured prompt timeout expires.
    """
    global _prompt_counter

    with _prompt_lock:
        _prompt_counter += 1
        prompt_id = f"p{_prompt_counter}"
        event = threading.Event()
        _pending_prompts[prompt_id] = event

    _broadcast_console(f"__PROMPT__:{prompt_id}:{label}")
    deadline = time.monotonic() + PROMPT_TIMEOUT_SECONDS

    try:
        while not event.wait(timeout=0.5):
            if _run_control.state == "stop_requested":
                raise StopRequested(f"prompt cancelled: {label}")

            if time.monotonic() >= deadline:
                raise TimeoutError(
                    f"operator prompt timed out after "
                    f"{PROMPT_TIMEOUT_SECONDS:.0f} seconds: {label}"
                )

        with _prompt_lock:
            value = _prompt_answers.get(prompt_id, "")

        runner.record_metadata(dut_uid, label, value)
        return value
    finally:
        with _prompt_lock:
            _pending_prompts.pop(prompt_id, None)
            _prompt_answers.pop(prompt_id, None)


# ---------------------------------------------------------------------------
# Generated-code validation
# ---------------------------------------------------------------------------

_ALLOWED_CALLS = {
    "set",
    "get",
    "wait",
    "log",
    "assert_that",
    "ask_operator",
    "range",
    "abs",
    "_checkpoint",
    "_report_iteration",
}

_ALLOWED_AST_NODES = (
    ast.Module,
    ast.Expr,
    ast.Assign,
    ast.AugAssign,
    ast.For,
    ast.While,
    ast.If,
    ast.IfExp,
    ast.Break,
    ast.Continue,
    ast.Pass,
    ast.Call,
    ast.Name,
    ast.Constant,
    ast.BinOp,
    ast.UnaryOp,
    ast.BoolOp,
    ast.Compare,
    ast.keyword,
    ast.Load,
    ast.Store,
    ast.Add,
    ast.Sub,
    ast.Mult,
    ast.Div,
    ast.FloorDiv,
    ast.Mod,
    ast.Pow,
    ast.UAdd,
    ast.USub,
    ast.Not,
    ast.And,
    ast.Or,
    ast.Eq,
    ast.NotEq,
    ast.Lt,
    ast.LtE,
    ast.Gt,
    ast.GtE,
)


class _GeneratedCodeValidator(ast.NodeVisitor):
    """Reject Python constructs that are not required by the Blockly toolbox."""

    def generic_visit(self, node: ast.AST) -> None:
        if not isinstance(node, _ALLOWED_AST_NODES):
            raise ValueError(
                f"Generated code contains unsupported syntax: "
                f"{type(node).__name__}"
            )
        super().generic_visit(node)

    def visit_Call(self, node: ast.Call) -> None:
        if not isinstance(node.func, ast.Name):
            raise ValueError(
                "Generated code may only call approved top-level functions"
            )

        if node.func.id not in _ALLOWED_CALLS:
            raise ValueError(
                f"Generated code calls an unsupported function: "
                f"{node.func.id}"
            )

        self.generic_visit(node)

    def visit_Name(self, node: ast.Name) -> None:
        if node.id.startswith("__"):
            raise ValueError("Generated code may not use dunder names")
        self.generic_visit(node)

    def visit_Assign(self, node: ast.Assign) -> None:
        for target in node.targets:
            if not isinstance(target, ast.Name):
                raise ValueError(
                    "Generated code may only assign to simple variables"
                )
        self.generic_visit(node)

    def visit_AugAssign(self, node: ast.AugAssign) -> None:
        if not isinstance(node.target, ast.Name):
            raise ValueError(
                "Generated code may only update simple variables"
            )
        self.generic_visit(node)


def _validate_generated_code(tree: ast.AST) -> None:
    _GeneratedCodeValidator().visit(tree)


# ---------------------------------------------------------------------------
# Application lifecycle
# ---------------------------------------------------------------------------

@app.on_event("startup")
def startup() -> None:
    global _config, _devices

    config = _load_config()
    devices = _connect_devices(config)

    with _device_lock:
        _config = config
        _devices = devices


@app.on_event("shutdown")
def shutdown() -> None:
    if _run_is_active():
        _run_control.request_stop()

        with _run_thread_lock:
            thread = _run_thread

        if thread is not None and thread.is_alive():
            thread.join(timeout=5.0)

    with _device_lock:
        _return_devices_to_safe_state(_devices)
        _close_devices(_devices)


# ---------------------------------------------------------------------------
# Pages
# ---------------------------------------------------------------------------

@app.get("/")
def index() -> FileResponse:
    return FileResponse(str(BASE_DIR / "static" / "index.html"))


@app.get("/devices")
def devices_page() -> FileResponse:
    return FileResponse(str(BASE_DIR / "static" / "devices.html"))


@app.get("/about")
def about_page() -> FileResponse:
    return FileResponse(str(BASE_DIR / "static" / "about.html"))


@app.get("/supported-devices")
def supported_devices_page() -> FileResponse:
    return FileResponse(str(BASE_DIR / "static" / "supported-devices.html"))


# ---------------------------------------------------------------------------
# Device and configuration API
# ---------------------------------------------------------------------------

@app.get("/api/devices")
def api_devices() -> JSONResponse:
    result: list[dict[str, Any]] = []

    with _device_lock:
        for device_id, driver in _devices.items():
            try:
                caps = driver.capabilities()
            except Exception as exc:
                result.append({
                    "device_id": device_id,
                    "error": str(exc),
                    "positions": [],
                })
                continue

            result.append({
                "device_id": caps.device_id,
                "device_type": caps.device_type,
                "display_name": caps.display_name,
                "positions": [
                    {
                        "id": position.id,
                        "label": position.label,
                        "kind": position.kind.value,
                        "unit": position.unit,
                    }
                    for position in caps.positions
                ],
            })

    return JSONResponse(result)


@app.get("/api/duts")
def api_duts() -> JSONResponse:
    with _device_lock:
        duts = sorted({
            entry["dut_uid"]
            for entry in _config.get("mapping", [])
        })
    return JSONResponse(duts)


@app.get("/api/device_types")
def api_device_types() -> JSONResponse:
    return JSONResponse(DEVICE_CATALOG)


@app.get("/api/config")
def api_config_get() -> JSONResponse:
    with _device_lock:
        snapshot = json.loads(json.dumps(_config))
    return JSONResponse(snapshot)


@app.post("/api/config")
def api_config_save(req: ConfigSaveRequest) -> JSONResponse:
    if _run_is_active():
        return JSONResponse(
            {
                "detail": (
                    "Can't change the configuration while a run is active "
                    f"(state: {_run_control.state})"
                )
            },
            status_code=409,
        )

    new_config = req.model_dump(exclude_none=True)
    _atomic_write_json(CONFIG_PATH, new_config)
    return JSONResponse({"status": "ok"})


@app.post("/api/reconnect")
def api_reconnect() -> JSONResponse:
    global _config, _devices

    if _run_is_active():
        return JSONResponse(
            {
                "detail": (
                    "Can't reconnect devices while a run is active "
                    f"(state: {_run_control.state})"
                )
            },
            status_code=409,
        )

    try:
        new_config = _load_config()
    except (RuntimeError, ValueError) as exc:
        return JSONResponse({"detail": str(exc)}, status_code=400)

    with _device_lock:
        old_devices = _devices
        _close_devices(old_devices)

        new_devices = _connect_devices(new_config)
        _config = new_config
        _devices = new_devices

    failed = [
        entry["device_id"]
        for entry in new_config.get("devices", [])
        if entry["device_id"] not in new_devices
    ]

    return JSONResponse({
        "status": "ok",
        "connected": list(new_devices.keys()),
        "failed": failed,
    })


@app.get("/api/live_values")
def api_live_values() -> JSONResponse:
    """
    Read current values only while no test is active.

    Individual read failures are returned to the browser instead of being
    silently discarded.
    """
    if _run_is_active():
        return JSONResponse({
            "busy": True,
            "values": {},
            "errors": {},
        })

    values: dict[str, dict[str, Any]] = {}
    errors: dict[str, dict[str, str]] = {}

    with _device_lock:
        for device_id, driver in _devices.items():
            device_values: dict[str, Any] = {}
            device_errors: dict[str, str] = {}

            try:
                positions = driver.capabilities().positions
            except Exception as exc:
                errors[device_id] = {"_capabilities": str(exc)}
                continue

            for position in positions:
                try:
                    device_values[position.id] = driver.read(position.id)
                except (NotImplementedError, KeyError):
                    # Expected for positions that are write-only or unsupported.
                    continue
                except Exception as exc:
                    device_errors[position.id] = str(exc)

            values[device_id] = device_values
            if device_errors:
                errors[device_id] = device_errors

    return JSONResponse({
        "busy": False,
        "values": values,
        "errors": errors,
    })


@app.post("/api/set_position")
def api_set_position(req: SetPositionRequest) -> JSONResponse:
    if _run_is_active():
        return JSONResponse(
            {
                "detail": (
                    "Can't change devices manually while a run is active "
                    f"(state: {_run_control.state})"
                )
            },
            status_code=409,
        )

    with _device_lock:
        driver = _devices.get(req.device_id)
        if driver is None:
            return JSONResponse(
                {
                    "detail": (
                        f"no such connected device '{req.device_id}'"
                    )
                },
                status_code=404,
            )

        try:
            driver.write(req.position_id, req.value)
        except Exception as exc:
            return JSONResponse({"detail": str(exc)}, status_code=500)

    return JSONResponse({"status": "ok"})


# ---------------------------------------------------------------------------
# Run execution
# ---------------------------------------------------------------------------

def _interruptible_wait(seconds: float) -> None:
    """
    Sleep in short intervals so Pause and Stop remain responsive during long
    waits such as chamber soak periods.
    """
    seconds = float(seconds)
    if seconds < 0:
        raise ValueError("wait time must not be negative")

    _broadcast_console(f"[wait] {seconds}s")
    deadline = time.monotonic() + seconds

    while True:
        remaining = deadline - time.monotonic()
        if remaining <= 0:
            break

        _run_control.checkpoint(
            f"wait ({remaining:.1f}s remaining)"
        )
        time.sleep(min(0.2, remaining))


def _execute_run(run_id: str, code: str) -> None:
    global _run_thread

    final_state = "finished"
    runner: TestRunner | None = None
    devices_snapshot: dict[str, Any] = {}

    try:
        # Hold the device lock only long enough to take stable snapshots and
        # attach this run's event logger. The generated procedure may run for
        # hours, so it must execute outside the lock; otherwise read-only API
        # requests such as /api/devices, /api/duts and /api/config would block
        # until the entire test completed.
        with _device_lock:
            config_snapshot = json.loads(json.dumps(_config))
            devices_snapshot = dict(_devices)

            mapping = _build_mapping(config_snapshot)

            runner = TestRunner.for_existing_devices(
                run_id=run_id,
                mapping=mapping,
                devices=devices_snapshot,
                output_dir=str(RUNS_DIR),
                console=_broadcast_console,
            )

        exec_globals = {
            "__builtins__": {},
            "set": runner.set,
            "get": runner.get,
            "wait": _interruptible_wait,
            "log": runner.log,
            "assert_that": runner.assert_that,
            "ask_operator": (
                lambda label, dut_uid: _ask_operator(
                    label,
                    dut_uid,
                    runner,
                )
            ),
            "range": range,
            "abs": abs,
            "_checkpoint": _run_control.checkpoint,
            "_report_iteration": (
                lambda label, number: _broadcast_console(
                    f"[loop] {label} — iteration {number}"
                )
            ),
        }

        _broadcast_console(f"=== run {run_id} starting ===")

        tree = instrument_source(code)
        _validate_generated_code(tree)
        compiled = compile(tree, "<generated>", "exec")
        exec(compiled, exec_globals, {})

        _broadcast_console(f"=== run {run_id} finished ===")

    except StopRequested:
        _broadcast_console(
            f"=== run {run_id} stopped by user ==="
        )
        final_state = "stopped"

    except AssertionFailure as exc:
        _broadcast_console(
            f"=== run {run_id} STOPPED — assertion failed: {exc} ==="
        )
        final_state = "failed"

    except Exception as exc:
        _broadcast_console(
            f"=== run {run_id} ERROR: {exc!r} ==="
        )
        _broadcast_console(traceback.format_exc())
        final_state = "error"

    finally:
        # Clean up the same device instances that were bound to this run.
        # Reacquire the lock only for the short lifecycle operation.
        with _device_lock:
            _return_devices_to_safe_state(devices_snapshot)

            if runner is not None:
                try:
                    runner.release_devices()
                except Exception:
                    _broadcast_console(
                        "[cleanup] runner.release_devices() failed"
                    )
                    _broadcast_console(traceback.format_exc())

        _run_control.finish(final_state)

        with _run_thread_lock:
            _run_thread = None


@app.post("/api/run")
def api_run(req: RunRequest) -> JSONResponse:
    global _run_thread

    with _run_thread_lock:
        if (
            _run_thread is not None
            and _run_thread.is_alive()
        ) or _run_control.state in ACTIVE_STATES:
            return JSONResponse(
                {
                    "detail": (
                        "A run is already in progress "
                        f"(state: {_run_control.state})"
                    )
                },
                status_code=409,
            )

        if not _run_control.start():
            return JSONResponse(
                {
                    "detail": (
                        "A run is already in progress "
                        f"(state: {_run_control.state})"
                    )
                },
                status_code=409,
            )

        run_id = datetime.now(timezone.utc).strftime(
            "%Y%m%d_%H%M%S_%f"
        )

        _run_thread = threading.Thread(
            target=_execute_run,
            args=(run_id, req.code),
            name=f"tiab-run-{run_id}",
            daemon=True,
        )
        _run_thread.start()

    return JSONResponse({
        "status": "started",
        "run_id": run_id,
    })


@app.get("/api/status")
def api_status() -> JSONResponse:
    return JSONResponse({
        "state": _run_control.state,
        "active": _run_is_active(),
    })


@app.post("/api/control/pause")
def api_pause() -> JSONResponse:
    if _run_control.state == "running":
        _run_control.request_pause()
    return JSONResponse({"state": _run_control.state})


@app.post("/api/control/resume")
def api_resume() -> JSONResponse:
    if _run_control.state in {"paused", "pause_requested"}:
        _run_control.request_resume()
    return JSONResponse({"state": _run_control.state})


@app.post("/api/control/step")
def api_step() -> JSONResponse:
    if _run_control.state == "paused":
        _run_control.request_step()
    return JSONResponse({"state": _run_control.state})


@app.post("/api/control/stop")
def api_stop() -> JSONResponse:
    if _run_is_active() and _run_control.state != "stop_requested":
        _run_control.request_stop()
    return JSONResponse({"state": _run_control.state})


@app.post("/api/control/prompt_response")
def api_prompt_response(req: PromptResponse) -> JSONResponse:
    with _prompt_lock:
        event = _pending_prompts.get(req.prompt_id)
        if event is None:
            return JSONResponse(
                {"detail": "no such pending prompt"},
                status_code=404,
            )

        _prompt_answers[req.prompt_id] = req.value
        event.set()

    return JSONResponse({"status": "ok"})


# ---------------------------------------------------------------------------
# Saved sequences
# ---------------------------------------------------------------------------

@app.get("/api/sequences")
def api_sequences_list() -> JSONResponse:
    names = sorted(path.stem for path in SEQUENCES_DIR.glob("*.json"))
    return JSONResponse(names)


@app.get("/api/sequences/{name}")
def api_sequences_get(name: str) -> JSONResponse:
    try:
        safe_name = _safe_sequence_name(name)
    except ValueError as exc:
        return JSONResponse({"detail": str(exc)}, status_code=400)

    path = SEQUENCES_DIR / f"{safe_name}.json"

    if not path.exists():
        return JSONResponse(
            {"detail": f"no sequence named '{safe_name}'"},
            status_code=404,
        )

    try:
        with path.open("r", encoding="utf-8") as handle:
            workspace = json.load(handle)
    except json.JSONDecodeError as exc:
        return JSONResponse(
            {"detail": f"saved sequence is not valid JSON: {exc}"},
            status_code=500,
        )

    return JSONResponse(workspace)


@app.post("/api/sequences/{name}")
def api_sequences_save(
    name: str,
    req: SequenceSaveRequest,
) -> JSONResponse:
    try:
        safe_name = _safe_sequence_name(name)
    except ValueError as exc:
        return JSONResponse({"detail": str(exc)}, status_code=400)

    path = SEQUENCES_DIR / f"{safe_name}.json"
    _atomic_write_json(path, req.workspace)

    return JSONResponse({
        "status": "ok",
        "name": safe_name,
    })


# ---------------------------------------------------------------------------
# Console WebSocket
# ---------------------------------------------------------------------------

@app.websocket("/ws/console")
async def ws_console(websocket: WebSocket) -> None:
    await websocket.accept()

    output_queue: queue.Queue[str] = queue.Queue(
        maxsize=CONSOLE_QUEUE_LIMIT
    )

    with _console_lock:
        _console_queues.append(output_queue)

    await websocket.send_text(
        f"__STATE__:{_run_control.state}"
    )

    try:
        while True:
            try:
                message = output_queue.get_nowait()
            except queue.Empty:
                await asyncio.sleep(0.1)
                continue

            await websocket.send_text(message)

    except WebSocketDisconnect:
        pass

    finally:
        with _console_lock:
            if output_queue in _console_queues:
                _console_queues.remove(output_queue)


if __name__ == "__main__":
    import uvicorn

    uvicorn.run(
        "webapp.server:app",
        host="127.0.0.1",
        port=8765,
        reload=False,
    )
