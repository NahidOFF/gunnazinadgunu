#!/usr/bin/env python3
"""The drawn strip fixes the order, so the string is a pattern with holes where I
cannot name the picture.  Find every way to cut such a pattern into dictionary words."""
import sys, re
W='/tmp/claude-0/-home-user-gunnazinadgunu/84fa90fa-750b-5180-b6a9-f390607e1640/scratchpad/words.txt'
words=set()
for line in open(W,errors='ignore'):
    w=''.join(c for c in line.strip().upper() if c.isalpha())
    if 1<=len(w)<=20: words.add(w)
bylen={}
for w in words: bylen.setdefault(len(w),set()).add(w)

def match(pat):
    rx=re.compile('^'+pat.replace('?','.')+'$')
    return [w for w in bylen.get(len(pat),()) if rx.match(w)]

pat=sys.argv[1].upper()
maxw=int(sys.argv[2]) if len(sys.argv)>2 else 2
minw=int(sys.argv[3]) if len(sys.argv)>3 else 3
out=[]
def rec(i, acc):
    if len(acc)>maxw: return
    if i==len(pat):
        if len(acc)>=2: out.append(' '.join(acc))
        return
    for j in range(i+minw, len(pat)+1):
        if len(pat)-j!=0 and len(pat)-j<minw: continue
        for w in match(pat[i:j]):
            rec(j, acc+[w])
rec(0,[])
print(len(out),'splits for',pat)
for s in sorted(set(out)): print('  ',s)
