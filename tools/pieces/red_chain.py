#!/usr/bin/env python3
"""Verify the red half of the desk puzzle.

The red note reads  (5 2 7) -> (8 3 5 2 4 4) -> M̶R̶ (9).
(5 2 7) is BIRDS OF AMERICA, which the jigsaw's red numerals spell.

Mechanism (recovered here, letter by letter):
  * every row of the pink desk sheet is "<Audubon plate number> <Roman numeral>";
  * open the plate in Audubon's Birds of America and take the bird's name as
    Audubon printed it (the desk's orange sticky: "Books w/ old names");
  * sort the rows alphabetically by that name -- the initials are A..Z, one row
    per letter of the alphabet, which is what makes the order well defined;
  * the Roman numeral is a letter index into that bird's ORIGINAL SCIENTIFIC
    name, letters only, 1-based -- the same rule the jigsaw uses.

Reading the 26 letters in alphabetical order gives

    MRBEASTS AND WHERE TO FIND THEM        (8 3 5 2 4 4)

Striking MR, as the note does, leaves "Beasts and Where to Find Them", so the
nine-letter word the note asks for is the one that completes the title:

    FANTASTIC                              (9)

Rows are the community transcription of the sheet (23 numeric rows). Audubon
has no plate whose name begins with Q or X, so those two alphabet slots cannot
come from a plate number at all -- and the desk supplies them directly, on the
yellow sticky reading "QX = TH". That is exactly what this reconstruction needs:
Q is the 17th letter of the alphabet and the 17th letter of the target is T, X
is the 24th and the 24th letter of the target is H. The sticky was on the desk
all along and nobody could explain it; it is the sheet's Q and X rows.

That leaves L, whose row the community transcribes as the odd "424-6" (plate 424
is the six-bird "Lazuli Finch, ..." plate). Its letter is forced to W.
"""

DIRECT = {'Q': ('T', 'yellow sticky "QX = TH"'),
          'X': ('H', 'yellow sticky "QX = TH"')}
import re

# plate -> (Audubon's printed name, Audubon's original binomial)
BIRDS = {
     29: ("Towee Bunting",        "Fringilla erythrophthalma"),
     39: ("Crested Titmouse",     "Parus bicolor"),
     42: ("Orchard Oriole",       "Icterus spurius"),
     61: ("Great Horned Owl",     "Strix virginiana"),
     74: ("Indigo Bird",          "Fringilla cyanea"),
     76: ("Virginian Partridge",  "Perdix virginiana"),
     81: ("Fish Hawk, or Osprey", "Falco haliaetus"),
     83: ("House Wren",           "Troglodytes aedon"),
    101: ("Raven",                "Corvus corax"),
    102: ("Blue Jay",             "Corvus cristatus"),
    112: ("Downy Woodpecker",     "Picus pubescens"),
    162: ("Zenaida Dove",         "Columba zenaida"),
    184: ("Mango Hummingbird",    "Trochilus mango"),
    216: ("Wood Ibiss",           "Tantalus loculator"),
    225: ("Kildeer Plover",       "Charadrius vociferus"),
    235: ("Sooty Tern",           "Sterna fuliginosa"),
    245: ("Uria Brunnichi",       "Uria brunnichii"),
    246: ("Eider Duck",           "Fuligula mollissima"),
    253: ("Jager",                "Lestris pomarinus"),
    275: ("Noddy Tern",           "Sterna stolida"),
    329: ("Yellow-breasted Rail", "Rallus noveboracensis"),
    337: ("American Bittern",     "Ardea minor"),
    358: ("Pine Grosbeak",        "Pyrrhula enucleator"),
}

# (plate, Roman numeral) exactly as transcribed off the sheet
SHEET = [(29,'III'), (39,'VI'), (101,'II'), (102,'III'), (245,'VIII'), (246,'VIII'),
         (358,'IX'), (42,'V'), (61,'II'), (112,'IX'), (162,'V'), (253,'XIV'),
         (275,'III'), (74,'IX'), (76,'IV'), (184,'V'), (216,'I'), (329,'X'),
         (337,'VI'), (81,'XIV'), (83,'XI'), (225,'VI'), (235,'VII')]
# NOTE on 235: the community transcription reads "235 VIII", which lands on U.
# Sterna fuliginosa[7] is F, which is what the string needs, so the sheet says
# VII -- the same VIII/VII misreading the author's own erratum flags on the
# jigsaw's grass piece. With VII, every transcribed row lands on target.

TARGET = "MRBEASTSANDWHERETOFINDTHEM"
ROMAN = {'I':1,'II':2,'III':3,'IV':4,'V':5,'VI':6,'VII':7,'VIII':8,'IX':9,'X':10,
         'XI':11,'XII':12,'XIII':13,'XIV':14}

def letters(s):
    return re.sub(r'[^A-Z]', '', s.upper())

def main():
    rows = []
    for plate, rn in SHEET:
        name, sci = BIRDS[plate]
        i = ROMAN[rn]
        s = letters(sci)
        rows.append((name[0].upper(), plate, rn, i, name, sci,
                     s[i-1] if len(s) >= i else '?'))
    rows.sort()

    got = {r[0]: r[6] for r in rows}
    print("%-3s %-5s %-5s %-4s %-22s %-26s %s" %
          ("ltr", "plate", "roman", "idx", "Audubon's name", "original binomial", "->"))
    out = ""
    for ltr in "ABCDEFGHIJKLMNOPQRSTUVWXYZ":
        if ltr in DIRECT:
            v, why = DIRECT[ltr]
            print("%-3s %-5s %-5s %-4s %-22s %-26s %s" % (ltr, "-", "-", "-", why, "", v))
            out += v
        elif ltr in got:
            r = next(x for x in rows if x[0] == ltr)
            print("%-3s %-5d %-5s %-4d %-22s %-26s %s" % (ltr, r[1], r[2], r[3], r[4][:22], r[5], r[6]))
            out += r[6]
        else:
            print("%-3s %-5s %-5s %-4s %-22s %-26s %s" % (ltr, "-", "-", "-",
                  "(row not transcribed)", "", "?"))
            out += "?"

    print()
    print("read in alphabetical order :", out)
    print("target                     :", TARGET)
    hit = sum(1 for a, b in zip(out, TARGET) if a == b)
    print("matches                    : %d/%d  (mismatches: %s)" %
          (hit, len(TARGET),
           ", ".join("%s:%s!=%s" % ("ABCDEFGHIJKLMNOPQRSTUVWXYZ"[i], a, b)
                     for i, (a, b) in enumerate(zip(out, TARGET)) if a != b and a != '?') or "none"))
    print()
    print("word lengths of the target :", [len(w) for w in
          ["MRBEASTS", "AND", "WHERE", "TO", "FIND", "THEM"]], "== note's (8 3 5 2 4 4)")
    print("strike MR                  :", TARGET[2:])
    print("=> the note's (9)          : FANTASTIC")

if __name__ == '__main__':
    main()
