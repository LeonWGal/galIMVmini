"""
galIMVmini Prompt Inspector.
Faithful implementation of galIMV's Lobe Neo design:
- Positive prompt and Negative prompt placed sequentially
- Pure Tabler vector icons strictly matching features (sparkles, circle-minus, adjustments, cpu, layers, file-text)
- Ultra-compact generation parameters grid
- Completely hidden sidecar card when no .txt exists
- Deep obsidian card surfaces (#1a1a23) and input areas (#101015)
- Responsive down to narrow viewports without clipping
"""

from typing import List, Tuple, Optional, Dict
import pyperclip

from PyQt6.QtWidgets import (
    QWidget, QVBoxLayout, QHBoxLayout, QLabel, QTextEdit,
    QPushButton, QFrame, QScrollArea, QGridLayout, QSizePolicy,
    QToolButton
)
from PyQt6.QtCore import Qt, pyqtSignal, QTimer, QSize
from PyQt6.QtGui import QCursor

try:
    from core.theme import ThemeManager
    from core.metadata import ImageMetadata
    from core.icons import get_tabler_icon
    from core.i18n import I18nManager
except ImportError:
    from galIMVmini.core.theme import ThemeManager
    from galIMVmini.core.metadata import ImageMetadata
    from galIMVmini.core.icons import get_tabler_icon
    from galIMVmini.core.i18n import I18nManager


class CopyIconButton(QToolButton):
    def __init__(self, tooltip: str = "", parent=None):
        super().__init__(parent)
        self.setFixedSize(22, 22)
        self.setCursor(QCursor(Qt.CursorShape.PointingHandCursor))
        self._custom_tooltip = tooltip
        self.update_style()
        ThemeManager.get_instance().add_listener(self.update_style)

    def update_style(self):
        c = ThemeManager.get_instance().get_colors()
        self.setIcon(get_tabler_icon("copy", c.text_secondary, 12))
        self.setIconSize(QSize(12, 12))
        tip = self._custom_tooltip or I18nManager.get_instance().tr("common.copy", "Копировать")
        self.setToolTip(tip)
        self.setStyleSheet(f"""
            QToolButton {{
                background-color: {c.bg_card};
                border: 1px solid {c.border_subtle};
                border-radius: 4px;
                padding: 0px;
            }}
            QToolButton:hover {{
                background-color: {c.bg_elevated};
                border-color: {c.accent};
            }}
        """)

    def flash_copied(self):
        self.setIcon(get_tabler_icon("check", "#10b981", 12))
        self.setToolTip(I18nManager.get_instance().tr("common.copied", "Скопировано!"))
        tip = self._custom_tooltip or I18nManager.get_instance().tr("common.copy", "Копировать")
        QTimer.singleShot(1400, lambda: (
            self.update_style(),
            self.setToolTip(tip)
        ))


class ElidedLabel(QLabel):
    def __init__(self, text: str = "", parent=None):
        super().__init__(text, parent)
        self._full_text = text
        self._last_w = -1
        self.setSizePolicy(QSizePolicy.Policy.Expanding, QSizePolicy.Policy.Preferred)
        self.setMinimumWidth(20)

    def setText(self, text: str):
        self._full_text = text
        self._last_w = -1
        self._update_elided()

    def text(self) -> str:
        return self._full_text

    def minimumSizeHint(self) -> QSize:
        return QSize(20, max(13, self.fontMetrics().height()))

    def sizeHint(self) -> QSize:
        fm = self.fontMetrics()
        return QSize(min(140, fm.horizontalAdvance(self._full_text) + 4), fm.height())

    def resizeEvent(self, event):
        super().resizeEvent(event)
        if self.width() != self._last_w:
            self._last_w = self.width()
            self._update_elided()

    def _update_elided(self):
        fm = self.fontMetrics()
        avail_w = max(10, self.width() - 2)
        elided = fm.elidedText(self._full_text, Qt.TextElideMode.ElideRight, avail_w)
        super().setText(elided)


