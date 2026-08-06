# Test in a Box – macOS and Raspberry Pi Setup Guide

This guide covers running **Test in a Box** on:

- **macOS** (Intel or Apple Silicon)
- **Raspberry Pi OS** (64-bit recommended; a Pi 4 or Pi 5 is plenty)
- Most other Linux distributions, with the same steps as the Pi section

It mirrors the Windows guide (`SETUP_INSTRUCTIONS.md`) but uses two shell
scripts, `1_install_dependencies.sh` and `2_start_app.sh`, in place of the
`.bat` files. Everything installs into a self-contained virtual environment
inside the project folder — nothing is installed system-wide, and no
`sudo`/root access is needed except for one optional, one-time step on
Linux (see [USB-serial permissions](#usb-serial-permissions-linuxraspberry-pi)
below).

---

## Step 1 — Get Python 3 onto the machine

**macOS:** Recent macOS ships with Python 3, but it's worth confirming:

```bash
python3 --version
```

If that fails or shows an older version (Python 3.10 or newer is required;
3.11/3.12 recommended), install a current one from [python.org](https://www.python.org/downloads/macos/)
or with Homebrew if you have it: `brew install python@3.12`.

**Raspberry Pi OS:** Python 3 is included by default. Confirm with:

```bash
python3 --version
```

If you're on an older Raspberry Pi OS image without a recent Python, update
the OS first (`sudo apt update && sudo apt full-upgrade`) or install a newer
Python via [pyenv](https://github.com/pyenv/pyenv) — most current
Raspberry Pi OS (Bookworm) images already ship Python 3.11.

---

## Step 2 — Copy the project onto the machine

Copy the whole `Test-in-a-Box` project folder onto the Mac or Pi — for
example via `git clone`, a USB drive, `scp`, or a shared network folder
copied locally first. You should end up with a folder like:

```text
Test-in-a-Box/
    webapp/
    tiab/
    requirements.txt
    1_install_dependencies.sh
    2_start_app.sh
    SETUP_INSTRUCTIONS_MAC_AND_RASPBERRY_PI.md
    ...
```

Open a terminal, `cd` into that folder, and make the two scripts
executable (only needed once, e.g. if they came from a `.zip` or a Windows
machine that didn't preserve execute permissions):

```bash
cd ~/Test-in-a-Box
chmod +x 1_install_dependencies.sh 2_start_app.sh
```

---

## Step 3 — Install dependencies

```bash
./1_install_dependencies.sh
```

This script:

1. Installs [`uv`](https://docs.astral.sh/uv/) for your user account only,
   if it isn't already on your machine (no root needed).
2. Creates a virtual environment in `.venv/` inside the project folder.
3. Installs everything listed in `requirements.txt` into that environment.
4. **On Linux/Raspberry Pi only:** checks whether your user account can
   already talk to USB-serial devices, and offers to fix it for you if not
   (see the next section for why this matters).

If your network blocks PyPI (`pypi.org` / `files.pythonhosted.org`), ask
whoever manages the network to allow it, or install the packages from a USB
drive using `uv pip install --python .venv/bin/python <path-to-wheels>`.

You only need to run this once, and again later if `requirements.txt`
changes.

---

## Step 4 — Start the app

```bash
./2_start_app.sh
```

A browser window should open automatically to `http://127.0.0.1:8765`. If it
doesn't (some minimal/headless Pi setups don't have a default browser
handler configured), just open that address manually in any browser on the
same machine.

Keep the terminal window open while you're using the app — closing it (or
pressing `Ctrl+C`) stops the app.

---

## USB-serial permissions (Linux/Raspberry Pi)

The Aim-TTi PSU and Seeit USB-RELAY08 serial driver talk over a USB-serial connection
(a virtual COM port, appearing as `/dev/ttyUSB0`, `/dev/ttyACM0`, etc. on
Linux). On Raspberry Pi OS and most Linux distributions, access to those
device files is restricted to users in the **`dialout`** group.

`1_install_dependencies.sh` checks this for you and offers to run:

```bash
sudo usermod -a -G dialout $USER
```

This is the *only* step in the whole setup that needs `sudo`, and it only
grants your own user account permission to access serial ports — it doesn't
install anything or change any files outside your account. **You must log
out and back in (or reboot) afterwards** for the new group membership to
take effect; group membership is only picked up when you start a new login
session.

If you skip this step, connecting to a real PSU or relay board will fail
with a "Permission denied" error even though `ls /dev/ttyUSB*` shows the
device is there.

macOS doesn't use a `dialout` group — serial devices there normally show
up as `/dev/cu.usbserial-XXXX` (or similar) and are usable without any
extra permission step, once the correct USB-serial driver is installed (see
below).

---

## Finding the right serial port name

Unlike Windows (`COM5`, `COM12`, ...), macOS and Linux use device paths.
Before editing `webapp/config.json` to point at a real Aim-TTi PSU or Seeit
relay board, find its device path:

**macOS:**
```bash
ls /dev/cu.*
```
Plug the device in and out and see which entry appears/disappears — that's
the one to use, e.g. `/dev/cu.usbserial-A5069RR4`.

**Raspberry Pi / Linux:**
```bash
ls /dev/ttyUSB* /dev/ttyACM*
```
or, for a more permanent name that survives reboots and doesn't depend on
plug order:
```bash
ls -l /dev/serial/by-id/
```
Use whichever path appears, e.g. `/dev/ttyUSB0` or
`/dev/serial/by-id/usb-FTDI_...`.

Whatever value you find, that's what goes in the `serial_port` field for a
device on the **Configure Devices** page (or directly in
`webapp/config.json`) — no drive-letter concept applies here.

---


## Platform-specific driver limitation

The **Seeit USBB Native USB** driver is not supported on macOS, Linux or
Raspberry Pi OS. It depends on the vendor's Windows-only
`usb_relay_device.dll`.

This limitation does not apply to the separate **Seeit USB-RELAY08 (Serial)**
driver, which uses a virtual serial port and is expected to work when the
relevant USB-to-serial device is supported by the operating system.

See [`../PLATFORM-SUPPORT.md`](../PLATFORM-SUPPORT.md) for the current
support matrix and validation status.

## Driver-specific notes for macOS/Pi

- **FTDI-based USB-serial adapters** (many bench PSUs and relay boards use
  an FTDI chip): macOS has included a native FTDI driver since around OS X
  10.9, so these normally work out of the box. Raspberry Pi OS's kernel
  also includes the `ftdi_sio` driver by default — no extra installation
  needed on either platform.
- **NI-VISA is not available on Raspberry Pi**, and installing it on macOS
  requires a separate download from NI. This project's generic SCPI driver
  uses `pyvisa` with the pure-Python `pyvisa-py` backend (already listed in
  `requirements.txt`), which talks to USB-TMC and LAN/VXI-11 instruments
  without needing NI-VISA at all — this is the path to use on macOS and Pi.
  For USB-TMC specifically on Linux, you may also need:
  ```bash
  sudo apt install libusb-1.0-0
  ```
- **PicoSDK (Pico TC-08 / ADC-20/24):** Pico Technology publish Linux
  builds of PicoSDK for both 32-bit and 64-bit ARM (covering Raspberry Pi)
  as well as macOS, from https://www.picotech.com/downloads — install the
  appropriate package for your OS/architecture before `picosdk` (the Python
  wrapper, already in `requirements.txt`) will be able to talk to the
  instrument. If PicoSDK isn't installed, the app still starts fine; the
  Pico drivers just report as unavailable at startup.

---

## Editing which hardware is connected

Exactly as on Windows: edit `webapp/config.json` (or use the **Configure
Devices** page in the browser) to replace the mock PSU/relay entries with
your real devices once you've found the correct serial port paths above.
