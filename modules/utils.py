import asyncio
import contextlib
import glob
import os
import random
import re
import subprocess
import sys
from io import StringIO
from pathlib import Path



from modules import globals, logger, progress
from modules.state_manager import state

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


def find_config_data(entry, replacement=None, config=f"{globals.spice_config}\\config-xpui.ini", splitchar=" = "):  # find_config_data("extensions") <- Example usage | Optional var: "replacement" [Used for set_config_entry].
    '''
    Finds a config entry and returns the data of it

    :param entry: The entry you want to find
    :param replacement: If you want to change the value of a config entry, you can use this parameter
    :param config: The config file to be used
    :return: a tuple of three values.
    '''
    if not os.path.isfile(config):
        return "config NULL"

    with open(config, "r") as file:
        count = 0
        line = ""
        for line in file:
            count += 1
            if entry in line:
                break
        if entry not in line:
            return None

    if replacement is not None:
        found_line_str = line
        found_line_int = count - 1
        a = found_line_str.split(splitchar, 1)[0]

        final_write_data = f"{a}{splitchar}{replacement}"
        return config, found_line_int, final_write_data

    else:
        found_line_str = line.strip("\n")
        a, b = found_line_str.split(splitchar, 1)
        final_write_data = b
        return final_write_data


def set_config_entry(entry, replacement, **kwargs):  # set_config_entry("current_theme", "themename") <- Example Usage | Sets specific parts of the config. [replacement = None to empty the value]
    '''
    This function is used to set specific parts of the config.

    :param entry: The entry you want to change
    :param replacement: The value you want to replace the current value with
    '''
    data = find_config_data(
        entry,
        replacement if replacement is not None else "", # statement important for wiping entries ("" is the equivelant to nothing)
        **kwargs,
    )
    replace_config_line(data[0], data[1], data[2])


def list_config_available(selection, theme=None):    # selection: themes, colorschemes, extensions, custom_apps
    '''
    It lists out all the available configurations

    :param selection: themes, colorschemes, extensions, custom_apps
    :param theme: The theme you want to use
    :return: A list of available configurations.
    '''
    if not is_installed():
        raise Exception("Not Installed")

    if selection == "themes":  # List Themes
        all_themes = sorted(os.listdir(f"{globals.spice_config}\\Themes") + os.listdir(f"{globals.spice_executable}\\Themes"))
        themes = []
        for t in all_themes:
            if t == "_Extra":
                continue
            if t not in themes:
                # Only include folder as a theme if it contains color.ini
                if os.path.exists(f"{globals.spice_config}\\Themes\\{t}\\color.ini") or os.path.exists(f"{globals.spice_executable}\\Themes\\{t}\\color.ini"):
                    themes.append(t)
        return themes

    elif selection == "colorschemes" and theme:  # List Color schemes
        colorschemes = []
        location = globals.spice_config if os.path.isdir(f"{globals.spice_config}\\Themes\\{theme}") else globals.spice_executable
        color_ini = f"{location}\\Themes\\{theme}\\color.ini"
        if os.path.exists(color_ini):
            with open(color_ini) as f:
                colorschemes.extend(
                    line[1:-2]
                    for line in f.readlines()
                    if line[0] == "[" and line[-2] == "]"
                )

        return colorschemes

    elif selection == "extensions":  # List Extensions
        extensions = sorted(os.listdir(f"{globals.spice_config}\\Extensions") + os.listdir(f"{globals.spice_executable}\\Extensions"))
        return extensions

    elif selection == "customapps":  # List Custom apps
        customapps = sorted(os.listdir(f"{globals.spice_config}\\CustomApps") + os.listdir(f"{globals.spice_executable}\\CustomApps"))
        return customapps

    else:
        raise Exception("Bad arguments")

# >[Config Tools]<

