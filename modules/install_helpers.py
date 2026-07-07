import asyncio
import os
import shutil
import re

from modules import globals, utils, gui
from modules.state_manager import state
from pathlib import Path

environ_check = f'& "{globals.spice_executable}\\spicetify.exe"'

async def prepare_variables(spicetify_version, spotify_version, pin_date, themes_version, needs_prep):
    filenames = []
    if needs_prep:
        try:
            if pin_date:
                if spicetify_version in globals.SHIPPED_SHAS:
                    shas = globals.SHIPPED_SHAS[spicetify_version]
                    addon_sha = shas["cli"]
                    default_theme_sha = globals.SHIPPED_SHAS.get(globals.SPICETIFY_VERSION, {}).get("themes", "c6e82dfeaa46ee9060d0c02fc437989eb77f6c61")
                    if themes_version == "Latest" or themes_version == shas.get("default_theme_ver", "Latest") or themes_version == default_theme_sha[:7]:
                        theme_sha = shas["themes"]
                    else:
                        theme_sha = themes_version
                else:
                    theme_sha = await utils.resolve_commit_by_date("spicetify/spicetify-themes", pin_date)
                    addon_sha = await utils.resolve_commit_by_date("spicetify/spicetify-cli", pin_date)

                if spicetify_version == "Latest":
                    state.runtime_spicetify_version = list(globals.SHIPPED_SHAS.keys())[0]
                else:
                    state.runtime_spicetify_version = spicetify_version

                if themes_version != "Latest":
                    theme_sha = themes_version

                state.runtime_themes_version = f"spicetify-themes-{theme_sha}"
                state.runtime_addons_version = f"spicetify-cli-{addon_sha}"
                state.runtime_themes_url = f"https://codeload.github.com/spicetify/spicetify-themes/zip/{theme_sha}"
                state.runtime_addons_url = f"https://codeload.github.com/spicetify/spicetify-cli/zip/{addon_sha}"
            else:
                if spicetify_version == "Latest":
                    latest_tag = list(globals.SHIPPED_SHAS.keys())[0]
                    state.runtime_spicetify_version = latest_tag

                    theme_sha = globals.SHIPPED_SHAS[latest_tag]["themes"]
                    if themes_version != "Latest":
                        theme_sha = themes_version

                    addon_sha = globals.SHIPPED_SHAS[latest_tag]["cli"]
                    state.runtime_themes_version = f"spicetify-themes-{theme_sha}"
                    state.runtime_addons_version = f"spicetify-cli-{addon_sha}"
                    state.runtime_themes_url = f"https://codeload.github.com/spicetify/spicetify-themes/zip/{theme_sha}"
                    state.runtime_addons_url = f"https://codeload.github.com/spicetify/spicetify-cli/zip/{addon_sha}"
                else:
                    state.runtime_spicetify_version = spicetify_version
                    if themes_version != "Latest":
                        theme_sha = themes_version
                    elif state.runtime_themes_version:
                        theme_sha = state.runtime_themes_version.replace("spicetify-themes-", "")
                    else:
                        # Fallback to shipped theme SHA for this spicetify version
                        shipped = globals.SHIPPED_SHAS.get(spicetify_version, {})
                        default_theme_sha = globals.SHIPPED_SHAS.get(globals.SPICETIFY_VERSION, {}).get("themes", "c6e82dfeaa46ee9060d0c02fc437989eb77f6c61")
                        theme_sha = shipped.get("themes", default_theme_sha)
                    state.runtime_themes_version = f"spicetify-themes-{theme_sha}"
                    state.runtime_themes_url = f"https://codeload.github.com/spicetify/spicetify-themes/zip/{theme_sha}"
                    # Also set addons using shipped SHA for this spicetify version
                    shipped = globals.SHIPPED_SHAS.get(spicetify_version, {})
                    default_addon_sha = globals.SHIPPED_SHAS.get(globals.SPICETIFY_VERSION, {}).get("cli", "b26a60e41dd4296ba337b58f68ec2b1de2b422cf")
                    addon_sha = shipped.get("cli", default_addon_sha)
                    state.runtime_addons_version = f"spicetify-cli-{addon_sha}"
                    state.runtime_addons_url = f"https://codeload.github.com/spicetify/spicetify-cli/zip/{addon_sha}"

            if spotify_version == "Latest":
                state.runtime_spotify_version = "SpotifySetup.exe"
                state.runtime_spotify_url = "https://download.scdn.co/SpotifySetup.exe"
                filenames = [state.runtime_spotify_version]
            else:
                clean_ver = spotify_version.split(" ")[0]
                preset_val = None
                for k, v in globals.SPOTIFY_PRESETS.items():
                    if k.startswith(clean_ver) or clean_ver.startswith(k.split(" ")[0]):
                        preset_val = v
                        break

                if isinstance(preset_val, dict):
                    base_ver = preset_val.get("version", clean_ver)
                    import platform
                    from modules import globals
                    machine = globals.DEBUG_ARCH.lower() if globals.DEBUG_ARCH else platform.machine().lower()
                    is_x86 = "x86" in machine and not "64" in machine
                    is_arm64 = "arm" in machine or "aarch64" in machine
                    if is_x86:
                        filename = f"spotify_installer-{base_ver}-x86.exe"
                        state.runtime_spotify_url = preset_val.get("loadspot_url_x86", f"https://loadspot.amd64fox1.workers.dev/download/{filename}")
                        state.runtime_archive_url = preset_val.get("archive_url_x86")
                    elif is_arm64:
                        filename = f"spotify_installer-{base_ver}-arm64.exe"
                        state.runtime_spotify_url = preset_val.get("loadspot_url_arm64", f"https://loadspot.amd64fox1.workers.dev/download/{filename}")
                        state.runtime_archive_url = preset_val.get("archive_url_arm64")
                    else:
                        filename = f"spotify_installer-{base_ver}-x64.exe"
                        state.runtime_spotify_url = preset_val.get("loadspot_url", f"https://loadspot.amd64fox1.workers.dev/download/{filename}")
                        state.runtime_archive_url = preset_val.get("archive_url")
                    state.runtime_spotify_version = filename
                    filenames = [filename]
                else:
                    # Fallback for non-dictionary (old format or missing)
                    full_ver = preset_val if preset_val else spotify_version
                    if "-" in full_ver:
                        base_ver = full_ver.rsplit("-", 1)[0]
                    else:
                        base_ver = full_ver
                    import platform
                    machine = platform.machine().lower()
                    is_x86 = "x86" in machine and not "64" in machine
                    is_arm64 = "arm" in machine or "aarch64" in machine
                    if is_x86:
                        arch_tag = "x86"
                    elif is_arm64:
                        arch_tag = "arm64"
                    else:
                        arch_tag = "x64"
                    filename = f"spotify_installer-{base_ver}-{arch_tag}.exe"
                    state.runtime_spotify_version = filename
                    state.runtime_spotify_url = f"https://loadspot.amd64fox1.workers.dev/download/{filename}"
                    filenames = [filename]
        except Exception as e:
            print(f"Exception in prepare_variables: {e}")
            return None

    return filenames

