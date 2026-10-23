#!/usr/bin/env python3
import sys, cv2, numpy as np, json
im=cv2.imread(sys.argv[1]); x0,y0,x1,y1=[int(v) for v in sys.argv[2].split(',')]
amin=int(sys.argv[3]) if len(sys.argv)>3 else 500
sub=im[y0:y1,x0:x1]
lab=cv2.cvtColor(sub,cv2.COLOR_BGR2LAB); L=lab[:,:,0].astype(np.int16); B=lab[:,:,2].astype(np.int16)-128
m=((B<16)&(L>135)).astype(np.uint8)
m=cv2.morphologyEx(m,cv2.MORPH_CLOSE,np.ones((3,3),np.uint8))
n,lb,st,ce=cv2.connectedComponentsWithStats(m,8)
out=[]
for k in range(1,n):
    x,y,w,h,a=st[k]
    if a<amin or a>20000: continue
    cnt,_=cv2.findContours((lb==k).astype(np.uint8),cv2.RETR_EXTERNAL,cv2.CHAIN_APPROX_SIMPLE)
    r=cv2.minAreaRect(max(cnt,key=cv2.contourArea)); box=cv2.boxPoints(r)+np.float32([x0,y0])
    s=box.sum(1); d=np.diff(box,axis=1).ravel()
    quad=[box[np.argmin(s)],box[np.argmin(d)],box[np.argmax(s)],box[np.argmax(d)]]
    out.append({'area':int(a),'cx':round(float(ce[k][0]+x0),1),'cy':round(float(ce[k][1]+y0),1),
                'wh':[round(float(v),1) for v in r[1]],
                'quad':[[round(float(p[0]),1),round(float(p[1]),1)] for p in quad]})
out.sort(key=lambda r:(-r['area']))
for o in out: print(json.dumps(o))
