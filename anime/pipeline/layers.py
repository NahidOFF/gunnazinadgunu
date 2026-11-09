"""Split each HD panel into a foreground layer (characters / near objects) and a
background plate with the foreground removed (LaMa inpainting), using the
depth map. This enables real 2.5D animation: the foreground can move, breathe,
lunge or shake independently, and camera parallax reveals clean background.

Outputs build/layers/<panel_id>_fg.png (RGBA) and _bg.png (RGB) plus
build/layers/index.json with fg coverage stats. Panels whose foreground
covers almost everything (face close-ups) or nothing are marked split=false.
Usage: python3 layers.py [panel_id_prefix ...]
"""
import json
import os
import sys

import numpy as np
from PIL import Image
from scipy import ndimage as ndi

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
from clean import lama_session  # noqa: E402

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
HD = os.path.join(ROOT, "build", "hd")
OUT = os.path.join(ROOT, "build", "layers")


def otsu(x, bins=128):
    h, e = np.histogram(x, bins=bins, range=(0, 1))
    h = h.astype(np.float64)
    c = (e[:-1] + e[1:]) / 2
    w0 = np.cumsum(h)
    w1 = w0[-1] - w0
    m0 = np.cumsum(h * c) / np.maximum(w0, 1)
    m1 = (np.sum(h * c) - np.cumsum(h * c)) / np.maximum(w1, 1)
    between = w0 * w1 * (m0 - m1) ** 2
    return c[np.argmax(between)]


def fg_mask(depth):
    small = np.asarray(Image.fromarray((depth * 255).astype(np.uint8)).resize((512, int(512 * depth.shape[0] / depth.shape[1]))), np.float32) / 255
    t = otsu(small)
    t = max(0.35, min(0.8, t))
    m = small > t
    m = ndi.binary_opening(m, iterations=2)
    m = ndi.binary_closing(m, iterations=3)
    m = ndi.binary_fill_holes(m)
    lab, n = ndi.label(m)
    if n:
        sizes = ndi.sum(m, lab, range(1, n + 1))
        keep = [i + 1 for i, s in enumerate(sizes) if s > 0.01 * m.size]
        m = np.isin(lab, keep)
    return m, t


def inpaint_bg(rgb, mask_small):
    h, w, _ = rgb.shape
    S = 1024
    s = S / max(h, w)
    sw, sh = max(8, int(w * s) // 8 * 8), max(8, int(h * s) // 8 * 8)
    im = np.asarray(Image.fromarray(rgb).resize((sw, sh), Image.BICUBIC), np.float32) / 255
    mm = np.asarray(Image.fromarray((mask_small * 255).astype(np.uint8)).resize((sw, sh), Image.NEAREST)) > 127
    mm = ndi.binary_dilation(mm, iterations=10).astype(np.float32)
    out = lama_session().run(None, {"image": im.transpose(2, 0, 1)[None], "mask": mm[None, None]})[0][0].transpose(1, 2, 0)
    if out.max() > 2:
        out = out / 255
    out = np.clip(out * 255, 0, 255).astype(np.uint8)
    big = np.asarray(Image.fromarray(out).resize((w, h), Image.BICUBIC))
    mb = np.asarray(Image.fromarray((mm * 255).astype(np.uint8)).resize((w, h), Image.BILINEAR), np.float32)[..., None] / 255
    return (rgb * (1 - mb) + big * mb).astype(np.uint8)


def main():
    os.makedirs(OUT, exist_ok=True)
    idx_path = os.path.join(OUT, "index.json")
    index = json.load(open(idx_path)) if os.path.exists(idx_path) else {}
    prefixes = sys.argv[1:]
    ids = sorted(f[:-4] for f in os.listdir(HD) if f.endswith(".png") and not f.endswith("_depth.png"))
    if prefixes:
        ids = [i for i in ids if any(i.startswith(p) for p in prefixes)]
    for pid in ids:
        if pid in index and os.path.exists(os.path.join(OUT, pid + "_bg.png")):
            continue
        rgb = np.asarray(Image.open(os.path.join(HD, pid + ".png")).convert("RGB"))
        depth = np.asarray(Image.open(os.path.join(HD, pid + "_depth.png")), np.float32) / 65535
        m, t = fg_mask(depth)
        cov = float(m.mean())
        split = 0.04 < cov < 0.62
        info = {"cov": round(cov, 3), "thr": round(float(t), 3), "split": split}
        if split:
            h, w, _ = rgb.shape
            alpha = np.asarray(Image.fromarray((m * 255).astype(np.uint8)).resize((w, h), Image.BILINEAR), np.float32) / 255
            alpha = ndi.gaussian_filter(alpha, 1.2)
            alpha = np.clip((alpha - 0.5) * 2.2 + 0.5, 0, 1)
            fg = np.dstack([rgb, (alpha * 255).astype(np.uint8)])
            Image.fromarray(fg, "RGBA").save(os.path.join(OUT, pid + "_fg.png"))
            bg = inpaint_bg(rgb, m)
            Image.fromarray(bg).save(os.path.join(OUT, pid + "_bg.png"))
            ys, xs = np.nonzero(m)
            info["fg_box"] = [float(xs.min() / m.shape[1]), float(ys.min() / m.shape[0]), float(xs.max() / m.shape[1]), float(ys.max() / m.shape[0])]
            info["fg_center"] = [float(xs.mean() / m.shape[1]), float(ys.mean() / m.shape[0])]
        index[pid] = info
        json.dump(index, open(idx_path, "w"), indent=1)
        print(pid, info, flush=True)


if __name__ == "__main__":
    main()
