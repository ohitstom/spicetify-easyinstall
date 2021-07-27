import os
import shutil
import psutil
import requests
import subprocess
from pathlib import Path
from colorama import init, Fore
from clint.textui import progress

FULL_SETUP_URL = 'https://github.com/OhItsTom/Spotify-Version/releases/download/spotify-1-1-62-583/spotify-1-1-62-583.exe'


init()
os.system("mode con: cols=90 lines=30")
os.system("title " + "Spicetify Easyinstall")


#SIDE FUNCTIONS
def requests_progress(url, path):
    if os.path.isdir(path) == True:
        os.mkdir(path)
    r = requests.get(url, stream=True)
    with open(path, 'wb') as f:
        total_length = int((r.headers.get('content-length')))
        for chunk in progress.bar(r.iter_content(chunk_size=1024000), expected_size=round(total_length/1024000)):
            if chunk:
                f.write(chunk)
                f.flush()
        print ("\033[A                                                     \033[A")


def start_process(path):
    SW_HIDE = 0
    info = subprocess.STARTUPINFO()
    info.dwFlags = subprocess.STARTF_USESHOWWINDOW
    info.wShowWindow = SW_HIDE
    subprocess.Popen(path, startupinfo=info)


def kill_process(name):
    for proc in psutil.process_iter():
        try:
            if name.lower() in proc.name().lower():
                proc.kill()
        except Exception:
            pass


def process_running(name):
    for proc in psutil.process_iter():
        try:
            if name.lower() in proc.name().lower():
                return True
        except Exception:
            pass
    return False;


#MAIN FUNCTIONS
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
        kill_process('Spotify.exe')
        subprocess.Popen(["powershell", 'cmd /c "%USERPROFILE%\AppData\Roaming\Spotify\Spotify.exe" /UNINSTALL /SILENT'])
        while True:
            if not process_running('powershell'):
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
    requests_progress(FULL_SETUP_URL, (temp + '\spotify-1-1-62-583.exe'))
    print(f'{Fore.GREEN}Finished Downloading Spotify Version.\n')

    print(f"{Fore.YELLOW}Installing Spotify.")
    kill_process('Spotify.exe')
    start_process(temp + '\spotify-1-1-62-583.exe')
    while True:
        if not process_running('spotify-1-1-62-583.exe') and spotify_prefs.is_file():
            # FIXME: again, unreliable check
            print(f"{Fore.GREEN}Finished Installing Spotify.\n")
            kill_process('Spotify.exe')
            os.remove(temp + '\spotify-1-1-62-583.exe')
            break

    print(f"{Fore.YELLOW}Installing Spicetify.")
    kill_process('powershell')

    subprocess.Popen(["powershell", "$ProgressPreference = 'SilentlyContinue'\n$v='2.5.0'; Invoke-WebRequest -UseBasicParsing 'https://raw.githubusercontent.com/OhItsTom/spicetify-easyinstall/Spicetify-v2/install.ps1' | Invoke-Expression\n$all = spicetify\n $all = spicetify backup apply enable-devtool"])

    while True:
        if not process_running('powershell'):
            # FIXME: again, unreliable check
            print(f"{Fore.GREEN}Finished Installing Spicetify.\n")

            if not os.path.isdir(appdata_local + "\\Spotify\\Update"):
                os.mkdir(appdata_local + "\\Spotify\\Update")
            subprocess.Popen(["powershell", '$all = cmd /c icacls %localappdata%\\Spotify\\Update /deny %username%:D'])
            subprocess.Popen(["powershell", '$all = cmd /c icacls %localappdata%\\Spotify\\Update /deny %username%:R'])
            kill_process('Spotify.exe')
            break

    print(f"{Fore.YELLOW}Downloading Themes.")
    kill_process('powershell')
    subprocess.Popen(["powershell",'$ProgressPreference = "SilentlyContinue"\n$sp_dir = "${HOME}\spicetify-cli"\n$zip_file = "${sp_dir}\Themes.zip"\n$download_uri = "https://github.com/morpheusthewhite/spicetify-themes/archive/refs/heads/master.zip"\nInvoke-WebRequest -Uri $download_uri -UseBasicParsing -OutFile $zip_file\nExpand-Archive -Path $zip_file -DestinationPath $sp_dir -Force\nRemove-Item -Path $zip_file\nRemove-Item -LiteralPath "${HOME}\spicetify-cli\Themes" -Force -Recurse\nRename-Item "${HOME}\spicetify-cli\spicetify-themes-master" "${HOME}\spicetify-cli\Themes"\nRemove-Item "${HOME}\spicetify-cli\Themes\*.*" -Force -Recurse | Where { ! $_.PSIsContainer }\nRename-Item "${HOME}\spicetify-cli\Themes\default" "${HOME}\spicetify-cli\Themes\SpicetifyDefault"'])
    while True:
        if not process_running('powershell'):
            # FIXME: still an unreliable check
            print(f"{Fore.GREEN}Finished Downloading Themes.")
            break


