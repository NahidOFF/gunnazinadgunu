#!/usr/bin/env python3
"""emocmp.py -- put one extracted picture beside candidate emoji, rendered at the
same tile size, for the eye to compare. Deliberately NOT an automatic matcher:
seven of those have already failed their controls in this hunt."""
import sys,cv2,numpy as np
from PIL import Image,ImageDraw,ImageFont
F=ImageFont.truetype('/usr/share/fonts/truetype/noto/NotoColorEmoji.ttf',109)
def emo(ch,size=200):
    im=Image.new('RGBA',(140,140),(255,255,255,255))
    ImageDraw.Draw(im).text((6,6),ch,font=F,embedded_color=True)
    a=cv2.cvtColor(np.array(im),cv2.COLOR_RGBA2BGR)
    return cv2.resize(a,(size,size),interpolation=cv2.INTER_AREA)
def shot(frame,box,size=200):
    im=cv2.imread(frame); x0,y0,x1,y1=box
    c=cv2.resize(im[y0:y1,x0:x1],None,fx=14,fy=14,interpolation=cv2.INTER_LANCZOS4).astype(np.float32)
    g=c.reshape(-1,3); L=g.mean(1); ref=g[L>=np.percentile(L,84)].mean(0)
    c=np.clip(c*(ref.mean()/ref),0,255).astype(np.uint8)
    h,w=c.shape[:2]; s=size/max(h,w)
    c=cv2.resize(c,(int(w*s),int(h*s)),interpolation=cv2.INTER_AREA)
    o=np.full((size,size,3),255,np.uint8)
    o[(size-c.shape[0])//2:(size-c.shape[0])//2+c.shape[0],(size-c.shape[1])//2:(size-c.shape[1])//2+c.shape[1]]=c
    return o
ROWS=[('figure',('REF803.png',(1644,396,1670,455)),'🧝🧙🎅🤶🕴🛼⛷🧑‍🌾🪆'),
      ('rectangle',('REF803.png',(1696,481,1726,535)),'📕📗🚪🧱🍫🧧🎴🛏🚌'),
      ('two objects',('REF803.png',(1688,712,1714,764)),'🕯🖊✏🥢🎿🔋📚🧻🚀'),
      ('ovoid',('REF803.png',(1506,826,1534,864)),'🪨🥔🥚🏈🥥🍞🌰🥜🫒'),
      ('silhouette',('REF803.png',(1698,930,1728,980)),'🥾👢🌶🪶🍃🦴🍆🌰🍐'),
      ('green plant',('REF803.png',(1718,944,1750,984)),'🌿🌱🍀🌾🎋🪴🌵🍁🥬')]
out=[]
for lab,(fr,bx),chars in ROWS:
    tiles=[shot(fr,bx)]
    for ch in chars: tiles.append(emo(ch))
    row=np.hstack(tiles)
    band=np.full((34,row.shape[1],3),250,np.uint8)
    cv2.putText(band,f'{lab}   <- photo | candidates ->',(6,25),cv2.FONT_HERSHEY_SIMPLEX,0.72,(0,0,180),2,cv2.LINE_AA)
    out.append(np.vstack([band,row]))
W=max(o.shape[1] for o in out)
out=[np.hstack([o,np.full((o.shape[0],W-o.shape[1],3),250,np.uint8)]) for o in out]
cv2.imwrite('EMOCMP.png',np.vstack(out)); print('wrote EMOCMP.png')
