import os
import psutil
import aiohttp
import aiofiles
import subprocess

from modules import globals, logger, progress


# >[Config Management]<


def replace_config_line(
    file_name, line_num, text
):  # replace_config_line("pathto\config.txt", 5, "new text") <- Example Usage | Last stage of set_config_entry.
    lines = open(file_name, "r").readlines()
    lines[line_num] = text + "\n"
    out = open(file_name, "w")
    out.writelines(lines)
    out.close()


def find_config_entry(
    entry, replacement=None
):  # find_config_entry("extensions") <- Example usage | Optional var: "replacement" [Used for set_config_entry].

    config = os.path.expanduser("~") + "\.spicetify\config-xpui.ini"
    with open(config, "r") as file:
        count = 0
        for line in file:
            count += 1
            if entry in line:
                break

        if replacement != None:
            found_line_str = line
            found_line_int = count - 1
            a, b = found_line_str.split(" = ")
            b = b.replace(b, replacement)
            final_write_data = a + " = " + b
            return (config, found_line_int, final_write_data)
        else:
            found_line_str = line.strip("\n")
            a, b = found_line_str.split(" = ")
            final_write_data = b
            return final_write_data


def set_config_entry(
    entry, replacement
):  # set_config_entry("current_theme", "themename") <- Example Usage | Sets specific parts of the config.

    data = find_config_entry(entry, replacement)
    replace_config_line(data[0], data[1], data[2])


def list_config_available(
    selection,
):  # 1=Themes, 2=Extensions, 3=Custom Apps <- Usage Options | Lists out available configurations.
    if is_installed() == True:
        if selection == 1:  # List Themes
            themes = os.listdir(os.path.expanduser("~") + "\spicetify-cli\Themes")
            themes.remove("_Extra")
            return themes

        elif selection == 2:  # List Extensions
            extensions = os.listdir(
                os.path.expanduser("~") + "\spicetify-cli\Extensions"
            )
            return extensions

        elif selection == 3:  # List Custom apps
            custom_apps = os.listdir(
                os.path.expanduser("~") + "\spicetify-cli\CustomApps"
            )
            return custom_apps
    else:
        return "Not Installed"


# >[Bool Checkers]<


def is_installed():  # Checks if spicetify is installed
    if os.path.exists(os.path.expanduser("~") + "\.spicetify\config-xpui.ini") == True:
        return True
    else:
        return False


def is_theme_set():  # Checks if a theme is set, made obsolete by find_config_entry
    config = os.path.expanduser("~") + "\.spicetify\config-xpui.ini"
    with open(config, "r") as file:
        for line in file:
            if "current_theme" in line:
                break
        found_line = line.rstrip("\n")
        a, b = found_line.split(" = ")
        if not b or b == "SpicetifyDefault":
            return False
        else:
            return b


# >[UI Management]<


async def chunked_download(
    url, path, label
):  # chunked_download("urltodownload.com/download.zip", "%userprofile%\\file.zip", "file.zip") <- Example Usage.
    async with aiohttp.ClientSession() as cs:
        async with cs.get(url, headers={"Accept-Encoding": "null"}) as r:
            async with aiofiles.open(path, "wb") as f:
                logger._pause_file_output = True
                total_length = int(r.headers.get("content-length"))
                bar = progress.Bar(
                    expected_size=total_length,
                    label=label,
                    width=28,
                    hide=False,
                )
                bar.show(0)
                done = 0
                async for chunk in r.content.iter_any():
                    if chunk:
                        done += await f.write(chunk)
                        bar.show(done)
                    else:
                        logger._pause_file_output = False
                        bar.done()
                        break


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
            pass


def process_running(name):
    name = name.lower()
    for proc in psutil.process_iter():
        try:
            if proc.name().lower() == name:
                return True
        except Exception:
            pass
    return False


def process_pid_running(pid):
    for proc in psutil.process_iter():
        try:
            if proc.pid == pid:
                return True
        except Exception:
            pass
    return False
