#!/usr/bin/env python3
"""Do the jigsaw pictures appear anywhere else in the room -- on the corkboard, on the
old puzzle's clue cards? If a card carrying the same picture also carries a label, that
label names the picture, which is the one thing the whole solve is missing."""
import cv2, numpy as np, glob, sys
SP='/tmp/claude-0/-home-user-gunnazinadgunu/84fa90fa-750b-5180-b6a9-f390607e1640/scratchpad/'
PIECES={'oman':(1638,888,1706,948),'joy':(1512,776,1580,832),'snow':(1806,486,1892,556),
        'chart':(1700,378,1752,442),'bow':(1648,480,1694,518),'rect':(1694,482,1740,536),
        'elf':(1642,396,1676,458),'sil':(1696,920,1736,980),'barn':(1782,638,1904,728),
        'cal':(1632,642,1696,724),'twothin':(1676,706,1722,772),'frames':(1660,392,1702,462),
        'eagle':(1508,822,1578,888)}
SCENES=['REF803.png','REF806.png','REF765.png','REF767.png','REF_OFFICE.png']
base=cv2.imread(SP+'REF803.png')
for name,(x0,y0,x1,y1) in PIECES.items():
    tpl=cv2.cvtColor(base[y0:y1,x0:x1],cv2.COLOR_BGR2GRAY)
    hits=[]
    for fn in SCENES:
        im=cv2.imread(SP+fn)
        if im is None: continue
        g=cv2.cvtColor(im,cv2.COLOR_BGR2GRAY)
        for s in np.arange(0.30,1.75,0.05):
            t=cv2.resize(tpl,None,fx=s,fy=s,interpolation=cv2.INTER_AREA)
            if t.shape[0]<8 or t.shape[1]<8 or t.shape[0]>=g.shape[0] or t.shape[1]>=g.shape[1]: continue
            r=cv2.matchTemplate(g,t,cv2.TM_CCOEFF_NORMED)
            th=0.62
            ys,xs=np.where(r>=th)
            for yy,xx in zip(ys,xs):
                # ignore the card's own location in its own frame
                if fn=='REF803.png' and abs(xx-x0)<60 and abs(yy-y0)<60: continue
                hits.append((round(float(r[yy,xx]),3),fn,int(xx),int(yy),round(float(s),2)))
    hits.sort(reverse=True)
    # de-duplicate nearby hits
    keep=[]
    for h in hits:
        if all(not(h[1]==k[1] and abs(h[2]-k[2])<40 and abs(h[3]-k[3])<40) for k in keep): keep.append(h)
        if len(keep)>=4: break
    print('%-8s %s'%(name, keep if keep else 'no second appearance above 0.62'))
