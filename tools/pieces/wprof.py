#!/usr/bin/env python3
"""wprof.py FRAME x0,y0,x1,y1 ZOOM PCT LABEL -- straighten the darkest blob along
its long axis and report its width every 10% of depth, in native pixels."""
import sys,cv2,numpy as np
fn=sys.argv[1]; x0,y0,x1,y1=[int(v) for v in sys.argv[2].split(',')]
Z=int(sys.argv[3]); PCT=float(sys.argv[4]); tag=sys.argv[5]
im=cv2.imread(fn)
c=cv2.resize(im[y0:y1,x0:x1],None,fx=Z,fy=Z,interpolation=cv2.INTER_LANCZOS4)
g=c.reshape(-1,3).astype(np.float32); L=g.mean(1); ref=g[L>=np.percentile(L,84)].mean(0)
c=np.clip(c.astype(np.float32)*(ref.mean()/ref),0,255).astype(np.uint8)
gr=cv2.cvtColor(c,cv2.COLOR_BGR2GRAY)
m=(gr<np.percentile(gr,PCT)).astype(np.uint8)
m=cv2.morphologyEx(m,cv2.MORPH_OPEN,np.ones((max(3,Z//2)|1,max(3,Z//2)|1),np.uint8))
n,lb,st,_=cv2.connectedComponentsWithStats(m,8)
if n<2: sys.exit(tag+': no blob')
k=int(np.argmax(st[1:,4])+1); s=(lb==k).astype(np.uint8)
ct=max(cv2.findContours(s,cv2.RETR_EXTERNAL,cv2.CHAIN_APPROX_NONE)[0],key=cv2.contourArea)
(cx,cy),(rw,rh),ang=cv2.minAreaRect(ct); A,B=max(rw,rh),min(rw,rh)
rot=ang if rw<rh else ang+90
M=cv2.getRotationMatrix2D((cx,cy),rot,1.0)
sr=cv2.warpAffine(s,M,(s.shape[1],s.shape[0]),flags=cv2.INTER_NEAREST)
ys,_=np.where(sr>0); a,b=ys.min(),ys.max()
sol=cv2.contourArea(ct)/max(cv2.contourArea(cv2.convexHull(ct)),1)
print(f'{tag}: {A/Z:.1f} x {B/Z:.1f} native, elong {A/B:.2f}, solidity {sol:.2f}')
ws=[]
for f in range(10,100,10):
    y=int(a+(b-a)*f/100); row=np.where(sr[y]>0)[0]
    w=(row.max()-row.min()+1)/Z if len(row) else 0.0; ws.append((f,w))
print('   ' + '  '.join(f'{f}%:{w:.1f}' for f,w in ws))
mx=max(w for _,w in ws); i=[f for f,w in ws if w==mx][0]
aft=[(f,w) for f,w in ws if f>i]
mono=all(aft[j][1]<=aft[j-1][1]+0.3 for j in range(1,len(aft)))
print(f'   widest at {i}% ; monotone after? {"yes" if mono else "NO (waist present)"}')
