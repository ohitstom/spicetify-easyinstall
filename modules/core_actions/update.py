import asyncio
import os
import shutil
from pathlib import Path
import re

from modules import globals, utils, gui

environ_check = (f'& "{globals.spice_executable}\\spicetify.exe"' if os.path.isdir(globals.spice_executable)  else "spicetify")


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
        if re.search(r'theme(?:\.|\.js)', fullpath):
            continue
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
    print("Finished downloading 'custom' addons!\n")


    print(f"(4/{steps_count}) Caching pixmaps...")
    if os.path.exists(globals.pix_cache_path):
        os.remove(globals.pix_cache_path)
    open(globals.pix_cache_path, 'w').close()
    globals.pix_cache.clear()

    themes = utils.list_config_available("themes")
    backgrounds = utils.theme_images()
    for theme in themes:
        background=str(backgrounds[themes.index(theme)])
        if background != "None":
            Brightness = gui.brightness(background)
            pixmapByteArray = gui.buttonPixmap(bg=background, rounded=True, width=284, height=160, typing="ByteArray")
            globals.pix_cache[background] = [pixmapByteArray, Brightness]
            with open(globals.pix_cache_path, 'a') as f:
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

    if os.path.exists(f"{globals.installer_config}\\Update.zip"):
        os.remove(f"{globals.installer_config}\\Update.zip")
    if os.path.isdir(f"{globals.installer_config}\\Update"):
        shutil.rmtree(f"{globals.installer_config}\\Update")

    # >[Section 1]<
    # Download the latest release from GitHub and extract it to the current directory.

    print(f"(1/{steps_count}) Downloading Update from {globals.RELEASE} to {latest_release}...")
    await utils.chunked_download(
        url=json["assets"][0]["browser_download_url"],
        path=(f"{globals.installer_config}\\Update.zip"),
        label=(f"{globals.installer_config}\\Update.zip") if globals.verbose else "Update.zip",
    )
    print("Finished Downloading Update!")

    # >[Section 2]<
    # Cleanup and restart.

    print(f"\n(2/{steps_count}) Extraction And Cleanup...")
    if not os.path.exists(f"{globals.installer_config}\\Update.zip"):
        return None
    try:
        shutil.unpack_archive(f"{globals.installer_config}\\Update.zip", f"{globals.installer_config}\\Update")
    except:
        print("Windows Defender Is Blocking The Extraction Of The Update.zip in your installer_config.\nPlease Disable It And Try Again.")
    os.remove(f"{globals.installer_config}\\Update.zip")
    print("Finished Extraction And Cleanup!")
    if os.path.isdir(f"{globals.installer_config}\\Update"):
        return True


