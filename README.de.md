# pytools

Zehn eigenständige Terminal-Programme, portiert aus den Befehlen `hmradio`,
`weather`, `news`, `clock`, `skript`, `nettest`, `speedtest`, `tetris`,
`snake` und dem Markdown-Viewer des versteckten OXINON-Web-Terminals —
jetzt als echte Kommandozeilen-Tools für Ubuntu/Debian, ohne Browser.

Genutzte Datenquellen sind identisch zur Web-Version:
- **Wetter**: Open-Meteo (`api.open-meteo.com`), gleiche 6 Städte
- **News**: Hacker-News-Algolia-API (`hn.algolia.com`)
- **Radio**: dieselben 8 Hirschmilch-Streams (`xfer.hirschmilch.de:8001`)
- **Nettest**: dieselben 4 Prüfgruppen (Control/Data/Radio/IP)
- **Speedtest**: Ping via ipify, Down-/Upload via speed.cloudflare.com
- **Script**: dieselben 26 Sysadmin-Snippets (a-z)
- **Uhr, Tetris, Snake**: rein lokal, keine Netzwerkverbindung
- **mdreader**: lokaler Markdown-Live-Viewer im Browser

## Voraussetzungen

- Python 3.8+ (bei Ubuntu/Debian meist vorinstalliert)
- `curses` (Teil der Python-Standardbibliothek unter Linux)
- `mpv` **nur** für das Radio-Tool:
  ```bash
  sudo apt update && sudo apt install mpv
  ```
- `xclip` (oder `xsel`/`wl-copy`) **optional** für `skript`, damit
  Snippets in die Zwischenablage kopiert werden können:
  ```bash
  sudo apt install xclip
  ```

Alle anderen Tools brauchen nur die Python-Standardbibliothek — keine
`pip install` nötig.

## Installation

```bash
chmod +x install.sh
sudo ./install.sh
```

Das Skript kopiert die Programme nach `/opt/ox-cli/` und legt kurze
Befehle in `/usr/local/bin/` an, die danach systemweit verfügbar sind:

```bash
hmradio
weather
news
clock
skript
nettest
speedtest
tetris
snake
mdreader
```

> **Warum `skript` statt `script`?**
> `script` ist auf jedem Ubuntu/Debian bereits ein Standard-Systembefehl
> (Paket `bsdutils`, zeichnet Terminal-Sitzungen auf). Um ihn nicht zu
> überschreiben, heißt das Sysadmin-Snippet-Tool hier `skript`.
>
> **Hinweis zu `hmradio`:** Das Radio-Tool heißt bewusst `hmradio` (statt
> nur `radio`), weil es im Debian/Ubuntu-Repo zufällig ein gleichnamiges
> Paket `radio` gibt. So gibt's von vornherein keine Kollision.
>
> `install.sh` prüft bei jedem Lauf automatisch, ob einer der Zielnamen
> bereits von einem *anderen* Systembefehl belegt ist, und installiert
> im Konfliktfall diesen einen Befehl nicht (mit Warnung), statt etwas
> Bestehendes zu überschreiben. Alte `ox-*`-Befehle einer früheren
> Installation werden automatisch entfernt.

### Ohne Installation direkt testen

```bash
cd ox-cli
python3 weather.py
python3 news.py
python3 clock.py
python3 hmradio.py       # benötigt mpv (Befehl nach Installation: hmradio)
python3 skript.py
python3 nettest.py
python3 speedtest.py
python3 tetris.py
python3 snake.py
python3 mdreader.py README.md
```

## Benutzung

### weather
```bash
weather                # Hamburg, aktuelle Bedingungen
weather tokyo          # andere Stadt
weather -f             # inkl. 5-Tage-Vorschau
weather -w             # Watch-Modus, Auto-Refresh alle 5 Min
weather -l             # Liste aller Städte
```

### news
```bash
news                   # HN Front Page
news -s newest         # Neueste Storys
news -s ask            # Ask HN
news -s show           # Show HN
news --open 3          # Artikel #3 im Browser öffnen
```

### hmradio
Interaktives TUI:
```
↑ / ↓      Sender wählen
Enter      Play / Stop
+ / -      Lautstärke (live, ohne Unterbrechung)
q          Beenden
```

### clock
Große Digitaluhr im Terminal:
```
12 / 2     24h- / 12h-Anzeige umschalten
d          Datum ein-/ausblenden
q          Beenden
```

### skript
```bash
skript                  # Liste aller 26 Snippets (a-z)
skript f                # zeigt Snippet 'f' (Show Disk Usage), kopiert in Zwischenablage
skript z --run          # zeigt + fragt nach, bevor ausgeführt wird (hier: Reboot!)
```
Kopiert standardmäßig nur in die Zwischenablage (über `xclip`/`xsel`/`wl-copy`,
je nachdem was installiert ist). Mit `--run` wird das Kommando direkt
ausgeführt — mit Sicherheitsabfrage, bei den drei destruktiven Snippets
(Auth-Log leeren, IPTables flushen, Reboot) sogar mit Extra-Warnung.

### nettest
```bash
nettest
```
Testet nacheinander alle vier Gruppen (Control/Data Services/Radio
Streams/IP) und gibt am Ende dieselbe Diagnose wie im Web-Terminal aus.

### speedtest
```bash
speedtest
```
Misst Ping, Jitter, Download und Upload gegen dieselben öffentlichen,
CORS-offenen Endpunkte wie die Browser-Version (ipify, speed.cloudflare.com).
Keine Daten werden gespeichert.

### tetris
10×20-Feld, 7 klassische Tetrominos, +100 Punkte pro geräumter Reihe:
```
←/→        bewegen
↑          drehen
↓          schneller fallen
q          Beenden
```

### snake
30×20-Feld, +10 Punkte pro Apfel:
```
↑ ↓ ← →    Richtung
q          Beenden
```

### mdreader
```bash
mdreader README.md              # im Browser anzeigen, Live-Reload
mdreader README.md --port 8080  # bestimmten Port verwenden
mdreader README.md --no-browser # Browser nicht automatisch öffnen
```

## Deinstallation

```bash
sudo rm -f /usr/local/bin/{hmradio,weather,news,clock,skript,nettest,speedtest,tetris,snake,mdreader}
sudo rm -rf /opt/pytools
```
