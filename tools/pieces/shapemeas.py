#!/usr/bin/env python3
"""shapemeas.py RECT.png LABEL -- measure a rectified drawing: outline bbox, aspect,
solidity, and the row-darkness profile that shows where internal dividers sit.
Measurements only.  Eleven automatic classifiers have failed their controls in
this hunt; a measurement that merely excludes candidates is worth more than a
twelfth one that names them."""
import sys,cv2,numpy as np
im=cv2.imread(sys.argv[1]); tag=sys.argv[2]
im=im[:,:im.shape[1]//2]                      # left half = balanced, not chroma-boosted
g=cv2.cvtColor(im,cv2.COLOR_BGR2GRAY).astype(np.float32)
d=255-g; d-=np.percentile(d,25); d=np.clip(d,0,None)
m=(d>0.45*d.max()).astype(np.uint8)
m=cv2.morphologyEx(m,cv2.MORPH_CLOSE,np.ones((5,5),np.uint8))
n,lb,st,_=cv2.connectedComponentsWithStats(m,8)
if n<2: sys.exit('no ink')
k=1+int(np.argmax(st[1:,4])); x,y,w,h,a=st[k]
cnt,_=cv2.findContours((lb==k).astype(np.uint8),cv2.RETR_EXTERNAL,cv2.CHAIN_APPROX_SIMPLE)
hull=cv2.convexHull(cnt[0]); ha=cv2.contourArea(hull)
print(f'== {tag}')
print(f'   outline bbox {w}x{h}  aspect h/w = {h/w:.2f}   solidity = {a/max(ha,1):.2f}')
prof=d[y:y+h,x:x+w].mean(1); prof/=prof.max()
print('   row darkness every 5% of height (1.00 = darkest row):')
for f in range(0,101,5):
    i=min(h-1,int(h*f/100)); bar='#'*int(prof[i]*40)
    print(f'     {f:3d}%  {prof[i]:.2f} {bar}')
col=d[y:y+h,x:x+w].mean(0); col/=col.max()
print('   column darkness every 10% of width:')
print('     '+' '.join(f'{col[min(w-1,int(w*f/100))]:.2f}' for f in range(0,101,10)))
