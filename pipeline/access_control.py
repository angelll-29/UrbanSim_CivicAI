import pandas as pd
from pathlib import Path

input_file = Path("data/processed/urban_secure.csv")

df = pd.read_csv(input_file)

print("UrbanSim Civic AI - Data Access Control")
print("---------------------------------------")

role = input("Enter role (Admin / Civic Officer / Citizen): ").strip().lower()

print()

if role == "admin":

    print("Access granted: Admin")
    print("Showing complete authorized dataset.")
    print()

    print(df.head())

elif role == "civic officer":

    print("Access granted: Civic Officer")
    print("Showing operational urban data.")
    print()

    officer_data = df[
        [
            "anonymous_id",
            "category",
            "status",
            "ward_id",
            "priority",
            "date"
        ]
    ]

    print(officer_data.head())

elif role == "citizen":

    print("Access granted: Citizen")
    print("Showing public information only.")
    print()

    citizen_data = df[
        [
            "category",
            "status",
            "ward_id",
            "priority"
        ]
    ]

    print(citizen_data.head())

else:

    print("Access denied!")
    print("Invalid role.")