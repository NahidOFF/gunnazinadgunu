#!/usr/bin/env python3
"""numsheet.py -- one sheet: every card's numerals at high zoom with the detected
ink blobs outlined and their width/height printed.

Why w/h: on all cards but the flag the letters of a numeral merge into a single
ink blob at native resolution, so letters cannot be counted.  But w/h is free of
scale and (near enough) of pose, and each letter contributes a known amount:
I~0.26, V or X~0.72, plus ~0.15 per inter-letter gap, calibrated on the flag card
whose IV and VII do resolve.  A prior whose predicted w/h is far from the measured
one is FALSIFIED; a prior that matches is merely not refuted -- V and X, and IV
VI IX XI, are indistinguishable by width alone."""
import cv2,numpy as np
P=[('01 figure',   (1636,392,1676,458),'II','XI'),
   ('02 calendar', (1634,640,1694,724),'II','IV'),
   ('03 shape+plant',(1689,906,1760,990),'IV','VIII'),
   ('04 butterfly',(1648,478,1700,540),'V','VII'),
   ('05 oman',     (1618,884,1700,966),'VI','V'),
   ('06 two objects',(1668,702,1732,780),'VI','VI'),
   ('07 rectangle',(1684,472,1750,540),'VI','VIII'),
   ('08 hidden',   (1662,394,1700,460),'VII','I'),
   ('09 usflag',   (1782,636,1906,730),'VII','IV'),
   ('10 chart',    (1698,376,1764,454),'VIII','IX'),
   ('11 snow',     (1798,480,1906,572),'IX','V'),
   ('12 joy',      (1504,768,1600,842),'X','XIV'),
   ('13 cabinet',  (1678,392,1716,458),'?','?'),
   ('14 ovoid+eagle',(1494,806,1600,900),'?','?')]
im=cv2.imread('REF803.png').astype(np.float32)
Z=10; TW,TH=560,470; COLS=4
tiles=[]
for name,(x0,y0,x1,y1),red,blue in P:
    c=cv2.resize(im[y0:y1,x0:x1],None,fx=Z,fy=Z,interpolation=cv2.INTER_LANCZOS4)
    g=c.reshape(-1,3); L=g.mean(1); ref=g[L>=np.percentile(L,85)].mean(0)
    c=np.clip(c*(ref.mean()/ref),0,255).astype(np.uint8)
    lab=cv2.cvtColor(c,cv2.COLOR_BGR2LAB).astype(np.float32)
    Lc,A,B=lab[:,:,0],lab[:,:,1]-128,lab[:,:,2]-128
    pap=Lc>=np.percentile(Lc,80)
    dA,dB,dL=A-A[pap].mean(),B-B[pap].mean(),Lc[pap].mean()-Lc
    ink=((dL>10)|(np.abs(dA)>4)|(np.abs(dB)>6)).astype(np.uint8)
    ink=cv2.morphologyEx(ink,cv2.MORPH_OPEN,np.ones((Z//2,Z//2),np.uint8))
    n,lb,st,_=cv2.connectedComponentsWithStats(ink,8)
    CH=y1-y0
    vis=c.copy()
    for i in range(1,n):
        x,y,w,h=st[i][:4]
        if not (0.10*CH <= h/Z <= 0.34*CH): continue
        if w/Z > 0.55*(x1-x0): continue
        m=lb==i; da,db=dA[m].mean(),dB[m].mean()
        col=(0,0,220) if (da>1.5 and da>db) else ((220,120,0) if db<-2 else (0,150,0))
        cv2.rectangle(vis,(x,y),(x+w,y+h),col,2)
        cv2.putText(vis,f'{w/Z:.0f}x{h/Z:.0f}',(x,max(12,y-4)),
                    cv2.FONT_HERSHEY_SIMPLEX,0.5,col,1,cv2.LINE_AA)
    s=min(TW/vis.shape[1],(TH-44)/vis.shape[0])
    vis=cv2.resize(vis,(int(vis.shape[1]*s),int(vis.shape[0]*s)),interpolation=cv2.INTER_AREA)
    t=np.full((TH,TW,3),250,np.uint8)
    t[44:44+vis.shape[0],(TW-vis.shape[1])//2:(TW-vis.shape[1])//2+vis.shape[1]]=vis
    cv2.putText(t,f'{name}   prior {red} / {blue}',(8,26),cv2.FONT_HERSHEY_SIMPLEX,0.62,(30,30,30),2,cv2.LINE_AA)
    cv2.rectangle(t,(0,0),(TW-1,TH-1),(210,210,210),1)
    tiles.append(t)
while len(tiles)%COLS: tiles.append(np.full((TH,TW,3),250,np.uint8))
sheet=np.vstack([np.hstack(tiles[i:i+COLS]) for i in range(0,len(tiles),COLS)])
cv2.imwrite('NUMSHEET.png',sheet); print('ok',sheet.shape)
