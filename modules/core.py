import glob
import os
import shutil
import subprocess
import tempfile
import time
from pathlib import Path

from colorama import Fore

from modules import globals, utils


def install():
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
    
    if os.path.isdir(appdata + "\Spotify"):  # Section 1
        print(f"{Fore.YELLOW}Uninstalling Spotify.")
        utils.kill_processes("Spotify.exe")
        powershell_uninstall_pid = subprocess.Popen(
            [
                "powershell",
                'cmd /c "%USERPROFILE%\AppData\Roaming\Spotify\Spotify.exe" /UNINSTALL /SILENT',
            ]
        ).pid
        while utils.process_pid_running(powershell_uninstall_pid):
            time.sleep(0.25)
        print(f"{Fore.GREEN}Finished Uninstalling Spotify.\n")
    else:
        print(f"{Fore.GREEN}Spotify Already Uninstalled.\n")

    print(f"{Fore.MAGENTA}[Wiping Folders]\n")  # Section 2
    for folder in folders:
        try:
            shutil.rmtree(folder)
            print(f'{Fore.GREEN}"{folder}" has been deleted.\n')
        except OSError as e:
            print(f'{Fore.RED}"{folder}" was not deleted: {e}\n')
    print(f"{Fore.MAGENTA}[Finished Wiping Folders]\n")

    print(f"{Fore.YELLOW}Downloading Spotify Version.")  # Section 3
    if not os.path.isdir(temp):
        os.mkdir(temp)
    utils.requests_progress(globals.FULL_SETUP_URL, (temp + globals.INSTALLER_NAME))
    print(f"{Fore.GREEN}Finished Downloading Spotify Version.\n")

    print(f"{Fore.YELLOW}Installing Spotify.")  # Section 4
    utils.kill_processes("Spotify.exe")
    spotify_install_pid = utils.start_process(temp + globals.INSTALLER_NAME).pid
    while utils.process_pid_running(spotify_install_pid) or not spotify_prefs.is_file():
        time.sleep(0.25)
    print(f"{Fore.GREEN}Finished Installing Spotify.\n")
    utils.kill_processes("Spotify.exe")
    os.remove(temp + globals.INSTALLER_NAME)

    print(f"{Fore.YELLOW}Installing Spicetify.")  # Section 6
    powershell_install_pid = subprocess.Popen(
        [
            "powershell",
            "$ProgressPreference = 'SilentlyContinue'\n$v='%s'; Invoke-WebRequest -UseBasicParsing 'https://raw.githubusercontent.com/OhItsTom/spicetify-easyinstall/Spicetify-v2/install.ps1' | Invoke-Expression\n$all = spicetify\n $all = spicetify backup apply enable-devtool"
            % globals.SPICETIFY_VERSION,
        ]
    ).pid
    while utils.process_pid_running(powershell_install_pid):
        time.sleep(0.25)
    utils.kill_processes("Spotify.exe")
    print(f"{Fore.GREEN}Finished Installing Spicetify.\n")

    print(f"{Fore.YELLOW}Preventing Spotify From Updating.")  # Section 8
    if not os.path.isdir(appdata_local + "\\Spotify\\Update"):
        os.mkdir(appdata_local + "\\Spotify\\Update")

    subprocess.Popen(
        [
            "powershell",
            "$all = cmd /c icacls %localappdata%\\Spotify\\Update /deny %username%:D",
        ]
    )
    subprocess.Popen(
        [
            "powershell",
            "$all = cmd /c icacls %localappdata%\\Spotify\\Update /deny %username%:R",
        ]
    )
    print(f"{Fore.GREEN}Finished Preventing Spotify From Updating.\n")

    print(f"{Fore.YELLOW}Downloading Themes.")  # Section 9
    shutil.rmtree(user_profile + "\spicetify-cli\Themes")
    utils.requests_progress(
        globals.DOWNLOAD_THEME_URL, (user_profile + "\spicetify-cli\Themes.zip")
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
    shutil.move(
        user_profile + "\spicetify-cli\Themes\Dribbblish\Dribbblish.js",
        user_profile + "\spicetify-cli\Extensions",
    )
    print(f"{Fore.GREEN}Finished Downloading Themes.")


def update_config():
    print("placeholder")


def update_addons():
    user_profile = os.environ["USERPROFILE"]
    print(f"{Fore.YELLOW}Downloading Themes.")
    shutil.rmtree(user_profile + "\spicetify-cli\Themes")
    utils.requests_progress(
        globals.DOWNLOAD_THEME_URL, (user_profile + "\spicetify-cli\Themes.zip")
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
    shutil.move(
        user_profile + "\spicetify-cli\Themes\Dribbblish\Dribbblish.js",
        user_profile + "\spicetify-cli\Extensions",
    )
    print(f"{Fore.GREEN}Finished Downloading Themes.")


def uninstall():
    user_profile = os.path.expanduser("~")  # Vars
    temp = tempfile.gettempdir()
    folders = [
        (user_profile + "\spicetify-cli"),
        (user_profile + "\.spicetify"),
        (temp),
    ]

    print(f"{Fore.MAGENTA}[Wiping Folders]\n")  # Section 1
    for folder in folders:
        try:
            shutil.rmtree(folder)
            print(f'{Fore.GREEN}"{folder}" has been deleted.\n')
        except OSError as e:
            print(f'{Fore.RED}"{folder}" was not deleted: {e}\n')

    # subprocess.Popen( #Delete ENV VAR
    # ["powershell", '$all = cmd /c setx Path '])
    print(f"{Fore.MAGENTA}[Finished Wiping Folders]\n")
