# MrBeast $10,000 puzzle — full cold-start briefing

Everything I have, written for someone with zero prior context. Paste this whole file into
a fresh assistant. The running research log is `MRBEAST_PUZZLE_NOTES.md` (1800+ lines, in
Azerbaijani); this file is the distilled English version.

**Confidence labels used throughout.**
`[MEASURED]` = I measured it myself from the source footage, text or a live fetch.
`[BORROWED]` = someone else's claim, plausible, not independently confirmed here.
`[INFERRED]` = reasoning on top of the above.
`[DEAD]` = tested and abandoned. Do not redo.

---

## 0. The task

MrBeast's video **"How 1 Person Solved A $1,000,000 Puzzle!"** — YouTube id `82CX6WULNA0`,
17:47 long, published 2026-09-02 on **@MrBeast2** — contains a **second, hidden puzzle
worth $10,000**, built by Colin Sanders (**@DoctorXOR**), the man who won the original
$1M hunt.

Transcript at 17:20 `[MEASURED]`:
> *"…there is a puzzle hidden within this video, created by Colin himself, and the first
> person to answer correctly wins $10,000."*

- Answer goes to **https://puzzle-video-sweepstakes.mrbeast.app/**
- Contest runs 2026-09-02 12:00 ET → 2027-09-02 11:59 ET, **or until the winning answer
  is received, whichever comes first** `[MEASURED, official rules]`
- **As of 2026-09-05 the site is byte-identical to my earlier copy (same md5), so nobody
  has won yet** `[MEASURED]`

### ★ THE SINGLE MOST IMPORTANT SCOPING RULE
There are **two puzzles** in play and they are constantly confused:
- the **old $1,000,000 hunt** (Super Bowl 2026, built by Lone Shark Games, solved by Colin)
- the **new $10,000 puzzle** (hidden in this video, built by Colin)

**The 84-page official answer key to the OLD hunt is a perfect filter: anything it
documents belongs to the old hunt.** Most of what is visible in the video is recap
dressing for the old hunt and is a waste of time. Section 3 below classifies every object.

### Rule of engagement
**Do not brute-force or probe the entry endpoint.** Nothing has been submitted from this
work. The site accepts multiple guesses, so a human owner can submit candidates freely,
but automated probing would be abuse.

---

## 1. Source material and how to get it

| thing | where |
|---|---|
| The video | YouTube `82CX6WULNA0` (@MrBeast2) |
| The 84-page official answer key to the **old** $1M hunt | linked from the video description as `https://mrb.gg/p/puzzle` → "Million Dollar Puzzle Answers", 84 pages, published 2026-09-01. Text extract kept locally at `scratchpad/site/puzzle_answers.txt` |
| Colin's channel | YouTube `@DoctorXOR`, channel id `UCG-K1h46MGpxrK4Aa9ygR-w` |
| MrBeast's pinned comment | *"Make sure you check out Colin's profile 👀"* plus a tinyurl to a CyberChef XOR recipe |
| Official rules | `https://puzzle-video-sweepstakes.mrbeast.app/official-rules` |
| Lone Shark Games (built the old hunt, credited in the description) | `https://lonesharkgames.com` |

### Access notes `[MEASURED]`
- **yt-dlp media download is blocked** from a datacenter IP: the visionos client still
  returns an m3u8, but AV1 (itag 399) crashes ffmpeg with SIGSEGV, and switching to H.264
  triggers *"Sign in to confirm you're not a bot"*. **4K does not exist for this work.**
- **yt-dlp metadata/channel listing sometimes works** between bot checks. Comment fetching
  is unreliable.
- **Invidious mirrors are also blocked** (403/401 from this IP): tried invidious.f5.si,
  inv.nadeko.net, yewtu.be, invidious.nerdvpn.de.
- WebFetch cannot render YouTube watch pages (returns only the footer).
- `mrbeast.salesforce.com` → 403.

### ★★ The resolution question is SETTLED: 1080p is enough
Both this session and another session worked from the same 1080p clips. **The difference
in what each could read was method, not resolution.** Stop asking for 4K. See section 2.

---

## 2. Tooling — this is the most transferable part of this work

Two scripts live in the scratchpad. They are what unlocked every read below.

### `srx.py` — multi-frame super-resolution

