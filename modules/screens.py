import asyncio
import os
import re
import sys
import webbrowser
import datetime
import traceback
from difflib import SequenceMatcher

from PyQt5 import QtCore, QtWidgets, QtGui
from qasync import asyncSlot

from modules import globals, gui, logger, utils
from modules.state_manager import state


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
        gui.connect(signal=bottom_bar.back.clicked, callback=state.gui.close)
        bottom_bar.back.setText("Quit")
        bottom_bar.back.setEnabled(True)
        # Setup next button
        def next_clicked(*_):
            state.license_accepted = True
            slider.slideTo(slider.main_menu_screen, direction="next")

        gui.connect(
            signal=bottom_bar.next.clicked,
            callback=next_clicked,
        )
        bottom_bar.next.setEnabled(self.accept_license.isChecked())


class MainMenuScreen(gui.MenuScreen):
    screen_name = "main_menu_screen"
    def __init__(self, parent):
        super().__init__(
            parent=parent,
            icon="󰙪",
            title="What do you want to do?",
            back_screen=None,
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

        footer_layout = QtWidgets.QHBoxLayout()

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
        footer_layout.addWidget(self.debug_mode)

        footer_layout.addStretch()

        self.export_btn = QtWidgets.QPushButton(parent=self, text="EXPORT")
        self.export_btn.setFixedSize(96, 32)
        self.export_btn.setStyleSheet(f"""
            QPushButton {{
                background: transparent;
                border: 2px solid rgba(255, 105, 34, 0.8);
                border-radius: 4px;
                color: rgba(255, 105, 34, 0.8);
                font-family: Inter;
                font-size: 8.5pt;
                font-weight: 900;
                letter-spacing: 1px;
                padding: 0px 10px;
                margin: 2px;
            }}
            QPushButton:hover {{
                border: 3px solid rgba(255, 105, 34, 1.0);
                color: rgba(255, 105, 34, 1.0);
                margin: 0px;
            }}
            QPushButton:pressed {{
                border: 1px solid {gui.DISABLED_ACCENT};
                color: {gui.DISABLED_ACCENT};
                margin: 4px;
            }}
        """)
        self.export_btn.clicked.connect(lambda: gui.export_profile(self))
        gui.clickable(self.export_btn)
        footer_layout.addWidget(self.export_btn)

        self.import_btn = QtWidgets.QPushButton(parent=self, text="IMPORT")
        self.import_btn.setFixedSize(96, 32)
        self.import_btn.setStyleSheet(f"""
            QPushButton {{
                background: transparent;
                border: 2px solid rgba(255, 105, 34, 0.8);
                border-radius: 4px;
                color: rgba(255, 105, 34, 0.8);
                font-family: Inter;
                font-size: 8.5pt;
                font-weight: 900;
                letter-spacing: 1px;
                padding: 0px 10px;
                margin: 2px;
            }}
            QPushButton:hover {{
                border: 3px solid rgba(255, 105, 34, 1.0);
                color: rgba(255, 105, 34, 1.0);
                margin: 0px;
            }}
            QPushButton:pressed {{
                border: 1px solid {gui.DISABLED_ACCENT};
                color: {gui.DISABLED_ACCENT};
                margin: 4px;
            }}
        """)
        self.import_btn.clicked.connect(lambda: gui.import_profile(self))
        gui.clickable(self.import_btn)
        footer_layout.addWidget(self.import_btn)

        self.layout().addLayout(footer_layout)

    async def check_app_updates(self):
        try:
            if hasattr(self, "update_avail_btn"):
                return

            # Fetch latest release info
            release_info = await utils.latest_github_release()
            latest_version = release_info.get("tag_name")
            if not latest_version:
                return

            def parse_ver(v):
                v_clean = v.strip().lower()
                if v_clean.startswith("v"):
                    v_clean = v_clean[1:]
                parts = [p for p in v_clean.split(".") if p.isdigit()]
                if not parts:
                    return 0.0
                if len(parts) > 1:
                    return float(f"{parts[0]}.{parts[1]}")
                return float(parts[0])

            if parse_ver(globals.RELEASE) < parse_ver(latest_version):
                # Update is available!
                self.toggleButton("update", True)

                self.update_avail_btn = QtWidgets.QPushButton(parent=self)
                self.update_avail_btn.setText(f"󰏗 Update Available (v{latest_version})")
                self.update_avail_btn.setStyleSheet(f"""
                    QPushButton {{
                        border: 1px solid {gui.ACCENT};
                        border-radius: 4px;
                        background: {gui.BACKGROUND};
                        font-family: Inter;
                        font-size: 9pt;
                        color: {gui.ACCENT};
                        padding: 4px 8px;
                    }}
                    QPushButton:hover {{
                        background: {gui.ACCENT};
                        color: #ffffff;
                    }}
                """)
                self.update_avail_btn.resize(self.update_avail_btn.sizeHint())
                self.update_avail_btn.move(self.width() - self.update_avail_btn.width() - 20, 20)
                self.update_avail_btn.show()
                gui.clickable(self.update_avail_btn)

                # Connect click to slide to update screen
                slider = self.parent()
                def on_update_clicked():
                    slider.update_app_confirm_screen.back_screen = "main_menu_screen"
                    asyncio.ensure_future(slider.slideTo(slider.update_app_confirm_screen, direction="next"))
                self.update_avail_btn.clicked.connect(on_update_clicked)
        except Exception as e:
            print(f"Failed to check for app updates: {e}")

    @asyncSlot()
    async def shownCallback(self):
        bottom_bar = self.parent().parent().bottom_bar
        bottom_bar.back.setEnabled(False)
        bottom_bar.next.setEnabled(False)

        is_installed = utils.is_installed()
        self.toggleButton("config", is_installed)
        self.toggleButton("uninstall", is_installed)
        self.toggleButton("update", is_installed)

        # Check for app updates asynchronously in the background
        asyncio.ensure_future(self.check_app_updates())

        await super().shownCallback()
        if state.license_accepted:
            from modules.widgets import connect
            def quit_app(*_):
                import sys
                sys.exit(0)
            try:
                bottom_bar.back.clicked.disconnect()
            except Exception:
                pass
            bottom_bar.back.clicked.connect(quit_app)
            bottom_bar.back.setText("Quit")
            bottom_bar.back.setEnabled(True)
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

        self.selected_spicetify_version = state.selected_spicetify_version

        # Prepare versions and URLs
        if state.selected_spotify_version != "latest":
            preset = globals.SPOTIFY_PRESETS.get(state.selected_spotify_version)
            if isinstance(preset, dict):
                version_str = preset.get("version")
                state.runtime_spotify_url = preset.get("loadspot_url")
                state.runtime_archive_url = preset.get("archive_url")
            else:
                version_str = preset if preset else state.selected_spotify_version
                state.runtime_spotify_url = f"https://loadspot.amd64fox1.workers.dev/download/spotify_installer-{version_str}-x64.exe"
                state.runtime_archive_url = None

            state.runtime_spotify_version = f"spotify_installer-{version_str}-x64.exe"
        else:
            state.runtime_spotify_version = "SpotifySetup.exe"
            state.runtime_spotify_url = "https://download.scdn.co/SpotifySetup.exe"
            state.runtime_archive_url = None

        self.selected_spotify_version = state.selected_spotify_version
        self.selected_themes_version = state.selected_themes_version
        self.pin_date = state.pin_date

        self.launch_after = QtWidgets.QCheckBox(parent=self, text="Launch When Ready")
        self.leaveSpotify = QtWidgets.QCheckBox(parent=self, text="Dont Uninstall Spotify - Can Be Unstable!")
        self.warning = QtWidgets.QLabel(parent=self, text="<b>WARNING</b>: This process will uninstall and reinstall Spotify and Spicetify.")
        gui.clickable(self.launch_after)
        gui.clickable(self.leaveSpotify)
        self.layout().addWidget(self.launch_after)
        self.layout().addWidget(self.leaveSpotify)
        self.layout().addWidget(self.warning)

        # Settings cog in top-right of the screen title layout
        self.settings_btn = QtWidgets.QPushButton(parent=self.title)
        self.settings_btn.setText("󰒓")
        self.settings_btn.setToolTip("Install Settings")
        self.settings_btn.setStyleSheet(f"""
            QPushButton {{
                border: none;
                background: transparent;
                font-family: Material Design Icons;
                font-size: 18pt;
                color: {gui.TEXT_COLOR};
                padding: 0px;
                margin-top: 4px;
            }}
            QPushButton:hover {{
                color: {gui.ACCENT};
            }}
        """)
        gui.clickable(self.settings_btn)
        self.title.layout().addWidget(self.settings_btn, alignment=QtCore.Qt.AlignTop)

        # Connect settings button
        self.settings_btn.clicked.connect(self.show_advanced_settings)

    def show_advanced_settings(self):
        dialog = gui.AdvancedSettingsDialog(self)
        if dialog.exec() == QtWidgets.QDialog.Accepted:
            selected_spice = dialog.spicetify_combo.currentText().split(" ")[0]
            selected_spot = dialog.spotify_combo.currentText().split(" ")[0]
            selected_themes = dialog.themes_combo.currentText().split(" ")[-1].strip("()")

            self.selected_spicetify_version = selected_spice
            self.selected_spotify_version = selected_spot
            self.selected_themes_version = selected_themes

            if dialog.pin_addons.isChecked():
                self.pin_date = dialog.current_pin_date.toString("yyyy-MM-dd")
            else:
                self.pin_date = None

            # Update rundown text asynchronously
            QtCore.QTimer.singleShot(0, lambda: asyncio.ensure_future(self.update_rundown_text()))

    @asyncSlot()
    async def update_rundown_text(self):
        SPOTIFY_VERSION_OLD = ".".join(utils.find_config_data("app.last-launched-version", config=f'{globals.appdata}\\Spotify\\prefs', splitchar="=").strip('"').split(".")[:3])
        SPICETIFY_VERSION_OLD = utils.find_config_data("with")

        spotify_resolved = self.selected_spotify_version
        spicetify_resolved = self.selected_spicetify_version
        themes_resolved = self.selected_themes_version

        need_spotify_query = (self.selected_spotify_version == "Latest")
        need_spicetify_query = (self.selected_spicetify_version == "Latest")
        need_themes_query = (self.selected_themes_version == "Latest")

        try:
            tasks = []

            async def get_themes():
                nonlocal themes_resolved
                if self.pin_date and need_themes_query:
                    themes_sha = await utils.resolve_commit_by_date("spicetify/spicetify-themes", self.pin_date)
                    themes_resolved = themes_sha[:7] if themes_sha else "master"
                elif need_themes_query:
                    latest_tag = list(globals.SHIPPED_SHAS.keys())[0]
                    themes_resolved = globals.SHIPPED_SHAS[latest_tag]["themes"][:7]

            async def get_spicetify():
                nonlocal spicetify_resolved
                if need_spicetify_query:
                    spicetify_resolved = list(globals.SHIPPED_SHAS.keys())[0]

            async def get_spotify():
                nonlocal spotify_resolved
                if need_spotify_query:
                    spotify_resolved = list(globals.SPOTIFY_PRESETS.keys())[0].split(" ")[0]

            await asyncio.gather(get_themes(), get_spicetify(), get_spotify())

        except Exception as e:
            if need_spicetify_query:
                spicetify_resolved = state.runtime_spicetify_version if state.runtime_spicetify_version else "Unknown"
            if need_spotify_query:
                if state.runtime_spotify_version == "SpotifySetup.exe" or not state.runtime_spotify_version:
                    spotify_resolved = "Latest"
                else:
                    spotify_resolved = ".".join(state.runtime_spotify_version[18:-4].split(".")[:3])
            if need_themes_query:
                themes_resolved = state.runtime_themes_version[17:24] if state.runtime_themes_version else "Unknown"
            import traceback
            print(f"Rate limited or offline. Using defaults. Error: {e}")
            traceback.print_exc()

        # Trim spotify version display to 3 segments
        spotify_display = spotify_resolved.split(" ")[0]
        spotify_display = ".".join(spotify_display.split(".")[:3])

        if SPOTIFY_VERSION_OLD == "config NULL" or SPOTIFY_VERSION_OLD == "":
            SPOTIFY_VERSION_OLD = "Not Installed"

        formatted = globals.INSTALL_RUNDOWN_MD.format(
            f"{SPICETIFY_VERSION_OLD} -> "
            if SPICETIFY_VERSION_OLD != spicetify_resolved
            and SPICETIFY_VERSION_OLD != "Path NULL"
            and SPICETIFY_VERSION_OLD != ""
            and utils.is_installed()
            else "",
            spicetify_resolved,
            f"{SPOTIFY_VERSION_OLD} -> "
            if SPOTIFY_VERSION_OLD != spotify_display
            and SPOTIFY_VERSION_OLD != "Path NULL"
            and SPOTIFY_VERSION_OLD != "Not Installed"
            and os.path.isdir(f"{globals.appdata}\\Spotify")
            else "",
            spotify_display,
            themes_resolved,
        )
        self.rundown.setMarkdown(formatted)

    @asyncSlot()
    async def shownCallback(self):
        bottom_bar = self.parent().parent().bottom_bar
        slider = self.parent().parent().slider
        bottom_bar.back.setEnabled(False)
        bottom_bar.next.setEnabled(False)

        await slider.waitForAnimations()
        await self.update_rundown_text()
        await super().shownCallback()

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
            from modules import core
            await core.install(
                launch=slider.install_confirm_screen.launch_after.isChecked(),
                leaveSpotify=slider.install_confirm_screen.leaveSpotify.isChecked(),
                spicetify_version=slider.install_confirm_screen.selected_spicetify_version,
                spotify_version=slider.install_confirm_screen.selected_spotify_version,
                pin_date=slider.install_confirm_screen.pin_date,
                themes_version=slider.install_confirm_screen.selected_themes_version
            )
        except PermissionError as e:
            print("\n" + "="*60)
            print("RATE LIMIT DETECTED")
            print("="*60)
            print(str(e))
            print("="*60 + "\n")
            print("\n\n^^ SOMETHING WENT WRONG! ^^")
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
        self.import_btn = QtWidgets.QPushButton(parent=self, text="Import Custom Theme (.zip)")
        self.import_btn.clicked.connect(lambda: gui.import_custom_addon_zip(self, "themes"))
        self.layout().addWidget(self.import_btn)

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
        await super().shownCallback()


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
        await super().shownCallback()


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
        self.import_btn = QtWidgets.QPushButton(parent=self, text="Import Custom Extension (.zip)")
        self.import_btn.clicked.connect(lambda: gui.import_custom_addon_zip(self, "extensions"))
        self.layout().addWidget(self.import_btn)

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
        await super().shownCallback()


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
                next_screen="config_snippets_menu_screen",
            )
            column += 1
        if self.first_run:
            self.first_run = False
            selected = utils.find_config_data("custom_apps").split("|")
        self.selectButtons(selected)
        await super().shownCallback()

