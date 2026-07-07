import asyncio
import os
import re
import sys
import webbrowser
import json as json_lib

# Suppress libpng warnings from PyQt5 image loading
os.environ["QT_LOGGING_RULES"] = "*.debug=false;qt.qpa.*=false;qt.gui.imageio.warning=false"

from PyQt5 import QtCore, QtGui, QtWidgets
from PyQt5.QtGui import QPixmap
from qasync import asyncSlot

from modules import globals, logger
from modules.state_manager import state

def get_resource_path(relative_path):
    """Get absolute path to resource, works for dev and for PyInstaller"""
    if getattr(sys, "frozen", False) and hasattr(sys, "_MEIPASS"):
        path_in_meipass = relative_path[len("resources/"):] if relative_path.startswith("resources/") else relative_path
        return os.path.join(sys._MEIPASS, path_in_meipass.replace("/", os.sep))
    else:
        base_path = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
        return os.path.join(base_path, relative_path.replace("/", os.sep))

CHECK_ICON_PATH = get_resource_path("resources/icons/check.png").replace("\\", "/")

if hasattr(QtCore.Qt, "AA_EnableHighDpiScaling"):
    QtWidgets.QApplication.setAttribute(QtCore.Qt.AA_EnableHighDpiScaling, True)

if hasattr(QtCore.Qt, "AA_UseHighDpiPixmaps"):
    QtWidgets.QApplication.setAttribute(QtCore.Qt.AA_UseHighDpiPixmaps, True)

os.environ["QT_AUTO_SCREEN_SCALE_FACTOR"] = "1"

WIDTH = 650
HEIGHT = 475
BOTTOM_BAR_HEIGHT = 60

from modules.styles import (
    BACKGROUND, ALT_BACKGROUND, ACCENT, DISABLED_ACCENT, BORDER, HOVER_BORDER,
    DISABLED_BORDER, TEXT_COLOR, DISABLED_TEXT_COLOR, QSS, QuickToolTipStyle, set_immersive_dark_mode
)
from modules.widgets import AddonListWidget, AddonListEditor, connect, clickable

ANIM_TYPE = QtCore.QEasingCurve.InOutQuart
ANIM_DURATION = 300

def buttonPixmap(bg, rounded, width, height, typing="Pixmap"):
    image = QtGui.QImage(bg)
    pixmap = QtGui.QPixmap.fromImage(image)

    # If image has transparent border, crop it (roughly)
    if QtGui.QColor(image.pixel(10, 10)).valueF() == 0.0:
        scalewidth, scaleheight = round(width * 109 / 100), round(height * 115 / 100)
    else:
        scalewidth, scaleheight = width, height

    scaledPixmap = pixmap.scaled(
        scalewidth,
        scaleheight,
        QtCore.Qt.IgnoreAspectRatio,
        QtCore.Qt.SmoothTransformation,
    )

    if rounded:
        roundPixmap = roundedPixmap(scaledPixmap, width - 4, height - 4, 9)

    if typing == "ByteArray":
        pixmapByteArray = QtCore.QByteArray()
        stream = QtCore.QDataStream(pixmapByteArray, QtCore.QIODevice.WriteOnly)
        stream << roundPixmap
        return pixmapByteArray

    return roundPixmap if rounded else scaledPixmap


def roundedPixmap(pixmap, btnwidth, btnheight, radius):
    pxm_width = pixmap.size().width()
    pxm_height = pixmap.size().height()
    pixmap = pixmap.copy(
        round((pxm_width - btnwidth) / 2),
        round((pxm_height - btnheight) / 2),
        btnwidth,
        btnheight,
    )
    rounded = QPixmap(pixmap.size())
    rounded.fill(QtGui.QColor("transparent"))
    painter = QtGui.QPainter(rounded)
    painter.setRenderHint(QtGui.QPainter.Antialiasing)
    painter.setBrush(QtGui.QBrush(pixmap))
    painter.setPen(QtCore.Qt.NoPen)
    painter.drawRoundedRect(pixmap.rect(), radius, radius)
    painter.end()
    return rounded


def brightness(file):
    from PIL import Image, ImageStat
    im = Image.open(file).convert("L")
    stat = ImageStat.Stat(im)
    return stat.mean[0]


class BlurLabel(QtWidgets.QLabel):
    """Helper class for controlling the blurRadius of a QLabel through the use of a QGraphicsBlurEffect"""

    def __init__(self, blur_amount, *args, **kwargs):
        self.blur_amount = blur_amount
        super().__init__(*args, **kwargs)
        self.applyBlur()
        connect(
            signal=self.parent().toggled,
            callback=lambda: self.removeBlur(static=True)
            if self.parent().isChecked()
            else self.applyBlur(),
        )

    def animateBlur(self, start, end, duration):
        effect = QtWidgets.QGraphicsBlurEffect(
            blurHints=QtWidgets.QGraphicsBlurEffect.AnimationHint
        )
        self.setGraphicsEffect(effect)

        self.anim = QtCore.QPropertyAnimation(effect, b"blurRadius")
        self.anim.setDuration(duration)
        self.anim.setStartValue(start)
        self.anim.setEndValue(end)
        self.anim.start()

    def applyBlur(self):
        self.animateBlur(0, self.blur_amount, 250)

    def removeBlur(self, static=None):
        if static:
            self.setGraphicsEffect(None)
        else:
            self.animateBlur(self.blur_amount, 0, 250)

    def enterEvent(self, *args):
        self.removeBlur(static=True if self.parent().isChecked() else None)
        return super().enterEvent(*args)

    def leaveEvent(self, *args):
        self.removeBlur(static=True) if self.parent().isChecked() else self.applyBlur()
        return super().leaveEvent(*args)


class QuickWidget(QtWidgets.QWidget):
    """Helper class to quickly create QWidgets with common attributes and a preassigned layout"""

    def __init__(
        self,
        parent=None,
        name=None,
        width=None,
        height=None,
        layout=QtWidgets.QGridLayout,
        margins=(0, 0, 0, 0),
        spacing=6,
    ):
        super().__init__(parent)
        if name:
            self.setObjectName(name)
        if width and height:
            self.setFixedSize(width, height)
        if layout:
            self.setLayout(layout())
            self.layout().setContentsMargins(*margins)
            self.layout().setSpacing(spacing)


class MainWindow(QuickWidget):
    """The main app window, houses two main widgets: sliding frame and bottom bar"""

    def __init__(self):
        super().__init__(
            name="main_window",
            width=WIDTH,
            height=HEIGHT,
            layout=QtWidgets.QVBoxLayout,
            margins=(0, 0, 0, 0),
            spacing=0,
        )

        set_immersive_dark_mode(self)
        self.exit_request = asyncio.Event()

        self.setWindowTitle("Spicetify EasyInstall")
        self.setWindowIcon(QtGui.QIcon(get_resource_path("resources/icons/icon.png")))

        QtGui.QFontDatabase.addApplicationFont(
            get_resource_path("resources/fonts/materialdesignicons-webfont.ttf")
        )
        QtGui.QFontDatabase.addApplicationFont(get_resource_path("resources/fonts/MesloLGS-Regular.ttf"))
        QtGui.QFontDatabase.addApplicationFont(get_resource_path("resources/fonts/Poppins-Medium.ttf"))
        QtGui.QFontDatabase.addApplicationFont(get_resource_path("resources/fonts/Inter.ttf"))

        self.slider = SlidingFrame(parent=self)
        self.layout().addWidget(self.slider)

        self.bottom_bar = BottomBar(parent=self)
        self.layout().addWidget(self.bottom_bar)

    def showEvent(self, event):
        super().showEvent(event)
        set_immersive_dark_mode(self)

    def closeEvent(self, *args):
        self.exit_request.set()


class SlidingFrame(QuickWidget):
    """Container for all screens, handles sliding between them with smooth animations"""

    def __init__(self, parent):
        super().__init__(
            parent=parent,
            name="sliding_frame",
            width=WIDTH,
            height=(HEIGHT - BOTTOM_BAR_HEIGHT),
            layout=None,
            margins=(0, 0, 0, 0),
            spacing=0,
        )

        # Animation timings
        self.old_anim_done = True
        self.new_anim_done = True

        # Dynamically import and setup all screens from screens.py
        from modules import screens

        for item in screens.__dict__.values():
            if hasattr(item, "screen_name"):
                setattr(self, item.screen_name, item(parent=self))
                getattr(self, item.screen_name).setVisible(False)

        if state.license_accepted:
            self.current_screen = self.main_menu_screen
        else:
            self.current_screen = self.license_screen

        self.current_screen.move(0, 0)
        self.current_screen.setVisible(True)
        self.current_screen.shownCallback()

    async def waitForAnimations(self):
        while not self.old_anim_done or not self.new_anim_done:
            # Returning while animation is still running will cause it to stop midway!
            await asyncio.sleep(0.1)

    @asyncSlot()
    async def slideTo(self, new_screen, direction):
        """Animation handler for switching smoothly"""
        old_screen = self.current_screen
        if new_screen is old_screen:
            return
        new_screen.setVisible(True)
        old_anim = QtCore.QPropertyAnimation(self.current_screen, b"pos")
        old_anim.setDuration(ANIM_DURATION)
        old_anim.setEasingCurve(ANIM_TYPE)
        new_anim = QtCore.QPropertyAnimation(new_screen, b"pos")
        new_anim.setDuration(ANIM_DURATION)
        new_anim.setEasingCurve(ANIM_TYPE)
        old_anim.setStartValue(QtCore.QPoint(0, 0))
        new_anim.setEndValue(QtCore.QPoint(0, 0))
        if direction == "next":
            old_anim.setEndValue(QtCore.QPoint(0 - WIDTH, 0))
            new_anim.setStartValue(QtCore.QPoint(WIDTH, 0))
        if direction == "back":
            old_anim.setEndValue(QtCore.QPoint(WIDTH, 0))
            new_anim.setStartValue(QtCore.QPoint(0 - WIDTH, 0))
        old_anim.start()
        new_anim.start()
        self.current_screen = new_screen
        self.old_anim_done = False
        self.new_anim_done = False
        old_anim.finished.connect(
            lambda *_: [
                setattr(self, "old_anim_done", True),
                old_screen.setVisible(False),
            ]
        )
        new_anim.finished.connect(lambda *_: setattr(self, "new_anim_done", True))
        await new_screen.shownCallback()
        await self.waitForAnimations()


class BottomBar(QuickWidget):
    """Bottom bar widget with icon, watermark and back / next buttons"""

    def __init__(self, parent):
        super().__init__(
            parent=parent,
            name="bottom_bar",
            width=WIDTH,
            height=BOTTOM_BAR_HEIGHT,
            layout=QtWidgets.QHBoxLayout,
            margins=(16, 12, 16, 12),
        )

        def watermark_callback(*_):
            webbrowser.open_new_tab(globals.HOMEPAGE)

        self.icon = QtWidgets.QLabel(parent=self)
        # Read image, scale to small square, cut off sides to only keep the relevant part
        self.icon.setPixmap(
            QtGui.QPixmap(get_resource_path("resources/icons/icon.png"))
            .scaled(36, 36, transformMode=QtCore.Qt.SmoothTransformation)
            .copy(6, 0, 24, 36)
        )
        # Labels don't have a clicked signal, need to replace mousePressEvent
        self.icon.mousePressEvent = watermark_callback
        clickable(self.icon)
        self.layout().addWidget(self.icon)

        self.watermark = QtWidgets.QLabel(parent=self)
        self.watermark.setText(globals.WATERMARK)
        self.watermark.mousePressEvent = watermark_callback
        clickable(self.watermark)
        self.layout().addWidget(self.watermark)

        self.spacer = QtWidgets.QSpacerItem(
            0, 0, hPolicy=QtWidgets.QSizePolicy.Expanding
        )
        self.layout().addItem(self.spacer)

        self.back = QtWidgets.QPushButton(parent=self)
        self.back.setText("Back")
        clickable(self.back)
        self.layout().addWidget(self.back)

        self.next = QtWidgets.QPushButton(parent=self)
        # Next button has acccent color
        self.next.setStyleSheet(
            f"""
            QPushButton {{
                background: {ACCENT};
            }}
            QPushButton:disabled {{
                background: {DISABLED_ACCENT};
            }}
        """
        )
        self.next.setText("Next")
        clickable(self.next)
        self.layout().addWidget(self.next)


