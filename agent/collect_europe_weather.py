#!/usr/bin/env python3
"""Collect current weather for European countries via Open-Meteo."""

from __future__ import annotations

import csv
import json
import sys
import urllib.error
import urllib.parse
import urllib.request
from dataclasses import dataclass
from datetime import datetime, timezone
from pathlib import Path
from typing import Any

API_URL = "https://api.open-meteo.com/v1/forecast"
OUTPUT_DIR = Path(__file__).resolve().parent
MEMORY_PATH = Path("/cursor/stores/automation/memories/latest.json")
MEMORY_CSV_PATH = Path("/cursor/stores/automation/memories/europe-weather.csv")
MEMORY_JSON_PATH = Path("/cursor/stores/automation/memories/europe-weather.json")

WEATHER_DESCRIPTIONS = {
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


@dataclass(frozen=True)
class Location:
    country: str
    country_code: str
    capital: str
    latitude: float
    longitude: float
    timezone: str


EUROPEAN_CAPITALS: list[Location] = [
    Location("Albania", "AL", "Tirana", 41.3275, 19.8187, "Europe/Tirane"),
    Location("Andorra", "AD", "Andorra la Vella", 42.5063, 1.5218, "Europe/Andorra"),
    Location("Austria", "AT", "Vienna", 48.2082, 16.3738, "Europe/Vienna"),
    Location("Belarus", "BY", "Minsk", 53.9006, 27.5590, "Europe/Minsk"),
    Location("Belgium", "BE", "Brussels", 50.8503, 4.3517, "Europe/Brussels"),
    Location("Bosnia and Herzegovina", "BA", "Sarajevo", 43.8563, 18.4131, "Europe/Sarajevo"),
    Location("Bulgaria", "BG", "Sofia", 42.6977, 23.3219, "Europe/Sofia"),
    Location("Croatia", "HR", "Zagreb", 45.8150, 15.9819, "Europe/Zagreb"),
    Location("Cyprus", "CY", "Nicosia", 35.1856, 33.3823, "Asia/Nicosia"),
    Location("Czech Republic", "CZ", "Prague", 50.0755, 14.4378, "Europe/Prague"),
    Location("Denmark", "DK", "Copenhagen", 55.6761, 12.5683, "Europe/Copenhagen"),
    Location("Estonia", "EE", "Tallinn", 59.4370, 24.7536, "Europe/Tallinn"),
    Location("Finland", "FI", "Helsinki", 60.1699, 24.9384, "Europe/Helsinki"),
    Location("France", "FR", "Paris", 48.8566, 2.3522, "Europe/Paris"),
    Location("Germany", "DE", "Berlin", 52.5200, 13.4050, "Europe/Berlin"),
    Location("Greece", "GR", "Athens", 37.9838, 23.7275, "Europe/Athens"),
    Location("Hungary", "HU", "Budapest", 47.4979, 19.0402, "Europe/Budapest"),
    Location("Iceland", "IS", "Reykjavik", 64.1466, -21.9426, "Atlantic/Reykjavik"),
    Location("Ireland", "IE", "Dublin", 53.3498, -6.2603, "Europe/Dublin"),
    Location("Italy", "IT", "Rome", 41.9028, 12.4964, "Europe/Rome"),
    Location("Kosovo", "XK", "Pristina", 42.6629, 21.1655, "Europe/Belgrade"),
    Location("Latvia", "LV", "Riga", 56.9496, 24.1052, "Europe/Riga"),
    Location("Liechtenstein", "LI", "Vaduz", 47.1410, 9.5209, "Europe/Vaduz"),
    Location("Lithuania", "LT", "Vilnius", 54.6872, 25.2797, "Europe/Vilnius"),
    Location("Luxembourg", "LU", "Luxembourg", 49.6116, 6.1319, "Europe/Luxembourg"),
    Location("Malta", "MT", "Valletta", 35.8989, 14.5146, "Europe/Malta"),
    Location("Moldova", "MD", "Chisinau", 47.0105, 28.8638, "Europe/Chisinau"),
    Location("Monaco", "MC", "Monaco", 43.7384, 7.4246, "Europe/Monaco"),
    Location("Montenegro", "ME", "Podgorica", 42.4304, 19.2594, "Europe/Podgorica"),
    Location("Netherlands", "NL", "Amsterdam", 52.3676, 4.9041, "Europe/Amsterdam"),
    Location("North Macedonia", "MK", "Skopje", 41.9981, 21.4254, "Europe/Skopje"),
    Location("Norway", "NO", "Oslo", 59.9139, 10.7522, "Europe/Oslo"),
    Location("Poland", "PL", "Warsaw", 52.2297, 21.0122, "Europe/Warsaw"),
    Location("Portugal", "PT", "Lisbon", 38.7223, -9.1393, "Europe/Lisbon"),
    Location("Romania", "RO", "Bucharest", 44.4268, 26.1025, "Europe/Bucharest"),
    Location("Russia", "RU", "Moscow", 55.7558, 37.6173, "Europe/Moscow"),
    Location("San Marino", "SM", "San Marino", 43.9424, 12.4578, "Europe/San_Marino"),
    Location("Serbia", "RS", "Belgrade", 44.7866, 20.4489, "Europe/Belgrade"),
    Location("Slovakia", "SK", "Bratislava", 48.1486, 17.1077, "Europe/Bratislava"),
    Location("Slovenia", "SI", "Ljubljana", 46.0569, 14.5058, "Europe/Ljubljana"),
    Location("Spain", "ES", "Madrid", 40.4168, -3.7038, "Europe/Madrid"),
    Location("Sweden", "SE", "Stockholm", 59.3293, 18.0686, "Europe/Stockholm"),
    Location("Switzerland", "CH", "Bern", 46.9480, 7.4474, "Europe/Zurich"),
    Location("Turkey", "TR", "Ankara", 39.9334, 32.8597, "Europe/Istanbul"),
    Location("Ukraine", "UA", "Kyiv", 50.4501, 30.5234, "Europe/Kyiv"),
    Location("United Kingdom", "GB", "London", 51.5074, -0.1278, "Europe/London"),
    Location("Vatican City", "VA", "Vatican City", 41.9029, 12.4534, "Europe/Vatican"),
]


def weather_description(code: int | None) -> str:
    if code is None:
        return "Unknown"
    return WEATHER_DESCRIPTIONS.get(code, f"Weather code {code}")


def fetch_weather(location: Location) -> dict[str, Any]:
    params = urllib.parse.urlencode(
        {
            "latitude": location.latitude,
            "longitude": location.longitude,
            "timezone": location.timezone,
            "current": ",".join(
                [
                    "temperature_2m",
                    "relative_humidity_2m",
                    "apparent_temperature",
                    "precipitation",
                    "weather_code",
                    "wind_speed_10m",
                    "wind_direction_10m",
                ]
            ),
        }
    )
    request = urllib.request.Request(f"{API_URL}?{params}", headers={"User-Agent": "europe-weather-collector/1.0"})
    with urllib.request.urlopen(request, timeout=30) as response:
        payload = json.load(response)

    current = payload["current"]
    weather_code = current.get("weather_code")
    return {
        "country": location.country,
        "country_code": location.country_code,
        "capital": location.capital,
        "latitude": location.latitude,
        "longitude": location.longitude,
        "timezone": location.timezone,
        "observed_at": current["time"],
        "temperature_c": current.get("temperature_2m"),
        "apparent_temperature_c": current.get("apparent_temperature"),
        "humidity_pct": current.get("relative_humidity_2m"),
        "precipitation_mm": current.get("precipitation"),
        "wind_speed_kmh": current.get("wind_speed_10m"),
        "wind_direction_deg": current.get("wind_direction_10m"),
        "weather_code": weather_code,
        "conditions": weather_description(weather_code),
    }


def build_snapshot(locations: list[dict[str, Any]], errors: list[dict[str, Any]]) -> dict[str, Any]:
    successful = [entry for entry in locations if entry.get("temperature_c") is not None]
    temperatures = [entry["temperature_c"] for entry in successful]
    warmest = max(successful, key=lambda entry: entry["temperature_c"]) if successful else None
    coldest = min(successful, key=lambda entry: entry["temperature_c"]) if successful else None
    average = round(sum(temperatures) / len(temperatures), 1) if temperatures else None

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
            "average_temperature_c": average,
        },
        "locations": locations,
        "errors": errors,
    }


