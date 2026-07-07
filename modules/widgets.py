from PyQt5 import QtCore, QtWidgets
from modules.styles import ALT_BACKGROUND, BORDER, TEXT_COLOR, ACCENT

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
    from PyQt5 import QtGui
    qobj.setCursor(QtGui.QCursor(QtCore.Qt.PointingHandCursor))

class AddonListWidget(QtWidgets.QListWidget):
    def sizeHint(self):
        count = self.count()
        if count == 0:
            return QtCore.QSize(100, 60)
        # Approximate item height is 24px
        total_height = 24 * count + 8
        return QtCore.QSize(100, max(60, min(total_height, 250)))

class AddonListEditor(QtWidgets.QWidget):
    def __init__(self, parent=None, placeholder_text="", is_extension=False):
        super().__init__(parent)
        self.is_extension = is_extension
        self.action_history = []

        layout = QtWidgets.QVBoxLayout(self)
        layout.setContentsMargins(4, 4, 4, 4)
        layout.setSpacing(8)

        self.list_widget = AddonListWidget(self)
        self.list_widget.setSizePolicy(QtWidgets.QSizePolicy.Expanding, QtWidgets.QSizePolicy.Preferred)
        self.list_widget.setStyleSheet(f"""
            QListWidget {{
                background: {ALT_BACKGROUND};
                border: 1px solid {BORDER};
                border-radius: 4px;
                color: {TEXT_COLOR};
            }}
        """)
        layout.addWidget(self.list_widget)

        # Bottom controls: Input row
        controls = QtWidgets.QHBoxLayout()
        controls.setSpacing(6)

        self.input_edit = QtWidgets.QLineEdit(self)
        self.input_edit.setPlaceholderText(f"Enter {placeholder_text} Link, File, or Folder path...")
        self.input_edit.setStyleSheet(f"""
            QLineEdit {{
                background: {ALT_BACKGROUND};
                border: 1px solid {BORDER};
                border-radius: 4px;
                padding: 4px 8px;
                color: {TEXT_COLOR};
            }}
            QLineEdit:focus {{
                border-color: {ACCENT};
            }}
        """)
        controls.addWidget(self.input_edit)

        btn_style = f"""
            QPushButton {{
                background: {ALT_BACKGROUND};
                border: 1px solid {BORDER};
                border-radius: 4px;
                padding: 4px 8px;
                color: {TEXT_COLOR};
                font-family: Inter;
                font-size: 9pt;
                font-weight: 500;
                min-width: 30px;
                max-width: 30px;
                min-height: 28px;
                max-height: 28px;
            }}
            QPushButton:hover {{
                border-color: {ACCENT};
                color: {ACCENT};
            }}
        """

        self.file_btn = QtWidgets.QPushButton("📁", self)
        self.file_btn.setToolTip("Browse File")
        self.file_btn.setStyleSheet(btn_style)
        self.file_btn.clicked.connect(self.browse_file)
        clickable(self.file_btn)
        controls.addWidget(self.file_btn)

        self.folder_btn = QtWidgets.QPushButton("📂", self)
        self.folder_btn.setToolTip("Browse Folder")
        self.folder_btn.setStyleSheet(btn_style)
        self.folder_btn.clicked.connect(self.browse_folder)
        clickable(self.folder_btn)
        controls.addWidget(self.folder_btn)

        self.add_btn = QtWidgets.QPushButton("＋", self)
        self.add_btn.setToolTip("Add to List")
        self.add_btn.setStyleSheet(btn_style)
        self.add_btn.clicked.connect(self.add_item_from_input)
        clickable(self.add_btn)
        controls.addWidget(self.add_btn)

        self.remove_btn = QtWidgets.QPushButton("－", self)
        self.remove_btn.setToolTip("Remove Selected")
        self.remove_btn.setStyleSheet(btn_style)
        self.remove_btn.clicked.connect(self.remove_item)
        clickable(self.remove_btn)
        controls.addWidget(self.remove_btn)

        self.undo_addon_btn = QtWidgets.QPushButton("↶", self)
        self.undo_addon_btn.setToolTip("Undo Last List Change")
        self.undo_addon_btn.setStyleSheet(btn_style)
        self.undo_addon_btn.clicked.connect(self.undo_action)
        clickable(self.undo_addon_btn)
        controls.addWidget(self.undo_addon_btn)

        layout.addLayout(controls)

    def add_items(self, items):
        for item in items:
            self.list_widget.addItem(item)

    def get_items(self):
        return [self.list_widget.item(i).text() for i in range(self.list_widget.count())]

    def add_item_from_input(self):
        text = self.input_edit.text().strip()
        if text:
            self.list_widget.addItem(text)
            self.action_history.append(('add', text))
            self.input_edit.clear()
            self.list_widget.updateGeometry()
            parent_dialog = self.window()
            if isinstance(parent_dialog, QtWidgets.QDialog):
                parent_dialog.resize(0, 0)
                parent_dialog.adjustSize()

    def browse_file(self):
        filter_str = "JavaScript Files (*.js);;Zip Files (*.zip);;All Files (*)" if self.is_extension else "Zip Files (*.zip);;All Files (*)"
        file_path, _ = QtWidgets.QFileDialog.getOpenFileName(
            self,
            "Select Custom Addon File",
            "",
            filter_str
        )
        if file_path:
            self.input_edit.setText(file_path.replace("/", "\\"))

    def browse_folder(self):
        folder_path = QtWidgets.QFileDialog.getExistingDirectory(
            self,
            "Select Custom Addon Folder",
            ""
        )
        if folder_path:
            self.input_edit.setText(folder_path.replace("/", "\\"))

    def remove_item(self):
        current_item = self.list_widget.currentItem()
        if current_item:
            row = self.list_widget.row(current_item)
            text = current_item.text()
            self.action_history.append(('remove', row, text))
            self.list_widget.takeItem(row)
            self.list_widget.updateGeometry()
            parent_dialog = self.window()
            if isinstance(parent_dialog, QtWidgets.QDialog):
                parent_dialog.resize(0, 0)
                parent_dialog.adjustSize()

    def undo_action(self):
        if self.action_history:
            action = self.action_history.pop()
            if action[0] == 'add':
                text = action[1]
                for i in range(self.list_widget.count()):
                    if self.list_widget.item(i).text() == text:
                        self.list_widget.takeItem(i)
                        break
            elif action[0] == 'remove':
                row, text = action[1], action[2]
                self.list_widget.insertItem(row, text)
            self.list_widget.updateGeometry()
            parent_dialog = self.window()
            if isinstance(parent_dialog, QtWidgets.QDialog):
                parent_dialog.resize(0, 0)
                parent_dialog.adjustSize()
