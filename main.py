#IMPORTS
import os
import sys
import time
import shutil
import psutil
import colorama
import requests
import icaclswrap as icacls
import subprocess;
from os import mkdir
from pathlib import Path
from clint.textui import progress
from colorama import init, Fore, Back, Style
init()
os.system("mode con: cols=90 lines=30")
os.system("title " + "Spicetify Easyinstall")

#SIDE FUNCTIONS
def requests_progress(url, path):
    if os.path.isdir(path) == True:
        mkdir(path)
    r = requests.get(url, stream=True) 
    with open(path, 'w') as f:
        total_length = int(r.headers.get('content-length'))
        for chunk in progress.bar(r.iter_content(chunk_size=1024000), expected_size=round(total_length/1024000)):
            if chunk:
                f.write(str(chunk))
                f.flush()
        print ("\033[A                                                     \033[A")

def startProgram(program):
    SW_HIDE = 0
    info = subprocess.STARTUPINFO()
    info.dwFlags = subprocess.STARTF_USESHOWWINDOW
    info.wShowWindow = SW_HIDE
    subprocess.Popen(program, startupinfo=info)
        
def terminateProgram(processName):
    for proc in psutil.process_iter():
        if processName.lower() in proc.name().lower():
            proc.terminate()
        else:
            continue

def checkIfProcessRunning(processName):
    for proc in psutil.process_iter():
        try:
            if processName.lower() in proc.name().lower():
                return True
        except (psutil.NoSuchProcess, psutil.AccessDenied, psutil.ZombieProcess):
            pass
    return False;

#MAIN FUNCTIONS
def INSTALL():
    user_profile = os.environ['USERPROFILE']
    appdata_local = os.environ['LOCALAPPDATA']
    appdata = os.environ['APPDATA']
    temp = os.environ['TEMP']
    FolderDictionary = [(user_profile + '\spicetify-cli'), (user_profile + '\.spicetify'), (appdata_local + '\spotify'), (appdata + '\spotify'), (temp)]
    my_file = Path(user_profile + "\AppData\Roaming\Spotify\prefs")
    
    if os.path.isdir(appdata + "\Spotify")== True:
        print(Fore.YELLOW + "Uninstalling Spotify.")
        terminateProgram('Spotify.exe')
        subprocess.Popen(["powershell", 'cmd /c "%USERPROFILE%\AppData\Roaming\Spotify\Spotify.exe" /UNINSTALL /SILENT'])
        while True:
            if checkIfProcessRunning('powershell') == False:
                print(Fore.GREEN + "Finished Uninstalling Spotify.\n")
                break
    else:
        print(Fore.GREEN + "Spotify Already Uninstalled.\n")
        
    print(Fore.MAGENTA + "[Wiping Folders]\n")
    for x in FolderDictionary:
        try:
            shutil.rmtree(x)
            print(Fore.GREEN + '"%s", has been deleted.\n' % x)
        except OSError as e :
            print(Fore.RED + '"%s", was not found.\n' % x)
    print(Fore.MAGENTA + "[Finished Wiping Folders]\n")

    print(Fore.YELLOW + 'Downloading Spotify Version.')
    if os.path.isdir(temp) == False:
        mkdir(temp)
    requests_progress('https://download1591.mediafire.com/9t6d6qio80xg/rcszp96g4nqiinj/spotify-1-1-62-583.exe',temp + '\spotify-1-1-62-583.exe')
    print(Fore.GREEN + 'Finished Downloading Spotify Version.\n')
    
    print(Fore.YELLOW + "Installing Spotify.")
    terminateProgram('Spotify.exe')
    startProgram(temp + '\spotify-1-1-62-583.exe')
    while True:
        if checkIfProcessRunning('spotify-1-1-62-583.exe') == False and my_file.is_file():
            print(Fore.GREEN + "Finished Installing Spotify.\n")
            terminateProgram('Spotify.exe')
            os.remove(temp + '\spotify-1-1-62-583.exe')
            break
    
    print(Fore.YELLOW + "Installing Spicetify.")
    terminateProgram('powershell')
    subprocess.Popen(["powershell","$ProgressPreference = 'SilentlyContinue'\n$v='2.5.0'; Invoke-WebRequest -UseBasicParsing 'https://raw.githubusercontent.com/OhItsTom/spicetify-easyinstall/Spicetify-v2/install.ps1' | Invoke-Expression\n$all = spicetify\n $all = spicetify backup apply enable-devtool"])
    while True:
        if checkIfProcessRunning('powershell') == False:
            print(Fore.GREEN + "Finished Installing Spicetify.\n")

            if os.path.isdir(appdata_local + "\\Spotify\\Update") == False:
                mkdir(appdata_local + "\\Spotify\\Update")
            subprocess.Popen(["powershell", '$all = cmd /c icacls %localappdata%\\Spotify\\Update /deny %username%:D'])
            subprocess.Popen(["powershell", '$all = cmd /c icacls %localappdata%\\Spotify\\Update /deny %username%:R'])
            terminateProgram('Spotify.exe')
            break

    print(Fore.YELLOW + "Downloading Themes.")
    terminateProgram('powershell')
    subprocess.Popen(["powershell",'$ProgressPreference = "SilentlyContinue"\n$sp_dir = "${HOME}\spicetify-cli"\n$zip_file = "${sp_dir}\Themes.zip"\n$download_uri = "https://github.com/morpheusthewhite/spicetify-themes/archive/refs/heads/master.zip"\nInvoke-WebRequest -Uri $download_uri -UseBasicParsing -OutFile $zip_file\nExpand-Archive -Path $zip_file -DestinationPath $sp_dir -Force\nRemove-Item -Path $zip_file\nRemove-Item -LiteralPath "${HOME}\spicetify-cli\Themes" -Force -Recurse\nRename-Item "${HOME}\spicetify-cli\spicetify-themes-master" "${HOME}\spicetify-cli\Themes"\nRemove-Item "${HOME}\spicetify-cli\Themes\*.*" -Force -Recurse | Where { ! $_.PSIsContainer }\nRename-Item "${HOME}\spicetify-cli\Themes\default" "${HOME}\spicetify-cli\Themes\SpicetifyDefault"']) 
    while True:
        if checkIfProcessRunning('powershell') == False:
            print(Fore.GREEN + "Finished Downloading Themes.")
            break

