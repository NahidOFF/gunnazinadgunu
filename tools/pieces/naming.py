#!/usr/bin/env python3
"""Per-piece candidate names, ranked by how natural the name is for the picture.

Rank 0 is what an ordinary person would write first. The ranks are the whole point:
the feasibility test alone says yes to everything, so the discriminator has to be
"which answer needs the least far-fetched naming", not "which answer is possible".

Piece 6 is FEASTABLES on the user's identification.
"""
import re
def L(s): return re.sub(r'[^A-Z]','',s.upper())

# piece key -> (red index, blue index, [names in rank order])
PIECES = {
 'calendar': (2, 4, ['calendar','christmas','december','calendar page','desk calendar',
                     'notepad','date','xmas','christmas day','twenty fifth','holiday',
                     'spiral calendar','tear off calendar','advent calendar','december twenty five',
                     'day planner','wall calendar','diary','almanac']),
 'gnome':    (2,11, ['santas helper','garden gnome','christmas elf','christmas gnome',
                     'elf on the shelf','gingerbread man','father christmas','garden dwarf',
                     'roller skate','roller skater','snowboarder','christmas elves',
                     'woodland elf','christmas figure','holiday gnome','little helper',
                     'christmas ornament','garden statue']),
 'africa':   (4, 8, ['continent','map of africa','african continent','silhouette',
                     'potted plant','africa and plant','houseplant','seedling','greenery',
                     'shrubbery','vegetation','savannah','rainforest','madagascar',
                     'south africa','african bush','thatching','africa and bush',
                     'continent of africa','map and plant']),
 'bow':      (5, 7, ['glasses','butterfly','eyeglasses','spectacles','sunglasses',
                     'hair bow','gift bow','shoelaces','infinity','moustache','mustache',
                     'propeller','ribbon bow','bow ribbon','reading glasses','eyewear',
                     'bowknot','shoelace bow']),
 'oman':     (6, 5, ['flag of oman','oman flag','flag oman','omani flag','muscat',
                     'sultanate of oman','the flag of oman','omani']),
 'feast':    (6, 6, ['feastables','feastables bar','feastable','chocolate bar','chocolate',
                     'mrbeast bar','candy bar','feastables chocolate']),
 'rect':     (6, 8, ['brown square','rectangle','red rectangle','terracotta','maroon square',
                     'brown rectangle','red square','chocolate','chocolate bar','clay tablet',
                     'closed book','notebook','red brick','brick wall','front door',
                     'red carpet','textbook','orange square','brown block']),
 'frames':   (7, 1, ['mosquito net','file cabinet','filing cabinet','picture frame',
                     'framed picture','picture frames','windows','window pane','window screen',
                     'window screens','card index','mosquito','solar panel','solar panels',
                     'two windows','bookcase','bookshelf','drawers','chest of drawers',
                     'speakers','radiator','air vent','mesh screen','screen door']),
 'barn':     (7, 4, ['american barn','american flag','flag and barn','united states',
                     'america','farmhouse','stars and stripes','us flag and barn',
                     'old glory','red barn','american farm','barn and flag','flag united states']),
 'chart':    (8, 9, ['column chart','histogram','chart decreasing','down arrow',
                     'downward arrow','decreasing','statistics','bar chart down',
                     'arrow and chart','graph and arrow','chart increasing','downwards arrow',
                     'bar chart and arrow','column graph','vertical bar chart']),
 'snow':     (9, 5, ['cloud with snow','snow cloud','snowflake','snowstorm','snow shower',
                     'light snow','cloud and snow','snowy weather','snowing cloud',
                     'snowy cloud','snowfall cloud','winter cloud']),
 'joy':      (10,14,['face with tears of joy','tears of joy face','tears of joy emoji',
                     'laughing crying face','crying laughing face','laughing so hard',
                     'laughing with tears','laughing tears face','rolling on the floor laughing',
                     'laughing face with tears']),
 'eagle':    (7, 9, ['bald eagle','golden egg','golden eagle','american eagle',
                     'egg and eagle','eagle and egg','gold nugget','eagle and rock',
                     'bubo ascalaphus','pharaoh eagle owl','stone eagle','rock and eagle',
                     'gold and eagle','nugget and eagle','golden egg and eagle']),
 'p14':      (7, None, ['swimsuit','arrowhead','spearhead','tank top','plumb bob',
                     'guitar pick','triangle','pendant','one piece swimsuit','bathing suit',
                     'swimwear','swimming','black shape','dark shape','shield shape']),
}
ORDER = list(PIECES)

def options():
    """piece -> list of (rank, name, redLetter, blueLetter or None); impossible names dropped"""
    out = {}
    for k,(ri,bi,names) in PIECES.items():
        lst=[]
        for rank,nm in enumerate(names):
            c=L(nm)
            if len(c) < ri: continue
            if bi is not None and len(c) < bi: continue
            lst.append((rank, nm, c[ri-1], c[bi-1] if bi else None))
        if not lst: raise SystemExit('no viable name for '+k)
        out[k]=lst
    return out

if __name__=='__main__':
    for k,lst in options().items():
        ri,bi,_=PIECES[k]
        print('%-9s r%-2s b%-3s  %s'%(k,ri,bi if bi else '?',
              '  '.join('%s=%s/%s'%(n.split()[0][:9],r,b or '?') for _,n,r,b in lst[:6])))