```
python3 srx.py CLIPID T0 T1 X0 Y0 X1 Y1 SCALE OUT.png [--sharp N] [--reftime T]
```

- `CLIPID` — 8-hex prefix of a source clip; `T0 T1` — **absolute video seconds**
- `X0 Y0 X1 Y1` — region in 1080p frame coordinates
- `SCALE` — output upscale factor (6–12 works)
- `--sharp N` — keep only the N sharpest frames before stacking
- `--reftime T` — **force the reference frame to time T**

It picks a reference frame, aligns every other frame onto it with **ORB features +
RANSAC homography** over a padded context window, warps each into a `SCALE`× grid and
averages.

**★ The single most important lesson of this whole project:**
The camera drifts and dollies through these shots, so the frames carry genuine sub-pixel
diversity and stacking really does add resolution. But the reference frame must be the one
where the object is **LARGEST**, not merely sharpest. Homography handles the scale change,
so distant frames still contribute to a close reference's grid. Before `--reftime` existed,
a 180-frame 4× stack of the jigsaw pieces resolved **no numeral at all**; with `--reftime`
pointed at the closest moment, a 161-frame 6× stack resolved them cleanly. The same fix
settled the telephone dial. **If a read fails, the first thing to check is whether you
picked the frame where the object is biggest.**

### `ink.py` — handwriting isolation and de-skew

```
python3 ink.py IN.png OUT_PREFIX [ANGLE|auto] [SIGMA]
```

Subtracts the object's **own blurred L\*** channel — this adds no information, but it
invents none either. Auto de-skew maximises row-profile variance. Prints a row-ink profile
so lines and character groups can be segmented and counted. Writes `*_ink.png` (dark ink on
white) and `*_rot.png`.

### Method rules — violating these produces false readings
1. **Never use deconvolution** (Richardson-Lucy, Wiener). Its ringing looks exactly like
   letters at this scale. Another solver had to retract a reading because of it.
2. **Count before you read.** Segment rows from the ink profile, then segment each row into
   character groups by column profile at 2–3 thresholds, and report the counts. A row of
   round letters and a row of vertical strokes segment very differently; the counts alone
   are often decisive when no glyph is legible.
3. **Report per-character confidence.** "Position 2 is a D (closed bowl), position 3 an O
   (ring with a hole), 1 and 4 unreadable" is a good answer; a confident full transcription
   you cannot defend character by character is a bad one.
4. **Say when you cannot read it.** A supported "5 rows, ~30 mark groups, content not
   recoverable" beats a guess.
5. **Do not fit to an expected answer.** Test the expected string as a hypothesis against
   the pixels and be willing to report that it fails.
6. **White-balance against the object's own paper** before judging ink colour. The set is
   lit with warm tungsten and it turns black ink reddish. My colour test is only reliable
   where a clean white paper reference sits inside the same crop.

### Clip map (`clipmap.json`) `[MEASURED]`
1080p clip coverage, derived by matching each clip's frames against a 1-fps signature
timeline built from three 360p clips that cover the whole video:

| clip id | covers (absolute video seconds) | what is in it |
|---|---|---|
| `94b4d23f` | 0.0 – 70.7 | **the office set** — desk, CRT, cards, boxes, both walls |
| `a16ce518` | 304.5 – 394.1 | corkboard room (old material) |
| `48b92c09` | 340.5 – 420.0 | corkboard room (old material) |
| `0f1d65d9` | 551.1 – 640.6 | corkboard room (old material) |
| `fba19fc0` | 854.9 – 931.4 | — |
| `fce1ee46` | 930.2 – 1025.0 | — |
| `dd608937` | 1008.3 – 1072.5 | **the closing set** — Zenith TV, phone, notepad |
| `29701bfa` | 1018.3 – 1050.4 | same closing set |

**1080p gaps: 1:11–5:05, 7:00–9:11, 10:41–14:15.** Three 360p clips (offsets 0.0, 400.68,
854.22) cover the whole video for locating shots.

---

## 3. The set — what is $10k material and what is old-hunt dressing

### ✅ $10,000 material (NOT in the 84-page key) `[MEASURED]`

**The office set** — clip `94b4d23f`, best around t = 16.6–22.0 s.
Coordinates below are 1080p frame coordinates at t ≈ 19.0 unless noted.