def theme_images(): # returns list of paths to screenshots
    img_list = []
    available = list_config_available("themes")
    identifiers = ["preview","screenshot","base", "dark"]
    for theme in available:
        imgs = list(Path(f"{globals.spice_config}\\Themes\\{theme}").glob(f"**/*.png")) + list(Path(f"{globals.spice_config}\\Themes\\{theme}").glob(f"**/*.jpg")) + list(Path(f"{globals.spice_executable}\\Themes\\{theme}").glob(f"**/*.png")) + list(Path(f"{globals.spice_executable}\\Themes\\{theme}").glob(f"**/*.jpg"))
        if not imgs:
            img_list.append(None)
            continue

        count = 0
        for i in range(len(imgs)):
            stem = imgs[i].stem
            if stem in identifiers:
                img_list.append(imgs[i])
                break
            else:
                count += 1
                if count == len(imgs):
                    img_list.append(imgs[count-1])
                    break
    return(img_list)

def colorscheme_average(theme): # returns list of 3 colors for each scheme in a dict
    # using var(theme) get the list_config_available("colorschemes", theme), then split up the themes color.ini by the list of colorschemes
    # then get the average color of each colorscheme lines 1-3 or something like that
    colorschemes = []
    available = list_config_available(selection="colorschemes", theme=theme)

def extension_descriptions(): # returns a list of extension descriptions
    descriptions = []
    available = list_config_available("extensions")
    for extension in available:
        if extension.lower()[:-3] in [x.lower() for x in list_config_available("themes")]:
            continue
        elif extension[:-3] in state.get_desc_cache():
            descriptions.append(state.get_desc_cache()[extension[:-3]])
        else:
            config = globals.spice_executable if os.path.isfile(f"{globals.spice_executable}\\Extensions\\{extension}") else globals.spice_config
            try:
                descriptions.append(str(find_config_data(entry="// DESCRIPTION", config=f"{config}\\Extensions\\{extension}", splitchar=": ")))
            except:
                descriptions.append(None)

    return descriptions


# >[TUI Management]<


