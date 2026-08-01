## Running this on Windows with no admin rights

See **SETUP_INSTRUCTIONS.md** for step-by-step, non-developer instructions.
Short version: a portable Python + double-click `.bat` files start a local
web server (`webapp/server.py`) that serves the Blockly-based builder in
your browser at `http://127.0.0.1:8765` — nothing is installed system-wide.

---

# hwapp — hardware abstraction + test-run core

This is the backend skeleton for the Blockly-style hardware test app: a
driver interface, a registry so new hardware is a drop-in, DUT-to-position
mapping, and per-DUT CSV logging. The Blockly frontend and code generator
are the next layer to build on top of this.

## Layout

```
hwapp/
  drivers/
    base.py            Driver ABC, CapabilityDescriptor, Position, LogEvent
    registry.py         @register_driver("type_name") registry
    scpi_generic.py     Config-driven generic SCPI driver (PyVISA)
    scpi_command_map.example.json   Example config for a new SCPI instrument
    seeit_relay.py      Seeit USBB-RELAY08 (serial, 8 channel)
    pico_tc08.py        Pico TC-08 thermocouple logger
    pico_adc.py         Pico ADC-20/24
    mock.py             mock_psu / mock_relay — no hardware needed, for dev/testing
  run/
    mapping.py          DutMapping — position -> DUT UID, locked for the run
    csv_logger.py        Routes every event to runs/<run_id>/run_<id>_DUT_<uid>.csv
    runner.py            TestRunner — what a generated script calls into
  example_scripts/
    demo_test.py         Hand-written stand-in for a Blockly-generated script
webapp/
  server.py              FastAPI app: serves the page, /api/devices, /api/run, /ws/console
  config.json            Which devices to connect + the DUT position mapping
  static/
    index.html           The Blockly workspace page
    app.js               Wires up devices, run button, live console
    custom_blocks.js     Hardware-specific Blockly blocks (set/get/wait/log/assert)
    generators.js        Python code generation for those blocks
    blockly/             Blockly library files, bundled locally (works with no internet)
1_install_dependencies.bat   Windows: install required packages (run once)
2_start_app.bat              Windows: start the app + open the browser
SETUP_INSTRUCTIONS.md        Non-developer setup guide for locked-down Windows 11
```

## Running the demo (no hardware required)

```
pip install -r requirements.txt   # only needed for real hardware drivers
python3 -m hwapp.example_scripts.demo_test
```

This runs a two-DUT multiplexed sweep test on mock PSUs/relays and writes:

```
runs/demo_run_001/run_demo_run_001_DUT_DUT-0001.csv
runs/demo_run_001/run_demo_run_001_DUT_DUT-0002.csv
runs/demo_run_001/run_demo_run_001_DUT_unassigned.csv   (events with no DUT mapping)
```

All three files share the same schema:
`timestamp, device_id, position, channel, value, unit, event_type`
where `event_type` is one of `measurement`, `state` (a commanded setpoint),
`log`, or `assert`.

## Adding new hardware

- **SCPI instrument**: no new code — copy `scpi_command_map.example.json`,
  fill in the VISA resource string and the SCPI strings for each
  position, then `runner.add_device("scpi", "my_instrument",
  command_map_path="my_instrument.json")`.
- **Non-SCPI instrument**: subclass `Driver` in a new file under
  `drivers/`, implement `connect`, `close`, `capabilities`, and whichever
  of `write`/`read`/`query` make sense, decorate the class with
  `@register_driver("your_type_name")`, and import the module once so the
  decorator runs (see how `demo_test.py` imports `hwapp.drivers.mock`).

## Known gaps / next steps

- **Seeit USBB-RELAY08 protocol** is adapted from a community driver for
  the same board family (no public vendor protocol doc) — worth
  confirming byte-for-byte against your actual unit before relying on it.
- **Pico TC-08 / ADC-20/24 drivers** call the picosdk wrapper functions as
  documented, but haven't been exercised against real hardware yet in
  this skeleton — check channel/units setup against your specific unit.
- **PSU driver**: `aimtti_psu` driver added, using Aim-TTi's standard
  remote command set (confirmed against the official CPX400 manual) over
  serial/USB-virtual-COM — no VISA/NI-VISA needed for this one. Verified
  against a simulated instrument that speaks the documented protocol;
  still worth a first real-hardware smoke test (COM port, baud, exact
  reply formatting) before relying on it for real runs.
- **Blockly frontend**: built — a full Blockly workspace with custom
  hardware blocks, Pause/Step/Stop, loop iteration reporting, sequence
  save/load, and operator-prompt blocks, served by `webapp/server.py`.
- **Report generation**: not started — reads the CSVs in a run directory
  and produces one section per DUT.

## License

This project ("Test in a Box") is licensed under
**Creative Commons Attribution-NonCommercial-ShareAlike 4.0 International
(CC BY-NC-SA 4.0)** — see the `LICENSE` file in the project root for the
full text.

In short: you're free to use, adapt, and share this project, provided
you (a) give attribution, (b) don't use it commercially, and (c) share
any adaptations under the same license terms.

Note that CC licenses are written for creative/media works rather than
software specifically (no patent grant, no software-specific
distribution terms) — this is a deliberate choice for this project, just
worth being aware of if you plan to combine it with other code under a
different license.
