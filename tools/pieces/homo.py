#!/usr/bin/env python3
"""Compute homographies of every office-set frame onto a reference frame, cache to .npz"""
import cv2,numpy as np,json,glob,sys,os
U='/root/.claude/uploads/84fa90fa-750b-5180-b6a9-f390607e1640'
cm=json.load(open('clipmap.json'))
CID=sys.argv[1]; REFT=float(sys.argv[2]); OUT=sys.argv[3]
ranges=[]
a=sys.argv[4:]
while '--range' in a:
    i=a.index('--range'); t0,t1=a[i+1].split(':'); ranges.append((float(t0),float(t1))); del a[i:i+2]
# alignment context window (generous, covers right half of frame)
CX0,CY0,CX1,CY1=[int(v) for v in a[:4]] if len(a)>=4 else (1400,150,1920,1080)
src=glob.glob(f'{U}/{CID}*')[0]; off=cm[CID]['offset']
cap=cv2.VideoCapture(src); fps=cap.get(cv2.CAP_PROP_FPS)
def grab(t):
    cap.set(cv2.CAP_PROP_POS_FRAMES,int(round((t-off)*fps))); ok,fr=cap.read(); return fr if ok else None
ref=grab(REFT)
cl=cv2.createCLAHE(3.0,(8,8))
def prep(im): return cl.apply(cv2.cvtColor(im[CY0:CY1,CX0:CX1],cv2.COLOR_BGR2GRAY))
orb=cv2.ORB_create(15000); bf=cv2.BFMatcher(cv2.NORM_HAMMING,crossCheck=True)
k1,d1=orb.detectAndCompute(prep(ref),None)
Hs=[]; ts=[]
for (t0,t1) in ranges:
    cap.set(cv2.CAP_PROP_POS_FRAMES,int(round((t0-off)*fps)))
    for k in range(int((t1-t0)*fps)):
        ok,fr=cap.read()
        if not ok: break
        k2,d2=orb.detectAndCompute(prep(fr),None)
        if d2 is None or len(k2)<40: continue
        m=bf.match(d1,d2)
        if len(m)<30: continue
        m=sorted(m,key=lambda x:x.distance)[:1200]
        s=np.float32([k2[x.trainIdx].pt for x in m]).reshape(-1,1,2)
        d=np.float32([k1[x.queryIdx].pt for x in m]).reshape(-1,1,2)
        H,mask=cv2.findHomography(s,d,cv2.RANSAC,1.8)
        if H is None or mask.sum()<30: continue
        Hs.append(H); ts.append(t0+k/fps)
cap.release()
np.savez(OUT,H=np.array(Hs),t=np.array(ts),ctx=np.array([CX0,CY0,CX1,CY1]),reft=REFT,cid=CID)
print(f'saved {len(Hs)} homographies -> {OUT}')
