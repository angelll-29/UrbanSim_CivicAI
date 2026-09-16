import pandas as pd
from pathlib import Path

# File locations
input_file = Path("data/processed/complaints_ingested.csv")
valid_file = Path("data/processed/complaints_validated.csv")
rejected_file = Path("data/rejected/complaints_rejected.csv")

# Required columns
required_columns = [
    "complaint_id",
    "timestamp",
    "complaint_text",
    "category",
    "latitude",
    "longitude",
    "ward_id",
    "status"
]

# Allowed values
valid_categories = ["Waste", "Water", "Road", "Electricity"]
valid_statuses = ["Open", "Resolved", "In Progress"]

# Read data
df = pd.read_csv(input_file)

print("Starting data validation...")
print(f"Records received: {len(df)}")

# Check required columns
missing_columns = [
    column for column in required_columns
    if column not in df.columns
]

if missing_columns:
    print("Validation failed!")
    print("Missing columns:", missing_columns)
    exit()

# Find invalid records
invalid = (
    df["complaint_id"].isna()
    | df["complaint_id"].duplicated()
    | df["category"].isna()
    | ~df["category"].isin(valid_categories)
    | df["status"].isna()
    | ~df["status"].isin(valid_statuses)
    | df["latitude"].isna()
    | df["longitude"].isna()
)

# Separate valid and rejected records
valid_df = df[~invalid]
rejected_df = df[invalid]

# Save results
valid_df.to_csv(valid_file, index=False)
rejected_df.to_csv(rejected_file, index=False)

print("Validation completed!")
print(f"Valid records: {len(valid_df)}")
print(f"Rejected records: {len(rejected_df)}")
print(f"Valid data saved to: {valid_file}")
print(f"Rejected data saved to: {rejected_file}")