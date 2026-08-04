"""
Seeit USBB relay commissioning and diagnostic utility.

This tool uses the vendor's 64-bit USB_RELAY_DEVICE.dll directly. It is intended
to prove that two boards with duplicate factory serial numbers can be opened by
their individual enumeration-list nodes.

Commands:

    python tools/seeit_relay_commission.py list
    python tools/seeit_relay_commission.py identify 1
    python tools/seeit_relay_commission.py identify 2
    python tools/seeit_relay_commission.py status 1
    python tools/seeit_relay_commission.py all-off

The identify command pulses relay channel 1 three times and always attempts to
leave it OFF.

Disconnect external loads before using identify. A relay click is the intended
physical indication.
"""

from __future__ import annotations

import argparse
import ctypes
import os
import sys
import time
from ctypes import POINTER, Structure, byref, c_char_p, c_int, c_ssize_t, c_uint
from pathlib import Path


class UsbRelayError(RuntimeError):
    """Raised when the vendor USB relay library reports an error."""


class UsbRelayDeviceInfo(Structure):
    pass


UsbRelayDeviceInfoPointer = POINTER(UsbRelayDeviceInfo)

UsbRelayDeviceInfo._fields_ = [
    ("serial_number", c_char_p),
    ("device_path", c_char_p),
    ("type", c_ssize_t),
    ("next", UsbRelayDeviceInfoPointer),
]


def decode_text(value: bytes | None) -> str:
    if value is None:
        return ""
    return value.decode("ascii", errors="replace")


def find_dll(explicit_path: str | None) -> Path:
    candidates: list[Path] = []

    if explicit_path:
        candidates.append(Path(explicit_path).expanduser())

    environment_path = os.environ.get("TIAB_USB_RELAY_DLL")
    if environment_path:
        candidates.append(Path(environment_path).expanduser())

    project_root = Path(__file__).resolve().parents[1]
    candidates.extend([
        project_root / "vendor" / "seeit" / "usb_relay_device.dll",
        project_root / "vendor" / "seeit" / "USB_RELAY_DEVICE.dll",
        Path.cwd() / "vendor" / "seeit" / "usb_relay_device.dll",
        Path.cwd() / "vendor" / "seeit" / "USB_RELAY_DEVICE.dll",
    ])

    for candidate in candidates:
        if candidate.exists():
            return candidate.resolve()

    raise FileNotFoundError(
        "Could not find USB_RELAY_DEVICE.dll. Place the Win64 DLL in "
        "vendor/seeit/ or pass --dll with its absolute path."
    )


class VendorLibrary:
    def __init__(self, dll_path: Path) -> None:
        if os.name != "nt":
            raise RuntimeError("This utility is for Windows only.")

        try:
            self.dll = ctypes.CDLL(str(dll_path))
        except OSError as exc:
            raise RuntimeError(
                f"Could not load {dll_path}. Confirm that 64-bit Python is "
                f"being used with the Win64 DLL. Original error: {exc}"
            ) from exc

        self._configure()

    def _configure(self) -> None:
        dll = self.dll

        dll.usb_relay_init.argtypes = []
        dll.usb_relay_init.restype = c_int

        dll.usb_relay_exit.argtypes = []
        dll.usb_relay_exit.restype = c_int

        dll.usb_relay_device_enumerate.argtypes = []
        dll.usb_relay_device_enumerate.restype = UsbRelayDeviceInfoPointer

        dll.usb_relay_device_free_enumerate.argtypes = [
            UsbRelayDeviceInfoPointer
        ]
        dll.usb_relay_device_free_enumerate.restype = None

        dll.usb_relay_device_open.argtypes = [
            UsbRelayDeviceInfoPointer
        ]
        dll.usb_relay_device_open.restype = c_ssize_t

        dll.usb_relay_device_close.argtypes = [c_ssize_t]
        dll.usb_relay_device_close.restype = None

        dll.usb_relay_device_open_one_relay_channel.argtypes = [
            c_ssize_t,
            c_int,
        ]
        dll.usb_relay_device_open_one_relay_channel.restype = c_int

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

        # The newer Win64 DLL may expose helper functions.
        self.has_lib_version = hasattr(dll, "usb_relay_device_lib_version")
        if self.has_lib_version:
            dll.usb_relay_device_lib_version.argtypes = []
            dll.usb_relay_device_lib_version.restype = c_int

        # The supplied Win64 DLL does not export usb_relay_device_set_serial.
        self.has_set_serial = hasattr(dll, "usb_relay_device_set_serial")


