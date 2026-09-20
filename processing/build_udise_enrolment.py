import pandas as pd

FILES = [
    "data/external/Mumbai City Enrolment Data Part 1.csv",
    "data/external/Mumbai Suburban Enrolment Data Part 1.csv"
]

BOY_COLS = [f"{c}_b" for c in ["cpp","c1","c2","c3","c4","c5","c6","c7","c8","c9","c10","c11","c12"]]
GIRL_COLS = [f"{c}_g" for c in ["cpp","c1","c2","c3","c4","c5","c6","c7","c8","c9","c10","c11","c12"]]

frames = []

for file in FILES:
    df = pd.read_csv(file)

    # Only the validated base enrolment record
    df = df[
        (df["item_group"] == 1) &
        (df["item_id"] == 1)
    ].copy()

    df["boys"] = df[BOY_COLS].sum(axis=1)
    df["girls"] = df[GIRL_COLS].sum(axis=1)
    df["total_enrolment"] = df["boys"] + df["girls"]

    frames.append(
        df[[
            "pseudocode",
            "boys",
            "girls",
            "total_enrolment"
        ]]
    )

out = pd.concat(frames, ignore_index=True)

# Safety checks
assert out["pseudocode"].notna().all()
assert out["pseudocode"].duplicated().sum() == 0
assert (out["total_enrolment"] == out["boys"] + out["girls"]).all()

output = "data/processed/udise_school_enrolment.csv"
out.to_csv(output, index=False)

print("Created:", output)
print("Rows:", len(out))
print("Unique schools:", out["pseudocode"].nunique())
print("Total boys:", int(out["boys"].sum()))
print("Total girls:", int(out["girls"].sum()))
print("Total enrolment:", int(out["total_enrolment"].sum()))
