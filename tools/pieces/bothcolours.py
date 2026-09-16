#!/usr/bin/env python3
"""Solve both colours together under a naming-cost budget.

A piece takes a position only through one of its candidate names, and that one name
fixes BOTH letters -- so red and blue prune each other. On top of that, every name
carries a plausibility rank, and the search is bounded by the total rank it spends.
Low budget = only orderings whose naming a normal person would actually write down.
"""
import sys, re, time
sys.path.insert(0,'/home/user/gunnazinadgunu/tools/pieces')
from naming import PIECES, ORDER, options
SP='/tmp/claude-0/-home-user-gunnazinadgunu/84fa90fa-750b-5180-b6a9-f390607e1640/scratchpad/'
N=14
BUDGET=float(sys.argv[1]) if len(sys.argv)>1 else 4
MINW=int(sys.argv[2]) if len(sys.argv)>2 else 3
MAXWORDS=int(sys.argv[3]) if len(sys.argv)>3 else 2

words=set()
for line in open(SP+'g10k.txt'):
    w=line.strip().upper()
    if w.isalpha() and MINW<=len(w)<=N-MINW: words.add(w)
words |= {w for w in 'THE AND FOR ARE BUT NOT YOU ALL ONE OUT TWO OFF TOP TEN SIX SUN SEA WHO WHY YES YET NEW NOW ODD OWN'.split() if len(w)>=MINW}
class T:
    __slots__=('c','t')
    def __init__(self): self.c={}; self.t=False
ROOT=T()
for w in words:
    n=ROOT
    for ch in w: n=n.c.setdefault(ch,T())
    n.t=True
def step(state, ch, i):
    out=set()
    for ph,node in state:
        nn=node.c.get(ch)
        if nn is None: continue
        out.add((ph,nn))
        if ph<MAXWORDS-1 and nn.t:
            rem=N-(i+1)
            if MINW<=rem<=N-MINW: out.add((ph+1,ROOT))
    return frozenset(out)
def accepts(state): return any(node.t for ph,node in state if ph>=1)
START=frozenset({(0,ROOT)})

OPT=options()
CAND=[]                      # per piece: list of (rank, name, redLetter, blueLetter or None)
for k in ORDER: CAND.append(sorted(OPT[k]))
AZ='ABCDEFGHIJKLMNOPQRSTUVWXYZ'
hits=[]; nodes=0; t0=time.time()
def rec(i, used, cost, rs, bs, red, blue, chosen):
    global nodes
    nodes+=1
    if i==N:
        if accepts(rs) and accepts(bs):
            hits.append((cost, ''.join(red), ''.join(blue), list(chosen)))
        return
    for u in range(N):
        if used>>u & 1: continue
        for rank,nm,rl,bl in CAND[u]:
            if cost+rank > BUDGET: break        # CAND is rank-sorted
            nrs=step(rs, rl, i)
            if not nrs: continue
            bls = [bl] if bl else list(AZ)
            for b in bls:
                nbs=step(bs, b, i)
                if not nbs: continue
                red.append(rl); blue.append(b); chosen.append((ORDER[u],nm))
                rec(i+1, used|(1<<u), cost+rank, nrs, nbs, red, blue, chosen)
                red.pop(); blue.pop(); chosen.pop()
rec(0,0,0,START,START,[],[],[])
print('budget %.0f  nodes %d  hits %d  %.0fs'%(BUDGET,nodes,len(hits),time.time()-t0))
seen=set()
hits.sort(key=lambda h:h[0])
for cost,red,blue,chosen in hits:
    key=(red,blue)
    if key in seen: continue
    seen.add(key)
    print('\ncost %.0f   RED %s   BLUE %s'%(cost,red,blue))
    print('   '+', '.join('%s=%s'%(k,n) for k,n in chosen))
    if len(seen)>=40: break
