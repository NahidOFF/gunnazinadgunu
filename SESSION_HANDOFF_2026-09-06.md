# Handoff — MrBeast $10,000 hidden puzzle · session of 2026-09-06

Self-contained. Written to be pasted into a fresh session. Every claim carries how
it was obtained. Labels: `[MEASURED]` = I measured it from the footage ·
`[QUOTED]` = verbatim from a primary source · `[INFERRED]` = reasoning ·
`[DEAD]` = tested and abandoned, do not redo · `[GUESS]` = flagged speculation.

Repo: `nahidingitabi/gunnazinadgunu`, branch `claude/mrbeast-secret-code-8z20e3`,
draft PR #1. Running log (Azerbaijani, ~10 500 lines): `MRBEAST_PUZZLE_NOTES.md`.
Earlier handoff: `HANDOFF.md` (§1–17). Contest background: `BRIEFING.md`.

---

## 0. The contest, in one paragraph

Video `82CX6WULNA0` on @MrBeast2, published 2026-09-02, 17:47 long. At 17:20 MrBeast
says a puzzle is **hidden inside the video**, made by **Colin Sanders (@doctorxor)**,
and the first correct answer wins **$10,000**. Entry is a form reached by the QR code
at 17:32 → `https://puzzle-video-sweepstakes.mrbeast.app`. Official rules `[QUOTED]`:
*"Clues to solving the Puzzle will be available in the Video."* — note it does **not**
say *only* or *all*. Contest runs to 2027-09-02. **Never submit anything to the form
yourself; all submissions belong to the user.**

---

## 1. ★★★★★ The author's own starting hint `[QUOTED]`

Colin Sanders, Twitch VOD `2864667604` (2026-09-03), transcribed by ASR:

> [131:04] *"So the starting hint is — you know, or maybe it's just a — it's a
> question. But the initial question is: **have you solved the jigsaw puzzle?**"*
> [132:47] *"**The jigsaw puzzle in MrBeast's video — the first thing you should do
> is look for a jigsaw puzzle.**"*
> [133:00] *"And that's as far as I'm going to say right now. It's just to get you started."*

Same stream, also `[QUOTED]`:
* *"I made it by myself. Yeah, it is not as big as the Super Bowl puzzle."*
  ⇒ a single-author, small-scale puzzle: expect **one chain**, not a 91-location hunt.
* On LLMs: *"I don't want to bother myself and go out of my way to add weird elements"*
  ⇒ **no deliberate anti-AI traps**; standard puzzle mechanics apply.
* He denied his own video *Riddle #0: The Hat Trick* (`aFo8P073eSY`) three times in its
  comments: *"This is not part of the 10k puzzle."*

**Consequence:** the fifteen paper jigsaw pieces are the confirmed entry point, and
*assembling them* (= finding the order) is a step the author intends, not our
assumption. But it is the **first** step — the fifteen letters need not be the final
answer.

---

## 2. What the jigsaw physically is `[MEASURED]`

**Fifteen** hand-cut paper pieces, white, taped onto the cardboard boxes in the office
set. They are **not in one pile** — they are stuck to different boxes around the room
(seen whole in the wide office frame at t = 19.8). So their physical adjacency is set
dressing, **not** the puzzle order.

Anatomy of a piece:
* Two Roman numerals, one **red**, one **blue**. Which sits above varies, so **colour
  is the only reliable discriminator**, never position.
* **One or two pictures** to the right of the numerals. Five pieces carry two pictures,
  ten carry one → **20 drawings** in total.
* Hand-cut edges: steps, wedges, waves, pennant points, sawteeth, swallowtails — **not**
  classic jigsaw knobs, so edge matching has to compare shapes, not tab-vs-blank.

---

## 3. ★★★★★ The mechanism — GC8. AIRRACK

The old Million Dollar Puzzle's answer key (84 pages, `https://mrb.gg/p/puzzle`) has on
**page 51** a puzzle built exactly like ours `[QUOTED]`:

> "Airrack receives a gift from Jimmy containing seven pictures in a Where's Waldo
> style… **There's a number or pair of numbers in the corner of each photo**…
> ANSWER: Airrack is identified by the item in the picture that contains the letters in
> his real name, ERIC. Here are those items, **with the letters indexed into those names
> by the numbers given**: ANNE RICE (A) · KYRA THE CLERIC (L) · GEORGE FRIDERIC HANDEL
> (G) · AMERICAN CHEESE (I/E) · CENTER ICE (E/R) · RICHIE RICH (R/I) · DALLAS MAVERICKS
> (S/A). After the first three letters, the letters diverge to spell a city and country:
> **Algiers, Algeria**."

