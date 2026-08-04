# Roadmap

## Current alpha capability

The current alpha includes:

- a local FastAPI web application;
- a Blockly test-procedure editor;
- the Configure Devices interface;
- mock instruments;
- driver-based hardware abstraction;
- run, pause, resume, step and stop controls;
- sequence save and load;
- DUT-to-position mapping;
- per-DUT CSV result logging;
- engineering examples;
- bench-tested control of a physical Thurlby Thandar QL355P;
- native Windows control of physical Seeit USBB relay hardware;
- driver-level instrument discovery;
- run metadata containing host, user, OS, Python and instrument identity.

## Remaining Version 0.1 work

Version 0.1 is intended to add or complete:

- reusable Instrument Library workflows;
- parameters defined in one place;
- explicit engineering units;
- logical hardware roles;
- progress percentage and estimated finish time;
- current DUT and current test step;
- a Markdown run summary;
- validated safe-state behaviour across applicable drivers;
- final validation of multiple identical native USBB relay boards in the main application;
- a complete real electrical or environmental validation procedure;
- at least two different physical instrument classes used together.

## After Version 0.1

Planned improvements include:

- better reports and plots;
- reusable engineering blocks;
- richer pass, warning and fail behaviour;
- stronger pre-run validation;
- improved recovery and diagnostics;
- additional instrument drivers.

## Longer term

Possible longer-term work includes:

- database storage;
- test versioning;
- calibration integration;
- operator workflows;
- barcode support;
- multi-rig dashboards;
- notifications;
- andon lights;
- production and end-of-line features.