class ConfigSnippetsMenuScreen(gui.SlidingScreen):
    screen_name = "config_snippets_menu_screen"

    def __init__(self, parent):
        super().__init__(parent=parent, icon="󰄨", title="Custom CSS Snippet")

        self.subtitle = QtWidgets.QLabel(parent=self, text="Inject raw CSS into your Spicetify theme:")
        self.layout().addWidget(self.subtitle)

        self.editor = QtWidgets.QPlainTextEdit(parent=self)
        self.editor.setFont(QtGui.QFont("MesloLGS Regular", 10))
        self.editor.setStyleSheet(f"background: {gui.ALT_BACKGROUND}; color: {gui.TEXT_COLOR}; border: 1px solid {gui.BORDER}; border-radius: 4px; padding: 4px;")

        self.snippet_path = os.path.join(globals.appdata_local, "spicetify-easyinstall", "custom_snippet.css")
        if os.path.exists(self.snippet_path):
            try:
                with open(self.snippet_path, "r", encoding="utf-8") as f:
                    self.editor.setPlainText(f.read())
            except Exception:
                pass

        self.layout().addWidget(self.editor)

    @asyncSlot()
    async def shownCallback(self):
        bottom_bar = self.parent().parent().bottom_bar
        slider = self.parent().parent().slider

        bottom_bar.back.setText("Back")
        await slider.waitForAnimations()

        # Setup back button
        gui.connect(
            signal=bottom_bar.back.clicked,
            callback=lambda *_: slider.slideTo(slider.config_customapps_menu_screen, direction="back"),
        )
        bottom_bar.back.setEnabled(True)

        # Setup next button
        def on_next(*_):
            os.makedirs(os.path.dirname(self.snippet_path), exist_ok=True)
            with open(self.snippet_path, "w", encoding="utf-8") as f:
                f.write(self.editor.toPlainText())
            slider.slideTo(slider.config_confirm_screen, direction="next")

        gui.connect(
            signal=bottom_bar.next.clicked,
            callback=on_next,
        )
        bottom_bar.next.setText("Next")
        bottom_bar.next.setEnabled(True)

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
            back_screen="config_snippets_menu_screen",
            next_screen="config_log_screen",
        )
        self.inject_theme_js = QtWidgets.QCheckBox(parent=self, text="Inject Theme JS")
        self.inject_theme_js.setChecked(True) if utils.is_installed() and utils.find_config_data("inject_theme_js") == "1" else self.inject_theme_js.setChecked(False)
        gui.clickable(self.inject_theme_js)
        self.layout().addWidget(self.inject_theme_js)
        self.overwrite_assets = QtWidgets.QCheckBox(parent=self, text="Overwrite Assets")
        self.overwrite_assets.setChecked(True) if utils.is_installed() and utils.find_config_data("overwrite_assets") == "1" else self.overwrite_assets.setChecked(False)
        gui.clickable(self.overwrite_assets)
        self.layout().addWidget(self.overwrite_assets)

        # Settings cog in top-right of the screen title layout
        self.settings_btn = QtWidgets.QPushButton(parent=self.title)
        self.settings_btn.setText("󰒓")
        self.settings_btn.setToolTip("Spicetify Settings")
        self.settings_btn.setStyleSheet(f"""
            QPushButton {{
                border: none;
                background: transparent;
                font-family: Material Design Icons;
                font-size: 18pt;
                color: {gui.TEXT_COLOR};
                padding: 0px;
                margin-top: 4px;
            }}
            QPushButton:hover {{
                color: {gui.ACCENT};
            }}
        """)
        gui.clickable(self.settings_btn)
        self.title.layout().addWidget(self.settings_btn, alignment=QtCore.Qt.AlignTop)

        # Connect settings button
        self.settings_btn.clicked.connect(self.show_config_settings)

    def show_config_settings(self):
        dialog = gui.SpicetifyConfigDialog(self)
        if dialog.exec() == QtWidgets.QDialog.Accepted:
            self.inject_theme_js.setChecked(True) if utils.is_installed() and utils.find_config_data("inject_theme_js") == "1" else self.inject_theme_js.setChecked(False)
            self.overwrite_assets.setChecked(True) if utils.is_installed() and utils.find_config_data("overwrite_assets") == "1" else self.overwrite_assets.setChecked(False)

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
        await super().shownCallback()


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
        inject_theme_js = "1" if slider.config_confirm_screen.inject_theme_js.isChecked() else "0"
        try:
            utils.set_config_entry("overwrite_assets", overwrite_assets)
            utils.set_config_entry("inject_theme_js", inject_theme_js)
            from modules import core
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

        self.uninstall_spotify = QtWidgets.QCheckBox(parent=self, text="Uninstall Spotify")
        self.super_wipe = QtWidgets.QCheckBox(parent=self, text="Reset EasyInstall (Deletes all saved configurations)")

        self.layout().addWidget(self.uninstall_spotify)
        self.layout().addWidget(self.super_wipe)

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
        await super().shownCallback()


