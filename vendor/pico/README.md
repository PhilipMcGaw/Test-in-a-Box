# Pico SDK Offline Installer

Bootstrap downloads the official 64-bit PicoSDK installer
into:

```text
vendor/pico/installer/
```

Bootstrap does not execute or delete the installer.

Administrator rights are required once to install Pico Technology's
Windows device drivers and native runtime for TC-08 and ADC-20/24 hardware.

After an administrator completes the installation, run `bootstrap.bat`
again. The bootstrap verification step checks whether the official
`picosdk` wrappers can load the native TC-08 and PicoHRDL runtimes.

`installer-manifest.json` records the official source URL and SHA-256
hashes of the downloaded bootstrapper and offline installer.

Pico Technology's licence applies to the downloaded installer and runtime.
