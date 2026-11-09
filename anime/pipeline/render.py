"""Anime compositor: turns build/timeline.json into video frames.

Per shot: an HD panel (upscaled, text-free) with depth map and optional
fg/bg layer split. A virtual camera (center/zoom/rotation, eased) frames a
16:9 view; 2.5D parallax moves the foreground layer more than the background
(or depth-displaces pixels when there is no split). Foreground "acting":
lunge / slide / breathe / shake. Effects: rain, speed lines, impact frames,
flashes, energy glow + crackle, particles, chromatic aberration, shake, bloom,
grain, vignette. Turkish subtitles are drawn in (cached text sprites).

Usage: python3 render.py <timeline.json> <out.mp4> [--from F --to F] [--preview]
"""
import argparse
import json
import math
import os
import subprocess
import sys

import cv2
import numpy as np
from PIL import Image, ImageDraw, ImageFont

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
HD = os.path.join(ROOT, "build", "hd")
LAYERS = os.path.join(ROOT, "build", "layers")
FONTS = os.path.join(ROOT, "build", "fonts")

cv2.setNumThreads(1)


# ----------------------------------------------------------------- helpers
def ease(x, kind="inout"):
    x = min(1.0, max(0.0, x))
    if kind == "linear":
        return x
    if kind == "in":
        return x * x * x
    if kind == "out":
        return 1 - (1 - x) ** 3
    if kind == "expo":  # fast start, long settle (anime camera snap)
        return 1 - 2 ** (-10 * x) if x < 1 else 1.0
    return 3 * x * x - 2 * x * x * x if kind == "smooth" else (4 * x ** 3 if x < 0.5 else 1 - (-2 * x + 2) ** 3 / 2)


def lerp(a, b, t):
    return a + (b - a) * t


def lerpv(a, b, t):
    return [lerp(x, y, t) for x, y in zip(a, b)]


def hash_noise(seed, t, freq=12.0):
    """smooth-ish deterministic noise in [-1,1]"""
    x = t * freq
    i = math.floor(x)
    f = x - i

    def r(k):
        v = math.sin((k + seed * 101.3) * 12.9898) * 43758.5453
        return (v - math.floor(v)) * 2 - 1
    u = f * f * (3 - 2 * f)
    return r(i) * (1 - u) + r(i + 1) * u


def window(t, t0, t1, fade=0.08):
    if t < t0 or t > t1:
        return 0.0
    a = min(1.0, (t - t0) / fade) if fade > 0 else 1.0
    b = min(1.0, (t1 - t) / fade) if fade > 0 else 1.0
    return max(0.0, min(a, b))


# ----------------------------------------------------------------- assets
class Panel:
    cache = {}

    @classmethod
    def get(cls, pid):
        if pid not in cls.cache:
            if len(cls.cache) > 6:
                cls.cache.pop(next(iter(cls.cache)))
            cls.cache[pid] = Panel(pid)
        return cls.cache[pid]

    def __init__(self, pid):
        self.pid = pid
        self.img = cv2.cvtColor(cv2.imread(os.path.join(HD, pid + ".png"), cv2.IMREAD_COLOR), cv2.COLOR_BGR2RGB)
        d = cv2.imread(os.path.join(HD, pid + "_depth.png"), cv2.IMREAD_UNCHANGED)
        self.depth = d.astype(np.float32) / 65535.0 if d is not None else np.full(self.img.shape[:2], 0.5, np.float32)
        self.h, self.w = self.img.shape[:2]
        fgp, bgp = os.path.join(LAYERS, pid + "_fg.png"), os.path.join(LAYERS, pid + "_bg.png")
        self.split = os.path.exists(fgp) and os.path.exists(bgp)
        if self.split:
            fg = cv2.imread(fgp, cv2.IMREAD_UNCHANGED)
            self.fg = cv2.cvtColor(fg[..., :3], cv2.COLOR_BGR2RGB)
            self.fga = fg[..., 3]
            self.bg = cv2.cvtColor(cv2.imread(bgp, cv2.IMREAD_COLOR), cv2.COLOR_BGR2RGB)
            ys, xs = np.nonzero(self.fga > 128)
            self.fg_anchor = (float(xs.mean()), float(ys.max())) if len(xs) else (self.w / 2, self.h)
        # energy key masks (hue based) at panel resolution, used for glow
        hsv = cv2.cvtColor(self.img, cv2.COLOR_RGB2HSV)
        hch, s, v = hsv[..., 0].astype(np.int16), hsv[..., 1], hsv[..., 2]
        self.key_blue = ((hch > 95) & (hch < 125) & (s > 110) & (v > 150)).astype(np.uint8) * 255
        self.key_green = ((hch > 35) & (hch < 85) & (s > 110) & (v > 140)).astype(np.uint8) * 255


