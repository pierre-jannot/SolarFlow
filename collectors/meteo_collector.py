import json
import os
from datetime import date
import requests
import pandas as pd

import config
import logging

METEO_ARCHIVE_URL = "https://archive-api.open-meteo.com/v1/archive"
_CACHE_DIR = os.path.join(os.path.dirname(__file__), "..", "data", "cache")

logger = logging.getLogger(__name__)


def _cache_path(key):
    os.makedirs(_CACHE_DIR, exist_ok=True)
    return os.path.join(_CACHE_DIR, f"{key}.json")


METEO_FORECAST_LOOKBACK_DAYS = 92


def _select_url(start_date_str):
    start = date.fromisoformat(start_date_str)
    oldest_forecast = date.today().toordinal() - METEO_FORECAST_LOOKBACK_DAYS
    if start.toordinal() < oldest_forecast:
        return METEO_ARCHIVE_URL
    return config.METEO_BASE_URL


def fetch_irradiance(lat, lon, start_date, end_date):
    """Récupère les données d'irradiance solaire depuis Open-Meteo.

    Args:
        lat: latitude du site
        lon: longitude du site
        start_date: date de début au format YYYY-MM-DD
        end_date: date de fin au format YYYY-MM-DD

    Returns:
        DataFrame avec les colonnes timestamp, ghi, dni, dhi
    """
    logger.info("Récupération irradiance Open-Meteo (%s, %s)...", lat, lon)

    cache_key = f"meteo_{lat}_{lon}_{start_date}_{end_date}"
    cache_file = _cache_path(cache_key)

    if os.path.exists(cache_file):
        logger.debug("Chargement depuis le cache local : %s", cache_file)
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

        try:
            response = requests.get(url, params=params)
            response.raise_for_status()
            data = response.json()
        except requests.exceptions.RequestException as e:
            raise RuntimeError(f"Erreur réseau Open-Meteo ({url}): {e}") from e

        with open(cache_file, "w") as f:
            json.dump(data, f)

    hourly = data["hourly"]

    df = pd.DataFrame({
        "timestamp": pd.to_datetime(hourly["time"]),
        "ghi": hourly["shortwave_radiation"],
        "dni": hourly["direct_radiation"],
        "dhi": hourly["diffuse_radiation"],
    })

    logger.info("Open-Meteo : %d enregistrements récupérés", len(df))
    return df
