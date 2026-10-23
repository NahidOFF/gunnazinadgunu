#!/usr/bin/env python3
"""Tools for the MrBeast $10k puzzle: morse decode, phone-code, what3words check."""
import re, sys, subprocess, time

MORSE = {
 '.-':'A','-...':'B','-.-.':'C','-..':'D','.':'E','..-.':'F','--.':'G','....':'H',
 '..':'I','.---':'J','-.-':'K','.-..':'L','--':'M','-.':'N','---':'O','.--.':'P',
 '--.-':'Q','.-.':'R','...':'S','-':'T','..-':'U','...-':'V','.--':'W','-..-':'X',
 '-.--':'Y','--..':'Z','-----':'0','.----':'1','..---':'2','...--':'3','....-':'4',
 '.....':'5','-....':'6','--...':'7','---..':'8','----.':'9'}
REV = {v:k for k,v in MORSE.items()}
PHONE = {'2':'ABC','3':'DEF','4':'GHI','5':'JKL','6':'MNO','7':'PQRS','8':'TUV','9':'WXYZ',
         '0':'','1':''}
PHONE_OLD = {'2':'ABC','3':'DEF','4':'GHI','5':'JKL','6':'MNO','7':'PRS','8':'TUV','9':'WXY'}

def morse_decode(s):
    """s: groups separated by space or /, e.g. '-.- .- -... ..- .-..'"""
    out=[]
    for tok in re.split(r'[\s/|]+', s.strip()):
        if not tok: continue
        out.append(MORSE.get(tok,'?'))
    return ''.join(out)

def morse_encode(s):
    return ' '.join(REV.get(c.upper(),'?') for c in s if c.strip())

def w3w(addr, retries=3):
    for i in range(retries):
        try:
            r=subprocess.run(['curl','-sS','-m','30','-A','Mozilla/5.0 (Windows NT 10.0; Win64; x64)',
                              f'https://what3words.com/{addr}'],capture_output=True,text=True,timeout=45)
            m=re.search(r'og:description" content="([^"]*)"', r.stdout)
            if m: return m.group(1)
            if 'could not be satisfied' in r.stdout: time.sleep(5+5*i); continue
            return None
        except Exception as e:
            time.sleep(3)
    return None

if __name__=='__main__':
    if len(sys.argv)>2 and sys.argv[1]=='morse':
        print(morse_decode(' '.join(sys.argv[2:])))
    elif len(sys.argv)>2 and sys.argv[1]=='enc':
        print(morse_encode(' '.join(sys.argv[2:])))
    elif len(sys.argv)>2 and sys.argv[1]=='w3w':
        for a in sys.argv[2:]:
            print(a, '->', w3w(a))
    else:
        print(__doc__)
