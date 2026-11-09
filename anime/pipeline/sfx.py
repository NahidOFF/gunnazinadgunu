"""Procedural SFX library (48 kHz stereo float32 WAVs in build/sfx/proc/).

Every sound is synthesized from noise, oscillators and filters so it is
deterministic and license-free. Textured sounds may also get an AudioLDM2
variant (sfx_ai.py); a judge picks the better one into build/sfx/<name>.wav.
"""
import os

import numpy as np
import soundfile as sf
from scipy import signal

SR = 48000
ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
OUT = os.path.join(ROOT, "build", "sfx", "proc")
rng = np.random.default_rng(1234)


def t_(d):
    return np.arange(int(round(d * SR))) / SR


def noise(d):
    return rng.standard_normal(int(round(d * SR)))


def pink(d):
    n = int(d * SR)
    w = np.fft.rfft(rng.standard_normal(n))
    f = np.fft.rfftfreq(n, 1 / SR)
    f[0] = 1
    return np.fft.irfft(w / np.sqrt(f), n) * 30


def brown(d):
    x = np.cumsum(rng.standard_normal(int(d * SR)))
    x = signal.lfilter([1, -1], [1, -0.995], x)
    return x / (np.abs(x).max() + 1e-9)


def bp(x, lo, hi, order=2):
    b, a = signal.butter(order, [lo / (SR / 2), min(0.999, hi / (SR / 2))], "band")
    return signal.lfilter(b, a, x)


def lp(x, f, order=2):
    b, a = signal.butter(order, min(0.999, f / (SR / 2)), "low")
    return signal.lfilter(b, a, x)


def hp(x, f, order=2):
    b, a = signal.butter(order, f / (SR / 2), "high")
    return signal.lfilter(b, a, x)


def sweep_bp(x, f0, f1, q=2.0, steps=64):
    """time-varying bandpass (piecewise) from f0 to f1"""
    out = np.zeros_like(x)
    n = len(x)
    seg = n // steps + 1
    zi = None
    for i in range(steps):
        a0, a1 = i * seg, min(n, (i + 1) * seg)
        if a0 >= n:
            break
        f = f0 * (f1 / f0) ** (i / max(1, steps - 1))
        lo, hi = f / (1 + 1 / q), f * (1 + 1 / q)
        b, a = signal.butter(2, [max(20, lo) / (SR / 2), min(0.99, hi / (SR / 2))], "band")
        if zi is None or len(zi) != max(len(a), len(b)) - 1:
            zi = signal.lfilter_zi(b, a) * 0
        out[a0:a1], zi = signal.lfilter(b, a, x[a0:a1], zi=zi)
    return out


def env(d, a=0.005, decay=0.3, shape=1.0):
    t = t_(d)
    e = np.minimum(1, t / max(1e-4, a)) * np.exp(-np.maximum(0, t - a) / max(1e-4, decay)) ** shape
    return e


def adsr(d, a, s_level, r):
    t = t_(d)
    e = np.minimum(1, t / max(a, 1e-4))
    rel = np.clip((d - t) / max(r, 1e-4), 0, 1)
    return e * rel * s_level + (1 - s_level) * e * rel * np.exp(-t * 3)


def norm(x, peak=0.9):
    return x / (np.abs(x).max() + 1e-9) * peak


def stereo(x, width=0.3, pan=0.0):
    d = int(SR * 0.011 * width)
    l = x.copy()
    r = np.concatenate([np.zeros(d), x[:-d]]) if d > 0 else x.copy()
    gl, gr = np.sqrt(0.5 * (1 - pan)), np.sqrt(0.5 * (1 + pan))
    return np.stack([l * gl, r * gr], 1) * 1.4


def reverb(x, size=0.6, wet=0.3):
    """cheap convolution reverb with exponentially decaying noise IR"""
    d = 0.4 + size * 2.2
    ir = noise(d) * np.exp(-t_(d) / (d / 5))
    ir = lp(ir, 6000)
    ir[0] = 0
    y = signal.fftconvolve(x, ir)[: len(x) + int(d * SR)]
    y = norm(y, np.abs(x).max() + 1e-9)
    xx = np.concatenate([x, np.zeros(len(y) - len(x))])
    return xx * (1 - wet) + y * wet


