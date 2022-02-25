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
    # 1. Checks if the Spotify directory exists.
    # 2. If it does, check if the backup directory exists.
    # 3. Moves the Spotify directory and the prefs file to the backup directory.

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
    # 1. Checks if Spotify is installed.
    # 2. If it is, kill Spotify processes and remove Spotify files.
    # 3. If it isn't, print that Spotify is not installed.

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
    # 1. For each folder in the list of folders, 
    # 2. try to delete the folder if it exists and is not empty. 
    # 3. If the folder does not exist or is empty, print a message saying so.

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
    # Download the Spotify setup file from the Spotify website.
    
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
    # 1. Kill all Spotify processes.
    # 2. Deletes the Spotify installation folder.
    # 3. Installs Spotify.
    # 5. Deletes the installation file.
    # 6. Kill all Spotify processes once preference file are found.

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
    # Installs Spicetify and Applies Spicetify default theme

    print(f"(6/{steps_count}) Installing Spicetify...")
    await utils.powershell(
        '\n'.join([
            '$ProgressPreference = "SilentlyContinue"',
            f'$v="{globals.SPICETIFY_VERSION}"; Invoke-WebRequest -UseBasicParsing "https://raw.githubusercontent.com/khanhas/spicetify-cli/master/install.ps1" | Invoke-Expression',
        ])
    )

    environ_check = (
        f"`{globals.user_profile}`\\spicetify-cli\\spicetify.exe"
        if os.path.isdir(f"{globals.user_profile}\\spicetify-cli")
        else "spicetify"
    )
    
    await utils.powershell(
        '\n'.join([
            f'{environ_check}',
        ])
    )

    prefs_check = utils.find_config_entry("prefs_path")
    if not prefs_check:
        utils.set_config_entry("prefs_path", f'{globals.appdata}\Spotify\prefs')

    await utils.powershell(
        '\n'.join([
            f'{environ_check} config current_theme SpicetifyDefault -n',
            f'{environ_check} backup apply enable-devtool -n',
        ])
    )
    print("Finished installing Spicetify!\n")

    # >[Section 7]<
    # 1. Creates a directory in the Spotify folder to prevent Spotify from updating.
    # 2. Prevents Spotify from updating by killing the Spotify process.
    # 3. Prevents the user from reading and writing to the Spotify folder.

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
    # Downloads the themes from the official Spicetify repository, and move them to the correct location.
    
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
    # Download all the custom addons and themes, unpack them, move them to the correct location, and
    # deletes the zip files.
    
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
                    shutil.move(src, unpacked_path)      
                if os.path.exists(f"{unpacked_path}\\{item}") and os.path.isdir(f"{unpacked_path}\\{item}"): # Cleanup
                    os.rmdir(f"{unpacked_path}\\{item}")

                # Moving all files with the js extension to {extensions}
                for src in Path(f"{unpacked_path}").glob("**/*.js"): # for files in {PARENT}\{ADDON-DUPE}\**\*.js where ** means any segment, null or otherwise.
                    if "Extensions" in str(src):
                        shutil.move(src, directory)
                if os.path.exists(unpacked_path) and os.path.isdir(unpacked_path) and "Extensions" in unpacked_path: # Cleanup
                    shutil.rmtree(unpacked_path)

            # Moving all theme extensions to the extensions folder
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
            utils.verbose_print(f"{unpacked_name} wasnt downloaded successfully...")
    print("\nFinished downloading 'custom' addons!\n")

    # >[Section 10]<
    # 1. The code below is a function that will restore the Spotify user data and credentials.
    # 2. The function will first check if the backup exists. If it does, it will move the backup to the
    # 3. Spotify directory.
    # 4. The function will then check if the user data and credentials were successfully restored.

    print(f"(10/{steps_count}) Restoring Credentials...")
    if os.path.isdir(f"{globals.cwd}\\Backup_Credentials\\Users"):
        if os.path.isdir(f"{globals.appdata}\\Spotify\\Users") is True:
            shutil.rmtree(f"{globals.appdata}\\Spotify\\Users")
        
        if os.path.isfile(f"{globals.appdata}\\Spotify\\prefs") is True:
            os.remove(f"{globals.appdata}\\Spotify\\prefs")

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
        f"`{globals.user_profile}`\\spicetify-cli\\spicetify.exe"
        if os.path.isdir(f"{globals.user_profile}\\spicetify-cli")
        else "spicetify"
    )

    # >[Section 1]<
    # Sets the config as per the users choices.

    print(f"(1/{steps_count}) Setting options...")
    utils.set_config_entry("current_theme", theme)
    utils.set_config_entry("color_scheme", colorscheme)
    utils.set_config_entry("extensions", "|".join(extension + ".js" for extension in extensions))
    utils.set_config_entry("custom_apps", "|".join(customapps))
    print("Finished setting options!\n")

    # >[Section 2]<
    # Applying the changes to the config.
    
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
    
    # >[Section 1]<
    # The code below is a function that will uninstall Spotify.
    
    print(f"(1/{steps_count}) Uninstalling Spotify...")
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

    # >[Section 2]<
    # Delete all folders in the `folders` list.

    print(f"(2/{steps_count}) Wiping folders...")
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

    # >[Section 3]<
    # If the spicetify-cli directory is in the user's PATH, remove it.

    print(f"(3/{steps_count}) Removing environment variables...")  
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


