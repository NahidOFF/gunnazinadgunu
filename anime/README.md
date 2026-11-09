# Doğanın Dişi (自然の牙) — manga → anime pipeline

Turns the 48 uploaded manga pages (M vs E, rainy wasteland fight) into an animated
episode: Japanese voice acting, Turkish subtitles, music and sound effects, 1920×1080 @ 24 fps.

Everything runs on CPU in this repo's container; generated files go to `build/` and
`output/` (git-ignored). The Gemini API key is read from the `GEMINI_API_KEY`
environment variable only and is never written to the repo.

## Pipeline

| Step | Script | What it does |
|---|---|---|
| 1 | `pipeline/panels.py` | Finds panels from the white gutters (slanted panels get masks); writes crops and annotated pages |
| 2 | (workflow) | Agents analyse every panel (action, motion idea, dialogue, SFX), find duplicate/alternate pages and set the story order → `build/analysis.json`, `build/order.json` |
| 3 | `pipeline/clean.py` | RT-DETR comic text/bubble detector + LaMa-manga inpainting removes speech bubbles, captions and "!?" bursts |
| 4 | `pipeline/enhance.py` | Real-ESRGAN anime video v3 4× upscale + Depth-Anything-V2 depth map per panel |
| 5 | `pipeline/layers.py` | Depth-based foreground/background split; LaMa fills the background behind characters (true 2.5D parallax, character acting) |
| 6 | (workflow) | Director agents write the shot list per act (camera, acting, FX, Japanese lines, Turkish subs, SFX, music cues); a Japanese editor agent checks the dialogue (`build/SPEC.md` is the format) |
| 7 | `pipeline/merge_script.py` | Merges acts + QA fixes and checks them → `build/script.json` |
| 8 | `pipeline/tts_local.py` | Japanese voices with Style-Bert-VITS2 (JVNV emotional male voices, run with `/opt/sbv2_312/bin/python`); `pipeline/tts.py` is the Gemini TTS variant (free tier allows only 10 requests/day/model) |
| 9 | `pipeline/verify_voice.py` | Whisper transcribes every voice line back and compares it with the script |
| 10 | `pipeline/sfx.py`, `sfx_ai.py`, `sfx_clap.py` | 57 procedural SFX + AudioLDM2 variants; Gemini/CLAP pick the better one per sound |
| 11 | `pipeline/music.py` | MusicGen soundtrack cues (opening, battle, despair, awakening, wolf theme, chase, climax, steam, ending) |
| 12 | `pipeline/timeline.py` | Fits shots to the voice lengths, times the subtitles, writes `timeline.json`, `audio_events.json` and `output/altyazi_tr.srt` |
| 13 | `pipeline/mix.py` | Dialogue FX (wolf pitch/reverb, inner-voice echo), music ducking, rain ambience, loudness −16 LUFS |
| 14 | `pipeline/render.py`, `make_video.py` | 2.5D compositor (camera, parallax, rain, speed lines, impact frames, glow, crackle, particles, shake, subtitles) rendered in parallel chunks, then muxed with the audio and soft Turkish subtitles |

## Re-run (after assets exist)

```bash
python3 pipeline/merge_script.py
/opt/sbv2_312/bin/python pipeline/tts_local.py
python3 pipeline/timeline.py && python3 pipeline/mix.py
python3 pipeline/make_video.py --workers 4
```
