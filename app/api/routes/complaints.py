import os, math
import pandas as pd
from fastapi import APIRouter

router = APIRouter()

ROOT = os.path.dirname(os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__)))))
CCRS_CSV = os.path.join(ROOT, 'data', 'processed', 'mumbai_ccrs_ward_complaints_2024.csv')

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

@router.get('/summary')
def get_complaints_summary():
    if os.path.exists(CCRS_CSV):
        df = pd.read_csv(CCRS_CSV)
        return clean_records(df.to_dict(orient='records'))
    return []
