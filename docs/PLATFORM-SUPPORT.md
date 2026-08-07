# Platform Support

## Overview

Test in a Box is intended to keep the engineering procedure independent of the
computer operating system. The web application and Blockly editor are
cross-platform, but individual hardware drivers depend on the transport and
vendor support available on each platform.

This document describes the current alpha state. It is not a guarantee that
every listed combination has been bench tested.

## Current support matrix

| Feature or driver | Windows | Linux / Raspberry Pi | macOS |
|---|:---:|:---:|:---:|
| FastAPI web application | Supported | Supported | Supported |
| Blockly test editor | Supported | Supported | Supported |
| Mock instruments | Supported | Supported | Supported |
| Generic SCPI with PyVISA/PyVISA-py | Supported | Supported | Supported |
| Aim-TTi serial driver | Bench tested on Windows | Expected; not yet bench tested | Expected; not yet bench tested |
| Seeit USB-RELAY08 serial driver | Available; not yet bench tested | Expected; not yet bench tested | Expected; not yet bench tested |
| Seeit USBB native USB driver | Bench tested | Not supported | Not supported |
| Pico TC-08 / ADC-20/24 | TC-08 driver bench-probed; ADC support depends on PicoSDK installation | Depends on PicoSDK installation; not bench-tested | Depends on PicoSDK installation; not bench-tested |

## Seeit USBB native USB limitation

The native USBB driver loads the vendor-supplied:

```text
usb_relay_device.dll
```

This is a Windows DLL, so the driver does not run on Linux, Raspberry Pi OS or
macOS.

The recommended portable location is:

```text
vendor/seeit/usb_relay_device.dll
```

No administrator rights are required when the DLL is loaded from that folder.
The Python and DLL architectures must match.

The DLL is not currently distributed with Test in a Box while redistribution
permission is being confirmed with Seeit.

## Multiple identical USBB boards

Some physical boards report the same factory serial number and the value
`NOTHING` as their DLL device path.

Test in a Box can distinguish them by selecting the live node returned by the
vendor enumeration list. The configuration therefore stores selectors such as:

```text
index:1
index:2
```

This works for the current connection, but enumeration order may change when:

- a board is moved to another USB port;
- a hub is changed;
- boards are added or removed;
- Windows is restarted.

After a USB-topology change, use **Scan for Devices**, select each board again
and verify its physical identity with the mimic controls.

This limitation makes enumeration-index selection suitable for current bench
use but not a permanent identity mechanism for a large fixed installation.

## Serial instruments on Linux and macOS

Serial instruments use paths rather than Windows COM names.

Typical Linux values are:

```text
/dev/ttyUSB0
/dev/ttyACM0
/dev/serial/by-id/...
```

Typical macOS values are:

```text
/dev/cu.usbserial-...
```

Linux users may need membership of the `dialout` group. macOS may require a
vendor USB-to-serial driver for some adapter chipsets.

## Support status terminology

- **Supported** means the software path is intended to work.
- **Expected** means the transport is cross-platform but has not been bench
  tested by the project.
- **Bench tested** means operation has been confirmed on physical hardware.
- **Not supported** means the required vendor component is unavailable on that
  platform.
