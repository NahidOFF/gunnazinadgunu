#!/usr/bin/env python3
"""axisband.py -- rank glyphs against a drawing measured as colour bands ALONG the
object's own long axis.

The first attempt used image rows and a bounding-box aspect filter, which threw
away the rocket, the syringe, the pen and the thermometer: Twemoji draws those
diagonally, so their bounding box is nearly square even though the object is
long and thin.  Rotating each glyph onto its principal axis first fixes that.

Both ends and the middle are reported so the ranking can be judged, and the
drawing's own numbers are printed beside them."""
import glob,cv2,numpy as np,sys
NAMES={'1f680':'rocket','1f321':'thermometer','1f489':'syringe','1f9f7':'safety pin',
 '1f58c':'paintbrush','1f4cf':'straight ruler','1f9e8':'firecracker','1f56f':'candle',
 '1f9ef':'fire extinguisher','1f52b':'water pistol','1f9f4':'lotion','1f9ec':'dna',
 '270f':'pencil','1f58b':'fountain pen','1f5dd':'old key','1f9c3':'beverage box',
 '1f58a':'pen','1f58d':'crayon','1f9ea':'test tube','1f956':'baguette','1f9cb':'bubble tea',
 '1f37a':'beer','1f376':'sake','1f9c1':'cupcake','1f37f':'popcorn','1f346':'eggplant',
 '1f952':'cucumber','1f32d':'hot dog','1f3a4':'microphone','1f302':'umbrella closed',
 '1f45f':'running shoe','1f37c':'baby bottle','1f9e6':'socks','1f955':'carrot',
 '1f336':'hot pepper','1fab6':'feather','1f52a':'knife','1f9b7':'tooth','1f9f2':'magnet',
 '1f527':'wrench','1f529':'nut and bolt','1f4cc':'pushpin','1f4ce':'paperclip',
 '1f3b7':'saxophone','1f3ba':'trumpet','1faa5':'toothbrush','1f9f9':'broom','1f5bc':'framed pic'}
TGT={'end1':(9.9,-1.6),'mid':(2.0,-7.0),'end2':(9.4,-3.2)}
rows=[]
for f in sorted(glob.glob('emo/*.png')):
    e=cv2.imread(f,cv2.IMREAD_UNCHANGED)
    if e is None or e.shape[2]<4: continue
    a=(e[:,:,3]>110)
    if a.sum()<200: continue
    n,lb,st,_=cv2.connectedComponentsWithStats(a.astype(np.uint8),8)
    if n>2: a=(lb==1+int(np.argmax(st[1:,4])))
    ys,xs=np.nonzero(a)
    p=np.stack([xs,ys]).astype(np.float64); mu=p.mean(1,keepdims=True)
    w,v=np.linalg.eigh(np.cov(p-mu)); ax=v[:,1]
    ang=np.degrees(np.arctan2(ax[1],ax[0]))
    M=cv2.getRotationMatrix2D((float(mu[0,0]),float(mu[1,0])),ang-90,1.0)
    R=cv2.warpAffine(e,M,(e.shape[1],e.shape[0]),flags=cv2.INTER_NEAREST)
    am=R[:,:,3]>110
    n,lb,st,_=cv2.connectedComponentsWithStats(am.astype(np.uint8),8)
    if n>2: am=(lb==1+int(np.argmax(st[1:,4])))
    if am.sum()<150: continue
    ys,xs=np.nonzero(am)
    am=am[ys.min():ys.max()+1, xs.min():xs.max()+1]
    sub=R[ys.min():ys.max()+1, xs.min():xs.max()+1]
    H,W=am.shape
    if H<W*1.5: continue                       # now a REAL aspect, after rotation
    lab=cv2.cvtColor(sub[:,:,:3],cv2.COLOR_BGR2LAB).astype(np.float32)
    A=lab[:,:,1]-128; B=lab[:,:,2]-128
    def band(y0,y1):
        m=am.copy(); m[:y0]=False; m[y1:]=False
        return (float(A[m].mean()),float(B[m].mean())) if m.sum()>20 else (0.,0.)
    t=band(0,int(H*0.18)); mid=band(int(H*0.35),int(H*0.65)); b=band(int(H*0.82),H)
    # the drawing has no known "up", so score both ways round and keep the better
    def dist(o):
        return sum(abs(o[i][0]-g[0])+abs(o[i][1]-g[1])
                   for i,g in enumerate([TGT['end1'],TGT['mid'],TGT['end2']]))/3
    d=min(dist([t,mid,b]),dist([b,mid,t]))
    rows.append((d,f.split('/')[-1][:-4],H/W,t,mid,b))
rows.sort()
print(f'{len(rows)} glyphs are genuinely long and thin once rotated onto their own axis')
print('(the bounding-box test found only 13 -- it missed everything drawn diagonally)\n')
print(f'{"dist":>5s} {"code":9s} {"name":18s} {"L/W":>5s}   end1         middle       end2')
for d,c,r,t,m,b in rows[:15]:
    print(f'{d:5.1f} {c:9s} {NAMES.get(c,"?"):18s} {r:5.2f}   '
          f'{t[0]:+5.1f},{t[1]:+5.1f}  {m[0]:+5.1f},{m[1]:+5.1f}  {b[0]:+5.1f},{b[1]:+5.1f}')
print('\nTHE DRAWING (card 6, right object)         +9.9, -1.6   +2.0, -7.0   +9.4, -3.2')
