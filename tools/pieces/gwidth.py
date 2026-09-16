#!/usr/bin/env python3
"""gwidth.py IMG box:label ... -> ink bbox + stroke-count profile"""
import sys, cv2, numpy as np
im = cv2.imread(sys.argv[1]); lab = cv2.cvtColor(im, cv2.COLOR_BGR2LAB).astype(np.float32)
L = lab[:,:,0]
for spec in sys.argv[2:]:
    box,lb = spec.split(':'); x0,y0,x1,y1 = [int(v) for v in box.split(',')]
    P = L[y0:y1, x0:x1]
    # local paper = high percentile; ink = below midpoint between p10 and p90
    p10,p90 = np.percentile(P,8), np.percentile(P,92)
    thr = p10 + 0.45*(p90-p10)
    m = (P < thr).astype(np.uint8)
    m = cv2.morphologyEx(m, cv2.MORPH_OPEN, np.ones((3,3),np.uint8))
    ys,xs = np.nonzero(m)
    if len(xs)<10: print(f'{lb}: no ink'); continue
    w = xs.max()-xs.min()+1; h = ys.max()-ys.min()+1
    prof = m[ys.min():ys.max()+1, xs.min():xs.max()+1].sum(axis=0).astype(float)
    prof = prof/max(prof.max(),1)
    # count runs above 0.45
    b = prof > 0.45
    runs = 0; prev=False
    for v in b:
        if v and not prev: runs+=1
        prev=v
    print(f'{lb:12s} w={w:4d} h={h:4d} w/h={w/h:5.2f} runs={runs} prof={"".join("#" if v else "." for v in b)}')
