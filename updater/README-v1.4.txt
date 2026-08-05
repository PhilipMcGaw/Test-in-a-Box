# Updater v1.4 channel transport fix

The menu was correctly selecting `stable`, but the PowerShell process was still
prompting for `Channel`. This means the named argument was being lost while
`cmd.exe` parsed the multi-line PowerShell command.

This patch removes that ambiguity:

- the PowerShell invocation is now one physical line;
- `CHANNEL` is passed as the named `-Channel` argument;
- it is also passed through `TIAB_UPDATE_CHANNEL` as a fallback;
- `update.ps1` no longer prompts interactively for a missing channel;
- PowerShell prints the channel it received before continuing.

Expected startup output:

```text
Selected update channel: stable

PowerShell received channel: stable
```

Valid commands remain:

```text
update.bat
update.bat S
update.bat stable
update.bat D
update.bat development
```
