#!/usr/bin/env python3
"""Build both colours at once.

Fourteen pieces, one order, two strings.  A piece can only sit at a position if one of
its candidate names puts the right letter there in RED -- and that same name then fixes
the BLUE letter at the same position.  So walk the positions left to right, choosing a
piece and a name for each, and prune the moment either string stops being the prefix of
a two-word fourteen-letter phrase.  Both prefixes have to stay alive; that is the whole
strength of the search.
"""
import sys
from functools import lru_cache
SP='/tmp/claude-0/-home-user-gunnazinadgunu/84fa90fa-750b-5180-b6a9-f390607e1640/scratchpad/'
N=14; MINW,MAXW=3,11
words=set()
for line in open(SP+'g10k.txt'):
    w=line.strip().upper()
    if w.isalpha() and MINW<=len(w)<=MAXW: words.add(w)
words|= {'THE','AND','FOR','ARE','BUT','NOT','YOU','ALL','CAN','HAD','HER','WAS','ONE',
         'OUR','OUT','DAY','GET','HAS','HIM','HIS','HOW','ITS','NEW','NOW','OLD','SEE',
         'TWO','WHO','BOY','DID','MAN','MEN','PUT','SAY','SHE','TOO','USE'}
class T:
    __slots__=('c','t')
    def __init__(self): self.c={}; self.t=False
ROOT=T()
for w in words:
    n=ROOT
    for ch in w:
        n=n.c.setdefault(ch,T())
    n.t=True
def step(state, ch, i):
    """state: frozenset of ('A'|'B', node). i = index of the letter just consumed (0-based)"""
    out=set()
    for ph,node in state:
        nn=node.c.get(ch)
        if nn is None: continue
        out.add((ph,nn))
        if ph=='A' and nn.t:
            l1=i+1
            if MINW<=l1<=MAXW and MINW<=N-l1<=MAXW: out.add(('B',ROOT))
    return frozenset(out)
def alive(state): return bool(state)
def accepts(state): return any(ph=='B' and node.t for ph,node in state)
START=frozenset({('A',ROOT)})

AZ='ABCDEFGHIJKLMNOPQRSTUVWXYZ'
PAIRS=[
 ('calendar', [('A','E'),('E','K'),('P','R'),('E','R'),('D','E')]),
 ('gnome',    [('A','E'),('H','L'),('H','S'),('L','H')]),
 ('sil+plant',[('O','F'),('I','O'),('T','N'),('T','A'),('H','T')]),
 ('bow',      [('E','F'),('S','S'),('L','S'),('N','B'),('B','W')]),
 ('oman',     [('F','O'),('L','F'),('M','O'),('I','I'),('T','A')]),
 ('twothin',  [(c,c) for c in AZ]),
 ('rect',     [('C','A'),('R','C'),('U','R'),('S','U'),('D','O'),('O','K')]),
 ('frames',   [('T','M'),('B','F'),('E','P'),('P','F'),('N','T'),('W','W'),('S','W')]),
 ('usbarn',   [('A','R'),('D','G'),('I','G'),('G','A')]),
 ('chart',    [('H','A'),('O','W'),('E','C'),('T','D'),('D','C')]),
 ('snow',     [('H','D'),('D','C'),('E','F'),('M','S'),('E','H'),('C','I')]),
 ('joy',      [('E','O'),('R','G'),('G','G'),('Y','J')]),
 ('eagle',    [('G','E'),('C','L'),('N','R'),('E','L'),('D','L')]),
 ('p15',      [(r,b) for r in 'IEGA' for b in AZ]),
]
LIMIT=int(sys.argv[1]) if len(sys.argv)>1 else 400
hits=[]; nodes=0
def rec(i, used, rs, bs, red, blue):
    global nodes
    nodes+=1
    if len(hits)>=LIMIT: return
    if i==N:
        if accepts(rs) and accepts(bs): hits.append((''.join(red),''.join(blue)))
        return
    for k,(lab,prs) in enumerate(PAIRS):
        if used>>k & 1: continue
        for r,b in prs:
            nrs=step(rs,r,i)
            if not nrs: continue
            nbs=step(bs,b,i)
            if not nbs: continue
            red.append(r); blue.append(b)
            rec(i+1, used|(1<<k), nrs, nbs, red, blue)
            red.pop(); blue.pop()
rec(0,0,START,START,[],[])
print('nodes visited',nodes,' hits',len(hits))
seen=set()
for r,b in hits:
    if (r,b) in seen: continue
    seen.add((r,b))
    print('RED',r,'  BLUE',b)
