import pandas as pd
from pathlib import Path
import hashlib

# Input and output files
input_file = Path("data/processed/urban_integrated.csv")
output_file = Path("data/processed/urban_secure.csv")

# Read integrated data
df = pd.read_csv(input_file)

print("Starting data anonymization...")
print(f"Records received: {len(df)}")

# --------------------------------------------------
# 1. PSEUDONYMIZE COMPLAINT IDs
# --------------------------------------------------

def anonymize_id(complaint_id):
    return hashlib.sha256(
        complaint_id.encode()
    ).hexdigest()[:12]


df["anonymous_id"] = (
    df["complaint_id"]
    .astype(str)
    .apply(anonymize_id)
)

# Remove original complaint ID
df = df.drop(columns=["complaint_id"])


# --------------------------------------------------
# 2. PROTECT LOCATION INFORMATION
# --------------------------------------------------

# The integrated dataset contains complaint coordinates
# as latitude_x / longitude_x.

if "latitude_x" in df.columns:
    df["latitude_x"] = df["latitude_x"].round(3)

if "longitude_x" in df.columns:
    df["longitude_x"] = df["longitude_x"].round(3)


# --------------------------------------------------
# 3. REMOVE UNNECESSARY PERSONAL INFORMATION
# --------------------------------------------------

personal_columns = [
    "name",
    "phone",
    "email",
    "address"
]

for column in personal_columns:
    if column in df.columns:
        df = df.drop(columns=[column])


# --------------------------------------------------
# 4. SAVE SECURE DATASET
# --------------------------------------------------

df.to_csv(output_file, index=False)

print()
print("Anonymization completed!")
print(f"Records: {len(df)}")
print(f"Columns after privacy protection: {len(df.columns)}")
print(f"Saved to: {output_file}")
print()
print("Privacy protections applied:")
print("- Complaint IDs pseudonymized")
print("- Location coordinates reduced in precision")
print("- Unnecessary personal information removed")