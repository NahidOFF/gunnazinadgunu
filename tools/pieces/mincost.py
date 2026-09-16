#!/usr/bin/env python3
"""Rank candidate answers by how far-fetched the naming they require is.

The feasibility test says yes to almost everything, so it cannot choose. This can:
give every candidate name a plausibility rank (0 = what anyone would call the picture),
and for a candidate answer solve the minimum-cost assignment of pieces to positions.
The answer that needs the least strained naming is the one worth believing.
"""
import sys, re, itertools
import numpy as np
from scipy.optimize import linear_sum_assignment
sys.path.insert(0,'/home/user/gunnazinadgunu/tools/pieces')
from naming import PIECES, ORDER, options
AZ='ABCDEFGHIJKLMNOPQRSTUVWXYZ'
INF=1e6
OPT=options()
N=len(ORDER)

def cost_table(colour):
    """C[piece][letter] = best (lowest) rank of a name putting that letter at that index"""
    C=np.full((N,26),INF)
    NAMES=[[[] for _ in range(26)] for _ in range(N)]
    for i,k in enumerate(ORDER):
        for rank,nm,rl,bl in OPT[k]:
            ch = rl if colour=='red' else bl
            if ch is None:                      # piece 14's blue is unread: free
                for c in range(26):
                    if rank < C[i][c]: C[i][c]=rank
                    NAMES[i][c].append((rank,nm))
                continue
            c=ord(ch)-65
            if rank < C[i][c]: C[i][c]=rank
            NAMES[i][c].append((rank,nm))
    return C,NAMES
CR,NR=cost_table('red')
CB,NB=cost_table('blue')

def solve(target, colour='red'):
    """min-cost assignment of pieces to the positions of `target`; None if impossible"""
    C = CR if colour=='red' else CB
    t=[ord(c)-65 for c in target]
    if len(t)!=N: return None
    M=C[:,t]
    if (M>=INF).all(axis=1).any(): return None
    r,c=linear_sum_assignment(M)
    tot=M[r,c].sum()
    if tot>=INF: return None
    return tot, {ORDER[i]:int(p) for i,p in zip(r,c)}

def detail(target, assign, colour='red'):
    NAMES = NR if colour=='red' else NB
    out=[None]*N
    for k,p in assign.items():
        i=ORDER.index(k)
        ch=ord(target[p])-65
        best=min(NAMES[i][ch])
        out[p]=(k,best[1],best[0])
    return out

def other_string(target, assign, colour='red'):
    """the string the OTHER colour takes, given the names the assignment picks"""
    s=[]
    for p in range(N):
        k=[kk for kk,pp in assign.items() if pp==p][0]
        i=ORDER.index(k)
        ch=ord(target[p])-65
        NAMES = NR if colour=='red' else NB
        rank,nm=min(NAMES[i][ch])
        c=re.sub(r'[^A-Z]','',nm.upper())
        ri,bi,_=PIECES[k]
        oi = bi if colour=='red' else ri
        s.append(c[oi-1] if oi else '?')
    return ''.join(s)

if __name__=='__main__':
    targets=[l.strip().upper() for l in open(sys.argv[1]) if l.strip()]
    colour=sys.argv[2] if len(sys.argv)>2 else 'red'
    res=[]
    for t in targets:
        tt=re.sub(r'[^A-Z]','',t)
        if len(tt)!=N: continue
        s=solve(tt,colour)
        if s: res.append((s[0],t,tt,s[1]))
    res.sort()
    print('%d of %d candidates are reachable at all\n'%(len(res),len(targets)))
    for tot,disp,tt,assign in res[:40]:
        print('cost %5.1f   %s' % (tot, disp))
        print('   other colour: %s'%other_string(tt,assign,colour))
        for p,(k,nm,rank) in enumerate(detail(tt,assign,colour)):
            print('     %s%-2d %-9s %-22s rank %d'%(tt[p],p+1,k,nm,rank))
        print()
