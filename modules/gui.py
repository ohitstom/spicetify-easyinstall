import asyncio
import os
import re
import sys
import webbrowser

import PIL
from PIL import Image, ImageStat
from PyQt5 import QtCore, QtGui, QtWidgets
from PyQt5.QtGui import QPixmap
from qasync import asyncSlot

from modules import globals, logger

if hasattr(QtCore.Qt, "AA_EnableHighDpiScaling"):
    QtWidgets.QApplication.setAttribute(QtCore.Qt.AA_EnableHighDpiScaling, True)

if hasattr(QtCore.Qt, "AA_UseHighDpiPixmaps"):
    QtWidgets.QApplication.setAttribute(QtCore.Qt.AA_UseHighDpiPixmaps, True)

os.environ["QT_AUTO_SCREEN_SCALE_FACTOR"] = "1"

WIDTH = 650
HEIGHT = 475
BOTTOM_BAR_HEIGHT = 60

BACKGROUND = "#050607"
ALT_BACKGROUND = "#191A1B"
ACCENT = "#FF6922"
DISABLED_ACCENT = "#662810"
BORDER = "#333333"
HOVER_BORDER = "#555555"
DISABLED_BORDER = "#111111"
TEXT_COLOR = "#EDEDED"
DISABLED_TEXT_COLOR = "#222222"

ANIM_TYPE = QtCore.QEasingCurve.InOutQuart
ANIM_DURATION = 300

QSS = f"""
* {{
    font-family: Inter;
    font-size: 10.85pt;
    color: {TEXT_COLOR};
    selection-background-color: {ACCENT};
    selection-color: {TEXT_COLOR};
}}

#main_window {{
    background: {BACKGROUND};
}}
#sliding_frame QPlainTextEdit {{
    background: {ALT_BACKGROUND};
    border-radius: 4px;
    padding: 0px 0px 0px 4px;
    font-family: Meslo LG S;
    font-size: 8pt;
}}
#sliding_frame QTextEdit {{
    background: transparent;
    border: none;
    padding: 0px;
    margin: 0px;
}}

QCheckBox::indicator {{
    border: 1px solid {BORDER};
    border-radius: 4px;
    background: transparent;
    width: 18px;
    height: 18px;
}}
QCheckBox::indicator:checked {{
    border-color: {ACCENT};
    background: {ACCENT};
    image: url(resources/icons/check.png);
}}
QCheckBox::indicator:unchecked:hover {{
    border-color: {HOVER_BORDER};
}}

QScrollBar:vertical {{
    background: transparent;
    width: 12px;
    padding: 4px;
}}
QScrollBar::handle:vertical {{
    background: {BORDER};
    border: 0px solid {BACKGROUND};
    border-radius: 2px;
    min-height: 30px;
}}
QScrollBar::handle:vertical:hover {{
    background: {HOVER_BORDER};
}}
QScrollBar::handle:vertical:pressed {{
    background: {ACCENT};
}}
QScrollBar::add-line:vertical {{
    height: 0px;
}}
QScrollBar::sub-line:vertical {{
    height: 0px;
}}
QScrollBar::add-page:vertical, QScrollBar::sub-page:vertical {{
    background: transparent;
}}

QPushButton {{
    margin: 0px;
    padding: 5px 10px 5px 10px;
    background: {BACKGROUND};
    border-radius: 4px;
    border: 1px solid {BORDER};
}}
QPushButton:hover {{
    border: 1px solid {HOVER_BORDER};
}}
QPushButton:disabled {{
    border: 1px solid {DISABLED_BORDER};
    color: {DISABLED_TEXT_COLOR};
}}

QScrollArea, QScrollArea > QWidget > QWidget {{
    background: transparent;
}}
"""


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
    im = Image.open(file).convert("L")
    stat = ImageStat.Stat(im)
    return stat.mean[0]


def connect(signal, callback, disconnect=True):
    """Disconnect all callbacks from a given signal and assign a new one, when disconnect is True"""

    if disconnect:
        try:
            signal.disconnect()
        except Exception:
            pass

    if callback:
        signal.connect(callback)


def clickable(qobj):
    """Apply a pointing hand cursor type to a given qobj"""
    qobj.setCursor(QtCore.Qt.PointingHandCursor)


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

        self.exit_request = asyncio.Event()
        
        self.setWindowTitle("Spicetify EasyInstall")
        self.setWindowIcon(QtGui.QIcon("resources/icons/icon.png"))

        QtGui.QFontDatabase.addApplicationFont(
            "resources/fonts/materialdesignicons-webfont.ttf"
        )
        QtGui.QFontDatabase.addApplicationFont("resources/fonts/MesloLGS-Regular.ttf")
        QtGui.QFontDatabase.addApplicationFont("resources/fonts/Poppins-Medium.ttf")
        QtGui.QFontDatabase.addApplicationFont("resources/fonts/Inter.ttf")

        self.slider = SlidingFrame(parent=self)
        self.layout().addWidget(self.slider)

        self.bottom_bar = BottomBar(parent=self)
        self.layout().addWidget(self.bottom_bar)
    
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
                if not hasattr(self, "current_screen"):
                    self.current_screen = getattr(self, item.screen_name)
                    self.current_screen.move(0, 0)
                else:
                    getattr(self, item.screen_name).setVisible(False)
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
            QtGui.QPixmap("resources/icons/icon.png")
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
        pass


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
            QScrollBar:vertical {{
                width: 16px;
                padding: 4px;
                padding-left: 8px;
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
        for child in self.buttons[btn_id].children():
            child.setEnabled(enabled)

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
            if kwargs["background"] not in globals.pix_cache:
                Brightness = brightness(kwargs["background"])
                pixmapByteArray = buttonPixmap(
                    bg=kwargs["background"],
                    rounded=True,
                    width=284,
                    height=160,
                    typing="ByteArray",
                )
                globals.pix_cache[kwargs["background"]] = [pixmapByteArray, Brightness]
                with open("pix_cache.txt", "a") as f:
                    f.write(
                        f'{kwargs["background"]}: {str(pixmapByteArray.toBase64())}, {Brightness}\n'
                    )

            # New label containing a pixmap, added to the button.
            pixmap = QPixmap()
            stream = QtCore.QDataStream(
                globals.pix_cache[kwargs["background"]][0], QtCore.QIODevice.ReadOnly
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
                if globals.pix_cache[kwargs["background"]][1] > 150:
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
            if kwargs.get("next_screen") == "config_customapps_menu_screen" and kwargs["text"] not in globals.desc_cache:
                globals.desc_cache[kwargs.get("text")] = kwargs["desc"]
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
            slider.slideTo(getattr(slider, self.back_screen), direction="back")
            if self.scrollable:
                self.scroll_pos = self.button_scroll_area.verticalScrollBar().value()

        connect(signal=bottom_bar.back.clicked, callback=back_button_callback)
        bottom_bar.back.setText("Back")
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
            # Update log widget
            text = self.log.toPlainText()
            if self.reset_last_line and len(msg) > 0 and msg[-1] == "\n":
                msg = msg[:-1]
                self.reset_last_line = False
            if self.reset_last_line and text.count("\n") > 1:
                text = text[: text[:-1].rfind("\n")] + "\n"
                self.reset_last_line = False
            if len(msg) > 0 and msg[-1] == "\r":
                self.reset_last_line = True
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
