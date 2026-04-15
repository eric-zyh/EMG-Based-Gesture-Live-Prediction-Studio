#!/bin/bash
# Double-clickable shim for Finder. Locates python3 on macOS and forwards to
# launch.py, which handles the actual bootstrap (.venv, pip install,
# launching the GUI). In VS Code you can open launch.py directly and click
# "Run Python File" — this shim just exists because Finder only reliably
# double-clicks .command files.

set -u

SCRIPT_DIR="$( cd "$( dirname "${BASH_SOURCE[0]}" )" && pwd )"
cd "$SCRIPT_DIR"

printf "\n=== EMG launcher (macOS shim) ===\n"
printf "Project: %s\n\n" "$SCRIPT_DIR"

PYTHON_BIN=""
for candidate in \
    /opt/homebrew/bin/python3 \
    /usr/local/bin/python3 \
    /Library/Frameworks/Python.framework/Versions/Current/bin/python3 \
    python3 \
    /usr/bin/python3; do
    if command -v "$candidate" >/dev/null 2>&1; then
        PYTHON_BIN="$candidate"
        break
    fi
done

if [ -z "$PYTHON_BIN" ]; then
    printf "ERROR: Python 3 is not installed.\n\n"
    printf "Install from https://www.python.org/downloads/\n"
    printf "  or run:  brew install python3\n\n"
    read -r -p "Press Enter to close..." _
    exit 1
fi

printf "Found Python: "
"$PYTHON_BIN" --version
printf "             at %s\n\n" "$PYTHON_BIN"

"$PYTHON_BIN" "$SCRIPT_DIR/launch.py"
EXIT_CODE=$?

if [ $EXIT_CODE -ne 0 ]; then
    printf "\nlaunch.py exited with code %d.\n" "$EXIT_CODE"
    read -r -p "Press Enter to close..." _
fi

exit $EXIT_CODE
