# Updater v1.2 channel-selection fix

This patch replaces the previous `update.bat`.

The earlier batch file placed labels such as `:stable` and `:development`
inside a parenthesized `if` block. Windows `cmd.exe` does not handle that
structure reliably, so the `CHANNEL` variable could remain empty even after
selecting Stable or Development.

The corrected batch file:

- keeps all labels at the top level;
- routes menu choices with `goto`;
- validates the selected channel before launching PowerShell;
- prints the selected channel;
- checks that `updater\update.ps1` exists;
- passes `-Channel stable` or `-Channel development` explicitly.

After applying the patch, run:

```text
update.bat
```

or bypass the menu with:

```text
update.bat stable
update.bat development
```
