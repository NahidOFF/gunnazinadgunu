#!/usr/bin/env python3
"""inkarea.py RENDER.png SCALE -- ink area of each numeral mark, in native px^2.
SCALE = canon pixels per native pixel (canon width / quad width)."""
import sys,cv2,numpy as np
im=cv2.imread(sys.argv[1]).astype(np.float32); S=float(sys.argv[2])
g=im.reshape(-1,3); L=g.mean(1); ref=g[L>=np.percentile(L,88)].mean(0)
w=np.clip(im*(ref.mean()/ref),0,255).astype(np.uint8)
lab=cv2.cvtColor(w,cv2.COLOR_BGR2LAB).astype(np.float32)
Lc,A,B=lab[:,:,0],lab[:,:,1]-128,lab[:,:,2]-128
sat=np.hypot(A,B)
paper=((Lc>np.percentile(Lc,72))&(sat<np.percentile(sat,50))).astype(np.uint8)
paper=cv2.morphologyEx(paper,cv2.MORPH_CLOSE,np.ones((15,15),np.uint8))
n,lb,st,_=cv2.connectedComponentsWithStats(paper,8)
k=int(np.argmax(st[1:,4])+1); card=(lb==k).astype(np.uint8)
cnt,_=cv2.findContours(card,cv2.RETR_EXTERNAL,cv2.CHAIN_APPROX_SIMPLE)
hull=cv2.convexHull(max(cnt,key=cv2.contourArea))
inside=np.zeros_like(card); cv2.drawContours(inside,[hull],-1,1,-1)
inside=cv2.erode(inside,np.ones((13,13),np.uint8)).astype(bool)
pm=card.astype(bool)&inside
pA,pB,pL=A[pm].mean(),B[pm].mean(),Lc[pm].mean()
ink=((Lc<pL-13)&inside)
ink=cv2.morphologyEx(ink.astype(np.uint8),cv2.MORPH_OPEN,np.ones((5,5),np.uint8))
n2,lb2,st2,_=cv2.connectedComponentsWithStats(ink,8)
for j in range(1,n2):
    x,y,ww,hh,ar=st2[j]
    if ar<300: continue
    m=lb2==j; da,db=A[m].mean()-pA,B[m].mean()-pB
    v='RED' if (da>2.0 and db<6.0) else ('BLUE' if db<-3.0 and da<2.0 else None)
    if v: print(f'  {v:4s} bbox=({x},{y}) {ww}x{hh}  area={ar/S**2:7.1f} native px^2  w={ww/S:5.2f} h={hh/S:5.2f}  da*={da:+5.2f} db*={db:+5.2f}')
