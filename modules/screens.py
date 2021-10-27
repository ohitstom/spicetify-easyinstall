import sys
import traceback
from modules.gui import *
from PyQt5 import QtWidgets
from qasync import asyncSlot

from modules import globals, core


class LicenseScreen(SlidingScreen):
    screen_name = "license_screen"

    def __init__(self, parent):
        super().__init__(parent=parent, icon="󰊛", title="License Agreement")

        self.license = QtWidgets.QPlainTextEdit(parent=self)
        # License text has weird width, compensate with left padding
        self.license.setStyleSheet(
            """
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


class MainMenuScreen(SlidingScreen):
    screen_name = "main_menu_screen"

    def __init__(self, parent):
        super().__init__(parent=parent, icon="󰙪", title="What do you want to do?")

        # Make sure alignment is ok
        self.top_spacer = QtWidgets.QSpacerItem(
            0, 0, vPolicy=QtWidgets.QSizePolicy.Expanding
        )
        self.layout().addItem(self.top_spacer)

        self.button_grid = QuickWidget(parent=self, margins=(0, 0, 0, 0), spacing=20)
        # Radio buttons that look like push buttons
        self.button_grid.setStyleSheet(
            f"""
            QRadioButton {{
                margin: 0px;
                padding: 5px 10px 5px 10px;
                background: {BACKGROUND};
                border-radius: 4px;
                border: 1px solid {BORDER};
                max-height: 100px;
            }}
            QRadioButton:hover {{
                border: 1px solid {HOVER_BORDER};
            }}
            QRadioButton::checked {{
                border: 1px solid {ACCENT};
            }}
            QRadioButton::disabled {{
                border: 1px solid {DISABLED_BORDER};
            }}
            QRadioButton::indicator {{
                image: url(disabled)
            }}
            #icon {{
                color: {ACCENT};
                font-family: Material Design Icons;
                font-size: 26pt;
            }}
            QLabel {{
                font-family: Poppins;
                font-size: 18pt;
                font-weight: 400;
            }}
        """
        )
        self.layout().addWidget(self.button_grid, stretch=1)

        # Define buttons and setup custom text + icon inside
        self.install = QtWidgets.QRadioButton(parent=self.button_grid, text="")
        self.install.setLayout(QtWidgets.QHBoxLayout())
        self.install.layout().addItem(
            QtWidgets.QSpacerItem(0, 0, hPolicy=QtWidgets.QSizePolicy.Expanding)
        )
        self.install.layout().addWidget(QtWidgets.QLabel(parent=self.install, text="󰄠"))
        self.install.children()[-1].setObjectName("icon")
        self.install.layout().addWidget(
            QtWidgets.QLabel(parent=self.install, text="Install")
        )
        self.install.layout().addItem(
            QtWidgets.QSpacerItem(0, 0, hPolicy=QtWidgets.QSizePolicy.Expanding)
        )
        clickable(self.install)
        self.button_grid.layout().addWidget(self.install, 0, 0)

        self.config = QtWidgets.QRadioButton(parent=self.button_grid, text="")
        self.config.setLayout(QtWidgets.QHBoxLayout())
        self.config.layout().addItem(
            QtWidgets.QSpacerItem(0, 0, hPolicy=QtWidgets.QSizePolicy.Expanding)
        )
        self.config.layout().addWidget(QtWidgets.QLabel(parent=self.config, text="󰢻"))
        self.config.children()[-1].setObjectName("icon")
        self.config.layout().addWidget(
            QtWidgets.QLabel(parent=self.config, text="Config")
        )
        self.config.layout().addItem(
            QtWidgets.QSpacerItem(0, 0, hPolicy=QtWidgets.QSizePolicy.Expanding)
        )
        clickable(self.config)
        self.button_grid.layout().addWidget(self.config, 0, 1)
        self.config.setEnabled(False)  # FIXME: implement config section

        self.uninstall = QtWidgets.QRadioButton(parent=self.button_grid, text="")
        self.uninstall.setLayout(QtWidgets.QHBoxLayout())
        self.uninstall.layout().addItem(
            QtWidgets.QSpacerItem(0, 0, hPolicy=QtWidgets.QSizePolicy.Expanding)
        )
        self.uninstall.layout().addWidget(
            QtWidgets.QLabel(parent=self.uninstall, text="󰩺")
        )
        self.uninstall.children()[-1].setObjectName("icon")
        self.uninstall.layout().addWidget(
            QtWidgets.QLabel(parent=self.uninstall, text="Uninstall")
        )
        self.uninstall.layout().addItem(
            QtWidgets.QSpacerItem(0, 0, hPolicy=QtWidgets.QSizePolicy.Expanding)
        )
        clickable(self.uninstall)
        self.button_grid.layout().addWidget(self.uninstall, 1, 0)

        self.update = QtWidgets.QRadioButton(parent=self.button_grid, text="")
        self.update.setLayout(QtWidgets.QHBoxLayout())
        self.update.layout().addItem(
            QtWidgets.QSpacerItem(0, 0, hPolicy=QtWidgets.QSizePolicy.Expanding)
        )
        self.update.layout().addWidget(QtWidgets.QLabel(parent=self.update, text="󰓦"))
        self.update.children()[-1].setObjectName("icon")
        self.update.layout().addWidget(
            QtWidgets.QLabel(parent=self.update, text="Update")
        )
        self.update.layout().addItem(
            QtWidgets.QSpacerItem(0, 0, hPolicy=QtWidgets.QSizePolicy.Expanding)
        )
        clickable(self.update)
        self.button_grid.layout().addWidget(self.update, 1, 1)

        # Make sure alignment is ok
        self.bottom_spacer = QtWidgets.QSpacerItem(
            0, 0, vPolicy=QtWidgets.QSizePolicy.Expanding
        )
        self.layout().addItem(self.bottom_spacer)

        self.debug_mode = QtWidgets.QCheckBox(
            parent=self, text="Enable Debug Mode (more verbose)"
        )
        clickable(self.debug_mode)
        self.layout().addWidget(self.debug_mode)

    @asyncSlot()
    async def shownCallback(self):
        bottom_bar = self.parent().parent().bottom_bar
        slider = self.parent().parent().slider

        # Enable next button when atleast one of the options is selected
        def set_next_button_enabled(*_):
            for btn in (self.install, self.config, self.uninstall, self.update):
                if btn.isChecked():
                    bottom_bar.next.setEnabled(True)
                    return
            bottom_bar.next.setEnabled(False)

        connect(signal=self.install.toggled, callback=set_next_button_enabled)
        connect(signal=self.config.toggled, callback=set_next_button_enabled)
        connect(signal=self.uninstall.toggled, callback=set_next_button_enabled)
        connect(signal=self.update.toggled, callback=set_next_button_enabled)

        # Setup back button
        connect(
            signal=bottom_bar.back.clicked,
            callback=lambda *_: slider.slideTo(slider.license_screen, direction="back"),
        )
        bottom_bar.back.setText("Back")
        bottom_bar.back.setEnabled(True)

        # Setup next button
        def next_button_callback(*_):
            next_screen = None
            if self.install.isChecked():
                next_screen = slider.install_confirm_screen
            if self.config.isChecked():
                next_screen = slider.current_screen
            if self.uninstall.isChecked():
                next_screen = slider.uninstall_confirm_screen
            if self.update.isChecked():
                next_screen = slider.update_menu_screen
            if next_screen:
                slider.slideTo(next_screen, direction="next")

        connect(signal=bottom_bar.next.clicked, callback=next_button_callback)
        bottom_bar.next.setText("Next")
        set_next_button_enabled()


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
        # Configure output widget
        await self.setup()

        # Actual install
        try:
            # await core.install()
            await core.install()
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


class UpdateMenuScreen(SlidingScreen):
    screen_name = "update_menu_screen"

    def __init__(self, parent):
        super().__init__(parent=parent, icon="󰓦", title="What do you want to update?")

        # Make sure alignment is ok
        self.top_spacer = QtWidgets.QSpacerItem(
            0, 0, vPolicy=QtWidgets.QSizePolicy.Expanding
        )
        self.layout().addItem(self.top_spacer)

        self.button_grid = QuickWidget(parent=self, margins=(0, 0, 0, 0), spacing=20)
        # Radio buttons that look like push buttons
        self.button_grid.setStyleSheet(
            f"""
            QRadioButton {{
                margin: 0px;
                padding: 5px 10px 5px 10px;
                background: {BACKGROUND};
                border-radius: 4px;
                border: 1px solid {BORDER};
                min-height: 125px;
                max-height: 125px;
            }}
            QRadioButton:hover {{
                border: 1px solid {HOVER_BORDER};
            }}
            QRadioButton::checked {{
                border: 1px solid {ACCENT};
            }}
            QRadioButton::disabled {{
                border: 1px solid {DISABLED_BORDER};
            }}
            QRadioButton::indicator {{
                image: url(disabled)
            }}
            #icon {{
                color: {ACCENT};
                font-family: Material Design Icons;
                font-size: 26pt;
            }}
            QLabel {{
                font-family: Poppins;
                font-size: 18pt;
                font-weight: 400;
            }}
            #description {{
                font-family: Poppins;
                font-size: 12pt;
                font-weight: 400;
                text-align: center;
            }}
        """
        )
        self.layout().addWidget(self.button_grid)

        # Define buttons and setup custom text + icon inside
        self.shipped = QtWidgets.QRadioButton(parent=self.button_grid, text="")
        self.shipped.setLayout(QtWidgets.QGridLayout())
        self.shipped.layout().addItem(
            QtWidgets.QSpacerItem(0, 0, vPolicy=QtWidgets.QSizePolicy.Expanding),
            0,
            0,
            1,
            4,
        )
        self.shipped.layout().addItem(
            QtWidgets.QSpacerItem(0, 0, hPolicy=QtWidgets.QSizePolicy.Expanding), 1, 0
        )
        self.shipped.layout().addWidget(
            QtWidgets.QLabel(parent=self.shipped, text="󰏗"), 1, 1
        )
        self.shipped.children()[-1].setObjectName("icon")
        self.shipped.layout().addWidget(
            QtWidgets.QLabel(parent=self.shipped, text="Shipped"), 1, 2
        )
        self.shipped.layout().addItem(
            QtWidgets.QSpacerItem(0, 0, hPolicy=QtWidgets.QSizePolicy.Expanding), 1, 3
        )
        self.shipped.layout().addWidget(
            QtWidgets.QLabel(parent=self.shipped, text="Preinstalled addons"),
            2,
            0,
            1,
            4,
            QtCore.Qt.AlignCenter,
        )
        self.shipped.children()[-1].setObjectName("description")
        self.shipped.layout().addItem(
            QtWidgets.QSpacerItem(0, 0, vPolicy=QtWidgets.QSizePolicy.Expanding),
            3,
            0,
            1,
            4,
        )
        clickable(self.shipped)
        self.button_grid.layout().addWidget(self.shipped, 0, 0)

        self.latest = QtWidgets.QRadioButton(parent=self.button_grid, text="")
        self.latest.setLayout(QtWidgets.QGridLayout())
        self.latest.layout().addItem(
            QtWidgets.QSpacerItem(0, 0, vPolicy=QtWidgets.QSizePolicy.Expanding),
            0,
            0,
            1,
            4,
        )
        self.latest.layout().addItem(
            QtWidgets.QSpacerItem(0, 0, hPolicy=QtWidgets.QSizePolicy.Expanding), 1, 0
        )
        self.latest.layout().addWidget(
            QtWidgets.QLabel(parent=self.latest, text="󰚰"), 1, 1
        )
        self.latest.children()[-1].setObjectName("icon")
        self.latest.layout().addWidget(
            QtWidgets.QLabel(parent=self.latest, text="Latest"), 1, 2
        )
        self.latest.layout().addItem(
            QtWidgets.QSpacerItem(0, 0, hPolicy=QtWidgets.QSizePolicy.Expanding), 1, 3
        )
        self.latest.layout().addWidget(
            QtWidgets.QLabel(parent=self.shipped, text="Third party addons"),
            2,
            0,
            1,
            4,
            QtCore.Qt.AlignCenter,
        )
        self.latest.children()[-1].setObjectName("description")
        self.latest.layout().addItem(
            QtWidgets.QSpacerItem(0, 0, vPolicy=QtWidgets.QSizePolicy.Expanding),
            3,
            0,
            1,
            4,
        )
        clickable(self.latest)
        self.button_grid.layout().addWidget(self.latest, 0, 1)

        # Make sure alignment is ok
        self.bottom_spacer = QtWidgets.QSpacerItem(
            0, 0, vPolicy=QtWidgets.QSizePolicy.Expanding
        )
        self.layout().addItem(self.bottom_spacer)

    @asyncSlot()
    async def shownCallback(self):
        bottom_bar = self.parent().parent().bottom_bar
        slider = self.parent().parent().slider

        # Enable next button when atleast one of the options is selected
        def set_next_button_enabled(*_):
            for btn in (self.shipped, self.latest):
                if btn.isChecked():
                    bottom_bar.next.setEnabled(True)
                    return
            bottom_bar.next.setEnabled(False)

        connect(signal=self.shipped.toggled, callback=set_next_button_enabled)
        connect(signal=self.latest.toggled, callback=set_next_button_enabled)

        # Setup back button
        connect(
            signal=bottom_bar.back.clicked,
            callback=lambda *_: slider.slideTo(
                slider.main_menu_screen, direction="back"
            ),
        )
        bottom_bar.back.setText("Back")
        bottom_bar.back.setEnabled(True)

        # Setup next button
        def next_button_callback(*_):
            next_screen = None
            if self.shipped.isChecked():
                next_screen = slider.update_shipped_confirm_screen
            if self.latest.isChecked():
                next_screen = slider.update_latest_confirm_screen
            if next_screen:
                slider.slideTo(next_screen, direction="next")

        connect(signal=bottom_bar.next.clicked, callback=next_button_callback)
        bottom_bar.next.setText("Next")
        set_next_button_enabled()


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
