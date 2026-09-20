import os, json, math
import pandas as pd
from fastapi import APIRouter, HTTPException

router = APIRouter()

ROOT = os.path.dirname(os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__)))))
GEOJSON_PATH = os.path.join(ROOT, 'data', 'spatial', 'mumbai_urbansim_intelligence.geojson')
BASE_CSV_PATH = os.path.join(ROOT, 'data', 'processed', 'mumbai_ward_civic_intelligence_base_area.csv')
EXP_CSV_PATH = os.path.join(ROOT, 'data', 'processed', 'urban_civic_ai_explanations.csv')

def clean_record(d):
    clean = {}
    for k, v in d.items():
        if isinstance(v, float) and (math.isnan(v) or math.isinf(v)):
            clean[k] = None
        else:
            clean[k] = v
    return clean

@router.get('/')
def get_all_wards():
    if not os.path.exists(GEOJSON_PATH):
        raise HTTPException(status_code=404, detail='Spatial dataset not found')
    with open(GEOJSON_PATH, 'r', encoding='utf-8') as f:
        geojson = json.load(f)
    return geojson

@router.get('/{ward_code}')
def get_ward_detail(ward_code: str):
    ward_code_clean = ward_code.upper().strip()
    if os.path.exists(BASE_CSV_PATH):
        df = pd.read_csv(BASE_CSV_PATH)
        ward_row = df[df['ward_code'].astype(str).str.upper() == ward_code_clean]
        if not ward_row.empty:
            result = clean_record(ward_row.iloc[0].to_dict())
            if os.path.exists(EXP_CSV_PATH):
                df_exp = pd.read_csv(EXP_CSV_PATH)
                exp_row = df_exp[df_exp['ward_code'].astype(str).str.upper() == ward_code_clean]
                if not exp_row.empty:
                    result['civic_ai_explanation'] = clean_record(exp_row.iloc[0].to_dict())
            return result
    raise HTTPException(status_code=404, detail=f'Ward {ward_code} not found')
