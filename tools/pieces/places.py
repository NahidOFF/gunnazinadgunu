#!/usr/bin/env python3
"""The author's previous puzzle answered in place names, so score every 14-letter place
string by the naming cost the pieces would need to spell it."""
import sys, re, unicodedata
import geonamescache
sys.path.insert(0,'/home/user/gunnazinadgunu/tools/pieces')
from mincost import solve, detail, other_string
def norm(s):
    s=unicodedata.normalize('NFKD',s)
    return re.sub(r'[^A-Z]','',s.upper())
gc=geonamescache.GeonamesCache()
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
print('14-letter place strings:',len(POOL))
colour = sys.argv[1] if len(sys.argv)>1 else 'red'
res=[]
for n,disp in POOL.items():
    s=solve(n,colour)
    if s: res.append((s[0],disp,n,s[1]))
res.sort()
print('reachable at all:',len(res))
for tot,disp,n,assign in res[:40]:
    print('cost %5.1f  %-34s other colour: %s'%(tot,disp,other_string(n,assign,colour)))