class Enumeration:
    """
    Keep the vendor enumeration list alive while selected nodes are opened.

    The vendor sample opens a device by passing the actual linked-list node to
    usb_relay_device_open(). This utility deliberately follows that pattern.
    """

    def __init__(self, library: VendorLibrary) -> None:
        self.library = library
        self.head = UsbRelayDeviceInfoPointer()
        self.nodes: list[UsbRelayDeviceInfoPointer] = []

    def __enter__(self) -> "Enumeration":
        self.head = self.library.dll.usb_relay_device_enumerate()
        if not self.head:
            return self

        current = self.head
        visited: set[int] = set()

        while current:
            address = ctypes.addressof(current.contents)
            if address in visited:
                raise UsbRelayError(
                    "Vendor enumeration returned a cyclic linked list."
                )
            visited.add(address)
            self.nodes.append(current)
            current = current.contents.next

        return self

    def __exit__(self, exc_type, exc, traceback) -> None:
        if self.head:
            self.library.dll.usb_relay_device_free_enumerate(self.head)
        self.nodes.clear()
        self.head = UsbRelayDeviceInfoPointer()

    def record(self, index: int) -> dict[str, object]:
        node = self.node(index)
        info = node.contents
        return {
            "index": index,
            "serial": decode_text(info.serial_number),
            "device_path": decode_text(info.device_path),
            "channels": int(info.type),
            "pointer": ctypes.addressof(info),
        }

    def node(self, index: int) -> UsbRelayDeviceInfoPointer:
        if not 1 <= index <= len(self.nodes):
            raise UsbRelayError(
                f"Device index {index} is invalid. Found {len(self.nodes)} "
                "device(s)."
            )
        return self.nodes[index - 1]


def check_result(result: int, operation: str) -> None:
    if result == 0:
        return
    detail = {
        1: "vendor operation failed",
        2: "relay channel is invalid",
    }.get(result, f"unknown result {result}")
    raise UsbRelayError(f"{operation}: {detail}")


def open_node(
    library: VendorLibrary,
    enumeration: Enumeration,
    index: int,
) -> int:
    node = enumeration.node(index)
    handle = int(library.dll.usb_relay_device_open(node))
    if handle == 0:
        raise UsbRelayError(
            f"Vendor DLL could not open enumerated device {index}."
        )
    return handle


def print_devices(library: VendorLibrary) -> int:
    with Enumeration(library) as enumeration:
        if not enumeration.nodes:
            print("No compatible relay boards found.")
            return 1

        print(f"Found {len(enumeration.nodes)} relay board(s):")
        print()

        for index in range(1, len(enumeration.nodes) + 1):
            record = enumeration.record(index)
            print(f"Device {record['index']}")
            print(f"  Factory serial : {record['serial'] or '<blank>'}")
            print(f"  Device path    : {record['device_path'] or '<blank>'}")
            print(f"  Relay channels : {record['channels']}")
            print(f"  Node pointer   : 0x{record['pointer']:X}")
            print()

    if library.has_lib_version:
        version = library.dll.usb_relay_device_lib_version() & 0xFFFF
        print(f"DLL version: 0x{version:04X}")

    print(
        "Serial-number write support: "
        + ("exported" if library.has_set_serial else "not exported by this DLL")
    )
    return 0


def status_device(library: VendorLibrary, index: int) -> int:
    with Enumeration(library) as enumeration:
        handle = open_node(library, enumeration, index)
        try:
            status = c_uint(0)
            result = library.dll.usb_relay_device_get_status(
                handle,
                byref(status),
            )
            check_result(result, "get status")
            channels = int(enumeration.node(index).contents.type)

            print(f"Device {index} status: 0x{status.value:08X}")
            for channel in range(1, channels + 1):
                is_on = bool(status.value & (1 << (channel - 1)))
                print(f"  Relay {channel}: {'ON' if is_on else 'OFF'}")
        finally:
            library.dll.usb_relay_device_close(handle)

    return 0


