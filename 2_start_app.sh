#!/usr/bin/env bash
#
# Test in a Box - start the app on macOS, Raspberry Pi OS, or other Linux.
#
# Run this after 1_install_dependencies.sh has completed successfully:
#   ./2_start_app.sh
#
# Keep the terminal window open while you're using the app; press Ctrl+C
# in this window (or just close it) to stop the app.

set -euo pipefail

SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
cd "$SCRIPT_DIR"

PYTHON="$SCRIPT_DIR/.venv/bin/python"

if [ ! -x "$PYTHON" ]; then
    echo "Could not find $PYTHON"
    echo
    echo "Run ./1_install_dependencies.sh first to set up the virtual"
    echo "environment."
    exit 1
fi

URL="http://127.0.0.1:8765"

echo "Starting Test in a Box..."
echo "This window must stay open while you're using the app."
echo "Press Ctrl+C here to stop it."
echo

# Open the browser a couple of seconds after launch, once the server has
# had a moment to start listening. This runs in the background so it
# doesn't block starting the server itself.
(
    sleep 2
    if [ "$(uname -s)" = "Darwin" ]; then
        open "$URL" >/dev/null 2>&1 || true
    elif command -v xdg-open >/dev/null 2>&1; then
        xdg-open "$URL" >/dev/null 2>&1 || true
    else
        echo "Open this URL in your browser: $URL"
    fi
) &

exec "$PYTHON" -m webapp.server
