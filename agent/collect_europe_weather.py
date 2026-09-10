#!/usr/bin/env python3
"""Collect current weather for European capital cities via Open-Meteo."""

import csv
import json
import sys
import urllib.error
import urllib.parse
import urllib.request
from datetime import datetime, timezone
from pathlib import Path

EUROPEAN_CAPITALS = [
    ("Albania", "AL", "Tirana", 41.3275, 19.8187, "Europe/Tirane"),
    ("Andorra", "AD", "Andorra la Vella", 42.5063, 1.5218, "Europe/Andorra"),
    ("Austria", "AT", "Vienna", 48.2082, 16.3738, "Europe/Vienna"),
    ("Belarus", "BY", "Minsk", 53.9006, 27.559, "Europe/Minsk"),
    ("Belgium", "BE", "Brussels", 50.8503, 4.3517, "Europe/Brussels"),
    ("Bosnia and Herzegovina", "BA", "Sarajevo", 43.8563, 18.4131, "Europe/Sarajevo"),
    ("Bulgaria", "BG", "Sofia", 42.6977, 23.3219, "Europe/Sofia"),
    ("Croatia", "HR", "Zagreb", 45.815, 15.9819, "Europe/Zagreb"),
    ("Cyprus", "CY", "Nicosia", 35.1856, 33.3823, "Asia/Nicosia"),
    ("Czech Republic", "CZ", "Prague", 50.0755, 14.4378, "Europe/Prague"),
    ("Denmark", "DK", "Copenhagen", 55.6761, 12.5683, "Europe/Copenhagen"),
    ("Estonia", "EE", "Tallinn", 59.437, 24.7536, "Europe/Tallinn"),
    ("Finland", "FI", "Helsinki", 60.1699, 24.9384, "Europe/Helsinki"),
    ("France", "FR", "Paris", 48.8566, 2.3522, "Europe/Paris"),
    ("Germany", "DE", "Berlin", 52.52, 13.405, "Europe/Berlin"),
    ("Greece", "GR", "Athens", 37.9838, 23.7275, "Europe/Athens"),
    ("Hungary", "HU", "Budapest", 47.4979, 19.0402, "Europe/Budapest"),
    ("Iceland", "IS", "Reykjavik", 64.1466, -21.9426, "Atlantic/Reykjavik"),
    ("Ireland", "IE", "Dublin", 53.3498, -6.2603, "Europe/Dublin"),
    ("Italy", "IT", "Rome", 41.9028, 12.4964, "Europe/Rome"),
    ("Kosovo", "XK", "Pristina", 42.6629, 21.1655, "Europe/Belgrade"),
    ("Latvia", "LV", "Riga", 56.9496, 24.1052, "Europe/Riga"),
    ("Liechtenstein", "LI", "Vaduz", 47.141, 9.5209, "Europe/Vaduz"),
    ("Lithuania", "LT", "Vilnius", 54.6872, 25.2797, "Europe/Vilnius"),
    ("Luxembourg", "LU", "Luxembourg", 49.6116, 6.1319, "Europe/Luxembourg"),
    ("Malta", "MT", "Valletta", 35.8989, 14.5146, "Europe/Malta"),
    ("Moldova", "MD", "Chisinau", 47.0105, 28.8638, "Europe/Chisinau"),
    ("Monaco", "MC", "Monaco", 43.7384, 7.4246, "Europe/Monaco"),
    ("Montenegro", "ME", "Podgorica", 42.4304, 19.2594, "Europe/Podgorica"),
    ("Netherlands", "NL", "Amsterdam", 52.3676, 4.9041, "Europe/Amsterdam"),
    ("North Macedonia", "MK", "Skopje", 41.9981, 21.4254, "Europe/Skopje"),
    ("Norway", "NO", "Oslo", 59.9139, 10.7522, "Europe/Oslo"),
    ("Poland", "PL", "Warsaw", 52.2297, 21.0122, "Europe/Warsaw"),
    ("Portugal", "PT", "Lisbon", 38.7223, -9.1393, "Europe/Lisbon"),
    ("Romania", "RO", "Bucharest", 44.4268, 26.1025, "Europe/Bucharest"),
    ("Russia", "RU", "Moscow", 55.7558, 37.6173, "Europe/Moscow"),
    ("San Marino", "SM", "San Marino", 43.9424, 12.4578, "Europe/San_Marino"),
    ("Serbia", "RS", "Belgrade", 44.7866, 20.4489, "Europe/Belgrade"),
    ("Slovakia", "SK", "Bratislava", 48.1486, 17.1077, "Europe/Bratislava"),
    ("Slovenia", "SI", "Ljubljana", 46.0569, 14.5058, "Europe/Ljubljana"),
    ("Spain", "ES", "Madrid", 40.4168, -3.7038, "Europe/Madrid"),
    ("Sweden", "SE", "Stockholm", 59.3293, 18.0686, "Europe/Stockholm"),
    ("Switzerland", "CH", "Bern", 46.948, 7.4474, "Europe/Zurich"),
    ("Turkey", "TR", "Ankara", 39.9334, 32.8597, "Europe/Istanbul"),
    ("Ukraine", "UA", "Kyiv", 50.4501, 30.5234, "Europe/Kyiv"),
    ("United Kingdom", "GB", "London", 51.5074, -0.1278, "Europe/London"),
    ("Vatican City", "VA", "Vatican City", 41.9029, 12.4534, "Europe/Vatican"),
]

