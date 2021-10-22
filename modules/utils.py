import os
import subprocess
import time

import psutil
import requests
import requests.exceptions
from clint.textui import progress
from colorama import Fore, init

# >[Config Management]<

def replace_config_line(file_name, line_num, text): #replace_config_line("pathto\config.txt", 5, "new text") <- Example Usage | Last stage of set_config_entry.
    lines = open(file_name, 'r').readlines()
    lines[line_num] = text+"\n"
    with open(file_name, 'w') as out:
        out.writelines(lines)


def find_config_entry(entry, replacement=None):     #find_config_entry("extensions") <- Example usage | Optional var: "replacement" [Used for set_config_entry].

    config = os.path.expanduser("~") + "\.spicetify\config-xpui.ini"
    with open(config, "r") as file:
        count = 0
        for line in file:
            count += 1
            if entry in line:
                break

        if replacement != None:
            found_line_str = line
            found_line_int = count-1
            a, b = found_line_str.split(" = ")
            b = b.replace(b, replacement)
            final_write_data = (a+" = "+b)
            return(config, found_line_int, final_write_data)
        else:
            found_line_str = line.strip("\n")
            a, b = found_line_str.split(" = ")
            final_write_data = b
            return(final_write_data)


def set_config_entry(entry, replacement):           #set_config_entry("current_theme", "themename") <- Example Usage | Sets specific parts of the config.

    data = find_config_entry(entry, replacement)
    replace_config_line(data[0], data[1], data[2])


def list_config_available(selection):               #1=Themes, 2=Extensions, 3=Custom Apps <- Usage Options | Lists out available configurations.
    if is_installed() != True:
        return("Not Installed")
    if selection == 1:  # List Themes
        themes = os.listdir(os.path.expanduser(
            "~") + "\spicetify-cli\Themes")
        themes.remove("_Extra")
        return(themes)

    elif selection == 2:  # List Extensions
        return os.listdir(os.path.expanduser(
                "~") + "\spicetify-cli\Extensions")

    elif selection == 3:  # List Custom apps
        return os.listdir(os.path.expanduser(
                "~") + "\spicetify-cli\CustomApps")


# >[Bool Checkers]<

def is_installed():                                 #Checks if spicetify is installed
    return (
        os.path.exists(os.path.expanduser("~") + "\.spicetify\config-xpui.ini")
        == True
    )

def is_theme_set():                                 #Checks if a theme is set, made obsolete by find_config_entry
    config = os.path.expanduser("~") + "\.spicetify\config-xpui.ini"
    with open(config, "r") as file:
        for line in file:
            if "current_theme" in line:
                break
        found_line = line.rstrip('\n')
        a, b = found_line.split(" = ")
        if not b or b == "SpicetifyDefault":
            return(False)
        else:
            return(b)


# >[UI Management]<

def requests_progress(url, path):                   #requests_progress("urltodownload.com/download.zip", "%userprofile%/desktop") <- Example Usage | Adds a timer and bar to downloads.
    if os.path.isdir(path) == True:
        os.mkdir(path)

    r = requests.get(url, stream=True, headers={'Accept-Encoding': None})
    try:
        with open(path, "wb") as f:
            total_length = int((r.headers.get("content-length")))
            for chunk in progress.bar(
                r.iter_content(chunk_size=1024000),
                expected_size=round(total_length / 1024000),
            ):
                if chunk:
                    f.write(chunk)
                    f.flush()

    except (TypeError, ZeroDivisionError, AttributeError) as e:
        print(
            "[!]ERROR Loading ProgressBar. Attempting To Downloading Without It.[!]\n"+f"[!]{e}[!]")
        r = requests.get(url, stream=True)
        with open(path, "wb") as f:
            f.write(r.content)

    print(
        "\033[A                                                                \033[A")

# >[Process Management]<

def start_process(path):
    SW_HIDE = 0
    info = subprocess.STARTUPINFO()
    info.dwFlags = subprocess.STARTF_USESHOWWINDOW
    info.wShowWindow = SW_HIDE
    return subprocess.Popen(path, startupinfo=info)


def kill_processes(name):
    name = name.lower()
    for proc in psutil.process_iter():
        try:
            if proc.name().lower() == name:
                proc.kill()
        except Exception:
            time.sleep(0.25)


def process_running(name):
    name = name.lower()
    for proc in psutil.process_iter():
        try:
            if proc.name().lower() == name:
                return True
        except Exception:
            time.sleep(0.25)
    return False


def process_pid_running(pid):
    for proc in psutil.process_iter():
        try:
            if proc.pid == pid:
                return True
        except Exception:
            time.sleep(0.25)
    return False
