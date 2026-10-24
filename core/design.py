"""Design tokens shared with galIMV's generated QML module."""
import json
from pathlib import Path
from PyQt6.QtGui import QColor
DESIGN = json.loads((Path(__file__).resolve().parents[1] / "resources" / "ui" / "design.json").read_text(encoding="utf-8"))
METRICS = DESIGN["metrics"]
def luminance(color):
    c=QColor(color)
    def linear(v): return v/12.92 if v<=0.04045 else ((v+0.055)/1.055)**2.4
    return 0.2126*linear(c.redF())+0.7152*linear(c.greenF())+0.0722*linear(c.blueF())
def contrast(a,b):
    x,y=luminance(a),luminance(b)
    return (max(x,y)+0.05)/(min(x,y)+0.05)
def text_on(color):
    ink="#ffffff" if contrast(color,"#ffffff")>=contrast(color,"#111318") else "#111318"
    if contrast(color,ink)<4.5:ink="#ffffff" if contrast(color,"#ffffff")>=contrast(color,"#000000") else "#000000"
    return ink
def readable_accent(color,background):
    c=QColor(color); end=QColor("#ffffff" if luminance(background)<0.18 else "#111318")
    if contrast(c,background)>=4.5: return c.name()
    original=QColor(c)
    for step in range(1,101):
        a=step/100
        c.setRgb(round(original.red()*(1-a)+end.red()*a),round(original.green()*(1-a)+end.green()*a),round(original.blue()*(1-a)+end.blue()*a))
        if contrast(c,background)>=4.5:return c.name()
    return end.name()
