#!/usr/bin/env python3
"""strokes4.py FRAME x0,y0,x1,y1 ZOOM LABEL [ANGLE] -- strokes3 with a deskew.

strokes3's top/middle/bottom bands assume the glyph's own axis is vertical. On a
card seen at an angle the numerals are sheared, the bands cut across strokes,
and the control fails (the flag card's red VII returned 0 top peaks on REF767
where it reads correctly on the near-frontal REF803). Rotating the crop first
fixes that -- but the rotation has to be CALIBRATED ON A KNOWN NUMERAL, not
guessed, which is what the sweep mode does."""
import sys,cv2,numpy as np
LET={'I':(1,1,1),'V':(2,2,1),'X':(2,1,2)}
ROMAN=['I','II','III','IV','V','VI','VII','VIII','IX','X','XI','XII','XIII','XIV','XV']
def sig(w):
    t=m=b=0
    for ch in w:
        a,c,d=LET[ch]; t+=a; m+=c; b+=d
    return (t,m,b)
fn=sys.argv[1]; x0,y0,x1,y1=[int(v) for v in sys.argv[2].split(',')]
Z=int(sys.argv[3]); tag=sys.argv[4]
angles=[float(sys.argv[5])] if len(sys.argv)>5 else list(range(-24,25,4))
im=cv2.imread(fn).astype(np.float32)
pad=6
sub=im[max(0,y0-pad):y1+pad, max(0,x0-pad):x1+pad]
best=[]
for ang in angles:
    c=cv2.resize(sub,None,fx=Z,fy=Z,interpolation=cv2.INTER_LANCZOS4)
    h,w=c.shape[:2]
    M=cv2.getRotationMatrix2D((w/2,h/2),ang,1.0)
    r=cv2.warpAffine(c,M,(w,h),flags=cv2.INTER_LANCZOS4,borderMode=cv2.BORDER_REPLICATE)
    r=r[pad*Z:h-pad*Z, pad*Z:w-pad*Z]
    if r.size==0: continue
    g=r.reshape(-1,3); L=g.mean(1); ref=g[L>=np.percentile(L,85)].mean(0)
    r=np.clip(r*(ref.mean()/ref),0,255).astype(np.uint8)
    gr=cv2.cvtColor(r,cv2.COLOR_BGR2GRAY).astype(np.float32)
    d=255-gr; d-=np.percentile(d,10); d=np.clip(d,0,None); H=d.shape[0]
    gap=max(3,Z//2)
    def peaks(a,b):
        p=d[int(a):int(b)].mean(0)
        p=np.convolve(p,np.ones(max(3,Z//3))/max(3,Z//3),'same')
        out=[]
        for i in range(gap,len(p)-gap):
            if p[i]==max(p[i-gap:i+gap+1]) and p[i]>0.42*p.max():
                if not out or i-out[-1]>gap: out.append(i)
        return out
    T,M2,B=peaks(H*0.08,H*0.36),peaks(H*0.40,H*0.60),peaks(H*0.64,H*0.92)
    obs=(len(T),len(M2),len(B))
    cand=[x for x in ROMAN if sig(x)==obs]
    best.append((ang,obs,cand))
for ang,obs,cand in best:
    mark='  <=' if cand else ''
    print(f'  {tag:22s} angle {ang:+6.1f}  signature {obs[0]}/{obs[1]}/{obs[2]}  -> {cand or "none"}{mark}')
