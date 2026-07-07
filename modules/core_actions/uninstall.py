import asyncio
import os
import shutil
from pathlib import Path
import re

from modules import globals, utils, gui, install_helpers

environ_check = (f'& "{globals.spice_executable}\\spicetify.exe"' if os.path.isdir(globals.spice_executable)  else "spicetify")


async def uninstall(spotify=False, super_wipe=False):
    current_step = 0
    steps_count = 3
    if spotify:
        steps_count += 1
    if super_wipe:
        steps_count += 1

    folders = [
        globals.spice_executable,
        globals.spice_config,
        globals.temp,
    ]

    current_step += 1
    print(f"\n({current_step}/{steps_count}) Restoring Spotify...")
    await utils.powershell(f"{environ_check} restore -q", start_new_session=False)

    current_step += 1
    print(f"\n({current_step}/{steps_count}) Un-wiring path...")
    await utils.powershell(
        '\n'.join([
            '$path = [System.Environment]::GetEnvironmentVariable("PATH", "User")',
            '$sp_dir = "${env:LOCALAPPDATA}\\spicetify"',
            '$paths = ($path.Split(";") | Where-Object { $_.TrimEnd("") -ne $sp_dir }) -join ";"',
            '$is_in_path = "$path".Contains("$sp_dir") -or "$path".Contains("${sp_dir}")',
            'if ($is_in_path) {[Environment]::SetEnvironmentVariable("PATH", "${paths}", "User")}',
            '$env:Path = $paths'
        ]), start_new_session=False
    )

    current_step += 1
    print(f"\n({current_step}/{steps_count}) Wiping folders...")
    for folder in folders:
        try:
            if not os.path.exists(folder) or len(os.listdir(folder)) == 0:
                print(f'"{folder}" is already empty.')
            else:
                shutil.rmtree(folder, ignore_errors=True)
                print(f'"{folder}" has been deleted.')
        except Exception as e:
            print(f'"{folder}" was not deleted: {e}.')

    if spotify:
        current_step += 1
        print(f"\n({current_step}/{steps_count}) Uninstalling Spotify...")
        await install_helpers.uninstall_spotify()

    if super_wipe:
        current_step += 1
        print(f"\n({current_step}/{steps_count}) Performing Super Wipe...")
        from modules.state_manager import state
        if os.path.exists(state.installer_config):
            shutil.rmtree(state.installer_config, ignore_errors=True)
            print("Successfully super-wiped spicetify-easyinstall state!")

    print("\nFinished Uninstall!")
