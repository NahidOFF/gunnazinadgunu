"""Panel extraction from manga pages.

Pages use white gutters around panels (often slanted). We find the gutter
(near-white pixels connected to the page border), and the panels are the
connected components of everything else. Each panel gets a bbox and a mask
(so slanted panels can be cut cleanly). Writes build/panels/<page>/pNN.png
crops, build/panels.json, and annotated overview images for review.
"""
import json
import os
import sys

import numpy as np
from PIL import Image, ImageDraw, ImageFont
from scipy import ndimage as ndi

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
PAGES = os.path.join(ROOT, "pages")
OUT = os.path.join(ROOT, "build", "panels")
ANN = os.path.join(ROOT, "build", "annotated")


def detect(img):
    a = np.asarray(img.convert("RGB")).astype(np.int16)
    h, w, _ = a.shape
    white = (a.min(axis=2) > 225) & ((a.max(axis=2) - a.min(axis=2)) < 30)
    # Gutter = white region connected to the page border. Speech bubbles are
    # white too but enclosed by panel art, so they are not border-connected.
    lab, n = ndi.label(white)
    border = np.unique(np.concatenate([lab[0], lab[-1], lab[:, 0], lab[:, -1]]))
    border = border[border > 0]
    gutter = np.isin(lab, border)
    # Thin gutters can be broken by art that slightly overlaps; also treat thin
    # straight white bands as gutter by closing the gutter a little.
    gutter = ndi.binary_dilation(gutter, iterations=2)
    content = ~gutter
    content = ndi.binary_opening(content, iterations=3)
    lab2, n2 = ndi.label(content)
    panels = []
    for i, sl in enumerate(ndi.find_objects(lab2), start=1):
        if sl is None:
            continue
        m = lab2[sl] == i
        area = m.sum()
        if area < 0.012 * h * w:
            continue
        if min(sl[0].stop - sl[0].start, sl[1].stop - sl[1].start) < 80:
            continue
        m = ndi.binary_fill_holes(m)
        y0, y1, x0, x1 = sl[0].start, sl[0].stop, sl[1].start, sl[1].stop
        panels.append({"bbox": [int(x0), int(y0), int(x1), int(y1)], "area": int(area), "mask": m})
    # reading order: by row (top), then left->right
    panels.sort(key=lambda p: (round(p["bbox"][1] / (h * 0.06)), p["bbox"][0]))
    return panels


def main():
    os.makedirs(OUT, exist_ok=True)
    os.makedirs(ANN, exist_ok=True)
    try:
        font = ImageFont.truetype("/usr/share/fonts/truetype/dejavu/DejaVuSans-Bold.ttf", 48)
    except OSError:
        font = ImageFont.load_default()
    result = {}
    names = sorted(f for f in os.listdir(PAGES) if f.endswith(".jpg"))
    if len(sys.argv) > 1:
        names = [n for n in names if n.split(".")[0] in sys.argv[1:]]
    for name in names:
        page = name.split(".")[0]
        img = Image.open(os.path.join(PAGES, name)).convert("RGB")
        panels = detect(img)
        d = os.path.join(OUT, page)
        os.makedirs(d, exist_ok=True)
        ann = img.copy()
        dr = ImageDraw.Draw(ann)
        entries = []
        for k, p in enumerate(panels, start=1):
            x0, y0, x1, y1 = p["bbox"]
            crop = img.crop((x0, y0, x1, y1))
            mask = Image.fromarray((p["mask"] * 255).astype(np.uint8))
            crop.save(os.path.join(d, f"p{k:02d}.png"))
            mask.save(os.path.join(d, f"p{k:02d}_mask.png"))
            dr.rectangle([x0, y0, x1, y1], outline=(255, 0, 0), width=5)
            dr.rectangle([x0 + 4, y0 + 4, x0 + 74, y0 + 60], fill=(255, 0, 0))
            dr.text((x0 + 10, y0 + 4), str(k), fill=(255, 255, 255), font=font)
            entries.append({"id": f"{page}_p{k:02d}", "bbox": p["bbox"],
                            "w": x1 - x0, "h": y1 - y0})
        ann.save(os.path.join(ANN, f"{page}.jpg"), quality=85)
        result[page] = {"size": img.size, "panels": entries}
        print(page, len(entries), [e["bbox"] for e in entries])
    path = os.path.join(ROOT, "build", "panels.json")
    old = json.load(open(path)) if os.path.exists(path) and len(sys.argv) > 1 else {}
    old.update(result)
    json.dump(old, open(path, "w"), indent=1)


if __name__ == "__main__":
    main()
