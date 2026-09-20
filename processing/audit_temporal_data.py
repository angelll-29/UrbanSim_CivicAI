import pandas as pd
import glob
import os

TIME_TERMS = [
    "date", "year", "month", "quarter",
    "time", "timestamp", "period"
]

files = glob.glob("data/**/*.csv", recursive=True)

print("=" * 60)
print("URBANSIM TEMPORAL DATA AUDIT")
print("=" * 60)

for f in files:

    name = os.path.basename(f)

    try:
        df = pd.read_csv(
            f,
            encoding="utf-8",
            encoding_errors="replace"
        )

        time_fields = [
            c for c in df.columns
            if any(term in c.lower() for term in TIME_TERMS)
        ]

        print(f"\n{name}")
        print(f"Rows       : {len(df):,}")
        print(f"Columns    : {len(df.columns)}")
        print(f"Time fields: {time_fields}")

        for col in time_fields:
            values = (
                df[col]
                .dropna()
                .astype(str)
                .head(5)
                .tolist()
            )

            print(f"  {col}: {values}")

    except Exception as e:
        print(f"\n{name}")
        print(f"ERROR: {e}")

print("\n" + "=" * 60)
print("AUDIT COMPLETE")
print("=" * 60)
