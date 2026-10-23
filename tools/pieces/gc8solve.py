#!/usr/bin/env python3
"""The GC8 mechanism, with its own control, applied to the fifteen pieces.

GC8 (page 51 of the answer document) gives seven pictures, each carrying a number
or a pair of numbers.  Each picture names an associated thing; the numbers index
letters into that name; the first number of each pair builds one string and the
second builds the other, and the two spell a city and a country.  Its control is
run first and must print ALGIERS / ALGERIA before anything else is trusted.

Our fifteen cards carry a red and a black numeral each.  Fill NAMES in below as
the drawings get identified and this prints the two strings.  A name shorter than
the larger of its two numerals is rejected, which is the mechanism's own filter.
"""
import re, sys

def clean(s):
    return re.sub(r'[^A-Z]', '', s.upper())

def idx(name, n):
    s = clean(name)
    return s[n-1] if 1 <= n <= len(s) else None

# ---------------------------------------------------------------- control ----
CONTROL = [
    ('ANNE RICE',              [1]),
    ('CLERIC',                 [2]),      # "Kyra the cleric" in the PDF's text
    ('GEORGE FRIDERIC HANDEL', [5]),
    ('AMERICAN CHEESE',        [5, 14]),
    ('CENTER ICE',             [2, 6]),
    ('RICHIE RICH',            [1, 5]),
    ('DALLAS MAVERICKS',       [6, 8]),
]

def run_control():
    a, b = [], []
    for name, nums in CONTROL:
        first = nums[0]
        second = nums[1] if len(nums) > 1 else nums[0]
        a.append(idx(name, first))
        b.append(idx(name, second))
    got = (''.join(a), ''.join(b))
    ok = got == ('ALGIERS', 'ALGERIA')
    print('NEZARET  %s / %s  ->  %s' % (got[0], got[1], 'KECDI' if ok else 'DUSDU'))
    return ok

# ------------------------------------------------------------------ cards ----
# (etiket, qirmizi, mavi, ad)   ad=None => hele adlandirilmayib
# Qirmizi/mavi reqemler REF803-den warp + 9-16x boyutme ile oxunub.
CARDS = [
    ('elf fiquru',               2,  11, None),   # ISTIFADECI: elf. Ad >=11 olmalidir -> 'CHRISTMAS ELF'(12) / 'ELF ON THE SHELF'(13) / 'SANTAS HELPER'(12)
    ('gizli sekilli kart',       7,   1, None),   # qirmizi VII: t=324-de 4 kadrda qeti
    ('barmaqliq',             None, None, None), # ISTIFADECI: barmaqliq. reqemleri gorunmur
    ('asagi ox + sutunlar',      8,   9, None),   # namized: 'chart decreasing'(15) -> C/R
    ('kepenek (bant?)',          5,   7, 'butterfly'),  # filtr `ribbon`(6)-ni kesir
    ('narinci-qirmizi duzbucaq', 6,   8, None),   # namized: 'red square'(9) -> U/R
    ("teqvim '25'",              2,   4, None),   # namized: 'spiral calendar'(14) -> P/R
    ('paz + firuzeyi obyekt',    6,   6, 'FEASTABLES'),  # ISTIFADECI: Feastables baton; 6-ci herf A -> her iki setre A
    ('sevinc uzu',              10,  14, 'face with tears of joy'),
    ('das + kecel qartal',       8,   9, None),   # yigin: qirmizi ~VIII, mavi ~IX (ilk defe gorunur)
    ('Oman bayragi',             6,   5, 'flag: Oman'),  # CLDR adi, 8 herf
    ('Afrika + yasil bitki',     4,   8, None),   # namized: 'globe showing Europe-Africa'(24) -> B/O
    ('qar buludu',               9,   5, 'cloud with snow'),
    ('ABS bayragi + tovle',      7,   4, None),   # namized: 'flag: United States'(16) -> I/G
    ('ureyeoxsar tund fiqur', None, None, None),
]

def solve():
    red, blue, gaps = [], [], []
    for label, r, b, name in CARDS:
        if r is None or b is None or not name:
            red.append('?'); blue.append('?')
            gaps.append(label + (' (reqem yox)' if r is None else ' (ad yox)'))
            continue
        need = max(r, b)
        if len(clean(name)) < need:
            print('  RED EDILDI  %-26s %r cemi %d herf, lazim >= %d'
                  % (label, name, len(clean(name)), need))
            red.append('!'); blue.append('!'); continue
        red.append(idx(name, r)); blue.append(idx(name, b))
    print('QIRMIZI :', ''.join(red))
    print('MAVI    :', ''.join(blue))
    if gaps:
        print('CATISMIR (%d):' % len(gaps))
        for g in gaps:
            print('   -', g)

if __name__ == '__main__':
    if not run_control():
        sys.exit('nezaret dusdu - hec bir netice etibarli deyil')
    print()
    solve()