async def simultaneous_chunked_download(urls_paths, label):  # utils.simultaneous_chunked_download({state.themes}, "Custom Addons.zip")| Chunked download except for dictionaries of downloads.
    '''
    Downloads a bunch of files in parallel.

    :param urls_paths: A dictionary of URLs and paths to save the files to
    :param label: The label to display above the bar
    '''
    import aiofiles
    import aiohttp
    from aiohttp import ClientTimeout
    sys.stderr = StringIO()
    sem = asyncio.Semaphore(5)
    timeout = ClientTimeout(total=60 * 60) #One hour timeout

    async def _fetch(session, url, path):
        async with sem:
            try:
                # If it's a local file path, just copy it instead of downloading
                if os.path.exists(url) or (len(url) > 1 and url[1] == ':'):
                    # Local path
                    verbose_print(f"Copying local addon from: {url}")
                    os.makedirs(os.path.dirname(path), exist_ok=True)
                    shutil.copy2(url, path)
                    if indeterminate:
                        bar._done += 1
                        bar.show(bar._done)
                    return

                async with session.get(url, headers={"User-Agent": "Mozilla/5.0"}) as r:
                    if r.status != 200:
                        verbose_print(f"Error downloading {url}: HTTP {r.status}")
                        raise Exception(f"HTTP Status {r.status}")
                    os.makedirs(os.path.dirname(path), exist_ok=True)
                    dl_size = 0
                    async with aiofiles.open(path, "wb") as f:
                        async for chunk in r.content.iter_any():
                            if not chunk:
                                break
                            size = await f.write(chunk)
                            dl_size += size
                            if not indeterminate:
                                bar._done += size
                                bar.show(bar._done)
                        if indeterminate:
                            bar._done += 1
                            bar.show(bar._done)
                    if dl_size < 22:
                        os.remove(path)
                        raise Exception(f"Downloaded file {url} is suspiciously small ({dl_size} bytes).")
            except Exception as e:
                verbose_print(f"Download exception for {url}: {e}")
                raise

    import shutil
    indeterminate = False
    total_length = 0
    resolved_urls = []

    async with aiohttp.ClientSession(connector=aiohttp.TCPConnector(verify_ssl=False), trust_env=True, timeout=timeout) as cs:
        # Check URLs/resolve lengths
        for url, path in urls_paths.items():
            verbose_print(f"{url}\nPENDING")
            if os.path.exists(url) or (len(url) > 1 and url[1] == ':'):
                # Local path
                total_length += os.path.getsize(url) if os.path.isfile(url) else 0
                resolved_urls.append((url, path))
                verbose_print("PASS (Local File)\n")
            else:
                try:
                    async with cs.head(url, headers={"User-Agent": "Mozilla/5.0"}, allow_redirects=True) as resp:
                        if resp.status == 200:
                            content_length = resp.headers.get("Content-Length")
                            if content_length:
                                total_length += int(content_length)
                            else:
                                indeterminate = True
                        else:
                            # Try GET headers if HEAD is not allowed
                            async with cs.get(url, headers={"User-Agent": "Mozilla/5.0"}) as get_resp:
                                if get_resp.status == 200:
                                    content_length = get_resp.headers.get("Content-Length")
                                    if content_length:
                                        total_length += int(content_length)
                                    else:
                                        indeterminate = True
                                else:
                                    indeterminate = True
                    resolved_urls.append((url, path))
                    verbose_print("PASS\n")
                except Exception as e:
                    verbose_print(f"Failed to resolve headers for {url}: {e}\n")
                    indeterminate = True
                    resolved_urls.append((url, path))

        if not resolved_urls:
            return

        if not indeterminate:
            bar = progress.Bar(
                expected_size=total_length, label=label, width=28, hide=False
            )
        else:
            bar = progress.Bar(
                expected_size=len(resolved_urls), label=label, width=28, hide=False
            )

        logger._pause_file_output = True
        bar.show(0)
        bar._done = 0
        tasks = [_fetch(cs, url, path) for url, path in resolved_urls]
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
    # If it's local, copy directly
    if os.path.exists(url) or (len(url) > 1 and url[1] == ':'):
        verbose_print(f"Copying local file from: {url}")
        os.makedirs(os.path.dirname(path), exist_ok=True)
        import shutil
        shutil.copy2(url, path)
        return

    import aiofiles
    import aiohttp
    from aiohttp import ClientTimeout
    asyncio.set_event_loop_policy(asyncio.WindowsSelectorEventLoopPolicy())
    timeout = ClientTimeout(total=60 * 60) #One hour timeout
    async with aiohttp.ClientSession(connector=aiohttp.TCPConnector(verify_ssl=False), trust_env=True, timeout=timeout) as cs:
        r = None
        for attempt in range(5):
            try:
                r = await cs.get(url, headers={"Accept-Encoding": "null", "User-Agent": "Mozilla/5.0"})
                if r.status == 200:
                    if "text/html" in r.headers.get("Content-Type", "").lower():
                        raise Exception("Received HTML instead of file (likely a Cloudflare block)")
                    break
                elif r.status in [429, 403]:
                    break # Don't retry if rate limited or forbidden
                else:
                    raise Exception(f"HTTP Status {r.status}")
            except Exception as e:
                if attempt == 0:
                    verbose_print(f"Download failed: {e} (URL: {url})")
                else:
                    verbose_print(f"Retrying... (Attempt {attempt+1}/5)")
            if attempt < 4:
                await asyncio.sleep(0.5)

        if not r or r.status != 200:
            if r and r.status in [429, 403]:
                raise PermissionError(f"HTTP {r.status}: Download server is rate-limiting your connection.")
            raise Exception(f"Failed to download from {url} after 5 attempts (Status {r.status if r else 'None'})")

        try:
            total_length = int(r.headers.get("content-length", 0))
            indeterminate = total_length == 0
        except Exception:
            total_length = 0
            indeterminate = True

        os.makedirs(os.path.dirname(path), exist_ok=True)
        async with aiofiles.open(path, "wb") as f:
            logger._pause_file_output = True
            bar = progress.Bar(
                expected_size=total_length,
                indeterminate=indeterminate,
                label=label,
                width=28,
                hide=False,
            )
            bar.show(0)
            done = 0
            for dl_attempt in range(3):
                try:
                    async for chunk in r.content.iter_any():
                        if chunk:
                            done += await f.write(chunk)
                            bar.show(done)
                        else:
                            break
                    break # Success
                except aiohttp.client_exceptions.ClientPayloadError:
                    if dl_attempt == 2:
                        raise # Give up after 3 tries
                    await asyncio.sleep(2)
                    verbose_print(f"Payload error on {url}, retrying chunk download...")
                    # Note: We aren't doing range requests, so we just restart the file.
                    await f.seek(0)
                    await f.truncate()
                    done = 0
            logger._pause_file_output = False
            if done < 22:
                bar.abort()
                raise Exception(f"Downloaded file is suspiciously small ({done} bytes). URL: {url}")
            bar.done()

