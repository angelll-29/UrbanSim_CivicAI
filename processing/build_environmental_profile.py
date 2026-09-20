from pathlib import Path
import pandas as pd


INPUT = Path(
    "data/processed/mumbai_openaq_latest_measurements_qc.csv"
)

GREEN = Path(
    "data/processed/mumbai_green_space_ward_summary.csv"
)

POP = Path(
    "data/processed/mumbai_ward_population_2011.csv"
)

AREA = Path(
    "data/processed/mumbai_ward_area_density.csv"
)

OUTPUT = Path(
    "data/processed/mumbai_ward_environmental_profile.csv"
)


df = pd.read_csv(INPUT)
green = pd.read_csv(GREEN)
population = pd.read_csv(POP)
area = pd.read_csv(AREA)


# ---------------------------------------------------------
# Use only observations from the last 7 days.
# Historical observations remain in the source dataset.
# ---------------------------------------------------------

recent = df[
    df["freshness_status"].isin(
        [
            "CURRENT_24H",
            "RECENT_72H",
            "RECENT_7D"
        ]
    )
].copy()


recent["value"] = pd.to_numeric(
    recent["value"],
    errors="coerce"
)


# ---------------------------------------------------------
# Major environmental parameters
# ---------------------------------------------------------

parameters = [
    "pm25",
    "pm10",
    "no2",
    "so2",
    "o3",
    "co",
    "temperature",
    "relativehumidity"
]


recent = recent[
    recent["parameter_name"].isin(parameters)
].copy()


# ---------------------------------------------------------
# Create a 24-ward base
# ---------------------------------------------------------

wards = pd.DataFrame({
    "ward_code": sorted(
        area["ward_code"]
        .dropna()
        .unique()
    )
})


# ---------------------------------------------------------
# Latest observation per ward + parameter + unit
# ---------------------------------------------------------

recent = recent.sort_values(
    "datetime_utc"
)

latest = (
    recent
    .groupby(
        [
            "urban_ward_code",
            "parameter_name",
            "unit"
        ],
        as_index=False
    )
    .tail(1)
)


# ---------------------------------------------------------
# Reshape pollutant values
# ---------------------------------------------------------

value_table = latest.pivot_table(
    index="urban_ward_code",
    columns="parameter_name",
    values="value",
    aggfunc="last"
).reset_index()

value_table = value_table.rename(
    columns={
        "urban_ward_code": "ward_code"
    }
)


# ---------------------------------------------------------
# Station/measurement counts
# ---------------------------------------------------------

counts = (
    recent
    .groupby(
        [
            "urban_ward_code",
            "parameter_name"
        ]
    )
    .agg(
        station_count=(
            "openaq_location_id",
            "nunique"
        ),
        measurement_count=(
            "value",
            "count"
        )
    )
    .reset_index()
)

count_table = counts.pivot_table(
    index="urban_ward_code",
    columns="parameter_name",
    values="station_count",
    aggfunc="sum"
).reset_index()

count_table = count_table.rename(
    columns={
        "urban_ward_code": "ward_code"
    }
)

for parameter in parameters:

    if parameter in count_table.columns:

        count_table = count_table.rename(
            columns={
                parameter:
                    f"{parameter}_station_count"
            }
        )


# ---------------------------------------------------------
# Age of latest observation
# ---------------------------------------------------------

latest["data_age_hours"] = pd.to_numeric(
    latest["data_age_hours"],
    errors="coerce"
)

age_table = latest.pivot_table(
    index="urban_ward_code",
    columns="parameter_name",
    values="data_age_hours",
    aggfunc="last"
).reset_index()

age_table = age_table.rename(
    columns={
        "urban_ward_code": "ward_code"
    }
)

for parameter in parameters:

    if parameter in age_table.columns:

        age_table = age_table.rename(
            columns={
                parameter:
                    f"{parameter}_age_hours"
            }
        )


# ---------------------------------------------------------
# Merge into 24 wards
# ---------------------------------------------------------

result = wards.merge(
    value_table,
    on="ward_code",
    how="left"
)

result = result.merge(
    count_table,
    on="ward_code",
    how="left"
)

result = result.merge(
    age_table,
    on="ward_code",
    how="left"
)


# ---------------------------------------------------------
# Green space
# ---------------------------------------------------------

green_columns = [
    column
    for column in [
        "ward_code",
        "green_space_count",
        "green_space_share_pct"
    ]
    if column in green.columns
]

result = result.merge(
    green[green_columns],
    on="ward_code",
    how="left"
)


# ---------------------------------------------------------
# Population
# ---------------------------------------------------------

result = result.merge(
    population[
        [
            "ward_code",
            "population_2011"
        ]
    ],
    on="ward_code",
    how="left"
)


# ---------------------------------------------------------
# Area
# ---------------------------------------------------------

result = result.merge(
    area[
        [
            "ward_code",
            "area_sq_km"
        ]
    ],
    on="ward_code",
    how="left"
)


# ---------------------------------------------------------
# Green-space derived indicators
# ---------------------------------------------------------

result["green_spaces_per_km2"] = (
    result["green_space_count"]
    /
    result["area_sq_km"]
)

result["green_spaces_per_100k_population"] = (
    result["green_space_count"]
    /
    result["population_2011"]
    * 100000
)


# ---------------------------------------------------------
# Overall environmental data freshness
# ---------------------------------------------------------

freshness_counts = (
    recent
    .groupby("urban_ward_code")
    .size()
)

result["recent_measurement_count"] = (
    result["ward_code"]
    .map(freshness_counts)
    .fillna(0)
    .astype(int)
)

result["environmental_station_presence"] = (
    result["recent_measurement_count"] > 0
)


# ---------------------------------------------------------
# Clean ordering
# ---------------------------------------------------------

result = result.sort_values(
    "ward_code"
).reset_index(drop=True)


OUTPUT.parent.mkdir(
    parents=True,
    exist_ok=True
)

result.to_csv(
    OUTPUT,
    index=False
)


print("\nUrbanSim Environmental Profile")
print("--------------------------------")

print(
    "Wards:",
    len(result)
)

print(
    "Wards with recent measurements:",
    result["environmental_station_presence"].sum()
)

print(
    "Wards without recent measurements:",
    (
        ~result[
            "environmental_station_presence"
        ]
    ).sum()
)

print("\nPollutant coverage:")

for parameter in [
    "pm25",
    "pm10",
    "no2",
    "so2",
    "o3",
    "co"
]:

    column = f"{parameter}_station_count"

    if column in result.columns:

        print(
            f"{parameter.upper():5} : "
            f"{(result[column] > 0).sum()} wards"
        )

print("\nWard environmental profile:")

display_columns = [
    "ward_code",
    "pm25",
    "pm10",
    "no2",
    "so2",
    "o3",
    "co",
    "recent_measurement_count"
]

display_columns = [
    c
    for c in display_columns
    if c in result.columns
]

print(
    result[
        display_columns
    ].to_string(index=False)
)

print(
    f"\nOutput: {OUTPUT}"
)
