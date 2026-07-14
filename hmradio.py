#!/usr/bin/env python3
"""
ox-radio — Terminal-Radio-Tuner

Portiert aus dem "radio"-Befehl des OXINON-Web-Terminals.
Spielt die Hirschmilch-Streams über den externen Player `mpv` ab
(muss installiert sein: `sudo apt install mpv`).

Steuerung:
    ↑ / ↓      Sender wählen
    Enter      Play / Stop
    + / -      Lautstärke
    q          Beenden
"""
import curses
import json
import os
import shutil
import socket
import subprocess
import sys
import tempfile
import time

from common import die

STATIONS = [
    {"name": "Hirschmilch Prog-House", "url": "https://xfer.hirschmilch.de:8001/prog-house.mp3"},
    {"name": "Hirschmilch Organic-House", "url": "https://xfer.hirschmilch.de:8001/organic-house.mp3"},
    {"name": "Hirschmilch Techno", "url": "https://xfer.hirschmilch.de:8001/techno.mp3"},
    {"name": "Hirschmilch Psytrance", "url": "https://xfer.hirschmilch.de:8001/psytrance.mp3"},
    {"name": "Hirschmilch Progressive", "url": "https://xfer.hirschmilch.de:8001/progressive.mp3"},
    {"name": "Hirschmilch Electronic", "url": "https://xfer.hirschmilch.de:8001/electronic.mp3"},
    {"name": "Hirschmilch Hypnotic", "url": "https://xfer.hirschmilch.de:8001/hypnotic.mp3"},
    {"name": "Hirschmilch Chillout", "url": "https://xfer.hirschmilch.de:8001/chillout.mp3"},
]


class MpvPlayer:
    """Startet mpv headless mit einer IPC-Socket-Datei, damit Lautstärke
    live per JSON-Kommando geändert werden kann, ohne den Stream neu
    zu verbinden."""

    def __init__(self):
        self.proc = None
        self.sock_path = os.path.join(tempfile.gettempdir(), f"ox-mpv-{os.getpid()}.sock")
        self.volume = 50

    def play(self, url):
        self.stop()
        self.proc = subprocess.Popen(
            [
                "mpv", "--no-video", "--no-terminal",
                f"--input-ipc-server={self.sock_path}",
                f"--volume={self.volume}",
                url,
            ],
            stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL,
        )
        # kurz warten, bis die IPC-Socket-Datei existiert
        for _ in range(20):
            if os.path.exists(self.sock_path):
                break
            time.sleep(0.1)

    def stop(self):
        if self.proc and self.proc.poll() is None:
            self.proc.terminate()
            try:
                self.proc.wait(timeout=2)
            except subprocess.TimeoutExpired:
                self.proc.kill()
        self.proc = None
        if os.path.exists(self.sock_path):
            try:
                os.remove(self.sock_path)
            except OSError:
                pass

    def is_playing(self):
        return self.proc is not None and self.proc.poll() is None

    def set_volume(self, vol):
        self.volume = max(0, min(100, vol))
        if not self.is_playing() or not os.path.exists(self.sock_path):
            return
        try:
            with socket.socket(socket.AF_UNIX, socket.SOCK_STREAM) as s:
                s.settimeout(0.5)
                s.connect(self.sock_path)
                cmd = json.dumps({"command": ["set_property", "volume", self.volume]}) + "\n"
                s.sendall(cmd.encode())
        except OSError:
            pass


def draw_box(stdscr, y, x, h, w, title=None, border_pair=3):
    """Zeichnet eine htop-artige Box mit Titel in der oberen Kante."""
    try:
        stdscr.addstr(y, x, "┌" + "─" * (w - 2) + "┐", curses.color_pair(border_pair))
        for i in range(1, h - 1):
            stdscr.addstr(y + i, x, "│", curses.color_pair(border_pair))
            stdscr.addstr(y + i, x + w - 1, "│", curses.color_pair(border_pair))
        stdscr.addstr(y + h - 1, x, "└" + "─" * (w - 2) + "┘", curses.color_pair(border_pair))
        if title:
            label = f" {title} "
            stdscr.addstr(y, x + 2, label, curses.color_pair(border_pair) | curses.A_BOLD)
    except curses.error:
        pass


