#!/usr/bin/env bash
#
# Test in a Box - dependency installer for macOS, Raspberry Pi OS, and other
# Linux systems.
#
# This creates a self-contained virtual environment inside this folder
# (.venv/) and installs the required Python packages into it, using `uv`
# (a fast, portable package/venv manager). Nothing is installed system-wide
# and no admin/root rights are needed beyond, on Linux, the one-time serial
# port permission step this script offers to do for you.
#
# Run this once (and again later if requirements.txt changes):
#   ./1_install_dependencies.sh

set -euo pipefail

SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
cd "$SCRIPT_DIR"

echo "Test in a Box - installing dependencies"
echo "Project folder: $SCRIPT_DIR"
echo

# ---------------------------------------------------------------------------
# 1. Make sure `uv` is available
# ---------------------------------------------------------------------------
if ! command -v uv >/dev/null 2>&1; then
    echo "'uv' was not found - installing it now for your user account only"
    echo "(this does not require sudo/root)."
    echo
    curl -LsSf https://astral.sh/uv/install.sh | sh

    # The installer puts uv in ~/.local/bin or ~/.cargo/bin depending on
    # version; make sure this shell can see it without a fresh login.
    export PATH="$HOME/.local/bin:$HOME/.cargo/bin:$PATH"

    if ! command -v uv >/dev/null 2>&1; then
        echo
        echo "Could not find 'uv' on PATH even after installing it."
        echo "Open a new terminal window (so your PATH picks up the change)"
        echo "and run this script again."
        exit 1
    fi
fi

echo "Using uv: $(command -v uv)"
echo

# ---------------------------------------------------------------------------
# 2. Create the virtual environment
# ---------------------------------------------------------------------------
if [ ! -d ".venv" ]; then
    echo "Creating virtual environment in .venv/ ..."
    uv venv .venv
else
    echo ".venv/ already exists - reusing it."
fi
echo

# ---------------------------------------------------------------------------
# 3. Install the required packages into that environment
# ---------------------------------------------------------------------------
echo "Installing packages from requirements.txt ..."
uv pip install --python .venv/bin/python -r requirements.txt
echo

# ---------------------------------------------------------------------------
# 4. Linux only: offer to fix USB-serial permissions
# ---------------------------------------------------------------------------
# On Raspberry Pi OS / other Linux, USB-serial devices (the Aim-TTi PSU, the
# Seeit relay board, FTDI adapters, etc.) normally belong to the "dialout"
# group. Without this, connecting to them fails with a permissions error
# even though the device shows up in /dev.
if [ "$(uname -s)" = "Linux" ]; then
    if id -nG "$USER" 2>/dev/null | grep -qw dialout; then
        echo "Your user is already in the 'dialout' group - USB serial"
        echo "devices should be accessible without sudo."
    else
        echo "NOTE: your user is not yet in the 'dialout' group, which Linux"
        echo "uses to control access to USB-serial devices (PSU, relay board,"
        echo "FTDI adapters, etc). Without this you may see 'Permission"
        echo "denied' errors when connecting to real hardware."
        echo
        read -r -p "Add '$USER' to the 'dialout' group now? [y/N] " reply
        if [[ "$reply" =~ ^[Yy]$ ]]; then
            sudo usermod -a -G dialout "$USER"
            echo
            echo "Done. You must log out and back in (or reboot) for this"
            echo "to take effect."
        else
            echo "Skipped. You can do this later with:"
            echo "  sudo usermod -a -G dialout \$USER"
        fi
    fi
    echo
fi

echo "All done. Start the app with:"
echo "  ./2_start_app.sh"
