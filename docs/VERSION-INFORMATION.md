# Version Information

Test in a Box exposes its installed software identity through:

```text
GET /api/version
```

The endpoint and About page use the same identity collector as run
manifests and Markdown reports.

## Sources

- `VERSION` — Test in a Box release version.
- `support/BUILD.json` — release stage, repository layout and component
  versions.
- `.update-state.json` — managed-update channel, ref, commit, update time
  and downloaded archive SHA-256.
- the running interpreter — Python version.

When `.update-state.json` is absent, the installation is reported as
`unmanaged`. This is expected for a freshly downloaded archive that has not
yet been updated by Updater V2.
