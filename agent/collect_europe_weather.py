#!/usr/bin/env python3
"""Collect current weather for European countries (capital cities) via Open-Meteo."""

from __future__ import annotations

import csv
import json
import sys
import urllib.error
import urllib.parse
import urllib.request
from datetime import datetime, timezone
from pathlib import Path

API_BASE = "https://api.open-meteo.com/v1/forecast"
BATCH_SIZE = 10

LOCATIONS = [
    {"country": "Albania", "country_code": "AL", "capital": "Tirana", "latitude": 41.3275, "longitude": 19.8187},
    {"country": "Andorra", "country_code": "AD", "capital": "Andorra la Vella", "latitude": 42.5063, "longitude": 1.5218},
    {"country": "Austria", "country_code": "AT", "capital": "Vienna", "latitude": 48.2082, "longitude": 16.3738},
    {"country": "Belarus", "country_code": "BY", "capital": "Minsk", "latitude": 53.9006, "longitude": 27.559},
    {"country": "Belgium", "country_code": "BE", "capital": "Brussels", "latitude": 50.8503, "longitude": 4.3517},
    {"country": "Bosnia and Herzegovina", "country_code": "BA", "capital": "Sarajevo", "latitude": 43.8563, "longitude": 18.4131},
    {"country": "Bulgaria", "country_code": "BG", "capital": "Sofia", "latitude": 42.6977, "longitude": 23.3219},
    {"country": "Croatia", "country_code": "HR", "capital": "Zagreb", "latitude": 45.815, "longitude": 15.9819},
    {"country": "Cyprus", "country_code": "CY", "capital": "Nicosia", "latitude": 35.1856, "longitude": 33.3823},
    {"country": "Czech Republic", "country_code": "CZ", "capital": "Prague", "latitude": 50.0755, "longitude": 14.4378},
    {"country": "Denmark", "country_code": "DK", "capital": "Copenhagen", "latitude": 55.6761, "longitude": 12.5683},
    {"country": "Estonia", "country_code": "EE", "capital": "Tallinn", "latitude": 59.437, "longitude": 24.7536},
    {"country": "Finland", "country_code": "FI", "capital": "Helsinki", "latitude": 60.1699, "longitude": 24.9384},
    {"country": "France", "country_code": "FR", "capital": "Paris", "latitude": 48.8566, "longitude": 2.3522},
    {"country": "Germany", "country_code": "DE", "capital": "Berlin", "latitude": 52.52, "longitude": 13.405},
    {"country": "Greece", "country_code": "GR", "capital": "Athens", "latitude": 37.9838, "longitude": 23.7275},
    {"country": "Hungary", "country_code": "HU", "capital": "Budapest", "latitude": 47.4979, "longitude": 19.0402},
    {"country": "Iceland", "country_code": "IS", "capital": "Reykjavik", "latitude": 64.1466, "longitude": -21.9426},
    {"country": "Ireland", "country_code": "IE", "capital": "Dublin", "latitude": 53.3498, "longitude": -6.2603},
    {"country": "Italy", "country_code": "IT", "capital": "Rome", "latitude": 41.9028, "longitude": 12.4964},
    {"country": "Kosovo", "country_code": "XK", "capital": "Pristina", "latitude": 42.6629, "longitude": 21.1655},
    {"country": "Latvia", "country_code": "LV", "capital": "Riga", "latitude": 56.9496, "longitude": 24.1052},
    {"country": "Liechtenstein", "country_code": "LI", "capital": "Vaduz", "latitude": 47.141, "longitude": 9.5209},
    {"country": "Lithuania", "country_code": "LT", "capital": "Vilnius", "latitude": 54.6872, "longitude": 25.2797},
    {"country": "Luxembourg", "country_code": "LU", "capital": "Luxembourg", "latitude": 49.6116, "longitude": 6.1319},
    {"country": "Malta", "country_code": "MT", "capital": "Valletta", "latitude": 35.8989, "longitude": 14.5146},
    {"country": "Moldova", "country_code": "MD", "capital": "Chisinau", "latitude": 47.0105, "longitude": 28.8638},
    {"country": "Monaco", "country_code": "MC", "capital": "Monaco", "latitude": 43.7384, "longitude": 7.4246},
    {"country": "Montenegro", "country_code": "ME", "capital": "Podgorica", "latitude": 42.4304, "longitude": 19.2594},
    {"country": "Netherlands", "country_code": "NL", "capital": "Amsterdam", "latitude": 52.3676, "longitude": 4.9041},
    {"country": "North Macedonia", "country_code": "MK", "capital": "Skopje", "latitude": 41.9981, "longitude": 21.4254},
    {"country": "Norway", "country_code": "NO", "capital": "Oslo", "latitude": 59.9139, "longitude": 10.7522},
    {"country": "Poland", "country_code": "PL", "capital": "Warsaw", "latitude": 52.2297, "longitude": 21.0122},
    {"country": "Portugal", "country_code": "PT", "capital": "Lisbon", "latitude": 38.7223, "longitude": -9.1393},
    {"country": "Romania", "country_code": "RO", "capital": "Bucharest", "latitude": 44.4268, "longitude": 26.1025},
    {"country": "Russia", "country_code": "RU", "capital": "Moscow", "latitude": 55.7558, "longitude": 37.6173},
    {"country": "San Marino", "country_code": "SM", "capital": "San Marino", "latitude": 43.9424, "longitude": 12.4578},
    {"country": "Serbia", "country_code": "RS", "capital": "Belgrade", "latitude": 44.7866, "longitude": 20.4489},
    {"country": "Slovakia", "country_code": "SK", "capital": "Bratislava", "latitude": 48.1486, "longitude": 17.1077},
    {"country": "Slovenia", "country_code": "SI", "capital": "Ljubljana", "latitude": 46.0569, "longitude": 14.5058},
    {"country": "Spain", "country_code": "ES", "capital": "Madrid", "latitude": 40.4168, "longitude": -3.7038},
    {"country": "Sweden", "country_code": "SE", "capital": "Stockholm", "latitude": 59.3293, "longitude": 18.0686},
    {"country": "Switzerland", "country_code": "CH", "capital": "Bern", "latitude": 46.948, "longitude": 7.4474},
    {"country": "Turkey", "country_code": "TR", "capital": "Ankara", "latitude": 39.9334, "longitude": 32.8597},
    {"country": "Ukraine", "country_code": "UA", "capital": "Kyiv", "latitude": 50.4501, "longitude": 30.5234},
    {"country": "United Kingdom", "country_code": "GB", "capital": "London", "latitude": 51.5074, "longitude": -0.1278},
    {"country": "Vatican City", "country_code": "VA", "capital": "Vatican City", "latitude": 41.9029, "longitude": 12.4534},
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

CSV_FIELDS = [
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


def describe_weather(code: int | None) -> str:
    if code is None:
        return "Unknown"
    return WEATHER_CODES.get(code, f"Code {code}")


def fetch_batch(batch: list[dict]) -> list[dict]:
    params = {
        "latitude": ",".join(str(loc["latitude"]) for loc in batch),
        "longitude": ",".join(str(loc["longitude"]) for loc in batch),
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
        "timezone": "auto",
        "wind_speed_unit": "kmh",
    }
    url = f"{API_BASE}?{urllib.parse.urlencode(params)}"
    request = urllib.request.Request(url, headers={"User-Agent": "europe-weather-automation/1.0"})
    with urllib.request.urlopen(request, timeout=60) as response:
        payload = json.load(response)

    if isinstance(payload, dict) and "current" in payload:
        return [payload]
    if isinstance(payload, list):
        return payload
    raise ValueError(f"Unexpected API response shape: {type(payload)}")


def parse_location(loc: dict, api_response: dict) -> dict:
    current = api_response.get("current") or {}
    weather_code = current.get("weather_code")
    return {
        **loc,
        "timezone": api_response.get("timezone"),
        "observed_at": current.get("time"),
        "temperature_c": current.get("temperature_2m"),
        "apparent_temperature_c": current.get("apparent_temperature"),
        "humidity_pct": current.get("relative_humidity_2m"),
        "precipitation_mm": current.get("precipitation"),
        "wind_speed_kmh": current.get("wind_speed_10m"),
        "wind_direction_deg": current.get("wind_direction_10m"),
        "weather_code": weather_code,
        "conditions": describe_weather(weather_code),
    }


def build_summary(locations: list[dict]) -> dict:
    temps = [loc["temperature_c"] for loc in locations if loc.get("temperature_c") is not None]
    warmest = max(locations, key=lambda loc: loc.get("temperature_c") or float("-inf"))
    coldest = min(locations, key=lambda loc: loc.get("temperature_c") or float("inf"))
    return {
        "warmest": warmest,
        "coldest": coldest,
        "average_temperature_c": round(sum(temps) / len(temps), 1) if temps else None,
    }


def write_csv(path: Path, locations: list[dict]) -> None:
    with path.open("w", newline="", encoding="utf-8") as handle:
        writer = csv.DictWriter(handle, fieldnames=CSV_FIELDS)
        writer.writeheader()
        for loc in locations:
            writer.writerow({field: loc.get(field) for field in CSV_FIELDS})


def collect() -> dict:
    collected_at = datetime.now(timezone.utc)
    results: list[dict] = []
    errors: list[dict] = []

    for start in range(0, len(LOCATIONS), BATCH_SIZE):
        batch = LOCATIONS[start : start + BATCH_SIZE]
        try:
            responses = fetch_batch(batch)
        except (urllib.error.URLError, TimeoutError, ValueError, json.JSONDecodeError) as exc:
            for loc in batch:
                errors.append(
                    {
                        "country": loc["country"],
                        "country_code": loc["country_code"],
                        "capital": loc["capital"],
                        "error": str(exc),
                    }
                )
            continue

        if len(responses) != len(batch):
            errors.append(
                {
                    "batch_start": start,
                    "error": f"Expected {len(batch)} responses, got {len(responses)}",
                }
            )
            continue

        for loc, response in zip(batch, responses):
            if "error" in response:
                errors.append(
                    {
                        "country": loc["country"],
                        "country_code": loc["country_code"],
                        "capital": loc["capital"],
                        "error": response.get("reason", "API error"),
                    }
                )
                continue
            results.append(parse_location(loc, response))

    results.sort(key=lambda loc: loc["country"])
    snapshot = {
        "collected_at_utc": collected_at.isoformat(),
        "source": "Open-Meteo (https://open-meteo.com)",
        "scope": "European countries — current weather at capital cities",
        "location_count": len(LOCATIONS),
        "successful_count": len(results),
        "failed_count": len(errors),
        "summary": build_summary(results) if results else {},
        "locations": results,
        "errors": errors,
    }
    return snapshot


def main() -> int:
    repo_root = Path(__file__).resolve().parents[1]
    agent_dir = repo_root / "agent"
    memories_dir = Path("/cursor/stores/automation/memories")

    agent_dir.mkdir(parents=True, exist_ok=True)
    memories_dir.mkdir(parents=True, exist_ok=True)

    snapshot = collect()

    json_path = agent_dir / "europe-weather.json"
    csv_path = agent_dir / "europe-weather.csv"
    latest_path = memories_dir / "latest.json"

    json_path.write_text(json.dumps(snapshot, indent=2, ensure_ascii=False) + "\n", encoding="utf-8")
    write_csv(csv_path, snapshot["locations"])
    latest_path.write_text(json.dumps(snapshot, indent=2, ensure_ascii=False) + "\n", encoding="utf-8")

    (memories_dir / "europe-weather.json").write_text(
        json_path.read_text(encoding="utf-8"), encoding="utf-8"
    )
    (memories_dir / "europe-weather.csv").write_text(
        csv_path.read_text(encoding="utf-8"), encoding="utf-8"
    )

    summary = snapshot.get("summary") or {}
    warmest = summary.get("warmest", {})
    coldest = summary.get("coldest", {})
    avg = summary.get("average_temperature_c")

    memories_md = memories_dir / "MEMORIES.md"
    memories_md.write_text(
        "\n".join(
            [
                "# European Weather Automation",
                "",
                "## Purpose",
                "Daily cron job collects current weather for 47 European countries (capital cities) via Open-Meteo API.",
                "",
                "## Artifacts",
                "- `agent/europe-weather.json` — full structured snapshot",
                "- `agent/europe-weather.csv` — tabular export",
                "- `agent/collect_europe_weather.py` — collection script",
                "- `/cursor/stores/automation/memories/latest.json` — persisted latest snapshot",
                "",
                "## Last run",
                f"- **{snapshot['collected_at_utc']}** — {snapshot['successful_count']}/{snapshot['location_count']} locations collected successfully. "
                f"Average {avg}°C. "
                f"Warmest: {warmest.get('capital', 'n/a')}, {warmest.get('country', 'n/a')} ({warmest.get('temperature_c', 'n/a')}°C). "
                f"Coldest: {coldest.get('capital', 'n/a')}, {coldest.get('country', 'n/a')} ({coldest.get('temperature_c', 'n/a')}°C).",
                "- See `latest.json` for the full snapshot.",
                "",
            ]
        ),
        encoding="utf-8",
    )

    print(
        f"Collected {snapshot['successful_count']}/{snapshot['location_count']} locations "
        f"(failed: {snapshot['failed_count']})"
    )
    if summary:
        print(
            f"Average: {avg}°C | Warmest: {warmest.get('capital')} ({warmest.get('temperature_c')}°C) | "
            f"Coldest: {coldest.get('capital')} ({coldest.get('temperature_c')}°C)"
        )

    return 0 if snapshot["failed_count"] == 0 else 1


if __name__ == "__main__":
    sys.exit(main())
