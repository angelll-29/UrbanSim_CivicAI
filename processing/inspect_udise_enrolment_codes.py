from pathlib import Path
import pandas as pd

BASE = Path("data/external")

FILES = [
    "Mumbai City Enrolment Data Part 1.csv",
    "Mumbai City Enrolment Data Part 2.csv",
    "Mumbai Suburban Enrolment Data Part 1.csv",
    "Mumbai Suburban Enrolment Data Part 2.csv",
]

VALUE_COLS = [
    "cpp_b", "cpp_g",
    "c1_b", "c1_g",
    "c2_b", "c2_g",
    "c3_b", "c3_g",
    "c4_b", "c4_g",
    "c5_b", "c5_g",
    "c6_b", "c6_g",
    "c7_b", "c7_g",
    "c8_b", "c8_g",
    "c9_b", "c9_g",
    "c10_b", "c10_g",
    "c11_b", "c11_g",
    "c12_b", "c12_g",
]

for filename in FILES:
    print("\n" + "=" * 100)
    print(filename)
    print("=" * 100)

    df = pd.read_csv(BASE / filename, low_memory=False)

    grouped = (
        df.groupby(["item_group", "item_id"])[VALUE_COLS]
        .sum()
        .reset_index()
    )

    grouped["total_students_all_classes"] = grouped[VALUE_COLS].sum(axis=1)

    print(grouped.to_string(index=False))