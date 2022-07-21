import asyncio
import os
import shutil
from pathlib import Path

from modules import globals, utils, gui

async def install(launch=False, latest=False):

    # >[Section 0]<
    # The code below will re-assign variables if edition is True.
       
    if latest:
        steps_count = 13
        
        print(f"\n(0/{steps_count}) Preparing latest variables...")
        try:
            spice = await utils.latest_github_release(Spicetify=True)
            spotify = await utils.latest_spotify_release(name=False)
            theme = await utils.latest_github_commit()
            addon = await utils.latest_github_commit(Spicetify=True)            
            globals.SPICETIFY_VERSION = spice["tag_name"][1:]
            globals.THEMES_VERSION = f"spicetify-themes-{theme['sha']}"
            globals.ADDONS_VERSION = f"spicetify-cli-{addon['sha']}"          
            globals.SPOTIFY_VERSION = "/".join(spotify.split("/")[-1:])      
            globals.THEMES_URL = f"https://codeload.github.com/spicetify/spicetify-themes/zip/{theme['sha']}"
            globals.ADDONS_URL = f"https://codeload.github.com/spicetify/spicetify-themes/zip/{theme['sha']}"
            globals.SPOTIFY_URL= spotify      
        
        except Exception as e:
            print(f"\nFailed to fetch variables, likely to be ratelimited.\nPlease try again later or uncheck 'install latest'.\nError: {e}")
            return None   
        print("Finished preparing latest variables!")
    
    else:
        steps_count = 12

    # >[Section 1]<
    # The code below will backup a users spotify login and creds.

    print(f"\n(1/{steps_count}) Backing Up Credentials...")
    if os.path.isdir(f"{globals.appdata}\\Spotify\\Users") and os.path.isfile(f"{globals.appdata}\\Spotify\\prefs"):
        if os.path.isdir(f"{globals.cwd}\\backup"):
            shutil.rmtree(f"{globals.cwd}\\backup")
        else:
            os.mkdir(f"{globals.cwd}\\backup")
        
        shutil.move(f"{globals.appdata}\\Spotify\\Users", f"{globals.cwd}\\backup\\Users")
        shutil.move(f"{globals.appdata}\\Spotify\\prefs", f"{globals.cwd}\\backup")
        print("Finished backing up!\n")
    
    else:
        print("No credentials found!\n")

    # >[Section 2]<
    # The code below will uninstall Spotify.

    print(f"(2/{steps_count}) Uninstalling Spotify...")
    process = await utils.powershell('Get-AppxPackage SpotifyAB.SpotifyMusic', wait=True, verbose=False)
    winstore_spotify = str(await process.stdout.read()).strip()

    if 'Version' in winstore_spotify:
        await utils.powershell('Get-AppxPackage SpotifyAB.SpotifyMusic | Remove-AppxPackage', wait=True)
        print("Finished uninstalling Spotify!\n")
    
    elif os.path.isdir(f"{globals.appdata}\\Spotify"):
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
    # The code below will remove a list of spicetify dependant folders.

    folders = [
        globals.spice_config,
        globals.spice_executable,
        f"{globals.appdata}\\spotify",
        f"{globals.appdata_local}\\spotify",
        globals.temp,
    ]

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
    # The code below will download Spotify.
    
    print(f"(4/{steps_count}) Downloading correct Spotify version...")
    if not os.path.isdir(globals.temp):
        os.mkdir(globals.temp)
    
    await utils.chunked_download(
        url=globals.SPOTIFY_URL,
        path=(f"{globals.temp}\\{globals.SPOTIFY_VERSION}"),
        label=(f"{globals.temp}\\{globals.SPOTIFY_VERSION}")
        if globals.verbose
        else globals.SPOTIFY_VERSION,
    )
    print("Finished downloading Spotify!\n")

    # >[Section 5]<
    # The code below will install Spotify.

    print(f"(5/{steps_count}) Installing Spotify...")
    utils.kill_processes("Spotify.exe")
    spotify_install_pid = (
        await utils.start_process(
            f"{globals.temp}\\{globals.SPOTIFY_VERSION}",
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
    os.remove(f"{globals.temp}\\{globals.SPOTIFY_VERSION}")
    print("Finished installing Spotify!\n")

    # >[Section 6]<
    # The code below will install Spicetify and do error checking.

    print(f"(6/{steps_count}) Installing Spicetify...")
    await utils.powershell(
        '\n'.join([
            '[Net.ServicePointManager]::SecurityProtocol = [Net.SecurityProtocolType]::Tls12',
            '$ProgressPreference = "SilentlyContinue"',
            f'$v="{globals.SPICETIFY_VERSION}"; Invoke-WebRequest -UseBasicParsing "https://raw.githubusercontent.com/spicetify/spicetify-cli/master/install.ps1" | Invoke-Expression',
        ])
    )

    environ_check = (
    f'& "{globals.spice_executable}\\spicetify.exe"' 
    if os.path.isdir(globals.spice_executable) 
    else "spicetify"
    )

    await utils.powershell(
        '\n'.join([
            f'{environ_check}',
        ])
    )

    if os.path.isfile(f"{globals.spice_config}\\config-xpui.ini"):
        prefs_check = utils.find_config_entry("prefs_path")
        if not prefs_check:
            utils.set_config_entry("prefs_path", f'{globals.appdata}\Spotify\prefs')
    else:
        print("Config wasnt created, Spicetify might not have installed correctly. Please retry with verbose if it doesnt work.")

    await utils.powershell(
        '\n'.join([
            f'{environ_check} config current_theme SpicetifyDefault -n',
            f'{environ_check} backup apply enable-devtools -n',
        ])
    )
    print("Finished installing Spicetify!\n")

    # >[Section 7]<
    # The code below will remove Spotifys ability to update.

    print(f"(7/{steps_count}) Preventing Spotify from updating...")
    utils.kill_processes("Spotify.exe")
    if not os.path.isdir(f"{globals.appdata_local}\\Spotify\\Update"):
        os.mkdir(f"{globals.appdata_local}\\Spotify\\Update")
    
    await utils.powershell(
        '\n'.join([
            'cmd /c icacls %localappdata%\\Spotify\\Update /deny %username%:D',
            'cmd /c icacls %localappdata%\\Spotify\\Update /deny %username%:R',
        ])
    )
    print("Finished blocking Spotify updates!\n")

    # >[Section 8]<
    # The code below will download spicetify-cli themes.
    
    print(f"(8/{steps_count}) Downloading 'official' themes...")
    await utils.chunked_download(
        url=globals.THEMES_URL,
        path=(f"{globals.spice_config}\\Themes.zip"),
        label=(f"{globals.spice_config}\\Themes.zip")
        if globals.verbose
        else "Themes.zip",
    )

    shutil.rmtree(f"{globals.spice_config}\\Themes", ignore_errors=True)
    shutil.unpack_archive(f"{globals.spice_config}\\Themes.zip", globals.spice_config)
    os.remove(f"{globals.spice_config}\\Themes.zip")
    os.rename(f"{globals.spice_config}\\{globals.THEMES_VERSION}", f"{globals.spice_config}\\Themes")

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
        destpath = (f"{globals.spice_config}\\Extensions"
        + fullpath[fullpath.rfind('\\') : fullpath.rfind('.')]
        + ".js"
        )
        if os.path.exists(destpath):
            os.remove(destpath)
        shutil.move(fullpath, destpath)
    print("Finished downloading 'official' themes!\n")

    # >[Section 9]<
    # The code below will download a list of custom Spicetify addons, declared in globals.py.
    
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
                    shutil.move(str(src), str(unpacked_path))      
                if os.path.exists(f"{unpacked_path}\\{item}") and os.path.isdir(f"{unpacked_path}\\{item}"): # Cleanup
                    os.rmdir(f"{unpacked_path}\\{item}")

                # Moving all files with the js extension to {extensions}
                for src in Path(f"{unpacked_path}").glob("**/*.js"): # for files in {PARENT}\{ADDON-DUPE}\**\*.js where ** means any segment, null or otherwise.
                    if "Extensions" in str(src):
                        shutil.move(str(src), str(directory))
                if os.path.exists(unpacked_path) and os.path.isdir(unpacked_path) and "Extensions" in unpacked_path: # Cleanup
                    shutil.rmtree(unpacked_path)

                # Recovering Repos with > 1 theme
                if not os.path.exists(f"{unpacked_path}\\user.css") and "Themes" in unpacked_path:
                    for src in Path(f"{unpacked_path}").glob("**/*"):
                        if os.path.isdir(str(src)) and ".github" not in str(src):
                            shutil.move(str(src), f"{globals.spice_config}\\Themes")
                    if os.path.exists(unpacked_path) and os.path.isdir(unpacked_path):
                        shutil.rmtree(unpacked_path)

            # Moving all theme extensions to the extensions folder
            for item in list(Path(f"{globals.spice_config}\\Themes").glob("**/*.js")):
                fullpath = str(item)
                destpath = (f"{globals.spice_config}\\Extensions"
                + fullpath[fullpath.rfind('\\') : fullpath.rfind('.')]
                + ".js"
                )
                if os.path.exists(destpath):
                    os.remove(destpath)
                shutil.move(fullpath, destpath)

        else:
            utils.verbose_print(f"{unpacked_name} wasnt downloaded successfully...")
    print("Finished downloading 'custom' addons!\n")

    # >[Section 10]<
    # The code below will restore the Spotify user data and credentials.

    print(f"(10/{steps_count}) Restoring Credentials...")
    if os.path.isdir(f"{globals.cwd}\\backup\\Users"):
        if os.path.isdir(f"{globals.appdata}\\Spotify\\Users") is True:
            shutil.rmtree(f"{globals.appdata}\\Spotify\\Users")
        
        if os.path.isfile(f"{globals.appdata}\\Spotify\\prefs") is True:
            os.remove(f"{globals.appdata}\\Spotify\\prefs")

        shutil.move(
            f"{globals.cwd}\\backup\\Users",
            f"{globals.appdata}\\Spotify"
        )

        shutil.move(
            f"{globals.cwd}\\backup\\prefs",
            f"{globals.appdata}\\Spotify"
        )
        shutil.rmtree(f"{globals.cwd}\\backup")

        utils.set_config_entry(
            entry="app.last-launched-version", 
            replacement= ".".join(globals.SPOTIFY_VERSION[18:-4].split(".")[:5]).split("-")[0], 
            config=f"{globals.appdata}//Spotify//prefs", 
            splitchar="="
        )

        print("Finished restoring!\n")

    elif os.path.isdir(f"{globals.cwd}\\backup") is False:
        print("No credentials to restore!\n")
    
    else:
        print("Credentials were lost during install!\n")
        shutil.rmtree(f"{globals.cwd}\\backup")

    # >[Section 11]<
    # The code below will cache pixmaps of each themes showcase screenshots.

    print(f"(11/{steps_count}) Caching pixmaps...")
    if os.path.exists('pix_cache.txt'):
        os.remove('pix_cache.txt')
    open('pix_cache.txt', 'w').close()
    globals.pix_cache.clear()

    themes = utils.list_config_available("themes")
    backgrounds = utils.theme_images()
    for theme in themes:
        background=str(backgrounds[themes.index(theme)])
        if background != "None":
            Brightness = gui.brightness(background)   
            pixmapByteArray = gui.buttonPixmap(bg=background, rounded=True, width=284, height=160, typing="ByteArray")
            globals.pix_cache[background] = [pixmapByteArray, Brightness]                
            with open('pix_cache.txt', 'a') as f:
                f.write(f'{background}: {str(pixmapByteArray.toBase64())}, {Brightness}\n') 
    print("Finished caching pixmaps!\n")

    # >[Section 12]<
    # The code below will cache descriptions of each extensions "//description" header.

    print(f"(12/{steps_count}) Caching descriptions...")
    if os.path.exists('desc_cache.txt'):
        os.remove('desc_cache.txt')
    else:
        open('desc_cache.txt', 'w').close()
    globals.desc_cache.clear()

    extensions=[]
    descriptions = utils.extension_descriptions()
    for extension in utils.list_config_available("extensions"):
        if extension.lower()[:-3] not in [x.lower() for x in utils.list_config_available("themes")]:
            extensions.append(extension)

    for extension in extensions:
        if extension[:-3] not in globals.desc_cache:
            globals.desc_cache[extension[:-3]] = descriptions[extensions.index(extension)]
            with open("desc_cache.txt", "a") as f:
                f.write(
                    f'{extension[:-3]}: {descriptions[extensions.index(extension)]}\n'
                )
    print("Finished caching extension descriptions!\n")
    
    if latest:
        print(f"\n(13/{steps_count}) Reverting latest variables...")
        globals.SPICETIFY_VERSION = globals.__SPICETIFY_VERSION__
        globals.THEMES_VERSION = globals.__THEMES_VERSION__
        globals.ADDONS_VERSION = globals.__ADDONS_VERSION__  
        globals.SPOTIFY_VERSION = globals.__SPOTIFY_VERSION__
        globals.THEMES_URL = globals.__THEMES_URL__
        globals.ADDONS_URL = globals.__ADDONS_URL__
        globals.SPOTIFY_URL = globals.__SPOTIFY_URL__

    if launch:
        await utils.start_process(f"{globals.appdata}\\spotify\\spotify.exe", silent=False)


async def apply_config(theme, colorscheme, extensions, customapps):
    steps_count = 2

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
    environ_check = (f'& "{globals.spice_executable}\\spicetify.exe"' if os.path.isdir(globals.spice_executable)  else "spicetify")    
    await utils.powershell(f"{environ_check} apply", start_new_session=False)
    await utils.start_process(f"{globals.appdata}\\spotify\\spotify.exe", silent=False)
    print("Finished applying config!\n")


async def uninstall():
    steps_count = 4
    folders = [
        globals.spice_executable,
        globals.spice_config,
        globals.temp,
    ]
    
    # >[Section 1]<
    # The code below will uninstall Spotify.
    
    print(f"(1/{steps_count}) Uninstalling Spotify...")
    process = await utils.powershell('Get-AppxPackage SpotifyAB.SpotifyMusic', wait=True, verbose=False)
    winstore_spotify = str(await process.stdout.read()).strip()

    if 'Version' in winstore_spotify:
        await utils.powershell('Get-AppxPackage SpotifyAB.SpotifyMusic | Remove-AppxPackage', wait=True)
        print("Finished uninstalling Spotify!\n")
    
    elif os.path.isdir(f"{globals.appdata}\\Spotify"):
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
    print("Finished removing environment variables!\n")

    print(f"(4/{steps_count}) Removing caches...")
    if os.path.exists('pix_cache.txt'):
        os.remove('pix_cache.txt')
    if os.path.exists('desc_cache.txt'):
        os.remove('desc_cache.txt')
    print("Finished removing cached caches!\n")



async def update_addons(shipped=False):
    steps_count = 5
    folders = [
        f"{globals.spice_config}\\Themes",
        f"{globals.spice_config}\\Extensions",
        f"{globals.spice_config}\\Customapps",
        f"{globals.spice_executable}\\Themes",
        f"{globals.spice_executable}\\Extensions",
        f"{globals.spice_executable}\\Customapps",
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
    
    Addons = {
        globals.THEMES_URL if shipped 
        else globals.THEMES_URL.replace(globals.THEMES_VERSION[17:], 'refs/heads/master'): f"{globals.spice_config}\\Themes.zip",
        
        globals.ADDONS_URL if shipped 
        else globals.ADDONS_URL.replace(globals.ADDONS_VERSION[14:], 'refs/heads/master'): f"{globals.spice_executable}\\Addons.zip",
    }

    await utils.simultaneous_chunked_download(
        Addons,
        "Shipped Official Addons.zip" if shipped 
        else "Newest Official Addons.zip",
    )

    shutil.unpack_archive(
        f"{globals.spice_config}\\Themes.zip",
        globals.spice_config
    )

    os.remove(
        f"{globals.spice_config}\\Themes.zip"
    )

    os.rename(
        f"{globals.spice_config}\\{globals.THEMES_VERSION if shipped else 'spicetify-themes-master'}",
        f"{globals.spice_config}\\Themes",
    )
    os.rename(
        f"{globals.spice_config}\\Themes\\Default",
        f"{globals.spice_config}\\Themes\\SpicetifyDefault",
    )
    shutil.move(
        f"{globals.spice_config}\\Themes\\SpicetifyDefault", f"{globals.spice_executable}\\Themes\\SpicetifyDefault"
    )

    for item in list(Path(f"{globals.spice_config}\\Themes").glob("*")):
        fullpath = str(item)
        if os.path.isdir(fullpath):
            filename = str(item.name)
            if filename[0] == ".":
                shutil.rmtree(fullpath)
        else:
            os.remove(fullpath)

    for item in list(Path(f"{globals.spice_config}\\Themes").glob("**/*.js")):
        fullpath = str(item)
        destpath = (f"{globals.spice_config}\\Extensions"
        + fullpath[fullpath.rfind('\\') : fullpath.rfind('.')]
        + ".js"
        )
        if os.path.exists(destpath):
            os.remove(destpath)
        shutil.move(fullpath, destpath)

    if os.path.exists(f"{globals.spice_executable}\\Addons"):
        shutil.rmtree(f"{globals.spice_executable}\\Addons")

    shutil.unpack_archive(
        f"{globals.spice_executable}\\Addons.zip",
        globals.spice_executable,
    )

    os.remove(
        f"{globals.spice_executable}\\Addons.zip"
    )

    os.rename(
        f"{globals.spice_executable}\\{globals.ADDONS_VERSION if shipped else 'spicetify-cli-master'}",
        f"{globals.spice_executable}\\Addons",
    )

    for item in os.listdir(f"{globals.spice_executable}\\Addons\\Extensions"):
        shutil.move(f"{globals.spice_executable}\\Addons\\Extensions\\{item}", f"{globals.spice_executable}\\Extensions")
    
    for item in os.listdir(f"{globals.spice_executable}\\Addons\\Customapps"):
        shutil.move(f"{globals.spice_executable}\\Addons\\Customapps\\{item}", f"{globals.spice_executable}\\Customapps")
    
    shutil.rmtree(f"{globals.spice_executable}\\Addons")
    
    if os.path.isfile(f"{globals.spice_config}\\Extensions\\eslintrc.js"):
        os.remove(f"{globals.spice_config}\\Extensions\\eslintrc.js")
    print("Finished downloading 'official' addons!\n")

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
    
    await utils.simultaneous_chunked_download(base if shipped else final, "Shipped Custom Addons.zip" if shipped else "Newest Custom Addons.zip")
    utils.verbose_print("")
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
                    shutil.move(str(src), str(unpacked_path))      
                if os.path.exists(f"{unpacked_path}\\{item}") and os.path.isdir(f"{unpacked_path}\\{item}"): # Cleanup
                    os.rmdir(f"{unpacked_path}\\{item}")

                # Moving all files with the js extension to {extensions}
                for src in Path(f"{unpacked_path}").glob("**/*.js"): # for files in {PARENT}\{ADDON-DUPE}\**\*.js where ** means any segment, null or otherwise.
                    if "Extensions" in str(src):
                        shutil.move(str(src), str(directory))
                if os.path.exists(unpacked_path) and os.path.isdir(unpacked_path) and "Extensions" in unpacked_path: # Cleanup
                    shutil.rmtree(unpacked_path)

                # Recovering Repos with > 1 theme
                if not os.path.exists(f"{unpacked_path}\\user.css") and "Themes" in unpacked_path:
                    for src in Path(f"{unpacked_path}").glob("**/*"):
                        if os.path.isdir(str(src)) and ".github" not in str(src):
                            shutil.move(str(src), f"{globals.spice_config}\\Themes")
                    if os.path.exists(unpacked_path) and os.path.isdir(unpacked_path):
                        shutil.rmtree(unpacked_path)

            # Moving all theme extensions to the extensions folder
            for item in list(Path(f"{globals.spice_config}\\Themes").glob("**/*.js")):
                fullpath = str(item)
                destpath = (f"{globals.spice_config}\\Extensions"
                + fullpath[fullpath.rfind('\\') : fullpath.rfind('.')]
                + ".js"
                )
                if os.path.exists(destpath):
                    os.remove(destpath)
                shutil.move(fullpath, destpath)

        else:
            utils.verbose_print(f"{unpacked_name} wasnt downloaded successfully...")
        print("Finished downloading 'custom' addons!\n")
        
        print(f"(4/{steps_count}) Caching pixmaps...")
        if os.path.exists('pix_cache.txt'):
            os.remove('pix_cache.txt')
        open('pix_cache.txt', 'w').close()
        globals.pix_cache.clear()

        themes = utils.list_config_available("themes")
        backgrounds = utils.theme_images()
        for theme in themes:
            background=str(backgrounds[themes.index(theme)])
            if background != "None":
                Brightness = gui.brightness(background)   
                pixmapByteArray = gui.buttonPixmap(bg=background, rounded=True, width=284, height=160, typing="ByteArray")
                globals.pix_cache[background] = [pixmapByteArray, Brightness]                
                with open('pix_cache.txt', 'a') as f:
                    f.write(f'{background}: {str(pixmapByteArray.toBase64())}, {Brightness}\n') 
        print("Finished caching pixmaps!\n")

        print(f"(5/{steps_count}) Caching descriptions...")
        if os.path.exists('desc_cache.txt'):
            os.remove('desc_cache.txt')
        else:
            open('desc_cache.txt', 'w').close()
        globals.desc_cache.clear()

        extensions=[]
        descriptions = utils.extension_descriptions()
        for extension in utils.list_config_available("extensions"):
            if extension.lower()[:-3] not in [x.lower() for x in utils.list_config_available("themes")]:
                extensions.append(extension)

        for extension in extensions:
            if extension[:-3] not in globals.desc_cache:
                globals.desc_cache[extension[:-3]] = descriptions[extensions.index(extension)]
                with open("desc_cache.txt", "a") as f:
                    f.write(
                        f'{extension[:-3]}: {descriptions[extensions.index(extension)]}\n'
                    )
        print("Finished caching extension descriptions!\n")


async def update_app():
    steps_count = 2
    json = await utils.latest_github_release()
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
    # Cleanup and restart.

    print(f"\n(2/{steps_count}) Extraction And Cleanup...")
    if not os.path.exists(f"{globals.cwd}\\Update.zip"):
        return None
    try:
        shutil.unpack_archive(f"{globals.cwd}\\Update.zip", f"{globals.cwd}\\Update")
    except:
        print("Windows Defender Is Blocking The Extraction Of The Update.zip in your CWD.\nPlease Disable It And Try Again.")
    os.remove(f"{globals.cwd}\\Update.zip")
    print("Finished Extraction And Cleanup!")
    if os.path.isdir(f"{globals.cwd}\\Update"):
        return True