**The rule:** each picture names a *thing*; the numbers are **letter indices into that
name**; one number of each pair builds string A, the other builds string B. A picture
with a *single* number contributes the **same letter to both strings** (that is how
ALG- is shared).

**Control, in code:** `tools/pieces/gc8solve.py` runs GC8's seven names first and exits
unless it prints `ALGIERS / ALGERIA`. It passes. Never trust its output for our cards
if the control ever fails.

Two rules that fall out of the mechanism:
1. **Name length ≥ max(red, blue)** — the mechanism's own filter, and our best tool.
2. Numerals index **one name per card**, not one per drawing. Proof: on the
   arrow+chart card blue IX = 9 overruns `bar chart` (8).

---

## 4. ★★★★★ The imaging method — this is the part worth copying

### 4.1 Multi-frame stacking (`tools/pieces/stackwin.py`)

Frame stacking failed **four times** in earlier sessions and was written off. The
missing step is step 4.

```
stackwin.py DIR x0 y0 x1 y1 OUT.png [SCALE]
```
1. Extract **every** frame of the shot: `ffmpeg -ss T0 -i CLIP -t DUR -vsync 0 out/f%04d.png`
2. Keep the sharpest 70 % by **Laplacian variance inside that window** (not the whole frame).
3. Register each to the sharpest with `cv2.findTransformECC`, `MOTION_HOMOGRAPHY`,
   300 iterations, eps 1e-8, 5 px Gaussian.
4. **Drop every frame whose correlation < 0.90.** ← without this the stack averages in
   motion blur and comes out *worse* than the best single frame.
5. Mean (not median), then 14 iterations of iterative back-projection at 3×
   (Gaussian σ = 0.45·S, step 0.7).

Measured gain: card 10's numeral strip, Laplacian variance **55.6 → 350.2**.
On a locked-off camera it keeps 46 of 46 frames at correlation 0.998. On handheld it
keeps 7–25 and is still clearly better. It does **not** converge when a person moves
through the window — there, fall back to the sharpest single frame.

### 4.2 Rendering after the stack
White-balance on the card's **own paper** (mean of the brightest 82 %), stretch L\* between
the 2nd and 98th percentile, multiply a\*/b\* by 1.9–2.2, then a light sharpening kernel.
Upscale with `INTER_LANCZOS4` at 16–26×.

### 4.3 Rotate the paper
Every desk note is rotated 90° or 180° in frame. **That is why nobody had read them.**
Stack, then `cv2.rotate` and look at all four orientations.

### 4.4 Find the best shot **per piece**, not one global best frame
REF803 (t = 803.53) is *not* the closest view of everything. Template-match a REF803 crop
of the piece into candidate frames at scales 0.4–2.6 (`TM_CCOEFF_NORMED`) and read off the
winning scale.

**Shots that show pieces** (video seconds; 1080p clips in `/root/.claude/uploads/…`):

| shot | clip | what it is best for |
|---|---|---|
| **19–22** | `94b4d23f` | whole office in one frame; the only view of piece 15 |
| **323.5–325.4** | `a16ce518` | **desk push-in; frames 68–85 give the clearest view of the top box in the whole video** |
| **337.0–339.2** | `a16ce518` | locked-off camera, 46 frames |
| **764.9–767.8** | `1bc10ec4` | 85-frame take; pieces 4–8 are **1.1× larger** than in REF803 |
| **803.4–807.0** | `67592638` | the box stack (REF803, REF806) |
| **1045.8–1047.8** | `dd608937` | the entry form being typed |

Clip time = video time − offset; offsets are in `tools/pieces/clipmap.json`.

---

## 5. The read table `[MEASURED]`

Every numeral below was read from a stacked render at 20–32×. Thirteen of fifteen
pieces have both numerals.

