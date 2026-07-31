"""
Driver registry.

New hardware support = write a Driver subclass, decorate it with
@register_driver("your_type_name"), done. The run config then references
devices by device_type + a small connection config dict, and the Blockly
toolbox generator (future work) can enumerate every registered type to
build its palette.
"""

from __future__ import annotations

from typing import Callable, Type

from .base import Driver

_REGISTRY: dict[str, Type[Driver]] = {}


def register_driver(device_type: str) -> Callable[[Type[Driver]], Type[Driver]]:
    def _wrap(cls: Type[Driver]) -> Type[Driver]:
        if device_type in _REGISTRY:
            raise ValueError(f"driver type '{device_type}' already registered")
        _REGISTRY[device_type] = cls
        return cls
    return _wrap


def get_driver_class(device_type: str) -> Type[Driver]:
    try:
        return _REGISTRY[device_type]
    except KeyError:
        raise KeyError(
            f"Unknown device_type '{device_type}'. Registered types: "
            f"{sorted(_REGISTRY.keys())}"
        )


def registered_types() -> list[str]:
    return sorted(_REGISTRY.keys())


def create_driver(device_type: str, device_id: str, on_event=None, **kwargs) -> Driver:
    cls = get_driver_class(device_type)
    return cls(device_id=device_id, on_event=on_event, **kwargs)
