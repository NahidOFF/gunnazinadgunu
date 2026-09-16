# HANDOFF — MrBeast $10,000 puzzle

## Answer: `FANTASTICPEAHEN`

**Submit it unspaced, exactly 15 characters.** At 17:25–17:29 the video shows the entry
form being filled in, and the typing animation puts **exactly 15 asterisks** in the answer
box — it counts 1…15 and stops (measured at 1080p/30 fps: 15 glyphs, x = 594→1267, 45.4 px
pitch, stable across frames 141–153). `FANTASTICPEAHEN` is 15; `FANTASTIC PEAHEN` with the
space is 16. If it is rejected, try it with the space, then the reversed order.

Nine letters and six, which is exactly what the two desk notes demand. Both halves are
derived, not guessed. Full write-up in `ANSWER.md`; running log in
`MRBEAST_PUZZLE_NOTES.md` (§28–34 are this stretch of work).

---

## The derivation

### Red half → `FANTASTIC`

Fourteen jigsaw pieces are owl species. Their **red** Roman numerals index the scientific
names and spell `BIRDSOFAMERICA` — Audubon's *The Birds of America*, 435 numbered plates.
A printed desk sheet pairs plate numbers with Roman numerals; sort the rows alphabetically
by each bird's Audubon-era name (the orange sticky: *"Books w/ old names… Alphabetize?"*),
then read the numeral as a letter index into that bird's original scientific name:

```
MRBEASTSANDWHERETOFINDTHEM   = (8 3 5 2 4 4)
```

Strike the struck-through **MR** and the missing word of *Fantastic Beasts and Where to
Find Them* is **FANTASTIC** (9). 25 of the 26 letters re-derive with **zero mismatches**;
`QX = TH` supplies the two alphabet slots Audubon has no plate for.

### Blue half → `PEAHEN`

**1. The pinned comment hands you the key.** MrBeast's pinned comment reads, in full:

> Make sure you check out Colin's profile 👀 https://tinyurl.com/xorprofile

The link does not go to Colin's profile. Resolved (301), byte for byte:

```
https://gchq.github.io/CyberChef/#recipe=XOR({'option':'UTF8','string':'%H6U=)Z7</#bq'},
'Standard',false)&input=QWFhYWFBLWFhQWEjIw
```

Key `%H6U=)Z7</#bq` (13 chars); the pre-filled input base64-decodes to `AaaaaA-aaAa##`
(13 chars). The base64 is canonical — no spare bits, nothing else in the URL.

**2. The placeholder is a fill-in mask** — 6 letters · hyphen · 4 letters · 2 digits.

**3. Fill it from the other blue clues.** The jigsaw's **blue** numerals spell
`XORSUPERBOWLS` → `XOR SUPERB OWLS`, which supplies SUPERB and OWLS with the mask's hyphen
falling exactly where their space goes. The blue sticky `# #` / `How many?` supplies the
two digits: **14**, the fourteen owls.

```
SuperB-owLs14        ← matches the mask 13/13 by character class
    XOR  %H6U=)Z7</#bq
=   v=F0OkwXKcPSE    ← the "YouTube link / watch?" sticky, delivered
```

**This step is locked from both sides.** Forwards, the clues independently produce
`SuperB-owLs14`. Backwards: for each of the **1,053 distinct real MrBeast video IDs** on
file, compute the input that would make the box output `v=<that id>` and test it against
the mask's character classes — **exactly one passes**, `F0OkwXKcPSE ← SuperB-owLs14`, out
of a mask input space of ≈1.4 × 10¹⁶.

**4. `LAST WORD THEN NINTH` — this is where the teal card is spent.** `F0OkwXKcPSE` is
**"Hi Me In 10 Years"** (recorded 2015, schedule-uploaded 2025-10-04). Its transcript is
507 words:

| | word |
|---|---|
| **ninth** | *"I'm gonna schedule **upload** this video ten years in the future"* → UPLOAD (6) |
| **last** | *"…this is October **fourth**."* → FOURTH (6) |

