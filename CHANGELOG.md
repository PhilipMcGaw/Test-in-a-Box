# Changelog

All notable changes to Test in a Box are recorded here.

## 0.1.0-alpha — unreleased

### Added

- Local FastAPI web application and Blockly procedure builder.
- Configure Devices interface and Instrument Library.
- Driver-based hardware abstraction and discovery.
- Aim-TTi, EA PS 2000 B, Korad/Tenma, KEL103, Pico and Seeit relay drivers.
- Native Windows Seeit USBB relay support.
- Relay and PSU Blockly blocks.
- DUT mapping, per-DUT CSV results and run metadata.
- Machine-readable run manifest and Markdown summary.
- Portable Windows bootstrap with automatic WinPython setup.
- Updater V2 with Stable, Development and Rollback actions.
- Repository Refactor v1 and shared build metadata.

### Known limitations

- EA PS 2000 B output-enable validation remains outstanding.
- Korad/Tenma and KEL103 drivers require current bench validation.
- Native Seeit USBB multi-board validation remains outstanding.
- Seeit native relay support is Windows-only.
