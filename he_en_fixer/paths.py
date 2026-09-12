"""Install and runtime locations (user-level, no admin)."""

from __future__ import annotations

import sys
from pathlib import Path

APP_NAME = "HE-EN Fixer"
APP_ID = "he-en-fixer"


def is_frozen() -> bool:
    return bool(getattr(sys, "frozen", False))


def project_root() -> Path:
    if is_frozen():
        return Path(sys.executable).resolve().parent
    return Path(__file__).resolve().parent.parent


def config_dir() -> Path:
    if sys.platform == "win32":
        return Path.home() / "AppData" / "Roaming" / APP_ID
    if sys.platform == "darwin":
        return Path.home() / "Library" / "Application Support" / APP_ID
    return Path.home() / ".config" / APP_ID


def install_dir() -> Path:
    if sys.platform == "win32":
        return Path.home() / "AppData" / "Local" / APP_NAME
    if sys.platform == "darwin":
        return Path.home() / "Library" / "Application Support" / APP_ID
    return Path.home() / ".local" / "share" / APP_ID


def desktop_dir() -> Path:
    return Path.home() / "Desktop"


def start_menu_dir() -> Path:
    if sys.platform == "win32":
        return (
            Path.home()
            / "AppData"
            / "Roaming"
            / "Microsoft"
            / "Windows"
            / "Start Menu"
            / "Programs"
        )
    if sys.platform == "darwin":
        return Path.home() / "Applications"
    return Path.home() / ".local" / "share" / "applications"


def launch_target() -> tuple[str, str, str]:
    """Return (executable, args, working_directory) for the installed or current app."""
    installed = install_dir()
    if sys.platform == "win32":
        frozen_exe = installed / f"{APP_NAME}.exe"
        if frozen_exe.exists():
            return str(frozen_exe), "", str(installed)
        pythonw = installed / ".venv" / "Scripts" / "pythonw.exe"
        script = installed / "main.py"
        if pythonw.exists() and script.exists():
            return str(pythonw), f'"{script}"', str(installed)
    else:
        frozen = installed / APP_NAME
        if frozen.exists():
            return str(frozen), "", str(installed)
        python = installed / ".venv" / "bin" / "python"
        script = installed / "main.py"
        if python.exists() and script.exists():
            return str(python), str(script), str(installed)

    if is_frozen():
        return str(Path(sys.executable)), "", str(Path(sys.executable).parent)
    root = project_root()
    if sys.platform == "win32":
        pythonw = root / ".venv" / "Scripts" / "pythonw.exe"
        if pythonw.exists():
            return str(pythonw), f'"{root / "main.py"}"', str(root)
        return sys.executable, f'"{root / "main.py"}"', str(root)
    python = root / ".venv" / "bin" / "python"
    if python.exists():
        return str(python), str(root / "main.py"), str(root)
    return sys.executable, str(root / "main.py"), str(root)
