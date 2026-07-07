import asyncio
import os
from modules import globals, utils, install_helpers
from modules.state_manager import state

async def install(launch=False, leaveSpotify=False, spicetify_version="Latest", spotify_version="Latest", pin_date=None, themes_version="Latest"):
    current_step = 0
    steps_count = 11
    if leaveSpotify:
        steps_count -= 3

    if spicetify_version != "Latest" and spicetify_version in globals.SPICETIFY_DATES and not pin_date:
        pin_date = globals.SPICETIFY_DATES[spicetify_version]

    needs_prep = (spicetify_version == "Latest" or spotify_version == "Latest" or pin_date is not None or themes_version == "Latest")
    if needs_prep:
        steps_count += 2

    if needs_prep:
        current_step += 1
        print(f"\n({current_step}/{steps_count}) Preparing variables...")
        filenames = await install_helpers.prepare_variables(spicetify_version, spotify_version, pin_date, themes_version, needs_prep)
        print("Finished preparing variables!")
    else:
        filenames = []
        state.runtime_spotify_version = spotify_version
        state.runtime_spicetify_version = spicetify_version
        state.runtime_themes_version = themes_version

    current_step += 1
    print(f"\n({current_step}/{steps_count}) Backing Up Credentials...")
    install_helpers.backup_credentials()
    print("Finished backing up!")

    current_step += 1
    print(f"\n({current_step}/{steps_count}) Uninstalling Spotify...")
    await install_helpers.uninstall_spotify()

    current_step += 1
    print(f"\n({current_step}/{steps_count}) Wiping folders...")
    install_helpers.wipe_folders(leaveSpotify)
    print("Finished wiping folders!")

    current_step += 1
    print(f"\n({current_step}/{steps_count}) Downloading correct Spotify version...")
    temp_dest, local_found = await install_helpers.download_spotify(filenames)
    if local_found:
        print("Skipping download phase (found locally).")
    else:
        print("Download succeeded and verified!")

    current_step += 1
    print(f"\n({current_step}/{steps_count}) Installing Spotify...")
    await install_helpers.install_spotify_exe(temp_dest)
    print("Finished installing Spotify!")

    current_step += 1
    print(f"\n({current_step}/{steps_count}) Installing Spicetify...")
    await install_helpers.install_spicetify()

    current_step += 1
    print(f"\n({current_step}/{steps_count}) Preventing Spotify from updating...")
    await install_helpers.prevent_spotify_updates()
    print("Finished blocking Spotify updates!")

    current_step += 1
    print(f"\n({current_step}/{steps_count}) Downloading 'official' themes...")
    await install_helpers.download_official_themes()
    print("Finished downloading 'official' themes!")

    current_step += 1
    print(f"\n({current_step}/{steps_count}) Downloading 'custom' addons...")
    await install_helpers.download_custom_addons()
    print("Finished downloading 'custom' addons!")

    current_step += 1
    print(f"\n({current_step}/{steps_count}) Restoring Credentials...")
    await install_helpers.restore_credentials()
    print("Finished restoring!")

    current_step += 1
    print(f"\n({current_step}/{steps_count}) Caching pixmaps...")
    await install_helpers.cache_pixmaps()
    print("Finished caching pixmaps!")

    current_step += 1
    print(f"\n({current_step}/{steps_count}) Caching descriptions...")
    await install_helpers.cache_descriptions()
    print("Finished caching extension descriptions!")

    if launch:
        print("Launching Spotify...")
        await utils.start_process(f"{globals.appdata}\\Spotify\\Spotify.exe")
