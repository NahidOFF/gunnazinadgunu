#!/usr/bin/env python3
"""maskchk.py RECT.png OUT.png LABEL -- show the drawing beside the exact mask the
row/column profile was taken from, with the detected horizontal and vertical
members marked.  Drawing what was measured is the only thing that has caught my
mis-measurements in this hunt."""
import sys,cv2,numpy as np
im=cv2.imread(sys.argv[1]); OUT=sys.argv[2]; tag=sys.argv[3]
im=im[:,:im.shape[1]//2]
g=cv2.cvtColor(im,cv2.COLOR_BGR2GRAY).astype(np.float32)
d=255-g; d-=np.percentile(d,25); d=np.clip(d,0,None)
m=(d>0.45*d.max()).astype(np.uint8)
m=cv2.morphologyEx(m,cv2.MORPH_CLOSE,np.ones((5,5),np.uint8))
n,lb,st,_=cv2.connectedComponentsWithStats(m,8)
k=1+int(np.argmax(st[1:,4])); x,y,w,h,_=st[k]
sel=(lb==k).astype(np.uint8)
vis=im.copy(); vis[sel>0]=(0.35*vis[sel>0]+0.65*np.float32([60,60,255])).astype(np.uint8)
cv2.rectangle(vis,(x,y),(x+w,y+h),(0,180,0),2)
row=d[y:y+h,x:x+w].mean(1); col=d[y:y+h,x:x+w].mean(0)
def loc(p,gap):
    p=np.convolve(p,np.ones(gap)/gap,'same'); out=[]
    for i in range(gap,len(p)-gap):
        if p[i]==max(p[i-gap:i+gap+1]) and p[i]>0.55*p.max():
            if not out or i-out[-1]>gap: out.append(i)
    return out
R=loc(row,max(3,h//14)); C=loc(col,max(3,w//8))
for r in R: cv2.line(vis,(x,y+r),(x+w,y+r),(0,220,255),2)
for c in C: cv2.line(vis,(x+c,y),(x+c,y+h),(255,80,255),2)
mk=cv2.cvtColor(sel*255,cv2.COLOR_GRAY2BGR)
pad=np.full((im.shape[0],14,3),250,np.uint8)
out=np.hstack([im,pad,vis,pad,mk])
hdr=np.full((70,out.shape[1],3),250,np.uint8)
cv2.putText(hdr,tag,(10,26),cv2.FONT_HERSHEY_SIMPLEX,0.62,(20,20,20),2,cv2.LINE_AA)
cv2.putText(hdr,f'horizontal members at {[round(100*r/h) for r in R]}% of height   '
                f'vertical at {[round(100*c/w) for c in C]}% of width   bbox {w}x{h}',
            (10,52),cv2.FONT_HERSHEY_SIMPLEX,0.55,(140,20,20),1,cv2.LINE_AA)
cv2.imwrite(OUT,np.vstack([hdr,out]))
print(f'{tag}: horiz {[round(100*r/h) for r in R]}%  vert {[round(100*c/w) for c in C]}%  bbox {w}x{h}')
