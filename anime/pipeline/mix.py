"""Mix dialogue, SFX, ambience and music into build/mix.wav (48 kHz stereo).

Dialogue gets per-speaker processing (wolf: pitched down + big reverb,
thoughts: reverb + softer, narration: light room), music is cue-sequenced with
crossfades and ducked under dialogue, rain ambience follows the rain shots,
then the master is limited and loudness-normalised (EBU R128, -16 LUFS).
"""
import json
import os
import subprocess

import numpy as np
import soundfile as sf
from scipy import signal

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
B = os.path.join(ROOT, "build")
SR = 48000

VOICE_FX = {
    "Wolf": "asetrate={SR}*0.93,aresample={SR},atempo=1.04,bass=g=5,aecho=0.8:0.6:60|120:0.35|0.2",
    "Narration": "aecho=0.8:0.5:40:0.15,equalizer=f=200:t=q:w=1:g=2",
    "Clone": "aecho=0.8:0.7:35|70:0.35|0.25,highpass=f=150",
}
THOUGHT_FX = "lowpass=f=6500,aecho=0.8:0.75:80|160:0.35|0.22"


def load(path, gain=1.0):
    x, sr = sf.read(path, dtype="float32", always_2d=True)
    if sr != SR:
        g = np.gcd(sr, SR)
        x = signal.resample_poly(x, SR // g, sr // g, axis=0).astype(np.float32)
    if x.shape[1] == 1:
        x = np.repeat(x, 2, axis=1)
    return x[:, :2] * gain


def place(buf, x, t, gain=1.0, pan=0.0):
    i = int(round(t * SR))
    if i >= len(buf):
        return
    if i < 0:
        x = x[-i:]
        i = 0
    n = min(len(x), len(buf) - i)
    gl, gr = np.sqrt(0.5 * (1 - pan)) * 1.414, np.sqrt(0.5 * (1 + pan)) * 1.414
    buf[i:i + n, 0] += x[:n, 0] * gain * gl
    buf[i:i + n, 1] += x[:n, 1] * gain * gr


def processed_voice(v):
    src = os.path.join(B, "voice", v["id"] + ".wav")
    if not os.path.exists(src):
        return None
    fx = VOICE_FX.get(v["speaker"])
    if fx:
        fx = fx.replace("{SR}", str(sf.info(src).samplerate))
    if v["kind"] == "thought":
        fx = (fx + "," if fx else "") + THOUGHT_FX
    if v["kind"] == "whisper":
        fx = (fx + "," if fx else "") + "volume=0.8"
    if not fx:
        return load(src)
    os.makedirs(os.path.join(B, "voice_fx"), exist_ok=True)
    dst = os.path.join(B, "voice_fx", v["id"] + ".wav")
    if v["speaker"] == "Wolf":
        # monstrous layer: main voice + an octave-down, low-passed double + sub boost
        sr = sf.info(src).samplerate
        graph = (f"[0:a]asplit=2[a][b];[a]{fx}[main];"
                 f"[b]asetrate={sr}*0.62,aresample={sr},atempo=1.6129,lowpass=f=700,volume=0.55[low];"
                 f"[main][low]amix=inputs=2:normalize=0,equalizer=f=80:t=q:w=1:g=5,"
                 f"aecho=0.8:0.5:90:0.25,apad=pad_dur=1.2[out]")
        subprocess.run(["ffmpeg", "-loglevel", "error", "-y", "-i", src, "-filter_complex", graph, "-map", "[out]", dst], check=True)
        x = load(dst)
        return x / (np.abs(x).max() + 1e-9) * 0.95
    subprocess.run(["ffmpeg", "-loglevel", "error", "-y", "-i", src, "-af", fx + ",apad=pad_dur=1.2", dst], check=True)
    x = load(dst)
    return x / (np.abs(x).max() + 1e-9) * 0.9


def music_track(events, dur):
    out = np.zeros((int((dur + 3) * SR), 2), np.float32)
    cues = sorted(events["music"], key=lambda c: c["t"])
    XF = 1.8
    for i, c in enumerate(cues):
        t0 = c["t"]
        t1 = cues[i + 1]["t"] if i + 1 < len(cues) else dur + 2
        if c["cue"] == "silence":
            continue
        p = os.path.join(B, "music", c["cue"] + ".wav")
        if not os.path.exists(p):
            print("missing music cue", c["cue"])
            continue
        x = load(p)
        need = int((t1 - t0 + XF) * SR)
        # loop with crossfade if needed
        seg = x
        while len(seg) < need:
            f = int(2.0 * SR)
            ramp = np.linspace(0, 1, f)[:, None]
            seg = np.concatenate([seg[:-f], seg[-f:] * (1 - ramp) + x[:f] * ramp, x[f:]])
        seg = seg[:need].copy()
        fi = int((0.6 if i == 0 else XF) * SR)
        seg[:fi] *= np.linspace(0, 1, fi)[:, None]
        fo = int(XF * SR)
        seg[-fo:] *= np.linspace(1, 0, fo)[:, None]
        place(out, seg, t0, 1.0 / 1.414)
    return out


def main():
    ev = json.load(open(os.path.join(B, "audio_events.json")))
    dur = ev["duration"]
    n = int((dur + 3) * SR)
    dia = np.zeros((n, 2), np.float32)
    fx = np.zeros((n, 2), np.float32)
    amb = np.zeros((n, 2), np.float32)
    for v in ev["voices"]:
        x = processed_voice(v)
        if x is None:
            continue
        g = {"effort": 0.85, "reaction": 0.85, "whisper": 0.8, "thought": 0.8}.get(v["kind"], 1.0)
        place(dia, x, v["t"], 0.9 * g)
    sfx_cache = {}
    rng = np.random.default_rng(3)
    for s in ev["sfx"]:
        p = os.path.join(B, "sfx", s["name"] + ".wav")
        if not os.path.exists(p):
            p = os.path.join(B, "sfx", "proc", s["name"] + ".wav")
        if not os.path.exists(p):
            print("missing sfx", s["name"])
            continue
        if p not in sfx_cache:
            sfx_cache[p] = load(p)
        place(fx, sfx_cache[p], s["t"], 0.55 * s["gain"], pan=float(rng.uniform(-0.25, 0.25)))
    # rain ambience
    rp = os.path.join(B, "sfx", "rain_loop.wav")
    if os.path.exists(rp):
        rain = load(rp)
        for a, b in ev["rain"]:
            need = int((b - a + 1.0) * SR)
            reps = int(np.ceil(need / len(rain))) + 1
            seg = np.concatenate([rain] * reps)[:need].copy()
            f = int(0.8 * SR)
            seg[:f] *= np.linspace(0, 1, f)[:, None]
            seg[-f:] *= np.linspace(1, 0, f)[:, None]
            place(amb, seg, a, 0.22)
    mus = music_track(ev, dur)[:n]
    # sidechain ducking from dialogue envelope
    e = np.abs(dia).max(axis=1)
    win = int(0.03 * SR)
    e = np.convolve(e, np.ones(win) / win, mode="same")
    active = (e > 0.02).astype(np.float32)
    rel = int(0.45 * SR)
    duck = np.convolve(active, np.ones(rel) / rel, mode="same")
    duck = np.clip(duck * 2, 0, 1)
    mus_gain = 0.42 * (1 - 0.55 * duck)[:, None]
    amb_gain = (1 - 0.35 * duck)[:, None]
    mix = dia * 1.0 + fx * 0.9 + amb * amb_gain + mus * mus_gain
    # gentle master limiter
    mix = np.tanh(mix * 1.1) / np.tanh(1.1)
    raw = os.path.join(B, "mix_raw.wav")
    sf.write(raw, mix.astype(np.float32), SR, subtype="FLOAT")
    subprocess.run(["ffmpeg", "-loglevel", "error", "-y", "-i", raw, "-af",
                    "loudnorm=I=-16:TP=-1.5:LRA=11", "-ar", str(SR), "-c:a", "pcm_s16le", os.path.join(B, "mix.wav")], check=True)
    print("mixed", round(dur, 1), "s")


if __name__ == "__main__":
    main()
