from pathlib import Path
import struct

root = Path(__file__).resolve().parents[1]
folder = root / "tools" / "icon-pngs"
sizes = (16, 20, 24, 32, 40, 48, 64, 96, 128, 256)
payloads = [(folder / f"{size}.png").read_bytes() for size in sizes]
offset = 6 + 16 * len(sizes)
entries = []
for size, data in zip(sizes, payloads):
    entries.append(struct.pack("<BBBBHHII", size % 256, size % 256, 0, 0, 1, 32, len(data), offset))
    offset += len(data)
(root / "resources" / "app.ico").write_bytes(
    struct.pack("<HHH", 0, 1, len(sizes)) + b"".join(entries) + b"".join(payloads)
)
print("Wrote", root / "resources" / "app.ico")
