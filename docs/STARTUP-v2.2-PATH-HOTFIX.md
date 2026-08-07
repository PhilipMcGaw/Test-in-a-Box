# Startup v2.2 Path Hotfix

The launcher no longer normalizes the project-root argument with the previous
path API that raised `Illegal characters in path` on the affected Windows
installation.

It now trims the incoming argument, verifies the directory exists, resolves the
existing directory with `Resolve-Path`, starts exactly one server process,
waits for `/api/version`, and opens the browser only after the application is
ready.
