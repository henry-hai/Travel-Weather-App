'''
Henry Hai Nguyen
Multithreading Travel Weather App
'''

import tkinter as tk
from tkinter import messagebox, filedialog
import requests
import json
import os
import time
import threading

regions = {
    "North Bay": ["Napa", "Sonoma"],
    "The Coast": ["Santa Cruz", "Monterey"],
    "East Bay": ["Berkeley", "Livermore"],
    "Peninsula": ["San Francisco", "San Mateo"],
    "South Bay": ["San Jose", "Los Gatos"]
}

class MainApp(tk.Tk):
    ''' Main application class for the weather app '''
    def __init__(self):
        super().__init__()
        self.title("Travel Weather App")
        self.geometry("350x350")

        # top 2 labels
        tk.Label(self, text="Look up weather at your destination!", fg='blue').pack(pady=25)
        tk.Label(self, text='Select your destinations then click "Submit"', fg='blue').pack()

        self.geocodes = self.load_or_fetch_geocodes_multithread()
        self.weather_data = {}

        # Region:City Listbox
        self.listbox = tk.Listbox(self, selectmode='multiple', width=22, height=10)
        for region, cities in regions.items():
            for city in cities:
                self.listbox.insert(tk.END, f"{region}: {city}")
        self.listbox.pack(pady=20)

        tk.Button(self, text="Submit", command=self.submit).pack()

    def load_or_fetch_geocodes_multithread(self):
        ''' Load or fetch geocodes using multithreading '''
        filename = 'geocodes.json'
        geocodes = {}

        try:
            with open(filename, 'r') as file:
                geocodes = json.load(file)
        except FileNotFoundError:
            start_time = time.time()    # start timer                  
            threads = []
            for region in regions:
                for city in regions[region]:
                    thread = threading.Thread(target=self.fetch_geocoding, args=(city, geocodes))       # create new thread
                    threads.append(thread)
                    thread.start()
            for thread in threads:
                thread.join()   # wait & sync threads
            with open(filename, 'w') as file:
                json.dump(geocodes, file)
            end_time = time.time()
            print(f"Elapsed time to fetch geocoding data with multithreading: {end_time - start_time:.2f} seconds")     # check output

        return geocodes

    def fetch_geocoding(self, city, geocodes):
        ''' Fetch geocoding data for a city '''
        url = f"https://geocoding-api.open-meteo.com/v1/search?name={city}&count=1&language=en&format=json"
        response = requests.get(url)
        if response.status_code == 200:
            data = response.json()['results'][0]
            geocodes[city] = {'latitude': data['latitude'], 'longitude': data['longitude']}

    def submit(self):
        ''' Handle submit action to fetch & display weather data using multithreading '''
        selected_indices = self.listbox.curselection()
        if not selected_indices:
            messagebox.showinfo("ERROR: No Selection", "Please select at least one location.")
            return

        self.weather_data = {}
        threads = []
        start_time = time.time()

        for index in selected_indices:
            item = self.listbox.get(index)
            region, city = item.split(': ')
            city = city.strip()
            if city in self.geocodes:
                coords = self.geocodes[city]
                thread = threading.Thread(target=self.fetch_weather_multithread, args=(coords, city, self.weather_data))
                threads.append(thread)
                thread.start()
        for thread in threads:
            thread.join()
        end_time = time.time()
        print(f"Elapsed time to fetch weather data with multithreading: {end_time - start_time:.2f} seconds")
        
        for city, weather_data in self.weather_data.items():
            WeatherDisplay(self, city, weather_data)
        self.listbox.selection_clear(0, tk.END)

    def on_closing(self):
        ''' Ask user if they want to save results in directory before exiting '''
        if self.weather_data:
            if messagebox.askokcancel("Quit", "Do you want to save your results in a directory of your choice?"):
                folder_selected = filedialog.askdirectory(initialdir=os.getcwd())
                if folder_selected:
                    with open(os.path.join(folder_selected, 'weather.txt'), 'w') as f:
                        for city, data in self.weather_data.items():
                            f.write(f"{city}:\n")
                            f.write(", ".join(data['time']) + "\n")
                            f.write(", ".join(map(str, data['temperature_2m_max'])) + "\n")
                            f.write(", ".join(map(str, data['temperature_2m_min'])) + "\n")
                            f.write(", ".join(map(str, data['wind_speed_10m_max'])) + "\n")
                            f.write(", ".join(map(str, data['uv_index_max'])) + "\n\n")
                        # messagebox to tell the user where the file is 
                        messagebox.showinfo("File Saved", f"Results saved to {os.path.join(folder_selected, 'weather.txt')}")
                    self.destroy()
                else:
                    return
            else:
                self.destroy()
        else:
            self.destroy()

    def fetch_weather_multithread(self, coords, city, results):
        ''' Fetch weather data using coordinates '''
        url = f"https://api.open-meteo.com/v1/forecast?latitude={coords['latitude']}&longitude={coords['longitude']}&daily=temperature_2m_max,temperature_2m_min,wind_speed_10m_max,uv_index_max&temperature_unit=fahrenheit&wind_speed_unit=mph&start=today&end=in+4-days&timezone=auto"
        response = requests.get(url)
        if response.status_code == 200:
            results[city] = response.json()['daily']

class WeatherDisplay(tk.Toplevel):
    ''' Display window for weather data '''
    def __init__(self, master, city, weather_data):
        super().__init__(master)
        self.geometry("550x185")
        self.title("City Weather")
        tk.Label(self, text=f"Weather for {city}", fg='blue').pack(pady=(10))
        frame = tk.Frame(self)
        frame.pack(pady=(0, 10))

        headers = ['Date', 'High Temp', 'Low Temp', 'Wind Speed', 'UV Index']
        for i, header in enumerate(headers):
            tk.Label(frame, text=header).grid(row=0, column=i)

        for i, key in enumerate(['time', 'temperature_2m_max', 'temperature_2m_min', 'wind_speed_10m_max', 'uv_index_max']):
            listbox = tk.Listbox(frame, height=5, width=11)
            listbox.grid(row=1, column=i)
            for item in weather_data[key]:
                listbox.insert(tk.END, item)


if __name__ == "__main__":
    app = MainApp()
    app.protocol("WM_DELETE_WINDOW", app.on_closing)
    app.mainloop()