def verbose_print(*args, **kwargs):
    '''
    If verbose is set, print the arguments and keyword arguments
    '''
    if globals.verbose:
        print(*args, **kwargs)


# >[Process Management]<

async def run_ps1_script(script_name, *args, verbose=None, wait=True, progress_label="Running Script...", **kwargs):
    '''
    Executes a powershell script from the resources/scripts/ directory.
    '''
    script_path = os.path.join(os.path.dirname(os.path.dirname(os.path.abspath(__file__))), "resources", "scripts", script_name)
    args_str = " ".join(f"'{str(a).replace(chr(39), chr(39)+chr(39))}'" for a in args)
    cmd = f"& '{script_path}' {args_str} *>&1"
    cmd_args = ["-ExecutionPolicy", "Bypass", "-Command", cmd]
    return await powershell(*cmd_args, verbose=verbose, wait=wait, progress_label=progress_label, **kwargs)

async def powershell(*args, verbose=None, wait=True, cwd=None, shell="powershell", progress_label="Running Script...", **kwargs):
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
        limit=10485760, # 10MB limit to prevent LimitOverrunError on massive base64 CSS outputs
        **kwargs,
    )

    if wait:
        captured_lines = []
        if verbose:
            while True:
                line = await proc.stdout.readline()
                if not line:
                    break
                line_str = str(line, encoding="utf-8", errors="replace")
                captured_lines.append(line_str)
                if line_str.strip() != "":
                    verbose_print(line_str, end="")
        else:
            logger._pause_file_output = True
            bar = progress.Bar(
                indeterminate=True, label=progress_label, width=28, hide=False
            )
            bar.show(0)
            ticks = 0
            while True:
                try:
                    line = await asyncio.wait_for(proc.stdout.readline(), timeout=0.1)
                    if not line:
                        break
                    captured_lines.append(str(line, encoding="utf-8", errors="replace"))
                except asyncio.TimeoutError:
                    pass
                ticks += 1
                bar.show(ticks)
            logger._pause_file_output = False
            bar.done()
        proc._captured_output = "".join(captured_lines)
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
    import psutil
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
    import psutil
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
    import psutil
    try:
        return psutil.pid_exists(pid)
    except Exception:
        return False


# >[Value Returns]<

async def latest_github_release(Spicetify=False): # Checks the latest release for a github repo.
    '''
    It gets the latest release from the github api.
    :return: The latest release of Spicetify-EasyInstall.
    '''
    import aiohttp
    url = "Spicetify/spicetify-cli" if Spicetify else "OhItsTom/Spicetify-EasyInstall"
    headers = {"User-Agent": "Spicetify-EasyInstall"}
    if state.github_token:
        headers["Authorization"] = f"token {state.github_token}"
    async with aiohttp.ClientSession(timeout=aiohttp.ClientTimeout(total=8)) as cs:
        async with cs.get(f"https://api.github.com/repos/{url}/releases/latest", headers=headers) as r:
            json = await r.json(content_type=None)
            return json


async def latest_github_commit(Spicetify=False):
    import aiohttp
    url = "spicetify/spicetify-cli" if Spicetify else "spicetify/spicetify-themes"
    branch = "main" if Spicetify else "master"
    headers = {"User-Agent": "Spicetify-EasyInstall"}
    if state.github_token:
        headers["Authorization"] = f"token {state.github_token}"
    async with aiohttp.ClientSession(timeout=aiohttp.ClientTimeout(total=8)) as cs:
        async with cs.get(f"https://api.github.com/repos/{url}/commits/{branch}", headers=headers) as r:
            json = await r.json(content_type=None)
            return json

