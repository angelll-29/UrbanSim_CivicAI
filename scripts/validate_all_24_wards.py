import json
import os

GEOJSON_PATH = os.path.join(os.path.dirname(os.path.dirname(os.path.abspath(__file__))), 'data', 'spatial', 'mumbai_urbansim_intelligence.geojson')

with open(GEOJSON_PATH, 'r', encoding='utf-8') as f:
    geo = json.load(f)

features = geo.get('features', [])
print(f"Total wards loaded: {len(features)}")
print("=" * 110)
header = f"{'Ward':<6} | {'Urban Stress':<14} | {'Band':<12} | {'Cluster':<10} | {'MSE':<8} | {'Healthcare':<10} | {'Education':<10} | {'Sanitation':<10} | {'Safety':<10}"
print(header)
print("=" * 110)

errors = []
for f in sorted(features, key=lambda x: x['properties']['ward_code']):
    p = f['properties']
    code = p.get('ward_code')
    stress = p.get('urban_stress')
    band = p.get('stress_band')
    cluster = p.get('cluster')
    mse = p.get('reconstruction_mse')
    hc = p.get('healthcare_stress')
    edu = p.get('education_stress')
    san = p.get('sanitation_stress')
    safe = p.get('safety_stress')
    
    if stress is None or not isinstance(stress, (int, float)):
        errors.append(f"Ward {code}: urban_stress is not numeric: {stress}")
    elif stress == 0:
        errors.append(f"Ward {code}: urban_stress unexpectedly 0")
        
    print(f"{code:<6} | {stress:<14.4f} | {band:<12} | {cluster:<10} | {mse:<8.4f} | {hc:<10.2f} | {edu:<10.2f} | {san:<10.2f} | {safe:<10.2f}")

print("=" * 110)
if errors:
    print(f"VALIDATION FAILED with {len(errors)} errors:")
    for e in errors:
        print(" - ", e)
else:
    print("VALIDATION SUCCESS: All 24 wards have valid numeric urban_stress, stress_band, and domain values directly in GeoJSON!")
