#!/usr/bin/env python3
"""One card, several takes.  Each take samples the card on a different pixel grid and at
a different scale, so fusing them buys real resolution that no single take has.

The card is flat, so a homography is exact: find the card in each take by multi-scale
template match, upscale, refine with ECC on a homography, then average.
"""
import sys, cv2, numpy as np
SP='/tmp/claude-0/-home-user-gunnazinadgunu/84fa90fa-750b-5180-b6a9-f390607e1640/scratchpad/'
name=sys.argv[1]
x0,y0,x1,y1=[int(v) for v in sys.argv[2:6]]
Z=int(sys.argv[6]) if len(sys.argv)>6 else 8
REFS=['REF803.png','REF806.png','REF765.png','REF767.png']
base=cv2.imread(SP+REFS[0])
tpl=base[y0:y1,x0:x1]
H,W=tpl.shape[:2]
canvas=cv2.resize(tpl,(W*Z,H*Z),interpolation=cv2.INTER_LANCZOS4).astype(np.float32)
ref_g=cv2.cvtColor(canvas.astype(np.uint8),cv2.COLOR_BGR2GRAY).astype(np.float32)
acc=canvas.copy(); n=1; used=[REFS[0]]
tg=cv2.cvtColor(tpl,cv2.COLOR_BGR2GRAY)
for fn in REFS[1:]:
    im=cv2.imread(SP+fn)
    if im is None: continue
    g=cv2.cvtColor(im,cv2.COLOR_BGR2GRAY)
    best=None
    for s in np.arange(0.7,1.65,0.02):
        t=cv2.resize(tg,None,fx=s,fy=s,interpolation=cv2.INTER_AREA)
        if t.shape[0]>=g.shape[0] or t.shape[1]>=g.shape[1]: continue
        r=cv2.matchTemplate(g,t,cv2.TM_CCOEFF_NORMED)
        _,mx,_,loc=cv2.minMaxLoc(r)
        if best is None or mx>best[0]: best=(mx,s,loc,t.shape)
    if not best or best[0]<0.55:
        print('  %-12s no match (%.2f)'%(fn,best[0] if best else -1)); continue
    mx,s,loc,shp=best
    crop=im[loc[1]:loc[1]+shp[0], loc[0]:loc[0]+shp[1]]
    up=cv2.resize(crop,(W*Z,H*Z),interpolation=cv2.INTER_LANCZOS4).astype(np.float32)
    ug=cv2.cvtColor(up.astype(np.uint8),cv2.COLOR_BGR2GRAY).astype(np.float32)
    warp=np.eye(3,dtype=np.float32)
    try:
        cc,warp=cv2.findTransformECC(ref_g,ug,warp,cv2.MOTION_HOMOGRAPHY,
            (cv2.TERM_CRITERIA_EPS|cv2.TERM_CRITERIA_COUNT,400,1e-8),None,9)
    except cv2.error as e:
        print('  %-12s ECC failed'%fn); continue
    print('  %-12s match %.2f scale %.2f  ECC %.3f'%(fn,mx,s,cc))
    if cc<0.55: continue
    al=cv2.warpPerspective(up,warp,(W*Z,H*Z),flags=cv2.INTER_CUBIC|cv2.WARP_INVERSE_MAP,
                           borderMode=cv2.BORDER_REFLECT)
    acc+=al; n+=1; used.append(fn)
m=acc/n
print('fused',n,'views:',', '.join(used))
def enh(b,sat=2.0):
    g=b.reshape(-1,3);L=g.mean(1);r=g[L>=np.percentile(L,85)].mean(0)
    b=np.clip(b*(r.mean()/np.maximum(r,1)),0,255).astype(np.uint8)
    lb=cv2.cvtColor(b,cv2.COLOR_BGR2LAB).astype(np.float32)
    lo,hi=np.percentile(lb[:,:,0],2),np.percentile(lb[:,:,0],98)
    lb[:,:,0]=np.clip((lb[:,:,0]-lo)*255/max(hi-lo,1),0,255)
    for c in (1,2): lb[:,:,c]=np.clip((lb[:,:,c]-128)*sat+128,0,255)
    return cv2.cvtColor(lb.astype(np.uint8),cv2.COLOR_LAB2BGR)
a=enh(canvas); b=enh(m)
b=cv2.filter2D(b,-1,np.array([[0,-.35,0],[-.35,2.4,-.35],[0,-.35,0]],np.float32))
pad=np.full((a.shape[0],24,3),250,np.uint8)
cv2.imwrite(SP+'MV_%s.png'%name, np.hstack([a,pad,b]))
lap=lambda z: cv2.Laplacian(cv2.cvtColor(z,cv2.COLOR_BGR2GRAY),cv2.CV_64F).var()
print('Laplacian var: single %.1f  fused %.1f'%(lap(a),lap(b)))
