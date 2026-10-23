#!/usr/bin/env python3
"""strokes.py IMG roi:label ...
Auto-locate the numeral inside the ROI, then count ink runs on horizontal slices at
20/35/50/65/80% of glyph height.  I=1 everywhere, V=2 near top -> 1 near bottom,
X=2 top and bottom (1 at the waist).  Prints the run profile so numerals can be read."""
import sys, cv2, numpy as np
im=cv2.imread(sys.argv[1]); lab=cv2.cvtColor(im,cv2.COLOR_BGR2LAB).astype(np.float32)
L=lab[:,:,0]
for spec in sys.argv[2:]:
    box,lb=spec.split(':'); x0,y0,x1,y1=[int(v) for v in box.split(',')]
    P=L[y0:y1,x0:x1]
    p20,p85=np.percentile(P,20),np.percentile(P,85)
    thr=p20+0.55*(p85-p20)
    m=(P<thr).astype(np.uint8)
    m=cv2.morphologyEx(m,cv2.MORPH_OPEN,np.ones((3,3),np.uint8))
    n,l,st,ce=cv2.connectedComponentsWithStats(m,8)
    comps=[(st[k,0],st[k,1],st[k,2],st[k,3],st[k,4]) for k in range(1,n) if st[k,4]>=0.0015*P.size]
    if not comps: print(f'{lb}: none'); continue
    hmax=max(c[3] for c in comps)
    comps=[c for c in comps if c[3]>0.35*hmax]           # keep tall strokes only
    xs0=min(c[0] for c in comps); xs1=max(c[0]+c[2] for c in comps)
    ys0=min(c[1] for c in comps); ys1=max(c[1]+c[3] for c in comps)
    g=m[ys0:ys1, xs0:xs1]; h,w=g.shape
    out=[]
    for f in (0.20,0.35,0.50,0.65,0.80):
        row=g[int(f*(h-1))]
        r=0; prev=0
        for v in row:
            if v and not prev: r+=1
            prev=v
        out.append(r)
    print(f'{lb:14s} bbox={w}x{h} w/h={w/h:5.2f} runs@20/35/50/65/80 = {out}')
