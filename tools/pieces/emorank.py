#!/usr/bin/env python3
"""emorank.py -- rank candidate emoji against a drawing by COLOUR, and check the
ranking on drawings whose identity is already known. If the control fails the
whole thing is discarded; the point is to find that out, not to get an answer.

Signature = mean and spread of a*,b* over the non-background pixels, plus the
fraction of pixels that are strongly warm / strongly cool / strongly green.
"""
import cv2,numpy as np
from PIL import Image,ImageDraw,ImageFont
F=ImageFont.truetype('/usr/share/fonts/truetype/noto/NotoColorEmoji.ttf',109)
def sig_from_bgr(bgr, bgmask):
    lab=cv2.cvtColor(bgr,cv2.COLOR_BGR2LAB).astype(np.float32)
    L,a,b=lab[:,:,0],lab[:,:,1]-128,lab[:,:,2]-128
    m=~bgmask
    if m.sum()<30: return None
    A,B=a[m],b[m]
    return np.array([A.mean(),B.mean(),A.std(),B.std(),
                     (A>6).mean()*20,(B<-6).mean()*20,(A<-6).mean()*20])
def emo_sig(ch):
    im=Image.new('RGBA',(140,140),(255,255,255,255))
    ImageDraw.Draw(im).text((6,6),ch,font=F,embedded_color=True)
    bgr=cv2.cvtColor(np.array(im),cv2.COLOR_RGBA2BGR)
    g=cv2.cvtColor(bgr,cv2.COLOR_BGR2GRAY)
    return sig_from_bgr(bgr,g>245)
def shot_sig(frame,box):
    im=cv2.imread(frame); x0,y0,x1,y1=box
    c=im[y0:y1,x0:x1].astype(np.float32)
    g=c.reshape(-1,3); L=g.mean(1); ref=g[L>=np.percentile(L,84)].mean(0)
    c=np.clip(c*(ref.mean()/ref),0,255).astype(np.uint8)
    gray=cv2.cvtColor(c,cv2.COLOR_BGR2GRAY)
    return sig_from_bgr(c,gray>np.percentile(gray,72))     # paper = brightest 28%
CAND='🌨🌧☁❄😂😭😅🥲🦋🎀🇴🇲🇺🇸🏚🏫🛖🚪📕🧱🧧🪟🗄🖼🪞🪨🥔🥚🏈🥥🌰🌿🌱🍀🌾🧝🧙🎅🛼📊📈📉⬇🕯🖊✏🚀🌡'
TESTS=[('snow cloud  [known 🌨]','REF803.png',(1810,492,1866,548),'🌨'),
       ('joy face    [known 😂]','REF803.png',(1532,790,1564,822),'😂'),
       ('butterfly   [known 🦋]','REF803.png',(1653,486,1684,516),'🦋'),
       ('barn        [known: none]','REF803.png',(1843,658,1888,708),None)]
E={ch:emo_sig(ch) for ch in CAND}
ok=0
for lab,fr,box,truth in TESTS:
    s=shot_sig(fr,box)
    d=sorted(((float(np.linalg.norm(s-E[ch])),ch) for ch in CAND if E[ch] is not None))
    top=[c for _,c in d[:5]]
    hit=(truth in top[:3]) if truth else None
    if hit: ok+=1
    print(f'{lab:26s} top5: {" ".join(top)}   ' + ('' if truth is None else ('HIT' if hit else 'MISS')))
print(f'\ncontrol: {ok}/3 known drawings placed their true emoji in the top 3')