def pitch_drop(d, f0, f1, k=8):
    t = t_(d)
    f = f1 + (f0 - f1) * np.exp(-t * k)
    return np.sin(2 * np.pi * np.cumsum(f) / SR)


def metallic(d, base=900, n=9, decay=0.6, inharm=1.37):
    t = t_(d)
    x = np.zeros_like(t)
    for i in range(n):
        f = base * (1 + i * inharm + rng.uniform(-0.05, 0.05)) * (1 + 0.3 * i % 2)
        x += np.sin(2 * np.pi * f * t + rng.uniform(0, 6)) * np.exp(-t / (decay / (1 + i * 0.35))) / (1 + i * 0.4)
    return x


def pad(x, d):
    n = int(d * SR)
    return np.concatenate([x, np.zeros(max(0, n - len(x)))])[:n] if len(x) < n else x[:n]


# --------------------------------------------------------------- sounds
def whoosh_fast():
    d = 0.45
    x = sweep_bp(noise(d), 600, 3500, q=1.5) * np.sin(np.pi * np.clip(t_(d) / d, 0, 1)) ** 2
    return stereo(norm(x, 0.8), 0.6)


def whoosh_heavy():
    d = 0.9
    x = sweep_bp(noise(d), 150, 1200, q=1.2) * np.sin(np.pi * t_(d) / d) ** 1.5
    x += lp(noise(d), 200) * np.sin(np.pi * t_(d) / d) * 0.6
    return stereo(norm(x, 0.85), 0.7)


def wind_gust():
    d = 3.0
    e = np.sin(np.pi * t_(d) / d) ** 2
    x = sweep_bp(pink(d), 300, 900, q=1.0, steps=40) * e + bp(pink(d), 1500, 4000) * e * 0.2
    return stereo(norm(x, 0.6), 1.0)


def thunder():
    d = 5.0
    crack = hp(noise(0.25), 1500) * env(0.25, 0.002, 0.05)
    rumble = lp(brown(d), 180, 3) * (env(d, 0.15, 1.6) + 0.4 * env(d, 1.0, 1.2) * (np.sin(t_(d) * 7) * 0.5 + 0.5))
    x = pad(crack * 0.5, d) + rumble * 1.5
    return stereo(reverb(norm(x, 0.95), 0.9, 0.35), 1.0)


def sword_draw():
    d = 0.8
    scrape = bp(noise(d), 2500, 9000) * np.sin(np.pi * np.clip(t_(d) / 0.55, 0, 1)) * (t_(d) < 0.55)
    ring = pad(metallic(0.8, 1800, 7, 0.5), d) * (t_(d) > 0.5) * 0.6
    return stereo(norm(scrape * 0.6 + ring, 0.8), 0.4)


def sword_slash():
    d = 0.5
    sw = sweep_bp(noise(d), 1200, 7000, q=2.5) * np.exp(-((t_(d) - 0.12) / 0.07) ** 2)
    sh = metallic(d, 2600, 6, 0.18) * env(d, 0.01, 0.15) * 0.4
    return stereo(norm(sw + sh, 0.9), 0.5)


def sword_clash():
    d = 1.4
    hit = hp(noise(0.05), 2000) * env(0.05, 0.0005, 0.01)
    ring = metallic(d, 1100, 11, 0.9)
    x = pad(hit, d) * 0.8 + ring * 0.7
    return stereo(reverb(norm(x, 0.95), 0.4, 0.25), 0.5)


def sword_stab():
    d = 0.7
    thrust = sweep_bp(noise(d), 3000, 800, q=2) * env(d, 0.005, 0.08)
    squelch = bp(noise(d), 200, 900) * env(d, 0.03, 0.18) * (1 + 0.6 * np.sin(2 * np.pi * 23 * t_(d)))
    thud = pitch_drop(d, 140, 50, 12) * env(d, 0.002, 0.12)
    return stereo(norm(thrust * 0.5 + squelch * 0.8 + thud * 0.6, 0.9), 0.3)


def sword_spin():
    d = 1.2
    x = np.zeros(int(d * SR))
    for k in range(4):
        c = 0.12 + k * 0.25
        x += sweep_bp(noise(d), 900, 5000, q=2) * np.exp(-((t_(d) - c) / 0.06) ** 2)
    return stereo(norm(x, 0.85), 0.9)


