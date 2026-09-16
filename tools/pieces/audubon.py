#!/usr/bin/env python3
"""Test the red half: pink-sheet numbers as Audubon plate numbers, its Roman numerals
as letter indices into the plate's bird name. The bundled plate list carries Audubon's
ORIGINAL titles (Towee Bunting, Wood Ibiss, Kildeer Plover), which is what the desk's
"Books w/ old names" sticky asks for."""
import json, re, sys
D={p['plate']:p['name'] for p in json.load(open('/home/user/gunnazinadgunu/tools/pieces/audubon_plates.json'))}
def L(s): return re.sub(r'[^A-Z]','',s.upper())
R={'I':1,'II':2,'III':3,'IV':4,'V':5,'VI':6,'VII':7,'VIII':8,'IX':9,'X':10,'XI':11,
   'XII':12,'XIII':13,'XIV':14,'XV':15,'XVI':16}
def run(pairs):
    rows=[]
    for p,rn in pairs:
        nm=D.get(p,'??'); c=L(nm); i=R[rn]
        rows.append((p,rn,i,nm,c[i-1] if len(c)>=i else '?'))
    return rows
if __name__=='__main__':
    src=sys.argv[1] if len(sys.argv)>1 else None
    if not src:
        print('usage: audubon.py "029 III, 042 V, ..."'); sys.exit(0)
    pairs=[]
    for tok in re.split(r'[,\n|]+',src):
        tok=tok.strip()
        if not tok: continue
        a,b=tok.split()
        pairs.append((int(a),b))
    rows=run(pairs)
    print('sheet order      : '+''.join(r[4] for r in rows))
    print('alphabetical name: '+''.join(r[4] for r in sorted(rows,key=lambda r:r[3].upper())))
    print('by plate number  : '+''.join(r[4] for r in sorted(rows,key=lambda r:r[0])))
    for p,rn,i,nm,ch in rows: print('  %3d %-5s [%2d] %-32s -> %s'%(p,rn,i,nm,ch))
