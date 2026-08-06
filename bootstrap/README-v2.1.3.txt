Bootstrap v2.1.3 fixes the optional Pico check in
bootstrap_verify.ps1.

Before the Pico SDK has been installed, the Python import probe writes a
traceback to stderr. Windows PowerShell 5.1 treated that expected stderr
as a terminating NativeCommandError because ErrorActionPreference was set
to Stop.

The verification probe now suppresses stdout/stderr, temporarily allows
native stderr, and records Pico support as INFO rather than failing the
required bootstrap checks.
