# Test in a Box Updater

The updater does not require Git to be installed.

Run:

```text
update.bat
```

It offers two update channels.

## Stable

Stable first checks for a published GitHub release. If there is no release, it
uses the newest repository tag.

If neither a release nor a tag exists, the updater explains that no stable
version is available and leaves the installation unchanged.

## Development

Development downloads the current `main` branch. This can include unfinished or
not-yet-validated changes and should only be used on development or evaluation
machines.

## Preserved local content

Updates preserve:

```text
python/
vendor/
logs/
runs/
results/
sequences/
webapp/config.json
```

A backup of the existing application files is created under:

```text
_update_backups/
```

before project files are replaced.

## Version state

After a successful managed update, `.update-state.json` records:

- the selected channel;
- the installed release, tag or branch;
- the repository;
- the update time;
- the backup location.

## Command-line selection

The interactive menu can be bypassed:

```text
update.bat stable
update.bat development
```

## Important

Close Test in a Box before running an update.

Stable source archives come from a published release tag or repository tag.
Development source archives come directly from the configured branch.
