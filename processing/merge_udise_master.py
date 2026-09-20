import pandas as pd

master_file = "data/processed/udise_school_master_base.csv"
enrolment_file = "data/processed/udise_school_enrolment.csv"
output_file = "data/processed/udise_school_master.csv"

master = pd.read_csv(master_file)
enrolment = pd.read_csv(enrolment_file)

master["pseudocode"] = master["pseudocode"].astype(str)
enrolment["pseudocode"] = enrolment["pseudocode"].astype(str)

print("Master schools:", len(master))
print("Enrolment schools:", len(enrolment))

merged = master.merge(
    enrolment,
    on="pseudocode",
    how="left",
    validate="one_to_one"
)

missing = merged["total_enrolment"].isna().sum()

print("Merged schools:", len(merged))
print("Missing enrolment:", missing)

assert len(merged) == len(master)
assert missing == 11

merged.to_csv(output_file, index=False)

print("\nCreated:", output_file)
print("Rows:", len(merged))
print("Columns:", len(merged.columns))
