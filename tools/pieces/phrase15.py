#!/usr/bin/env python3
"""Given the fifteen (red, blue) letter pairs, find every ordering whose RED string
reads as a run of dictionary words, and print the BLUE string each ordering implies.

The answer field holds fifteen characters and every piece contributes one letter, so
the answer is fifteen letters with no spaces -- a spaceless phrase.  This searches the
letter multiset for such phrases, then solves a bipartite matching to see which pieces
can sit in which positions, which fixes the blue string too.

  phrase15.py            run the control and exit
  phrase15.py PAIRS      PAIRS like "AE,EF,EO,MO,HD,AR,..." (15 comma-separated pairs)
"""
import sys, os, itertools
from collections import Counter

WORDS = '/tmp/claude-0/-home-user-gunnazinadgunu/84fa90fa-750b-5180-b6a9-f390607e1640/scratchpad/words.txt'
MINW, MAXPHRASE = 4, 4          # generator: words >= 4 letters, at most 4 words
# ...plus these short words, which real phrases need and a bare length floor would drop
SHORT = set('''A I AN AS AT BE BY DO GO HE IF IN IS IT ME MY NO OF ON OR SO TO UP US WE
ALL AND ANY ARE BIG DAY FOR GET HAS HER HIS HOW ITS LET MAN NEW NOT NOW ODD OFF ONE OUR
OUT OWN SEA SIX SUN THE TEN TOO TOP TWO WAS WAY WHO WHY YES YET YOU'''.split())

def load(path=WORDS):
    ws = set()
    if not os.path.exists(path):
        sys.exit('word list missing: ' + path)
    for line in open(path, errors='ignore'):
        w = ''.join(ch for ch in line.strip().upper() if ch.isalpha())
        if 2 <= len(w) <= 15:
            ws.add(w)
    ws |= SHORT
    return ws

def gen_words(words):
    """What the phrase generator is allowed to use: long words plus common short ones."""
    return {w for w in words if len(w) >= MINW} | (SHORT & words) | SHORT

def phrases(multiset, words, maxwords=MAXPHRASE):
    """Every multiset of <= maxwords dictionary words that spends the pool exactly.

    Signature lookup, not a blind DFS: filter the list to words that fit the pool
    (the letter-SET test kills almost everything first), index the survivors by their
    26-tuple signature, then close one, two or three words by looking the remainder up.
    """
    AZ = 'ABCDEFGHIJKLMNOPQRSTUVWXYZ'
    def sig(c):
        return tuple(c.get(ch, 0) for ch in AZ)
    pool_set = set(multiset)
    pool = sig(multiset)
    cand, sig2w = [], {}
    for w in words:
        if len(w) > 15 or not set(w) <= pool_set:
            continue
        c = Counter(w)
        s = sig(c)
        if any(s[i] > pool[i] for i in range(26)):
            continue
        cand.append((w, s, len(w)))
        sig2w.setdefault(s, []).append(w)
    def sub(x, y):
        out = []
        for i in range(26):
            d = x[i] - y[i]
            if d < 0: return None
            out.append(d)
        return tuple(out)
    ZERO = tuple([0] * 26)
    out = []
    if pool in sig2w:
        for w in sig2w[pool]: out.append([w])
    if maxwords >= 2:
        for w1, s1, _ in cand:
            r = sub(pool, s1)
            if r is None or r == ZERO: continue
            for w2 in sig2w.get(r, ()):
                if w1 <= w2: out.append([w1, w2])
    if maxwords >= 3:
        for i, (w1, s1, _) in enumerate(cand):
            r1 = sub(pool, s1)
            if r1 is None or r1 == ZERO: continue
            for w2, s2, _ in cand[i:]:
                r2 = sub(r1, s2)
                if r2 is None or r2 == ZERO: continue
                for w3 in sig2w.get(r2, ()):
                    if w2 <= w3: out.append([w1, w2, w3])
    return out

def all_blues(pairs, target):
    """Every blue string consistent with this red target.

    A piece can sit in any position whose red letter matches, so ties exist only
    between pieces sharing a red letter.  Permuting each such group gives exactly the
    achievable blue strings."""
    n = len(pairs)
    groups = {}
    for i, (r, _) in enumerate(pairs):
        groups.setdefault(r, []).append(i)
    slots = {}
    for p, ch in enumerate(target):
        slots.setdefault(ch, []).append(p)
    if set(groups) != set(slots): return []
    for ch in groups:
        if len(groups[ch]) != len(slots[ch]): return []
    keys = sorted(groups)
    perms = [list(itertools.permutations(groups[k])) for k in keys]
    if any(len(p) == 0 for p in perms): return []
    total = 1
    for pr in perms: total *= len(pr)
    if total > 5000: perms = [pr[:1] for pr in perms]      # too degenerate to enumerate
    out = []
    for combo in itertools.product(*perms):
        blue = [None] * n
        for k, order in zip(keys, combo):
            for pos, piece in zip(slots[k], order):
                blue[pos] = pairs[piece][1]
        out.append(''.join(blue))
    return out

