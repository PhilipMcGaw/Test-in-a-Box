# Test in a Box – Windows Setup Guide (No Administrator Rights Required)

This guide explains how to run **Test in a Box** on a Windows computer where
you do not have administrator rights.

The application has been designed to work in engineering environments where
software installation may be restricted. It uses a **portable Python**
installation, allowing the application to run without modifying Windows,
installing software system-wide, or writing to the registry.

Once installed, starting Test in a Box is simply a matter of running a batch
file and opening the local web interface in your browser.

---

# Step 1 – Download a portable copy of Python

Download **WinPython** from:

https://winpython.github.io/

Choose a recent **64-bit Dot release** (Python 3.11 or newer).

The Dot releases contain everything required to run Test in a Box without the
additional development tools included in the full WinPython distribution.

Although the download is an `.exe` file, it is **not** an installer. It simply
extracts a portable copy of Python into a folder of your choosing.

Extract it somewhere temporary.

For example:

```text
C:\Users\<you>\Downloads\WinPythonTemp
```

No administrator rights are required.

---

# Step 2 – Arrange the folders

Create a folder for Test in a Box.

For example:

```text
C:\Users\<you>\Documents\Test-in-a-Box
```

Inside the extracted WinPython folder you'll find a directory similar to:

```text
WPy64-312xx\
    python-3.xx.x.amd64\
```

Rename the **python-3.xx.x.amd64** folder to simply:

```text
python
```

and move it into your Test-in-a-Box folder.

You should end up with something similar to:

```text
Test-in-a-Box\
    python\
        python.exe
```

The temporary WinPython download folder can then be deleted.

---

# Step 3 – Copy the Test in a Box files

Extract the Test in a Box repository into the same folder.

The resulting structure should look similar to:

```text
Test-in-a-Box\
    python\
        python.exe

    tiab\
    webapp\
    docs\

    requirements.txt

    1_install_dependencies.bat
    2_start_app.bat

    README.md
    SETUP_INSTRUCTIONS.md
```

---

# Step 4 – Install the required Python packages

Double-click:

```text
1_install_dependencies.bat
```

A command window will open and download the required Python packages.

This only needs to be done:

- when first installing Test in a Box;
- or when the `requirements.txt` file changes.

Internet access is required for this step.

If your organisation blocks access to Python package repositories, you may need
to ask your IT department to allow access to:

- pypi.org
- files.pythonhosted.org

---

# Step 5 – Start Test in a Box

Double-click:

```text
2_start_app.bat
```

A command window will open.

Leave this window running while using Test in a Box.

Your web browser should automatically open.

If it does not, browse to:

```text
http://127.0.0.1:8765
```

To stop the application simply close the command window.

---

# First Run

The default configuration uses **mock hardware**.

This allows you to:

- explore the interface;
- create Blockly test procedures;
- run the supplied demonstration;
- generate CSV result files;

without connecting any laboratory equipment.

---

# Configuring your hardware

Once the application is running, open the **Configure Devices** page.

From there you can:

- Add instruments.
- Configure communication settings.
- Save hardware definitions.
- Connect and reconnect hardware.
- Verify operation using the live mimic panel.

For most users there should be no need to edit:

```text
webapp\config.json
```

directly.

The configuration file remains available for troubleshooting or advanced
configuration if required.

---

# Instrument Drivers

## Generic SCPI Instruments

Many SCPI instruments can be supported without writing new Python code.

Create a command map based on:

```text
tiab/drivers/scpi_command_map.example.json
```

and specify the VISA resource together with the commands required by your
instrument.

The generic SCPI driver can then communicate with the instrument using those
definitions.

---

## Aim-TTi Power Supplies

Support is included for Aim-TTi programmable power supplies using their serial
remote command protocol.

These drivers communicate using USB virtual COM ports or RS232 and do not
require NI-VISA.

Driver behaviour has been validated against protocol-accurate simulators but
should still be confirmed against your own hardware before relying on it for
critical testing.

---

## Pico TC-08 and Pico ADC-20/24

Support is included for:

- Pico TC-08
- Pico ADC-20
- Pico ADC-24

using the official PicoSDK.

If PicoScope or PicoLog is already installed there is a good chance the
required SDK is already present.

If not, install the official PicoSDK from Pico Technology.

As with all hardware drivers, confirm correct operation against your own
hardware before relying on it for production work.

---

## Seeit USB-RELAY08

The Seeit USB-RELAY08 uses a **Prolific PL2303 USB-to-serial converter**, not an
FTDI converter.

Windows may require the PL2303 driver before the board appears as a COM port.
The driver is available from the manufacturer product page:

https://seeit.fr/produits.php?produit_ref=USB-RELAY08

Installing the driver normally requires **administrator rights**.

After installing the driver, reconnect the board and use Windows Device Manager
to determine the assigned COM port.

For regular bench use, shared laboratories or education, consider fitting the
relay board inside an enclosure and breaking the relay contacts out to clearly
labelled, touch-safe connectors. Document how each external connector maps to
the logical relay number used by Test in a Box.

---

# Troubleshooting

If Test in a Box does not start correctly:

1. Confirm that Python dependencies installed successfully.
2. Check that the command window has remained open.
3. Verify that your browser can reach:

```text
http://127.0.0.1:8765
```

4. Try the supplied mock hardware configuration before connecting real
   laboratory equipment.
5. Check the Configure Devices page to confirm your instruments have connected.

For SCPI instruments it is often useful to verify that the instrument responds
correctly to:

```text
*IDN?
```

before attempting to automate it.

---

# Need Help?

If you encounter a problem, please include as much of the following information
as possible:

- Windows version.
- Python version.
- Instrument make and model.
- Driver being used.
- Error messages.
- Screenshots where appropriate.

Project website:

https://philipmcgaw.com/projects/test-in-a-box/

GitHub repository:

https://github.com/PhilipMcGaw/Test-in-a-Box

Email:

philip@mcgaw.eu