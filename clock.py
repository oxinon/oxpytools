#!/usr/bin/env python3
"""
ox-clock — große Terminal-Digitaluhr

Portiert aus dem "clock"-Befehl des OXINON-Web-Terminals
(dort auf dem <canvas>-Spiele-Engine gezeichnet — hier als curses-TUI).

Steuerung:
    12    zwischen 24h- und 12h-Anzeige umschalten
    d     Datum ein-/ausblenden
    q     Beenden
"""
import curses
import time
from datetime import datetime

# 5x4 Punktraster pro Ziffer (1 = Block an), wie bei klassischen Digitaluhren.
FONT = {
    "0": ["1111", "1001", "1001", "1001", "1111"],
    "1": ["0010", "0010", "0010", "0010", "0010"],
    "2": ["1111", "0001", "1111", "1000", "1111"],
    "3": ["1111", "0001", "1111", "0001", "1111"],
    "4": ["1001", "1001", "1111", "0001", "0001"],
    "5": ["1111", "1000", "1111", "0001", "1111"],
    "6": ["1111", "1000", "1111", "1001", "1111"],
    "7": ["1111", "0001", "0001", "0001", "0001"],
    "8": ["1111", "1001", "1111", "1001", "1111"],
    "9": ["1111", "1001", "1111", "0001", "1111"],
    ":": ["0", "1", "0", "1", "0"],
    " ": ["00", "00", "00", "00", "00"],
}

BLOCK = "██"  # 2 Zeichen breit pro Punkt -> gedrungenere, "eckige" Optik


def render_lines(text):
    """Baut 5 Textzeilen aus dem übergebenen String (z.B. '14:32:07')."""
    rows = ["" for _ in range(5)]
    for ch in text:
        pattern = FONT.get(ch, FONT[" "])
        for r in range(5):
            rows[r] += "".join(BLOCK if bit == "1" else "  " for bit in pattern[r])
            rows[r] += "  "  # Abstand zur nächsten Ziffer
    return rows


def run_tui(stdscr):
    curses.curs_set(0)
    stdscr.nodelay(True)
    stdscr.timeout(200)
    curses.start_color()
    curses.use_default_colors()
    curses.init_pair(1, curses.COLOR_CYAN, -1)
    curses.init_pair(2, curses.COLOR_GREEN, -1)

    hour24 = True
    show_date = True

    while True:
        now = datetime.now()
        if hour24:
            time_str = now.strftime("%H:%M:%S")
        else:
            time_str = now.strftime("%I:%M:%S %p")

        lines = render_lines(time_str.replace(" AM", "").replace(" PM", ""))
        suffix = "" if hour24 else (" PM" if now.strftime("%p") == "PM" else " AM")

        stdscr.erase()
        h, w = stdscr.getmaxyx()
        block_w = len(lines[0])
        start_y = max(0, (h - 7) // 2)
        start_x = max(0, (w - block_w) // 2)

        for i, line in enumerate(lines):
            try:
                stdscr.addstr(start_y + i, start_x, line + suffix, curses.color_pair(2) | curses.A_BOLD)
            except curses.error:
                pass

        if show_date:
            date_str = now.strftime("%A, %d.%m.%Y")
            try:
                stdscr.addstr(start_y + 6, max(0, (w - len(date_str)) // 2), date_str,
                               curses.color_pair(1))
            except curses.error:
                pass

        footer = "12: 12h/24h umschalten   d: Datum   q: Beenden"
        try:
            stdscr.addstr(h - 1, max(0, (w - len(footer)) // 2), footer, curses.A_DIM)
        except curses.error:
            pass

        stdscr.refresh()

        try:
            key = stdscr.getch()
        except curses.error:
            key = -1

        if key == ord('q'):
            break
        elif key == ord('1') or key == ord('2'):
            hour24 = not hour24
        elif key == ord('d'):
            show_date = not show_date

        time.sleep(0.05)


def main():
    curses.wrapper(run_tui)


if __name__ == "__main__":
    try:
        main()
    except KeyboardInterrupt:
        pass