def backup_credentials():
    if os.path.isdir(f"{globals.appdata}\\Spotify\\Users") and os.path.isfile(f"{globals.appdata}\\Spotify\\prefs"):
        if os.path.isdir(f"{globals.installer_config}\\backup"):
            shutil.rmtree(f"{globals.installer_config}\\backup")
        os.makedirs(f"{globals.installer_config}\\backup", exist_ok=True)
        shutil.move(f"{globals.appdata}\\Spotify\\Users", f"{globals.installer_config}\\backup\\Users")
        shutil.move(f"{globals.appdata}\\Spotify\\prefs", f"{globals.installer_config}\\backup")
        return True
    return False

async def uninstall_spotify():
    process = await utils.powershell('Get-AppxPackage SpotifyAB.SpotifyMusic', wait=True, verbose=False)
    winstore_spotify = getattr(process, '_captured_output', '').strip()

    if 'Version' in winstore_spotify:
        await utils.powershell('Get-AppxPackage SpotifyAB.SpotifyMusic | Remove-AppxPackage', wait=True, progress_label="Removing MS Store Spotify...")
    elif os.path.isdir(f"{globals.appdata}\\Spotify"):
        import subprocess
        for img in ["spotify.exe", "spotifyhelper.exe", "spotifywebhelper.exe", "spicetify.exe"]:
            subprocess.run(f"taskkill /f /im {img} /t", shell=True, creationflags=subprocess.CREATE_NO_WINDOW)
            utils.kill_processes(img)

        spotify_exe = f"{globals.appdata}\\Spotify\\Spotify.exe"
        uninstaller = f"{globals.appdata}\\Spotify\\uninstall.exe"
        if os.path.isfile(spotify_exe):
            uninstall_proc = await utils.start_process(spotify_exe, "/uninstall", "/silent")
            try:
                await asyncio.wait_for(uninstall_proc.wait(), timeout=10.0)
            except asyncio.TimeoutError:
                for img in ["spotify.exe", "spotifyhelper.exe", "spotifywebhelper.exe"]:
                    subprocess.run(f"taskkill /f /im {img} /t", shell=True, creationflags=subprocess.CREATE_NO_WINDOW)
                    utils.kill_processes(img)
        elif os.path.isfile(uninstaller):
            uninstall_proc = await utils.start_process(uninstaller, "/uninstall", "/silent")
            try:
                await asyncio.wait_for(uninstall_proc.wait(), timeout=10.0)
            except asyncio.TimeoutError:
                for img in ["spotify.exe", "spotifyhelper.exe", "spotifywebhelper.exe"]:
                    subprocess.run(f"taskkill /f /im {img} /t", shell=True, creationflags=subprocess.CREATE_NO_WINDOW)
                    utils.kill_processes(img)
        else:
            try:
                await asyncio.wait_for(
                    utils.run_ps1_script("force_uninstall_spotify.ps1", verbose=False, progress_label="Uninstalling Spotify..."),
                    timeout=10.0
                )
            except asyncio.TimeoutError:
                pass
    else:
        return False
    return True

