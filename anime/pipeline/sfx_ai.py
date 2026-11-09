"""AI sound effects (AudioLDM2, CPU) for textured sounds + Gemini judge.

For each name in PROMPTS, generates an AudioLDM2 clip into build/sfx/ai/,
then asks a Gemini audio model to compare it against the procedural version
(build/sfx/proc/) for the intended sound, and copies the winner to
build/sfx/<name>.wav. Names not in PROMPTS just use the procedural version.
Usage: python3 sfx_ai.py [gen|judge|all]
"""
import base64
import json
import os
import shutil
import subprocess
import sys
import time

import numpy as np
import soundfile as sf

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
PROC = os.path.join(ROOT, "build", "sfx", "proc")
AI = os.path.join(ROOT, "build", "sfx", "ai")
FINAL = os.path.join(ROOT, "build", "sfx")
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

PROMPTS = {
    "rain_loop": ("Heavy rain falling on a wide open stone plain, steady downpour, no thunder, ambient field recording", 10.0),
    "thunder": ("A loud close thunder crack followed by long rolling thunder rumble", 6.0),
    "wind_gust": ("Strong howling wind gust blowing across an open wasteland", 4.0),
    "wolf_growl": ("A huge wolf growling deeply and menacingly, low snarl", 4.0),
    "wolf_roar": ("A giant monster wolf roaring loudly, powerful aggressive roar", 4.0),
    "water_wave": ("A large ocean wave surging and crashing, powerful rushing water", 4.0),
    "water_vortex": ("A powerful swirling water vortex, roaring whirlpool of rushing water", 5.0),
    "water_breath": ("A massive torrent of water blasting out like a fire hose, roaring water jet", 4.0),
    "steam_hiss": ("Thick steam hissing loudly from a large vent, continuous hiss", 4.0),
    "steam_burst": ("A huge burst of steam exploding outward with a whoosh", 3.0),
    "explosion": ("A big explosion with deep boom and debris", 4.0),
    "rock_crumble": ("Stone wall crumbling, rocks and rubble falling", 3.0),
    "tree_fall": ("A large tree cracking and falling to the ground with a heavy thud", 4.0),
    "body_fall": ("A person falling hard onto wet muddy ground, thud and splash", 2.0),
    "splash_big": ("A large heavy splash in water", 2.5),
    "footsteps_wet": ("Fast running footsteps splashing through shallow water", 3.0),
    "punch_heavy": ("A very hard punch impact, cinematic fight hit", 1.5),
    "sword_clash": ("Two metal swords clashing with a ringing metallic clang", 2.0),
    "sword_draw": ("A katana sword being drawn from its scabbard, metallic scrape and ring", 1.5),
    "crackle": ("Electric sparks crackling, static electricity arcs", 2.5),
    "heartbeat": ("A slow loud heartbeat, deep thump", 2.0),
}


def gen():
    import torch
    from diffusers import AudioLDM2Pipeline
    torch.set_num_threads(int(os.environ.get("THREADS", "4")))
    os.makedirs(AI, exist_ok=True)
    pipe = AudioLDM2Pipeline.from_pretrained("cvssp/audioldm2", torch_dtype=torch.float32)
    # transformers>=5: GPT2Model lost GenerationMixin helpers that diffusers' AudioLDM2 still calls
    from transformers.generation.utils import GenerationMixin
    lm_cls = pipe.language_model.__class__
    for attr in ("_update_model_kwargs_for_generation", "_extract_past_from_model_output", "_cache_dependant_input_preparation"):
        if not hasattr(lm_cls, attr) and hasattr(GenerationMixin, attr):
            setattr(lm_cls, attr, getattr(GenerationMixin, attr))
    for name, (prompt, dur) in PROMPTS.items():
        out = os.path.join(AI, name + ".wav")
        if os.path.exists(out):
            continue
        t = time.time()
        g = torch.Generator().manual_seed(42)
        audio = pipe(prompt, negative_prompt="low quality, music, speech, voice, distorted",
                     num_inference_steps=int(os.environ.get("STEPS", "60")), audio_length_in_s=dur,
                     generator=g).audios[0]
        audio = np.asarray(audio, np.float32)
        audio = audio / (np.abs(audio).max() + 1e-9) * 0.9
        sf.write(out, audio, 16000)
        print(name, f"{time.time() - t:.0f}s", flush=True)


def to48(src, dst):
    subprocess.run(["ffmpeg", "-loglevel", "error", "-y", "-i", src, "-ar", "48000", "-ac", "2", "-c:a", "pcm_f32le", dst], check=True)


def judge():
    import tts
    os.makedirs(FINAL, exist_ok=True)
    verdicts = {}
    vpath = os.path.join(FINAL, "judge.json")
    if os.path.exists(vpath):
        verdicts = json.load(open(vpath))
    for f in sorted(os.listdir(PROC)):
        name = f[:-4]
        dst = os.path.join(FINAL, name + ".wav")
        aip = os.path.join(AI, name + ".wav")
        if name not in PROMPTS or not os.path.exists(aip):
            shutil.copy(os.path.join(PROC, f), dst)
            continue
        if name in verdicts:
            pick = verdicts[name]["pick"]
        else:
            tmpa = os.path.join(AI, name + "_cmp.mp3")
            tmpb = os.path.join(PROC, name + "_cmp.mp3")
            subprocess.run(["ffmpeg", "-loglevel", "error", "-y", "-i", aip, "-ac", "1", "-b:a", "64k", tmpa], check=True)
            subprocess.run(["ffmpeg", "-loglevel", "error", "-y", "-i", os.path.join(PROC, f), "-ac", "1", "-b:a", "64k", tmpb], check=True)
            body = {"contents": [{"parts": [
                {"text": f"Intended sound effect for an anime fight scene: '{PROMPTS[name][0]}'. Clip A:"},
                {"inlineData": {"mimeType": "audio/mp3", "data": base64.b64encode(open(tmpa, 'rb').read()).decode()}},
                {"text": "Clip B:"},
                {"inlineData": {"mimeType": "audio/mp3", "data": base64.b64encode(open(tmpb, 'rb').read()).decode()}},
                {"text": "Which clip is more realistic, clean (no artifacts, no music/voice) and fits the intended sound better? "
                         "Reply JSON: {\"pick\": \"A\" or \"B\", \"scoreA\": 1-10, \"scoreB\": 1-10, \"why\": \"...\"}"}]}],
                "generationConfig": {"responseMimeType": "application/json"}}
            d = None
            for m in tts.CHECK_MODELS:
                d, err = tts.post(m, body, timeout=120)
                if d:
                    break
            try:
                txt = "".join(p.get("text", "") for p in d["candidates"][0]["content"]["parts"])
                v = json.loads(txt)
                v = v[0] if isinstance(v, list) else v
            except Exception:
                v = {"pick": "B", "why": "judge failed"}
            pick = "ai" if v.get("pick") == "A" else "proc"
            verdicts[name] = {"pick": pick, **v}
            json.dump(verdicts, open(vpath, "w"), indent=1)
            print(name, pick, v.get("scoreA"), v.get("scoreB"), v.get("why", "")[:120], flush=True)
            time.sleep(2)
        if pick == "ai":
            to48(aip, dst)
        else:
            shutil.copy(os.path.join(PROC, f), dst)


if __name__ == "__main__":
    mode = sys.argv[1] if len(sys.argv) > 1 else "all"
    if mode in ("gen", "all"):
        gen()
    if mode in ("judge", "all"):
        judge()
