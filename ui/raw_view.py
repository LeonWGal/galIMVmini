"""
galIMVmini Raw Metadata Text & JSON Inspector.
Allows viewing unparsed raw chunk data, ComfyUI node graphs, and EXIF dumps.
"""

import json
from typing import Optional
import pyperclip

from PyQt6.QtWidgets import (
    QWidget, QVBoxLayout, QHBoxLayout, QComboBox, QTextEdit,
    QPushButton, QLabel
)
from PyQt6.QtCore import Qt, pyqtSignal
from PyQt6.QtGui import QFont, QCursor

try:
    from core.theme import ThemeManager
    from core.metadata import ImageMetadata
    from core.i18n import I18nManager
except ImportError:
    from galIMVmini.core.theme import ThemeManager
    from galIMVmini.core.metadata import ImageMetadata
    from galIMVmini.core.i18n import I18nManager


class RawTextView(QWidget):
    status_requested = pyqtSignal(str)

    def __init__(self, parent=None):
        super().__init__(parent)
        self._meta: Optional[ImageMetadata] = None

        layout = QVBoxLayout(self)
        layout.setContentsMargins(6, 4, 6, 6)
        layout.setSpacing(5)

        # Header controls
        hdr = QHBoxLayout()
        hdr.setSpacing(8)

        self._lbl = QLabel("Источник:", self)
        hdr.addWidget(self._lbl)

        self._combo = QComboBox(self)
        self._combo.currentIndexChanged.connect(self._on_source_changed)
        hdr.addWidget(self._combo, 1)

        self._fmt_json_btn = QPushButton("Форматировать JSON", self)
        self._fmt_json_btn.clicked.connect(self._format_json)
        hdr.addWidget(self._fmt_json_btn)

        self._copy_btn = QPushButton("Копировать всё", self)
        self._copy_btn.clicked.connect(self._copy_all)
        hdr.addWidget(self._copy_btn)

        layout.addLayout(hdr)

        # Monospace Text Box
        self._text_edit = QTextEdit(self)
        self._text_edit.setReadOnly(True)
        mono_font = QFont("Consolas, Courier New, monospace", 10)
        self._text_edit.setFont(mono_font)
        layout.addWidget(self._text_edit)

        self.update_translations()
        self.update_theme()
        ThemeManager.get_instance().add_listener(self.update_theme)
        I18nManager.get_instance().add_listener(self.update_translations)

    def update_translations(self):
        i18n = I18nManager.get_instance()
        self._lbl.setText(i18n.tr("common.source", "Источник:"))
        self._fmt_json_btn.setText(i18n.tr("common.format_json", "Форматировать JSON"))
        self._copy_btn.setText(i18n.tr("common.copy_all", "Копировать всё"))
        if not self._meta or not self._meta.raw_texts:
            self._text_edit.setPlainText(i18n.tr("raw.no_data", "Нет исходных текстовых метаданных"))

    def update_theme(self):
        c = ThemeManager.get_instance().get_colors()
        self._combo.setStyleSheet(f"""
            QComboBox {{
                background-color: {c.bg_card};
                color: {c.text_primary};
                border: 1px solid {c.border_subtle};
                border-radius: 6px;
                padding: 4px 10px;
            }}
            QComboBox::drop-down {{
                border: none;
            }}
        """)

    def set_metadata(self, meta: ImageMetadata):
        self._meta = meta
        self._combo.clear()
        self._text_edit.clear()

        if not meta or not meta.raw_texts:
            self._text_edit.setPlainText(I18nManager.get_instance().tr("raw.no_data", "Нет исходных текстовых метаданных"))
            return

        for key in sorted(meta.raw_texts.keys()):
            self._combo.addItem(key, meta.raw_texts[key])

        if meta.sidecar_text:
            self._combo.addItem("sidecar_text (.txt)", meta.sidecar_text)

        if self._combo.count() > 0:
            self._combo.setCurrentIndex(0)
            self._on_source_changed(0)

    def _on_source_changed(self, index: int):
        if index >= 0:
            data = self._combo.itemData(index)
            if data is not None:
                self._text_edit.setPlainText(str(data))

    def _format_json(self):
        txt = self._text_edit.toPlainText().strip()
        i18n = I18nManager.get_instance()
        try:
            parsed = json.loads(txt)
            formatted = json.dumps(parsed, indent=2, ensure_ascii=False)
            self._text_edit.setPlainText(formatted)
            self.status_requested.emit(i18n.tr("raw.json_formatted", "JSON отформатирован"))
        except Exception:
            self.status_requested.emit(i18n.tr("raw.invalid_json", "Текст не является валидным JSON"))

    def _copy_all(self):
        txt = self._text_edit.toPlainText()
        if txt:
            pyperclip.copy(txt)
            i18n = I18nManager.get_instance()
            self.status_requested.emit(i18n.tr("status.copied", "Скопировано"))