class Title(QuickWidget):
    """Common title widget for most screens"""

    def __init__(self, parent, icon, text):
        super().__init__(
            parent=parent, layout=QtWidgets.QHBoxLayout, margins=(0, 0, 0, 0)
        )

        self.icon = QtWidgets.QLabel(parent=self, text=icon)
        # Use icon font and change color
        self.icon.setStyleSheet(
            f"""
            QLabel {{
                color: {ACCENT};
                font-family: Material Design Icons;
                font-size: 24.4pt;
            }}
        """
        )
        self.layout().addWidget(self.icon, alignment=QtCore.Qt.AlignTop)

        self.text = QtWidgets.QLabel(parent=self, text=text)
        # Change font type and size
        self.text.setStyleSheet(
            f"""
            QLabel {{
                font-family: Poppins;
                font-size: 14.5pt;
                font-weight: 400;
            }}
        """
        )
        self.layout().addWidget(self.text, alignment=QtCore.Qt.AlignBottom)

        # Make sure title aligns to left
        self.spacer = QtWidgets.QSpacerItem(
            0, 0, hPolicy=QtWidgets.QSizePolicy.Expanding
        )
        self.layout().addItem(self.spacer)


class SlidingScreen(QuickWidget):
    """Sliding screen template, gets initialized with a vertical layout and a title + icon"""

    def __init__(self, parent, icon, title):
        super().__init__(
            parent=parent,
            width=WIDTH,
            height=(HEIGHT - BOTTOM_BAR_HEIGHT),
            layout=QtWidgets.QVBoxLayout,
            margins=(16, 12, 16, 0),
            spacing=10,
        )

        self.title = Title(parent=self, icon=icon, text=title)
        self.layout().addWidget(self.title)

    @asyncSlot()
    async def shownCallback(self):
        await super().shownCallback()


class MenuScreen(SlidingScreen):
    """Screen template for a menu selection"""

    def __init__(
        self,
        parent,
        icon,
        title,
        back_screen,
        multichoice=False,
        allow_no_selection=True,
        scrollable=False,
        buttons={},
        font_size_ratio=1.25,
        min_height=0,
        max_height=225,
        min_width=0,
        max_width=325,
    ):
        super().__init__(parent=parent, icon=icon, title=title)

        # Store options
        self.scrollable = scrollable
        self.back_screen = back_screen
        self.multichoice = multichoice
        self.allow_no_selection = allow_no_selection

        self.button_grid = QuickWidget(parent=self, margins=(0, 0, 0, 0), spacing=20)
        if scrollable:
            self.scroll_pos = 0
            self.button_scroll_area = QtWidgets.QScrollArea(parent=parent)
            self.button_scroll_area.setFrameShape(QtWidgets.QFrame.NoFrame)
            self.button_scroll_area.setWidgetResizable(True)
            self.button_scroll_area.verticalScrollBar().setSingleStep(10)

        # Radio buttons that look like push buttons
        qss = f"""
            QRadioButton {{
                margin: 0px;
                padding: 5px 10px 5px 10px;
                background: {BACKGROUND};
                border-radius: 10px;
                border: 1px solid {BORDER};
                min-height: {min_height}px;
                max-height: {max_height}px;
                min-width: {min_width}px;
                max-width: {max_width}px;
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
                image: url(disabled);
            }}
            #icon {{
                color: {ACCENT};
                font-family: Material Design Icons;
                font-size: {round(26 * font_size_ratio, 1)}pt;
            }}
            QLabel {{
                font-family: Poppins;
                font-size: {round(18 * font_size_ratio, 1)}pt;
                font-weight: 400;
            }}
            #description {{
                font-family: Poppins;
                font-size: {round(12 * font_size_ratio, 1)}pt;
                font-weight: 400;
                text-align: center;
            }}
            QLabel::disabled, #icon::disabled, #description::disabled {{
                color: {DISABLED_TEXT_COLOR};
            }}
        """
        if not scrollable:
            self.button_grid.setStyleSheet(qss)
            self.layout().addWidget(self.button_grid, stretch=1)
        else:
            self.button_scroll_area.setStyleSheet(qss)
            self.button_scroll_area.setWidget(self.button_grid)
            self.layout().addWidget(self.button_scroll_area, stretch=1)

        # Create buttons from given template
        self.buttons = {}
        for btn_id in buttons:
            self.addMenuButton(btn_id, **buttons[btn_id])

    def toggleButton(self, btn_id, enabled):
        self.buttons[btn_id].setEnabled(enabled)
        if enabled:
            self.buttons[btn_id].setCursor(QtCore.Qt.PointingHandCursor)
        else:
            self.buttons[btn_id].setCursor(QtCore.Qt.ArrowCursor)
        for child in self.buttons[btn_id].children():
            child.setEnabled(enabled)
            if hasattr(child, "setCursor"):
                if enabled:
                    child.setCursor(QtCore.Qt.PointingHandCursor)
                else:
                    child.setCursor(QtCore.Qt.ArrowCursor)

    def addMenuButton(self, btn_id, row, column, **kwargs):
        self.buttons[btn_id] = QtWidgets.QRadioButton(parent=self.button_grid, text="")
        for key, value in kwargs.items():
            setattr(self.buttons[btn_id], f"_{key}", value)
        if self.multichoice:
            self.buttons[btn_id].setAutoExclusive(False)
        self.buttons[btn_id].setLayout(QtWidgets.QGridLayout())

        self.buttons[btn_id].layout().addItem(
            QtWidgets.QSpacerItem(0, 0, vPolicy=QtWidgets.QSizePolicy.Expanding),
            0,
            0,
            1,
            4,
        )
        self.buttons[btn_id].layout().addItem(
            QtWidgets.QSpacerItem(0, 0, hPolicy=QtWidgets.QSizePolicy.Expanding),
            1,
            0,
        )

        if kwargs.get("background") and kwargs["background"] != "None":
            # Caching pixmap and brightness values, memory + physical.
            if kwargs["background"] not in state.get_pix_cache():
                Brightness = brightness(kwargs["background"])
                pixmapByteArray = buttonPixmap(
                    bg=kwargs["background"],
                    rounded=True,
                    width=284,
                    height=160,
                    typing="ByteArray",
                )
                state.get_pix_cache()[kwargs["background"]] = [pixmapByteArray, Brightness]
                with open(globals.pix_cache_path, "a") as f:
                    f.write(
                        f'{kwargs["background"]}: {str(pixmapByteArray.toBase64())}, {Brightness}\n'
                    )

            # New label containing a pixmap, added to the button.
            pixmap = QPixmap()
            stream = QtCore.QDataStream(
                state.get_pix_cache()[kwargs["background"]][0], QtCore.QIODevice.ReadOnly
            )
            stream >> pixmap

            label = BlurLabel(blur_amount=2, parent=self.buttons[btn_id], pixmap=pixmap)

            self.buttons[btn_id].layout().addWidget(
                label,
                0,
                0,
                0,
                0,
                QtCore.Qt.AlignCenter,
            )
            self.buttons[btn_id].layout().setContentsMargins(0, 0, 0, 0)

        if kwargs.get("icon"):
            self.buttons[btn_id].layout().addWidget(
                QtWidgets.QLabel(parent=self.buttons[btn_id], text=kwargs["icon"]),
                1,
                1,
            )
            self.buttons[btn_id].children()[-1].setObjectName("icon")
        if kwargs.get("text"):
            label = QtWidgets.QLabel(parent=self.buttons[btn_id], text=kwargs["text"])
            label.setAttribute(QtCore.Qt.WA_TransparentForMouseEvents)

            if kwargs.get("background") and kwargs["background"] != "None":
                if state.get_pix_cache()[kwargs["background"]][1] > 150:
                    label.setStyleSheet("color: #111111")

            self.buttons[btn_id].layout().addWidget(
                label,
                1,
                2,
            )

        self.buttons[btn_id].layout().addItem(
            QtWidgets.QSpacerItem(0, 0, hPolicy=QtWidgets.QSizePolicy.Expanding),
            1,
            3,
        )
        if kwargs.get("desc"):
            # Caching extension name + description, memory + physical.
            if kwargs.get("next_screen") == "config_customapps_menu_screen" and kwargs["text"] not in state.get_desc_cache():
                state.get_desc_cache()[kwargs.get("text")] = kwargs["desc"]
                with open("desc_cache.txt", "a") as f:
                    f.write(
                        f'{kwargs["text"]}: {kwargs["desc"]}\n'
                    )

            if kwargs["desc"] != "None":
                label = QtWidgets.QLabel(parent=self.buttons[btn_id], text=kwargs["desc"])
                label.setWordWrap(True)
                label.setAlignment(QtCore.Qt.AlignCenter)
                self.buttons[btn_id].layout().addWidget(
                    label,
                    2,
                    0,
                    1,
                    4,
                    QtCore.Qt.AlignCenter,
                )
                self.buttons[btn_id].children()[-1].setObjectName("description")

        self.buttons[btn_id].layout().addItem(
            QtWidgets.QSpacerItem(0, 0, vPolicy=QtWidgets.QSizePolicy.Expanding),
            3,
            0,
            1,
            4,
        )

        clickable(self.buttons[btn_id])
        if self.scrollable:
            self.button_grid.layout().addWidget(
                self.buttons[btn_id],
                row,
                column,
                QtCore.Qt.AlignTop | QtCore.Qt.AlignLeft,
            )
            self.button_grid.layout().setRowStretch(row, 0)
            self.button_grid.layout().setRowStretch(row + 1, 1)
        else:
            self.button_grid.layout().addWidget(self.buttons[btn_id], row, column)

    def clearCurrentButtons(self):
        for btn_id in list(self.buttons.keys()):
            self.button_grid.layout().removeWidget(self.buttons[btn_id])
            self.buttons[btn_id].setVisible(False)
            self.buttons[btn_id].destroy()
            del self.buttons[btn_id]

    @asyncSlot()
    async def shownCallback(self):
        bottom_bar = self.parent().parent().bottom_bar
        slider = self.parent().parent().slider

        if hasattr(self, 'back_screen') and self.back_screen:
            bottom_bar.back.setText("Back")
        else:
            bottom_bar.back.setText("Quit")

        # Wait for animations to finish before enabling buttons again
        await slider.waitForAnimations()

        # Enable next button when atleast one of the options is selected
        def set_next_button_enabled(*_):
            if self.multichoice and self.allow_no_selection:
                bottom_bar.next.setEnabled(True)
                return
            for btn in self.buttons.values():
                if btn.isChecked():
                    bottom_bar.next.setEnabled(True)
                    return
            bottom_bar.next.setEnabled(False)

        for btn in self.buttons.values():
            connect(
                signal=btn.toggled, callback=set_next_button_enabled, disconnect=False
            )

        # Setup back button
        def back_button_callback(*_):
            if hasattr(self, 'back_screen') and self.back_screen:
                slider.slideTo(getattr(slider, self.back_screen), direction="back")
                if self.scrollable:
                    self.scroll_pos = self.button_scroll_area.verticalScrollBar().value()
            else:
                QtWidgets.QApplication.quit()

        connect(signal=bottom_bar.back.clicked, callback=back_button_callback)
        bottom_bar.back.setEnabled(True)

        # Setup next button
        def next_button_callback(*_):
            if self.scrollable:
                self.scroll_pos = self.button_scroll_area.verticalScrollBar().value()
            for btn in self.buttons.values():
                if btn.isChecked():
                    slider.slideTo(
                        getattr(slider, btn._next_screen),
                        direction="next",
                    )
                    return
            for btn in self.buttons.values():
                slider.slideTo(
                    getattr(slider, btn._next_screen),
                    direction="next",
                )
                return

        connect(signal=bottom_bar.next.clicked, callback=next_button_callback)
        bottom_bar.next.setText("Next")
        set_next_button_enabled()

    def getSelection(self):
        selected = [
            btn_id
            for btn_id, btn in self.buttons.items()
            if (hasattr(btn, "isChecked") and btn.isChecked())
        ]
        if not self.multichoice:
            selected.append(None)
            selected = selected[0]
        return selected

    @asyncSlot()
    async def selectButtons(self, selected):
        if not isinstance(selected, list):
            selected = [selected]

        did_select = False
        for selection in selected:
            if selection in self.buttons:
                self.buttons[selection].setChecked(True)
                did_select = True
                if self.scrollable:
                    self.button_scroll_area.ensureWidgetVisible(self.buttons[selection])

        if not did_select and self.scrollable:
            self.button_scroll_area.verticalScrollBar().setValue(0)


