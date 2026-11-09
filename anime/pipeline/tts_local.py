"""Local Japanese TTS with Style-Bert-VITS2 (JVNV emotional male voices).

Used because the Gemini free tier allows only 10 TTS requests/day/model.
Run with the isolated venv:  /opt/sbv2/bin/python pipeline/tts_local.py [line_id ...]
Reads build/script.json, writes build/voice/<line_id>.wav (44.1 kHz mono).
Emotion style is chosen from the line kind + English direction keywords.
"""
import json
import os
import re
import sys

import numpy as np
import soundfile as sf

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
B = os.path.join(ROOT, "build")
M = os.path.join(B, "models", "sbv2")
BERT = "ku-nlp/deberta-v2-large-japanese-char-wwm"

VOICES = {
    # speaker: (model dir, safetensors, pitch_scale, length_scale)
    "M": ("jvnv-M1-jp", "jvnv-M1-jp_e158_s14000.safetensors", 1.04, 0.95),
    "E": ("jvnv-M2-jp", "jvnv-M2-jp_e159_s17000.safetensors", 0.97, 1.0),
    "Clone": ("jvnv-M2-jp", "jvnv-M2-jp_e159_s17000.safetensors", 0.97, 1.0),
    "Wolf": ("jvnv-M2-jp", "jvnv-M2-jp_e159_s17000.safetensors", 0.86, 1.12),
    "Narration": ("jvnv-M1-jp", "jvnv-M1-jp_e158_s14000.safetensors", 0.96, 1.06),
}

KEYS = [
    ("Angry", r"angr|furious|rage|roar|battle cry|fierce|snarl|yell|scream|shout|growl|defiant|aggress|kiai|full power|furi"),
    ("Surprise", r"surpris|shock|startl|gasp|stunned|disbelief|wide-eyed|realiz|alarm|!\?"),
    ("Fear", r"fear|panic|terrif|desperat|urgent|frantic|strain"),
    ("Sad", r"sad|despair|weak|exhaust|pant|wheez|pain|hurt|broken|quiet|breath|faint|dying|tired|hoarse"),
    ("Disgust", r"contempt|disgust|sneer|scorn|arrogan|disdain|annoy|irritat|cold|menac|smug"),
]


def pick_style(l):
    d = (l.get("direction", "") + " " + l.get("kind", "")).lower()
    if l.get("speaker") == "Narration":
        return "Neutral", 1.0
    for style, pat in KEYS:
        if re.search(pat, d):
            w = 6.0 if l.get("kind") in ("shout", "effort") else 3.5
            if style == "Disgust":
                w = 2.0  # keep the cold rival subtle
            return style, w
    if l.get("kind") in ("shout",):
        return "Angry", 5.0
    if l.get("kind") in ("whisper", "thought"):
        return "Sad", 1.5
    return "Neutral", 1.0


def clean_text(ja):
    t = ja.replace("―", "、").replace("—", "、").replace("…", "…").strip()
    t = re.sub(r"[「」『』（）()]", "", t)
    return t


def main():
    from style_bert_vits2.constants import Languages
    from style_bert_vits2.nlp import bert_models
    from style_bert_vits2.tts_model import TTSModel
    bm = bert_models.load_model(Languages.JP, BERT)
    bm.float()  # checkpoint is fp16; CPU inference needs fp32
    bert_models.load_tokenizer(Languages.JP, BERT)
    models = {}
    script = json.load(open(os.path.join(B, "script.json")))
    os.makedirs(os.path.join(B, "voice"), exist_ok=True)
    want = set(sys.argv[1:])
    report = {}
    for sh in script["shots"]:
        for l in sh.get("lines", []):
            lid = l["id"]
            if want and lid not in want:
                continue
            out = os.path.join(B, "voice", lid + ".wav")
            if os.path.exists(out) and not want:
                continue
            spk = l.get("speaker", "Narration")
            mdir, wfile, pitch, length = VOICES.get(spk, VOICES["Narration"])
            if mdir not in models:
                models[mdir] = TTSModel(model_path=os.path.join(M, mdir, wfile), config_path=os.path.join(M, mdir, "config.json"),
                                        style_vec_path=os.path.join(M, mdir, "style_vectors.npy"), device="cpu")
            style, weight = pick_style(l)
            text = clean_text(l["ja"])
            if l.get("kind") in ("thought", "whisper"):
                length *= 1.05
            sr, audio = models[mdir].infer(text=text, language=Languages.JP, style=style, style_weight=weight,
                                           sdp_ratio=0.35 if spk != "Narration" else 0.2, noise=0.6, noise_w=0.8,
                                           length=length, pitch_scale=pitch, intonation_scale=1.15 if spk != "Wolf" else 0.9)
            audio = np.asarray(audio, np.float32)
            if audio.dtype != np.float32 or np.abs(audio).max() > 1.5:
                audio = audio / 32768.0
            audio = audio / (np.abs(audio).max() + 1e-9) * 0.9
            sf.write(out, audio, sr)
            report[lid] = {"style": style, "w": weight, "dur": round(len(audio) / sr, 2), "ja": text}
            print(lid, spk, style, round(len(audio) / sr, 2), text, flush=True)
    rp = os.path.join(B, "voice", "report_local.json")
    old = json.load(open(rp)) if os.path.exists(rp) else {}
    old.update(report)
    json.dump(old, open(rp, "w"), ensure_ascii=False, indent=1)


if __name__ == "__main__":
    main()
