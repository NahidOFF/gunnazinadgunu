"""Merge act shot lists (+ Japanese QA fixes) into build/script.json and validate.

Input: build/acts_raw.json (list of acts, each a list of shots) and optional
build/qa.json ({"fixes": [{shot, k, ja?, tr?, direction?}]}).
Assigns line ids "<shot>_<k>", sanitises camera/fx values, drops unknown
sfx/music names (reported), and checks that every panel exists.
"""
import json
import os
import re

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
B = os.path.join(ROOT, "build")
SFX = set(f[:-4] for f in os.listdir(os.path.join(B, "sfx", "proc")) if f.endswith(".wav"))
MUSIC = {"opening", "tension_rain", "battle_1", "despair", "awakening", "wolf_theme", "battle_2", "chase", "climax",
         "mystery_steam", "ending", "silence"}


def main():
    acts = json.load(open(os.path.join(B, "acts_raw.json")))
    qa = json.load(open(os.path.join(B, "qa.json"))) if os.path.exists(os.path.join(B, "qa.json")) else {"fixes": []}
    fixes = {(f["shot"], f["k"]): f for f in qa.get("fixes", [])}
    shots, problems = [], []
    for ai, act in enumerate(acts):
        if not act:
            problems.append(f"act {ai + 1} missing")
            continue
        for sh in act:
            kind = sh.get("kind", "panel")
            if kind == "panel" or sh.get("panel"):
                pid = sh.get("panel")
                if not pid or not os.path.exists(os.path.join(B, "hd", pid + ".png")):
                    problems.append(f"{sh['id']}: missing panel {pid}")
                    continue
                sh["kind"] = "panel"
            cam = sh.setdefault("cam", {})
            for key in ("from", "to"):
                if key in cam:
                    c = list(cam[key]) + [1.0] * (3 - len(cam[key]))
                    cam[key] = [min(1, max(0, float(c[0]))), min(1, max(0, float(c[1]))), max(1.0, min(3.0, float(c[2])))]
            sh["dur"] = max(0.4, float(sh.get("dur", 1.5)))
            if str(sh.get("panel", "")).startswith("b3_16"):
                sh["rain"] = None  # clear-sky canyon: no rain
            sh["fx"] = [f for f in sh.get("fx", []) if isinstance(f, dict) and "type" in f]
            ok_sfx = []
            for s in sh.get("sfx", []):
                if s.get("name") in SFX:
                    ok_sfx.append(s)
                else:
                    problems.append(f"{sh['id']}: unknown sfx {s.get('name')}")
            sh["sfx"] = ok_sfx
            if sh.get("music") and sh["music"] not in MUSIC:
                problems.append(f"{sh['id']}: unknown music {sh['music']}")
                sh["music"] = None
            for k, l in enumerate(sh.get("lines", [])):
                f = fixes.get((sh["id"], k))
                if f:
                    for key in ("ja", "tr", "direction"):
                        if key in f and f[key] is not None or (key == "tr" and key in f):
                            l[key] = f[key]
                l["id"] = f"{sh['id']}_{k}"
                l["ja"] = re.sub(r"[「」『』]", "", l.get("ja", "")).strip()
                if l.get("tr") in ("", "null"):
                    l["tr"] = None
            shots.append(sh)
    json.dump({"width": 1920, "height": 1080, "fps": 24, "look": {"bloom": 0.22, "grain": 0.012}, "shots": shots},
              open(os.path.join(B, "script.json"), "w"), ensure_ascii=False, indent=1)
    nl = sum(len(s.get("lines", [])) for s in shots)
    print(f"{len(shots)} shots, {nl} lines, est {sum(s['dur'] for s in shots) / 60:.1f} min; {len(fixes)} QA fixes")
    for p in problems:
        print("WARN", p)


if __name__ == "__main__":
    main()