def wipe_folders(leaveSpotify):
    folders = [
        globals.spice_config,
        globals.spice_executable,
        f"{globals.appdata}\\spotify",
        f"{globals.appdata_local}\\spotify"
    ] if not leaveSpotify else [
        globals.spice_config,
        globals.spice_executable,
        globals.temp
    ]
    for folder in folders:
        try:
            if not os.path.exists(folder) or len(os.listdir(folder)) == 0:
                utils.verbose_print(f'"{folder}" is already empty.')
            else:
                shutil.rmtree(folder, ignore_errors=True)
                utils.verbose_print(f'"{folder}" has been deleted.')
        except Exception as e:
            utils.verbose_print(f'"{folder}" was not deleted: {e}.')

def is_valid_exe(file_path):
    if os.path.isfile(file_path) and os.path.getsize(file_path) > 60000000:
        try:
            with open(file_path, "rb") as f:
                return f.read(2).startswith(b'MZ')
        except Exception:
            pass
    return False

async def download_spotify(filenames):
    import sys
    exec_dir = os.path.dirname(os.path.abspath(sys.argv[0]))

    if not filenames:
        filenames = [state.runtime_spotify_version]

    local_found = False
    temp_dest = os.path.join(globals.temp, state.runtime_spotify_version)

    for f_name in filenames:
        local_src = os.path.join(exec_dir, f_name)
        t_dest = os.path.join(globals.temp, f_name)
        if is_valid_exe(local_src):
            shutil.copy2(local_src, t_dest)
            state.runtime_spotify_version = f_name
            temp_dest = t_dest
            local_found = True
            break
        elif is_valid_exe(t_dest):
            state.runtime_spotify_version = f_name
            temp_dest = t_dest
            local_found = True
            break

    if local_found:
        return temp_dest, True

    url = state.runtime_spotify_url
    curr_filename = state.runtime_spotify_version
    curr_temp_dest = os.path.join(globals.temp, curr_filename)

    try:
        if os.path.exists(curr_temp_dest):
            os.remove(curr_temp_dest)
        utils.verbose_print(f"Starting primary download from: {url}")
        await utils.chunked_download(
            url=url,
            path=curr_temp_dest,
            label=f"{curr_filename[:10]}...exe",
        )
        if not is_valid_exe(curr_temp_dest):
            if getattr(utils.logger, '_pause_file_output', False):
                sys.stdout.write("\033[F\033[K\r")
                sys.stdout.flush()
            raise ValueError("Downloaded file is not a valid executable.")
        else:
            return curr_temp_dest, False
    except Exception:
        # Primary endpoint failed (e.g. 429 Rate Limited or 403 Forbidden).
        # Initiate fallback to the Archive.org mirror
        try:
            utils.verbose_print("Primary download failed. Attempting fallback mirror...")
            mirror_url = state.runtime_archive_url
            if not mirror_url:
                mirror_url = await utils.fetch_archive_mirror_url(curr_filename)

            if mirror_url:
                if os.path.exists(curr_temp_dest):
                    os.remove(curr_temp_dest)
                utils.verbose_print(f"Primary failed. Starting fallback mirror download from: {mirror_url}")
                await utils.chunked_download(
                    url=mirror_url,
                    path=curr_temp_dest,
                    label="[Mirror] " + (curr_temp_dest if globals.verbose else curr_filename),
                )
                if is_valid_exe(curr_temp_dest):
                    return curr_temp_dest, False
        except Exception as mirror_e:
            raise PermissionError(f"SpotX rate limit hit, and Archive mirror also failed ({mirror_e}). Please wait an hour or manually download {curr_filename} from {url} or {mirror_url} and place it in the Temp folder.")

    # If both primary and fallback fail, raise the manual download error.
    raise PermissionError(f"SpotX rate limit hit: Please wait an hour or manually download {curr_filename} from {url} and place it in the Temp folder.")

