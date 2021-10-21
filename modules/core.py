import os
import shutil
import asyncio
import tempfile
import subprocess
from pathlib import Path
from typing import Type

from modules import globals, utils


async def install():
    steps_count = 7
    user_profile = os.path.expanduser("~")  # Vars
    appdata_local = os.environ["LOCALAPPDATA"]
    appdata = os.environ["APPDATA"]
    temp = tempfile.gettempdir()
    spotify_prefs = Path(user_profile + "\AppData\Roaming\Spotify\prefs")
    folders = [
        (user_profile  + "\spicetify-cli"),
        (user_profile  + "\.spicetify"),
        (appdata_local + "\spotify"),
        (appdata + "\spotify"),
        (temp),
    ]

    print(f"(1/{steps_count}) Uninstalling Spotify...")  # Section 1
    if os.path.isdir(appdata + "\Spotify"):
        utils.kill_processes("Spotify.exe")
        powershell_uninstall_pid = subprocess.Popen(
            [
                "powershell",
                'cmd /c "%USERPROFILE%\AppData\Roaming\Spotify\Spotify.exe" /UNINSTALL /SILENT\n$all = cmd /c icacls %localappdata%\\Spotify\\Update /grant %username%:D\n$all = cmd /c icacls %localappdata%\\Spotify\\Update /grant %username%:R'
            ]
        ).pid
        while utils.process_pid_running(powershell_uninstall_pid):
            await asyncio.sleep(0.25)
        print(f"Finished uninstalling Spotify!\n")
    else:
        print(f"Spotify is not installed!\n")

    print(f"(2/{steps_count}) Wiping folders...")  # Section 2
    for folder in folders:
        try:
            shutil.rmtree(folder, ignore_errors=True)
            if os.path.exists(folder) != True:
                print(f'"{folder}" is already empty.')
            else:
                print(f'"{folder}" has been deleted.')

        except Exception as e:
            print(f'"{folder}" was not deleted: {e}.')
    print(f"Finished wiping folders!\n")

    print(f"(3/{steps_count}) Downloading correct Spotify version...")  # Section 3
    if not os.path.isdir(temp):
        os.mkdir(temp)
    await utils.chunked_download(
        url=globals.FULL_SETUP_URL,
        path=(temp + globals.INSTALLER_NAME),
        label=globals.INSTALLER_NAME[1:]
    )
    print(f"Finished downloading Spotify!\n")

    print(f"(4/{steps_count}) Installing Spotify...")  # Section 4
    utils.kill_processes("Spotify.exe")
    spotify_install_pid = utils.start_process(temp + globals.INSTALLER_NAME).pid
    while utils.process_pid_running(spotify_install_pid) or not spotify_prefs.is_file():
        await asyncio.sleep(0.25)
    utils.kill_processes("Spotify.exe")
    os.remove(temp + globals.INSTALLER_NAME)
    print(f"Finished installing Spotify!\n")

    print(f"(5/{steps_count}) Installing Spicetify...")  # Section 5
    powershell_install_pid = subprocess.Popen(
        [
            "powershell",
            "$ProgressPreference = 'SilentlyContinue'\n$v='%s'; Invoke-WebRequest -UseBasicParsing 'https://raw.githubusercontent.com/OhItsTom/spicetify-easyinstall/Spicetify-v2/install.ps1' | Invoke-Expression\n$all = spicetify\n $all = spicetify backup apply enable-devtool"
            % globals.SPICETIFY_VERSION,
        ]
    ).pid
    while utils.process_pid_running(powershell_install_pid):
        await asyncio.sleep(0.25)
    print(f"Finished installing Spicetify!\n")

    print(f"(6/{steps_count}) Preventing Spotify from updating...")  # Section 6
    utils.kill_processes("Spotify.exe")
    if not os.path.isdir(appdata_local + "\\Spotify\\Update"):
        os.mkdir(appdata_local + "\\Spotify\\Update")
    powershell_prevention_pid = subprocess.Popen(
        [
            "powershell",
            "$all = cmd /c icacls %localappdata%\\Spotify\\Update /deny %username%:D\n$all = cmd /c icacls %localappdata%\\Spotify\\Update /deny %username%:R",
        ]
    ).pid
    while utils.process_pid_running(powershell_prevention_pid):
        await asyncio.sleep(0.25)
    print(f"Finished blocking Spotify updates!\n")

    print(f"(7/{steps_count}) Downloading themes...")  # Section 7
    shutil.rmtree(user_profile + "\spicetify-cli\Themes")
    retries = 0
    while True:
        try:
            await utils.chunked_download(
                url=globals.DOWNLOAD_THEME_URL,
                path=(user_profile + "\spicetify-cli\Themes.zip"),
                label="Themes.zip"
            )
            break
        except TypeError:
            retries += 1
            if retries > 20:
                raise ConnectionError("Couldn't retrieve 'content-length' header")
            continue
    shutil.unpack_archive(
        user_profile + "\spicetify-cli\Themes.zip", user_profile + "\spicetify-cli"
    )
    os.remove(user_profile + "\spicetify-cli\Themes.zip")
    os.rename(
        user_profile
        + "\spicetify-cli" + globals.THEMES_EXTRACTED,
        user_profile + "\spicetify-cli\Themes",
    )
    for item in list(Path(user_profile + "\spicetify-cli\Themes").glob("*")):
        fullpath = str(item)
        filename = str(item.name)
        if os.path.isdir(fullpath):
            if filename[0] == ".":
                shutil.rmtree(fullpath)
        else:
            os.remove(fullpath)
    os.rename(
        user_profile + "\spicetify-cli\Themes\Default",
        user_profile + "\spicetify-cli\Themes\SpicetifyDefault",
    )
    print(f"Finished downloading themes!\n")

    # End of the terminal page
    # I need to add a bool checker for if launch when ready is enabled

