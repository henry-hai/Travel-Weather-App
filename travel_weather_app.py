"""
Travel Weather App — Tkinter GUI with threaded weather fetches and JSON geocode cache.
"""

from __future__ import annotations

import json
import os
import threading
import time
import tkinter as tk
from tkinter import filedialog, messagebox
from urllib.parse import urlencode

import requests

GEOCODES_FILE = "geocodes.json"
# Disambiguate short city names (e.g. "Sonoma", "San Mateo") to California.
GEOCODE_QUERY_SUFFIX = ", California, United States"

REGIONS = {
    "North Bay": ["Napa", "Sonoma"],
    "The Coast": ["Santa Cruz", "Monterey"],
    "East Bay": ["Berkeley", "Livermore"],
    "Peninsula": ["San Francisco", "San Mateo"],
    "South Bay": ["San Jose", "Los Gatos"],
}


class MainApp(tk.Tk):
    def __init__(self) -> None:
        super().__init__()
        self.title("Travel Weather App")
        self.geometry("350x350")

        tk.Label(self, text="Look up weather at your destination!", fg="blue").pack(pady=25)
        tk.Label(self, text='Select your destinations then click "Submit"', fg="blue").pack()

        self._geocode_lock = threading.Lock()
        self._weather_lock = threading.Lock()
        self.geocodes = self._load_or_fetch_geocodes()
        self.weather_data: dict[str, dict] = {}

        self.listbox = tk.Listbox(self, selectmode="multiple", width=22, height=10)
        for region, cities in REGIONS.items():
            for city in cities:
                self.listbox.insert(tk.END, f"{region}: {city}")
        self.listbox.pack(pady=20)

        tk.Button(self, text="Submit", command=self.submit).pack()

    def _load_or_fetch_geocodes(self) -> dict:
        if os.path.isfile(GEOCODES_FILE):
            with open(GEOCODES_FILE, encoding="utf-8") as f:
                return json.load(f)

        geocodes: dict[str, dict] = {}
        threads: list[threading.Thread] = []
        start = time.perf_counter()

        for region in REGIONS:
            for city in REGIONS[region]:
                t = threading.Thread(target=self._fetch_geocoding, args=(city, geocodes))
                threads.append(t)
                t.start()
        for t in threads:
            t.join()

        with open(GEOCODES_FILE, "w", encoding="utf-8") as f:
            json.dump(geocodes, f, indent=2)

        elapsed = time.perf_counter() - start
        print(f"Geocoding (multithreaded) finished in {elapsed:.2f}s — saved to {GEOCODES_FILE}")
        return geocodes

    def _fetch_geocoding(self, city: str, geocodes: dict) -> None:
        params = {
            "name": f"{city}{GEOCODE_QUERY_SUFFIX}",
            "count": 1,
            "language": "en",
            "format": "json",
        }
        url = f"https://geocoding-api.open-meteo.com/v1/search?{urlencode(params)}"
        try:
            r = requests.get(url, timeout=15)
            r.raise_for_status()
            data = r.json()
            results = data.get("results") or []
            if not results:
                print(f"Geocoding: no results for {city!r}")
                return
            loc = results[0]
            entry = {"latitude": loc["latitude"], "longitude": loc["longitude"]}
            with self._geocode_lock:
                geocodes[city] = entry
        except (requests.RequestException, KeyError, ValueError) as e:
            print(f"Geocoding failed for {city!r}: {e}")

    def submit(self) -> None:
        selected = self.listbox.curselection()
        if not selected:
            messagebox.showinfo("No selection", "Please select at least one location.")
            return

        self.weather_data = {}
        threads: list[threading.Thread] = []
        start = time.perf_counter()
        missing: list[str] = []

        for index in selected:
            item = self.listbox.get(index)
            _region, city = item.split(": ", 1)
            city = city.strip()
            coords = self.geocodes.get(city)
            if coords:
                t = threading.Thread(
                    target=self._fetch_weather,
                    args=(coords, city, self.weather_data),
                )
                threads.append(t)
                t.start()
            else:
                missing.append(city)
        if missing:
            messagebox.showwarning(
                "Missing coordinates",
                "No cached coordinates for:\n" + "\n".join(missing),
            )

        for t in threads:
            t.join()

        elapsed = time.perf_counter() - start
        if threads:
            print(f"Weather fetch ({len(threads)} cities, multithreaded) in {elapsed:.2f}s")

        for city, payload in self.weather_data.items():
            WeatherDisplay(self, city, payload)
        self.listbox.selection_clear(0, tk.END)

    def _fetch_weather(self, coords: dict, city: str, results: dict) -> None:
        q = urlencode(
            {
                "latitude": coords["latitude"],
                "longitude": coords["longitude"],
                "daily": "temperature_2m_max,temperature_2m_min,wind_speed_10m_max,uv_index_max",
                "temperature_unit": "fahrenheit",
                "wind_speed_unit": "mph",
                "forecast_days": 5,
                "timezone": "auto",
            }
        )
        url = f"https://api.open-meteo.com/v1/forecast?{q}"
        try:
            r = requests.get(url, timeout=20)
            r.raise_for_status()
            daily = r.json().get("daily")
            if daily:
                with self._weather_lock:
                    results[city] = daily
        except (requests.RequestException, KeyError, ValueError) as e:
            print(f"Weather request failed for {city!r}: {e}")

    def on_closing(self) -> None:
        if not self.weather_data:
            self.destroy()
            return
        if not messagebox.askokcancel(
            "Quit",
            "Save your results to a folder before exiting?",
        ):
            self.destroy()
            return
        folder = filedialog.askdirectory(initialdir=os.getcwd())
        if not folder:
            return
        path = os.path.join(folder, "weather.txt")
        with open(path, "w", encoding="utf-8") as f:
            for city, data in self.weather_data.items():
                f.write(f"{city}:\n")
                f.write(", ".join(data["time"]) + "\n")
                f.write(", ".join(map(str, data["temperature_2m_max"])) + "\n")
                f.write(", ".join(map(str, data["temperature_2m_min"])) + "\n")
                f.write(", ".join(map(str, data["wind_speed_10m_max"])) + "\n")
                f.write(", ".join(map(str, data["uv_index_max"])) + "\n\n")
        messagebox.showinfo("File saved", f"Results saved to:\n{path}")
        self.destroy()


class WeatherDisplay(tk.Toplevel):
    def __init__(self, master: tk.Misc, city: str, weather_data: dict) -> None:
        super().__init__(master)
        self.geometry("550x185")
        self.title(f"Weather — {city}")
        tk.Label(self, text=f"Weather for {city}", fg="blue").pack(pady=(10, 0))
        frame = tk.Frame(self)
        frame.pack(pady=(0, 10))

        headers = ["Date", "High", "Low", "Wind", "UV"]
        for i, header in enumerate(headers):
            tk.Label(frame, text=header, font=("", 9, "bold")).grid(row=0, column=i, padx=2)

        keys = [
            "time",
            "temperature_2m_max",
            "temperature_2m_min",
            "wind_speed_10m_max",
            "uv_index_max",
        ]
        for i, key in enumerate(keys):
            lb = tk.Listbox(frame, height=5, width=11)
            lb.grid(row=1, column=i, padx=2)
            for item in weather_data.get(key, []):
                lb.insert(tk.END, item)


if __name__ == "__main__":
    app = MainApp()
    app.protocol("WM_DELETE_WINDOW", app.on_closing)
    app.mainloop()