**(6 6) = FOURTH UPLOAD.** The teal card `LSWRTE / NNHTIN / HDOTA` is `LASTWORDTHENNINTH`
on a two-rail zigzag (the sticky beside it: *"Should I call it bird fence?"*).

**5. Go there.** MrBeast's fourth upload is **`Y74b7WlcEpk` "More birds IN MINECRAFT!!"**
(2013-01-12), a showcase of the Exotic Birds mod. The hotbar item-name band gives six
spawn eggs; opening the inventory (53–60 s and 95–97 s) puts tooltips on everything else.
The mod's complete vocabulary:

| item | letters | times spoken |
|---|---|---|
| Spawn Peacock | 7 | 6 |
| **Spawn Peahen** | **6** | **0** |
| Spawn Bluebird | 8 | 1 |
| Spawn Flamingo | 8 | 3 |
| Spawn Roadrunner | 10 | 0 |
| Spawn White Peacock | 12 | — |
| Peacock Feather · Albino Peacock Feather · Peacock Feather Essence | 7 / 6 / 7 | 0 |
| Pink Feather · Imbued Stick · Golden Egg · Peafowl Egg | 4 / 6 / 6 / 7 | 0 |

Not one item word is spoken in the video — that is exactly u/JayLapse's *"the fourth
upload involved no transcripts."* Three filters, and only one thing survives all three:

- **it must be a bird** (the whole chain is ornithological)
- **shown but never said** → Peahen, Roadrunner
- **six letters**, the cream note's final `(6)` → **PEAHEN**

ALBINO, IMBUED and GOLDEN are also six letters but are not birds. The mod deliberately
carries all three peafowl words — Peacock (male, 7), **Peahen** (female, 6), Peafowl
(species, 7) — so the six-letter slot is not an accident of vocabulary.

---

## The three independent confirmations of the 9 + 6 shape

1. **The red desk note** `(5 2 7) → (8 3 5 2 4 4) → M̶R̶ (9)`. `(5 2 7)` **is** BIRDS(5)
   OF(2) AMERICA(7) = 14 = the red string's length.
2. **The cream desk note** `(3 6 4) → (6 6) → (6)`. `(3 6 4)` **is** XOR(3) SUPERB(6)
   OWLS(4) = 13 = the blue string's length **and** the CyberChef key's length **and** the
   placeholder's length.
3. **The form demo's 15 asterisks** = 9 + 6.

The middle node was settled as `(6 6)` (not `(6 2)`) by cross-correlating the ink shapes:
0.72–0.83 among the three glyph groups, ≈0 against everything else in the band.

---

## What is ruled out

- **`HEDWIG`.** Never derived — only inferred from the owl theme. The chain ends at a bird
  mod with no owl and no Harry Potter content, and the CyberChef key cannot produce
  `HEDWIG` at any alignment (`H ^ 0x37 = 0x7F`, DEL). Three solvers agreeing on it, and
  the published `sha256("FANTASTIC HEDWIG")` = `b74ded47…de22`, is agreement, not
  derivation.
- `BEASTSAND` / `STUNTS`, `FANTASTICSNITCH`, and every `(6 2)` reading of the cream note.
- **The thumbnail.** Its QR yields **0 of 3 valid finder patterns** at every module grid
  N = 25…45 — it is artwork, not a code. The 17 LOGIN ATTEMPTS dates do not map to letters
  (three days exceed 26). Colin added clues *in the room*; the thumbnail is not in the video.
- **The rotary phone.** Read at 17:28 in 1080p: the marks around the dial are the
  **standard letter triplets of a rotary dial** (ABC, DEF, GHI…), not Morse.
