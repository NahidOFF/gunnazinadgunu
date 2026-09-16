#!/usr/bin/env python3
"""strokes3.py FRAME x0,y0,x1,y1 ZOOM LABEL -- read a Roman numeral by counting
the vertical strokes crossing three horizontal bands of the glyph.

Why three bands: a column-darkness profile of the TOP and BOTTOM alone cannot
separate II from X (both 2/2).  The MIDDLE band can: X pinches to one crossing
point, II stays two.  Signatures (top/mid/bot):
    I 1/1/1   V 2/2/1   X 2/1/2
so any numeral's signature is the sum of its letters'.  IV and VI share 3/3/2;
they are told apart by ORDER -- whether the lone I sits left or right of the V.
Raw peak positions are always printed so the reading can be judged, never just
a verdict."""
import sys,cv2,numpy as np
from itertools import product

LET={'I':(1,1,1),'V':(2,2,1),'X':(2,1,2)}
def sig(word):
    t=m=b=0
    for ch in word:
        a,c,d=LET[ch]; t+=a; m+=c; b+=d
    return (t,m,b)
ROMAN=['I','II','III','IV','V','VI','VII','VIII','IX','X','XI','XII','XIII','XIV','XV','XVI','XVII','XVIII','XIX','XX']

fn=sys.argv[1]; x0,y0,x1,y1=[int(v) for v in sys.argv[2].split(',')]
Z=int(sys.argv[3]); tag=sys.argv[4]
im=cv2.imread(fn).astype(np.float32)
c=cv2.resize(im[y0:y1,x0:x1],None,fx=Z,fy=Z,interpolation=cv2.INTER_LANCZOS4)
g=c.reshape(-1,3); L=g.mean(1); ref=g[L>=np.percentile(L,85)].mean(0)
c=np.clip(c*(ref.mean()/ref),0,255).astype(np.uint8)
gr=cv2.cvtColor(c,cv2.COLOR_BGR2GRAY).astype(np.float32)
d=255-gr; d-=np.percentile(d,10); d=np.clip(d,0,None)
H=d.shape[0]

def peaks(p,frac=0.42):
    gap=max(3,Z//2)
    p=np.convolve(p,np.ones(max(3,Z//3))/max(3,Z//3),'same')
    out=[]
    for i in range(gap,len(p)-gap):
        if p[i]==max(p[i-gap:i+gap+1]) and p[i]>frac*p.max():
            if not out or i-out[-1]>gap: out.append(i)
    return out

BANDS={'TOP':(0.08,0.36),'MID':(0.40,0.60),'BOT':(0.64,0.92)}
res={}
for band,(a,b) in BANDS.items():
    pk=peaks(d[int(H*a):int(H*b)].mean(0))
    res[band]=[round(x/Z,1) for x in pk]
    print(f'  {tag:18s} {band}: {len(pk)}  x(native)={res[band]}')
obs=(len(res['TOP']),len(res['MID']),len(res['BOT']))
cand=[r for r in ROMAN if sig(r)==obs]
print(f'  {"":18s} signature {obs[0]}/{obs[1]}/{obs[2]}  -> candidates: {cand or "none"}')
if len(cand)>1:
    # order test: a V contributes a BOT peak lying BETWEEN two TOP peaks;
    # an I contributes a BOT peak ALIGNED with one TOP peak.
    T,B=res['TOP'],res['BOT']
    kinds=[]
    for x in B:
        near=min(abs(x-t) for t in T)
        kinds.append('I' if near<=1.2 else 'V/X')
    print(f'  {"":18s} bottom peaks read left->right as {kinds}')
