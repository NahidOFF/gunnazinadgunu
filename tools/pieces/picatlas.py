#!/usr/bin/env python3
"""Pictures only, at maximum useful zoom, one tile per drawing."""
import cv2,numpy as np
im=cv2.imread('REF803.png')
P=[('1 figure (skater?)',      1644,396,1670,455),
   ('2 window / frame',        1681,396,1709,455),
   ('3 down arrow',            1707,396,1724,440),
   ('4 bar chart',             1718,390,1750,440),
   ('5 BUTTERFLY',             1653,486,1684,516),
   ('6 red-brown rectangle',   1696,481,1726,535),
   ('7 cloud with snow',       1810,492,1866,548),
   ('8 calendar "25"',         1643,656,1670,704),
   ('9 two tall objects',      1688,712,1714,764),
   ('10 US flag',              1796,661,1844,702),
   ('11 barn / red building',  1843,658,1888,708),
   ('12 face with tears',      1532,790,1564,822),
   ('13 ovoid (rock?)',        1506,826,1534,864),
   ('14 bald eagle',           1530,850,1560,888),
   ('15 Oman flag',            1650,898,1692,944),
   ('16 dark silhouette',      1698,930,1728,980),
   ('17 green plant',          1718,944,1750,984)]
Z=20; tiles=[]
for lab,x0,y0,x1,y1 in P:
    b=cv2.resize(im[y0:y1,x0:x1],None,fx=Z,fy=Z,interpolation=cv2.INTER_LANCZOS4).astype(np.float32)
    g=b.reshape(-1,3); L=g.mean(1); ref=g[L>=np.percentile(L,82)].mean(0)
    b=np.clip(b*(ref.mean()/ref),0,255)
    lb=cv2.cvtColor(b.astype(np.uint8),cv2.COLOR_BGR2LAB).astype(np.float32)
    Lc=lb[:,:,0]; lo,hi=np.percentile(Lc,2),np.percentile(Lc,98)
    lb[:,:,0]=np.clip((Lc-lo)*255/max(hi-lo,1),0,255)
    lb[:,:,1]=np.clip((lb[:,:,1]-128)*1.6+128,0,255)
    lb[:,:,2]=np.clip((lb[:,:,2]-128)*1.6+128,0,255)
    tiles.append((lab,cv2.cvtColor(lb.astype(np.uint8),cv2.COLOR_LAB2BGR)))
CH=max(t.shape[0] for _,t in tiles)+46; CW=max(t.shape[1] for _,t in tiles)+24
COLS=5; rows=[]
for i in range(0,len(tiles),COLS):
    row=np.full((CH,CW*COLS,3),250,np.uint8)
    for j,(lab,t) in enumerate(tiles[i:i+COLS]):
        h,w=t.shape[:2]; ox=j*CW+(CW-w)//2; oy=40+(CH-40-h)//2
        row[oy:oy+h,ox:ox+w]=t
        cv2.rectangle(row,(ox-2,oy-2),(ox+w+2,oy+h+2),(150,150,150),2)
        cv2.putText(row,lab,(j*CW+12,30),cv2.FONT_HERSHEY_SIMPLEX,0.85,(15,15,15),2,cv2.LINE_AA)
    rows.append(row)
o=np.vstack(rows); cv2.imwrite('PICTURES_ONLY.png',o); print('PICTURES_ONLY.png',o.shape)
