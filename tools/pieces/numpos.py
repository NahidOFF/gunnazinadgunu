#!/usr/bin/env python3
"""numpos.py -- for a rectified card render, locate the red and the blue numeral
and report their positions as fractions of the card, plus their relative layout."""
import sys,cv2,numpy as np
im=cv2.imread(sys.argv[1]).astype(np.float32); tag=sys.argv[2]
g=im.reshape(-1,3); L=g.mean(1); ref=g[L>=np.percentile(L,88)].mean(0)
w=np.clip(im*(ref.mean()/ref),0,255).astype(np.uint8)
lab=cv2.cvtColor(w,cv2.COLOR_BGR2LAB).astype(np.float32)
Lc,A,B=lab[:,:,0],lab[:,:,1]-128,lab[:,:,2]-128
sat=np.hypot(A,B)
paper=((Lc>np.percentile(Lc,72))&(sat<np.percentile(sat,50))).astype(np.uint8)
paper=cv2.morphologyEx(paper,cv2.MORPH_CLOSE,np.ones((15,15),np.uint8))
n,lb,st,_=cv2.connectedComponentsWithStats(paper,8)
if n<2: sys.exit(f'{tag}: no card')
k=int(np.argmax(st[1:,4])+1); card=(lb==k).astype(np.uint8)
cx0,cy0,cw,ch,_=st[k]
hull=cv2.convexHull(max(cv2.findContours(card,cv2.RETR_EXTERNAL,cv2.CHAIN_APPROX_SIMPLE)[0],key=cv2.contourArea))
inside=np.zeros_like(card); cv2.drawContours(inside,[hull],-1,1,-1)
inside=cv2.erode(inside,np.ones((13,13),np.uint8)).astype(bool)
pm=card.astype(bool)&inside; pa,pb,pL=A[pm].mean(),B[pm].mean(),Lc[pm].mean()
ink=cv2.morphologyEx(((Lc<pL-13)&inside).astype(np.uint8),cv2.MORPH_OPEN,np.ones((5,5),np.uint8))
n2,lb2,st2,ce2=cv2.connectedComponentsWithStats(ink,8)
best={'RED':None,'BLUE':None}
for j in range(1,n2):
    x,y,ww,hh,ar=st2[j]
    if ar<300 or ar>0.25*cw*ch: continue      # numerals are small marks
    m=lb2==j; da,db=A[m].mean()-pa,B[m].mean()-pb
    v='RED' if (da>2.0 and db<6.0) else ('BLUE' if db<-3.0 and da<2.0 else None)
    if not v: continue
    if best[v] is None or ar>best[v][0]: best[v]=(ar,ce2[j][0],ce2[j][1])
out=[]
for v in ('RED','BLUE'):
    if best[v] is None: out.append(f'{v}: not found'); continue
    _,x,y=best[v]
    fx,fy=(x-cx0)/cw,(y-cy0)/ch
    out.append(f'{v}: x={fx:.2f} y={fy:.2f}')
rel=''
if best['RED'] and best['BLUE']:
    ry,by=best['RED'][2],best['BLUE'][2]; rx,bx=best['RED'][1],best['BLUE'][1]
    rel=f"  -> red is {'ABOVE' if ry<by else 'BELOW'} blue, {'LEFT of' if rx<bx else 'RIGHT of'} blue"
print(f'{tag:22s} ' + ' | '.join(out) + rel)
