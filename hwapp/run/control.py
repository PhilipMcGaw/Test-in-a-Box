"""
Pause / Step / Stop coordination for a running test script.

The execution thread calls checkpoint(label) between every generated
statement (see instrument.py for how those checkpoints get inserted).
The HTTP control endpoints (pause/resume/step/stop) just flip `state`
under a lock and notify — checkpoint() does all the actual waiting.

State machine:
  idle -> running -> (pause_requested -> paused -> (step -> paused)* )* -> running -> finished
  paused branch can also go: -> stop_requested -> stopped
  running -> stop_requested -> stopped
  any error during execution -> error
"""

from __future__ import annotations

import threading


class StopRequested(Exception):
    """Raised inside the execution thread when the user hits Stop."""


class RunControl:
    def __init__(self):
        self._lock = threading.Lock()
        self._cond = threading.Condition(self._lock)
        self.state = "idle"
        self.on_change = None  # optional callable, invoked (without the lock held) on any state change

    def _set_state(self, new_state: str) -> None:
        self.state = new_state
        if self.on_change is not None:
            self.on_change()

    # -- called by the execution thread, between every statement ----------
    def checkpoint(self, label: str = "") -> None:
        with self._cond:
            if self.state == "pause_requested":
                self._set_state("paused")
                self._cond.notify_all()
            while self.state == "paused":
                self._cond.wait(timeout=0.5)
            if self.state == "step":
                # let exactly this one statement through, then pause again
                self._set_state("paused")
            if self.state == "stop_requested":
                raise StopRequested(label)

    # -- called by the HTTP control endpoints ------------------------------
    def start(self) -> bool:
        """Returns False if a run is already active."""
        with self._cond:
            if self.state in ("running", "paused", "pause_requested", "step"):
                return False
            self._set_state("running")
            return True

    def request_pause(self) -> None:
        with self._cond:
            if self.state == "running":
                self._set_state("pause_requested")

    def request_resume(self) -> None:
        with self._cond:
            if self.state in ("paused", "pause_requested"):
                self._set_state("running")
                self._cond.notify_all()

    def request_step(self) -> None:
        with self._cond:
            if self.state == "paused":
                self._set_state("step")
                self._cond.notify_all()

    def request_stop(self) -> None:
        with self._cond:
            self._set_state("stop_requested")
            self._cond.notify_all()

    def finish(self, final_state: str) -> None:
        with self._cond:
            self._set_state(final_state)
            self._cond.notify_all()