| object | box | status |
|---|---|---|
| CRT showing a `SalesForce MrBeast xp` boot screen | x 60–350, y 620–830 | decor |
| **teal cipher card** (5 rows: 3 cipher + 2 subtext) | x 215–320, y 768–812 at t=19; x 225–350, y 390–500 at t=20.83 | partly read, see §4 |
| **orange card**, last line a large `?` | x 305–465, y 365–500 at t=20.83 | `?` confirmed, text not |
| keyboard | x 165–390, y 820–880 | decor |
| **pink index sheet** (rows of short groups) | x 0–150, y 860–940; generous box x 0–240, y 840–1000 | structure only, see §4 |
| **olive / tan card** below the keyboard | ~x 280–400, y 580–640 at t=21 | unread |
| yellow sticky | right of the keyboard | unread |
| **black book reading `Boo!`** with a caption card | x 150–290, y 970–1080 | **"Boo!" read cleanly** |
| **left-wall conduit stickers** | x 30–60, y 500–540 | 3 discs: navy, cream, salmon |
| **right-wall conduit stickers** | x 1630–1670, y 290–560 | **6 (blue) / 7 (pink) / 4 (white)**, digits legible |
| **"PUZZLE CLUES" boxes** | x 1150–1560, y 780–1030 | label legible |
| **jigsaw piece cards** on the box stack | x 1690–1920, y 600–920 and x 1780–1920, y 940–1080 | numerals read, see §4 |
| **floor papers** bottom-right | x 1560–1920, y 940–1080 | one new handwritten sheet, see §4 |

**The closing set** — clips `dd608937` / `29701bfa`, t ≈ 1019–1060 s. One fixed camera
angle for the whole scene.

| object | box (1080p) | status |
|---|---|---|
| Zenith TV/VCR, front reads `COLOR TV-VCR COMBINATION`, `Z` logo | centre | shows **`PAUSE ⏸`** at 1019.9–1021.4 s |
| **rotary telephone** | x 280–700, y 840–1080 | **settled, see §4** |
| **spiral notepad** with the note | x 660–1000, y 990–1080 | **read, see §4** |
| green sticky note | left of the notepad | appears blank |
| cardboard box with a green tape strip | x 950–1920, y 840–1080 | **plain, nothing on it** |
| form / QR / `$10,000` screens | on the TV, 1046–1054 s | the entry flow |

### ❌ OLD $1M material — do not re-investigate `[MEASURED]`
- **The entire corkboard room** — photos of the old hunt, globes from its metapuzzle,
  crosswords, cryptic-trio cards, string links, a `META PUZZLE` label, pictorial rebus
  cards. Every category maps onto the answer key.
