"""
Local web server for Test in a Box.

Run with (from the project root, portable Python):
    python -m webapp.server

Then open http://127.0.0.1:8765 in a browser. Everything — the Blockly
library, the page, the API — is served from this one process on
localhost, so no internet access is needed once the Python packages are
installed, and no admin rights are needed to run it (it's just a normal
user-level process listening on a local port).

Devices to connect (real or mock) and the DUT position mapping both live
in config.json next to this file — edit that file to point at your real
hardware instead of the mock demo devices.
"""

from __future__ import annotations

import asyncio
import contextlib
import io
import json
import queue
import re
import sys
import threading
import time
from datetime import datetime, timezone
from pathlib import Path

from fastapi import FastAPI, WebSocket, WebSocketDisconnect
from fastapi.responses import FileResponse, JSONResponse
from fastapi.staticfiles import StaticFiles
from pydantic import BaseModel

# make sure every driver module registers itself
import hwapp.drivers.mock          # noqa: F401
import hwapp.drivers.scpi_generic  # noqa: F401
import hwapp.drivers.seeit_relay   # noqa: F401
import hwapp.drivers.aimtti_psu    # noqa: F401
try:
    import hwapp.drivers.pico_tc08   # noqa: F401
    import hwapp.drivers.pico_adc    # noqa: F401
except Exception as exc:  # picosdk may not be installed / driver not present
    print(f"[startup] Pico drivers not fully available: {exc}")

from hwapp.drivers.registry import create_driver
from hwapp.run.mapping import DutMapping
from hwapp.run.runner import TestRunner, AssertionFailure
from hwapp.run.control import RunControl, StopRequested
from hwapp.run.instrument import instrument_source

BASE_DIR = Path(__file__).resolve().parent
CONFIG_PATH = BASE_DIR / "config.json"
RUNS_DIR = BASE_DIR / "runs"
SEQUENCES_DIR = BASE_DIR / "sequences"
SEQUENCES_DIR.mkdir(exist_ok=True)

app = FastAPI()
app.mount("/static", StaticFiles(directory=str(BASE_DIR / "static")), name="static")

_devices: dict[str, object] = {}
_config: dict = {}
_console_queues: list[queue.Queue] = []
_console_lock = threading.Lock()
_run_control = RunControl()
_run_control.on_change = lambda: _broadcast_console(f"__STATE__:{_run_control.state}")

_prompt_lock = threading.Lock()
_pending_prompts: dict[str, threading.Event] = {}
_prompt_answers: dict[str, str] = {}
_prompt_counter = 0


def _broadcast_console(message: str) -> None:
    with _console_lock:
        for q in _console_queues:
            q.put(message)


def _broadcast_state() -> None:
    _broadcast_console(f"__STATE__:{_run_control.state}")


def _load_config() -> dict:
    with open(CONFIG_PATH) as f:
        return json.load(f)


def _ask_operator(label: str, dut_uid: str, runner: TestRunner) -> str:
    """
    Blocks the execution thread until the operator answers a prompt in the
    browser (or Stop is pressed, in which case this raises StopRequested).
    """
    global _prompt_counter
    with _prompt_lock:
        _prompt_counter += 1
        prompt_id = f"p{_prompt_counter}"
        event = threading.Event()
        _pending_prompts[prompt_id] = event

    _broadcast_console(f"__PROMPT__:{prompt_id}:{label}")

    while not event.wait(timeout=0.5):
        if _run_control.state == "stop_requested":
            with _prompt_lock:
                _pending_prompts.pop(prompt_id, None)
                _prompt_answers.pop(prompt_id, None)
            raise StopRequested(f"prompt cancelled: {label}")

    with _prompt_lock:
        value = _prompt_answers.pop(prompt_id, "")
        _pending_prompts.pop(prompt_id, None)

    runner.record_metadata(dut_uid, label, value)
    return value


