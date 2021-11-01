import os
import shutil
import asyncio
import tempfile
import subprocess
from pathlib import Path

from modules import globals, utils


async def install(launch=False):
    steps_count = 8
    user_profile = os.path.expanduser("~")  # Vars
    appdata_local = os.environ["LOCALAPPDATA"]
    appdata = os.environ["APPDATA"]
    temp = tempfile.gettempdir()
    spotify_prefs = Path(user_profile + "\\AppData\\Roaming\\Spotify\\prefs")
    folders = [
        (user_profile + "\\spicetify-cli"),
        (user_profile + "\\.spicetify"),
        (appdata_local + "\\spotify"),
        (appdata + "\\spotify"),
        (temp),
    ]

    print(f"(1/{steps_count}) Uninstalling Spotify...")  # Section 1
    if os.path.isdir(appdata + "\\Spotify"):
        utils.kill_processes("Spotify.exe")
        powershell_uninstall_proc = subprocess.Popen(
            [
                "powershell",
                'cmd /c "%USERPROFILE%\\AppData\\Roaming\\Spotify\\Spotify.exe" /UNINSTALL /SILENT\n$all = cmd /c icacls %localappdata%\\Spotify\\Update /grant %username%:D\n$all = cmd /c icacls %localappdata%\\Spotify\\Update /grant %username%:R',
            ],
            creationflags=subprocess.CREATE_NO_WINDOW,
        )
        while utils.process_pid_running(powershell_uninstall_proc.pid):
            await asyncio.sleep(0.25)
        print("Finished uninstalling Spotify!\n")
    else:
        print("Spotify is not installed!\n")

    print(f"(2/{steps_count}) Wiping folders...")  # Section 2
    for folder in folders:
        try:
            if not os.path.exists(folder) or len(os.listdir(folder)) == 0:
                print(f'"{folder}" is already empty.')
            else:
                shutil.rmtree(folder, ignore_errors=True)
                print(f'"{folder}" has been deleted.')
        except Exception as e:
            print(f'"{folder}" was not deleted: {e}.')
    print("Finished wiping folders!\n")

    print(f"(3/{steps_count}) Downloading correct Spotify version...")  # Section 3
    if not os.path.isdir(temp):
        os.mkdir(temp)
    await utils.chunked_download(
        url=globals.FULL_SETUP_URL,
        path=(temp + globals.INSTALLER_NAME),
        label=globals.INSTALLER_NAME[1:],
    )
    print("Finished downloading Spotify!\n")

    print(f"(4/{steps_count}) Installing Spotify...")  # Section 4
    utils.kill_processes("Spotify.exe")
    spotify_install_pid = utils.start_process(temp + globals.INSTALLER_NAME).pid
    while utils.process_pid_running(spotify_install_pid):
        await asyncio.sleep(0.25)
    i = 0
    while not spotify_prefs.is_file():
        i += 1
        if i > 40:
            raise FileNotFoundError(
                "Spotify preferences were not created, something went wrong installing."
            )
        await asyncio.sleep(0.25)
    utils.kill_processes("Spotify.exe")
    os.remove(temp + globals.INSTALLER_NAME)
    print("Finished installing Spotify!\n")

    print(f"(5/{steps_count}) Installing Spicetify...")  # Section 5
    powershell_install_proc = subprocess.Popen(
        [
            "powershell",
            "$ProgressPreference = 'SilentlyContinue'\n$v='%s'; Invoke-WebRequest -UseBasicParsing 'https://raw.githubusercontent.com/OhItsTom/spicetify-easyinstall/Spicetify-v2/install.ps1' | Invoke-Expression\n$all = spicetify\n $all = spicetify backup apply enable-devtool"
            % globals.SPICETIFY_VERSION,
        ],
        creationflags=subprocess.CREATE_NO_WINDOW,
    )
    while utils.process_pid_running(powershell_install_proc.pid):
        await asyncio.sleep(0.25)
    print("Finished installing Spicetify!\n")

    print(f"(6/{steps_count}) Preventing Spotify from updating...")  # Section 6
    utils.kill_processes("Spotify.exe")
    if not os.path.isdir(appdata_local + "\\Spotify\\Update"):
        os.mkdir(appdata_local + "\\Spotify\\Update")
    powershell_prevention_proc = subprocess.Popen(
        [
            "powershell",
            "$all = cmd /c icacls %localappdata%\\Spotify\\Update /deny %username%:D\n$all = cmd /c icacls %localappdata%\\Spotify\\Update /deny %username%:R",
        ],
        creationflags=subprocess.CREATE_NO_WINDOW,
    )
    while utils.process_pid_running(powershell_prevention_proc.pid):
        await asyncio.sleep(0.25)
    print("Finished blocking Spotify updates!\n")

    print(f"(7/{steps_count}) Downloading themes...")  # Section 7
    shutil.rmtree(user_profile + "\\spicetify-cli\\Themes", ignore_errors=True)
    await utils.chunked_download(
        url=globals.DOWNLOAD_THEME_URL,
        path=(user_profile + "\\spicetify-cli\\Themes.zip"),
        label="Themes.zip",
    )
    print("Finished downloading themes!\n")

    print(f"(8/{steps_count}) Unpacking themes...")  # Section 8
    shutil.unpack_archive(
        user_profile + "\\spicetify-cli\\Themes.zip", user_profile + "\\spicetify-cli"
    )
    os.remove(user_profile + "\\spicetify-cli\\Themes.zip")
    os.rename(
        user_profile + "\\spicetify-cli" + globals.THEMES_EXTRACTED,
        user_profile + "\\spicetify-cli\\Themes",
    )
    for item in list(Path(user_profile + "\\spicetify-cli\\Themes").glob("*")):
        fullpath = str(item)
        filename = str(item.name)
        if os.path.isdir(fullpath):
            if filename[0] == ".":
                shutil.rmtree(fullpath)
        else:
            os.remove(fullpath)
    os.rename(
        user_profile + "\\spicetify-cli\\Themes\\Default",
        user_profile + "\\spicetify-cli\\Themes\\SpicetifyDefault",
    )
    print("Finished unpacking themes!\n")

    if launch:
        subprocess.Popen([appdata + "\\spotify\\spotify.exe"])


