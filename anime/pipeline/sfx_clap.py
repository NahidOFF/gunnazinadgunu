"""Local judge for AI vs procedural SFX using CLAP audio-text similarity.

For every sound that has both an AudioLDM2 and a procedural version and no
Gemini verdict, scores both against the intended description with
laion/clap-htsat-unfused and copies the better one to build/sfx/<name>.wav.
"""
import json
import os
import shutil
import subprocess
import sys

import numpy as np
import soundfile as sf
from scipy import signal

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
B = os.path.join(ROOT, "build", "sfx")
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
from sfx_ai import PROMPTS, to48  # noqa: E402


def load48k_mono(p):
    x, sr = sf.read(p, dtype="float32", always_2d=True)
    x = x.mean(axis=1)
    if sr != 48000:
        g = np.gcd(sr, 48000)
        x = signal.resample_poly(x, 48000 // g, sr // g)
    return x[: 48000 * 10]


def main():
    import torch
    from transformers import ClapModel, ClapProcessor
    torch.set_num_threads(2)
    model = ClapModel.from_pretrained("laion/clap-htsat-unfused").eval()
    proc = ClapProcessor.from_pretrained("laion/clap-htsat-unfused")
    vpath = os.path.join(B, "judge.json")
    verdicts = json.load(open(vpath)) if os.path.exists(vpath) else {}
    for name, (prompt, _) in PROMPTS.items():
        v = verdicts.get(name, {})
        if v.get("scoreA") is not None:
            continue  # Gemini already judged
        a, p = os.path.join(B, "ai", name + ".wav"), os.path.join(B, "proc", name + ".wav")
        if not (os.path.exists(a) and os.path.exists(p)):
            continue
        auds = [load48k_mono(a), load48k_mono(p)]
        inp = proc(text=[prompt, "music", "speech", "noise artifacts"], audio=auds, sampling_rate=48000, return_tensors="pt", padding=True)
        with torch.no_grad():
            out = model(**inp)
        sims = out.logits_per_audio.softmax(dim=-1)[:, 0].numpy()  # prob of intended prompt vs distractors
        pick = "ai" if sims[0] > sims[1] else "proc"
        verdicts[name] = {"pick": pick, "clap_ai": float(sims[0]), "clap_proc": float(sims[1]), "judge": "clap"}
        print(name, pick, round(float(sims[0]), 3), round(float(sims[1]), 3), flush=True)
        dst = os.path.join(B, name + ".wav")
        if pick == "ai":
            to48(a, dst)
        else:
            shutil.copy(p, dst)
    json.dump(verdicts, open(vpath, "w"), indent=1)


if __name__ == "__main__":
    main()
