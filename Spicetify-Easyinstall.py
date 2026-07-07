#  ______  ______  __  ______  ______  ______  __  ______  __  __         ______  ______  ______  __  __  __  __   __  ______  ______  ______  __      __
# /\  ___\/\  == \/\ \/\  ___\/\  ___\/\__  _\/\ \/\  ___\/\ \_\ \       /\  ___\/\  __ \/\  ___\/\ \_\ \/\ \/\ "-.\ \/\  ___\/\__  _\/\  __ \/\ \    /\ \
# \ \___  \ \  _-/\ \ \ \ \___\ \  __\\/_/\ \/\ \ \ \  __\\ \____ \      \ \  __\\ \  __ \ \___  \ \____ \ \ \ \ \-.  \ \___  \/_/\ \/\ \  __ \ \ \___\ \ \____
#  \/\_____\ \_\   \ \_\ \_____\ \_____\ \ \_\ \ \_\ \_\   \/\_____\      \ \_____\ \_\ \_\/\_____\/\_____\ \_\ \_\\"\_\/\_____\ \ \_\ \ \_\ \_\ \_____\ \_____\
#   \/_____/\/_/    \/_/\/_____/\/_____/  \/_/  \/_/\/_/    \/_____/       \/_____/\/_/\/_/\/_____/\/_____/\/_/\/_/ \/_/\/_____/  \/_/  \/_/\/_/\/_____/\/_____/

import asyncio
import sys

# Only start if running as main and not import
if __name__ == "__main__":
    # Setup logging console to file output
    from modules import logger
    import os
    print(f"DEBUG: os.getcwd() = {os.getcwd()}")
    print(f"DEBUG: sys._MEIPASS = {getattr(sys, '_MEIPASS', None)}")
    print(f"DEBUG: sys.executable = {sys.executable}")
    print(f"DEBUG: __file__ = {__file__}")

    # Sanity check: try importing all needed third party libs
    from PyQt5 import QtCore, QtGui, QtWidgets
    from qasync import asyncSlot, QEventLoop
    import win32api, win32event, winerror
    import aiofiles
    import aiohttp
    import psutil

    # Sanity checck: try importing all local modules
    from modules import globals, gui, progress, screens, singleton, utils, styles
    from modules.state_manager import state

    import argparse
    parser = argparse.ArgumentParser(description="Spicetify Easyinstall")
    parser.add_argument("--diagnose", action="store_true", help="Dump diagnostics to diagnostics.json and exit")
    parser.add_argument("--debug", action="store_true", help="Enable verbose debug logging")
    args, unknown = parser.parse_known_args()

    if args.debug:
        globals.verbose = True
        print("Debug mode enabled.")

    if args.diagnose:
        import json
        diag = {
            "state_config": state._config,
            "globals": {k: getattr(globals, k) for k in dir(globals) if not k.startswith("__") and isinstance(getattr(globals, k), (str, int, float, bool, dict, list))},
            "spicetify_installed": utils.is_installed(),
            "env": {
                "APPDATA": os.environ.get("APPDATA"),
                "LOCALAPPDATA": os.environ.get("LOCALAPPDATA"),
                "USERNAME": os.environ.get("USERNAME"),
            }
        }
        with open("diagnostics.json", "w", encoding="utf-8") as f:
            json.dump(diag, f, indent=4)
        print("Diagnostics dumped to diagnostics.json")
        sys.exit(0)

    # Setup singleton: only one app instance running at a time
    # state.singleton = singleton.Singleton("spicetify-easyinstall")

    # Create App
    state.app = QtWidgets.QApplication(sys.argv)
    state.app.setStyle(styles.QuickToolTipStyle())
    state.app.setStyleSheet(styles.QSS)

    # Configure asyncio loop to work with PyQt5
    asyncio.set_event_loop_policy(asyncio.WindowsSelectorEventLoopPolicy())
    loop = QEventLoop(state.app)
    asyncio.set_event_loop(loop)

    # Fetch updates asynchronously in the background so they are ready by the time the user opens settings
    asyncio.ensure_future(utils.fetch_data_updates())

    # Setup GUI
    state.gui = gui.MainWindow()
    state.gui.show()

    # Set off loop
    with loop:
        sys.exit(loop.run_until_complete(state.gui.exit_request.wait()))