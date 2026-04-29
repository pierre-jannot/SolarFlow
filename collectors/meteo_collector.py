import json
import os
from datetime import date
import requests
import pandas as pd
import numpy as np

import config
import logging
from utils import validate_dataframe

METEO_ARCHIVE_URL = "https://archive-api.open-meteo.com/v1/archive"
_CACHE_DIR = os.path.join(os.path.dirname(__file__), "..", "data", "cache")

logger = logging.getLogger(__name__)


def _cache_path(key):
    os.makedirs(_CACHE_DIR, exist_ok=True)
    return os.path.join(_CACHE_DIR, f"{key}.json")


def _select_url(start_date_str):
    METEO_FORECAST_LOOKBACK_DAYS = 92
    start = date.fromisoformat(start_date_str)
    oldest_forecast = date.today().toordinal() - METEO_FORECAST_LOOKBACK_DAYS
    if start.toordinal() < oldest_forecast:
        return METEO_ARCHIVE_URL
    return config.METEO_BASE_URL


def fetch_irradiance_point(lat, lon, start_date, end_date):
    """Récupère les données d'irradiance pour un point donné."""
    logger.debug("Récupération irradiance Open-Meteo point (%s, %s)...", lat, lon)
    empty_df = pd.DataFrame(columns=["timestamp", "ghi", "dni", "dhi"])

    cache_key = f"meteo_{lat}_{lon}_{start_date}_{end_date}"
    cache_file = _cache_path(cache_key)

    try:
        if os.path.exists(cache_file):
            with open(cache_file, "r") as f:
                data = json.load(f)
        else:
            url = _select_url(start_date)
            params = {
                "latitude": lat,
                "longitude": lon,
                "hourly": "shortwave_radiation,direct_radiation,diffuse_radiation",
                "start_date": start_date,
                "end_date": end_date,
                "timezone": "auto",
            }

            response = requests.get(url, params=params)
            response.raise_for_status()
            data = response.json()

            with open(cache_file, "w") as f:
                json.dump(data, f)
    except Exception as e:
        logger.warning("Erreur réseau Open-Meteo pour le point (%s, %s) : %s", lat, lon, e)
        return empty_df

    if "hourly" not in data or "time" not in data["hourly"]:
        return empty_df

    hourly = data["hourly"]
    df = pd.DataFrame({
        "timestamp": pd.to_datetime(hourly["time"], utc=True),
        "ghi": hourly.get("shortwave_radiation", []),
        "dni": hourly.get("direct_radiation", []),
        "dhi": hourly.get("diffuse_radiation", []),
    })

    validate_dataframe(df, ["timestamp", "ghi", "dni", "dhi"], start_date, end_date)
    return df


def fetch_irradiance(lat, lon, start_date, end_date):
    """Récupère les données d'irradiance, potentiellement moyennées au niveau national.

    Args:
        lat: latitude du site (utilisé si grille désactivée)
        lon: longitude du site (utilisé si grille désactivée)
        start_date: date de début au format YYYY-MM-DD
        end_date: date de fin au format YYYY-MM-DD

    Returns:
        DataFrame avec les colonnes timestamp, ghi, dni, dhi
    """
    if not getattr(config, "USE_NATIONAL_IRRADIANCE", False):
        logger.info("Irradiance: mode point unique (%s, %s)", lat, lon)
        return fetch_irradiance_point(lat, lon, start_date, end_date)

    logger.info("Irradiance: mode grille nationale activé")
    resolution = getattr(config, "IRRADIANCE_GRID_RESOLUTION", 1.0)
    
    # Grille France métropolitaine
    lats = np.arange(42.0, 51.0 + resolution, resolution)
    lons = np.arange(-5.0, 8.0 + resolution, resolution)
    
    all_dfs = []
    
    for current_lat in lats:
        for current_lon in lons:
            df_point = fetch_irradiance_point(current_lat, current_lon, start_date, end_date)
            if not df_point.empty:
                all_dfs.append(df_point)
                
    if not all_dfs:
        logger.error("Irradiance nationale: aucun point n'a retourné de données.")
        return pd.DataFrame(columns=["timestamp", "ghi", "dni", "dhi"])
        
    logger.info("Irradiance nationale: calcul de la moyenne sur %d points", len(all_dfs))
    
    # Concatener tous les DataFrames
    combined_df = pd.concat(all_dfs, ignore_index=True)
    
    # Calculer la moyenne pour chaque timestamp
    mean_df = combined_df.groupby("timestamp").mean().reset_index()
    
    validate_dataframe(mean_df, ["timestamp", "ghi", "dni", "dhi"], start_date, end_date)
    return mean_df
