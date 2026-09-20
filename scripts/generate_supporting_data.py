import pandas as pd
import random
from datetime import datetime, timedelta
from pathlib import Path

random.seed(42)

# Output folder
output_folder = Path("data/raw")

# Same wards used in complaints dataset
wards = {
    "W001": ("Ward A", 19.0760, 72.8777),
    "W002": ("Ward B", 19.0800, 72.8800),
    "W003": ("Ward C", 19.0850, 72.8750),
    "W004": ("Ward D", 19.0700, 72.8850),
    "W005": ("Ward E", 19.0900, 72.8700),
    "W006": ("Ward F", 19.0650, 72.8900),
    "W007": ("Ward G", 19.0820, 72.8920),
    "W008": ("Ward H", 19.0680, 72.8720),
    "W009": ("Ward I", 19.0950, 72.8820),
    "W010": ("Ward J", 19.0600, 72.8780),
}

# Dates
start_date = datetime(2026, 1, 1)

dates = [
    start_date + timedelta(days=i)
    for i in range(181)
]

# --------------------------------------------------
# 1. WEATHER DATA
# --------------------------------------------------

weather_data = []

for date in dates:
    for ward_id in wards:

        rainfall = round(random.uniform(0, 120), 2)
        temperature = round(random.uniform(24, 34), 2)
        humidity = round(random.uniform(55, 90), 2)
        aqi = random.randint(50, 250)

        weather_data.append([
            date.strftime("%Y-%m-%d"),
            ward_id,
            rainfall,
            temperature,
            humidity,
            aqi
        ])

weather_df = pd.DataFrame(weather_data, columns=[
    "date",
    "ward_id",
    "rainfall",
    "temperature",
    "humidity",
    "aqi"
])

weather_df.to_csv(output_folder / "weather.csv", index=False)


# --------------------------------------------------
# 2. SENSOR DATA
# --------------------------------------------------

sensor_data = []

for date in dates:
    for ward_id in wards:

        traffic_density = random.randint(20, 100)
        water_level = round(random.uniform(10, 100), 2)
        waste_bin_level = round(random.uniform(10, 100), 2)

        sensor_data.append([
            date.strftime("%Y-%m-%d"),
            ward_id,
            traffic_density,
            water_level,
            waste_bin_level
        ])

sensor_df = pd.DataFrame(sensor_data, columns=[
    "date",
    "ward_id",
    "traffic_density",
    "water_level",
    "waste_bin_level"
])

sensor_df.to_csv(output_folder / "sensors.csv", index=False)


# --------------------------------------------------
# 3. WARD DATA
# --------------------------------------------------

ward_data = []

zones = {
    "W001": "South",
    "W002": "South",
    "W003": "West",
    "W004": "Central",
    "W005": "West",
    "W006": "Central",
    "W007": "East",
    "W008": "West",
    "W009": "North",
    "W010": "South"
}

for ward_id, (ward_name, latitude, longitude) in wards.items():

    ward_data.append([
        ward_id,
        ward_name,
        zones[ward_id],
        latitude,
        longitude
    ])

ward_df = pd.DataFrame(ward_data, columns=[
    "ward_id",
    "ward_name",
    "zone",
    "latitude",
    "longitude"
])

ward_df.to_csv(output_folder / "wards.csv", index=False)


# --------------------------------------------------
# COMPLETION MESSAGE
# --------------------------------------------------

print("Supporting datasets generated successfully!")
print()
print(f"Weather records: {len(weather_df)}")
print(f"Sensor records: {len(sensor_df)}")
print(f"Ward records: {len(ward_df)}")
print()
print("Files created:")
print("data/raw/weather.csv")
print("data/raw/sensors.csv")
print("data/raw/wards.csv")