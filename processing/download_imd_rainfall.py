import requests
from pathlib import Path

BASE = "https://mausam.imd.gov.in/mumbai/mcdata"

files = {
    "mumbai_daily_rainfall.gif": "DRF_Mumbai.gif",
    "colaba_cumulative.gif": "Cum_Colaba.gif",
    "santacruz_cumulative.gif": "Cum_Scz.gif",
    "colaba_september.gif": "Monthly_Col_Sep.gif",
    "santacruz_september.gif": "Monthly_Scz_Sep.gif",
}

OUT = Path("data/external/imd")
OUT.mkdir(parents=True, exist_ok=True)

for output_name, remote_name in files.items():

    url = f"{BASE}/{remote_name}"

    response = requests.get(
        url,
        timeout=30
    )

    print(
        f"{output_name} | HTTP {response.status_code}"
    )

    if response.status_code == 200:

        path = OUT / output_name

        path.write_bytes(
            response.content
        )

        print(
            f"  Saved: {path}"
        )

print("\nIMD rainfall resources downloaded.")
