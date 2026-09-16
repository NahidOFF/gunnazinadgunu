#!/usr/bin/env python3
"""Per-piece multi-shot super-resolution.

  piecesr.py SPEC.json OUT.png

SPEC = {
  "canon": {"w":..,"h":..},                       # canonical patch size in px
  "shots": [
     {"cache":"h803.npz", "quad":[[x,y],...4],    # quad in that cache's REFERENCE frame coords
      "ecc":true},
     ...
  ]
}
Every shot's reference quad is mapped to the canonical rectangle; each frame of the
shot is warped through its cached homography; ECC refines each frame against the
running template.  Result = masked median of all warped frames from all shots.
"""
import sys, json, glob, cv2, numpy as np
U='/root/.claude/uploads/84fa90fa-750b-5180-b6a9-f390607e1640'
cm=json.load(open('clipmap.json'))
spec=json.load(open(sys.argv[1])); OUT=sys.argv[2]
W,H = spec['canon']['w'], spec['canon']['h']
dst = np.float32([[0,0],[W,0],[W,H],[0,H]])
acc=[]; msks=[]
tmpl=None
for si,sh in enumerate(spec['shots']):
    z=np.load(sh['cache']); CID=str(z['cid']); CX0,CY0,CX1,CY1=z['ctx']; Hs=z['H']; ts=z['t']
    src=glob.glob(f'{U}/{CID}*')[0]; off=cm[CID]['offset']
    q0=np.float32(sh['quad']) - np.float32([CX0,CY0])     # into ctx coords
    rots=[np.roll(q0,-r,axis=0) for r in range(4)] if tmpl is not None else [q0]
    Hq=cv2.getPerspectiveTransform(rots[0], dst); rot_locked=(tmpl is None)
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
                if not rot_locked:
                    best=(-2,0)
                    for r,qq in enumerate(rots):
                        Hqr=cv2.getPerspectiveTransform(qq,dst)
                        gr=cv2.cvtColor(cv2.warpPerspective(C,Hqr@Hs[k],(W,H),flags=cv2.INTER_CUBIC),
                                        cv2.COLOR_BGR2GRAY).astype(np.float32)
                        t4=cv2.resize(tmpl,None,fx=0.25,fy=0.25); g4=cv2.resize(gr,None,fx=0.25,fy=0.25)
                        cc=float(np.corrcoef(t4.ravel(),g4.ravel())[0,1])
                        if cc>best[0]: best=(cc,r)
                    if best[0] < 0.35:
                        print(f'  SKIPPING shot: best rotation only corr {best[0]:.3f} '
                              f'- quad does not correspond, fusing it would poison the median',flush=True)
                        break
                    Hq=cv2.getPerspectiveTransform(rots[best[1]],dst); rot_locked=True
                    print(f'  rotation {best[1]} (corr {best[0]:.3f})',flush=True)
                    Hf=Hq@Hs[k]
                    v=cv2.warpPerspective(np.full(C.shape[:2],255,np.uint8),Hf,(W,H),flags=cv2.INTER_NEAREST)
                im=cv2.warpPerspective(C,Hf,(W,H),flags=cv2.INTER_CUBIC)
                g=cv2.cvtColor(im,cv2.COLOR_BGR2GRAY).astype(np.float32)
                if tmpl is None:
                    tmpl=g.copy()
                elif sh.get('ecc',True):
                    warp=np.eye(3,dtype=np.float32)
                    ok2=True
                    for sc in (0.25,0.5,1.0):
                        t2=cv2.resize(tmpl,None,fx=sc,fy=sc); g2=cv2.resize(g,None,fx=sc,fy=sc)
                        S=np.diag([sc,sc,1.0]).astype(np.float32)
                        w2=S@warp@np.linalg.inv(S); w2=(w2/w2[2,2]).astype(np.float32)
                        try:
                            cc,w2=cv2.findTransformECC(t2,g2,w2,cv2.MOTION_HOMOGRAPHY,
                                     (cv2.TERM_CRITERIA_EPS|cv2.TERM_CRITERIA_COUNT,80,1e-6),None,5)
                        except cv2.error:
                            ok2=False; break
                        warp=np.linalg.inv(S)@w2@S; warp=(warp/warp[2,2]).astype(np.float32)
                    if ok2:
                        im=cv2.warpPerspective(im,warp,(W,H),flags=cv2.INTER_CUBIC|cv2.WARP_INVERSE_MAP)
                        v=cv2.warpPerspective(v,warp,(W,H),flags=cv2.INTER_NEAREST|cv2.WARP_INVERSE_MAP)
                    else:
                        fn+=1; continue
                acc.append(im); msks.append(v>0); n+=1
        fn+=1
    cap.release()
    print(f'shot{si} {sh["cache"]}: {n} frames', flush=True)
arr=np.stack(acc); msk=np.stack(msks)
out=np.zeros((H,W,3),np.float32)
band=max(1,int(3e7//(W*3*len(acc)*4)))
for r0 in range(0,H,band):
    r1=min(H,r0+band); sub=arr[:,r0:r1].astype(np.float32); sub[~msk[:,r0:r1]]=np.nan
    out[r0:r1]=np.nanmedian(sub,axis=0)
out=np.nan_to_num(out,nan=0)
cv2.imwrite(OUT,out.clip(0,255).astype(np.uint8))
print(f'{len(acc)} frames -> {OUT} {W}x{H}')