def fit_view(pw, ph, W, H):
    """largest W:H rect inside the panel (cover fit) -> width in panel px"""
    ar = W / H
    return min(pw, ph * ar)


# ----------------------------------------------------------------- overlays
class Overlays:
    def __init__(self, W, H, seed=7):
        self.W, self.H = W, H
        rng = np.random.default_rng(seed)
        # rain tiles: 3 layers
        self.rain = []
        for k, (n, ln, th, a) in enumerate([(900, 40, 1, 0.35), (500, 80, 2, 0.45), (140, 170, 3, 0.55)]):
            T = 1024
            tile = np.zeros((T, T), np.uint8)
            for _ in range(n):
                x, y = rng.integers(0, T, 2)
                l = int(ln * rng.uniform(0.6, 1.3))
                cv2.line(tile, (int(x), int(y)), (int(x), int(y + l)), int(255 * a * rng.uniform(0.5, 1)), th, cv2.LINE_AA)
            tile = cv2.GaussianBlur(tile, (0, 0), 0.6 + k * 0.5)
            self.rain.append(tile)
        # speed line variants (radial) as alpha masks
        self.speed = []
        cx, cy = W // 2, H // 2
        R = int(math.hypot(W, H))
        for v in range(4):
            m = np.zeros((H, W), np.uint8)
            for _ in range(140):
                ang = rng.uniform(0, 2 * math.pi)
                r0 = rng.uniform(0.33, 0.55) * min(W, H)
                wdt = rng.uniform(0.004, 0.02)
                p0 = (cx + math.cos(ang) * r0, cy + math.sin(ang) * r0)
                pts = np.array([[cx + math.cos(ang - wdt) * R, cy + math.sin(ang - wdt) * R],
                                [cx + math.cos(ang + wdt) * R, cy + math.sin(ang + wdt) * R], p0], np.int32)
                cv2.fillConvexPoly(m, pts, 255, cv2.LINE_AA)
            self.speed.append(cv2.GaussianBlur(m, (0, 0), 1.0))
        # parallel speed lines (horizontal) for dash shots
        self.hlines = []
        for v in range(4):
            m = np.zeros((H, W), np.uint8)
            for _ in range(70):
                y = int(rng.uniform(0, H))
                x0 = int(rng.uniform(-W * 0.2, W * 0.8))
                l = int(rng.uniform(W * 0.2, W * 0.7))
                cv2.line(m, (x0, y), (x0 + l, y), int(rng.uniform(120, 255)), int(rng.uniform(1, 5)), cv2.LINE_AA)
            self.hlines.append(cv2.GaussianBlur(m, (0, 0), 0.8))
        self.grain = [rng.normal(0, 1, (H // 2, W // 2)).astype(np.float32) for _ in range(6)]
        yy, xx = np.mgrid[0:H, 0:W].astype(np.float32)
        d = np.sqrt(((xx - W / 2) / (W / 2)) ** 2 + ((yy - H / 2) / (H / 2)) ** 2)
        self.vignette = np.clip(1 - 0.32 * np.clip(d - 0.55, 0, None) ** 1.6, 0, 1)[..., None].astype(np.float32)


def rain_layer(ov, t, angle_deg, speed, alpha):
    W, H = ov.W, ov.H
    acc = np.zeros((H, W), np.float32)
    for k, tile in enumerate(ov.rain):
        sp = speed * (0.6 + 0.5 * k)
        T = tile.shape[0]
        off = (t * sp * 60 * (1 + k)) % T
        a = math.radians(angle_deg)
        M = cv2.getRotationMatrix2D((T / 2, T / 2), angle_deg, 1.0)
        M[0, 2] += math.sin(a) * off
        M[1, 2] += math.cos(a) * off
        rot = cv2.warpAffine(tile, M, (T, T), borderMode=cv2.BORDER_WRAP)
        reps = (math.ceil(H / T), math.ceil(W / T))
        big = np.tile(rot, reps)[:H, :W]
        acc += big.astype(np.float32) / 255.0 * (0.55 + 0.25 * k)
    return np.clip(acc * alpha, 0, 1)


# ----------------------------------------------------------------- subtitles
class Subs:
    def __init__(self, W, H):
        self.W, self.H = W, H
        self.font = ImageFont.truetype(os.path.join(FONTS, "Noto_Sans_wght_800.ttf"), int(H * 0.046))
        self.font_i = ImageFont.truetype(os.path.join(FONTS, "Noto_Sans_wght_600.ttf"), int(H * 0.042))
        self.cache = {}

    def wrap(self, text, font, maxw):
        words, lines, cur = text.split(), [], ""
        for w in words:
            test = (cur + " " + w).strip()
            if font.getlength(test) <= maxw or not cur:
                cur = test
            else:
                lines.append(cur)
                cur = w
        if cur:
            lines.append(cur)
        return lines

    def sprite(self, text, style):
        key = (text, style)
        if key in self.cache:
            return self.cache[key]
        font = self.font_i if style in ("thought", "narration") else self.font
        lines = self.wrap(text, font, self.W * 0.78)
        lh = int(font.size * 1.28)
        w = int(max(font.getlength(l) for l in lines)) + 40
        h = lh * len(lines) + 30
        im = Image.new("RGBA", (w, h), (0, 0, 0, 0))
        d = ImageDraw.Draw(im)
        fill = {"thought": (200, 225, 255, 255), "narration": (255, 236, 170, 255)}.get(style, (255, 255, 255, 255))
        for i, l in enumerate(lines):
            lw = font.getlength(l)
            d.text(((w - lw) / 2, 12 + i * lh), l, font=font, fill=fill, stroke_width=max(3, font.size // 11), stroke_fill=(0, 0, 0, 255))
        arr = np.asarray(im).astype(np.float32) / 255.0
        # soft drop shadow
        sh = cv2.GaussianBlur(arr[..., 3], (0, 0), 3) * 0.6
        self.cache[key] = (arr, sh)
        return self.cache[key]

    def draw(self, frame, text, style, alpha, top=False):
        arr, sh = self.sprite(text, style)
        h, w = arr.shape[:2]
        x = (self.W - w) // 2
        y = int(self.H * 0.06) if top else int(self.H * 0.955) - h
        reg = frame[y:y + h, x:x + w]
        a = arr[..., 3:4] * alpha
        s = sh[..., None] * alpha
        reg[:] = reg * (1 - s) * (1 - a) + arr[..., :3] * a
        return frame


# ----------------------------------------------------------------- shot render
class Renderer:
    def __init__(self, tl):
        self.tl = tl
        self.W, self.H, self.fps = tl["width"], tl["height"], tl["fps"]
        self.ov = Overlays(self.W, self.H)
        self.subs = Subs(self.W, self.H)
        yy, xx = np.mgrid[0:self.H, 0:self.W].astype(np.float32)
        self.gx, self.gy = xx - self.W / 2, yy - self.H / 2

    # camera state for a shot at local time t
    def camera(self, sh, t):
        dur = max(1e-3, sh["dur"])
        cam = sh.get("cam", {})
        p = ease(t / dur, cam.get("ease", "inout"))
        c0 = cam.get("from", [0.5, 0.5, 1.0])
        c1 = cam.get("to", c0)
        cx, cy, z = lerpv(c0, c1, p)
        rot = lerp(*(cam.get("rot", [0, 0])), p)
        # zoom punches
        for fx in sh.get("fx", []):
            if fx["type"] == "zoompunch":
                dt = t - fx["t"]
                if 0 <= dt < 0.5:
                    z *= 1 + fx.get("amt", 0.08) * math.exp(-dt * 9) * (1 if dt > 0.03 else dt / 0.03)
        # shake (camera space, px)
        sx = sy = 0.0
        for fx in sh.get("fx", []):
            if fx["type"] == "shake":
                w = window(t, fx["t0"], fx["t1"], 0.0)
                if w > 0:
                    decay = math.exp(-(t - fx["t0"]) * fx.get("decay", 3.0))
                    amp = fx.get("amp", 18) * decay
                    sx += hash_noise(1, t, fx.get("freq", 22)) * amp
                    sy += hash_noise(2, t, fx.get("freq", 22)) * amp
        # idle handheld drift so nothing is ever frozen
        hh = cam.get("drift", 0.6)
        sx += hash_noise(5, t, 0.7) * 3 * hh
        sy += hash_noise(6, t, 0.6) * 2 * hh
        return cx, cy, z, rot, sx, sy

    def affine(self, P, cx, cy, z, rot, sx, sy, extra_scale=1.0):
        """matrix mapping output px -> panel px"""
        vw = fit_view(P.w, P.h, self.W, self.H) / max(0.05, z) / extra_scale
        s = vw / self.W
        # clamp center so view stays inside panel (allow a bit of overscan)
        vh = vw * self.H / self.W
        X = cx * P.w
        Y = cy * P.h
        if vw <= P.w:
            X = min(max(X, vw / 2), P.w - vw / 2)
        if vh <= P.h:
            Y = min(max(Y, vh / 2), P.h - vh / 2)
        a = math.radians(rot)
        ca, sa = math.cos(a) * s, math.sin(a) * s
        # src = [ca -sa; sa ca] * (out - center) + (X,Y) ; shake in output px
        M = np.array([[ca, -sa, X - ca * (self.W / 2 + sx) + sa * (self.H / 2 + sy)],
                      [sa, ca, Y - sa * (self.W / 2 + sx) - ca * (self.H / 2 + sy)]], np.float32)
        return M

    def render_shot(self, sh, t):
        W, H = self.W, self.H
        kind = sh.get("kind", "panel")
        if kind == "black":
            return np.zeros((H, W, 3), np.float32)
        if kind == "card":
            return self.render_card(sh, t)
        P = Panel.get(sh["panel"])
        cx, cy, z, rot, sx, sy = self.camera(sh, t)
        mot = sh.get("motion", {})
        dur = max(1e-3, sh["dur"])
        par = mot.get("parallax", 0.25)
        cam0 = sh.get("cam", {}).get("from", [0.5, 0.5, 1.0])
        flags = cv2.INTER_LINEAR | cv2.WARP_INVERSE_MAP
        if P.split and mot.get("layers", True):
            Mb = self.affine(P, cx, cy, z, rot, sx, sy)
            bg = cv2.warpAffine(P.bg, Mb, (W, H), flags=flags, borderMode=cv2.BORDER_REFLECT)
            # foreground: extra parallax + acting
            fcx = cam0[0] + (cx - cam0[0]) * (1 + par)
            fcy = cam0[1] + (cy - cam0[1]) * (1 + par)
            fz = z * (1 + par * 0.6 * (z / max(1e-3, cam0[2]) - 1))
            Mf = self.affine(P, fcx, fcy, fz, rot, sx * 1.15, sy * 1.15)
            # acting transform in panel space around anchor
            act = self.acting(sh, t, P)
            if act is not None:
                A = np.vstack([act, [0, 0, 1]])
                Mf = (np.linalg.inv(A) @ np.vstack([Mf, [0, 0, 1]]))[:2].astype(np.float32)
            fg = cv2.warpAffine(P.fg, Mf, (W, H), flags=flags, borderMode=cv2.BORDER_REFLECT)
            fa = cv2.warpAffine(P.fga, Mf, (W, H), flags=flags, borderMode=cv2.BORDER_CONSTANT, borderValue=0)
            blur = self.motion_blur_amount(sh, t)
            if blur > 1.5:
                k = int(blur) | 1
                ker = np.zeros((k, k), np.float32)
                ang = mot.get("blur_angle", 0)
                cv2.line(ker, (k // 2 - int(math.cos(math.radians(ang)) * k / 2), k // 2 - int(math.sin(math.radians(ang)) * k / 2)),
                         (k // 2 + int(math.cos(math.radians(ang)) * k / 2), k // 2 + int(math.sin(math.radians(ang)) * k / 2)), 1.0, 1)
                ker /= max(1e-6, ker.sum())
                fg = cv2.filter2D(fg, -1, ker)
                fa = cv2.filter2D(fa, -1, ker)
            a = fa.astype(np.float32)[..., None] / 255.0
            out = bg.astype(np.float32) * (1 - a) + fg.astype(np.float32) * a
            frame = out / 255.0
        else:
            M = self.affine(P, cx, cy, z, rot, sx, sy)
            if par > 0 and mot.get("depth_warp", True):
                # depth displacement: near pixels shift with camera motion
                mapx = M[0, 0] * (self.gx + W / 2) + M[0, 1] * (self.gy + H / 2) + M[0, 2]
                mapy = M[1, 0] * (self.gx + W / 2) + M[1, 1] * (self.gy + H / 2) + M[1, 2]
                d = cv2.remap(P.depth, mapx, mapy, cv2.INTER_LINEAR, borderMode=cv2.BORDER_REFLECT)
                vw = fit_view(P.w, P.h, W, H) / max(0.05, z)
                dx = (cx - cam0[0]) * P.w * par + hash_noise(9, t, 0.35) * vw * 0.004 * mot.get("breathe_bg", 1)
                dy = (cy - cam0[1]) * P.h * par
                dz = (z / max(1e-3, cam0[2]) - 1) * par
                off = (d - 0.5)
                mapx = mapx - dx * off - (mapx - cx * P.w) * dz * off
                mapy = mapy - dy * off - (mapy - cy * P.h) * dz * off
                frame = cv2.remap(P.img, mapx, mapy, cv2.INTER_LINEAR, borderMode=cv2.BORDER_REFLECT).astype(np.float32) / 255.0
            else:
                frame = cv2.warpAffine(P.img, M, (W, H), flags=flags, borderMode=cv2.BORDER_REFLECT).astype(np.float32) / 255.0
        frame = self.apply_fx(frame, sh, t, P, (cx, cy, z, rot, sx, sy))
        return frame

    def acting(self, sh, t, P):
        mot = sh.get("motion", {})
        dur = max(1e-3, sh["dur"])
        ax, ay = P.fg_anchor
        tx = ty = 0.0
        sc = 1.0
        r = 0.0
        if "fg" in mot:  # keyframed move: from/to [dx, dy, scale] in panel-width fractions
            f = mot["fg"]
            t0, t1 = f.get("t0", 0), f.get("t1", dur)
            p = ease((t - t0) / max(1e-3, t1 - t0), f.get("ease", "out"))
            a0, a1 = f.get("from", [0, 0, 1]), f.get("to", [0, 0, 1])
            dx, dy, s = lerpv(a0, a1, p)
            tx += dx * P.w
            ty += dy * P.w
            sc *= s
        if mot.get("breathe", 0):
            sc *= 1 + mot["breathe"] * math.sin(2 * math.pi * t / mot.get("breathe_period", 2.6))
        if mot.get("tremble", 0):
            tx += hash_noise(11, t, 18) * mot["tremble"] * P.w
            ty += hash_noise(12, t, 18) * mot["tremble"] * P.w
        if mot.get("sway", 0):
            r += mot["sway"] * math.sin(2 * math.pi * t / 3.1)
        for fx in sh.get("fx", []):  # recoil on hit: quick shove then settle
            if fx["type"] == "recoil":
                dt = t - fx["t"]
                if dt >= 0:
                    k = math.exp(-dt * 7) * math.sin(min(dt * 25, math.pi / 2))
                    tx += fx.get("dx", -0.03) * P.w * k
                    ty += fx.get("dy", 0.0) * P.w * k
        if tx == 0 and ty == 0 and sc == 1 and r == 0:
            return None
        M = cv2.getRotationMatrix2D((ax, ay), r, sc)
        M[0, 2] += tx
        M[1, 2] += ty
        return M.astype(np.float32)

    def motion_blur_amount(self, sh, t):
        mot = sh.get("motion", {})
        if "fg" not in mot:
            return 0
        f = mot["fg"]
        dur = sh["dur"]
        t0, t1 = f.get("t0", 0), f.get("t1", dur)
        if not (t0 <= t <= t1):
            return 0
        a0, a1 = f.get("from", [0, 0, 1]), f.get("to", [0, 0, 1])
        dist = math.hypot(a1[0] - a0[0], a1[1] - a0[1]) * self.W
        dt = 1 / self.fps
        e = f.get("ease", "out")
        p0 = ease((t - t0) / max(1e-3, t1 - t0), e)
        p1 = ease((t + dt - t0) / max(1e-3, t1 - t0), e)
        return min(45, abs(p1 - p0) * dist * f.get("blur", 1.0))

    def render_card(self, sh, t):
        W, H = self.W, self.H
        img = Image.new("RGB", (W, H), tuple(sh.get("bgcolor", [8, 8, 14])))
        d = ImageDraw.Draw(img)
        for i, item in enumerate(sh.get("texts", [])):
            font = ImageFont.truetype(os.path.join(FONTS, item.get("font", "Noto_Serif_JP_wght_900.ttf")), int(H * item.get("size", 0.1)))
            txt = item["text"]
            tw = font.getlength(txt)
            y = int(H * item.get("y", 0.45))
            d.text(((W - tw) / 2, y), txt, font=font, fill=tuple(item.get("color", [240, 240, 240])),
                   stroke_width=item.get("stroke", 0), stroke_fill=(0, 0, 0))
        frame = np.asarray(img).astype(np.float32) / 255.0
        return self.apply_fx(frame, sh, t, None, None)

    # ------------------------------------------------------------- effects
    def apply_fx(self, frame, sh, t, P, cam):
        W, H = self.W, self.H
        for fx in sh.get("fx", []):
            ty = fx["type"]
            if ty == "glow" and P is not None:
                small = cv2.resize(frame, (W // 4, H // 4), interpolation=cv2.INTER_AREA)
                hsv = cv2.cvtColor((small * 255).astype(np.uint8), cv2.COLOR_RGB2HSV)
                hch, s, v = hsv[..., 0].astype(np.int16), hsv[..., 1], hsv[..., 2]
                if fx.get("color", "blue") == "blue":
                    m = ((hch > 95) & (hch < 128) & (s > 90) & (v > 120)).astype(np.float32)
                    col = np.array([0.35, 0.6, 1.0], np.float32)
                elif fx["color"] == "green":
                    m = ((hch > 35) & (hch < 85) & (s > 90) & (v > 120)).astype(np.float32)
                    col = np.array([0.45, 1.0, 0.4], np.float32)
                else:
                    m = ((v > 238) & (s < 60)).astype(np.float32) * 0.5
                    col = np.array([0.8, 0.85, 1.0], np.float32)
                g = cv2.GaussianBlur(m, (0, 0), 6) * 1.2 + cv2.GaussianBlur(m, (0, 0), 18) * 1.6
                g = cv2.resize(g, (W, H), interpolation=cv2.INTER_LINEAR)
                pulse = 0.75 + 0.25 * math.sin(t * fx.get("rate", 7)) + 0.15 * hash_noise(3, t, 14)
                amt = fx.get("amt", 0.5) * pulse * window(t, fx.get("t0", 0), fx.get("t1", 1e9), 0.2)
                frame = frame + g[..., None] * col * amt
            elif ty == "crackle":
                w = window(t, fx.get("t0", 0), fx.get("t1", 1e9), 0.05)
                if w > 0:
                    frame = self.crackle(frame, t, fx, w)
            elif ty == "particles":
                frame = self.particles(frame, t, fx)
        # rain
        rain = sh.get("rain")
        if rain:
            r = rain_layer(self.ov, t + sh.get("start", 0), rain.get("angle", 18), rain.get("speed", 1.0), rain.get("alpha", 0.5))
            tint = np.array(rain.get("color", [0.85, 0.88, 1.0]), np.float32)
            frame = frame * (1 - r[..., None] * 0.35) + r[..., None] * tint * 0.8
        for fx in sh.get("fx", []):
            ty = fx["type"]
            if ty == "speedlines":
                w = window(t, fx.get("t0", 0), fx.get("t1", 1e9), 0.05)
                if w > 0:
                    idx = int(t * self.fps / 2) % 4
                    m = (self.ov.hlines if fx.get("mode") == "horizontal" else self.ov.speed)[idx].astype(np.float32) / 255.0
                    if fx.get("mode") == "horizontal" and fx.get("angle", 0):
                        Mr = cv2.getRotationMatrix2D((W / 2, H / 2), fx["angle"], 1.3)
                        m = cv2.warpAffine(m, Mr, (W, H))
                    if fx.get("center") and fx.get("mode") != "horizontal":
                        cxp, cyp = fx["center"]
                        Mt = np.float32([[1, 0, (cxp - 0.5) * W], [0, 1, (cyp - 0.5) * H]])
                        m = cv2.warpAffine(m, Mt, (W, H), borderMode=cv2.BORDER_REFLECT)
                    col = np.array(fx.get("color", [1, 1, 1]), np.float32)
                    a = (m * fx.get("amt", 0.75) * w)[..., None]
                    frame = frame * (1 - a) + col * a
            elif ty == "chroma":
                w = window(t, fx.get("t0", 0), fx.get("t1", 1e9), 0.05)
                if w > 0:
                    sft = fx.get("amt", 6) * w
                    Mr = np.float32([[1 + sft / W, 0, -sft / 2], [0, 1 + sft / W, -sft * H / W / 2]])
                    Mb = np.float32([[1 - sft / W, 0, sft / 2], [0, 1 - sft / W, sft * H / W / 2]])
                    frame[..., 0] = cv2.warpAffine(frame[..., 0], Mr, (W, H), borderMode=cv2.BORDER_REFLECT)
                    frame[..., 2] = cv2.warpAffine(frame[..., 2], Mb, (W, H), borderMode=cv2.BORDER_REFLECT)
            elif ty == "impact":  # anime impact frame: inverted high-contrast mono
                if fx["t"] <= t < fx["t"] + fx.get("dur", 0.125):
                    g = frame.mean(axis=2)
                    g = np.clip((g - 0.5) * 3.0 + 0.5, 0, 1)
                    phase = int((t - fx["t"]) * self.fps) % 2
                    g = 1 - g if phase == 0 else g
                    col = np.array(fx.get("color", [1, 1, 1]), np.float32)
                    frame = g[..., None] * col
            elif ty == "flash":
                dt = t - fx["t"]
                d = fx.get("dur", 0.25)
                if 0 <= dt < d:
                    a = (1 - dt / d) ** 2 * fx.get("amt", 0.9)
                    frame = frame * (1 - a) + np.array(fx.get("color", [1, 1, 1]), np.float32) * a
            elif ty == "tint":
                w = window(t, fx.get("t0", 0), fx.get("t1", 1e9), fx.get("fade", 0.3))
                col = np.array(fx["color"], np.float32)
                frame = frame * (1 - fx.get("amt", 0.3) * w) + frame * col * fx.get("amt", 0.3) * w
            elif ty == "darken":
                w = window(t, fx.get("t0", 0), fx.get("t1", 1e9), fx.get("fade", 0.3))
                frame = frame * (1 - fx.get("amt", 0.4) * w)
            elif ty == "fade":
                dur = sh["dur"]
                if fx.get("dir", "in") == "in":
                    a = 1 - min(1, t / fx.get("dur", 0.6))
                else:
                    a = min(1, max(0, (t - (dur - fx.get("dur", 0.6))) / fx.get("dur", 0.6)))
                frame = frame * (1 - a) + np.array(fx.get("color", [0, 0, 0]), np.float32) * a
            elif ty == "desat":
                w = window(t, fx.get("t0", 0), fx.get("t1", 1e9), 0.3)
                g = frame.mean(axis=2, keepdims=True)
                frame = frame * (1 - fx.get("amt", 0.6) * w) + g * fx.get("amt", 0.6) * w
            elif ty == "blur":
                w = window(t, fx.get("t0", 0), fx.get("t1", 1e9), fx.get("fade", 0.1))
                if w > 0.02:
                    k = fx.get("amt", 12) * w
                    frame = cv2.GaussianBlur(frame, (0, 0), k)
        return frame

    def crackle(self, frame, t, fx, w):
        W, H = self.W, self.H
        layer = np.zeros((H // 2, W // 2), np.float32)
        seed = int(t * self.fps / 2)  # animate on twos
        rng = np.random.default_rng(seed * 31 + fx.get("seed", 0))
        reg = fx.get("region", [0, 0, 1, 1])
        for _ in range(fx.get("n", 5)):
            x = rng.uniform(reg[0], reg[2]) * W / 2
            y = rng.uniform(reg[1], reg[3]) * H / 2
            pts = [(x, y)]
            ang = rng.uniform(0, 2 * math.pi)
            for _ in range(rng.integers(4, 9)):
                ang += rng.uniform(-0.9, 0.9)
                ln = rng.uniform(8, 30)
                x += math.cos(ang) * ln
                y += math.sin(ang) * ln
                pts.append((x, y))
            cv2.polylines(layer, [np.array(pts, np.int32)], False, 1.0, 1, cv2.LINE_AA)
        glow = cv2.GaussianBlur(layer, (0, 0), 4) * 2.5 + layer
        glow = cv2.resize(glow, (W, H))
        col = np.array(fx.get("color", [0.5, 0.75, 1.0]), np.float32)
        return frame + glow[..., None] * col * w * fx.get("amt", 0.8)

    def particles(self, frame, t, fx):
        W, H = self.W, self.H
        w = window(t, fx.get("t0", 0), fx.get("t1", 1e9), 0.2)
        if w <= 0:
            return frame
        rng = np.random.default_rng(fx.get("seed", 1))
        n = fx.get("n", 60)
        kind = fx.get("kind", "embers")
        p0 = rng.uniform(0, 1, (n, 2)) * [W, H]
        v = rng.normal(0, 1, (n, 2)) * fx.get("spread", 40)
        v += np.array(fx.get("vel", [0, -60]))
        life = rng.uniform(1.0, 3.0, n)
        layer = np.zeros((H, W), np.float32)
        tt = (t - fx.get("t0", 0)) % 3.0
        for i in range(n):
            age = (tt + i * 0.13) % life[i]
            x, y = p0[i] + v[i] * age + np.array([0, fx.get("grav", 0)]) * age * age
            x %= W
            y %= H
            a = math.sin(math.pi * age / life[i])
            if kind == "leaves":
                cv2.ellipse(layer, (int(x), int(y)), (7, 3), (t * 200 + i * 40) % 360, 0, 360, a, -1, cv2.LINE_AA)
            elif kind == "debris":
                cv2.circle(layer, (int(x), int(y)), 2 + i % 4, a, -1, cv2.LINE_AA)
            else:
                cv2.circle(layer, (int(x), int(y)), 2 + (i % 3), a, -1, cv2.LINE_AA)
        if kind in ("embers", "sparks", "spirit"):
            layer = cv2.GaussianBlur(layer, (0, 0), 2) * 2 + layer
        col = np.array(fx.get("color", [1.0, 0.8, 0.4]), np.float32)
        if kind in ("leaves", "debris"):
            a = np.clip(layer, 0, 1)[..., None] * w
            return frame * (1 - a) + col * a
        return frame + layer[..., None] * col * w * fx.get("amt", 0.8)

    def grade(self, frame, fidx, look):
        # bloom
        b = look.get("bloom", 0.25)
        if b > 0:
            small = cv2.resize(frame, (self.W // 4, self.H // 4), interpolation=cv2.INTER_AREA)
            hi = np.clip(small - 0.65, 0, None)
            hi = cv2.GaussianBlur(hi, (0, 0), 6)
            frame = frame + cv2.resize(hi, (self.W, self.H)) * b * 2
        frame = frame * self.ov.vignette
        g = self.ov.grain[fidx % len(self.ov.grain)]
        g = cv2.resize(g, (self.W, self.H), interpolation=cv2.INTER_NEAREST)
        frame = frame + g[..., None] * look.get("grain", 0.012)
        return frame

    # ------------------------------------------------------------- timeline
    def frame_at(self, fidx):
        t = fidx / self.fps
        shots = self.tl["shots"]
        cur = None
        for i, sh in enumerate(shots):
            if sh["start"] <= t < sh["start"] + sh["dur"]:
                cur = i
                break
        if cur is None:
            cur = len(shots) - 1
        sh = shots[cur]
        lt = t - sh["start"]
        frame = self.render_shot(sh, lt)
        tr = sh.get("trans", {"type": "cut"})
        td = tr.get("dur", 0.0)
        if cur > 0 and tr["type"] != "cut" and lt < td:
            prev = shots[cur - 1]
            p = ease(lt / td, "inout")
            ty = tr["type"]
            if ty == "crossfade":
                pf = self.render_shot(prev, prev["dur"] + lt)
                frame = pf * (1 - p) + frame * p
            elif ty in ("white", "black", "red"):
                col = {"white": [1, 1, 1], "black": [0, 0, 0], "red": [0.6, 0, 0]}[ty]
                if lt < td / 2:
                    pf = self.render_shot(prev, prev["dur"] + lt)
                    a = lt / (td / 2)
                    frame = pf * (1 - a) + np.array(col, np.float32) * a
                else:
                    a = 1 - (lt - td / 2) / (td / 2)
                    frame = frame * (1 - a) + np.array(col, np.float32) * a
            elif ty == "whip":
                pf = self.render_shot(prev, prev["dur"] + lt)
                k = int(1 + 60 * math.sin(math.pi * p)) | 1
                ker = np.zeros((1, k), np.float32)
                ker[0, :] = 1.0 / k
                mix = pf * (1 - p) + frame * p
                frame = cv2.filter2D(mix, -1, ker)
        # subtitles
        for sub in self.tl.get("subs", []):
            if sub["t0"] - 0.12 <= t <= sub["t1"] + 0.12:
                a = min(1, (t - (sub["t0"] - 0.12)) / 0.12, ((sub["t1"] + 0.12) - t) / 0.12)
                frame = np.clip(frame, 0, 1)
                frame = self.subs.draw(frame, sub["text"], sub.get("style", "speech"), max(0, a), top=sub.get("top", False))
        frame = self.grade(frame, fidx, self.tl.get("look", {}))
        return np.clip(frame * 255 + 0.5, 0, 255).astype(np.uint8)


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("timeline")
    ap.add_argument("out")
    ap.add_argument("--from", dest="f0", type=int, default=0)
    ap.add_argument("--to", dest="f1", type=int, default=-1)
    ap.add_argument("--still", type=float, nargs="*", help="write PNG stills at these seconds instead of video")
    ap.add_argument("--crf", type=int, default=16)
    args = ap.parse_args()
    tl = json.load(open(args.timeline))
    R = Renderer(tl)
    if args.still:
        for s in args.still:
            fr = R.frame_at(int(round(s * tl["fps"])))
            Image.fromarray(fr).save(f"{args.out}_{s:07.2f}.png")
        return
    total = int(math.ceil(tl["duration"] * tl["fps"]))
    f1 = total if args.f1 < 0 else min(total, args.f1)
    cmd = ["ffmpeg", "-loglevel", "error", "-y", "-f", "rawvideo", "-pix_fmt", "rgb24", "-s", f"{R.W}x{R.H}",
           "-r", str(tl["fps"]), "-i", "-", "-c:v", "libx264", "-preset", "medium", "-crf", str(args.crf),
           "-pix_fmt", "yuv420p", "-x264-params", "threads=2", args.out]
    p = subprocess.Popen(cmd, stdin=subprocess.PIPE)
    for f in range(args.f0, f1):
        p.stdin.write(R.frame_at(f).tobytes())
        if f % 240 == 0:
            print(f"frame {f}/{f1}", flush=True)
    p.stdin.close()
    p.wait()


if __name__ == "__main__":
    main()