def update_config():
    print("placeholder")


def update_addons():
    print("Downloading Themes.")
    kill_process('powershell')
    subprocess.Popen(["powershell",'$sp_dir = "${HOME}\spicetify-cli"\n$zip_file = "${sp_dir}\Themes.zip"\n$download_uri = "https://github.com/morpheusthewhite/spicetify-themes/archive/refs/heads/master.zip"\nInvoke-WebRequest -Uri $download_uri -UseBasicParsing -OutFile $zip_file\nExpand-Archive -Path $zip_file -DestinationPath $sp_dir -Force\nRemove-Item -Path $zip_file\nRemove-Item -LiteralPath "${HOME}\spicetify-cli\Themes" -Force -Recurse\nRename-Item "${HOME}\spicetify-cli\spicetify-themes-master" "${HOME}\spicetify-cli\Themes"\nRemove-Item "${HOME}\spicetify-cli\Themes\*.*" -Force -Recurse | Where { ! $_.PSIsContainer }\nRename-Item "${HOME}\spicetify-cli\Themes\default" "${HOME}\spicetify-cli\Themes\SpicetifyDefault"'])
    while True:
        if not process_running('powershell'):
            # FIXME: and again, unreliable check
            print("Finished Downloading Themes.")
            break


def uninstall():
    print("placeholder")


#START MENU
if __name__ == "__main__":
    while True:
        try:
            print(f"{Fore.MAGENTA}\n"
                  f"[Startup]\n"
                  f"\n{Fore.GREEN}"
                  f" 1) Install\n"
                  f"\n"
                  f" 2) Update Config\n"
                  f"\n"
                  f" 3) Download Latest Themes And Extensions\n"
                  f"\n"
                  f" 4) Uninstall\n"
                  f"{Fore.MAGENTA}")

            try:
                launch = int(input("Choose From The List Above (1-4): "))
            except Exception:
                os.system("cls")
                print(f"{Fore.RED}[!] INVALID OPTION! Make Sure To Choose A (WHOLE) Number Corresponding To Your Choice [!]")
                continue

            os.system("cls")

            if launch == 1:
                install()
                return_start = input(f"{Fore.MAGENTA}\nReturn To Startup? Y/N: ")
                if return_start.lower() in ["n", "no"]:
                    break
                os.system("cls")

            elif launch == 2:
                update_config()
                break

            elif launch == 3:
                update_addons()
                return_start = input(f"{Fore.MAGENTA}\nReturn To Startup? Y/N: ")
                if return_start.lower() in ["n", "no"]:
                    break
                os.system("cls")

            elif launch == 4:
                uninstall()
                break

            else:
                print(f"{Fore.RED}[!] INVALID OPTION! Please Make Sure To Choose A Valid Option (1-4) [!]")

        except Exception as e:
            os.system("cls")
            print(f"{Fore.RED}[!]{e}[!]")
