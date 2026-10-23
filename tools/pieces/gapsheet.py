import sys,glob,cv2,numpy as np,json
U='/root/.claude/uploads/84fa90fa-750b-5180-b6a9-f390607e1640'
cm=json.load(open('clipmap.json'))
CID=sys.argv[1]; T0=float(sys.argv[2]); T1=float(sys.argv[3]); N=int(sys.argv[4]); OUT=sys.argv[5]
COLS=int(sys.argv[6]) if len(sys.argv)>6 else 6
src=glob.glob(f'{U}/{CID}*')[0]; off=cm[CID]['offset']
cap=cv2.VideoCapture(src); fps=cap.get(cv2.CAP_PROP_FPS)
ts=np.linspace(T0,T1,N)
tiles=[]
for t in ts:
    cap.set(cv2.CAP_PROP_POS_FRAMES,int(round((t-off)*fps)))
    ok,fr=cap.read()
    if not ok: continue
    fr=cv2.resize(fr,(320,180))
    cv2.putText(fr,f'{t:.0f}',(4,16),cv2.FONT_HERSHEY_SIMPLEX,0.5,(0,255,255),1,cv2.LINE_AA)
    tiles.append(fr)
rows=[]
for i in range(0,len(tiles),COLS):
    r=tiles[i:i+COLS]
    while len(r)<COLS: r.append(np.zeros_like(tiles[0]))
    rows.append(np.hstack(r))
cv2.imwrite(OUT,np.vstack(rows)); print(OUT,len(tiles))