class ParamBadge(QFrame):
    copied = pyqtSignal(str)

    def __init__(self, key: str, value: str, is_copyable: bool = False, parent=None):
        super().__init__(parent)
        self.key = key
        self.value = value
        self.is_copyable = is_copyable
        self.setFixedHeight(22)
        self.setFrameShape(QFrame.Shape.NoFrame)
        self.setSizePolicy(QSizePolicy.Policy.Expanding, QSizePolicy.Policy.Fixed)

        layout = QHBoxLayout(self)
        layout.setContentsMargins(6, 1, 6, 1)
        layout.setSpacing(5)

        c = ThemeManager.get_instance().get_colors()

        self._key_lbl = QLabel(key.upper(), self)
        self._key_lbl.setSizePolicy(QSizePolicy.Policy.Fixed, QSizePolicy.Policy.Preferred)
        layout.addWidget(self._key_lbl)

        # Compact elided value label
        self._val_lbl = ElidedLabel(value, self)
        self._val_lbl.setTextInteractionFlags(Qt.TextInteractionFlag.TextSelectableByMouse)
        layout.addWidget(self._val_lbl, 1)

        self.setToolTip(f"{key}: {value}" + ("\n(Кликните, чтобы скопировать)" if is_copyable else ""))
        if is_copyable:
            self.setCursor(QCursor(Qt.CursorShape.PointingHandCursor))

        self.update_style()
        ThemeManager.get_instance().add_listener(self.update_style)

    def update_style(self):
        c = ThemeManager.get_instance().get_colors()
        self._key_lbl.setStyleSheet(f"color: {c.text_muted}; font-size: 9px; font-weight: 700; letter-spacing: 0.4px; background: transparent; border: none;")
        self._val_lbl.setStyleSheet(f"color: {c.text_primary}; font-size: 10.5px; font-weight: 600; background: transparent; border: none;")
        
        self.setStyleSheet(f"""
            ParamBadge {{
                background-color: {c.bg_input};
                border: 1px solid {c.border_subtle};
                border-radius: 4px;
            }}
            ParamBadge:hover {{
                border-color: {c.accent if self.is_copyable else c.border_subtle};
                background-color: {c.accent_subtle if self.is_copyable else c.bg_elevated};
            }}
        """)

    def mousePressEvent(self, event):
        if self.is_copyable and event.button() == Qt.MouseButton.LeftButton:
            pyperclip.copy(self.value)
            self.copied.emit(f"{self.key}: {self.value}")
        super().mousePressEvent(event)


