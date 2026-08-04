"""
Native Windows driver for Seeit USBB-RELAY devices.

This driver uses the vendor-supplied ``usb_relay_device.dll`` through
``ctypes``. It does not use a virtual COM port.

The implementation is based on the declarations in the supplied
``usb_relay_device.h`` header and supports the vendor's one, two, four and
eight-channel devices.

The Python process and DLL must use matching architectures: 64-bit Python with
a 64-bit DLL, or 32-bit Python with a 32-bit DLL.
"""

from __future__ import annotations

import ctypes
import os
import threading
from ctypes import POINTER, Structure, byref, c_char_p, c_int, c_ssize_t, c_uint
from pathlib import Path
from typing import Any

from ..base import CapabilityDescriptor, Driver, Position, PositionKind
from ..registry import register_driver


class UsbRelayError(RuntimeError):
    """Raised when the vendor USB relay library reports an error."""


class _UsbRelayDeviceInfo(Structure):
    pass


_UsbRelayDeviceInfoPointer = POINTER(_UsbRelayDeviceInfo)

_UsbRelayDeviceInfo._fields_ = [
    ("serial_number", c_char_p),
    ("device_path", c_char_p),
    ("type", c_ssize_t),
    ("next", _UsbRelayDeviceInfoPointer),
]


def _decode_text(value: bytes | None) -> str:
    if value is None:
        return ""
    return value.decode("ascii", errors="replace")


def _resolve_dll_path(dll_path: str | os.PathLike[str]) -> Path:
    candidate = Path(dll_path).expanduser()

    search_paths: list[Path] = []
    environment_path = os.environ.get("TIAB_USB_RELAY_DLL")
    if environment_path:
        search_paths.append(Path(environment_path).expanduser())

    project_root = Path(__file__).resolve().parents[3]

    if candidate.is_absolute():
        search_paths.append(candidate)
    else:
        search_paths.extend([
            # Preferred no-admin location inside the Test in a Box folder.
            project_root / "vendor" / "seeit" / candidate,

            # Current working directory, useful for portable deployments.
            Path.cwd() / candidate,

            # Driver directory, retained as a final local fallback.
            Path(__file__).resolve().parent / candidate,
        ])

    for path in search_paths:
        if path.exists():
            return path.resolve()

    raise FileNotFoundError(
        "usb_relay_device.dll was not found. Place it in "
        "'vendor/seeit/' inside the Test in a Box folder, set an absolute "
        "'dll_path' in the Instrument Library, or define TIAB_USB_RELAY_DLL."
    )


class _UsbRelayLibrary:
    """Configured ctypes wrapper around the vendor DLL."""

    def __init__(self, dll_path: Path) -> None:
        if os.name != "nt":
            raise RuntimeError(
                "The native Seeit USBB relay driver is Windows-only."
            )

        try:
            self.dll = ctypes.CDLL(str(dll_path))
        except OSError as exc:
            raise RuntimeError(
                f"Could not load '{dll_path}'. Confirm that the DLL "
                "architecture matches Python and that its dependencies are "
                f"available. Original error: {exc}"
            ) from exc

        self.path = dll_path
        self._configure_functions()

    def _configure_functions(self) -> None:
        dll = self.dll

        dll.usb_relay_init.argtypes = []
        dll.usb_relay_init.restype = c_int

        dll.usb_relay_exit.argtypes = []
        dll.usb_relay_exit.restype = c_int

        dll.usb_relay_device_enumerate.argtypes = []
        dll.usb_relay_device_enumerate.restype = _UsbRelayDeviceInfoPointer

        dll.usb_relay_device_free_enumerate.argtypes = [
            _UsbRelayDeviceInfoPointer
        ]
        dll.usb_relay_device_free_enumerate.restype = None

        dll.usb_relay_device_open_with_serial_number.argtypes = [
            c_char_p,
            c_uint,
        ]
        dll.usb_relay_device_open_with_serial_number.restype = c_ssize_t

        dll.usb_relay_device_close.argtypes = [c_ssize_t]
        dll.usb_relay_device_close.restype = None

        dll.usb_relay_device_open_one_relay_channel.argtypes = [
            c_ssize_t,
            c_int,
        ]
        dll.usb_relay_device_open_one_relay_channel.restype = c_int

        dll.usb_relay_device_open_all_relay_channel.argtypes = [c_ssize_t]
        dll.usb_relay_device_open_all_relay_channel.restype = c_int

        dll.usb_relay_device_close_one_relay_channel.argtypes = [
            c_ssize_t,
            c_int,
        ]
        dll.usb_relay_device_close_one_relay_channel.restype = c_int

        dll.usb_relay_device_close_all_relay_channel.argtypes = [c_ssize_t]
        dll.usb_relay_device_close_all_relay_channel.restype = c_int

        dll.usb_relay_device_get_status.argtypes = [
            c_ssize_t,
            POINTER(c_uint),
        ]
        dll.usb_relay_device_get_status.restype = c_int


