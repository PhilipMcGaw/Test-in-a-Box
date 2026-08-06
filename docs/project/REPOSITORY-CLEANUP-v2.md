# Repository Cleanup v2

## Baseline

This cleanup was built from `Test-in-a-Box-main(6).zip`.

## Scope

The cleanup removes superseded files, standardises runtime paths, improves
startup diagnostics, and polishes reporting without redesigning the current
architecture.

## Removed files

- `bootstrap/README-v2.1.2.txt`
- `bootstrap/README-v2.1.3.txt`
- `bootstrap/README-v2.1.4.txt`
- `bootstrap/README-v2.2.txt`
- `tiab/drivers/seeit_relay.py`
- `webapp/sequences/test 1.json`
- `docs/automatic-winpython-setup.md`
- `docs/relay-channel-labels.md`
- `docs/updater-roadmap.md`

## Runtime path standardisation

The application now uses:

```text
webapp/config.json
webapp/runs/
webapp/sequences/
```

Bootstrap no longer creates root-level `runs/` or `sequences/` directories.
Updater preservation and exclusions were updated to match the application
paths.

## Reporting improvements

- Markdown summaries include run duration.
- The software section is formatted as an engineering summary table.
- Every configured instrument is listed, even when its identity was not
  captured.
- The manifest contains `configured_instruments` separately from
  `instrument_identities`.
- Configuration, DUT mapping and generated-procedure hashes remain unchanged.

## Startup improvements

The startup banner now prints:

- version and component versions;
- update channel, ref and commit;
- configuration path;
- run-output path;
- sequence path;
- Pico runtime availability;
- local server address.

Optional Pico runtime absence is reported once and no longer resembles a
startup failure.

## Compatibility note

The manifest schema remains version `1`, but the old `instruments` field is
replaced by the clearer fields:

```text
configured_instruments
instrument_identities
```

Consumers that parse the old field should be updated before adopting this
cleanup.


## Validation

- Python syntax: passed for 29 files.
- JavaScript syntax: passed for 5 files.
- JSON parsing: passed.
- Canonical native USB relay driver: present.
- Duplicate native USB relay driver: removed.
- Markdown relative-link warnings: 0.