class ConfirmScreen(SlidingScreen):
    """Screen template for action rundown and confirmation"""

    def __init__(
        self,
        parent,
        icon,
        title,
        subtitle,
        rundown,
        action_name,
        back_screen,
        next_screen,
    ):
        super().__init__(parent=parent, icon=icon, title=title)

        if subtitle:
            self.subtitle = QtWidgets.QLabel(parent=self, text=subtitle)
            self.layout().addWidget(self.subtitle)

        # Rundown of action details, uses GitHub flavored markdown
        self.rundown = QtWidgets.QTextEdit(parent=self)
        self.rundown.findChild(QtGui.QTextDocument).setIndentWidth(10)
        self.rundown.setMarkdown(rundown)
        self.rundown.setReadOnly(True)
        self.layout().addWidget(self.rundown)

        # Make sure alignment is ok
        self.spacer = QtWidgets.QSpacerItem(0, 0, vPolicy=QtWidgets.QSizePolicy.Maximum)
        self.layout().addItem(self.spacer)

        # Store other options
        self.action_name = action_name
        self.back_screen = back_screen
        self.next_screen = next_screen

    @asyncSlot()
    async def shownCallback(self):
        bottom_bar = self.parent().parent().bottom_bar
        slider = self.parent().parent().slider

        bottom_bar.back.setText("Back")

        # Wait for animations to finish before enabling buttons again
        await slider.waitForAnimations()

        # Setup back button
        connect(
            signal=bottom_bar.back.clicked,
            callback=lambda *_: slider.slideTo(
                getattr(slider, self.back_screen), direction="back"
            ),
        )
        bottom_bar.back.setEnabled(True)
        # Setup next button
        connect(
            signal=bottom_bar.next.clicked,
            callback=lambda *_: slider.slideTo(
                getattr(slider, self.next_screen), direction="next"
            ),
        )
        bottom_bar.next.setText(self.action_name)
        bottom_bar.next.setEnabled(True)


class ConsoleLogScreen(SlidingScreen):
    """Screen template for console output widget"""

    def __init__(self, parent, icon, title):
        super().__init__(parent=parent, icon=icon, title=title)

        self.reset_last_line = False
        self.original_file_write = None

        self.log = QtWidgets.QPlainTextEdit(parent=self)
        self.log.setReadOnly(True)
        self.log.children()[3].children()[0].setDocumentMargin(8)
        self.layout().addWidget(self.log)

    async def setup(self):
        bottom_bar = self.parent().parent().bottom_bar
        slider = self.parent().parent().slider

        # Setup back button
        connect(signal=bottom_bar.back.clicked, callback=None)
        bottom_bar.back.setEnabled(False)
        # Setup next button
        connect(signal=bottom_bar.next.clicked, callback=None)
        bottom_bar.next.setText("Next")
        bottom_bar.next.setEnabled(False)

        self.log.setPlainText("")

        # Wait for animations to finish before enabling buttons again
        await slider.waitForAnimations()

        # Setup console output redirection
        self.original_file_write = logger._file_write

        def override_file_write(msg):
            # Save scroll data
            prev_scroll = self.log.verticalScrollBar().value()
            prev_max = self.log.verticalScrollBar().maximum()
            # Remove color codes
            msg = re.sub("\\x1b\\[38;2;\\d\\d?\\d?;\\d\\d?\\d?;\\d\\d?\\d?m", "", msg)
            msg = re.sub("\\x1b\\[\\d\\d?\\d?m", "", msg)
            msg = msg.replace("\x1b[K", "")
            # Update log widget
            text = self.log.toPlainText()

            # Overwrite the last line if the previous message was a carriage return
            if self.reset_last_line and len(text) > 0:
                last_nl = text.rfind("\n")
                if last_nl == -1:
                    text = ""
                else:
                    text = text[:last_nl + 1]

            if msg.endswith("\r"):
                self.reset_last_line = True
                msg = msg[:-1]
            else:
                self.reset_last_line = False

            self.log.setPlainText(text + msg)
            # Manage scrolling
            new_max = self.log.verticalScrollBar().maximum()
            if prev_scroll == prev_max:
                self.log.verticalScrollBar().setValue(new_max)
            else:
                self.log.verticalScrollBar().setValue(prev_scroll)
            # Run original callback
            self.original_file_write(msg)

        logger._file_write = override_file_write

    async def cleanup(self):
        bottom_bar = self.parent().parent().bottom_bar
        slider = self.parent().parent().slider

        # Restore original console output
        logger._file_write = self.original_file_write

        # Setup next button
        connect(
            signal=bottom_bar.next.clicked,
            callback=lambda *_: slider.slideTo(
                slider.main_menu_screen, direction="back"
            ),
        )
        bottom_bar.next.setText("Back to Menu")
        bottom_bar.next.setEnabled(True)

    @asyncSlot()
    async def shownCallback(self):
        pass


class CalendarDialog(QtWidgets.QDialog):
    """A reliable custom calendar popup dialog to replace the buggy QDateEdit drop-down."""
    def __init__(self, parent, initial_date):
        super().__init__(parent)
        self.setWindowTitle("Settings")
        self.setMinimumWidth(500)
        self.setWindowFlags(QtCore.Qt.Popup)
        layout = QtWidgets.QVBoxLayout(self)
        layout.setContentsMargins(0, 0, 0, 0)

        self.calendar = QtWidgets.QCalendarWidget(self)
        self.calendar.setGridVisible(False)
        self.calendar.setVerticalHeaderFormat(QtWidgets.QCalendarWidget.NoVerticalHeader)
        self.calendar.setSelectedDate(initial_date)

        # Apply the exact same theming we had for the QCalendarWidget
        self.calendar.setStyleSheet(f"""
            QCalendarWidget QWidget#qt_calendar_navigationbar {{
                background-color: {ALT_BACKGROUND};
                border-bottom: 1px solid {BORDER};
            }}
            QCalendarWidget QToolButton {{
                color: {TEXT_COLOR};
                background-color: transparent;
                border: none;
                margin: 2px;
                padding: 4px;
                border-radius: 4px;
                font-weight: bold;
            }}
            QCalendarWidget QToolButton:hover {{
                background-color: {BORDER};
            }}
            QCalendarWidget QMenu {{
                background-color: {BACKGROUND};
                color: {TEXT_COLOR};
            }}
            QCalendarWidget QSpinBox {{
                background-color: {ALT_BACKGROUND};
                color: {TEXT_COLOR};
                selection-background-color: {ACCENT};
                selection-color: #ffffff;
            }}
            QCalendarWidget QAbstractItemView:enabled {{
                color: {TEXT_COLOR};
                background-color: {BACKGROUND};
                selection-background-color: {ACCENT};
                selection-color: #ffffff;
                outline: none;
            }}
            QCalendarWidget QAbstractItemView:disabled {{
                color: #555555;
            }}
            QCalendarWidget QTableView {{
                alternate-background-color: {ALT_BACKGROUND};
                background-color: {BACKGROUND};
                color: {TEXT_COLOR};
                selection-background-color: {ACCENT};
            }}
            QCalendarWidget QHeaderView::section {{
                background-color: {ALT_BACKGROUND};
                color: {TEXT_COLOR};
                border: 1px solid {BORDER};
            }}
        """)

        layout.addWidget(self.calendar)
        self.calendar.clicked.connect(self.accept)

    def get_date(self):
        return self.calendar.selectedDate()


def get_spicetify_compatibility(commit_date_str):
    if not commit_date_str:
        return None
    import datetime
    try:
        commit_dt = datetime.datetime.strptime(commit_date_str, "%Y-%m-%d")
        spicetify_releases = []
        for s_ver, s_date_str in globals.SPICETIFY_DATES.items():
            if s_ver != "Latest" and s_date_str:
                try:
                    s_dt = datetime.datetime.strptime(s_date_str, "%Y-%m-%d")
                    spicetify_releases.append((s_ver, s_dt))
                except Exception:
                    pass
        spicetify_releases.sort(key=lambda x: x[1])

        active_ver = None
        for s_ver, s_dt in spicetify_releases:
            if s_dt <= commit_dt:
                active_ver = s_ver
            else:
                break
        return active_ver
    except Exception:
        pass
    return None


