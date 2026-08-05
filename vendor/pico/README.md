# Pico Runtime Support

This directory is populated by `bootstrap/bootstrap_pico.ps1`.

Bootstrap downloads the official current 64-bit PicoSDK installer from
Pico Technology, installs it into a temporary project-local directory, and
retains only runtime DLLs required by Test in a Box.

Expected runtime files include:

```text
runtime/usb_tc08.dll
runtime/picohrdl.dll
runtime-manifest.json
```

Runtime DLLs are generated installation artifacts and should not normally
be committed to the repository. The manifest records the official source
URL and SHA-256 of the downloaded installer.

Pico Technology licensing applies to the downloaded software.
