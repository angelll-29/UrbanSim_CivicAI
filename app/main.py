import os
from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from fastapi.staticfiles import StaticFiles

from app.api.routes import auth, wards, dashboard, predictions, complaints

app = FastAPI(
    title='UrbanSim Civic AI API',
    description='GIS-based Urban Intelligence & Participatory Planning Platform for Mumbai BMC (24 Wards)',
    version='2.0.0-RBAC'
)

app.add_middleware(
    CORSMiddleware,
    allow_origins=['*'],
    allow_credentials=True,
    allow_methods=['*'],
    allow_headers=['*'],
)

# Authentication & Admin
app.include_router(auth.router, prefix='/api/auth', tags=['Authentication & Admin'])

# Domain & GIS Datasets
app.include_router(wards.router, prefix='/api/wards', tags=['Wards'])
app.include_router(dashboard.router, prefix='/api/dashboard', tags=['Dashboard'])
app.include_router(predictions.router, prefix='/api/predictions', tags=['Predictions & AI'])
app.include_router(complaints.router, prefix='/api/complaints', tags=['Complaints & CCRS'])

# Static mount for spatial datasets
SPATIAL_DIR = os.path.join(os.path.dirname(os.path.dirname(os.path.abspath(__file__))), 'data', 'spatial')
if os.path.exists(SPATIAL_DIR):
    app.mount('/api/spatial', StaticFiles(directory=SPATIAL_DIR), name='spatial')

@app.get('/api/health')
def health_check():
    return {
        'status': 'online',
        'platform': 'UrbanSim Civic AI',
        'security': 'RBAC Active',
        'region': 'Mumbai BMC 24 Wards'
    }
