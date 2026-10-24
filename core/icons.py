"""The same Tabler paths, viewBox and stroke used by galIMV."""
from PyQt6.QtGui import QIcon,QPixmap,QPainter,QColor
from PyQt6.QtSvg import QSvgRenderer
from PyQt6.QtCore import QByteArray
from .design import DESIGN
TABLER_SVGS=DESIGN["icons"]
_icon_cache={}
def get_tabler_icon(name, color="#c8c8d2", size=18, stroke_width=2.0):
    key=(name,color,size,stroke_width)
    if key in _icon_cache:return _icon_cache[key]
    if not name:return QIcon()
    body=TABLER_SVGS.get(name,TABLER_SVGS["info"])
    svg=f'<svg xmlns="http://www.w3.org/2000/svg" width="24" height="24" viewBox="0 0 24 24" fill="none" stroke="{color}" stroke-width="{stroke_width}" stroke-linecap="round" stroke-linejoin="round">{body}</svg>'
    renderer=QSvgRenderer(QByteArray(svg.encode("utf-8")))
    icon=QIcon()
    for dpr in (1,2,3):
        pixmap=QPixmap(size*dpr,size*dpr);pixmap.fill(QColor(0,0,0,0))
        painter=QPainter(pixmap);renderer.render(painter);painter.end()
        pixmap.setDevicePixelRatio(dpr);icon.addPixmap(pixmap)
    _icon_cache[key]=icon
    return icon
