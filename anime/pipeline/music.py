"""Generate the soundtrack cues with MusicGen (stereo-small, CPU).

Each cue = one or more ~30 s segments; later segments continue from the tail
of the previous one (audio prompt) so long cues stay coherent.
Writes build/music/<cue>.wav (32 kHz stereo).
Usage: python3 music.py [cue ...]
"""
import os
import sys
import time

import numpy as np
import soundfile as sf

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
OUT = os.path.join(ROOT, "build", "music")

CUES = {
    "opening": ("epic japanese anime opening sting, huge taiko drum hits, shamisen flourish, orchestral brass swell, dark fantasy, cinematic, powerful", 1),
    "tension_rain": ("dark suspenseful ambient anime soundtrack, low strings drone, soft taiko pulses, tense and slow, cinematic underscore", 2),
    "battle_1": ("intense japanese anime battle music, fast taiko drums, aggressive staccato strings, distorted electric guitar riffs, shakuhachi accents, 160 bpm, action", 3),
    "despair": ("sad emotional anime soundtrack, slow solo piano and cello, melancholic, despair, quiet and heartbreaking", 2),
    "awakening": ("epic anime power awakening theme, rising choir, thunderous drums, building orchestral crescendo, dark and heroic, goosebumps", 2),
    "wolf_theme": ("majestic heavy anime theme for a giant spirit wolf, deep brass, male choir, slow war drums, ancient japanese flavor, powerful", 2),
    "battle_2": ("high energy shonen anime fight music, rock guitars and orchestra, driving drums, heroic and intense, fast 170 bpm", 3),
    "chase": ("fast pursuit anime action music, pulsing bass, rapid percussion, tense strings ostinato, urgent, 150 bpm", 2),
    "climax": ("epic climactic anime final battle music, full orchestra, choir, taiko drums, electric guitar, intense and emotional, huge", 3),
    "mystery_steam": ("eerie suspense anime soundtrack, foggy atmosphere, low drones, sparse percussion hits, glassy high textures, tension", 2),
    "ending": ("calm hopeful anime ending soundtrack, soft strings and piano, bittersweet and peaceful, open sky", 2),
}


def main():
    import torch
    from transformers import AutoProcessor, MusicgenForConditionalGeneration
    torch.set_num_threads(int(os.environ.get("THREADS", "4")))
    os.makedirs(OUT, exist_ok=True)
    name = "facebook/musicgen-stereo-small"
    proc = AutoProcessor.from_pretrained(name)
    model = MusicgenForConditionalGeneration.from_pretrained(name).float().eval()
    sr = model.config.audio_encoder.sampling_rate
    cues = sys.argv[1:] or list(CUES)
    for cue in cues:
        out = os.path.join(OUT, cue + ".wav")
        if os.path.exists(out):
            continue
        prompt, nseg = CUES[cue]
        audio = None
        t0 = time.time()
        for k in range(nseg):
            torch.manual_seed(100 + k)
            if audio is None:
                inp = proc(text=[prompt], padding=True, return_tensors="pt")
                with torch.no_grad():
                    a = model.generate(**inp, max_new_tokens=1500, do_sample=True, guidance_scale=3.5, temperature=1.0)
                audio = a[0].float().numpy()
            else:
                tail = audio[:, -sr * 6:]
                inp = proc(text=[prompt], audio=[tail], sampling_rate=sr, padding=True, return_tensors="pt")
                with torch.no_grad():
                    a = model.generate(**inp, max_new_tokens=1500, do_sample=True, guidance_scale=3.5)
                new = a[0].float().numpy()[:, tail.shape[1]:]
                audio = np.concatenate([audio, new], axis=1)
            print(cue, "seg", k, f"{time.time() - t0:.0f}s", audio.shape, flush=True)
        audio = audio / (np.abs(audio).max() + 1e-9) * 0.89
        sf.write(out, audio.T.astype(np.float32), sr)


if __name__ == "__main__":
    main()