def UPDATE_CONFIG():
    print("placeholder")

def UPDATE_ADDONS():
    print("Downloading Themes.")
    terminateProgram('powershell')
    subprocess.Popen(["powershell",'$sp_dir = "${HOME}\spicetify-cli"\n$zip_file = "${sp_dir}\Themes.zip"\n$download_uri = "https://github.com/morpheusthewhite/spicetify-themes/archive/refs/heads/master.zip"\nInvoke-WebRequest -Uri $download_uri -UseBasicParsing -OutFile $zip_file\nExpand-Archive -Path $zip_file -DestinationPath $sp_dir -Force\nRemove-Item -Path $zip_file\nRemove-Item -LiteralPath "${HOME}\spicetify-cli\Themes" -Force -Recurse\nRename-Item "${HOME}\spicetify-cli\spicetify-themes-master" "${HOME}\spicetify-cli\Themes"\nRemove-Item "${HOME}\spicetify-cli\Themes\*.*" -Force -Recurse | Where { ! $_.PSIsContainer }\nRename-Item "${HOME}\spicetify-cli\Themes\default" "${HOME}\spicetify-cli\Themes\SpicetifyDefault"']) 
    while True:
        if checkIfProcessRunning('powershell') == False:
            print("Finished Downloading Themes.")
            break

def UNINSTALL():
    print("placeholder")

#START MENU
while True:
    try:
        print(Fore.MAGENTA + "\n[Startup]\n\n" + Fore.GREEN + ' -Install\n\n -Update Config\n\n -Download Latest Themes And Extensions\n\n -Uninstall\n' + Fore.MAGENTA)

        try:
            launch = int(input("Choose From The List Above (1-4): "))
        except:
            print(Fore.RESET)
            os.system("cls")
            print(Fore.RED + "[!] INVALID OPTION! Make Sure To Choose A (WHOLE) Number Corresponding To Your Choice [!]")
            continue

        print(Fore.RESET)
        os.system("cls")
 
        if launch == 1:
            INSTALL()
            print(Fore.MAGENTA)
            return_start = input("Return To Startup? Y/N: ")
            if return_start == "N" or return_start == "n" or return_start == "no" or return_start == "No" or return_start == "NO":
                break
            os.system("cls")
            
        elif launch == 2:
            UPDATE_CONFIG()
            break
        
        elif launch == 3:
            UPDATE_ADDONS()
            print(Fore.MAGENTA)
            return_start = input("Return To Startup? Y/N: ")
            if return_start == "N" or return_start == "n" or return_start == "no" or return_start == "No" or return_start == "NO":
                break
            os.system("cls")
        
        elif launch == 4:
            UNINSTALL()
            break

        else:
            print(Fore.RED + "[!] INVALID OPTION! Please Make Sure To Choose A Valid Option (1-4) [!]")
            
    except Exception as e:
        os.system("cls")
        print(Fore.RED + "[!]", e ,"[!]")