async def update_addons(shipped=False):
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

    print(f"(2/{steps_count}) Downloading 'official' themes...")
    
    await utils.chunked_download(
        url=globals.THEMES_URL if shipped else globals.THEMES_URL.replace(globals.THEMES_VERSION[17:], 'refs/heads/master'),
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
        f"{globals.user_profile}\\spicetify-cli\\{globals.THEMES_VERSION if shipped else 'spicetify-themes-master'}",
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
    if not shipped:
        for url, directory in base.items():
            if "releases" not in url:
                newval = f"{url[:-40]}refs/heads/"
                final[newval + await utils.heads_value(newval)] = directory
            else:
                final[url] = directory
    
    await utils.simultaneous_chunked_download(base if shipped else final, "Stock Custom Addons.zip" if shipped else "Custom Addons.zip")
    for url, download in base.items() if shipped else final.items():
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
                    shutil.move(src, unpacked_path)      
                if os.path.exists(f"{unpacked_path}\\{item}") and os.path.isdir(f"{unpacked_path}\\{item}"): # Cleanup
                    os.rmdir(f"{unpacked_path}\\{item}")

                # Moving all files with the js extension to {extensions}
                for src in Path(f"{unpacked_path}").glob("**/*.js"): # for files in {PARENT}\{ADDON-DUPE}\**\*.js where ** means any segment, null or otherwise.
                    if "Extensions" in str(src):
                        shutil.move(src, directory)
                if os.path.exists(unpacked_path) and os.path.isdir(unpacked_path) and "Extensions" in unpacked_path: # Cleanup
                    shutil.rmtree(unpacked_path)

            # Moving all theme extensions to the extensions folder
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
            utils.verbose_print(f"{unpacked_name} wasnt downloaded successfully...")
    print("\nFinished downloading 'custom' themes!")


async def update_app():
    steps_count = 2
    json = await utils.latest_release_GET()
    latest_release = json["tag_name"]

    if os.path.exists(f"{globals.cwd}\\Update.zip"):
        os.remove(f"{globals.cwd}\\Update.zip") 
    if os.path.isdir(f"{globals.cwd}\\Update"):
        shutil.rmtree(f"{globals.cwd}\\Update")

    # >[Section 1]<
    # Download the latest release from GitHub and extract it to the current directory.

    print(f"(1/{steps_count}) Downloading Update from {globals.RELEASE} to {latest_release}...")
    await utils.chunked_download(
        url=json["assets"][0]["browser_download_url"],
        path=(f"{globals.cwd}\\Update.zip"),
        label=(f"{globals.cwd}\\Update.zip") if globals.verbose else "Update.zip",
    )
    print("Finished Downloading Update!")

    # >[Section 2]<
    # 1. Check if there's an update.zip in the current working directory.
    # 2. If there is, unpack it and remove it.
    # 3. If there is an extracted folder, trigger the restart by returning True.

    print(f"\n(2/{steps_count}) Extraction And Cleanup...")
    if not os.path.exists(f"{globals.cwd}\\Update.zip"):
        return None

    shutil.unpack_archive(f"{globals.cwd}\\Update.zip", f"{globals.cwd}\\Update")
    os.remove(f"{globals.cwd}\\Update.zip")
    print("Finished Extraction And Cleanup!")
    if os.path.isdir(f"{globals.cwd}\\Update"):
        return True
