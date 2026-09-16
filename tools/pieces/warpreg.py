#!/usr/bin/env python3
"""Masked-median SR of several regions from cached homographies (memory-lean, uint8 stack).
usage: warpreg.py CACHE.npz REGIONS.json OUTDIR [--minvalid F] [--mode median|mean]"""
import cv2,numpy as np,sys,json,glob,os
U='/root/.claude/uploads/84fa90fa-750b-5180-b6a9-f390607e1640'
cm=json.load(open('clipmap.json'))
a=sys.argv[1:]; minv=0.55; mode='median'
if '--minvalid' in a: i=a.index('--minvalid'); minv=float(a[i+1]); del a[i:i+2]
if '--mode' in a: i=a.index('--mode'); mode=a[i+1]; del a[i:i+2]
z=np.load(a[0]); REG=json.load(open(a[1])); OUTD=a[2]; os.makedirs(OUTD,exist_ok=True)
CID=str(z['cid']); CX0,CY0,CX1,CY1=z['ctx']; Hs=z['H']; ts=z['t']
src=glob.glob(f'{U}/{CID}*')[0]; off=cm[CID]['offset']
cap=cv2.VideoCapture(src); fps=cap.get(cv2.CAP_PROP_FPS)
# read frames sequentially, index by frame number
want={int(round((t-off)*fps)):k for k,t in enumerate(ts)}
frames={}
cap.set(cv2.CAP_PROP_POS_FRAMES,min(want))
fn=min(want)
while fn<=max(want):
    ok,fr=cap.read()
    if not ok: break
    if fn in want: frames[want[fn]]=fr[CY0:CY1,CX0:CX1].copy()
    fn+=1
cap.release()
print(f'decoded {len(frames)} frames',flush=True)
for name,(x0,y0,x1,y1,S) in REG.items():
    W,Hh=(x1-x0)*S,(y1-y0)*S
    Hb=np.array([[S,0,-S*(x0-CX0)],[0,S,-S*(y0-CY0)],[0,0,1]],float)
    imgs=[]; msks=[]
    for k,C in frames.items():
        Hsf=Hb@Hs[k]
        v=cv2.warpPerspective(np.full(C.shape[:2],255,np.uint8),Hsf,(W,Hh),flags=cv2.INTER_NEAREST)
        if (v>0).mean()<minv: continue
        imgs.append(cv2.warpPerspective(C,Hsf,(W,Hh),flags=cv2.INTER_CUBIC))
        msks.append(v>0)
    if not imgs: print(name,'EMPTY'); continue
    arr=np.stack(imgs); msk=np.stack(msks)
    out=np.zeros((Hh,W,3),np.float32)
    band=max(1,int(4e7//(W*3*len(imgs)*4)))
    for r0 in range(0,Hh,band):
        r1=min(Hh,r0+band)
        sub=arr[:,r0:r1].astype(np.float32)
        sub[~msk[:,r0:r1]]=np.nan
        out[r0:r1]=np.nanmedian(sub,axis=0) if mode=='median' else np.nanmean(sub,axis=0)
    out=np.nan_to_num(out,nan=0)
    p=os.path.join(OUTD,name+'.png'); cv2.imwrite(p,out.clip(0,255).astype(np.uint8))
    print(f'{name}: n={len(imgs)} {W}x{Hh} -> {p}',flush=True)
    del arr,msk,imgs,msks
