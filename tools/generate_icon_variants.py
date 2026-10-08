"""Create simple.svg variants using the Lobe accent palette."""
from pathlib import Path
from html import escape

root = Path(__file__).resolve().parents[1]
source = root / "resources" / "app.svg"
out = root / "resources" / "lobe-variants"
out.mkdir(parents=True, exist_ok=True)
template = source.read_text(encoding="utf-8")

palette = {
    "blue":    ("Lobe Blue", "#123B70", "#4D8DDE", "#A8D1FF", "#1677ff", "#69B1FF", "#8CC8FF", "#D6EBFF"),
    "purple":  ("Lobe Purple", "#24154A", "#5B25A8", "#B37FEB", "#722ed1", "#B37FEB", "#C9A7F5", "#E7D8FF"),
    "magenta": ("Lobe Magenta", "#4A1637", "#B52173", "#F27DB2", "#eb2f96", "#FF85C0", "#FFADD2", "#FFE0EF"),
    "cyan":    ("Lobe Cyan", "#103B3D", "#229A9A", "#63D8D3", "#13c2c2", "#5CDBD3", "#87E8DE", "#D7FFFC"),
    "green":   ("Lobe Green", "#1B3A20", "#439F22", "#95DE64", "#52c41a", "#95DE64", "#B7EB8F", "#E1FFD2"),
    "orange":  ("Lobe Orange", "#4A2810", "#C66C12", "#FFC069", "#fa8c16", "#FFD591", "#FFB84D", "#FFF0D9"),
    "zinc":    ("Monochrome Zinc", "#27272A", "#5B5B63", "#A1A1AA", "#71717a", "#A1A1AA", "#C4C4CC", "#E4E4E7"),
}

replacements = (
    ("#103B2D", 0), ("#4D9272", 1), ("#9DCEB3", 2),
    ("#287653", 3), ("#61AE86", 4), ("#82A394", 5), ("#F4FFF8", 6),
)

cards = []
for slug, (name, *colors) in palette.items():
    svg = template
    for old, index in replacements:
        svg = svg.replace(old, colors[index])
    svg = svg.replace("Image — green flat icon", f"Image — {name} icon")
    svg = svg.replace("emerald green", name.lower())
    target = out / f"simple-{slug}.svg"
    target.write_text(svg, encoding="utf-8")
    cards.append((name, target.name, colors[3]))

sizes = (16, 24, 32, 48, 64, 128, 256)
html = """<!doctype html><meta charset='utf-8'><title>galIMVmini · Lobe icon variants</title>
<style>
*{box-sizing:border-box}body{margin:0;background:#09090b;color:#f4f4f5;font:14px 'Segoe UI',sans-serif}main{max-width:1280px;margin:auto;padding:32px}h1{font-size:24px;font-weight:500;margin:0 0 8px}p{color:#a1a1aa;margin:0 0 26px}.grid{display:grid;grid-template-columns:repeat(auto-fit,minmax(300px,1fr));gap:18px}.card{padding:16px;border:1px solid #27272a;border-radius:16px;background:#121215}.name{font-weight:600}.hex{margin-top:5px;color:#a1a1aa;font-family:monospace}.backgrounds{display:grid;grid-template-columns:repeat(2,1fr);gap:8px;margin-top:14px}.stage{height:140px;border-radius:10px;display:grid;place-items:center;border:1px solid rgba(255,255,255,.12)}.stage img{width:112px;height:112px}.light{background:#f4f4f5}.dark{background:#09090b}.color{background:#334155}.warm{background:#f8ead8}.checker{background-color:#d4d4d8;background-image:linear-gradient(45deg,#a1a1aa 25%,transparent 25%),linear-gradient(-45deg,#a1a1aa 25%,transparent 25%),linear-gradient(45deg,transparent 75%,#a1a1aa 75%),linear-gradient(-45deg,transparent 75%,#a1a1aa 75%);background-size:20px 20px;background-position:0 0,0 10px,10px -10px,-10px 0}.label{font-size:11px;color:#a1a1aa;margin-top:5px}.sizes{display:flex;align-items:end;gap:12px;min-height:145px;padding:14px 4px 4px;overflow-x:auto}.size{display:flex;flex-direction:column;align-items:center;gap:5px;color:#a1a1aa;font-size:10px;min-width:30px}.size img{object-fit:contain}.size img[src$='16']{image-rendering:auto}
</style>
<main><h1>galIMVmini · Lobe accent variants</h1><p>Проверка контраста: светлый, тёмный, slate, тёплый и прозрачный шахматный фон. Ниже — реальные размеры Windows-иконки.</p><div class='grid'>
"""

def render_card(card):
    name, filename, hex_color = card
    scale = "".join(
        f"<div class='size'><img src='{escape(filename)}' width='{size}' height='{size}' alt='{size}px'><span>{size}</span></div>"
        for size in sizes
    )
    return (
        f"<article class='card'><div class='name'>{escape(name)}</div><div class='hex'>{hex_color}</div>"
        f"<div class='backgrounds'>"
        f"<div><div class='stage light'><img src='{escape(filename)}' alt='{escape(name)} light'></div><div class='label'>light</div></div>"
        f"<div><div class='stage dark'><img src='{escape(filename)}' alt='{escape(name)} dark'></div><div class='label'>dark</div></div>"
        f"<div><div class='stage color'><img src='{escape(filename)}' alt='{escape(name)} slate'></div><div class='label'>slate</div></div>"
        f"<div><div class='stage warm'><img src='{escape(filename)}' alt='{escape(name)} warm'></div><div class='label'>warm</div></div>"
        f"<div><div class='stage checker'><img src='{escape(filename)}' alt='{escape(name)} transparent'></div><div class='label'>transparent</div></div>"
        f"</div><div class='sizes'>{scale}</div></article>"
    )

html += "\n".join(render_card(card) for card in cards) + "</div></main>"
(out / "preview.html").write_text(html, encoding="utf-8")
print(f"Generated {len(cards)} variants in {out}")
