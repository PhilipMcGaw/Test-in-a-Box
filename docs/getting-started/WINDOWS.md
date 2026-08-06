# Test in a Box – Windows Setup Guide (No Administrator Rights Required)


> This guide is for Windows. For Linux, Raspberry Pi OS and macOS, use
> [`MAC-LINUX-RASPBERRY-PI.md`](MAC-LINUX-RASPBERRY-PI.md).
> Driver availability differs by platform; see
> [`../PLATFORM-SUPPORT.md`](../PLATFORM-SUPPORT.md).

This guide explains how to run **Test in a Box** on a Windows computer where
you do not have administrator rights.

The application has been designed to work in engineering environments where
software installation may be restricted. It uses a **portable Python**
installation, allowing the application to run without modifying Windows,
installing software system-wide, or writing to the registry.

Once installed, starting Test in a Box is simply a matter of running a batch
file and opening the local web interface in your browser.

---

# Step 1 – Extract Test in a Box

Extract the repository to a local folder or a mapped drive.

For example:

```text
C:\Users\<you>\Documents\Test-in-a-Box
```

Do not run bootstrap directly from a UNC path such as
`\\server\share\Test-in-a-Box`. Map the share to a drive letter first.

---

# Step 2 – Run the bootstrap

Double-click:

```text
bootstrap.bat
```

The bootstrap checks for:

```text
python\python.exe
```

If it is missing, bootstrap downloads a stable official 64-bit WinPython Dot
runtime and creates the project `python` folder automatically. WinPython is
portable and does not require administrator rights.

Bootstrap then:

- creates required writable folders;
- installs or updates `requirements.txt`;
- checks optional vendor components;
- verifies the Python environment and project imports;
- offers to start Test in a Box.

The older file `1_install_dependencies.bat` remains as a compatibility wrapper
and now launches the same bootstrap process.

Internet access may be required for:

- `api.github.com`
- `github.com`
- `objects.githubusercontent.com`
- `pypi.org`
- `files.pythonhosted.org`

The Seeit native USB relay DLL is optional and is not downloaded by bootstrap.
Place a licensed matching DLL at:

```text
vendor\seeit\usb_relay_device.dll
```

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
---


# Seeit USBB Native USB Relay

The native USBB relay driver is Windows-only because it uses the vendor DLL:

```text
usb_relay_device.dll
```

Place the matching Win64 or Win32 DLL in:

```text
Test-in-a-Box\
    vendor\
        seeit\
            usb_relay_device.dll
```

No administrator rights are required. The DLL architecture must match the
portable Python architecture.

The DLL is not currently included with Test in a Box while redistribution
permission is being confirmed with Seeit.

For more than one identical board, use **Scan for Devices** in the instrument
cog menu. Some boards have duplicate factory serial numbers and no useful DLL
device path, so the current driver may save enumeration selectors such as
`index:1` and `index:2`. Re-scan and verify the boards after changing USB ports,
hubs or connected-board count.

See:

[`../instruments/seeit-usb-relay08.md`](../instruments/seeit-usb-relay08.md)

