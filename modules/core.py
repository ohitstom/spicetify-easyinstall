import asyncio
import os
import shutil
from pathlib import Path

from modules import globals, utils


async def install(launch=False):
    steps_count = 10
    folders = [
        f"{globals.user_profile}\\spicetify-cli",
        f"{globals.user_profile}\\.spicetify",
        f"{globals.appdata_local}\\spotify",
        f"{globals.appdata}\\spotify",
        globals.temp,
    ]

    # >[Section 1]<

    print(f"\n(1/{steps_count}) Backing Up Credentials...")
    if os.path.isdir(f"{globals.appdata}\\Spotify\\Users") and os.path.isfile(f"{globals.appdata}\\Spotify\\prefs"):
        if os.path.isdir(f"{globals.cwd}\\Backup_Credentials"):
            shutil.rmtree(f"{globals.cwd}\\Backup_Credentials")
        else:
            os.mkdir(f"{globals.cwd}\\Backup_Credentials")
        
        shutil.move(
            f"{globals.appdata}\\Spotify\\Users",
            f"{globals.cwd}\\Backup_Credentials\\Users",
        )
        shutil.move(
            f"{globals.appdata}\\Spotify\\prefs", f"{globals.cwd}\\Backup_Credentials"
        )
        print("Finished backing up!\n")
    
    else:
        print("No credentials found!\n")

    # >[Section 2]<

    print(f"(2/{steps_count}) Uninstalling Spotify...")
    if os.path.isdir(f"{globals.appdata}\\Spotify"):
        utils.kill_processes("spicetify.exe")
        utils.kill_processes("Spotify.exe")
        
        await utils.powershell(
            '\n'.join([
                'cmd /c "%USERPROFILE%\\AppData\\Roaming\\Spotify\\Spotify.exe" /UNINSTALL /SILENT',
                'cmd /c icacls %localappdata%\\Spotify\\Update /grant %username%:D',
                'cmd /c icacls %localappdata%\\Spotify\\Update /grant %username%:R'
            ]),
            verbose=False,
        )
        print("Finished uninstalling Spotify!\n")
    
    else:
        print("Spotify is not installed!\n")

    # >[Section 3]<

    print(f"(3/{steps_count}) Wiping folders...")
    for folder in folders:
        try:
            if not os.path.exists(folder) or len(os.listdir(folder)) == 0:
                utils.verbose_print(f'"{folder}" is already empty.')
            else:
                shutil.rmtree(folder, ignore_errors=True)
                utils.verbose_print(f'"{folder}" has been deleted.')
        except Exception as e:
            utils.verbose_print(f'"{folder}" was not deleted: {e}.')
    print("Finished wiping folders!\n")

    # >[Section 4]<

    print(f"(4/{steps_count}) Downloading correct Spotify version...")
    if not os.path.isdir(globals.temp):
        os.mkdir(globals.temp)
    
    await utils.chunked_download(
        url=globals.SPOTIFY_SETUP_URL,
        path=(globals.temp + "\\" + globals.SPOTIFY_VERSION),
        label=(globals.temp + "\\" + globals.SPOTIFY_VERSION)
        if globals.verbose
        else globals.SPOTIFY_VERSION,
    )
    print("Finished downloading Spotify!\n")

    # >[Section 5]<

    print(f"(5/{steps_count}) Installing Spotify...")
    utils.kill_processes("Spotify.exe")
    spotify_install_pid = (
        await utils.start_process(
            globals.temp + "\\" + globals.SPOTIFY_VERSION,
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
    os.remove(globals.temp + "\\" + globals.SPOTIFY_VERSION)
    print("Finished installing Spotify!\n")

    # >[Section 6]<

    print(f"(6/{steps_count}) Installing Spicetify...")
    await utils.powershell(
        '\n'.join([
            '$ProgressPreference = "SilentlyContinue"',
            f'$v="{globals.SPICETIFY_VERSION}"; Invoke-WebRequest -UseBasicParsing "https://raw.githubusercontent.com/khanhas/spicetify-cli/master/install.ps1" | Invoke-Expression',
        ])
    )

    environ_check = (
        f"{globals.user_profile}\\spicetify-cli\\spicetify.exe"
        if os.path.isdir(f"{globals.user_profile}\\spicetify-cli")
        else "spicetify"
    )

    await utils.powershell(
        '\n'.join([
            f'{environ_check} config current_theme SpicetifyDefault -n',
            f'{environ_check} backup apply enable-devtool -n',
        ])
    )
    print("Finished installing Spicetify!\n")

    # >[Section 7]<

    print(f"(7/{steps_count}) Preventing Spotify from updating...")
    utils.kill_processes("Spotify.exe")
    if not os.path.isdir(f"{globals.appdata_local}\\Spotify\\Update"):
        os.mkdir(f"{globals.appdata_local}\\Spotify\\Update")
    
    await utils.powershell(
        '\n'.join([
            'cmd /c icacls %localappdata%\\Spotify\\Update /deny %username%:D',
            'cmd /c icacls %localappdata%\\Spotify\\Update /deny %username%:R'
        ])
    )
    print("Finished blocking Spotify updates!\n")

    # >[Section 8]<

    print(f"(8/{steps_count}) Downloading 'official' themes...")
    shutil.rmtree(f"{globals.user_profile}\\spicetify-cli\\Themes", ignore_errors=True)
    
    await utils.chunked_download(
        url=globals.THEMES_URL,
        path=(f"{globals.user_profile}\\spicetify-cli\\Themes.zip"),
        label=(f"{globals.user_profile}\\spicetify-cli\\Themes.zip")
        if globals.verbose
        else "Themes.zip",
    )

    shutil.unpack_archive(
        f"{globals.user_profile}\\spicetify-cli\\Themes.zip",
        f"{globals.user_profile}\\spicetify-cli",
    )

    os.remove(
        f"{globals.user_profile}\\spicetify-cli\\Themes.zip"
    )
    os.rename(
        f"{globals.user_profile}\\spicetify-cli\\{globals.THEMES_VERSION}",
        f"{globals.user_profile}\\spicetify-cli\\Themes",
    )

    for item in list(Path(f"{globals.user_profile}\\spicetify-cli\\Themes").glob("*")):
        fullpath = str(item)
        if os.path.isdir(fullpath):
            filename = str(item.name)
            if filename[0] == ".":
                shutil.rmtree(fullpath)
        else:
            os.remove(fullpath)

    os.rename(
        f"{globals.user_profile}\\spicetify-cli\\Themes\\Default",
        f"{globals.user_profile}\\spicetify-cli\\Themes\\SpicetifyDefault",
    )

    for item in list(Path(f"{globals.user_profile}\\spicetify-cli\\Themes").glob("**/*.js")):
        fullpath = str(item)
        destpath = (f"{globals.user_profile}\\spicetify-cli\\Extensions"
        + fullpath[fullpath.rfind('\\') : fullpath.rfind('.')]
        + "Theme.js"
        )
        if os.path.exists(destpath):
            os.remove(destpath)
        shutil.move(fullpath, destpath)
    print("Finished downloading 'official' themes!\n")

    # >[Section 9]<

    print(f"(9/{steps_count}) Downloading 'custom' addons...")
    await utils.simultaneous_chunked_download(
        {
            **globals.CUSTOM_THEMES,
            **globals.CUSTOM_APPS,
            **globals.CUSTOM_EXTENSIONS

         }, "Custom Addons.zip")

    for url, download in ({**globals.CUSTOM_THEMES, **globals.CUSTOM_APPS, **globals.CUSTOM_EXTENSIONS}).items():
        if os.path.exists(download):
            captured = Path(download)
            directory = captured.parent
            unpacked_name = captured.with_suffix("").name
            unpacked_path = f"{directory}\\{unpacked_name}"

            if os.path.exists(unpacked_path):
                shutil.rmtree(unpacked_path)

            shutil.unpack_archive(download, unpacked_path)
            os.remove(download)

            for item in os.listdir(unpacked_path):
                if os.path.isdir(f"{unpacked_path}\\{item}") and "assets" not in item:
                    for src in Path(f"{unpacked_path}\\{item}").glob("*"):
                        if url not in utils.globals.CUSTOM_EXTENSIONS:
                            shutil.move(src, unpacked_path)

                        elif ".js" in str(src):
                            persistent_src = str(src.with_suffix(".js").name)
                            if os.path.exists(f"{directory}\\{persistent_src}"):
                                os.remove(f"{directory}\\{persistent_src}")

                            shutil.move(src, directory)

                    try:
                        os.rmdir(f"{unpacked_path}\\{item}")
                    except Exception:
                        shutil.rmtree(unpacked_path)

            for item in list(Path(f"{globals.user_profile}\\spicetify-cli\\Themes").glob("**/*.js")):
                fullpath = str(item)
                destpath = (f"{globals.user_profile}\\spicetify-cli\\Extensions"
                + fullpath[fullpath.rfind('\\') : fullpath.rfind('.')]
                + "Theme.js"
                )
                if os.path.exists(destpath):
                    os.remove(destpath)
                shutil.move(fullpath, destpath)

        else:
            print(f"{url} was not downloaded")
    print("Finished downloading 'custom' themes!\n")

    # >[Section 10]<

    print(f"(10/{steps_count}) Restoring Credentials...")
    if os.path.isdir(f"{globals.appdata}\\Spotify\\Users") is True:
        shutil.rmtree(f"{globals.appdata}\\Spotify\\Users")
    
    elif os.path.isfile(f"{globals.appdata}\\Spotify\\prefs") is True:
        os.remove(f"{globals.appdata}\\Spotify\\prefs")

    if os.path.isdir(f"{globals.cwd}\\Backup_Credentials\\Users"):
        shutil.move(
            f"{globals.cwd}\\Backup_Credentials\\Users",
            f"{globals.appdata}\\Spotify"
        )

        shutil.move(
            f"{globals.cwd}\\Backup_Credentials\\prefs",
            f"{globals.appdata}\\Spotify"
        )
        shutil.rmtree(f"{globals.cwd}\\Backup_Credentials")
        print("Finished restoring!\n")

    elif os.path.isdir(f"{globals.cwd}\\Backup_Credentials") is False:
        print("No credentials to restore!")
    
    else:
        print("Credentials were lost during install!\n")
        shutil.rmtree(f"{globals.cwd}\\Backup_Credentials")

    if launch:
        await utils.start_process(f"{globals.appdata}\\spotify\\spotify.exe", silent=False)


async def apply_config(theme, colorscheme, extensions, customapps):
    steps_count = 2
    environ_check = (
        f"{globals.user_profile}\\spicetify-cli\\spicetify.exe"
        if os.path.isdir(f"{globals.user_profile}\\spicetify-cli")
        else "spicetify"
    )

    # >[Section 1]<

    print(f"(1/{steps_count}) Setting options...")
    utils.set_config_entry("current_theme", theme)
    utils.set_config_entry("color_scheme", colorscheme)
    utils.set_config_entry("extensions", "|".join(extension + ".js" for extension in extensions))
    utils.set_config_entry("custom_apps", "|".join(customapps))
    print("Finished setting options!\n")

    # >[Section 2]<

    print(f"(2/{steps_count}) Applying config...")
    await utils.powershell(f"{environ_check} apply -n", start_new_session=False, verbose=True)
    await utils.powershell(f"{environ_check} restart", wait=False, verbose=False)
    print("Finished applying config!\n")


async def uninstall():
    steps_count = 3
    user_profile = os.path.expanduser("~")  # Vars
    temp = "C:\\Users\\WDAGUtilityAccount\\AppData\\Local\\temp"
    folders = [
        f"{user_profile}\\spicetify-cli",
        f"{user_profile}\\.spicetify",
        temp,
    ]

    print(f"(1/{steps_count}) Uninstalling Spotify...")  # Section 1
    if os.path.isdir(f"{globals.appdata}\\Spotify"):
        utils.kill_processes("spicetify.exe")
        utils.kill_processes("Spotify.exe")
        
        await utils.powershell(
            '\n'.join([
                'cmd /c "%USERPROFILE%\\AppData\\Roaming\\Spotify\\Spotify.exe" /UNINSTALL /SILENT',
                'cmd /c icacls %localappdata%\\Spotify\\Update /grant %username%:D',
                'cmd /c icacls %localappdata%\\Spotify\\Update /grant %username%:R',

            ]),
            verbose=False,
        )
        print("Finished uninstalling Spotify!\n")
    
    else:
        print("Spotify is not installed!\n")

    print(f"(2/{steps_count}) Wiping folders...")  # Section 2
    for folder in folders:
        try:
            if not os.path.exists(folder) or len(os.listdir(folder)) == 0:
                utils.verbose_print(f'"{folder}" is already empty.')
            else:
                shutil.rmtree(folder, ignore_errors=True)
                utils.verbose_print(f'"{folder}" has been deleted.')
        
        except Exception as e:
            utils.verbose_print(f'"{folder}" was not deleted: {e}.')
    print("Finished wiping folders!\n")

    print(f"(3/{steps_count}) Removing environment variables...")  # Section 3
    await utils.powershell(
        '\n'.join([
            '$path = [System.Environment]::GetEnvironmentVariable("PATH", "User")',
            '$sp_dir = "${HOME}\\spicetify-cli"',
            '$paths = ($path.Split(";") | Where-Object { $_.TrimEnd("") -ne $sp_dir }) -join ";"',
            '$is_in_path = "$path".Contains("$sp_dir") -or "$path".Contains("${sp_dir}")',
            'if ($is_in_path) {[Environment]::SetEnvironmentVariable("PATH", "${paths}", "User")}',
        ]),
        wait=True,
    )
    print("Finished removing environment variables!")


async def update_addons():
    steps_count = 3
    folders = [
        f"{globals.user_profile}\\spicetify-cli\\Themes",
        f"{globals.user_profile}\\spicetify-cli\\Extensions",
        f"{globals.user_profile}\\spicetify-cli\\Customapps",
    ]

    # >[Section 1]<

    print(f"(1/{steps_count}) Wiping old addons...")
    for folder in folders:
        try:
            if not os.path.exists(folder):
                utils.verbose_print(f'"{folder}" is already empty.')
            
            elif len(os.listdir(folder)) == 0:
                os.rmdir(folder)
                utils.verbose_print(f'"{folder}" is already empty.')
            
            else:
                shutil.rmtree(folder, ignore_errors=True)
                utils.verbose_print(f'"{folder}" has been deleted.')
            
            if "Themes" not in folder:
                os.mkdir(folder)
        
        except Exception as e:
            utils.verbose_print(f'"{folder}" was not deleted: {e}.')
    print("Finished wiping old addons!\n")

    # >[Section 2]<

    print(f"(2/{steps_count}) Downloading 'official' addons...")
    await utils.chunked_download(
        url=globals.THEMES_URL.replace(globals.THEMES_VERSION[17:], 'refs/heads/master'),
        path=(f"{globals.user_profile}\\spicetify-cli\\Themes.zip"),
        label=(f"{globals.user_profile}\\spicetify-cli\\Themes.zip")
        if globals.verbose
        else "Themes.zip",
    )

    shutil.unpack_archive(
        f"{globals.user_profile}\\spicetify-cli\\Themes.zip",
        f"{globals.user_profile}\\spicetify-cli",
    )
    os.remove(
        f"{globals.user_profile}\\spicetify-cli\\Themes.zip"
    )
    os.rename(
        f"{globals.user_profile}\\spicetify-cli\\spicetify-themes-master",
        f"{globals.user_profile}\\spicetify-cli\\Themes",
    )
    os.rename(
        f"{globals.user_profile}\\spicetify-cli\\Themes\\Default",
        f"{globals.user_profile}\\spicetify-cli\\Themes\\SpicetifyDefault",
    )

    for item in list(Path(f"{globals.user_profile}\\spicetify-cli\\Themes").glob("*")):
        fullpath = str(item)
        if os.path.isdir(fullpath):
            filename = str(item.name)
            if filename[0] == ".":
                shutil.rmtree(fullpath)
        else:
            os.remove(fullpath)

    for item in list(Path(f"{globals.user_profile}\\spicetify-cli\\Themes").glob("**/*.js")):
        fullpath = str(item)
        destpath = (f"{globals.user_profile}\\spicetify-cli\\Extensions"
        + fullpath[fullpath.rfind('\\') : fullpath.rfind('.')]
        + "Theme.js"
        )
        if os.path.exists(destpath):
            os.remove(destpath)
        shutil.move(fullpath, destpath)
    print("Finished downloading 'official' themes!\n")

    # >[Section 3]<

    print(f"(3/{steps_count}) Downloading 'custom' addons...")
    base = {**globals.CUSTOM_THEMES, **globals.CUSTOM_APPS, **globals.CUSTOM_EXTENSIONS}
    final = {}
    for url, directory in base.items():
        if "releases" not in url:
            newval = f"{url[:-40]}refs/heads/"
            final[newval + await utils.heads_value(newval)] = directory
        else:
            final[url] = directory

    if globals.verbose:
        for item in final.items():
            utils.verbose_print(f"{item}\n")

    await utils.simultaneous_chunked_download(final, "Custom Addons.zip")
    for url, download in final.items():
        if os.path.exists(download):
            utils.verbose_print(f"{url} was downloaded successfully!")
            captured = Path(download)
            directory = captured.parent
            unpacked_name = captured.with_suffix("").name
            unpacked_path = f"{directory}\\{unpacked_name}"

            if os.path.exists(unpacked_path):
                shutil.rmtree(unpacked_path)

            shutil.unpack_archive(download, unpacked_path)
            os.remove(download)

            for item in os.listdir(unpacked_path):
                if os.path.isdir(f"{unpacked_path}\\{item}") and "assets" not in item:
                    for src in Path(f"{unpacked_path}\\{item}").glob("*"):
                        if url not in utils.globals.CUSTOM_EXTENSIONS:
                            shutil.move(src, unpacked_path)

                        elif ".js" in str(src):
                            persistent_src = str(src.with_suffix(".js").name)
                            if os.path.exists(f"{directory}\\{persistent_src}"):
                                os.remove(f"{directory}\\{persistent_src}")

                            shutil.move(src, directory)

                    try:
                        os.rmdir(f"{unpacked_path}\\{item}")
                    except Exception:
                        shutil.rmtree(unpacked_path)

            for item in list(Path(f"{globals.user_profile}\\spicetify-cli\\Themes").glob("**/*.js")):
                fullpath = str(item)
                destpath = (f"{globals.user_profile}\\spicetify-cli\\Extensions"
                + fullpath[fullpath.rfind('\\') : fullpath.rfind('.')]
                + "Theme.js"
                )
                if os.path.exists(destpath):
                    os.remove(destpath)
                shutil.move(fullpath, destpath)

        else:
            utils.verbose_print(f"\n{url} was not downloaded...")
            print("Download Errored, Please retry with verbose enabled for full error info!")
    print("Finished downloading 'custom' themes!\n")

async def update_app():
    steps_count = 2
    json = await utils.latest_release_GET()
    latest_release = json["tag_name"]

    # >[Section 1]<

    if os.path.exists(f"{globals.cwd}\\Update.zip"):
        os.remove(f"{globals.cwd}\\Update.zip") 
    if os.path.isdir(f"{globals.cwd}\\Update"):
        shutil.rmtree(f"{globals.cwd}\\Update")

    print(f"(1/{steps_count}) Downloading Update from {globals.RELEASE} to {latest_release}...")
    await utils.chunked_download(
        url=json["assets"][0]["browser_download_url"],
        path=(f"{globals.cwd}\\Update.zip"),
        label=(f"{globals.cwd}\\Update.zip") if globals.verbose else "Update.zip",
    )
    print("Finished Downloading Update!")

    # >[Section 2]<

    print(f"\n(2/{steps_count}) Extraction And Cleanup...")
    if not os.path.exists(f"{globals.cwd}\\Update.zip"):
        return None

    shutil.unpack_archive(f"{globals.cwd}\\Update.zip", f"{globals.cwd}\\Update")
    os.remove(f"{globals.cwd}\\Update.zip")
    print("Finished Extraction And Cleanup!")
    if os.path.isdir(f"{globals.cwd}\\Update"):
        return True
