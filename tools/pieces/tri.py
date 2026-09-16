#!/usr/bin/env python3
"""Each unnamed drawing from every angle that shows it, side by side."""
import cv2,numpy as np,os
def crop(fn,box,H=340):
    if not os.path.exists(fn): return None
    im=cv2.imread(fn); x0,y0,x1,y1=box
    c=im[y0:y1,x0:x1].astype(np.float32)
    if c.size==0: return None
    g=c.reshape(-1,3); L=g.mean(1); ref=g[L>=np.percentile(L,84)].mean(0)
    c=np.clip(c*(ref.mean()/ref),0,255)
    lb=cv2.cvtColor(c.astype(np.uint8),cv2.COLOR_BGR2LAB).astype(np.float32)
    Lc=lb[:,:,0]; lo,hi=np.percentile(Lc,2),np.percentile(Lc,98)
    lb[:,:,0]=np.clip((Lc-lo)*255/max(hi-lo,1),0,255)
    lb[:,:,1]=np.clip((lb[:,:,1]-128)*1.6+128,0,255); lb[:,:,2]=np.clip((lb[:,:,2]-128)*1.6+128,0,255)
    t=cv2.cvtColor(lb.astype(np.uint8),cv2.COLOR_LAB2BGR)
    s=H/t.shape[0]
    return cv2.resize(t,(max(1,int(t.shape[1]*s)),H),interpolation=cv2.INTER_LANCZOS4)
ROWS=[('1  figure (green hat, red lower, 2 discs)',
       [('h803','REF803.png',(1642,394,1672,458)),('hn765','REF767.png',(1248,56,1284,112))]),
      ('3  black silhouette 32x11 + green plant',
       [('h803','REF803.png',(1694,926,1752,986)),('hn765','REF765.png',(1244,556,1302,624))]),
      ('6  navy object + red-tipped object',
       [('h803','REF803.png',(1686,710,1716,766)),('h806','REF806.png',(1782,640,1822,732)),
        ('hn765','REF767.png',(1271,401,1319,469))]),
      ('7  flat terracotta rectangle 1:2.14',
       [('h803','REF803.png',(1694,479,1728,537)),('hn765','REF767.png',(1294,154,1354,216))]),
      ('13 grey frame, 2 panels (file cabinet?)',
       [('h803','REF803.png',(1679,394,1711,457)),('hn765','REF767.png',(1291,58,1329,109))]),
      ('14 warm brown ovoid + bald eagle',
       [('h803','REF803.png',(1504,824,1560,890)),('office','REF_OFFICE.png',(1690,744,1724,790))]),
      ('15 two peaks, tapers (19x8 px)',
       [('office','REF_OFFICE.png',(1668,848,1692,884))])]
out=[]
for lab,views in ROWS:
    tiles=[]
    for tag,fn,box in views:
        t=crop(fn,box)
        if t is None: continue
        cv2.putText(t,tag,(6,26),cv2.FONT_HERSHEY_SIMPLEX,0.7,(0,0,220),2,cv2.LINE_AA)
        tiles.append(t); tiles.append(np.full((t.shape[0],18,3),252,np.uint8))
    if not tiles: continue
    row=np.hstack(tiles)
    band=np.full((34,row.shape[1],3),252,np.uint8)
    cv2.putText(band,lab,(6,25),cv2.FONT_HERSHEY_SIMPLEX,0.72,(15,15,15),2,cv2.LINE_AA)
    out.append(np.vstack([band,row]))
W=max(o.shape[1] for o in out)
out=[np.hstack([o,np.full((o.shape[0],W-o.shape[1],3),252,np.uint8)]) for o in out]
cv2.imwrite('TRIANGLES.png',np.vstack(out)); print('ok')
