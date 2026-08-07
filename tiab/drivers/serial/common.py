"""Shared helpers for serial instrument drivers."""

from __future__ import annotations


def decode_terminator(value: str) -> bytes:
    """Convert configured escape text such as ``\\r\\n`` into bytes."""
    return str(value).encode("utf-8").decode("unicode_escape").encode("ascii")
