#!/usr/bin/env python3
"""Separate overlapping cards: erode the white mask, label, then dilate each
label back so touching cards come apart."""
import sys,cv2,numpy as np,json
im=cv2.imread(sys.argv[1]); x0,y0,x1,y1=[int(v) for v in sys.argv[2].split(',')]
amin=int(sys.argv[3]) if len(sys.argv)>3 else 250
ER=int(sys.argv[4]) if len(sys.argv)>4 else 3
sub=im[y0:y1,x0:x1]
lab=cv2.cvtColor(sub,cv2.COLOR_BGR2LAB)
L=lab[:,:,0].astype(np.int16); B=lab[:,:,2].astype(np.int16)-128
m=((B<16)&(L>135)).astype(np.uint8)
m=cv2.morphologyEx(m,cv2.MORPH_CLOSE,np.ones((3,3),np.uint8))
er=cv2.erode(m,np.ones((ER,ER),np.uint8))
n,lb,st,ce=cv2.connectedComponentsWithStats(er,8)
out=[]
for k in range(1,n):
    if st[k,4]<amin: continue
    s=cv2.dilate((lb==k).astype(np.uint8),np.ones((ER,ER),np.uint8))&m
    cnt,_=cv2.findContours(s,cv2.RETR_EXTERNAL,cv2.CHAIN_APPROX_SIMPLE)
    if not cnt: continue
    c=max(cnt,key=cv2.contourArea)
    r=cv2.minAreaRect(c); box=cv2.boxPoints(r)+np.float32([x0,y0])
    ss=box.sum(1); dd=np.diff(box,axis=1).ravel()
    quad=[box[np.argmin(ss)],box[np.argmin(dd)],box[np.argmax(ss)],box[np.argmax(dd)]]
    out.append({'area':int(cv2.contourArea(c)),'cx':round(float(ce[k][0]+x0),1),'cy':round(float(ce[k][1]+y0),1),
                'wh':[round(float(v),1) for v in r[1]],
                'quad':[[round(float(p[0]),1),round(float(p[1]),1)] for p in quad]})
out.sort(key=lambda r:(r['cy'],r['cx']))
for o in out: print(json.dumps(o))
