import pandas as pd
from pathlib import Path

# Input files
complaints_file = Path("data/processed/complaints_transformed.csv")
weather_file = Path("data/raw/weather.csv")
sensors_file = Path("data/raw/sensors.csv")
wards_file = Path("data/raw/wards.csv")

# Output file
output_file = Path("data/processed/urban_integrated.csv")

print("Starting data integration...")

# Read datasets
complaints = pd.read_csv(complaints_file)
weather = pd.read_csv(weather_file)
sensors = pd.read_csv(sensors_file)
wards = pd.read_csv(wards_file)

print(f"Complaints: {len(complaints)}")
print(f"Weather records: {len(weather)}")
print(f"Sensor records: {len(sensors)}")
print(f"Wards: {len(wards)}")

# Make sure date columns have the same format
complaints["date"] = pd.to_datetime(
    complaints["date"]
).dt.strftime("%Y-%m-%d")

weather["date"] = pd.to_datetime(
    weather["date"]
).dt.strftime("%Y-%m-%d")

sensors["date"] = pd.to_datetime(
    sensors["date"]
).dt.strftime("%Y-%m-%d")

# Integrate complaint data with ward information
integrated = complaints.merge(
    wards,
    on="ward_id",
    how="left"
)

# Integrate weather information
integrated = integrated.merge(
    weather,
    on=["ward_id", "date"],
    how="left"
)

# Integrate sensor information
integrated = integrated.merge(
    sensors,
    on=["ward_id", "date"],
    how="left"
)

# Save integrated dataset
integrated.to_csv(output_file, index=False)

print()
print("Data integration completed!")
print(f"Final records: {len(integrated)}")
print(f"Final columns: {len(integrated.columns)}")
print(f"Saved to: {output_file}")