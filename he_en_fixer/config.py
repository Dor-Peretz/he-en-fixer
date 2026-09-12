"""Persistent settings in %APPDATA%/he-en-fixer."""

from __future__ import annotations

import json
from dataclasses import asdict, dataclass, fields

from .paths import config_dir

APP_DIR = config_dir()
SETTINGS_PATH = APP_DIR / "settings.json"


@dataclass
class Settings:
    enabled: bool = True
    auto_fix: bool = True
    he_to_en: bool = True
    en_to_he: bool = True
    min_word_length: int = 2
    start_with_windows: bool = False
    convert_hotkey: str = "<ctrl>+<space>"


def load_settings() -> Settings:
    APP_DIR.mkdir(parents=True, exist_ok=True)
    if not SETTINGS_PATH.exists():
        settings = Settings()
        save_settings(settings)
        return settings
    try:
        data = json.loads(SETTINGS_PATH.read_text(encoding="utf-8"))
        known = {field.name for field in fields(Settings)}
        filtered = {k: v for k, v in data.items() if k in known}
        return Settings(**filtered)
    except (OSError, json.JSONDecodeError, TypeError):
        return Settings()


def save_settings(settings: Settings) -> None:
    APP_DIR.mkdir(parents=True, exist_ok=True)
    SETTINGS_PATH.write_text(
        json.dumps(asdict(settings), indent=2) + "\n",
        encoding="utf-8",
    )
