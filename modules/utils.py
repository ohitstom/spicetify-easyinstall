import asyncio
import os
import subprocess
import sys
from io import StringIO

import aiofiles
import aiohttp
import contextlib
import psutil
from aiohttp import ClientTimeout
from bs4 import UnicodeDammit

from modules import globals, logger, progress

# >[Config Management]<

def replace_config_line(file_name, line_num, text):  # replace_config_line("pathto\\config.txt", 5, "new text") <- Example Usage | Last stage of set_config_entry.
    '''
    Replace a line in a text file
    
    :param file_name: The path to the file you want to edit
    :param line_num: The line number you want to replace
    :param text: The text that you want to replace the line with
    '''
    lines = open(file_name, "r").readlines()
    lines[line_num] = f"{text}\n"
    with open(file_name, "w") as out:
        out.writelines(lines)


def find_config_entry(entry, replacement=None, config=None, encoding=None, splitchar=" = "):  # find_config_entry("extensions") <- Example usage | Optional var: "replacement" [Used for set_config_entry].
    '''
    Finds a config entry and returns the value of it
    
    :param entry: The entry you want to find
    :param replacement: If you want to change the value of a config entry, you can use this parameter
    :param config: The config file to be used
    :param json: If you want to use the json format, set this to True
    :return: a tuple of three values.
    '''
    if config is None:
        config = f"{globals.user_profile}\\.spicetify\\config-xpui.ini"

    elif not os.path.isfile(config):
        return "Path NULL"
    
    if encoding is None:
        with open(config, 'rb') as filetemp: #Sanity
            content = filetemp.read()
        encoding = UnicodeDammit(content).original_encoding

    with open(config, "r", encoding=encoding) as file:
        count = 0
        line = ""
        for line in file:
            count += 1
            if entry in line:
                break

        if replacement is not None:
            found_line_str = line
            found_line_int = count - 1
            a = found_line_str.split(splitchar)[0]

            final_write_data = f"{a} = {replacement}"
            return config, found_line_int, final_write_data

        else:
            found_line_str = line.strip("\n")
            a, b = found_line_str.split(splitchar)
            final_write_data = b
            return final_write_data


def set_config_entry(entry, replacement):  # set_config_entry("current_theme", "themename") <- Example Usage | Sets specific parts of the config. [replacement = None to empty the value]
    '''
    This function is used to set specific parts of the config.
    
    :param entry: The entry you want to change
    :param replacement: The value you want to replace the current value with
    '''
    data = find_config_entry(entry, replacement if replacement is not None else "")
    replace_config_line(data[0], data[1], data[2])


def list_config_available(selection, theme=None):    # selection: themes, colorschemes, extensions, custom_apps | Lists out available configurations.
    '''
    It lists out all the available configurations
    
    :param selection: themes, colorschemes, extensions, custom_apps
    :param theme: The theme you want to use
    :return: A list of available configurations.
    '''
    if not is_installed():
        raise Exception("Not Installed")

    if selection == "themes":  # List Themes
        themes = os.listdir(f"{globals.user_profile}\\spicetify-cli\\Themes")
        if "_Extra" in themes:
            themes.remove("_Extra")
        return themes

    elif selection == "colorschemes" and theme:  # List Color schemes
        colorschemes = []
        color_ini = f"{globals.user_profile}\\spicetify-cli\\Themes\\{theme}\\color.ini"
        if os.path.exists(color_ini):
            with open(color_ini) as f:
                colorschemes.extend(
                    line[1:-2]
                    for line in f.readlines()
                    if line[0] == "[" and line[-2] == "]"
                )

        return colorschemes

    elif selection == "extensions":  # List Extensions
        return os.listdir(f"{globals.user_profile}\\spicetify-cli\\Extensions")

    elif selection == "customapps":  # List Custom apps
        return os.listdir(f"{globals.user_profile}\\spicetify-cli\\CustomApps")

    else:
        raise Exception("Bad arguments")


# >[TUI Management]<


async def simultaneous_chunked_download(urls_paths, label):  # utils.simultaneous_chunked_download({globals.CUSTOM_THEMES}, "Custom Addons.zip")| Chunked download except for dictionaries of downloads.
    '''
    It downloads a bunch of files in parallel.
    
    :param urls_paths: A dictionary of URLs and paths to save the files to
    :param label: The label to display above the bar
    '''
    sys.stderr = StringIO()
    sem = asyncio.Semaphore(5)    
    timeout = ClientTimeout(total=60 * 60) #One hour timeout

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
        verbose_print(f"\n{url}\nPENDING")
        r = await aiohttp.ClientSession(connector=aiohttp.TCPConnector(verify_ssl=False), timeout=timeout).get(url)
        
        if not indeterminate:
            try:
                total_length += r.content_length
            except Exception:
                indeterminate = True
                
        tasks.append(_fetch(r, path))
        verbose_print("PASS\n")

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


