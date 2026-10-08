"""
galIMVmini Filmstrip / Thumbnail Navigation Strip.
Displays a horizontal scrollable row of thumbnails from the active folder,
providing instant one-click switching and next/previous browsing.
"""

import os
from typing import List, Optional
from PyQt6.QtWidgets import (
    QWidget, QHBoxLayout, QScrollArea, QLabel, QFrame,
    QSizePolicy, QPushButton
)
from PyQt6.QtCore import Qt, pyqtSignal, QSize
from PyQt6.QtGui import QPixmap, QCursor, QColor

try:
    from core.theme import ThemeManager
except ImportError:
    from galIMVmini.core.theme import ThemeManager


class ThumbnailItem(QFrame):
    clicked = pyqtSignal(str)

    def __init__(self, file_path: str, is_active: bool = False, parent=None):
        super().__init__(parent)
        self.file_path = file_path
        self._is_active = is_active
        self.setFixedSize(68, 68)
        self.setFrameShape(QFrame.Shape.NoFrame)
        self.setCursor(QCursor(Qt.CursorShape.PointingHandCursor))

        self._layout = QHBoxLayout(self)
        self._layout.setContentsMargins(2, 2, 2, 2)
        self._layout.setAlignment(Qt.AlignmentFlag.AlignCenter)

        self._img_label = QLabel(self)
        self._img_label.setAlignment(Qt.AlignmentFlag.AlignCenter)
        self._img_label.setScaledContents(False)
        self._img_label.setStyleSheet("border: none; background: transparent;")
        self._layout.addWidget(self._img_label)

        self.setToolTip(os.path.basename(file_path))
        self._load_thumb()
        self.update_style()

    def _load_thumb(self):
        pix = QPixmap(self.file_path)
        if not pix.isNull():
            scaled = pix.scaled(
                60, 60,
                Qt.AspectRatioMode.KeepAspectRatio,
                Qt.TransformationMode.SmoothTransformation
            )
            self._img_label.setPixmap(scaled)

    def set_active(self, active: bool):
        if self._is_active != active:
            self._is_active = active
            self.update_style()

    def update_style(self):
        c = ThemeManager.get_instance().get_colors()
        if self._is_active:
            border = f"2px solid {c.accent}"
            bg = c.accent_subtle
        else:
            border = f"1px solid {c.border_subtle}"
            bg = c.bg_card

        self.setStyleSheet(f"""
            ThumbnailItem {{
                background-color: {bg};
                border: {border};
                border-radius: 6px;
            }}
            ThumbnailItem:hover {{
                border-color: {c.accent};
                background-color: {c.bg_elevated};
            }}
        """)

    def mousePressEvent(self, event):
        if event.button() == Qt.MouseButton.LeftButton:
            self.clicked.emit(self.file_path)
        super().mousePressEvent(event)


class FilmstripBar(QFrame):
    image_selected = pyqtSignal(str)

    def __init__(self, parent=None):
        super().__init__(parent)
        self.setFixedHeight(82)
        self.setFrameShape(QFrame.Shape.NoFrame)
        self._items: List[ThumbnailItem] = []
        self._active_path: str = ""
        self.setVisible(False)  # Hidden by default until an image folder is loaded!

        main_layout = QHBoxLayout(self)
        main_layout.setContentsMargins(6, 4, 6, 4)
        main_layout.setSpacing(6)

        # Scroll Area for thumbnails - Explicitly transparent to eliminate white box!
        self._scroll = QScrollArea(self)
        self._scroll.setVerticalScrollBarPolicy(Qt.ScrollBarPolicy.ScrollBarAlwaysOff)
        self._scroll.setHorizontalScrollBarPolicy(Qt.ScrollBarPolicy.ScrollBarAsNeeded)
        self._scroll.setWidgetResizable(True)
        self._scroll.setFrameShape(QFrame.Shape.NoFrame)
        self._scroll.setStyleSheet("background: transparent; border: none;")
        self._scroll.viewport().setStyleSheet("background: transparent;")

        self._container = QWidget()
        self._container.setStyleSheet("background: transparent;")
        self._container_layout = QHBoxLayout(self._container)
        self._container_layout.setContentsMargins(2, 2, 2, 2)
        self._container_layout.setSpacing(6)
        self._container_layout.setAlignment(Qt.AlignmentFlag.AlignLeft | Qt.AlignmentFlag.AlignVCenter)
        self._scroll.setWidget(self._container)

        main_layout.addWidget(self._scroll)

        self.update_theme()
        ThemeManager.get_instance().add_listener(self.update_theme)

    def update_theme(self):
        c = ThemeManager.get_instance().get_colors()
        self.setStyleSheet(f"""
            FilmstripBar {{
                background-color: {c.bg_surface};
                border-top: 1px solid {c.border_subtle};
            }}
        """)
        for item in self._items:
            item.update_style()

    def set_images(self, file_paths: List[str], current_path: str):
        self._active_path = current_path
        
        # Clear existing items
        while self._container_layout.count():
            it = self._container_layout.takeAt(0)
            if it and it.widget():
                it.widget().deleteLater()
        self._items.clear()

        if not file_paths:
            self.setVisible(False)
            return

        self.setVisible(True)

        # Add new thumbnails
        active_widget = None
        for p in file_paths:
            is_act = (os.path.abspath(p) == os.path.abspath(current_path))
            item = ThumbnailItem(p, is_active=is_act, parent=self._container)
            item.clicked.connect(self._on_item_clicked)
            self._container_layout.addWidget(item)
            self._items.append(item)
            if is_act:
                active_widget = item

        # Scroll active item into view
        if active_widget:
            self._scroll.ensureWidgetVisible(active_widget, 40, 0)

    def set_active_image(self, current_path: str):
        self._active_path = current_path
        active_widget = None
        for item in self._items:
            is_act = (os.path.abspath(item.file_path) == os.path.abspath(current_path))
            item.set_active(is_act)
            if is_act:
                active_widget = item

        if active_widget:
            self._scroll.ensureWidgetVisible(active_widget, 40, 0)

    def _on_item_clicked(self, file_path: str):
        self.image_selected.emit(file_path)
