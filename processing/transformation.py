import pandas as pd
from pathlib import Path

# File locations
input_file = Path("data/processed/complaints_cleaned.csv")
output_file = Path("data/processed/complaints_transformed.csv")

# Read cleaned data
df = pd.read_csv(input_file)

print("Starting data transformation...")
print(f"Records received: {len(df)}")

# Convert timestamp
df["timestamp"] = pd.to_datetime(df["timestamp"])

# Create useful time features
df["date"] = df["timestamp"].dt.date
df["hour"] = df["timestamp"].dt.hour
df["day_of_week"] = df["timestamp"].dt.day_name()
df["month"] = df["timestamp"].dt.month

# Create priority based on complaint category
priority_map = {
    "Water": "High",
    "Road": "High",
    "Waste": "Medium",
    "Electricity": "Medium"
}

df["priority"] = df["category"].map(priority_map)

# Save transformed data
df.to_csv(output_file, index=False)

print("Transformation completed!")
print(f"Records: {len(df)}")
print(f"New columns added: date, hour, day_of_week, month, priority")
print(f"Saved to: {output_file}")