class AdvancedSettingsDialog(QtWidgets.QDialog):
    def __init__(self, parent=None):
        super().__init__(parent)
        self.setWindowFlags(QtCore.Qt.Dialog | QtCore.Qt.WindowTitleHint | QtCore.Qt.WindowCloseButtonHint)
        self.setWindowTitle("Settings")
        self.setStyleSheet(f"QDialog {{ background-color: {BACKGROUND}; color: {TEXT_COLOR}; }}")
        self.setFixedSize(550, 650)
        set_immersive_dark_mode(self)

        # Position to the right of the parent main window
        if parent:
            main_win = parent
            while main_win.parent():
                main_win = main_win.parent()
            pos = main_win.pos()
            self.move(pos.x() + main_win.width() + 12, pos.y())

        layout = QtWidgets.QVBoxLayout(self)
        layout.setContentsMargins(16, 16, 16, 16)
        layout.setSpacing(12)

        title = QtWidgets.QLabel("Configure Installation", self)
        title.setStyleSheet(f"font-family: Poppins; font-size: 14pt; font-weight: bold; color: {ACCENT};")
        layout.addWidget(title)

        # Grid layout for fields
        grid = QtWidgets.QGridLayout()
        grid.setSpacing(10)

        # Get initial values from parent (InstallConfirmScreen) or defaults
        self.parent_screen = parent
        if parent and hasattr(parent, "selected_spicetify_version"):
            self.initial_spice = parent.selected_spicetify_version
            self.initial_spot = parent.selected_spotify_version
            self.initial_themes = parent.selected_themes_version
            self.initial_pin_date = parent.pin_date
        else:
            self.initial_spice = "Latest"
            self.initial_spot = "Latest"
            self.initial_themes = "Latest"
            self.initial_pin_date = None

        if self.initial_themes and self.initial_themes.startswith("spicetify-themes-"):
            self.initial_themes = self.initial_themes[len("spicetify-themes-"):]
        elif not self.initial_themes:
            self.initial_themes = "Latest"

        self.initial_custom_themes = list(state.themes.keys())
        self.initial_custom_apps = list(state.apps.keys())
        self.initial_custom_exts = list(state.extensions.keys())

        # Helper version sorting key
        def version_key(v_str):
            try:
                clean = v_str.split(" ")[0].strip()
                if clean.startswith("v"):
                    clean = clean[1:]
                return [int(x) for x in clean.split(".") if x.isdigit()]
            except Exception:
                return []

        # Quick Actions
        quick_actions_layout = QtWidgets.QHBoxLayout()
        quick_actions_layout.addWidget(QtWidgets.QLabel("<b>Quick Actions:</b>"))

        self.btn_set_latest = QtWidgets.QPushButton("Latest", self)
        self.btn_set_latest.setStyleSheet(f"""
            QPushButton {{
                background: {ALT_BACKGROUND}; border: 1px solid {BORDER}; border-radius: 4px; padding: 4px 8px; color: {TEXT_COLOR};
            }}
            QPushButton:hover {{ border-color: {ACCENT}; color: {ACCENT}; }}
        """)
        clickable(self.btn_set_latest)
        self.btn_set_latest.clicked.connect(self.on_set_all_latest)
        quick_actions_layout.addWidget(self.btn_set_latest)

        self.btn_set_recommended = QtWidgets.QPushButton("Set Recommended", self)
        self.btn_set_recommended.setStyleSheet(f"""
            QPushButton {{
                background: {ALT_BACKGROUND}; border: 1px solid {BORDER}; border-radius: 4px; padding: 4px 12px; color: {TEXT_COLOR};
            }}
            QPushButton:hover {{ border-color: {ACCENT}; color: {ACCENT}; }}
        """)
        clickable(self.btn_set_recommended)
        self.btn_set_recommended.clicked.connect(self.on_set_recommended)
        quick_actions_layout.addWidget(self.btn_set_recommended)



        quick_actions_layout.addStretch()

        layout.addLayout(quick_actions_layout)

        # 1. Spotify Version
        grid.addWidget(QtWidgets.QLabel("1. Spotify Version:"), 0, 0)
        self.spotify_combo = QtWidgets.QComboBox(self)
        self.spotify_combo.setEditable(False)

        import platform
        from modules import globals
        machine = globals.DEBUG_ARCH.lower() if globals.DEBUG_ARCH else platform.machine().lower()
        is_x86 = "x86" in machine and not "64" in machine
        is_arm64 = "arm" in machine or "aarch64" in machine
        
        spotify_keys = sorted(globals.SPOTIFY_PRESETS.keys(), key=version_key, reverse=True)
        spotify_options = ["Latest"]
        for k in spotify_keys:
            preset_val = globals.SPOTIFY_PRESETS.get(k)
            if isinstance(preset_val, dict):
                if is_x86 and not preset_val.get("loadspot_url_x86") and not preset_val.get("archive_url_x86"):
                    continue
                elif is_arm64 and not preset_val.get("loadspot_url_arm64") and not preset_val.get("archive_url_arm64"):
                    continue
            if k == globals.SPOTIFY_VERSION:
                spotify_options.append(f"{k} (Recommended)")
            else:
                spotify_options.append(k)
        self.spotify_combo.addItems(spotify_options)

        clean_initial_spot = self.initial_spot.split(" ")[0].strip()
        if clean_initial_spot.startswith("spotify_installer-") and clean_initial_spot.endswith(".exe"):
            clean_initial_spot = clean_initial_spot[len("spotify_installer-"):-len(".exe")]

        found_preset = clean_initial_spot
        if clean_initial_spot == "SpotifySetup.exe":
            found_preset = "Latest"
        for preset_name, preset_val in globals.SPOTIFY_PRESETS.items():
            if isinstance(preset_val, dict):
                ver = preset_val.get("version", "")
            else:
                ver = preset_val
            if ver == clean_initial_spot or ver.startswith(clean_initial_spot):
                found_preset = preset_name
                break

        found_idx = self.spotify_combo.findText(found_preset, QtCore.Qt.MatchStartsWith)
        if found_idx >= 0:
            self.spotify_combo.setCurrentIndex(found_idx)
        else:
            self.spotify_combo.addItem(clean_initial_spot)
            self.spotify_combo.setCurrentIndex(self.spotify_combo.count() - 1)
        grid.addWidget(self.spotify_combo, 0, 1)

        # 2. Spicetify Version
        grid.addWidget(QtWidgets.QLabel("2. Spicetify Version:"), 1, 0)
        self.spicetify_combo = QtWidgets.QComboBox(self)
        self.spicetify_combo.setEditable(False)

        spicetify_keys = sorted([k for k in globals.SPICETIFY_DATES.keys() if k != "Latest"], key=version_key, reverse=True)
        spicetify_options = ["Latest"]
        for v in spicetify_keys:
            date_str = globals.SPICETIFY_DATES.get(v)
            label = f"{v} ({date_str})" if date_str else v
            if v == globals.SPICETIFY_VERSION or v == f"v{globals.SPICETIFY_VERSION}":
                label += " (Recommended)"
            spicetify_options.append(label)

        self.spicetify_combo.addItems(spicetify_options)

        found_spice = self.initial_spice.split(" ")[0].strip()
        if found_spice == globals.SPICETIFY_VERSION or found_spice == f"v{globals.SPICETIFY_VERSION}":
            found_spice = globals.SPICETIFY_VERSION # Match prefix

        found_idx = self.spicetify_combo.findText(found_spice, QtCore.Qt.MatchStartsWith)
        if found_idx >= 0:
            self.spicetify_combo.setCurrentIndex(found_idx)
        else:
            self.spicetify_combo.addItem(self.initial_spice)
            self.spicetify_combo.setCurrentIndex(self.spicetify_combo.count() - 1)
        grid.addWidget(self.spicetify_combo, 1, 1)

        # 3. Official Themes Version (Hidden to reduce confusion, auto-matches Spicetify version)
        self.themes_combo = QtWidgets.QComboBox(self)
        self.themes_combo.hide()

        themes_options = ["Latest"]
        for v, shas in globals.SHIPPED_SHAS.items():
            t_sha = shas.get("themes", "")
            if t_sha:
                themes_options.append(f"v{v} Compatible ({t_sha[:7]})")
        self.themes_combo.addItems(themes_options)

        if self.initial_themes == "Latest":
            self.themes_combo.setCurrentIndex(0)
        else:
            matched_ver = None
            for v, shas in globals.SHIPPED_SHAS.items():
                if v == self.initial_themes:
                    matched_ver = f"v{v} Compatible ({shas.get('themes', '')[:7]})"
                    break
            if matched_ver:
                idx = self.themes_combo.findText(matched_ver)
                if idx >= 0:
                    self.themes_combo.setCurrentIndex(idx)

        # 4. Pin Addons to Date
        self.pin_addons = QtWidgets.QCheckBox("Pin Addons to Date:", self)

        self.pin_date_container = QtWidgets.QWidget(self)
        pin_date_layout = QtWidgets.QHBoxLayout(self.pin_date_container)
        pin_date_layout.setContentsMargins(0, 0, 0, 0)

        self.pin_date_input = QtWidgets.QLineEdit(self)
        self.pin_date_input.setReadOnly(True)
        self.pin_date_input.setFixedWidth(100)
        self.pin_date_input.setStyleSheet(f"""
            QLineEdit {{
                background: {ALT_BACKGROUND};
                border: 1px solid {BORDER};
                border-radius: 4px;
                padding: 4px 8px;
                color: {TEXT_COLOR};
                min-height: 28px;
                max-height: 28px;
            }}
        """)

        self.pin_date_btn = QtWidgets.QPushButton("📅", self)
        self.pin_date_btn.setCursor(QtCore.Qt.PointingHandCursor)
        self.pin_date_btn.setFixedSize(36, 28)
        self.pin_date_btn.setStyleSheet(f"""
            QPushButton {{
                background: {ALT_BACKGROUND};
                border: 1px solid {BORDER};
                border-radius: 4px;
            }}
            QPushButton:hover {{
                background: {BORDER};
            }}
        """)

        pin_date_layout.addWidget(self.pin_date_input)
        pin_date_layout.addWidget(self.pin_date_btn)
        pin_date_layout.addSpacerItem(QtWidgets.QSpacerItem(40, 20, QtWidgets.QSizePolicy.Expanding, QtWidgets.QSizePolicy.Minimum))
        pin_date_layout.setSpacing(6)

        # Parse initial date or default to today
        if self.initial_pin_date:
            self.current_pin_date = QtCore.QDate.fromString(self.initial_pin_date, "yyyy-MM-dd")
        else:
            self.current_pin_date = QtCore.QDate.currentDate()

        self.pin_date_input.setText(self.current_pin_date.toString("yyyy-MM-dd"))

        def open_calendar():
            dialog = CalendarDialog(self, self.current_pin_date)
            # Position dialog directly under the button
            button_pos = self.pin_date_btn.mapToGlobal(QtCore.QPoint(0, self.pin_date_btn.height()))
            # shift it to the left slightly so it aligns with the line_edit
            button_pos.setX(self.pin_date_input.mapToGlobal(QtCore.QPoint(0,0)).x())
            dialog.move(button_pos)
            if dialog.exec_():
                self.current_pin_date = dialog.get_date()
                self.pin_date_input.setText(self.current_pin_date.toString("yyyy-MM-dd"))

        self.pin_date_btn.clicked.connect(open_calendar)

        if self.initial_pin_date:
            self.pin_addons.setChecked(True)
            self.pin_date_container.setEnabled(True)
        else:
            self.pin_addons.setChecked(False)
            self.pin_date_container.setEnabled(False)

        grid.addWidget(self.pin_addons, 3, 0)
        grid.addWidget(self.pin_date_container, 3, 1)

        # 5. GitHub Token (Optional)
        grid.addWidget(QtWidgets.QLabel("GitHub Token (Optional):"), 4, 0)
        self.github_token_input = QtWidgets.QLineEdit(self)
        self.github_token_input.setEchoMode(QtWidgets.QLineEdit.Password)
        self.github_token_input.setText(state.github_token)
        self.github_token_input.setPlaceholderText("Enter GitHub PAT to prevent rate limits")
        self.github_token_input.setStyleSheet(f"""
            QLineEdit {{
                background: {ALT_BACKGROUND};
                border: 1px solid {BORDER};
                border-radius: 4px;
                padding: 4px 8px;
                color: {TEXT_COLOR};
                min-height: 28px;
                max-height: 28px;
            }}
            QLineEdit:focus {{
                border-color: {ACCENT};
            }}
        """)
        grid.addWidget(self.github_token_input, 4, 1)

        layout.addLayout(grid)

        # Connect changes
        self.spotify_combo.currentTextChanged.connect(self.on_spotify_changed)
        self.spicetify_combo.currentTextChanged.connect(self.on_spicetify_changed)
        self.pin_addons.toggled.connect(self.pin_date_input.setEnabled)

        layout.addWidget(QtWidgets.QLabel("<b>Manage Custom Addons</b>:", self))

        self.tab_widget = QtWidgets.QTabWidget(self)
        self.tab_widget.setStyleSheet(f"""
            QTabWidget::pane {{
                border: 1px solid {BORDER};
                background: {BACKGROUND};
            }}
            QTabBar::tab {{
                background: {ALT_BACKGROUND};
                border: 1px solid {BORDER};
                border-bottom: none;
                padding: 6px 12px;
                color: {TEXT_COLOR};
                font-family: Inter;
                font-size: 9pt;
            }}
            QTabBar::tab:selected {{
                background: {BACKGROUND};
                border-bottom: 2px solid {ACCENT};
                color: {ACCENT};
                font-weight: bold;
            }}
        """)

        # Themes Tab
        self.themes_editor = AddonListEditor(self, placeholder_text="Themes", is_extension=False)
        self.themes_editor.add_items(state.themes.keys())
        self.tab_widget.addTab(self.themes_editor, "Themes")

        # Custom Apps Tab
        self.apps_editor = AddonListEditor(self, placeholder_text="Custom Apps", is_extension=False)
        self.apps_editor.add_items(state.apps.keys())
        self.tab_widget.addTab(self.apps_editor, "Custom Apps")

        # Extensions Tab
        self.extensions_editor = AddonListEditor(self, placeholder_text="Extensions", is_extension=True)
        self.extensions_editor.add_items(state.extensions.keys())
        self.tab_widget.addTab(self.extensions_editor, "Extensions")

        layout.addWidget(self.tab_widget)

        # Profile Import/Export Buttons
        profile_btns = QtWidgets.QHBoxLayout()

        self.import_profile_btn = QtWidgets.QPushButton("Import Profile", self)
        self.import_profile_btn.setStyleSheet(f"""
            QPushButton {{
                background: {ALT_BACKGROUND};
                border: 1px solid {BORDER};
                border-radius: 4px;
                padding: 6px 12px;
                color: {TEXT_COLOR};
                font-family: Inter;
                font-size: 9pt;
                font-weight: bold;
            }}
            QPushButton:hover {{
                border-color: {ACCENT};
                color: {ACCENT};
            }}
        """)
        clickable(self.import_profile_btn)
        self.import_profile_btn.clicked.connect(lambda: import_profile(self))

        self.export_profile_btn = QtWidgets.QPushButton("Export Profile", self)
        self.export_profile_btn.setStyleSheet(f"""
            QPushButton {{
                background: {ALT_BACKGROUND};
                border: 1px solid {BORDER};
                border-radius: 4px;
                padding: 6px 12px;
                color: {TEXT_COLOR};
                font-family: Inter;
                font-size: 9pt;
                font-weight: bold;
            }}
            QPushButton:hover {{
                border-color: {ACCENT};
                color: {ACCENT};
            }}
        """)
        clickable(self.export_profile_btn)
        self.export_profile_btn.clicked.connect(lambda: export_profile(self))

        profile_btns.addWidget(self.import_profile_btn)
        profile_btns.addWidget(self.export_profile_btn)
        layout.addLayout(profile_btns)

        # Save / Undo / Cancel Buttons
        btns = QtWidgets.QHBoxLayout()
        self.save_btn = QtWidgets.QPushButton("Save", self)
        self.save_btn.setStyleSheet(f"QPushButton {{ background: {ACCENT}; color: #ffffff; font-weight: bold; }}")
        self.save_btn.clicked.connect(self.on_save)

        self.refresh_btn = QtWidgets.QPushButton("Refresh", self)
        self.refresh_btn.clicked.connect(lambda: asyncio.ensure_future(self.refresh_versions()))

        self.undo_btn = QtWidgets.QPushButton("Reset", self)
        self.undo_btn.clicked.connect(self.on_undo)

        self.cancel_btn = QtWidgets.QPushButton("Cancel", self)
        self.cancel_btn.clicked.connect(self.reject)

        btns.addWidget(self.save_btn)
        btns.addWidget(self.refresh_btn)
        btns.addWidget(self.undo_btn)
        btns.addWidget(self.cancel_btn)
        layout.addLayout(btns)

        # Asynchronously fetch available versions
        asyncio.ensure_future(self.load_versions_async())

    async def load_versions_async(self):
        def version_key(v_str):
            try:
                clean = v_str.split(" ")[0].strip()
                if clean.startswith("v"):
                    clean = clean[1:]
                return [int(x) for x in clean.split(".") if x.isdigit()]
            except Exception:
                return []

    @asyncSlot()
    async def refresh_versions(self):
        # Prevent multiple clicks
        self.refresh_btn.setEnabled(False)
        original_text = self.refresh_btn.text()
        self.refresh_btn.setText("Fetching...")

        from modules import utils, globals

        success = await utils.fetch_data_updates()
        if success:
            def version_key(v_str):
                try:
                    return tuple(int(x) for x in v_str.replace("v", "").split("."))
                except Exception:
                    return (0,)

            # Update Spicetify Combobox
            current_spice = self.spicetify_combo.currentText()
            self.spicetify_combo.blockSignals(True)
            self.spicetify_combo.clear()
            spicetify_keys = sorted([k for k in globals.SPICETIFY_DATES.keys() if k != "Latest"], key=version_key, reverse=True)
            spicetify_options = ["Latest"]
            for v in spicetify_keys:
                label = f"{v} ({globals.SPICETIFY_DATES.get(v, '')})" if globals.SPICETIFY_DATES.get(v, '') else v
                if v == globals.SPICETIFY_VERSION or v == f"v{globals.SPICETIFY_VERSION}":
                    label += " (Recommended)"
                spicetify_options.append(label)
            self.spicetify_combo.addItems(spicetify_options)

            found_idx = self.spicetify_combo.findText(current_spice, QtCore.Qt.MatchStartsWith)
            if found_idx >= 0:
                self.spicetify_combo.setCurrentIndex(found_idx)
            else:
                self.spicetify_combo.addItem(current_spice)
                self.spicetify_combo.setCurrentIndex(self.spicetify_combo.count() - 1)
            self.spicetify_combo.blockSignals(False)

            # Update Spotify Combobox
            current_spot = self.spotify_combo.currentText()
            self.spotify_combo.blockSignals(True)
            self.spotify_combo.clear()

            def spotify_version_key(k):
                try:
                    ver_part = k.split(" ")[0]
                    return tuple(int(x) for x in ver_part.split("."))
                except Exception:
                    return (0,)

            import platform
            from modules import globals
            machine = globals.DEBUG_ARCH.lower() if globals.DEBUG_ARCH else platform.machine().lower()
            is_x86 = "x86" in machine and not "64" in machine
            is_arm64 = "arm" in machine or "aarch64" in machine
            
            spotify_options = ["Latest"]
            sorted_spotify = sorted(list(globals.SPOTIFY_PRESETS.keys()), key=spotify_version_key, reverse=True)
            for k in sorted_spotify:
                preset_val = globals.SPOTIFY_PRESETS.get(k)
                
                # Check architecture support
                if isinstance(preset_val, dict):
                    if is_x86:
                        if not preset_val.get("loadspot_url_x86") and not preset_val.get("archive_url_x86"):
                            continue
                    elif is_arm64:
                        if not preset_val.get("loadspot_url_arm64") and not preset_val.get("archive_url_arm64"):
                            continue
                
                label = k
                if k.split(" ")[0] == globals.SPOTIFY_VERSION.split(" ")[0]:
                    label += " (Recommended)"
                spotify_options.append(label)

            self.spotify_combo.addItems(spotify_options)
            found_idx = self.spotify_combo.findText(current_spot, QtCore.Qt.MatchStartsWith)
            if found_idx >= 0:
                self.spotify_combo.setCurrentIndex(found_idx)
            else:
                self.spotify_combo.addItem(current_spot)
                self.spotify_combo.setCurrentIndex(self.spotify_combo.count() - 1)
            self.spotify_combo.blockSignals(False)

        self.refresh_btn.setText(original_text)
        self.refresh_btn.setEnabled(True)

    def on_spotify_changed(self, text):
        ver = text.split(" ")[0]
        if ver == "Latest":
            self.spicetify_combo.setCurrentIndex(0) # Default to Latest
            return

        # 2. Date-based matching
        matched_spice = None
        if not matched_spice:
            spot_date_str = None
            for name in globals.SPOTIFY_PRESETS.keys():
                if name.startswith(ver) and "(" in name:
                    spot_date_str = name.split("(")[1].split(")")[0]
                    break

            if spot_date_str:
                import datetime
                try:
                    spot_dt = datetime.datetime.strptime(spot_date_str, "%Y-%m-%d")
                    # Find the oldest Spicetify version release date >= spot_dt
                    eligible_spices = []
                    for s_ver, s_date_str in globals.SPICETIFY_DATES.items():
                        if s_ver != "Latest" and s_date_str:
                            try:
                                s_dt = datetime.datetime.strptime(s_date_str, "%Y-%m-%d")
                                if s_dt >= spot_dt:
                                    eligible_spices.append((s_ver, s_dt))
                            except Exception:
                                pass
                    if eligible_spices:
                        eligible_spices.sort(key=lambda x: x[1])
                        matched_spice = eligible_spices[0][0]
                    else:
                        all_spices = []
                        for s_ver, s_date_str in globals.SPICETIFY_DATES.items():
                            if s_ver != "Latest" and s_date_str:
                                try:
                                    s_dt = datetime.datetime.strptime(s_date_str, "%Y-%m-%d")
                                    all_spices.append((s_ver, s_dt))
                                except Exception:
                                    pass
                        if all_spices:
                            all_spices.sort(key=lambda x: x[1], reverse=True)
                            matched_spice = all_spices[0][0]
                except Exception:
                    pass

        if matched_spice:
            idx = self.spicetify_combo.findText(matched_spice, QtCore.Qt.MatchStartsWith)
            if idx >= 0:
                self.spicetify_combo.setCurrentIndex(idx)

    def on_spicetify_changed(self, text):
        ver = text.split(" ")[0]
        if ver == "Latest":
            self.spotify_combo.blockSignals(True)
            self.spotify_combo.setCurrentIndex(0)
            self.spotify_combo.blockSignals(False)
            self.pin_addons.setChecked(False)
            self.themes_combo.setCurrentIndex(0)
            return

        # 1. Explicit pairing
        matched_spot = None
        for r_ver, r_data in globals.RECOMMENDED.items():
            if r_data.get("spicetify") == ver:
                matched_spot = r_data.get("spotify")
                break

        # 2. Date-based fallback
        if not matched_spot:
            spice_date = globals.SPICETIFY_DATES.get(ver, "")
            if spice_date:
                import datetime
                try:
                    spice_dt = datetime.datetime.strptime(spice_date, "%Y-%m-%d")
                    # Find the newest Spotify version whose date is < spice_dt
                    eligible_spots = []
                    for name, fullversion in globals.SPOTIFY_PRESETS.items():
                        if "(" in name:
                            spot_date_str = name.split("(")[1].split(")")[0]
                            try:
                                spot_dt = datetime.datetime.strptime(spot_date_str, "%Y-%m-%d")
                                if spot_dt < spice_dt:
                                    eligible_spots.append((name, spot_dt))
                            except Exception:
                                pass
                    if eligible_spots:
                        eligible_spots.sort(key=lambda x: x[1], reverse=True)
                        matched_spot = eligible_spots[0][0].split(" ")[0]
                except Exception:
                    pass

        if matched_spot:
            self.spotify_combo.blockSignals(True)
            idx = self.spotify_combo.findText(matched_spot, QtCore.Qt.MatchStartsWith)
            if idx >= 0:
                self.spotify_combo.setCurrentIndex(idx)
            self.spotify_combo.blockSignals(False)

        date = globals.SPICETIFY_DATES.get(ver, "")
        if date:
            self.pin_addons.blockSignals(True)
            self.pin_addons.setChecked(True)
            self.pin_addons.blockSignals(False)
            self.pin_date_container.setEnabled(True)
            self.current_pin_date = QtCore.QDate.fromString(date, "yyyy-MM-dd")
            self.pin_date_input.setText(self.current_pin_date.toString("yyyy-MM-dd"))

            # Set theme version synchronously if shipped
            if ver in globals.SHIPPED_SHAS:
                theme_sha = globals.SHIPPED_SHAS[ver]["themes"]
                display_themes = f"v{ver} Compatible ({theme_sha[:7]})"
                self.themes_combo.blockSignals(True)
                idx = self.themes_combo.findText(display_themes, QtCore.Qt.MatchContains)
                if idx < 0:
                    self.themes_combo.addItem(display_themes)
                    idx = self.themes_combo.count() - 1
                self.themes_combo.setCurrentIndex(idx)
                self.themes_combo.blockSignals(False)
            else:
                asyncio.ensure_future(self.resolve_theme_sha_async(date))
        else:
            self.pin_addons.setChecked(False)
            self.themes_combo.setCurrentIndex(0) # Default to Latest

    async def resolve_theme_sha_async(self, date_str):
        from modules import utils
        self.themes_combo.blockSignals(True)
        idx = self.themes_combo.findText("Resolving...")
        if idx >= 0:
            self.themes_combo.setCurrentIndex(idx)
        else:
            self.themes_combo.addItem("Resolving...")
            self.themes_combo.setCurrentIndex(self.themes_combo.count() - 1)
        self.themes_combo.blockSignals(False)
        try:
            ver = self.spicetify_combo.currentText().split(' ')[0]
            if ver in globals.SHIPPED_SHAS:
                theme_sha = globals.SHIPPED_SHAS[ver]["themes"]
            else:
                theme_sha = await utils.resolve_commit_by_date("spicetify/spicetify-themes", date_str)

            self.themes_combo.blockSignals(True)
            idx_resolving = self.themes_combo.findText("Resolving...")
            if idx_resolving >= 0:
                self.themes_combo.removeItem(idx_resolving)
            if theme_sha:
                display_themes = f"v{ver} Compatible ({theme_sha[:7]})"
                idx = self.themes_combo.findText(display_themes, QtCore.Qt.MatchContains)
                if idx < 0:
                    self.themes_combo.addItem(display_themes)
                    idx = self.themes_combo.count() - 1
                self.themes_combo.setCurrentIndex(idx)
            else:
                self.themes_combo.setCurrentIndex(0)
            self.themes_combo.blockSignals(False)
        except Exception:
            self.themes_combo.blockSignals(True)
            idx_resolving = self.themes_combo.findText("Resolving...")
            if idx_resolving >= 0:
                self.themes_combo.removeItem(idx_resolving)
            self.themes_combo.setCurrentIndex(0)
            self.themes_combo.blockSignals(False)

    def on_theme_override(self):
        dialog = QtWidgets.QInputDialog(self)
        dialog.setWindowTitle("Override Themes Version")
        dialog.setLabelText("Enter custom Git commit hash:")
        dialog.setTextValue("")
        dialog.setStyleSheet(f"""
            QInputDialog {{
                background-color: {BACKGROUND};
            }}
            QLabel {{
                color: {TEXT_COLOR};
                font-family: Inter;
                font-size: 9.5pt;
            }}
            QLineEdit {{
                background: {ALT_BACKGROUND};
                border: 1px solid {BORDER};
                border-radius: 4px;
                padding: 4px 8px;
                color: {TEXT_COLOR};
            }}
            QPushButton {{
                background-color: {ALT_BACKGROUND};
                color: {TEXT_COLOR};
                border: 1px solid {BORDER};
                border-radius: 4px;
                padding: 6px 16px;
                font-family: Inter;
                font-size: 9pt;
                font-weight: bold;
            }}
            QPushButton:hover {{
                border-color: {ACCENT};
                color: {ACCENT};
            }}
        """)
        set_immersive_dark_mode(dialog)
        if dialog.exec() == QtWidgets.QDialog.Accepted:
            custom_hash = dialog.textValue().strip()
            if custom_hash:
                display_text = f"Custom Hash ({custom_hash[:7]})"
                self.themes_combo.blockSignals(True)
                idx = self.themes_combo.findText(display_text, QtCore.Qt.MatchContains)
                if idx < 0:
                    self.themes_combo.addItem(display_text)
                    idx = self.themes_combo.count() - 1
                self.themes_combo.setCurrentIndex(idx)
                self.themes_combo.blockSignals(False)

    def on_undo(self):
        # Restore Spotify Version
        spotify_default = globals.SPOTIFY_VERSION
        found_idx = self.spotify_combo.findText(spotify_default, QtCore.Qt.MatchStartsWith)
        if found_idx >= 0:
            self.spotify_combo.setCurrentIndex(found_idx)
        else:
            self.spotify_combo.addItem(spotify_default)
            self.spotify_combo.setCurrentIndex(self.spotify_combo.count() - 1)

        # Restore Spicetify Version
        spicetify_default = globals.SPICETIFY_VERSION
        found_idx = self.spicetify_combo.findText(spicetify_default, QtCore.Qt.MatchStartsWith)
        if found_idx >= 0:
            self.spicetify_combo.setCurrentIndex(found_idx)
        else:
            self.spicetify_combo.addItem(spicetify_default)
            self.spicetify_combo.setCurrentIndex(self.spicetify_combo.count() - 1)

        # Restore Official Themes Version dynamically based on globals.THEMES_VERSION
        themes_hash = globals._themes_sha[:7]
        themes_default = f"v{globals.SPICETIFY_VERSION} Compatible ({themes_hash})"
        idx = self.themes_combo.findText(themes_hash, QtCore.Qt.MatchContains)
        if idx >= 0:
            self.themes_combo.setCurrentIndex(idx)
        else:
            self.themes_combo.addItem(themes_default)
            self.themes_combo.setCurrentIndex(self.themes_combo.count() - 1)

        # Restore Pin Addons and Pin Date -> Off by default (since user maintains exact commits)
        self.pin_addons.setChecked(False)
        self.pin_date_input.setEnabled(False)

        # Restore Custom Addon Lists to recommended shipped defaults
        self.themes_editor.list_widget.clear()
        self.themes_editor.add_items(globals.DEFAULT_THEMES.keys())
        self.themes_editor.list_widget.updateGeometry()

        self.apps_editor.list_widget.clear()
        self.apps_editor.add_items(globals.DEFAULT_APPS.keys())
        self.apps_editor.list_widget.updateGeometry()

        self.extensions_editor.list_widget.clear()
        self.extensions_editor.add_items(globals.DEFAULT_EXTENSIONS.keys())
        self.extensions_editor.list_widget.updateGeometry()

        self.github_token_input.setText("")

        self.window().resize(0, 0)
        self.window().adjustSize()

    def load_ui_from_globals(self):
        # 1. Spotify version
        self.spotify_combo.blockSignals(True)
        found_preset = state.selected_spotify_version
        for preset_name, preset_val in globals.SPOTIFY_PRESETS.items():
            ver = preset_val.get("version", "") if isinstance(preset_val, dict) else preset_val
            if ver == state.selected_spotify_version or ver.startswith(state.selected_spotify_version):
                found_preset = preset_name
                break
        found_idx = self.spotify_combo.findText(found_preset, QtCore.Qt.MatchStartsWith)
        if found_idx >= 0:
            self.spotify_combo.setCurrentIndex(found_idx)
        else:
            self.spotify_combo.addItem(state.selected_spotify_version)
            self.spotify_combo.setCurrentIndex(self.spotify_combo.count() - 1)
        self.spotify_combo.blockSignals(False)

        # 2. Spicetify version
        self.spicetify_combo.blockSignals(True)
        found_idx = self.spicetify_combo.findText(state.selected_spicetify_version, QtCore.Qt.MatchStartsWith)
        if found_idx >= 0:
            self.spicetify_combo.setCurrentIndex(found_idx)
        else:
            self.spicetify_combo.addItem(state.selected_spicetify_version)
            self.spicetify_combo.setCurrentIndex(self.spicetify_combo.count() - 1)
        self.spicetify_combo.blockSignals(False)

        # 3. Themes version
        self.themes_combo.blockSignals(True)
        if state.selected_themes_version == "Latest":
            self.themes_combo.setCurrentIndex(0)
        else:
            matched_ver = None
            for v, shas in globals.SHIPPED_SHAS.items():
                if shas.get("themes") == state.selected_themes_version or shas.get("themes", "")[:7] == state.selected_themes_version[:7]:
                    matched_ver = v
                    break
            if matched_ver:
                display_text = f"v{matched_ver} Compatible ({state.selected_themes_version[:7]})"
            else:
                display_text = f"Compatible ({state.selected_themes_version[:7]})"

            idx = self.themes_combo.findText(display_text, QtCore.Qt.MatchContains)
            if idx < 0:
                self.themes_combo.addItem(display_text)
                idx = self.themes_combo.count() - 1
            self.themes_combo.setCurrentIndex(idx)
        self.themes_combo.blockSignals(False)

        # 4. Pin Addons to Date
        self.pin_addons.blockSignals(True)
        if state.pin_date:
            self.pin_addons.setChecked(True)
            self.pin_date_container.setEnabled(True)
            self.current_pin_date = QtCore.QDate.fromString(state.pin_date, "yyyy-MM-dd")
            self.pin_date_input.setText(self.current_pin_date.toString("yyyy-MM-dd"))
        else:
            self.pin_addons.setChecked(False)
            self.pin_date_container.setEnabled(False)
            self.current_pin_date = QtCore.QDate.currentDate()
            self.pin_date_input.setText(self.current_pin_date.toString("yyyy-MM-dd"))
        self.pin_addons.blockSignals(False)

        # 5. GitHub Token
        self.github_token_input.setText(state.github_token or "")

        # 6. Custom addon list editors
        self.themes_editor.list_widget.clear()
        self.themes_editor.add_items(state.themes.keys())
        self.themes_editor.list_widget.updateGeometry()

        self.apps_editor.list_widget.clear()
        self.apps_editor.add_items(state.apps.keys())
        self.apps_editor.list_widget.updateGeometry()

        self.extensions_editor.list_widget.clear()
        self.extensions_editor.add_items(state.extensions.keys())
        self.extensions_editor.list_widget.updateGeometry()

        self.window().resize(0, 0)
        self.window().adjustSize()

    def on_set_all_latest(self):
        idx_spot = self.spotify_combo.findText("Latest", QtCore.Qt.MatchStartsWith)
        if idx_spot >= 0: self.spotify_combo.setCurrentIndex(idx_spot)

        idx_spice = self.spicetify_combo.findText("Latest", QtCore.Qt.MatchStartsWith)
        if idx_spice >= 0: self.spicetify_combo.setCurrentIndex(idx_spice)

        idx_themes = self.themes_combo.findText("Latest", QtCore.Qt.MatchStartsWith)
        if idx_themes >= 0: self.themes_combo.setCurrentIndex(idx_themes)

        self.pin_addons.setChecked(False)

    def on_set_recommended(self):
        rec_spot = globals.SPOTIFY_VERSION
        rec_spice = globals.SPICETIFY_VERSION

        idx_spot = self.spotify_combo.findText(rec_spot, QtCore.Qt.MatchStartsWith)
        if idx_spot >= 0: self.spotify_combo.setCurrentIndex(idx_spot)

        idx_spice = self.spicetify_combo.findText(rec_spice, QtCore.Qt.MatchStartsWith)
        if idx_spice >= 0: self.spicetify_combo.setCurrentIndex(idx_spice)

        self.pin_addons.setChecked(False)

    def on_save(self):
        themes = self.themes_editor.get_items()
        apps = self.apps_editor.get_items()
        exts = self.extensions_editor.get_items()

        state.themes = {}
        for t in themes:
            base = os.path.basename(t)
            name = base.split(".zip")[0]
            if not name.endswith(".zip"):
                name += ".zip"
            state.themes[t] = f"{globals.spice_config}\\Themes\\{name}"

        state.apps = {}
        for a in apps:
            base = os.path.basename(a)
            name = base.split(".zip")[0]
            if not name.endswith(".zip"):
                name += ".zip"
            state.apps[a] = f"{globals.spice_config}\\CustomApps\\{name}"

        state.extensions = {}
        for e in exts:
            base = os.path.basename(e)
            name = base.split(".zip")[0]
            if not name.endswith(".zip"):
                name += ".zip"
            state.extensions[e] = f"{globals.spice_config}\\Extensions\\{name}"

        # Update settings variables in globals
        state.selected_spicetify_version = self.spicetify_combo.currentText().split(" ")[0]
        state.selected_spotify_version = self.spotify_combo.currentText().split(" ")[0]

        themes_text = self.themes_combo.currentText().strip()
        if themes_text == "Latest":
            state.selected_themes_version = "Latest"
        elif "(" in themes_text:
            if "Compatible" in themes_text:
                state.selected_themes_version = themes_text.split("(")[-1].split(")")[0].strip()
            else:
                state.selected_themes_version = themes_text.split("(")[0].strip()
        else:
            state.selected_themes_version = themes_text

        if self.pin_addons.isChecked():
            state.pin_date = self.current_pin_date.toString("yyyy-MM-dd")
        else:
            state.pin_date = None

        state.github_token = self.github_token_input.text().strip()

        # Sync version selections to the parent screen (InstallConfirmScreen) if present
        if self.parent_screen:
            self.parent_screen.selected_spicetify_version = state.selected_spicetify_version
            self.parent_screen.selected_spotify_version = state.selected_spotify_version
            self.parent_screen.selected_themes_version = state.selected_themes_version
            self.parent_screen.pin_date = state.pin_date

        try:
            with open(globals.custom_addons_json_path, "w") as f:
                json_lib.dump({
                    "extensions": state.extensions,
                    "apps": state.apps,
                    "themes": state.themes,
                    "theme_commit_cache": state.theme_commit_cache,
                    "selected_spicetify_version": state.selected_spicetify_version,
                    "selected_spotify_version": state.selected_spotify_version,
                    "selected_themes_version": state.selected_themes_version,
                    "pin_date": state.pin_date,
                    "github_token": state.github_token
                }, f, indent=4)
        except Exception:
            pass

        self.accept()

    def showEvent(self, event):
        super().showEvent(event)
        set_immersive_dark_mode(self)


