import os, math
import pandas as pd
from fastapi import APIRouter

router = APIRouter()

ROOT = os.path.dirname(os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__)))))
ANOMALY_CSV = os.path.join(ROOT, 'data', 'processed', 'urban_ward_anomaly_scores.csv')
CLUSTERS_CSV = os.path.join(ROOT, 'data', 'processed', 'urban_cluster_profiles.csv')
SCENARIOS_CSV = os.path.join(ROOT, 'data', 'processed', 'urban_scenario_results_v2.csv')

def clean_records(records):
    cleaned = []
    for r in records:
        cr = {}
        for k, v in r.items():
            if isinstance(v, float) and (math.isnan(v) or math.isinf(v)):
                cr[k] = None
            else:
                cr[k] = v
        cleaned.append(cr)
    return cleaned

@router.get('/anomalies')
def get_anomalies():
    if os.path.exists(ANOMALY_CSV):
        df = pd.read_csv(ANOMALY_CSV)
        return clean_records(df.to_dict(orient='records'))
    return []

@router.get('/clusters')
def get_clusters():
    if os.path.exists(CLUSTERS_CSV):
        df = pd.read_csv(CLUSTERS_CSV)
        return clean_records(df.to_dict(orient='records'))
    return []

@router.get('/scenarios')
def get_scenarios():
    if os.path.exists(SCENARIOS_CSV):
        df = pd.read_csv(SCENARIOS_CSV)
        return clean_records(df.to_dict(orient='records'))
    return []