def blood_splat():
    d = 0.5
    x = bp(noise(d), 300, 3000) * env(d, 0.002, 0.06)
    drops = np.zeros(int(d * SR))
    for _ in range(14):
        i = int(rng.uniform(0.03, 0.45) * SR)
        drops[i:i + 300] += bp(noise(300 / SR), 1500, 5000) * np.exp(-np.arange(300) / 60) * rng.uniform(0.2, 0.6)
    return stereo(norm(x + drops, 0.8), 0.5)


def punch():
    d = 0.45
    thump = pitch_drop(d, 180, 55, 18) * env(d, 0.001, 0.09)
    slap = bp(noise(d), 800, 5000) * env(d, 0.0005, 0.025)
    return stereo(norm(thump + slap * 0.7, 0.95), 0.2)


def punch_heavy():
    d = 1.2
    thump = pitch_drop(d, 120, 35, 10) * env(d, 0.001, 0.25)
    crack = hp(noise(d), 1500) * env(d, 0.0005, 0.03)
    body = lp(noise(d), 400) * env(d, 0.002, 0.12)
    x = thump * 1.2 + crack * 0.6 + body * 0.5
    return stereo(reverb(norm(x, 0.98), 0.5, 0.2), 0.3)


def kick():
    d = 0.55
    sw = sweep_bp(noise(d), 500, 2500) * np.exp(-((t_(d) - 0.08) / 0.05) ** 2) * 0.5
    hit = pitch_drop(d, 150, 45, 14) * env(d, 0.001, 0.11) * (t_(d) > 0.12)
    slap = bp(noise(d), 1000, 6000) * env(d, 0.0005, 0.02)
    slap = np.roll(slap, int(0.12 * SR))
    return stereo(norm(sw + hit + slap * 0.7, 0.95), 0.3)


def body_fall():
    d = 1.0
    thud = pitch_drop(d, 90, 40, 8) * env(d, 0.003, 0.15)
    grit = bp(noise(d), 500, 4000) * env(d, 0.01, 0.2) * 0.4
    splash = hp(noise(d), 1200) * env(d, 0.01, 0.25) * 0.35
    return stereo(norm(thud + grit + splash, 0.9), 0.5)


def body_slide():
    d = 1.4
    x = bp(noise(d), 300, 3000) * np.sin(np.pi * t_(d) / d) * (1 + 0.4 * np.sin(2 * np.pi * 11 * t_(d)))
    return stereo(norm(x, 0.7), 0.6)


def splash(d, size):
    x = hp(noise(d), 600) * env(d, 0.004, 0.12 * size)
    x += bp(noise(d), 150, 800) * env(d, 0.01, 0.2 * size) * 0.6
    drops = np.zeros(int(d * SR))
    for _ in range(int(25 * size)):
        i = int(rng.uniform(0.05, d * 0.9) * SR)
        f = rng.uniform(900, 3500)
        n = int(0.03 * SR)
        drops[i:i + n] += np.sin(2 * np.pi * np.linspace(f, f * 1.6, n) * np.arange(n) / SR) * np.exp(-np.arange(n) / (n / 4)) * rng.uniform(0.1, 0.3)
    return norm(x + drops[: len(x)], 0.85)


def splash_small():
    return stereo(splash(0.6, 0.6), 0.5)


def splash_big():
    return stereo(reverb(splash(1.6, 1.8), 0.4, 0.2), 1.0)


def footsteps_wet():
    d = 2.0
    x = np.zeros(int(d * SR))
    for k in range(6):
        i = int((0.1 + k * 0.3) * SR)
        s = splash(0.25, 0.3) * 0.6 + pitch_drop(0.25, 110, 60, 20) * env(0.25, 0.001, 0.04) * 0.5
        x[i:i + len(s)] += s[: len(x) - i]
    return stereo(norm(x, 0.7), 0.4)


def dash_burst():
    d = 0.8
    x = sweep_bp(noise(d), 200, 4000, q=1.2) * env(d, 0.01, 0.2) + lp(noise(d), 150) * env(d, 0.002, 0.15)
    return stereo(norm(x, 0.9), 0.8)


