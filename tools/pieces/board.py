#!/usr/bin/env python3
"""One board: every piece with its picture, numerals, date and status."""
import cv2,numpy as np
im=cv2.imread('REF803.png'); p15=cv2.imread('P15_Q.png')
P=[('1',(1636,392,1676,458),'red II . blue XI','11 Feb','figure: green hat, red lower + 2 discs'),
   ('2',(1636,644,1692,722),'red II . blue IV','4 Feb','spiral pad, glyph 25 or &'),
   ('3',(1689,906,1760,990),'red IV . blue VIII','8 Apr','black shape (elong 2.9) + green plant'),
   ('4',(1648,478,1700,540),'red V . blue VII','7 May','BUTTERFLY'),
   ('5',(1618,884,1700,966),'red VI . blue V','5 Jun','OMAN FLAG'),
   ('6',(1668,702,1732,780),'red VI . blue VI','6 Jun','navy object + red-pale-red object'),
   ('7',(1684,472,1750,540),'red VI . blue VIII','8 Jun','plain maroon rectangle'),
   ('8',(1662,394,1700,460),'red VII . blue I','1 Jul','picture HIDDEN'),
   ('9',(1782,636,1906,730),'red VII . blue IV','4 Jul','US FLAG + BARN'),
   ('10',(1700,378,1762,452),'red VIII . blue IX','9 Aug','down arrow + 3-bar chart'),
   ('11',(1798,480,1906,572),'red IX . blue V','5 Sep','CLOUD WITH SNOW'),
   ('12',(1504,768,1600,842),'red X . blue XIV','14 Oct','FACE WITH TEARS OF JOY'),
   ('13',(1678,392,1716,458),'? . ?','—','window / file cabinet'),
   ('14',(1494,806,1600,900),'? . ?','—','ovoid (gold inside) + BALD EAGLE'),
   ('15',None,'? . ?','—','15th piece: two peaks, tapers')]
CW,CH=430,300; COLS=5
rows=[]
for i in range(0,len(P),COLS):
    row=np.full((CH+92,CW*COLS,3),252,np.uint8)
    for j,(n,box,num,date,lab) in enumerate(P[i:i+COLS]):
        if box is None:
            t=cv2.resize(p15,(int(p15.shape[1]*CH/p15.shape[0]),CH),interpolation=cv2.INTER_AREA)
        else:
            x0,y0,x1,y1=box
            c=im[y0:y1,x0:x1].astype(np.float32)
            g=c.reshape(-1,3); L=g.mean(1); ref=g[L>=np.percentile(L,84)].mean(0)
            c=np.clip(c*(ref.mean()/ref),0,255).astype(np.uint8)
            s=min(CW/c.shape[1],CH/c.shape[0])*0.95
            t=cv2.resize(c,(max(1,int(c.shape[1]*s)),max(1,int(c.shape[0]*s))),interpolation=cv2.INTER_LANCZOS4)
        oy=48+(CH-t.shape[0])//2; ox=j*CW+(CW-t.shape[1])//2
        row[oy:oy+t.shape[0],ox:ox+t.shape[1]]=t
        cv2.putText(row,f'{n}.  {num}',(j*CW+12,26),cv2.FONT_HERSHEY_SIMPLEX,0.72,(20,20,20),2,cv2.LINE_AA)
        cv2.putText(row,date,(j*CW+12,44),cv2.FONT_HERSHEY_SIMPLEX,0.62,(160,40,40),2,cv2.LINE_AA)
        cv2.putText(row,lab[:44],(j*CW+12,CH+74),cv2.FONT_HERSHEY_SIMPLEX,0.5,(60,60,60),1,cv2.LINE_AA)
    rows.append(row)
out=np.vstack(rows)
hdr=np.full((60,out.shape[1],3),252,np.uint8)
cv2.putText(hdr,'15 pieces - ordered by date (red = month, blue = day).  Frozen hypothesis.',
            (16,40),cv2.FONT_HERSHEY_SIMPLEX,1.0,(0,0,150),2,cv2.LINE_AA)
cv2.imwrite('BOARD.png',np.vstack([hdr,out])); print('ok',out.shape)
