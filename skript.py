#!/usr/bin/env python3
"""
skript — Script Executer

Portiert aus dem "script"-Befehl des OXINON-Web-Terminals: eine Liste
vorgefertigter Sysadmin-Einzeiler (a-z). Im Web wurde nur in die
Zwischenablage kopiert; hier auf einem echten Terminal kannst du sie
zusätzlich direkt ausführen (immer mit Bestätigung — nichts läuft
automatisch, gerade weil ein paar Kommandos hier bewusst destruktiv sind:
Reboot, Auth-Log leeren, IPTables flushen, ...).

Benutzung:
    skript             interaktive Liste
    skript a           zeigt Snippet 'a' direkt (ohne Menü)
    skript a --run     führt Snippet 'a' direkt aus (mit Bestätigung)
"""
import argparse
import shutil
import subprocess
import sys

from common import C, hr, die

SCRIPTS = {
    'a': ("Docker Install", "curl -fsSL https://get.docker.com -o get-docker.sh && sh get-docker.sh"),
    'b': ("Update System", "sudo apt update && apt upgrade -y"),
    'c': ("Install Apache2", "sudo apt install apache2 -y && sudo systemctl start apache2"),
    'd': ("Install Fail2Ban", "sudo apt install fail2ban -y && systemctl enable fail2ban && systemctl start fail2ban"),
    'e': ("Check Network Ports", "ss -tulpn"),
    'f': ("Show Disk Usage", "df -h"),
    'g': ("Show RAM Usage", "free -m"),
    'h': ("Show Uptime", "uptime -p"),
    'i': ("Docker Portainer get Key", "sudo docker logs portainer 2>&1 | grep 'setup_token'="),
    'j': ("Install Git", "sudo apt install git -y"),
    'k': ("List Active Services", "systemctl list-units --type=service --state=running"),
    'l': ("Clear Auth Log", "> /var/log/auth.log"),
    'm': ("Install Htop", "sudo apt install htop -y"),
    'n': ("Check Kernel Version", "uname -a"),
    'o': ("Generate SSH Key", "ssh-keygen -t ed25519 -C 'oxinon@server'"),
    'p': ("Find Large Files", "find / -type f -size +100M"),
    'q': ("Show IP Address", "ip addr show"),
    'r': ("Restart Apache2", "sudo systemctl restart apache2"),
    's': ("Set Timezone (UTC)", "timedatectl set-timezone UTC"),
    't': ("Check Firewall Status", "sudo ufw status"),
    'u': ("Add New User", "read -p 'Username: ' user && adduser $user && usermod -aG sudo $user"),
    'v': ("Check Debian Version", "cat /etc/debian_version"),
    'w': ("View Last Logins", "last | head -n 20"),
    'x': ("Flush IPTables", "iptables -F"),
    'y': ("Install Curl", "sudo apt install curl -y"),
    'z': ("Reboot System", "sudo reboot"),
}

# Kommandos, bei denen zusätzlich noch mal ausdrücklich nachgefragt wird,
# selbst wenn --run schon gesetzt ist.
DESTRUCTIVE = {'l', 'x', 'z'}


def copy_to_clipboard(text):
    for tool, args in (("xclip", ["xclip", "-selection", "clipboard"]),
                        ("xsel", ["xsel", "--clipboard", "--input"]),
                        ("wl-copy", ["wl-copy"])):
        if shutil.which(tool):
            try:
                subprocess.run(args, input=text.encode(), check=True)
                return tool
            except Exception:
                continue
    return None


def print_list():
    print()
    print(f"{C.BOLD}SCRIPT EXECUTER — verfügbare Snippets{C.RESET}")
    hr()
    keys = sorted(SCRIPTS.keys())
    for i in range(0, len(keys), 2):
        col1 = keys[i]
        name1 = SCRIPTS[col1][0]
        left = f"{C.BR_CYAN}[{col1}]{C.RESET} {name1}"
        line = f"  {left:<48}"
        if i + 1 < len(keys):
            col2 = keys[i + 1]
            name2 = SCRIPTS[col2][0]
            line += f"{C.BR_CYAN}[{col2}]{C.RESET} {name2}"
        print(line)
    hr()
    print(f"{C.GREY}Aufruf: skript <buchstabe> [--run]{C.RESET}")
    print()


def show_and_maybe_run(letter, run):
    letter = letter.lower()
    if letter not in SCRIPTS:
        die(f"Unbekannte Auswahl '{letter}'. Siehe: skript (ohne Argument für die Liste).")

    name, cmd = SCRIPTS[letter]
    print()
    print(f"{C.BR_CYAN}[{letter}]{C.RESET} {C.BOLD}{name}{C.RESET}")
    print(f"{C.GREY}$ {cmd}{C.RESET}")
    print()

    if not run:
        copied_via = copy_to_clipboard(cmd)
        if copied_via:
            print(f"{C.GREEN}[OK]{C.RESET} In Zwischenablage kopiert (via {copied_via}).")
        else:
            print(f"{C.YELLOW}[!]{C.RESET} Kein Clipboard-Tool gefunden (xclip/xsel/wl-copy).")
            print(f"    Kommando steht oben — einfach von Hand kopieren.")
        return

    warn = " ⚠ Dieses Kommando ist potenziell destruktiv!" if letter in DESTRUCTIVE else ""
    answer = input(f"{C.YELLOW}Wirklich ausführen?{warn} [y/N] {C.RESET}").strip().lower()
    if answer != 'y':
        print(f"{C.GREY}Abgebrochen.{C.RESET}")
        return

    subprocess.run(cmd, shell=True)


def main():
    parser = argparse.ArgumentParser(
        prog="skript",
        description="Sysadmin Script Executer",
    )
    parser.add_argument("letter", nargs="?", help="Buchstabe des Snippets (a-z)")
    parser.add_argument("--run", action="store_true", help="Kommando direkt ausführen statt nur zu kopieren")
    args = parser.parse_args()

    if not args.letter:
        print_list()
        return

    show_and_maybe_run(args.letter, args.run)


if __name__ == "__main__":
    try:
        main()
    except KeyboardInterrupt:
        sys.exit(0)
