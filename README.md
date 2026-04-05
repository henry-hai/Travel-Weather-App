# Travel Weather App

A small **Python + Tkinter** desktop app that lets you pick multiple Bay Area destinations, then fetches **multi-day forecasts** in parallel using **threads**. Geocoding results are **cached in JSON** so repeat runs avoid extra geocoding API calls.

**Repository:** [github.com/henry-hai/Travel-Weather-App](https://github.com/henry-hai/Travel-Weather-App)

## Highlights (resume-aligned)

- **JSON caching** for geocoded coordinates to cut redundant geocoding requests and speed up startup after the first run.
- **Concurrent weather requests** with `threading` so several destinations load at once instead of strictly one-by-one.
- **Tkinter GUI** with multi-select list, per-city forecast windows, and optional export of results to a text file.

## Requirements

- Python 3.9+ (3.10+ recommended)
- `requests` (see `requirements.txt`)
- Tkinter (bundled with most Python installs on Windows; on some Linux distros install `python3-tk`.)

## Setup

```bash
cd Travel-Weather-App
python -m venv .venv
.venv\Scripts\activate
pip install -r requirements.txt
```

On macOS/Linux, activate with `source .venv/bin/activate`.

## Run

```bash
python travel_weather_app.py
```

On first run (or if `geocodes.json` is missing), the app fetches coordinates from the Open-Meteo geocoding API and writes `geocodes.json`. After that, coordinates load from disk.

## APIs

- [Open-Meteo Geocoding API](https://open-meteo.com/en/docs/geocoding-api) — resolve city names to latitude/longitude (no API key).
- [Open-Meteo Weather API](https://open-meteo.com/en/docs) — daily forecast fields (no API key).

## License

This project is licensed under the MIT License — see [LICENSE](LICENSE).
