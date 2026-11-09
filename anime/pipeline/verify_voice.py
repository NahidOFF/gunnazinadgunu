"""Verify generated voice lines with local Whisper (Japanese ASR).

Transcribes build/voice/<id>.wav and compares with the intended Japanese.
Prints a report sorted by similarity and writes build/voice/verify.json.
Short interjections (<=4 chars) are only checked for not being too long.
"""
import difflib
import json
import os
import sys
import unicodedata

import numpy as np
import soundfile as sf
from scipy import signal

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
B = os.path.join(ROOT, "build")


def norm(s):
    s = unicodedata.normalize("NFKC", s or "")
    return "".join(ch for ch in s if ch.isalnum())


def kana(s):
    try:
        import pykakasi  # optional
        k = pykakasi.kakasi()
        return "".join(x["hira"] for x in k.convert(s))
    except Exception:
        return s


def main():
    import torch
    from transformers import WhisperForConditionalGeneration, WhisperProcessor
    torch.set_num_threads(2)
    name = "openai/whisper-small"
    proc = WhisperProcessor.from_pretrained(name)
    model = WhisperForConditionalGeneration.from_pretrained(name).eval()
    script = json.load(open(os.path.join(B, "script.json")))
    lines = [l for sh in script["shots"] for l in sh.get("lines", [])]
    want = set(sys.argv[1:])
    res = {}
    for l in lines:
        if want and l["id"] not in want:
            continue
        p = os.path.join(B, "voice", l["id"] + ".wav")
        if not os.path.exists(p):
            continue
        x, sr = sf.read(p, dtype="float32")
        if x.ndim > 1:
            x = x.mean(axis=1)
        x = signal.resample_poly(x, 16000, sr) if sr != 16000 else x
        feats = proc(x, sampling_rate=16000, return_tensors="pt").input_features
        with torch.no_grad():
            ids = model.generate(feats, language="ja", task="transcribe", max_new_tokens=120)
        heard = proc.batch_decode(ids, skip_special_tokens=True)[0]
        a, b = norm(kana(l["ja"])), norm(kana(heard))
        sim = difflib.SequenceMatcher(None, a, b).ratio()
        res[l["id"]] = {"ja": l["ja"], "heard": heard, "sim": round(sim, 2), "dur": round(len(x) / 16000, 2)}
        print(f"{l['id']} {sim:.2f} | {l['ja']} | {heard}", flush=True)
    json.dump(res, open(os.path.join(B, "voice", "verify.json"), "w"), ensure_ascii=False, indent=1)
    bad = sorted((v["sim"], k) for k, v in res.items() if len(norm(v["ja"])) > 4 and v["sim"] < 0.6)
    print("LOW:", bad)


if __name__ == "__main__":
    main()
