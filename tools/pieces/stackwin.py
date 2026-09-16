#!/usr/bin/env python3
"""Registered multi-frame stack (mean) + light IBP, for a card window."""
import sys,glob,cv2,numpy as np
d,x0,y0,x1,y1,OUT=sys.argv[1],*[int(v) for v in sys.argv[2:6]],sys.argv[6]
S=int(sys.argv[7]) if len(sys.argv)>7 else 3
PAD=16
fs=sorted(glob.glob(d+'/*.png'))
cr=[]
for f in fs:
    im=cv2.imread(f)
    if im is None: continue
    c=im[y0-PAD:y1+PAD, x0-PAD:x1+PAD]
    if c.size==0: continue
    g=cv2.cvtColor(c,cv2.COLOR_BGR2GRAY)
    cr.append((cv2.Laplacian(g,cv2.CV_64F).var(),c,g.astype(np.float32)))
cr.sort(key=lambda r:-r[0])
cr=cr[:max(8,int(len(cr)*0.7))]
ref=cr[0][2]; H,W=ref.shape
acc=np.zeros((H,W,3),np.float64); n=0; kept=[]
for lv,c,g in cr:
    warp=np.eye(3,dtype=np.float32)
    try:
        cc,warp=cv2.findTransformECC(ref,g,warp,cv2.MOTION_HOMOGRAPHY,
            (cv2.TERM_CRITERIA_EPS|cv2.TERM_CRITERIA_COUNT,300,1e-8),None,5)
    except cv2.error: continue
    if cc<0.90: continue
    al=cv2.warpPerspective(c,warp,(W,H),flags=cv2.INTER_CUBIC|cv2.WARP_INVERSE_MAP,borderMode=cv2.BORDER_REFLECT)
    acc+=al; n+=1; kept.append(cc)
print('stacked',n,'of',len(cr),'mean corr %.3f'%(np.mean(kept) if kept else 0))
mean=(acc/max(n,1)).astype(np.float32)
hr=cv2.resize(mean,None,fx=S,fy=S,interpolation=cv2.INTER_CUBIC)
k=cv2.getGaussianKernel(2*S+1,S*0.45); K=(k@k.T).astype(np.float32)
for _ in range(14):
    sim=cv2.resize(cv2.filter2D(hr,-1,K),(W,H),interpolation=cv2.INTER_AREA)
    hr=hr+0.7*cv2.filter2D(cv2.resize(mean-sim,None,fx=S,fy=S,interpolation=cv2.INTER_CUBIC),-1,K)
hr=np.clip(hr,0,255)
def enh(b,sat=2.0):
    g=b.reshape(-1,3);L=g.mean(1);r=g[L>=np.percentile(L,82)].mean(0)
    b=np.clip(b*(r.mean()/np.maximum(r,1)),0,255).astype(np.uint8)
    lb=cv2.cvtColor(b,cv2.COLOR_BGR2LAB).astype(np.float32)
    Lc=lb[:,:,0];lo,hi=np.percentile(Lc,2),np.percentile(Lc,98)
    lb[:,:,0]=np.clip((Lc-lo)*255/max(hi-lo,1),0,255)
    for c in (1,2): lb[:,:,c]=np.clip((lb[:,:,c]-128)*sat+128,0,255)
    return cv2.cvtColor(lb.astype(np.uint8),cv2.COLOR_LAB2BGR)
Z=16
a=cv2.resize(enh(cr[0][1].astype(np.float32)),None,fx=Z,fy=Z,interpolation=cv2.INTER_LANCZOS4)
b=cv2.resize(enh(mean),(a.shape[1],a.shape[0]),interpolation=cv2.INTER_LANCZOS4)
c=cv2.resize(enh(hr),(a.shape[1],a.shape[0]),interpolation=cv2.INTER_LANCZOS4)
pad=np.full((a.shape[0],30,3),250,np.uint8)
body=np.hstack([a,pad,b,pad,c])
o=np.full((body.shape[0]+34,body.shape[1],3),250,np.uint8)
o[34:]=body
x=5
for nm,t in (('tek kadr',a),('yigin',b),('IBP',c)):
    cv2.putText(o,nm,(x,26),cv2.FONT_HERSHEY_SIMPLEX,0.9,(0,0,0),2,cv2.LINE_AA); x+=t.shape[1]+30
cv2.imwrite(OUT,o); print(OUT,o.shape)
