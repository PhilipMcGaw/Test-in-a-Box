Bootstrap v2.1.2 fixes the Pico runtime availability probe on Windows
PowerShell 5.1.

A missing Pico runtime is expected before the offline installer has been
installed. Python writes the import traceback to stderr. With
ErrorActionPreference set to Stop, PowerShell converted that expected
stderr output into a terminating NativeCommandError and stopped bootstrap.

The probe now suppresses Python output, temporarily allows native stderr,
and uses Python's exit code to decide whether the Pico runtime is present.
