#!/usr/bin/env python3
"""colorbox.py -- measure named boxes against a paper box on the same card, AND
draw the boxes on a zoom so the placement can be checked by eye. Placement was
the failure mode: a 3-px slip at this scale lands on a neighbouring colour."""
import sys,cv2,numpy as np,json
im=cv2.imread(sys.argv[1]).astype(np.float32)
spec=json.load(open(sys.argv[2])); OUT=sys.argv[3]
px0,py0,px1,py1=spec['paper']
ref=im[py0:py1,px0:px1].reshape(-1,3); L=ref.mean(1)
wb=ref[L>=np.percentile(L,70)].mean(0)
w=np.clip(im*(wb.mean()/wb),0,255)
lab=cv2.cvtColor(w.astype(np.uint8),cv2.COLOR_BGR2LAB).astype(np.float32)
Lc,A,B=lab[:,:,0],lab[:,:,1]-128,lab[:,:,2]-128
p=(slice(py0,py1),slice(px0,px1)); pa,pb=A[p].mean(),B[p].mean()
print(f"paper: L={Lc[p].mean():.1f} a*={pa:+.2f} b*={pb:+.2f}")
for name,(x0,y0,x1,y1) in spec['boxes'].items():
    s=(slice(y0,y1),slice(x0,x1))
    print(f"  {name:22s} L={Lc[s].mean():6.1f}  da*={A[s].mean()-pa:+7.2f}  db*={B[s].mean()-pb:+7.2f}")
X0,Y0,X1,Y1=spec['view']; Z=spec.get('zoom',20)
v=cv2.resize(np.clip(w,0,255).astype(np.uint8)[Y0:Y1,X0:X1],None,fx=Z,fy=Z,interpolation=cv2.INTER_LANCZOS4)
def rect(b,c,t):
    x0,y0,x1,y1=b; cv2.rectangle(v,((x0-X0)*Z,(y0-Y0)*Z),((x1-X0)*Z,(y1-Y0)*Z),c,3)
    cv2.putText(v,t,((x0-X0)*Z+3,(y0-Y0)*Z-6),cv2.FONT_HERSHEY_SIMPLEX,0.7,c,2,cv2.LINE_AA)
rect(spec['paper'],(255,0,255),'paper')
for i,(name,b) in enumerate(spec['boxes'].items()): rect(b,(0,0,255),name)
cv2.imwrite(OUT,v); print('wrote',OUT)
