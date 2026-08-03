"""
Pause, step and stop coordination for a running Test in a Box procedure.

The execution thread calls :meth:`RunControl.checkpoint` between generated
statements. HTTP control endpoints request state changes; checkpoint() performs
the actual pause, single-step and stop behaviour.

Typical state flow::

    idle
      -> running
      -> pause_requested
      -> paused
      -> step
      -> paused
      -> running
      -> finished

A running, pausing, paused or stepping procedure may also move to
``stop_requested`` and then ``stopped``. Execution failures may finish in
``failed`` or ``error``.

Callbacks registered through ``on_change`` are always invoked after the
internal condition lock has been released.
"""

from __future__ import annotations

import threading
from collections.abc import Callable


class StopRequested(Exception):
    """Raised in the execution thread when the operator requests Stop."""


class RunControl:
    """Thread-safe state machine for controlling one test run at a time."""

    ACTIVE_STATES = frozenset({
        "running",
        "pause_requested",
        "paused",
        "step",
        "stop_requested",
    })

    STARTABLE_STATES = frozenset({
        "idle",
        "finished",
        "stopped",
        "failed",
        "error",
    })

    FINAL_STATES = frozenset({
        "finished",
        "stopped",
        "failed",
        "error",
    })

    def __init__(self) -> None:
        self._cond = threading.Condition(threading.Lock())
        self._state = "idle"

        # Optional zero-argument callback invoked after each real state change.
        self.on_change: Callable[[], None] | None = None

    @property
    def state(self) -> str:
        """Return the current state using the same lock as state transitions."""
        with self._cond:
            return self._state

    def is_active(self) -> bool:
        """Return True while a run still owns the execution state machine."""
        with self._cond:
            return self._state in self.ACTIVE_STATES

    def _set_state_locked(self, new_state: str) -> bool:
        """
        Change state while ``self._cond`` is held.

        Returns True only when the value actually changed. The caller is
        responsible for invoking the callback after releasing the lock.
        """
        if self._state == new_state:
            return False

        self._state = new_state
        self._cond.notify_all()
        return True

    def _emit_change(self, changed: bool) -> None:
        """Invoke the state callback outside the condition lock."""
        if not changed:
            return

        callback = self.on_change
        if callback is not None:
            callback()

    # ------------------------------------------------------------------
    # Called by the execution thread
    # ------------------------------------------------------------------

    def checkpoint(self, label: str = "") -> None:
        """
        Honour pending pause, step and stop requests.

        A ``step`` request allows the statement immediately following this
        checkpoint to execute, then returns the controller to ``paused`` before
        the statement runs. The next checkpoint therefore blocks again.
        """
        while True:
            changed = False
            should_return = False

            with self._cond:
                if self._state == "stop_requested":
                    raise StopRequested(label)

                if self._state == "pause_requested":
                    changed = self._set_state_locked("paused")

                elif self._state == "paused":
                    # Timeout protects against a missed notification and gives
                    # the execution thread regular opportunities to re-check.
                    self._cond.wait(timeout=0.5)
                    continue

                elif self._state == "step":
                    # Permit exactly one generated statement, then pause again.
                    changed = self._set_state_locked("paused")
                    should_return = True

                else:
                    # running, or a final state reached during cleanup.
                    should_return = True

            self._emit_change(changed)

            if should_return:
                return

            # A pause request has just become paused. Loop once more so this
            # checkpoint enters the paused wait state.

    # ------------------------------------------------------------------
    # Called by the API/control thread
    # ------------------------------------------------------------------

    def start(self) -> bool:
        """
        Start a new run.

        Returns False while an existing run is active, including the interval
        after Stop has been requested but before the execution thread finishes.
        """
        with self._cond:
            if self._state not in self.STARTABLE_STATES:
                return False
            changed = self._set_state_locked("running")

        self._emit_change(changed)
        return True

    def request_pause(self) -> bool:
        """Request a pause. Returns True when the state changed."""
        with self._cond:
            changed = False
            if self._state == "running":
                changed = self._set_state_locked("pause_requested")

        self._emit_change(changed)
        return changed

    def request_resume(self) -> bool:
        """Resume a paused or not-yet-paused run."""
        with self._cond:
            changed = False
            if self._state in {"paused", "pause_requested"}:
                changed = self._set_state_locked("running")

        self._emit_change(changed)
        return changed

    def request_step(self) -> bool:
        """Allow one generated statement to execute from the paused state."""
        with self._cond:
            changed = False
            if self._state == "paused":
                changed = self._set_state_locked("step")

        self._emit_change(changed)
        return changed

    def request_stop(self) -> bool:
        """
        Request that the active run stop at its next checkpoint.

        Calling this while idle or after a run has finished is a no-op.
        """
        with self._cond:
            changed = False
            if self._state in {
                "running",
                "pause_requested",
                "paused",
                "step",
            }:
                changed = self._set_state_locked("stop_requested")

        self._emit_change(changed)
        return changed

    def finish(self, final_state: str) -> None:
        """Record the final state of the current run."""
        if final_state not in self.FINAL_STATES:
            raise ValueError(
                f"invalid final state {final_state!r}; "
                f"expected one of {sorted(self.FINAL_STATES)}"
            )

        with self._cond:
            changed = self._set_state_locked(final_state)

        self._emit_change(changed)
