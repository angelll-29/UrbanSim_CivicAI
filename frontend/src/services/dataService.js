let cachedGeoJSON = null;
let cachedBaseWardData = null;
let cachedExplanations = null;
let cachedAnomalies = null;
let cachedAnomalyFeatures = null;
let cachedScenarios = null;
let cachedClusters = null;
let cachedEnvProfiles = null;
let cachedComplaints = null;

export const loadMasterGeoJSON = async () => {
  if (cachedGeoJSON) return cachedGeoJSON;
  try {
    const res = await fetch('/data/mumbai_urbansim_intelligence.geojson');
    if (!res.ok) throw new Error('Failed to load spatial intelligence GeoJSON');
    cachedGeoJSON = await res.json();
    return cachedGeoJSON;
  } catch (err) {
    console.error('Error loading GeoJSON:', err);
    throw err;
  }
};

export const loadAllDatasets = async () => {
  try {
    const [
      geojson,
      baseData,
      explanations,
      anomalies,
      anomalyFeatures,
      scenarios,
      clusters,
      envProfiles,
      complaints
    ] = await Promise.all([
      loadMasterGeoJSON(),
      fetch('/data/ward_base_intelligence.json').then(r => r.json()).catch(() => []),
      fetch('/data/civic_ai_explanations.json').then(r => r.json()).catch(() => []),
      fetch('/data/ward_anomaly_scores.json').then(r => r.json()).catch(() => []),
      fetch('/data/ward_anomaly_features.json').then(r => r.json()).catch(() => []),
      fetch('/data/scenario_results.json').then(r => r.json()).catch(() => []),
      fetch('/data/cluster_profiles.json').then(r => r.json()).catch(() => []),
      fetch('/data/environmental_profiles.json').then(r => r.json()).catch(() => []),
      fetch('/data/ccrs_complaints_2024.json').then(r => r.json()).catch(() => [])
    ]);

    cachedBaseWardData = baseData;
    cachedExplanations = explanations;
    cachedAnomalies = anomalies;
    cachedAnomalyFeatures = anomalyFeatures;
    cachedScenarios = scenarios;
    cachedClusters = clusters;
    cachedEnvProfiles = envProfiles;
    cachedComplaints = complaints;

    return {
      geojson,
      baseData,
      explanations,
      anomalies,
      anomalyFeatures,
      scenarios,
      clusters,
      envProfiles,
      complaints
    };
  } catch (err) {
    console.error('Error loading all datasets:', err);
    throw err;
  }
};

export const loadFacilityLayerData = async (filename) => {
  try {
    const res = await fetch(`/data/${filename}`);
    if (!res.ok) throw new Error(`Failed to load ${filename}`);
    return await res.json();
  } catch (err) {
    console.error(`Error loading layer ${filename}:`, err);
    return null;
  }
};
