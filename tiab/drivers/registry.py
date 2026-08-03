"""
Driver registry.

The registry maps driver type names used by the Instrument Library to the
corresponding Python driver classes.

Adding support for a new instrument normally requires:

1. Implement a Driver subclass.
2. Decorate it with @register_driver("driver_type").
3. Add an entry to the Instrument Library catalogue.

No further registration code is required.
"""

from __future__ import annotations

from threading import RLock
from typing import Callable, Final, Type

from .base import Driver

_REGISTRY: Final[dict[str, Type[Driver]]] = {}
_LOCK = RLock()


def register_driver(device_type: str) -> Callable[[Type[Driver]], Type[Driver]]:
    """
    Register a Driver subclass.

    Raises:
        ValueError: if the driver type has already been registered.
    """
    device_type = device_type.strip()
    if not device_type:
        raise ValueError("driver type must not be empty")

    def _wrap(cls: Type[Driver]) -> Type[Driver]:
        if not issubclass(cls, Driver):
            raise TypeError(
                f"{cls.__name__} must inherit from Driver"
            )

        with _LOCK:
            existing = _REGISTRY.get(device_type)
            if existing is not None:
                raise ValueError(
                    f"driver type {device_type!r} already registered "
                    f"by {existing.__name__}"
                )
            _REGISTRY[device_type] = cls

        return cls

    return _wrap


def get_driver_class(device_type: str) -> Type[Driver]:
    """Return the registered driver class for a driver type."""
    with _LOCK:
        try:
            return _REGISTRY[device_type]
        except KeyError as exc:
            raise KeyError(
                f"Unknown driver type {device_type!r}. "
                f"Registered types: {', '.join(sorted(_REGISTRY))}"
            ) from exc


def registered_types() -> list[str]:
    """Return registered driver types in alphabetical order."""
    with _LOCK:
        return sorted(_REGISTRY)


def create_driver(
    device_type: str,
    device_id: str,
    on_event=None,
    **kwargs,
) -> Driver:
    """
    Construct a driver instance.

    The driver is not connected automatically; callers remain responsible for
    calling Driver.connect().
    """
    cls = get_driver_class(device_type)

    try:
        return cls(
            device_id=device_id,
            on_event=on_event,
            **kwargs,
        )
    except TypeError as exc:
        raise TypeError(
            f"Failed to construct driver {device_type!r}: {exc}"
        ) from exc
