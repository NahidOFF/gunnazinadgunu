#!/usr/bin/env python3
"""cardline.py FRAME x0,y0,x1,y1 ZOOM OUT.png -- draw the outline of every white
card blob over a zoom of the region, so it can be seen which drawings sit on the
SAME card.

This matters structurally: several cards look like they carry two drawings, but
the pieces overlap heavily, so a 'pair' could just as easily be one drawing each
on two cards.  The card outline is what settles it, and it has to be seen, not
inferred from a bounding box drawn by hand."""
import sys,cv2,numpy as np
fn=sys.argv[1]; x0,y0,x1,y1=[int(v) for v in sys.argv[2].split(',')]
Z=int(sys.argv[3]); OUT=sys.argv[4]
im=cv2.imread(fn)
sub=im[y0:y1,x0:x1]
lab=cv2.cvtColor(sub,cv2.COLOR_BGR2LAB)
L=lab[:,:,0].astype(np.int16); B=lab[:,:,2].astype(np.int16)-128
m=((B<16)&(L>132)).astype(np.uint8)
m=cv2.morphologyEx(m,cv2.MORPH_CLOSE,np.ones((3,3),np.uint8))
m=cv2.morphologyEx(m,cv2.MORPH_OPEN,np.ones((2,2),np.uint8))
big=cv2.resize(sub.astype(np.float32),None,fx=Z,fy=Z,interpolation=cv2.INTER_LANCZOS4)
g=big.reshape(-1,3); Lm=g.mean(1); ref=g[Lm>=np.percentile(Lm,88)].mean(0)
big=np.clip(big*(ref.mean()/ref),0,255).astype(np.uint8)
cn,_=cv2.findContours(m,cv2.RETR_EXTERNAL,cv2.CHAIN_APPROX_NONE)
cols=[(0,0,230),(230,0,0),(0,170,0),(200,0,200),(0,160,230),(120,60,0),(0,90,90)]
vis=big.copy(); n=0
for c in sorted(cn,key=cv2.contourArea,reverse=True):
    if cv2.contourArea(c)<120: continue
    col=cols[n%len(cols)]
    cv2.drawContours(vis,[c*Z],-1,col,3)
    M=cv2.moments(c)
    if M['m00']:
        cv2.putText(vis,chr(65+n),(int(M['m10']/M['m00'])*Z,int(M['m01']/M['m00'])*Z),
                    cv2.FONT_HERSHEY_SIMPLEX,1.4,col,4,cv2.LINE_AA)
    print(f'  blob {chr(65+n)}: area {int(cv2.contourArea(c))} px  bbox {cv2.boundingRect(c)} (+{x0},{y0})')
    n+=1
cv2.imwrite(OUT,np.hstack([big,np.full((big.shape[0],10,3),250,np.uint8),vis]))
print(OUT,vis.shape,'blobs',n)
