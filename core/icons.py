"""
galIMVmini Tabler Vector Icons Engine.
Renders crisp Tabler SVG icons at any requested size and color.
Zero emojis, pure vector aesthetic matching galIMV / Lobe Hub Neo.
"""

from typing import Dict, Optional
from PyQt6.QtGui import QIcon, QPixmap, QPainter, QColor
from PyQt6.QtSvg import QSvgRenderer
from PyQt6.QtCore import QByteArray, QSize

TABLER_SVGS: Dict[str, str] = {
    "photo": '<path d="M15 8h.01" /><rect x="4" y="4" width="16" height="16" rx="3" /><path d="M4 15l4 -4a3 5 0 0 1 3 0l5 5" /><path d="M14 14l1 -1a3 5 0 0 1 3 0l2 2" />',
    "folder": '<path d="M5 4h4l3 3h7a2 2 0 0 1 2 2v8a2 2 0 0 1 -2 2h-14a2 2 0 0 1 -2 -2v-11a2 2 0 0 1 2 -2" />',
    "history": '<path d="M12 8l0 4l2 2" /><path d="M3.05 11a9 9 0 1 1 .5 4m-.5 5v-5h5" />',
    "chevron-left": '<path d="M15 6l-6 6l6 6" />',
    "chevron-right": '<path d="M9 6l6 6l-6 6" />',
    "arrows-maximize": '<path d="M16 4h4v4" /><path d="M14 10l6 -6" /><path d="M8 20h-4v-4" /><path d="M4 20l6 -6" />',
    "zoom-in": '<circle cx="10" cy="10" r="7" /><path d="M21 21l-6 -6" /><path d="M10 7v6" /><path d="M7 10h6" />',
    "zoom-out": '<circle cx="10" cy="10" r="7" /><path d="M21 21l-6 -6" /><path d="M7 10h6" />',
    "zoom-reset": '<path d="M9 16v-8l-2 2" /><path d="M13 16l4 -4" /><path d="M17 16l-4 -4" />',
    "multiplier-1x": '<path d="M9 16v-8l-2 2" /><path d="M13 16l4 -4" /><path d="M17 16l-4 -4" />',
    "maximize": '<path d="M4 8v-2a2 2 0 0 1 2 -2h2" /><path d="M4 16v2a2 2 0 0 0 2 2h2" /><path d="M16 4h2a2 2 0 0 1 2 2v2" /><path d="M16 20h2a2 2 0 0 0 2 -2v-2" />',
    "minimize": '<path d="M15 19v-2a2 2 0 0 1 2 -2h2" /><path d="M15 5v2a2 2 0 0 0 2 2h2" /><path d="M5 15h2a2 2 0 0 1 2 2v2" /><path d="M5 9h2a2 2 0 0 0 2 -2v-2" />',
    "world": '<circle cx="12" cy="12" r="9" /><line x1="3.6" y1="9" x2="20.4" y2="9" /><line x1="3.6" y1="15" x2="20.4" y2="15" /><path d="M11.5 3a17 17 0 0 0 0 18" /><path d="M12.5 3a17 17 0 0 1 0 18" />',
    "language": '<path d="M4 5h7" /><path d="M9 3v2c0 4.418 -2.239 8 -5 8" /><path d="M5 9c0 2.144 2.952 3.908 6.7 4" /><path d="M12 20l4 -9l4 9" /><path d="M19.1 18h-6.2" />',
    "aspect-ratio": '<rect x="3" y="5" width="18" height="14" rx="2" /><path d="M7 12v.01" /><path d="M12 12v.01" /><path d="M17 12v.01" />',
    "copy": '<rect x="8" y="8" width="12" height="12" rx="2" /><path d="M16 8v-2a2 2 0 0 0 -2 -2h-8a2 2 0 0 0 -2 2v8a2 2 0 0 0 2 2h2" />',
    "check": '<path d="M5 12l5 5l10 -10" />',
    "download": '<path d="M4 17v2a2 2 0 0 0 2 2h12a2 2 0 0 0 2 -2v-2" /><path d="M7 11l5 5l5 -5" /><path d="M12 4l0 12" />',
    "external-link": '<path d="M12 6h-6a2 2 0 0 0 -2 2v10a2 2 0 0 0 2 2h10a2 2 0 0 0 2 -2v-6" /><path d="M11 13l9 -9" /><path d="M15 4h5v5" />',
    "palette": '<path d="M12 21a9 9 0 0 1 0 -18c4.97 0 9 3.582 9 8c0 1.06 -.474 2.078 -1.318 2.828c-.844 .75 -1.989 1.172 -3.182 1.172h-2.5a2 2 0 0 0 -1 3.732a1 1 0 0 1 -.5 .268z" /><circle cx="7.5" cy="10.5" r="1" /><circle cx="12" cy="7.5" r="1" /><circle cx="16.5" cy="10.5" r="1" />',
    "sun": '<circle cx="12" cy="12" r="4" /><path d="M3 12h1m8 -9v1m8 8h1m-9 8v1M5.6 5.6l.7 .7m12.1 -.7l-.7 .7m0 11.4l.7 .7m-12.1 -.7l-.7 .7" />',
    "moon": '<path d="M12 3c.132 0 .263 0 .393 0a7.5 7.5 0 0 0 7.92 12.446a9 9 0 1 1 -8.313 -12.454z" />',
    "layout-bottombar": '<rect x="4" y="4" width="16" height="16" rx="2" /><line x1="4" y1="15" x2="20" y2="15" />',
    "layout-sidebar": '<rect x="4" y="4" width="16" height="16" rx="2" /><line x1="15" y1="4" x2="15" y2="20" />',
    "sparkles": '<path d="M16 18a2 2 0 0 1 2 2a2 2 0 0 1 2 -2a2 2 0 0 1 -2 -2a2 2 0 0 1 -2 2zm0 -12a2 2 0 0 1 2 2a2 2 0 0 1 2 -2a2 2 0 0 1 -2 -2a2 2 0 0 1 -2 2zm-7 3a5 5 0 0 1 5 5a5 5 0 0 1 -5 5a5 5 0 0 1 -5 -5a5 5 0 0 1 5 -5z" />',
    "tag": '<path d="M3 8v4.172a2 2 0 0 0 .586 1.414l7.71 7.71a2.41 2.41 0 0 0 3.408 0l5.592 -5.592a2.41 2.41 0 0 0 0 -3.408l-7.71 -7.71a2 2 0 0 0 -1.414 -.586h-6.172a2 2 0 0 0 -2 2z" /><circle cx="7.5" cy="7.5" r=".5" fill="currentColor" />',
    "trash": '<line x1="4" y1="7" x2="20" y2="7" /><line x1="10" y1="11" x2="10" y2="17" /><line x1="14" y1="11" x2="14" y2="17" /><path d="M5 7l1 12a2 2 0 0 0 2 2h8a2 2 0 0 0 2 -2l1 -12" /><path d="M9 7v-3a1 1 0 0 1 1 -1h4a1 1 0 0 1 1 1v3" />',
    "chevron-down": '<path d="M6 9l6 6l6 -6" />',
    "chevron-up": '<path d="M6 15l6 -6l6 6" />',
    "table": '<rect x="4" y="4" width="16" height="16" rx="2" /><line x1="4" y1="10" x2="20" y2="10" /><line x1="10" y1="4" x2="10" y2="20" />',
    "code": '<polyline points="7 8 3 12 7 16" /><polyline points="17 8 21 12 17 16" /><line x1="14" y1="4" x2="10" y2="20" />',
    "file-text": '<path d="M14 3v4a1 1 0 0 0 1 1h4" /><path d="M17 21h-10a2 2 0 0 1 -2 -2v-14a2 2 0 0 1 2 -2h7l5 5v11a2 2 0 0 1 -2 2z" /><line x1="9" y1="9" x2="10" y2="9" /><line x1="9" y1="13" x2="15" y2="13" /><line x1="9" y1="17" x2="15" y2="17" />',
    "circle-minus": '<circle cx="12" cy="12" r="9" /><line x1="9" y1="12" x2="15" y2="12" />',
    "ban": '<circle cx="12" cy="12" r="9" /><line x1="5.7" y1="5.7" x2="18.3" y2="18.3" />',
    "adjustments": '<circle cx="6" cy="10" r="2" /><line x1="6" y1="4" x2="6" y2="8" /><line x1="6" y1="12" x2="6" y2="20" /><circle cx="12" cy="16" r="2" /><line x1="12" y1="4" x2="12" y2="14" /><line x1="12" y1="18" x2="12" y2="20" /><circle cx="18" cy="7" r="2" /><line x1="18" y1="4" x2="18" y2="5" /><line x1="18" y1="9" x2="18" y2="20" />',
    "cpu": '<rect x="5" y="5" width="14" height="14" rx="2" /><rect x="9" y="9" width="6" height="6" /><line x1="9" y1="1" x2="9" y2="4" /><line x1="15" y1="1" x2="15" y2="4" /><line x1="9" y1="20" x2="9" y2="23" /><line x1="15" y1="20" x2="15" y2="23" /><line x1="20" y1="9" x2="23" y2="9" /><line x1="20" y1="14" x2="23" y2="14" /><line x1="1" y1="9" x2="4" y2="9" /><line x1="1" y1="14" x2="4" y2="14" />',
    "layers": '<path d="M12 2l-8 4l8 4l8 -4l-8 -4" /><path d="M4 10l8 4l8 -4" /><path d="M4 14l8 4l8 -4" />',
    "folder-open": '<path d="M5 4h4l3 3h7a2 2 0 0 1 2 2v8a2 2 0 0 1 -2 2h-14a2 2 0 0 1 -2 -2v-11a2 2 0 0 1 2 -2" /><path d="M5 19l2.75 -7.42a2 2 0 0 1 1.88 -1.28h11.74a1 1 0 0 1 .95 1.32l-2.07 6.1a2 2 0 0 1 -1.9 1.28h-13.35" />',
}

_icon_cache: Dict[str, QIcon] = {}

def get_tabler_icon(name: str, color: str = "#e4e4e7", size: int = 18, stroke_width: float = 2.0) -> QIcon:
    """Renders a Tabler SVG icon into a high-DPI QIcon."""
    cache_key = f"{name}_{color}_{size}_{stroke_width}"
    if cache_key in _icon_cache:
        return _icon_cache[cache_key]

    body = TABLER_SVGS.get(name, TABLER_SVGS["photo"])
    svg_template = f'''<svg xmlns="http://www.w3.org/2000/svg" width="{size}" height="{size}" viewBox="0 0 24 24" fill="none" stroke="{color}" stroke-width="{stroke_width}" stroke-linecap="round" stroke-linejoin="round">{body}</svg>'''
    
    renderer = QSvgRenderer(QByteArray(svg_template.encode("utf-8")))
    
    # Render at 2x size for high-DPI crispness
    render_size = size * 2
    pixmap = QPixmap(render_size, render_size)
    pixmap.fill(QColor(0, 0, 0, 0))

    painter = QPainter(pixmap)
    renderer.render(painter)
    painter.end()

    icon = QIcon(pixmap)
    _icon_cache[cache_key] = icon
    return icon
