import pandas as pd
from pathlib import Path

INPUT = Path("data/external/Mumbai City Profile Part 1.csv")
OUTPUT = Path("data/processed/udise_city_school_ward_mapping.csv")

df = pd.read_csv(INPUT)

# Extract the broad BMC ward prefix from LGD ward name.
# Examples:
# K/West - Ward No. 61 -> KW
# R/South - Ward No. 22 -> RS
# F/North - Ward No. 177 -> FN
# L - Ward No. 165 -> L

def normalize_udise_ward(value):
    if pd.isna(value):
        return None

    value = str(value).strip().upper()

    # Take everything before " - WARD"
    prefix = value.split(" - WARD")[0].strip()

    # Special source naming variants
    prefix = prefix.replace("MCGM", "").strip()

    # Normalize slash-based ward names
    mapping = {
        "A": "A",
        "B": "B",
        "C": "C",
        "D": "D",
        "E": "E",
        "F/NORTH": "FN",
        "F/SOUTH": "FS",
        "G/NORTH": "GN",
        "G/SOUTH": "GS",
        "H/EAST": "HE",
        "H/WEST": "HW",
        "K/EAST": "KE",
        "K/WEST": "KW",
        "L": "L",
        "M/EAST": "ME",
        "M/WEST": "MW",
        "N": "N",
        "P/NORTH": "PN",
        "P/SOUTH": "PS",
        "R/CENTRAL": "RC",
        "R/NORTH": "RN",
        "R/SOUTH": "RS",
        "S": "S",
        "T": "T",
    }

    return mapping.get(prefix)


df["bmc_ward_code"] = df["lgd_ward_name"].apply(normalize_udise_ward)

# Keep the original source field for provenance
output = df[
    [
        "pseudocode",
        "lgd_ward_name",
        "bmc_ward_code",
        "pincode",
    ]
].copy()

OUTPUT.parent.mkdir(parents=True, exist_ok=True)
output.to_csv(OUTPUT, index=False)

print("UDISE City ward mapping created successfully.")
print("Rows:", len(output))

print("\nUnique source LGD wards:",
      output["lgd_ward_name"].nunique())

print("Unique BMC wards:",
      output["bmc_ward_code"].nunique())

print("\nMissing BMC ward mappings:",
      output["bmc_ward_code"].isna().sum())

print("\nBMC ward distribution:")
print(
    output["bmc_ward_code"]
    .value_counts()
    .sort_index()
    .to_string()
)

print("\nSaved:")
print(OUTPUT)