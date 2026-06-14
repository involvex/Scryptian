# settings.py - Persistent settings manager for Scryptian

import json
import os

DEFAULTS = {
    "disabled_skills": [],
    "editor_font_family": "Consolas",
    "editor_font_size": 12,
    "word_wrap": False,
    "theme": "mocha",
    "autostart": True,
    "telemetry": True,
}


class Settings:
    def __init__(self, path):
        self._path = path
        self._data = dict(DEFAULTS)
        self._load()

    def _load(self):
        try:
            if os.path.exists(self._path):
                with open(self._path, "r", encoding="utf-8") as f:
                    stored = json.load(f)
                self._data.update(stored)
        except Exception:
            pass

    def save(self):
        try:
            os.makedirs(os.path.dirname(self._path), exist_ok=True)
            with open(self._path, "w", encoding="utf-8") as f:
                json.dump(self._data, f, indent=2)
        except Exception:
            pass

    def get(self, key, default=None):
        return self._data.get(key, default)

    def set(self, key, value):
        self._data[key] = value
        self.save()

    def set_many(self, mapping):
        self._data.update(mapping)
        self.save()

    def is_skill_enabled(self, filename):
        return filename not in self._data.get("disabled_skills", [])

    def toggle_skill(self, filename):
        disabled = self._data.setdefault("disabled_skills", [])
        if filename in disabled:
            disabled.remove(filename)
        else:
            disabled.append(filename)
        self.save()
