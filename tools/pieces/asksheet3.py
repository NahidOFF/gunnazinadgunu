#!/usr/bin/env python3
"""All fifteen pieces at the largest size their own best shot allows, labelled with the
numerals, so the pictures I still cannot name can be put in front of someone who can."""
import cv2, numpy as np
P=[('1','II','IV','REF803.png',(1630,640,1698,726)),
   ('2','II','XI','REF803.png',(1640,392,1678,460)),
   ('3','IV','VIII','REF803.png',(1694,918,1738,982)),
   ('4','V','VII','REF803.png',(1646,478,1696,522)),
   ('5','VI','V','REF803.png',(1636,886,1708,950)),
   ('6','VI','VI','REF803.png',(1674,704,1724,776)),
   ('7','VI','VIII','REF803.png',(1690,476,1742,542)),
   ('8','VII','I','REF803.png',(1656,390,1704,466)),
   ('9','VII','IV','REF803.png',(1780,636,1906,730)),
   ('10','VIII','IX','REF803.png',(1696,374,1754,448)),
   ('11','IX','V','REF803.png',(1796,476,1904,570)),
   ('12','X','XIV','REF803.png',(1504,768,1600,842)),
   ('13','VII','?','REF803.png',(1672,388,1722,464)),
   ('14','VII','IX','REF803.png',(1504,816,1584,894)),
   ('15','?','?','REF_OFFICE.png',(1652,840,1698,888))]
ROWH=340
tiles=[]
for tag,r,b,fn,(x0,y0,x1,y1) in P:
    im=cv2.imread(fn)
    if im is None:
        print('missing',fn); continue
    Z=max(6,int(ROWH/max(1,(y1-y0))))
    c=cv2.resize(im[y0:y1,x0:x1].astype(np.float32),None,fx=Z,fy=Z,interpolation=cv2.INTER_LANCZOS4)
    g=c.reshape(-1,3); L=g.mean(1); ref=g[L>=np.percentile(L,85)].mean(0)
    bal=np.clip(c*(ref.mean()/np.maximum(ref,1)),0,255).astype(np.uint8)
    lab=cv2.cvtColor(bal,cv2.COLOR_BGR2LAB).astype(np.float32)
    lo,hi=np.percentile(lab[:,:,0],2),np.percentile(lab[:,:,0],98)
    lab[:,:,0]=np.clip((lab[:,:,0]-lo)*(255/max(1,hi-lo)),0,255)
    lab[:,:,1]=np.clip((lab[:,:,1]-128)*2.0+128,0,255)
    lab[:,:,2]=np.clip((lab[:,:,2]-128)*2.0+128,0,255)
    out=cv2.cvtColor(lab.astype(np.uint8),cv2.COLOR_LAB2BGR)
    out=cv2.filter2D(out,-1,np.array([[0,-.4,0],[-.4,2.6,-.4],[0,-.4,0]],np.float32))
    hdr=np.full((46,out.shape[1],3),250,np.uint8)
    cv2.putText(hdr,f'#{tag}   red {r}  blue {b}',(8,33),cv2.FONT_HERSHEY_SIMPLEX,0.9,(15,15,15),2,cv2.LINE_AA)
    t=np.vstack([hdr,out])
    tiles.append(t)
H=max(t.shape[0] for t in tiles); W=max(t.shape[1] for t in tiles)
pad=lambda t: np.pad(t,((0,H-t.shape[0]),(0,W-t.shape[1]),(0,0)),constant_values=250)
tiles=[pad(t) for t in tiles]
rows=[np.hstack(tiles[i:i+5]+[np.full((H,W,3),250,np.uint8)]*(5-len(tiles[i:i+5]))) for i in range(0,len(tiles),5)]
sheet=np.vstack(rows)
cv2.imwrite('SHEET15.png',sheet); print('SHEET15',sheet.shape)