async def apply_config(theme, colorscheme, extensions, customapps):
    steps_count = 2

    print(f"(1/{steps_count}) Setting opptions...")  # Section 1
    utils.set_config_entry("current_theme", theme)
    utils.set_config_entry("color_scheme", colorscheme)
    utils.set_config_entry("extensions", "|".join(extensions))
    utils.set_config_entry("custom_apps", "|".join(customapps))
    print("Finished setting options!\n")

    print(f"(2/{steps_count}) Applying config...")  # Section 2
    apply_proc = subprocess.Popen(
        [
            "powershell",
            "spicetify apply",
        ],
        creationflags=subprocess.CREATE_NO_WINDOW,
    )
    while utils.process_pid_running(apply_proc.pid):
        await asyncio.sleep(0.25)
    print("Finished applying config!\n")


async def uninstall():
    steps_count = 1
    user_profile = os.path.expanduser("~")  # Vars
    temp = "C:\\Users\\WDAGUtilityAccount\\AppData\\Local\\temp"
    folders = [
        (user_profile + "\\spicetify-cli"),
        (user_profile + "\\.spicetify"),
        (temp),
    ]

    print(f"(1/{steps_count}) Wiping folders...")  # Section 1
    for folder in folders:
        try:
            if not os.path.exists(folder) or len(os.listdir(folder)) == 0:
                print(f'"{folder}" is already empty.')
            else:
                shutil.rmtree(folder, ignore_errors=True)
                print(f'"{folder}" has been deleted.')
        except Exception as e:
            print(f'"{folder}" was not deleted: {e}.')
    print("Finished wiping folders!\n")
    # subprocess.Popen( #Delete ENV VAR
    # ["powershell", '$all = cmd /c setx Path '])

    # End of the terminal page
    # Needs rewriting


async def update_addons(addon_type):
    steps_count = 3
    if addon_type == "shipped":
        download_url = globals.DOWNLOAD_THEME_URL
    elif addon_type == "latest":
        download_url = globals.DOWNLOAD_THEME_URL
    user_profile = os.environ["USERPROFILE"]

    print(f"(1/{steps_count}) Wiping old themes...")  # Section 1
    shutil.rmtree(user_profile + "\\spicetify-cli\\Themes", ignore_errors=True)
    print("Finished wiping old themes!\n")

    print(f"(2/{steps_count}) Downloading {addon_type} themes...")  # Section 2
    await utils.chunked_download(
        url=download_url,
        path=(user_profile + "\\spicetify-cli\\Themes.zip"),
        label="Themes.zip",
    )
    print(f"Finished downloading {addon_type} themes!\n")

    print(f"(3/{steps_count}) Unpacking new themes...")  # Section 3
    shutil.unpack_archive(
        user_profile + "\\spicetify-cli\\Themes.zip", user_profile + "\\spicetify-cli"
    )
    os.remove(user_profile + "\\spicetify-cli\\Themes.zip")
    os.rename(
        user_profile + "\\spicetify-cli" + globals.THEMES_EXTRACTED,
        user_profile + "\\spicetify-cli\\Themes",
    )
    for item in list(Path(user_profile + "\\spicetify-cli\\Themes").glob("*")):
        fullpath = str(item)
        filename = str(item.name)
        if os.path.isdir(fullpath):
            if filename[0] == ".":
                shutil.rmtree(fullpath)
        else:
            os.remove(fullpath)
    os.rename(
        user_profile + "\\spicetify-cli\\Themes\\Default",
        user_profile + "\\spicetify-cli\\Themes\\SpicetifyDefault",
    )
    print("Finished unpacking new themes!\n")