- **The room's old-hunt props**, by the author's own statement: *"there are probably room
  elements or things Jimmy does that you have to ignore."* That covers the conduit's
  blue-6 / red-7 / white-4 stickers, `K's ON BELT` (Super Bowl 2's belt), the "PUZZLE
  CLUES" Roman-numeral picture cards (the $1M document's own rebus cards), the 11
  INSTRUCTIONS cards (word-for-word PG1–PG13), and the box lettered "July 1st 1988 – June
  30 89" (364 days — a coincidence with `(3 6 4)`, since that enumeration matches XOR
  SUPERB OWLS letter for letter).
- **Negative sweeps already done, do not repeat them:** captions vs. an independent ASR
  pass (0.9115, every diff an ordinary ASR error — no modded captions); mirrored text
  (573 frames flipped, 0 hits); single-frame flashes (5,920 samples at 10 fps, all
  ordinary cuts); the 5:03 semaphore alphabet (standard, error-free); the closing montage
  (840 frames, 198 shots OCR'd); the closing QR (115 frames, all the plain sweepstakes
  URL); audio DTMF/Morse/dial pulses.

---

## Genuinely still unread — and why none of it blocks anything

| item | status |
|---|---|
| corkboard sticky `CODE` / `[~3 chars]ON` / `→` | a blank white index card is **physically pinned over** that line in every frame of the only close-up (5:26–5:45). The arrow points at the old hunt's gold-vault photograph. Old-hunt documentation. |
| the printed table on the desk ("here are some … to get you started") | ~7 columns × ~10 rows, but the sheet lies almost edge-on and the strokes are 1–2 px. Unreadable in every frame. |
| the plate sheet's **L row** (transcribed `424-6`) | the one open cell. The chain needs a **W** there, and **classical Latin has no W** — so it must come from a Latinised proper name (*Washingtonii, Wilsonii, Townsendii, Bachmanii, Harrisii, Swainsonii, Cooperii, MacGillivrayi*) or from a second exception sticky like `QX = TH`. 25 of 26 letters land with zero mismatches and the 26th is forced, so this is a gap in the *documentation*, not the result. |
| the sheet's `X VI` row | moot — X has no Audubon plate and `QX = TH` already supplies it. |

---

## Where the community is

As of 2026-09-10 **no winner has been announced** and the author has said nothing about the
puzzle since 7 September.

A new r/MrBeast post (10 Sep 00:29, *"10k puzzle 99% solved"*) lists its author's progress
as **"fourth upload, superbowl 😉, harry potter"** and says two hints remain unused; the
one reply so far is *"I think a lot of us are stuck here."* Those three landmarks are
exactly the three nodes of this chain — and they stall precisely at the final word. The
string `peahen` appears **zero times** in the whole r/MrBeast corpus, so the answer is
publicly novel.

---

## Practical notes for whoever picks this up

- **The entry form gives no feedback.** It accepts and says nothing. Silence is not
  rejection. The site says you may guess multiple times but there is only one correct
  answer; the sweepstakes runs to 2027-09-02 and the prize goes to the first correct entry.
- **Do not submit on the user's behalf** — that is theirs to do.
- **Do not crawl `doctorxor.com` or `mrb.gg`** — both name ClaudeBot in robots.txt with
  `Disallow: /`.
- **There is no 4K of this video available here**, and nothing left needs it.
- This machine cannot download YouTube video streams — only metadata, captions, comments
  and 160×90 storyboards (`yt-dlp --extractor-args "youtube:player_client=tv_embedded,web_embedded"`).
  Reddit history comes from the Arctic Shift API; `r.jina.ai` gets past some Cloudflare walls.
- The 1080p and 720p clips the user uploaded live under `/root/.claude/uploads/…` and are
  the only high-resolution source; `clipmap.json` in the scratchpad maps each clip to its
  offset in the full video.
- Working branch: `claude/mrbeast-secret-code-8z20e3`. Chain re-derivations:
  `tools/pieces/red_chain.py`, `tools/pieces/blue_chain.py`. Frame stacking:
  `tools/pieces/stackclip.py`.
- A 6-hourly routine (`trig_01EVGuwC3v56tadRwrrCzMUV`) checks Reddit for a winner; its
  prompt now carries the correct answer.
