#!/usr/bin/env python3
"""zoomgrid.py FRAME x0,y0,x1,y1 ZOOM OUT.png -- white-balanced Lanczos zoom with a
labelled coordinate grid.  Grid first: twice in this hunt I measured the wrong
thing because I placed a window by eye on an ungridded render."""
import sys,cv2,numpy as np
fn=sys.argv[1]; x0,y0,x1,y1=[int(v) for v in sys.argv[2].split(',')]
Z=int(sys.argv[3]); OUT=sys.argv[4]
im=cv2.imread(fn).astype(np.float32)
c=cv2.resize(im[y0:y1,x0:x1],None,fx=Z,fy=Z,interpolation=cv2.INTER_LANCZOS4)
g=c.reshape(-1,3); L=g.mean(1); ref=g[L>=np.percentile(L,85)].mean(0)
c=np.clip(c*(ref.mean()/ref),0,255).astype(np.uint8)
for X in range(x0-x0%10+10,x1,10):
    px=(X-x0)*Z; cv2.line(c,(px,0),(px,c.shape[0]),(0,200,255),1)
    cv2.putText(c,str(X),(px+2,14),cv2.FONT_HERSHEY_SIMPLEX,0.4,(0,90,200),1,cv2.LINE_AA)
for Y in range(y0-y0%10+10,y1,10):
    py=(Y-y0)*Z; cv2.line(c,(0,py),(c.shape[1],py),(0,200,255),1)
    cv2.putText(c,str(Y),(2,py-3),cv2.FONT_HERSHEY_SIMPLEX,0.4,(0,90,200),1,cv2.LINE_AA)
cv2.imwrite(OUT,c); print(OUT,c.shape)
