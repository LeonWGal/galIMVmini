"""
galIMVmini Main Application Window.
Unified interface combining galMDV's metadata extraction with
galIMV's authentic Lobe Neo styling, Tabler vector icons, and lightweight single-image inspection.
"""

import os
import sys
import json
import csv
from typing import List, Optional
import pyperclip

from PyQt6.QtWidgets import (
    QMainWindow, QWidget, QVBoxLayout, QHBoxLayout, QSplitter,
    QToolBar, QToolButton, QPushButton, QLabel, QFileDialog, QTabWidget,
    QStatusBar, QMenu, QDialog, QMessageBox, QFrame, QApplication,
    QSizePolicy
)
from PyQt6.QtCore import Qt, QSettings, QTimer, QUrl, QSize
from PyQt6.QtGui import (
    QAction, QIcon, QKeySequence, QDesktopServices, QColor, QFont
)

try:
    from core.theme import ThemeManager, LOBE_ACCENTS
    from core.metadata import MetadataReader, ImageMetadata
    from core.icons import get_tabler_icon
    from core.i18n import I18nManager, LOCALES
    from ui.image_canvas import ImageCanvas
    from ui.prompt_card import PromptCardView
    from ui.metadata_table import MetadataTableView
    from ui.raw_view import RawTextView
except ImportError:
    from galIMVmini.core.theme import ThemeManager, LOBE_ACCENTS
    from galIMVmini.core.metadata import MetadataReader, ImageMetadata
    from galIMVmini.core.icons import get_tabler_icon
    from galIMVmini.core.i18n import I18nManager, LOCALES
    from galIMVmini.ui.image_canvas import ImageCanvas
    from galIMVmini.ui.prompt_card import PromptCardView
    from galIMVmini.ui.metadata_table import MetadataTableView
    from galIMVmini.ui.raw_view import RawTextView

SUPPORTED_EXTS = (".png", ".jpg", ".jpeg", ".webp", ".gif", ".bmp", ".tiff")


