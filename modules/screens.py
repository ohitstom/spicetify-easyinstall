import sys
import traceback
from PyQt5 import QtWidgets
from qasync import asyncSlot

from modules import globals, core
from modules.gui import *


class LicenseScreen(SlidingScreen):
    screen_name = "license_screen"

    def __init__(self, parent):
        super().__init__(parent=parent, icon="󰊛", title="License Agreement")

        self.license = QtWidgets.QPlainTextEdit(parent=self)
        # License text has weird width, compensate with left padding
        self.license.setStyleSheet(
            f"""
            QPlainTextEdit {{
                padding: 0px 0px 0px 24px;
                font-size: 7.5pt;
            }}
        """
        )
        self.license.setPlainText(globals.LICENSE_AGREEMENT)
        self.license.setReadOnly(True)
        self.license.children()[3].children()[0].setDocumentMargin(12)
        self.layout().addWidget(self.license)

        self.accept_license = QtWidgets.QCheckBox(
            parent=self, text="I accept the license agreement"
        )
        clickable(self.accept_license)
        self.layout().addWidget(self.accept_license)

    @asyncSlot()
    async def shownCallback(self):
        bottom_bar = self.parent().parent().bottom_bar
        slider = self.parent().parent().slider

        # Toggle the next buttom when accept checkbox is toggled
        connect(
            signal=self.accept_license.stateChanged,
            callback=lambda *_: bottom_bar.next.setEnabled(
                self.accept_license.isChecked()
            ),
        )

        # Setup quit button
        connect(signal=bottom_bar.back.clicked, callback=globals.app.quit)
        bottom_bar.back.setText("Quit")
        bottom_bar.back.setEnabled(True)
        # Setup next button
        connect(
            signal=bottom_bar.next.clicked,
            callback=lambda *_: slider.slideTo(
                slider.main_menu_screen, direction="next"
            ),
        )
        bottom_bar.next.setEnabled(self.accept_license.isChecked())


class MainMenuScreen(MenuScreen):
    screen_name = "main_menu_screen"

    def __init__(self, parent):
        super().__init__(
            parent=parent,
            icon="󰙪",
            title="What do you want to do?",
            back_screen="license_screen",
            options={
                "install": {
                    "icon": "󰄠",
                    "text": "Install",
                    "desc": "",
                    "next_screen": "install_confirm_screen",
                    "row": 0,
                    "column": 0,
                },
                "config": {
                    "icon": "󰢻",
                    "text": "Config",
                    "desc": "",
                    "next_screen": "current_screen",
                    "row": 0,
                    "column": 1,
                },
                "uninstall": {
                    "icon": "󰩺",
                    "text": "Uninstall",
                    "desc": "",
                    "next_screen": "uninstall_confirm_screen",
                    "row": 1,
                    "column": 0,
                },
                "update": {
                    "icon": "󰓦",
                    "text": "Update",
                    "desc": "",
                    "next_screen": "update_menu_screen",
                    "row": 1,
                    "column": 1,
                },
            },
        )

        self.buttons["config"].setEnabled(False)  # FIXME: implement config section

        self.debug_mode = QtWidgets.QCheckBox(
            parent=self, text="Enable Debug Mode (more verbose)"
        )
        clickable(self.debug_mode)
        self.layout().addWidget(self.debug_mode)

    @asyncSlot()
    async def shownCallback(self):
        super().shownCallback()


class InstallConfirmScreen(ConfirmScreen):
    screen_name = "install_confirm_screen"

    def __init__(self, parent):
        super().__init__(
            parent=parent,
            icon="󰄠",
            title="Install Spicetify",
            subtitle="Details of this install:",
            rundown=globals.INSTALL_RUNDOWN_MD,
            action_name="Install",
            back_screen="main_menu_screen",
            next_screen="install_log_screen",
        )

        self.launch_after = QtWidgets.QCheckBox(parent=self, text="Launch when ready")
        clickable(self.launch_after)
        self.layout().addWidget(self.launch_after)

    @asyncSlot()
    async def shownCallback(self):
        super().shownCallback()


class InstallLogScreen(ConsoleLogScreen):
    screen_name = "install_log_screen"

    def __init__(self, parent):
        super().__init__(parent=parent, icon="󰉺", title="Install Log")

    @asyncSlot()
    async def shownCallback(self):
        slider = self.parent().parent().slider

        # Configure output widget
        await self.setup()

        # Actual install
        try:
            await core.install(
                launch=slider.install_confirm_screen.launch_after.isChecked()
            )
        except Exception:
            exc = "".join(traceback.format_exception(*sys.exc_info()))
            print(exc)
            print("\n\n^^ SOMETHING WENT WRONG! ^^")

        # Disconnect console output
        await self.cleanup()


