#!/usr/bin/env python3
"""profcmp.py -- measure candidate emoji the SAME way the drawings were measured:
silhouette, long axis, width at each 10% of depth, elongation, solidity.

Then compare numbers, not impressions.  The test is only worth anything if the
candidates SEPARATE: if every candidate's profile looks alike at this scale the
measurement carries no information and is discarded, like the eleven similarity
measures before it.  That check is printed first."""
import sys,cv2,numpy as np
NAME={'1f3a4':'microphone','1f574':'suit levit','1f5ff':'moai','1f302':'umbrella closed',
 '1f987':'bat','1f9ea':'test tube','1f58a':'pen','1f97e':'hiking boot','1f426':'bird',
 '1f511':'key','1f4a1':'light bulb','1f9e6':'socks','1f3b8':'guitar','1f955':'carrot',
 '1f336':'hot pepper','1f9b7':'tooth','1f343':'leaf','1fab6':'feather','1f52a':'knife',
 '1f9c5':'onion','1f525':'fire','1f6a9':'flag triangular','1f360':'sweet potato',
 '1fab5':'wood','1f330':'chestnut','1faa8':'rock','1f346':'eggplant','1f95c':'peanuts',
 '1f36f':'honey pot','1f956':'baguette','1f954':'potato'}
def profile(mask,nbins=10):
    ys,xs=np.nonzero(mask)
    p=np.stack([xs,ys]).astype(np.float64); mu=p.mean(1,keepdims=True)
    w,v=np.linalg.eigh(np.cov(p-mu)); ax=v[:,1]; perp=v[:,0]
    t=(p-mu).T@ax; d=(p-mu).T@perp
    if t[np.argmax(np.abs(t))]<0: t=-t                 #長 axis points one way
    L=t.max()-t.min()
    ws=[]
    for i in range(nbins):
        a=t.min()+L*i/nbins; b=t.min()+L*(i+1)/nbins
        m=(t>=a)&(t<b)
        ws.append((d[m].max()-d[m].min()) if m.sum()>3 else 0.0)
    W=max(ws) or 1
    cn,_=cv2.findContours(mask.astype(np.uint8),cv2.RETR_EXTERNAL,cv2.CHAIN_APPROX_SIMPLE)
    c=max(cn,key=cv2.contourArea); sol=cv2.contourArea(c)/max(cv2.contourArea(cv2.convexHull(c)),1)
    return L,W,sol,[w/W for w in ws]
def emo_mask(code,H=32):
    e=cv2.imread(f'emo/{code}.png',cv2.IMREAD_UNCHANGED)
    if e is None: return None
    a=e[:,:,3]>110
    # Several glyphs carry detached decoration (the microphone's music notes,
    # the leaf's motion lines).  Those are not part of the object's silhouette
    # and they wrecked the elongation on the first run, so keep only the main body.
    n,lb,st,_=cv2.connectedComponentsWithStats(a.astype(np.uint8),8)
    if n>2: a=(lb==1+int(np.argmax(st[1:,4])))
    ys,xs=np.nonzero(a)
    a=a[ys.min():ys.max()+1, xs.min():xs.max()+1]
    s=H/a.shape[0]
    a=cv2.resize(a.astype(np.uint8)*255,(max(2,int(a.shape[1]*s)),H),interpolation=cv2.INTER_AREA)
    return a>110
TARGET=sys.argv[1]                       # 'shape3' or 'shape15'
SPEC={'shape3':  dict(elong=2.92, w=[None,None,1.00,None,0.68,None,0.84,None,None,0.33],
                      sol=0.82, note='card 3: elong 2.87-2.98, widths 30%=10.6 45%=7.2 65%=8.9 95%=3.5, max=H/3'),
      'shape15': dict(elong=2.36, w=[None]*10, sol=0.91,
                      note='card 15: elong 2.36, solidity 0.91, widest at 20%, monotone taper')}[TARGET]
print(SPEC['note']); print()
cands=sys.argv[2:]
rows=[]
for c in cands:
    m=emo_mask(c)
    if m is None: print('missing',c); continue
    L,W,sol,ws=profile(m)
    rows.append((NAME.get(c,c),L/W,sol,ws))
print(f'{"candidate":18s} {"elong":>6s} {"solid":>6s}  width at 5,15,...,95% of depth (1.00 = widest)')
for n,e,s,ws in rows:
    print(f'{n:18s} {e:6.2f} {s:6.2f}  '+' '.join(f'{w:4.2f}' for w in ws))
# does the measurement separate the candidates at all?
M=np.array([r[3] for r in rows])
spread=np.mean(np.std(M,axis=0))
print(f'\nseparation check: mean spread across candidates = {spread:.3f}')
print('  (below ~0.08 the profiles are alike at this scale and the test says nothing)')
