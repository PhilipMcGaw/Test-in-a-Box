# Pico TC-08 and ADC-20/24 Runtime Setup

Pico Technology's Windows SDK installer requires administrator access
because it installs native Windows device drivers and runtime components.

Test in a Box therefore does not attempt to install PicoSDK silently.

## Bootstrap behaviour

Run:

```text
bootstrap.bat
```

When the Pico runtime is unavailable, bootstrap:

1. resolves Pico Technology's current official 64-bit SDK installer;
2. downloads it directly into `vendor/pico/installer/`;
3. records its URL, size and SHA-256 in
   `vendor/pico/installer-manifest.json`;
4. leaves the installer in place for an administrator;
5. continues bootstrap without requiring elevation.

Bootstrap never executes or deletes the Pico installer.

## One-time administrator step

An administrator must run the downloaded versioned installer once on each
Windows machine that will use Pico TC-08, ADC-20 or ADC-24 hardware.

After installation, rerun `bootstrap.bat`. The verification stage checks
that both official Python wrappers can load:

- `picosdk.usbtc08`
- `picosdk.picohrdl`

Machines that do not use Pico hardware remain fully functional without
installing PicoSDK.