class UninstallLogScreen(gui.ConsoleLogScreen):
    screen_name = "uninstall_log_screen"

    def __init__(self, parent):
        super().__init__(parent=parent, icon="󰉺", title="Uninstall Log")

    @asyncSlot()
    async def shownCallback(self):
        slider = self.parent().parent().slider

        # Configure output widget
        await self.setup()

        # Actual uninstall
        try:
            from modules import core
            await core.uninstall(
                spotify=slider.uninstall_confirm_screen.uninstall_spotify.isChecked(),
                super_wipe=slider.uninstall_confirm_screen.super_wipe.isChecked()
            )
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
        await super().shownCallback()

        import aiohttp
        try:
            async with aiohttp.ClientSession() as session:
                async with session.get("https://raw.githubusercontent.com/ohitstom/Spicetify-EasyInstall/main/modules/globals.py") as resp:
                    if resp.status == 200:
                        text = await resp.text()
                        match = re.search(r'RELEASE\s*=\s*["\']([^"\']+)["\']', text)
                        latest_version = match.group(1) if match else globals.RELEASE
                    else:
                        latest_version = globals.RELEASE
        except Exception:
            latest_version = globals.RELEASE


        def parse_ver(v):
            v_clean = v.strip().lower()
            if v_clean.startswith("v"):
                v_clean = v_clean[1:]
            parts = [p for p in v_clean.split(".") if p.isdigit()]
            if not parts:
                return 0.0
            if len(parts) > 1:
                return float(f"{parts[0]}.{parts[1]}")
            return float(parts[0])

        enable = parse_ver(globals.RELEASE) < parse_ver(latest_version)
        self.toggleButton("app", enable)

        is_installed = utils.is_installed()
        self.toggleButton("latest", is_installed)

        await super().shownCallback()


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
        await super().shownCallback()


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
            from modules import core
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
        self.warning = QtWidgets.QLabel(parent=self, text="<b>WARNING</b>: This process will delete all addons in both Spicetify folders.")
        gui.clickable(self.version)
        self.layout().addWidget(self.version)
        self.layout().addWidget(self.warning)

    @asyncSlot()
    async def shownCallback(self):
        bottom_bar = self.parent().parent().bottom_bar
        bottom_bar.next.setEnabled(False)
        await super().shownCallback()


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
            from modules import core
            await core.update_addons(shipped=slider.update_addons_confirm_screen.version.isChecked())
        except Exception:
            exc = "".join(traceback.format_exception(*sys.exc_info()))
            print(exc)
            print("\n\n^^ SOMETHING WENT WRONG! ^^")

        # Disconnect console output
        await self.cleanup()
