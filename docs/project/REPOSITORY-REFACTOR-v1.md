# Repository Refactor v1 Migration

## Purpose

This refactor freezes the high-level repository layout before
`v0.1.0-alpha`.

## User entry points retained at the repository root

- `bootstrap.bat`
- `update.bat`
- `2_start_app.bat`
- `1_install_dependencies.bat` (compatibility wrapper)
- `1_install_dependencies.sh`
- `2_start_app.sh`

## Responsibilities

- `bootstrap/` — Windows environment preparation.
- `updater/` — no-Git update and rollback support.
- `tools/` — engineering and driver commissioning utilities.
- `support/` — shared build metadata.
- `tiab/` — application and driver code.
- `webapp/` — local web UI and server.
- `vendor/` — optional third-party runtime components.
- `docs/` — project and user documentation.

## Moved files

- `DEVELOPMENT_STATUS.md` → `docs/project/DEVELOPMENT-STATUS.md`
- `SETUP_INSTRUCTIONS.md` → `docs/getting-started/WINDOWS.md`
- `SETUP_INSTRUCTIONS_MAC_AND_RASPBERRY_PI.md`
  → `docs/getting-started/MAC-LINUX-RASPBERRY-PI.md`
- `code review.md` → `docs/reviews/CODE-REVIEW.md`

## Removed obsolete duplicates

- `tools/bootstrap_winpython.ps1`
- `updater/update.ps1`
- `updater/update_config.json`
- `updater/README-v1.1.txt`
- `updater/README-v1.2.txt`
- `updater/README-v1.3.txt`
- `updater/README-v1.4.txt`
- `.update-state.json` from the source distribution

The active updater is:

```text
updater/updater.ps1
updater/updater_config.json
```

The active WinPython bootstrap helper is:

```text
bootstrap/bootstrap_winpython.ps1
```
