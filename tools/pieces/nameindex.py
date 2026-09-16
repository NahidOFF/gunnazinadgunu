#!/usr/bin/env python3
"""The old hunt's own jigsaw mechanism, applied to the new pieces.

OP1 of the answer document: jigsaw pieces each carry a number, and the numbers
are "counted by number into the name of the puzzle maker" - LONE SHARK GAMES -
to spell A HOME AREA NEAR KAM LAKE. Our fifteen pieces carry two numbers each,
so this indexes those numbers into candidate names and scores the result as
English. The control is the old puzzle itself, run first.
"""
import re,itertools
W={w.strip().upper() for w in open('words.txt') if 3<=len(w.strip())<=15}
def score(s):
    """number of dictionary words findable greedily, plus coverage"""
    s=s.replace('?','')
    n=len(s); best=[0]*(n+1); cov=[0]*(n+1)
    for i in range(1,n+1):
        best[i]=best[i-1]; cov[i]=cov[i-1]
        for L in range(3,min(15,i)+1):
            w=s[i-L:i]
            if w in W and best[i-L]+1>=best[i]:
                if best[i-L]+1>best[i] or cov[i-L]+L>cov[i]:
                    best[i]=best[i-L]+1; cov[i]=cov[i-L]+L
    return cov[n]/max(n,1), best[n]
def idx(name,nums):
    s=re.sub(r'[^A-Z]','',name.upper())
    out=[]
    for n in nums:
        out.append(s[n-1] if 1<=n<=len(s) else '?')
    return ''.join(out)

# ---- control: the old puzzle ----
OLD=[11,6,2,12,4,7,8,13,7,3,13,11,8,9,7,12,1,11,9,4]
ctl=idx('LONE SHARK GAMES',OLD)
print('NEZARET (kohne OP1):',ctl,'  gozlenilen: AHOMEAREANEARKAMLAKE',
      'UYGUN' if ctl=='AHOMEAREANEARKAMLAKE' else 'SEHV')
print('   nezaretin bali:',score(ctl))
print()

RED=[2,2,4,5,6,6,6,7,7,8,9,10]
BLUE=[11,4,8,7,5,6,8,1,4,9,5,14]
ORDERS={
 'q,m cutlerle (tarix)': [v for p in zip(RED,BLUE) for v in p],
 'm,q cutlerle (tarix)': [v for p in zip(BLUE,RED) for v in p],
 'evvel butun qirmizi': RED+BLUE,
 'evvel butun mavi':    BLUE+RED,
 'yalniz qirmizi':      RED,
 'yalniz mavi':         BLUE,
 'ters tarix q,m':      [v for p in zip(RED[::-1],BLUE[::-1]) for v in p],
}
NAMES=['LONE SHARK GAMES','JIMMY DONALDSON','MRBEAST YOUTUBE','BEAST INDUSTRIES',
 'COLIN SANDERS','DOCTOR XOR','COLIN SANDERS XOR','DOCTORXOR COLIN','MIKE SELINKER',
 'MICHAEL SELINKER','THE PUZZLE MAKER','PUZZLE MAKER','MRBEAST YOUTUBE LLC',
 'SALESFORCE SLACK','THE HAT TRICK','THE MILLION DOLLAR PUZZLE','FEASTABLES',
 'BEAST GAMES','JIMMY DONALDSON MRBEAST','COLIN','SANDERS','LONESHARK',
 'THE FOREST CITY','A NICE SUGAR','BEAST TRAVEL','ROAMY THE GLOBE',
 'THE RAMBLINGS OF A MILLION DOLLAR WINNER','RIDDLE ZERO THE HAT TRICK',
 'HOW ONE PERSON SOLVED A MILLION DOLLAR PUZZLE','PUZZLE VIDEO SWEEPSTAKES',
 'CHRISTIAN TYSON','KARL JACOBS','CHANDLER HALLOW','NOLAN HANSEN','TAREQ',
 'THE BEST FRIEND','EVIL TRAITOR','MOSCOW RUSSIA','YELLOWKNIFE']
res=[]
for nm in NAMES:
    L=len(re.sub(r'[^A-Z]','',nm.upper()))
    for on,nums in ORDERS.items():
        if max(nums)>L: continue
        s=idx(nm,nums)
        c,w=score(s)
        res.append((c,w,nm,on,s))
res.sort(reverse=True)
print('EN YAXSI 25 (sozluk ortuyu, soz sayi):')
for c,w,nm,on,s in res[:25]:
    print(f'  {c:.2f} {w:2d}  {nm:32s} {on:22s} {s}')
print()
print(f'(cemi {len(res)} kombinasiya sinandi; uzunlugu 14-den qisa adlar avtomatik atildi)')