async def chunked_download(url, path, label):  # chunked_download("urltodownload.com/download.zip", f"{userprofile}\\file.zip", "file.zip") <- Example Usage.
    '''
    It downloads a file in chunks.
    
    :param url: The url of the file you want to download
    :param path: The path to where the file will be downloaded
    :param label: The label of the bar
    '''
    asyncio.set_event_loop_policy(asyncio.WindowsSelectorEventLoopPolicy())
    timeout = ClientTimeout(total=60 * 60) #One hour timeout
    async with aiohttp.ClientSession(connector=aiohttp.TCPConnector(verify_ssl=False), timeout=timeout) as cs:
        async with cs.get(url, headers={"Accept-Encoding": "null"}) as r:
            async with aiofiles.open(path, "wb") as f:
                logger._pause_file_output = True
                for buffer in range(25):
                    try:
                        r = await cs.get(url)
                        total_length = int(r.headers.get("content-length"))
                        indeterminate = False
                    except Exception:
                        total_length = 0
                        indeterminate = True
                    if not indeterminate:
                        break

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
    '''
    If verbose is set, print the arguments and keyword arguments
    '''
    if globals.verbose:
        print(*args, **kwargs)


# >[Process Management]<

async def powershell(*args, verbose=None, wait=True, cwd=None, shell="powershell", **kwargs):
    '''
    It runs a powershell command and returns the process object.
    
    :param verbose: If True, print the output of the command
    :param wait: If True, wait for the process to finish. If False, return immediately, defaults to True
    (optional)
    :param cwd: The current working directory to run the command in
    :param shell: The shell to use, defaults to powershell (optional)
    :return: The return value is a Process object.
    '''
    if verbose is None:
        verbose = globals.verbose

    if cwd and os.path.isdir(cwd) is False:
        cwd = None

    proc = await asyncio.create_subprocess_exec(
        shell,
        *args,
        stdout=asyncio.subprocess.PIPE,
        stderr=asyncio.subprocess.STDOUT,
        creationflags=subprocess.CREATE_NO_WINDOW,
        **kwargs,
    )

    if wait:
        if verbose:
            # while proc.returncode is None:  # for some reason this can break...? sometimes after the process exits the loop continues and the pc fans spin up...
            while process_pid_running(proc.pid):
                line = str(await proc.stdout.readline(), encoding="utf-8")
                if line.strip() != "":
                    verbose_print(line, end="")
        else:
            await proc.wait()
    return proc


async def start_process(program, *args, silent=True):
    '''
    It starts a process in the background and hides the console window.
    
    :param program: The name of the program to run
    :param silent: If True, the process will be started with the `SW_HIDE` flag, defaults to True
    (optional)
    :return: The subprocess object.
    '''
    if not silent:
        return await asyncio.create_subprocess_exec(program, *args)

    info = subprocess.STARTUPINFO()
    info.dwFlags = subprocess.STARTF_USESHOWWINDOW
    info.wShowWindow = subprocess.SW_HIDE
    return await asyncio.create_subprocess_exec(program, *args, startupinfo=info)


def kill_processes(name):
    '''
    It kills all processes with the given name.
    
    :param name: The name of the process to kill
    '''
    name = name.lower()
    for proc in psutil.process_iter():
        with contextlib.suppress(Exception):
            if proc.name().lower() == name:
                proc.kill()


def process_running(name):    # Boolean operator for running application names.
    '''
    Check if a process is running by name
    
    :param name: The name of the process to look for
    :return: A boolean value.
    '''
    name = name.lower()
    for proc in psutil.process_iter():
        with contextlib.suppress(Exception):
            if proc.name().lower() == name:
                return True
    return False


def process_pid_running(pid): # Boolean operator for running pids.
    '''
    Check if a process is running by process id
    
    :param pid: The process ID you want to check
    :return: A boolean value.
    '''
    try:
        return psutil.pid_exists(pid)
    except Exception:
        return False


# >[Value Returns]<


async def latest_release_GET(): # Checks the latest release for a github repo.
    '''
    It gets the latest release from the github api.
    :return: The latest release of Spicetify-EasyInstall.
    '''
    async with aiohttp.ClientSession() as cs:
        async with cs.get(
            "https://api.github.com/repos/OhItsTom/Spicetify-EasyInstall/releases/latest"
        ) as r:
            json = await r.json()
            return json


def is_installed():  # Checks if spicetify is installed.
    '''
    Checks if spicetify is installed
    :return: A boolean value.
    '''
    return (
        os.path.exists(f"{globals.user_profile}\\.spicetify\\config-xpui.ini") is True)


async def heads_value(url): # Checks the heads of urls to see what branch is default.
    '''
    It returns the value of the Content-Disposition header.
    
    :param url: The URL of the repository
    :return: the value of the Content-Disposition header.
    '''
    async with aiohttp.ClientSession() as cs:
        async with cs.get(url + "main") as r:
            headers = r.headers.get("Content-Disposition")
            return "main" if headers else "master"
