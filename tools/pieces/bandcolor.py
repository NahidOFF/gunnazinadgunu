#!/usr/bin/env python3
"""bandcolor.py FRAME x0,y0,x1,y1 ZOOM N OUT.png LABEL -- split a drawing into N
horizontal bands from top to bottom, report each band's mean a*/b* against the
card's own paper, AND draw the bands on the zoom.

The paper is taken from the same crop, so the reading is a difference against
the paper the drawing sits on, not against an absolute white.  The bands are
drawn because placing them by eye is what went wrong in every earlier colour
test."""
import sys,cv2,numpy as np
fn=sys.argv[1]; x0,y0,x1,y1=[int(v) for v in sys.argv[2].split(',')]
Z=int(sys.argv[3]); N=int(sys.argv[4]); OUT=sys.argv[5]; tag=sys.argv[6]
im=cv2.imread(fn).astype(np.float32)
c=cv2.resize(im[y0:y1,x0:x1],None,fx=Z,fy=Z,interpolation=cv2.INTER_LANCZOS4)
g=c.reshape(-1,3); L=g.mean(1); ref=g[L>=np.percentile(L,88)].mean(0)
c=np.clip(c*(ref.mean()/ref),0,255).astype(np.uint8)
lab=cv2.cvtColor(c,cv2.COLOR_BGR2LAB).astype(np.float32)
Lc,A,B=lab[:,:,0],lab[:,:,1]-128,lab[:,:,2]-128
pap=Lc>=np.percentile(Lc,82)
pa,pb=A[pap].mean(),B[pap].mean()
# drawing = pixels whose COLOUR departs from the paper, or that are much darker.
# The earlier "not paper by lightness" rule selected the whole crop -- the mask
# panel showed it, which is why the mask is drawn.
chroma=np.hypot(A-pa,B-pb)
ink=(chroma>7)|(Lc<np.percentile(Lc,82)-22)
ys,xs=np.nonzero(ink)
if len(ys)<50: sys.exit('too little ink')
Y0,Y1=np.percentile(ys,2),np.percentile(ys,98)
vis=c.copy()
print(f'== {tag}   paper a*={pa:+.1f} b*={pb:+.1f}   ink rows {int(Y0)}..{int(Y1)}')
for i in range(N):
    a0=int(Y0+(Y1-Y0)*i/N); a1=int(Y0+(Y1-Y0)*(i+1)/N)
    m=np.zeros_like(ink); m[a0:a1]=ink[a0:a1]
    if m.sum()<20: print(f'   band {i+1}/{N}  (empty)'); continue
    da,db,dl=A[m].mean()-pa,B[m].mean()-pb,Lc[m].mean()
    hue=('green' if da<-3 else 'red/pink' if da>4 else 'warm' if db>6 else
         'cool/blue' if db<-4 else 'neutral')
    print(f'   band {i+1}/{N} rows {a0:4d}-{a1:4d}  da*={da:+6.1f} db*={db:+6.1f} '
          f'L={dl:5.1f}  {hue}')
    cv2.line(vis,(0,a0),(vis.shape[1],a0),(0,180,255),2)
    cv2.putText(vis,f'{i+1}: a{da:+.0f} b{db:+.0f}',(6,a0+22),
                cv2.FONT_HERSHEY_SIMPLEX,0.6,(0,90,220),2,cv2.LINE_AA)
cv2.line(vis,(0,int(Y1)),(vis.shape[1],int(Y1)),(0,180,255),2)
ov=c.copy(); ov[ink]=(0.45*ov[ink]+0.55*np.float32([255,0,255])).astype(np.uint8)
cv2.imwrite(OUT,np.hstack([c,np.full((c.shape[0],10,3),250,np.uint8),vis,
                           np.full((c.shape[0],10,3),250,np.uint8),ov]))
print('   ->',OUT)
