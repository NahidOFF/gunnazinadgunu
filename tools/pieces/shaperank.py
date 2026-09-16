#!/usr/bin/env python3
"""shaperank.py -- rank candidate emoji against a measured drawing by SHAPE
(elongation, solidity, and the width-by-depth profile), with a control first.
"""
import cv2,numpy as np
from PIL import Image,ImageDraw,ImageFont
F=ImageFont.truetype('/usr/share/fonts/truetype/noto/NotoColorEmoji.ttf',109)
def desc_from_mask(m):
    n,lb,st,_=cv2.connectedComponentsWithStats(m,8)
    if n<2: return None
    k=int(np.argmax(st[1:,4])+1); s=(lb==k).astype(np.uint8)
    cs,_=cv2.findContours(s,cv2.RETR_EXTERNAL,cv2.CHAIN_APPROX_NONE)
    ct=max(cs,key=cv2.contourArea)
    if cv2.contourArea(ct)<80: return None
    (cx,cy),(rw,rh),ang=cv2.minAreaRect(ct); A,B=max(rw,rh),min(rw,rh)
    sol=cv2.contourArea(ct)/max(cv2.contourArea(cv2.convexHull(ct)),1)
    rot=ang if rw<rh else ang+90
    M=cv2.getRotationMatrix2D((cx,cy),rot,1.0)
    r=cv2.warpAffine(s,M,(s.shape[1],s.shape[0]),flags=cv2.INTER_NEAREST)
    ys,_=np.where(r>0)
    if len(ys)<20: return None
    a,b=ys.min(),ys.max()
    prof=[]
    for f in range(10,100,10):
        y=int(a+(b-a)*f/100); row=np.where(r[y]>0)[0]
        prof.append((row.max()-row.min()+1)/(b-a) if len(row) else 0.0)
    return np.array([A/B/3.0, sol] + prof)      # elongation scaled to ~profile range
def emo_desc(ch):
    im=Image.new('RGBA',(200,200),(255,255,255,255))
    ImageDraw.Draw(im).text((10,10),ch,font=F,embedded_color=True)
    g=cv2.cvtColor(np.array(im),cv2.COLOR_RGBA2GRAY)
    return desc_from_mask((g<235).astype(np.uint8))
def shot_desc(fn,box,Z,pct):
    im=cv2.imread(fn); x0,y0,x1,y1=box
    c=cv2.resize(im[y0:y1,x0:x1],None,fx=Z,fy=Z,interpolation=cv2.INTER_LANCZOS4)
    g=c.reshape(-1,3).astype(np.float32); L=g.mean(1); ref=g[L>=np.percentile(L,84)].mean(0)
    c=np.clip(c.astype(np.float32)*(ref.mean()/ref),0,255).astype(np.uint8)
    gr=cv2.cvtColor(c,cv2.COLOR_BGR2GRAY)
    m=(gr<np.percentile(gr,pct)).astype(np.uint8)
    m=cv2.morphologyEx(m,cv2.MORPH_OPEN,np.ones((Z//2|1,Z//2|1),np.uint8))
    return desc_from_mask(m)
CAND=('🥜🎳👢🥾🍐🌰🍑🥒🌶🍆🥑🦴🕊🐦🐧🦅🪶🎸🎻🍾🏺♟🌵🍌🥕🫑🥔🥚🧦🕯🖊✏🔥🍃🪵🦈')
E={ch:emo_desc(ch) for ch in CAND}
E={k:v for k,v in E.items() if v is not None}
def rank(d,n=6):
    return sorted(((float(np.linalg.norm(d-E[c])),c) for c in E))[:n]
print('CONTROL — the eagle-card bird (known: a bird)')
d=shot_desc('REF803.png',(1535,845,1557,884),30,26)
r=rank(d); print('   ',' '.join(f'{c}({s:.2f})' for s,c in r))
birds={'🕊','🐦','🐧','🦅'}
hit=any(c in birds for _,c in r[:3])
print(f'    a bird in the top 3? {"YES -> method usable" if hit else "NO -> method NOT usable"}')
print()
if hit:
    for lab,box,Z,pct in [('#3 silhouette',(1700,930,1730,984),30,20),
                          ('#15 wedge',(1672,852,1690,880),44,26),
                          ('#14 left form',(1517,827,1537,868),34,26),
                          ('#6 dark object',(1784,644,1800,730),30,26)]:
        fn='REF_OFFICE.png' if '15' in lab else ('REF806.png' if '#6' in lab else 'REF803.png')
        dd=shot_desc(fn,box,Z,pct)
        if dd is None: print(f'{lab}: no shape'); continue
        print(f'{lab:18s} ' + ' '.join(f'{c}({s:.2f})' for s,c in rank(dd)))
