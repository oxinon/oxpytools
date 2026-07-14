"""Gemeinsame Helfer für alle ox-* Terminal-Tools."""
import os
import sys
import shutil


class C:
    """ANSI-Farbcodes für Terminal-Ausgabe."""
    RESET = "\033[0m"
    BOLD = "\033[1m"
    DIM = "\033[2m"
    GREEN = "\033[32m"
    BR_GREEN = "\033[92m"
    RED = "\033[31m"
    BR_RED = "\033[91m"
    YELLOW = "\033[33m"
    CYAN = "\033[36m"
    BR_CYAN = "\033[96m"
    GREY = "\033[90m"
    WHITE = "\033[97m"


def term_width(default=80):
    try:
        return shutil.get_terminal_size((default, 24)).columns
    except Exception:
        return default


def clear():
    os.system("cls" if os.name == "nt" else "clear")


def hr(char="─", width=None):
    width = width or term_width()
    print(C.GREY + (char * width) + C.RESET)


def die(msg, code=1):
    print(f"{C.BR_RED}[FEHLER]{C.RESET} {msg}", file=sys.stderr)
    sys.exit(code)
