import glob
import os
import shutil
import subprocess
import time
from pathlib import Path

from colorama import Fore

from modules import globals, utils


def install():
    user_profile = os.environ['USERPROFILE']
    appdata_local = os.environ['LOCALAPPDATA']
    appdata = os.environ['APPDATA']
    temp = os.environ['TEMP']
    folders = [
        (user_profile + '\spicetify-cli'),
        (user_profile + '\.spicetify'),
        (appdata_local + '\spotify'),
        (appdata + '\spotify'),
        (temp)
    ]
    spotify_prefs = Path(user_profile + "\AppData\Roaming\Spotify\prefs")

    if os.path.isdir(appdata + "\Spotify"):
        print(f"{Fore.YELLOW}Uninstalling Spotify.")
        utils.kill_processes('Spotify.exe')
        powershell_uninstall_pid = subprocess.Popen(
            ["powershell", 'cmd /c "%USERPROFILE%\AppData\Roaming\Spotify\Spotify.exe" /UNINSTALL /SILENT']).pid
        while utils.process_pid_running(powershell_uninstall_pid):
            time.sleep(0.25)
        print(f"{Fore.GREEN}Finished Uninstalling Spotify.\n")
    else:
        print(f"{Fore.GREEN}Spotify Already Uninstalled.\n")

    print(f"{Fore.MAGENTA}[Wiping Folders]\n")
    for folder in folders:
        try:
            shutil.rmtree(folder)
            print(f'{Fore.GREEN}"{folder}" has been deleted.\n')
        except OSError as e:
            print(f'{Fore.RED}"{folder}" was not deleted: {e}\n')
    print(f"{Fore.MAGENTA}[Finished Wiping Folders]\n")

    print(f'{Fore.YELLOW}Downloading Spotify Version.')
    if not os.path.isdir(temp):
        os.mkdir(temp)
    utils.requests_progress(globals.FULL_SETUP_URL,
                            (temp + '\spotify-1-1-62-583.exe'))
    print(f'{Fore.GREEN}Finished Downloading Spotify Version.\n')

    print(f"{Fore.YELLOW}Installing Spotify.")
    utils.kill_processes('Spotify.exe')
    spotify_install_pid = utils.start_process(
        temp + '\spotify-1-1-62-583.exe').pid
    while utils.process_pid_running(spotify_install_pid) or not spotify_prefs.is_file():
        time.sleep(0.25)
    print(f"{Fore.GREEN}Finished Installing Spotify.\n")
    utils.kill_processes('Spotify.exe')
    os.remove(temp + '\spotify-1-1-62-583.exe')

    print(f"{Fore.YELLOW}Downloading Spicetify.")
    utils.requests_progress(globals.OLD_EXTRACTED_URL,
                            (temp + 'Extracted.zip'))
    print(f'{Fore.GREEN}Finished Downloading Spicetify.\n')

    print(f"{Fore.YELLOW}Installing Spicetify.")
    powershell_install_pid = subprocess.Popen(
        ["powershell", "$ProgressPreference = 'SilentlyContinue'\n$v='2.5.0'; Invoke-WebRequest -UseBasicParsing 'https://raw.githubusercontent.com/OhItsTom/spicetify-easyinstall/Spicetify-v2/install.ps1' | Invoke-Expression\n$all = spicetify\n $all = spicetify backup apply enable-devtool"]).pid
    while utils.process_pid_running(powershell_install_pid):
        time.sleep(0.25)
    utils.kill_processes('Spotify.exe')
    print(f'{Fore.GREEN}Finished Installing Spicetify.\n')

    print(f"{Fore.YELLOW}Replacing Deprecated Files.")
    shutil.rmtree(user_profile + '\.spicetify\Extracted')
    shutil.unpack_archive(temp + 'Extracted.zip', user_profile + '\.spicetify')
    os.remove(temp + 'Extracted.zip')
    print(f'{Fore.GREEN}Finished Replacing Deprecated Files.\n')

    print(f"{Fore.YELLOW}Preventing Spotify From Updating.")
    if not os.path.isdir(appdata_local + "\\Spotify\\Update"):
        os.mkdir(appdata_local + "\\Spotify\\Update")
    subprocess.Popen(
        ["powershell", '$all = cmd /c icacls %localappdata%\\Spotify\\Update /deny %username%:D'])
    subprocess.Popen(
        ["powershell", '$all = cmd /c icacls %localappdata%\\Spotify\\Update /deny %username%:R'])
    print(f"{Fore.GREEN}Finished Preventing Spotify From Updating.\n")

    print(f"{Fore.YELLOW}Downloading Themes.")
    shutil.rmtree(user_profile + '\spicetify-cli\Themes')
    utils.requests_progress(globals.DOWNLOAD_THEME_URL,
                            (user_profile + '\spicetify-cli\Themes.zip'))
    shutil.unpack_archive(
        user_profile + '\spicetify-cli\Themes.zip', user_profile + '\spicetify-cli')
    os.remove(user_profile + '\spicetify-cli\Themes.zip')
    os.rename(user_profile + '\spicetify-cli\spicetify-themes-cbd332f7c683575f65b102b662ee9fd008d4d284',
              user_profile + '\spicetify-cli\Themes')

    for item in os.listdir(user_profile + '\\spicetify-cli\\Themes\\'):
        if item.find(".") != -1:
            try:
                os.remove((user_profile + '\\spicetify-cli\\Themes\\') + item)
            except:
                shutil.rmtree(
                    (user_profile + '\\spicetify-cli\\Themes\\') + item)

    os.rename(user_profile + '\spicetify-cli\Themes\Default',
              user_profile + '\spicetify-cli\Themes\SpicetifyDefault')
    shutil.move(user_profile + '\spicetify-cli\Themes\Dribbblish\Dribbblish.js',
                user_profile + '\spicetify-cli\Extensions')
    print(f"{Fore.GREEN}Finished Downloading Themes.")


def update_config():
    print("placeholder")


def update_addons():
    user_profile = os.environ['USERPROFILE']
    print(f"{Fore.YELLOW}Downloading Themes.")
    shutil.rmtree(user_profile + '\spicetify-cli\Themes')
    utils.requests_progress(globals.DOWNLOAD_THEME_URL,
                            (user_profile + '\spicetify-cli\Themes.zip'))
    shutil.unpack_archive(
        user_profile + '\spicetify-cli\Themes.zip', user_profile + '\spicetify-cli')
    os.remove(user_profile + '\spicetify-cli\Themes.zip')
    os.rename(user_profile + '\spicetify-cli\spicetify-themes-cbd332f7c683575f65b102b662ee9fd008d4d284',
              user_profile + '\spicetify-cli\Themes')

    for item in os.listdir(user_profile + '\\spicetify-cli\\Themes\\'):
        if item.find(".") != -1:
            try:
                os.remove((user_profile + '\\spicetify-cli\\Themes\\') + item)
            except:
                shutil.rmtree(
                    (user_profile + '\\spicetify-cli\\Themes\\') + item)

    os.rename(user_profile + '\spicetify-cli\Themes\Default',
              user_profile + '\spicetify-cli\Themes\SpicetifyDefault')
    shutil.move(user_profile + '\spicetify-cli\Themes\Dribbblish\Dribbblish.js',
                user_profile + '\spicetify-cli\Extensions')
    print(f"{Fore.GREEN}Finished Downloading Themes.")


def uninstall():
    print("placeholder")
