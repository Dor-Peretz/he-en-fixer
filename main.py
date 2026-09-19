"""HE↔EN Fixer — local wrong-keyboard-layout corrector."""

from __future__ import annotations

import sys


def main() -> int:
    if "--setup" in sys.argv or "--install" in sys.argv:
        from he_en_fixer.installer_gui import run_installer

        return run_installer()
    if "--settings" in sys.argv:
        from he_en_fixer.settings_gui import run_settings

        return run_settings()
    if "--uninstall" in sys.argv:
        from he_en_fixer.install import uninstall

        uninstall()
        return 0
    if sys.platform not in {"win32", "darwin"}:
        print("he-en-fixer supports Windows and macOS.")
        return 1
    from he_en_fixer.config import load_settings
    from he_en_fixer.tray import TrayApp

    settings = load_settings()
    TrayApp(settings).run()
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
