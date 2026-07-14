#!/usr/bin/env python3
"""
ox-speedtest — Bandbreitentest

Portiert aus dem "speedtest"-Befehl des OXINON-Web-Terminals:
    Ping/Jitter : 5x Request gegen api.ipify.org
    Download    : GET  https://speed.cloudflare.com/__down?bytes=N
    Upload      : POST https://speed.cloudflare.com/__up

Keine Daten werden gesammelt oder gespeichert — alles läuft nur lokal,
genau wie in der Browser-Version.
"""
import os
import sys
import time
import urllib.request
import urllib.error

from common import C, hr

PING_URL = "https://api.ipify.org?format=json"
DOWN_URL = "https://speed.cloudflare.com/__down?bytes={}"
UP_URL = "https://speed.cloudflare.com/__up"


def measure_ping(n=5):
    times = []
    for _ in range(n):
        t0 = time.perf_counter()
        try:
            req = urllib.request.Request(PING_URL, headers={"User-Agent": "ox-speedtest/1.0"})
            with urllib.request.urlopen(req, timeout=6) as res:
                res.read()
            times.append((time.perf_counter() - t0) * 1000)
        except Exception:
            pass
    if not times:
        return -1, -1
    ping = round(sum(times) / len(times))
    jitter = round(max(times) - min(times)) if len(times) > 1 else 0
    return ping, jitter


def measure_download(min_s=5, max_s=15):
    total_bytes = 0
    start = time.perf_counter()
    chunk_bytes = 2 * 1024 * 1024  # 2 MB Start-Chunk
    try:
        while (time.perf_counter() - start) < max_s:
            t0 = time.perf_counter()
            req = urllib.request.Request(DOWN_URL.format(chunk_bytes),
                                          headers={"User-Agent": "ox-speedtest/1.0"})
            with urllib.request.urlopen(req, timeout=10) as res:
                data = res.read()
            dt = time.perf_counter() - t0
            total_bytes += len(data)
            elapsed = time.perf_counter() - start
            if elapsed >= min_s and dt < 0.5:
                break
            # Chunk vergrößern, falls die Anfrage sehr schnell war (schnelle Leitung)
            if dt < 1.0:
                chunk_bytes = min(chunk_bytes * 2, 25 * 1024 * 1024)
        elapsed = max(time.perf_counter() - start, 0.001)
        mbps = (total_bytes * 8 / 1_000_000) / elapsed
        return round(mbps, 1)
    except Exception:
        return -1


def measure_upload(min_s=5, max_s=10):
    total_bytes = 0
    start = time.perf_counter()
    chunk_bytes = 1 * 1024 * 1024
    payload = os.urandom(chunk_bytes)
    try:
        while (time.perf_counter() - start) < max_s:
            req = urllib.request.Request(UP_URL, data=payload, method="POST",
                                          headers={"User-Agent": "ox-speedtest/1.0",
                                                   "Content-Type": "application/octet-stream"})
            t0 = time.perf_counter()
            with urllib.request.urlopen(req, timeout=10) as res:
                res.read()
            dt = time.perf_counter() - t0
            total_bytes += len(payload)
            if (time.perf_counter() - start) >= min_s and dt < 0.5:
                break
        elapsed = max(time.perf_counter() - start, 0.001)
        mbps = (total_bytes * 8 / 1_000_000) / elapsed
        return round(mbps, 1)
    except Exception:
        return -1


def speed_bar(mbps, width=20):
    filled = min(round(mbps / 1000 * width), width) if mbps > 0 else 0
    bar = ""
    for i in range(width):
        pct = (i / width) * 100
        if i < filled:
            col = C.GREEN if pct < 60 else (C.YELLOW if pct < 80 else C.BR_RED)
            bar += col + "█" + C.RESET
        else:
            bar += C.GREY + "█" + C.RESET
    return bar


def main():
    print()
    print(f"{C.GREY}SPEEDTEST v1.0 — keine Daten werden gespeichert{C.RESET}")
    hr()

    print(f"{C.CYAN}[....] Messe Ping/Jitter ...{C.RESET}", end="\r")
    ping, jitter = measure_ping()
    if ping < 0:
        print(f"{C.BR_RED}[FAIL]{C.RESET} PING       n/a" + " " * 20)
    else:
        print(f"{C.GREEN}[OK]  {C.RESET} PING       {ping} ms")
        print(f"{C.GREEN}[OK]  {C.RESET} JITTER     {jitter} ms")

    print(f"{C.CYAN}[....] Messe Download ...{C.RESET}", end="\r")
    dl = measure_download()
    if dl < 0:
        print(f"{C.BR_RED}[FAIL]{C.RESET} DOWNLOAD   endpoint unreachable" + " " * 10)
    else:
        print(f"{C.GREEN}[OK]  {C.RESET} DOWNLOAD   {dl:>7.1f} Mbit/s  [{speed_bar(dl)}]")

    print(f"{C.CYAN}[....] Messe Upload ...{C.RESET}", end="\r")
    ul = measure_upload()
    if ul < 0:
        print(f"{C.BR_RED}[FAIL]{C.RESET} UPLOAD     endpoint unreachable" + " " * 10)
    else:
        print(f"{C.GREEN}[OK]  {C.RESET} UPLOAD     {ul:>7.1f} Mbit/s  [{speed_bar(ul)}]")

    print()
    hr()
    print()


if __name__ == "__main__":
    try:
        main()
    except KeyboardInterrupt:
        sys.exit(0)