def update_config():
    count = 0
    for themes in utils.list_config_available(1):
        count += 1
        print(f"\n{count}) {themes}")

        launch = int(input(f"\nChoose From The List Above (1-{count}): "))  # FIXME
        utils.set_config_entry("current_theme", utils.list_config_available(1)[launch-1])

    # Current Quick Mockup of function usage
    # Needs to run after the gui is finished, so i need to have the config menu rendered here? Or just pass variables saved in main.py to the func on run after gui is closed.

async def update_addons(addon_type):
    if addon_type == "shipped":
        print("Not yet implemented!")
    elif addon_type == "latest":
        print("Not yet implemented!")
    return
    user_profile = os.environ["USERPROFILE"]
    print(f"Downloading Themes.")
    shutil.rmtree(user_profile + "\spicetify-cli\Themes")
    await utils.chunked_download(
        url=globals.DOWNLOAD_THEME_URL,
        path=(user_profile + "\spicetify-cli\Themes.zip"),
        label="Themes.zip"
    )
    shutil.unpack_archive(
        user_profile + "\spicetify-cli\Themes.zip", user_profile + "\spicetify-cli"
    )
    os.remove(user_profile + "\spicetify-cli\Themes.zip")
    os.rename(
        user_profile
        + "\spicetify-cli" + globals.THEMES_EXTRACTED,
        user_profile + "\spicetify-cli\Themes",
    )

    for item in list(Path(user_profile + "\spicetify-cli\Themes").glob("*")):
        fullpath = str(item)
        filename = str(item.name)
        if os.path.isdir(fullpath):
            if filename[0] == ".":
                shutil.rmtree(fullpath)
        else:
            os.remove(fullpath)

    os.rename(
        user_profile + "\spicetify-cli\Themes\Default",
        user_profile + "\spicetify-cli\Themes\SpicetifyDefault",
    )
    print(f"Finished Downloading Themes.")
    # End of the terminal page
    # Needs to read a bool of what was selected, latest or current.

async def uninstall():
    steps_count = 1
    user_profile = os.path.expanduser("~")  # Vars
    appdata_local = os.environ["LOCALAPPDATA"]
    temp = "C:\\Users\\WDAGUtilityAccount\\AppData\\Local\\temp"
    folders = [
        (user_profile + "\spicetify-cli"),
        (user_profile + "\.spicetify"),
        (temp),
    ]

    print(f"(1/{steps_count}) Wiping folders...")  # Section 1
    for folder in folders:
        try:
            shutil.rmtree(folder, ignore_errors=True)
            if os.path.exists(folder) != True:
                print(f'"{folder}" is already empty.')
            else:
                print(f'"{folder}" has been deleted.')

        except Exception as e:
            print(f'"{folder}" was not deleted: {e}.')
    print(f"Finished wiping folders!\n")
    # subprocess.Popen( #Delete ENV VAR
    # ["powershell", '$all = cmd /c setx Path '])

    # End of the terminal page
    # Needs rewriting