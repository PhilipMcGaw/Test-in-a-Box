# Updater V2

Updater V2 deploys Test in a Box without requiring Git.

## Channels

- **Stable** uses the latest published release, falling back to the newest tag.
- **Development** uses the configured branch (`main` by default).
- **Rollback** restores a previous application backup.

## Preserved local state

- `python/`
- `vendor/`
- `logs/`
- `runs/`
- `results/`
- `sequences/`
- `webapp/config.json`

## Traceability

A successful update writes `.update-state.json` containing:

- updater version;
- channel;
- release/tag/branch;
- commit identity where available;
- downloaded archive SHA-256;
- update time;
- backup path.

Run reports use this file to record the exact deployed Test in a Box build.

## Usage

```text
update.bat
update.bat stable
update.bat development
update.bat rollback
```


## Repository responsibility

The `updater/` directory contains deployment and rollback logic only.
Bootstrap owns Python and dependency preparation; engineering utilities
belong in `tools/`.

## Running application detection

Updater v2.1 checks for a Test in a Box process associated with the current
repository and for a process listening on `127.0.0.1:8765`.

When an instance is found, the operator can:

- wait five seconds and check again;
- explicitly force-close the detected process;
- cancel the update.

The updater does not silently terminate a running test. A future web-interface
shutdown button and graceful shutdown API are tracked on the project roadmap.

## Bootstrap console handling — Updater v2.2

Bootstrap now runs in the updater's existing console rather than through a
separate `Start-Process` call for the batch file.

During a managed update:

- bootstrap output remains visible in the updater console;
- the updater waits for bootstrap to finish;
- bootstrap does not ask whether it should launch Test in a Box;
- the updater asks once, after bootstrap succeeds;
- no orphaned bootstrap `cmd.exe` window should remain.

If bootstrap fails, the updater reports the exit code and the outer
`update.bat` keeps the console available for review.
