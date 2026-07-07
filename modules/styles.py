import os
import sys
from PyQt5 import QtCore, QtWidgets

def get_resource_path(relative_path):
    """Get absolute path to resource, works for dev and for PyInstaller"""
    if getattr(sys, "frozen", False) and hasattr(sys, "_MEIPASS"):
        path_in_meipass = relative_path[len("resources/"):] if relative_path.startswith("resources/") else relative_path
        return os.path.join(sys._MEIPASS, path_in_meipass.replace("/", os.sep))
    else:
        base_path = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
        return os.path.join(base_path, relative_path.replace("/", os.sep))

CHECK_ICON_PATH = get_resource_path("resources/icons/check.png").replace("\\", "/")

BACKGROUND = "#050607"
ALT_BACKGROUND = "#191A1B"
ACCENT = "#FF6922"
DISABLED_ACCENT = "#662810"
BORDER = "#333333"
HOVER_BORDER = "#555555"
DISABLED_BORDER = "#111111"
TEXT_COLOR = "#EDEDED"
DISABLED_TEXT_COLOR = "#222222"

class QuickToolTipStyle(QtWidgets.QProxyStyle):
    def styleHint(self, hint, option=None, widget=None, returnData=None):
        if hint == QtWidgets.QStyle.SH_ToolTip_WakeUpDelay:
            return 50  # 50 ms delay
        if hint == QtWidgets.QStyle.SH_ToolTip_FallAsleepDelay:
            return 2000
        return super().styleHint(hint, option, widget, returnData)

