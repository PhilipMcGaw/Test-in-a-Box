"""Helpers for locating portable third-party runtime libraries."""

from __future__ import annotations

import os
import sys
from pathlib import Path

_DLL_DIRECTORY_HANDLES: list[object] = []


def project_root() -> Path:
    """Return the Test in a Box repository root."""
    return Path(__file__).resolve().parent.parent


def vendor_root() -> Path:
    return project_root() / "vendor"


def vendor_runtime_paths(vendor: str) -> list[Path]:
    """Return existing runtime directories for one vendor."""
    base = vendor_root() / vendor
    candidates = [
        base / "runtime",
        base / "bin",
        base,
    ]
    return [path for path in candidates if path.is_dir()]


def prepare_vendor_runtime(vendor: str) -> list[Path]:
    """
    Make a portable vendor runtime visible to ctypes and dependent DLLs.

    On Python 3.8+ for Windows, ``os.add_dll_directory`` is required for
    reliable dependent-DLL resolution. PATH is also updated for wrappers that
    load libraries by bare filename.
    """
    paths = vendor_runtime_paths(vendor)

    if not paths:
        return []

    existing_path = os.environ.get("PATH", "")
    existing_parts = existing_path.split(os.pathsep) if existing_path else []

    for path in paths:
        path_text = str(path)

        if path_text not in existing_parts:
            existing_parts.insert(0, path_text)

        if sys.platform == "win32" and hasattr(os, "add_dll_directory"):
            try:
                handle = os.add_dll_directory(path_text)
            except OSError:
                continue
            _DLL_DIRECTORY_HANDLES.append(handle)

    os.environ["PATH"] = os.pathsep.join(existing_parts)
    return paths


def require_vendor_library(
    vendor: str,
    filename: str,
    *,
    install_hint: str = "Run bootstrap.bat.",
) -> Path:
    """Return a portable vendor library path or raise a useful error."""
    for directory in vendor_runtime_paths(vendor):
        candidate = directory / filename
        if candidate.is_file():
            return candidate

    searched = ", ".join(
        str(path / filename)
        for path in [
            vendor_root() / vendor / "runtime",
            vendor_root() / vendor / "bin",
            vendor_root() / vendor,
        ]
    )
    raise RuntimeError(
        f"{vendor} runtime library {filename!r} was not found. "
        f"Searched: {searched}. {install_hint}"
    )
