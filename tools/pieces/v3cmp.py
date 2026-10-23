#!/usr/bin/env python3
"""v3cmp.py -- each unresolved drawing beside the SAME candidate drawn by three
vendors (Noto, Twemoji, OpenMoji), plus one control row whose answer is known.

Comparing against one vendor is what produced the wrong 'these are not standard
emoji' conclusion.  OpenMoji matters here because its flat, outlined style is
the closest of the three to a pen drawing, and several of these drawings are
uncoloured outlines rather than filled shapes."""
import cv2,numpy as np
from PIL import Image,ImageFont,ImageDraw
FONT='/usr/share/fonts/truetype/noto/NotoColorEmoji.ttf'
def noto(ch,T):
    f=ImageFont.truetype(FONT,109)
    im=Image.new('RGBA',(160,160),(252,252,252,255))
    ImageDraw.Draw(im).text((80,80),ch,font=f,anchor='mm',embedded_color=True)
    a=cv2.cvtColor(np.array(im),cv2.COLOR_RGBA2BGR)
    return a
def load(p):
    e=cv2.imread(p,cv2.IMREAD_UNCHANGED)
    if e is None: return None
    if e.shape[2]==4:
        a=e[:,:,3:4].astype(np.float32)/255
        e=(e[:,:,:3]*a+252*(1-a)).astype(np.uint8)
    return e
ROWS=[("CONTROL 4  butterfly (answer known: 4 lobes = 4 wings)",
       'REF803.png',(1652,484,1690,516),'🦋','1f98b','1F98B'),
      ("13  frame + one divider, grey ink",'REF803.png',(1676,392,1718,460),'🗄','1f5c4','1F5C4'),
      ("13  same drawing vs WINDOW",'REF803.png',(1676,392,1718,460),'🪟','1fa9f','1FA9F'),
      ("7   plain terracotta rectangle 1:2.14",'REF803.png',(1696,482,1736,534),'🚪','1f6aa','1F6AA'),
      ("7   same drawing vs CLOSED BOOK",'REF803.png',(1696,482,1736,534),'📕','1f4d5','1F4D5'),
      ("14L smooth lump, gold facet",'REF803.png',(1515,823,1539,871),'🪨','1faa8','1FAA8'),
      ("3   dark silhouette vs MICROPHONE",'REF803.png',(1698,922,1734,978),'🎤','1f3a4','1F3A4'),
      ("15  notched wedge vs TOOTH",'REF_OFFICE.png',(1662,848,1688,880),'🦷','1f9b7','1F9B7'),
      ("1   figure, green hat, two dark discs",'REF803.png',(1648,399,1663,452),'🛼','1f6fc','1F6FC'),
     ]
T=185
def tile(im):
    h,w=im.shape[:2]; s=min(T/w,T/h)*0.94
    r=cv2.resize(im,(max(1,int(w*s)),max(1,int(h*s))),interpolation=cv2.INTER_AREA)
    t=np.full((T,T,3),252,np.uint8)
    t[(T-r.shape[0])//2:(T-r.shape[0])//2+r.shape[0],(T-r.shape[1])//2:(T-r.shape[1])//2+r.shape[1]]=r
    return t
rows=[]
for tag,fn,(x0,y0,x1,y1),ch,tw,omj in ROWS:
    im=cv2.imread(fn).astype(np.float32)
    c=cv2.resize(im[y0:y1,x0:x1],None,fx=14,fy=14,interpolation=cv2.INTER_LANCZOS4)
    g=c.reshape(-1,3); L=g.mean(1); ref=g[L>=np.percentile(L,88)].mean(0)
    c=np.clip(c*(ref.mean()/ref),0,255).astype(np.uint8)
    cells=[tile(c),tile(noto(ch,T))]
    for p in (f'emo/{tw}.png',f'om/{omj}.png'):
        e=load(p); cells.append(tile(e) if e is not None else np.full((T,T,3),252,np.uint8))
    band=np.hstack(cells)
    lbl=np.full((24,band.shape[1],3),252,np.uint8)
    for i,n in enumerate(['THE DRAWING','Noto','Twemoji','OpenMoji']):
        cv2.putText(lbl,n,(T*i+6,17),cv2.FONT_HERSHEY_SIMPLEX,0.44,
                    (150,20,20) if i==0 else (40,40,40),1,cv2.LINE_AA)
    hdr=np.full((28,band.shape[1],3),252,np.uint8)
    cv2.putText(hdr,tag,(6,20),cv2.FONT_HERSHEY_SIMPLEX,0.58,(20,20,20),2,cv2.LINE_AA)
    rows.append(np.vstack([hdr,band,lbl,np.full((10,band.shape[1],3),235,np.uint8)]))
cv2.imwrite('V3CMP.png',np.vstack(rows)); print('ok')
