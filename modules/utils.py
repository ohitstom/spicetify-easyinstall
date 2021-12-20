import asyncio
import os
import subprocess

import aiofiles
import aiohttp
import psutil

from modules import globals, logger, progress

# >[Config Management]<


def replace_config_line(
    file_name, line_num, text
):  # replace_config_line("pathto\\config.txt", 5, "new text") <- Example Usage | Last stage of set_config_entry.
    lines = open(file_name, "r").readlines()
    lines[line_num] = f"{text}\n"
    with open(file_name, "w") as out:
        out.writelines(lines)


def find_config_entry(
    entry, replacement=None
):  # find_config_entry("extensions") <- Example usage | Optional var: "replacement" [Used for set_config_entry].

    config = f"{globals.user_profile}\\.spicetify\\config-xpui.ini"
    with open(config, "r") as file:
        count = 0
        for line in file:
            count += 1
            if entry in line:
                break

        if replacement:
            found_line_str = line
            found_line_int = count - 1
            a = found_line_str.split(" = ")[0]
            final_write_data = f"{a} = {replacement}"     
            if replacement != "wipe":
                return (config, found_line_int, final_write_data)
            else:
                return(config, found_line_int, "")

        else:
            found_line_str = line.strip("\n")
            a, b = found_line_str.split(" = ")
            final_write_data = b
            return final_write_data


def set_config_entry(entry, replacement):  # set_config_entry("current_theme", "themename") <- Example Usage | Sets specific parts of the config. [replacement = "wipe" to empty line]

    data = find_config_entry(entry, replacement)
    replace_config_line(data[0], data[1], data[2])


def list_config_available(
    selection, theme=None
):  # selection: themes, colorschemes, extensions, custom_apps | Lists out available configurations.
    if not is_installed():
        raise Exception("Not Installed")
    if selection == "themes":  # List Themes
        themes = os.listdir(f"{globals.user_profile}\\spicetify-cli\\Themes")
        themes.remove("_Extra") if ("_Extra" in themes) == True else None
        return themes

    elif selection == "colorschemes" and theme:  # List Color schemes
        colorschemes = []
        color_ini = f"{globals.user_profile}\\spicetify-cli\\Themes\\{theme}\\color.ini"
        if os.path.exists(color_ini):
            with open(color_ini) as f:
                for line in f.readlines():
                    if line[0] == "[" and line[-2] == "]":
                        colorschemes.append(line[1:-2])
        return colorschemes

    elif selection == "extensions":  # List Extensions
        return os.listdir(f"{globals.user_profile}\\spicetify-cli\\Extensions")

    elif selection == "customapps":  # List Custom apps
        return os.listdir(f"{globals.user_profile}\\spicetify-cli\\CustomApps")

    else:
        raise Exception("Bad arguments")


# >[TUI Management]<


async def simultaneous_chunked_download(urls_paths, label):
    async with aiohttp.ClientSession() as cs:
        async def _fetch(r, path):
            async with sem:
                async with aiofiles.open(path, "wb") as f:
                    async for chunk in r.content.iter_any():
                        if not chunk:
                            break
                        size = await f.write(chunk)
                        if not indeterminate:
                            bar._done += size
                            bar.show(bar._done)
                    if indeterminate:
                        bar._done += 1
                        bar.show(bar._done)

        indeterminate = False
        total_length = 0
        tasks = []
        for url, path in urls_paths.items():
            r = await cs.get(url)
            if not indeterminate:
                try:
                    total_length += r.content_length
                except Exception:
                    indeterminate = True
            tasks.append(_fetch(r, path))

        sem = asyncio.Semaphore(5)
        if not indeterminate:
            bar = progress.Bar(
                expected_size=total_length, label=label, width=28, hide=False
            )
        else:
            bar = progress.Bar(
                expected_size=len(tasks), label=label, width=28, hide=False
            )

        logger._pause_file_output = True
        bar.show(0)
        bar._done = 0
        await asyncio.gather(*tasks)
        logger._pause_file_output = False
        bar.done()


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


def verbose_print(
    *args, **kwargs
):  # checks if verbose is set before printing args and kwargs
    if globals.verbose:
        print(*args, **kwargs)


# >[Process Management]<


async def powershell(
    cmd, verbose=None, wait=True, cwd=None, shell="powershell", **kwargs
):
    if verbose is None:
        verbose = globals.verbose

    if cwd and os.path.isdir(cwd) is False:
        cwd = None

    proc = subprocess.Popen(
        [
            shell,
            cmd,
        ],
        stdout=subprocess.PIPE,
        stderr=subprocess.STDOUT,
        creationflags=subprocess.CREATE_NO_WINDOW,
        **kwargs,
    )
    if wait:
        if verbose:
            while True:
                line = str(proc.stdout.readline(), encoding="utf-8")
                if line.strip() != "":
                    verbose_print(line, end="")
                elif proc.poll() != None:
                    break
                globals.app.processEvents()
        else:
            while process_pid_running(proc.pid):
                await asyncio.sleep(0.25)
    return proc


def start_process(path, silent=True):
    if not silent:
        return subprocess.Popen(path)

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


# >[Value Returns]<


async def spicetify_version():
    if is_installed():
        environ_check = (
            (f"{globals.user_profile}\spicetify-cli\spicetify.exe")
            if os.path.isdir(f"{globals.user_profile}\spicetify-cli")
            else ("spicetify")
        )
        return (
            str(
                (
                    await powershell(
                        "%s -v" % environ_check,
                        verbose=False,
                        wait=True,
                        start_new_session=False,
                    )
                ).stdout.read(),
                encoding="utf-8",
            ).strip()
            + ">>"
        )
    return ""


async def latest_release_GET():
    async with aiohttp.ClientSession() as cs:
        async with cs.get(
            "https://api.github.com/repos/OhItsTom/Spicetify-EasyInstall/releases/latest"
        ) as r:
            json = await r.json()
            return(json)

def is_installed():  # Checks if spicetify is installed
    return (
        os.path.exists(f"{globals.user_profile}\\.spicetify\\config-xpui.ini") == True
    )

async def heads_value(url):
    async with aiohttp.ClientSession() as cs:
        async with cs.get(url + "main") as r:
            headers = r.headers.get("Content-Disposition")
            if headers:
                return("main")
            else:
                return("master")

