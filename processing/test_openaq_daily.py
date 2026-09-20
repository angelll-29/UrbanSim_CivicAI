import os
import requests
from pathlib import Path
from dotenv import load_dotenv

load_dotenv(dotenv_path=Path(".env").resolve())

API_KEY = os.getenv("OPENAQ_API_KEY")

if not API_KEY:
    raise RuntimeError("OPENAQ_API_KEY not found in .env")

sensor_id = 12238567

url = (
    f"https://api.openaq.org/v3/"
    f"sensors/{sensor_id}/days"
)

params = {
    "datetime_from": "2025-02-18T00:00:00Z",
    "datetime_to": "2025-03-18T00:00:00Z",
    "limit": 100,
    "page": 1
}

response = requests.get(
    url,
    headers={"X-API-Key": API_KEY},
    params=params,
    timeout=30
)

print("HTTP:", response.status_code)
print("\nURL:")
print(response.url)

print("\nResponse:")
print(response.text[:12000])
