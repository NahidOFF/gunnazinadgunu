#!/usr/bin/env python3
"""Lanczos contact sheet of every piece visible in one raw frame."""
import cv2,numpy as np
im=cv2.imread('REF803.png')
P=[  # label, x0,y0,x1,y1  (frame coords), numerals
 ('skater  II/XI',      1626,392,1676,455),
 ('window  VII/I',      1661,395,1714,446),
 ('arrow+chart VIII/IX',1701,376,1764,449),
 ('bow  V/VII',         1642,479,1699,536),
 ('rectangle VI/VIII',  1683,470,1746,539),
 ('snow cloud IX/V',    1801,483,1902,568),
 ('calendar III/IV',    1636,648,1689,714),
 ('two objects VI/VI',  1673,704,1733,777),
 ('US flag+barn VII/IV',1786,651,1902,727),
 ('joy  X/XIV',         1507,782,1596,833),
 ('rock+eagle ?',       1501,820,1583,896),
 ('Oman flag VI/V',     1636,889,1696,964),
 ('silhouette+plant IV/VIII',1689,911,1758,983),
]
Z=9; tiles=[]
for lab,x0,y0,x1,y1 in P:
    c=im[y0:y1,x0:x1]
    b=cv2.resize(c,None,fx=Z,fy=Z,interpolation=cv2.INTER_LANCZOS4)
    # white balance on the card's own paper
    g=b.reshape(-1,3).astype(np.float32); L=g.mean(1); ref=g[L>=np.percentile(L,85)].mean(0)
    b=np.clip(b.astype(np.float32)*(ref.mean()/ref),0,255).astype(np.uint8)
    tiles.append((lab,b))
CH=max(t.shape[0] for _,t in tiles)+34
CW=max(t.shape[1] for _,t in tiles)+16
COLS=5
rows=[]
for i in range(0,len(tiles),COLS):
    row=np.full((CH,CW*COLS,3),245,np.uint8)
    for j,(lab,t) in enumerate(tiles[i:i+COLS]):
        h,w=t.shape[:2]; ox=j*CW+(CW-w)//2; oy=30+(CH-30-h)//2
        row[oy:oy+h,ox:ox+w]=t
        cv2.putText(row,lab,(j*CW+8,22),cv2.FONT_HERSHEY_SIMPLEX,0.62,(0,0,0),2,cv2.LINE_AA)
    rows.append(row)
out=np.vstack(rows)
cv2.imwrite('PIECES_RAW803.png',out); print('PIECES_RAW803.png',out.shape)
