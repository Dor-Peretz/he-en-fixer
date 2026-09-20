"""Settings window for the options that change how fixing behaves."""

from __future__ import annotations

import time
import tkinter as tk
from tkinter import ttk

from PIL import ImageTk

from . import startup
from .calibrate import (
    CALIBRATE_SENTENCE,
    MAX_IDLE_FIX_DELAY,
    MIN_IDLE_FIX_DELAY,
    CalibrationError,
    CalibrationResult,
    delay_from_typing,
)
from .config import load_settings, save_settings
from .icon import icon_ico_path, load_icon
from .paths import APP_NAME


def _delay_text(seconds: float) -> str:
    if seconds <= 0.6:
        feel = "fixes almost immediately"
    elif seconds <= 1.5:
        feel = "fixes shortly after you pause"
    else:
        feel = "waits until you clearly stopped"
    return f"Wait {seconds:.1f} seconds after the last key — {feel}"


def run_settings() -> int:
    settings = load_settings()

    root = tk.Tk()
    root.title(f"{APP_NAME} Settings")
    root.resizable(False, False)

    ico = icon_ico_path()
    if ico is not None:
        try:
            root.iconbitmap(str(ico))
        except tk.TclError:
            pass

    frame = ttk.Frame(root, padding=8)
    frame.pack(fill=tk.BOTH, expand=True)

    header = ttk.Frame(frame)
    header.pack(anchor="w", padx=24, pady=(8, 10), fill=tk.X)
    photo = ImageTk.PhotoImage(load_icon(56))
    root._app_icon = photo
    ttk.Label(header, image=photo).pack(side=tk.LEFT, padx=(0, 14))
    titles = ttk.Frame(header)
    titles.pack(side=tk.LEFT, fill=tk.X)
    ttk.Label(titles, text="Settings", font=("Segoe UI", 16, "bold")).pack(anchor="w")
    ttk.Label(
        titles,
        text="Changes apply right away — no restart needed.",
        font=("Segoe UI", 10),
    ).pack(anchor="w")

    enabled = tk.BooleanVar(value=settings.enabled)
    auto_fix = tk.BooleanVar(value=settings.auto_fix)
    switch_layout = tk.BooleanVar(value=settings.switch_layout)
    he_to_en = tk.BooleanVar(value=settings.he_to_en)
    en_to_he = tk.BooleanVar(value=settings.en_to_he)
    login = tk.BooleanVar(value=settings.start_with_windows)
    delay = tk.DoubleVar(value=settings.idle_fix_delay)

    ttk.Checkbutton(frame, text="Fixer is on", variable=enabled).pack(anchor="w", padx=24)
    ttk.Checkbutton(
        frame,
        text="Fix what I typed when I stop typing",
        variable=auto_fix,
    ).pack(anchor="w", padx=24)

    delay_box = ttk.LabelFrame(frame, text="How long to wait", padding=10)
    delay_box.pack(fill=tk.X, padx=24, pady=(10, 4))
    delay_label = ttk.Label(delay_box, text=_delay_text(delay.get()), wraplength=420)
    delay_label.pack(anchor="w", pady=(0, 6))

    def on_delay(_value: str) -> None:
        delay.set(round(delay.get(), 1))
        delay_label.configure(text=_delay_text(delay.get()))

    ttk.Scale(
        delay_box,
        from_=MIN_IDLE_FIX_DELAY,
        to=MAX_IDLE_FIX_DELAY,
        orient=tk.HORIZONTAL,
        variable=delay,
        command=on_delay,
    ).pack(fill=tk.X)

    def open_calibrate() -> None:
        result = _run_calibrate_dialog(root)
        if result is None:
            return
        delay.set(result.idle_fix_delay)
        delay_label.configure(text=_delay_text(delay.get()))
        status.set(
            f"Wait set to {result.idle_fix_delay:.1f}s from your typing. "
            "Click Save to keep it."
        )

    ttk.Button(
        delay_box,
        text="Calibrate from my typing…",
        command=open_calibrate,
    ).pack(anchor="w", pady=(8, 0))

    ttk.Checkbutton(
        frame,
        text="Switch my keyboard to the right language after a fix",
        variable=switch_layout,
    ).pack(anchor="w", padx=24, pady=(10, 0))

    directions = ttk.LabelFrame(frame, text="Allowed corrections", padding=10)
    directions.pack(fill=tk.X, padx=24, pady=(10, 4))
    ttk.Checkbutton(directions, text="Hebrew → English", variable=he_to_en).pack(anchor="w")
    ttk.Checkbutton(directions, text="English → Hebrew", variable=en_to_he).pack(anchor="w")

    ttk.Checkbutton(frame, text="Start when I log in", variable=login).pack(
        anchor="w", padx=24, pady=(10, 0)
    )

    status = tk.StringVar(value="")
    ttk.Label(frame, textvariable=status, wraplength=420).pack(anchor="w", padx=24, pady=(10, 0))

    buttons = ttk.Frame(frame)
    buttons.pack(fill=tk.X, padx=24, pady=16)

    def do_save() -> None:
        settings.enabled = enabled.get()
        settings.auto_fix = auto_fix.get()
        settings.switch_layout = switch_layout.get()
        settings.he_to_en = he_to_en.get()
        settings.en_to_he = en_to_he.get()
        settings.idle_fix_delay = round(
            max(MIN_IDLE_FIX_DELAY, min(MAX_IDLE_FIX_DELAY, delay.get())), 1
        )
        if login.get() != settings.start_with_windows:
            settings.start_with_windows = login.get()
            try:
                startup.set_enabled(settings.start_with_windows)
            except Exception as exc:
                status.set(f"Saved, but could not change the login item: {exc}")
        save_settings(settings)
        status.set("Saved.")

    def do_save_and_close() -> None:
        do_save()
        root.after(250, root.destroy)

    ttk.Button(buttons, text="Save", command=do_save).pack(side=tk.LEFT, padx=(0, 8))
    ttk.Button(buttons, text="Save and close", command=do_save_and_close).pack(
        side=tk.LEFT, padx=(0, 8)
    )
    ttk.Button(buttons, text="Close", command=root.destroy).pack(side=tk.LEFT)

    root.eval("tk::PlaceWindow . center")
    root.mainloop()
    return 0


