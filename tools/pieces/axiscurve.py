#!/usr/bin/env python3
"""axiscurve.py FRAME x0,y0,x1,y1 ZOOM LABEL [--dark] -- is a shape's spine curved
or straight?

Takes the shape's mask, finds its long axis by PCA, then walks the axis in ten
steps and reports how far the local centroid sits off that axis, as a percentage
of the shape's length.  A straight shape (a pen, a bar) stays near 0; an arc (a
banana, a croissant) bows to one side and comes back, so the offsets trace a
single-signed hump.  'sagitta' is the largest offset -- the depth of the bow.

Run against synthetic controls first: this only means something if a drawn
straight bar and a drawn arc of the same size separate cleanly."""
import sys,cv2,numpy as np
def spine(mask):
    ys,xs=np.nonzero(mask)
    if len(xs)<40: return None
    p=np.stack([xs,ys]).astype(np.float64); mu=p.mean(1,keepdims=True)
    w,v=np.linalg.eigh(np.cov(p-mu)); ax=v[:,1]; perp=v[:,0]
    t=(p-mu).T@ax; d=(p-mu).T@perp
    L=t.max()-t.min()
    offs=[]
    for i in range(10):
        a=t.min()+L*i/10; b=t.min()+L*(i+1)/10
        m=(t>=a)&(t<b)
        offs.append(float(d[m].mean())/L*100 if m.sum()>5 else np.nan)
    W=(d.max()-d.min())
    return L,W,offs
def report(tag,mask):
    r=spine(mask)
    if r is None: print(f'   {tag:22s} too small'); return
    L,W,offs=r
    # The PCA axis passes through the centroid, so on an arc the middle sits to
    # one side of it and both ends to the other.  The depth of the bow is that
    # difference; on a straight shape it is ~0.  This is what the controls set.
    mid=np.nanmean(offs[3:7]); end=np.nanmean([offs[0],offs[-1]])
    sag=mid-end
    # An arc bends both ends the same way, so its two end offsets match; a shape
    # with a hook at ONE end does not.  Without this the two look alike on 'bow'
    # alone, and a hooked pen reads as an arc.
    asym=abs(offs[0]-offs[-1])
    v=('straight' if abs(sag)<=6 else
       'ARC (bends as a whole)' if asym<0.45*abs(sag) else
       'hook at ONE end, body straight')
    print(f'   {tag:22s} len={L:5.1f} wid={W:5.1f} elong={L/max(W,.1):4.2f}  '
          f'bow={sag:+5.1f}% asym={asym:4.1f}  {v}')
    print(f'   {"":22s} offsets ' + ' '.join(f'{x:+5.1f}' for x in offs))
# --- synthetic controls at the real scale -------------------------------------
for name,curve in (('CONTROL straight bar',0.0),('CONTROL arc (banana-like)',0.30)):
    m=np.zeros((320,320),np.uint8)
    for i in range(200):
        u=i/199.0; x=60+int(200*u); y=160+int(curve*200*(4*u*(1-u)))-0
        cv2.circle(m,(x,y),14,255,-1)
    m=cv2.resize(m,(32,32),interpolation=cv2.INTER_AREA)
    m=cv2.resize((m>110).astype(np.uint8)*255,None,fx=10,fy=10,interpolation=cv2.INTER_NEAREST)
    report(name,m>0)
# --- the real shape -----------------------------------------------------------
fn=sys.argv[1]; x0,y0,x1,y1=[int(v) for v in sys.argv[2].split(',')]
Z=int(sys.argv[3]); tag=sys.argv[4]; DARK='--dark' in sys.argv
im=cv2.imread(fn).astype(np.float32)
c=cv2.resize(im[y0:y1,x0:x1],None,fx=Z,fy=Z,interpolation=cv2.INTER_LANCZOS4)
g=c.reshape(-1,3); L=g.mean(1); ref=g[L>=np.percentile(L,88)].mean(0)
c=np.clip(c*(ref.mean()/ref),0,255).astype(np.uint8)
lab=cv2.cvtColor(c,cv2.COLOR_BGR2LAB).astype(np.float32)
Lc,A,B=lab[:,:,0],lab[:,:,1]-128,lab[:,:,2]-128
pap=Lc>=np.percentile(Lc,82); pa,pb=A[pap].mean(),B[pap].mean()
m=(Lc<np.percentile(Lc,82)-26) if DARK else (np.hypot(A-pa,B-pb)>9)
m=cv2.morphologyEx(m.astype(np.uint8),cv2.MORPH_CLOSE,np.ones((Z,Z),np.uint8))
n,lb,st,ct=cv2.connectedComponentsWithStats(m,8)
if n<2: sys.exit('no shape')
# Pick the component nearest the crop centre whose area is a plausible fraction
# of the crop, not simply the largest: on these cards the largest chromatic
# component is usually the desk or the neighbouring card, which is how the two
# previous readings of this shape came out of a mask that was mostly background.
H0,W0=m.shape; tot=H0*W0; cand=[]
for i in range(1,n):
    a=st[i][4]
    if not (0.03*tot < a < 0.55*tot): continue
    cand.append((np.hypot(ct[i][0]-W0/2,ct[i][1]-H0/2),i))
if not cand: sys.exit('no plausible component -- widen or re-cut the box')
k=min(cand)[1]; sel=(lb==k)
hull=cv2.convexHull(cv2.findContours(sel.astype(np.uint8),cv2.RETR_EXTERNAL,
     cv2.CHAIN_APPROX_SIMPLE)[0][0])
print(f'== {tag}   solidity={sel.sum()/max(cv2.contourArea(hull),1):.2f}')
report(tag,sel)
vis=c.copy(); vis[sel]=(0.4*vis[sel]+0.6*np.float32([255,0,255])).astype(np.uint8)
cv2.imwrite(f'AX_{tag.split()[0]}.png',np.hstack([c,np.full((c.shape[0],8,3),250,np.uint8),vis]))
