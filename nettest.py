#!/usr/bin/env python3
"""
ox-nettest — Network Diagnostic

Portiert aus dem "nettest"-Befehl des OXINON-Web-Terminals: testet vier
Gruppen von Endpunkten, um zu unterscheiden, ob ein Problem am eigenen
Netzwerk (Firewall/DNS/Proxy) liegt oder an einem einzelnen Dienst.

    CONTROL          bekannte, praktisch nie blockierte APIs
    DATA SERVICES     dieselben APIs, die ox-weather/ox-news/ox-ticker nutzen
    RADIO STREAMS     HEAD-Check jedes Hirschmilch-Streams
    IP / CONNECTIVITY  öffentliche IPv4/IPv6-Adresse via ipify
"""
import json
import socket
import sys
import time
import urllib.request
import urllib.error

from common import C, hr

TIMEOUT = 6

GROUPS = [
    ("CONTROL", [
        ("jsonplaceholder.typicode.com", "https://jsonplaceholder.typicode.com/todos/1", "GET", False),
        ("httpbin.org", "https://httpbin.org/json", "GET", False),
    ]),
    ("DATA SERVICES", [
        ("hn.algolia.com (News)", "https://hn.algolia.com/api/v1/search?tags=front_page&hitsPerPage=1", "GET", False),
        ("api.open-meteo.com (Weather)", "https://api.open-meteo.com/v1/forecast?latitude=53.55&longitude=9.99&current=temperature_2m", "GET", False),
        ("api.coingecko.com (Ticker)", "https://api.coingecko.com/api/v3/ping", "GET", False),
    ]),
    ("RADIO STREAMS", [
        ("Hirschmilch Prog-House", "https://xfer.hirschmilch.de:8001/prog-house.mp3", "HEAD", False),
        ("Hirschmilch Organic-House", "https://xfer.hirschmilch.de:8001/organic-house.mp3", "HEAD", False),
        ("Hirschmilch Techno", "https://xfer.hirschmilch.de:8001/techno.mp3", "HEAD", False),
        ("Hirschmilch Psytrance", "https://xfer.hirschmilch.de:8001/psytrance.mp3", "HEAD", False),
        ("Hirschmilch Progressive", "https://xfer.hirschmilch.de:8001/progressive.mp3", "HEAD", False),
        ("Hirschmilch Electronic", "https://xfer.hirschmilch.de:8001/electronic.mp3", "HEAD", False),
        ("Hirschmilch Hypnotic", "https://xfer.hirschmilch.de:8001/hypnotic.mp3", "HEAD", False),
        ("Hirschmilch Chillout", "https://xfer.hirschmilch.de:8001/chillout.mp3", "HEAD", False),
    ]),
    ("IP / CONNECTIVITY", [
        ("IPv4 (api.ipify.org)", "https://api.ipify.org?format=json", "GET", True),
        ("IPv6 (api6.ipify.org)", "https://api6.ipify.org?format=json", "GET", True),
    ]),
]


def run_test(url, method, is_ip):
    req = urllib.request.Request(url, method=method, headers={"User-Agent": "ox-nettest/1.0"})
    t0 = time.perf_counter()
    try:
        with urllib.request.urlopen(req, timeout=TIMEOUT) as res:
            ms = round((time.perf_counter() - t0) * 1000)
            if is_ip:
                data = json.loads(res.read().decode())
                return "ok", f"{data.get('ip', '?')} ({ms}ms)"
            return "ok", f"{ms}ms"
    except urllib.error.HTTPError as e:
        # HEAD auf Stream-Server antwortet manchmal mit Nicht-200, obwohl erreichbar
        ms = round((time.perf_counter() - t0) * 1000)
        if method == "HEAD":
            return "ok", f"{ms}ms"
        return "fail", f"HTTP {e.code}"
    except (urllib.error.URLError, socket.timeout, TimeoutError) as e:
        ms = round((time.perf_counter() - t0) * 1000)
        reason = "timeout" if "timed out" in str(e).lower() else ("no route" if is_ip else "blocked/network error")
        return "fail", f"{reason} ({ms}ms)"


def icon(state):
    if state == "ok":
        return f"{C.GREEN}[OK]  {C.RESET}"
    if state == "fail":
        return f"{C.BR_RED}[FAIL]{C.RESET}"
    return f"{C.GREY}[ -- ]{C.RESET}"


def main():
    print()
    print(f"{C.GREY}NETWORK DIAGNOSTIC v1.0{C.RESET}")
    hr()

    results = {}
    for label, tests in GROUPS:
        print(f"\n{C.GREY}{label}:{C.RESET}")
        for name, url, method, is_ip in tests:
            sys.stdout.write(f"  {icon('loading')} {name:<32}")
            sys.stdout.flush()
            state, detail = run_test(url, method, is_ip)
            results.setdefault(label, []).append(state)
            color = C.BR_RED if state == "fail" else C.WHITE
            print(f"\r  {icon(state)} {color}{name:<32}{C.RESET}{C.GREY}{detail}{C.RESET}")

    # Verdict
    ctrl = results.get("CONTROL", [])
    data = results.get("DATA SERVICES", [])
    controls_ok = all(s == "ok" for s in ctrl)
    controls_fail = all(s == "fail" for s in ctrl)
    data_ok = any(s == "ok" for s in data)

    if controls_fail:
        verdict, color = "Selbst Control-Domains sind fehlgeschlagen. Das deutet auf einen " \
                          "Adblocker, VPN, Firewall oder Proxy hin — nicht auf die Dienste selbst.", C.BR_RED
    elif controls_ok and not data_ok:
        verdict, color = "Controls waren erreichbar, Datendienste nicht. Entweder blockiert eine " \
                          "Filterliste gezielt diese Domains, oder die Dienste sind gerade down.", C.YELLOW
    elif controls_ok and data_ok:
        verdict, color = "Netzwerk sieht gesund aus. Control- und Datendomains sind erreichbar.", C.GREEN
    else:
        verdict, color = "Gemischtes Ergebnis — siehe Zeilen oben.", C.WHITE

    print()
    hr()
    print(f"{color}[!] {verdict}{C.RESET}")
    print()


if __name__ == "__main__":
    try:
        main()
    except KeyboardInterrupt:
        sys.exit(0)
