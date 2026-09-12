# -*- mode: python ; coding: utf-8 -*-
import sys
from PyInstaller.utils.hooks import collect_data_files, collect_submodules

datas = collect_data_files("wordfreq") + collect_data_files("langcodes")
hidden = (
    collect_submodules("wordfreq")
    + collect_submodules("pynput")
    + collect_submodules("pystray")
    + [
        "tkinter",
        "tkinter.ttk",
        "he_en_fixer",
        "he_en_fixer.installer_gui",
        "he_en_fixer.install",
        "he_en_fixer.injector_win",
        "he_en_fixer.injector_generic",
        "PIL._tkinter_finder",
    ]
)

if sys.platform == "win32":
    hidden += ["pynput.keyboard._win32", "pynput.mouse._win32", "pystray._win32"]
elif sys.platform == "darwin":
    hidden += ["pynput.keyboard._darwin", "pynput.mouse._darwin", "pystray._darwin"]

a = Analysis(
    ["main.py"],
    pathex=[],
    binaries=[],
    datas=datas,
    hiddenimports=hidden,
    hookspath=[],
    hooksconfig={},
    runtime_hooks=[],
    excludes=[],
    noarchive=False,
)
pyz = PYZ(a.pure)

exe = EXE(
    pyz,
    a.scripts,
    [],
    exclude_binaries=True,
    name="HE-EN Fixer",
    debug=False,
    bootloader_ignore_signals=False,
    strip=False,
    upx=False,
    console=False,
    disable_windowed_traceback=False,
    argv_emulation=sys.platform == "darwin",
    icon="packaging/icon.ico" if sys.platform == "win32" else None,
)
coll = COLLECT(
    exe,
    a.binaries,
    a.datas,
    strip=False,
    upx=False,
    name="HE-EN Fixer",
)
if sys.platform == "darwin":
    app = BUNDLE(
        coll,
        name="HE-EN Fixer.app",
        icon=None,
        bundle_identifier="com.heenfixer.app",
        info_plist={
            "LSUIElement": True,
            "NSHighResolutionCapable": True,
            "CFBundleName": "HE-EN Fixer",
        },
    )
