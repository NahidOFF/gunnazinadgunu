#!/usr/bin/env python3
import cv2, numpy as np
SPEC = [
 ("01 rolik/qnom fiquru",      "qirmizi II  · mavi XI",   "PSR_topbox.png", (60,300,340,1060)),
 ("02 sekli gizli",            "qirmizi VII · mavi I",    "PSR_topbox.png", (330,240,700,1050)),
 ("03 asagi ox + sutun diaqram","qirmizi VIII· mavi IX",  "PSR_topbox.png", (790,130,1270,760)),
 ("04 bant / ilme",            "qirmizi V   · mavi VII",  "PSR_topbox.png", (150,1150,520,1650)),
 ("05 terrakota duzbucaq",     "qirmizi VI  · mavi VIII", "PSR_topbox.png", (520,1080,1110,1660)),
 ("06 pencere / qapi",         "rəqəmlər gizli",          "PSR_topbox.png", (520,260,800,1060)),
 ("07 spiral tequim '25'",     "qirmizi III · mavi IV",   "sr765/V_mid.png",(230,330,700,1120)),
 ("08 iki hundur obyekt",      "qirmizi VII · mavi VI",   "PSR_two.png",    (330,60,950,650)),
 ("09 ABS bayragi + anbar",    "qirmizi VII · mavi IV",   "PSR_usflag.png", (100,180,800,470)),
 ("10 Oman bayragi",           "qirmizi VI  · mavi V",    "PSR_oman.png",   (250,40,980,540)),
 ("11 Afrika + yasil bitki",   "qirmizi IV  · mavi VIII", "sr803/R8_bottom.png",(1250,780,2010,1500)),
 ("12 qar buludu",             "qirmizi IX  · mavi V",    "sr803/R3_snow.png",(300,200,1300,1100)),
 ("13 sevinc goz yasi 😂",      "qirmizi X   · mavi XIV",  "PSR_joy.png",    (230,60,720,540)),
 ("14 DAS + QARTAL",           "rəqəmlər qismən gizli",   "PSR_eagle.png",  (60,20,900,470)),
 ("15 tund silue (en asagi)",  "rəqəmlər oxunmayib",      "sr15/X15.png",   (200,150,900,850)),
]
tiles=[]
for name, nums, path, (x0,y0,x1,y1) in SPEC:
    im = cv2.imread(path)
    if im is None: print('MISSING', path); continue
    h,w = im.shape[:2]
    x0,x1 = max(0,min(x0,w-2)), max(2,min(x1,w)); y0,y1 = max(0,min(y0,h-2)), max(2,min(y1,h))
    c = im[y0:y1, x0:x1]
    if c.size == 0: print('EMPTY', name); continue
    a = c.astype(np.float32)
    # white-balance on the paper, then stretch
    flat = a.reshape(-1,3); pap = flat[np.argsort(flat.sum(1))[-max(20,int(.12*len(flat))):]].mean(0)
    a = np.clip(a*(np.array([238.,238.,238.])/np.maximum(pap,1)),0,255)
    lo,hi = np.percentile(a,2), np.percentile(a,99)
    c = np.clip((a-lo)*255/max(hi-lo,1),0,255).astype(np.uint8)
    s = 430/max(c.shape[0], c.shape[1])
    c = cv2.resize(c,(max(1,int(c.shape[1]*s)), max(1,int(c.shape[0]*s))), interpolation=cv2.INTER_LANCZOS4)
    pad = np.full((470,470,3),255,np.uint8)
    yo=(430-c.shape[0])//2+36; xo=(470-c.shape[1])//2
    pad[yo:yo+c.shape[0], xo:xo+c.shape[1]] = c
    cv2.putText(pad, name[:30], (6,18), 0, 0.52, (0,0,180), 1, cv2.LINE_AA)
    cv2.putText(pad, nums,      (6,33), 0, 0.45, (120,0,0), 1, cv2.LINE_AA)
    cv2.rectangle(pad,(0,0),(469,469),(190,190,190),1)
    tiles.append(pad)
rows=[np.hstack(tiles[i:i+5]) for i in range(0,len(tiles),5)]
wmax=max(r.shape[1] for r in rows)
rows=[np.pad(r,((0,0),(0,wmax-r.shape[1]),(0,0)),constant_values=255) for r in rows]
out=np.vstack(rows)
cv2.imwrite('PIECE_PICTURES.png', out); print('wrote', out.shape, len(tiles),'tiles')
