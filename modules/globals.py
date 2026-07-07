import os
import sys
import json
from pathlib import Path

verbose = False

def _get_resource_path(relative_path):
    if getattr(sys, "frozen", False) and hasattr(sys, "_MEIPASS"):
        path_in_meipass = relative_path[len("resources/"):] if relative_path.startswith("resources/") else relative_path
        return os.path.join(sys._MEIPASS, path_in_meipass.replace("/", os.sep))
    else:
        base_path = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
        return os.path.join(base_path, relative_path.replace("/", os.sep))

def _load_json(filename):
    appdata = os.environ.get("APPDATA", "")
    installer_config = f"{appdata}\\spicetify-easyinstall"
    cached_path = os.path.join(installer_config, "data", filename)
    if os.path.exists(cached_path):
        try:
            with open(cached_path, "r", encoding="utf-8") as f:
                return json.load(f)
        except Exception:
            pass

    path = _get_resource_path(f"resources/data/{filename}")
    with open(path, "r", encoding="utf-8") as f:
        return json.load(f)

def _load_md(filename):
    path = _get_resource_path(f"resources/markdown/{filename}")
    with open(path, "r", encoding="utf-8") as f:
        return f.read()

## All '__xyz__' variables are temporary variables used for re-assigning.

# Github Variables
RELEASE = "4.0-beta"
HOMEPAGE = "https://github.com/ohitstom/spicetify-easyinstall"
WATERMARK = "Spicetify EasyInstall by OhItsTom and WillyJL"

# Directory Constants
user_profile = os.path.expanduser("~")
appdata_local = os.environ.get("LOCALAPPDATA", "")
appdata = os.environ.get("APPDATA", "")
spotify_prefs = Path(f"{appdata}\\Spotify\\prefs")
spice_executable = f"{appdata_local}\\spicetify"
spice_config = f"{appdata}\\spicetify"
installer_config = f"{appdata}\\spicetify-easyinstall"
pix_cache_path = f"{installer_config}\\pix_cache.txt"
desc_cache_path = f"{installer_config}\\desc_cache.txt"
temp = f"{installer_config}\\temp"
custom_addons_json_path = f"{installer_config}\\custom_addons.json"

# Load bulky data from resources
RECOMMENDED = _load_json("recommended.json")
SPOTIFY_PRESETS = _load_json("spotify_presets.json")
SPICETIFY_DATES = _load_json("spicetify_dates.json")
SHIPPED_SHAS = _load_json("shipped_shas.json")
DEFAULT_EXTENSIONS = _load_json("default_extensions.json")
DEFAULT_APPS = _load_json("default_apps.json")
DEFAULT_THEMES = _load_json("default_themes.json")

# Version Variables dynamically loaded
if RELEASE in RECOMMENDED:
    SPICETIFY_VERSION = RECOMMENDED[RELEASE].get("spicetify", "2.38.5")
    SPOTIFY_VERSION = RECOMMENDED[RELEASE].get("spotify", "1.2.51 (2024-12-01)")
else:
    SPICETIFY_VERSION = "2.38.5"
    SPOTIFY_VERSION = "1.2.51 (2024-12-01)"

# Download URLS dynamically resolved from SHIPPED_SHAS based on the recommended SPICETIFY_VERSION
_themes_sha = SHIPPED_SHAS.get(SPICETIFY_VERSION, {}).get("themes", "c6e82dfeaa46ee9060d0c02fc437989eb77f6c61")
_addons_sha = SHIPPED_SHAS.get(SPICETIFY_VERSION, {}).get("cli", "b26a60e41dd4296ba337b58f68ec2b1de2b422cf")



DEFAULT_CONFIG = {
    "extensions": DEFAULT_EXTENSIONS.copy() if isinstance(DEFAULT_EXTENSIONS, dict) else DEFAULT_EXTENSIONS,
    "apps": DEFAULT_APPS.copy() if isinstance(DEFAULT_APPS, dict) else DEFAULT_APPS,
    "themes": DEFAULT_THEMES.copy() if isinstance(DEFAULT_THEMES, dict) else DEFAULT_THEMES,
    "theme_commit_cache": {},
    "selected_spicetify_version": SPICETIFY_VERSION,
    "selected_spotify_version": SPOTIFY_VERSION,
    "architecture": "64-bit"
}

INSTALL_RUNDOWN_MD = _load_md("install_rundown.md")
UNINSTALL_RUNDOWN_MD = _load_md("uninstall_rundown.md")
UPDATE_APP_RUNDOWN_MD = _load_md("update_app_rundown.md")
UPDATE_LATEST_RUNDOWN_MD = _load_md("update_latest_rundown.md")
LICENSE_AGREEMENT = _load_md("license_agreement.md")
