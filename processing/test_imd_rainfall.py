import requests

URL = "https://mausam.imd.gov.in/api/districtwise_rainfall_api.php"

response = requests.get(
    URL,
    timeout=30
)

print("HTTP status:", response.status_code)
print("\nContent type:")
print(response.headers.get("content-type"))

print("\nResponse preview:")
print(response.text[:5000])
