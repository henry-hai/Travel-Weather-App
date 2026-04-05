# Travel Weather App

Desktop application for multi-day weather forecasts across predefined San Francisco Bay Area locations. The interface is built with Python and Tkinter. Forecast data is retrieved from Open-Meteo; geocoding results are stored locally in JSON so coordinates are not refetched on every launch.

## Features

- Local JSON cache for geocoded coordinates (fewer geocoding requests after the first successful run).
- Concurrent forecast requests with Python `threading` when multiple cities are selected.
- Multi-select list, per-city forecast windows, and optional export of results to a text file.

## Requirements

- Python 3.9 or newer (3.10+ recommended)
- Dependencies listed in `requirements.txt`
- Tkinter (included with most Windows/macOS Python builds; on Linux, install the `python3-tk` package where applicable)

## Setup

```bash
cd Travel-Weather-App
python -m venv .venv
.venv\Scripts\activate
pip install -r requirements.txt
```

On macOS or Linux, activate the environment with `source .venv/bin/activate`.

## Usage

```bash
python travel_weather_app.py
```

If `geocodes.json` is not present, the application fetches coordinates from the Open-Meteo geocoding API and writes that file. Later runs load coordinates from disk.

To print debug timing (geocoding and weather fetch duration) to the console, set the environment variable `TRAVEL_WEATHER_DEBUG` to `1`, `true`, or `yes` before launching. Example (PowerShell): `$env:TRAVEL_WEATHER_DEBUG = "1"; python travel_weather_app.py`

## APIs

- [Open-Meteo Geocoding API](https://open-meteo.com/en/docs/geocoding-api) — city names to latitude and longitude (no API key).
- [Open-Meteo Weather API](https://open-meteo.com/en/docs) — daily forecast variables (no API key).

## License

This project is licensed under the MIT License. See [LICENSE](LICENSE).