class UninstallConfirmScreen(ConfirmScreen):
    screen_name = "uninstall_confirm_screen"

    def __init__(self, parent):
        super().__init__(
            parent=parent,
            icon="󰩺",
            title="Uninstall Spicetify",
            subtitle="Details of this uninstall:",
            rundown=globals.UNINSTALL_RUNDOWN_MD,
            action_name="Uninstall",
            back_screen="main_menu_screen",
            next_screen="uninstall_log_screen",
        )

    @asyncSlot()
    async def shownCallback(self):
        super().shownCallback()


class UninstallLogScreen(ConsoleLogScreen):
    screen_name = "uninstall_log_screen"

    def __init__(self, parent):
        super().__init__(parent=parent, icon="󰉺", title="Uninstall Log")

    @asyncSlot()
    async def shownCallback(self):
        # Configure output widget
        await self.setup()

        # Actual uninstall
        try:
            await core.uninstall()
        except Exception:
            exc = "".join(traceback.format_exception(*sys.exc_info()))
            print(exc)
            print("\n\n^^ SOMETHING WENT WRONG! ^^")

        # Disconnect console output
        await self.cleanup()


class UpdateMenuScreen(MenuScreen):
    screen_name = "update_menu_screen"

    def __init__(self, parent):
        super().__init__(
            parent=parent,
            icon="󰓦",
            title="What do you want to update?",
            back_screen="main_menu_screen",
            options={
                "shipped": {
                    "icon": "󰏗",
                    "text": "Shipped",
                    "desc": "Preinstalled addons",
                    "next_screen": "update_shipped_confirm_screen",
                    "row": 0,
                    "column": 0,
                },
                "latest": {
                    "icon": "󰚰",
                    "text": "Latest",
                    "desc": "Third party addons",
                    "next_screen": "update_latest_confirm_screen",
                    "row": 0,
                    "column": 1,
                },
            },
        )

    @asyncSlot()
    async def shownCallback(self):
        super().shownCallback()


class UpdateShippedConfirmScreen(ConfirmScreen):
    screen_name = "update_shipped_confirm_screen"

    def __init__(self, parent):
        super().__init__(
            parent=parent,
            icon="󰏗",
            title="Update Shipped Addons",
            subtitle="Details of this update:",
            rundown=globals.UPDATE_SHIPPED_RUNDOWN_MD,
            action_name="Update",
            back_screen="update_menu_screen",
            next_screen="update_shipped_log_screen",
        )

    @asyncSlot()
    async def shownCallback(self):
        super().shownCallback()


class UpdateShippedLogScreen(ConsoleLogScreen):
    screen_name = "update_shipped_log_screen"

    def __init__(self, parent):
        super().__init__(parent=parent, icon="󰉺", title="Update Log")

    @asyncSlot()
    async def shownCallback(self):
        # Configure output widget
        await self.setup()

        # Actual update
        try:
            await core.update_addons("shipped")
        except Exception:
            exc = "".join(traceback.format_exception(*sys.exc_info()))
            print(exc)
            print("\n\n^^ SOMETHING WENT WRONG! ^^")

        # Disconnect console output
        await self.cleanup()


class UpdateLatestConfirmScreen(ConfirmScreen):
    screen_name = "update_latest_confirm_screen"

    def __init__(self, parent):
        super().__init__(
            parent=parent,
            icon="󰚰",
            title="Update Latest Addons",
            subtitle="Details of this update:",
            rundown=globals.UPDATE_LATEST_RUNDOWN_MD,
            action_name="Update",
            back_screen="update_menu_screen",
            next_screen="update_latest_log_screen",
        )

    @asyncSlot()
    async def shownCallback(self):
        super().shownCallback()


class UpdateLatestLogScreen(ConsoleLogScreen):
    screen_name = "update_latest_log_screen"

    def __init__(self, parent):
        super().__init__(parent=parent, icon="󰉺", title="Update Log")

    @asyncSlot()
    async def shownCallback(self):
        # Configure output widget
        await self.setup()

        # Actual update
        try:
            await core.update_addons("latest")
        except Exception:
            exc = "".join(traceback.format_exception(*sys.exc_info()))
            print(exc)
            print("\n\n^^ SOMETHING WENT WRONG! ^^")

        # Disconnect console output
        await self.cleanup()
