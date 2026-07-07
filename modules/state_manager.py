import os
import json
from PyQt5 import QtCore

class StateManager:
    _instance = None

    def __new__(cls, *args, **kwargs):
        if not cls._instance:
            cls._instance = super(StateManager, cls).__new__(cls, *args, **kwargs)
            cls._instance._initialized = False
        return cls._instance

    def __init__(self):
        if self._initialized: return

        self.appdata = os.environ["APPDATA"]
        self.installer_config = os.path.join(self.appdata, "spicetify-easyinstall")

        self.config_path = os.path.join(self.installer_config, "custom_addons.json")
        self.pix_cache_path = os.path.join(self.installer_config, "pix_cache.txt")
        self.desc_cache_path = os.path.join(self.installer_config, "desc_cache.txt")

        self._config = {}
        self._pix_cache = None
        self._desc_cache = None

        # Temp vars mapped from globals
        self.app = None
        self.gui = None
        self.singleton = None
        self.verbose = False
        self.json = None
        self.runtime_spotify_version = None
        self.runtime_spicetify_version = None
        self.runtime_themes_version = None
        self.runtime_addons_version = None
        self.runtime_spotify_url = None
        self.runtime_themes_url = None
        self.runtime_addons_url = None

        self._initialized = True

    def load_config(self):
        from modules import globals as gl
        defaults = gl.DEFAULT_CONFIG
        if not os.path.exists(self.config_path):
            self._config = defaults.copy()
            self.save_config()
            return

        try:
            with open(self.config_path, "r", encoding="utf-8") as f:
                saved = json.load(f)
            self._config = {
                "extensions": saved.get("extensions", defaults.get("extensions", {})),
                "apps": saved.get("apps", defaults.get("apps", {})),
                "themes": saved.get("themes", defaults.get("themes", {})),
                "theme_commit_cache": saved.get("theme_commit_cache", defaults.get("theme_commit_cache", {})),
                "selected_spicetify_version": saved.get("selected_spicetify_version", defaults.get("selected_spicetify_version")),
                "selected_spotify_version": saved.get("selected_spotify_version", defaults.get("selected_spotify_version")),

                "selected_themes_version": saved.get("selected_themes_version", defaults.get("selected_themes_version")),
                "pin_date": saved.get("pin_date", defaults.get("pin_date")),
                "github_token": saved.get("github_token", defaults.get("github_token")),
                "license_accepted": saved.get("license_accepted", defaults.get("license_accepted", False))
            }
        except Exception:
            self._config = defaults.copy()

    def save_config(self):
        try:
            os.makedirs(os.path.dirname(self.config_path), exist_ok=True)
            with open(self.config_path, "w", encoding="utf-8") as f:
                json.dump(self._config, f, indent=4)
        except Exception:
            pass

    @property
    def selected_spicetify_version(self):
        if not self._config: self.load_config()
        return self._config.get("selected_spicetify_version")

    @selected_spicetify_version.setter
    def selected_spicetify_version(self, val):
        if not self._config: self.load_config()
        self._config["selected_spicetify_version"] = val
        self.save_config()

    @property
    def selected_spotify_version(self):
        if not self._config: self.load_config()
        return self._config.get("selected_spotify_version")

    @selected_spotify_version.setter
    def selected_spotify_version(self, val):
        if not self._config: self.load_config()
        self._config["selected_spotify_version"] = val
        self.save_config()

    @property
    def selected_themes_version(self):
        if not self._config: self.load_config()
        return self._config.get("selected_themes_version")

    @selected_themes_version.setter
    def selected_themes_version(self, val):
        if not self._config: self.load_config()
        self._config["selected_themes_version"] = val
        self.save_config()

    @property
    def pin_date(self):
        if not self._config: self.load_config()
        return self._config.get("pin_date")

    @pin_date.setter
    def pin_date(self, val):
        if not self._config: self.load_config()
        self._config["pin_date"] = val
        self.save_config()

    @property
    def github_token(self):
        if not self._config: self.load_config()
        return self._config.get("github_token", "")

    @github_token.setter
    def github_token(self, val):
        if not self._config: self.load_config()
        self._config["github_token"] = val
        self.save_config()

    @property
    def license_accepted(self):
        if not self._config: self.load_config()
        return self._config.get("license_accepted", False)

    @license_accepted.setter
    def license_accepted(self, val):
        if not self._config: self.load_config()
        self._config["license_accepted"] = val
        self.save_config()

    @property
    def extensions(self):
        if not self._config: self.load_config()
        return self._config.get("extensions", {})

    @extensions.setter
    def extensions(self, val):
        if not self._config: self.load_config()
        self._config["extensions"] = val
        self.save_config()

    @property
    def apps(self):
        if not self._config: self.load_config()
        return self._config.get("apps", {})

    @apps.setter
    def apps(self, val):
        if not self._config: self.load_config()
        self._config["apps"] = val
        self.save_config()

    @property
    def themes(self):
        if not self._config: self.load_config()
        return self._config.get("themes", {})

    @themes.setter
    def themes(self, val):
        if not self._config: self.load_config()
        self._config["themes"] = val
        self.save_config()

    @property
    def theme_commit_cache(self):
        if not self._config: self.load_config()
        return self._config.get("theme_commit_cache", {})

    @theme_commit_cache.setter
    def theme_commit_cache(self, val):
        if not self._config: self.load_config()
        self._config["theme_commit_cache"] = val
        self.save_config()

    def get_pix_cache(self):
        if self._pix_cache is not None: return self._pix_cache
        self._pix_cache = {}
        if os.path.exists(self.pix_cache_path):
            try:
                with open(self.pix_cache_path, "r", encoding="utf-8") as f:
                    sections = f.readlines()
                    for count, line in enumerate(sections[:-1]):
                        key, value = line.split(": ", 1)
                        pix, bright = value.rsplit(", ", 1)
                        self._pix_cache[key] = [
                            QtCore.QByteArray.fromBase64(pix[2:-1].encode()),
                            float(bright),
                        ]
            except Exception: pass
        else:
            try: open(self.pix_cache_path, "w").close()
            except Exception: pass
        return self._pix_cache

    def get_desc_cache(self):
        if self._desc_cache is not None: return self._desc_cache
        self._desc_cache = {}
        if os.path.exists(self.desc_cache_path):
            try:
                with open(self.desc_cache_path, "r", encoding="utf-8") as f:
                    sections = f.readlines()
                    for count, line in enumerate(sections[:-1]):
                        key, value = line.split(": ", 1)
                        self._desc_cache[key] = value.strip()
            except Exception: pass
        else:
            try: open(self.desc_cache_path, "w").close()
            except Exception: pass
        return self._desc_cache

state = StateManager()
