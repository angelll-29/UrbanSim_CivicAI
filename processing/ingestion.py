import pandas as pd
from pathlib import Path
from datetime import datetime

# File locations
raw_file = Path("data/raw/complaints.csv")
processed_file = Path("data/processed/complaints_ingested.csv")

# Check if the raw file exists
if not raw_file.exists():
    print("ERROR: complaints.csv not found.")
    exit()

# Read the raw data
df = pd.read_csv(raw_file)

# Basic ingestion information
print("Data ingestion successful!")
print(f"Records loaded: {len(df)}")
print(f"Columns: {len(df.columns)}")
print(f"Ingestion time: {datetime.now()}")

# Save the ingested data
df.to_csv(processed_file, index=False)

print(f"Saved to: {processed_file}")