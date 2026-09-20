export const WARD_NAMES = {
  'A': 'Colaba / Fort / Churchgate',
  'B': 'Sandhurst Road / Dongri / Bhendi Bazaar',
  'C': 'Marine Lines / Dhobi Talao / Bhuleshwar',
  'D': 'Malabar Hill / Grant Road / Walkeshwar / Tardeo',
  'E': 'Byculla / Mazgaon',
  'FN': 'Matunga / Sion / Wadala North',
  'FS': 'Parel / Sewri / Wadala South',
  'GN': 'Dadar / Dharavi / Mahim',
  'GS': 'Worli / Lower Parel / Prabhadevi',
  'HE': 'Santacruz East / Khar East / Bandra East',
  'HW': 'Bandra West / Khar West / Santacruz West',
  'KE': 'Andheri East / Jogeshwari East / Vile Parle East',
  'KW': 'Andheri West / Jogeshwari West / Versova',
  'L': 'Kurla / Sakinaka / Chunabhatti',
  'ME': 'Mankhurd / Govandi / Shivaji Nagar',
  'MW': 'Chembur / Tilak Nagar / Trombay',
  'N': 'Ghatkopar / Vikhroli West',
  'PN': 'Malad / Marve / Manori',
  'PS': 'Goregaon / Oshiwara',
  'RC': 'Borivali / Gorai',
  'RN': 'Dahisar',
  'RS': 'Kandivali / Charkop',
  'S': 'Bhandup / Powai / Kanjurmarg',
  'T': 'Mulund / Nahur'
};

export const STRESS_BANDS = {
  'Very Low': { label: 'Very Low', color: '#10b981', bg: 'rgba(16, 185, 129, 0.15)', border: 'rgba(16, 185, 129, 0.4)', text: '#34d399', range: '0 - 30' },
  'Low': { label: 'Low', color: '#06b6d4', bg: 'rgba(6, 182, 212, 0.15)', border: 'rgba(6, 182, 212, 0.4)', text: '#22d3ee', range: '30 - 45' },
  'Moderate': { label: 'Moderate', color: '#eab308', bg: 'rgba(234, 179, 8, 0.15)', border: 'rgba(234, 179, 8, 0.4)', text: '#facc15', range: '45 - 60' },
  'High': { label: 'High', color: '#f97316', bg: 'rgba(249, 115, 22, 0.15)', border: 'rgba(249, 115, 22, 0.4)', text: '#fb923c', range: '60 - 75' },
  'Very High': { label: 'Very High', color: '#ef4444', bg: 'rgba(239, 68, 68, 0.15)', border: 'rgba(239, 68, 68, 0.4)', text: '#f87171', range: '75 - 100' }
};

export const LENSES = [
  { id: 'livability', name: 'Relative Urban Pressure', icon: 'Activity', desc: 'Percentile-based analytical index across 24 BMC wards (non-governmental)', field: 'urban_stress', unit: 'Percentile Index (0-100)' },
  { id: 'healthcare', name: 'Healthcare', icon: 'HeartPulse', desc: 'UPHCs, Dispensaries, Hospitals & Population Ratios', field: 'healthcare_stress', unit: 'Relative %' },
  { id: 'education', name: 'Education', icon: 'GraduationCap', desc: 'Schools, Student/Teacher Ratios & Facility Quality', field: 'education_stress', unit: 'Relative %' },
  { id: 'safety', name: 'Safety', icon: 'Shield', desc: 'Police Stations, Fire Stations & Population Coverage', field: 'safety_stress', unit: 'Relative %' },
  { id: 'mobility', name: 'Mobility / Transport', icon: 'Bus', desc: 'BEST Bus, Suburban Rail, Metro & Monorail Nodes', field: 'transport_stress', unit: 'Relative %' },
  { id: 'sanitation', name: 'Sanitation', icon: 'Droplets', desc: 'Public Toilet Density & Population Coverage Ratios', field: 'sanitation_stress', unit: 'Relative %' },
  { id: 'green_space', name: 'Green Space', icon: 'Trees', desc: 'Parks, Gardens & Green Space Area per Capita', field: 'green_space_stress', unit: 'Relative %' },
  { id: 'environment', name: 'Environment', icon: 'Wind', desc: 'Freshness-aware Air Quality Monitoring Network', field: 'environmental_station_presence', unit: 'Stations' },
  { id: 'civic', name: 'Civic Complaints', icon: 'MessageSquare', desc: '2024 CCRS Grievance Volumes, Closure Rates & Aging', field: 'civic_stress', unit: 'Relative %' },
  { id: 'clusters', name: 'AI Clusters', icon: 'Network', desc: 'Deep Learning Latent Spatial Typology (4 Clusters)', field: 'cluster', unit: 'Cluster ID' },
  { id: 'anomalies', name: 'AI Anomalies', icon: 'AlertTriangle', desc: 'Autoencoder Reconstruction Anomaly Candidates', field: 'anomaly_candidate', unit: 'Reconstruction Error' },
  { id: 'scenarios', name: 'What-if Scenarios', icon: 'Sliders', desc: 'Simulated 20% Capacity Interventions & Modeled Delta', field: 'best_scenario_change', unit: 'Modeled Delta' }
];