def run_tui(stdscr):
    curses.curs_set(0)
    stdscr.nodelay(True)
    stdscr.timeout(300)
    curses.start_color()
    curses.use_default_colors()
    curses.init_pair(1, curses.COLOR_BLACK, curses.COLOR_GREEN)   # Header-Bar (wie htop)
    curses.init_pair(2, curses.COLOR_GREEN, -1)                   # PLAYING-Status
    curses.init_pair(3, curses.COLOR_CYAN, -1)                    # Box-Rahmen
    curses.init_pair(4, curses.COLOR_BLACK, curses.COLOR_CYAN)    # ausgewählte Zeile
    curses.init_pair(5, curses.COLOR_GREEN, -1)                   # Meter grün
    curses.init_pair(6, curses.COLOR_YELLOW, -1)                  # Meter gelb
    curses.init_pair(7, curses.COLOR_RED, -1)                     # Meter rot / STOPPED
    curses.init_pair(8, curses.COLOR_WHITE, -1)                   # normaler Text

    player = MpvPlayer()
    selected = 0
    status_msg = "Bereit."

    box_w = max(len(s["name"]) for s in STATIONS) + 8
    box_w = max(box_w, 40)
    stations_h = len(STATIONS) + 2
    nowplaying_h = 4

    try:
        while True:
            stdscr.erase()
            h, w = stdscr.getmaxyx()
            box_w_eff = min(box_w, max(w - 4, 20))

            # ── Header-Bar (wie htop: farbiger Balken über volle Breite) ──
            state = "PLAYING" if player.is_playing() else "STOPPED"
            header = " OX-RADIO TUNER".ljust(w - len(state) - 2) + state + " "
            try:
                stdscr.addstr(0, 0, header[:w], curses.color_pair(1) | curses.A_BOLD)
            except curses.error:
                pass

            y = 2
            # ── Box: Senderliste ──
            draw_box(stdscr, y, 1, stations_h, box_w_eff, title="Stations")
            for i, st in enumerate(STATIONS):
                row = y + 1 + i
                playing_here = player.is_playing() and i == selected
                marker = "▶" if playing_here else " "
                text = f" {marker} {i + 1:>2}  {st['name']}"
                text = text[:box_w_eff - 2].ljust(box_w_eff - 2)
                try:
                    if i == selected:
                        stdscr.addstr(row, 2, text, curses.color_pair(4) | curses.A_BOLD)
                    else:
                        col = curses.color_pair(2) if playing_here else curses.color_pair(8)
                        stdscr.addstr(row, 2, text, col)
                except curses.error:
                    pass

            y += stations_h + 1
            # ── Box: Now Playing / Volume (htop-Meter-Optik) ──
            draw_box(stdscr, y, 1, nowplaying_h, box_w_eff, title="Now Playing")
            now_name = STATIONS[selected]["name"] if player.is_playing() else "—"
            state_pair = curses.color_pair(2) if player.is_playing() else curses.color_pair(7)
            state_txt = "PLAYING" if player.is_playing() else "STOPPED"
            try:
                stdscr.addstr(y + 1, 3, f"[{state_txt}]", state_pair | curses.A_BOLD)
                stdscr.addstr(y + 1, 14, now_name[:box_w_eff - 16])

                bar_w = box_w_eff - 14
                filled = round(player.volume / 100 * bar_w)
                stdscr.addstr(y + 2, 3, "Vol", curses.color_pair(8))
                stdscr.addstr(y + 2, 7, "[", curses.color_pair(3))
                for i in range(bar_w):
                    pct = (i / bar_w) * 100
                    ch = "|" if i < filled else " "
                    pair = 5 if pct < 60 else (6 if pct < 85 else 7)
                    stdscr.addstr(y + 2, 8 + i, ch, curses.color_pair(pair) | curses.A_BOLD)
                stdscr.addstr(y + 2, 8 + bar_w, f"] {player.volume:>3}%", curses.color_pair(8))
            except curses.error:
                pass

            y += nowplaying_h + 1
            try:
                stdscr.addstr(y, 2, status_msg[:w - 4], curses.color_pair(8) | curses.A_DIM)
                stdscr.addstr(y + 1, 2, "↑/↓ wählen   Enter Play/Stop   +/- Lautstärke   q Beenden",
                               curses.color_pair(3))
            except curses.error:
                pass

            stdscr.refresh()

            try:
                key = stdscr.getch()
            except curses.error:
                key = -1

            if key in (curses.KEY_UP, ord('k')):
                selected = (selected - 1) % len(STATIONS)
            elif key in (curses.KEY_DOWN, ord('j')):
                selected = (selected + 1) % len(STATIONS)
            elif key in (10, 13, curses.KEY_ENTER):
                if player.is_playing():
                    player.stop()
                    status_msg = "Stopped."
                else:
                    status_msg = f"Connecting to {STATIONS[selected]['name']} ..."
                    stdscr.refresh()
                    player.play(STATIONS[selected]["url"])
                    status_msg = f"Now playing: {STATIONS[selected]['name']}"
            elif key in (ord('+'), ord('=')):
                player.set_volume(player.volume + 5)
            elif key in (ord('-'), ord('_')):
                player.set_volume(player.volume - 5)
            elif key == ord('q'):
                break
    finally:
        player.stop()


def main():
    if not shutil.which("mpv"):
        die("mpv ist nicht installiert. Bitte installieren mit:  sudo apt install mpv")
    try:
        curses.wrapper(run_tui)
    except KeyboardInterrupt:
        pass


if __name__ == "__main__":
    main()