def _safe_sequence_name(name: str) -> str:
    name = name.strip()
    if not name or not re.fullmatch(r"[A-Za-z0-9 _\-]+", name):
        raise ValueError(
            "Sequence names can only contain letters, numbers, spaces, "
            "hyphens, and underscores."
        )
    return name


def _connect_devices(config: dict) -> dict[str, object]:
    devices = {}
    for entry in config.get("devices", []):
        device_id = entry["device_id"]
        device_type = entry["device_type"]
        kwargs = entry.get("kwargs", {})
        try:
            driver = create_driver(device_type, device_id, on_event=None, **kwargs)
            driver.connect()
            devices[device_id] = driver
            print(f"[startup] connected {device_id} ({device_type})")
        except Exception as exc:
            print(f"[startup] FAILED to connect {device_id} ({device_type}): {exc}")
    return devices


def _build_mapping(config: dict) -> DutMapping:
    mapping = DutMapping()
    for entry in config.get("mapping", []):
        mapping.assign(entry["device_id"], entry["position_id"], entry["dut_uid"])
    mapping.lock()
    return mapping


@app.on_event("startup")
def startup() -> None:
    global _config, _devices
    _config = _load_config()
    _devices = _connect_devices(_config)


@app.on_event("shutdown")
def shutdown() -> None:
    for driver in _devices.values():
        with contextlib.suppress(Exception):
            driver.close()


@app.get("/")
def index() -> FileResponse:
    return FileResponse(str(BASE_DIR / "static" / "index.html"))


@app.get("/api/devices")
def api_devices() -> JSONResponse:
    result = []
    for device_id, driver in _devices.items():
        caps = driver.capabilities()
        result.append({
            "device_id": caps.device_id,
            "device_type": caps.device_type,
            "display_name": caps.display_name,
            "positions": [
                {"id": p.id, "label": p.label, "kind": p.kind.value, "unit": p.unit}
                for p in caps.positions
            ],
        })
    return JSONResponse(result)


@app.get("/api/duts")
def api_duts() -> JSONResponse:
    duts = sorted({entry["dut_uid"] for entry in _config.get("mapping", [])})
    return JSONResponse(duts)


class RunRequest(BaseModel):
    code: str


def _interruptible_wait(seconds: float) -> None:
    """
    Like runner.wait(), but checks pause/stop every 0.2s instead of only
    between statements — otherwise a `wait(3600)` block would ignore Pause
    and Stop for up to an hour.
    """
    _broadcast_console(f"[wait] {seconds}s")
    remaining = float(seconds)
    interval = 0.2
    while remaining > 0:
        _run_control.checkpoint(f"wait ({remaining:.1f}s remaining)")
        step = min(interval, remaining)
        time.sleep(step)
        remaining -= step


def _execute_run(run_id: str, code: str) -> None:
    mapping = _build_mapping(_config)

    runner = TestRunner.for_existing_devices(
        run_id=run_id, mapping=mapping, devices=_devices,
        output_dir=str(RUNS_DIR), console=_broadcast_console,
    )

    exec_globals = {
        "set": runner.set,
        "get": runner.get,
        "wait": _interruptible_wait,
        "log": runner.log,
        "assert_that": runner.assert_that,
        "ask_operator": lambda label, dut_uid: _ask_operator(label, dut_uid, runner),
        "_checkpoint": _run_control.checkpoint,
        "_report_iteration": lambda label, n: _broadcast_console(f"[loop] {label} — iteration {n}"),
    }

    _broadcast_console(f"=== run {run_id} starting ===")
    final_state = "finished"
    try:
        tree = instrument_source(code)
        compiled = compile(tree, "<generated>", "exec")
        exec(compiled, exec_globals, {})
        _broadcast_console(f"=== run {run_id} finished ===")
    except StopRequested:
        _broadcast_console(f"=== run {run_id} stopped by user ===")
        final_state = "stopped"
    except AssertionFailure as exc:
        _broadcast_console(f"=== run {run_id} STOPPED — assertion failed: {exc} ===")
        final_state = "failed"
    except Exception as exc:
        _broadcast_console(f"=== run {run_id} ERROR: {exc!r} ===")
        final_state = "error"
    finally:
        runner.release_devices()
        _run_control.finish(final_state)