class PromptCardView(QWidget):
    status_requested = pyqtSignal(str)
    save_sidecar_requested = pyqtSignal()

    def __init__(self, parent=None):
        super().__init__(parent)
        self._meta: Optional[ImageMetadata] = None
        self._card_titles: List[QLabel] = []
        self._card_title_keys: List[Tuple[QLabel, str]] = []
        self._card_icons: List[Tuple[QLabel, str]] = []
        self._card_badges: List[QLabel] = []

        main_layout = QVBoxLayout(self)
        main_layout.setContentsMargins(0, 0, 0, 0)

        # Scroll Area for the whole card stack
        scroll = QScrollArea(self)
        scroll.setWidgetResizable(True)
        scroll.setFrameShape(QFrame.Shape.NoFrame)
        scroll.setHorizontalScrollBarPolicy(Qt.ScrollBarPolicy.ScrollBarAlwaysOff)
        scroll.setStyleSheet("background: transparent; border: none;")
        scroll.viewport().setStyleSheet("background: transparent;")

        self._container = QWidget()
        self._container.setStyleSheet("background: transparent;")
        self._layout = QVBoxLayout(self._container)
        self._layout.setContentsMargins(8, 6, 8, 8)
        self._layout.setSpacing(6)
        scroll.setWidget(self._container)

        main_layout.addWidget(scroll)

        # Build Card Sections in sequence:
        self._create_prompt_section()
        self._create_neg_prompt_section()
        self._create_params_section()
        self._create_extra_params_section()
        self._create_lora_section()
        self._create_sidecar_section()
        self._layout.addStretch(1)

        self.update_theme()
        ThemeManager.get_instance().add_listener(self.update_theme)
        I18nManager.get_instance().add_listener(self.update_translations)

    def update_theme(self):
        c = ThemeManager.get_instance().get_colors()
        for frame in (self._prompt_frame, self._neg_frame,
                      self._params_frame, self._extra_params_frame,
                      self._lora_frame, self._sidecar_frame):
            frame.setStyleSheet(f"""
                QFrame#cardFrame {{
                    background-color: {c.bg_card};
                    border: 1px solid {c.border_subtle};
                    border-radius: 6px;
                }}
            """)

        text_edit_style = f"""
            QTextEdit {{
                background-color: {c.bg_input};
                color: {c.text_primary};
                border: 1px solid {c.border_subtle};
                border-radius: 5px;
                padding: 4px 6px;
                font-size: 11.5px;
                line-height: 1.35;
            }}
            QTextEdit:focus {{
                border-color: {c.accent};
            }}
        """
        self._prompt_edit.setStyleSheet(text_edit_style)
        self._neg_edit.setStyleSheet(text_edit_style)
        self._sidecar_edit.setStyleSheet(text_edit_style)

        # Update all card header titles, icons, and badges
        for title_lbl in self._card_titles:
            title_lbl.setStyleSheet(f"font-size: 11.5px; font-weight: 600; color: {c.text_primary}; background: transparent; border: none;")
        for icon_lbl, icon_name in self._card_icons:
            icon_lbl.setPixmap(get_tabler_icon(icon_name, c.accent, 13).pixmap(13, 13))
        for badge_lbl in self._card_badges:
            badge_lbl.setStyleSheet(f"font-size: 9.5px; color: {c.text_muted}; padding: 1px 4px; "
                                    f"background: {c.bg_elevated}; border: 1px solid {c.border_subtle}; border-radius: 3px;")

        # Refresh parameter widgets if metadata is loaded
        if self._meta:
            self.set_metadata(self._meta)

    def update_translations(self):
        i18n = I18nManager.get_instance()
        for title_lbl, key in self._card_title_keys:
            if key:
                title_lbl.setText(i18n.tr(key, title_lbl.text()))
        if self._meta:
            self.set_metadata(self._meta)

    def _create_card_frame(self, title: str, icon_name: str = "sparkles", copy_action=None, i18n_key: str = "") -> Tuple[QFrame, QVBoxLayout, QLabel]:
        c = ThemeManager.get_instance().get_colors()
        frame = QFrame(self._container)
        frame.setObjectName("cardFrame")
        frame.setFrameShape(QFrame.Shape.NoFrame)
        frame.setSizePolicy(QSizePolicy.Policy.Expanding, QSizePolicy.Policy.Maximum)
        frame.setMinimumWidth(0)
        layout = QVBoxLayout(frame)
        layout.setContentsMargins(7, 5, 7, 5)
        layout.setSpacing(4)

        # Header
        hdr = QHBoxLayout()
        hdr.setContentsMargins(0, 0, 0, 0)
        hdr.setSpacing(5)

        # Function-accurate Tabler Icon
        icon_lbl = QLabel(frame)
        icon_lbl.setPixmap(get_tabler_icon(icon_name, c.accent, 13).pixmap(13, 13))
        icon_lbl.setStyleSheet("background: transparent; border: none;")
        hdr.addWidget(icon_lbl)

        disp_title = I18nManager.get_instance().tr(i18n_key, title) if i18n_key else title
        title_lbl = QLabel(disp_title, frame)
        title_lbl.setStyleSheet(f"font-size: 11.5px; font-weight: 600; color: {c.text_primary}; background: transparent; border: none;")
        hdr.addWidget(title_lbl)

        count_badge = QLabel("", frame)
        count_badge.setStyleSheet(f"font-size: 9.5px; color: {c.text_muted}; padding: 1px 4px; "
                                  f"background: {c.bg_elevated}; border: 1px solid {c.border_subtle}; border-radius: 3px;")
        count_badge.setVisible(False)
        hdr.addWidget(count_badge)
        hdr.addStretch()

        self._card_titles.append(title_lbl)
        self._card_title_keys.append((title_lbl, i18n_key))
        self._card_icons.append((icon_lbl, icon_name))
        self._card_badges.append(count_badge)

        if copy_action:
            copy_prefix = I18nManager.get_instance().tr("common.copy", "Копировать")
            btn = CopyIconButton(f"{copy_prefix} ({disp_title})", frame)
            btn.clicked.connect(lambda: (copy_action(), btn.flash_copied()))
            hdr.addWidget(btn)

        layout.addLayout(hdr)
        self._layout.addWidget(frame)
        return frame, layout, count_badge

    def _adjust_text_edit_height(self, edit: QTextEdit, min_h: int = 26, max_h: int = 220):
        doc = edit.document()
        avail_w = max(50, edit.viewport().width() if edit.viewport() else edit.width() - 14)
        doc.setTextWidth(avail_w)
        h = int(doc.documentLayout().documentSize().height()) + 8
        edit.setFixedHeight(max(min_h, min(max_h, h)))

    def resizeEvent(self, event):
        super().resizeEvent(event)
        if hasattr(self, "_meta") and self._meta:
            if self._meta.prompt:
                self._adjust_text_edit_height(self._prompt_edit, 28, 240)
            if self._meta.negative_prompt:
                self._adjust_text_edit_height(self._neg_edit, 26, 160)
            if self._meta.sidecar_text:
                self._adjust_text_edit_height(self._sidecar_edit, 26, 160)

    def _create_prompt_section(self):
        # Icon: sparkles for creative AI generation prompt
        self._prompt_frame, layout, self._prompt_badge = self._create_card_frame(
            "Промпт",
            icon_name="sparkles",
            copy_action=lambda: self._copy_text(self._prompt_edit.toPlainText(), "Промпт"),
            i18n_key="prompt.positive"
        )
        self._prompt_edit = QTextEdit(self._prompt_frame)
        self._prompt_edit.setReadOnly(True)
        self._prompt_edit.document().setDocumentMargin(3)
        self._prompt_edit.setFixedHeight(28)
        self._prompt_edit.setLineWrapMode(QTextEdit.LineWrapMode.WidgetWidth)
        self._prompt_edit.setFrameShape(QFrame.Shape.NoFrame)
        layout.addWidget(self._prompt_edit)

    def _create_neg_prompt_section(self):
        # Icon: circle-minus for negative prompt exclusion
        self._neg_frame, layout, self._neg_badge = self._create_card_frame(
            "Негативный промпт",
            icon_name="circle-minus",
            copy_action=lambda: self._copy_text(self._neg_edit.toPlainText(), "Негативный промпт"),
            i18n_key="prompt.negative"
        )
        self._neg_edit = QTextEdit(self._neg_frame)
        self._neg_edit.setReadOnly(True)
        self._neg_edit.document().setDocumentMargin(3)
        self._neg_edit.setFixedHeight(26)
        self._neg_edit.setLineWrapMode(QTextEdit.LineWrapMode.WidgetWidth)
        self._neg_edit.setFrameShape(QFrame.Shape.NoFrame)
        layout.addWidget(self._neg_edit)

    def _create_params_section(self):
        # Icon: adjustments for settings & parameters
        self._params_frame, layout, _ = self._create_card_frame("Параметры", icon_name="adjustments", i18n_key="prompt.params")
        self._params_grid = QGridLayout()
        self._params_grid.setSpacing(4)
        layout.addLayout(self._params_grid)

    def _create_extra_params_section(self):
        # Icon: cpu for extra model engine parameters (ADetailer, TIPO)
        self._extra_params_frame, layout, self._extra_badge = self._create_card_frame("Дополнительно", icon_name="cpu", i18n_key="prompt.extra")
        self._extra_container = QWidget(self._extra_params_frame)
        self._extra_container.setStyleSheet("background: transparent;")
        self._extra_layout = QVBoxLayout(self._extra_container)
        self._extra_layout.setContentsMargins(0, 2, 0, 2)
        self._extra_layout.setSpacing(4)
        layout.addWidget(self._extra_container)
        self._extra_params_frame.setVisible(False)

    def _create_lora_section(self):
        # Icon: layers for LoRA fine-tuning weights
        self._lora_frame, self._lora_layout, _ = self._create_card_frame("LoRA", icon_name="layers", i18n_key="prompt.lora")
        self._lora_frame.setVisible(False)

    def _create_sidecar_section(self):
        # Icon: file-text for textual sidecar document
        self._sidecar_frame, layout, _ = self._create_card_frame(
            "Sidecar (.txt)",
            icon_name="file-text",
            copy_action=lambda: self._copy_text(self._sidecar_edit.toPlainText(), "Sidecar"),
            i18n_key="prompt.sidecar"
        )
        self._sidecar_edit = QTextEdit(self._sidecar_frame)
        self._sidecar_edit.setReadOnly(True)
        self._sidecar_edit.document().setDocumentMargin(3)
        self._sidecar_edit.setFixedHeight(28)
        self._sidecar_edit.setLineWrapMode(QTextEdit.LineWrapMode.WidgetWidth)
        self._sidecar_edit.setFrameShape(QFrame.Shape.NoFrame)
        layout.addWidget(self._sidecar_edit)
        self._sidecar_frame.setVisible(False)

    def set_metadata(self, meta: ImageMetadata):
        self._meta = meta
        i18n = I18nManager.get_instance()
        words_unit = i18n.tr("prompt.words", "слов")

        # 1. Prompt (Positive)
        prompt_text = meta.prompt.strip() if meta.prompt else ""
        self._prompt_edit.setPlainText(prompt_text or "Нет данных промпта")
        self._prompt_frame.setVisible(bool(prompt_text) or meta.has_ai_metadata)
        if prompt_text:
            word_count = len(prompt_text.split())
            self._prompt_badge.setText(f"{word_count} {words_unit}")
            self._prompt_badge.setVisible(True)
            self._adjust_text_edit_height(self._prompt_edit, 28, 240)
        else:
            self._prompt_badge.setVisible(False)
            self._prompt_edit.setFixedHeight(26)

        # 2. Negative Prompt (placed right under positive prompt)
        neg_text = meta.negative_prompt.strip() if meta.negative_prompt else ""
        self._neg_edit.setPlainText(neg_text or "")
        self._neg_frame.setVisible(bool(neg_text))
        if neg_text:
            self._neg_badge.setText(f"{len(neg_text.split())} {words_unit}")
            self._neg_badge.setVisible(True)
            self._adjust_text_edit_height(self._neg_edit, 26, 160)
        else:
            self._neg_badge.setVisible(False)
            self._neg_edit.setFixedHeight(26)

        # 3. Compact Core Parameters Grid
        while self._params_grid.count():
            it = self._params_grid.takeAt(0)
            if it and it.widget():
                it.widget().setParent(None)
                it.widget().deleteLater()

        core_badges = []
        if meta.model_name:
            core_badges.append((i18n.tr("param.model", "Model"), meta.model_name, True))
        if meta.seed:
            core_badges.append((i18n.tr("param.seed", "Seed"), meta.seed, True))

        # Sampler + Schedule
        sampler_str = meta.sampler
        schedule_type = meta.generation_params.get("Schedule type", "")
        if schedule_type and schedule_type.lower() not in sampler_str.lower():
            sampler_str = f"{sampler_str} {schedule_type}".strip()
        if sampler_str:
            core_badges.append((i18n.tr("param.sampler", "Sampler"), sampler_str, False))

        if meta.steps:
            core_badges.append((i18n.tr("param.steps", "Steps"), meta.steps, False))
        if meta.cfg_scale:
            core_badges.append((i18n.tr("param.cfg", "CFG"), meta.cfg_scale, False))
        if meta.width and meta.height:
            core_badges.append((i18n.tr("param.size", "Size"), f"{meta.width} × {meta.height}", False))
        if meta.aspect_ratio_str:
            aspect_lbl = i18n.tr("param.aspect", "Aspect")
            core_badges.append((aspect_lbl, meta.aspect_ratio_str, True))
        if meta.clip_skip:
            core_badges.append((i18n.tr("param.clip_skip", "Clip Skip"), meta.clip_skip, False))
        if meta.denoise:
            core_badges.append((i18n.tr("param.denoise", "Denoise"), meta.denoise, False))
        if meta.model_hash:
            core_badges.append((i18n.tr("param.model_hash", "Model Hash"), meta.model_hash, True))

        copied_prefix = i18n.tr("status.copied", "Скопировано")
        row, col = 0, 0
        for key, val, copyable in core_badges:
            b = ParamBadge(key, val, is_copyable=copyable, parent=self._params_frame)
            b.copied.connect(lambda msg, cp=copied_prefix: self.status_requested.emit(f"{cp}: {msg}"))
            self._params_grid.addWidget(b, row, col)
            col += 1
            if col >= 2:
                col = 0
                row += 1

        self._params_frame.setVisible(bool(core_badges))

        # 4. Extra / Secondary Parameters (Structured TIPO, ADetailer, and Other)
        while self._extra_layout.count():
            it = self._extra_layout.takeAt(0)
            if it:
                if it.widget():
                    it.widget().setParent(None)
                    it.widget().deleteLater()
                elif it.layout():
                    while it.layout().count():
                        sub = it.layout().takeAt(0)
                        if sub and sub.widget():
                            sub.widget().setParent(None)
                            sub.widget().deleteLater()

        c = ThemeManager.get_instance().get_colors()
        has_extras = False

        # Structured TIPO
        tipo_data = meta.parsed_extensions.get("TIPO", {})
        if tipo_data:
            has_extras = True
            t_lbl = QLabel("TIPO PROMPT OPTIMIZER", self._extra_container)
            t_lbl.setStyleSheet(f"font-size: 9.5px; font-weight: 700; color: {c.accent}; letter-spacing: 0.5px; padding-top: 2px;")
            self._extra_layout.addWidget(t_lbl)

            t_grid = QGridLayout()
            t_grid.setSpacing(4)
            tr, tc = 0, 0
            for tk, tv in tipo_data.items():
                if tv:
                    b = ParamBadge(f"TIPO {tk}", str(tv), is_copyable=True, parent=self._extra_container)
                    b.copied.connect(lambda msg, cp=copied_prefix: self.status_requested.emit(f"{cp}: {msg}"))
                    t_grid.addWidget(b, tr, tc)
                    tc += 1
                    if tc >= 2:
                        tc = 0
                        tr += 1
            self._extra_layout.addLayout(t_grid)

        # ADetailer parameters
        ad_items = [(k, v) for k, v in meta.generation_params.items() if "adetailer" in k.lower()]
        if ad_items:
            has_extras = True
            ad_lbl = QLabel("ADETAILER", self._extra_container)
            ad_lbl.setStyleSheet(f"font-size: 9.5px; font-weight: 700; color: {c.accent}; letter-spacing: 0.5px; padding-top: 4px;")
            self._extra_layout.addWidget(ad_lbl)

            ad_grid = QGridLayout()
            ad_grid.setSpacing(4)
            ar, ac = 0, 0
            for ak, av in ad_items:
                disp_k = ak.replace("ADetailer", "").strip() or ak
                b = ParamBadge(disp_k, str(av), is_copyable=True, parent=self._extra_container)
                b.copied.connect(lambda msg, cp=copied_prefix: self.status_requested.emit(f"{cp}: {msg}"))
                ad_grid.addWidget(b, ar, ac)
                ac += 1
                if ac >= 2:
                    ac = 0
                    ar += 1
            self._extra_layout.addLayout(ad_grid)

        # Other parameters
        excluded_keys = {
            "model", "seed", "sampler", "steps", "cfg scale", "cfg", "size", "denoising strength",
            "denoise", "clip skip", "model hash", "schedule type", "system", "tipo parameters"
        }
        remaining_items = []
        for k, v in meta.generation_params.items():
            k_low = k.lower()
            if k_low not in excluded_keys and "adetailer" not in k_low and "tipo" not in k_low:
                remaining_items.append((k, str(v).strip()))

        if remaining_items:
            has_extras = True
            rem_title = i18n.tr("prompt.other_params", "Прочие параметры").upper()
            rem_lbl = QLabel(rem_title, self._extra_container)
            rem_lbl.setStyleSheet(f"font-size: 9.5px; font-weight: 700; color: {c.text_muted}; letter-spacing: 0.5px; padding-top: 4px;")
            self._extra_layout.addWidget(rem_lbl)

            rem_grid = QGridLayout()
            rem_grid.setSpacing(4)
            rr, rc = 0, 0
            for rk, rv in remaining_items:
                b = ParamBadge(rk, rv, is_copyable=True, parent=self._extra_container)
                b.copied.connect(lambda msg, cp=copied_prefix: self.status_requested.emit(f"{cp}: {msg}"))
                rem_grid.addWidget(b, rr, rc)
                rc += 1
                if rc >= 2:
                    rc = 0
                    rr += 1
            self._extra_layout.addLayout(rem_grid)

        if has_extras:
            self._extra_params_frame.setVisible(True)
            total_extra_count = len(tipo_data) + len(ad_items) + len(remaining_items)
            param_unit = i18n.tr("prompt.params_count", "параметров")
            self._extra_badge.setText(f"{total_extra_count} {param_unit}")
            self._extra_badge.setVisible(True)
        else:
            self._extra_params_frame.setVisible(False)

        # 5. LoRA Section
        while self._lora_layout.count() > 1:
            it = self._lora_layout.takeAt(1)
            if it and it.widget():
                it.widget().setParent(None)
                it.widget().deleteLater()

        if meta.loras:
            self._lora_frame.setVisible(True)
            weight_unit = i18n.tr("prompt.weight", "вес")
            for lora_name, lora_w in meta.loras:
                b = ParamBadge(f"LoRA: {lora_name}", f"{weight_unit} {lora_w}", is_copyable=True, parent=self._lora_frame)
                b.copied.connect(lambda msg, cp=copied_prefix: self.status_requested.emit(f"{cp}: {msg}"))
                self._lora_layout.addWidget(b)
        else:
            self._lora_frame.setVisible(False)

        # 6. Sidecar Section (Strictly hidden if no sidecar file exists!)
        if meta.sidecar_text and meta.sidecar_text.strip():
            self._sidecar_frame.setVisible(True)
            self._sidecar_edit.setPlainText(meta.sidecar_text.strip())
            self._adjust_text_edit_height(self._sidecar_edit, 26, 160)
        else:
            self._sidecar_frame.setVisible(False)

    def _copy_text(self, text: str, name: str):
        if text:
            pyperclip.copy(text)
            self.status_requested.emit(I18nManager.get_instance().tr("status.prompt_copied", "Промпт скопирован в буфер обмена"))
