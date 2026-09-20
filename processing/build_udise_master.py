from pathlib import Path
import pandas as pd

BASE = Path("data/external")
OUT = Path("data/processed")
OUT.mkdir(parents=True, exist_ok=True)


def load_csv(filename):
    path = BASE / filename

    if not path.exists():
        raise FileNotFoundError(f"Missing file: {path}")

    df = pd.read_csv(path, low_memory=False)

    if "pseudocode" not in df.columns:
        raise ValueError(f"'pseudocode' missing from {filename}")

    df["pseudocode"] = (
        pd.to_numeric(df["pseudocode"], errors="coerce")
        .astype("Int64")
        .astype(str)
    )

    return df


def prepare_city():
    facilities = load_csv("Mumbai City Facilities.csv")
    teachers = load_csv("Mumbai City Teachers Data.csv")

    facilities = facilities.add_prefix("facility_")
    teachers = teachers.add_prefix("teacher_")

    facilities = facilities.rename(
        columns={"facility_pseudocode": "pseudocode"}
    )

    teachers = teachers.rename(
        columns={"teacher_pseudocode": "pseudocode"}
    )

    df = facilities.merge(
        teachers,
        on="pseudocode",
        how="outer",
        validate="one_to_one"
    )

    df.insert(0, "district_area", "Mumbai City")

    return df


def prepare_suburban():
    facilities = load_csv("Mumbai Suburban Facilities.csv")
    teachers = load_csv("Mumbai Suburban Teachers Data.csv")

    facilities = facilities.add_prefix("facility_")
    teachers = teachers.add_prefix("teacher_")

    facilities = facilities.rename(
        columns={"facility_pseudocode": "pseudocode"}
    )

    teachers = teachers.rename(
        columns={"teacher_pseudocode": "pseudocode"}
    )

    df = facilities.merge(
        teachers,
        on="pseudocode",
        how="outer",
        validate="one_to_one"
    )

    df.insert(0, "district_area", "Mumbai Suburban")

    return df


print("=" * 80)
print("BUILDING UDISE SCHOOL MASTER")
print("=" * 80)

city = prepare_city()
suburban = prepare_suburban()

master = pd.concat(
    [city, suburban],
    ignore_index=True
)

# Remove accidental duplicate school IDs across districts only if they occur.
duplicate_count = master["pseudocode"].duplicated().sum()

print(f"\nMumbai City schools     : {len(city):,}")
print(f"Mumbai Suburban schools : {len(suburban):,}")
print(f"Combined schools        : {len(master):,}")
print(f"Duplicate pseudocodes   : {duplicate_count:,}")

# Basic completeness checks
print("\nDistrict distribution:")
print(master["district_area"].value_counts())

print("\nMissing values in key datasets:")
print(
    master[
        [
            "pseudocode",
            "facility_building_status",
            "teacher_total_tch"
        ]
    ].isna().sum()
)

output = OUT / "udise_school_master_base.csv"
master.to_csv(output, index=False)

print(f"\nSaved:")
print(output)
print(f"Rows    : {len(master):,}")
print(f"Columns : {len(master.columns):,}")