#!/usr/bin/env python3
"""Iterative back-projection super-resolution for one piece, across several shots.

  piecesr_ibp.py SPEC.json OUT.png [ITERS] [SCALE]

Same SPEC as piecesr.py. Instead of taking a masked median of the up-warped
frames, this estimates a high-resolution image x that, when blurred and
down-sampled through each frame's own warp, reproduces the observed frames:

    x <- x + a * mean_k  W_k^T [ up( y_k - down( B W_k x ) ) ]

Registration comes from the cached homographies plus a pyramid-ECC refinement
against the first frame, exactly as in piecesr.py; only the estimator differs.
"""
import sys, json, glob, cv2, numpy as np
U='/root/.claude/uploads/84fa90fa-750b-5180-b6a9-f390607e1640'
cm=json.load(open('clipmap.json'))
spec=json.load(open(sys.argv[1])); OUT=sys.argv[2]
ITERS=int(sys.argv[3]) if len(sys.argv)>3 else 24
W,H = spec['canon']['w'], spec['canon']['h']
S    = int(sys.argv[4]) if len(sys.argv)>4 else 4      # HR grid = canonical/S is the LR sampling
dst=np.float32([[0,0],[W,0],[W,H],[0,H]])

obs=[]      # (lr image float32, valid mask, warp-to-canonical is already applied)
tmpl=None
for si,sh in enumerate(spec['shots']):
    z=np.load(sh['cache']); CID=str(z['cid']); CX0,CY0,CX1,CY1=z['ctx']; Hs=z['H']; ts=z['t']
    src=glob.glob(f'{U}/{CID}*')[0]; off=cm[CID]['offset']
    q0=np.float32(sh['quad'])-np.float32([CX0,CY0])
    rots=[np.roll(q0,-r,axis=0) for r in range(4)] if tmpl is not None else [q0]
    Hq=cv2.getPerspectiveTransform(rots[0],dst); locked=(tmpl is None)
    cap=cv2.VideoCapture(src); fps=cap.get(cv2.CAP_PROP_FPS)
    want={int(round((t-off)*fps)):k for k,t in enumerate(ts)}
    cap.set(cv2.CAP_PROP_POS_FRAMES,min(want)); fn=min(want); n=0
    while fn<=max(want):
        ok,fr=cap.read()
        if not ok: break
        if fn in want:
            k=want[fn]; C=fr[CY0:CY1,CX0:CX1]
            Hf=Hq@Hs[k]
            v=cv2.warpPerspective(np.full(C.shape[:2],255,np.uint8),Hf,(W,H),flags=cv2.INTER_NEAREST)
            if (v>0).mean()>0.90:
                im=cv2.warpPerspective(C,Hf,(W,H),flags=cv2.INTER_CUBIC)
                g=cv2.cvtColor(im,cv2.COLOR_BGR2GRAY).astype(np.float32)
                if tmpl is None:
                    tmpl=g.copy()
                else:
                    if not locked:
                        best=(-2,0)
                        for r,qq in enumerate(rots):
                            Hqr=cv2.getPerspectiveTransform(qq,dst)
                            gr=cv2.cvtColor(cv2.warpPerspective(C,Hqr@Hs[k],(W,H),flags=cv2.INTER_CUBIC),
                                            cv2.COLOR_BGR2GRAY).astype(np.float32)
                            t4=cv2.resize(tmpl,None,fx=.25,fy=.25); g4=cv2.resize(gr,None,fx=.25,fy=.25)
                            cc=float(np.corrcoef(t4.ravel(),g4.ravel())[0,1])
                            if cc>best[0]: best=(cc,r)
                        if best[0]<0.35:
                            print(f'  shot{si}: skipped (corr {best[0]:.3f})',flush=True); break
                        Hq=cv2.getPerspectiveTransform(rots[best[1]],dst); locked=True
                        print(f'  shot{si}: rotation {best[1]} corr {best[0]:.3f}',flush=True)
                        Hf=Hq@Hs[k]
                        v=cv2.warpPerspective(np.full(C.shape[:2],255,np.uint8),Hf,(W,H),flags=cv2.INTER_NEAREST)
                        im=cv2.warpPerspective(C,Hf,(W,H),flags=cv2.INTER_CUBIC)
                        g=cv2.cvtColor(im,cv2.COLOR_BGR2GRAY).astype(np.float32)
                    warp=np.eye(3,dtype=np.float32); ok2=True
                    for sc in (0.25,0.5,1.0):
                        t2=cv2.resize(tmpl,None,fx=sc,fy=sc); g2=cv2.resize(g,None,fx=sc,fy=sc)
                        Sm=np.diag([sc,sc,1.0]).astype(np.float32)
                        w2=Sm@warp@np.linalg.inv(Sm); w2=(w2/w2[2,2]).astype(np.float32)
                        try:
                            _,w2=cv2.findTransformECC(t2,g2,w2,cv2.MOTION_HOMOGRAPHY,
                                   (cv2.TERM_CRITERIA_EPS|cv2.TERM_CRITERIA_COUNT,80,1e-6),None,5)
                        except cv2.error: ok2=False; break
                        warp=np.linalg.inv(Sm)@w2@Sm; warp=(warp/warp[2,2]).astype(np.float32)
                    if not ok2: fn+=1; continue
                    im=cv2.warpPerspective(im,warp,(W,H),flags=cv2.INTER_CUBIC|cv2.WARP_INVERSE_MAP)
                    v =cv2.warpPerspective(v ,warp,(W,H),flags=cv2.INTER_NEAREST|cv2.WARP_INVERSE_MAP)
                # store the frame already in canonical geometry, at LR sampling
                lr = cv2.resize(im.astype(np.float32),(W//S,H//S),interpolation=cv2.INTER_AREA)
                mk = cv2.resize((v>0).astype(np.float32),(W//S,H//S),interpolation=cv2.INTER_AREA)>0.98
                obs.append((lr,mk)); n+=1
        fn+=1
    cap.release()
    print(f'shot{si}: {n} frames',flush=True)

print(f'{len(obs)} observations, HR grid {W}x{H}, LR {W//S}x{H//S}',flush=True)
# initial estimate: mean of the up-sampled frames
acc=np.zeros((H,W,3),np.float32); cnt=np.zeros((H,W,1),np.float32)
for lr,mk in obs:
    up=cv2.resize(lr,(W,H),interpolation=cv2.INTER_CUBIC)
    m=cv2.resize(mk.astype(np.float32),(W,H),interpolation=cv2.INTER_NEAREST)[...,None]
    acc+=up*m; cnt+=m
x=acc/np.maximum(cnt,1e-6)
BLUR=(0,0); SIG=S*0.45
alpha=0.9
for it in range(ITERS):
    grad=np.zeros_like(x); gc=np.zeros((H,W,1),np.float32)
    for lr,mk in obs:
        sim=cv2.GaussianBlur(x,BLUR,SIG)
        sim=cv2.resize(sim,(W//S,H//S),interpolation=cv2.INTER_AREA)
        r=(lr-sim); r[~mk]=0
        rup=cv2.resize(r,(W,H),interpolation=cv2.INTER_CUBIC)
        rup=cv2.GaussianBlur(rup,BLUR,SIG)
        m=cv2.resize(mk.astype(np.float32),(W,H),interpolation=cv2.INTER_NEAREST)[...,None]
        grad+=rup*m; gc+=m
    x=x+alpha*grad/np.maximum(gc,1e-6)
    x=cv2.bilateralFilter(np.clip(x,0,255).astype(np.uint8),5,18,7).astype(np.float32)  # mild edge-preserving prior
    if it%6==0: print(f'  iter {it} rms {np.sqrt((grad**2).mean()):.3f}',flush=True)
cv2.imwrite(OUT,np.clip(x,0,255).astype(np.uint8))
print('wrote',OUT)