def water_wave():
    d = 3.0
    e = np.sin(np.pi * np.clip(t_(d) / d, 0, 1)) ** 0.7
    x = sweep_bp(pink(d), 200, 1500, q=0.8, steps=40) * e
    x += hp(noise(d), 2500) * e * 0.25 * (1 + 0.5 * np.sin(2 * np.pi * 3 * t_(d)))
    return stereo(reverb(norm(x, 0.85), 0.5, 0.2), 1.0)


def water_bullet():
    d = 0.6
    x = sweep_bp(noise(d), 4000, 900, q=3) * env(d, 0.003, 0.12)
    pop = pitch_drop(d, 600, 200, 25) * env(d, 0.001, 0.05)
    return stereo(norm(x + pop * 0.5, 0.85), 0.4)


def water_vortex():
    d = 4.0
    e = np.minimum(1, t_(d) / 1.0) * np.minimum(1, (d - t_(d)) / 0.6)
    x = bp(pink(d), 150, 1200) * (1 + 0.6 * np.sin(2 * np.pi * 4.5 * t_(d))) * e
    x += hp(noise(d), 3000) * e * 0.2
    x += lp(brown(d), 120) * e * 0.8
    return stereo(reverb(norm(x, 0.9), 0.7, 0.25), 1.0)


def water_breath():
    d = 3.5
    roar = sweep_bp(pink(d), 120, 900, q=0.9, steps=40) * env(d, 0.15, 1.6)
    x = roar + water_vortex()[: int(d * SR), 0] * 0.6
    return stereo(reverb(norm(x, 0.95), 0.8, 0.3), 1.0)


def vine_whip():
    d = 0.6
    sw = sweep_bp(noise(d), 400, 3000) * np.exp(-((t_(d) - 0.15) / 0.07) ** 2)
    crack = hp(noise(d), 2500) * np.exp(-np.maximum(0, t_(d) - 0.22) / 0.015) * (t_(d) > 0.22)
    return stereo(norm(sw + crack * 0.8, 0.9), 0.5)


def vine_wrap():
    d = 1.2
    x = np.zeros(int(d * SR))
    for k in range(10):  # creaks
        i = int(rng.uniform(0, d - 0.15) * SR)
        n = int(0.12 * SR)
        f = rng.uniform(250, 700)
        tt = np.arange(n) / SR
        c = signal.sawtooth(2 * np.pi * f * tt * (1 + 0.3 * tt)) * np.exp(-tt / 0.04)
        x[i:i + n] += bp(c, 300, 3000) * rng.uniform(0.3, 0.8)
    x += bp(noise(d), 1500, 6000) * np.sin(np.pi * t_(d) / d) * 0.2
    return stereo(norm(x, 0.8), 0.5)


def vine_snap():
    d = 0.6
    snap = hp(noise(d), 1200) * env(d, 0.0005, 0.02)
    fib = bp(noise(d), 800, 4000) * env(d, 0.01, 0.12) * 0.5
    return stereo(norm(snap + fib, 0.9), 0.4)


def energy_charge(color):
    d = 2.2
    t = t_(d)
    f0, f1 = (90, 420) if color == "blue" else (120, 520)
    f = f0 + (f1 - f0) * (t / d) ** 2
    ph = 2 * np.pi * np.cumsum(f) / SR
    mod = np.sin(ph * (2.01 if color == "blue" else 1.5)) * (2 + 4 * t / d)
    x = np.sin(ph + mod) * (t / d) ** 1.2
    x += hp(noise(d), 4000) * (t / d) ** 3 * 0.3 * (np.sin(2 * np.pi * 30 * t) > 0.6)
    x = x * np.minimum(1, (d - t) / 0.05)
    return stereo(reverb(norm(x, 0.8), 0.6, 0.3), 0.8)


def energy_charge_green():
    return energy_charge("green")


def energy_charge_blue():
    return energy_charge("blue")


def energy_burst():
    d = 2.0
    boom = pitch_drop(d, 200, 40, 6) * env(d, 0.002, 0.5)
    hiss = sweep_bp(noise(d), 6000, 800, q=1) * env(d, 0.005, 0.4)
    x = boom * 1.2 + hiss * 0.6
    return stereo(reverb(norm(x, 0.97), 0.8, 0.3), 1.0)


