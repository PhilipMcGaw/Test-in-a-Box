# Updater v2.2 — Bootstrap Console Cleanup

The updater previously launched `bootstrap.bat` with `Start-Process`.
Windows executes batch files through a separate `cmd.exe`, which could
leave an additional command window open after the application restarted.

Updater v2.2 invokes bootstrap using the current console:

```powershell
& $env:ComSpec /D /C "call `"$Bootstrap`""
```

It also sets:

```text
TIAB_BOOTSTRAP_NONINTERACTIVE=1
```

while bootstrap is running. Bootstrap therefore skips its own application
launch prompt and returns control to the updater. The updater remains the
single place that asks whether Test in a Box should be launched.
