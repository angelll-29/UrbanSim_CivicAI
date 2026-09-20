import os, json
import pandas as pd
from fastapi import APIRouter

router = APIRouter()

ROOT = os.path.dirname(os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__)))))
GEOJSON_PATH = os.path.join(ROOT, 'data', 'spatial', 'mumbai_urbansim_intelligence.geojson')
BASE_CSV_PATH = os.path.join(ROOT, 'data', 'processed', 'mumbai_ward_civic_intelligence_base_area.csv')

@router.get('/summary')
def get_dashboard_summary():
    summary = {
        'total_wards': 24,
        'domains_count': 7,
        'ai_clusters_count': 4,
        'ai_anomaly_candidates_count': 3,
        'metro_monorail_nodes': 155,
        'bus_stops_count': 5555,
        'city_name': 'Mumbai',
        'authority': 'Brihanmumbai Municipal Corporation (BMC)',
        'stress_model': 'Urban Stress V2 (Percentile-Normalized Composite Index)',
    }
    if os.path.exists(GEOJSON_PATH):
        with open(GEOJSON_PATH, 'r', encoding='utf-8') as f:
            data = json.load(f)
            stresses = [f['properties'].get('urban_stress', 0) for f in data.get('features', []) if f['properties'].get('urban_stress') is not None]
            if stresses:
                summary['avg_urban_stress'] = round(sum(stresses) / len(stresses), 2)
                summary['min_urban_stress'] = round(min(stresses), 2)
                summary['max_urban_stress'] = round(max(stresses), 2)
    return summary
