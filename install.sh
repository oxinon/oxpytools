#!/usr/bin/env bash
# Installiert die ox-cli Terminal-Tools systemweit unter Ubuntu/Debian,
# als kurze Befehle ohne "ox-"-Präfix (z.B. "tetris" statt "ox-tetris").
# Aufruf: sudo ./install.sh   (NICHT "sudo sh install.sh" — siehe unten)

# Falls das Skript versehentlich per "sh install.sh" (= dash) statt
# "bash install.sh" / "./install.sh" gestartet wurde, mit bash neu starten.
# dash kennt weder "declare -A" noch "${BASH_SOURCE[0]}".
if [ -z "$BASH_VERSION" ]; then
    exec bash "$0" "$@"
fi

set -e

if [ "$(id -u)" -ne 0 ]; then
    echo "Bitte mit sudo ausführen: sudo ./install.sh"
    exit 1
fi

INSTALL_DIR="/opt/pytools"
BIN_DIR="/usr/local/bin"
SRC_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"

echo "[*] Prüfe Python 3 ..."
command -v python3 >/dev/null || { echo "python3 fehlt. Bitte installieren: apt install python3"; exit 1; }

# Zuordnung: Python-Datei -> gewünschter Befehlsname.
# "script.py" wird bewusst NICHT "script" genannt, weil /usr/bin/script
# bereits ein Standard-Systembefehl ist (Paket bsdutils, Teil jeder
# Ubuntu/Debian-Installation). Stattdessen: "skript".
declare -A APPS=(
    [hmradio]="hmradio"
    [weather]="weather"
    [news]="news"
    [clock]="clock"
    [skript]="skript"
    [nettest]="nettest"
    [speedtest]="speedtest"
    [tetris]="tetris"
    [snake]="snake"
    [mdreader]="mdreader"
)

# --- Namenskonflikt-Check vor der Installation ---
echo "[*] Prüfe Befehlsnamen auf Konflikte mit vorhandenen Systembefehlen ..."
conflict_found=0
for src in "${!APPS[@]}"; do
    bin="${APPS[$src]}"
    existing="$(command -v "$bin" 2>/dev/null || true)"
    # Ein bereits von einer früheren ox-cli-Installation angelegter Befehl
    # in $BIN_DIR ist kein echter Konflikt, sondern wird einfach ersetzt.
    if [ -n "$existing" ] && [ "$existing" != "${BIN_DIR}/${bin}" ]; then
        echo "    [KONFLIKT] '${bin}' zeigt bereits auf ${existing} — wird NICHT installiert."
        conflict_found=1
        unset "APPS[$src]"
    fi
done
if [ "$conflict_found" -eq 1 ]; then
    echo "    -> Für kollidierende Namen bitte APPS-Zuordnung in install.sh anpassen."
fi

echo "[*] Kopiere Programme nach ${INSTALL_DIR} ..."
mkdir -p "$INSTALL_DIR"
cp "$SRC_DIR"/common.py "$INSTALL_DIR"/
for src in "${!APPS[@]}"; do
    cp "$SRC_DIR/${src}.py" "$INSTALL_DIR"/
done

echo "[*] Entferne alte ox-* Befehle (falls vorhanden) ..."
for old in radio weather news clock script nettest speedtest tetris snake mdreader; do
    rm -f "${BIN_DIR}/ox-${old}"
done

echo "[*] Lege Befehle in ${BIN_DIR} an ..."
for src in "${!APPS[@]}"; do
    bin="${APPS[$src]}"
    cat > "${BIN_DIR}/${bin}" <<EOF
#!/usr/bin/env bash
exec python3 "${INSTALL_DIR}/${src}.py" "\$@"
EOF
    chmod +x "${BIN_DIR}/${bin}"
done

echo
echo "[OK] Installiert. Verfügbare Befehle:"
for src in "${!APPS[@]}"; do
    echo "     ${APPS[$src]}"
done | sort
echo
echo "[!] Hinweis: 'script.py' wurde absichtlich als 'skript' installiert,"
echo "    da 'script' bereits ein Standard-Linux-Befehl ist (bsdutils)."
echo
if ! command -v mpv >/dev/null; then
    echo "[!] Hinweis: 'mpv' ist nicht installiert (wird für 'hmradio' benötigt)."
    echo "    Installieren mit: sudo apt install mpv"
fi
