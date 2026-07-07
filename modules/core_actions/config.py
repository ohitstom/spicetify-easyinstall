import asyncio
import os
import shutil
from pathlib import Path
import re

from modules import globals, utils, gui, install_helpers
from modules.state_manager import state

environ_check = f'& "{globals.spice_executable}\\spicetify.exe"'


async def apply_config(theme, colorscheme, extensions, customapps):
    steps_count = 2

    # >[Section 1]<
    # Sets the config as per the users choices.

    print(f"(1/{steps_count}) Setting options...")
    utils.set_config_entry("current_theme", theme)
    utils.set_config_entry("color_scheme", colorscheme)

    # Custom CSS Snippet Injector
    snippet_path = os.path.join(globals.appdata_local, "spicetify-easyinstall", "custom_snippet.css")
    js_snippet_path = os.path.join(globals.spice_config, "Extensions", "CustomCSSSnippet.js")

    if os.path.exists(snippet_path):
        with open(snippet_path, "r", encoding="utf-8") as f:
            css_content = f.read().strip()

        if css_content:
            # Escape backticks and backslashes for JS template literal
            css_escaped = css_content.replace("\\", "\\\\").replace("`", "\\`")
            js_content = f"""(function CustomCSSSnippet() {{
    const style = document.createElement("style");
    style.innerHTML = `{css_escaped}`;
    document.head.appendChild(style);
}})();"""
            os.makedirs(os.path.dirname(js_snippet_path), exist_ok=True)
            with open(js_snippet_path, "w", encoding="utf-8") as f:
                f.write(js_content)

            if "CustomCSSSnippet" not in extensions:
                extensions.append("CustomCSSSnippet")
        elif os.path.exists(js_snippet_path):
            os.remove(js_snippet_path)

    utils.set_config_entry("extensions", "|".join(extension + ".js" for extension in extensions))
    utils.set_config_entry("custom_apps", "|".join(customapps))
    print("Finished setting options!\n")

    # >[Section 2]<
    # Applying the changes to the config.

    print(f"(2/{steps_count}) Applying config...")
    await utils.run_ps1_script("apply_theme.ps1", f"{globals.spice_executable}\\spicetify.exe", start_new_session=False)
    await utils.start_process(f"{globals.appdata}\\spotify\\spotify.exe", silent=False)
    print("Finished applying config!\n")
