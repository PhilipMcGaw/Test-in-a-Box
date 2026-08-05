# Automatic WinPython bootstrap patch

This patch changes `1_install_dependencies.bat` so a new Windows installation
does not require the user to manually download, extract and rename WinPython.

## Behaviour

When `python\python.exe` already exists, setup uses it unchanged.

When it is missing, setup calls:

```text
tools\bootstrap_winpython.ps1
```

The helper:

1. queries the official `winpython/winpython` GitHub releases;
2. ignores draft and pre-release releases;
3. selects a stable 64-bit Python 3.13 Dot ZIP, falling back to 3.12;
4. downloads the official release asset;
5. verifies its SHA-256 digest when GitHub publishes one;
6. extracts the `python-*.amd64` runtime;
7. moves that runtime to the project's `python` folder;
8. returns control to the batch file;
9. installs `requirements.txt` with the new portable Python.

No administrator rights are required.

## Required internet access

First-time setup may need access to:

- `api.github.com`
- `github.com`
- `objects.githubusercontent.com`
- `pypi.org`
- `files.pythonhosted.org`

## Safety and failure behaviour

- An existing working `python` folder is never replaced.
- A non-empty incomplete `python` folder causes setup to stop rather than
  deleting unknown files.
- Draft and pre-release WinPython releases are ignored.
- Temporary extraction files are kept after a failure for inspection.
- The downloaded asset is checked for a plausible file size.
- SHA-256 is checked when the GitHub release API supplies a digest.

## Applying the patch

Extract the ZIP over the repository root. It replaces:

```text
1_install_dependencies.bat
```

and adds:

```text
tools\bootstrap_winpython.ps1
docs\automatic-winpython-setup.md
```
