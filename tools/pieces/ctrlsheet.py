#!/usr/bin/env python3
"""ctrlsheet.py -- the CONTROL for the Twemoji comparison: the drawings whose
identity is already settled, beside their own glyph and two decoys.

If a known drawing does not visibly favour its own glyph over the decoys, the
comparison carries no information and must be discarded, exactly as the eleven
similarity measures before it were.  Running this before trusting any unnamed
result is the whole point."""
import cv2,numpy as np
ROWS=[("4  BUTTERFLY (known)",'REF803.png',(1652,484,1690,516),
       [('1f98b','butterfly = ITS OWN'),('1f41d','bee'),('1f99a','peacock')]),
      ("12 FACE W/ TEARS OF JOY (known)",'REF803.png',(1530,782,1572,818),
       [('1f602','joy = ITS OWN'),('1f4c5','calendar'),('1faa8','rock')]),
      ("11 CLOUD WITH SNOW (known)",'REF803.png',(1806,494,1868,540),
       [('1f328','cloud+snow = ITS OWN'),('2601','cloud'),('1f326','sun behind rain')]),
      ("9  US FLAG (known)",'REF803.png',(1798,672,1842,700),
       [('us','US flag = ITS OWN'),('om','Oman flag'),('1f3f3','white flag')]),
      ("5  OMAN FLAG (known)",'REF803.png',(1652,900,1700,940),
       [('om','Oman flag = ITS OWN'),('us','US flag'),('1f6a9','triangular flag')]),
      ("14R BALD EAGLE (known)",'REF803.png',(1540,844,1572,888),
       [('1f985','eagle = ITS OWN'),('1f426','bird'),('1f987','bat')]),
     ]
T=170
def tile(im):
    h,w=im.shape[:2]; s=min(T/w,T/h)*0.94
    r=cv2.resize(im,(max(1,int(w*s)),max(1,int(h*s))),interpolation=cv2.INTER_AREA)
    t=np.full((T,T,3),252,np.uint8)
    t[(T-r.shape[0])//2:(T-r.shape[0])//2+r.shape[0],(T-r.shape[1])//2:(T-r.shape[1])//2+r.shape[1]]=r
    return t
rows=[]
for tag,fn,(x0,y0,x1,y1),cands in ROWS:
    im=cv2.imread(fn).astype(np.float32)
    c=cv2.resize(im[y0:y1,x0:x1],None,fx=14,fy=14,interpolation=cv2.INTER_LANCZOS4)
    g=c.reshape(-1,3); L=g.mean(1); ref=g[L>=np.percentile(L,88)].mean(0)
    c=np.clip(c*(ref.mean()/ref),0,255).astype(np.uint8)
    cells=[tile(c)]; labs=['THE DRAWING']
    for k,nm in cands:
        e=cv2.imread(f'emo/{k}.png',cv2.IMREAD_UNCHANGED)
        if e is None: continue
        a=e[:,:,3:4].astype(np.float32)/255
        e=(e[:,:,:3]*a+252*(1-a)).astype(np.uint8)
        cells.append(tile(e)); labs.append(nm)
    band=np.hstack(cells)
    lbl=np.full((26,band.shape[1],3),252,np.uint8)
    for i,n in enumerate(labs):
        cv2.putText(lbl,n,(T*i+6,18),cv2.FONT_HERSHEY_SIMPLEX,0.42,
                    (150,20,20) if i==0 else (40,40,40),1,cv2.LINE_AA)
    hdr=np.full((28,band.shape[1],3),252,np.uint8)
    cv2.putText(hdr,tag,(6,20),cv2.FONT_HERSHEY_SIMPLEX,0.62,(20,20,20),2,cv2.LINE_AA)
    rows.append(np.vstack([hdr,band,lbl,np.full((10,band.shape[1],3),235,np.uint8)]))
W=max(r.shape[1] for r in rows)
rows=[np.hstack([r,np.full((r.shape[0],W-r.shape[1],3),252,np.uint8)]) for r in rows]
cv2.imwrite('CTRL.png',np.vstack(rows)); print('ok')