def write_csv(path: Path, locations: list[dict[str, Any]]) -> None:
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
        for entry in locations:
            writer.writerow({field: entry.get(field) for field in fieldnames})


def write_json(path: Path, snapshot: dict[str, Any]) -> None:
    path.write_text(json.dumps(snapshot, indent=2, ensure_ascii=False) + "\n", encoding="utf-8")


def main() -> int:
    locations: list[dict[str, Any]] = []
    errors: list[dict[str, Any]] = []

    for location in EUROPEAN_CAPITALS:
        try:
            locations.append(fetch_weather(location))
        except (urllib.error.URLError, TimeoutError, KeyError, ValueError) as exc:
            errors.append(
                {
                    "country": location.country,
                    "country_code": location.country_code,
                    "capital": location.capital,
                    "error": str(exc),
                }
            )

    snapshot = build_snapshot(locations, errors)

    for directory in (OUTPUT_DIR, MEMORY_PATH.parent):
        directory.mkdir(parents=True, exist_ok=True)

    write_json(OUTPUT_DIR / "europe-weather.json", snapshot)
    write_csv(OUTPUT_DIR / "europe-weather.csv", locations)
    write_json(MEMORY_JSON_PATH, snapshot)
    write_csv(MEMORY_CSV_PATH, locations)
    write_json(MEMORY_PATH, snapshot)

    print(
        f"Collected weather for {snapshot['successful_count']}/{snapshot['location_count']} locations. "
        f"Average: {snapshot['summary']['average_temperature_c']}°C"
    )
    if errors:
        for error in errors:
            print(f"FAILED {error['country']}: {error['error']}", file=sys.stderr)
        return 1
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
