#!/usr/bin/env python3
"""numcheck.py RENDER.png [minarea] -- for one rectified card, report every ink
mark inside the card and whether it is red or blue against THAT card's own paper.

The card is the largest bright, low-saturation region; marks are only counted
inside its eroded convex hull, so the cardboard around it cannot be mistaken for
red ink. Red ink is high a* but not strongly yellow; the cardboard is warm in
both, which is what the db* column is there to show.
"""
import sys,cv2,numpy as np
im=cv2.imread(sys.argv[1]).astype(np.float32)
MIN=int(sys.argv[2]) if len(sys.argv)>2 else 250
g=im.reshape(-1,3); L=g.mean(1); ref=g[L>=np.percentile(L,88)].mean(0)
w=np.clip(im*(ref.mean()/ref),0,255).astype(np.uint8)
lab=cv2.cvtColor(w,cv2.COLOR_BGR2LAB).astype(np.float32)
Lc,A,B=lab[:,:,0],lab[:,:,1]-128,lab[:,:,2]-128
sat=np.hypot(A,B)
paper=((Lc>np.percentile(Lc,72))&(sat<np.percentile(sat,50))).astype(np.uint8)
paper=cv2.morphologyEx(paper,cv2.MORPH_CLOSE,np.ones((15,15),np.uint8))
n,lb,st,_=cv2.connectedComponentsWithStats(paper,8)
if n<2: sys.exit('no card found')
k=int(np.argmax(st[1:,4])+1); card=(lb==k).astype(np.uint8)
cnt,_=cv2.findContours(card,cv2.RETR_EXTERNAL,cv2.CHAIN_APPROX_SIMPLE)
hull=cv2.convexHull(max(cnt,key=cv2.contourArea))
inside=np.zeros_like(card); cv2.drawContours(inside,[hull],-1,1,-1)
inside=cv2.erode(inside,np.ones((13,13),np.uint8)).astype(bool)
pm=card.astype(bool)&inside
pA,pB,pL=A[pm].mean(),B[pm].mean(),Lc[pm].mean()
print(f'{sys.argv[1]}  card paper L={pL:.1f} a*={pA:+.2f} b*={pB:+.2f}  (card = {pm.mean()*100:.0f}% of frame)')
ink=((Lc<pL-13)&inside)
ink=cv2.morphologyEx(ink.astype(np.uint8),cv2.MORPH_OPEN,np.ones((5,5),np.uint8))
n2,lb2,st2,ce2=cv2.connectedComponentsWithStats(ink,8)
rows=[]
for j in range(1,n2):
    x,y,ww,hh,ar=st2[j]
    if ar<MIN: continue
    m=lb2==j; da,db,dl=A[m].mean()-pA,B[m].mean()-pB,Lc[m].mean()-pL
    v='RED ' if (da>2.0 and db<6.0) else ('BLUE' if db<-3.0 and da<2.0 else 'dark')
    rows.append((ar,x,y,ww,hh,da,db,dl,v))
rows.sort(reverse=True)
for ar,x,y,ww,hh,da,db,dl,v in rows[:10]:
    print(f'  {v}  a={ar:6d} bbox=({x:4d},{y:4d}) {ww:3d}x{hh:3d}  da*={da:+6.2f} db*={db:+6.2f} dL={dl:+6.1f}')
