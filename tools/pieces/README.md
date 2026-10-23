# Piece-reading toolchain

Everything used to read the jigsaw pieces off the box stack. Written for the
1080p footage; all of it works unchanged on higher-resolution clips, which is
what it is really waiting for.

Run these from a directory containing `clipmap.json`, with the clips in
`/root/.claude/uploads/*/`.

| script | use |
|---|---|
| **`pipe4k.py CLIPID T0 T1 [OUT]`** | **start here for a new clip.** Picks the sharpest reference frame in the range, builds the homography cache, auto-detects every piece outline, super-resolves each one and writes `OUT/ATLAS.png` — every piece, raw and contrast-stretched, side by side. |
| **`piecesr_ibp.py SPEC.json OUT.png [ITERS] [S]`** | **use this, not the median.** Same SPEC and registration as `piecesr.py`, but estimates the high-resolution image by iterative back-projection instead of taking a masked median, which recovers the sub-pixel information a median throws away. Measured on a control piece (US flag + barn, 96 frames): Laplacian variance 8.7 for the median against **49.9** for IBP. Set `S` so the low-resolution grid equals the piece's true pixel size — canonical width / S ≈ native width (e.g. 880/8 = 110 px). |
| **`piecesr.py SPEC.json OUT.png`** | fuses ONE piece across *several camera angles*. Each piece is its own plane, so a per-piece quad plus pyramid ECC (¼→½→1) can register shots that a single global homography cannot. `SPEC` = `{"canon":{"w":..,"h":..},"shots":[{"cache":"h803.npz","quad":[[x,y]×4]},…]}`; quads are in each cache's reference-frame coordinates, and the tool tries all four cyclic rotations and keeps the best-correlating one. |
| `homo.py CID REFT OUT.npz --range T0:T1 CX0 CY0 CX1 CY1` | ORB(15000)+RANSAC homography of every frame onto the reference |
| `warpreg.py CACHE REGIONS.json OUTDIR` | masked-median SR of listed regions from a cache |
| `sharp.py CID T0 T1 x0,y0,x1,y1 OUT [N] [SCALE]` | ranks frames by Laplacian variance over a crop |
| `allquads.py FRAME x0,y0,x1,y1 [minarea]` / `findquad.py` | piece outlines via `b* < 16 & L > 135`, returned as min-area-rect corners |
| `inkq.py IMG x0,y0,x1,y1:label …` | red-vs-blue verdict from Δa\* against the card's *own* paper (cancels the tungsten cast). Δa\* > +1.5 red, < +0.5 blue |
| `gwidth.py`, `strokes.py` | glyph width / stroke-run profiles — **both too noisy at 1080p**; numerals were read by eye off the fused images instead |
| `emomatch2.py CROP.png [N]` | ranks Noto Color Emoji glyphs against a picture crop (histogram + shape). **Fails its controls: 1 of 3.** Flags match well (Oman scored 0.95 vs 0.73 next); faces and pale prints do not. Do not trust it beyond flags. |

## Calibration notes

* Best 1080p frame of the box stack: **t = 803.527** (clip `67592638`), the
  first frame of the 803.49–806.96 shot. Laplacian variance 117 against 15 and
  51 in the neighbouring shots. Nothing in the video is closer to the boxes.
* A piece is ~45 px wide at 1080p; its numerals ~10 px. **There is no 4K of this
  video** — 1080p is the ceiling, so every gain has to come from the estimator
  and from fusing more shots per piece.
* Region coordinates passed to `warpreg.py` must lie inside the cache's `ctx`
  window, or the region comes back EMPTY.

## 2026-09-06 additions

**Use these first — they beat the super-resolution pipeline for these cards.**

- `clean.py IN.png OUT.png [k]` — white-balance a render on the card's own paper,
  stretch L, amplify chroma. Writes `[raw | balanced | chroma]` side by side.
- `picatlas.py` — 20x Lanczos crops of every drawing from `REF803.png`, one tile
  each, white-balanced per tile. Produces `PICTURES_ONLY.png`. **The best view of
  the pictures so far.**
- `sheet803.py` — the same idea but one tile per whole card (`PIECES_RAW803.png`).
- `quads2.py FRAME x0,y0,x1,y1 [minarea] [erode]` — like `allquads.py` but erodes
  before labelling, to pull touching cards apart. Does **not** separate the top
  box, whose cards physically overlap; hand-place those from a grid overlay.
- `gapsheet.py CID T0 T1 N OUT [cols]` — contact sheet over a time span.
- `cardsweep.py CID [step]` — ranks frames by the largest card-like white blob.
  Blunt: its size cap saturates on the desk sheets. Of limited use.

### Two rules that decided results on 2026-09-06

1. **The canonical canvas must match the quad's aspect ratio.** Compare
   `W/H` against the quad's own measured `w/h` before trusting any render.
   Three specs were stretched 2-5x; the "Africa" one was also in the wrong
   place, straddling two cards.
2. **The low-resolution grid must equal the piece's native pixel size**:
   `canon/S` must equal the quad's measured size. `sp_15.json` ran with a grid
   4.7x too large and produced noise; at S=16 the picture appeared.

Also: a quad must fully **contain** the numerals. A clipped stroke turned the
calendar's III into a II and nearly moved its date by a month.
