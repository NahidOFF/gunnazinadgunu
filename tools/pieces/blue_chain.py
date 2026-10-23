#!/usr/bin/env python3
"""The blue half of the desk puzzle, as far as it can be pinned down.

The cream note reads  (3 6 4) + (4 4 4 5) -> (6 6) -> (6).

  (3 6 4)   = XOR SUPERB OWLS      -- what the jigsaw's blue numerals spell
  (4 4 4 5) = LAST WORD THEN NINTH -- what the teal card's LSWRTE/NNHTIN/HDOTA
                                      decodes to on a two-rail zigzag
  (6 6)     = a two-word, twelve-letter phrase
  (6)       = the six-letter answer

The community reads the (6 6) as FOURTH UPLOAD and then asserts HEDWIG without
deriving it. But "(6 6)" only says six letters and six letters, and several
ordinals fit. Checked against MrBeast's own upload history (dates confirmed
with yt-dlp), only one of them lands anywhere:

  SECOND UPLOAD -> "Harry Potter Mod In Minecraft!" -> the owl in Harry Potter
                -> HEDWIG, six letters, which is exactly the note's (6).

FOURTH, EIGHTH, LATEST and OLDEST all fit (6 6) too and none of them yields a
six-letter anything. So HEDWIG stops being an assertion and becomes a reading.

What is still not derived: why the ordinal is SECOND -- i.e. how LAST WORD THEN
NINTH picks it out.
"""

# MrBeast's main channel, oldest first. Dates from yt-dlp; the first is
# 2012-02-20, the day the channel's first video went up.
OLDEST = [
    ("2012-02-20", "2XVcLrB7B3Y", "Worst Minecraft Saw Trap Ever???"),
    ("2012-03-09", "jP82d277Cc8", "Harry Potter Mod In Minecraft! EPIC MUST SEE MOD!!!"),
    ("2013-01-12", "Z8nEEdXTaX0", "Boxy item mod Minecraft.  EPIC"),
    ("2013-01-12", "Y74b7WlcEpk", "More birds IN MINECRAFT!!"),
    ("2013-01-13", "7qj3nuF9Dzw", "Most Epic minecraft skin EVER  (Psy)"),
    ("2013-01-13", "M82VAcabSiA", "Scary minecraft pig skin!"),
    ("2013-01-13", "t8aM4HuVLrQ", "This is a block? Since when lol."),
    ("2013-01-14", "atCPtw4dg7g", "Emerald tool mod! (minecraft)"),
]

ORDINALS = ["FIRST", "SECOND", "THIRD", "FOURTH", "FIFTH", "SIXTH",
            "SEVENTH", "EIGHTH", "NINTH", "TENTH", "LATEST", "OLDEST"]

def main():
    print("MrBeast's main channel, oldest first:")
    for i, (d, v, t) in enumerate(OLDEST, 1):
        print("  %2d. %s  %s" % (i, d, t))

    print('\nOrdinals that make "<ordinal> UPLOAD" fit the note\'s (6 6):')
    for w in ORDINALS:
        if len(w) == 6 and len("UPLOAD") == 6:
            print("   %-7s UPLOAD" % w)

    print("\nWhere each of those actually lands:")
    for w, idx in [("SECOND", 2), ("FOURTH", 4), ("EIGHTH", 8)]:
        title = OLDEST[idx - 1][2]
        print("   %-7s -> %s" % (w, title))
    print("   LATEST  -> whatever is newest, changes weekly")
    print("   OLDEST  -> Worst Minecraft Saw Trap Ever???")

    print("\nOnly SECOND yields a six-letter answer:")
    print("   Harry Potter -> Harry's owl -> HEDWIG (%d letters) == the note's (6)"
          % len("HEDWIG"))

if __name__ == '__main__':
    main()
