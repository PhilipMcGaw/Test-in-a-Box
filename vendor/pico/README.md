# Pico SDK Installer

Bootstrap downloads the current official 64-bit PicoSDK installer directly
into:

```text
vendor/pico/installer/
```

Bootstrap does not run, move, or delete the installer.

Administrator rights are required once to install Pico Technology's
Windows drivers and native runtime for TC-08 and ADC-20/24 hardware.

After an administrator completes the installation, rerun `bootstrap.bat`.
Bootstrap then verifies that the official `picosdk` Python wrappers can
load the native TC-08 and PicoHRDL runtimes.

`installer-manifest.json` records the official source URL, file size, and
SHA-256 of the downloaded installer.