def splittable(s, words, maxwords=5, minw=2):
    """Can this string be cut into <= maxwords dictionary words?  Returns the cut."""
    n = len(s)
    best = [None] * (n + 1)
    reach = {0: []}
    for i in range(n):
        if i not in reach: continue
        for j in range(min(n, i + 15), i + minw - 1, -1):   # longest word first
            w = s[i:j]
            if w in words and len(reach[i]) + 1 <= maxwords:
                cur = reach[i] + [w]
                if j not in reach or len(cur) < len(reach[j]):
                    reach[j] = cur
    return reach.get(n)

def orderings(pairs, target):
    """Positions each piece may take, then one perfect matching per solution."""
    n = len(pairs)
    cand = [[p for p in range(n) if pairs[i][0] == target[p]] for i in range(n)]
    if any(not c for c in cand): return None
    used, assign = [False] * n, [None] * n
    order = sorted(range(n), key=lambda i: len(cand[i]))
    def rec(k):
        if k == n: return True
        i = order[k]
        for p in cand[i]:
            if not used[p]:
                used[p] = True; assign[i] = p
                if rec(k + 1): return True
                used[p] = False; assign[i] = None
        return False
    if not rec(0): return None
    blue = [None] * n
    for i, p in enumerate(assign): blue[p] = pairs[i][1]
    return ''.join(blue)

def run(pairs, words, label='', contains=None, top=60, both=True):
    """Both strings must read as phrases -- that is the real filter, and it is what
    GC8 does (ALGIERS *and* ALGERIA)."""
    ms = Counter(p[0] for p in pairs)
    found = phrases(ms, gen_words(words))
    if contains:
        found = [ph for ph in found if any(contains in w for w in ph)]
    found.sort(key=lambda ph: (len(ph), -max(len(w) for w in ph)))
    print('%s%d hərf · %d qırmızı ifadə dəsti%s'
          % (label, sum(ms.values()), len(found),
             (' (süzgəc: %s)' % contains) if contains else ''))
    seen, shown, tested = set(), 0, 0
    for ph in found:
        for perm in sorted(set(itertools.permutations(ph))):
            t = ''.join(perm)
            if t in seen: continue
            seen.add(t); tested += 1
            for blue in all_blues(pairs, t):
                cut = splittable(blue, words) if both else True
                if not cut: continue
                print('   QIRMIZI %-15s = %-30s' % (t, ' '.join(perm)))
                print('   MAVI    %-15s = %-30s' % (blue, ' '.join(cut) if cut is not True else ''))
                print()
                shown += 1
                if shown >= top:
                    print('   … (ilk %d göstərildi; %d qırmızı sətir yoxlanıldı)' % (top, tested))
                    return
                break
    print('   %d qırmızı sətir yoxlandı, %d cütdə HƏR İKİ sətir söz(lər)ə bölündü' % (tested, shown))

if __name__ == '__main__':
    words = load()
    if len(sys.argv) < 2:
        # control: DULUTH MINNESOTA must come back out of its own letters
        ctrl = [(c, 'X') for c in 'DULUTHMINNESOTA']
        ms = Counter(c for c, _ in ctrl)
        got = phrases(ms, gen_words(words))
        ok = any(sorted(p) == sorted(['DULUTH', 'MINNESOTA']) for p in got)
        print('NEZARET: DULUTHMINNESOTA -> %d ifadə, {DULUTH, MINNESOTA} %s'
              % (len(got), 'TAPILDI' if ok else 'TAPILMADI'))
        sys.exit(0 if ok else 1)
    pairs = [tuple(x.strip().upper()) for x in sys.argv[1].split(',')]
    if len(pairs) != 15 or any(len(p) != 2 for p in pairs):
        sys.exit('15 ədəd "QM" cütü lazımdır, vergüllə')
    contains = sys.argv[2].upper() if len(sys.argv) > 2 else None
    run(pairs, words, contains=contains)
