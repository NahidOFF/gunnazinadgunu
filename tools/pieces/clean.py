#!/usr/bin/env python3
"""clean.py IN.png OUT.png [chroma_k] -- white-balance on the card's own paper,
stretch L, amplify chroma. Writes [raw | balanced | chroma-boosted]."""
import sys,cv2,numpy as np
im=cv2.imread(sys.argv[1]).astype(np.float32); OUT=sys.argv[2]
K=float(sys.argv[3]) if len(sys.argv)>3 else 2.6
g=im.reshape(-1,3); L=g.mean(1); ref=g[L>=np.percentile(L,88)].mean(0)
w=np.clip(im*(ref.mean()/ref),0,255)
lab=cv2.cvtColor(w.astype(np.uint8),cv2.COLOR_BGR2LAB).astype(np.float32)
Lc=lab[:,:,0]; lo,hi=np.percentile(Lc,2),np.percentile(Lc,98)
Ls=np.clip((Lc-lo)*255/max(hi-lo,1),0,255)
bal=cv2.cvtColor(cv2.merge([Ls,lab[:,:,1],lab[:,:,2]]).astype(np.uint8),cv2.COLOR_LAB2BGR)
lab2=lab.copy(); lab2[:,:,0]=Ls
lab2[:,:,1]=np.clip((lab2[:,:,1]-128)*K+128,0,255)
lab2[:,:,2]=np.clip((lab2[:,:,2]-128)*K+128,0,255)
ch=cv2.cvtColor(lab2.astype(np.uint8),cv2.COLOR_LAB2BGR)
out=np.hstack([np.clip(im,0,255).astype(np.uint8),bal,ch])
h=out.shape[0]
if h<900: out=cv2.resize(out,None,fx=900/h,fy=900/h,interpolation=cv2.INTER_CUBIC)
cv2.imwrite(OUT,out); print(OUT,out.shape)
