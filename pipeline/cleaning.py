import pandas as pd
from pathlib import Path

# File locations
input_file = Path("data/processed/complaints_validated.csv")
output_file = Path("data/processed/complaints_cleaned.csv")

# Read validated data
df = pd.read_csv(input_file)

print("Starting data cleaning...")
print(f"Records received: {len(df)}")

# Remove duplicate records
before = len(df)
df = df.drop_duplicates(subset="complaint_id")
duplicates_removed = before - len(df)

# Clean text columns
df["complaint_text"] = df["complaint_text"].astype(str).str.strip()
df["category"] = df["category"].astype(str).str.strip().str.title()
df["status"] = df["status"].astype(str).str.strip().str.title()
df["ward_id"] = df["ward_id"].astype(str).str.strip()

# Convert timestamp to proper datetime format
df["timestamp"] = pd.to_datetime(df["timestamp"], errors="coerce")

# Convert location values to numbers
df["latitude"] = pd.to_numeric(df["latitude"], errors="coerce")
df["longitude"] = pd.to_numeric(df["longitude"], errors="coerce")

# Remove rows where important values became invalid
df = df.dropna(
    subset=[
        "complaint_id",
        "timestamp",
        "complaint_text",
        "category",
        "latitude",
        "longitude",
        "ward_id",
        "status"
    ]
)

# Save cleaned data
df.to_csv(output_file, index=False)

print("Cleaning completed!")
print(f"Duplicates removed: {duplicates_removed}")
print(f"Clean records: {len(df)}")
print(f"Saved to: {output_file}")