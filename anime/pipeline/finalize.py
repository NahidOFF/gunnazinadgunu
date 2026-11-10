"""Patch small re-rendered windows into the master render and make delivery encodes.

- re-renders every window in build/fix_windows.json (frame-accurate, padded)
- splices them into build/video_noaudio.mp4 via a trim/concat filter graph
- muxes the latest build/mix.wav and soft Turkish subtitles
- writes output/<name>_1080p.mp4 and output/<name>_720p.mp4 in one decode pass
"""
import json
import math
import os
import subprocess
import sys

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
B = os.path.join(ROOT, "build")
OUT = os.path.join(ROOT, "output")
NAME = "dogaun_disi_anime"


def main():
    tl = json.load(open(os.path.join(B, "timeline.json")))
    fps = tl["fps"]
    total = int(math.ceil(tl["duration"] * fps))
    wins = json.load(open(os.path.join(B, "fix_windows.json"))) if os.path.exists(os.path.join(B, "fix_windows.json")) else []
    ranges = sorted((max(0, int(w[0] * fps) - 12), min(total, int(math.ceil(w[1] * fps)) + 12)) for w in wins)
    merged = []
    for a, b in ranges:
        if merged and a <= merged[-1][1]:
            merged[-1][1] = max(merged[-1][1], b)
        else:
            merged.append([a, b])
    os.makedirs(os.path.join(B, "fix"), exist_ok=True)
    fixes = []
    for i, (a, b) in enumerate(merged):
        p = os.path.join(B, "fix", f"w{i:02d}.mp4")
        subprocess.run([sys.executable, os.path.join(ROOT, "pipeline", "render.py"), os.path.join(B, "timeline.json"), p,
                        "--from", str(a), "--to", str(b), "--crf", "10"], check=True, stdout=subprocess.DEVNULL)
        fixes.append((a, b, p))
        print("patched window", a, b, flush=True)
    inputs = ["-i", os.path.join(B, "video_noaudio.mp4")]
    for _, _, p in fixes:
        inputs += ["-i", p]
    inputs += ["-i", os.path.join(B, "mix.wav")]
    audio_idx = 1 + len(fixes)
    parts, cur, k = [], 0, 0
    graph = []
    for i, (a, b, _) in enumerate(fixes):
        graph.append(f"[0:v]trim=start_frame={cur}:end_frame={a},setpts=PTS-STARTPTS[m{k}]")
        parts.append(f"[m{k}]")
        k += 1
        graph.append(f"[{i + 1}:v]setpts=PTS-STARTPTS[f{i}]")
        parts.append(f"[f{i}]")
        cur = b
    graph.append(f"[0:v]trim=start_frame={cur},setpts=PTS-STARTPTS[m{k}]")
    parts.append(f"[m{k}]")
    graph.append("".join(parts) + f"concat=n={len(parts)}:v=1:a=0,split=2[v1][v2]")
    graph.append("[v2]scale=1280:720:flags=lanczos[v720]")
    srt = os.path.join(OUT, "altyazi_tr.srt")
    os.makedirs(OUT, exist_ok=True)
    common_a = ["-c:a", "aac", "-b:a", "192k", "-metadata:s:a:0", "language=jpn"]
    sub_in = ["-i", srt]
    sub_idx = audio_idx + 1
    cmd = ["ffmpeg", "-loglevel", "error", "-stats", "-y", *inputs, *sub_in, "-filter_complex", ";".join(graph),
           "-map", "[v1]", "-map", f"{audio_idx}:a", "-map", f"{sub_idx}:s",
           "-c:v", "libx264", "-preset", "medium", "-crf", "20", "-maxrate", "5M", "-bufsize", "10M", "-pix_fmt", "yuv420p",
           *common_a, "-c:s", "mov_text", "-metadata:s:s:0", "language=tur", "-movflags", "+faststart", "-shortest",
           os.path.join(OUT, f"{NAME}_1080p.mp4"),
           "-map", "[v720]", "-map", f"{audio_idx}:a", "-map", f"{sub_idx}:s",
           "-c:v", "libx264", "-preset", "medium", "-crf", "22", "-maxrate", "2.5M", "-bufsize", "5M", "-pix_fmt", "yuv420p",
           *common_a, "-c:s", "mov_text", "-metadata:s:s:0", "language=tur", "-movflags", "+faststart", "-shortest",
           os.path.join(OUT, f"{NAME}_720p.mp4")]
    subprocess.run(cmd, check=True)
    print("done")


if __name__ == "__main__":
    main()
