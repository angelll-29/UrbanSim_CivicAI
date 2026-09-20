from pathlib import Path
import pandas as pd

EXTERNAL = Path("data/external")

files = [
    "Mumbai City Enrolment Data Part 1.csv",
    "Mumbai City Enrolment Data Part 2.csv",
    "Mumbai City Facilities.csv",
    "Mumbai City Profile Part 1.csv",
    "Mumbai City Profile Part 2.csv",
    "Mumbai City Teachers Data.csv",
    "Mumbai Suburban Enrolment Data Part 1.csv",
    "Mumbai Suburban Enrolment Data Part 2.csv",
    "Mumbai Suburban Facilities.csv",
    "Mumbai Suburban Profile Part 1.csv",
    "Mumbai Suburban Profile Part 2.csv",
    "Mumbai Suburban Teachers Data.csv",
]

for filename in files:
    path = EXTERNAL / filename

    print("\n" + "=" * 100)
    print(filename)
    print("=" * 100)

    try:
        df = pd.read_csv(path, low_memory=False)

        print(f"Rows    : {len(df):,}")
        print(f"Columns : {len(df.columns):,}")

        print("\nColumns:")
        for i, col in enumerate(df.columns, 1):
            print(f"{i:3}. {col}")

        print("\nFirst 2 rows:")
        print(df.head(2).to_string())

    except Exception as e:
        print(f"ERROR: {e}")