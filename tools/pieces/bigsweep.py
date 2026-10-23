#!/usr/bin/env python3
"""bigsweep.py -- measure the whole Twemoji set (1326 glyphs, every Object, Food,
Animal, Place, Symbol, Activity and Flag) exactly as the drawings were measured,
then report which survive each drawing's constraints.

Only pose-invariant quantities are used as hard filters -- solidity, the shape of
the width profile, and colour -- because the cards are tilted and elongation is
not preserved.  Elongation is printed as context.

The point is exclusion.  A drawing with nothing left is as useful a result as one
with a single survivor, and more honest than a ranked list of near-misses."""
import glob,cv2,numpy as np,json,sys
IDX=json.load(open('emoji_index.json'))
def measure(path):
    e=cv2.imread(path,cv2.IMREAD_UNCHANGED)
    if e is None or e.shape[0]<32 or e.shape[2]<4: return None
    a=e[:,:,3]>110
    if a.sum()<200: return None
    n,lb,st,_=cv2.connectedComponentsWithStats(a.astype(np.uint8),8)
    if n>2: a=(lb==1+int(np.argmax(st[1:,4])))
    if a.sum()<200: return None
    ys,xs=np.nonzero(a)
    p=np.stack([xs,ys]).astype(np.float64); mu=p.mean(1,keepdims=True)
    w,v=np.linalg.eigh(np.cov(p-mu)); ax=v[:,1]; perp=v[:,0]
    t=(p-mu).T@ax; d=(p-mu).T@perp
    L=t.max()-t.min()
    ws=[]
    for i in range(10):
        m=(t>=t.min()+L*i/10)&(t<t.min()+L*(i+1)/10)
        ws.append((d[m].max()-d[m].min()) if m.sum()>3 else 0.0)
    W=max(ws) or 1.0
    cn,_=cv2.findContours(a.astype(np.uint8),cv2.RETR_EXTERNAL,cv2.CHAIN_APPROX_SIMPLE)
    c=max(cn,key=cv2.contourArea)
    sol=cv2.contourArea(c)/max(cv2.contourArea(cv2.convexHull(c)),1)
    lab=cv2.cvtColor(e[:,:,:3],cv2.COLOR_BGR2LAB).astype(np.float32)
    A=lab[:,:,1]-128; B=lab[:,:,2]-128
    def band(f0,f1):
        m=(t>=t.min()+L*f0)&(t<t.min()+L*f1)
        idx=(ys[m],xs[m])
        return (float(A[idx].mean()),float(B[idx].mean())) if m.sum()>20 else (0.,0.)
    Lm=lab[:,:,0]
    return dict(L=L,W=W,elong=L/W,sol=sol,ws=[x/W for x in ws],
                a=float(A[a].mean()),b=float(B[a].mean()),Lm=float(Lm[a].mean()),
                e1=band(0,.18),mid=band(.35,.65),e2=band(.82,1.0))
M={}
for f in sorted(glob.glob('tw/*.png')):
    r=measure(f)
    if r: M[f.split('/')[-1][:-4]]=r
print(f'measured {len(M)} glyphs\n')
def nm(k): return IDX.get(k,{}).get('name',k)
def show(title,keys,extra=lambda k:''):
    print(f'--- {title}: {len(keys)} survive')
    for k in keys[:12]:
        m=M[k]
        print(f'    {nm(k)[:34]:34s} elong {m["elong"]:4.2f} sol {m["sol"]:4.2f} '
              f'a* {m["a"]:+5.1f} b* {m["b"]:+5.1f} {extra(k)}')
    if not keys: print('    (none)')
    print()
# --- card 3: neutral black, solidity ~0.82, bulge-waist-bulge-taper
def bwb(ws):
    for o in (ws,ws[::-1]):
        if o[2]>0.85 and o[4]<o[2]-0.12 and o[6]>o[4]+0.10 and o[9]<0.55: return True
    return False
k3=[k for k,m in M.items() if abs(m['a'])<6 and abs(m['b'])<6 and m['L']/m['W']>2.0
    and 0.74<=m['sol']<=0.90 and bwb(m['ws'])]
show('CARD 3  neutral black, elong>2, solidity 0.74-0.90, bulge-waist-bulge-taper',
     sorted(k3,key=lambda k:abs(M[k]['sol']-0.82)))
# how much of that filter is the bulge-waist-bulge feature doing?  Report the set
# without it, so a single survivor is not mistaken for a strong result.
k3b=[k for k,m in M.items() if abs(m['a'])<6 and abs(m['b'])<6 and m['Lm']<130
     and m['L']/m['W']>2.0 and 0.74<=m['sol']<=0.90]
show('CARD 3  same but WITHOUT the bulge-waist-bulge requirement (and dark)',
     sorted(k3b,key=lambda k:abs(M[k]['sol']-0.82)))
# --- card 6 right: red at both ends, cool middle
# The first pass let through glyphs whose middle was merely LESS warm than their
# ends.  The drawing's middle is genuinely cool (b* -7 against its paper), so the
# filter now demands that, not a relative difference.
k6=[k for k,m in M.items() if m['L']/m['W']>2.0 and
    min(m['e1'][0],m['e2'][0])>6 and m['mid'][1]<2 and m['mid'][0]<6]
show('CARD 6R  long-thin, a*>+6 at BOTH ends, middle GENUINELY cool (b*<+2)', sorted(k6),
     lambda k: f'ends a* {M[k]["e1"][0]:+.0f}/{M[k]["e2"][0]:+.0f} mid b* {M[k]["mid"][1]:+.0f}')
# --- card 7: flat uniform warm rectangle
k7=[k for k,m in M.items() if m['sol']>=0.95 and min(m['ws'][1:9])>0.88
    and m['a']>10 and m['b']>8 and 1.4<m['elong']<3.2]
show('CARD 7  near-rectangular, uniform width, warm (a*>10,b*>8), elong 1.4-3.2',
     sorted(k7,key=lambda k:abs(M[k]['elong']-2.14)))
# --- card 14L: very convex, straight, warm with a lighter patch
k14=[k for k,m in M.items() if m['sol']>=0.95 and m['a']>4 and m['b']>6 and m['elong']>1.8]
show('CARD 14L  solidity>=0.95, warm (a*>4,b*>6), elong>1.8',
     sorted(k14,key=lambda k:-M[k]['sol']))
# --- card 15: dark near-neutral, solidity ~0.91, widest near one end then monotone
def front(ws):
    for o in (ws,ws[::-1]):
        i=int(np.argmax(o))
        if i<=3 and all(b<=a+0.05 for a,b in zip(o[i:],o[i+1:])) and o[-1]<0.6: return True
    return False
# The drawing is 76 L below its paper -- it is DARK.  The first pass returned
# clouds, which are near-neutral but light, because lightness was not filtered.
k15=[k for k,m in M.items() if abs(m['a'])<7 and abs(m['b'])<8 and m['Lm']<130
     and 0.86<=m['sol']<=0.96 and m['elong']>1.8 and front(m['ws'])]
show('CARD 15  near-neutral AND DARK (L<130), solidity 0.86-0.96, elong>1.8, front-loaded taper',
     sorted(k15,key=lambda k:abs(M[k]['sol']-0.91)))
