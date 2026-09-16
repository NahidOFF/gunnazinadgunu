#!/usr/bin/env python3
"""Each piece's outline, rotated onto its own principal axis, drawn side by side.

The pieces chain left-to-right: a sawtooth left edge and a rounded right bulge.
If the teeth differ from piece to piece the chain order can be recovered from
shape alone, independently of the dates. This draws what it measures so the
mask can be checked by eye.
"""
import cv2,numpy as np
CARDS=[
 ('1','REF767.png',(1240,45,1300,140)),
 ('4','REF767.png',(1246,140,1316,215)),
 ('10','REF767.png',(1296,32,1390,130)),
 ('13','REF767.png',(1258,40,1316,112)),
 ('3','REF803.png',(1682,900,1766,996)),
 ('5','REF803.png',(1612,878,1706,972)),
 ('9','REF803.png',(1776,630,1912,736)),
 ('11','REF803.png',(1792,474,1912,578)),
 ('12','REF803.png',(1498,762,1606,848)),
 ('14','REF803.png',(1488,800,1606,906)),
 ('6','REF806.png',(1774,650,1826,732)),
]
def cardmask(sub):
    lab=cv2.cvtColor(sub,cv2.COLOR_BGR2LAB)
    L=lab[:,:,0].astype(np.int16); B=lab[:,:,2].astype(np.int16)-128
    m=((B<16)&(L>132)).astype(np.uint8)
    m=cv2.morphologyEx(m,cv2.MORPH_CLOSE,np.ones((3,3),np.uint8))
    n,lb,st,ce=cv2.connectedComponentsWithStats(m,8)
    if n<2: return None
    h,w=sub.shape[:2]; cx,cy=w/2,h/2
    best=None
    for k in range(1,n):
        x,y,ww,hh,a=st[k]
        if a<150: continue
        d=np.hypot(ce[k][0]-cx,ce[k][1]-cy)
        sc=a/(1+d)
        if best is None or sc>best[0]: best=(sc,k)
    if best is None: return None
    return (lb==best[1]).astype(np.uint8)*255
tiles=[]
for name,path,box in CARDS:
    im=cv2.imread(path)
    if im is None: continue
    x0,y0,x1,y1=box
    h,w=im.shape[:2]; x1=min(x1,w); y1=min(y1,h)
    sub=im[y0:y1,x0:x1]
    m=cardmask(sub)
    if m is None: print('no mask',name); continue
    cnts,_=cv2.findContours(m,cv2.RETR_EXTERNAL,cv2.CHAIN_APPROX_NONE)
    c=max(cnts,key=cv2.contourArea)
    rect=cv2.minAreaRect(c); ang=rect[2]
    if rect[1][0]<rect[1][1]: ang+=90
    M=cv2.getRotationMatrix2D((m.shape[1]/2,m.shape[0]/2),ang,1.0)
    D=int(max(m.shape)*1.6)
    M[0,2]+=D/2-m.shape[1]/2; M[1,2]+=D/2-m.shape[0]/2
    rm=cv2.warpAffine(m,M,(D,D),flags=cv2.INTER_NEAREST)
    rs=cv2.warpAffine(sub,M,(D,D),flags=cv2.INTER_CUBIC)
    ys,xs=np.where(rm>0)
    if len(xs)<20: continue
    pad=3
    rm=rm[max(0,ys.min()-pad):ys.max()+pad,max(0,xs.min()-pad):xs.max()+pad]
    rs=rs[max(0,ys.min()-pad):ys.max()+pad,max(0,xs.min()-pad):xs.max()+pad]
    Z=max(1,int(360/max(rm.shape)))
    big=cv2.resize(rs,(rm.shape[1]*Z,rm.shape[0]*Z),interpolation=cv2.INTER_LANCZOS4)
    bm=cv2.resize(rm,(rm.shape[1]*Z,rm.shape[0]*Z),interpolation=cv2.INTER_NEAREST)
    ov=big.copy()
    cn,_=cv2.findContours(bm,cv2.RETR_EXTERNAL,cv2.CHAIN_APPROX_NONE)
    cv2.drawContours(ov,cn,-1,(0,0,255),2)
    # per-row left/right extents = the two edge profiles
    prof=np.full((bm.shape[0],260,3),255,np.uint8)
    Hh=bm.shape[0]
    lefts=[];rights=[]
    for r in range(Hh):
        xs2=np.where(bm[r]>0)[0]
        if len(xs2)==0: lefts.append(np.nan); rights.append(np.nan); continue
        lefts.append(xs2.min()); rights.append(xs2.max())
    lf=np.array(lefts,dtype=float); rt=np.array(rights,dtype=float)
    def draw(arr,col,off):
        v=arr-np.nanmin(arr)
        v=v/max(np.nanmax(v),1)*110
        for r in range(1,Hh):
            if np.isnan(v[r]) or np.isnan(v[r-1]): continue
            cv2.line(prof,(off+int(v[r-1]),r-1),(off+int(v[r]),r),col,2)
    draw(lf,(180,0,0),10); draw(rt,(0,120,0),135)
    cv2.putText(prof,'sol',(10,18),0,0.5,(180,0,0),1,cv2.LINE_AA)
    cv2.putText(prof,'sag',(135,18),0,0.5,(0,120,0),1,cv2.LINE_AA)
    hgt=max(ov.shape[0],prof.shape[0])
    def padto(a,H):
        if a.shape[0]>=H: return a[:H]
        return np.vstack([a,np.full((H-a.shape[0],a.shape[1],3),255,np.uint8)])
    row=np.hstack([padto(ov,hgt),np.full((hgt,8,3),255,np.uint8),padto(prof,hgt)])
    tile=np.full((hgt+34,row.shape[1],3),255,np.uint8); tile[34:]=row
    cv2.putText(tile,f'kart {name}   {rm.shape[1]}x{rm.shape[0]} px',(6,24),0,0.62,(0,0,180),2,cv2.LINE_AA)
    tiles.append(tile)
    print(f'kart {name}: mask {rm.shape[1]}x{rm.shape[0]}  area {int((rm>0).sum())}')
W=max(t.shape[1] for t in tiles); Hm=max(t.shape[0] for t in tiles)
tiles=[np.pad(t,((0,Hm-t.shape[0]),(0,W-t.shape[1]),(0,0)),constant_values=255) for t in tiles]
rows=[np.hstack(tiles[i:i+4]) for i in range(0,len(tiles),4)]
Wm=max(r.shape[1] for r in rows)
rows=[np.pad(r,((0,0),(0,Wm-r.shape[1]),(0,0)),constant_values=255) for r in rows]
out=np.vstack(rows)
hdr=np.full((52,out.shape[1],3),255,np.uint8)
cv2.putText(hdr,'PARCA KONTURLARI - oz oxuna dondurulub. Qirmizi = olculen maska. Sagda: sol/sag kenar profili.',
            (10,36),0,0.8,(0,0,0),2,cv2.LINE_AA)
cv2.imwrite('TABS.png',np.vstack([hdr,out])); print('wrote TABS.png',out.shape)