- The explanatory graphic at t = 44 s (nine sub-puzzle cards each captioned with one word,
  assembling into *"every challenge leads towards a location name somewhere around the
  world"*). It is the old hunt's own mechanism, shown on screen.
- The money-wall graphic at t = 68–70 s.
- `BEAST CITY` on the TV at t = 1029 s — the key contains *"letters in BEAST CITY HUB"*.
- The vault code `R62L39R05L73606623093121200300` and the whole 16:00–16:40 sequence.
- All MP / SB / PG / EP / GC / OP sub-puzzle answers.

---

## 4. What has actually been read

### 4.1 The teal cipher card `[MEASURED]`
Method: clip `94b4d23f`, sharpest frame t = 20.83 s, 10× upscale, ink isolated by
subtracting the card's own blurred L\*, auto de-skew −12.0°, **no deconvolution**.

The card carries **five rows**: three cipher rows then two rows of smaller subtext.

| row | y band | character groups at 3 thresholds | expected |
|---|---|---|---|
| 1 | 345–445 | **6** | `LSWRTE` (6) ✓ |
| 2 | 478–565 | 7–9, over-segmenting | `NNHTIN` — all vertical strokes ✓ |
| 3 | 598–712 | **5** | `HDOTA` (5) ✓ |

In row 3 the glyphs are visible: **position 2 is a D** (closed bowl), **position 3 an O**
(ring with a hole), **position 5 an A** (splayed legs); position 4 is a T or Y.

**The decode `[MEASURED — the arithmetic, computed]`:**
```
LASTWORDTHENNINTH  (17 letters)
even positions, forward   -> L S W R T E N N H
odd  positions, reversed  -> T I N H D O T A
concatenated              -> LSWRTENNHTINHDOTA
split 6 / 6 / 5           -> LSWRTE / NNHTIN / HDOTA     <- exact match
```
A two-rail zigzag with the bottom rail reversed. Reversible letter for letter, and it
yields a grammatical English instruction: **`LAST WORD THEN NINTH`**.

**This decode is already public** — a commenter posted
*"Rail Fence / LSWRTE / NNHTIN / HDOTA / LAST WORD THEN NINTH"* on Colin's video. It is
not a private edge. `[MEASURED]`

**Rows 4 and 5 (the subtext) have never been read by anyone.** A commenter on Colin's video
wrote *"OMG BIRD FENCE"*, and another solver reports the subtext mentions *"bird fence"* —
which would be a hint at the RAIL FENCE cipher. `[BORROWED]`

### 4.2 The closing note `[MEASURED]`
Method: `srx.py dd608937 1021 1042 660 990 1000 1080 10 --sharp 90` → 90 frames, all
aligned. This is the sharpest view anyone has produced of it.

```
(3 6 4)
      ↘
       (6 2        <- the closing bracket is hidden behind the cardboard box
        ↓
       (6)         <- fully legible, bracket included
```

- Line 1's `4` is **unambiguous**.
- Line 2's digit is a **2**: the visible left half shows a top horizontal stroke, a
  descending diagonal and a base stroke. **It cannot be an 8** (no upper closed loop) and
  cannot be 0 or 9 (the left side does not close).
- Line 3 gives ~97 px per glyph; line 2's visible part gives ~94 px per glyph — consistent.
  A `)` would fall behind the box, so `(6 2)` is the natural reading, but `(6 2…)` with
  more hidden characters cannot be excluded.
- The paper is a **spiral-bound lined notepad**, not a map. The "scale bar" some earlier
  passes reported is the spiral binding.
- Independent corroboration from viewer comments: *"364-62-6?"*, *"(364) (62) 6"*.

### 4.3 The telephone dial — SETTLED, there is no morse `[MEASURED]`
A widely repeated viewer claim says the dial carries morse code. **It does not.**

Method: `srx.py dd608937 1021 1042 280 840 700 1080 6 --sharp 90` → 90 frames, all
aligned, 2520×1440. In the closing clip the phone occupies a quarter of the frame, far
larger than in any office-set frame — this is why earlier attempts failed.

At every one of the **ten** dial positions the same structure appears: **three small marks
in a row, plus one separate mark**. That is a letter triplet (ABC, DEF, GHI …) and a digit
— a standard Western Electric printed dial face. Morse groups would vary between one and
four elements and would not repeat a three-plus-one pattern ten times.

### 4.4 The jigsaw pieces `[MEASURED]`
Method: `srx.py 94b4d23f 16.6 22.0 1540 380 1920 1080 6 --reftime 19.2` → 161 frames,
113 aligned, 2280×4200.

**This is the first clean read of these numerals by anyone.** Another session's 180-frame
4× stack produced nothing here.

| card | numerals | prior claim | outcome |
|---|---|---|---|
| **US flag** | **IV** (upper right) · **VII** (lower left) | "IV / VII, weak" | **confirmed** |
| **Oman flag** | **VI** (upper left) · **V** (below it) | "blue V or VI, red VI" | **both present** |
| **Africa + Madagascar** | **VIII** (upper left) · **IV** (right) | "blue VII or VIII, red IV" | **resolved to VIII** |
| **snow cloud** (grey cloud, white dots) | **IX** (lower left) | *absent from every inventory* | **new card** |

**Colour:** white-balancing against the card's own paper makes the US flag's **IV blue**
and its **VII red** (r−b = −21 and +60). On the other cards the warm light and cardboard
background defeat the white reference, so **only the numeral shapes are claimed there**.
A community comment says the numerals are **red and black**, not red and blue — treat my
"blue" with caution. `[BORROWED]`

Still unread: a gold-oval card, at least two dark-shape cards, a lower-left card, and a
small board of images. All sit at the frame's right edge in shadow.

### 4.5 The wall conduit stickers `[MEASURED]`
Two vertical electrical conduits, one on each wall of the office set, each carrying round
numbered stickers.

| colour family | left wall | right wall |
|---|---|---|
| blue / navy | **2** | **6** |
| white / cream | **1** | **4** |
| red / salmon / pink | **4** | **7** |

The right-wall digits are legible in a 3× stack. The left-wall digits are ~6 px in the
source: I confirm the **three colours and their arrangement** with a 116-frame 8× stack,
and take the digits `2 / 1 / 4` from another solver's reading. `[BORROWED for the digits]`

**★ An idea nobody else has raised `[INFERRED]`:** each cluster holds exactly **one blue,
one white and one red** sticker, and the jigsaw cards use a blue-and-red numeral
convention. So the white numeral may be the **piece index** and the blue|red pair its
**domino value** — making each wall cluster itself a piece:
- left = piece **1**, domino **2|4**
- right = piece **4**, domino **6|7**

If the cards also carry a third, white or black numeral, the chain's ordering is solved.
**This is untested.**

### 4.6 The `Boo!` book `[MEASURED]`
A 110-frame 5× stack of the desk renders the black book's cover as **`Boo!`**
unambiguously, in white script. A caption card sits with it, reported as
*"Five of these."* `[BORROWED]`

### 4.7 The pink index sheet `[MEASURED — structure only]`
A 116-frame 8× stack (`srx.py 94b4d23f 16.6 22.0 0 840 240 1000 8 --reftime`) resolves
**about five rows** carrying **about thirty short mark groups**, plus a header row of
larger characters. That corroborates the reported shape of ~28 page-and-Roman-numeral
pairs. **The content is not recoverable**: the marks are ~2 px in the source and the sheet
lies almost flat, so the rows curve under severe perspective.

Three published community transcriptions disagree on the digits. `[BORROWED]`

### 4.8 A new object nobody has reported `[MEASURED]`
On the **floor of the office set**, bottom right (~x 1540–1690, y 957–1002), there is a
**handwritten sheet carrying bracketed groups in the same idiom as the closing note**.
Method: segment the sheet's bright mask, fit its quadrilateral with `minAreaRect`, warp it
flat (583×1737). The bracket structure is clear; the characters are not readable — the
sheet lies at a steep angle on a dark floor and is partly occluded.

Nearby: the already-known upside-down `$10,000!` sheet, and a sheet with a drawn `⊙ ✕`
figure.

### 4.9 The entry form `[MEASURED]`
The on-screen form fill at 17:26 was measured by peak-counting the asterisks across
consecutive frames of the closing clip:

```
frame 84: 10   frame 86: 12   frame 88: 15
frame 85: 10   frame 87: 14   frame 89: 15   frame 90: 15   <- stabilises
```
Step ≈ 45.7 px, the last asterisk ends at x = 1266, the field is not clipped.
**Exactly 15 characters.**

Caveat: this is a staged fill by an editor. If they typed a placeholder, its length means
nothing. But it is the only length signal that exists.

**The real form** has `maxLength: 500` and no pattern or normaliser, and its own copy says
**"You can guess multiple times, but there is only 1 correct answer."** `[MEASURED]`

---

## 5. The two competing candidates

Both are exactly 15 characters. Both are city nicknames. **Each is supported by evidence
the other cannot explain.**

### Candidate A — `PEARLOFTHENORTH`

The chain, with my own verification of each link:

1. **MrBeast's pinned comment** points at Colin's profile: *"Make sure you check out
   Colin's profile 👀"*. `[MEASURED]`
2. **Colin's channel description ends with a book title.** Fetched directly with yt-dlp
   (303 characters): `[MEASURED]`
   > *"Send me a puzzle - or join me solving puzzles on Twitch every Thursday evening
   > (US eastern time). / "And, as with all retold tales that are in people's hearts,
   > there are only good and bad things and black and white things and good and evil
   > things and no in-between anywhere." — **John Steinbeck, The Pearl**"*

   **Last word: `Pearl`.**
3. **The teal card decodes to `LAST WORD THEN NINTH`** — arithmetic exact, card structure
   6 / over-segmented / 5 confirmed, D, O and A legible in row 3. `[MEASURED]`
4. **`Pearl` occurs exactly once in the entire 84-page key, and it is the ninth entry of
   its table:** `[MEASURED]`
   ```
   line 2843: MP9
   line 2844: OCHROLEUCOUS
   line 2845: Pearl of the North
   line 2846: Mosul, Iraq
   ```
   Decoy check: `Send`, `join` and `John` also occur exactly once each, so "occurs once"
   alone is weak — but the other three occur inside filler text, and `Pearl` is the only
   one in an answer row, at position nine.
5. **Only one string in that row is 15 characters:** `[MEASURED]`
   ```
   OCHROLEUCOUS     12
   MOSULIRAQ         9
   PEARLOFTHENORTH  15   <- matches the measured field length
   ```

**Weaknesses:**
- The "then ninth" step is **circular**: `Pearl` leads you to MP9, and MP9 is where `Pearl`
  is. The instruction does no independent work — unless it is meant as a self-check.
- **It does not fit the closing note at all**: `PEARL OF THE NORTH` = (5 2 3 5),
  `MOSUL IRAQ` = (5 4), `MOSUL` = (5). None of `(3 6 4)`, `(6 2)`, `(6)`.

### Candidate B — `THE ZENITH CITY`

1. The closing set's TV is a **Zenith**, and it is the object that displays the only
   `PAUSE` instruction in the whole video. `[MEASURED]`
2. **`The Zenith City` is Duluth, Minnesota's nickname.** Across a dataset of **2867 city
   nicknames** I built from Wikipedia (50 US states plus Canada and the UK), it is the
   **only nickname containing the word "zenith"**. `[MEASURED]`
3. **It satisfies every line of the closing note:** `[MEASURED]`
   ```
   (3 6 4)  =  THE(3) ZENITH(6) CITY(4)   -> 13 letters + 2 spaces = 15 characters
   (6 2)    =  DULUTH(6) MN(2)
   (6)      =  DULUTH(6)
   ```
4. Of the 45 nicknames matching the (3 6 4) shape, only four pair with a 6-letter city and
   a 2-letter state: Azalea/Mobile AL, Circle/Corona CA, Garden/Newton MA, **Zenith/Duluth
   MN**. Only Duluth's is physically present in the video. `[MEASURED]`
5. City nicknames are the **author's documented signature mechanic**: the old key's MP1–15
   and MP25–40 both open with the poem *"A nickname for your destination / (But not its
   name or its translation)"* and every answer is "City, State/Country". `[MEASURED]`