def _run_calibrate_dialog(parent: tk.Tk) -> CalibrationResult | None:
    """Ask the user to type a sentence and return a delay, or None if cancelled."""
    dialog = tk.Toplevel(parent)
    dialog.title("Calibrate typing wait")
    dialog.resizable(False, False)
    dialog.transient(parent)
    dialog.grab_set()

    body = ttk.Frame(dialog, padding=16)
    body.pack(fill=tk.BOTH, expand=True)

    ttk.Label(body, text="Type this sentence at your usual speed:", font=("Segoe UI", 10)).pack(
        anchor="w"
    )
    ttk.Label(body, text=CALIBRATE_SENTENCE, font=("Segoe UI", 12, "bold")).pack(
        anchor="w", pady=(4, 10)
    )
    ttk.Label(
        body,
        text="Pauses between letters and words set how long the fixer waits.",
        wraplength=420,
    ).pack(anchor="w")

    typed = tk.StringVar()
    events: list[tuple[str, float]] = []
    hint = tk.StringVar(value="")

    entry = ttk.Entry(body, textvariable=typed, width=48, font=("Segoe UI", 12))
    entry.pack(fill=tk.X, pady=(10, 4))
    entry.focus_set()
    tk.Label(body, textvariable=hint, wraplength=420, fg="#a00", anchor="w", justify="left").pack(
        anchor="w"
    )

    def on_key(event: tk.Event) -> None:
        hint.set("")
        if event.keysym == "BackSpace":
            if events:
                events.pop()
            return
        if event.keysym == "Return":
            finish()
            return "break"
        char = event.char or ""
        if char and char.isprintable():
            events.append((char, time.monotonic()))

    def block_paste(_event: tk.Event) -> str:
        hint.set("Type the words yourself so the pauses can be measured.")
        return "break"

    entry.bind("<KeyPress>", on_key)
    entry.bind("<<Paste>>", block_paste)
    entry.bind("<Control-v>", block_paste)
    entry.bind("<Command-v>", block_paste)

    result_holder: list = []

    def finish() -> None:
        try:
            result_holder.append(delay_from_typing(events))
        except CalibrationError as exc:
            hint.set(str(exc))
            return
        dialog.destroy()

    def cancel() -> None:
        dialog.destroy()

    buttons = ttk.Frame(body)
    buttons.pack(fill=tk.X, pady=(12, 0))
    ttk.Button(buttons, text="Use this typing", command=finish).pack(side=tk.LEFT, padx=(0, 8))
    ttk.Button(buttons, text="Cancel", command=cancel).pack(side=tk.LEFT)

    dialog.protocol("WM_DELETE_WINDOW", cancel)
    parent.eval(f"tk::PlaceWindow {dialog} center")
    dialog.wait_window()
    return result_holder[0] if result_holder else None


if __name__ == "__main__":
    raise SystemExit(run_settings())
