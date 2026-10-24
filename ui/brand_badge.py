"""The shared contour mark and classic galIMV wordmark, with mini edition badge."""
from PyQt6.QtCore import Qt, QSize
from PyQt6.QtGui import QColor, QFont
from PyQt6.QtWidgets import QWidget, QFrame, QLabel, QHBoxLayout, QSizePolicy
from core.design import DESIGN, readable_accent
from core.icons import get_tabler_icon


class BrandBadge(QWidget):
    def __init__(self, parent=None):
        super().__init__(parent)
        self.setObjectName("viewerBrand")
        self.setAccessibleName("galIMV mini")
        self.setSizePolicy(QSizePolicy.Policy.Fixed,QSizePolicy.Policy.Fixed)
        self.setFixedHeight(36)
        self.metrics=DESIGN["brand"]
        row=QHBoxLayout(self)
        row.setContentsMargins(4,0,8,0)
        row.setSpacing(self.metrics["gap"])
        self._mark=QFrame(self)
        self._mark.setObjectName("brandMark")
        self._mark.setFixedSize(self.metrics["markSize"],self.metrics["markSize"])
        mark_layout=QHBoxLayout(self._mark)
        mark_layout.setContentsMargins(0,0,0,0)
        self._icon=QLabel(self._mark)
        self._icon.setAlignment(Qt.AlignmentFlag.AlignCenter)
        self._icon.setStyleSheet("background:transparent;border:none;padding:0;")
        mark_layout.addWidget(self._icon)
        row.addWidget(self._mark)
        self.wordmark=QLabel(self)
        self.wordmark.setObjectName("brandWordmark")
        self.wordmark.setTextFormat(Qt.TextFormat.RichText)
        font=QFont("Segoe UI")
        font.setPixelSize(self.metrics["fontSize"])
        font.setWeight(QFont.Weight.Bold)
        font.setLetterSpacing(QFont.SpacingType.AbsoluteSpacing,self.metrics["letterSpacing"])
        self.wordmark.setFont(font)
        self.wordmark.setStyleSheet(f"background:transparent;border:none;padding:0;font-family:'Segoe UI';font-size:{self.metrics['fontSize']}px;font-weight:700;")
        row.addWidget(self.wordmark)
        self._edition=QLabel("mini",self)
        self._edition.setFixedHeight(18)
        row.addWidget(self._edition)

    def update_theme(self, colors):
        ink=readable_accent(colors.accent,colors.bg_surface)
        color=QColor(ink);r,g,b=color.red(),color.green(),color.blue()
        self._mark.setStyleSheet(f"QFrame#brandMark{{background:rgba({r},{g},{b},0.10);border:1px solid rgba({r},{g},{b},0.40);border-radius:{self.metrics['markRadius']}px;}}")
        size=self.metrics["iconSize"]
        self._icon.setPixmap(get_tabler_icon(self.metrics["icon"],ink,size).pixmap(QSize(size,size),self.devicePixelRatioF()))
        self.wordmark.setText(f'<span style="font-weight:400;color:{ink}">gal</span><span style="color:{colors.text_primary}">IMV</span>')
        self._edition.setStyleSheet(f"background:rgba({r},{g},{b},0.08);color:{ink};border:1px solid rgba({r},{g},{b},0.32);border-radius:5px;padding:0 5px;font-size:11px;font-weight:500;")
