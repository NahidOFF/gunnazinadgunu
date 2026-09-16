#!/usr/bin/env python3
"""edgeprof.py FRAME x0,y0,x1,y1 SIDE LABEL -- the profile of one card edge.

For each row of the card blob, take the extreme white pixel on the chosen side.
Fit and remove the straight trend (the card is tilted), leaving the deviation:
that is the tooth pattern.  Reported in pixels along the edge so two cards can
be compared directly.

The point is a yes/no question: do all the pieces carry the SAME zigzag, in
which case the edges are decoration, or DIFFERENT ones, in which case the edges
order the pieces."""
import sys,cv2,numpy as np
fn=sys.argv[1]; x0,y0,x1,y1=[int(v) for v in sys.argv[2].split(',')]
side=sys.argv[3]; tag=sys.argv[4]
im=cv2.imread(fn); sub=im[y0:y1,x0:x1]
lab=cv2.cvtColor(sub,cv2.COLOR_BGR2LAB)
L=lab[:,:,0].astype(np.int16); B=lab[:,:,2].astype(np.int16)-128
m=((B<16)&(L>132)).astype(np.uint8)
m=cv2.morphologyEx(m,cv2.MORPH_CLOSE,np.ones((3,3),np.uint8))
n,lb,st,_=cv2.connectedComponentsWithStats(m,8)
k=1+int(np.argmax(st[1:,4])); sel=(lb==k)
rows=[]
for r in range(sel.shape[0]):
    xs=np.nonzero(sel[r])[0]
    if len(xs)<6: continue
    rows.append((r, xs.min() if side=='left' else xs.max()))
if len(rows)<12: sys.exit(f'{tag}: edge too short')
r=np.array([v[0] for v in rows],float); e=np.array([v[1] for v in rows],float)
# Drop 12% of rows at each end: near the corners the extreme pixel of a row
# belongs to the TOP or BOTTOM edge, not the side, and those outliers dominated
# the straight-line fit on the first run.
c=max(2,int(0.12*len(r))); r=r[c:-c]; e=e[c:-c]
a,b=np.polyfit(r,e,1); dev=e-(a*r+b)
L2=r.max()-r.min()
print(f'== {tag}  {side} edge, {len(r)} rows, span {L2:.0f}px, tilt {a:+.2f}px/row')
print(f'   deviation from the straight trend, at 5% steps along the edge:')
s=''
for f in range(0,101,5):
    i=int(np.clip(np.searchsorted(r,r.min()+L2*f/100),0,len(r)-1))
    s+=f'{dev[i]:+5.1f} '
print('   '+s)
print(f'   peak-to-peak {dev.max()-dev.min():.1f}px   rms {dev.std():.2f}px   '
      f'({100*(dev.max()-dev.min())/L2:.0f}% of edge length)')
