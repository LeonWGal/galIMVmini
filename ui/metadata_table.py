"""
galIMVmini Detailed Metadata Inspector Table.
Presents all extracted file properties, image metrics, generation parameters,
EXIF tags, and GPS coordinates with live search and fast clipboard copying.
"""

from typing import Dict, Optional
import pyperclip

from PyQt6.QtWidgets import (
    QWidget, QVBoxLayout, QHBoxLayout, QLabel, QLineEdit,
    QTableWidget, QTableWidgetItem, QHeaderView, QMenu
)
from PyQt6.QtCore import Qt, pyqtSignal
from PyQt6.QtGui import QColor, QFont, QCursor, QAction

try:
    from core.theme import ThemeManager
    from core.metadata import ImageMetadata
    from core.i18n import I18nManager
except ImportError:
    from galIMVmini.core.theme import ThemeManager
    from galIMVmini.core.metadata import ImageMetadata
    from galIMVmini.core.i18n import I18nManager


class MetadataTableView(QWidget):
    status_requested = pyqtSignal(str)

    def __init__(self, parent=None):
        super().__init__(parent)
        self._meta: Optional[ImageMetadata] = None

        layout = QVBoxLayout(self)
        layout.setContentsMargins(6, 4, 6, 6)
        layout.setSpacing(5)

        # Search Bar
        search_layout = QHBoxLayout()
        search_layout.setSpacing(8)

        self._search_input = QLineEdit(self)
        self._search_input.setPlaceholderText("Фильтр по метаданным...")
        self._search_input.setClearButtonEnabled(True)
        self._search_input.textChanged.connect(self._filter_table)
        search_layout.addWidget(self._search_input)

        layout.addLayout(search_layout)

        # Table Widget
        self._table = QTableWidget(0, 2, self)
        self._table.setHorizontalHeaderLabels(["Свойство", "Значение"])
        self._table.horizontalHeader().setSectionResizeMode(0, QHeaderView.ResizeMode.Interactive)
        self._table.setColumnWidth(0, 150)
        self._table.horizontalHeader().setSectionResizeMode(1, QHeaderView.ResizeMode.Stretch)
        self._table.verticalHeader().setVisible(False)
        self._table.setWordWrap(True)
        self._table.setContextMenuPolicy(Qt.ContextMenuPolicy.CustomContextMenu)
        self._table.customContextMenuRequested.connect(self._show_context_menu)
        self._table.cellDoubleClicked.connect(self._on_cell_double_clicked)

        layout.addWidget(self._table)

        self.update_translations()
        self.update_theme()
        ThemeManager.get_instance().add_listener(self.update_theme)
        I18nManager.get_instance().add_listener(self.update_translations)

    def update_translations(self):
        i18n = I18nManager.get_instance()
        self._search_input.setPlaceholderText(i18n.tr("sidebar.filter_tags", "Фильтр по метаданным..."))
        prop_lbl = i18n.tr("common.property", "Свойство")
        val_lbl = i18n.tr("common.value", "Значение")
        self._table.setHorizontalHeaderLabels([prop_lbl, val_lbl])
        if self._meta:
            self.set_metadata(self._meta)

    def update_theme(self):
        c = ThemeManager.get_instance().get_colors()
        self._table.setStyleSheet(f"""
            QTableWidget {{
                background-color: {c.bg_surface};
                color: {c.text_primary};
                border: 1px solid {c.border_subtle};
                border-radius: 8px;
                gridline-color: {c.border_subtle};
                selection-background-color: {c.accent_subtle};
            }}
            QHeaderView::section {{
                background-color: {c.bg_card};
                color: {c.text_secondary};
                padding: 6px 10px;
                border: none;
                border-bottom: 1px solid {c.border_subtle};
                font-weight: 600;
            }}
        """)
        self._reapply_row_styles()

    def set_metadata(self, meta: ImageMetadata):
        self._meta = meta
        self._table.setUpdatesEnabled(False)
        try:
            self._table.setRowCount(0)
            self._search_input.clear()

            if not meta:
                return

            for category, items in meta.categories.items():
                if not items:
                    continue

                # Insert Category Header Row
                cat_row = self._table.rowCount()
                self._table.insertRow(cat_row)
                cat_slug = category.lower().replace(" ", "_").replace("/", "___")
                cat_name = I18nManager.get_instance().tr(f"category.{cat_slug}", category.upper())
                cat_item = QTableWidgetItem(f"  {cat_name.upper()}")
                cat_item.setTextAlignment(Qt.AlignmentFlag.AlignLeft | Qt.AlignmentFlag.AlignVCenter)
                cat_item.setFlags(Qt.ItemFlag.NoItemFlags)

                font = cat_item.font()
                font.setBold(True)
                font.setPointSize(9)
                cat_item.setFont(font)

                self._table.setItem(cat_row, 0, cat_item)
                self._table.setSpan(cat_row, 0, 1, 2)

                # Insert Key-Value items
                for key, val in items.items():
                    row = self._table.rowCount()
                    self._table.insertRow(row)

                    k_item = QTableWidgetItem(str(key))
                    k_item.setFlags(k_item.flags() & ~Qt.ItemFlag.ItemIsEditable)
                    k_item.setToolTip(str(key))

                    v_item = QTableWidgetItem(str(val))
                    v_item.setFlags(v_item.flags() & ~Qt.ItemFlag.ItemIsEditable)
                    v_item.setToolTip(str(val))

                    self._table.setItem(row, 0, k_item)
                    self._table.setItem(row, 1, v_item)

        finally:
            self._table.setUpdatesEnabled(True)

        self._reapply_row_styles()
        self._table.resizeRowsToContents()
        for r in range(self._table.rowCount()):
            if self._table.columnSpan(r, 0) == 2:
                self._table.setRowHeight(r, 26)
            else:
                curr_h = self._table.rowHeight(r)
                self._table.setRowHeight(r, max(22, min(95, curr_h)))

    def _reapply_row_styles(self):
        c = ThemeManager.get_instance().get_colors()
        cat_bg = QColor(c.bg_card)
        cat_fg = QColor(c.accent)

        for r in range(self._table.rowCount()):
            if self._table.columnSpan(r, 0) == 2:
                item = self._table.item(r, 0)
                if item:
                    item.setBackground(cat_bg)
                    item.setForeground(cat_fg)
            else:
                bg = QColor(c.bg_surface if r % 2 == 0 else c.bg_card)
                k_item = self._table.item(r, 0)
                v_item = self._table.item(r, 1)
                if k_item:
                    k_item.setBackground(bg)
                    k_item.setForeground(QColor(c.text_secondary))
                if v_item:
                    v_item.setBackground(bg)
                    v_item.setForeground(QColor(c.text_primary))

    def _filter_table(self, query: str):
        q = query.strip().lower()
        if not q:
            for r in range(self._table.rowCount()):
                self._table.setRowHidden(r, False)
            return

        cat_row = None
        has_visible_in_cat = False
        cat_rows_to_show = set()

        for r in range(self._table.rowCount()):
            if self._table.columnSpan(r, 0) == 2:
                # Previous category
                if cat_row is not None and has_visible_in_cat:
                    cat_rows_to_show.add(cat_row)
                cat_row = r
                has_visible_in_cat = False
                self._table.setRowHidden(r, True)
            else:
                k_item = self._table.item(r, 0)
                v_item = self._table.item(r, 1)
                k_txt = k_item.text().lower() if k_item else ""
                v_txt = v_item.text().lower() if v_item else ""
                match = (q in k_txt or q in v_txt)
                self._table.setRowHidden(r, not match)
                if match:
                    has_visible_in_cat = True

        if cat_row is not None and has_visible_in_cat:
            cat_rows_to_show.add(cat_row)

        for cr in cat_rows_to_show:
            self._table.setRowHidden(cr, False)

    def _on_cell_double_clicked(self, row: int, col: int):
        if self._table.columnSpan(row, 0) == 2:
            return
        item = self._table.item(row, col)
        if item and item.text():
            pyperclip.copy(item.text())
            i18n = I18nManager.get_instance()
            self.status_requested.emit(i18n.tr("status.val_copied", "Значение скопировано"))

    def _show_context_menu(self, pos):
        item = self._table.itemAt(pos)
        if not item:
            return

        row = item.row()
        if self._table.columnSpan(row, 0) == 2:
            return

        i18n = I18nManager.get_instance()
        menu = QMenu(self)
        copy_val_act = menu.addAction(i18n.tr("context.copy_val", "Копировать значение"))
        copy_row_act = menu.addAction(i18n.tr("context.copy_row", "Копировать строку (Свойство: Значение)"))
        copy_all_act = menu.addAction(i18n.tr("context.copy_all_meta", "Копировать все метаданные"))

        action = menu.exec(self._table.mapToGlobal(pos))
        k_item = self._table.item(row, 0)
        v_item = self._table.item(row, 1)

        if action == copy_val_act and v_item:
            pyperclip.copy(v_item.text())
            self.status_requested.emit(i18n.tr("status.val_copied", "Значение скопировано"))
        elif action == copy_row_act and k_item and v_item:
            pyperclip.copy(f"{k_item.text()}: {v_item.text()}")
            self.status_requested.emit(i18n.tr("status.row_copied", "Строка скопирована"))
        elif action == copy_all_act:
            self.copy_all_formatted()

    def copy_all_formatted(self):
        lines = []
        for r in range(self._table.rowCount()):
            if self._table.columnSpan(r, 0) == 2:
                hdr = self._table.item(r, 0).text().strip()
                lines.append(f"\n=== {hdr} ===")
            else:
                k = self._table.item(r, 0).text() if self._table.item(r, 0) else ""
                v = self._table.item(r, 1).text() if self._table.item(r, 1) else ""
                lines.append(f"{k}: {v}")
        result = "\n".join(lines).strip()
        pyperclip.copy(result)
        i18n = I18nManager.get_instance()
        self.status_requested.emit(i18n.tr("status.all_meta_copied", "Все метаданные скопированы"))
