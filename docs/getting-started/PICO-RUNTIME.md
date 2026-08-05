# Portable Pico Runtime Support

Test in a Box can prepare Windows runtime support for:

- Pico TC-08;
- Pico ADC-20;
- Pico ADC-24.

Run:

```text
bootstrap.bat
```

Bootstrap uses Pico Technology's official 64-bit SDK download page to find
the current stable installer. It downloads the installer, stages it in a
temporary project-local directory, and copies the required runtime DLLs to:

```text
vendor/pico/runtime/
```

No permanent system PATH modification is made. The Pico drivers add this
project-local directory to the DLL search path before importing the
official `picosdk` Python wrappers.

Bootstrap records the download URL, installer SHA-256 and copied filenames
in:

```text
vendor/pico/runtime-manifest.json
```

## Network access

First-time setup requires access to `www.picotech.com`.

## Licensing

The runtime is downloaded directly from Pico Technology. Pico's licence
applies. Test in a Box does not include Pico binaries in the source
repository.

## Troubleshooting

If the unattended installer options change, bootstrap retains the
downloaded installer under `_bootstrap_pico` and reports its path.
