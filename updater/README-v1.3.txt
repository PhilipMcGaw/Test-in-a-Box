# Updater v1.3 channel alias fix

This patch fixes the case where PowerShell received `s` instead of `stable`.

Both launch layers now accept and normalise:

- `S`
- `stable`
- `D`
- `development`

The batch launcher always passes the full channel name to PowerShell, and the
PowerShell script also normalises aliases itself as a second line of defence.

After applying the patch, any of these are valid:

```text
update.bat
update.bat S
update.bat stable
update.bat D
update.bat development
```