class SpicetifyConfigDialog(QtWidgets.QDialog):
    def __init__(self, parent=None):
        super().__init__(parent)
        self.setWindowFlags(QtCore.Qt.Dialog | QtCore.Qt.WindowTitleHint | QtCore.Qt.WindowCloseButtonHint)
        self.setWindowTitle("Spicetify Configuration Options")
        self.setStyleSheet(f"QDialog {{ background-color: {BACKGROUND}; color: {TEXT_COLOR}; }}")
        self.resize(450, 420)
        set_immersive_dark_mode(self)

        # Position to the right of the parent main window
        if parent:
            main_win = parent
            while main_win.parent():
                main_win = main_win.parent()
            pos = main_win.pos()
            self.move(pos.x() + main_win.width() + 12, pos.y())

        layout = QtWidgets.QVBoxLayout(self)
        layout.setContentsMargins(16, 16, 16, 16)
        layout.setSpacing(12)

        title = QtWidgets.QLabel("Spicetify Configuration Options", self)
        title.setStyleSheet(f"font-family: Poppins; font-size: 14pt; font-weight: bold; color: {ACCENT};")
        layout.addWidget(title)

        from modules import utils

        # Read current config values
        self.inject_css = utils.find_config_data("inject_css") == "1"
        self.replace_colors = utils.find_config_data("replace_colors") == "1"
        self.disable_ui_reveal = utils.find_config_data("disable_ui_reveal") == "1"
        self.check_spicetify_update = utils.find_config_data("check_spicetify_update") == "1"
        self.spotify_path = utils.find_config_data("spotify_path") or ""
        self.prefs_path = utils.find_config_data("prefs_path") or ""

        self.cb_inject_css = QtWidgets.QCheckBox("Inject CSS (inject_css)", self)
        self.cb_inject_css.setChecked(self.inject_css)
        layout.addWidget(self.cb_inject_css)

        self.cb_replace_colors = QtWidgets.QCheckBox("Replace Colors (replace_colors)", self)
        self.cb_replace_colors.setChecked(self.replace_colors)
        layout.addWidget(self.cb_replace_colors)

        self.cb_disable_ui_reveal = QtWidgets.QCheckBox("Disable UI Reveal (disable_ui_reveal)", self)
        self.cb_disable_ui_reveal.setChecked(self.disable_ui_reveal)
        layout.addWidget(self.cb_disable_ui_reveal)

        self.cb_check_spicetify_update = QtWidgets.QCheckBox("Check Spicetify Update (check_spicetify_update)", self)
        self.cb_check_spicetify_update.setChecked(self.check_spicetify_update)
        layout.addWidget(self.cb_check_spicetify_update)

        grid = QtWidgets.QGridLayout()
        grid.setSpacing(10)
        grid.addWidget(QtWidgets.QLabel("Spotify Path:"), 0, 0)

        spotify_path_layout = QtWidgets.QHBoxLayout()
        self.edit_spotify_path = QtWidgets.QLineEdit(self)
        self.edit_spotify_path.setText(self.spotify_path)
        self.edit_spotify_path.setStyleSheet(f"QLineEdit {{ background: {ALT_BACKGROUND}; border: 1px solid {BORDER}; border-radius: 4px; padding: 4px 8px; color: {TEXT_COLOR}; }} QLineEdit:focus {{ border-color: {ACCENT}; }}")
        spotify_path_layout.addWidget(self.edit_spotify_path)

        self.browse_spotify_btn = QtWidgets.QPushButton("📁", self)
        self.browse_spotify_btn.setToolTip("Browse Spotify.exe")
        self.browse_spotify_btn.setStyleSheet(f"QPushButton {{ background: {ALT_BACKGROUND}; border: 1px solid {BORDER}; border-radius: 4px; padding: 4px; color: {TEXT_COLOR}; min-width: 30px; }} QPushButton:hover {{ border-color: {ACCENT}; color: {ACCENT}; }}")
        self.browse_spotify_btn.clicked.connect(self.browse_spotify_path)
        clickable(self.browse_spotify_btn)
        spotify_path_layout.addWidget(self.browse_spotify_btn)
        grid.addLayout(spotify_path_layout, 0, 1)

        grid.addWidget(QtWidgets.QLabel("Prefs Path:"), 1, 0)

        prefs_path_layout = QtWidgets.QHBoxLayout()
        self.edit_prefs_path = QtWidgets.QLineEdit(self)
        self.edit_prefs_path.setText(self.prefs_path)
        self.edit_prefs_path.setStyleSheet(f"QLineEdit {{ background: {ALT_BACKGROUND}; border: 1px solid {BORDER}; border-radius: 4px; padding: 4px 8px; color: {TEXT_COLOR}; }} QLineEdit:focus {{ border-color: {ACCENT}; }}")
        prefs_path_layout.addWidget(self.edit_prefs_path)

        self.browse_prefs_btn = QtWidgets.QPushButton("📁", self)
        self.browse_prefs_btn.setToolTip("Browse Prefs File")
        self.browse_prefs_btn.setStyleSheet(f"QPushButton {{ background: {ALT_BACKGROUND}; border: 1px solid {BORDER}; border-radius: 4px; padding: 4px; color: {TEXT_COLOR}; min-width: 30px; }} QPushButton:hover {{ border-color: {ACCENT}; color: {ACCENT}; }}")
        self.browse_prefs_btn.clicked.connect(self.browse_prefs_path)
        clickable(self.browse_prefs_btn)
        prefs_path_layout.addWidget(self.browse_prefs_btn)
        grid.addLayout(prefs_path_layout, 1, 1)

        layout.addLayout(grid)

        layout.addWidget(QtWidgets.QLabel("<b>Raw Config Commands</b> (one config cmd per line, e.g. config inject_theme_js 0):", self))
        self.raw_commands = QtWidgets.QPlainTextEdit(self)
        self.raw_commands.setPlaceholderText("config inject_theme_js 0\nconfig overwrite_assets 1")
        layout.addWidget(self.raw_commands)

        btns = QtWidgets.QHBoxLayout()
        self.save_btn = QtWidgets.QPushButton("Save", self)
        self.save_btn.setStyleSheet(f"QPushButton {{ background: {ACCENT}; color: #ffffff; font-weight: bold; }}")
        self.save_btn.clicked.connect(self.on_save)
        self.cancel_btn = QtWidgets.QPushButton("Cancel", self)
        self.cancel_btn.clicked.connect(self.reject)
        btns.addWidget(self.save_btn)
        btns.addWidget(self.cancel_btn)
        layout.addLayout(btns)

    def browse_spotify_path(self):
        file_path, _ = QtWidgets.QFileDialog.getOpenFileName(
            self,
            "Select Spotify Executable",
            "",
            "Spotify Executable (Spotify.exe);;All Files (*)"
        )
        if file_path:
            self.edit_spotify_path.setText(file_path.replace("/", "\\"))

    def browse_prefs_path(self):
        file_path, _ = QtWidgets.QFileDialog.getOpenFileName(
            self,
            "Select Spotify Prefs File",
            "",
            "Prefs File (prefs);;All Files (*)"
        )
        if file_path:
            self.edit_prefs_path.setText(file_path.replace("/", "\\"))

    def showEvent(self, event):
        super().showEvent(event)
        set_immersive_dark_mode(self)

    def on_save(self):
        from modules import utils
        # Write config values (silently fail if config doesn't exist)
        try:
            utils.set_config_entry("inject_css", "1" if self.cb_inject_css.isChecked() else "0")
            utils.set_config_entry("replace_colors", "1" if self.cb_replace_colors.isChecked() else "0")
            utils.set_config_entry("disable_ui_reveal", "1" if self.cb_disable_ui_reveal.isChecked() else "0")
            utils.set_config_entry("check_spicetify_update", "1" if self.cb_check_spicetify_update.isChecked() else "0")
            if self.edit_spotify_path.text().strip():
                utils.set_config_entry("spotify_path", self.edit_spotify_path.text().strip())
            if self.edit_prefs_path.text().strip():
                utils.set_config_entry("prefs_path", self.edit_prefs_path.text().strip())
        except Exception as e:
            pass

        # Run raw config commands
        commands = [line.strip() for line in self.raw_commands.toPlainText().splitlines() if line.strip()]
        if commands:
            import subprocess
            from modules import core
            for cmd in commands:
                try:
                    run_cmd = core.environ_check
                    if run_cmd.startswith("& "):
                        run_cmd = run_cmd[2:]
                    subprocess.run(f"{run_cmd} {cmd}", shell=True, creationflags=subprocess.CREATE_NO_WINDOW)
                except Exception:
                    pass
        self.accept()