QSS = f"""
QToolTip {{
    background-color: {ALT_BACKGROUND};
    color: {TEXT_COLOR};
    border: 1px solid {BORDER};
    border-radius: 4px;
    padding: 6px;
    font-family: Inter;
    font-size: 9pt;
}}

QScrollBar:vertical {{
    border: none;
    background: {BACKGROUND};
    width: 10px;
    margin: 0px;
}}
QScrollBar::handle:vertical {{
    background: {BORDER};
    min-height: 20px;
    border-radius: 5px;
}}
QScrollBar::handle:vertical:hover {{
    background: {ACCENT};
}}
QScrollBar::add-line:vertical, QScrollBar::sub-line:vertical {{
    height: 0px;
    background: none;
}}
QScrollBar::add-page:vertical, QScrollBar::sub-page:vertical {{
    background: none;
}}

QScrollBar:horizontal {{
    border: none;
    background: {BACKGROUND};
    height: 10px;
    margin: 0px;
}}
QScrollBar::handle:horizontal {{
    background: {BORDER};
    min-width: 20px;
    border-radius: 5px;
}}
QScrollBar::handle:horizontal:hover {{
    background: {ACCENT};
}}
QScrollBar::add-line:horizontal, QScrollBar::sub-line:horizontal {{
    width: 0px;
    background: none;
}}
QScrollBar::add-page:horizontal, QScrollBar::sub-page:horizontal {{
    background: none;
}}

QCalendarWidget {{
    background-color: {BACKGROUND};
    border: 1px solid {BORDER};
    border-radius: 8px;
}}
QCalendarWidget QWidget#qt_calendar_navigationbar {{
    background-color: {ALT_BACKGROUND};
    border-bottom: 1px solid {BORDER};
}}
QCalendarWidget QToolButton {{
    background-color: transparent;
    color: {TEXT_COLOR};
    border: none;
    border-radius: 4px;
    font-weight: bold;
    padding: 4px 8px;
    margin: 2px;
}}
QCalendarWidget QToolButton:hover {{
    background-color: {ACCENT};
    color: #ffffff;
}}
QCalendarWidget QToolButton::menu-indicator {{
    image: none;
}}
QCalendarWidget QMenu {{
    background-color: {ALT_BACKGROUND};
    color: {TEXT_COLOR};
    border: 1px solid {BORDER};
}}
QCalendarWidget QSpinBox {{
    background-color: {ALT_BACKGROUND};
    color: {TEXT_COLOR};
    border: 1px solid {BORDER};
    border-radius: 4px;
    margin-right: 4px;
}}
QCalendarWidget QSpinBox::up-button, QCalendarWidget QSpinBox::down-button {{
    subcontrol-origin: border;
    width: 16px;
}}
QCalendarWidget QTableView {{
    background-color: {BACKGROUND};
    color: {TEXT_COLOR};
    selection-background-color: {ACCENT};
    selection-color: #ffffff;
    border: none;
    gridline-color: {ALT_BACKGROUND};
}}
QCalendarWidget QHeaderView::section {{
    background-color: {ALT_BACKGROUND};
    color: {TEXT_COLOR};
    border: none;
    padding: 4px;
}}
QCalendarWidget QAbstractItemView:enabled {{
    color: {TEXT_COLOR};
    background-color: {BACKGROUND};
    selection-background-color: {ACCENT};
    selection-color: #ffffff;
}}
QCalendarWidget QAbstractItemView:disabled {{
    color: #555555;
}}

* {{
    font-family: Inter;
    font-size: 10.85pt;
    color: {TEXT_COLOR};
    selection-background-color: {ACCENT};
    selection-color: {TEXT_COLOR};
}}

QDialog {{
    background-color: {BACKGROUND};
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
QComboBox, QDateEdit {{
    background: {ALT_BACKGROUND};
    border: 1px solid {BORDER};
    border-radius: 4px;
    padding: 4px 12px;
    color: {TEXT_COLOR};
    min-height: 28px;
    max-height: 28px;
}}
QComboBox:hover, QDateEdit:hover {{
    border-color: {HOVER_BORDER};
}}
QComboBox:focus, QDateEdit:focus {{
    border-color: {ACCENT};
}}
QComboBox::drop-down {{
    subcontrol-origin: padding;
    subcontrol-position: top right;
    width: 24px;
    border-left: none;
}}
QComboBox QListView {{
    background-color: {ALT_BACKGROUND};
    border: 1px solid {BORDER};
    color: {TEXT_COLOR};
    selection-background-color: {ACCENT};
    selection-color: #ffffff;
    outline: 0;
}}
QComboBox QListView::item {{
    padding: 6px 10px;
    color: {TEXT_COLOR};
    background-color: {ALT_BACKGROUND};
}}
QComboBox QListView::item:selected {{
    background-color: {ACCENT};
    color: #ffffff;
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
    image: url({CHECK_ICON_PATH});
}}
QCheckBox::indicator:unchecked:hover {{
    border-color: {HOVER_BORDER};
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

def set_immersive_dark_mode(window):
    try:
        import ctypes
        hwnd = int(window.winId())
        dwmapi = ctypes.windll.dwmapi

        # 1. Enable Immersive Dark Mode (for dark titlebar text & controls)
        DWMWA_USE_IMMERSIVE_DARK_MODE = 20
        DWMWA_USE_IMMERSIVE_DARK_MODE_OLD = 19
        value = ctypes.c_int(1)
        hr = dwmapi.DwmSetWindowAttribute(
            hwnd,
            DWMWA_USE_IMMERSIVE_DARK_MODE,
            ctypes.byref(value),
            ctypes.sizeof(value)
        )
        if hr != 0:
            dwmapi.DwmSetWindowAttribute(
                hwnd,
                DWMWA_USE_IMMERSIVE_DARK_MODE_OLD,
                ctypes.byref(value),
                ctypes.sizeof(value)
            )

        # 2. Set Custom Caption Color (Win11) to BACKGROUND (#050607) -> 0x00070605
        DWMWA_CAPTION_COLOR = 35
        caption_color = ctypes.c_int(0x00070605)
        dwmapi.DwmSetWindowAttribute(
            hwnd,
            DWMWA_CAPTION_COLOR,
            ctypes.byref(caption_color),
            ctypes.sizeof(caption_color)
        )

        # 3. Set Border Color (Win11) to BORDER (#333333) -> 0x00333333
        DWMWA_BORDER_COLOR = 34
        border_color = ctypes.c_int(0x00333333)
        dwmapi.DwmSetWindowAttribute(
            hwnd,
            DWMWA_BORDER_COLOR,
            ctypes.byref(border_color),
            ctypes.sizeof(border_color)
        )
    except Exception:
        pass