WEATHER_CODES = {
    0: "Clear sky",
    1: "Mainly clear",
    2: "Partly cloudy",
    3: "Overcast",
    45: "Fog",
    48: "Depositing rime fog",
    51: "Light drizzle",
    53: "Moderate drizzle",
    55: "Dense drizzle",
    56: "Light freezing drizzle",
    57: "Dense freezing drizzle",
    61: "Slight rain",
    63: "Moderate rain",
    65: "Heavy rain",
    66: "Light freezing rain",
    67: "Heavy freezing rain",
    71: "Slight snow fall",
    73: "Moderate snow fall",
    75: "Heavy snow fall",
    77: "Snow grains",
    80: "Slight rain showers",
    81: "Moderate rain showers",
    82: "Violent rain showers",
    85: "Slight snow showers",
    86: "Heavy snow showers",
    95: "Thunderstorm",
    96: "Thunderstorm with slight hail",
    99: "Thunderstorm with heavy hail",
}

API_BASE = "https://api.open-meteo.com/v1/forecast"
CURRENT_FIELDS = ",".join(
    [
        "temperature_2m",
        "relative_humidity_2m",
        "apparent_temperature",
        "precipitation",
        "weather_code",
        "wind_speed_10m",
        "wind_direction_10m",
    ]
)


def fetch_weather(country, code, capital, lat, lon, tz):
    params = urllib.parse.urlencode(
        {
            "latitude": lat,
            "longitude": lon,
            "current": CURRENT_FIELDS,
            "timezone": tz,
            "wind_speed_unit": "kmh",
        }
    )
    url = f"{API_BASE}?{params}"
    with urllib.request.urlopen(url, timeout=30) as response:
        payload = json.load(response)

    current = payload["current"]
    weather_code = current["weather_code"]
    return {
        "country": country,
        "country_code": code,
        "capital": capital,
        "latitude": lat,
        "longitude": lon,
        "timezone": payload.get("timezone", tz),
        "observed_at": current["time"],
        "temperature_c": current["temperature_2m"],
        "apparent_temperature_c": current["apparent_temperature"],
        "humidity_pct": current["relative_humidity_2m"],
        "precipitation_mm": current["precipitation"],
        "wind_speed_kmh": current["wind_speed_10m"],
        "wind_direction_deg": current["wind_direction_10m"],
        "weather_code": weather_code,
        "conditions": WEATHER_CODES.get(weather_code, f"Code {weather_code}"),
    }