def identify_device(
    library: VendorLibrary,
    index: int,
    pulses: int,
    dwell_seconds: float,
) -> int:
    if pulses < 1:
        raise ValueError("pulses must be at least 1")
    if dwell_seconds <= 0:
        raise ValueError("dwell time must be greater than zero")

    print()
    print("WARNING")
    print("Relay channel 1 will be pulsed.")
    print("Disconnect external loads before continuing.")
    print()

    confirmation = input(
        f"Type IDENTIFY to pulse enumerated device {index}: "
    ).strip()
    if confirmation != "IDENTIFY":
        print("Cancelled.")
        return 1

    with Enumeration(library) as enumeration:
        record = enumeration.record(index)
        print(
            f"Opening device {index}: serial={record['serial']!r}, "
            f"path={record['device_path']!r}"
        )

        handle = open_node(library, enumeration, index)
        try:
            # Start from a known all-off state.
            check_result(
                library.dll.usb_relay_device_close_all_relay_channel(handle),
                "all relays OFF",
            )

            for pulse in range(1, pulses + 1):
                print(f"Pulse {pulse}/{pulses}: relay 1 ON")
                check_result(
                    library.dll.usb_relay_device_open_one_relay_channel(
                        handle,
                        1,
                    ),
                    "relay 1 ON",
                )
                time.sleep(dwell_seconds)

                print(f"Pulse {pulse}/{pulses}: relay 1 OFF")
                check_result(
                    library.dll.usb_relay_device_close_one_relay_channel(
                        handle,
                        1,
                    ),
                    "relay 1 OFF",
                )
                time.sleep(dwell_seconds)
        finally:
            # Best-effort all-off cleanup before closing.
            try:
                library.dll.usb_relay_device_close_all_relay_channel(handle)
            finally:
                library.dll.usb_relay_device_close(handle)

    print("Identify sequence complete; all relays were commanded OFF.")
    return 0


def all_off(library: VendorLibrary) -> int:
    failures = 0

    with Enumeration(library) as enumeration:
        if not enumeration.nodes:
            print("No compatible relay boards found.")
            return 1

        for index in range(1, len(enumeration.nodes) + 1):
            handle = 0
            try:
                handle = open_node(library, enumeration, index)
                check_result(
                    library.dll.usb_relay_device_close_all_relay_channel(
                        handle
                    ),
                    f"device {index} all OFF",
                )
                print(f"Device {index}: all relays OFF")
            except Exception as exc:
                failures += 1
                print(f"Device {index}: FAILED: {exc}", file=sys.stderr)
            finally:
                if handle:
                    library.dll.usb_relay_device_close(handle)

    return 1 if failures else 0


def build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(
        description=(
            "Commission and diagnose Seeit USBB relay boards through the "
            "vendor DLL."
        )
    )
    parser.add_argument(
        "--dll",
        help="Absolute path to USB_RELAY_DEVICE.dll",
    )

    subparsers = parser.add_subparsers(dest="command", required=True)

    subparsers.add_parser("list", help="List enumerated relay boards")

    status_parser = subparsers.add_parser(
        "status",
        help="Read relay states from one enumerated board",
    )
    status_parser.add_argument("index", type=int)

    identify_parser = subparsers.add_parser(
        "identify",
        help="Pulse relay 1 on one enumerated board",
    )
    identify_parser.add_argument("index", type=int)
    identify_parser.add_argument("--pulses", type=int, default=3)
    identify_parser.add_argument("--dwell", type=float, default=0.4)

    subparsers.add_parser(
        "all-off",
        help="Command all relays OFF on every enumerated board",
    )

    return parser


def main() -> int:
    parser = build_parser()
    args = parser.parse_args()

    try:
        dll_path = find_dll(args.dll)
        print(f"Using DLL: {dll_path}")

        library = VendorLibrary(dll_path)
        result = library.dll.usb_relay_init()
        if result != 0:
            raise UsbRelayError(
                f"usb_relay_init() failed with result {result}"
            )

        try:
            if args.command == "list":
                return print_devices(library)
            if args.command == "status":
                return status_device(library, args.index)
            if args.command == "identify":
                return identify_device(
                    library,
                    args.index,
                    args.pulses,
                    args.dwell,
                )
            if args.command == "all-off":
                return all_off(library)

            parser.error(f"Unknown command: {args.command}")
            return 2
        finally:
            exit_result = library.dll.usb_relay_exit()
            if exit_result != 0:
                print(
                    f"Warning: usb_relay_exit() returned {exit_result}",
                    file=sys.stderr,
                )
    except Exception as exc:
        print(f"ERROR: {exc}", file=sys.stderr)
        return 1


if __name__ == "__main__":
    raise SystemExit(main())
