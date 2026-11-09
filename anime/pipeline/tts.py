"""Gemini TTS for Japanese voice lines, with free-tier aware fallback + verify.

Reads build/script.json (lines with id, speaker, ja, direction) and writes
build/voice/<id>.wav (24 kHz mono). Each take is transcribed back by a Gemini
text model and compared to the intended Japanese; mismatches are retried.
API key from env GEMINI_API_KEY (never stored in the repo).
Usage: python3 tts.py [line_id ...]
"""
import base64
import json
import os
import subprocess
import sys
import time
import urllib.error
import urllib.request

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
VOICE = os.path.join(ROOT, "build", "voice")
KEY = os.environ.get("GEMINI_API_KEY", "")
API = "https://generativelanguage.googleapis.com/v1beta/models/{m}:generateContent?key=" + KEY
TTS_MODELS = ["gemini-3.8-flash-tts", "gemini-3.1-flash-tts-preview", "gemini-2.5-flash-preview-tts", "gemini-3.8-flash-lite-tts"]
CHECK_MODELS = ["gemini-3.5-flash", "gemini-3-flash-preview", "gemini-2.5-flash", "gemini-flash-latest"]

CAST = {
    # speaker -> (voice name, persona for style prompt)
    "M": ("Fenrir", "a 17-year-old Japanese shonen anime protagonist, hot-blooded, raw, wounded but defiant"),
    "E": ("Orus", "a 17-year-old Japanese anime rival, cold, calm, controlled and menacing, low voice"),
    "Wolf": ("Algenib", "an ancient giant wolf spirit, deep, gravelly, slow, proud and arrogant"),
    "Narration": ("Charon", "a calm, serious Japanese anime narrator explaining a technique"),
    "Clone": ("Orus", "the same cold rival but slightly distant and hollow"),
}


def post(model, body, timeout=180):
    req = urllib.request.Request(API.format(m=model), data=json.dumps(body).encode(), headers={"Content-Type": "application/json"})
    try:
        with urllib.request.urlopen(req, timeout=timeout) as r:
            return json.load(r), None
    except urllib.error.HTTPError as e:
        try:
            err = json.load(e)
        except Exception:
            err = {"error": {"code": e.code, "message": str(e)}}
        return None, err
    except Exception as e:  # network
        return None, {"error": {"code": 0, "message": str(e)}}


def synth(text, voice, style):
    prompt = f"{style}\n{text}"
    body = {"contents": [{"parts": [{"text": prompt}]}],
            "generationConfig": {"responseModalities": ["AUDIO"],
                                 "speechConfig": {"voiceConfig": {"prebuiltVoiceConfig": {"voiceName": voice}}}}}
    last = None
    for attempt in range(8):
        for m in TTS_MODELS:
            d, err = post(m, body)
            if d and "candidates" in d:
                for p in d["candidates"][0].get("content", {}).get("parts", []):
                    if "inlineData" in p:
                        return base64.b64decode(p["inlineData"]["data"]), m
                last = {"error": {"code": -1, "message": "no audio part"}}
                continue
            last = err
            code = err["error"].get("code")
            if code in (429, 503, 500, 0, -1):
                continue  # try next model
            if code == 400:
                break
        time.sleep(min(60, 8 * (attempt + 1)))
    raise RuntimeError(f"TTS failed: {last}")


def transcribe(wav_path):
    b64 = base64.b64encode(open(wav_path, "rb").read()).decode()
    body = {"contents": [{"parts": [{"inlineData": {"mimeType": "audio/wav", "data": b64}},
                                    {"text": "Transcribe the spoken Japanese exactly (kana/kanji). Output only the transcription. If there is any English or non-Japanese speech, include it too."}]}]}
    for attempt in range(6):
        for m in CHECK_MODELS:
            d, err = post(m, body, timeout=90)
            if d and "candidates" in d:
                parts = d["candidates"][0].get("content", {}).get("parts", [])
                return "".join(p.get("text", "") for p in parts if not p.get("thought")).strip()
        time.sleep(10 * (attempt + 1))
    return None


def norm(s):
    import unicodedata
    s = unicodedata.normalize("NFKC", s or "")
    return "".join(ch for ch in s if ch.isalnum())


def similar(a, b):
    import difflib
    return difflib.SequenceMatcher(None, norm(a), norm(b)).ratio()


def to_wav(raw, path):
    # API returns raw 16-bit PCM 24 kHz mono (mime may say audio/wav or L16)
    fmt = [] if raw[:4] == b"RIFF" else ["-f", "s16le", "-ar", "24000", "-ac", "1"]
    # trim leading/trailing silence (some TTS models pad several seconds)
    trim = ("silenceremove=start_periods=1:start_threshold=-45dB:start_silence=0.05,"
            "areverse,silenceremove=start_periods=1:start_threshold=-45dB:start_silence=0.12,areverse")
    subprocess.run(["ffmpeg", "-loglevel", "error", "-y", *fmt, "-i", "-", "-af", trim, "-ar", "24000", "-ac", "1", path],
                   input=raw, check=True)


def main():
    os.makedirs(VOICE, exist_ok=True)
    script = json.load(open(os.path.join(ROOT, "build", "script.json")))
    lines = [l for sh in script["shots"] for l in sh.get("lines", [])]
    want = set(sys.argv[1:])
    report_path = os.path.join(VOICE, "report.json")
    report = json.load(open(report_path)) if os.path.exists(report_path) else {}
    for l in lines:
        lid = l["id"]
        if want and lid not in want:
            continue
        out = os.path.join(VOICE, lid + ".wav")
        if os.path.exists(out) and not want and report.get(lid, {}).get("ok"):
            continue
        voice, persona = CAST.get(l["speaker"], CAST["Narration"])
        style = (f"You are voice acting {persona}. Performance direction: {l.get('direction', '')}. "
                 f"Speak ONLY the following Japanese line, in natural native Japanese, nothing else:")
        best = None
        for take in range(3):
            raw, model = synth(l["ja"], voice, style)
            tmp = out + f".take{take}.wav"
            to_wav(raw, tmp)
            heard = transcribe(tmp)
            sc = similar(heard, l["ja"]) if heard is not None else 0.5
            dur = float(subprocess.run(["ffprobe", "-v", "error", "-show_entries", "format=duration", "-of", "csv=p=0", tmp], capture_output=True, text=True).stdout or 0)
            print(f"{lid} take{take} {model} score={sc:.2f} dur={dur:.1f}s heard={heard!r}", flush=True)
            if best is None or sc > best[0]:
                best = (sc, tmp, heard, model, dur)
            if sc >= 0.8 or len(norm(l["ja"])) <= 3:
                break
            time.sleep(4)
        os.replace(best[1], out)
        for t in range(3):
            p = out + f".take{t}.wav"
            if os.path.exists(p):
                os.remove(p)
        report[lid] = {"ok": best[0] >= 0.6, "score": round(best[0], 3), "heard": best[2], "model": best[3], "dur": best[4], "ja": l["ja"]}
        json.dump(report, open(report_path, "w"), ensure_ascii=False, indent=1)
        time.sleep(2)


if __name__ == "__main__":
    main()
