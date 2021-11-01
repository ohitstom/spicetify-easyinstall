import os
import psutil
import asyncio
import aiohttp
import aiofiles
import subprocess

from modules import globals, logger, progress


# >[Config Management]<


def replace_config_line(
    file_name, line_num, text
):  # replace_config_line("pathto\\config.txt", 5, "new text") <- Example Usage | Last stage of set_config_entry.
    lines = open(file_name, "r").readlines()
    lines[line_num] = text + "\n"
    out = open(file_name, "w")
    out.writelines(lines)
    out.close()


def find_config_entry(
    entry, replacement=None
):  # find_config_entry("extensions") <- Example usage | Optional var: "replacement" [Used for set_config_entry].

    config = os.path.expanduser("~") + "\\.spicetify\\config-xpui.ini"
    with open(config, "r") as file:
        count = 0
        for line in file:
            count += 1
            if entry in line:
                break

        if replacement != None:
            found_line_str = line
            found_line_int = count - 1
            a = found_line_str.split(" = ")[0]
            final_write_data = a + " = " + replacement
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
    theme=None,
):  # selection: themes, colorschemes, extensions, custom_apps | Lists out available configurations.
    if is_installed():
        if selection == "themes":  # List Themes
            themes = os.listdir(os.path.expanduser("~") + "\\spicetify-cli\\Themes")
            themes.remove("_Extra")
            return themes

        elif selection == "colorschemes" and theme:  # List Color schemes
            colorschemes = []
            color_ini = (
                os.path.expanduser("~")
                + "\\spicetify-cli\\Themes\\"
                + theme
                + "\\color.ini"
            )
            if os.path.exists(color_ini):
                with open(color_ini) as f:
                    for line in f.readlines():
                        if line[0] == "[" and line[-2] == "]":
                            colorschemes.append(line[1:-2])
            return colorschemes

        elif selection == "extensions":  # List Extensions
            extensions = os.listdir(
                os.path.expanduser("~") + "\\spicetify-cli\\Extensions"
            )
            return extensions

        elif selection == "customapps":  # List Custom apps
            custom_apps = os.listdir(
                os.path.expanduser("~") + "\\spicetify-cli\\CustomApps"
            )
            return custom_apps

        else:
            raise Exception("Bad arguments")
    else:
        raise Exception("Not Installed")


# >[Bool Checkers]<


def is_installed():  # Checks if spicetify is installed
    if (
        os.path.exists(os.path.expanduser("~") + "\\.spicetify\\config-xpui.ini")
        == True
    ):
        return True
    else:
        return False


def is_theme_set():  # Checks if a theme is set, made obsolete by find_config_entry
    config = os.path.expanduser("~") + "\\.spicetify\\config-xpui.ini"
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
):  # chunked_download("urltodownload.com/download.zip", f"{userprofile}\\file.zip", "file.zip") <- Example Usage.
    async with aiohttp.ClientSession() as cs:
        async with cs.get(url, headers={"Accept-Encoding": "null"}) as r:
            async with aiofiles.open(path, "wb") as f:
                logger._pause_file_output = True
                try:
                    total_length = int(r.headers.get("content-length"))
                    indeterminate = False
                except Exception:
                    total_length = 0
                    indeterminate = True
                bar = progress.Bar(
                    expected_size=total_length,
                    indeterminate=indeterminate,
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
                        break
                logger._pause_file_output = False
                bar.done()


def verbose_print(*args, **kwargs):
    if globals.verbose:
        print(*args, **kwargs)


# >[Process Management]<


def start_process(path, silent=True):
    if silent:
        SW_HIDE = 0
        info = subprocess.STARTUPINFO()
        info.dwFlags = subprocess.STARTF_USESHOWWINDOW
        info.wShowWindow = SW_HIDE
        return subprocess.Popen(path, startupinfo=info)
    else:
        return subprocess.Popen(path)


async def powershell(cmd, verbose=None, wait=True):
    if verbose is None:
        verbose = globals.verbose
    if verbose:
        proc = subprocess.Popen(
            [
                "powershell",
                cmd,
            ],
            stdout=subprocess.PIPE,
            stderr=subprocess.STDOUT,
            creationflags=subprocess.CREATE_NO_WINDOW,
        )
        if wait:
            while True:
                line = str(proc.stdout.readline(), encoding="utf-8")
                if line.strip() != "":
                    verbose_print(line, end="")
                elif proc.poll() != None:
                    break
                globals.app.processEvents()
    else:
        proc = subprocess.Popen(
            [
                "powershell",
                cmd,
            ],
            creationflags=subprocess.CREATE_NO_WINDOW,
        )
        if wait:
            while process_pid_running(proc.pid):
                await asyncio.sleep(0.25)
    return proc


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
