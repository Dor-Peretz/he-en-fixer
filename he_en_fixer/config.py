"""Persistent settings in %APPDATA%/he-en-fixer."""

from __future__ import annotations

import json
from dataclasses import asdict, dataclass, fields

from .layouts import DEFAULT_LANGUAGE, LAYOUTS
from .paths import config_dir

APP_DIR = config_dir()
SETTINGS_PATH = APP_DIR / "settings.json"


@dataclass
class Settings:
    enabled: bool = True
    auto_fix: bool = True
    language: str = DEFAULT_LANGUAGE
    other_to_en: bool = True
    en_to_other: bool = True
    min_word_length: int = 2
    idle_fix_delay: float = 1.2
    switch_layout: bool = True
    start_with_windows: bool = False
    convert_hotkey: str = "<ctrl>+<space>"
    # Legacy fields — still saved for older builds reading settings.json.
    he_to_en: bool = True
    en_to_he: bool = True


def _normalize_language(value: str | None) -> str:
    if value and value.lower() in LAYOUTS:
        return value.lower()
    return DEFAULT_LANGUAGE


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
        settings = Settings(**filtered)
        settings.language = _normalize_language(data.get("language"))
        if "other_to_en" not in data and "he_to_en" in data:
            settings.other_to_en = bool(data["he_to_en"])
        if "en_to_other" not in data and "en_to_he" in data:
            settings.en_to_other = bool(data["en_to_he"])
        settings.he_to_en = settings.other_to_en
        settings.en_to_he = settings.en_to_other
        return settings
    except (OSError, json.JSONDecodeError, TypeError):
        return Settings()


def save_settings(settings: Settings) -> None:
    settings.language = _normalize_language(settings.language)
    settings.he_to_en = settings.other_to_en
    settings.en_to_he = settings.en_to_other
    APP_DIR.mkdir(parents=True, exist_ok=True)
    SETTINGS_PATH.write_text(
        json.dumps(asdict(settings), indent=2) + "\n",
        encoding="utf-8",
    )
