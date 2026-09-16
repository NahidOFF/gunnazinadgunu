#!/usr/bin/env python3
"""Rank Noto emoji against a picture crop using colour histogram + shape mask.
usage: emomatch2.py CROP.png [topN]"""
import sys, numpy as np, cv2
from PIL import Image, ImageFont, ImageDraw
FONT='/usr/share/fonts/truetype/noto/NotoColorEmoji.ttf'; SZ=109
font=ImageFont.truetype(FONT,SZ)
CANDS=("😂 🤣 😅 🇴🇲 🇺🇸 🌨️ ☃️ ❄️ 🌧️ ⛅ ☁️ 🎀 🎗️ 🦋 🟥 🟫 🟧 🟦 🪟 🚪 🖼️ 🪞 📊 📈 📉 ⬇️ ⬆️ ➡️ 🗡️ "
       "📅 🗓️ 📆 🛼 ⛸️ 🛹 🧝 🎅 🧙 🧚 🪨 🦅 🦆 🐦 🦉 🌿 🌱 🌳 🌲 ☘️ 🍀 🥔 🥜 🌍 🌎 🌏 🏠 🏚️ ⛪ 🏭 "
       "🧱 🍫 📕 📗 📘 📙 🚩 🏳️ 🎌 🔋 🧴 🧃 🥤 🖊️ ✏️ 🕯️ 🌡️ 🔦 🎁 💼 📦 🪵 🧀 🍞 🥖 🏈 🥚 🦴 🍄").split()
def render(e):
    img=Image.new('RGBA',(SZ+40,SZ+40),(0,0,0,0)); ImageDraw.Draw(img).text((20,20),e,font=font,embedded_color=True)
    a=np.array(img)
    if a[...,3].max()==0: return None
    ys,xs=np.nonzero(a[...,3]>16)
    a=a[ys.min():ys.max()+1, xs.min():xs.max()+1]
    rgb=a[...,:3].astype(np.float32); al=a[...,3:4]/255.0
    comp=(rgb*al+255*(1-al)).astype(np.uint8)
    return cv2.cvtColor(comp,cv2.COLOR_RGB2BGR)
def prep(bgr, N=40):
    h,w=bgr.shape[:2]; s=N/max(h,w)
    r=cv2.resize(bgr,(max(1,int(w*s)),max(1,int(h*s))),interpolation=cv2.INTER_AREA)
    out=np.full((N,N,3),255,np.uint8)
    y0=(N-r.shape[0])//2; x0=(N-r.shape[1])//2
    out[y0:y0+r.shape[0], x0:x0+r.shape[1]]=r
    lab=cv2.cvtColor(out,cv2.COLOR_BGR2LAB).astype(np.float32)
    L,A,B=lab[...,0],lab[...,1]-128,lab[...,2]-128
    # chroma-normalise: print on paper is far less saturated than a font glyph
    C=np.hypot(A,B); c95=np.percentile(C,97)
    if c95>2: A=A*(45.0/c95); B=B*(45.0/c95); C=np.hypot(A,B)
    Lo,Lhi=np.percentile(L,3),np.percentile(L,99)
    L=np.clip((L-Lo)*(100.0/max(Lhi-Lo,1))*2.55,0,255)
    ink=((L<225)&((C>10)|(L<185)))                               # non-paper
    # colour histogram over ink pixels: 8 hue bins x 3 lightness bins
    hue=(np.degrees(np.arctan2(B,A))+360)%360
    hist=np.zeros(8*3+1,np.float32)
    if ink.sum()>0:
        hb=(hue[ink]//45).astype(int).clip(0,7); lb=(L[ink]//86).astype(int).clip(0,2)
        for a_,b_ in zip(hb,lb): hist[a_*3+b_]+=1
        hist/=ink.sum()
    hist[-1]=ink.mean()
    return hist, ink.astype(np.float32)
crop=cv2.imread(sys.argv[1]); topN=int(sys.argv[2]) if len(sys.argv)>2 else 10
f=crop.astype(np.float32).reshape(-1,3)
pap=f[np.argsort(f.sum(1))[-max(20,int(0.12*len(f))):]].mean(0)
crop=np.clip(crop.astype(np.float32)*(np.array([240.,240.,240.])/np.maximum(pap,1)),0,255).astype(np.uint8)
ch,cm=prep(crop)
rows=[]
for e in CANDS:
    b=render(e)
    if b is None: continue
    eh,em=prep(b)
    hs=float(np.minimum(ch,eh).sum())                        # histogram intersection
    a1=cm-cm.mean(); a2=em-em.mean()
    ss=float((a1*a2).sum()/(np.sqrt((a1*a1).sum()*(a2*a2).sum())+1e-6))
    rows.append((0.55*hs+0.45*max(ss,0), hs, ss, e))
rows.sort(reverse=True)
for t,hs,ss,e in rows[:topN]: print(f'  {t:.3f}  (hist {hs:.2f} shape {ss:+.2f})  {e}')
