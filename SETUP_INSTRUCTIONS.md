# Setup instructions — no admin rights needed

This app is three things sitting in one folder: a portable copy of
Python (like a program that doesn't need installing), the app itself,
and a webpage you open in your normal browser. Nothing here uses a
Windows installer, writes to Program Files, or touches the registry —
that's what makes it work without admin rights.

Do these steps once. After that, starting the app is one double-click.

## Step 1 — Get a portable Python

1. On any PC (or this one, in your browser), go to:
   **https://winpython.github.io/**
2. Download a **"Dot" build** of WinPython for **64-bit Windows**, a
   recent Python 3.11 or 3.12 version (the "Dot" builds are smaller and
   are all you need — you don't need the full build with extra editors).
   It downloads as a single `.exe` file, but it's a **self-extracting
   zip, not an installer** — double-clicking it just unpacks files to a
   folder you choose. It does not need admin rights.
3. When it asks where to extract, choose somewhere like:
   `C:\Users\<you>\Documents\HardwareTestApp\pythontemp`

## Step 2 — Arrange the folders

1. Create a folder for the whole app, e.g.
   `C:\Users\<you>\Documents\HardwareTestApp`
2. Inside `pythontemp` from Step 1, you'll find a folder with a name
   like `WPy64-31241`, and inside *that*, a folder like
   `python-3.11.9.amd64`. That inner folder contains `python.exe`
   directly — **rename that inner folder to `python`** and move it
   into `HardwareTestApp`, so you end up with:
   ```
   HardwareTestApp\
     python\
       python.exe          <- this exact path matters
       ...
   ```
   You can delete `pythontemp` afterwards.
3. Unzip the app package (the one I gave you) into the same
   `HardwareTestApp` folder, so you end up with:
   ```
   HardwareTestApp\
     python\
       python.exe
     hwapp\
     webapp\
     requirements.txt
     1_install_dependencies.bat
     2_start_app.bat
     README.md
     SETUP_INSTRUCTIONS.md
   ```

## Step 3 — Install the extra bits Python needs

Double-click **`1_install_dependencies.bat`**.

A black window will open and download some files (this needs internet
access — if it fails with a network/connection error, that likely means
your work network blocks it, and you'd need to ask IT to allow access to
`pypi.org` and `files.pythonhosted.org`, or install these files from a
USB drive instead). When it finishes, press any key to close the window.

You only need to do this once (and again later if I give you an updated
`requirements.txt`).

## Step 4 — Start the app

Double-click **`2_start_app.bat`**.

A black window opens (this is the app running quietly — don't close it
while you're using the app) and your browser should open automatically
to the test builder. If the page doesn't load right away, wait a couple
of seconds and refresh.

To stop the app, close the black window.

## About your hardware drivers

- **SCPI bench instruments over USB**: you can get **NI-VISA** installed
  via IT — do that once, up front. With NI-VISA present, any USB-TMC SCPI
  instrument will show up as a normal VISA resource (something like
  `USB0::0x0AAD::0x0197::123456::INSTR`) and the app's generic SCPI driver
  talks to it directly — no extra driver work needed per instrument. To
  find the exact resource string for a connected instrument, open
  **NI MAX** (installed alongside NI-VISA) → Devices and Interfaces —
  it'll be listed there.
- **Pico TC-08 / ADC-20/24**: you mentioned PicoScope and PicoLog are
  already installed by IT. That's a good sign, but it's worth checking
  whether the underlying **PicoSDK** is also present — open Windows
  Settings → Apps → Installed apps and search for "Pico". If you only
  see PicoScope/PicoLog and not anything called "PicoSDK" or "Pico
  Technology SDK", ask IT to add that — it's a small, official driver
  package from Pico Technology.
- **Seeit relay board / FTDI-based instruments**: since FTDI and serial
  drivers are already installed, these should "just work" when plugged
  in — Windows will assign them a COM port (check Device Manager → Ports
  (COM & LPT) to find out which one).

## Editing which hardware is connected

Open `webapp\config.json` in Notepad. It currently lists two mock PSUs
and a mock relay, purely so the app has something to show you and run
against with zero hardware attached. When you're ready to connect real
hardware, we'll walk through replacing those entries together — no need
to touch anything else in the app to do that.
