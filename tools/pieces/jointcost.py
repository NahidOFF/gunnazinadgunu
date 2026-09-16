#!/usr/bin/env python3
"""Take the red phrases the cost sweep liked and ask what the blue string would be.

The assignment fixes which piece sits where; the piece's name fixes both letters, so
blue is not free. Where several names give the same red letter, try each, and keep the
orderings whose blue string also splits into dictionary words.
"""
import sys, re, json, itertools
import numpy as np
from scipy.optimize import linear_sum_assignment
sys.path.insert(0,'/home/user/gunnazinadgunu/tools/pieces')
from naming import PIECES, ORDER, options
from mincost import CR, CB, N, INF
SP='/tmp/claude-0/-home-user-gunnazinadgunu/84fa90fa-750b-5180-b6a9-f390607e1640/scratchpad/'
OPT=options()
def L(s): return re.sub(r'[^A-Z]','',s.upper())

words=set()
for line in open(SP+'g10k.txt'):
    w=line.strip().upper()
    if w.isalpha() and 3<=len(w)<=12: words.add(w)
big=set()
for line in open(SP+'words.txt',errors='ignore'):
    w=L(line)
    if 3<=len(w)<=12: big.add(w)
def splits(s, pool, maxw=3):
    out=[]
    def rec(i,acc):
        if i==len(s):
            if 2<=len(acc)<=maxw: out.append(' '.join(acc))
            return
        if len(acc)>=maxw: return
        for j in range(i+3,len(s)+1):
            if len(s)-j!=0 and len(s)-j<3: continue
            if s[i:j] in pool: rec(j,acc+[s[i:j]])
    rec(0,[])
    return out

def blue_options(red, assign):
    """for each position, the set of (blueLetter, rank) the assignment allows"""
    per=[]
    for p in range(N):
        k=[kk for kk,pp in assign.items() if pp==p][0]
        ri,bi,_=PIECES[k]
        opts={}
        for rank,nm,rl,bl in OPT[k]:
            if rl!=red[p]: continue
            b = bl if bl else '?'
            if b not in opts or rank<opts[b]: opts[b]=rank
        per.append((k,opts))
    return per

def enumerate_blue(per, cap=4000):
    """all blue strings the naming allows, cheapest first (piece 14's '?' is a wildcard)"""
    lists=[]
    for k,opts in per:
        lists.append(sorted(((r,b) for b,r in opts.items())))
    out=[]
    for combo in itertools.product(*lists):
        out.append((sum(c[0] for c in combo), ''.join(c[1] for c in combo)))
        if len(out)>=cap: break
    out.sort()
    return out

if __name__=='__main__':
    data=json.load(open(SP+'SWEEP_red.json'))
    print('%d red candidates from the sweep'%len(data))
    res=[]
    for cost,disp,tt in data:
        M=CR[:,[ord(c)-65 for c in tt]]
        if (M>=INF).all(axis=1).any(): continue
        r,c=linear_sum_assignment(M)
        assign={ORDER[i]:int(p) for i,p in zip(r,c)}
        per=blue_options(tt,assign)
        for bcost,bs in enumerate_blue(per):
            pat=bs.replace('?','.')
            if '?' in bs:
                cand=[]
                for i in range(3,len(bs)-2):
                    a,b=bs[:i],bs[i:]
                    ra=[w for w in words if len(w)==len(a) and re.match('^'+a.replace('?','.')+'$',w)]
                    rb=[w for w in words if len(w)==len(b) and re.match('^'+b.replace('?','.')+'$',w)]
                    for x in ra:
                        for y in rb: cand.append(x+' '+y)
                sp=cand
            else:
                sp=splits(bs,words)
            if sp:
                res.append((cost+bcost,cost,bcost,disp,bs,sp[:3])); break
    res.sort()
    print('\n%d red phrases whose blue string also reads\n'%len(res))
    for tot,rc,bc,disp,bs,sp in res[:50]:
        print('total %5.1f (red %4.1f + blue %4.1f)   RED %-16s   BLUE %-14s -> %s'%(tot,rc,bc,disp,bs,sp))
