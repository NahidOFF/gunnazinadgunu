"""Build the final timeline from build/script.json + generated voice clips.

- shots get absolute start times; a shot is extended so its voice lines fit
- lines inside a shot are placed at their `t`, pushed later to avoid overlap
- subtitles (Turkish) are timed to the voice clip with a readable minimum
Writes build/timeline.json (for render.py) and build/audio_events.json (for mix.py)
and build/output subtitles (SRT).
"""
import json
import os

import soundfile as sf

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
B = os.path.join(ROOT, "build")


def voice_dur(lid):
    p = os.path.join(B, "voice", lid + ".wav")
    if not os.path.exists(p):
        return None
    info = sf.info(p)
    return info.frames / info.samplerate


def srt_time(t):
    h, r = divmod(t, 3600)
    m, s = divmod(r, 60)
    return f"{int(h):02d}:{int(m):02d}:{int(s):02d},{int(round((s - int(s)) * 1000)):03d}"


def main():
    script = json.load(open(os.path.join(B, "script.json")))
    shots = script["shots"]
    t = 0.0
    subs, voices, sfx, music, rain = [], [], [], [], []
    missing = []
    for sh in shots:
        lines = sh.get("lines", [])
        cursor = 0.0
        for k, l in enumerate(lines):
            lid = l.get("id") or f"{sh['id']}_{k}"
            l["id"] = lid
            d = voice_dur(lid)
            if d is None:
                missing.append(lid)
                d = max(0.6, len(l.get("ja", "")) * 0.13)
            st = max(float(l.get("t", 0.0)), cursor)
            l["_st"], l["_d"] = st, d
            cursor = st + d + (0.12 if l.get("kind") in ("effort", "reaction") else 0.25)
        need = max([l["_st"] + l["_d"] for l in lines] or [0]) + (0.45 if lines else 0)
        sh["dur"] = round(max(float(sh.get("dur", 1.0)), need), 3)
        sh["start"] = round(t, 4)
        for l in lines:
            at = t + l["_st"]
            voices.append({"id": l["id"], "t": round(at, 3), "speaker": l["speaker"], "kind": l.get("kind", "speech"), "dur": l["_d"]})
            if l.get("tr"):
                style = {"thought": "thought", "narration": "narration"}.get(l.get("kind"), "speech")
                subs.append({"t0": round(at, 3), "t1": round(at + max(l["_d"] + 0.25, 0.9 + len(l["tr"]) / 17.0), 3),
                             "text": l["tr"], "style": style, "top": style == "narration", "speaker": l["speaker"]})
        for s in sh.get("sfx", []):
            sfx.append({"name": s["name"], "t": round(t + float(s.get("t", 0)), 3), "gain": float(s.get("gain", 1.0))})
        if sh.get("music"):
            music.append({"cue": sh["music"], "t": round(t, 3)})
        if sh.get("rain"):
            if rain and abs(rain[-1][1] - t) < 0.05:
                rain[-1][1] = t + sh["dur"]
            else:
                rain.append([t, t + sh["dur"]])
        t += sh["dur"]
    # resolve subtitle overlaps (same position)
    subs.sort(key=lambda s: s["t0"])
    for a, b in zip(subs, subs[1:]):
        if a["top"] == b["top"] and a["t1"] > b["t0"] - 0.08:
            a["t1"] = max(a["t0"] + 0.5, b["t0"] - 0.08)
    tl = {"width": script.get("width", 1920), "height": script.get("height", 1080), "fps": script.get("fps", 24),
          "look": script.get("look", {"bloom": 0.22, "grain": 0.012}), "shots": shots, "subs": subs, "duration": round(t, 3)}
    json.dump(tl, open(os.path.join(B, "timeline.json"), "w"), ensure_ascii=False, indent=1)
    json.dump({"duration": t, "voices": voices, "sfx": sfx, "music": music, "rain": rain},
              open(os.path.join(B, "audio_events.json"), "w"), ensure_ascii=False, indent=1)
    os.makedirs(os.path.join(ROOT, "output"), exist_ok=True)
    with open(os.path.join(ROOT, "output", "altyazi_tr.srt"), "w", encoding="utf-8") as f:
        for i, s in enumerate(subs, 1):
            f.write(f"{i}\n{srt_time(s['t0'])} --> {srt_time(s['t1'])}\n{s['text']}\n\n")
    print(f"{len(shots)} shots, {t:.1f}s ({t / 60:.1f} min), {len(voices)} voice lines, {len(subs)} subs, {len(sfx)} sfx, missing voice: {len(missing)}")


if __name__ == "__main__":
    main()
