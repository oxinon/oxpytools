#!/usr/bin/env python3
"""
ox-weather — Terminal-Wetterstation

Portiert aus dem "weather"-Befehl des OXINON-Web-Terminals.
Datenquelle: Open-Meteo (api.open-meteo.com) — kostenlos, kein API-Key nötig.

Benutzung:
    ox-weather                 Wetter für Hamburg (Standard)
    ox-weather berlin          Wetter für eine bestimmte Stadt
    ox-weather -l              Liste verfügbarer Städte
    ox-weather -f              inkl. 5-Tage-Vorschau
    ox-weather -w              Watch-Modus, aktualisiert alle 5 Min
"""
import argparse
import sys
import time
import urllib.request
import urllib.error
import json
from datetime import datetime

from common import C, clear, die, hr

CITIES = [
    {"name": "Hamburg", "lat": 53.5511, "lon": 9.9937},
    {"name": "Berlin", "lat": 52.5200, "lon": 13.4050},
    {"name": "Munich", "lat": 48.1351, "lon": 11.5820},
    {"name": "Taipeh", "lat": 25.0531, "lon": 121.5264},
    {"name": "New York", "lat": 40.7128, "lon": -74.0060},
    {"name": "Tokyo", "lat": 35.6762, "lon": 139.6503},
]

# WMO Weather-Codes -> (ASCII-Symbol, Beschreibung). 1:1 aus dem Web-Terminal übernommen.
WMO = {
    0: ("\\  /", "Clear sky"),
    1: (" .-.", "Mainly clear"),
    2: (" .-.", "Partly cloudy"),
    3: (" .--.", "Overcast"),
    45: ("~ ~ ~", "Fog"),
    48: ("~ ~ ~", "Rime fog"),
    51: ("''''", "Light drizzle"),
    53: ("''''", "Drizzle"),
    55: ("''''", "Dense drizzle"),
    61: ("/,/,", "Light rain"),
    63: ("/,/,", "Rain"),
    65: ("/,/,", "Heavy rain"),
    71: (" *  *", "Light snow"),
    73: (" *  *", "Snow"),
    75: (" *  *", "Heavy snow"),
    80: ("/,/,", "Rain showers"),
    81: ("/,/,", "Rain showers"),
    82: ("/,/,", "Violent showers"),
    95: ("⚡⚡", "Thunderstorm"),
    96: ("⚡⚡", "Thunderstorm + hail"),
    99: ("⚡⚡", "Severe thunderstorm"),
}


def wmo_info(code):
    return WMO.get(code, ("?", "Unknown"))


def fetch_weather(city):
    url = (
        "https://api.open-meteo.com/v1/forecast"
        f"?latitude={city['lat']}&longitude={city['lon']}"
        "&current=temperature_2m,relative_humidity_2m,apparent_temperature,wind_speed_10m,weather_code"
        "&daily=weather_code,temperature_2m_max,temperature_2m_min"
        "&timezone=auto&forecast_days=5"
    )
    req = urllib.request.Request(url, headers={"User-Agent": "ox-weather/1.0"})
    with urllib.request.urlopen(req, timeout=8) as res:
        return json.loads(res.read().decode())


def find_city(name):
    name = name.lower()
    for c in CITIES:
        if c["name"].lower().startswith(name):
            return c
    return None


def render(city, data, show_forecast):
    cur = data["current"]
    icon, desc = wmo_info(cur["weather_code"])

    print()
    print(f"{C.GREY}WEATHER STATION v1.0 — (open-meteo.com){C.RESET}")
    hr()
    print(f"{C.BOLD}LOCATION   :{C.RESET}  {city['name']}")
    print(f"{C.BOLD}CONDITIONS :{C.RESET}  {C.BR_CYAN}{icon}{C.RESET}  {desc}")
    print(f"{C.BOLD}TEMP       :{C.RESET}  {cur['temperature_2m']}°C  (feels like {cur['apparent_temperature']}°C)")
    print(f"{C.BOLD}HUMIDITY   :{C.RESET}  {cur['relative_humidity_2m']}%")
    print(f"{C.BOLD}WIND       :{C.RESET}  {cur['wind_speed_10m']} km/h")

    if show_forecast:
        days = data["daily"]
        print()
        print(f"{C.GREY}5-DAY FORECAST:{C.RESET}")
        for i in range(len(days["time"])):
            d = datetime.fromisoformat(days["time"][i])
            label = "Today" if i == 0 else d.strftime("%a")
            f_icon, _ = wmo_info(days["weather_code"][i])
            tmax = round(days["temperature_2m_max"][i])
            tmin = round(days["temperature_2m_min"][i])
            print(f"  {C.GREY}{label:<6}{C.RESET} {C.BR_CYAN}{f_icon:<6}{C.RESET} "
                  f"{tmax:>3}° / {tmin:>3}°")
    print()


def main():
    parser = argparse.ArgumentParser(
        prog="ox-weather",
        description="Terminal-Wetterstation (Open-Meteo)",
    )
    parser.add_argument("city", nargs="?", default="hamburg",
                         help="Stadt (Hamburg, Berlin, Munich, Taipeh, New York, Tokyo)")
    parser.add_argument("-l", "--list", action="store_true", help="Verfügbare Städte auflisten")
    parser.add_argument("-f", "--forecast", action="store_true", help="5-Tage-Vorschau anzeigen")
    parser.add_argument("-w", "--watch", action="store_true",
                         help="Alle 5 Minuten automatisch aktualisieren (Strg+C zum Beenden)")
    args = parser.parse_args()

    if args.list:
        print(f"{C.BOLD}Verfügbare Städte:{C.RESET}")
        for c in CITIES:
            print(f"  - {c['name']}")
        return

    city = find_city(args.city)
    if not city:
        die(f"Unbekannte Stadt '{args.city}'. Siehe: ox-weather -l")

    try:
        while True:
            if args.watch:
                clear()
            print(f"{C.GREY}Connecting to api.open-meteo.com ...{C.RESET}")
            try:
                data = fetch_weather(city)
            except (urllib.error.URLError, TimeoutError) as e:
                die(f"Connection to weather satellite failed. ({e})")
            clear() if args.watch else None
            render(city, data, args.forecast)
            if not args.watch:
                break
            print(f"{C.GREY}Aktualisiere in 5 Minuten … (Strg+C zum Beenden){C.RESET}")
            time.sleep(300)
    except KeyboardInterrupt:
        print()
        sys.exit(0)


if __name__ == "__main__":
    main()
