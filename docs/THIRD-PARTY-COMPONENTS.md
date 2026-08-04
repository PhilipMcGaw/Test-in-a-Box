# Third-Party Components

Test in a Box uses open-source Python packages and can optionally use
vendor-supplied hardware libraries.

This document records the current project understanding. It is not a substitute
for the licence text supplied with each component.

## Python dependencies

The Python packages installed from `requirements.txt` retain their own licences.
Users and distributors should review the licence information published with
the installed package versions.

Core dependencies currently include:

- FastAPI;
- Uvicorn;
- Pydantic;
- PyVISA and PyVISA-py;
- PySerial;
- PicoSDK Python wrappers;
- WebSockets.

## Seeit native USB relay DLL

The Windows native Seeit USBB relay driver uses:

```text
usb_relay_device.dll
```

The project author has contacted Seeit to confirm whether this DLL may be
redistributed with Test in a Box.

Until written permission or applicable licence terms are confirmed:

- the DLL is not included in the public repository;
- users obtain it from the hardware supplier;
- users place it in `vendor/seeit/`;
- `.gitignore` excludes it from commits.

The absence of the DLL only affects the Windows native USBB relay driver. The
web application, mock drivers and other instrument drivers can still run.

## PicoSDK

Pico TC-08 and ADC-20/24 support depends on vendor PicoSDK components in
addition to the Python wrapper. Availability and installation vary by operating
system and architecture.

## Hardware documentation and SDK examples

Vendor documentation, headers, DLLs and example programs remain subject to
their original licences. Do not copy vendor binary or source packages into a
public Test in a Box release unless redistribution permission is clear.
