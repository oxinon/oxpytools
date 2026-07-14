#!/usr/bin/env python3
"""
ox-tetris — Tetris im Terminal

Portiert aus dem "tetris"-Befehl des OXINON-Web-Terminals: 10x20-Feld,
7 klassische Tetrominos, +100 Punkte pro geräumter Reihe.

Steuerung:
    ← / →   bewegen
    ↑       drehen
    ↓       schneller fallen lassen
    q       Beenden
"""
import curses
import random
import sys
import time

COLS, ROWS = 10, 20
DROP_MS = 250

SHAPES = [
    ([[1, 1, 1, 1]], 1),                    # I
    ([[1, 1, 1], [0, 1, 0]], 2),            # T
    ([[1, 1, 1], [1, 0, 0]], 3),            # J
    ([[1, 1, 1], [0, 0, 1]], 4),            # L
    ([[1, 1], [1, 1]], 5),                  # O
    ([[1, 1, 0], [0, 1, 1]], 6),            # S
    ([[0, 1, 1], [1, 1, 0]], 7),            # Z
]

# Curses-Farbpaar je Piece-ID (1-7), grob an die Web-Farben angelehnt
COLOR_MAP = {
    1: curses.COLOR_CYAN,
    2: curses.COLOR_MAGENTA,
    3: curses.COLOR_BLUE,
    4: curses.COLOR_YELLOW,   # orange nicht verfügbar -> yellow
    5: curses.COLOR_WHITE,
    6: curses.COLOR_GREEN,
    7: curses.COLOR_RED,
}

CELL = "██"


class Piece:
    def __init__(self, matrix, pid):
        self.matrix = matrix
        self.id = pid
        self.x = 3
        self.y = 0


def new_piece():
    matrix, pid = random.choice(SHAPES)
    p = Piece([row[:] for row in matrix], pid)
    p.x = COLS // 2 - len(matrix[0]) // 2
    return p


def collides(board, piece, ax, ay, matrix=None):
    matrix = matrix if matrix is not None else piece.matrix
    for y, row in enumerate(matrix):
        for x, v in enumerate(row):
            if not v:
                continue
            nx, ny = piece.x + x + ax, piece.y + y + ay
            if nx < 0 or nx >= COLS or ny >= ROWS:
                return True
            if ny >= 0 and board[ny][nx]:
                return True
    return False


def lock_piece(board, piece, score):
    for y, row in enumerate(piece.matrix):
        for x, v in enumerate(row):
            if v and piece.y + y >= 0:
                board[piece.y + y][piece.x + x] = piece.id
    cleared = 0
    y = ROWS - 1
    while y >= 0:
        if all(board[y]):
            del board[y]
            board.insert(0, [0] * COLS)
            cleared += 1
        else:
            y -= 1
    return score + cleared * 100


def rotate(matrix):
    return [list(row) for row in zip(*matrix[::-1])]


def draw(stdscr, board, piece, score, game_over, colors):
    stdscr.erase()
    h, w = stdscr.getmaxyx()
    board_w = COLS * len(CELL)
    ox = max(0, (w - board_w - 20) // 2)
    oy = max(0, (h - ROWS - 3) // 2)

    stdscr.addstr(oy, ox, "OX-TETRIS", curses.A_BOLD)
    stdscr.addstr(oy, ox + board_w + 4, f"Score: {score}")
    stdscr.addstr(oy + 2, ox + board_w + 4, "←/→ move")
    stdscr.addstr(oy + 3, ox + board_w + 4, "↑ rotate")
    stdscr.addstr(oy + 4, ox + board_w + 4, "↓ drop")
    stdscr.addstr(oy + 5, ox + board_w + 4, "q quit")

    display = [row[:] for row in board]
    if not game_over:
        for y, row in enumerate(piece.matrix):
            for x, v in enumerate(row):
                if v and 0 <= piece.y + y < ROWS:
                    display[piece.y + y][piece.x + x] = piece.id

    # Grauer Rahmen rings um das Spielfeld, wie bei ox-snake
    try:
        stdscr.addstr(oy + 1, ox, "┌" + "─" * board_w + "┐", curses.color_pair(8))
        stdscr.addstr(oy + 2 + ROWS, ox, "└" + "─" * board_w + "┘", curses.color_pair(8))
        for y in range(ROWS):
            stdscr.addstr(oy + 2 + y, ox, "│", curses.color_pair(8))
            stdscr.addstr(oy + 2 + y, ox + 1 + board_w, "│", curses.color_pair(8))
    except curses.error:
        pass

    for y in range(ROWS):
        for x in range(COLS):
            cid = display[y][x]
            try:
                if cid:
                    stdscr.addstr(oy + 2 + y, ox + 1 + x * len(CELL), CELL,
                                   curses.color_pair(cid) | curses.A_BOLD)
                else:
                    stdscr.addstr(oy + 2 + y, ox + 1 + x * len(CELL), "  ")
            except curses.error:
                pass

    if game_over:
        msg = " GAME OVER — q zum Beenden "
        try:
            stdscr.addstr(oy + 2 + ROWS // 2, ox + 1 + max(0, (board_w - len(msg)) // 2), msg,
                           curses.A_REVERSE | curses.A_BOLD)
        except curses.error:
            pass

    stdscr.refresh()


def run(stdscr):
    curses.curs_set(0)
    stdscr.nodelay(True)
    curses.start_color()
    curses.use_default_colors()
    for pid, col in COLOR_MAP.items():
        curses.init_pair(pid, col, -1)
    curses.init_pair(8, curses.COLOR_WHITE, -1)  # grauer Rahmen, wie bei ox-snake

    board = [[0] * COLS for _ in range(ROWS)]
    piece = new_piece()
    score = 0
    game_over = False
    last_drop = time.time()

    while True:
        draw(stdscr, board, piece, score, game_over, COLOR_MAP)

        try:
            key = stdscr.getch()
        except curses.error:
            key = -1

        if key == ord('q'):
            break

        if not game_over:
            if key == curses.KEY_LEFT and not collides(board, piece, -1, 0):
                piece.x -= 1
            elif key == curses.KEY_RIGHT and not collides(board, piece, 1, 0):
                piece.x += 1
            elif key == curses.KEY_UP:
                r = rotate(piece.matrix)
                if not collides(board, piece, 0, 0, r):
                    piece.matrix = r
            elif key == curses.KEY_DOWN:
                last_drop = 0  # erzwingt sofortigen Fall-Tick unten

            if time.time() - last_drop >= DROP_MS / 1000:
                if not collides(board, piece, 0, 1):
                    piece.y += 1
                else:
                    score = lock_piece(board, piece, score)
                    piece = new_piece()
                    if collides(board, piece, 0, 0):
                        game_over = True
                last_drop = time.time()

        time.sleep(0.02)


def main():
    try:
        curses.wrapper(run)
    except KeyboardInterrupt:
        pass


if __name__ == "__main__":
    main()
