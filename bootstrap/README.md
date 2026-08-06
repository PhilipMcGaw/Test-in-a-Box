# Test in a Box Bootstrap

Run the repository-root file:

```text
bootstrap.bat
```

The bootstrap is intended for Windows systems where administrator rights may
not be available.

## What it does

1. Checks for `python\python.exe`.
2. Downloads a stable official 64-bit WinPython Dot runtime when Python is
   missing.
3. Creates required writable project folders.
4. Installs or updates `requirements.txt`.
5. Checks optional vendor components.
6. Runs installation verification.
7. Offers to start Test in a Box.

The process is idempotent: running it again reuses the existing portable Python
runtime and only updates or verifies what is required.

## Files

- `bootstrap.bat` — orchestrator called by the root launcher.
- `bootstrap_winpython.ps1` — downloads and extracts WinPython.
- `bootstrap_folders.ps1` — creates writable project directories.
- `bootstrap_dependencies.ps1` — installs Python dependencies.
- `bootstrap_vendor.ps1` — reports optional vendor components.
- `bootstrap_verify.ps1` — produces the final bootstrap report.

## Internet access

First-time bootstrap may require access to:

- `api.github.com`
- `github.com`
- `objects.githubusercontent.com`
- `pypi.org`
- `files.pythonhosted.org`

## Optional Seeit DLL

The Seeit native USBB relay DLL is not downloaded automatically. Redistribution
permission and licensing must be respected.

Place the correct licensed DLL at:

```text
vendor\seeit\usb_relay_device.dll
```

## WinPython archive layout

Bootstrap does not depend on a particular WinPython folder name. After
extraction it searches recursively for `python.exe` and selects the runtime
folder that also contains:

```text
Lib\
DLLs\
Lib\os.py
```

If the archive layout changes again, bootstrap lists every discovered
`python.exe` and every runtime candidate before stopping. This makes failures
diagnosable without manually inspecting the archive.

## GitHub rate limiting

Bootstrap does not use the GitHub REST API for normal WinPython discovery.

Instead, it downloads WinPython's public checksum manifest:

```text
https://winpython.github.io/md5_sha1.txt
```

It selects the newest stable matching 64-bit Python 3.13 Dot build, falling
back to Python 3.12, and downloads the named asset through GitHub's ordinary
`releases/latest/download` endpoint.

This avoids the low unauthenticated REST API allowance that can affect several
machines sharing the same public IP address. The downloaded file is always
verified against the SHA-256 value published in the WinPython manifest.


## Repository responsibility

The `bootstrap/` directory contains installation and environment
preparation only. Engineering utilities belong in `tools/`; update and
rollback logic belongs in `updater/`.

## Pico runtime support

Pico Technology's Windows runtime requires a one-time administrator
installation. Bootstrap does not elevate or execute the installer.

When the runtime is missing, `bootstrap_pico.ps1` downloads the official PicoSDK installer directly into
`vendor/pico/installer/` and reports
its location. An administrator can install it later, after which rerunning
bootstrap verifies the TC-08 and PicoHRDL runtimes.

See `docs/getting-started/PICO-RUNTIME.md`.
