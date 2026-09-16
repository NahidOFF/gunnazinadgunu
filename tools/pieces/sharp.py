#!/usr/bin/env python3
"""sharp.py CLIP T0 T1 x0,y0,x1,y1 OUTDIR [N] [SCALE]
Decode frames in [T0,T1] (global secs), crop region, rank by Laplacian variance,
write top-N upscaled crops + a montage."""
import sys, os, json, cv2, numpy as np
cid,t0,t1,box,outd = sys.argv[1],float(sys.argv[2]),float(sys.argv[3]),sys.argv[4],sys.argv[5]
N   = int(sys.argv[6]) if len(sys.argv)>6 else 6
SC  = int(sys.argv[7]) if len(sys.argv)>7 else 8
cm  = json.load(open('clipmap.json')); off = cm[cid]['offset']
import glob
path = glob.glob(f'/root/.claude/uploads/*/{cid}-*')[0]
x0,y0,x1,y1 = [int(v) for v in box.split(',')]
cap = cv2.VideoCapture(path)
fps = cap.get(cv2.CAP_PROP_FPS)
l0,l1 = t0-off, t1-off
cap.set(cv2.CAP_PROP_POS_MSEC, max(0,l0-0.2)*1000)
rows=[]
while True:
    ok,fr = cap.read()
    if not ok: break
    lt = cap.get(cv2.CAP_PROP_POS_MSEC)/1000.0
    if lt > l1: break
    if lt < l0: continue
    c = fr[y0:y1, x0:x1]
    if c.size==0: continue
    g = cv2.cvtColor(c, cv2.COLOR_BGR2GRAY)
    v = cv2.Laplacian(g, cv2.CV_64F).var()
    rows.append((v, lt+off, c.copy()))
cap.release()
rows.sort(key=lambda r:-r[0])
os.makedirs(outd, exist_ok=True)
sel = rows[:N]
print(f'{len(rows)} frames scanned; sharpness top{N}:')
tiles=[]
for i,(v,gt,c) in enumerate(sel):
    print(f'  #{i} t={gt:.3f} lapvar={v:.1f}')
    up = cv2.resize(c, None, fx=SC, fy=SC, interpolation=cv2.INTER_LANCZOS4)
    cv2.imwrite(f'{outd}/s{i}_t{gt:.2f}.png', up)
    tiles.append(up)
if tiles:
    h = max(t.shape[0] for t in tiles)
    tiles = [cv2.copyMakeBorder(t,0,h-t.shape[0],0,8,cv2.BORDER_CONSTANT,value=(0,255,0)) for t in tiles]
    cv2.imwrite(f'{outd}/montage.png', np.hstack(tiles))
    print(f'wrote {outd}/montage.png  {np.hstack(tiles).shape}')
