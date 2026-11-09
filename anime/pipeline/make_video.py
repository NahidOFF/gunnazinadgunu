"""Render the whole timeline in parallel chunks, concat, and mux with the mix.

Usage: python3 make_video.py [--workers 4] [--out output/anime.mp4]
"""
import argparse
import json
import math
import os
import subprocess
import sys

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
B = os.path.join(ROOT, "build")


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--workers", type=int, default=4)
    ap.add_argument("--out", default=os.path.join(ROOT, "output", "dogaun_disi_anime.mp4"))
    ap.add_argument("--crf", type=int, default=17)
    args = ap.parse_args()
    tl = json.load(open(os.path.join(B, "timeline.json")))
    total = int(math.ceil(tl["duration"] * tl["fps"]))
    os.makedirs(os.path.join(B, "chunks"), exist_ok=True)
    # split on shot boundaries close to equal frame counts (keeps panel cache warm)
    bounds = [0]
    for w in range(1, args.workers):
        target = total * w / args.workers
        best = min((round(sh["start"] * tl["fps"]) for sh in tl["shots"]), key=lambda f: abs(f - target))
        bounds.append(best)
    bounds.append(total)
    bounds = sorted(set(bounds))
    procs = []
    parts = []
    for i in range(len(bounds) - 1):
        part = os.path.join(B, "chunks", f"part{i:02d}.mp4")
        parts.append(part)
        log = open(os.path.join(B, "chunks", f"part{i:02d}.log"), "w")
        procs.append(subprocess.Popen([sys.executable, os.path.join(ROOT, "pipeline", "render.py"), os.path.join(B, "timeline.json"), part,
                                       "--from", str(bounds[i]), "--to", str(bounds[i + 1]), "--crf", str(args.crf)], stdout=log, stderr=subprocess.STDOUT))
    for p in procs:
        p.wait()
        if p.returncode:
            sys.exit(f"render chunk failed ({p.returncode})")
    lst = os.path.join(B, "chunks", "list.txt")
    with open(lst, "w") as f:
        for p in parts:
            f.write(f"file '{p}'\n")
    video = os.path.join(B, "video_noaudio.mp4")
    subprocess.run(["ffmpeg", "-loglevel", "error", "-y", "-f", "concat", "-safe", "0", "-i", lst, "-c", "copy", video], check=True)
    os.makedirs(os.path.dirname(args.out), exist_ok=True)
    srt = os.path.join(ROOT, "output", "altyazi_tr.srt")
    cmd = ["ffmpeg", "-loglevel", "error", "-y", "-i", video, "-i", os.path.join(B, "mix.wav")]
    if os.path.exists(srt):
        cmd += ["-i", srt, "-map", "0:v", "-map", "1:a", "-map", "2:s", "-c:s", "mov_text", "-metadata:s:s:0", "language=tur"]
    else:
        cmd += ["-map", "0:v", "-map", "1:a"]
    cmd += ["-c:v", "copy", "-c:a", "aac", "-b:a", "256k", "-metadata:s:a:0", "language=jpn", "-movflags", "+faststart", "-shortest", args.out]
    subprocess.run(cmd, check=True)
    print("wrote", args.out)


if __name__ == "__main__":
    main()
