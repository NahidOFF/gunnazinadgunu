#!/usr/bin/env python3
"""Every numeral I have read, cropped from the sharpest available image, at one
size, so all 24 can be checked side by side."""
import cv2, numpy as np
N = [
 ("rolik",      "RED II",   "IBP_topbox.png", (55,300,180,495)),
 ("rolik",      "BLU XI",   "IBP_topbox.png", (75,665,215,825)),
 ("gizli sekil","RED VII",  "IBP_topbox.png", (415,400,575,560)),
 ("gizli sekil","BLU I",    "IBP_topbox.png", (365,415,430,560)),
 ("diaqram",    "RED VIII", "IBP_topbox.png", (845,155,1065,285)),
 ("diaqram",    "BLU IX",   "IBP_topbox.png", (1125,535,1245,685)),
 ("bant",       "RED V",    "IBP_topbox.png", (225,1465,335,1635)),
 ("bant",       "BLU VII",  "IBP_topbox.png", (365,1465,505,1645)),
 ("duzbucaq",   "RED VI",   "IBP_topbox.png", (525,1455,665,1635)),
 ("duzbucaq",   "BLU VIII", "IBP_topbox.png", (915,1455,1095,1645)),
 ("teqvim",     "BLU IV",   "IBP_cal765.png", (430,60,620,260)),
 ("teqvim",     "RED III",  "IBP_cal765.png", (500,480,660,700)),
 ("iki obyekt", "RED VII",  "IBP_two.png",    (720,10,950,110)),
 ("iki obyekt", "BLU VI",   "IBP_two.png",    (180,255,400,395)),
 ("ABS bayragi","BLU IV",   "IBP_usflag.png", (255,90,450,270)),
 ("ABS bayragi","RED VII",  "IBP_usflag.png", (60,430,300,600)),
 ("Oman",       "RED VI",   "PSR_oman.png",   (60,60,250,230)),
 ("Oman",       "BLU V",    "PSR_oman.png",   (200,300,350,520)),
 ("Afrika",     "BLU VIII", "sr803/R8_bottom.png",(1200,480,1470,700)),
 ("Afrika",     "RED IV",   "sr803/R8_bottom.png",(1500,720,1720,940)),
 ("qar buludu", "RED IX",   "PSR_snow.png",   (60,600,420,900)),
 ("qar buludu", "BLU V",    "PSR_snow.png",   (830,150,1080,430)),
 ("sevinc uz",  "BLU XIV",  "PSR_joy.png",    (600,60,930,260)),
 ("sevinc uz",  "RED X",    "PSR_joy.png",    (790,330,980,520)),
]
tiles=[]
for piece,label,path,(x0,y0,x1,y1) in N:
    im=cv2.imread(path)
    if im is None: print('MISSING',path); continue
    h,w=im.shape[:2]
    x0,x1=max(0,min(x0,w-2)),max(2,min(x1,w)); y0,y1=max(0,min(y0,h-2)),max(2,min(y1,h))
    c=im[y0:y1,x0:x1]
    if c.size==0: print('EMPTY',piece,label); continue
    a=c.astype(np.float32)
    flat=a.reshape(-1,3); pap=flat[np.argsort(flat.sum(1))[-max(10,int(.25*len(flat))):]].mean(0)
    a=np.clip(a*(np.array([242.,242.,242.])/np.maximum(pap,1)),0,255)
    lo,hi=np.percentile(a,3),np.percentile(a,99)
    c=np.clip((a-lo)*255/max(hi-lo,1),0,255).astype(np.uint8)
    s=200/max(c.shape[0],c.shape[1])
    c=cv2.resize(c,(max(1,int(c.shape[1]*s)),max(1,int(c.shape[0]*s))),interpolation=cv2.INTER_LANCZOS4)
    pad=np.full((250,230,3),255,np.uint8)
    yo=(200-c.shape[0])//2+44; xo=(230-c.shape[1])//2
    pad[yo:yo+c.shape[0],xo:xo+c.shape[1]]=c
    cv2.putText(pad,piece[:16],(5,17),0,0.45,(0,0,170),1,cv2.LINE_AA)
    col=(0,0,200) if label.startswith('RED') else (170,60,0)
    cv2.putText(pad,label,(5,35),0,0.55,col,1,cv2.LINE_AA)
    cv2.rectangle(pad,(0,0),(229,249),(200,200,200),1)
    tiles.append(pad)
rows=[np.hstack(tiles[i:i+8]) for i in range(0,len(tiles),8)]
w=max(r.shape[1] for r in rows)
rows=[np.pad(r,((0,0),(0,w-r.shape[1]),(0,0)),constant_values=255) for r in rows]
out=np.vstack(rows)
hdr=np.full((44,out.shape[1],3),255,np.uint8)
cv2.putText(hdr,"24 REQEM - hamisi en yaxsi goruntuden, eyni olcude, kagizin oz agina gore balanslanmis",(10,30),0,0.7,(0,0,0),2,cv2.LINE_AA)
cv2.imwrite('NUMERALS_ALL.png',np.vstack([hdr,out])); print('wrote',out.shape,len(tiles),'tiles')