def show_message(parent, title, text, msg_type="info"):
    msg = QtWidgets.QMessageBox(parent)
    msg.setWindowTitle(title)
    msg.setText(text)

    icon_map = {
        "info": QtWidgets.QMessageBox.Information,
        "warning": QtWidgets.QMessageBox.Warning,
        "critical": QtWidgets.QMessageBox.Critical,
    }
    msg.setIcon(icon_map.get(msg_type, QtWidgets.QMessageBox.Information))

    msg.setStyleSheet(f"""
        QMessageBox, QDialog, QWidget {{
            background-color: {BACKGROUND};
        }}
        QLabel {{
            color: {TEXT_COLOR};
            background-color: transparent;
            font-family: Inter;
            font-size: 9.5pt;
        }}
        QPushButton {{
            background-color: {ALT_BACKGROUND};
            color: {TEXT_COLOR};
            border: 1px solid {BORDER};
            border-radius: 4px;
            padding: 6px 16px;
            min-width: 65px;
            font-family: Inter;
            font-size: 9pt;
            font-weight: bold;
        }}
        QPushButton:hover {{
            border-color: {ACCENT};
            color: {ACCENT};
        }}
    """)
    set_immersive_dark_mode(msg)
    return msg.exec()


def export_profile(parent):
    file_path, _ = QtWidgets.QFileDialog.getSaveFileName(
        parent,
        "Export EasyInstall Profile",
        "easyinstall-profile.json",
        "JSON Files (*.json)"
    )
    if not file_path:
        return

    try:
        from modules import utils
        profile = {
            "easyinstall": {
                "custom_extensions": state.extensions,
                "custom_apps": state.apps,
                "custom_themes": state.themes,
                "selected_spicetify_version": state.selected_spicetify_version,
                "selected_spotify_version": state.selected_spotify_version,
                "selected_themes_version": state.selected_themes_version,
                "pin_date": state.pin_date
            },
            "spicetify_config": {
                "inject_css": utils.find_config_data("inject_css"),
                "replace_colors": utils.find_config_data("replace_colors"),
                "disable_ui_reveal": utils.find_config_data("disable_ui_reveal"),
                "check_spicetify_update": utils.find_config_data("check_spicetify_update"),
                "current_theme": utils.find_config_data("current_theme"),
                "color_scheme": utils.find_config_data("color_scheme"),
                "spotify_path": utils.find_config_data("spotify_path"),
                "prefs_path": utils.find_config_data("prefs_path"),
                "extensions": utils.find_config_data("extensions"),
                "custom_apps_list": utils.find_config_data("custom_apps")
            }
        }
        with open(file_path, "w") as f:
            json_lib.dump(profile, f, indent=4)
        show_message(parent, "Success", "Profile exported successfully!", "info")
    except Exception as e:
        show_message(parent, "Error", f"Failed to export profile: {e}", "critical")


