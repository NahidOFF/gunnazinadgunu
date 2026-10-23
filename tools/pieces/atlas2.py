#!/usr/bin/env python3
import cv2, numpy as np
SPEC = [
 ("01 rolik/qnom fiquru",  "II · XI  = 11 fev",  "IBP_topbox.png", (60,300,340,1060), 0),
 ("02 sekli GIZLI",        "VII · I  = 1 iyul",  "IBP_topbox.png", (330,240,700,1050), 0),
 ("03 ox + sutun diaqram", "VIII · IX = 9 avq",  "IBP_topbox.png", (790,130,1270,760), 0),
 ("04 BANT (ilme+quyruq)", "V · VII  = 7 may",   "IBP_topbox.png", (150,1150,520,1650), 0),
 ("05 SAQULI duzbucaq",    "VI · VIII = 8 iyun", "IBP_topbox.png", (520,1080,1110,1660), 0),
 ("06 pencere (2 goz)",    "reqemler gizli",     "IBP_topbox.png", (520,260,800,1060), 0),
 ("07 spiral teqvim",      "III · IV = 4 mart",  "sr765/V_mid.png",(230,330,700,1120), 0),
 ("08 iki obyekt",         "VII · VI = 6 iyul",  "IBP_two.png",    (330,60,950,650), 0),
 ("09 ABS bayragi + ANBAR","VII · IV = 4 IYUL",  "IBP_usflag.png", (100,180,800,470), 0),
 ("10 Oman bayragi",       "VI · V   = 5 iyun",  "PSR_oman.png",   (250,40,980,540), 0),
 ("11 Afrika + yasil bitki","IV · VIII = 8 apr", "PSR_afr.png",    (0,0,1000,580), 0),
 ("12 qar buludu",         "IX · V   = 5 sen",   "PSR_snow.png",   (150,120,1050,900), 0),
 ("13 sevinc goz yasi",    "X · XIV  = 14 okt",  "PSR_joy.png",    (230,60,720,540), 0),
 ("14 DAS + QARTAL",       "reqemler gizli",     "PSR_eagle.png",  (60,20,900,470), 0),
 ("15 tund siluet",        "reqemler oxunmayib", "sr15/X15.png",   (200,150,900,850), 0),
]
tiles=[]
for name, nums, path, (x0,y0,x1,y1), rot in SPEC:
    im = cv2.imread(path)
    if im is None: print('MISSING',path); continue
    h,w=im.shape[:2]
    x0,x1=max(0,min(x0,w-2)),max(2,min(x1,w)); y0,y1=max(0,min(y0,h-2)),max(2,min(y1,h))
    c=im[y0:y1,x0:x1]
    if c.size==0: print('EMPTY',name); continue
    a=c.astype(np.float32)
    flat=a.reshape(-1,3); pap=flat[np.argsort(flat.sum(1))[-max(20,int(.12*len(flat))):]].mean(0)
    a=np.clip(a*(np.array([238.,238.,238.])/np.maximum(pap,1)),0,255)
    lo,hi=np.percentile(a,2),np.percentile(a,99)
    c=np.clip((a-lo)*255/max(hi-lo,1),0,255).astype(np.uint8)
    s=450/max(c.shape[0],c.shape[1])
    c=cv2.resize(c,(max(1,int(c.shape[1]*s)),max(1,int(c.shape[0]*s))),interpolation=cv2.INTER_LANCZOS4)
    pad=np.full((500,490,3),255,np.uint8)
    yo=(450-c.shape[0])//2+44; xo=(490-c.shape[1])//2
    pad[yo:yo+c.shape[0],xo:xo+c.shape[1]]=c
    cv2.putText(pad,name[:30],(6,20),0,0.55,(0,0,180),1,cv2.LINE_AA)
    cv2.putText(pad,nums,(6,38),0,0.52,(140,0,0),1,cv2.LINE_AA)
    cv2.rectangle(pad,(0,0),(489,499),(190,190,190),1)
    tiles.append(pad)
rows=[np.hstack(tiles[i:i+5]) for i in range(0,len(tiles),5)]
wmax=max(r.shape[1] for r in rows)
rows=[np.pad(r,((0,0),(0,wmax-r.shape[1]),(0,0)),constant_values=255) for r in rows]
out=np.vstack(rows)
hdr=np.full((54,out.shape[1],3),255,np.uint8)
cv2.putText(hdr,"15 PARCA - IBP super-rezolyusiya  |  reqemler:  QIRMIZI = ay,  MAVI = gun (aparici ferziyye)",(10,36),0,0.85,(0,0,0),2,cv2.LINE_AA)
cv2.imwrite('PIECE_PICTURES2.png',np.vstack([hdr,out])); print('wrote',out.shape,len(tiles))
