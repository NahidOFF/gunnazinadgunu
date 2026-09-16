#!/usr/bin/env python3
"""numread.py FRAME x0,y0,x1,y1 LABEL -- read both Roman numerals on one card by
TWO independent measurements, and say whether they agree.

  (a) BLOB WIDTHS.  Each letter is usually its own ink blob: an I is ~3.5 native
      px wide, a V or X ~10.  Counting blobs and their widths gives a reading.
  (b) STROKE SIGNATURE.  Peaks crossing the top / middle / bottom of the group's
      bounding box: I=1/1/1, V=2/2/1, X=2/1/2.  Summing gives a second reading.

Neither is trusted alone.  Where they disagree the card is reported UNRESOLVED
rather than given a value -- that is the whole point of running two of them."""
import sys,cv2,numpy as np
fn=sys.argv[1]; x0,y0,x1,y1=[int(v) for v in sys.argv[2].split(',')]; tag=sys.argv[3]
Z=8
LET={'I':(1,1,1),'V':(2,2,1),'X':(2,1,2)}
ROMAN=['I','II','III','IV','V','VI','VII','VIII','IX','X','XI','XII','XIII',
       'XIV','XV','XVI','XVII','XVIII','XIX','XX']
def sig(w):
    t=m=b=0
    for ch in w:
        a,c,d=LET[ch]; t+=a; m+=c; b+=d
    return (t,m,b)

im=cv2.imread(fn).astype(np.float32)
def prep(sub,z):
    c=cv2.resize(sub,None,fx=z,fy=z,interpolation=cv2.INTER_LANCZOS4)
    g=c.reshape(-1,3); L=g.mean(1); ref=g[L>=np.percentile(L,85)].mean(0)
    return np.clip(c*(ref.mean()/ref),0,255).astype(np.uint8)
c=prep(im[y0:y1,x0:x1],Z)
lab=cv2.cvtColor(c,cv2.COLOR_BGR2LAB).astype(np.float32)
Lc,A,B=lab[:,:,0],lab[:,:,1]-128,lab[:,:,2]-128
pap=Lc>=np.percentile(Lc,80)
dA,dB,dL=A-A[pap].mean(),B-B[pap].mean(),Lc[pap].mean()-Lc
ink=(dL>14)|(np.abs(dA)>7)|(np.abs(dB)>9)
ink=cv2.morphologyEx(ink.astype(np.uint8),cv2.MORPH_OPEN,np.ones((Z//2,Z//2),np.uint8))
n,lb,st,_=cv2.connectedComponentsWithStats(ink,8)
CH=y1-y0
blobs=[]
for i in range(1,n):
    x,y,w,h,a=[v/Z for v in st[i][:4]]+[st[i][4]/Z/Z]
    if not (0.09*CH <= h <= 0.30*CH): continue      # numeral-height only
    if h/max(w,.1) < 1.05 or a > 130: continue      # thin & small only
    m=lb==i; da,db=dA[m].mean(),dB[m].mean()
    col='RED' if (da>2.5 and db<7) else ('BLUE' if (db<-4 and da<3) else None)
    if col: blobs.append((col,x,y,w,h))
print(f'== {tag}')
def peaks(d,a,b,z):
    p=d[int(a):int(b)].mean(0); gap=max(3,z//2)
    p=np.convolve(p,np.ones(max(3,z//3))/max(3,z//3),'same')
    out=[]
    for i in range(gap,len(p)-gap):
        if p[i]==max(p[i-gap:i+gap+1]) and p[i]>0.42*p.max():
            if not out or i-out[-1]>gap: out.append(i)
    return out
for col in ('RED','BLUE'):
    bs=sorted([b for b in blobs if b[0]==col],key=lambda t:t[1])
    if not bs: print(f'   {col:4s}: no numeral blobs found'); continue
    ys=np.median([b[2] for b in bs])
    bs=[b for b in bs if abs(b[2]-ys)<0.09*CH]        # keep one y-band
    widths=[round(b[3],1) for b in bs]
    thin=np.median([w for w in widths if w<6]) if any(w<6 for w in widths) else 3.5
    guess=''.join('I'*max(1,round(w/thin)) if w<thin*1.9 else '?' for w in widths)
    bx0=min(b[1] for b in bs)-1; bx1=max(b[1]+b[3] for b in bs)+1
    by0=min(b[2] for b in bs)-1; by1=max(b[2]+b[4] for b in bs)+1
    # (b) stroke signature over the group box, at high zoom
    ZZ=14
    cc=prep(im[y0+int(by0):y0+int(by1)+1, x0+int(bx0):x0+int(bx1)+1],ZZ)
    gr=cv2.cvtColor(cc,cv2.COLOR_BGR2GRAY).astype(np.float32)
    d=255-gr; d-=np.percentile(d,10); d=np.clip(d,0,None); H=d.shape[0]
    T=peaks(d,H*0.08,H*0.36,ZZ); M=peaks(d,H*0.40,H*0.60,ZZ); Bo=peaks(d,H*0.64,H*0.92,ZZ)
    obs=(len(T),len(M),len(Bo))
    cand=[r for r in ROMAN if sig(r)==obs]
    order=''
    if len(cand)>1:
        Tn=[t/ZZ for t in T]; kinds=['I' if min(abs(x/ZZ-t) for t in Tn)<=1.2 else 'W' for x in Bo]
        order=' order='+''.join(kinds)
    # combine: blobs give which slots are I and which are wide (V or X);
    # the mid-band count then splits wide into V vs X, since
    #   MID = n_I + 2*n_V + n_X  and  n_V+n_X = k  =>  n_V = MID - n_I - k
    slots=['I' if w < thin*1.9 else 'W' for w in widths]
    nI,k=slots.count('I'),slots.count('W')
    nV=len(M)-nI-k; nX=k-nV
    ok_top = (len(T)==nI+2*k)
    if 0<=nV<=k and ok_top:
        wide=['V']*nV+['X']*nX
        # a V before an I reads VI..; an X sits before smaller letters, so the
        # left-to-right slot order is taken as printed and V/X assigned in order
        read=''.join(wide.pop(0) if s=='W' else 'I' for s in slots)
        verdict = read if read in ROMAN else f'{read} (not a standard numeral)'
    else:
        verdict='UNRESOLVED (blob count and stroke profile disagree)'
    wtxt='['+', '.join(f'{w:.1f}' for w in widths)+']'
    print(f'   {col:4s}: {len(bs)} blob(s) w={wtxt} -> box '
          f'x={x0+bx0:.0f}..{x0+bx1:.0f} y={y0+by0:.0f}..{y0+by1:.0f}')
    print(f'         (a) slots {"".join(slots)}   (b) peaks {obs[0]}/{obs[1]}/{obs[2]}'
          f' -> {cand or "-"}{order}')
    print(f'         READ: {verdict}')
