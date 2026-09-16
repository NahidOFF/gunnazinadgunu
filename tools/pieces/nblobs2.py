#!/usr/bin/env python3
"""nblobs2.py FRAME x0,y0,x1,y1 LABEL -- list EVERY ink blob of numeral height on
one card, with no colour gate.  The colour gate was the thing that failed: on a
small tilted card the ink mixes with paper and da/db collapse toward zero, so a
fixed threshold silently drops the numerals.  Here the numbers are printed and
the grouping is judged by hand."""
import sys,cv2,numpy as np
fn=sys.argv[1]; x0,y0,x1,y1=[int(v) for v in sys.argv[2].split(',')]; tag=sys.argv[3]
Z=8
im=cv2.imread(fn).astype(np.float32)
c=cv2.resize(im[y0:y1,x0:x1],None,fx=Z,fy=Z,interpolation=cv2.INTER_LANCZOS4)
g=c.reshape(-1,3); L=g.mean(1); ref=g[L>=np.percentile(L,85)].mean(0)
c=np.clip(c*(ref.mean()/ref),0,255).astype(np.uint8)
lab=cv2.cvtColor(c,cv2.COLOR_BGR2LAB).astype(np.float32)
Lc,A,B=lab[:,:,0],lab[:,:,1]-128,lab[:,:,2]-128
pap=Lc>=np.percentile(Lc,80)
dA,dB,dL=A-A[pap].mean(),B-B[pap].mean(),Lc[pap].mean()-Lc
CH=y1-y0
ink=((dL>10)|(np.abs(dA)>4)|(np.abs(dB)>6)).astype(np.uint8)
ink=cv2.morphologyEx(ink,cv2.MORPH_OPEN,np.ones((Z//2,Z//2),np.uint8))
n,lb,st,_=cv2.connectedComponentsWithStats(ink,8)
print(f'== {tag}   card {x1-x0}x{y1-y0}')
rows=[]
for i in range(1,n):
    x,y,w,h=[v/Z for v in st[i][:4]]; a=st[i][4]/Z/Z
    if not (0.10*CH <= h <= 0.34*CH): continue
    if w > 0.55*(x1-x0): continue
    m=lb==i
    rows.append((y,x,w,h,a,dA[m].mean(),dB[m].mean(),dL[m].mean()))
for y,x,w,h,a,da,db,dl in sorted(rows):
    hue='red' if da>1.5 and da>db else ('blue' if db<-2 else ('dark' if dl>22 else '?'))
    print(f'   x={x0+x:7.1f} y={y0+y:7.1f} w={w:5.1f} h={h:5.1f} '
          f'da={da:+5.1f} db={db:+5.1f} dL={dl:+5.1f}  {hue}')
if not rows: print('   (nothing of numeral height)')