**Weaknesses:**
- It uses **no cipher step** and ignores both the teal card and the pinned comment.
- I searched the whole 84-page key for any (3 6 4) three-word phrase: 32 hits, all ordinary
  word sequences ("the answer Name", "The solver must"). **The note therefore points
  outside the key** — which is consistent with B, but is not proof. `[MEASURED]`
- The old hunt's idiom is *N puzzle objects → N extracted units → one assembled answer*. If
  the ~13–15 jigsaw pieces each yield one **letter**, the answer is 15 letters with **no
  spaces**, which favours `PEARLOFTHENORTH` or `DULUTHMINNESOTA` over the spaced form.

### Recommended submission order
The site never reports correctness, so submitting teaches nothing — but only the **first**
correct submission wins, so waiting costs. **Submit both leaders immediately.**

```
wave 1   PEARLOFTHENORTH          THE ZENITH CITY
wave 2   PEARL OF THE NORTH       DULUTHMINNESOTA      MOSUL, IRAQ      DULUTH
wave 3   MOSUL IRAQ · MOSULIRAQ · MOSUL · OCHROLEUCOUS
         DULUTH, MINNESOTA · DULUTH MN · ZENITH CITY · ZENITH
         THE SECOND CITY · THE GARDEN CITY · THE FOREST CITY · THE CIRCLE CITY · THE AZALEA CITY
```

