"""Remove speech bubbles, narration boxes and SFX lettering from pages.

1. RT-DETR comic text/bubble detector finds bubbles, text in bubbles, free text.
2. Build an inpaint mask: bubbles -> the bright interior + outline (flood from
   bubble centre, dilated); free text -> dilated box of dark/bright strokes.
3. LaMa (manga-tuned) inpaints each masked area using a context crop.
Writes build/clean/<page>.png and build/clean/<page>_mask.png.
Usage: python3 clean.py [page ...]
"""
import json
import os
import sys

import numpy as np
import onnxruntime as ort
from PIL import Image
from scipy import ndimage as ndi

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
MODELS = os.path.join(ROOT, "build", "models")
OUT = os.path.join(ROOT, "build", "clean")

_det = None
_lama = None


def det_session():
    global _det
    if _det is None:
        so = ort.SessionOptions()
        so.intra_op_num_threads = 4
        _det = ort.InferenceSession(os.path.join(MODELS, "ctd_detector.onnx"), so)
    return _det


def lama_session():
    global _lama
    if _lama is None:
        so = ort.SessionOptions()
        so.intra_op_num_threads = 4
        _lama = ort.InferenceSession(os.path.join(MODELS, "lama_manga.onnx"), so)
    return _lama


def detect_text(img, thr=0.35):
    w, h = img.size
    x = np.asarray(img.convert("RGB").resize((640, 640), Image.BILINEAR), dtype=np.float32) / 255.0
    x = x.transpose(2, 0, 1)[None]
    labels, boxes, scores = det_session().run(None, {"images": x, "orig_target_sizes": np.array([[w, h]], dtype=np.int64)})
    out = []
    for l, b, s in zip(labels[0], boxes[0], scores[0]):
        if s >= thr:
            x0, y0, x1, y1 = [float(v) for v in b]
            out.append({"cls": int(l), "score": float(s), "box": [max(0, x0), max(0, y0), min(w, x1), min(h, y1)]})
    return out


def build_mask(img, dets):
    a = np.asarray(img.convert("RGB")).astype(np.int16)
    h, w, _ = a.shape
    gray = a.mean(axis=2)
    mask = np.zeros((h, w), bool)
    for d in dets:
        x0, y0, x1, y1 = [int(round(v)) for v in d["box"]]
        if x1 - x0 < 4 or y1 - y0 < 4:
            continue
        if d["cls"] == 0:  # bubble: white interior connected to centre + its outline
            sub = gray[y0:y1, x0:x1]
            bright = sub > 200
            lab, n = ndi.label(bright)
            cy, cx = (y1 - y0) // 2, (x1 - x0) // 2
            # pick the largest bright component overlapping the central region
            core = lab[max(0, cy - (y1 - y0) // 4): cy + (y1 - y0) // 4 + 1, max(0, cx - (x1 - x0) // 4): cx + (x1 - x0) // 4 + 1]
            ids, counts = np.unique(core[core > 0], return_counts=True)
            m = np.zeros_like(bright)
            if len(ids):
                m = lab == ids[np.argmax(counts)]
                m = ndi.binary_fill_holes(m)
                # bubble is mostly the box; if flood is tiny fall back to ellipse
            if m.sum() < 0.3 * bright.size:
                yy, xx = np.mgrid[0:y1 - y0, 0:x1 - x0]
                m = (((xx - cx) / max(1, cx)) ** 2 + ((yy - cy) / max(1, cy)) ** 2) <= 1.05
            m = ndi.binary_dilation(m, iterations=7)  # include the black outline + tail base
            mask[y0:y1, x0:x1] |= m
        else:  # text: dilate box a bit
            pad = 6 if d["cls"] == 1 else 10
            mask[max(0, y0 - pad):min(h, y1 + pad), max(0, x0 - pad):min(w, x1 + pad)] = True
    return mask


def lama_inpaint(img, mask):
    """Inpaint per connected region using a context crop (LaMa works best ~512)."""
    a = np.asarray(img.convert("RGB")).copy()
    h, w, _ = a.shape
    lab, n = ndi.label(ndi.binary_dilation(mask, iterations=24))
    for i, sl in enumerate(ndi.find_objects(lab), start=1):
        y0, y1, x0, x1 = sl[0].start, sl[0].stop, sl[1].start, sl[1].stop
        bh, bw = y1 - y0, x1 - x0
        side = int(max(bh, bw) * 1.8) + 64
        cy, cx = (y0 + y1) // 2, (x0 + x1) // 2
        Y0, Y1 = max(0, cy - side // 2), min(h, cy + side // 2)
        X0, X1 = max(0, cx - side // 2), min(w, cx + side // 2)
        crop = a[Y0:Y1, X0:X1]
        cm = mask[Y0:Y1, X0:X1] & (lab[Y0:Y1, X0:X1] == i)
        ch, cw = crop.shape[:2]
        S = 512
        im = np.asarray(Image.fromarray(crop).resize((S, S), Image.BICUBIC), dtype=np.float32) / 255.0
        mm = np.asarray(Image.fromarray((cm * 255).astype(np.uint8)).resize((S, S), Image.NEAREST), dtype=np.float32) / 255.0
        mm = (mm > 0.5).astype(np.float32)
        out = lama_session().run(None, {"image": im.transpose(2, 0, 1)[None], "mask": mm[None, None]})[0][0]
        out = out.transpose(1, 2, 0)
        if out.max() > 2:
            out = out / 255.0
        out = np.clip(out * 255, 0, 255).astype(np.uint8)
        out = np.asarray(Image.fromarray(out).resize((cw, ch), Image.BICUBIC))
        soft = ndi.gaussian_filter(cm.astype(np.float32), 1.5)[..., None]
        soft = np.clip(soft * 1.6, 0, 1)
        a[Y0:Y1, X0:X1] = (crop * (1 - soft) + out * soft).astype(np.uint8)
    return Image.fromarray(a)


def main():
    os.makedirs(OUT, exist_ok=True)
    pages = sys.argv[1:] or sorted(f[:-4] for f in os.listdir(os.path.join(ROOT, "pages")) if f.endswith(".jpg"))
    meta = {}
    mpath = os.path.join(OUT, "detections.json")
    if os.path.exists(mpath):
        meta = json.load(open(mpath))
    for p in pages:
        img = Image.open(os.path.join(ROOT, "pages", p + ".jpg")).convert("RGB")
        dets = detect_text(img)
        mask = build_mask(img, dets)
        clean = lama_inpaint(img, mask) if mask.any() else img
        clean.save(os.path.join(OUT, p + ".png"))
        Image.fromarray((mask * 255).astype(np.uint8)).save(os.path.join(OUT, p + "_mask.png"))
        meta[p] = dets
        print(p, len(dets), "dets", round(mask.mean() * 100, 1), "% masked", flush=True)
    json.dump(meta, open(mpath, "w"), indent=1)


if __name__ == "__main__":
    main()
