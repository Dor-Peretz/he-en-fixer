"""Login-item helpers for Windows and macOS (user-level only)."""

from __future__ import annotations

import subprocess
import sys
from pathlib import Path

from .paths import APP_ID, APP_NAME, launch_target

LAUNCH_AGENT = Path.home() / "Library" / "LaunchAgents" / f"com.{APP_ID}.plist"

STARTUP_DIR = (
    Path.home()
    / "AppData"
    / "Roaming"
    / "Microsoft"
    / "Windows"
    / "Start Menu"
    / "Programs"
    / "Startup"
)
SHORTCUT_NAME = f"{APP_NAME}.lnk"


def _shortcut_path() -> Path:
    return STARTUP_DIR / SHORTCUT_NAME


def is_enabled() -> bool:
    if sys.platform == "darwin":
        return LAUNCH_AGENT.exists()
    if sys.platform == "win32":
        return _shortcut_path().exists()
    return False


def set_enabled(enabled: bool) -> None:
    if sys.platform == "darwin":
        _set_macos(enabled)
        return
    if sys.platform == "win32":
        _set_windows(enabled)
        return


def _set_windows(enabled: bool) -> None:
    path = _shortcut_path()
    if not enabled:
        if path.exists():
            path.unlink()
        return
    STARTUP_DIR.mkdir(parents=True, exist_ok=True)
    target, args, workdir = launch_target()
    from .icon import icon_ico_path

    _create_windows_shortcut(path, target, args, workdir, icon=icon_ico_path())


def _set_macos(enabled: bool) -> None:
    if not enabled:
        if LAUNCH_AGENT.exists():
            subprocess.run(["launchctl", "unload", str(LAUNCH_AGENT)], check=False)
            LAUNCH_AGENT.unlink()
        return
    target, args, workdir = launch_target()
    program_args = [target]
    if args:
        program_args.extend(args.replace('"', "").split())
    arg_xml = "\n".join(f"      <string>{_xml(a)}</string>" for a in program_args)
    plist = f"""<?xml version="1.0" encoding="UTF-8"?>
<!DOCTYPE plist PUBLIC "-//Apple//DTD PLIST 1.0//EN" "http://www.apple.com/DTDs/PropertyList-1.0.dtd">
<plist version="1.0">
<dict>
  <key>Label</key>
  <string>com.{APP_ID}</string>
  <key>ProgramArguments</key>
  <array>
{arg_xml}
  </array>
  <key>WorkingDirectory</key>
  <string>{_xml(workdir)}</string>
  <key>RunAtLoad</key>
  <true/>
</dict>
</plist>
"""
    LAUNCH_AGENT.parent.mkdir(parents=True, exist_ok=True)
    LAUNCH_AGENT.write_text(plist, encoding="utf-8")
    subprocess.run(["launchctl", "load", str(LAUNCH_AGENT)], check=False)


def _xml(value: str) -> str:
    return (
        value.replace("&", "&amp;")
        .replace("<", "&lt;")
        .replace(">", "&gt;")
        .replace('"', "&quot;")
    )


def _ps_escape(value: str) -> str:
    return value.replace("'", "''")


def _create_windows_shortcut(
    path: Path, target: str, args: str, workdir: str, icon: Path | None = None
) -> None:
    icon_line = ""
    if icon is not None and icon.exists():
        icon_line = f"$sc.IconLocation = '{_ps_escape(str(icon))},0'; "
    script = (
        "$ws = New-Object -ComObject WScript.Shell; "
        f"$sc = $ws.CreateShortcut('{_ps_escape(str(path))}'); "
        f"$sc.TargetPath = '{_ps_escape(target)}'; "
        f"$sc.Arguments = '{_ps_escape(args)}'; "
        f"$sc.WorkingDirectory = '{_ps_escape(workdir)}'; "
        f"{icon_line}"
        "$sc.WindowStyle = 7; "
        "$sc.Save()"
    )
    subprocess.run(
        ["powershell", "-NoProfile", "-Command", script],
        check=False,
        creationflags=getattr(subprocess, "CREATE_NO_WINDOW", 0),
    )


def create_shortcut(path: Path, target: str, args: str, workdir: str, icon: Path | None = None) -> None:
    if sys.platform == "win32":
        path.parent.mkdir(parents=True, exist_ok=True)
        _create_windows_shortcut(path, target, args, workdir, icon=icon)
        return
    path.parent.mkdir(parents=True, exist_ok=True)
    body = "#!/bin/bash\n"
    body += f'cd "{workdir}"\n'
    if args:
        body += f'exec "{target}" {args}\n'
    else:
        body += f'exec "{target}"\n'
    path.write_text(body, encoding="utf-8")
    path.chmod(path.stat().st_mode | 0o111)
