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

1. downloads Pico Technology's small 64-bit SDK web bootstrapper;
2. runs its `/layout` action to download the complete offline bundle;
3. stores the full versioned installer under
   `vendor/pico/installer/`;
4. records SHA-256 hashes in
   `vendor/pico/installer-manifest.json`;
5. continues bootstrap without requiring elevation.

Bootstrap never executes the Pico installer.

## One-time administrator step

An administrator must run the downloaded versioned installer once on each
Windows machine that will use Pico TC-08, ADC-20 or ADC-24 hardware.

After installation, rerun `bootstrap.bat`. The verification stage checks
that both official Python wrappers can load:

- `picosdk.usbtc08`
- `picosdk.picohrdl`

Machines that do not use Pico hardware remain fully functional without
installing PicoSDK.
