from colorama import Fore
from pathlib import Path
import subprocess
import shutil
import os

from modules import globals, utils


def install():
    user_profile  = os.environ['USERPROFILE']
    appdata_local = os.environ['LOCALAPPDATA']
    appdata       = os.environ['APPDATA']
    temp          = os.environ['TEMP']
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
        utils.kill_process('Spotify.exe')
        subprocess.Popen(["powershell", 'cmd /c "%USERPROFILE%\AppData\Roaming\Spotify\Spotify.exe" /UNINSTALL /SILENT'])
        while True:
            if not utils.process_running('powershell'):
                print(f"{Fore.GREEN}Finished Uninstalling Spotify.\n")
                break
            # FIXME: very unreliable check, should catch PID of spawned process and check that instead of common executable name
    else:
        print(f"{Fore.GREEN}Spotify Already Uninstalled.\n")

    print(f"{Fore.MAGENTA}[Wiping Folders]\n")
    for folder in folders:
        try:
            shutil.rmtree(folder)
            print(f'{Fore.GREEN}"{folder}" has been deleted.\n')
        except OSError as e :
            print(f'{Fore.RED}"{folder}" was not deleted: {e}\n')
    print(f"{Fore.MAGENTA}[Finished Wiping Folders]\n")

    print(f'{Fore.YELLOW}Downloading Spotify Version.')
    if not os.path.isdir(temp):
        os.mkdir(temp)
    utils.requests_progress(globals.FULL_SETUP_URL, (temp + '\spotify-1-1-62-583.exe'))
    print(f'{Fore.GREEN}Finished Downloading Spotify Version.\n')

    print(f"{Fore.YELLOW}Installing Spotify.")
    utils.kill_process('Spotify.exe')
    utils.start_process(temp + '\spotify-1-1-62-583.exe')
    while True:
        if not utils.process_running('spotify-1-1-62-583.exe') and spotify_prefs.is_file():
            # FIXME: again, unreliable check
            print(f"{Fore.GREEN}Finished Installing Spotify.\n")
            utils.kill_process('Spotify.exe')
            os.remove(temp + '\spotify-1-1-62-583.exe')
            break

    print(f"{Fore.YELLOW}Installing Spicetify.")
    utils.kill_process('powershell')

    subprocess.Popen(["powershell", "$ProgressPreference = 'SilentlyContinue'\n$v='2.5.0'; Invoke-WebRequest -UseBasicParsing 'https://raw.githubusercontent.com/OhItsTom/spicetify-easyinstall/Spicetify-v2/install.ps1' | Invoke-Expression\n$all = spicetify\n $all = spicetify backup apply enable-devtool"])

    while True:
        if not utils.process_running('powershell'):
            # FIXME: again, unreliable check
            print(f"{Fore.GREEN}Finished Installing Spicetify.\n")

            if not os.path.isdir(appdata_local + "\\Spotify\\Update"):
                os.mkdir(appdata_local + "\\Spotify\\Update")
            subprocess.Popen(["powershell", '$all = cmd /c icacls %localappdata%\\Spotify\\Update /deny %username%:D'])
            subprocess.Popen(["powershell", '$all = cmd /c icacls %localappdata%\\Spotify\\Update /deny %username%:R'])
            utils.kill_process('Spotify.exe')
            break

    print(f"{Fore.YELLOW}Downloading Themes.")
    utils.kill_process('powershell')
    subprocess.Popen(["powershell",'$ProgressPreference = "SilentlyContinue"\n$sp_dir = "${HOME}\spicetify-cli"\n$zip_file = "${sp_dir}\Themes.zip"\n$download_uri = "https://github.com/morpheusthewhite/spicetify-themes/archive/refs/heads/master.zip"\nInvoke-WebRequest -Uri $download_uri -UseBasicParsing -OutFile $zip_file\nExpand-Archive -Path $zip_file -DestinationPath $sp_dir -Force\nRemove-Item -Path $zip_file\nRemove-Item -LiteralPath "${HOME}\spicetify-cli\Themes" -Force -Recurse\nRename-Item "${HOME}\spicetify-cli\spicetify-themes-master" "${HOME}\spicetify-cli\Themes"\nRemove-Item "${HOME}\spicetify-cli\Themes\*.*" -Force -Recurse | Where { ! $_.PSIsContainer }\nRename-Item "${HOME}\spicetify-cli\Themes\default" "${HOME}\spicetify-cli\Themes\SpicetifyDefault"'])
    while True:
        if not utils.process_running('powershell'):
            # FIXME: still an unreliable check
            print(f"{Fore.GREEN}Finished Downloading Themes.")
            break


def update_config():
    print("placeholder")


def update_addons():
    print("Downloading Themes.")
    utils.kill_process('powershell')
    subprocess.Popen(["powershell",'$sp_dir = "${HOME}\spicetify-cli"\n$zip_file = "${sp_dir}\Themes.zip"\n$download_uri = "https://github.com/morpheusthewhite/spicetify-themes/archive/refs/heads/master.zip"\nInvoke-WebRequest -Uri $download_uri -UseBasicParsing -OutFile $zip_file\nExpand-Archive -Path $zip_file -DestinationPath $sp_dir -Force\nRemove-Item -Path $zip_file\nRemove-Item -LiteralPath "${HOME}\spicetify-cli\Themes" -Force -Recurse\nRename-Item "${HOME}\spicetify-cli\spicetify-themes-master" "${HOME}\spicetify-cli\Themes"\nRemove-Item "${HOME}\spicetify-cli\Themes\*.*" -Force -Recurse | Where { ! $_.PSIsContainer }\nRename-Item "${HOME}\spicetify-cli\Themes\default" "${HOME}\spicetify-cli\Themes\SpicetifyDefault"'])
    while True:
        if not utils.process_running('powershell'):
            # FIXME: and again, unreliable check
            print("Finished Downloading Themes.")
            break


def uninstall():
    print("placeholder")