async def install_spotify_exe(temp_dest):
    utils.kill_processes("Spotify.exe")
    spotify_install_pid = (
        await utils.start_process(
            temp_dest,
            silent=True
        )
    ).pid

    while utils.process_pid_running(spotify_install_pid):
        await asyncio.sleep(0.25)
    i = 0
    while not globals.spotify_prefs.is_file():
        i += 1
        if i > 40:
            raise FileNotFoundError(
                "Spotify preferences were not created, something went wrong installing."
            )
        await asyncio.sleep(0.25)

    utils.kill_processes("Spotify.exe")
    os.remove(temp_dest)


async def install_spicetify():


    # >[Section 6]<
    # The code below will install Spicetify and do error checking.

    os.makedirs(globals.spice_config, exist_ok=True)
    os.makedirs(globals.spice_executable, exist_ok=True)
    local_install_ps1 = f"{globals.temp}\\install.ps1"
    os.makedirs(globals.temp, exist_ok=True)

    try:
        await utils.chunked_download(
            url="https://raw.githubusercontent.com/spicetify/spicetify-cli/master/install.ps1",
            path=local_install_ps1,
            label="install.ps1",
        )
        with open(local_install_ps1, "r", encoding="utf-8") as f:
            ps1_content = f.read()

        # Bypass interactive prompts (admin and marketplace choices)
        ps1_content = re.sub(
            r'\$choice\s*=\s*\$Host\.UI\.PromptForChoice\([^)]*abort[^)]*\)',
            '$choice = 1',
            ps1_content,
            flags=re.IGNORECASE | re.DOTALL
        )
        ps1_content = re.sub(
            r'\$choice\s*=\s*\$Host\.UI\.PromptForChoice\([^)]*Marketplace[^)]*\)',
            '$choice = 1',
            ps1_content,
            flags=re.IGNORECASE | re.DOTALL
        )
        with open(local_install_ps1, "w", encoding="utf-8") as f:
            f.write(ps1_content)

        await utils.run_ps1_script(
            "install_spicetify_local.ps1",
            state.runtime_spicetify_version,
            local_install_ps1,
            progress_label="Installing Spicetify..."
        )
    except Exception as e:
        utils.verbose_print(f"Failed to run modified installer: {e}. Falling back to original installer...")
        await utils.run_ps1_script(
            "install_spicetify_web.ps1",
            state.runtime_spicetify_version,
            progress_label="Installing Spicetify..."
        )

    await utils.powershell(f'{environ_check}', progress_label="Checking Env.")

    if os.path.isfile(f"{globals.spice_config}\\config-xpui.ini"):
        prefs_check = utils.find_config_data("prefs_path")
        if not prefs_check:
            utils.set_config_entry("prefs_path", f'{globals.appdata}\\Spotify\\prefs')
    else:
        print("Config wasnt created, Spicetify might not have installed correctly. Please retry with verbose if it doesnt work.")

    # Launch Spotify briefly to generate the offline.bnk cache file, preventing the Spicetify offline.bnk error
    await utils.start_process(f"{globals.appdata}\\Spotify\\Spotify.exe", silent=True)
    import progress
    with progress.Bar(label="Generating Cache.", expected_size=40, hide=getattr(utils.logger, 'verbose', False)) as bar:
        for i in range(40):
            await asyncio.sleep(0.1)
            bar.show(i + 1)
    utils.kill_processes("Spotify.exe")

    await utils.run_ps1_script(
        "configure_spicetify.ps1",
        f"{globals.spice_executable}\\spicetify.exe",
        progress_label="Configuring Spicetify..."
    )
    print("Finished installing Spicetify!")

