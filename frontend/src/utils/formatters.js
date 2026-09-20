import { STRESS_BANDS, CLUSTER_COLORS } from '../constants';

export const formatNumber = (val) => {
  if (val === null || val === undefined || isNaN(val) || val === '') return 'No data';
  return Number(val).toLocaleString('en-IN');
};

export const formatPercent = (val, decimals = 1) => {
  if (val === null || val === undefined || isNaN(val) || val === '') return 'No data';
  return `${Number(val).toFixed(decimals)}%`;
};

export const formatStressScore = (val) => {
  if (val === null || val === undefined || isNaN(val) || val === '') return 'No data';
  return Number(val).toFixed(1);
};

/**
 * Returns style metadata for the authoritative GeoJSON stress_band.
 * Does NOT recompute or alter the band supplied by GeoJSON.
 */
export const getStressBandStyle = (stressBand) => {
  if (stressBand && STRESS_BANDS[stressBand]) {
    return STRESS_BANDS[stressBand];
  }
  return STRESS_BANDS['Moderate'];
};

export const getStressBand = getStressBandStyle;

/**
 * Returns the color for a ward using the authoritative stress_band directly,
 * or derives it from a numeric stress score if the band is not supplied.
 * Handles arguments in any order (band or score).
 */
export const getStressColor = (arg1, arg2 = null) => {
  // Check if arg1 is a recognized stress band
  if (typeof arg1 === 'string' && STRESS_BANDS[arg1]) {
    return STRESS_BANDS[arg1].color;
  }
  // Check if arg2 is a recognized stress band
  if (typeof arg2 === 'string' && STRESS_BANDS[arg2]) {
    return STRESS_BANDS[arg2].color;
  }

  // Parse numeric score from either argument
  let score = null;
  if (arg1 !== null && arg1 !== undefined && !isNaN(Number(arg1)) && arg1 !== '') {
    score = Number(arg1);
  } else if (arg2 !== null && arg2 !== undefined && !isNaN(Number(arg2)) && arg2 !== '') {
    score = Number(arg2);
  }

  if (score !== null) {
    if (score < 30) return STRESS_BANDS['Very Low'].color;
    if (score < 45) return STRESS_BANDS['Low'].color;
    if (score < 60) return STRESS_BANDS['Moderate'].color;
    if (score < 75) return STRESS_BANDS['High'].color;
    return STRESS_BANDS['Very High'].color;
  }

  return '#64748b';
};

export const getClusterColor = (clusterName) => {
  return CLUSTER_COLORS[clusterName] || '#94a3b8';
};
