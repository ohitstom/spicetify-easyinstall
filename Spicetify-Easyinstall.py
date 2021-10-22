# Setup logging console to file output
from modules import logger

# Sanity check: try importing all needed packages
from qasync import asyncSlot, QApplication
from PyQt5 import QtCore, QtGui, QtWidgets
import win32api, win32event, winerror
import functools
import aiofiles
import asyncio
import aiohttp
import psutil
import qasync
import sys

# Local imports
from modules import globals, core, gui, progress, screens, singleton, utils

# Setup singleton: only one app instance running at a time
globals.singleton = singleton.Singleton("spicetify-easyinstall")


# Most of this is the setup for qasync, allowing the gui to run asynchronously
# instead of threaded. This code was taken from the example at the qasync repo:
# https://github.com/CabbageDevelopment/qasync/blob/master/examples/aiohttp_fetch.py

async def main():
    def close_future(future, loop):
        loop.call_later(10, future.cancel)
        future.cancel("Close Application")
    future = asyncio.Future()
    globals.app = QApplication.instance()
    globals.app.setStyleSheet(gui.QSS)
    if hasattr(globals.app, 'aboutToQuit'):
        getattr(globals.app, 'aboutToQuit').connect(functools.partial(close_future, future, asyncio.get_event_loop()))

    globals.gui = gui.MainWindow()
    globals.gui.show()

    await future
    return True


if __name__ == "__main__":
    try:
        qasync.run(main())
    except asyncio.exceptions.CancelledError:
        sys.exit(0)
