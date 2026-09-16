import pandas as pd
import random
from datetime import datetime, timedelta
from pathlib import Path

# Make results reproducible
random.seed(42)

# Output location
output_file = Path("data/raw/complaints.csv")

# Mumbai-style wards and approximate locations
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

complaints = {
    "Waste": [
        "Garbage not collected",
        "Garbage overflowing",
        "Waste collection delayed",
        "Waste dumped on road",
        "Dustbin is full",
    ],
    "Water": [
        "Water leakage on road",
        "Water supply interruption",
        "Low water pressure",
        "Pipeline leakage",
        "Dirty water supply",
    ],
    "Road": [
        "Pothole near bus stop",
        "Road damaged",
        "Large pothole on main road",
        "Broken footpath",
        "Road surface damaged",
    ],
    "Electricity": [
        "Street light not working",
        "Street light damaged",
        "Power line issue",
        "Electric pole damaged",
        "Street light flickering",
    ],
}

categories = list(complaints.keys())
statuses = ["Open", "Resolved", "In Progress"]

start_date = datetime(2026, 1, 1)

data = []

for i in range(1, 501):
    ward_id = random.choice(list(wards.keys()))
    ward_name, base_lat, base_lon = wards[ward_id]

    category = random.choice(categories)
    complaint_text = random.choice(complaints[category])

    timestamp = start_date + timedelta(
        days=random.randint(0, 180),
        hours=random.randint(0, 23),
        minutes=random.randint(0, 59)
    )

    # Small location variation around the ward
    latitude = round(base_lat + random.uniform(-0.005, 0.005), 6)
    longitude = round(base_lon + random.uniform(-0.005, 0.005), 6)

    status = random.choice(statuses)

    data.append([
        f"C{i:04d}",
        timestamp.strftime("%Y-%m-%d %H:%M:%S"),
        complaint_text,
        category,
        latitude,
        longitude,
        ward_id,
        status
    ])

# Create DataFrame
df = pd.DataFrame(data, columns=[
    "complaint_id",
    "timestamp",
    "complaint_text",
    "category",
    "latitude",
    "longitude",
    "ward_id",
    "status"
])

# Save
df.to_csv(output_file, index=False)

print("Dataset generated successfully!")
print(f"Records created: {len(df)}")
print(f"Wards: {df['ward_id'].nunique()}")
print(f"Categories: {df['category'].nunique()}")
print(f"Saved to: {output_file}")