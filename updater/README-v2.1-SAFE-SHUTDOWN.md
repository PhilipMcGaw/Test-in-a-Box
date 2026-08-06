# Updater v2.1 — Safe Running-Instance Handling

The updater no longer relies on the operator confirming that Test in a Box
has been closed.

It detects:

- processes whose command line refers to the current project and starts
  `webapp/server.py`, Uvicorn, or `2_start_app.bat`;
- the process listening on `127.0.0.1:8765`.

When found, the updater offers:

- **C** — wait five seconds and check again;
- **F** — force-close only the detected process IDs;
- **Q** — cancel without changing files.

A graceful shutdown button/API is deliberately not included in this patch.
It has been added to the roadmap so the UI location and safety behaviour can
be designed separately.
