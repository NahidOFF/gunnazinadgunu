#!/usr/bin/env python3
"""huematch.py -- match a drawing to emoji by the HUE of its ink, not its shape.

Shape does not transfer: the artist redraws rather than copies (proved on the
eagle, 3.43 elongation against 1.0-1.5 for every vendor).  Hue should transfer,
and for a good reason: a 10-pixel drawing mixes ink with the paper under it, and
mixing with a near-neutral paper drags (a*,b*) toward the origin ALONG A
STRAIGHT LINE.  Magnitude is destroyed; the angle survives.

A drawing is described as a weighted histogram over hue angle, weighted by
chroma so that near-neutral pixels do not vote.  Glyphs are described the same
way, then compared by histogram intersection.

THE CONTROL RUNS FIRST and its result is printed before anything else.  If the
known drawings do not rank their own glyph near the top, the method is discarded
like the twelve before it."""
import cv2,numpy as np,json,glob,sys
IDX=json.load(open('emoji_index.json'))
NB=24
def hist_from(A,B,mask,w=None):
    a=A[mask]; b=B[mask]
    ch=np.hypot(a,b)
    keep=ch>4
    if keep.sum()<20: return None
    ang=(np.degrees(np.arctan2(b[keep],a[keep]))%360)
    h,_=np.histogram(ang,bins=NB,range=(0,360),weights=ch[keep])
    s=h.sum()
    return h/s if s>0 else None
def glyph_hist(path):
    e=cv2.imread(path,cv2.IMREAD_UNCHANGED)
    if e is None or e.shape[0]<32 or e.shape[2]<4: return None
    m=e[:,:,3]>110
    if m.sum()<200: return None
    lab=cv2.cvtColor(e[:,:,:3],cv2.COLOR_BGR2LAB).astype(np.float32)
    return hist_from(lab[:,:,1]-128,lab[:,:,2]-128,m)
def draw_hist(fn,box,Z=18):
    im=cv2.imread(fn).astype(np.float32); x0,y0,x1,y1=box
    c=cv2.resize(im[y0:y1,x0:x1],None,fx=Z,fy=Z,interpolation=cv2.INTER_LANCZOS4)
    g=c.reshape(-1,3); L=g.mean(1); ref=g[L>=np.percentile(L,88)].mean(0)
    c=np.clip(c*(ref.mean()/ref),0,255).astype(np.uint8)
    lab=cv2.cvtColor(c,cv2.COLOR_BGR2LAB).astype(np.float32)
    Lc,A,B=lab[:,:,0],lab[:,:,1]-128,lab[:,:,2]-128
    pap=Lc>=np.percentile(Lc,84); pa,pb=A[pap].mean(),B[pap].mean()
    A=A-pa; B=B-pb
    ink=(np.hypot(A,B)>5)|((Lc[pap].mean()-Lc)>22)
    return hist_from(A,B,ink)
G={}
for f in sorted(glob.glob('tw/*.png')):
    h=glyph_hist(f)
    if h is not None: G[f.split('/')[-1][:-4]]=h
def rank(h,topn=6):
    sc=sorted(((float(np.minimum(h,g).sum()),k) for k,g in G.items()),reverse=True)
    return sc[:topn]
def nm(k): return IDX.get(k,{}).get('name',k)
CONTROL=[('face with tears of joy','1f602','REF803.png',(1528,780,1572,820)),
         ('cloud with snow','1f328','REF803.png',(1806,494,1872,552)),
         ('flag: Oman','1f1f4-1f1f2','REF803.png',(1652,900,1700,944)),
         ('flag: United States','1f1fa-1f1f8','REF803.png',(1798,672,1844,700)),
         ('butterfly','1f98b','REF803.png',(1654,486,1690,514))]
print(f'{len(G)} glyph histograms\n=== CONTROL (identity known) ===')
ok=0
for name,code,fn,box in CONTROL:
    h=draw_hist(fn,box)
    if h is None: print(f'  {name:24s} -> too little chroma to measure'); continue
    top=rank(h)
    pos=[i for i,(s,k) in enumerate(top) if k==code]
    place=f'#{pos[0]+1}' if pos else 'not in top 6'
    ok+= 1 if pos else 0
    print(f'  {name:24s} own glyph {place:12s} | top: '
          +', '.join(f'{nm(k)[:18]}({s:.2f})' for s,k in top[:4]))
print(f'\n  -> {ok} of {len(CONTROL)} controls put their own glyph in the top 6')
print('  -> the method is used below only if that is most of them\n')
if ok >= 3:
    print('=== OPEN DRAWINGS ===')
    for name,fn,box in [('3  black silhouette','REF803.png',(1700,926,1732,974)),
                        ('6R right object','REF803.png',(1699,717,1717,773)),
                        ('7  terracotta rect','REF803.png',(1698,484,1734,536)),
                        ('14L lump','REF803.png',(1515,823,1539,871)),
                        ('15 dark form','REF_OFFICE.png',(1662,848,1690,882))]:
        h=draw_hist(fn,box)
        if h is None: print(f'  {name:22s} -> too little chroma'); continue
        print(f'  {name:22s} '+', '.join(f'{nm(k)[:20]}({s:.2f})' for s,k in rank(h,8)))
else:
    print('CONTROL FAILED -- method discarded, no results reported.')
