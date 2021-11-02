import sys
import traceback
from PyQt5 import QtWidgets
from qasync import asyncSlot

from modules import globals, core, utils
from modules.gui import *


class LicenseScreen(SlidingScreen):
    screen_name = "license_screen"

    def __init__(self, parent):
        super().__init__(parent=parent, icon="󰊛", title="License Agreement")

        self.license = QtWidgets.QPlainTextEdit(parent=self)
        # License text has weird width, compensate with left padding
        self.license.setStyleSheet(
            '\x1f            QPlainTextEdit {\x1f                padding: 0px 0px 0px 24px;\x1f                font-size: 7.5pt;\x1f            }\x1f        '
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
        connect(signal=bottom_bar.back.clicked, callback=globals.gui.close)
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
            buttons={
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
                    "next_screen": "config_theme_menu_screen",
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

        self.debug_mode = QtWidgets.QCheckBox(
            parent=self, text="Enable Debug Mode (more verbose)"
        )
        connect(
            signal=self.debug_mode.stateChanged,
            callback=lambda *_: setattr(
                globals, "verbose", self.debug_mode.isChecked()
            ),
        )
        clickable(self.debug_mode)
        self.layout().addWidget(self.debug_mode)

    @asyncSlot()
    async def shownCallback(self):
        is_installed = utils.is_installed()
        self.toggleButton("config", is_installed)
        self.toggleButton("uninstall", is_installed)
        self.toggleButton("update", is_installed)
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


class ConfigThemeMenuScreen(MenuScreen):
    screen_name = "config_theme_menu_screen"

    def __init__(self, parent):
        super().__init__(
            parent=parent,
            icon="󰠲",
            title="What theme do you want to use?",
            back_screen="main_menu_screen",
            scrollable=True,
            multichoice=False,
            buttons={},
            font_size_ratio=0.69,
            min_height=69,
            max_height=69,
            min_width=212,
            max_width=226,
        )

    @asyncSlot()
    async def shownCallback(self):
        themes = utils.list_config_available("themes")
        selected = self.getSelection()
        self.clearCurrentButtons()
        row = 0
        column = 0
        for theme in themes:
            if column == 2:
                column = 0
                row += 1
            self.addMenuButton(
                theme,
                text=theme,
                row=row,
                column=column,
                next_screen="config_colorscheme_menu_screen",
            )
            column += 1
        if not selected:
            selected = utils.find_config_entry("current_theme")
        if selected in self.buttons:
            self.buttons[selected].setChecked(True)
        super().shownCallback()


class ConfigColorschemeMenuScreen(MenuScreen):
    screen_name = "config_colorscheme_menu_screen"

    def __init__(self, parent):
        super().__init__(
            parent=parent,
            icon="󰸌",
            title="What colorscheme do you want for your theme?",
            back_screen="config_theme_menu_screen",
            scrollable=True,
            multichoice=False,
            buttons={},
            font_size_ratio=0.69,
            min_height=69,
            max_height=69,
            min_width=212,
            max_width=226,
        )

    @asyncSlot()
    async def shownCallback(self):
        bottom_bar = self.parent().parent().bottom_bar
        slider = self.parent().parent().slider

        theme = slider.config_theme_menu_screen.getSelection()
        colorschemes = utils.list_config_available("colorschemes", theme)
        if not colorschemes:
            self.clearCurrentButtons()
            self.buttons["none"] = QtWidgets.QLabel(
                parent=self.button_grid, text="This theme has no colorschemes."
            )
            self.button_grid.layout().addWidget(
                self.buttons["none"],
                0,
                0,
                QtCore.Qt.AlignBottom | QtCore.Qt.AlignHCenter,
            )
            self.buttons["nope"] = QtWidgets.QLabel(
                parent=self.button_grid, text="You can skip this screen!"
            )
            self.button_grid.layout().addWidget(
                self.buttons["nope"], 1, 0, QtCore.Qt.AlignTop | QtCore.Qt.AlignHCenter
            )
            connect(
                signal=bottom_bar.back.clicked,
                callback=lambda *_: slider.slideTo(
                    slider.config_theme_menu_screen, direction="back"
                ),
            )
            bottom_bar.back.setEnabled(True)
            connect(
                signal=bottom_bar.next.clicked,
                callback=lambda *_: slider.slideTo(
                    slider.config_extensions_menu_screen, direction="next"
                ),
            )
            bottom_bar.next.setEnabled(True)
            # super().shownCallback()
            return
        selected = self.getSelection()
        self.clearCurrentButtons()
        row = 0
        column = 0
        for colorscheme in colorschemes:
            if column == 2:
                column = 0
                row += 1
            self.addMenuButton(
                colorscheme,
                text=colorscheme,
                row=row,
                column=column,
                next_screen="config_extensions_menu_screen",
            )
            column += 1
        if not selected:
            selected = utils.find_config_entry("color_scheme")
        if selected in self.buttons:
            self.buttons[selected].setChecked(True)
        super().shownCallback()


class ConfigExtensionsMenuScreen(MenuScreen):
    screen_name = "config_extensions_menu_screen"

    def __init__(self, parent):
        super().__init__(
            parent=parent,
            icon="󰩦",
            title="What extensions do you want to enable?",
            back_screen="config_colorscheme_menu_screen",
            scrollable=True,
            multichoice=True,
            allow_no_selection=True,
            buttons={},
            font_size_ratio=0.69,
            min_height=69,
            max_height=69,
            min_width=212,
            max_width=226,
        )
        self.first_run = True

    @asyncSlot()
    async def shownCallback(self):
        extensions = utils.list_config_available("extensions")
        selected = self.getSelection()
        self.clearCurrentButtons()
        row = 0
        column = 0
        for extension in extensions:
            if extension[-3:] != ".js":
                continue
            extension = extension[:-3]
            if column == 2:
                column = 0
                row += 1
            self.addMenuButton(
                extension,
                text=extension,
                row=row,
                column=column,
                next_screen="config_customapps_menu_screen",
            )
            column += 1
        if self.first_run:
            self.first_run = False
            selected = [
                extension[:-3]
                for extension in utils.find_config_entry("extensions").split("|")
            ]
        for selection in selected:
            if selection in self.buttons:
                self.buttons[selection].setChecked(True)
        super().shownCallback()


class ConfigCustomappsMenuScreen(MenuScreen):
    screen_name = "config_customapps_menu_screen"

    def __init__(self, parent):
        super().__init__(
            parent=parent,
            icon="󰲌",
            title="What custom apps do you want to enable?",
            back_screen="config_extensions_menu_screen",
            scrollable=True,
            multichoice=True,
            allow_no_selection=True,
            buttons={},
            font_size_ratio=0.69,
            min_height=69,
            max_height=69,
            min_width=212,
            max_width=226,
        )
        self.first_run = True

    @asyncSlot()
    async def shownCallback(self):
        customapps = utils.list_config_available("customapps")
        selected = self.getSelection()
        self.clearCurrentButtons()
        row = 0
        column = 0
        for customapp in customapps:
            if column == 2:
                column = 0
                row += 1
            self.addMenuButton(
                customapp,
                text=customapp,
                row=row,
                column=column,
                next_screen="config_confirm_screen",
            )
            column += 1
        if self.first_run:
            self.first_run = False
            selected = utils.find_config_entry("custom_apps").split("|")
        for selection in selected:
            if selection in self.buttons:
                self.buttons[selection].setChecked(True)
        super().shownCallback()


class ConfigConfirmScreen(ConfirmScreen):
    screen_name = "config_confirm_screen"

    def __init__(self, parent):
        super().__init__(
            parent=parent,
            icon="󰢻",
            title="Apply Config",
            subtitle="Details of this config:",
            rundown="",
            action_name="Apply",
            back_screen="config_customapps_menu_screen",
            next_screen="config_log_screen",
        )

    @asyncSlot()
    async def shownCallback(self):
        slider = self.parent().parent().slider

        self.rundown.setMarkdown(
            f"""
 - **Theme**: {slider.config_theme_menu_screen.getSelection()}
 - **Color Scheme**: {slider.config_colorscheme_menu_screen.getSelection() or "Default"}
 - **Extensions**: {", ".join(slider.config_extensions_menu_screen.getSelection()) or "None"}
 - **Custom Apps**: {", ".join(slider.config_customapps_menu_screen.getSelection()) or "None"}
""".strip()
        )
        super().shownCallback()


class ConfigLogScreen(ConsoleLogScreen):
    screen_name = "config_log_screen"

    def __init__(self, parent):
        super().__init__(parent=parent, icon="󰢻", title="Config Log")

    @asyncSlot()
    async def shownCallback(self):
        slider = self.parent().parent().slider

        # Configure output widget
        await self.setup()

        # Actual config
        theme = slider.config_theme_menu_screen.getSelection()
        colorscheme = slider.config_colorscheme_menu_screen.getSelection() or ""
        extensions = slider.config_extensions_menu_screen.getSelection()
        customapps = slider.config_customapps_menu_screen.getSelection()
        try:
            await core.apply_config(theme, colorscheme, extensions, customapps)
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
            buttons={
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