def build_snapshot(locations, errors):
    successful = [loc for loc in locations if "error" not in loc]
    temps = [loc["temperature_c"] for loc in successful]
    warmest = max(successful, key=lambda loc: loc["temperature_c"]) if successful else None
    coldest = min(successful, key=lambda loc: loc["temperature_c"]) if successful else None
    avg_temp = round(sum(temps) / len(temps), 1) if temps else None

    return {
        "collected_at_utc": datetime.now(timezone.utc).isoformat(),
        "source": "Open-Meteo (https://open-meteo.com)",
        "scope": "European countries — current weather at capital cities",
        "location_count": len(EUROPEAN_CAPITALS),
        "successful_count": len(successful),
        "failed_count": len(errors),
        "summary": {
            "warmest": warmest,
            "coldest": coldest,
            "average_temperature_c": avg_temp,
        },
        "locations": successful,
        "errors": errors,
    }


def write_csv(path, locations):
    fieldnames = [
        "country",
        "country_code",
        "capital",
        "latitude",
        "longitude",
        "timezone",
        "observed_at",
        "temperature_c",
        "apparent_temperature_c",
        "humidity_pct",
        "precipitation_mm",
        "wind_speed_kmh",
        "wind_direction_deg",
        "weather_code",
        "conditions",
    ]
    with path.open("w", newline="", encoding="utf-8") as handle:
        writer = csv.DictWriter(handle, fieldnames=fieldnames)
        writer.writeheader()
        writer.writerows(locations)


def main():
    script_dir = Path(__file__).resolve().parent
    output_json = script_dir / "europe-weather.json"
    output_csv = script_dir / "europe-weather.csv"
    memory_dir = Path("/cursor/stores/automation/memories")
    memory_json = memory_dir / "latest.json"
    memory_csv = memory_dir / "europe-weather.csv"
    memory_full_json = memory_dir / "europe-weather.json"

    locations = []
    errors = []

    for country, code, capital, lat, lon, tz in EUROPEAN_CAPITALS:
        try:
            locations.append(fetch_weather(country, code, capital, lat, lon, tz))
        except (urllib.error.URLError, urllib.error.HTTPError, KeyError, TimeoutError) as exc:
            errors.append(
                {
                    "country": country,
                    "country_code": code,
                    "capital": capital,
                    "error": str(exc),
                }
            )

    snapshot = build_snapshot(locations, errors)

    output_json.write_text(json.dumps(snapshot, indent=2), encoding="utf-8")
    write_csv(output_csv, snapshot["locations"])

    memory_dir.mkdir(parents=True, exist_ok=True)
    memory_json.write_text(json.dumps(snapshot, indent=2), encoding="utf-8")
    memory_full_json.write_text(json.dumps(snapshot, indent=2), encoding="utf-8")
    write_csv(memory_csv, snapshot["locations"])

    print(
        f"Collected {snapshot['successful_count']}/{snapshot['location_count']} locations. "
        f"Average {snapshot['summary']['average_temperature_c']}°C."
    )
    if snapshot["summary"]["warmest"]:
        warmest = snapshot["summary"]["warmest"]
        print(
            f"Warmest: {warmest['capital']}, {warmest['country']} "
            f"({warmest['temperature_c']}°C)."
        )
    if snapshot["summary"]["coldest"]:
        coldest = snapshot["summary"]["coldest"]
        print(
            f"Coldest: {coldest['capital']}, {coldest['country']} "
            f"({coldest['temperature_c']}°C)."
        )
    if errors:
        print(f"Failures: {len(errors)}", file=sys.stderr)
        for error in errors:
            print(f"  - {error['country']}: {error['error']}", file=sys.stderr)
        sys.exit(1)

    return 0


if __name__ == "__main__":
    raise SystemExit(main())
