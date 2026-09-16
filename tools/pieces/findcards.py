#!/usr/bin/env python3
"""findcards.py FRAME.png -- list every card-sized white blob in a frame.

Hunting for a card by eye in a new camera angle wastes reads and misses cards:
this is how the second angle's better views of cards 3, 10 and 13 were found
after they had been declared unreachable."""
import sys,cv2,numpy as np
fn=sys.argv[1]
im=cv2.imread(fn)
if im is None: sys.exit('missing '+fn)
lab=cv2.cvtColor(im,cv2.COLOR_BGR2LAB)
L=lab[:,:,0].astype(np.int16); B=lab[:,:,2].astype(np.int16)-128
m=((B<14)&(L>138)).astype(np.uint8)
m=cv2.morphologyEx(m,cv2.MORPH_CLOSE,np.ones((3,3),np.uint8))
n,lb,st,ct=cv2.connectedComponentsWithStats(m,8)
rows=[]
for i in range(1,n):
    x,y,w,h,a=st[i]
    if not (250<a<12000): continue
    if w<16 or h<16 or w>230 or h>230: continue
    rows.append((a,x,y,w,h))
rows.sort(reverse=True)
print(f'{fn}: {len(rows)} card-sized white blobs')
for a,x,y,w,h in rows[:16]:
    print(f'   area {a:5d}  box {x},{y},{x+w},{y+h}  ({w}x{h})')
