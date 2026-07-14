#!/usr/bin/env python3
"""
ox-snake — Snake im Terminal

Portiert aus dem "snake"-Befehl des OXINON-Web-Terminals: 30x20-Feld,
+10 Punkte pro Apfel, Kollision mit Rand oder eigenem Körper beendet das Spiel.

Steuerung:
    ↑ ↓ ← →   Richtung
    q         Beenden
"""
import curses
import random
import sys
import time

COLS, ROWS = 30, 20
TICK_MS = 110


def run(stdscr):
    curses.curs_set(0)
    stdscr.nodelay(True)
    curses.start_color()
    curses.use_default_colors()
    curses.init_pair(1, curses.COLOR_GREEN, -1)   # snake
    curses.init_pair(2, curses.COLOR_RED, -1)     # apple
    curses.init_pair(3, curses.COLOR_WHITE, -1)   # border/text

    snake = [(5, 5), (4, 5)]
    direction = (1, 0)
    pending_dir = direction
    apple = (12, 8)
    score = 0
    game_over = False
    last_tick = time.time()

    def rand_apple():
        while True:
            p = (random.randint(1, COLS - 2), random.randint(1, ROWS - 2))
            if p not in snake:
                return p

    while True:
        stdscr.erase()
        h, w = stdscr.getmaxyx()
        ox = max(0, (w - COLS * 2 - 20) // 2)
        oy = max(0, (h - ROWS - 2) // 2)

        stdscr.addstr(oy, ox, "OX-SNAKE", curses.A_BOLD)
        stdscr.addstr(oy, ox + COLS * 2 + 4, f"Score: {score}")
        stdscr.addstr(oy + 2, ox + COLS * 2 + 4, "arrows move")
        stdscr.addstr(oy + 3, ox + COLS * 2 + 4, "q quit")

        try:
            stdscr.addstr(oy + 1, ox, "┌" + "─" * (COLS * 2) + "┐", curses.color_pair(3))
            stdscr.addstr(oy + 2 + ROWS, ox, "└" + "─" * (COLS * 2) + "┘", curses.color_pair(3))
            for y in range(ROWS):
                stdscr.addstr(oy + 2 + y, ox, "│", curses.color_pair(3))
                stdscr.addstr(oy + 2 + y, ox + 1 + COLS * 2, "│", curses.color_pair(3))
        except curses.error:
            pass

        for i, (sx, sy) in enumerate(snake):
            ch = "██" if i > 0 else "▓▓"
            try:
                stdscr.addstr(oy + 2 + sy, ox + 1 + sx * 2, ch, curses.color_pair(1) | curses.A_BOLD)
            except curses.error:
                pass
        try:
            stdscr.addstr(oy + 2 + apple[1], ox + 1 + apple[0] * 2, "●●", curses.color_pair(2) | curses.A_BOLD)
        except curses.error:
            pass

        if game_over:
            msg = f" GAME OVER — Score {score} — q zum Beenden "
            try:
                stdscr.addstr(oy + 2 + ROWS // 2, ox + max(0, (COLS * 2 - len(msg)) // 2), msg,
                               curses.A_REVERSE | curses.A_BOLD)
            except curses.error:
                pass

        stdscr.refresh()

        try:
            key = stdscr.getch()
        except curses.error:
            key = -1

        if key == ord('q'):
            break
        elif key == curses.KEY_UP and direction != (0, 1):
            pending_dir = (0, -1)
        elif key == curses.KEY_DOWN and direction != (0, -1):
            pending_dir = (0, 1)
        elif key == curses.KEY_LEFT and direction != (1, 0):
            pending_dir = (-1, 0)
        elif key == curses.KEY_RIGHT and direction != (-1, 0):
            pending_dir = (1, 0)

        if not game_over and time.time() - last_tick >= TICK_MS / 1000:
            direction = pending_dir
            head = (snake[0][0] + direction[0], snake[0][1] + direction[1])
            if (head[0] < 0 or head[0] >= COLS or head[1] < 0 or head[1] >= ROWS
                    or head in snake):
                game_over = True
            else:
                snake.insert(0, head)
                if head == apple:
                    score += 10
                    apple = rand_apple()
                else:
                    snake.pop()
            last_tick = time.time()

        time.sleep(0.02)


def main():
    try:
        curses.wrapper(run)
    except KeyboardInterrupt:
        pass


if __name__ == "__main__":
    main()
