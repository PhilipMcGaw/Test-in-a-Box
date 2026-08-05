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