| # | drawing(s) | red | blue | name ≥ |
|---|---|---|---|---|
| 1 | elf/gnome figure: green pointed hat, **red coat, green trousers**, orange hair, one arm raised, holding a dark-red object | **II** 2 | **XI** 11 | 11 |
| 2 | **picture completely hidden** under piece 3 in every angle | **VII** 7 | **I** 1 | 7 |
| 3 | rectangle filled with **~7 vertical bars** — cage / barred window / gate | ? | ? | — |
| 4 | **⬇ down arrow** + **4 increasing bars** (blue-grey, magenta, yellow, green) | **VIII** 8 | **IX** 9 | 9 |
| 5 | **bow** — two loops with a central knot, dark outline | **V** 5 | **VII** 7 | 7 |
| 6 | tall **terracotta/maroon filled rectangle**, rounded corners | **VI** 6 | **VIII** 8 | 8 |
| 7 | **spiral-bound calendar**, reddish glyph (reads "25") | **II** 2 | **IV** 4 | 4 |
| 8 | **black wedge** (wide top, tapers down) + **tall teal rectangle with magenta bands at both ends and a thin dark line down the middle** | **VI** 6 | **VI** 6 | 6 |
| 9 | 😂 face with tears of joy | **X** 10 | **XIV** 14 | 14 |
| 10 | brown-gold **ovoid** + **bald eagle** (dark body, white head, hooked beak) | ~**VIII** 8 | ~**IX** 9 | 9 |
| 11 | 🇴🇲 Oman flag | **VI** 6 | **V** 5 | 6 |
| 12 | dark **silhouette** + **potted plant with long spiky green leaves** | **IV** 4 | **VIII** 8 | 8 |
| 13 | 🌨 cloud with snow | **IX** 9 | **V** 5 | 9 |
| 14 | 🇺🇸 US flag + **red barn, grey gambrel roof, cupola** | **VII** 7 | **IV** 4 | 7 |
| 15 | dark notched form, on a separate small box, far from camera | ? | ? | — |

**Corrections made this session** (all were mine, or long-standing):
* piece 1 blue is **XI**, not XII — four frames at 26× in the t=324 shot show `X` + **one**
  `I`; in REF803 the card's own edge line reads as a second stroke. Name needs **11**, not 12.
* piece 2 red is **VII**, not VIII.
* piece 8 is **VI/VI**, not VII/VII. Still equal, so that position carries the same
  letter in both strings — the GC8 shared-letter case.
* piece 3's drawing is **vertical bars**, not "a thick frame with two panels".
* piece 4's left object is a **down arrow**; the small blue-grey rectangle under it is
  the chart's shortest bar, not a pedestal.

### Letters that are robust to which candidate name is right
* **piece 14 → red `A`, blue `R`** — 7 and 4 both land inside "AMERICAN", so
  `american barn`, `american gothic` and `american farm` all give the same pair.
* **piece 11 → blue `O`** — for both `flag oman` and `flag of oman`.
* **piece 1 → red `A`, blue `E`** — `garden gnome`(11) and `santas helper`(12) agree.
* piece 9 → red `E`, blue `O` (`face with tears of joy`, 18, essentially forced by ≥14).
* piece 13 → red `H`, blue `D` (`cloud with snow`, 13) — or `D`/`C` if `snow cloud`(9).
* piece 5 → red `E`, blue `F` (`butterfly`, 9) — `ribbon`(6) fails the ≥7 filter.

---

## 6. The answer is 15 characters `[MEASURED]` — re-verified from scratch

Form animation: **t = 1045.8 – 1047.8**, typing runs 1046.5 → 1047.4, then the screen
scrolls to Policy/SUBMIT. Method: column projection over the band `g[500:585, 480:1250]`
at four brightness thresholds (86/88/90/92 percentile), keeping **only rows whose
inter-glyph spacing is actually regular** (std/mean < 0.12).

| frame | t | threshold | asterisks | spacing | std |
|---|---|---|---|---|---|
| 40 | 1047.13 | 88 % | **15** | 44.8 | 2.37 |
| 43 | 1047.23 | 88 % | **15** | 44.7 | 2.05 |
| 45 | 1047.30 | 86 % / 88 % | **15** | 44.3 / 44.6 | 2.30 / 1.89 |
| 47 | 1047.37 | 86 % | **15** | 44.5 | 1.92 |
| 48 | 1047.40 | 86 % | **15** | 44.3 | 1.91 |

Six independent (frame, threshold) pairs give exactly 15. Lower thresholds split each
asterisk's six arms and inflate the count to 16–21 — the regularity test rejects those
(std 10–40). The rules specify no length or format, so this is the only length constraint.

---

## 7. The four desk notes — three of them are NOT old-puzzle material `[MEASURED]`

The room is dressed as Colin's solving room. Each paper was searched in the 84-page
answer document (control terms `Moscow`, `Wichita`, `Algiers`, `Sucre` all extract, so
the search is sound).

### 7.1 Blue sheet — **old**, and read in full for the first time
Stacked 42 frames of the 767 take, rotated upright:

```
( 3 6 4 )        ( 4 4 4 5 )
       ↘            ↙
          ( 6 6 )
             ↓
            ( 6 )
```

`(3 6 4)` = **RED SQUARE CUBE**, the old puzzle PG3 (all-red Rubik's cube, cube = square
→ Red Square) → `(6 6)` = **MOSCOW RUSSIA** → `(6)` = **MOSCOW**. Verbatim in the
document at "PG3. Rubik's cube… It's entirely red… the resulting concept, Red Square, is
a place in Moscow, Russia."

⚠ **Every earlier session recorded only the `(3 6 4)` input.** The second input
**`(4 4 4 5)`** had never been seen. No 4-4-4-5 word pattern in the answer document
corresponds to it (automated search: 10 hits, all accidental word runs). **Open question.**

★ The note's *shape* is a template: `A ↘ result ↙ B → final`.

### 7.2 Red sheet — **no counterpart in the old document**
Stacked 22–25 frames, rotated upright:

```
( 5 2 7 )
    ↓
( 8 3 5 4 4 )
    ↓
~~M R~~  ( 9 )
```
The digits are certain. The last line has a **struck-out "MR"** before `(9)`. Unlike the
blue note this chain is **linear** — no second input.
Neither `(5,2,7)` nor `(8,3,5,4,4)` matches anything in the 84 pages.
`[GUESS]` `(5,2,7)` fits **WHEEL OF FORTUNE** exactly — but `wheel` and `fortune` occur
**zero** times in the document. `[GUESS]` MrBeast's surname **DONALDSON is 9 letters**,
which is suggestive next to `~~MR~~ (9)`. Both flagged, neither relied on.

### 7.3 Teal cipher card — **no counterpart**, and it decodes to an instruction
Three lines `LSWRTE / NNHTIN / HDOTA`, caption *"Should I call it bird fence?"*.
Verified independently, not taken on trust:

```
LASTWORDTHENNINTH                       (17 letters)
rail 1 (even positions):  L S W R T E N N H  -> "LSWRTENNH"
rail 2 (odd positions):   A T O D H N I T    -> reversed "TINHDOTA"
concatenated:             LSWRTENNHTINHDOTA
the card's three lines:   LSWRTE + NNHTIN + HDOTA = LSWRTENNHTINHDOTA   ✓ identical
```
⇒ the card says **`LAST WORD THEN NINTH`** (two-rail rail fence, lower rail reversed).
`rail fence`, `ninth`, `last word`, `LSWRTE`, `HDOTA` — **zero** hits in the old document.

**This is a decoded instruction that has never been applied to the jigsaw.** The author
says the jigsaw is only the *first* step. The obvious chain to test the moment the order
is known: `jigsaw → text → LAST WORD THEN NINTH → answer`. Tried and failed as targets:
the video description (last word "com"), the caption tail (last word "video"), the
answer document (last word "CONTENTS").

### 7.4 Mint sticky — **no counterpart**
Three lines: `YouTube` / `link` / `watch?`. Read for the first time this session.

### 7.5 Also on the desk
An orange sticky reading *"Books w/ old names. **Alphabetize?**"*, and a sheet with
**`$10,000!`** hand-written in purple marker (not noticed by any session before).

⚠ **Honest limit:** the answer document is a summary, not a prop inventory, and the room
is dressed as Colin's *personal* solving room — so "absent from the document" is not
proof of "new". But the blue note matches word-for-word while the other three leave no
trace at all, and that asymmetry held up twice.

---

## 8. `[DEAD]` — tested and refuted, do not redo

