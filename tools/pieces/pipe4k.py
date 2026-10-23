#!/usr/bin/env python3
"""One-shot pipeline for a NEW (ideally 2160p) clip of the box-stack shot.

  pipe4k.py CLIPID T0 T1 [OUTDIR]

1. picks the sharpest frame in [T0,T1] as the reference
2. builds an ORB+RANSAC homography cache over the whole shot
3. auto-detects every jigsaw-piece outline in the reference frame
4. runs masked-median super-resolution per piece
5. writes an atlas: each piece, plus its numerals contrast-stretched

Assumes clipmap.json already has the clip's offset (add it first if new).
"""
import sys, os, json, glob, subprocess, cv2, numpy as np
cid, t0, t1 = sys.argv[1], float(sys.argv[2]), float(sys.argv[3])
OUT = sys.argv[4] if len(sys.argv) > 4 else f'p4k_{cid}'
os.makedirs(OUT, exist_ok=True)
cm = json.load(open('clipmap.json')); off = cm[cid]['offset']
src = glob.glob(f'/root/.claude/uploads/*/{cid}-*')[0]

# --- 1. sharpest reference frame ------------------------------------------
cap = cv2.VideoCapture(src); cap.set(cv2.CAP_PROP_POS_MSEC, (t0-off)*1000)
best = (-1, None, None)
while True:
    ok, fr = cap.read()
    if not ok: break
    lt = cap.get(cv2.CAP_PROP_POS_MSEC)/1000.0
    if lt+off > t1: break
    g = cv2.cvtColor(fr, cv2.COLOR_BGR2GRAY)
    v = cv2.Laplacian(g, cv2.CV_64F).var()
    if v > best[0]: best = (v, lt+off, fr.copy())
cap.release()
sharp, reft, ref = best
H, W = ref.shape[:2]
cv2.imwrite(f'{OUT}/ref.png', ref)
print(f'reference t={reft:.3f} lapvar={sharp:.1f} size={W}x{H}', flush=True)

# --- 2. homography cache ---------------------------------------------------
cache = f'{OUT}/h.npz'
ctx = f'{int(W*0.55)},{int(H*0.2)},{W},{H}'      # right-hand side: the box stack
subprocess.run([sys.executable,'homo.py',cid,f'{reft:.3f}',cache,
                '--range',f'{t0:.2f}:{t1:.2f}'] + ctx.split(','), check=True)

# --- 3. auto-detect piece outlines ----------------------------------------
cx0,cy0,cx1,cy1 = [int(v) for v in ctx.split(',')]
sub = ref[cy0:cy1, cx0:cx1]
lab = cv2.cvtColor(sub, cv2.COLOR_BGR2LAB)
L = lab[:,:,0].astype(np.int16); B = lab[:,:,2].astype(np.int16)-128
m = ((B < 16) & (L > 135)).astype(np.uint8)
m = cv2.morphologyEx(m, cv2.MORPH_CLOSE, np.ones((3,3), np.uint8))
n, lb, st, ce = cv2.connectedComponentsWithStats(m, 8)
scale = (W*H)/(1920*1080)                                    # area scales with resolution
regions = {}
for k in range(1, n):
    x,y,w,h,a = st[k]
    if not (500*scale < a < 40000*scale): continue
    if min(w,h) < 12: continue
    pad = int(8*np.sqrt(scale))
    x0,y0 = max(0,x-pad)+cx0, max(0,y-pad)+cy0
    x1,y1 = min(sub.shape[1],x+w+pad)+cx0, min(sub.shape[0],y+h+pad)+cy0
    s = max(4, int(round(900/max(x1-x0, y1-y0))))            # ~900 px on the long side
    regions[f"P{len(regions):02d}_x{x0}_y{y0}"] = [int(x0),int(y0),int(x1),int(y1),int(s)]
json.dump(regions, open(f'{OUT}/regions.json','w'), indent=1)
print(f'{len(regions)} piece candidates', flush=True)

# --- 4. super-resolve each -------------------------------------------------
subprocess.run([sys.executable,'warpreg.py',cache,f'{OUT}/regions.json',f'{OUT}/sr',
                '--minvalid','0.5'], check=True)

# --- 5. atlas --------------------------------------------------------------
tiles = []
for f in sorted(glob.glob(f'{OUT}/sr/*.png')):
    im = cv2.imread(f)
    a = im.astype(np.float32); lo,hi = np.percentile(a,2), np.percentile(a,98)
    st_ = np.clip((a-lo)*255/max(hi-lo,1),0,255).astype(np.uint8)
    both = np.hstack([im, st_])
    both = cv2.resize(both, (int(560*both.shape[1]/both.shape[0]), 560))
    both = cv2.copyMakeBorder(both, 30, 6, 6, 12, cv2.BORDER_CONSTANT, value=(255,255,255))
    cv2.putText(both, os.path.basename(f)[:-4], (6, 22), 0, 0.7, (0,0,255), 2)
    tiles.append(both)
if tiles:
    rows = [np.hstack(tiles[i:i+3]) for i in range(0, len(tiles), 3)]
    wmax = max(r.shape[1] for r in rows)
    rows = [np.pad(r, ((0,0),(0,wmax-r.shape[1]),(0,0)), constant_values=255) for r in rows]
    cv2.imwrite(f'{OUT}/ATLAS.png', np.vstack(rows))
    print(f'wrote {OUT}/ATLAS.png', flush=True)
