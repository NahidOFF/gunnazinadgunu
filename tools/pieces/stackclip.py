#!/usr/bin/env python3
"""Stack a short clip's frames over one region and blow it up.

Reading the props in this video is limited by noise, not by resolution: any one
1080p frame puts only a couple of pixels on each pen stroke. Averaging many
frames of the same shot, registered to sub-pixel accuracy first, is what makes
them legible.

  stackclip.py CLIP.mp4 --roi X0 Y0 X1 Y1 [--from 11.9] [--to 12.4]
               [--scale 6] [--out OUT.png] [--min-cc 0.90]

Registration is ECC (Euclidean); frames whose correlation falls below --min-cc
are dropped rather than smeared into the average. The result gets CLAHE on L and
a light unsharp pass, which is what made the desk notes and the cabinet stickies
readable.
"""
import argparse, glob, os, shutil, subprocess, sys, tempfile
import cv2, numpy as np

FFMPEG = "/usr/local/lib/python3.11/dist-packages/imageio_ffmpeg/binaries/ffmpeg-linux-x86_64-v7.0.2"


def extract(clip, t0, t1, into):
    cmd = [FFMPEG, "-v", "error", "-y"]
    if t0 is not None:
        cmd += ["-ss", str(t0)]
    if t1 is not None:
        cmd += ["-to", str(t1)]
    cmd += ["-i", clip, "-vsync", "0", os.path.join(into, "%05d.png")]
    subprocess.run(cmd, check=True)
    return sorted(glob.glob(os.path.join(into, "*.png")))


def stack(frames, roi, min_cc):
    x0, y0, x1, y1 = roi
    ref = cv2.imread(frames[0])[y0:y1, x0:x1].astype(np.float32)
    refg = cv2.cvtColor(ref.astype(np.uint8), cv2.COLOR_BGR2GRAY)
    acc, n, dropped = ref.copy(), 1, 0
    for f in frames[1:]:
        im = cv2.imread(f)[y0:y1, x0:x1].astype(np.float32)
        g = cv2.cvtColor(im.astype(np.uint8), cv2.COLOR_BGR2GRAY)
        W = np.eye(2, 3, dtype=np.float32)
        try:
            cc, W = cv2.findTransformECC(
                refg, g, W, cv2.MOTION_EUCLIDEAN,
                (cv2.TERM_CRITERIA_EPS | cv2.TERM_CRITERIA_COUNT, 200, 1e-6), None, 3)
        except cv2.error:
            dropped += 1
            continue
        if cc < min_cc:
            dropped += 1
            continue
        acc += cv2.warpAffine(im, W, (im.shape[1], im.shape[0]),
                              flags=cv2.INTER_CUBIC + cv2.WARP_INVERSE_MAP)
        n += 1
    return (acc / n).astype(np.uint8), n, dropped


def enhance(img, scale):
    big = cv2.resize(img, None, fx=scale, fy=scale, interpolation=cv2.INTER_CUBIC)
    lab = cv2.cvtColor(big, cv2.COLOR_BGR2LAB)
    l, a, b = cv2.split(lab)
    l = cv2.createCLAHE(clipLimit=3.0, tileGridSize=(8, 8)).apply(l)
    big = cv2.cvtColor(cv2.merge([l, a, b]), cv2.COLOR_LAB2BGR)
    k = np.array([[0, -1, 0], [-1, 5, -1], [0, -1, 0]], np.float32)
    return cv2.filter2D(big, -1, k)


def main():
    p = argparse.ArgumentParser()
    p.add_argument("clip")
    p.add_argument("--roi", nargs=4, type=int, required=True, metavar=("X0", "Y0", "X1", "Y1"))
    p.add_argument("--from", dest="t0", type=float, default=None)
    p.add_argument("--to", dest="t1", type=float, default=None)
    p.add_argument("--scale", type=int, default=6)
    p.add_argument("--min-cc", type=float, default=0.90)
    p.add_argument("--out", default="stacked.png")
    a = p.parse_args()

    tmp = tempfile.mkdtemp(prefix="stackclip_")
    try:
        frames = extract(a.clip, a.t0, a.t1, tmp)
        if not frames:
            sys.exit("no frames in that range")
        img, n, dropped = stack(frames, a.roi, a.min_cc)
        cv2.imwrite(a.out, enhance(img, a.scale))
        print("%s  frames=%d used=%d dropped=%d" % (a.out, len(frames), n, dropped))
    finally:
        shutil.rmtree(tmp, ignore_errors=True)


if __name__ == "__main__":
    main()
