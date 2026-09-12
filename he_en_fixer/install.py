"""User-level install and uninstall. Never needs administrator rights."""

from __future__ import annotations

import json
import shutil
import subprocess
import sys
import time
from dataclasses import dataclass
from pathlib import Path

from . import __version__
from .paths import (
    APP_NAME,
    config_dir,
    desktop_dir,
    install_dir,
    is_frozen,
    launch_target,
    project_root,
    start_menu_dir,
)
from . import startup

SKIP_NAMES = {
    ".git",
    ".venv",
    "__pycache__",
    ".pytest_cache",
    "build",
    "dist",
    "release",
    ".idea",
    ".vscode",
}


@dataclass
class InstallOptions:
    desktop_shortcut: bool = True
    start_menu: bool = True
    start_at_login: bool = False


def is_installed() -> bool:
    marker = install_dir() / "installed.json"
    return marker.exists()


def install(options: InstallOptions, progress=None) -> Path:
    dest = install_dir()
    dest.mkdir(parents=True, exist_ok=True)
    _log(progress, f"Installing to {dest}")

    if is_frozen():
        _copy_frozen(dest, progress)
    else:
        _copy_source(dest, progress)
        _make_venv(dest, progress)

    marker = {
        "version": __version__,
        "installed_at": time.strftime("%Y-%m-%dT%H:%M:%S"),
        "frozen": is_frozen(),
        "platform": sys.platform,
    }
    (dest / "installed.json").write_text(json.dumps(marker, indent=2) + "\n", encoding="utf-8")

    target, args, workdir = launch_target()
    icon = dest / "he_en_fixer" / "assets" / "icon.ico"
    if not icon.exists():
        icon = dest / f"{APP_NAME}.exe" if (dest / f"{APP_NAME}.exe").exists() else None
    if options.desktop_shortcut:
        _log(progress, "Creating desktop shortcut")
        startup.create_shortcut(
            desktop_dir() / _launcher_name(), target, args, workdir, icon=icon
        )
    if options.start_menu:
        _log(progress, "Adding to Start Menu / Applications")
        startup.create_shortcut(
            start_menu_dir() / _launcher_name(), target, args, workdir, icon=icon
        )
    if options.start_at_login:
        _log(progress, "Enabling start at login")
        startup.set_enabled(True)
    else:
        startup.set_enabled(False)

    _log(progress, "Done")
    return dest


def uninstall(progress=None) -> None:
    _log(progress, "Removing shortcuts and login item")
    for path in (
        desktop_dir() / _launcher_name(),
        start_menu_dir() / _launcher_name(),
    ):
        if path.exists():
            path.unlink()
    startup.set_enabled(False)

    dest = install_dir()
    settings = config_dir()
    running_from_install = False
    try:
        running_from_install = dest in Path(sys.executable).resolve().parents or Path(
            sys.executable
        ).resolve().parent == dest
    except Exception:
        running_from_install = False

    if dest.exists():
        _log(progress, f"Removing {dest}")
        if running_from_install:
            _delayed_delete(dest)
        else:
            shutil.rmtree(dest, ignore_errors=True)
    if settings.exists():
        shutil.rmtree(settings, ignore_errors=True)
    _log(progress, "Uninstalled")


def launch_app() -> None:
    target, args, workdir = launch_target()
    cmd = [target]
    if args:
        cmd.append(args.strip().strip('"'))
    kwargs = {"cwd": workdir, "close_fds": True}
    if sys.platform == "win32":
        kwargs["creationflags"] = subprocess.DETACHED_PROCESS | subprocess.CREATE_NEW_PROCESS_GROUP
        subprocess.Popen(cmd, **kwargs)
        return
    subprocess.Popen(cmd, start_new_session=True, **kwargs)


def _launcher_name() -> str:
    if sys.platform == "win32":
        return f"{APP_NAME}.lnk"
    return f"{APP_NAME}.command"


def _copy_frozen(dest: Path, progress) -> None:
    source = Path(sys.executable).resolve().parent
    _log(progress, "Copying application files")
    for item in source.iterdir():
        target = dest / item.name
        if item.is_dir():
            if target.exists():
                shutil.rmtree(target)
            shutil.copytree(item, target, ignore=shutil.ignore_patterns(*SKIP_NAMES))
        else:
            shutil.copy2(item, target)


def _copy_source(dest: Path, progress) -> None:
    source = project_root()
    _log(progress, "Copying program files")
    names = ["he_en_fixer", "main.py", "requirements.txt", "README.md"]
    for name in names:
        src = source / name
        if not src.exists():
            continue
        target = dest / name
        if src.is_dir():
            if target.exists():
                shutil.rmtree(target)
            shutil.copytree(
                src,
                target,
                ignore=shutil.ignore_patterns("__pycache__", "*.pyc", ".git"),
            )
        else:
            shutil.copy2(src, target)


def _make_venv(dest: Path, progress) -> None:
    venv = dest / ".venv"
    py = sys.executable
    _log(progress, "Creating a private Python environment")
    subprocess.run([py, "-m", "venv", str(venv)], check=True)
    if sys.platform == "win32":
        pip = venv / "Scripts" / "python.exe"
    else:
        pip = venv / "bin" / "python"
    req = dest / "requirements.txt"
    _log(progress, "Installing packages (this stays on your computer)")
    subprocess.run(
        [str(pip), "-m", "pip", "install", "--upgrade", "pip"],
        check=True,
        cwd=str(dest),
    )
    subprocess.run(
        [str(pip), "-m", "pip", "install", "-r", str(req)],
        check=True,
        cwd=str(dest),
    )


def _delayed_delete(path: Path) -> None:
    if sys.platform == "win32":
        subprocess.Popen(f'cmd /c timeout /t 2 /nobreak > nul & rmdir /s /q "{path}"', shell=True)
        return
    subprocess.Popen(["/bin/bash", "-lc", f"sleep 2; rm -rf '{path}'"])


def _log(progress, message: str) -> None:
    if progress:
        progress(message)
    else:
        print(message)
