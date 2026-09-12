"""One-click user-level installer. No administrator rights."""

from __future__ import annotations

import sys
import threading
import tkinter as tk
from tkinter import ttk

from .install import InstallOptions, install, is_installed, launch_app, uninstall
from .paths import APP_NAME, install_dir


SAFE_POINTS = [
    "Installs only for your user account — no administrator password.",
    "Runs only on this computer. It does not send what you type to the internet.",
    "You can uninstall from this same window at any time.",
]


def run_installer() -> int:
    root = tk.Tk()
    root.title(f"Install {APP_NAME}")
    root.resizable(False, False)
    root.configure(bg="#f4f6fb")

    pad = {"padx": 24, "pady": 6}
    frame = ttk.Frame(root, padding=8)
    frame.pack(fill=tk.BOTH, expand=True)

    ttk.Label(frame, text=APP_NAME, font=("Segoe UI", 18, "bold")).pack(anchor="w", **pad)
    ttk.Label(
        frame,
        text="Hebrew ↔ English keyboard fixer",
        font=("Segoe UI", 10),
    ).pack(anchor="w", padx=24)

    for line in SAFE_POINTS:
        ttk.Label(frame, text=f"•  {line}", wraplength=460, justify="left").pack(
            anchor="w", padx=24, pady=2
        )

    loc = ttk.Label(frame, text=f"Location: {install_dir()}", wraplength=460)
    loc.pack(anchor="w", padx=24, pady=(12, 8))

    desktop = tk.BooleanVar(value=True)
    menu = tk.BooleanVar(value=True)
    login = tk.BooleanVar(value=False)
    ttk.Checkbutton(frame, text="Desktop shortcut", variable=desktop).pack(anchor="w", padx=24)
    ttk.Checkbutton(
        frame,
        text="Start Menu / Applications shortcut",
        variable=menu,
    ).pack(anchor="w", padx=24)
    ttk.Checkbutton(frame, text="Start when I log in", variable=login).pack(anchor="w", padx=24)

    status = tk.StringVar(value="Ready. Nothing has been changed yet.")
    ttk.Label(frame, textvariable=status, wraplength=460).pack(anchor="w", padx=24, pady=(12, 4))

    buttons = ttk.Frame(frame)
    buttons.pack(fill=tk.X, padx=24, pady=16)
    install_btn = ttk.Button(buttons, text="Install")
    uninstall_btn = ttk.Button(buttons, text="Uninstall")
    launch_btn = ttk.Button(buttons, text="Open app", state=tk.DISABLED)
    install_btn.pack(side=tk.LEFT, padx=(0, 8))
    uninstall_btn.pack(side=tk.LEFT, padx=(0, 8))
    launch_btn.pack(side=tk.LEFT)

    if is_installed():
        status.set("Already installed. You can reinstall, uninstall, or open the app.")
        launch_btn.configure(state=tk.NORMAL)

    def set_busy(busy: bool) -> None:
        state = tk.DISABLED if busy else tk.NORMAL
        install_btn.configure(state=state)
        uninstall_btn.configure(state=state)

    def on_progress(message: str) -> None:
        root.after(0, lambda: status.set(message))

    def do_install() -> None:
        set_busy(True)
        status.set("Installing…")

        def worker() -> None:
            try:
                install(
                    InstallOptions(
                        desktop_shortcut=desktop.get(),
                        start_menu=menu.get(),
                        start_at_login=login.get(),
                    ),
                    progress=on_progress,
                )
            except Exception as exc:
                root.after(0, lambda: _fail(str(exc)))
                return
            root.after(0, _installed)

        threading.Thread(target=worker, daemon=True).start()

    def _fail(message: str) -> None:
        set_busy(False)
        status.set(f"Could not install: {message}")

    def _installed() -> None:
        set_busy(False)
        launch_btn.configure(state=tk.NORMAL)
        extra = ""
        if sys.platform == "darwin":
            extra = (
                " On a Mac, allow Accessibility for this app in "
                "System Settings → Privacy & Security → Accessibility."
            )
        status.set(f"Installed. You can open the app now.{extra}")

    def do_uninstall() -> None:
        set_busy(True)
        status.set("Uninstalling…")

        def worker() -> None:
            try:
                uninstall(progress=on_progress)
            except Exception as exc:
                root.after(0, lambda: _fail(str(exc)))
                return
            root.after(
                0,
                lambda: (
                    set_busy(False),
                    launch_btn.configure(state=tk.DISABLED),
                    status.set("Removed from this computer."),
                ),
            )

        threading.Thread(target=worker, daemon=True).start()

    def do_launch() -> None:
        launch_app()
        root.after(400, root.destroy)

    install_btn.configure(command=do_install)
    uninstall_btn.configure(command=do_uninstall)
    launch_btn.configure(command=do_launch)

    root.eval("tk::PlaceWindow . center")
    root.mainloop()
    return 0


if __name__ == "__main__":
    raise SystemExit(run_installer())