| what | why it is dead |
|---|---|
| **Domino chain** (a piece's right numeral equals the next piece's left) | With both numerals known for 13 pieces the value multiset has **eight odd-degree values**; an Eulerian path needs 0 or 2, and the two unread pieces can change at most four. |
| **Order from the numerals** | All four obvious sort keys — red, blue, sum, difference — have ties. |
| **Two strings = a 15/15 city + country pair** | Bipartite match of six constrained pieces against **3762** fifteen-letter place strings (city, city+country, city+state, countries, US states, from geonamescache) returns **0**. The four-piece version returned thousands, so the filter is real. Consistent with the old hunt's meta-answer having been a **code** (R62L39R05…), not a location. |
| **Pure CLDR-emoji naming** | There is no barn emoji and no ≥11-letter CLDR name for the elf figure. Names are ordinary names, as in GC8. |
| **"Numeral tracks name length" as evidence** | Spearman 0.648 over 10 pieces looks supportive, but the names were *chosen* to pass the `len ≥ max(numeral)` filter — the correlation is manufactured. Recorded, not relied on. |
| **Black numeral = position (a permutation of I–XV)** | Duplicate blue values are real: V on both Oman and snow, VIII on both silhouette and rectangle. |
| **Numeral = length of the drawing's name** | Card 2's blue is I = 1 and card 1's red is II = 2; no drawing has a one- or two-letter name. |
| **Charlotte Amalie / U.S. Virgin Islands** | The only 15/15 gazetteer pair, and it dies on the joy card: that position needs `E`/`O`, and USVIRGINISLANDS has neither. |
| **Date reading** (red = month, blue = day) | closed in an earlier session |
| **Month-name indexing across 1082 CLDR locales** | closed |
| **Riddle #0 / The Hat Trick** | the author denied it three times, in writing |
| **"View corrections" info card** | a YouTube A/B artefact present on every video |
| **MP1–15 rebus style** | page 70 at 200 dpi: those are coloured squares with emoji arithmetic; ours are white, jigsaw-edged, pictures + two numerals |
| **Automatic piece segmentation on single frames** | fails; **it does work on stacks** — see §9 |
| **Frame stacking without the 0.90 correlation filter** | four failures; see §4.1 |
| Caption style layer · the 2018 retro edit · tinyurl siblings · the old playlist-endpoint pattern · mrb.gg `/p/` namespace · Selinker's Bluesky posts · the Hello Puzzlers episode · jigsaw teeth at ~8 px | all closed in earlier sessions |

---

## 9. Where it stands, and what to do next

**Solved:** the mechanism, the entry point (author-confirmed), the answer length,
13 of 15 numeral pairs, 4–6 letters that are robust to naming, three desk notes read
for the first time, one decoded but unapplied instruction.

**Blocked by physics:** piece 2's picture is under piece 3 in every angle; piece 3's
numerals are covered on one side or the other in every angle; piece 15 is too far away
in the only shot that contains it. There is no 4K source — **do not ask for one.**

**Open, in priority order:**

1. **Name the remaining pieces.** This is the binding constraint — everything downstream
   is mechanical once the names are in. Best instrument is a human eye on the stacked
   renders. The decision table with candidates and the letters each would give is at the
   end of `MRBEAST_PUZZLE_NOTES.md`. Hardest: piece 1 (needs ≥11), piece 8 (the black
   wedge + teal object), piece 3 (the barred form), piece 15.
2. **The order.** Automatic edge matching does not converge at 1080p — hole-filled
   segmentation on stacks gives clean outlines for four pieces (13, 12, 11, 9) but
   swallows the cardboard on piece 14, because the box is as bright as the paper. Two
   live routes: (a) catalogue the edge shapes by eye from `EDGES_STACK.png` and build the
   chain; (b) test **alphabetical by name** — cheap, independent of the jigsaw, and
   prompted by the desk sticky that says "Alphabetize?".
   **Rule: find the order independently first, then read the letters. Never pick an
   order because it produces a word** — I fell into that once already (the "FOOD"
   reading, which turned out to be every-other-card in an arbitrary catalogue order).
3. **Apply `LAST WORD THEN NINTH`** to whatever the jigsaw produces.
4. Piece 3 and piece 15's numerals; the second input `(4 4 4 5)` on the blue note; the
   pink index sheet on the desk (~5 lines, ~30 mark groups, ~2 px per mark — still
   unreadable).

**Standing constraints:** answer in Azerbaijani · never submit to the form yourself ·
do not brute-force or probe the entry endpoint · `doctorxor.com` and `mrb.gg` both name
ClaudeBot in `robots.txt` with a blanket `Disallow: /`, so no automated requests to
either (the user may open them in a browser) · never disable TLS verification.

---

## 10. Files worth having open

| path | what |
|---|---|
| `tools/pieces/stackwin.py` | the stacking tool of §4.1 |
| `tools/pieces/gc8solve.py` | the mechanism + its self-check; edit `CARDS` as names land |
| `tools/pieces/clipmap.json` | clip id → video-time offset |
| `tools/pieces/README.md` | the older warp/super-resolution toolchain and its calibration notes |
| `MRBEAST_PUZZLE_NOTES.md` | the full running log, newest at the bottom |
| `HANDOFF.md` §17 | the same session in condensed form |

Scratchpad renders referenced above live under
`/tmp/claude-0/-home-user-gunnazinadgunu/84fa90fa-750b-5180-b6a9-f390607e1640/scratchpad/`
and are ephemeral — they can all be regenerated from the clips with §4.