async def prevent_spotify_updates():


    # >[Section 7]<
    # The code below will remove Spotifys ability to update.

    utils.kill_processes("Spotify.exe")
    if not os.path.isdir(f"{globals.appdata_local}\\Spotify\\Update"):
        os.mkdir(f"{globals.appdata_local}\\Spotify\\Update")

    await utils.run_ps1_script("prevent_spotify_updates.ps1", progress_label="Blocking SpotUpdates...")

async def download_official_themes():


    # >[Section 8]<
    # The code below will download spicetify-cli themes.

    os.makedirs(globals.spice_config, exist_ok=True)
    await utils.chunked_download(
        url=state.runtime_themes_url,
        path=(f"{globals.spice_config}\\Themes.zip"),
        label=(f"{globals.spice_config}\\Themes.zip")
        if state.verbose
        else "Themes.zip",
    )

    shutil.rmtree(f"{globals.spice_config}\\Themes", ignore_errors=True)
    shutil.unpack_archive(f"{globals.spice_config}\\Themes.zip", globals.spice_config)
    os.remove(f"{globals.spice_config}\\Themes.zip")

    unpacked_themes_dir = None
    for name in os.listdir(globals.spice_config):
        if name.startswith("spicetify-themes-") and os.path.isdir(f"{globals.spice_config}\\{name}"):
            unpacked_themes_dir = name
            break
    if unpacked_themes_dir:
        os.rename(f"{globals.spice_config}\\{unpacked_themes_dir}", f"{globals.spice_config}\\Themes")
    else:
        raise Exception("Failed to locate extracted themes folder.")

    for item in list(Path(f"{globals.spice_config}\\Themes").glob("*")):
        fullpath = str(item)
        if os.path.isdir(fullpath):
            filename = str(item.name)
            if filename[0] == ".":
                shutil.rmtree(fullpath)
        else:
            os.remove(fullpath)

    os.rename(f"{globals.spice_config}\\Themes\\Default", f"{globals.spice_config}\\Themes\\SpicetifyDefault")

    for item in list(Path(f"{globals.spice_config}\\Themes").glob("**/*.js")):
        fullpath = str(item)
        if re.search(r'theme(?:\.|\.js)', fullpath):
            continue
        destpath = (f"{globals.spice_config}\\Extensions"
        + fullpath[fullpath.rfind('\\') : fullpath.rfind('.')]
        + ".js"
        )
        if os.path.exists(destpath):
            os.remove(destpath)
        shutil.move(fullpath, destpath)
