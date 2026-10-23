#!/usr/bin/env python3
"""Sweep every two-word fourteen-letter phrase and rank it by naming cost.

For each phrase, the minimum-cost assignment of pieces to positions says how strained
the naming would have to be. A phrase that needs only rank-0 and rank-1 names is worth
looking at; one that needs rank-6 names for half the pieces is noise.
"""
import sys, re, time
import numpy as np
from scipy.optimize import linear_sum_assignment
sys.path.insert(0,'/home/user/gunnazinadgunu/tools/pieces')
from mincost import CR, CB, NR, NB, ORDER, N, INF, detail, other_string
SP='/tmp/claude-0/-home-user-gunnazinadgunu/84fa90fa-750b-5180-b6a9-f390607e1640/scratchpad/'
colour = sys.argv[1] if len(sys.argv)>1 else 'red'
LIMIT  = float(sys.argv[2]) if len(sys.argv)>2 else 14.0
WORDS  = sys.argv[3] if len(sys.argv)>3 else SP+'g10k.txt'
C = CR if colour=='red' else CB
print('floor (sum of each piece\'s cheapest letter): %.1f'%C.min(axis=1).sum())

words=set()
for line in open(WORDS,errors='ignore'):
    w=re.sub(r'[^A-Za-z]','',line.strip()).upper()
    if 2<=len(w)<=12: words.add(w)
SHORT=set('OF IN TO ON AT IS IT BY AS MY NO SO UP US WE AN OR DO GO HE ME BE IF A I'.split())
words |= SHORT
bylen={}
for w in words: bylen.setdefault(len(w),[]).append(w)
print('words', len(words), {k:len(v) for k,v in sorted(bylen.items())})

# cheap lower bound: relax the distinctness of positions
def lb(idx):
    return C[:, idx].min(axis=1).sum()

hits=[]; tested=0; t0=time.time()
for l1 in sorted(bylen):
    l2=N-l1
    if l2 not in bylen: continue
    if l1<2 or l2<2: continue
    A=bylen[l1]; B=bylen[l2]
    Aidx={w:np.array([ord(c)-65 for c in w]) for w in A}
    Bidx={w:np.array([ord(c)-65 for c in w]) for w in B}
    for w1 in A:
        i1=Aidx[w1]
        for w2 in B:
            tested+=1
            idx=np.concatenate([i1,Bidx[w2]])
            if lb(idx) > LIMIT: continue
            M=C[:,idx]
            if (M>=INF).all(axis=1).any(): continue
            r,c=linear_sum_assignment(M)
            tot=M[r,c].sum()
            if tot<=LIMIT:
                hits.append((tot,w1+' '+w2,''.join(w1+w2),{ORDER[i]:int(p) for i,p in zip(r,c)}))
    print('  %2d+%-2d done  tested %9d  hits %5d  %.0fs'%(l1,l2,tested,len(hits),time.time()-t0),flush=True)
hits.sort(key=lambda h:h[0])
print('\nTESTED %d   HITS %d\n'%(tested,len(hits)))
for tot,disp,tt,assign in hits[:60]:
    print('cost %5.1f   %-16s   other colour: %s'%(tot,disp,other_string(tt,assign,colour)))
import json
json.dump([[h[0],h[1],h[2]] for h in hits[:4000]], open(SP+'SWEEP_%s.json'%colour,'w'))
