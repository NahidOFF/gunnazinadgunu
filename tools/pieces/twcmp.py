#!/usr/bin/env python3
"""twcmp.py -- each unnamed drawing beside candidate emoji from a SECOND vendor
(Twemoji), at one tile size, for the eye.

Deliberately not a ranker: eleven automatic similarity measures have failed
their controls in this hunt.  The reason a second vendor matters is that my
"these are not standard emoji" conclusion was tested against Noto alone, and
vendors draw the same emoji very differently.  A hand copy may follow one
vendor's art and match no other."""
import cv2,numpy as np
NAME={'1fa9f':'window','1f6aa':'door','1f5c4':'file cabinet','1f5bc':'framed pic',
 '1faa8':'rock','1f985':'eagle','1f9f1':'brick','1f4d5':'closed book',
 '1f36b':'chocolate','1fab6':'feather','1f343':'leaf','1f525':'fire',
 '1f955':'carrot','1f336':'hot pepper','1f9b7':'tooth','1f9dd':'elf',
 '1f385':'santa','1f9d9':'mage','1f6fc':'roller skate','1f4ca':'bar chart',
 '1f4c9':'chart down','1f331':'seedling','1f33f':'herb','1f426':'bird',
 '1f97e':'hiking boot','1f9e6':'socks','1f3a4':'microphone','1f511':'key',
 '1f4a1':'light bulb','1f3b8':'guitar','1f95c':'peanuts','1f956':'baguette',
 '1f330':'chestnut','1f3fa':'amphora','1f954':'potato','1f9f3':'luggage',
 '1f6cb':'couch','1f3e0':'house','1f6d6':'hut','1fab5':'wood','1f360':'sweet potato',
 '1f346':'eggplant','1f36f':'honey pot','1f5ff':'moai','1f574':'suit levitating',
 '1f3a9':'top hat','1f987':'bat','1f302':'closed umbrella','2693':'anchor',
 '1fa93':'axe','1f528':'hammer','1f9cc':'troll','1f9da':'fairy','1f9df':'zombie',
 '1f936':'mrs claus','1fa86':'nesting dolls','1f38e':'japanese dolls',
 '26c4':'snowman','1f9ca':'ice','1f4c8':'chart up','1f4b9':'chart yen',
 '1f3f7':'label','1f52a':'knife','1f9f2':'magnet','1f3f3':'white flag',
 '1f6a9':'triangular flag','1f9ea':'test tube','1f9f4':'lotion','1f58a':'pen',
 '1f4d3':'notebook','1f4d2':'ledger','1f4bc':'briefcase','1f6e2':'oil drum',
 '1f95a':'egg','1f9c5':'onion'}
ROWS=[("13  frame + one divider  (ink COOLER than paper = grey)",'REF803.png',(1676,392,1718,460),
       ['1f5c4','1fa9f','1f6aa','1f4bc','1f4d3','1f3f7']),
      ("7   plain rectangle  (a*+16.4 b*+13.8 terracotta, 1 : 2.14)",'REF803.png',(1696,482,1736,534),
       ['1f6aa','1f9f1','1f4d5','1f36b','1fab5','1f6e2']),
      ("14L smooth lump, gold facet  (elong 2.63, solidity 0.97, straight)",'REF803.png',(1515,823,1539,871),
       ['1f360','1fab5','1f330','1faa8','1f346','1f95c','1f36f']),
      ("3   dark silhouette  (NEUTRAL BLACK, elong 2.78, waist)",'REF803.png',(1698,922,1734,978),
       ['1f3a4','1f574','1f5ff','1f302','1f987','1f9ea','1f58a','1f97e']),
      ("15  notched wedge  (elong 2.36, solidity 0.91, notch on TOP edge)",'REF_OFFICE.png',(1662,848,1688,880),
       ['1f9b7','1f343','1f525','1f6a9','1fab6','1f52a','1f9c5']),
      ("1   figure: green hat, red lower, TWO DARK DISCS below",'REF803.png',(1648,399,1663,452),
       ['1f9cc','1f9dd','1f9df','1f6fc','1fa86','1f38e','26c4']),
      ("10  down arrow + bars (pink/yellow/green)",'REF803.png',(1704,382,1748,438),
       ['1f4ca','1f4c9','1f4c8','1f4b9']),
     ]
T=150
def tile(im):
    h,w=im.shape[:2]; s=min(T/w,T/h)*0.94
    r=cv2.resize(im,(max(1,int(w*s)),max(1,int(h*s))),interpolation=cv2.INTER_AREA)
    t=np.full((T,T,3),252,np.uint8)
    t[(T-r.shape[0])//2:(T-r.shape[0])//2+r.shape[0],(T-r.shape[1])//2:(T-r.shape[1])//2+r.shape[1]]=r
    return t
rows=[]
NC=max(len(r[3]) for r in ROWS)
for tag,fn,(x0,y0,x1,y1),cands in ROWS:
    im=cv2.imread(fn).astype(np.float32)
    c=cv2.resize(im[y0:y1,x0:x1],None,fx=14,fy=14,interpolation=cv2.INTER_LANCZOS4)
    g=c.reshape(-1,3); L=g.mean(1); ref=g[L>=np.percentile(L,88)].mean(0)
    c=np.clip(c*(ref.mean()/ref),0,255).astype(np.uint8)
    cells=[tile(c)]
    for k in cands:
        e=cv2.imread(f'emo/{k}.png',cv2.IMREAD_UNCHANGED)
        if e is None: continue
        if e.shape[2]==4:
            a=e[:,:,3:4].astype(np.float32)/255
            e=(e[:,:,:3]*a+252*(1-a)).astype(np.uint8)
        cells.append(tile(e))
    while len(cells)<NC+1: cells.append(np.full((T,T,3),252,np.uint8))
    band=np.hstack(cells)
    lbl=np.full((26,band.shape[1],3),252,np.uint8)
    cv2.putText(lbl,'THE DRAWING',(6,18),cv2.FONT_HERSHEY_SIMPLEX,0.42,(150,20,20),1,cv2.LINE_AA)
    for i,k in enumerate(cands):
        cv2.putText(lbl,NAME.get(k,k),(T*(i+1)+6,18),cv2.FONT_HERSHEY_SIMPLEX,0.42,(40,40,40),1,cv2.LINE_AA)
    hdr=np.full((28,band.shape[1],3),252,np.uint8)
    cv2.putText(hdr,tag,(6,20),cv2.FONT_HERSHEY_SIMPLEX,0.62,(20,20,20),2,cv2.LINE_AA)
    rows.append(np.vstack([hdr,band,lbl,np.full((10,band.shape[1],3),235,np.uint8)]))
cv2.imwrite('TWCMP.png',np.vstack(rows)); print('ok')
