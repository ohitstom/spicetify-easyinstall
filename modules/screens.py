import os
import sys
import traceback
from difflib import SequenceMatcher

from PyQt5 import QtCore, QtWidgets, QtGui
from qasync import asyncSlot

from modules import core, globals, gui, logger, utils


class LicenseScreen(gui.SlidingScreen):
    screen_name = "license_screen"
    def __init__(self, parent):
        super().__init__(parent=parent, icon="󰊛", title="License Agreement")

        self.license = QtWidgets.QPlainTextEdit(parent=self)
        # License text has weird width, compensate with left padding
        self.license.setStyleSheet(
            f"""
            QPlainTextEdit {{
                font-size: 8.75pt;
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
        gui.clickable(self.accept_license)
        self.layout().addWidget(self.accept_license)

    @asyncSlot()
    async def shownCallback(self):
        bottom_bar = self.parent().parent().bottom_bar
        slider = self.parent().parent().slider
        bottom_bar.back.setEnabled(False)
        bottom_bar.next.setEnabled(False)

        # Wait for animations to finish before enabling buttons again
        await slider.waitForAnimations()

        # Toggle the next buttom when accept checkbox is toggled
        gui.connect(
            signal=self.accept_license.stateChanged,
            callback=lambda *_: bottom_bar.next.setEnabled(
                self.accept_license.isChecked()
            ),
        )

        # Setup quit button
        gui.connect(signal=bottom_bar.back.clicked, callback=globals.gui.close)
        bottom_bar.back.setText("Quit")
        bottom_bar.back.setEnabled(True)
        # Setup next button
        gui.connect(
            signal=bottom_bar.next.clicked,
            callback=lambda *_: slider.slideTo(
                slider.main_menu_screen, direction="next"
            ),
        )
        bottom_bar.next.setEnabled(self.accept_license.isChecked())


class MainMenuScreen(gui.MenuScreen):
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
                    "icon": "󰸌",
                    "text": "Customize",
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
                    "icon": "󰚰",
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
        gui.connect(
            signal=self.debug_mode.stateChanged,
            callback=lambda *_: setattr(
                globals, "verbose", self.debug_mode.isChecked()
            ),
        )
        gui.clickable(self.debug_mode)
        self.layout().addWidget(self.debug_mode)

    @asyncSlot()
    async def shownCallback(self):
        bottom_bar = self.parent().parent().bottom_bar
        bottom_bar.back.setEnabled(False)
        bottom_bar.next.setEnabled(False)

        is_installed = utils.is_installed()
        self.toggleButton("config", is_installed)
        self.toggleButton("uninstall", is_installed)
        self.toggleButton("update", is_installed)
        super().shownCallback()
class InstallConfirmScreen(gui.ConfirmScreen):
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

        self.launch_after = QtWidgets.QCheckBox(parent=self, text="Launch When Ready")
        self.use_latest = QtWidgets.QCheckBox(parent=self, text="Install Latest Versions - Can Be Unstable!")
        gui.clickable(self.launch_after)
        gui.clickable(self.use_latest)
        self.layout().addWidget(self.launch_after)
        self.layout().addWidget(self.use_latest)

    @asyncSlot()
    async def shownCallback(self):
        bottom_bar = self.parent().parent().bottom_bar
        slider = self.parent().parent().slider
        bottom_bar.back.setEnabled(False)
        bottom_bar.next.setEnabled(False)            

        # Wait for animations to finish before enabling buttons again
        await slider.waitForAnimations()

        # Connect buttons to their respective functions
        gui.connect(
            signal=slider.install_confirm_screen.use_latest.clicked,
            callback=lambda *_: slider.install_confirm_screen.shownCallback(),
        )

        # Variables
        SPOTIFY_VERSION_OLD = ".".join(utils.find_config_data("app.last-launched-version", config=f'{globals.appdata}\\Spotify\\prefs', splitchar="=").strip('"').split(".")[:3])
        SPOTIFY_VERSION_UPDATE = ".".join(globals.SPOTIFY_VERSION[18:-4].split(".")[:3])     
        SPICETIFY_VERSION = globals.SPICETIFY_VERSION
        SPICETIFY_VERSION_OLD = utils.find_config_data("with")
        THEMES_VERSION = globals.THEMES_VERSION[17:-33]
        
        if slider.install_confirm_screen.use_latest.isChecked():
            try:
                spice_json = await utils.latest_github_release(Spicetify=True)
                spotify_str = await utils.latest_spotify_release(name=True)
                theme_json = await utils.latest_github_commit()
                SPICETIFY_VERSION = spice_json["tag_name"][1:]
                SPOTIFY_VERSION_UPDATE = ".".join(spotify_str.split(".")[:3])
                THEMES_VERSION = theme_json["sha"][:-33]
            
            except Exception as e:
                msgBox = QtWidgets.QMessageBox(
                    QtWidgets.QMessageBox.Warning, 
                    "Error!", 
                    "Rate Limited.", 
                    detailedText = f'Rate limited, If you proceed with installing the latest versions its likely to fail.\n\nError: {e}.',
                    buttons = QtWidgets.QMessageBox.Ignore | QtWidgets.QMessageBox.Cancel, 
                    flags = QtCore.Qt.FramelessWindowHint
                )
                msgBox.setStyleSheet("color:white;background:black")
                
                if msgBox.exec() == QtWidgets.QMessageBox.Cancel:
                    slider.install_confirm_screen.use_latest.setChecked(False)

        # Format rundown message
        formatted = globals.INSTALL_RUNDOWN_MD.format(
            f"{SPICETIFY_VERSION_OLD} -> "
            if SPICETIFY_VERSION_OLD != SPICETIFY_VERSION
            and SPICETIFY_VERSION_OLD != "Path NULL"
            and SPICETIFY_VERSION_OLD != ""
            and utils.is_installed()
            else "",
            SPICETIFY_VERSION,
            f"{SPOTIFY_VERSION_OLD} -> "
            if SPOTIFY_VERSION_OLD != SPOTIFY_VERSION_UPDATE
            and SPOTIFY_VERSION_OLD != "Path NULL"
            and os.path.isdir(f"{globals.appdata}\\Spotify")
            else "",
            SPOTIFY_VERSION_UPDATE,
            THEMES_VERSION,
        )     
        self.rundown.setMarkdown(formatted)
        super().shownCallback()

class InstallLogScreen(gui.ConsoleLogScreen):
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
                launch=slider.install_confirm_screen.launch_after.isChecked(),
                latest=slider.install_confirm_screen.use_latest.isChecked()
            )
        except Exception:
            exc = "".join(traceback.format_exception(*sys.exc_info()))
            print(exc)
            print("\n\n^^ SOMETHING WENT WRONG! ^^")

        # Disconnect console output
        await self.cleanup()


class ConfigThemeMenuScreen(gui.MenuScreen):
    screen_name = "config_theme_menu_screen"

    def __init__(self, parent):
        super().__init__(
            parent=parent,
            icon="󰥶",
            title="What theme do you want to use?",
            back_screen="main_menu_screen",
            scrollable=True,
            multichoice=False,
            buttons={},
            font_size_ratio=0.75,
            min_height=146,
            max_height=146,
            min_width=260,
            max_width=260,
        )

    @asyncSlot()
    async def shownCallback(self):
        bottom_bar = self.parent().parent().bottom_bar
        bottom_bar.back.setEnabled(False)
        bottom_bar.next.setEnabled(False)
        
        themes = utils.list_config_available("themes")
        backgrounds = utils.theme_images()
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
                background=str(backgrounds[themes.index(theme)]),
                row=row,
                column=column,
                next_screen="config_colorscheme_menu_screen",
            )
            column += 1
        if not selected:
            selected = utils.find_config_data("current_theme")
        self.selectButtons(selected)
        super().shownCallback()


class ConfigColorschemeMenuScreen(gui.MenuScreen):
    screen_name = "config_colorscheme_menu_screen"

    def __init__(self, parent):
        super().__init__(
            parent=parent,
            icon="󰉦",
            title="What colorscheme do you want for your theme?",
            back_screen="config_theme_menu_screen",
            scrollable=True,
            multichoice=False,
            buttons={},
            font_size_ratio=0.75,
            min_height=146,
            max_height=146,
            min_width=260,
            max_width=260,
        )

    @asyncSlot()
    async def shownCallback(self):
        bottom_bar = self.parent().parent().bottom_bar
        slider = self.parent().parent().slider
        bottom_bar.back.setEnabled(False)
        bottom_bar.next.setEnabled(False)

        theme = slider.config_theme_menu_screen.getSelection()
        colorschemes = utils.list_config_available("colorschemes", theme)
        if not colorschemes or len(colorschemes) == 1:
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
            await slider.waitForAnimations()
            gui.connect(
                signal=bottom_bar.back.clicked,
                callback=lambda *_: slider.slideTo(
                    slider.config_theme_menu_screen, direction="back"
                ),
            )
            bottom_bar.back.setEnabled(True)
            gui.connect(
                signal=bottom_bar.next.clicked,
                callback=lambda *_: slider.slideTo(
                    slider.config_extensions_menu_screen, direction="next"
                ),
            )
            bottom_bar.next.setEnabled(True)
            bottom_bar.next.setText("Skip")
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
            selected = utils.find_config_data("color_scheme")
        self.selectButtons(selected)
        super().shownCallback()


class ConfigExtensionsMenuScreen(gui.MenuScreen):
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
            font_size_ratio=0.75,
            min_height=146,
            max_height=146,
            min_width=260,
            max_width=260,
        )
        self.first_run = True

    @asyncSlot()
    async def shownCallback(self):
        bottom_bar = self.parent().parent().bottom_bar
        bottom_bar.back.setEnabled(False)
        bottom_bar.next.setEnabled(False)
        slider = self.parent().parent().slider

        # Removing theme extensions
        extensions=[]
        for extension in utils.list_config_available("extensions"):
            if extension.lower()[:-3] not in [x.lower() for x in utils.list_config_available("themes")]:
                extensions.append(extension)

        descriptions = utils.extension_descriptions()
        selected = self.getSelection()
        self.clearCurrentButtons()
        row = 0
        column = 0
        for extension in extensions:
            if extension[-3:] != ".js":
                continue
            if ".script" in extension or "eslint" in extension:
                continue
            if column == 2:
                column = 0
                row += 1
            self.addMenuButton(
                extension[:-3],
                text=extension[:-3],
                desc=descriptions[extensions.index(extension)],
                row=row,
                column=column,
                next_screen="config_customapps_menu_screen",
            )
            column += 1

        if self.first_run:
            self.first_run = False
            selected = [
                extension[:-3]
                for extension in utils.find_config_data("extensions").split("|")
            ]
        self.selectButtons(selected)
        super().shownCallback()


class ConfigCustomappsMenuScreen(gui.MenuScreen):
    screen_name = "config_customapps_menu_screen"

    def __init__(self, parent):
        super().__init__(
            parent=parent,
            icon="󰀻",
            title="What custom apps do you want to enable?",
            back_screen="config_extensions_menu_screen",
            scrollable=True,
            multichoice=True,
            allow_no_selection=True,
            buttons={},
            font_size_ratio=0.75,
            min_height=146,
            max_height=146,
            min_width=260,
            max_width=260,
        )
        self.first_run = True

    @asyncSlot()
    async def shownCallback(self):
        bottom_bar = self.parent().parent().bottom_bar
        bottom_bar.back.setEnabled(False)
        bottom_bar.next.setEnabled(False)

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
                desc="",
                row=row,
                column=column,
                next_screen="config_confirm_screen",
            )
            column += 1
        if self.first_run:
            self.first_run = False
            selected = utils.find_config_data("custom_apps").split("|")
        self.selectButtons(selected)
        super().shownCallback()

class ConfigConfirmScreen(gui.ConfirmScreen):
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
        self.overwrite_assets = QtWidgets.QCheckBox(parent=self, text="Overwrite Assets")
        self.overwrite_assets.setChecked(True) if utils.is_installed() and utils.find_config_data("overwrite_assets") == "1" else self.overwrite_assets.setChecked(False)
        gui.clickable(self.overwrite_assets)
        self.layout().addWidget(self.overwrite_assets)

    @asyncSlot()
    async def shownCallback(self):
        slider = self.parent().parent().slider
        bottom_bar = self.parent().parent().bottom_bar
        bottom_bar.back.setEnabled(False)
        bottom_bar.next.setEnabled(False)
        
        # Adding back theme extension based on choice
        self.theme_extension = []
        for extension in utils.list_config_available("extensions"):
            extension = extension[:-3]
            if ".script" in extension:
                pass
            elif extension.lower() == slider.config_theme_menu_screen.getSelection().lower():
                self.theme_extension.append(extension)
            elif SequenceMatcher(None, extension.lower(), slider.config_theme_menu_screen.getSelection().lower()).ratio() > 0.8:
                self.theme_extension.append(extension)
        
        self.rundown.setMarkdown(
            f"""
 - **Theme**: {slider.config_theme_menu_screen.getSelection()}{(" + " + ", ".join(self.theme_extension)) + ".js" if len(self.theme_extension) > 0 else ""}
 - **Color Scheme**: {slider.config_colorscheme_menu_screen.getSelection() or "Default"}
 - **Extensions**: {", ".join(slider.config_extensions_menu_screen.getSelection()) or "None"}
 - **Custom Apps**: {", ".join(slider.config_customapps_menu_screen.getSelection()) or "None"}
""".strip()
        )
        super().shownCallback()


class ConfigLogScreen(gui.ConsoleLogScreen):
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
        colorscheme = slider.config_colorscheme_menu_screen.getSelection()
        extensions = slider.config_extensions_menu_screen.getSelection() + slider.config_confirm_screen.theme_extension
        customapps = slider.config_customapps_menu_screen.getSelection()
        overwrite_assets = "1" if slider.config_confirm_screen.overwrite_assets.isChecked() else "0"
        try:
            utils.set_config_entry("overwrite_assets", overwrite_assets)
            await core.apply_config(theme, colorscheme, extensions, customapps)
        except Exception:
            exc = "".join(traceback.format_exception(*sys.exc_info()))
            print(exc)
            print("\n\n^^ SOMETHING WENT WRONG! ^^")

        # Disconnect console output
        await self.cleanup()


class UninstallConfirmScreen(gui.ConfirmScreen):
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
        bottom_bar = self.parent().parent().bottom_bar
        slider = self.parent().parent().slider
        bottom_bar.back.setEnabled(False)
        bottom_bar.next.setEnabled(False)

        # Wait for animations to finish before enabling buttons again
        await slider.waitForAnimations()

        formatted = globals.UNINSTALL_RUNDOWN_MD.format(
            ".".join( utils.find_config_data("version").split(".")[:3]),
            "Not Implemented",
            utils.find_config_data("with"),
            "Not Implemented"
        )
        self.rundown.setMarkdown(formatted)
        super().shownCallback()


class UninstallLogScreen(gui.ConsoleLogScreen):
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


class UpdateMenuScreen(gui.MenuScreen):
    screen_name = "update_menu_screen"

    def __init__(self, parent):
        super().__init__(
            parent=parent,
            icon="󰓦",
            title="What do you want to update?",
            back_screen="main_menu_screen",
            buttons={
                "app": {
                    "icon": "󰏗",
                    "text": "App",
                    "desc": "Update EasyInstall",
                    "next_screen": "update_app_confirm_screen",
                    "row": 0,
                    "column": 0,
                },
                "latest": {
                    "icon": "󰚰",
                    "text": "Addons",
                    "desc": "Most Recent Addons",
                    "next_screen": "update_addons_confirm_screen",
                    "row": 0,
                    "column": 1,
                },
            },
        )

    @asyncSlot()
    async def shownCallback(self):
        bottom_bar = self.parent().parent().bottom_bar
        bottom_bar.back.setEnabled(False)
        super().shownCallback()

        json = await utils.latest_github_release()
        enable = float(globals.RELEASE) < float(json["tag_name"])
        self.toggleButton("app", enable)
        super().shownCallback()


class UpdateAppConfirmScreen(gui.ConfirmScreen):
    screen_name = "update_app_confirm_screen"

    def __init__(self, parent):
        super().__init__(
            parent=parent,
            icon="󰏗",
            title="Update App",
            subtitle="Details of this update:",
            rundown=globals.UPDATE_APP_RUNDOWN_MD,
            action_name="Update",
            back_screen="update_menu_screen",
            next_screen="update_app_log_screen",
        )

    @asyncSlot()
    async def shownCallback(self):
        bottom_bar = self.parent().parent().bottom_bar
        slider = self.parent().parent().slider
        bottom_bar.back.setEnabled(False)
        bottom_bar.next.setEnabled(False)

        # Wait for animations to finish before enabling buttons again
        await slider.waitForAnimations()

        json = await utils.latest_github_release()
        formatted = globals.UPDATE_APP_RUNDOWN_MD.format(
            f'{globals.RELEASE} -> '
            if float(globals.RELEASE) < float(json["tag_name"])
            else "",
            json["tag_name"],
            json["body"].strip().replace("\n", "\n\n").strip("`#"),
        )
        self.rundown.setMarkdown(formatted)
        super().shownCallback()


class UpdateAppLogScreen(gui.ConsoleLogScreen):
    screen_name = "update_app_log_screen"

    def __init__(self, parent):
        super().__init__(parent=parent, icon="󰉺", title="Update Log")

    @asyncSlot()
    async def shownCallback(self):
        bottom_bar = self.parent().parent().bottom_bar

        # Configure output widget
        await self.setup()

        # Actual update
        try:
            download = await core.update_app()
            if not download:
                print("Download Was Not Completed Properly, Please Retry!")
                await self.cleanup()
            
            else:
                @asyncSlot()
                async def restart_app_callback(*_):
                    if getattr(sys, "frozen", False) and hasattr(sys, "_MEIPASS"):
                        exec_type = "exe"
                    else:
                        exec_type = "py"
                        
                    cwd = os.getcwd()
                    await utils.powershell(
                        '\n'.join([
                            f"Wait-Process -Id {os.getpid()}",
                            f"(Get-ChildItem '{cwd}' -recurse | select -ExpandProperty fullname) -notlike '{cwd}\\Update*' | sort length -descending | remove-item",
                            f"Get-ChildItem -Path '{cwd}\\Update' -Recurse | Move-Item -Destination '{cwd}'",
                            f"Remove-Item '{cwd}\\Update'",
                            f"./spicetify-easyinstall.{exec_type}",
                        ]),
                        wait=False,
                        cwd=cwd,
                        start_new_session=True,
                    )
                    sys.exit()

                gui.connect(
                    signal=bottom_bar.next.clicked, 
                    callback=restart_app_callback
                )   
                bottom_bar.next.setText("Restart")
                bottom_bar.next.setEnabled(True)

        except Exception:
            exc = "".join(traceback.format_exception(*sys.exc_info()))
            print(exc)
            print("\n\n^^ SOMETHING WENT WRONG! ^^")
            await self.cleanup()
        
        # Restore original console output
        logger._file_write = self.original_file_write


class UpdateAddonsConfirmScreen(gui.ConfirmScreen):
    screen_name = "update_addons_confirm_screen"

    def __init__(self, parent):
        super().__init__(
            parent=parent,
            icon="󰚰",
            title="Update Latest Addons",
            subtitle="Details of this update:",
            rundown=globals.UPDATE_LATEST_RUNDOWN_MD,
            action_name="Update",
            back_screen="update_menu_screen",
            next_screen="update_addons_log_screen",
        )
        self.version = QtWidgets.QCheckBox(parent=self, text="Re-install Stock Addons")
        gui.clickable(self.version)
        self.layout().addWidget(self.version)

    @asyncSlot()
    async def shownCallback(self):
        bottom_bar = self.parent().parent().bottom_bar
        bottom_bar.next.setEnabled(False)
        super().shownCallback()


class UpdateAddonsLogScreen(gui.ConsoleLogScreen):
    screen_name = "update_addons_log_screen"

    def __init__(self, parent):
        super().__init__(parent=parent, icon="󰉺", title="Update Log")

    @asyncSlot()
    async def shownCallback(self):
        slider = self.parent().parent().slider
        # Configure output widget
        await self.setup()

        # Actual update
        try:
            await core.update_addons(shipped=slider.update_addons_confirm_screen.version.isChecked())
        except Exception:
            exc = "".join(traceback.format_exception(*sys.exc_info()))
            print(exc)
            print("\n\n^^ SOMETHING WENT WRONG! ^^")

        # Disconnect console output
        await self.cleanup()
