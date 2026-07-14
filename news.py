#!/usr/bin/env python3
"""
ox-news — Terminal-Newsfeed

Portiert aus dem "news"-Befehl des OXINON-Web-Terminals.
Datenquelle: Hacker News Algolia-API (hn.algolia.com) — kostenlos, kein API-Key.

Benutzung:
    ox-news                Front Page (Standard)
    ox-news -s newest      Neueste Storys
    ox-news -s ask         Ask HN
    ox-news -s show        Show HN
    ox-news --open 3       Öffnet Artikel #3 im Standard-Browser
"""
import argparse
import sys
import webbrowser
import urllib.request
import json

from common import C, die, hr

SOURCES = {
    "front": ("HN Front Page", "https://hn.algolia.com/api/v1/search?tags=front_page&hitsPerPage=9"),
    "newest": ("HN Newest", "https://hn.algolia.com/api/v1/search_by_date?tags=story&hitsPerPage=9"),
    "ask": ("HN Ask HN", "https://hn.algolia.com/api/v1/search_by_date?tags=ask_hn&hitsPerPage=9"),
    "show": ("HN Show HN", "https://hn.algolia.com/api/v1/search_by_date?tags=show_hn&hitsPerPage=9"),
}


def fetch(url):
    req = urllib.request.Request(url, headers={"User-Agent": "ox-news/1.0"})
    with urllib.request.urlopen(req, timeout=8) as res:
        return json.loads(res.read().decode())


def main():
    parser = argparse.ArgumentParser(
        prog="ox-news",
        description="Terminal-Newsfeed (Hacker News)",
    )
    parser.add_argument("-s", "--source", choices=SOURCES.keys(), default="front",
                         help="front | newest | ask | show (Standard: front)")
    parser.add_argument("--open", type=int, metavar="N",
                         help="Artikel Nummer N direkt im Browser öffnen")
    args = parser.parse_args()

    label, url = SOURCES[args.source]
    print(f"{C.GREY}Connecting to News Feed ({label}) ...{C.RESET}")
    try:
        data = fetch(url)
    except Exception as e:
        die(f"News Feed nicht erreichbar. ({e})")

    hits = data.get("hits", [])
    if not hits:
        print(f"{C.YELLOW}Keine Artikel gefunden.{C.RESET}")
        return

    if args.open is not None:
        idx = args.open - 1
        if idx < 0 or idx >= len(hits):
            die(f"Ungültige Auswahl '{args.open}'.")
        item = hits[idx]
        link = item.get("url") or f"https://news.ycombinator.com/item?id={item['objectID']}"
        print(f"{C.GREEN}Öffne:{C.RESET} {link}")
        webbrowser.open(link)
        return

    print()
    print(f"{C.BOLD}{label}{C.RESET}")
    hr()
    for i, item in enumerate(hits, start=1):
        title = item.get("title") or item.get("story_title") or "(ohne Titel)"
        points = item.get("points", 0) or 0
        comments = item.get("num_comments", 0) or 0
        author = item.get("author", "?")
        print(f"{C.BR_CYAN}[{i}]{C.RESET} {C.WHITE}{title}{C.RESET}")
        print(f"    {C.GREY}{points} pts · {comments} comments · by {author}{C.RESET}")
    hr()
    print(f"{C.GREY}Tipp: --open <Nr.> öffnet den Artikel im Browser.{C.RESET}")
    print()


if __name__ == "__main__":
    try:
        main()
    except KeyboardInterrupt:
        sys.exit(0)
