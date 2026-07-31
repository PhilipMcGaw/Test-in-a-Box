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
try:
    import hwapp.drivers.pico_tc08   # noqa: F401
    import hwapp.drivers.pico_adc    # noqa: F401
except Exception as exc:  # picosdk may not be installed / driver not present
    print(f"[startup] Pico drivers not fully available: {exc}")

from hwapp.drivers.registry import create_driver
from hwapp.run.mapping import DutMapping
from hwapp.run.runner import TestRunner, AssertionFailure

BASE_DIR = Path(__file__).resolve().parent
CONFIG_PATH = BASE_DIR / "config.json"
RUNS_DIR = BASE_DIR / "runs"

app = FastAPI()
app.mount("/static", StaticFiles(directory=str(BASE_DIR / "static")), name="static")

_devices: dict[str, object] = {}
_config: dict = {}
_console_queues: list[queue.Queue] = []
_console_lock = threading.Lock()


def _broadcast_console(message: str) -> None:
    with _console_lock:
        for q in _console_queues:
            q.put(message)


def _load_config() -> dict:
    with open(CONFIG_PATH) as f:
        return json.load(f)


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


class RunRequest(BaseModel):
    code: str


@app.post("/api/run")
def api_run(req: RunRequest) -> JSONResponse:
    run_id = datetime.now(timezone.utc).strftime("%Y%m%d_%H%M%S")
    mapping = _build_mapping(_config)

    def console(message: str) -> None:
        _broadcast_console(message)

    runner = TestRunner.for_existing_devices(
        run_id=run_id, mapping=mapping, devices=_devices,
        output_dir=str(RUNS_DIR), console=console,
    )

    exec_globals = {
        "set": runner.set,
        "get": runner.get,
        "wait": runner.wait,
        "log": runner.log,
        "assert_that": runner.assert_that,
    }

    console(f"=== run {run_id} starting ===")
    try:
        exec(compile(req.code, "<generated>", "exec"), exec_globals, {})
        console(f"=== run {run_id} finished ===")
    except AssertionFailure as exc:
        console(f"=== run {run_id} STOPPED — assertion failed: {exc} ===")
        return JSONResponse({"status": "failed", "run_id": run_id}, status_code=200)
    except Exception as exc:
        console(f"=== run {run_id} ERROR: {exc!r} ===")
        return JSONResponse({"detail": str(exc)}, status_code=500)
    finally:
        runner.release_devices()

    return JSONResponse({"status": "ok", "run_id": run_id})


@app.websocket("/ws/console")
async def ws_console(websocket: WebSocket) -> None:
    await websocket.accept()
    q: queue.Queue = queue.Queue()
    with _console_lock:
        _console_queues.append(q)
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