**Operational note `[MEASURED from the site's own JavaScript]`:** each guess needs
answer + email + the 18+/rules checkbox, and then **a 6-digit code emailed to you must be
entered** or the guess does not count. The site's strings, in order:
*"We'll send a verification code to confirm your entry."* → *"We sent a 6-digit code to…"*
→ *"Enter the 6-digit code."* → *"Your guess is confirmed for…"* → *"You're in the running."*

---

## 6. What the author himself has ruled out — the most valuable external finding

Colin replies in the comments of his own videos, from `@doctorxor`: `[MEASURED]`

> **"This is not part of the 10k puzzle"** — about his "Hat Trick / Riddle #0" video
> **"It is not relevant to MrBeast's challenges, I promise 😅 I made this quite a bit earlier."**
> **"Nope, not relevant to the MrBeast puzzle!"** — about his own $1M walkthrough video,
> adding *"although the generic puzzlehunt advice in the intro doesn't hurt to know."*

**So Colin's own videos are out of scope. Only his channel profile is in scope**, because
MrBeast's pinned comment points there.

A hint of his that circulates as if it were a $10k clue —
**"Try saying it out loud … the third line is faster!"** — is a **red herring**: I traced
the parent comments and it answers a question about a **separate brain teaser in his own
video**, which he has explicitly said is unrelated. `[MEASURED]`

