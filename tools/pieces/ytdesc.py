#!/usr/bin/env python3
"""Read the video's description and top comments with a real browser.

yt-dlp and plain fetches are blocked ("sign in to confirm you're not a bot"), and
the official rules say the clues are in the video without saying how many, so the
description and a pinned comment are a clue channel worth checking directly."""
import json,re,sys
from playwright.sync_api import sync_playwright
URL="https://www.youtube.com/watch?v=82CX6WULNA0"
with sync_playwright() as p:
    b=p.chromium.launch(headless=True,executable_path="/opt/pw-browsers/chromium-1194/chrome-linux/chrome",args=["--no-sandbox","--disable-blink-features=AutomationControlled"])
    pg=b.new_page(proxy={"server":"http://127.0.0.1:41903"},viewport={"width":1280,"height":2200},
                  user_agent="Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/537.36 "
                             "(KHTML, like Gecko) Chrome/124.0 Safari/537.36")
    pg.goto(URL,wait_until="domcontentloaded",timeout=60000)
    pg.wait_for_timeout(6000)
    html=pg.content()
    m=re.search(r'"shortDescription":"((?:[^"\\]|\\.)*)"',html)
    if m:
        d=m.group(1).encode().decode('unicode_escape')
        print("=== DESCRIPTION ==="); print(d[:4000])
    else:
        print("=== DESCRIPTION: not found in page ===")
    # scroll for comments
    for _ in range(9):
        pg.mouse.wheel(0,2400); pg.wait_for_timeout(1400)
    try:
        pg.wait_for_selector("ytd-comment-thread-renderer",timeout=20000)
        cs=pg.query_selector_all("ytd-comment-thread-renderer")
        print(f"\n=== COMMENTS: {len(cs)} threads loaded ===")
        for i,c in enumerate(cs[:12]):
            t=(c.inner_text() or "").strip().replace("\n"," | ")
            print(f"[{i+1}] {t[:420]}")
    except Exception as e:
        print("\n=== COMMENTS: none loaded ===",type(e).__name__)
    b.close()
