#!/usr/bin/env python3
"""Isolate each drawing from its card: white-balance, cut everything that is
card paper or darker-than-paper background, keep the drawing, upscale, upright."""
import cv2,numpy as np
def iso(fn,box,Z=26,keep_dark=True,rot=0):
    im=cv2.imread(fn); x0,y0,x1,y1=box
    c=cv2.resize(im[y0:y1,x0:x1],None,fx=Z,fy=Z,interpolation=cv2.INTER_LANCZOS4).astype(np.float32)
    g=c.reshape(-1,3); L=g.mean(1); ref=g[L>=np.percentile(L,84)].mean(0)
    c=np.clip(c*(ref.mean()/ref),0,255).astype(np.uint8)
    lab=cv2.cvtColor(c,cv2.COLOR_BGR2LAB).astype(np.float32)
    Lc,A,B=lab[:,:,0],lab[:,:,1]-128,lab[:,:,2]-128
    sat=np.hypot(A,B)
    pl=np.percentile(Lc,80)
    draw=((Lc<pl-16)|(sat>9))            # ink or colour = the drawing
    draw=cv2.morphologyEx(draw.astype(np.uint8),cv2.MORPH_CLOSE,np.ones((Z//2|1,Z//2|1),np.uint8))
    draw=cv2.morphologyEx(draw,cv2.MORPH_OPEN,np.ones((Z//3|1,Z//3|1),np.uint8))
    n,lb,st,_=cv2.connectedComponentsWithStats(draw,8)
    if n<2: return None
    keep=np.zeros_like(draw)
    big=sorted(range(1,n),key=lambda k:-st[k,4])[:3]
    for k in big:
        if st[k,4] > 0.02*draw.size: keep[lb==k]=1
    out=np.full_like(c,255); out[keep>0]=c[keep>0]
    ys,xs=np.where(keep>0)
    if len(xs)<20: return None
    p=Z
    out=out[max(0,ys.min()-p):ys.max()+p, max(0,xs.min()-p):xs.max()+p]
    if rot: out=cv2.rotate(out,rot)
    return out
ITEMS=[('1 figure','REF803.png',(1645,397,1670,454),0),
       ('3 silhouette+plant','REF803.png',(1697,929,1752,984),0),
       ('6 two objects','REF806.png',(1782,642,1820,732),0),
       ('7 rectangle','REF803.png',(1697,482,1725,534),0),
       ('13 grey 2-panel','REF803.png',(1683,399,1708,452),0),
       ('14 curved form + bird','REF803.png',(1512,827,1558,886),0),
       ('15 wedge','REF_OFFICE.png',(1672,852,1690,880),0)]
tiles=[]
for lab,fn,box,rot in ITEMS:
    t=iso(fn,box,26,rot=rot)
    if t is None: print('skip',lab); continue
    s=560/max(t.shape[0],t.shape[1]); t=cv2.resize(t,(int(t.shape[1]*s),int(t.shape[0]*s)),interpolation=cv2.INTER_LANCZOS4)
    canvas=np.full((620,620,3),255,np.uint8)
    oy,ox=(620-t.shape[0])//2,(620-t.shape[1])//2
    canvas[oy:oy+t.shape[0],ox:ox+t.shape[1]]=t
    cv2.putText(canvas,lab,(10,32),cv2.FONT_HERSHEY_SIMPLEX,0.8,(0,0,200),2,cv2.LINE_AA)
    tiles.append(canvas)
rows=[np.hstack(tiles[i:i+4]) for i in range(0,len(tiles),4)]
W=max(r.shape[1] for r in rows)
rows=[np.hstack([r,np.full((r.shape[0],W-r.shape[1],3),255,np.uint8)]) for r in rows]
cv2.imwrite('ISOLATED.png',np.vstack(rows)); print('ok',len(tiles))