The official rules also settle the scope: *"Clues to solving the Puzzle will be available
**in the Video**."* `[MEASURED]`

---

## 7. A live hypothesis worth pursuing — the book cipher

`[INFERRED, untested]`

Three things point the same way:
1. The orange card reportedly reads **"Books w/ old names… / Alphabetize?"** `[BORROWED]`
   — I have confirmed only that it has four lines and ends in a large `?`. `[MEASURED]`
2. The drawer card shows a black book reading **`Boo!`** `[MEASURED]` captioned
   **"Five of these."** `[BORROWED]`
3. The pink index sheet looks like **~28 pairs of a page number and a Roman numeral**.
   `[MEASURED for the shape]`

And Colin, in his own comments, describes exactly this kind of mechanism: `[MEASURED]`
> *"…and THEN if you knew what to do with the algorithm after all that, you had to do an
> **evil little book cipher**. In my opinion, book ciphers and their equivalents are the
> hardest things out there already."*

**Which book?** The most likely candidate is the **84-page answer-key PDF** — it is free,
linked in the video description, and Colin himself links it in a comment. The reported page
values (`029`, `039`) are all below 84, which fits. The Roman numeral would then select a
word or line on that page.

A second possibility: **Lone Shark Games**, credited in the description as the old hunt's
builder, publishes a small book set — *Dealer's Choice, Letters to Margaret, Mindspaces,
Puzzlecraft, The Hunting of the Shark, The Maze of Games*. "Five of these" and "Alphabetize"
could select and order them. This requires physical books, which is a heavy ask for a
$10,000 contest, so I rank it below the PDF.

**Reading the pink index sheet is the highest-value open task.** It is the one planted
object whose content is entirely unknown and which is plainly machinery rather than
decoration.

---

## 8. Everything ruled out — do not redo `[all DEAD]`

**Ruled out by measurement here:**
- **Morse on the telephone dial** — it is a standard printed dial face (§4.3).
- **The canvas drop-cloth backdrop** — 100-frame 3× stack plus high-pass: folds, stains and
  paint specks only, no writing.
- **The office desk's wooden surface and drawer fronts** — 110-frame 5× stack, blank.
- **The closing set's cardboard box** — 88-frame 5× stack, plain cardboard.
- **The on-screen legal strip** at 1050–1056 s — OCR'd; it is word-for-word identical to
  the video description's disclaimer. No hidden message.
- **`mrb.gg/p/puzzle`** — only the answer-key page.
- **The video description's last word** is "com" — useless as a `LAST WORD` source.
- **Steinbeck's novels** as the target of `LAST WORD THEN NINTH` — the ninth by publication
  is *Cannery Row* (10), the ninth alphabetically is *The Pastures of Heaven*. Nothing 15
  characters long.
- **"Ninth letter of each MP caption word"** — the ninth letters of all forty are
  `OTHMCURECEOHEAHTFTTTDTTTDAHDDCSUONHLATKN`: nine T's, five H's, and **no P, I, Y, G, V,
  W or Q at all**. Neither `PEARLOFTHENORTH` nor `THE ZENITH CITY` is buildable from that
  pool. This kills the whole family.
- **Zenith and Duluth domains** — `zenith.mrbeast.app`, `mrbeast.app/zenith`,
  `duluth.mrbeast.app`, `beast.travel/zenith|duluth`, `thezenithcity.com/.org`: all 404 or
  a catch-all Okta portal. `zenithcity.com` is a real Duluth history site with no MrBeast
  connection.