@app.post("/api/run")
def api_run(req: RunRequest) -> JSONResponse:
    if not _run_control.start():
        return JSONResponse(
            {"detail": f"A run is already in progress (state: {_run_control.state})"},
            status_code=409,
        )
    run_id = datetime.now(timezone.utc).strftime("%Y%m%d_%H%M%S")
    thread = threading.Thread(target=_execute_run, args=(run_id, req.code), daemon=True)
    thread.start()
    return JSONResponse({"status": "started", "run_id": run_id})


@app.get("/api/status")
def api_status() -> JSONResponse:
    return JSONResponse({"state": _run_control.state})


@app.post("/api/control/pause")
def api_pause() -> JSONResponse:
    _run_control.request_pause()
    return JSONResponse({"state": _run_control.state})


@app.post("/api/control/resume")
def api_resume() -> JSONResponse:
    _run_control.request_resume()
    return JSONResponse({"state": _run_control.state})


@app.post("/api/control/step")
def api_step() -> JSONResponse:
    _run_control.request_step()
    return JSONResponse({"state": _run_control.state})


@app.post("/api/control/stop")
def api_stop() -> JSONResponse:
    _run_control.request_stop()
    return JSONResponse({"state": _run_control.state})


class PromptResponse(BaseModel):
    prompt_id: str
    value: str


@app.post("/api/control/prompt_response")
def api_prompt_response(req: PromptResponse) -> JSONResponse:
    with _prompt_lock:
        event = _pending_prompts.get(req.prompt_id)
        if event is None:
            return JSONResponse({"detail": "no such pending prompt"}, status_code=404)
        _prompt_answers[req.prompt_id] = req.value
    event.set()
    return JSONResponse({"status": "ok"})


@app.get("/api/sequences")
def api_sequences_list() -> JSONResponse:
    names = sorted(p.stem for p in SEQUENCES_DIR.glob("*.json"))
    return JSONResponse(names)


@app.get("/api/sequences/{name}")
def api_sequences_get(name: str) -> JSONResponse:
    try:
        safe_name = _safe_sequence_name(name)
    except ValueError as exc:
        return JSONResponse({"detail": str(exc)}, status_code=400)
    path = SEQUENCES_DIR / f"{safe_name}.json"
    if not path.exists():
        return JSONResponse({"detail": f"no sequence named '{safe_name}'"}, status_code=404)
    with open(path) as f:
        return JSONResponse(json.load(f))


class SequenceSaveRequest(BaseModel):
    workspace: dict


@app.post("/api/sequences/{name}")
def api_sequences_save(name: str, req: SequenceSaveRequest) -> JSONResponse:
    try:
        safe_name = _safe_sequence_name(name)
    except ValueError as exc:
        return JSONResponse({"detail": str(exc)}, status_code=400)
    path = SEQUENCES_DIR / f"{safe_name}.json"
    with open(path, "w") as f:
        json.dump(req.workspace, f, indent=2)
    return JSONResponse({"status": "ok", "name": safe_name})


@app.websocket("/ws/console")
async def ws_console(websocket: WebSocket) -> None:
    await websocket.accept()
    q: queue.Queue = queue.Queue()
    with _console_lock:
        _console_queues.append(q)
    await websocket.send_text(f"__STATE__:{_run_control.state}")
    try:
        while True:
            try:
                message = q.get_nowait()
                await websocket.send_text(message)
            except queue.Empty:
                await asyncio.sleep(0.1)
    except WebSocketDisconnect:
        pass
    finally:
        with _console_lock:
            if q in _console_queues:
                _console_queues.remove(q)


if __name__ == "__main__":
    import uvicorn
    uvicorn.run("webapp.server:app", host="127.0.0.1", port=8765, reload=False)