def crackle():
    d = 1.5
    x = np.zeros(int(d * SR))
    for _ in range(60):
        i = int(rng.uniform(0, d - 0.02) * SR)
        n = int(rng.uniform(0.002, 0.012) * SR)
        x[i:i + n] += hp(noise(n / SR), 2000) * rng.uniform(0.2, 1)
    x += np.sin(2 * np.pi * 60 * t_(d)) * 0.05 * (np.abs(x) > 0.01)
    return stereo(norm(x, 0.7), 0.8)


def aura_hum():
    d = 4.0
    t = t_(d)
    x = sum(signal.sawtooth(2 * np.pi * f * t) for f in (55, 55.4, 82.6, 110.3)) * 0.25
    x = lp(x, 500) * (1 + 0.3 * np.sin(2 * np.pi * 0.8 * t))
    x *= np.minimum(1, t / 0.5) * np.minimum(1, (d - t) / 0.5)
    return stereo(norm(x, 0.6), 1.0)


def heal_shimmer():
    d = 2.5
    t = t_(d)
    x = np.zeros_like(t)
    for k, f in enumerate([880, 1108, 1318, 1760, 2217]):
        x += np.sin(2 * np.pi * f * t) * np.exp(-((t - 0.25 - k * 0.12) % 1.2) * 3) * 0.2
    x *= np.minimum(1, t / 0.3) * np.minimum(1, (d - t) / 0.6)
    return stereo(reverb(norm(x, 0.6), 0.9, 0.45), 1.0)


def growl(d, f0=70, rough=1.0):
    t = t_(d)
    f = f0 * (1 + 0.08 * np.sin(2 * np.pi * 3.3 * t)) * (1 + 0.04 * rng.standard_normal(len(t)).cumsum() / np.sqrt(len(t)) * 30)
    src = signal.sawtooth(2 * np.pi * np.cumsum(f) / SR)
    src = src * (1 + rough * 0.8 * np.sin(2 * np.pi * 27 * t + np.sin(2 * np.pi * 5 * t)))  # roughness / rattle
    src += noise(d) * 0.3
    form = bp(src, 200, 600) * 1.0 + bp(src, 700, 1200) * 0.6 + bp(src, 2200, 3200) * 0.2
    return form


def wolf_growl():
    d = 2.6
    x = growl(d, 62, 1.2) * np.minimum(1, t_(d) / 0.3) * np.minimum(1, (d - t_(d)) / 0.5)
    x += lp(brown(d), 90) * 0.5 * np.minimum(1, t_(d) / 0.3)
    return stereo(reverb(norm(x, 0.85), 0.7, 0.25), 0.6)


def wolf_roar():
    d = 3.2
    t = t_(d)
    e = np.minimum(1, t / 0.15) * np.exp(-np.maximum(0, t - 0.6) / 1.0)
    x = growl(d, 95, 1.6) * e
    x += sweep_bp(pink(d), 300, 1500, q=0.7, steps=30) * e * 0.8
    x += lp(brown(d), 120) * e
    return stereo(reverb(norm(x, 0.98), 0.9, 0.35), 1.0)


def wolf_bite():
    d = 0.8
    clamp = pitch_drop(d, 220, 70, 30) * env(d, 0.001, 0.06)
    crunch = bp(noise(d), 600, 5000) * env(d, 0.002, 0.08) * (1 + np.sign(np.sin(2 * np.pi * 60 * t_(d))))
    return stereo(norm(clamp + crunch * 0.6 + growl(d, 80)[: int(d * SR)] * env(d, 0.05, 0.3) * 0.4, 0.95), 0.4)


def heartbeat():
    d = 1.6
    x = np.zeros(int(d * SR))
    for st, g in ((0.05, 1.0), (0.33, 0.7)):
        b = pitch_drop(0.3, 70, 40, 10) * env(0.3, 0.004, 0.08) * g
        i = int(st * SR)
        x[i:i + len(b)] += b
    return stereo(norm(lp(x, 200), 0.95), 0.0)


def impact_big():
    d = 2.5
    boom = pitch_drop(d, 110, 28, 5) * env(d, 0.001, 0.7)
    crack = hp(noise(d), 1000) * env(d, 0.0005, 0.06)
    deb = bp(noise(d), 400, 3000) * env(d, 0.05, 0.6) * 0.3
    x = boom * 1.3 + crack * 0.7 + deb
    return stereo(reverb(norm(x, 0.99), 0.9, 0.3), 1.0)


