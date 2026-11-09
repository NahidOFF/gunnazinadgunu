"""Upscale cleaned panels (Real-ESRGAN anime) and compute depth maps.

For every panel in build/panels.json (optionally filtered by page), crops the
cleaned page with the panel mask, fills outside-mask corners (slanted panels)
by edge extension, upscales 4x with realesr-animevideov3 (tiled), then
estimates depth with Depth-Anything-V2-Small.
Outputs build/hd/<panel_id>.png (RGB) and build/hd/<panel_id>_depth.png (16-bit).
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
HD = os.path.join(ROOT, "build", "hd")
MAX_SIDE = 3200  # cap upscaled long side

_sr = None
_depth = None


def sr_session():
    global _sr
    if _sr is None:
        so = ort.SessionOptions()
        so.intra_op_num_threads = int(os.environ.get("THREADS", "4"))
        _sr = ort.InferenceSession(os.path.join(MODELS, "animevideov3.onnx"), so)
    return _sr


def upscale(rgb, tile=256, pad=12):
    h, w, _ = rgb.shape
    x = rgb.astype(np.float32) / 255.0
    out = np.zeros((h * 4, w * 4, 3), np.float32)
    for ty in range(0, h, tile):
        for tx in range(0, w, tile):
            y0, x0 = max(0, ty - pad), max(0, tx - pad)
            y1, x1 = min(h, ty + tile + pad), min(w, tx + tile + pad)
            t = x[y0:y1, x0:x1].transpose(2, 0, 1)[None]
            o = sr_session().run(None, {"input": t})[0][0].transpose(1, 2, 0)
            oy, ox = (ty - y0) * 4, (tx - x0) * 4
            hh, ww = min(tile, h - ty) * 4, min(tile, w - tx) * 4
            out[ty * 4:ty * 4 + hh, tx * 4:tx * 4 + ww] = o[oy:oy + hh, ox:ox + ww]
    return np.clip(out * 255 + 0.5, 0, 255).astype(np.uint8)


def depth_model():
    global _depth
    if _depth is None:
        import torch
        from transformers import AutoImageProcessor, AutoModelForDepthEstimation
        torch.set_num_threads(int(os.environ.get("THREADS", "4")))
        name = "depth-anything/Depth-Anything-V2-Small-hf"
        _depth = (AutoImageProcessor.from_pretrained(name), AutoModelForDepthEstimation.from_pretrained(name).eval())
    return _depth


def depth(rgb):
    import torch
    proc, model = depth_model()
    im = Image.fromarray(rgb)
    s = 518 / max(im.size)
    small = im.resize((max(14, int(im.width * s)), max(14, int(im.height * s))), Image.BICUBIC)
    inp = proc(images=small, return_tensors="pt")
    with torch.no_grad():
        pred = model(**inp).predicted_depth[0].numpy()  # relative inverse depth: high = near
    d = np.asarray(Image.fromarray(pred.astype(np.float32)).resize(im.size, Image.BICUBIC))
    lo, hi = np.percentile(d, 1), np.percentile(d, 99)
    d = np.clip((d - lo) / max(1e-6, hi - lo), 0, 1)
    return d


def fill_outside(rgb, mask):
    """Replace pixels outside the panel mask (neighbour slivers / gutter) by
    nearest inside pixel, so slanted cuts don't show other panels."""
    if mask.all():
        return rgb
    idx = ndi.distance_transform_edt(~mask, return_distances=False, return_indices=True)
    out = rgb[idx[0], idx[1]]
    # soften the extension
    blur = np.stack([ndi.gaussian_filter(out[..., c].astype(np.float32), 6) for c in range(3)], -1)
    m = ndi.gaussian_filter(mask.astype(np.float32), 2)[..., None]
    return (rgb * m + blur * (1 - m)).astype(np.uint8)


def main():
    os.makedirs(HD, exist_ok=True)
    panels = json.load(open(os.path.join(ROOT, "build", "panels.json")))
    pages = sys.argv[1:] or sorted(panels)
    for page in pages:
        src = os.path.join(ROOT, "build", "clean", page + ".png")
        if not os.path.exists(src):
            src = os.path.join(ROOT, "pages", page + ".jpg")
        img = np.asarray(Image.open(src).convert("RGB"))
        for k, p in enumerate(panels[page]["panels"], start=1):
            pid = p["id"]
            outp = os.path.join(HD, pid + ".png")
            if os.path.exists(outp) and os.path.exists(os.path.join(HD, pid + "_depth.png")):
                continue
            x0, y0, x1, y1 = p["bbox"]
            crop = img[y0:y1, x0:x1]
            mpath = os.path.join(ROOT, "build", "panels", page, f"p{k:02d}_mask.png")
            mask = np.asarray(Image.open(mpath)) > 127
            # erode mask slightly to drop the black border line of the panel
            mask = ndi.binary_erosion(mask, iterations=4)
            crop = fill_outside(crop, mask)
            # trim 4px border (panel frame line)
            crop = crop[4:-4, 4:-4] if min(crop.shape[:2]) > 40 else crop
            up = upscale(crop)
            if max(up.shape[:2]) > MAX_SIDE:
                s = MAX_SIDE / max(up.shape[:2])
                up = np.asarray(Image.fromarray(up).resize((int(up.shape[1] * s), int(up.shape[0] * s)), Image.LANCZOS))
            Image.fromarray(up).save(outp)
            d = depth(up)
            Image.fromarray((d * 65535).astype(np.uint16)).save(os.path.join(HD, pid + "_depth.png"))
            print(pid, crop.shape[:2], "->", up.shape[:2], flush=True)


if __name__ == "__main__":
    main()
