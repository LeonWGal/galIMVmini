from pathlib import Path
import struct

root = Path(__file__).resolve().parents[1]
source = root / "tools" / "variant-pngs"
target = root / "resources" / "lobe-variants"
sizes = (16, 20, 24, 32, 40, 48, 64, 96, 128, 256)
for folder in sorted(source.iterdir()):
    if not folder.is_dir():
        continue
    payloads = [(folder / f"{size}.png").read_bytes() for size in sizes]
    offset = 6 + 16 * len(sizes)
    entries = []
    for size, data in zip(sizes, payloads):
        entries.append(struct.pack("<BBBBHHII", size % 256, size % 256, 0, 0, 1, 32, len(data), offset))
        offset += len(data)
    ico = struct.pack("<HHH", 0, 1, len(sizes)) + b"".join(entries) + b"".join(payloads)
    (target / f"simple-{folder.name}.ico").write_bytes(ico)
print("Packed ICO variants")
