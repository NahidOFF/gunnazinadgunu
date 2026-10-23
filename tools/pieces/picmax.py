#!/usr/bin/env python3
"""picmax.py -- the unnamed drawings at the largest useful size, three ways each:
white-balanced on the card's own paper, then contrast-stretched, then chroma
boosted.  No rectification: the quads I can draw for these cards are eyeballed,
and forcing an eyeballed quad to a chosen canvas distorts the shape -- which is
exactly how two earlier measurements went wrong."""
import cv2,numpy as np
P=[("1  -- 11 Feb   figure",        'REF803.png',(1644,396,1674,456)),
   ("3  -- 8 Apr    dark shape + plant",'REF803.png',(1698,922,1748,976)),
   ("6  -- 6 Jun    two objects",   'REF803.png',(1678,708,1720,772)),
   ("7  -- 8 Jun    plain rectangle",'REF803.png',(1694,480,1738,536)),
   ("13 -- ?        frame, one divider",'REF803.png',(1676,392,1718,460)),
   ("14 -- ?        curved form + bird",'REF803.png',(1510,828,1570,890)),
   ("3  -- 8 Apr    (second angle)", 'REF765.png',(1246,528,1320,632))]
ROWH=430
rows=[]
for tag,fn,(x0,y0,x1,y1) in P:
    im=cv2.imread(fn)
    if im is None: print('missing',fn); continue
    Z=max(6,int(ROWH/max(1,(y1-y0))))
    c=cv2.resize(im[y0:y1,x0:x1].astype(np.float32),None,fx=Z,fy=Z,interpolation=cv2.INTER_LANCZOS4)
    g=c.reshape(-1,3); L=g.mean(1); ref=g[L>=np.percentile(L,88)].mean(0)
    b=np.clip(c*(ref.mean()/ref),0,255).astype(np.uint8)
    lab=cv2.cvtColor(b,cv2.COLOR_BGR2LAB).astype(np.float32)
    lo,hi=np.percentile(lab[:,:,0],2),np.percentile(lab[:,:,0],98)
    s=lab.copy(); s[:,:,0]=np.clip((s[:,:,0]-lo)*(255/max(1,hi-lo)),0,255)
    st=cv2.cvtColor(s.astype(np.uint8),cv2.COLOR_LAB2BGR)
    k=s.copy(); k[:,:,1]=np.clip((k[:,:,1]-128)*2.4+128,0,255); k[:,:,2]=np.clip((k[:,:,2]-128)*2.4+128,0,255)
    ch=cv2.cvtColor(k.astype(np.uint8),cv2.COLOR_LAB2BGR)
    trio=np.hstack([b,np.full((b.shape[0],10,3),250,np.uint8),st,
                    np.full((b.shape[0],10,3),250,np.uint8),ch])
    hdr=np.full((40,trio.shape[1],3),250,np.uint8)
    cv2.putText(hdr,f'{tag}    [balanced | contrast | chroma]   {x1-x0}x{y1-y0}px at {Z}x',
                (8,27),cv2.FONT_HERSHEY_SIMPLEX,0.66,(20,20,20),2,cv2.LINE_AA)
    rows.append(np.vstack([hdr,trio,np.full((14,trio.shape[1],3),250,np.uint8)]))
W=max(r.shape[1] for r in rows)
rows=[np.hstack([r,np.full((r.shape[0],W-r.shape[1],3),250,np.uint8)]) for r in rows]
cv2.imwrite('PICMAX.png',np.vstack(rows)); print('ok',sum(r.shape[0] for r in rows),W)
