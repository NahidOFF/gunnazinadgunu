#!/usr/bin/env python3
"""findquad.py FRAME.png x0,y0,x1,y1 -> min-area rect corners of the largest white piece blob"""
import sys, cv2, numpy as np
im=cv2.imread(sys.argv[1]); x0,y0,x1,y1=[int(v) for v in sys.argv[2].split(',')]
sub=im[y0:y1,x0:x1]
lab=cv2.cvtColor(sub,cv2.COLOR_BGR2LAB); L=lab[:,:,0].astype(np.int16); B=lab[:,:,2].astype(np.int16)-128
m=((B<16)&(L>135)).astype(np.uint8)
m=cv2.morphologyEx(m,cv2.MORPH_CLOSE,np.ones((3,3),np.uint8))
n,lb,st,ce=cv2.connectedComponentsWithStats(m,8)
if n<2: print('none'); sys.exit()
k=1+int(np.argmax(st[1:,4]))
cnt,_=cv2.findContours((lb==k).astype(np.uint8),cv2.RETR_EXTERNAL,cv2.CHAIN_APPROX_SIMPLE)
r=cv2.minAreaRect(cnt[0]); box=cv2.boxPoints(r)+np.float32([x0,y0])
# order: tl,tr,br,bl
s=box.sum(1); d=np.diff(box,axis=1).ravel()
tl=box[np.argmin(s)]; br=box[np.argmax(s)]; tr=box[np.argmin(d)]; bl=box[np.argmax(d)]
print('area',st[k,4],'rect',[round(v,1) for v in r[1]],'ang',round(r[2],1))
print(json.dumps([[round(float(p[0]),1),round(float(p[1]),1)] for p in [tl,tr,br,bl]]) if (json:=__import__('json')) else '')