def import_profile(parent):
    file_path, _ = QtWidgets.QFileDialog.getOpenFileName(
        parent,
        "Import EasyInstall Profile",
        "",
        "JSON Files (*.json)"
    )
    if not file_path:
        return

    try:
        from modules import utils
        with open(file_path, "r") as f:
            profile = json_lib.load(f)

        # Restore EasyInstall config
        ei = profile.get("easyinstall", {})
        state.extensions = ei.get("custom_extensions", state.extensions)
        state.apps = ei.get("custom_apps", state.apps)
        state.themes = ei.get("custom_themes", state.themes)
        state.selected_spicetify_version = ei.get("selected_spicetify_version", state.selected_spicetify_version)
        state.selected_spotify_version = ei.get("selected_spotify_version", state.selected_spotify_version)
        state.selected_themes_version = ei.get("selected_themes_version", state.selected_themes_version)
        state.pin_date = ei.get("pin_date", state.pin_date)

        # Sync version selections to the parent screen (InstallConfirmScreen) if present
        slider = None
        current_widget = parent
        while current_widget:
            if hasattr(current_widget, "slider"):
                slider = current_widget.slider
                break
            current_widget = current_widget.parent()

        if slider and hasattr(slider, "install_confirm_screen"):
            slider.install_confirm_screen.selected_spicetify_version = state.selected_spicetify_version
            slider.install_confirm_screen.selected_spotify_version = state.selected_spotify_version
            slider.install_confirm_screen.selected_themes_version = state.selected_themes_version
            slider.install_confirm_screen.pin_date = state.pin_date
            # Refresh rundown text
            QtCore.QTimer.singleShot(0, lambda: asyncio.ensure_future(slider.install_confirm_screen.update_rundown_text()))

        # Save to custom_addons.json, preserving local GITHUB_TOKEN
        with open(state.config_path, "w") as f:
            json_lib.dump({
                "extensions": state.extensions,
                "apps": state.apps,
                "themes": state.themes,
                "theme_commit_cache": state.theme_commit_cache,
                "selected_spicetify_version": state.selected_spicetify_version,
                "selected_spotify_version": state.selected_spotify_version,
                "selected_themes_version": state.selected_themes_version,
                "pin_date": state.pin_date,
                "github_token": state.github_token
            }, f, indent=4)

        # Restore Spicetify config
        sc = profile.get("spicetify_config", {})
        for k, v in sc.items():
            if v and v != "config NULL" and v is not None:
                key_map = {
                    "inject_css": "inject_css",
                    "replace_colors": "replace_colors",
                    "disable_ui_reveal": "disable_ui_reveal",
                    "check_spicetify_update": "check_spicetify_update",
                    "current_theme": "current_theme",
                    "color_scheme": "color_scheme",
                    "spotify_path": "spotify_path",
                    "prefs_path": "prefs_path",
                    "extensions": "extensions",
                    "custom_apps_list": "custom_apps"
                }
                if k in key_map:
                    utils.set_config_entry(key_map[k], v)

        show_message(parent, "Success", "Profile imported successfully!", "info")
    except Exception as e:
        show_message(parent, "Error", f"Failed to import profile: {e}", "critical")