export const FACILITY_LAYERS = [
  { id: 'healthcare', name: 'Healthcare Facilities', icon: 'HeartPulse', color: '#ef4444', file: 'mumbai_healthcare_validated.geojson', defaultOn: false, count: 458 },
  { id: 'schools', name: 'Schools & Education', icon: 'GraduationCap', color: '#3b82f6', file: 'mumbai_schools_validated.geojson', defaultOn: false, count: 2247 },
  { id: 'transport', name: 'Transport Nodes', icon: 'Bus', color: '#f59e0b', file: 'mumbai_metro_monorail_validated.geojson', extraFile: 'mumbai_suburban_railway_stations_validated.geojson', defaultOn: false, count: 271 },
  { id: 'safety', name: 'Safety (Police & Fire)', icon: 'Shield', color: '#8b5cf6', file: 'mumbai_police_stations_validated.geojson', extraFile: 'mumbai_fire_stations_validated.geojson', defaultOn: false, count: 154 },
  { id: 'toilets', name: 'Public Toilets', icon: 'Droplets', color: '#06b6d4', file: 'mumbai_public_toilets_validated.geojson', defaultOn: false, count: 8411 },
  { id: 'green_spaces', name: 'Green Spaces', icon: 'Trees', color: '#10b981', file: 'mumbai_green_spaces_validated.geojson', defaultOn: false, count: 988 },
  { id: 'environment', name: 'AQ Stations (Freshness)', icon: 'Wind', color: '#ec4899', file: 'mumbai_air_quality_stations_validated.geojson', defaultOn: true, count: 31 }
];

export const SCENARIOS = [
  { id: 'healthcare_capacity_plus_20', name: 'Healthcare Capacity +20%', desc: 'Increases local primary and hospital capacity coverage by 20%', domain: 'Healthcare' },
  { id: 'public_toilet_plus_20', name: 'Public Toilet Capacity +20%', desc: 'Expands public toilet seat density across high-density wards by 20%', domain: 'Sanitation' },
  { id: 'green_space_plus_20', name: 'Green Space +20%', desc: 'Expands accessible urban green canopy and park infrastructure by 20%', domain: 'Green Space' },
  { id: 'public_transport_plus_20', name: 'Public Transport Nodes +20%', desc: 'Adds feeder transit coverage and bus frequency by 20%', domain: 'Transport' },
  { id: 'resolution_time_minus_20', name: 'CCRS Resolution Time -20%', desc: 'Accelerates civic grievance turnaround speed by 20%', domain: 'Civic' }
];

export const CLUSTER_COLORS = {
  'Cluster_1': '#38bdf8',
  'Cluster_2': '#a855f7',
  'Cluster_3': '#f59e0b',
  'Cluster_4': '#ec4899'
};

export const DOMAINS = [
  { key: 'healthcare_stress', name: 'Healthcare', icon: 'HeartPulse', color: '#ef4444' },
  { key: 'education_stress', name: 'Education', icon: 'GraduationCap', color: '#3b82f6' },
  { key: 'sanitation_stress', name: 'Sanitation', icon: 'Droplets', color: '#06b6d4' },
  { key: 'safety_stress', name: 'Safety', icon: 'Shield', color: '#8b5cf6' },
  { key: 'transport_stress', name: 'Transport', icon: 'Bus', color: '#f59e0b' },
  { key: 'civic_stress', name: 'Civic Grievances', icon: 'MessageSquare', color: '#eab308' },
  { key: 'green_space_stress', name: 'Green Space', icon: 'Trees', color: '#10b981' }
];

export const METHODOLOGY_NOTE = "Relative Urban Pressure is a percentile-normalized composite index across Mumbai's 24 BMC wards. It reflects relative model-derived pressure across 15 audited indicators and 7 domains, and is not an official government risk rating.";

export const SCENARIO_DISCLAIMER = "The scenario engine represents modeled changes under fixed-reference assumptions and should not be interpreted as causal estimates.";
