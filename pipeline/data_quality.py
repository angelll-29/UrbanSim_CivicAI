import pandas as pd
from pathlib import Path

# Input file
input_file = Path("data/processed/urban_integrated.csv")

# Read integrated data
df = pd.read_csv(input_file)

print("Starting data quality check...")
print()

# --------------------------------------------------
# 1. BASIC INFORMATION
# --------------------------------------------------

print("DATASET INFORMATION")
print("--------------------")
print(f"Total records: {len(df)}")
print(f"Total columns: {len(df.columns)}")
print()

# --------------------------------------------------
# 2. MISSING VALUES
# --------------------------------------------------

print("MISSING VALUES")
print("--------------")

missing_values = df.isnull().sum()

total_missing = missing_values.sum()

if total_missing == 0:
    print("No missing values found!")
else:
    print(missing_values[missing_values > 0])

print()

# --------------------------------------------------
# 3. DUPLICATE COMPLAINT IDs
# --------------------------------------------------

print("DUPLICATE CHECK")
print("---------------")

duplicate_ids = df["complaint_id"].duplicated().sum()

print(f"Duplicate complaint IDs: {duplicate_ids}")
print()

# --------------------------------------------------
# 4. CATEGORY DISTRIBUTION
# --------------------------------------------------

print("COMPLAINT CATEGORY DISTRIBUTION")
print("-------------------------------")

print(df["category"].value_counts())
print()

# --------------------------------------------------
# 5. STATUS DISTRIBUTION
# --------------------------------------------------

print("COMPLAINT STATUS DISTRIBUTION")
print("-----------------------------")

print(df["status"].value_counts())
print()

# --------------------------------------------------
# 6. WARD DISTRIBUTION
# --------------------------------------------------

print("WARD DISTRIBUTION")
print("-----------------")

print(df["ward_id"].value_counts())
print()

# --------------------------------------------------
# 7. FINAL RESULT
# --------------------------------------------------

print("DATA QUALITY CHECK COMPLETED!")

if total_missing == 0 and duplicate_ids == 0:
    print("Result: PASS")
    print("The integrated dataset is ready for the next stage.")
else:
    print("Result: REVIEW REQUIRED")