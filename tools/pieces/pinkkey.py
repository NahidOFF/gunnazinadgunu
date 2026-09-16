#!/usr/bin/env python3
"""The pink desk sheet is a complete letter-to-number key built from Audubon plates.

Twenty-three rows of "plate number + Roman numeral". Look each plate up in Audubon's
Birds of America and take the INITIAL of the bird's name: the twenty-three initials are
twenty-three DIFFERENT letters -- the alphabet minus L, Q and X. That is not a
coincidence, it is the design.

The sheet's two odd lines are the completion:
  * no Audubon plate name begins with X, so the sheet writes "X VI" outright;
  * plate 424 is "Lazuli Finch, ..." which begins with L, so "424-6" supplies L = 6;
  * no plate begins with Q either, and the sheet does not supply it -- Q is unused.

So the sheet defines a number for 25 of the 26 letters.
"""
import json, re
D={p['plate']:p['name'] for p in json.load(open('/home/user/gunnazinadgunu/tools/pieces/audubon_plates.json'))}
R={'I':1,'II':2,'III':3,'IV':4,'V':5,'VI':6,'VII':7,'VIII':8,'IX':9,'X':10,'XI':11,'XIV':14}
SHEET=[(29,'III'),(39,'VI'),(42,'V'),(61,'II'),(74,'IX'),(76,'IV'),(81,'XIV'),(83,'XI'),
       (101,'II'),(102,'III'),(112,'IX'),(162,'V'),(184,'V'),(216,'I'),(225,'VI'),(235,'VIII'),
       (245,'VIII'),(246,'VIII'),(253,'XIV'),(275,'III'),(329,'X'),(337,'VI'),(358,'IX')]
KEY={}
for p,rn in SHEET:
    nm=D[p]; KEY[nm[0].upper()]=(R[rn],p,nm)
KEY['X']=(6,None,'given outright on the sheet as "X VI" -- no plate name starts with X')
KEY['L']=(6,424,D[424])                      # the sheet's "424-6"
if __name__=='__main__':
    print('%d letters keyed; missing: %s\n'%(len(KEY),
          ''.join(c for c in 'ABCDEFGHIJKLMNOPQRSTUVWXYZ' if c not in KEY)))
    for c in sorted(KEY):
        n,p,nm=KEY[c]
        print('  %s = %-2d   %s'%(c,n,('plate %-3d %s'%(p,nm[:52])) if p else nm))
    print('\nnumbers in letter order A..Z (Q absent):')
    print('  '+' '.join('%s%d'%(c,KEY[c][0]) for c in sorted(KEY)))