_library_lock = threading.RLock()
_library_cache: dict[Path, tuple[_UsbRelayLibrary, int]] = {}


def _acquire_library(dll_path: Path) -> _UsbRelayLibrary:
    with _library_lock:
        cached = _library_cache.get(dll_path)
        if cached is not None:
            library, references = cached
            _library_cache[dll_path] = (library, references + 1)
            return library

        library = _UsbRelayLibrary(dll_path)
        result = library.dll.usb_relay_init()
        if result != 0:
            raise UsbRelayError(
                f"usb_relay_init() failed with result {result}"
            )

        _library_cache[dll_path] = (library, 1)
        return library


def _release_library(dll_path: Path) -> None:
    with _library_lock:
        cached = _library_cache.get(dll_path)
        if cached is None:
            return

        library, references = cached
        if references > 1:
            _library_cache[dll_path] = (library, references - 1)
            return

        result = library.dll.usb_relay_exit()
        del _library_cache[dll_path]

        if result != 0:
            raise UsbRelayError(
                f"usb_relay_exit() failed with result {result}"
            )


def _enumerate_devices(
    library: _UsbRelayLibrary,
) -> list[dict[str, Any]]:
    head = library.dll.usb_relay_device_enumerate()
    devices: list[dict[str, Any]] = []

    if not head:
        return devices

    try:
        current = head
        visited: set[int] = set()

        while current:
            address = ctypes.addressof(current.contents)
            if address in visited:
                raise UsbRelayError(
                    "The vendor enumeration returned a cyclic linked list"
                )
            visited.add(address)

            info = current.contents
            devices.append({
                "serial_number": _decode_text(info.serial_number),
                "device_path": _decode_text(info.device_path),
                "num_channels": int(info.type),
            })
            current = info.next
    finally:
        library.dll.usb_relay_device_free_enumerate(head)

    return devices