def reset_profile(parent):
    # Confirm
    confirm = QtWidgets.QMessageBox(parent)
    confirm.setWindowTitle("Reset Profile")
    confirm.setText("Are you sure you want to reset all selected versions, custom repos, and cached data?")
    confirm.setIcon(QtWidgets.QMessageBox.Warning)
    confirm.setStandardButtons(QtWidgets.QMessageBox.Yes | QtWidgets.QMessageBox.No)
    confirm.setDefaultButton(QtWidgets.QMessageBox.No)
    if confirm.exec() == QtWidgets.QMessageBox.Yes:
        try:
            import os
            if os.path.exists(state.config_path):
                os.remove(state.config_path)
            state._config = None
            state.load_config() # Reloads default

            slider = None
            current_widget = parent
            while current_widget:
                if hasattr(current_widget, "slider"):
                    slider = current_widget.slider
                    break
                current_widget = current_widget.parent()

            if slider and hasattr(slider, "install_confirm_screen"):
                slider.install_confirm_screen.selected_spicetify_version = state.selected_spicetify_version
                slider.install_confirm_screen.selected_spotify_version = state.selected_spotify_version
                slider.install_confirm_screen.selected_themes_version = state.selected_themes_version
                slider.install_confirm_screen.pin_date = state.pin_date
                # Refresh rundown text
                import asyncio
                from PyQt5 import QtCore
                QtCore.QTimer.singleShot(0, lambda: asyncio.ensure_future(slider.install_confirm_screen.update_rundown_text()))

            show_message(parent, "Success", "Profile has been reset to defaults.", "info")
        except Exception as e:
            show_message(parent, "Error", f"Failed to reset profile: {e}", "critical")


def import_custom_addon_zip(parent, addon_type):
    file_path, _ = QtWidgets.QFileDialog.getOpenFileName(
        parent,
        "Import Custom Addon (.zip)",
        "",
        "Zip Files (*.zip)"
    )
    if not file_path:
        return

    try:
        import tempfile
        import zipfile
        from pathlib import Path
        import shutil
        from modules import globals, utils
        from modules.state_manager import state

        temp_dir = tempfile.mkdtemp()
        shutil.unpack_archive(file_path, temp_dir)

        imported_names = []
        if addon_type == "themes":
            theme_dirs = []
            for root_walk, dirs_walk, files_walk in os.walk(temp_dir):
                if "color.ini" in files_walk or "user.css" in files_walk:
                    theme_dirs.append(Path(root_walk))

            if not theme_dirs:
                show_message(parent, "Error", "No theme (color.ini / user.css) found in the selected ZIP file.", "warning")
                shutil.rmtree(temp_dir, ignore_errors=True)
                return

            outside_imgs = []
            for root_walk, dirs_walk, files_walk in os.walk(temp_dir):
                rpath = Path(root_walk)
                if any(rpath == td or td in rpath.parents for td in theme_dirs):
                    continue
                for file in files_walk:
                    if file.lower().endswith(('.png', '.jpg', '.jpeg', '.gif')):
                        outside_imgs.append(rpath / file)

            for td in theme_dirs:
                dest = Path(globals.spice_config) / "Themes" / td.name
                if dest.exists():
                    shutil.rmtree(dest, ignore_errors=True)
                shutil.move(str(td), str(dest))
                imported_names.append(td.name)

                if outside_imgs:
                    dest_img_dir = dest / "images"
                    os.makedirs(dest_img_dir, exist_ok=True)
                    for img in outside_imgs:
                        try:
                            shutil.copy2(str(img), str(dest_img_dir / img.name))
                        except Exception:
                            pass

        elif addon_type == "extensions":
            js_files = []
            for root_walk, dirs_walk, files_walk in os.walk(temp_dir):
                for file in files_walk:
                    if file.endswith(".js"):
                        js_files.append(Path(root_walk) / file)

            if not js_files:
                show_message(parent, "Error", "No JavaScript extensions (.js) found in the selected ZIP file.", "warning")
                shutil.rmtree(temp_dir, ignore_errors=True)
                return

            dest_dir = Path(globals.spice_config) / "Extensions"
            os.makedirs(dest_dir, exist_ok=True)
            for jf in js_files:
                dest = dest_dir / jf.name
                if dest.exists():
                    os.remove(dest)
                shutil.copy2(str(jf), str(dest))
                imported_names.append(jf.name)

        shutil.rmtree(temp_dir, ignore_errors=True)
        show_message(parent, "Success", f"Successfully imported: {', '.join(imported_names)}", "info")

        # Trigger refresh on the screen
        QtCore.QTimer.singleShot(0, lambda: asyncio.ensure_future(parent.shownCallback()))

    except Exception as e:
        show_message(parent, "Error", f"Failed to import ZIP: {e}", "critical")