async def download_custom_addons():


    # >[Section 9]<
    # The code below will download a list of custom Spicetify addons, declared in globals.py.

    for download in {**state.themes, **state.apps, **state.extensions}.values():
        os.makedirs(os.path.dirname(download), exist_ok=True)
    await utils.simultaneous_chunked_download(
        {
            **state.themes,
            **state.apps,
            **state.extensions

         }, "Custom Addons.zip")

    for url, download in ({**state.themes, **state.apps, **state.extensions}).items():
        if os.path.exists(download):
            captured = Path(download)
            directory = captured.parent

            global unpacked_name
            unpacked_name = captured.with_suffix("").name
            unpacked_path = f"{directory}\\{unpacked_name}"
            utils.verbose_print(f"{unpacked_name} was downloaded successfully!")

            if os.path.exists(unpacked_path):
                shutil.rmtree(unpacked_path)

            shutil.unpack_archive(download, unpacked_path)
            os.remove(download)

            # Unzipped download dupe folder removal + Extension extraction + cleanup
            for item in os.listdir(unpacked_path):
                # Moving all files/folders from ./extractedzip/duplicate-extracted-zip to just ./extractedzip
                for src in Path(f"{unpacked_path}\\{item}").glob("*"): # for files and folders in {PARENT}\{ADDON-DUPE}\{ACTUAL-ADDON}.glob(*) - * meanys any non zero file
                    shutil.move(str(src), str(unpacked_path))
                if os.path.exists(f"{unpacked_path}\\{item}") and os.path.isdir(f"{unpacked_path}\\{item}"): # Cleanup
                    os.rmdir(f"{unpacked_path}\\{item}")

                # Moving all files with the js extension to {extensions}
                for src in Path(f"{unpacked_path}").glob("**/*.js"): # for files in {PARENT}\{ADDON-DUPE}\**\*.js where ** means any segment, null or otherwise.
                    if "Extensions" in str(src):
                        shutil.move(str(src), str(directory))
                if os.path.exists(unpacked_path) and os.path.isdir(unpacked_path) and "Extensions" in unpacked_path: # Cleanup
                    shutil.rmtree(unpacked_path)

                # Recovering Repos with > 1 theme (or nested theme folder)
                if not os.path.exists(f"{unpacked_path}\\user.css") and "Themes" in unpacked_path:
                    # Find all directories that contain color.ini (defining a theme)
                    theme_dirs = []
                    for root_walk, dirs_walk, files_walk in os.walk(unpacked_path):
                        if "color.ini" in files_walk:
                            theme_dirs.append(Path(root_walk))

                    # Find all images in the unpacked_path that are outside of theme directories
                    outside_imgs = []
                    for root_walk, dirs_walk, files_walk in os.walk(unpacked_path):
                        rpath = Path(root_walk)
                        if any(rpath == td or td in rpath.parents for td in theme_dirs):
                            continue
                        for file in files_walk:
                            if file.lower().endswith(('.png', '.jpg', '.jpeg', '.gif')):
                                outside_imgs.append(rpath / file)

                    # Move actual theme directories to Themes/
                    for td in theme_dirs:
                        dest = Path(globals.spice_config) / "Themes" / td.name
                        if os.path.exists(dest):
                            shutil.rmtree(dest, ignore_errors=True)
                        shutil.move(str(td), str(dest))

                        # Copy outside images to the theme's images folder as preview fallbacks
                        if outside_imgs:
                            dest_img_dir = dest / "images"
                            os.makedirs(dest_img_dir, exist_ok=True)
                            for img in outside_imgs:
                                try:
                                    shutil.copy2(str(img), str(dest_img_dir / img.name))
                                except Exception:
                                    pass

                    if os.path.exists(unpacked_path) and os.path.isdir(unpacked_path):
                        shutil.rmtree(unpacked_path, ignore_errors=True)

            # Moving all theme extensions to the extensions folder
            for item in list(Path(f"{globals.spice_config}\\Themes").glob("**/*.js")):
                fullpath = str(item)
                if re.search(r'theme(?:\.|\.js)', fullpath):
                    continue
                destpath = (f"{globals.spice_config}\\Extensions"
                + fullpath[fullpath.rfind('\\') : fullpath.rfind('.')]
                + ".js"
                )
                if os.path.exists(destpath):
                    os.remove(destpath)
                shutil.move(fullpath, destpath)

        else:
            utils.verbose_print(f"{unpacked_name} wasnt downloaded successfully...")

    # Create Marketplace placeholder theme
    import aiohttp
    market_theme_dir = f"{globals.spice_config}\\Themes\\marketplace"
    os.makedirs(market_theme_dir, exist_ok=True)
    try:
        async with aiohttp.ClientSession() as cs_market:
            async with cs_market.get("https://raw.githubusercontent.com/spicetify/marketplace/main/resources/color.ini") as r_market:
                if r_market.status == 200:
                    with open(f"{market_theme_dir}\\color.ini", "w") as f_market:
                        f_market.write(await r_market.text())
    except Exception as e_market:
        utils.verbose_print(f"Failed to download marketplace color.ini: {e_market}")
        with open(f"{market_theme_dir}\\color.ini", "w") as f_market:
            f_market.write("[marketplace]\ntext = ffffff\n")

    with open(f"{market_theme_dir}\\user.css", "w") as f_market:
        f_market.write("/* Spicetify Marketplace Placeholder */\n")

