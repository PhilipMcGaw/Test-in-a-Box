Bootstrap v2.2 replaces all previous Pico download logic.

Changes:

- no `/layout` command;
- no `_bootstrap_pico` temporary directory;
- no installer execution;
- no installer deletion;
- direct download to `vendor/pico/installer/`;
- SHA-256 and source metadata recorded;
- missing Pico support remains optional;
- PowerShell 5.1 runtime probes no longer terminate bootstrap.
