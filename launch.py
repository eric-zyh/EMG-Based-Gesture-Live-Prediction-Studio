#!/usr/bin/env python3
"""
launch.py — one-click launcher for the EMG app.

Works identically whether you:
  * Double-click it in Finder (macOS Python Launcher, or via the
    setup_mac.command shim that just calls this file)
  * Click "Run Python File" in VS Code
  * Run `python3 launch.py` from any terminal
  * Double-click setup_windows.bat on Windows

Behavior:
  * First run  — creates `.venv` next to this file, installs
    `requirements.txt`, then relaunches itself using the venv's Python
    and starts `emg_data_gui.py`.
  * Later runs — skip bootstrap, relaunch straight into the venv Python
    and start `emg_data_gui.py`.

Bootstrap only uses the Python standard library. The GUI code (numpy,
sklearn, matplotlib, tkinter, pyserial, ...) is only imported after the
venv is guaranteed to exist and have its deps installed.
"""
from __future__ import annotations

import os
import subprocess
import sys
from pathlib import Path


PROJECT_DIR = Path(__file__).resolve().parent
VENV_DIR = PROJECT_DIR / ".venv"
REQUIREMENTS = PROJECT_DIR / "requirements.txt"
GUI_SCRIPT = PROJECT_DIR / "emg_data_gui.py"


# ---------------------------------------------------------------------------
# venv introspection
# ---------------------------------------------------------------------------

def _venv_python() -> Path:
    if os.name == "nt":
        return VENV_DIR / "Scripts" / "python.exe"
    return VENV_DIR / "bin" / "python"


def _running_inside_our_venv() -> bool:
    """True when this interpreter is the venv's Python (not the system one).

    We use sys.prefix vs sys.base_prefix (the standard venv indicator) and
    also require the prefix to match our `.venv` path so we don't pick up
    some unrelated venv the user happens to have activated.
    """
    in_any_venv = sys.prefix != getattr(sys, "base_prefix", sys.prefix)
    if not in_any_venv:
        return False
    try:
        return Path(sys.prefix).resolve() == VENV_DIR.resolve()
    except OSError:
        return False


# ---------------------------------------------------------------------------
# UI helpers
# ---------------------------------------------------------------------------

def _pause_if_interactive() -> None:
    """If we were double-clicked in Finder (stdin attached to a terminal),
    keep the window open so the user can read any error message before it
    vanishes. A no-op in non-interactive contexts (piped, CI, etc.)."""
    try:
        if sys.stdin is not None and sys.stdin.isatty():
            try:
                input("\nPress Enter to close...")
            except EOFError:
                pass
    except Exception:
        pass


def _die(message: str, code: int = 1) -> "None":
    print(f"ERROR: {message}", file=sys.stderr)
    _pause_if_interactive()
    sys.exit(code)


# ---------------------------------------------------------------------------
# Bootstrap
# ---------------------------------------------------------------------------

def _create_venv() -> None:
    print(f"Creating virtual environment at {VENV_DIR} ...", flush=True)
    try:
        subprocess.check_call([sys.executable, "-m", "venv", str(VENV_DIR)])
    except subprocess.CalledProcessError as exc:
        _die(
            "Failed to create virtualenv.\n"
            "Install Python 3 from https://www.python.org/downloads/ or\n"
            "  brew install python3           (macOS)\n"
            f"Underlying error: {exc}"
        )


def _install_requirements() -> None:
    venv_py = _venv_python()
    if not venv_py.exists():
        _die(f"venv Python not found at {venv_py} after creating venv")

    print("Upgrading pip ...", flush=True)
    try:
        subprocess.check_call(
            [str(venv_py), "-m", "pip", "install", "--upgrade", "pip"]
        )
    except subprocess.CalledProcessError as exc:
        _die(f"pip upgrade failed: {exc}")

    if REQUIREMENTS.exists():
        print(f"Installing dependencies from {REQUIREMENTS.name} ...", flush=True)
        try:
            subprocess.check_call(
                [str(venv_py), "-m", "pip", "install", "-r", str(REQUIREMENTS)]
            )
        except subprocess.CalledProcessError as exc:
            _die(f"Dependency install failed: {exc}")
    else:
        print(
            f"WARNING: {REQUIREMENTS} not found — skipping dependency install.",
            file=sys.stderr,
            flush=True,
        )


def _relaunch_in_venv() -> "None":
    """Spawn a new process using the venv's Python that re-runs this script.
    Using subprocess.run (not os.execv) keeps this cross-platform — os.execv
    has awkward semantics on Windows and confuses some IDE integrations.
    """
    venv_py = _venv_python()
    print(f"\nRelaunching under {venv_py} ...\n", flush=True)
    try:
        result = subprocess.run(
            [str(venv_py), str(Path(__file__).resolve())],
            cwd=str(PROJECT_DIR),
        )
    except KeyboardInterrupt:
        sys.exit(130)
    sys.exit(result.returncode)


# ---------------------------------------------------------------------------
# GUI entry
# ---------------------------------------------------------------------------

def _launch_gui() -> None:
    if not GUI_SCRIPT.exists():
        _die(f"{GUI_SCRIPT} does not exist")

    # Make sure the project directory is importable for `import emg_data_gui`.
    if str(PROJECT_DIR) not in sys.path:
        sys.path.insert(0, str(PROJECT_DIR))

    print(f"Launching EMG app from {GUI_SCRIPT} ...", flush=True)
    try:
        import emg_data_gui  # type: ignore
    except ModuleNotFoundError as exc:
        _die(
            f"Failed to import emg_data_gui: {exc}.\n"
            "This usually means the venv is missing a dependency.\n"
            "Try deleting the .venv folder and running launch.py again."
        )
    except Exception as exc:  # noqa: BLE001
        _die(f"Failed to import emg_data_gui: {exc}")

    if not hasattr(emg_data_gui, "main"):
        _die("emg_data_gui.main() is missing — cannot start the GUI")

    try:
        emg_data_gui.main()
    except SystemExit:
        raise
    except KeyboardInterrupt:
        sys.exit(130)
    except Exception as exc:  # noqa: BLE001
        print(f"ERROR: the GUI exited with an exception: {exc}", file=sys.stderr)
        _pause_if_interactive()
        sys.exit(1)


# ---------------------------------------------------------------------------
# Main
# ---------------------------------------------------------------------------

def main() -> None:
    os.chdir(PROJECT_DIR)
    print(f"=== EMG launcher (project: {PROJECT_DIR}) ===", flush=True)
    print(f"Python: {sys.version.split()[0]}  @ {sys.executable}", flush=True)

    if _running_inside_our_venv():
        _launch_gui()
        return

    if _venv_python().exists():
        # venv already set up; just relaunch through it.
        _relaunch_in_venv()
        return

    # First-run bootstrap.
    _create_venv()
    _install_requirements()
    _relaunch_in_venv()


if __name__ == "__main__":
    main()
