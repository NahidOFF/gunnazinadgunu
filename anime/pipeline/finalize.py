"""Deliver the episode: stream the master render frame by frame, replace the
frames inside build/fix_windows.json with freshly rendered ones, and encode
1080p + 720p in one pass (constant memory), muxing build/mix.wav and soft
Turkish subtitles.
"""
import json
import math
import os
import subprocess
import sys

import numpy as np

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
B = os.path.join(ROOT, "build")
OUT = os.path.join(ROOT, "output")
NAME = "dogaun_disi_anime"
sys.path.insert(0, os.path.join(ROOT, "pipeline"))


def main():
    from render import Renderer
    tl = json.load(open(os.path.join(B, "timeline.json")))
    W, H, fps = tl["width"], tl["height"], tl["fps"]
    total = int(math.ceil(tl["duration"] * fps))
    wins = json.load(open(os.path.join(B, "fix_windows.json"))) if os.path.exists(os.path.join(B, "fix_windows.json")) else []
    patch = set()
    for w in wins:
        patch.update(range(max(0, int(w[0] * fps) - 6), min(total, int(math.ceil(w[1] * fps)) + 6)))
    R = Renderer(tl)
    os.makedirs(OUT, exist_ok=True)
    dec = subprocess.Popen(["ffmpeg", "-loglevel", "error", "-i", os.path.join(B, "video_noaudio.mp4"),
                            "-f", "rawvideo", "-pix_fmt", "rgb24", "-"], stdout=subprocess.PIPE, bufsize=W * H * 3 * 4)
    a = ["-c:a", "aac", "-b:a", "192k", "-metadata:s:a:0", "language=jpn",
         "-c:s", "mov_text", "-metadata:s:s:0", "language=tur", "-movflags", "+faststart", "-t", f"{total / fps:.3f}"]
    enc = subprocess.Popen(
        ["ffmpeg", "-loglevel", "error", "-y", "-f", "rawvideo", "-pix_fmt", "rgb24", "-s", f"{W}x{H}", "-r", str(fps), "-i", "-",
         "-i", os.path.join(B, "mix.wav"), "-i", os.path.join(OUT, "altyazi_tr.srt"),
         "-filter_complex", "[0:v]split=2[v1][v2];[v2]scale=1280:720:flags=lanczos[v720]",
         "-map", "[v1]", "-map", "1:a", "-map", "2:s", "-c:v", "libx264", "-preset", "medium", "-crf", "20",
         "-maxrate", "5M", "-bufsize", "10M", "-pix_fmt", "yuv420p", "-x264-params", "threads=3", *a,
         os.path.join(OUT, f"{NAME}_1080p.mp4"),
         "-map", "[v720]", "-map", "1:a", "-map", "2:s", "-c:v", "libx264", "-preset", "medium", "-crf", "22",
         "-maxrate", "2.5M", "-bufsize", "5M", "-pix_fmt", "yuv420p", "-x264-params", "threads=2", *a,
         os.path.join(OUT, f"{NAME}_720p.mp4")],
        stdin=subprocess.PIPE)
    n = W * H * 3
    f = 0
    while True:
        buf = dec.stdout.read(n)
        if len(buf) < n:
            break
        if f in patch:
            buf = R.frame_at(f).tobytes()
        enc.stdin.write(buf)
        f += 1
        if f % 1200 == 0:
            print(f"{f}/{total}", flush=True)
    enc.stdin.close()
    enc.wait()
    dec.wait()
    print("done", f, "frames; patched", len(patch), "returncode", enc.returncode)
    if enc.returncode:
        sys.exit(1)


if __name__ == "__main__":
    main()
