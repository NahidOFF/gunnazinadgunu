#!/usr/bin/env python3
"""GC8's answer was a city and a country -- one built from the red numerals, one from
the blue.  With fourteen pieces both strings are fourteen characters.  Search every
14-letter place string pair for one consistent with the pieces the sketch names."""
import geonamescache, re, unicodedata, itertools
from collections import Counter
gc=geonamescache.GeonamesCache()
def norm(s):
    s=unicodedata.normalize('NFKD',s)
    return re.sub(r'[^A-Z]','',s.upper())
cities=gc.get_cities(); countries=gc.get_countries(); usst=gc.get_us_states()
cc2={k:v['name'] for k,v in countries.items()}
st2={k:(v['name'] if isinstance(v,dict) else v) for k,v in usst.items()}
POOL={}
def add(d):
    n=norm(d)
    if len(n)==14: POOL.setdefault(n,d)
for c in cities.values():
    nm=c['name']; cc=c['countrycode']
    add(nm)
    if cc in cc2: add(nm+' '+cc2[cc])
    if cc=='US':
        s=st2.get(c.get('admin1code'))
        if s: add(nm+' '+s)
for v in cc2.values(): add(v)
for v in st2.values(): add(v)
print('14-char place strings:',len(POOL))

PIECES=[('Country','R','T'),('Calendar','A','E'),('Chocolate','L','L'),
        ('Snowing',None,None),('Square',None,None),('Thatching','T','N'),
        ('LaughEmoji','E','I'),('Glasses','S','S'),('ColumnChart','C','H'),
        ('Swimsuit','I',None),('AmerBarn','A','R'),('SantaHelper','A','L'),
        ('Bubo','S','A'),('MosqNet','T','M')]
FIX=[p for p in PIECES if p[1] is not None]
redneed=Counter(p[1] for p in FIX)
blueneed=Counter(p[2] for p in FIX if p[2] is not None)

def prefilter(pool, need):
    ok=[]
    for n in pool:
        c=Counter(n)
        if all(c[k]>=v for k,v in need.items()): ok.append(n)
    return ok
A_c=prefilter(POOL, redneed)
B_c=prefilter(POOL, blueneed)
print('red candidates',len(A_c),' blue candidates',len(B_c))

def match(A,B):
    """bijection of the 12 constrained pieces onto distinct positions of A/B"""
    slots=[]
    for nm,r,b in FIX:
        s=[i for i in range(14) if A[i]==r and (b is None or B[i]==b)]
        if not s: return None
        slots.append((nm,s))
    slots.sort(key=lambda x:len(x[1]))
    used=set(); res={}
    def rec(k):
        if k==len(slots): return True
        nm,s=slots[k]
        for i in s:
            if i in used: continue
            used.add(i); res[nm]=i
            if rec(k+1): return True
            used.discard(i); res.pop(nm,None)
        return False
    return dict(res) if rec(0) else None

hits=[]
for A in A_c:
    for B in B_c:
        if A==B: continue
        m=match(A,B)
        if m: hits.append((A,B,m))
print('HITS',len(hits))
for A,B,m in hits[:80]:
    print(f'RED  {A}  ({POOL[A]})\nBLUE {B}  ({POOL[B]})\n  {m}\n')
