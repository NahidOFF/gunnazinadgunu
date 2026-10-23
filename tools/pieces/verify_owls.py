#!/usr/bin/env python3
"""Full verification of the jigsaw stage.

Every picture is an owl species, and the numerals index into its SCIENTIFIC name
(letters only, 1-indexed). Fourteen red numerals spell BIRDS OF AMERICA; the thirteen
blue ones -- the Tasmania piece carries no blue numeral -- spell XOR SUPERB OWLS.
Both are exactly the word-length signatures written on the desk notes, (5 2 7) and
(3 6 4).
"""
import re
def L(s): return re.sub(r'[^A-Z]','',s.upper())
# position: (picture, common name, scientific name, red index, blue index or None)
SOLUTION = [
 ( 1,'flag of Oman',            'Omani owl',            'Strix butleri',           6, 5),
 ( 2,'calendar showing 25',     'Christmas boobook',    'Ninox natalis',           2, 4),
 ( 3,'Feastables chocolate bar','Chocolate boobook',    'Ninox randi',             6, 6),
 ( 4,'cloud with snow',         'Snowy owl',            'Bubo scandiacus',         9, 5),
 ( 5,'brown square',            'Brown boobook',        'Ninox scutulata',         6, 8),
 ( 6,'Africa + grass',          'African grass owl',    'Tyto capensis',           4, 7),
 ( 7,'face with tears of joy',  'Laughing owl',         'Ninox albifacies',       10,14),
 ( 8,'glasses',                 'Spectacled owl',       'Pulsatrix perspicillata', 5, 7),
 ( 9,'down arrow + bar chart',  'Least boobook',        'Ninox sumbaensis',        8, 9),
 (10,'Tasmania',                'Tasmanian boobook',    'Ninox leucopsis',         7, None),
 (11,'US flag + barn',          'American barn owl',    'Tyto furcata',            7, 4),
 (12,'gnome / elf figure',      'Elf owl',              'Micrathene whitneyi',     2,11),
 (13,'stone + eagle',           'Pharaoh eagle-owl',    'Bubo ascalaphus',         7, 9),
 (14,'barred door',             'Barred owl',           'Strix varia',             7, 1),
]
red=[]; blue=[]
print('%-3s %-24s %-19s %-24s %-9s %s'%('pos','picture','owl','scientific name','red','blue'))
for pos,pic,common,sci,ri,bi in SOLUTION:
    c=L(sci)
    assert len(c)>=ri, (sci,ri)
    r=c[ri-1]; red.append(r)
    if bi is None:
        b='-'
    else:
        assert len(c)>=bi, (sci,bi)
        b=c[bi-1]; blue.append(b)
    print('%-3d %-24s %-19s %-24s r%-2d=%s   %s'%(pos,pic,common,sci,ri,r,('b%d=%s'%(bi,b)) if bi else '(no blue numeral)'))
R=''.join(red); B=''.join(blue)
print('\nRED  (14 numerals): %s'%R)
print('BLUE (13 numerals): %s'%B)
print('\nRED  == BIRDSOFAMERICA : %s'%(R=='BIRDSOFAMERICA'))
print('BLUE == XORSUPERBOWLS  : %s'%(B=='XORSUPERBOWLS'))
print('\nDesk-note signatures: BIRDS(5) OF(2) AMERICA(7) = (5 2 7)  |  XOR(3) SUPERB(6) OWLS(4) = (3 6 4)')
boobooks=[s for s in SOLUTION if 'boobook' in s[2].lower()]
print('boobooks among the fourteen: %d  -> %s'%(len(boobooks),', '.join(s[2] for s in boobooks)))
print('   (the desk "Boo!" book was captioned "five of these": boo + book)')
import hashlib
h=hashlib.sha256(b'FANTASTIC HEDWIG').hexdigest()
print('\nSHA256("FANTASTIC HEDWIG") = %s'%h)
print('committed by u/CiviledXI     = b74ded47baecf147821e2bcaa97c4735d5002cc37dc7e7fe93ea3845872dde22')
print('match: %s'%(h=='b74ded47baecf147821e2bcaa97c4735d5002cc37dc7e7fe93ea3845872dde22'))
