#!/usr/bin/env python3
"""Trace the white piece outlines in a fused image and draw them, so the tab
shapes on each edge can be catalogued."""
import sys, cv2, numpy as np
im=cv2.imread(sys.argv[1]); out=sys.argv[2]
lab=cv2.cvtColor(im,cv2.COLOR_BGR2LAB)
L=lab[:,:,0].astype(np.int16); B=lab[:,:,2].astype(np.int16)-128
m=((B<14)&(L>128)).astype(np.uint8)
m=cv2.morphologyEx(m,cv2.MORPH_CLOSE,np.ones((7,7),np.uint8))
m=cv2.morphologyEx(m,cv2.MORPH_OPEN,np.ones((5,5),np.uint8))
n,lb,st,ce=cv2.connectedComponentsWithStats(m,8)
vis=im.copy()
for k in range(1,n):
    if st[k,4] < 0.01*m.size: continue
    cnts,_=cv2.findContours((lb==k).astype(np.uint8),cv2.RETR_EXTERNAL,cv2.CHAIN_APPROX_NONE)
    c=max(cnts,key=cv2.contourArea)
    eps=0.004*cv2.arcLength(c,True)
    ap=cv2.approxPolyDP(c,eps,True)
    cv2.drawContours(vis,[c],-1,(0,0,255),2)
    cv2.drawContours(vis,[ap],-1,(0,200,0),2)
    for p in ap.reshape(-1,2):
        cv2.circle(vis,tuple(p),5,(255,0,0),-1)
    print(f'blob {k}: area {st[k,4]}, contour pts {len(c)}, corners {len(ap)}')
cv2.imwrite(out,vis); print('wrote',out)
