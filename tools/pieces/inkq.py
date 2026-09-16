#!/usr/bin/env python3
"""inkq.py IMG.png x0,y0,x1,y1:label ...  -> per-box ink hue vs local paper"""
import sys, cv2, numpy as np
im = cv2.imread(sys.argv[1]); lab = cv2.cvtColor(im, cv2.COLOR_BGR2LAB).astype(np.float32)
L,A,B = lab[:,:,0], lab[:,:,1]-128, lab[:,:,2]-128
for spec in sys.argv[2:]:
    box,lb = spec.split(':')
    x0,y0,x1,y1 = [int(v) for v in box.split(',')]
    sl = (slice(y0,y1), slice(x0,x1))
    Ls = L[sl]
    thr = np.percentile(Ls, 25)
    ink = Ls <= thr
    pap = Ls >= np.percentile(Ls, 70)
    da = float(A[sl][ink].mean() - A[sl][pap].mean())
    db = float(B[sl][ink].mean() - B[sl][pap].mean())
    verdict = 'RED ' if da > 1.5 else ('BLUE' if da < 0.5 else '????')
    print(f'{lb:14s} da*={da:+6.2f} db*={db:+6.2f} Link={Ls[ink].mean():5.1f} Lpap={Ls[pap].mean():5.1f} -> {verdict}')