async def restore_credentials():



    # >[Section 10]<
    # The code below will restore the Spotify user data and credentials.

    if os.path.isdir(f"{globals.installer_config}\\backup\\Users"):
        if os.path.isdir(f"{globals.appdata}\\Spotify\\Users") is True:
            shutil.rmtree(f"{globals.appdata}\\Spotify\\Users")

        if os.path.isfile(f"{globals.appdata}\\Spotify\\prefs") is True:
            os.remove(f"{globals.appdata}\\Spotify\\prefs")

        shutil.move(
            f"{globals.installer_config}\\backup\\Users",
            f"{globals.appdata}\\Spotify"
        )

        shutil.move(
            f"{globals.installer_config}\\backup\\prefs",
            f"{globals.appdata}\\Spotify"
        )
        shutil.rmtree(f"{globals.installer_config}\\backup")

        utils.set_config_entry(
            entry="app.last-launched-version",
            replacement= ".".join(state.runtime_spotify_version[18:-4].split(".")[:5]).split("-")[0],
            config=f"{globals.appdata}//Spotify//prefs",
            splitchar="="
        )

    elif os.path.isdir(f"{globals.installer_config}\\backup") is False:
        print("No credentials to restore!\n")

    else:
        print("Credentials were lost during install!\n")
        shutil.rmtree(f"{globals.installer_config}\\backup")

async def cache_pixmaps():


    # >[Section 11]<
    # The code below will cache pixmaps of each themes showcase screenshots.

    try:
        if os.path.exists(globals.pix_cache_path):
            os.remove(globals.pix_cache_path)
        open(globals.pix_cache_path, 'w').close()
        state.get_pix_cache().clear()

        themes = utils.list_config_available("themes")
        backgrounds = utils.theme_images()
        for theme in themes:
            background=str(backgrounds[themes.index(theme)])
            if background != "None":
                Brightness = gui.brightness(background)
                pixmapByteArray = gui.buttonPixmap(bg=background, rounded=True, width=284, height=160, typing="ByteArray")
                state.get_pix_cache()[background] = [pixmapByteArray, Brightness]
                with open(globals.pix_cache_path, 'a') as f:
                    f.write(f'{background}: {str(pixmapByteArray.toBase64())}, {Brightness}\n')
    except:
        print("Pixmaps could not be cached, this does not hinder your install.\nHowever customization page might take a second to load.")

async def cache_descriptions():


    # >[Section 12]<
    # The code below will cache descriptions of each extensions "//description" header.

    try:
        if os.path.exists('desc_cache.txt'):
            os.remove('desc_cache.txt')
        else:
            open('desc_cache.txt', 'w').close()
        state.get_desc_cache().clear()

        extensions=[]
        descriptions = utils.extension_descriptions()
        for extension in utils.list_config_available("extensions"):
            if extension.lower()[:-3] not in [x.lower() for x in utils.list_config_available("themes")]:
                extensions.append(extension)

        for extension in extensions:
            if extension[:-3] not in state.get_desc_cache():
                state.get_desc_cache()[extension[:-3]] = descriptions[extensions.index(extension)]
                with open("desc_cache.txt", "a") as f:
                    f.write(
                        f'{extension[:-3]}: {descriptions[extensions.index(extension)]}\n'
                )
    except:
        print("Descriptions could not be cached, this does not hinder your install.\nHowever the extensions page may take a second to load.")

