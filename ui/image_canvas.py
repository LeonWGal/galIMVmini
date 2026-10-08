"""
galIMVmini Interactive Image Canvas.
High-performance zoomable and pannable image viewer powered by QGraphicsView.
Supports smooth mouse wheel zoom, click-drag panning, fit-to-window, 100% zoom,
and double-click toggle.
"""

from PyQt6.QtWidgets import (
    QGraphicsView, QGraphicsScene, QGraphicsPixmapItem,
    QFrame, QVBoxLayout, QLabel, QWidget
)
from PyQt6.QtCore import Qt, pyqtSignal, QPointF, QRectF
from PyQt6.QtGui import (
    QPixmap, QPainter, QWheelEvent, QMouseEvent, QColor, QFont,
    QDragEnterEvent, QDropEvent
)

try:
    from core.theme import ThemeManager
    from core.i18n import I18nManager
except ImportError:
    from galIMVmini.core.theme import ThemeManager
    from galIMVmini.core.i18n import I18nManager

class ImageCanvas(QGraphicsView):
    zoom_changed = pyqtSignal(float)   # Emits zoom factor e.g. 1.0 = 100%
    image_dropped = pyqtSignal(str)    # Emits dropped file path
    open_requested = pyqtSignal()      # Emits when empty area clicked to browse

    def __init__(self, parent=None):
        super().__init__(parent)
        self._scene = QGraphicsScene(self)
        self.setScene(self._scene)

        self._pixmap_item: QGraphicsPixmapItem | None = None
        self._zoom_factor = 1.0
        self._min_zoom = 0.05
        self._max_zoom = 30.0
        self._is_fitting = True
        self._has_image = False
        self._current_pixmap: QPixmap | None = None

        # Rendering options
        self.setRenderHints(
            QPainter.RenderHint.Antialiasing |
            QPainter.RenderHint.SmoothPixmapTransform
        )
        self.setViewportUpdateMode(QGraphicsView.ViewportUpdateMode.SmartViewportUpdate)
        self.setOptimizationFlags(QGraphicsView.OptimizationFlag.DontAdjustForAntialiasing)
        self.setDragMode(QGraphicsView.DragMode.ScrollHandDrag)
        self.setTransformationAnchor(QGraphicsView.ViewportAnchor.AnchorUnderMouse)
        self.setResizeAnchor(QGraphicsView.ViewportAnchor.AnchorViewCenter)
        self.setVerticalScrollBarPolicy(Qt.ScrollBarPolicy.ScrollBarAsNeeded)
        self.setHorizontalScrollBarPolicy(Qt.ScrollBarPolicy.ScrollBarAsNeeded)
        self.setFrameShape(QFrame.Shape.NoFrame)
        self.setAcceptDrops(True)

        # Empty state overlay
        self._overlay = QWidget(self)
        self._overlay_layout = QVBoxLayout(self._overlay)
        self._overlay_layout.setAlignment(Qt.AlignmentFlag.AlignCenter)
        
        self._drop_label = QLabel(self._overlay)
        self._drop_label.setAlignment(Qt.AlignmentFlag.AlignCenter)
        self._drop_label.setWordWrap(True)
        self._drop_label.setCursor(Qt.CursorShape.PointingHandCursor)
        self._drop_label.mousePressEvent = lambda e: self.open_requested.emit()
        self._overlay_layout.addWidget(self._drop_label)

        self.update_theme()
        ThemeManager.get_instance().add_listener(self.update_theme)
        I18nManager.get_instance().add_listener(self.update_theme)

    def update_theme(self):
        c = ThemeManager.get_instance().get_colors()
        self.setBackgroundBrush(QColor(c.bg_app))
        
        # Style drop label with i18n
        accent = c.accent
        i18n = I18nManager.get_instance()
        title = i18n.tr("drop.title", "Перетащите изображение сюда")
        hint = i18n.tr("drop.hint", "или нажмите, чтобы открыть файл (JPG, PNG, WebP, GIF, BMP, TIFF)")
        btn = i18n.tr("drop.browse", "Обзор файлов (Ctrl+O)")
        self._drop_label.setText(
            f"<div style='font-size: 15px; font-weight: 600; margin-bottom: 8px; color: {c.text_primary};'>{title}</div>"
            f"<div style='font-size: 12px; color: {c.text_secondary}; margin-bottom: 14px;'>{hint}</div>"
            f"<div style='display: inline-block; padding: 6px 14px; background-color: {c.bg_card}; "
            f"border: 1px solid {c.border_subtle}; border-radius: 6px; font-size: 12px; color: {accent}; font-weight: 500;'>{btn}</div>"
        )
        self._drop_label.setStyleSheet(f"""
            QLabel {{
                background-color: {c.bg_surface};
                border: 2px dashed {c.border_subtle};
                border-radius: 12px;
                padding: 30px 40px;
            }}
            QLabel:hover {{
                border-color: {c.accent};
                background-color: {c.bg_card};
            }}
        """)

    def set_pixmap(self, pixmap: QPixmap):
        self._scene.clear()
        self._current_pixmap = pixmap
        if pixmap.isNull():
            self._has_image = False
            self._overlay.setVisible(True)
            self._pixmap_item = None
            return

        self._has_image = True
        self._overlay.setVisible(False)
        self._pixmap_item = self._scene.addPixmap(pixmap)
        self._scene.setSceneRect(QRectF(pixmap.rect()))
        
        self.fit_to_window()

    def clear(self):
        self._scene.clear()
        self._current_pixmap = None
        self._has_image = False
        self._pixmap_item = None
        self._overlay.setVisible(True)

    def fit_to_window(self):
        if not self._has_image or not self._pixmap_item:
            return
        self._is_fitting = True
        self.resetTransform()
        rect = self._scene.sceneRect()
        if rect.isEmpty():
            return
        
        # Fit with slight margin (16px)
        view_rect = self.viewport().rect().adjusted(16, 16, -16, -16)
        scale_x = view_rect.width() / rect.width()
        scale_y = view_rect.height() / rect.height()
        scale = min(scale_x, scale_y)
        
        # Clamp scale so small images don't get blown up beyond 1.0 unless tiny
        if scale > 1.0 and rect.width() > 100 and rect.height() > 100:
            scale = 1.0

        self.scale(scale, scale)
        self._zoom_factor = scale
        self.zoom_changed.emit(self._zoom_factor)

    def set_original_size(self):
        if not self._has_image:
            return
        self._is_fitting = False
        self.resetTransform()
        self._zoom_factor = 1.0
        self.centerOn(self._scene.sceneRect().center())
        self.zoom_changed.emit(self._zoom_factor)

    def zoom_in(self):
        self._apply_zoom(1.25)

    def zoom_out(self):
        self._apply_zoom(0.8)

    def _apply_zoom(self, factor: float):
        if not self._has_image:
            return
        new_zoom = self._zoom_factor * factor
        if self._min_zoom <= new_zoom <= self._max_zoom:
            self._is_fitting = False
            self.scale(factor, factor)
            self._zoom_factor = new_zoom
            self.zoom_changed.emit(self._zoom_factor)

    def wheelEvent(self, event: QWheelEvent):
        if not self._has_image:
            super().wheelEvent(event)
            return

        delta = event.angleDelta().y()
        if delta > 0:
            factor = 1.15
        elif delta < 0:
            factor = 1.0 / 1.15
        else:
            return

        self._apply_zoom(factor)
        event.accept()

    def mouseDoubleClickEvent(self, event: QMouseEvent):
        if not self._has_image:
            super().mouseDoubleClickEvent(event)
            return

        if self._is_fitting or abs(self._zoom_factor - 1.0) > 0.05:
            if abs(self._zoom_factor - 1.0) < 0.05:
                self.fit_to_window()
            else:
                self.set_original_size()
        else:
            self.fit_to_window()
        event.accept()

    def resizeEvent(self, event):
        super().resizeEvent(event)
        self._overlay.setGeometry(self.rect())
        if self._is_fitting and self._has_image:
            self.fit_to_window()

    # Drag and Drop handlers
    def dragEnterEvent(self, event: QDragEnterEvent):
        if event.mimeData().hasUrls():
            for url in event.mimeData().urls():
                p = url.toLocalFile().lower()
                if p.endswith((".png", ".jpg", ".jpeg", ".webp", ".gif", ".bmp", ".tiff")):
                    event.acceptProposedAction()
                    return
        event.ignore()

    def dragMoveEvent(self, event):
        event.acceptProposedAction()

    def dropEvent(self, event: QDropEvent):
        if event.mimeData().hasUrls():
            for url in event.mimeData().urls():
                p = url.toLocalFile()
                if p.lower().endswith((".png", ".jpg", ".jpeg", ".webp", ".gif", ".bmp", ".tiff")):
                    self.image_dropped.emit(p)
                    event.acceptProposedAction()
                    return
        event.ignore()
