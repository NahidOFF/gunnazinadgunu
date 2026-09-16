#!/usr/bin/env python3
"""board2.py -- one board: all 15 pieces in (red, blue) order, each with its best
crop, its numerals, what is MEASURED about the drawing, and the current status of
its name.  The measurement line is the record; the name is a verdict only where
it is earned."""
import cv2,numpy as np
P=[  # order, red, blue, source, box, name-status, measured facts
 ('1','II','IV','REF803.png',(1630,640,1698,726),'CALENDAR / spiral pad','ok'),
 ('2','II','XI','REF803.png',(1644,396,1674,456),'figure on ROLLER SKATES','ok?'),
 ('3','IV','VIII','REF803.png',(1698,922,1734,978),'? neutral BLACK silhouette','open'),
 ('4','V','VII','REF803.png',(1650,482,1692,518),'BUTTERFLY (4 lobes)','ok'),
 ('5','VI','V','REF803.png',(1640,890,1704,946),'OMAN FLAG','ok'),
 ('6','VI','VI','REF803.png',(1678,708,1720,772),'? two thin objects','open'),
 ('7','VI','VIII','REF803.png',(1694,480,1738,538),'? plain terracotta rect','open'),
 ('8','VII','I','REF803.png',(1660,394,1700,462),'PICTURE HIDDEN','never'),
 ('9','VII','IV','REF803.png',(1784,640,1902,726),'US FLAG + barn','ok'),
 ('10','VIII','IX','REF803.png',(1700,378,1750,444),'DOWN ARROW + BAR CHART','ok'),
 ('11','IX','V','REF803.png',(1800,480,1900,566),'CLOUD WITH SNOW','ok'),
 ('12','X','XIV','REF803.png',(1508,772,1596,838),'FACE W/ TEARS OF JOY','ok'),
 ('13','?','?','REF803.png',(1676,392,1718,460),'FILE CABINET (3 vendors)','new'),
 ('14','?','?','REF803.png',(1508,820,1580,890),'? lump + BALD EAGLE','open'),
 ('15','?','?','REF_OFFICE.png',(1656,844,1694,884),'? dark notched form','open'),
]
FACT={'3':'elong 2.78 solid 0.82 | shallow arc | neutral black | mic & suit-figure survive',
 '6':'dark obj ~8px wide, at the resolution limit | light obj has red at top AND bottom',
 '7':'1 : 2.14 | a*+16.4 b*+13.8 terracotta | 24x: NO knob, NO panel (but 22x47px)',
 '13':'one horizontal divider, two panels, bumps = handles | ink COOLER than paper',
 '14':'lump: solid 0.97, spine STRAIGHT, gold facet upper-right | NOT rock, NOT banana',
 '15':'solid 0.91 | tall peak left, dip, low shoulder right | parallel sides | NOT eggplant',
 '1':'spiral binding + a glyph read as 25 or &','2':'green cone hat, red lower, dark wheels',
 '4':'four lobes = four wings; uncoloured OUTLINE drawing','5':'red hoist band, white/red/green',
 '8':'hidden on all three camera angles','9':'one card holds BOTH flag and barn',
 '10':'bars pink / yellow / green, increasing','11':'~7 marks in two rows below the cloud',
 '12':'yellow face, blue tears'}
COL={'ok':(30,120,30),'ok?':(180,120,0),'open':(0,0,200),'never':(110,110,110),'new':(160,0,160)}
CW,CH,COLS=470,300,5
rows=[]
for i in range(0,len(P),COLS):
    row=np.full((CH+112,CW*COLS,3),252,np.uint8)
    for j,(n,r,b,fn,(x0,y0,x1,y1),nm,st) in enumerate(P[i:i+COLS]):
        im=cv2.imread(fn).astype(np.float32)
        c=cv2.resize(im[y0:y1,x0:x1],None,fx=8,fy=8,interpolation=cv2.INTER_LANCZOS4)
        g=c.reshape(-1,3); L=g.mean(1); ref=g[L>=np.percentile(L,88)].mean(0)
        c=np.clip(c*(ref.mean()/ref),0,255).astype(np.uint8)
        s=min(CW/c.shape[1],CH/c.shape[0])*0.95
        t=cv2.resize(c,(int(c.shape[1]*s),int(c.shape[0]*s)),interpolation=cv2.INTER_LANCZOS4)
        oy=52+(CH-t.shape[0])//2; ox=j*CW+(CW-t.shape[1])//2
        row[oy:oy+t.shape[0],ox:ox+t.shape[1]]=t
        cv2.putText(row,f'{n}.  red {r}  .  blue {b}',(j*CW+10,26),
                    cv2.FONT_HERSHEY_SIMPLEX,0.66,(20,20,20),2,cv2.LINE_AA)
        cv2.putText(row,nm[:40],(j*CW+10,46),cv2.FONT_HERSHEY_SIMPLEX,0.55,COL[st],2,cv2.LINE_AA)
        f=FACT.get(n,'')
        for k,part in enumerate([f[m:m+62] for m in range(0,len(f),62)][:3]):
            cv2.putText(row,part,(j*CW+10,CH+72+k*17),cv2.FONT_HERSHEY_SIMPLEX,0.40,(70,70,70),1,cv2.LINE_AA)
        cv2.line(row,(j*CW,0),(j*CW,row.shape[0]),(225,225,225),1)
    rows.append(row)
out=np.vstack(rows)
hdr=np.full((72,out.shape[1],3),252,np.uint8)
cv2.putText(hdr,'15 pieces in (red, blue) order.  GREEN = named   ORANGE = probable   '
            'PURPLE = named tonight   RED = still open   GREY = never readable',
            (16,30),cv2.FONT_HERSHEY_SIMPLEX,0.72,(0,0,140),2,cv2.LINE_AA)
cv2.putText(hdr,'The order does not depend on the date model: sorting by (red, blue) IS that sort.',
            (16,56),cv2.FONT_HERSHEY_SIMPLEX,0.62,(80,80,80),1,cv2.LINE_AA)
cv2.imwrite('BOARD2.png',np.vstack([hdr,out])); print('ok',out.shape)
