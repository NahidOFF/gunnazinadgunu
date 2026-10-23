#!/usr/bin/env python3
"""cardsweep.py — sweep every 1080p clip for frames in which a jigsaw piece is
BIG and SHARP.

A piece is white paper (high L*, low b*) on tan cardboard (high b*), so the ink
side of the card is found by the same rule findcards.py uses.  For each sampled
frame this records, for the best card-sized blob, its width and the Tenengrad
edge energy inside it; a close-up of a piece is a frame where both are high.

Output: CSV of (clip, frame, video_t, n_cards, best_w, best_sharp, score, cx, cy).
"""
import sys, glob, json, cv2, numpy as np
U='/root/.claude/uploads/84fa90fa-750b-5180-b6a9-f390607e1640'
cm=json.load(open('clipmap.json'))
STEP=int(sys.argv[1]) if len(sys.argv)>1 else 3
rows=[]
for src in sorted(glob.glob(f'{U}/*.mov')):
    cid=src.split('/')[-1][:8]
    cap=cv2.VideoCapture(src)
    W=int(cap.get(cv2.CAP_PROP_FRAME_WIDTH))
    if W<1900: cap.release(); continue
    fps=cap.get(cv2.CAP_PROP_FPS); off=cm.get(cid,{}).get('offset',0.0)
    fn=0; kept=0
    while True:
        ok=cap.grab()
        if not ok: break
        if fn%STEP==0:
            ok,fr=cap.retrieve()
            if ok:
                lab=cv2.cvtColor(fr,cv2.COLOR_BGR2LAB)
                L=lab[:,:,0].astype(np.int16); B=lab[:,:,2].astype(np.int16)-128
                m=((B<14)&(L>138)).astype(np.uint8)
                m=cv2.morphologyEx(m,cv2.MORPH_CLOSE,np.ones((3,3),np.uint8))
                n,lb,st,ce=cv2.connectedComponentsWithStats(m,8)
                best=None; ncard=0
                for k in range(1,n):
                    x,y,w,h,a=st[k]
                    if a<250 or a>60000: continue
                    if not (14<=w<=400 and 14<=h<=400): continue
                    if a/float(w*h)<0.35: continue
                    ncard+=1
                    g=cv2.cvtColor(fr[y:y+h,x:x+w],cv2.COLOR_BGR2GRAY).astype(np.float32)
                    gx=cv2.Sobel(g,cv2.CV_32F,1,0,3); gy=cv2.Sobel(g,cv2.CV_32F,0,1,3)
                    e=np.sqrt(gx*gx+gy*gy)
                    sh=float(np.percentile(e,97))
                    sc=min(w,h)*sh
                    if best is None or sc>best[0]: best=(sc,w,h,sh,int(ce[k][0]),int(ce[k][1]))
                if best:
                    rows.append((cid,fn,round(off+fn/fps,2),ncard,best[1],best[2],
                                 round(best[3],1),round(best[0],1),best[4],best[5]))
                    kept+=1
        fn+=1
    cap.release()
    print(f'{cid}: {fn} frames, {kept} sampled',flush=True)
rows.sort(key=lambda r:-r[7])
with open('CARDSWEEP.csv','w') as f:
    f.write('clip,frame,t,ncard,w,h,sharp,score,cx,cy\n')
    for r in rows: f.write(','.join(str(v) for v in r)+'\n')
print('wrote CARDSWEEP.csv',len(rows))
for r in rows[:40]: print(r)
