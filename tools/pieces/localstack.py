#!/usr/bin/env python3
"""localstack.py CACHE.npz REFPNG x0,y0,x1,y1 ZOOM OUT.png -- median-stack one small
box across many frames, aligned LOCALLY.

The cached homographies are fitted over the whole right half of the frame, so at
one small card they carry parallax error.  Each frame's box is therefore warped
with its global homography and then refined by ECC on the box itself before
stacking.  Median, not mean, so a frame the refinement failed on cannot smear
the result.

Prints a sharpness number for the single reference frame and for the stack, so
the stack is only worth using if it actually wins.  Every earlier attempt at
combining frames lost to plain Lanczos on one frame."""
import sys,cv2,numpy as np,json,glob
U='/root/.claude/uploads/84fa90fa-750b-5180-b6a9-f390607e1640'
cm=json.load(open('clipmap.json'))
z=np.load(sys.argv[1]); REF=sys.argv[2]
x0,y0,x1,y1=[int(v) for v in sys.argv[3].split(',')]; Z=int(sys.argv[4]); OUT=sys.argv[5]
CX0,CY0,CX1,CY1=[int(v) for v in z['ctx']]
cid=str(z['cid']); off=cm[cid]['offset']
src=glob.glob(f'{U}/{cid}*')[0]
cap=cv2.VideoCapture(src); fps=cap.get(cv2.CAP_PROP_FPS)
ref=cv2.imread(REF)
def crop(im): return im[y0:y1,x0:x1].astype(np.float32)
tmpl=crop(ref)
tg=cv2.cvtColor(cv2.resize(tmpl,None,fx=Z,fy=Z,interpolation=cv2.INTER_LANCZOS4),
                cv2.COLOR_BGR2GRAY)
tg=(tg-tg.mean())/(tg.std()+1e-6)
def quality(a):
    # Laplacian variance is the wrong metric here: it REWARDS noise, which is
    # exactly what a stack removes, so it called an obvious improvement a tie.
    # Report the two things separately -- contrast across real edges, and the
    # scatter inside flat areas.
    g=cv2.cvtColor(a.astype(np.uint8),cv2.COLOR_BGR2GRAY).astype(np.float32)
    gx=cv2.Sobel(g,cv2.CV_32F,1,0,ksize=3); gy=cv2.Sobel(g,cv2.CV_32F,0,1,ksize=3)
    m=np.hypot(gx,gy)
    edge=m[m>=np.percentile(m,97)].mean()          # contrast on the strongest edges
    flat=m<np.percentile(m,40)
    hp=g-cv2.GaussianBlur(g,(0,0),2.0)
    noise=hp[flat].std()                            # scatter where nothing happens
    return edge,noise
obs=[]; used=0
for H,t in zip(z['H'],z['t']):
    cap.set(cv2.CAP_PROP_POS_FRAMES,int(round((t-off)*fps)))
    ok,fr=cap.read()
    if not ok: continue
    # H maps the frame's ctx-crop into the reference's ctx-crop
    sub=fr[CY0:CY1,CX0:CX1]
    w=cv2.warpPerspective(sub,H,(CX1-CX0,CY1-CY0),flags=cv2.INTER_LANCZOS4)
    full=np.zeros_like(fr); full[CY0:CY1,CX0:CX1]=w
    c=cv2.resize(crop(full),None,fx=Z,fy=Z,interpolation=cv2.INTER_LANCZOS4)
    if c.mean()<8: continue
    g=cv2.cvtColor(c,cv2.COLOR_BGR2GRAY); g=(g-g.mean())/(g.std()+1e-6)
    try:
        wm=np.eye(2,3,dtype=np.float32)
        cv2.findTransformECC(tg,g,wm,cv2.MOTION_EUCLIDEAN,
            (cv2.TERM_CRITERIA_EPS|cv2.TERM_CRITERIA_COUNT,60,1e-5),None,5)
    except cv2.error:
        continue
    a=cv2.warpAffine(c,wm,(c.shape[1],c.shape[0]),
                     flags=cv2.INTER_LANCZOS4|cv2.WARP_INVERSE_MAP,
                     borderMode=cv2.BORDER_REPLICATE)
    obs.append(a); used+=1
cap.release()
one=cv2.resize(tmpl,None,fx=Z,fy=Z,interpolation=cv2.INTER_LANCZOS4)
# Lucky imaging: the frames differ mostly in motion blur, and a median over all
# of them averages the sharp ones into the smeared ones.  Keep only the sharpest
# quarter -- that is the whole point of stacking hand-held footage.
def edgeE(a):
    g=cv2.cvtColor(a.astype(np.uint8),cv2.COLOR_BGR2GRAY).astype(np.float32)
    m=np.hypot(cv2.Sobel(g,cv2.CV_32F,1,0,ksize=3),cv2.Sobel(g,cv2.CV_32F,0,1,ksize=3))
    return m[m>=np.percentile(m,97)].mean()
if obs:
    sc=sorted(range(len(obs)),key=lambda i:-edgeE(obs[i]))
    keep=[obs[i] for i in sc[:max(4,len(obs)//4)]]
    print(f'lucky imaging: keeping the sharpest {len(keep)} of {len(obs)}')
    st=np.median(np.stack(keep),0)
else:
    st=one
def wb(a):
    g=a.reshape(-1,3); L=g.mean(1); r=g[L>=np.percentile(L,88)].mean(0)
    return np.clip(a*(r.mean()/r),0,255).astype(np.uint8)
one_w,st_w=wb(one),wb(st)
print(f'frames aligned: {used} of {len(z["H"])}')
e1,n1=quality(one_w); e2,n2=quality(st_w)
print(f'  single frame : edge contrast {e1:7.1f}   flat-area noise {n1:6.2f}')
print(f'  stack        : edge contrast {e2:7.1f}   flat-area noise {n2:6.2f}')
print(f'  -> edges {100*(e2-e1)/max(e1,1e-6):+5.1f}%   noise {100*(n2-n1)/max(n1,1e-6):+5.1f}%'
      f'   {"STACK BETTER" if (n2<n1*0.8 and e2>e1*0.85) else "no clear gain"}')
cv2.imwrite(OUT,np.hstack([one_w,np.full((one_w.shape[0],8,3),250,np.uint8),st_w]))
print(OUT)
