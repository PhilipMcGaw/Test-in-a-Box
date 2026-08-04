"""
Compatibility import for the Seeit serial relay driver.

New code should import:

    tiab.drivers.serial.seeit_relay

This module remains so existing imports and third-party code do not break.
"""

from .serial.seeit_relay import (  # noqa: F401
    SeeitRelay08Driver,
    SeeitRelay08SerialDriver,
)

__all__ = [
    "SeeitRelay08Driver",
    "SeeitRelay08SerialDriver",
]