class MainWindow(QMainWindow):
    def __init__(self):
        super().__init__()
        self.setWindowTitle("galIMVmini")
        self.setMinimumSize(860, 520)
        self.resize(1200, 780)

        self._settings = QSettings("galIMV", "galIMVmini")
        self._current_path: str = ""
        self._current_meta: Optional[ImageMetadata] = None

        # Load icon if available
        icon_path = os.path.join(os.path.dirname(__file__), "..", "resources", "app.ico")
        if os.path.exists(icon_path):
            self.setWindowIcon(QIcon(icon_path))

        # Build UI layout
        self._init_ui()
        self._load_settings()
        self._setup_shortcuts()

        # Update styling
        self.update_theme()
        ThemeManager.get_instance().add_listener(self.update_theme)
        I18nManager.get_instance().add_listener(self.update_translations)

    def _init_ui(self):
        # 1. Central Splitter & Widgets
        central = QWidget(self)
        self.setCentralWidget(central)
        central_layout = QVBoxLayout(central)
        central_layout.setContentsMargins(0, 0, 0, 0)
        central_layout.setSpacing(0)

        self._splitter = QSplitter(Qt.Orientation.Horizontal, self)
        self._splitter.setChildrenCollapsible(False)
        central_layout.addWidget(self._splitter)

        # Left Container: Canvas only (no metrics bar, no constraint from filename)
        left_container = QWidget(self)
        left_layout = QVBoxLayout(left_container)
        left_layout.setContentsMargins(0, 0, 0, 0)
        left_layout.setSpacing(0)

        self._canvas = ImageCanvas(left_container)
        self._canvas.image_dropped.connect(self.load_image)
        self._canvas.open_requested.connect(self.browse_file)
        self._canvas.zoom_changed.connect(self._on_zoom_changed)
        left_layout.addWidget(self._canvas, 1)

        self._splitter.addWidget(left_container)

        # Right Container: Inspector Tabs (50/50 proportion, responsive)
        self._right_container = QWidget(self)
        self._right_container.setMinimumWidth(300)
        right_layout = QVBoxLayout(self._right_container)
        right_layout.setContentsMargins(4, 2, 4, 2)
        right_layout.setSpacing(2)

        self._tabs = QTabWidget(self._right_container)
        
        self._prompt_card = PromptCardView(self._tabs)
        self._prompt_card.status_requested.connect(self.show_status)
        self._tabs.addTab(self._prompt_card, "Промпт")

        self._meta_table = MetadataTableView(self._tabs)
        self._meta_table.status_requested.connect(self.show_status)
        self._tabs.addTab(self._meta_table, "Метаданные")

        self._raw_view = RawTextView(self._tabs)
        self._raw_view.status_requested.connect(self.show_status)
        self._tabs.addTab(self._raw_view, "Raw")

        right_layout.addWidget(self._tabs)
        self._splitter.addWidget(self._right_container)

        # Splitter proportion: Default 50 / 50 equal stretch
        self._splitter.setStretchFactor(0, 1)
        self._splitter.setStretchFactor(1, 1)
        self._splitter.setSizes([600, 600])

        # 2. Main Toolbar
        self._create_toolbar()

        # 3. Status Bar
        self._status_bar = QStatusBar(self)
        self.setStatusBar(self._status_bar)
        self._status_msg = QLabel(I18nManager.get_instance().tr("status.ready", "Готов к работе"))
        self._status_msg.setSizePolicy(QSizePolicy.Policy.Ignored, QSizePolicy.Policy.Preferred)
        self._status_bar.addWidget(self._status_msg, 1)

        self._zoom_status_lbl = QLabel("100%", self)
        self._status_bar.addPermanentWidget(self._zoom_status_lbl)

    def _create_toolbar(self):
        tb = QToolBar("MainToolbar", self)
        tb.setMovable(False)
        tb.setIconSize(QSize(16, 16))
        self.addToolBar(tb)

        # Brand Badge (galIMV style: accent dot + bold title)
        self._brand_lbl = QLabel(self)
        self._brand_lbl.setStyleSheet("background: transparent; border: none;")
        self._brand_lbl.setContentsMargins(4, 0, 8, 0)
        tb.addWidget(self._brand_lbl)

        # Primary Open Button (galIMV accent pill button)
        self._open_btn = QPushButton(" Открыть", self)
        self._open_btn.setObjectName("primaryOpenBtn")
        self._open_btn.setFixedHeight(28)
        self._open_btn.setCursor(Qt.CursorShape.PointingHandCursor)
        self._open_btn.setToolTip("Открыть изображение (Ctrl+O)")
        self._open_btn.clicked.connect(self.browse_file)
        tb.addWidget(self._open_btn)

        # Recent Files (Compact 28x28 icon button)
        self._recent_menu = QMenu(I18nManager.get_instance().tr("recent.title", "Недавние"), self)
        self._recent_btn = QToolButton(self)
        self._recent_btn.setToolTip("История открытых файлов (Ctrl+H)")
        self._recent_btn.setFixedSize(28, 28)
        self._recent_btn.setCursor(Qt.CursorShape.PointingHandCursor)
        self._recent_btn.setPopupMode(QToolButton.ToolButtonPopupMode.InstantPopup)
        self._recent_btn.setMenu(self._recent_menu)
        tb.addWidget(self._recent_btn)

        tb.addSeparator()

        # Zoom Controls (compact 28x28 icon buttons)
        self._fit_btn = QToolButton(self)
        self._fit_btn.setFixedSize(28, 28)
        self._fit_btn.setCursor(Qt.CursorShape.PointingHandCursor)
        self._fit_btn.setToolTip("Вписать в окно (0)")
        self._fit_btn.clicked.connect(self._canvas.fit_to_window)
        tb.addWidget(self._fit_btn)

        self._orig_btn = QToolButton(self)
        self._orig_btn.setFixedSize(28, 28)
        self._orig_btn.setCursor(Qt.CursorShape.PointingHandCursor)
        self._orig_btn.setToolTip("100% реальный размер (1)")
        self._orig_btn.clicked.connect(self._canvas.set_original_size)
        tb.addWidget(self._orig_btn)

        self._zoom_out_btn = QToolButton(self)
        self._zoom_out_btn.setFixedSize(28, 28)
        self._zoom_out_btn.setCursor(Qt.CursorShape.PointingHandCursor)
        self._zoom_out_btn.setToolTip("Уменьшить (-)")
        self._zoom_out_btn.clicked.connect(self._canvas.zoom_out)
        tb.addWidget(self._zoom_out_btn)

        self._zoom_in_btn = QToolButton(self)
        self._zoom_in_btn.setFixedSize(28, 28)
        self._zoom_in_btn.setCursor(Qt.CursorShape.PointingHandCursor)
        self._zoom_in_btn.setToolTip("Увеличить (+)")
        self._zoom_in_btn.clicked.connect(self._canvas.zoom_in)
        tb.addWidget(self._zoom_in_btn)

        tb.addSeparator()

        # Action Buttons
        self._copy_prompt_btn = QToolButton(self)
        self._copy_prompt_btn.setText("Промпт")
        self._copy_prompt_btn.setToolButtonStyle(Qt.ToolButtonStyle.ToolButtonTextBesideIcon)
        self._copy_prompt_btn.setFixedHeight(28)
        self._copy_prompt_btn.setCursor(Qt.CursorShape.PointingHandCursor)
        self._copy_prompt_btn.setToolTip("Скопировать промпт (Ctrl+C)")
        self._copy_prompt_btn.clicked.connect(self.copy_prompt)
        tb.addWidget(self._copy_prompt_btn)

        self._export_btn = QToolButton(self)
        self._export_btn.setText("Экспорт")
        self._export_btn.setToolButtonStyle(Qt.ToolButtonStyle.ToolButtonTextBesideIcon)
        self._export_btn.setFixedHeight(28)
        self._export_btn.setCursor(Qt.CursorShape.PointingHandCursor)
        self._export_btn.setToolTip("Экспортировать метаданные (Ctrl+E)")
        self._export_btn.clicked.connect(self.export_metadata)
        tb.addWidget(self._export_btn)

        # Right-aligned spacer
        spacer = QWidget()
        spacer.setSizePolicy(QSizePolicy.Policy.Expanding, QSizePolicy.Policy.Preferred)
        tb.addWidget(spacer)

        # Accent Palette Menu (compact 28x28)
        self._palette_btn = QToolButton(self)
        self._palette_btn.setToolTip("Цветовой акцент Lobe")
        self._palette_btn.setFixedSize(28, 28)
        self._palette_btn.setCursor(Qt.CursorShape.PointingHandCursor)
        self._palette_menu = QMenu(self)
        for name in LOBE_ACCENTS.keys():
            act = QAction(name, self)
            act.triggered.connect(lambda ch, n=name: ThemeManager.get_instance().set_accent(n))
            self._palette_menu.addAction(act)
        self._palette_btn.setMenu(self._palette_menu)
        self._palette_btn.setPopupMode(QToolButton.ToolButtonPopupMode.InstantPopup)
        tb.addWidget(self._palette_btn)

        # Dark/Light Toggle (compact 28x28)
        self._theme_btn = QToolButton(self)
        self._theme_btn.setToolTip("Переключить тему (Светлая / Тёмная)")
        self._theme_btn.setFixedSize(28, 28)
        self._theme_btn.setCursor(Qt.CursorShape.PointingHandCursor)
        self._theme_btn.clicked.connect(ThemeManager.get_instance().toggle_dark_light)
        tb.addWidget(self._theme_btn)

        # Language Selector (all 20 languages)
        self._lang_btn = QToolButton(self)
        self._lang_btn.setToolTip("Язык интерфейса (20 языков)")
        self._lang_btn.setFixedSize(28, 28)
        self._lang_btn.setCursor(Qt.CursorShape.PointingHandCursor)
        self._lang_menu = QMenu(self)
        self._lang_btn.setMenu(self._lang_menu)
        self._lang_btn.setPopupMode(QToolButton.ToolButtonPopupMode.InstantPopup)
        tb.addWidget(self._lang_btn)
        self._rebuild_lang_menu()

        # Toggle Inspector (compact 28x28)
        self._inspector_btn = QToolButton(self)
        self._inspector_btn.setToolTip("Показать/скрыть инспектор (I)")
        self._inspector_btn.setFixedSize(28, 28)
        self._inspector_btn.setCursor(Qt.CursorShape.PointingHandCursor)
        self._inspector_btn.setCheckable(True)
        self._inspector_btn.setChecked(True)
        self._inspector_btn.toggled.connect(self._on_inspector_toggled)
        tb.addWidget(self._inspector_btn)

    def _rebuild_lang_menu(self):
        self._lang_menu.clear()
        curr_loc = I18nManager.get_instance().get_locale()
        for code, name in LOCALES:
            act = QAction(name, self)
            act.setCheckable(True)
            act.setChecked(code == curr_loc)
            act.triggered.connect(lambda ch, c=code: I18nManager.get_instance().set_locale(c))
            self._lang_menu.addAction(act)

    def _on_inspector_toggled(self, checked: bool):
        self._right_container.setVisible(checked)
        c = ThemeManager.get_instance().get_colors()
        self._inspector_btn.setIcon(get_tabler_icon("layout-sidebar", c.accent if checked else c.text_secondary, 16))

    def _setup_shortcuts(self):
        open_shortcut = QAction(self)
        open_shortcut.setShortcut(QKeySequence.StandardKey.Open)
        open_shortcut.triggered.connect(self.browse_file)
        self.addAction(open_shortcut)

        copy_shortcut = QAction(self)
        copy_shortcut.setShortcut(QKeySequence("Ctrl+C"))
        copy_shortcut.triggered.connect(self.copy_prompt)
        self.addAction(copy_shortcut)

        export_shortcut = QAction(self)
        export_shortcut.setShortcut(QKeySequence("Ctrl+E"))
        export_shortcut.triggered.connect(self.export_metadata)
        self.addAction(export_shortcut)

        i_shortcut = QAction(self)
        i_shortcut.setShortcut(QKeySequence(Qt.Key.Key_I))
        i_shortcut.triggered.connect(lambda: self._inspector_btn.toggle())
        self.addAction(i_shortcut)

        f_shortcut = QAction(self)
        f_shortcut.setShortcut(QKeySequence(Qt.Key.Key_0))
        f_shortcut.triggered.connect(self._canvas.fit_to_window)
        self.addAction(f_shortcut)

        one_shortcut = QAction(self)
        one_shortcut.setShortcut(QKeySequence(Qt.Key.Key_1))
        one_shortcut.triggered.connect(self._canvas.set_original_size)
        self.addAction(one_shortcut)

        plus_shortcut = QAction(self)
        plus_shortcut.setShortcut(QKeySequence(Qt.Key.Key_Plus))
        plus_shortcut.triggered.connect(self._canvas.zoom_in)
        self.addAction(plus_shortcut)

        equal_shortcut = QAction(self)
        equal_shortcut.setShortcut(QKeySequence(Qt.Key.Key_Equal))
        equal_shortcut.triggered.connect(self._canvas.zoom_in)
        self.addAction(equal_shortcut)

        minus_shortcut = QAction(self)
        minus_shortcut.setShortcut(QKeySequence(Qt.Key.Key_Minus))
        minus_shortcut.triggered.connect(self._canvas.zoom_out)
        self.addAction(minus_shortcut)

        f11_shortcut = QAction(self)
        f11_shortcut.setShortcut(QKeySequence(Qt.Key.Key_F11))
        f11_shortcut.triggered.connect(self._toggle_fullscreen)
        self.addAction(f11_shortcut)

        esc_shortcut = QAction(self)
        esc_shortcut.setShortcut(QKeySequence(Qt.Key.Key_Escape))
        esc_shortcut.triggered.connect(self._exit_fullscreen)
        self.addAction(esc_shortcut)

    def keyPressEvent(self, event):
        if event.key() == Qt.Key.Key_Escape and self.isFullScreen():
            self._exit_fullscreen()
            event.accept()
            return
        super().keyPressEvent(event)

    def _exit_fullscreen(self):
        if self.isFullScreen():
            self._toggle_fullscreen()

    def showEvent(self, event):
        super().showEvent(event)
        if not hasattr(self, "_initial_split_done"):
            self._initial_split_done = True
            total_w = self._splitter.width()
            if total_w > 100:
                half = total_w // 2
                self._splitter.setSizes([half, half])

    def toggle_fullscreen(self):
        self._toggle_fullscreen()

    def _toggle_fullscreen(self):
        if self.isFullScreen():
            self.showNormal()
            if hasattr(self, "_status_bar"):
                self._status_bar.show()
        else:
            self.showFullScreen()
            if hasattr(self, "_status_bar"):
                self._status_bar.hide()
        QTimer.singleShot(60, self._canvas.fit_to_window)

    def update_translations(self):
        i18n = I18nManager.get_instance()
        self._open_btn.setText(" " + i18n.tr("toolbar.open", "Открыть"))
        self._open_btn.setToolTip(f"{i18n.tr('toolbar.open', 'Открыть')} (Ctrl+O)")
        self._recent_btn.setToolTip(i18n.tr("toolbar.recent", "История открытых файлов (Ctrl+H)"))
        self._fit_btn.setToolTip(f"{i18n.tr('toolbar.fit', 'Вписать в окно')} (0)")
        self._orig_btn.setToolTip(f"{i18n.tr('toolbar.real_size', '100% реальный размер')} (1)")
        self._zoom_out_btn.setToolTip(f"{i18n.tr('toolbar.zoom_out', 'Уменьшить')} (-)")
        self._zoom_in_btn.setToolTip(f"{i18n.tr('toolbar.zoom_in', 'Увеличить')} (+)")

        self._copy_prompt_btn.setText(i18n.tr("toolbar.prompt", "Промпт"))
        self._copy_prompt_btn.setToolTip(f"{i18n.tr('context.copy_prompt', 'Скопировать промпт')} (Ctrl+C)")
        self._export_btn.setText(i18n.tr("toolbar.export", "Экспорт"))
        self._export_btn.setToolTip(f"{i18n.tr('toolbar.export', 'Экспортировать метаданные')} (Ctrl+E)")

        self._palette_btn.setToolTip(i18n.tr("toolbar.palette", "Цветовой акцент Lobe"))
        self._theme_btn.setToolTip(i18n.tr("toolbar.theme", "Переключить тему (Светлая / Тёмная)"))
        self._lang_btn.setToolTip(i18n.tr("toolbar.language", "Язык интерфейса (20 языков)"))
        self._inspector_btn.setToolTip(i18n.tr("toolbar.inspector", "Показать/скрыть инспектор (I)"))

        self._tabs.setTabText(0, i18n.tr("tabs.prompt", "Промпт"))
        self._tabs.setTabText(1, i18n.tr("tabs.metadata", "Метаданные"))
        self._tabs.setTabText(2, i18n.tr("tabs.raw", "Raw"))

        self._recent_menu.setTitle(i18n.tr("recent.title", "Недавние"))
        self._rebuild_lang_menu()

        recent = self._settings.value("recentFiles", [])
        if isinstance(recent, list):
            self._update_recent_menu(recent)

        if hasattr(self, "_current_meta") and self._current_meta:
            m = self._current_meta
            filename = os.path.basename(self._current_path)
            ar_info = f" • {m.aspect_ratio_str}" if m.aspect_ratio_str else ""
            loaded_str = i18n.tr("status.loaded", "Загружено")
            self.show_status(f"{loaded_str}: {filename} • {m.width}×{m.height} px{ar_info} • {m.file_size_str}")
        else:
            self._status_msg.setText(i18n.tr("status.ready", "Готов к работе"))

    def update_theme(self):
        c = ThemeManager.get_instance().get_colors()
        QApplication.instance().setStyleSheet(ThemeManager.get_instance().get_application_stylesheet())
        self._apply_accent_icon(c.accent_name)
        
        # Brand indicator (galIMV minimalist typography with accent dot)
        self._brand_lbl.setText(
            f"<span style='color: {c.accent}; font-size: 13px;'>●</span> "
            f"<span style='font-weight: 700; font-size: 13px; color: {c.text_primary};'>galIMV</span> "
            f"<span style='font-size: 10px; font-weight: 600; color: {c.text_muted}; text-transform: uppercase;'>mini</span>"
        )

        # Tabler vector icons strictly matching functions
        icon_color = c.text_secondary
        self._open_btn.setIcon(get_tabler_icon("photo", "#ffffff", 15))
        self._recent_btn.setIcon(get_tabler_icon("history", icon_color, 16))
        self._fit_btn.setIcon(get_tabler_icon("arrows-maximize", icon_color, 16))
        self._orig_btn.setIcon(get_tabler_icon("aspect-ratio", icon_color, 16))
        self._zoom_out_btn.setIcon(get_tabler_icon("zoom-out", icon_color, 16))
        self._zoom_in_btn.setIcon(get_tabler_icon("zoom-in", icon_color, 16))
        self._copy_prompt_btn.setIcon(get_tabler_icon("copy", icon_color, 15))
        self._export_btn.setIcon(get_tabler_icon("download", icon_color, 15))
        self._palette_btn.setIcon(get_tabler_icon("palette", icon_color, 16))
        self._theme_btn.setIcon(get_tabler_icon("sun" if c.is_dark else "moon", icon_color, 16))
        self._lang_btn.setIcon(get_tabler_icon("world", icon_color, 16))
        self._inspector_btn.setIcon(get_tabler_icon("layout-sidebar", c.accent if self._inspector_btn.isChecked() else icon_color, 16))

        # Set tab icons: sparkles, table, code
        self._tabs.setTabIcon(0, get_tabler_icon("sparkles", c.accent if self._tabs.currentIndex() == 0 else icon_color, 14))
        self._tabs.setTabIcon(1, get_tabler_icon("table", c.accent if self._tabs.currentIndex() == 1 else icon_color, 14))
        self._tabs.setTabIcon(2, get_tabler_icon("code", c.accent if self._tabs.currentIndex() == 2 else icon_color, 14))

        if hasattr(self, "_zoom_status_lbl"):
            self._zoom_status_lbl.setStyleSheet(f"""
                QLabel {{
                    color: {c.text_secondary};
                    font-weight: 600;
                    font-size: 11px;
                    padding: 1px 6px;
                }}
            """)

    def _apply_accent_icon(self, accent_name: str):
        """Keep the application/window icon in sync with the selected Lobe accent."""
        icon_files = {
            "Lobe Blue": "simple-blue.ico",
            "Lobe Purple": "simple-purple.ico",
            "Lobe Magenta": "simple-magenta.ico",
            "Lobe Cyan": "simple-cyan.ico",
            "Lobe Green": "simple-green.ico",
            "Lobe Orange": "simple-orange.ico",
            "Monochrome Zinc": "simple-zinc.ico",
        }
        resources = os.path.abspath(os.path.join(os.path.dirname(__file__), "..", "resources"))
        fallback = os.path.join(resources, "app.ico")
        variant = icon_files.get(accent_name)
        candidate = os.path.join(resources, "lobe-variants", variant) if variant else ""
        icon_path = candidate if candidate and os.path.exists(candidate) else fallback
        icon = QIcon(icon_path)
        if icon.isNull():
            icon = QIcon(fallback)
        self.setWindowIcon(icon)
        app = QApplication.instance()
        if app is not None:
            app.setWindowIcon(icon)

    def load_image(self, file_path: str):
        i18n = I18nManager.get_instance()
        if not file_path or not os.path.exists(file_path):
            self.show_status(i18n.tr("status.file_not_found", "Файл не найден"))
            return

        self._current_path = os.path.abspath(file_path)
        
        # Load pixmap
        from PyQt6.QtGui import QPixmap
        pixmap = QPixmap(self._current_path)
        if pixmap.isNull():
            err_title = i18n.tr("status.load_error", "Ошибка загрузки")
            self.show_status(f"{err_title}: {os.path.basename(file_path)}")
            return

        self._canvas.set_pixmap(pixmap)

        # Read metadata
        self._current_meta = MetadataReader.read_metadata(self._current_path)

        # Update Inspector tabs
        self._prompt_card.set_metadata(self._current_meta)
        self._meta_table.set_metadata(self._current_meta)
        self._raw_view.set_metadata(self._current_meta)

        filename = os.path.basename(self._current_path)
        m = self._current_meta
        ar_disp = f", {m.aspect_ratio_str}" if m.aspect_ratio_str else ""
        self.setWindowTitle(f"{filename} ({m.width}×{m.height}{ar_disp}) - galIMVmini")

        # Update Recent Files
        self._add_recent_file(self._current_path)

        ar_info = f" • {m.aspect_ratio_str}" if m.aspect_ratio_str else ""
        loaded_str = i18n.tr("status.loaded", "Загружено")
        self.show_status(f"{loaded_str}: {filename} • {m.width}×{m.height} px{ar_info} • {m.file_size_str}")

    def browse_file(self):
        i18n = I18nManager.get_instance()
        start_dir = os.path.dirname(self._current_path) if self._current_path else ""
        dlg_title = i18n.tr("dialog.open_image", "Выберите изображение")
        file_path, _ = QFileDialog.getOpenFileName(
            self, dlg_title, start_dir,
            "Изображения (*.png *.jpg *.jpeg *.webp *.gif *.bmp *.tiff);;Все файлы (*.*)"
        )
        if file_path:
            self.load_image(file_path)

    def copy_prompt(self):
        i18n = I18nManager.get_instance()
        if self._current_meta and self._current_meta.prompt:
            pyperclip.copy(self._current_meta.prompt)
            self.show_status(i18n.tr("status.prompt_copied", "Промпт скопирован в буфер обмена"))
        else:
            self.show_status(i18n.tr("status.no_prompt", "Промпт отсутствует"))

    def save_sidecar(self):
        i18n = I18nManager.get_instance()
        if not self._current_meta or not self._current_meta.prompt:
            self.show_status(i18n.tr("status.no_prompt_save", "Нет промпта для сохранения"))
            return

        base, _ = os.path.splitext(self._current_path)
        txt_path = base + ".txt"
        try:
            with open(txt_path, "w", encoding="utf-8") as f:
                f.write(self._current_meta.prompt)
            self._current_meta.sidecar_path = txt_path
            self._current_meta.sidecar_text = self._current_meta.prompt
            self._prompt_card.set_metadata(self._current_meta)
            saved_str = i18n.tr("status.sidecar_saved", "Sidecar сохранен")
            self.show_status(f"{saved_str}: {os.path.basename(txt_path)}")
        except Exception as e:
            err_str = i18n.tr("status.sidecar_error", "Ошибка сохранения sidecar")
            self.show_status(f"{err_str}: {e}")

    def export_metadata(self):
        i18n = I18nManager.get_instance()
        if not self._current_meta:
            self.show_status(i18n.tr("status.no_meta_export", "Нет метаданных для экспорта"))
            return

        base_name = os.path.splitext(os.path.basename(self._current_path))[0]
        dlg_title = i18n.tr("dialog.export_meta", "Экспорт метаданных")
        file_dialog = QFileDialog(self, dlg_title, f"{base_name}_meta.txt")
        file_dialog.setAcceptMode(QFileDialog.AcceptMode.AcceptSave)
        file_dialog.setNameFilter(
            "Текстовый файл (*.txt);;Формат Markdown (*.md);;JSON (*.json);;Таблица CSV (*.csv)"
        )

        if file_dialog.exec():
            selected = file_dialog.selectedFiles()
            if not selected:
                return
            out_path = selected[0]
            ext = os.path.splitext(out_path)[1].lower()
            m = self._current_meta

            try:
                if ext in (".txt", ""):
                    with open(out_path, "w", encoding="utf-8") as f:
                        f.write(f"Метаданные изображения: {m.file_name}\n")
                        f.write(f"Путь: {m.file_path}\n\n")
                        if m.prompt:
                            f.write(f"=== Промпт ===\n{m.prompt}\n\n")
                        if m.negative_prompt:
                            f.write(f"=== Негативный промпт ===\n{m.negative_prompt}\n\n")
                        for cat, items in m.categories.items():
                            f.write(f"\n=== {cat} ===\n")
                            for k, v in items.items():
                                f.write(f"{k}: {v}\n")

                elif ext == ".md":
                    with open(out_path, "w", encoding="utf-8") as f:
                        f.write(f"# Метаданные: `{m.file_name}`\n\n")
                        if m.prompt:
                            f.write(f"### Prompt\n```text\n{m.prompt}\n```\n\n")
                        if m.negative_prompt:
                            f.write(f"### Negative Prompt\n```text\n{m.negative_prompt}\n```\n\n")
                        for cat, items in m.categories.items():
                            f.write(f"### {cat}\n\n| Свойство | Значение |\n|---|---|\n")
                            for k, v in items.items():
                                f.write(f"| {k} | {v} |\n")
                            f.write("\n")

                elif ext == ".json":
                    export_dict = {
                        "file": m.file_name,
                        "path": m.file_path,
                        "prompt": m.prompt,
                        "negative_prompt": m.negative_prompt,
                        "parameters": m.generation_params,
                        "categories": m.categories,
                        "raw_texts": m.raw_texts
                    }
                    with open(out_path, "w", encoding="utf-8") as f:
                        json.dump(export_dict, f, indent=2, ensure_ascii=False)

                elif ext == ".csv":
                    with open(out_path, "w", newline="", encoding="utf-8") as f:
                        writer = csv.writer(f)
                        writer.writerow(["Категория", "Свойство", "Значение"])
                        for cat, items in m.categories.items():
                            for k, v in items.items():
                                writer.writerow([cat, k, v])

                done_str = i18n.tr("status.export_done", "Экспортировано")
                self.show_status(f"{done_str}: {os.path.basename(out_path)}")
            except Exception as e:
                err_str = i18n.tr("status.export_error", "Ошибка экспорта")
                self.show_status(f"{err_str}: {e}")

    def reveal_in_explorer(self):
        if self._current_path and os.path.exists(self._current_path):
            folder = os.path.dirname(self._current_path)
            QDesktopServices.openUrl(QUrl.fromLocalFile(folder))
            self.show_status(f"Folder: {folder}")

    def _on_zoom_changed(self, factor: float):
        if hasattr(self, "_zoom_status_lbl"):
            self._zoom_status_lbl.setText(f"{int(round(factor * 100))}%")

    def show_status(self, text: str, timeout: int = 4000):
        self._status_msg.setText(text)
        if timeout > 0:
            ready_str = I18nManager.get_instance().tr("status.ready", "Готов к работе")
            QTimer.singleShot(timeout, lambda: self._status_msg.setText(ready_str))

    def _load_settings(self):
        geom = self._settings.value("geometry")
        if geom:
            self.restoreGeometry(geom)
        recent = self._settings.value("recentFiles", [])
        if isinstance(recent, list):
            self._update_recent_menu(recent)

    def _add_recent_file(self, path: str):
        recent = self._settings.value("recentFiles", [])
        if not isinstance(recent, list):
            recent = []
        if path in recent:
            recent.remove(path)
        recent.insert(0, path)
        recent = recent[:15]
        self._settings.setValue("recentFiles", recent)
        self._update_recent_menu(recent)

    def _update_recent_menu(self, recent_files: List[str]):
        i18n = I18nManager.get_instance()
        self._recent_menu.clear()
        if not recent_files:
            act = self._recent_menu.addAction(i18n.tr("recent.empty", "Нет недавних файлов"))
            act.setEnabled(False)
            return

        for p in recent_files:
            if os.path.exists(p):
                act = self._recent_menu.addAction(os.path.basename(p))
                act.setIcon(get_tabler_icon("photo", "#a1a1aa", 14))
                act.setToolTip(p)
                act.triggered.connect(lambda ch, path=p: self.load_image(path))

        self._recent_menu.addSeparator()
        clear_act = self._recent_menu.addAction(i18n.tr("recent.clear", "Очистить историю"))
        clear_act.setIcon(get_tabler_icon("trash", "#f43f5e", 14))
        clear_act.triggered.connect(self._clear_recent)

    def _clear_recent(self):
        self._settings.setValue("recentFiles", [])
        self._update_recent_menu([])
        i18n = I18nManager.get_instance()
        self.show_status(i18n.tr("recent.cleared", "История очищена"))

    def closeEvent(self, event):
        self._settings.setValue("geometry", self.saveGeometry())
        super().closeEvent(event)
