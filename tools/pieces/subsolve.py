#!/usr/bin/env python3
"""Solve for the name itself.

The pieces' numerals index into an unknown name, so the message is a simple
substitution over the DISTINCT index values - eleven of them. That is small
enough to solve directly: hill-climb an assignment of letters to positions
against English quadgram statistics. The control is the old puzzle, whose
answer is known.
"""
import re,math,random
random.seed(7)
# quadgram model from the word list (weighted by word, good enough for 24 chars)
CNT={}
for w in open('words.txt'):
    w=w.strip().upper()
    if len(w)<4: continue
    for i in range(len(w)-3):
        g=w[i:i+4]; CNT[g]=CNT.get(g,0)+1
TOT=sum(CNT.values()); FLOOR=math.log(0.01/TOT)
def q(s):
    s=re.sub(r'[^A-Z]','',s)
    if len(s)<4: return -999
    return sum(math.log(CNT[s[i:i+4]]/TOT) if s[i:i+4] in CNT else FLOOR
               for i in range(len(s)-3))/(len(s)-3)
ALPHA='ETAOINSRHLDCUMFPGWYBVKXJQZ'
def solve(seq,iters=60000,restarts=40):
    syms=sorted(set(seq))
    best=(-1e9,None)
    for r in range(restarts):
        m={s:random.choice(ALPHA) for s in syms}
        cur=q(''.join(m[x] for x in seq))
        T=1.0
        for it in range(iters):
            s=random.choice(syms); old=m[s]
            m[s]=random.choice(ALPHA)
            new=q(''.join(m[x] for x in seq))
            if new>cur or random.random()<math.exp((new-cur)/max(T,1e-6)):
                cur=new
            else:
                m[s]=old
            T=max(0.02,1.0*(1-it/iters))
        if cur>best[0]: best=(cur,dict(m))
    return best
def show(seq,label):
    sc,m=solve(seq)
    txt=''.join(m[x] for x in seq)
    print(f'{label:26s} bal {sc:6.3f}  ->  {txt}')
    print(f'{"":26s} mövqe→hərf: '+' '.join(f'{k}={m[k]}' for k in sorted(m)))
    return sc,m,txt
# ---- control ----
OLD=[11,6,2,12,4,7,8,13,7,3,13,11,8,9,7,12,1,11,9,4]
print('NEZARET - kohne OP1 (dogru cavab AHOMEAREANEARKAMLAKE):')
show(OLD,'kohne 20 reqem')
print()
RED=[2,2,4,5,6,6,6,7,7,8,9,10]
BLUE=[11,4,8,7,5,6,8,1,4,9,5,14]
seqs={
 'q,m cut (tarix)':[v for p in zip(RED,BLUE) for v in p],
 'm,q cut (tarix)':[v for p in zip(BLUE,RED) for v in p],
 'butun q + butun m':RED+BLUE,
 'butun m + butun q':BLUE+RED,
 'ters tarix q,m':[v for p in zip(RED[::-1],BLUE[::-1]) for v in p],
}
print('BIZIM REQEMLER:')
for k,v in seqs.items(): show(v,k); print()
