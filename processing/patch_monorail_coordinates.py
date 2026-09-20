import pandas as pd

INPUT_FILE = "data/processed/mumbai_metro_monorail_stations.csv"

df = pd.read_csv(INPUT_FILE)

coordinates = {
    "MONO-002": {
        "latitude": 19.052700,
        "longitude": 72.894199,
    },
    "MONO-003": {
        "latitude": 19.043849,
        "longitude": 72.893397,
    },
}

for station_id, coord in coordinates.items():

    mask = df["station_id"] == station_id

    df.loc[mask, "latitude"] = coord["latitude"]
    df.loc[mask, "longitude"] = coord["longitude"]

    df.loc[mask, "geocode_status"] = "WEB_VERIFIED"

    df.loc[mask, "geocode_display_name"] = (
        "Web-verified Monorail station coordinates"
    )

df.to_csv(INPUT_FILE, index=False)

print("=" * 60)
print("MONORAIL COORDINATE PATCH")
print("=" * 60)

result = df[
    df["station_id"].isin(coordinates.keys())
][
    [
        "station_id",
        "station_name",
        "latitude",
        "longitude",
        "geocode_status",
    ]
]

print(result.to_string(index=False))

print("\nSaved:", INPUT_FILE)