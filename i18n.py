import json
from pathlib import Path
from config import settings

def _load(lang: str) -> dict:
    path = Path(settings.LOCALE_DIR) / f"{lang}.json"
    with open(path, "r", encoding="utf-8") as f:
        return json.load(f)

MESSAGES = { "ru": _load("ru"), "en": _load("en") }

def t(lang: str, key: str, **kwargs) -> str:
    lang = lang if lang in MESSAGES else settings.DEFAULT_LANG
    s = MESSAGES[lang].get(key, key)
    try:
        return s.format(**kwargs)
    except Exception:
        return s
