# Pico TC-08 and ADC-20/24 Runtime Setup

Pico Technology's Windows SDK requires administrator access because it
installs native Windows drivers and runtime components.

Test in a Box therefore downloads the installer but never runs it.

## Bootstrap behaviour

Run:

```text
bootstrap.bat
```

When Pico runtime support is unavailable, bootstrap:

1. resolves Pico Technology's current official 64-bit installer;
2. downloads it directly into `vendor/pico/installer/`;
3. records its URL, size, and SHA-256 in
   `vendor/pico/installer-manifest.json`;
4. leaves the installer in place;
5. continues without elevation.

Bootstrap does not use `/layout`, does not create `_bootstrap_pico`, and
does not delete the installer.

## One-time administrator step

An administrator must run the downloaded installer once on each Windows
machine that will use Pico TC-08, ADC-20, or ADC-24 hardware.

After installation, rerun `bootstrap.bat`. Pico support remains optional
on machines that do not use this hardware.