def explosion():
    d = 3.5
    x = lp(brown(d), 300, 3) * env(d, 0.005, 1.0) * 2 + bp(noise(d), 300, 4000) * env(d, 0.002, 0.35) * 0.7
    x += pitch_drop(d, 90, 25, 4) * env(d, 0.002, 0.8)
    return stereo(reverb(norm(x, 0.99), 1.0, 0.35), 1.0)


def rock_crumble():
    d = 2.0
    x = np.zeros(int(d * SR))
    for _ in range(80):
        i = int(rng.uniform(0, d - 0.1) * SR)
        n = int(rng.uniform(0.01, 0.06) * SR)
        x[i:i + n] += bp(noise(n / SR), rng.uniform(200, 800), rng.uniform(1500, 5000)) * np.exp(-np.arange(n) / (n / 3)) * rng.uniform(0.2, 1)
    x += lp(brown(d), 150) * env(d, 0.05, 0.8) * 0.5
    return stereo(norm(x, 0.85), 1.0)


def wall_crash():
    d = 2.5
    a = impact_big()[: int(d * SR), 0] * 0.8
    b = rock_crumble()
    b = pad(b[:, 0], d) * 0.8
    return stereo(norm(a + np.roll(b, int(0.05 * SR)), 0.98), 1.0)


def tree_crack():
    d = 1.2
    x = np.zeros(int(d * SR))
    for _ in range(25):
        i = int(rng.uniform(0, 0.5) * SR)
        n = int(rng.uniform(0.005, 0.03) * SR)
        x[i:i + n] += bp(noise(n / SR), 300, 4000) * rng.uniform(0.3, 1)
    x += hp(noise(d), 800) * env(d, 0.0005, 0.04) * 1.2
    x += pitch_drop(d, 160, 60, 10) * env(d, 0.002, 0.2) * 0.5
    return stereo(norm(x, 0.95), 0.6)


def tree_fall():
    d = 3.0
    creak = vine_wrap()[:, 0]
    creak = pad(creak, d) * 0.6
    thud = pitch_drop(1.5, 70, 30, 6) * env(1.5, 0.003, 0.5)
    x = creak + np.roll(pad(thud, d) * 1.2, int(1.4 * SR)) + np.roll(pad(rock_crumble()[:, 0], d) * 0.3, int(1.45 * SR))
    return stereo(norm(x, 0.95), 1.0)


def kunai_throw():
    d = 0.6
    x = sweep_bp(noise(d), 2500, 6000, q=4) * np.exp(-((t_(d) - 0.2) / 0.08) ** 2)
    whistle = np.sin(2 * np.pi * np.cumsum(3000 - 1500 * t_(d)) / SR) * np.exp(-((t_(d) - 0.22) / 0.1) ** 2) * 0.2
    return stereo(norm(x + whistle, 0.8), 0.6, 0.3)


def kunai_shatter():
    d = 1.0
    x = metallic(d, 2400, 8, 0.25) * 0.5 + hp(noise(d), 3000) * env(d, 0.0005, 0.05)
    x += splash(1.0, 0.5) * 0.5
    return stereo(norm(x, 0.9), 0.6)


def clone_shatter():
    d = 1.5
    x = np.zeros(int(d * SR))
    for _ in range(40):
        i = int(rng.uniform(0, 0.6) * SR)
        x[i:i + 2400] += metallic(0.05, rng.uniform(2500, 6000), 3, 0.03) * rng.uniform(0.2, 0.7)
    x += sweep_bp(noise(d), 3000, 500, q=1) * env(d, 0.002, 0.3) * 0.6
    return stereo(reverb(norm(x, 0.85), 0.6, 0.35), 1.0)


def glass_ring():
    d = 2.5
    return stereo(reverb(norm(metallic(d, 1600, 6, 1.4, 1.73), 0.6), 0.9, 0.4), 1.0)


def steam_hiss():
    d = 4.0
    e = np.minimum(1, t_(d) / 0.4) * np.minimum(1, (d - t_(d)) / 1.0)
    x = hp(noise(d), 3000) * e * (1 + 0.15 * np.sin(2 * np.pi * 1.3 * t_(d)))
    return stereo(norm(x, 0.5), 1.0)


