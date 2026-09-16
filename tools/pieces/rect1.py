#!/usr/bin/env python3
"""rect1.py FRAME 'x,y;x,y;x,y;x,y' W H OUT.png -- warp one quad to a frontal
rectangle with Lanczos and white-balance it on its own paper.  Single frame on
purpose: for these cards raw Lanczos has beaten the multi-frame SR pipeline
every time it was compared."""
import sys,cv2,numpy as np
fn=sys.argv[1]
q=np.float32([[float(v) for v in p.split(',')] for p in sys.argv[2].split(';')])
W,H=int(sys.argv[3]),int(sys.argv[4]); OUT=sys.argv[5]
im=cv2.imread(fn).astype(np.float32)
M=cv2.getPerspectiveTransform(q,np.float32([[0,0],[W,0],[W,H],[0,H]]))
c=cv2.warpPerspective(im,M,(W,H),flags=cv2.INTER_LANCZOS4)
g=c.reshape(-1,3); L=g.mean(1); ref=g[L>=np.percentile(L,88)].mean(0)
b=np.clip(c*(ref.mean()/ref),0,255)
lab=cv2.cvtColor(b.astype(np.uint8),cv2.COLOR_BGR2LAB).astype(np.float32)
lab[:,:,0]=np.clip((lab[:,:,0]-np.percentile(lab[:,:,0],2))*
                   (255/max(1,np.percentile(lab[:,:,0],98)-np.percentile(lab[:,:,0],2))),0,255)
lab[:,:,1]=np.clip((lab[:,:,1]-128)*2.2+128,0,255); lab[:,:,2]=np.clip((lab[:,:,2]-128)*2.2+128,0,255)
s=cv2.cvtColor(lab.astype(np.uint8),cv2.COLOR_LAB2BGR)
cv2.imwrite(OUT,np.hstack([b.astype(np.uint8),s])); print(OUT)