- **The contest site's hidden pages** — no answer or hash in the client JavaScript.
- **The whole corkboard** — every category maps onto the old answer key.
- **The TV montage** (840 frames OCR'd), the ending QR (115 frames, one URL), the final
  12 seconds (a CRT collapse animation), stereo side-channel, spectrograms, whole-video
  brightness and flicker (31 996 frames), video metadata (no zero-width characters), the
  `N/91` counter, MrBeast's 843 video titles.
- **No occurrence of `218`, `MN`, `zenith`, `duluth`, `Lake Superior` or `Twin Ports`**
  anywhere in any OCR dataset or in the captions.
- **what3words** — the closing note has no three-letter words to feed it.

**Ruled out by the author:** Colin's own videos, and the "say it out loud / third line is
faster" hint (§6).

**Ruled out by another session, not re-verified here `[BORROWED]`:** caption colours,
zero-width characters, single-frame inserts, audio steganography, description acrostics,
`LAST WORD THEN NINTH` applied to the transcript / captions / rules / description, the
XOR key from the pinned comment's tinyurl (a 1.1 MB sweep across 18 corpora found zero
mask-shaped outputs — it is a format joke on the handle "DoctorXOR"), the thumbnail's QR
(generated art, does not decode), the box dates, and the "computer tower stickies" that
appear to have been invented by chatbots.

---

## 9. Open questions, in priority order

1. **Read the pink index sheet.** The one wholly unknown planted object, and the key to the
   book-cipher hypothesis. Three community transcriptions disagree; none can be trusted.
2. **Read the teal card's two subtext rows.** Nobody has. A "bird fence" mention there
   would confirm the rail-fence reading from the author's side.
3. **Read the new floor sheet** (§4.8) — bracketed groups in the closing note's idiom,
   unreported by anyone.
4. **Read the remaining piece numerals** — gold oval, the dark-shape cards, the lower-left
   card. Use `--reftime` at the moment each is largest; also try the t = 44–52 s angle.
5. **Test the "white numeral = piece index" hypothesis** (§4.5). If the cards carry a third
   numeral, the domino ordering is solved.
6. **Settle the ink colours.** A community comment says red and black, my white-balance says
   blue and red on the one card where the test is reliable. This matters for the chain.
7. **Read the orange card** — "Books w/ old names… / Alphabetize?" is still borrowed.
8. **Resolve the note against Candidate A.** Either `(3 6 4) → (6 2) → (6)` has a reading
   that fits `PEARLOFTHENORTH`, or the two chains genuinely disagree and one is wrong.

### A first domino attempt, and why it does not close yet `[INFERRED]`
```
left wall   2 | 4        US flag     4 | 7        right wall  6 | 7
Oman        6 | 5  or 5 | 6          Africa      8 | 4  or 4 | 8
snow cloud  9 | ?
```
A run **2–4 → 4–7 → 7–6 → 6–5** exists. But `4` appears in three dominoes (2|4, 4|7, 8|4)
and a simple chain allows each value at most twice. So either a colour assignment is wrong,
or the wall clusters are not pieces, or the chain is not simple. Too early to conclude.

---

## 10. Files

Working directory:
`/tmp/claude-0/-home-user-gunnazinadgunu/84fa90fa-750b-5180-b6a9-f390607e1640/scratchpad`
Uploaded clips: `/root/.claude/uploads/84fa90fa-750b-5180-b6a9-f390607e1640/*.mov`

| file | what it is |
|---|---|
| `MRBEAST_PUZZLE_NOTES.md` | the full chronological research log, in Azerbaijani, including every retraction |
| `srx.py` | multi-frame super-resolution (§2) |
| `ink.py` | ink isolation and de-skew (§2) |
| `clipmap.json` | clip id → absolute video time |
| `AGENT_BRIEF.md` | the brief handed to extraction sub-agents |
| `DESK_GRID.png`, `CLOSE_GRID.png` | both sets with a 100 px coordinate grid overlaid |
| `site/puzzle_answers.txt` | the 84-page old answer key, as text |
| `site/*.js`, `site/index.html` | the contest site's client bundle |
| `nicknames_all.json` | 2867 city nicknames from Wikipedia |
| `vs/S00–S05.png` | whole-video contact sheets with correct timestamps, one frame per 4 s |
| `sr_*.png` | every super-resolution stack produced |
| `cards_numerals.png` | the piece numerals, read |
| `dial2_groups.png` | the ten dial positions, settling the morse question |
| `sr_note2_v.png` | the closing note, sharpest view |

**A warning about an older artefact:** `allframes/` contains 1776 low-resolution frames
whose timestamps I originally mis-derived. **Its labels are wrong — use `vs/` instead.**