def steam_burst():
    d = 3.0
    x = hp(noise(d), 1500) * env(d, 0.01, 0.9) + lp(brown(d), 200) * env(d, 0.005, 0.5)
    return stereo(reverb(norm(x, 0.9), 0.8, 0.3), 1.0)


def shadow_whoosh():
    d = 1.4
    x = sweep_bp(noise(d), 1500, 120, q=1.0) * np.sin(np.pi * t_(d) / d) ** 2
    x = x[::-1] * 0.6 + x * 0.4
    x += np.sin(2 * np.pi * 45 * t_(d)) * np.sin(np.pi * t_(d) / d) * 0.4
    return stereo(reverb(norm(x, 0.85), 0.8, 0.4), 1.0)


def shadow_claw():
    d = 2.0
    a = shadow_whoosh()[:, 0]
    b = pad(impact_big()[:, 0], d) * 0.7
    x = pad(a, d) + np.roll(b, int(0.9 * SR))
    return stereo(norm(x, 0.97), 1.0)


def riser():
    d = 2.5
    t = t_(d)
    x = sweep_bp(noise(d), 300, 8000, q=1.5) * (t / d) ** 2
    x += np.sin(2 * np.pi * np.cumsum(200 + 800 * (t / d) ** 2) / SR) * (t / d) ** 2 * 0.3
    return stereo(reverb(norm(x, 0.8), 0.7, 0.3), 1.0)


def stinger():
    d = 3.0
    t = t_(d)
    x = sum(signal.sawtooth(2 * np.pi * f * t) for f in (55, 82.4, 110, 164.8, 220)) * 0.2
    x = lp(x, 1800) * env(d, 0.005, 1.0)
    x += pitch_drop(d, 80, 30, 4) * env(d, 0.002, 0.8) * 0.8
    return stereo(reverb(norm(x, 0.9), 1.0, 0.4), 1.0)


def sub_drop():
    d = 2.5
    return stereo(norm(pitch_drop(d, 90, 25, 2) * env(d, 0.01, 1.0), 0.95), 0.0)


def ground_burst():
    d = 2.0
    x = lp(brown(d), 250) * env(d, 0.003, 0.5) * 1.5 + rock_crumble()[: int(d * SR), 0] * 0.6
    x += sweep_bp(noise(d), 300, 3000) * env(d, 0.01, 0.3) * 0.5
    return stereo(norm(x, 0.97), 1.0)


def rain_loop():
    d = 20.0
    x = bp(pink(d), 400, 9000) * 0.5 + lp(brown(d), 300) * 0.25
    drops = np.zeros(int(d * SR))
    n = int(0.008 * SR)
    for _ in range(2500):
        i = int(rng.uniform(0, d - 0.01) * SR)
        drops[i:i + n] += hp(noise(n / SR), 2000) * np.exp(-np.arange(n) / (n / 5)) * rng.uniform(0.05, 0.4)
    x = norm(x + drops, 0.5)
    # seamless loop: crossfade tail into head
    f = int(1.0 * SR)
    x[:f] = x[:f] * np.linspace(0, 1, f) + x[-f:] * np.linspace(1, 0, f)
    x = x[:-f]
    l = x
    r = np.roll(x, int(0.37 * SR))
    return np.stack([l, r], 1) * 0.9


NAMES = [n for n, v in list(globals().items()) if callable(v) and n not in (
    "t_", "noise", "pink", "brown", "bp", "lp", "hp", "sweep_bp", "env", "adsr", "norm", "stereo", "reverb",
    "pitch_drop", "metallic", "pad", "splash", "growl", "energy_charge", "main") and not n[0].isupper()
    and v.__module__ == __name__]


def main():
    os.makedirs(OUT, exist_ok=True)
    for n in NAMES:
        x = globals()[n]()
        x = np.asarray(x, np.float32)
        if x.ndim == 1:
            x = stereo(x)
        sf.write(os.path.join(OUT, n + ".wav"), x.astype(np.float32), SR, subtype="FLOAT")
        print(n, round(len(x) / SR, 2), flush=True)


if __name__ == "__main__":
    main()
