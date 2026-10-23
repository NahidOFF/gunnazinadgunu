#!/usr/bin/env python3
"""Verify the owl reading against the two target strings.

The desk notes give the two phrases as word-length signatures: (5 2 7) = BIRDS OF
AMERICA and (3 6 4) = XOR SUPERB OWLS. Fourteen pieces carry a red numeral and
thirteen carry a blue one (the Tasmania piece has no blue), and BIRDSOFAMERICA is
fourteen letters while XORSUPERBOWLS is thirteen. So the jigsaw should spell exactly
those, one letter per numeral.

For each picture, try every candidate owl name -- common and scientific -- and search
for the ordering that produces both strings at once.
"""
import re, itertools, sys
def L(s): return re.sub(r'[^A-Z]','',s.upper())
RED  = 'BIRDSOFAMERICA'
BLUE = 'XORSUPERBOWLS'
# picture -> (red index, blue index or None, candidate names)
P = {
 'oman':   (6, 5, ['Strix butleri','Strix omanensis','Omani owl','Hume\'s owl','desert owl',
                   'Arabian eagle-owl','Bubo milesi','Arabian scops owl','Otus pamelae']),
 'cal25':  (2, 4, ['Ninox natalis','Christmas boobook','Christmas Island boobook',
                   'Christmas Island hawk-owl']),
 'choc':   (6, 6, ['Ninox randi','Chocolate boobook']),
 'snow':   (9, 5, ['Bubo scandiacus','Snowy owl','Nyctea scandiaca']),
 'square': (6, 8, ['Ninox ochracea','Ochre-bellied boobook','Ninox ios','Cinnabar boobook',
                   'Brown boobook','Ninox scutulata','Rufous owl','Ninox rufa',
                   'Reddish scops owl','Otus rufescens','Chestnut-backed owlet',
                   'Glaucidium castanonotum','Ninox burhani','Togian boobook']),
 'africa': (4, 7, ['Tyto capensis','African grass owl','Grass owl','African wood owl',
                   'Strix woodfordii']),
 'joy':    (10,14,['Sceloglaux albifacies','Laughing owl','Whekau','Laughing boobook']),
 'glass':  (5, 7, ['Pulsatrix perspicillata','Spectacled owl']),
 'chart':  (8, 9, ['Ninox strenua','Powerful owl','Surnia ulula','Northern hawk-owl',
                   'Glaucidium brasilianum','Ferruginous pygmy owl','Bar-bellied owl',
                   'Pulsatrix melanota','Band-bellied owl','Barred owl','Strix varia',
                   'Athene noctua','Little owl','Asio flammeus','Short-eared owl',
                   'Xenoglaux loweryi','Long-whiskered owlet','Taenioptynx brodiei',
                   'Collared owlet','Glaucidium gnoma','Northern pygmy-owl']),
 'tasman': (7, None,['Ninox leucopsis','Tasmanian boobook','Ninox novaeseelandiae leucopsis']),
 'barn':   (7, 4, ['Tyto alba','Barn owl','Common barn owl','American barn owl',
                   'Tyto furcata','Western barn owl','Tyto americana']),
 'elf':    (2, 11,['Micrathene whitneyi','Elf owl','Glaucidium gnoma','Gnome owl',
                   'Northern pygmy-owl','Athene cunicularia','Burrowing owl']),
 'eagle':  (7, 9, ['Bubo bengalensis','Rock eagle-owl','Indian eagle-owl','Bubo ascalaphus',
                   'Pharaoh eagle-owl','Bubo bubo','Eurasian eagle-owl','Ketupa blakistoni',
                   'Bubo shelleyi','Shelley\'s eagle-owl']),
 'door':   (7, 1, ['Strix varia','Barred owl','Ketupa sumatrana','Barred eagle-owl',
                   'Asio clamator','Striped owl']),
}
KEYS=list(P)
# per piece: list of (name, redLetter, blueLetter or None)
OPT={}
for k,(ri,bi,names) in P.items():
    o=[]
    for nm in names:
        c=L(nm)
        if len(c)<ri: continue
        if bi is not None and len(c)<bi: continue
        o.append((nm, c[ri-1], c[bi-1] if bi else None))
    OPT[k]=o
    print('%-7s r%-2s b%-4s %s'%(k,ri,bi,'  '.join('%s=%s/%s'%(n.split()[0][:11],r,b or '-') for n,r,b in o)))
print()

N=14
sols=[]
def search():
    for tpos in range(N):                      # where the no-blue piece sits
        # blue letter demanded at each position: BLUE consumed skipping tpos
        bl=[None]*N; bi=0
        for p in range(N):
            if p==tpos: continue
            bl[p]=BLUE[bi]; bi+=1
        if bi!=len(BLUE): continue
        # candidate pieces per position
        cand=[[] for _ in range(N)]
        for p in range(N):
            for k in KEYS:
                for nm,r,b in OPT[k]:
                    if r!=RED[p]: continue
                    if p==tpos:
                        if b is not None: continue
                    else:
                        if b!=bl[p]: continue
                    cand[p].append((k,nm))
        if any(not c for c in cand): continue
        order=sorted(range(N), key=lambda p: len(cand[p]))
        used=set(); assign={}
        def rec(i):
            if i==N: sols.append((tpos,dict(assign))); return
            p=order[i]
            for k,nm in cand[p]:
                if k in used: continue
                used.add(k); assign[p]=(k,nm)
                rec(i+1)
                used.discard(k); assign.pop(p,None)
                if len(sols)>50: return
        rec(0)
search()
print('solutions:',len(sols))
for tpos,a in sols[:6]:
    print('\n--- no-blue piece at position %d ---'%(tpos+1))
    for p in range(N):
        k,nm=a[p]
        ri,bi,_=P[k]
        c=L(nm)
        print('  %2d  RED %s  BLUE %s   %-8s %-26s (r%d,b%s)'%(
            p+1, RED[p], (c[bi-1] if bi else '-'), k, nm, ri, bi))