async def latest_spotify_release(name=False): # Checks the latest release for the spotify app.
    import aiohttp
    import re
    async with aiohttp.ClientSession(headers={"User-Agent": "Mozilla/5.0"}) as cs:
        async with cs.get(f"https://www.spotify.com/us/opensource/") as r:
            body = await r.text()
            match = re.search(r'"clientVersion":"([^"]+)"', body)
            if match:
                version = match.group(1)
                if name:
                    return version
                else:
                    return version
    return "Not Found"


async def resolve_commit_by_date(repo, date_str):
    # Check cache first
    cache_key = f"{repo}:{date_str}"
    if cache_key in state.theme_commit_cache:
        return state.theme_commit_cache[cache_key]

    import aiohttp
    url = f"https://api.github.com/repos/{repo}/commits?until={date_str}T23:59:59Z&per_page=1"
    headers = {"User-Agent": "Spicetify-EasyInstall"}
    if state.github_token:
        headers["Authorization"] = f"token {state.github_token}"
    async with aiohttp.ClientSession(timeout=aiohttp.ClientTimeout(total=8)) as cs:
        async with cs.get(url, headers=headers) as r:
            if r.status == 200:
                json_data = await r.json(content_type=None)
                if json_data and isinstance(json_data, list) and len(json_data) > 0:
                    sha = json_data[0]["sha"]
                    state.theme_commit_cache[cache_key] = sha
                    try:
                        import json as json_lib
                        with open(globals.custom_addons_json_path, "r") as f:
                            saved = json_lib.load(f)
                        saved["theme_commit_cache"] = state.theme_commit_cache
                        with open(globals.custom_addons_json_path, "w") as f:
                            json_lib.dump(saved, f, indent=4)
                    except Exception:
                        pass
                    return sha
            raise Exception(f"Failed to resolve commit for {repo} by date {date_str} (status {r.status})")



def is_installed():  # Checks if spicetify is installed.
    '''
    Checks if spicetify is installed
    :return: A boolean value.
    '''
    return (
        os.path.exists(f"{globals.spice_config}\\config-xpui.ini") is True)


async def heads_value(url): # Checks the heads of urls to see if a github branch is the default.
    '''
    It returns the value of the Content-Disposition header.

    :param url: The URL of the repository
    :return: the value of the Content-Disposition header.
    '''
    if "marketplace" in url:
        return "dist"

    import aiohttp
    async with aiohttp.ClientSession(timeout=aiohttp.ClientTimeout(total=8)) as cs:
        async with cs.get(url + "main") as r:
            headers = r.headers.get("Content-Disposition")
            return "main" if headers else "master"

