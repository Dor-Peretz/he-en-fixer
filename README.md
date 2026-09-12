# HE↔EN Fixer

A small local app for Windows and Mac. It watches what you type and fixes the classic mistake: you meant **English**, but the keyboard was still on **Hebrew** (or the other way around).

Example: Hebrew layout is on, you type `hello`, the screen shows `יקךךם`. When you press Space, Enter, or Tab, the app rewrites it to `hello`.

Real words are left alone. `שלום` and `אם` stay Hebrew. `hello` and `to` stay English.

The app runs only on your computer. It does not send your typing to the internet.

---

## Install (one click)

No administrator password. Installs only for the current user. The same window can uninstall it.

### Windows

1. Open `HE-EN-Fixer-Windows.zip`
2. Double-click **Install.bat**
3. Click **Install**
4. Click **Open app**

Windows may show a SmartScreen prompt because this is not from the Microsoft Store. If you trust this copy: **More info → Run anyway**.

### Mac

1. Open `HE-EN-Fixer-macOS.zip`
2. Double-click **Install.command**
3. Click **Install**
4. Allow **Accessibility** in **System Settings → Privacy & Security → Accessibility**
5. Click **Open app**

If macOS says the app is from an unidentified developer: right-click → **Open**.

### From this project folder

If you already have this folder on the computer:

- Windows: double-click `Install.bat`
- Mac: double-click `Install.command`

That copies the app into your user folder and can add a desktop shortcut.

---

## How to use it

After install, a tray icon appears (`A א`). Leave it running while you type.

**Auto-fix** runs when you finish a word (Space, Enter, or Tab).

**Force convert** if auto-fix misses a name or a rare word:

| | Windows | Mac |
|---|---|---|
| Convert current word | **Ctrl+Space**, **Pause**, or **F9** | **Ctrl+Shift+Space** or **F9** |
| Convert selected text | Same shortcut, with text selected | Same |

On a Mac, Ctrl+Space is not used, so it does not steal the language-switch shortcut.

Right-click the tray icon to:

- Turn the fixer on or off
- Turn auto-fix on or off
- Allow only Hebrew → English, only English → Hebrew, or both
- Start when you log in
- Open the install / uninstall window
- Quit

Turn it off from the tray before passwords, games, or mixed-language typing you want left as-is.

---

## Uninstall

Double-click **Install.bat** (Windows) or **Install.command** (Mac), then click **Uninstall**.

Or: tray icon → **Install / Uninstall…** → **Uninstall**.

---

## Safety

- Installs only under your user folder
  - Windows: `%LOCALAPPDATA%\HE-EN Fixer`
  - Mac: `~/Library/Application Support/he-en-fixer`
- Does not need administrator rights
- Does not send keystrokes over the network
- Source is MIT licensed — you can read what it does

---

## Share it with other people

Send the zip, not the whole source tree.

**Windows zip** (build on a Windows PC):

```bat
packaging\build_windows.ps1
```

The file to send is `release\HE-EN-Fixer-Windows.zip`.

**Mac zip** must be built on a Mac, or with the **Build installers** GitHub Action in this repo. Then send `release\HE-EN-Fixer-macOS.zip`.

---

## Run from source (developers)

Python 3.10+ is required.

```bat
run.bat
```

Or with a console window:

```bat
run-debug.bat
```

Preview a conversion without installing the keyboard hook:

```bat
.venv\Scripts\python.exe -m he_en_fixer יקךךם
.venv\Scripts\python.exe -m he_en_fixer --force hello
```

Tests:

```bat
.venv\Scripts\python.exe -m unittest discover -s tests -v
```

---

## License

MIT. See [LICENSE](LICENSE).
