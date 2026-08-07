# Startup v2.1 Hotfix

Startup v2 accidentally launched the FastAPI server twice. The second process
then failed to bind port 8765 and could also fail to open serial ports already
owned by the first process.

Startup v2.1 moves startup orchestration into `support/launcher.ps1`.

The launcher:

- starts exactly one `python -m webapp.server` process;
- keeps server output in the original command window;
- polls `/api/version` until the application is ready;
- opens the browser only after readiness;
- waits for the server process for the lifetime of the application;
- terminates startup cleanly if readiness times out.