async def fetch_data_updates():
    """
    Downloads the latest recommended.json, spotify_presets.json, shipped_shas.json,
    and spicetify_dates.json from the 'data' branch and caches them in AppData.
    """
    import aiohttp
    import json
    import os
    from modules import globals

    cache_dir = os.path.join(globals.installer_config, "data")
    os.makedirs(cache_dir, exist_ok=True)

    base_url = "https://raw.githubusercontent.com/ohitstom/spicetify-easyinstall/data/"
    files = ["recommended.json", "spotify_presets.json", "shipped_shas.json", "spicetify_dates.json"]

    success = True
    try:
        async with aiohttp.ClientSession(headers={"User-Agent": "Spicetify-EasyInstall"}, timeout=aiohttp.ClientTimeout(total=5)) as session:
            for file in files:
                url = base_url + file + f"?t={random.randint(1, 999999)}"
                async with session.get(url) as resp:
                    if resp.status == 200:
                        data = await resp.json(content_type=None)
                        with open(os.path.join(cache_dir, file), "w", encoding="utf-8") as f:
                            json.dump(data, f, indent=4)
                    else:
                        success = False
    except Exception as e:
        verbose_print(f"Failed to fetch data updates: {e}")
        success = False

    if success:
        verbose_print("Successfully updated offline data cache from GitHub.")
        # Reload all globals dictionaries from newly cached AppData
        globals.RECOMMENDED = globals._load_json("recommended.json")
        globals.SPOTIFY_PRESETS = globals._load_json("spotify_presets.json")
        globals.SPICETIFY_DATES = globals._load_json("spicetify_dates.json")
        globals.SHIPPED_SHAS = globals._load_json("shipped_shas.json")

        # Recalculate dynamic version variables based on current RELEASE mapping
        if globals.RELEASE in globals.RECOMMENDED:
            globals.SPICETIFY_VERSION = globals.RECOMMENDED[globals.RELEASE].get("spicetify", globals.SPICETIFY_VERSION)
            globals.SPOTIFY_VERSION = globals.RECOMMENDED[globals.RELEASE].get("spotify", globals.SPOTIFY_VERSION)

        _themes_sha = globals.SHIPPED_SHAS.get(globals.SPICETIFY_VERSION, {}).get("themes", "c6e82dfeaa46ee9060d0c02fc437989eb77f6c61")
        _addons_sha = globals.SHIPPED_SHAS.get(globals.SPICETIFY_VERSION, {}).get("cli", "b26a60e41dd4296ba337b58f68ec2b1de2b422cf")
        globals.THEMES_URL = f"https://codeload.github.com/spicetify/spicetify-themes/zip/{_themes_sha}"
        globals.ADDONS_URL = f"https://codeload.github.com/spicetify/spicetify-cli/zip/{_addons_sha}"
        globals.THEMES_VERSION = f"spicetify-themes-{_themes_sha}"
        globals.ADDONS_VERSION = f"spicetify-cli-{_addons_sha}"

    return success

async def fetch_spotify_manifest():
    import aiohttp
    import json
    import os
    from modules import globals
    from modules.state_manager import state

    manifest = None
    cache_file = os.path.join(globals.installer_config, "spotify_versions_cache.json")

    try:
        async with aiohttp.ClientSession(headers={"User-Agent": "Spicetify-EasyInstall"}, timeout=aiohttp.ClientTimeout(total=8)) as session:
            async with session.get("https://loadspot.pages.dev/versions.json") as resp:
                if resp.status == 200:
                    manifest = await resp.json(content_type=None)
                    try:
                        os.makedirs(os.path.dirname(cache_file), exist_ok=True)
                        with open(cache_file, "w") as f:
                            json.dump(manifest, f)
                    except Exception:
                        pass
    except Exception:
        pass

    if not manifest:
        try:
            if os.path.exists(cache_file):
                with open(cache_file, "r") as f:
                    manifest = json.load(f)
        except Exception:
            pass

    return manifest

async def fetch_archive_mirror_url(version_filename):
    """
    Given a version filename like 'spotify_installer-1.2.92.148.g882cc571-x64.exe',
    fetches the directory listing from Jetfire's Archive.org mirror and finds
    the exact available file (since build IDs might differ, e.g. -26.exe instead of -x64.exe).
    Returns the direct download URL if found, or None.
    """
    if "spotify_installer-" not in version_filename:
        return None

    base_ver = version_filename.replace("spotify_installer-", "").replace("-x64.exe", "")
    base_ver = base_ver.rsplit("-", 1)[0] if "-" in base_ver else base_ver # Strip any existing build suffix

    search_prefix = f"spotify_installer-{base_ver}"
    archive_url = "https://archive.org/download/spotify-installer-museum/windows/x86_64/exe/"

    import aiohttp
    import re

    try:
        async with aiohttp.ClientSession(timeout=aiohttp.ClientTimeout(total=20)) as session:
            headers = {"User-Agent": "Spicetify-EasyInstall"}
            async with session.get(archive_url, headers=headers) as resp:
                if resp.status == 200:
                    html = await resp.text()
                    links = re.findall(r'href=[\'\"]?([^\'\" >]+)', html)
                    for link in links:
                        if search_prefix in link and link.endswith(".exe"):
                            verbose_print(f"Archive mirror found: {archive_url + link}")
                            return archive_url + link
                else:
                    verbose_print(f"Archive mirror returned status {resp.status}")
    except Exception as e:
        verbose_print(f"Archive mirror fetch failed: {e}")
    return None