@register_driver("seeit_usbb_native")
class SeeitUsbbNativeDriver(Driver):
    """Seeit USBB relay driver using the vendor's native Windows DLL."""

    VALID_SAFE_STATES = {"open_all", "close_all"}

    def __init__(
        self,
        device_id: str,
        dll_path: str = "usb_relay_device.dll",
        serial_number: str = "",
        safe_state: str = "close_all",
        on_event=None,
    ) -> None:
        super().__init__(device_id, on_event)

        safe_state = safe_state.strip().lower()
        if safe_state not in self.VALID_SAFE_STATES:
            raise ValueError(
                "safe_state must be 'open_all' or 'close_all'"
            )

        self._configured_dll_path = dll_path
        self._serial_number = serial_number.strip() or None
        self._safe_state_name = safe_state

        self._dll_path: Path | None = None
        self._library: _UsbRelayLibrary | None = None
        self._handle = 0
        self._num_channels = 0
        self._device_path = ""
        self._io_lock = threading.RLock()

    def connect(self) -> None:
        with self._io_lock:
            if self._connected:
                return

            dll_path = _resolve_dll_path(self._configured_dll_path)
            library = _acquire_library(dll_path)
            handle = 0

            try:
                devices = _enumerate_devices(library)
                if not devices:
                    raise UsbRelayError(
                        "No Seeit USBB relay devices were found"
                    )

                selected: dict[str, Any] | None = None

                if self._serial_number:
                    selected = next(
                        (
                            item
                            for item in devices
                            if item["serial_number"] == self._serial_number
                        ),
                        None,
                    )
                    if selected is None:
                        available = ", ".join(
                            item["serial_number"] or "<blank>"
                            for item in devices
                        )
                        raise UsbRelayError(
                            f"Serial {self._serial_number!r} was not found. "
                            f"Available serials: {available}"
                        )
                elif len(devices) == 1:
                    selected = devices[0]
                    self._serial_number = selected["serial_number"]
                else:
                    available = ", ".join(
                        item["serial_number"] or "<blank>"
                        for item in devices
                    )
                    raise UsbRelayError(
                        "Multiple native USB relay devices are connected. "
                        "Configure 'serial_number'. Available serials: "
                        f"{available}"
                    )

                assert selected is not None
                serial_text = self._serial_number or ""
                serial_bytes = serial_text.encode("ascii")

                handle = (
                    library.dll
                    .usb_relay_device_open_with_serial_number(
                        serial_bytes,
                        len(serial_bytes),
                    )
                )
                if handle == 0:
                    raise UsbRelayError(
                        f"Could not open relay serial {serial_text!r}"
                    )

                num_channels = int(selected["num_channels"])
                if num_channels not in {1, 2, 4, 8}:
                    raise UsbRelayError(
                        f"Unsupported relay channel count: {num_channels}"
                    )

                self._dll_path = dll_path
                self._library = library
                self._handle = handle
                self._num_channels = num_channels
                self._device_path = str(selected["device_path"])
                self._connected = True

            except Exception:
                if handle:
                    library.dll.usb_relay_device_close(handle)
                _release_library(dll_path)
                raise

    def close(self) -> None:
        with self._io_lock:
            if self._handle and self._library is not None:
                self._library.dll.usb_relay_device_close(self._handle)

            self._handle = 0
            self._connected = False

            dll_path = self._dll_path
            self._library = None
            self._dll_path = None

            if dll_path is not None:
                _release_library(dll_path)

    def safe_state(self) -> None:
        """
        Apply the configured all-channel state.

        The current vendor SDK documents ``open`` as relay ON and ``close`` as
        relay OFF. Confirm the resulting NO/NC contact behaviour in the
        external circuit before relying on this as a safety function.
        """
        if self._safe_state_name == "open_all":
            self.open_all()
        else:
            self.close_all()

    def identify(self) -> dict[str, str]:
        model = (
            f"USBB-RELAY{self._num_channels:02d}"
            if self._num_channels
            else "USBB-RELAY"
        )
        serial = self._serial_number or ""

        return {
            "manufacturer": "Seeit",
            "model": model,
            "serial": serial,
            "firmware": "",
            "idn": f"SEEIT,{model},{serial},USB-DLL",
            "transport": "native_usb",
            "device_path": self._device_path,
            "driver": "seeit_usbb_native",
        }

    def capabilities(self) -> CapabilityDescriptor:
        channel_count = self._num_channels or 8

        return CapabilityDescriptor(
            device_type="seeit_usbb_native",
            device_id=self.device_id,
            display_name=(
                f"Seeit USBB-RELAY{channel_count:02d} (Native USB)"
            ),
            positions=[
                Position(
                    id=f"relay{channel}",
                    label=f"Relay {channel}",
                    kind=PositionKind.OUTPUT_DIGITAL,
                )
                for channel in range(1, channel_count + 1)
            ],
        )

    def write(self, position_id: str, value: Any) -> None:
        """
        Set one vendor relay state.

        A truthy value maps to the vendor's ``open`` command (relay ON) and a
        false value maps to the vendor's ``close`` command (relay OFF).
        """
        with self._io_lock:
            self._require_connected()
            channel = self._channel_number(position_id)
            requested_open = bool(value)

            if requested_open:
                result = (
                    self._library.dll
                    .usb_relay_device_open_one_relay_channel(
                        self._handle,
                        channel,
                    )
                )
                operation = "open_one"
            else:
                result = (
                    self._library.dll
                    .usb_relay_device_close_one_relay_channel(
                        self._handle,
                        channel,
                    )
                )
                operation = "close_one"

            self._check_result(result, operation, channel)
            self._emit(
                position_id,
                requested_open,
                None,
                event_type="state",
            )

    def read(self, position_id: str) -> bool:
        """Read one relay-state bit from the vendor DLL."""
        with self._io_lock:
            self._require_connected()
            channel = self._channel_number(position_id)

            status = c_uint(0)
            result = (
                self._library.dll
                .usb_relay_device_get_status(
                    self._handle,
                    byref(status),
                )
            )
            self._check_result(result, "get_status")

            is_open = bool(status.value & (1 << (channel - 1)))
            self._emit(
                position_id,
                is_open,
                None,
                event_type="measurement",
            )
            return is_open

    def open_all(self) -> None:
        with self._io_lock:
            self._require_connected()
            result = (
                self._library.dll
                .usb_relay_device_open_all_relay_channel(self._handle)
            )
            self._check_result(result, "open_all")
            self._emit(None, True, None, event_type="state")

    def close_all(self) -> None:
        with self._io_lock:
            self._require_connected()
            result = (
                self._library.dll
                .usb_relay_device_close_all_relay_channel(self._handle)
            )
            self._check_result(result, "close_all")
            self._emit(None, False, None, event_type="state")

    def _require_connected(self) -> None:
        if (
            not self._connected
            or self._library is None
            or self._handle == 0
        ):
            raise RuntimeError(
                f"{self.device_id}: native USB relay is not connected"
            )

    def _channel_number(self, position_id: str) -> int:
        if not position_id.startswith("relay"):
            raise KeyError(
                f"{self.device_id}: no such position {position_id!r}"
            )

        suffix = position_id[len("relay"):]
        if not suffix.isdigit():
            raise KeyError(
                f"{self.device_id}: no such position {position_id!r}"
            )

        channel = int(suffix)
        if not 1 <= channel <= self._num_channels:
            raise KeyError(
                f"{self.device_id}: relay channel out of range: {channel}"
            )

        return channel

    def _check_result(
        self,
        result: int,
        operation: str,
        channel: int | None = None,
    ) -> None:
        if result == 0:
            return

        detail = {
            1: "vendor operation failed",
            2: "relay channel is outside the device channel count",
        }.get(result, f"unknown vendor result {result}")

        suffix = (
            f" for relay {channel}"
            if channel is not None
            else ""
        )
        raise UsbRelayError(
            f"{self.device_id}: {operation}{suffix}: {detail}"
        )
